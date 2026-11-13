"""Fake execution only; synthetic v2 payload is not a new native observation."""
import json
import os
from pathlib import Path
import sys
from hashlib import sha256
from dataclasses import replace
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'evaluation/windows_runner'))
from models import ExecutionSuccess, ExecutionFailure, Evidence, Issue, Code
import c1_strict_control as control
from c1_replay_flow import ReplayFailure

@pytest.fixture
def paths():
    configured=os.environ.get('AOI_C1_R2_PCB')
    assert configured,'Real PCB required; no fallback'
    ev=ROOT/'evaluation/windows_runner/evidence/c1-boundary-native-01'
    return dict(pcb=Path(configured),boundary=ev/'stdout.bin',report=ev/'report.json',transport=ev/'transport.json')

@pytest.fixture
def fake_v2():
    # Test-only synthetic v2 model seeded by saved values. Never relabel persisted
    # legacy bytes, never claim this came from KiCad or use it as native evidence.
    data=json.loads((ROOT/'evaluation/kicad-reader/runs/errata-r2-01/pcbnew.stdout.txt').read_bytes())
    data.update(protocol_version=2,footprint_edges=[],geometry_coverage=dict(board_edges_scope='board-drawings-only',footprint_edges_scope='footprint-graphical-items-only',geometry_complete=False))
    return data

def success(raw):
    return ExecutionSuccess(raw,b'fake stderr',Evidence(123,0,0,True,True,'cleaned',1,len(raw),11,True,True,'REAL-PCB-01-r2-pcb','owned-stage','kicad-local-test-v1'))

def reject(result):
    assert isinstance(result,ReplayFailure),result
    assert not hasattr(result,'candidates') and not hasattr(result,'replay')

@pytest.mark.parametrize('indent',[None,2])
def test_exact_new_stdout_and_separate_transport(paths,fake_v2,tmp_path,monkeypatch,indent):
    raw=json.dumps(fake_v2,indent=indent).encode()+b'\n '
    captured=[];observed=[]
    original=control._evaluate_admitted
    def spy(data,inventory,**kwargs):
        observed.append(data['observation'])
        assert kwargs=={'strict_v2':True}
        assert json.loads(data['transport'])['result']['evidence']['root_pid']!=123
        return original(data,inventory,**kwargs)
    monkeypatch.setattr(control,'_evaluate_admitted',spy)
    def execute(stage,temp):
        assert stage.read_bytes()==paths['pcb'].read_bytes()
        assert stage!=paths['pcb'] and not any(temp.iterdir())
        captured.append(stage.parent)
        return success(raw)
    result=control.run_control(paths,execute=execute,staging_root=tmp_path)
    assert isinstance(result,control.ControlSuccess),result
    assert observed==[raw] and observed[0] is raw
    assert result.observation_transport.stdout is raw
    assert result.observation_sha256==sha256(raw).hexdigest()
    assert result.staging_removed and all(not p.exists() for p in captured)
    assert len(result.replay.candidates)==2
    for candidate in result.replay.candidates:
        refs={r.artifact_id:r.computed_sha256 for r in candidate.source.provenance.evidence}
        assert refs['observation']==sha256(raw).hexdigest()
        assert refs['boundary']==dict((k,h) for k,h,n in control.PINS)['boundary']
        assert not candidate.published and not candidate.targeting_authorized

@pytest.mark.parametrize('case',['timeout','failure','cleanup','active','exit','eof','temp','stage','count','overflow'])
def test_execution_failure_no_observation_decision(paths,fake_v2,tmp_path,monkeypatch,case):
    def forbidden(*args,**kwargs):pytest.fail('Execution failure reached observation gates')
    monkeypatch.setattr(control,'_evaluate_admitted',forbidden)
    def execute(stage,temp):
        transport=success(json.dumps(fake_v2).encode())
        if case=='timeout':raise TimeoutError()
        if case=='failure':return ExecutionFailure((Issue(Code.TIMEOUT,'fake'),),transport.stdout,b'',transport.evidence)
        if case=='cleanup':return replace(transport,evidence=replace(transport.evidence,cleanup_state='unknown'))
        if case=='active':return replace(transport,evidence=replace(transport.evidence,active_processes=1))
        if case=='exit':return replace(transport,evidence=replace(transport.evidence,root_exit=1))
        if case=='eof':return replace(transport,evidence=replace(transport.evidence,stdout_eof=False))
        if case=='temp':(temp/'leftover').write_bytes(b'x')
        if case=='stage':stage.write_bytes(b'changed')
        if case=='count':return replace(transport,evidence=replace(transport.evidence,observed_stdout=1))
        if case=='overflow':return success(b'x'*(2*1024**2+1))
        return transport
    reject(control.run_control(paths,execute=execute,staging_root=tmp_path))
    assert list(tmp_path.iterdir())==[]

@pytest.mark.parametrize('case',['legacy','malformed-v2','json','source','build','boundary-corners'])
def test_fake_output_rejection(paths,fake_v2,tmp_path,case):
    if case=='legacy':fake_v2.pop('protocol_version');fake_v2.pop('footprint_edges');fake_v2.pop('geometry_coverage')
    elif case=='malformed-v2':fake_v2.pop('geometry_coverage')
    elif case=='source':fake_v2['input_sha256']='0'*64
    elif case=='build':fake_v2['build']='wrong'
    elif case=='boundary-corners':
        f=next(f for f in fake_v2['footprints'] if f['reference']=='C1')
        f['pads'][0]['position_mm'][0]+=1
    raw=b'{' if case=='json' else json.dumps(fake_v2).encode()
    result=control.run_control(paths,execute=lambda *_:success(raw),staging_root=tmp_path)
    reject(result)
    if case in ('legacy','malformed-v2'):assert result.code=='SCHEMA_INVALID'

@pytest.mark.parametrize('key',['pcb','boundary','report','transport'])
def test_pinned_inputs_reject_before_execution(paths,tmp_path,key):
    data=bytearray(paths[key].read_bytes());data[0]^=1
    bad=tmp_path/'bad';bad.write_bytes(data);paths[key]=bad
    def forbidden(*args):pytest.fail('Bad pin launched execution')
    result=control.run_control(paths,execute=forbidden,staging_root=tmp_path)
    reject(result);assert result.gate=='inventory'


@pytest.mark.parametrize('field',['artifact_id','source_id','policy_id'])
def test_current_execution_identity_mismatch_blocks_observation(paths,fake_v2,tmp_path,monkeypatch,field):
    transport=success(json.dumps(fake_v2).encode())
    wrong=replace(transport,evidence=replace(transport.evidence,**{field:'wrong-identity'}))
    def forbidden(*args,**kwargs):
        pytest.fail('Identity mismatch reached _evaluate_admitted')
    monkeypatch.setattr(control,'_evaluate_admitted',forbidden)
    result=control.run_control(paths,execute=lambda *_:wrong,staging_root=tmp_path)
    reject(result)
    assert result.gate=='observation-identity'
    assert result.code=='EXECUTION_IDENTITY_MISMATCH'
    assert field in result.detail and 'wrong-identity' in result.detail
    assert list(tmp_path.iterdir())==[]
