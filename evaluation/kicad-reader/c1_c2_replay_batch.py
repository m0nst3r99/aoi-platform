"""Pinned C2 replay only. Strict-v2 only; no native execution, legacy opt-in or publication."""
from dataclasses import dataclass, replace
from io import BytesIO
from pathlib import Path
import json
from aoi_platform.inventory import ArtifactDeclaration, InventoryManifest, InventoryLimits, InventorySuccess, inventory_artifacts
from aoi_platform.geometry.models import Frame, FrameKind, Unit, AxisDirection as Axis, Point2
from aoi_platform.pad_candidates import (SyntheticPadPolicy, EvidenceReference, PadProvenance, PadParent, SourcePad, PadRectangle, PadCandidateRequest, PadBatchSuccess, CanonicalPadCandidate, build_rectangular_pad_candidates)
from aoi_platform.geometry.transforms import Transform2, TransformKind
import c1_boundary_compare as boundary_c1
import c2_boundary_compare as boundary_c2
from outline_decision import evaluate_outline

PROFILE_ID = 'c1-c2-pinned-replay-v1'
GROUPS = (('C1', boundary_c1), ('C2', boundary_c2))
PINS = (('pcb', '67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0', 912379), ('observation', 'cd3734ece758d2611b44dc89cec2c88e439ba2d5585024d484671645ed7725b9', 196944), ('C1_boundary', '9cd1d26d7756d81fc91d81712be01cba295a742ece11f9847c83866b897748b2', 1689), ('C1_report', 'ae359be006e70c9b6d97b87d80b250d365b27b8196b3d230d1d21954f90852cc', 813), ('C1_transport', '003d26bee58ac17377275ca8e5c74d5dc4c9a57038b35f0e0a282f047537da07', 1354), ('C2_boundary', 'a8134211861f9f2709330e6d8e4c8185662e3d58f153895dbf5811270329b176', 1689), ('C2_report', '098fc91d66b941f1c02fbeb4177816026837c40ed014a69bd9872ecbaa57d7ae', 813), ('C2_transport', '3a1381fa096b973de18f9fc9c96130775da0da8771d03803a516ee4f0c5b8d2e', 1355))
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
        raise _Blocked('Required C1+C2 batch condition not satisfied')

def replay_batch(paths):
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
        InventoryLimits(PROFILE_ID,8,2*1024**2,4*1024**2,65536))
    if not isinstance(inventory, InventorySuccess):
        return ReplayFailure('inventory', 'BYTE_ADMISSION_FAILED', inventory.report.to_json() if hasattr(inventory.report,'to_json') else str(inventory.report))
    return _evaluate_admitted(raw, inventory)

def _evaluate_admitted(raw, inventory):
    """Private gates; mutated raw with admitted inventory is only a test double."""
    gate = 'observation-schema'
    try:
        decision = evaluate_outline(raw['observation'])
        if decision.status == 'rejected':
            return ReplayFailure(gate, decision.diagnostics[0].code, str(decision.diagnostics))
        observation = json.loads(raw['observation'])
        admitted = {a.declaration.artifact_id:a.computed_sha256 for a in inventory.inventory.artifacts}
        gate = 'observation-binding'
        _require(observation['build']=='10.0.7' and observation['input_sha256']==admitted['pcb']==PINS[0][1])
        s = Frame('normalized',FrameKind.SOURCE,Unit.MM,'native-board',Axis.RIGHT,Axis.UP,'c1-c2-unpublished')
        target = Frame('P',FrameKind.PCB,Unit.MM,'native-board',Axis.RIGHT,Axis.UP,'c1-c2-unpublished')
        transform = Transform2('declared-zero-translation',s,target,((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID)
        parents=[]; pads=[]; checks={}; correspondence={}
        for group, comparator in GROUPS:
            gate = group + ':transport'
            transport = json.loads(raw[group+'_transport'])
            report = json.loads(raw[group+'_report'])
            ev = transport['result']['evidence']
            _require(transport['success'] is True and type(ev['root_exit']) is int and ev['root_exit']==0)
            _require(ev['cleanup_state']=='cleaned' and type(ev['active_processes']) is int and ev['active_processes']==0)
            _require(all(ev[k] is True for k in ('stdout_eof','stderr_eof','limits_verified')))
            _require(all(transport[k] is True for k in ('caller_handle_usable','stage_unchanged','helper_temp_empty')))
            _require(all(report[k] is True for k in ('transport','cleanup','staging_removed','inputs_unchanged','fixture_unchanged')))
            gate = group + ':binding'
            _require(report['output_hashes']['stdout.bin']==admitted[group+'_boundary'])
            boundary=json.loads(raw[group+'_boundary'])
            _require(boundary['input_sha256']==admitted['pcb'])
            gate = group + ':boundary'
            comparison=comparator.compare(boundary)
            _require(comparison['passed'] is True)
            gate = group + ':observation'
            selected=[f for f in observation['footprints'] if f['uuid']==comparator.PARENT]
            _require(len(selected)==1)
            f=selected[0]
            _require(f['layer']=='F.Cu' and len(f['pads'])==2 and {p['uuid'] for p in f['pads']}==comparator.PADS)
            keys=('pcb','observation',group+'_boundary',group+'_report',group+'_transport')
            refs=tuple(EvidenceReference(k,admitted[k],'Pinned '+group+'; N(x,y)=(x,-y); native-board datum; P translation (0,0); correspondence (3,2,1,0)') for k in keys)
            prov=PadProvenance('pcb','pcb',admitted['pcb'],comparator.PARENT,'accepted-snapshot','REAL-PCB-01-r2',PROFILE_ID,'1',refs)
            parents.append(PadParent(group,comparator.PARENT,'pcb',s,'board-source','top',transform,refs,prov))
            by_id={p['uuid']:p for p in boundary['pads']}
            for p in f['pads']:
                _require(p['shape']==1 and p['attribute']==1 and p['drill_mm']==[0,0] and set(p['layers'])=={'F.Cu','F.Mask','F.Paste'})
                x,y=p['position_mm']
                pads.append(SourcePad(p['uuid'],group,p['uuid'],comparator.PARENT,'pcb',s,p['number'],'top',('F.Cu',),'smd',None,PadRectangle(Point2(x,-y,s),*p['size_mm'],p['angle_deg']),replace(prov,source_entity_id=p['uuid'])))
                checks[p['uuid']]=(group,comparator.EXPECTED[p['uuid']],by_id[p['uuid']]['contours'][0]['vertices_iu'],comparison['oracle_to_raw_indices'][p['uuid']])
            correspondence.update(comparison['oracle_to_raw_indices'])
        gate='candidate'
        result=build_rectangular_pad_candidates(PadCandidateRequest('rect-pad-candidate-v1',POLICY,'C1-C2-board','c1-c2-unpublished',target,inventory,tuple(parents),tuple(pads)))
        _require(isinstance(result,PadBatchSuccess))
        _require(len(result.candidates)==4 and {c.pad_id for c in result.candidates}==set(checks))
        for c in result.candidates:
            group,expected,vertices,indices=checks[c.pad_id]
            gate=group+':candidate-boundary'
            for i,j in enumerate((3,2,1,0)):
                v=c.vertices[j]
                for point in (expected[i],vertices[indices[i]]):
                    _require(abs(v.x-point[0]/1e6)<=1e-6 and abs(v.y+point[1]/1e6)<=1e-6)
        return ReplaySuccess(result.candidates,inventory,tuple((k,tuple(v)) for k,v in sorted(correspondence.items())))
    except (_Blocked, KeyError, TypeError, ValueError, IndexError) as error:
        return ReplayFailure(gate,'C1_C2_BATCH_REJECTED',str(error))
