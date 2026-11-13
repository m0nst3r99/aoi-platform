"""Pinned C1 replay only. No native execution, legacy upgrade or publication."""
from dataclasses import dataclass, replace
from io import BytesIO
from pathlib import Path
import json
from aoi_platform.inventory import ArtifactDeclaration, InventoryManifest, InventoryLimits, InventorySuccess, inventory_artifacts
from aoi_platform.geometry.models import Frame, FrameKind, Unit, AxisDirection as Axis, Point2
from aoi_platform.pad_candidates import (SyntheticPadPolicy, EvidenceReference, PadProvenance, PadParent, SourcePad, PadRectangle, PadCandidateRequest, PadBatchSuccess, CanonicalPadCandidate, build_rectangular_pad_candidates)
from aoi_platform.geometry.transforms import Transform2, TransformKind
from c1_boundary_compare import compare, EXPECTED
from c1_boundary_probe import SOURCE_HASH, PARENT, PADS

PINS = (
 ('pcb','67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0',912379),
 ('observation','10f57cac75d8d998e450cf91d2aaf748e289fd512f1c1568b5ca9298a9494b9c',196715),
 ('boundary','9cd1d26d7756d81fc91d81712be01cba295a742ece11f9847c83866b897748b2',1689),
 ('report','ae359be006e70c9b6d97b87d80b250d365b27b8196b3d230d1d21954f90852cc',813),
 ('transport','003d26bee58ac17377275ca8e5c74d5dc4c9a57038b35f0e0a282f047537da07',1354),
)
POLICY = SyntheticPadPolicy('synthetic-rect-pad-candidate','1',4096,4096,1024,256,1024,16,32768,8388608,128,4096,524288,1000000.,.000001,1000000.,360000.,1e-12,0.,1e-6)

@dataclass(frozen=True)
class ReplaySuccess:
    candidates: tuple[CanonicalPadCandidate, ...]
    inventory: InventorySuccess
    correspondence: tuple

@dataclass(frozen=True)
class ReplayFailure:
    gate: str
    code: str
    detail: str

class _Blocked(Exception):
    pass

def _require(condition):
    if not condition:
        raise _Blocked('Required C1 replay condition not satisfied')

def replay_c1(paths):
    """Explicit local paths only; fixed sizes bound capture before byte admission.

    Inventory hashes the same captured immutable bytes subsequently parsed.
    Pin failures cannot be bypassed via caller-supplied hashes or policy.
    """
    raw = {}
    try:
        _require(set(paths) == {k for k, _, _ in PINS})
        for key, _, size in PINS:
            path = Path(paths[key])
            _require(path.is_absolute())
            with path.open('rb') as stream:
                raw[key] = stream.read(size + 1)
            _require(len(raw[key]) == size)
    except (OSError, ValueError, TypeError, _Blocked) as error:
        return ReplayFailure('input', 'SOURCE_INVALID', str(error))
    declarations = tuple(ArtifactDeclaration(k, 'kicad_pcb' if k == 'pcb' else 'supporting', k, h, n, reference_only=k != 'pcb') for k,h,n in PINS)
    inventory = inventory_artifacts(
        InventoryManifest('geometry', declarations, 'REAL-PCB-01-r2', 'accepted-snapshot'),
        {k: (lambda data=data: BytesIO(data)) for k,data in raw.items()},
        InventoryLimits('c1-bound-replay-v1',5,2*1024**2,4*1024**2,65536))
    if not isinstance(inventory, InventorySuccess):
        return ReplayFailure('inventory', 'BYTE_ADMISSION_FAILED', inventory.report.to_json() if hasattr(inventory.report,'to_json') else str(inventory.report))
    return _evaluate_admitted(raw, inventory)

def _evaluate_admitted(raw, inventory, *, strict_v2=False):
    """Private post-admission gates; direct calls in tests are explicitly doubles."""
    gate = 'transport'
    try:
        transport = json.loads(raw['transport'])
        report = json.loads(raw['report'])
        ev = transport['result']['evidence']
        _require(transport['success'] is True and type(ev['root_exit']) is int and ev['root_exit'] == 0)
        _require(ev['cleanup_state'] == 'cleaned' and type(ev['active_processes']) is int and ev['active_processes'] == 0)
        _require(all(ev[k] is True for k in ('stdout_eof','stderr_eof','limits_verified')))
        _require(all(transport[k] is True for k in ('caller_handle_usable','stage_unchanged','helper_temp_empty')))
        _require(all(report[k] is True for k in ('transport','cleanup','staging_removed','inputs_unchanged','fixture_unchanged')))
        admitted = {a.declaration.artifact_id:a.computed_sha256 for a in inventory.inventory.artifacts}
        gate = 'binding'
        _require(report['output_hashes']['stdout.bin'] == admitted['boundary'])
        observation = json.loads(raw['observation'])
        boundary = json.loads(raw['boundary'])
        _require(observation['input_sha256'] == boundary['input_sha256'] == admitted['pcb'] == SOURCE_HASH)
        _require(observation['build'] == '10.0.7')
        if strict_v2:
            from outline_decision import evaluate_outline
            decision = evaluate_outline(raw['observation'])
            if decision.status == 'rejected':
                return ReplayFailure('observation-schema', decision.diagnostics[0].code, str(decision.diagnostics))
        else:
            _require('protocol_version' not in observation)
        gate = 'boundary'
        comparison = compare(boundary)
        _require(comparison['passed'] is True)
        gate = 'observation'
        parents = [f for f in observation['footprints'] if f['uuid'] == PARENT]
        _require(len(parents) == 1)
        f = parents[0]
        _require(f['layer'] == 'F.Cu' and len(f['pads']) == 2 and {p['uuid'] for p in f['pads']} == PADS)
        s = Frame('normalized',FrameKind.SOURCE,Unit.MM,'declared-C1-datum',Axis.RIGHT,Axis.UP,'c1-unpublished')
        target = Frame('P',FrameKind.PCB,Unit.MM,'declared-C1-datum',Axis.RIGHT,Axis.UP,'c1-unpublished')
        transform = Transform2('declared-zero-translation',s,target,((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID)
        refs = tuple(EvidenceReference(k, admitted[k], 'Pinned C1 replay; N(x,y)=(x,-y); P same datum; translation (0,0); correspondence (3,2,1,0)') for k,_,_ in PINS)
        prov = PadProvenance('pcb','pcb',admitted['pcb'],PARENT,'accepted-snapshot','REAL-PCB-01-r2','C1-boundary-replay','1',refs)
        parent = PadParent('C1',PARENT,'pcb',s,'board-source','top',transform,refs,prov)
        pads = []
        for p in f['pads']:
            _require(p['shape']==1 and p['attribute']==1 and p['drill_mm']==[0,0] and set(p['layers'])=={'F.Cu','F.Mask','F.Paste'})
            x,y = p['position_mm']
            pads.append(SourcePad(p['uuid'],'C1',p['uuid'],PARENT,'pcb',s,p['number'],'top',('F.Cu',),'smd',None,PadRectangle(Point2(x,-y,s),*p['size_mm'],p['angle_deg']),replace(prov,source_entity_id=p['uuid'])))
        gate = 'candidate'
        result = build_rectangular_pad_candidates(PadCandidateRequest('rect-pad-candidate-v1',POLICY,'C1-board','c1-unpublished',target,inventory,(parent,),tuple(pads)))
        _require(isinstance(result,PadBatchSuccess))
        gate = 'candidate-boundary'
        _require(len(result.candidates)==2 and {c.pad_id for c in result.candidates}==PADS)
        by_id = {p['uuid']:p for p in boundary['pads']}
        for c in result.candidates:
            vertices = by_id[c.pad_id]['contours'][0]['vertices_iu']
            indices = comparison['oracle_to_raw_indices'][c.pad_id]
            for i,j in enumerate((3,2,1,0)):
                v = c.vertices[j]
                for expected in (EXPECTED[c.pad_id][i], vertices[indices[i]]):
                    _require(abs(v.x-expected[0]/1e6)<=1e-6 and abs(v.y+expected[1]/1e6)<=1e-6)
        return ReplaySuccess(result.candidates,inventory,tuple((k,tuple(v)) for k,v in sorted(comparison['oracle_to_raw_indices'].items())))
    except (_Blocked, KeyError, TypeError, ValueError, IndexError) as error:
        return ReplayFailure(gate, 'C1_REPLAY_REJECTED', str(error))
