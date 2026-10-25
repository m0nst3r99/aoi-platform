"""Fixture-specific portable replay, not a native reader or publication adapter."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import runpy

from aoi_platform.inventory import InventorySuccess
from aoi_platform.pad_candidates import (PadCandidateRequest, PadParent, SourcePad,
    PadRectangle, PadProvenance, EvidenceReference, PadBatchFailure, PadTruncation,
    build_rectangular_pad_candidates)
from aoi_platform.geometry.models import Frame, FrameKind, Unit, AxisDirection, Point2
from aoi_platform.geometry.transforms import Transform2, TransformKind
from aoi_platform.geometry.errors import GeometryError, ErrorCode
from aoi_platform.geometry.reports import ContractError, ValidationReport

schema = runpy.run_path(str(Path(__file__).with_name('observation_schema.py')))['schema']
PCB_HASH = '56ef80c3e8ef0bf2d530f10a93155b423506756fac63c9961098fd5fd85747a6'
PARENT = '00000000-0000-0000-0000-000000000834'
PADS = ('00000000-0000-0000-0000-000000000835', '00000000-0000-0000-0000-000000000836')


@dataclass(frozen=True)
class NormalizationEvidence:
    native_frame: Frame
    normalized_frame: Frame
    formula: str
    translation_mm: tuple
    observation_sha256: str
    raw_layers: tuple
    coordinate_accessor: str = 'PAD.GetPosition (world); no footprint translation reapplied'
    scope: str = 'fixture replay; build/schema values are not backend authentication'


@dataclass(frozen=True)
class ReplaySuccess:
    batch: object
    normalization: NormalizationEvidence


def _require(ok, field, code=ErrorCode.SCHEMA_INVALID):
    if not ok:
        raise GeometryError(code, 'Replay declaration or observation rejected.', field_path=field)


def replay_repeated_pads(pcb_bytes, raw, inventory, *, pcb_artifact_id, observation_artifact_id,
                         board_id, scope_id, parent_id, pad_ids, native_frame, normalized_frame,
                         target_frame, normalization, translation_mm, policy,
                         max_pcb_bytes, max_observation_bytes):
    """Caller supplies identities, conventions, transforms and explicit byte limits.

    Only the accepted repeated-pads source snapshot is admitted. Observation JSON
    is validated but not authenticated. Reflection is separate from the candidate's
    rigid transform; all original layers survive in immutable replay evidence.
    """
    try:
        for limit in (max_pcb_bytes, max_observation_bytes):
            _require(type(limit) is int and 0 < limit <= 16*1024*1024, 'limits', ErrorCode.POLICY_INVALID)
        _require(type(raw) is bytes and type(pcb_bytes) is bytes, 'bytes')
        _require(len(raw) <= max_observation_bytes and len(pcb_bytes) <= max_pcb_bytes,
                 'bytes.limit', ErrorCode.INPUT_LIMIT_EXCEEDED)
        _require(type(inventory) is InventorySuccess, 'inventory')
        inv = inventory.inventory
        _require(type(inv.artifacts) is tuple and len(inv.artifacts) <= 1024, 'inventory.artifacts')
        matches = {}
        for identity, content, role in ((pcb_artifact_id, pcb_bytes, 'kicad_pcb'),
                                       (observation_artifact_id, raw, 'supporting')):
            found = [o for o in inv.artifacts if o.declaration.artifact_id == identity]
            _require(len(found) == 1, 'inventory.artifact', ErrorCode.SOURCE_CONFLICT)
            o = found[0]; digest = sha256(content).hexdigest()
            _require(o.declaration.role == role and o.eof is True and
                     type(o.actual_size) is int and o.actual_size == len(content) == o.bytes_read and
                     o.computed_sha256 == digest == o.declaration.declared_sha256.lower(),
                     'inventory.hash_or_size', ErrorCode.SOURCE_CONFLICT)
            matches[role] = o
        _require(sha256(pcb_bytes).hexdigest() == PCB_HASH, 'fixture.hash', ErrorCode.SOURCE_CONFLICT)
        data = json.loads(raw)
        schema(data)  # Strict-v2 only, never legacy opt-in.
        _require(data['input_sha256'] == PCB_HASH, 'input_sha256', ErrorCode.SOURCE_CONFLICT)
        _require(data['build'] == '10.0.7' and data['format_version'] == 20240108,
                 'build_or_format', ErrorCode.FORMAT_UNSUPPORTED)
        _require(data['outline']['valid'] is True, 'outline.valid', ErrorCode.OUTLINE_INVALID)
        _require(normalization == 'N(x,y)=(x,-y)' and type(translation_mm) is tuple and
                 len(translation_mm) == 2 and all(type(v) in (int,float) for v in translation_mm)
                 and translation_mm == (0,20), 'normalization')
        for frame, kind, axis in ((native_frame,FrameKind.SOURCE,AxisDirection.DOWN),
                                 (normalized_frame,FrameKind.SOURCE,AxisDirection.UP),
                                 (target_frame,FrameKind.PCB,AxisDirection.UP)):
            _require(type(frame) is Frame and frame.kind is kind and frame.unit is Unit.MM and
                     frame.x_direction is AxisDirection.RIGHT and frame.y_direction is axis and
                     frame.board_revision_id == scope_id and frame.machine_id is None and
                     frame.capture_id is None, 'frame', ErrorCode.CONTEXT_MISMATCH)
        _require(native_frame.origin == normalized_frame.origin and
                 native_frame.frame_id != normalized_frame.frame_id, 'normalization.frames', ErrorCode.CONTEXT_MISMATCH)
        _require(len(data['footprints']) == 1 and not data['footprint_edges'], 'fixture.subset', ErrorCode.GEOMETRY_UNSUPPORTED)
        f = data['footprints'][0]
        _require(f['uuid'] == PARENT and f['layer'] == 'F.Cu' and f['angle_deg'] == 0 and
                 len(f['pads']) == 2 and {p['uuid'] for p in f['pads']} == set(PADS),
                 'fixture.entities', ErrorCode.GEOMETRY_UNSUPPORTED)
        _require(type(pad_ids) is tuple and len(pad_ids) == 2 and all(type(pair) is tuple and
                 len(pair) == 2 and all(type(s) is str and s for s in pair) for pair in pad_ids), 'pad_ids')
        ids = dict(pad_ids)
        _require(len(ids) == 2 and set(ids) == set(PADS), 'pad_ids')
        obs_hash = sha256(raw).hexdigest()
        refs = (EvidenceReference(pcb_artifact_id, PCB_HASH, 'accepted repeated-pads source'),
                EvidenceReference(observation_artifact_id, obs_hash, normalization+'; caller translation (0,20)'))
        def provenance(entity):
            return PadProvenance(pcb_artifact_id, matches['kicad_pcb'].declaration.source_id,
                PCB_HASH, entity, inv.manifest.source_snapshot, inv.manifest.fixture_revision,
                'repeated-pads-replay', '1', refs)
        transform = Transform2('replay-declared-translation', normalized_frame, target_frame,
            ((1.,0.,float(translation_mm[0])),(0.,1.,float(translation_mm[1])),(0.,0.,1.)), TransformKind.RIGID)
        parent = PadParent(parent_id, PARENT, pcb_artifact_id, normalized_frame, 'board-source',
                           'top', transform, refs, provenance(PARENT))
        pads = []
        for p in f['pads']:
            _require(p['shape'] == 1 and p['attribute'] == 1 and p['angle_deg'] == 0 and
                     p['drill_mm'] == [0,0] and sorted(p['layers']) == ['F.Cu','F.Mask','F.Paste'],
                     'pad.subset', ErrorCode.GEOMETRY_UNSUPPORTED)
            x,y = p['position_mm']  # Already world coordinates. Never add f.position_mm.
            pads.append(SourcePad(ids[p['uuid']], parent_id, p['uuid'], PARENT, pcb_artifact_id,
                normalized_frame, p['number'], 'top', ('F.Cu',), 'smd', None,
                PadRectangle(Point2(x,-y,normalized_frame), *p['size_mm'], 0.), provenance(p['uuid']), p['net']))
        batch = build_rectangular_pad_candidates(PadCandidateRequest('rect-pad-candidate-v1', policy,
            board_id, scope_id, target_frame, inventory, (parent,), tuple(pads)))
        if isinstance(batch, PadBatchFailure):
            return batch
        return ReplaySuccess(batch, NormalizationEvidence(native_frame, normalized_frame, normalization,
            translation_mm, obs_hash, tuple(sorted((p['uuid'],tuple(p['layers'])) for p in f['pads']))))
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as exc:
        error = exc if isinstance(exc, GeometryError) else GeometryError(ErrorCode.SCHEMA_INVALID,
            'Malformed replay input.', field_path='replay')
        issue = ContractError.from_geometry_error(error, remediation='Correct explicit replay inputs; do not infer metadata.')
        return PadBatchFailure(ValidationReport('repeated-pads-replay','fixture-replay-v1',
            (issue,), (('scope','evaluation-replay-only'),)), PadTruncation(False))
