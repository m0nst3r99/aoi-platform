"""Portable replay only; independent corner oracle, no native imports."""
from dataclasses import replace
from pathlib import Path
from io import BytesIO
from hashlib import sha256
import json
import runpy
import pytest

bridge = runpy.run_path(str(Path(__file__).with_name('repeated_pads_bridge.py')))
replay = bridge['replay_repeated_pads']
Success = bridge['ReplaySuccess']
from aoi_platform.inventory import ArtifactDeclaration, InventoryManifest, InventoryLimits, inventory_artifacts
from aoi_platform.pad_candidates import SyntheticPadPolicy, PadBatchFailure
from aoi_platform.geometry.models import Frame, FrameKind, Unit, AxisDirection as Axis

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT/'evaluation/windows_runner/evidence/repeated-pads-01'
PCB = (FIXTURE/'repeated-pads.kicad_pcb').read_bytes()
RAW = (FIXTURE/'stdout.bin').read_bytes()
POLICY = SyntheticPadPolicy('synthetic-rect-pad-candidate','1',4096,4096,1024,256,1024,
    16,32768,8388608,128,4096,524288,1000000.,.000001,1000000.,360000.,1e-12,0.,1e-6)


def arguments(raw=RAW, pcb=PCB):
    declarations = (ArtifactDeclaration('pcb','kicad_pcb','pcb-source',sha256(pcb).hexdigest()),
        ArtifactDeclaration('observation','supporting','observation-source',sha256(raw).hexdigest(),reference_only=True))
    inv = inventory_artifacts(InventoryManifest('geometry',declarations,'repeated-pads-01','accepted-snapshot'),
        {'pcb-source':lambda:BytesIO(pcb),'observation-source':lambda:BytesIO(raw)},
        InventoryLimits('replay-test',2,65536,131072,4096))
    return dict(pcb_bytes=pcb,raw=raw,inventory=inv,pcb_artifact_id='pcb',observation_artifact_id='observation',
        board_id='synthetic-board',scope_id='unpublished-scope',parent_id='parent',
        pad_ids=((bridge['PADS'][0],'pad-a'),(bridge['PADS'][1],'pad-b')),
        native_frame=Frame('native',FrameKind.SOURCE,Unit.MM,'declared-datum',Axis.RIGHT,Axis.DOWN,'unpublished-scope'),
        normalized_frame=Frame('normalized',FrameKind.SOURCE,Unit.MM,'declared-datum',Axis.RIGHT,Axis.UP,'unpublished-scope'),
        target_frame=Frame('P',FrameKind.PCB,Unit.MM,'declared-datum',Axis.RIGHT,Axis.UP,'unpublished-scope'),
        normalization='N(x,y)=(x,-y)',translation_mm=(0,20),policy=POLICY,
        max_pcb_bytes=65536,max_observation_bytes=65536)


def rejected(result,code):
    assert isinstance(result,PadBatchFailure)
    assert not hasattr(result,'candidates') and not hasattr(result,'batch')
    assert code in [i.code.value for i in result.report.errors]


def test_accepted_raw_replay_independent_oracle_nonmutation():
    args=arguments(); before=repr(args)
    result=replay(**args)
    assert isinstance(result,Success),result
    expected=[[(10,7.5),(12,7.5),(12,8.5),(10,8.5)],
              [(13,6.5),(15,6.5),(15,7.5),(13,7.5)]]
    for c,vertices in zip(result.batch.candidates,expected):
        assert c.source.pad_number=='1' and c.source.footprint_id=='parent'
        assert c.association_status=='declaration-consistent'
        assert not c.published and not c.targeting_authorized
        for p,xy in zip(c.vertices,vertices): assert (p.x,p.y)==pytest.approx(xy,abs=1e-6,rel=0)
        assert c.source.provenance.computed_sha256==sha256(PCB).hexdigest()
        assert c.source.provenance.evidence[1].computed_sha256==sha256(RAW).hexdigest()
        assert c.parent.source_to_p.matrix==((1.,0.,0.),(0.,1.,20.),(0.,0.,1.))
    assert [c.pad_id for c in result.batch.candidates]==['pad-a','pad-b']
    assert result.normalization.formula=='N(x,y)=(x,-y)'
    assert all(layers==('F.Cu','F.Mask','F.Paste') for _,layers in result.normalization.raw_layers)
    assert repr(args)==before and args['raw']==RAW


@pytest.mark.parametrize('field',['raw','pcb_bytes'])
def test_content_hash_mismatch(field):
    a=arguments();a[field]+=b' '
    rejected(replay(**a),'SOURCE_CONFLICT')


@pytest.mark.parametrize('case,code',[
    ('json','SCHEMA_INVALID'),('schema','SCHEMA_INVALID'),('legacy','SCHEMA_INVALID'),
    ('build','FORMAT_UNSUPPORTED'),('input-hash','SOURCE_CONFLICT'),('shape','GEOMETRY_UNSUPPORTED'),
    ('bottom','GEOMETRY_UNSUPPORTED'),('angle','GEOMETRY_UNSUPPORTED'),('outline','OUTLINE_INVALID'),
    ('dimension','SCHEMA_INVALID')])
def test_admitted_negative_observations(case,code):
    data=json.loads(RAW)
    if case=='schema': del data['footprints'][0]['pads'][0]['size_mm']
    if case=='legacy': del data['protocol_version']
    if case=='build': data['build']='other'
    if case=='input-hash': data['input_sha256']='0'*64
    if case=='shape': data['footprints'][0]['pads'][1]['shape']=2
    if case=='bottom': data['footprints'][0]['layer']='B.Cu'
    if case=='angle': data['footprints'][0]['pads'][1]['angle_deg']=90
    if case=='outline': data['outline']['valid']=False
    if case=='dimension': data['footprints'][0]['pads'][1]['size_mm']=[0,1]
    raw=b'{' if case=='json' else json.dumps(data).encode()
    a=arguments(raw); before=raw
    rejected(replay(**a),code)
    assert a['raw']==before


@pytest.mark.parametrize('field,value,code',[
    ('normalization',None,'SCHEMA_INVALID'),('translation_mm',(0,0),'SCHEMA_INVALID'),
    ('pad_ids',(),'SCHEMA_INVALID'),('parent_id','','SCHEMA_INVALID'),
    ('max_observation_bytes',True,'POLICY_INVALID'),('max_observation_bytes',1,'INPUT_LIMIT_EXCEEDED'),
    ('scope_id','other','CONTEXT_MISMATCH')])
def test_missing_or_wrong_declarations(field,value,code):
    a=arguments();a[field]=value
    rejected(replay(**a),code)


def test_exact_byte_boundaries_and_duplicate_canonical_ids():
    a=arguments();a.update(max_pcb_bytes=len(PCB),max_observation_bytes=len(RAW))
    assert isinstance(replay(**a),Success)
    a['pad_ids']=tuple((uid,'same') for uid in bridge['PADS'])
    rejected(replay(**a),'DUPLICATE_ID')
