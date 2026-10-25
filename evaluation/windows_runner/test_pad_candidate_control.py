"""Portable orchestration tests; execute is fake, never loads runner/pcbnew."""
from dataclasses import replace
from pathlib import Path
from hashlib import sha256
import json
import runpy
import pytest

import pad_candidate_control as control
from models import Code, Evidence, ExecutionSuccess, ExecutionFailure, Issue

READER = Path(__file__).resolve().parents[1]/'kicad-reader'
fixtures = runpy.run_path(str(READER/'test_repeated_pads_bridge.py'))
PCB, RAW = fixtures['PCB'], fixtures['RAW']


def declarations():
    a = fixtures['arguments']()
    return {k:a[k] for k in ('board_id','scope_id','parent_id','pad_ids','native_frame',
        'normalized_frame','target_frame','normalization','translation_mm','policy')}


def success(raw=RAW):
    return ExecutionSuccess(raw,b'',Evidence(123,0,0,True,True,'cleaned',10,len(raw),0,True,True,
        'synthetic-repeated-pads-v1','owned-stage','kicad-local-test-v1'))


def no_bridge(monkeypatch):
    def forbidden(*args,**kwargs): raise AssertionError('bridge called before required gates')
    monkeypatch.setitem(control.BRIDGE,'replay_repeated_pads',forbidden)


def assert_failure(result,code):
    assert isinstance(result,control.ControlFailure)
    assert result.code==code
    assert not hasattr(result,'replay') and not hasattr(result,'candidates')


def test_forwards_execution_bytes_after_owner_cleanup(monkeypatch,tmp_path):
    raw=json.dumps(json.loads(RAW),separators=(',',':')).encode()+b'\n\n'
    assert raw!=RAW
    paths=[]; calls=[]
    actual_bridge=control.BRIDGE['replay_repeated_pads']
    def execute(stage,temp):
        assert stage.read_bytes()==PCB and not list(temp.iterdir())
        paths.append(stage.parent)
        return success(raw)
    def spy(pcb,output,inventory,**kwargs):
        assert not paths[0].exists()  # Cleanup precedes candidate creation.
        assert output is raw and pcb is PCB
        obs=[o for o in inventory.inventory.artifacts if o.declaration.role=='supporting'][0]
        assert obs.computed_sha256==sha256(raw).hexdigest()
        assert obs.computed_sha256!=sha256(RAW).hexdigest()
        assert obs.declaration.source_id=='current-execution-stdout'
        calls.append(output)
        return actual_bridge(pcb,output,inventory,**kwargs)
    monkeypatch.setitem(control.BRIDGE,'replay_repeated_pads',spy)
    result=control.run_control(PCB,declarations(),execute=execute,staging_root=tmp_path)
    assert isinstance(result,control.ControlSuccess),result
    assert len(calls)==1 and result.observation_sha256==sha256(raw).hexdigest()
    assert result.pcb_sha256==result.staged_sha256==sha256(PCB).hexdigest()
    assert result.staging_removed and result.helper_temp_empty and not list(tmp_path.iterdir())
    expected=[[(10,7.5),(12,7.5),(12,8.5),(10,8.5)],[(13,6.5),(15,6.5),(15,7.5),(13,7.5)]]
    for c,wanted in zip(result.replay.batch.candidates,expected):
        assert c.source.pad_number=='1'
        for p,xy in zip(c.vertices,wanted): assert (p.x,p.y)==pytest.approx(xy,abs=1e-6,rel=0)


@pytest.mark.parametrize('code',[Code.TIMEOUT,Code.EXIT,Code.OUTPUT,Code.CLEANUP])
def test_transport_failure_never_uses_diagnostic_prefix(monkeypatch,tmp_path,code):
    no_bridge(monkeypatch)
    result=ExecutionFailure((Issue(code,'fake-execution'),),RAW,b'',success().evidence)
    out=control.run_control(PCB,declarations(),execute=lambda *_:result,staging_root=tmp_path)
    assert_failure(out,code.value)
    assert out.transport is result and not list(tmp_path.iterdir())


def test_timeout_exception_blocks(monkeypatch,tmp_path):
    no_bridge(monkeypatch)
    def execute(*args): raise TimeoutError('fake executor')
    assert_failure(control.run_control(PCB,declarations(),execute=execute,staging_root=tmp_path),'TIMEOUT')
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('field,value',[('cleanup_state','unconfirmed'),('active_processes',1),
    ('active_processes',None),('root_exit',1),('stdout_eof',False),('stderr_eof',False),
    ('limits_verified',False),('resumed',False)])
def test_success_shape_without_cleanup_proof_blocks(monkeypatch,tmp_path,field,value):
    no_bridge(monkeypatch)
    t=success();t=replace(t,evidence=replace(t.evidence,**{field:value}))
    assert_failure(control.run_control(PCB,declarations(),execute=lambda *_:t,staging_root=tmp_path),'CLEANUP_UNCONFIRMED')
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('case',['pcb','staged','observation'])
def test_hash_mismatch_before_bridge(monkeypatch,tmp_path,case):
    no_bridge(monkeypatch); calls=[]
    def execute(stage,temp):
        calls.append(True)
        if case=='staged': stage.write_bytes(b'changed')
        data=json.loads(RAW)
        if case=='observation': data['input_sha256']='0'*64
        return success(json.dumps(data).encode())
    out=control.run_control(PCB+b'x' if case=='pcb' else PCB,declarations(),execute=execute,staging_root=tmp_path)
    assert_failure(out,'SOURCE_CONFLICT')
    assert bool(calls)==(case!='pcb')
    assert not list(tmp_path.iterdir())


def test_helper_residue_blocks_before_bridge(monkeypatch,tmp_path):
    no_bridge(monkeypatch)
    def execute(stage,temp):
        (temp/'leftover').write_bytes(b'x')
        return success()
    assert_failure(control.run_control(PCB,declarations(),execute=execute,staging_root=tmp_path),'CLEANUP_UNCONFIRMED')
    assert not list(tmp_path.iterdir())


def test_owner_cleanup_failure_blocks_before_bridge(monkeypatch,tmp_path):
    no_bridge(monkeypatch)
    original=control.tempfile.TemporaryDirectory
    class CleanupFailure:
        def __init__(self,*args,**kwargs): self.temp=original(*args,**kwargs)
        def __enter__(self): return self.temp.__enter__()
        def __exit__(self,*args):
            self.temp.__exit__(*args)
            raise OSError('simulated cleanup confirmation failure')
    monkeypatch.setattr(control.tempfile,'TemporaryDirectory',CleanupFailure)
    assert_failure(control.run_control(PCB,declarations(),execute=lambda *_:success(),staging_root=tmp_path),'CLEANUP_UNCONFIRMED')


@pytest.mark.parametrize('field,value',[('artifact_id','wrong'),('source_id','wrong'),('policy_id','wrong')])
def test_transport_identity_conflict(monkeypatch,tmp_path,field,value):
    no_bridge(monkeypatch);t=success();t=replace(t,evidence=replace(t.evidence,**{field:value}))
    assert_failure(control.run_control(PCB,declarations(),execute=lambda *_:t,staging_root=tmp_path),'SOURCE_CONFLICT')


def test_candidate_rejection_has_no_candidates(tmp_path):
    data=json.loads(RAW);data['footprints'][0]['pads'][1]['shape']=2
    t=success(json.dumps(data).encode())
    result=control.run_control(PCB,declarations(),execute=lambda *_:t,staging_root=tmp_path)
    assert_failure(result,'CANDIDATE_REJECTED')
    assert not hasattr(result.diagnostic,'candidates')


def test_partial_or_malformed_stdout_has_no_fallback(monkeypatch,tmp_path):
    no_bridge(monkeypatch)
    assert_failure(control.run_control(PCB,declarations(),execute=lambda *_:success(b'{'),staging_root=tmp_path),'SCHEMA_INVALID')


def test_observed_length_mismatch_blocks(monkeypatch,tmp_path):
    no_bridge(monkeypatch); t=success();t=replace(t,evidence=replace(t.evidence,observed_stdout=len(RAW)+1))
    assert_failure(control.run_control(PCB,declarations(),execute=lambda *_:t,staging_root=tmp_path),'OUTPUT_BUDGET_OR_LENGTH')
