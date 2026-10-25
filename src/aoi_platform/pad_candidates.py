"""Bounded synthetic rectangular copper candidates; no parsing or publication."""
from dataclasses import dataclass, fields, asdict
from collections import Counter
from math import cos, sin, radians, isfinite
from typing import Literal

from .inventory import (InventorySuccess, ArtifactInventory, InventoryManifest,
                        ArtifactObservation, ArtifactDeclaration)
from .geometry.models import Frame, FrameKind, Unit, AxisDirection, Parity, Point2, require_same_frame, frame_evidence
from .geometry.transforms import Transform2, TransformKind
from .geometry.errors import GeometryError, ErrorCode as Code, finite_number, diagnostic_json
from .geometry.reports import ContractError, SourceLocation, ValidationReport, ReportStatus, Severity


@dataclass(frozen=True, slots=True)
class SyntheticPadPolicy:
    policy_id: str
    version: str
    max_pads: int
    max_parents: int
    max_inventory_artifacts: int
    max_id_utf8_bytes: int
    max_text_utf8_bytes: int
    max_evidence_refs_per_record: int
    max_total_evidence_refs: int
    max_total_input_utf8_bytes: int
    max_diagnostics: int
    max_diagnostic_utf8_bytes: int
    max_total_diagnostic_utf8_bytes: int
    max_abs_coordinate_mm: float
    min_dimension_mm: float
    max_dimension_mm: float
    max_abs_angle_deg: float
    rigid_guard_abs: float
    rigid_guard_rel: float
    test_oracle_abs_mm: float


# Exact selected synthetic policy values; callers must explicitly supply every field.
_POLICY = ('synthetic-rect-pad-candidate', '1', 4096, 4096, 1024, 256, 1024,
           16, 32768, 8388608, 128, 4096, 524288, 1000000.0, 0.000001,
           1000000.0, 360000.0, 1e-12, 0.0, 1e-6)


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    artifact_id: str
    computed_sha256: str
    locator: str


@dataclass(frozen=True, slots=True)
class PadProvenance:
    artifact_id: str
    source_id: str
    computed_sha256: str
    source_entity_id: str
    source_snapshot: str
    fixture_revision: str
    authoring_profile: str
    version: str
    evidence: tuple[EvidenceReference, ...]
    source_location: SourceLocation | None = None


@dataclass(frozen=True, slots=True)
class PadParent:
    footprint_id: str
    source_entity_id: str
    artifact_id: str
    source_frame: Frame
    coordinate_basis: Literal['board-source', 'footprint-local']
    side: Literal['top']
    source_to_p: Transform2
    convention_evidence: tuple[EvidenceReference, ...]
    provenance: PadProvenance


@dataclass(frozen=True, slots=True)
class PadRectangle:
    center: Point2
    width: float
    height: float
    angle_deg: float


@dataclass(frozen=True, slots=True)
class SourcePad:
    pad_id: str
    footprint_id: str
    source_entity_id: str
    source_parent_entity_id: str
    artifact_id: str
    source_frame: Frame
    pad_number: str
    side: Literal['top']
    copper_layers: tuple[str, ...]
    pad_type: Literal['smd']
    drill: None
    rectangle: PadRectangle
    provenance: PadProvenance
    net: str | None = None


@dataclass(frozen=True, slots=True)
class PadCandidateRequest:
    schema_version: str
    policy: SyntheticPadPolicy
    board_id: str
    candidate_scope_id: str
    target_frame: Frame
    inventory: InventorySuccess
    parents: tuple[PadParent, ...]
    pads: tuple[SourcePad, ...]


@dataclass(frozen=True, slots=True)
class CanonicalPadCandidate:
    board_id: str
    candidate_scope_id: str
    schema_version: str
    policy: SyntheticPadPolicy
    source: SourcePad
    parent: PadParent
    vertices: tuple[Point2, Point2, Point2, Point2]
    # No public constructor switches can grant authority.
    @property
    def published(self) -> Literal[False]:
        return False

    @property
    def targeting_authorized(self) -> Literal[False]:
        return False

    @property
    def association_status(self) -> Literal['declaration-consistent']:
        return 'declaration-consistent'

    @property
    def pad_id(self) -> str:
        return self.source.pad_id


@dataclass(frozen=True, slots=True)
class PadTruncation:
    occurred: bool
    reason: str | None = None
    omitted_count: int | None = None


@dataclass(frozen=True, slots=True)
class PadBatchSuccess:
    candidates: tuple[CanonicalPadCandidate, ...]
    report: ValidationReport


@dataclass(frozen=True, slots=True)
class PadBatchFailure:
    report: ValidationReport
    truncation: PadTruncation


class _Stop(Exception):
    pass


def _fail(code, path, message, expected=None, actual=None):
    raise GeometryError(code, message, field_path=path,
                        expected=expected, actual=actual)


def _require(ok, path, message='Invalid required field.', code=Code.SCHEMA_INVALID):
    if not ok:
        _fail(code, path, message)


def _id(value, path):
    _require(type(value) is str and len(value) > 0, path, 'Nonempty exact identity required.')


def _digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


class _Issues:
    def __init__(self, policy):
        self.policy = policy
        self.issues = []
        self.used = 0
        self.truncation = PadTruncation(False)
        self.context = ()
        self.entity = None
        self.artifact = None
        self.location = None

    def exhaust(self, reason):
        self.truncation = PadTruncation(True, reason, None)
        self.issues.append(ContractError(Code.INPUT_LIMIT_EXCEEDED,
            'Bounded validation incomplete.', 'budget', 'Reduce the request and retry.',
            context=(('reason', reason), ('policy_id', self.policy.policy_id))))
        raise _Stop

    def add(self, error):
        # Report text fields disallow whitespace-only strings; opaque candidate
        # identities do not. Preserve these exact values as JSON, never trim IDs.
        context = tuple((k, v if v.strip() else diagnostic_json(v)) for k, v in self.context)
        entity, artifact = self.entity, self.artifact
        for key, value in (('entity_id_json', entity), ('artifact_id_json', artifact)):
            if value is not None and not value.strip():
                context += ((key, diagnostic_json(value)),)
        issue = ContractError.from_geometry_error(error, remediation='Correct the declaration and retry.',
            context=context, entity_id=entity if entity and entity.strip() else None,
            artifact_id=artifact if artifact and artifact.strip() else None,
            source_location=self.location)
        # Each input string has already been bounded. The issue has bounded field
        # count, so this serialization is bounded even when it exceeds one issue cap.
        size = len(diagnostic_json(issue.to_dict()).encode('utf-8'))
        if len(self.issues) >= self.policy.max_diagnostics - 1:
            self.exhaust('issue_count')
        if size > self.policy.max_diagnostic_utf8_bytes or self.used + size > (
                self.policy.max_total_diagnostic_utf8_bytes - self.policy.max_diagnostic_utf8_bytes):
            self.exhaust('issue_bytes')
        self.issues.append(issue)
        self.used += size

    def check(self, fn):
        try:
            fn()
            return True
        except GeometryError as error:
            self.add(error)
            return False

    def finish(self, candidates=()):
        report = ValidationReport('canonical-pad-candidate', self.policy.policy_id,
            tuple(self.issues), (('scope', 'canonical-pad-candidate-only'),),
            context=(('published', 'false'), ('targeting_authorized', 'false')))
        if self.issues:
            return PadBatchFailure(report, self.truncation)
        return PadBatchSuccess(tuple(candidates), report)


_ALLOWED = {PadCandidateRequest, SyntheticPadPolicy, EvidenceReference, PadProvenance,
            PadParent, PadRectangle, SourcePad, Frame, Point2, Transform2,
            InventorySuccess, ArtifactInventory, InventoryManifest, ArtifactObservation,
            ArtifactDeclaration, ValidationReport, ContractError, SourceLocation}


def _preflight(request, sink):
    """Bound work BEFORE sorting, building indexes, repr/asdict or encoding metadata.

    Visit occurrences (not unique object identities). Derived node budget bounds
    malformed empty nested tuples too; depth 32 exceeds valid record nesting.
    Exact types exclude executable iterators, custom getattr and mutable containers.
    """
    p = sink.policy
    nodes = 0
    text_bytes = 0
    refs = 0
    max_nodes = 64 * (p.max_pads + p.max_parents + p.max_inventory_artifacts + p.max_total_evidence_refs)
    stack = [(request, 'request', 0)]
    while stack:
        value, name, depth = stack.pop()
        nodes += 1
        if nodes > max_nodes or depth > 32:
            sink.exhaust('input_budget')
        if type(value) is str:
            cap = p.max_text_utf8_bytes if name in {
                'net', 'locator', 'source', 'message', 'remediation', 'expected', 'actual',
                'source_snapshot', 'fixture_revision'} else p.max_id_utf8_bytes
            if len(value) > cap:
                sink.exhaust('input_budget')
            size = 0
            for char in value:
                n = ord(char)
                _require(not 0xD800 <= n <= 0xDFFF, name, 'Invalid Unicode scalar.')
                size += 1 if n < 128 else 2 if n < 2048 else 3 if n < 65536 else 4
                if size > cap:
                    sink.exhaust('input_budget')
            text_bytes += size
            if text_bytes > p.max_total_input_utf8_bytes:
                sink.exhaust('input_budget')
        elif type(value) is tuple:
            cap = {'pads': p.max_pads, 'parents': p.max_parents,
                   'artifacts': p.max_inventory_artifacts,
                   'evidence': p.max_evidence_refs_per_record,
                   'convention_evidence': p.max_evidence_refs_per_record}.get(name, p.max_total_evidence_refs)
            if len(value) > cap:
                sink.exhaust('input_budget')
            # Wide metadata structures are bounded without expanding the stack.
            if nodes + len(stack) + len(value) > max_nodes:
                sink.exhaust('input_budget')
            stack.extend((v, name, depth + 1) for v in reversed(value))
        elif type(value) in _ALLOWED:
            if type(value) is EvidenceReference:
                refs += 1
                if refs > p.max_total_evidence_refs:
                    sink.exhaust('input_budget')
            stack.extend((getattr(value, f.name), f.name, depth + 1) for f in reversed(fields(value)))
        elif type(value) is int:
            _require(value.bit_length() <= 1024, name, 'Integer exceeds binary64 input range.')
        elif value is None or type(value) in (bool, float, FrameKind, Unit, AxisDirection,
                                              Parity, TransformKind, Code, ReportStatus, Severity):
            pass
        else:
            _fail(Code.SCHEMA_INVALID, name, 'Immutable declared record/tuple required.')


def _frame(frame, request, source=False):
    _require(type(frame) is Frame, 'frame')
    expected = request.candidate_scope_id
    if frame.board_revision_id != expected:
        _fail(Code.CONTEXT_MISMATCH, 'frame.board_revision_id', 'Candidate revision context differs.',
              expected, frame.board_revision_id)
    _require(frame.machine_id is None and frame.capture_id is None, 'frame.context',
             'Board-only candidate context required.', Code.CONTEXT_MISMATCH)
    _require(frame.unit is Unit.MM and frame.x_direction is AxisDirection.RIGHT and
             frame.y_direction is AxisDirection.UP, 'frame.conventions',
             'Only mm/right/up supported.', Code.GEOMETRY_UNSUPPORTED)
    kinds = (FrameKind.SOURCE, FrameKind.FOOTPRINT) if source else (FrameKind.PCB,)
    _require(frame.kind in kinds, 'frame.kind', 'Unsupported frame kind.', Code.GEOMETRY_UNSUPPORTED)


def _inventory(value):
    _require(type(value) is InventorySuccess, 'inventory')
    inv = value.inventory
    _require(type(inv) is ArtifactInventory and type(inv.manifest) is InventoryManifest,
             'inventory.records')
    _require(type(inv.artifacts) is tuple and type(inv.manifest.artifacts) is tuple,
             'inventory.artifacts')
    _id(inv.manifest.source_snapshot, 'inventory.source_snapshot')
    _id(inv.manifest.fixture_revision, 'inventory.fixture_revision')
    _require(type(value.report) is ValidationReport and value.report.status is ReportStatus.ACCEPTED
             and not value.report.errors, 'inventory.report', 'Successful inventory required.', Code.SOURCE_CONFLICT)
    _require(inv.manifest.schema_version == 'artifact-inventory-v1', 'inventory.schema_version')
    _require(dict(value.report.checks).get('scope') == 'artifact-bytes-only', 'inventory.report.scope')
    _require(len(inv.artifacts) == len(inv.manifest.artifacts), 'inventory.artifacts', code=Code.SOURCE_CONFLICT)
    declared = {}
    for d in inv.manifest.artifacts:
        _require(type(d) is ArtifactDeclaration, 'inventory.declaration')
        _id(d.artifact_id, 'inventory.artifact_id')
        _require(d.artifact_id not in declared, 'inventory.artifact_id', code=Code.DUPLICATE_ID)
        declared[d.artifact_id] = d
    result = {}
    for obs in inv.artifacts:
        _require(type(obs) is ArtifactObservation and type(obs.declaration) is ArtifactDeclaration,
                 'inventory.observation')
        d = obs.declaration
        _require(d.artifact_id not in result, 'inventory.observation.artifact_id', code=Code.DUPLICATE_ID)
        _require(declared.get(d.artifact_id) == d, 'inventory.declaration', code=Code.SOURCE_CONFLICT)
        _require(obs.eof is True and type(obs.actual_size) is int and obs.actual_size >= 0
                 and type(obs.bytes_read) is int and obs.actual_size == obs.bytes_read
                 and _digest(obs.computed_sha256) and type(d.declared_sha256) is str
                 and d.declared_sha256.lower() == obs.computed_sha256
                 and (d.declared_size is None or (type(d.declared_size) is int and d.declared_size == obs.actual_size)),
                 'inventory.bytes', 'Complete matching byte observations required.', Code.SOURCE_CONFLICT)
        _id(d.source_id, 'inventory.source_id')
        result[d.artifact_id] = obs
    return result


def _evidence(refs, artifacts):
    _require(type(refs) is tuple and bool(refs), 'evidence', 'Nonempty evidence references required.')
    for ref in refs:
        _require(type(ref) is EvidenceReference, 'evidence')
        _id(ref.artifact_id, 'evidence.artifact_id')
        _id(ref.locator, 'evidence.locator')
        obs = artifacts.get(ref.artifact_id)
        _require(obs is not None and ref.computed_sha256 == obs.computed_sha256,
                 'evidence.computed_sha256', 'Evidence artifact/hash mismatch.', Code.SOURCE_CONFLICT)


def _provenance(prov, artifact_id, entity, artifacts, manifest):
    _require(type(prov) is PadProvenance, 'provenance')
    for key in ('artifact_id', 'source_id', 'source_entity_id', 'source_snapshot',
                'fixture_revision', 'authoring_profile', 'version'):
        _id(getattr(prov, key), 'provenance.' + key)
    _require(_digest(prov.computed_sha256), 'provenance.computed_sha256')
    obs = artifacts.get(artifact_id)
    _require(obs is not None, 'provenance.artifact_id', 'Unknown artifact.', Code.SOURCE_CONFLICT)
    _require(not obs.declaration.reference_only and obs.declaration.role == 'kicad_pcb',
             'provenance.role', 'Primary geometric artifact required.', Code.SOURCE_CONFLICT)
    pairs = ((prov.artifact_id, artifact_id, 'artifact_id'),
             (prov.source_id, obs.declaration.source_id, 'source_id'),
             (prov.source_entity_id, entity, 'source_entity_id'),
             (prov.computed_sha256, obs.computed_sha256, 'computed_sha256'),
             (prov.source_snapshot, manifest.source_snapshot, 'source_snapshot'),
             (prov.fixture_revision, manifest.fixture_revision, 'fixture_revision'))
    for actual, expected, key in pairs:
        if actual != expected:
            _fail(Code.SOURCE_CONFLICT, 'provenance.' + key, 'Provenance mismatch.', expected, actual)
    _require(prov.source_location is None or type(prov.source_location) is SourceLocation, 'provenance.source_location')
    _evidence(prov.evidence, artifacts)


def _coordinate(x, p, path):
    value = finite_number(x, path)
    _require(abs(value) <= p.max_abs_coordinate_mm, path, 'Coordinate bound exceeded.', Code.INPUT_LIMIT_EXCEEDED)
    return value


def _record_context(request, record, parent=None):
    """Only after bounded preflight; retain declarations, not inferred metadata."""
    result = (('candidate_scope_id', request.candidate_scope_id),
              ('board_id', request.board_id), ('policy_id', request.policy.policy_id),
              ('policy_version', request.policy.version),
              ('source_entity_id', record.source_entity_id))
    result += frame_evidence('source', record.source_frame)
    result += frame_evidence('target', request.target_frame)
    if type(record) is SourcePad:
        result += (('parent_id', record.footprint_id),)
    if type(record.provenance) is PadProvenance:
        for name in ('computed_sha256', 'source_id', 'source_snapshot', 'fixture_revision'):
            value = getattr(record.provenance, name)
            if type(value) is str:
                result += ((name, value),)
    if type(parent) is PadParent and type(parent.source_to_p) is Transform2:
        result += (('transform_id', parent.source_to_p.transform_id),)
    return result


def _ordered(records, identity):
    # Only duplicate identities need a tie-breaker. Preflight already bounded
    # the complete record tree and its strings before this serialization.
    counts = Counter(getattr(r, identity) for r in records)
    return sorted(records, key=lambda r: (getattr(r, identity),
        diagnostic_json(asdict(r)) if counts[getattr(r, identity)] > 1 else ''))


def _parent_geometry(parent, request):
    _frame(parent.source_frame, request, True)
    _require(parent.side == 'top', 'parent.side', code=Code.GEOMETRY_UNSUPPORTED)
    _require((parent.coordinate_basis, parent.source_frame.kind) in (
        ('board-source', FrameKind.SOURCE), ('footprint-local', FrameKind.FOOTPRINT)), 'parent.coordinate_basis')
    transform = parent.source_to_p
    _require(transform is not None, 'parent.source_to_p', code=Code.TRANSFORM_MISSING)
    _require(type(transform) is Transform2, 'parent.source_to_p')
    require_same_frame(transform.from_frame, parent.source_frame, 'transform.from_frame')
    require_same_frame(transform.to_frame, request.target_frame, 'transform.to_frame')
    _require(transform.kind is TransformKind.RIGID, 'transform.kind',
             'Proper rigid transform required.', Code.GEOMETRY_UNSUPPORTED)
    transform._require_validated_conventions()
    transform._validate_isometry()  # Exact existing core guard; no relaxed tolerance.
    for row in transform.matrix[:2]:
        _coordinate(row[2], request.policy, 'transform.translation')


def _vertices(pad, parent, request):
    p = request.policy
    rect = pad.rectangle
    _require(type(rect) is PadRectangle, 'pad.rectangle', 'Only rectangles supported.', Code.GEOMETRY_UNSUPPORTED)
    _require(type(rect.center) is Point2, 'pad.rectangle.center')
    require_same_frame(rect.center.frame, pad.source_frame, 'pad.rectangle.center.frame')
    cx = _coordinate(rect.center.x, p, 'rectangle.center.x')
    cy = _coordinate(rect.center.y, p, 'rectangle.center.y')
    w, h = finite_number(rect.width, 'rectangle.width'), finite_number(rect.height, 'rectangle.height')
    _require(w > 0 and h > 0, 'rectangle.dimensions')
    _require(p.min_dimension_mm <= w <= p.max_dimension_mm and p.min_dimension_mm <= h <= p.max_dimension_mm,
             'rectangle.dimensions', 'Dimension bound exceeded.', Code.INPUT_LIMIT_EXCEEDED)
    angle = finite_number(rect.angle_deg, 'rectangle.angle_deg')
    _require(abs(angle) <= p.max_abs_angle_deg, 'rectangle.angle_deg', code=Code.INPUT_LIMIT_EXCEEDED)
    # Reduce only the trig argument, retain original declaration in result.
    a = radians(angle % 360.0)
    c, s = cos(a), sin(a)
    result = []
    for u, v in ((-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)):
        x, y = cx + u*c-v*s, cy+u*s+v*c
        _coordinate(x, p, 'rectangle.corner.x'); _coordinate(y, p, 'rectangle.corner.y')
        point = parent.source_to_p.apply(Point2(x, y, pad.source_frame))
        _coordinate(point.x, p, 'candidate.corner.x'); _coordinate(point.y, p, 'candidate.corner.y')
        result.append(point)
    # Work in local differences, NOT a shoelace sum of large absolute products.
    # Each consecutive cross must be positive: also rejects collapsed/folded output.
    for i in range(4):
        x, y, z = result[i], result[(i+1) % 4], result[(i+2) % 4]
        cross = (y.x-x.x)*(z.y-y.y) - (y.y-x.y)*(z.x-y.x)
        _require(isfinite(cross) and cross > 0, 'candidate.vertices', 'Degenerate transformed rectangle.')
    return tuple(result)


def build_rectangular_pad_candidates(request: PadCandidateRequest) -> PadBatchSuccess | PadBatchFailure:
    """Validate a bounded trusted in-process declaration; never parse or publish.

    Policy is required in request. Successful inventory is a trusted byte-admission
    result, not an authentication primitive. No input is mutated or normalized.
    """
    policy = request.policy if type(request) is PadCandidateRequest else None
    valid_policy = type(policy) is SyntheticPadPolicy
    if valid_policy:
        for f, expected in zip(fields(policy), _POLICY):
            actual = getattr(policy, f.name)
            if type(actual) is not type(expected) or actual != expected:
                valid_policy = False
                break
    if not valid_policy:
        error = ContractError(Code.POLICY_INVALID, 'Exact synthetic policy v1 required.',
                              'policy', 'Supply all selected policy values explicitly.')
        return PadBatchFailure(ValidationReport('canonical-pad-candidate', 'invalid-policy',
            (error,), (('scope', 'canonical-pad-candidate-only'),)), PadTruncation(False))
    sink = _Issues(policy)
    candidates = []
    try:
        _preflight(request, sink)
        _id(request.board_id, 'board_id'); _id(request.candidate_scope_id, 'candidate_scope_id')
        sink.context = (('candidate_scope_id', request.candidate_scope_id),
                        ('board_id', request.board_id), ('policy_id', policy.policy_id),
                        ('policy_version', policy.version)) + frame_evidence('target', request.target_frame)
        _require(request.schema_version == 'rect-pad-candidate-v1', 'schema_version')
        _require(type(request.parents) is tuple and bool(request.parents), 'parents', 'Nonempty immutable batch required.')
        _require(type(request.pads) is tuple and bool(request.pads), 'pads', 'Nonempty immutable batch required.')
        _frame(request.target_frame, request)
        artifacts = _inventory(request.inventory)
        manifest = request.inventory.inventory.manifest
        parents = {}
        valid_parents = set()
        parent_sources = {}
        # Validate identities before sorting; malformed records use original index.
        for i, parent in enumerate(request.parents):
            _require(type(parent) is PadParent, f'parents[{i}]')
            for key in ('footprint_id', 'artifact_id', 'source_entity_id'):
                _id(getattr(parent, key), f'parents[{i}].{key}')
        for i, pad in enumerate(request.pads):
            _require(type(pad) is SourcePad, f'pads[{i}]')
            for key in ('pad_id', 'footprint_id', 'artifact_id', 'source_entity_id', 'source_parent_entity_id'):
                _id(getattr(pad, key), f'pads[{i}].{key}')
        for parent in _ordered(request.parents, 'footprint_id'):
            sink.entity, sink.artifact = parent.footprint_id, parent.artifact_id
            sink.context = _record_context(request, parent, parent)
            sink.location = (parent.provenance.source_location if type(parent.provenance) is PadProvenance
                             and type(parent.provenance.source_location) is SourceLocation else None)
            start = len(sink.issues)
            if parent.footprint_id in parents:
                sink.add(GeometryError(Code.DUPLICATE_ID, 'Duplicate parent ID.', field_path='parent.footprint_id'))
                valid_parents.discard(parent.footprint_id)
                continue
            parents[parent.footprint_id] = parent
            key = (parent.artifact_id, parent.source_entity_id)
            if key in parent_sources:
                sink.add(GeometryError(Code.SOURCE_CONFLICT, 'Typed parent source alias.', field_path='parent.source_entity_id',
                                       expected=parent_sources[key], actual=parent.footprint_id))
            parent_sources[key] = parent.footprint_id
            sink.check(lambda: _provenance(parent.provenance, parent.artifact_id, parent.source_entity_id, artifacts, manifest))
            sink.check(lambda: _evidence(parent.convention_evidence, artifacts))
            sink.check(lambda: _parent_geometry(parent, request))
            if len(sink.issues) == start:
                valid_parents.add(parent.footprint_id)
        pad_ids = set()
        pad_sources = {}
        for pad in _ordered(request.pads, 'pad_id'):
            sink.entity, sink.artifact = pad.pad_id, pad.artifact_id
            sink.location = (pad.provenance.source_location if type(pad.provenance) is PadProvenance
                             and type(pad.provenance.source_location) is SourceLocation else None)
            sink.context = _record_context(request, pad, parents.get(pad.footprint_id))
            start = len(sink.issues)
            if pad.pad_id in pad_ids:
                sink.add(GeometryError(Code.DUPLICATE_ID, 'Duplicate pad ID.', field_path='pad.pad_id'))
                continue
            pad_ids.add(pad.pad_id)
            key = (pad.artifact_id, pad.source_entity_id)
            if key in pad_sources:
                sink.add(GeometryError(Code.SOURCE_CONFLICT, 'Typed pad source alias.', field_path='pad.source_entity_id',
                                       expected=pad_sources[key], actual=pad.pad_id))
            pad_sources[key] = pad.pad_id
            sink.check(lambda: _provenance(pad.provenance, pad.artifact_id, pad.source_entity_id, artifacts, manifest))
            sink.check(lambda: _frame(pad.source_frame, request, True))
            sink.check(lambda: _require(type(pad.pad_number) is str and (pad.net is None or type(pad.net) is str), 'pad.number_or_net'))
            sink.check(lambda: _require(pad.side == 'top' and pad.copper_layers == ('F.Cu',) and
                pad.pad_type == 'smd' and pad.drill is None, 'pad.subset', 'Only top SMD/F.Cu without drill.', Code.GEOMETRY_UNSUPPORTED))
            parent = parents.get(pad.footprint_id)
            if parent is None:
                sink.add(GeometryError(Code.SCHEMA_INVALID, 'Unknown parent.', field_path='pad.footprint_id', actual=pad.footprint_id))
                continue
            sink.check(lambda: _require(pad.artifact_id == parent.artifact_id and
                pad.source_parent_entity_id == parent.source_entity_id, 'pad.source_parent_entity_id',
                'Source parent declaration conflicts.', Code.SOURCE_CONFLICT))
            if type(pad.source_frame) is Frame and type(parent.source_frame) is Frame:
                sink.check(lambda: require_same_frame(pad.source_frame, parent.source_frame, 'pad.source_frame'))
            if pad.footprint_id not in valid_parents or len(sink.issues) != start:
                continue
            try:
                vertices = _vertices(pad, parent, request)
                candidates.append(CanonicalPadCandidate(request.board_id, request.candidate_scope_id,
                    request.schema_version, policy, pad, parent, vertices))
            except GeometryError as error:
                sink.add(error)
    except GeometryError as error:
        try:
            sink.add(error)
        except _Stop:
            pass
    except _Stop:
        pass
    return sink.finish(candidates)
