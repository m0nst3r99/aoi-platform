"""Portable callback tests. Popen is always fake; no runner/native launch."""
from dataclasses import asdict,replace
from pathlib import Path
import json
import subprocess
import pytest
import pad_candidate_native as native
from models import Code, Evidence, ExecutionSuccess, ExecutionFailure, Issue


def evidence(raw=b'current stdout'):
    return Evidence(12,0,0,True,True,'cleaned',10,len(raw),0,True,True,
                    'synthetic-repeated-pads-v1','owned-stage','kicad-local-test-v1')


def setup(monkeypatch,tmp_path,mode='success'):
    stage=tmp_path/'stage.pcb';stage.write_bytes(b'staged')
    helper=tmp_path/'helper';helper.mkdir()
    output=tmp_path/'evidence';output.mkdir()
    calls=[]
    monkeypatch.setattr(native.sys,'platform','win32')
    class FakeProcess:
        def __init__(self,argv,**kwargs):
            self.waits=[];self.killed=False;calls.append(self)
            self.argv=argv;self.options=kwargs
            assert kwargs['shell'] is False and kwargs['creationflags']==0x08000000
            assert Path(argv[0]).is_absolute()
            assert Path(argv[1]).name=='repeated_pads_control.py' and argv[2]=='--worker'
            assert Path(argv[4])==stage and Path(argv[5])==helper
            d=Path(argv[3]);self.directory=d
            if mode=='missing': return
            raw=b'current stdout';e=evidence(raw)
            if mode=='failure':
                result=ExecutionFailure((Issue(Code.TIMEOUT,'runner'),),b'partial',b'',e)
            else: result=ExecutionSuccess(raw,b'',e)
            record=asdict(result)
            for key in ('stdout','stderr','diagnostic_stdout_prefix','diagnostic_stderr_prefix'):
                if key in record: (d/(key+'.bin')).write_bytes(record.pop(key))
            obj=dict(success=mode!='failure',result=record,caller_handle_usable=True,
                     stage_unchanged=True,helper_temp_empty=True)
            if mode=='owner':obj['caller_handle_usable']=False
            if mode=='cleanup':obj['result']['evidence']['active_processes']=1
            if mode=='schema':obj['result']['evidence']['stdout_eof']=1
            if mode=='length':obj['result']['evidence']['observed_stdout']=999
            (d/'transport.json').write_text('{' if mode=='json' else json.dumps(obj))
        def wait(self,timeout):
            self.waits.append(timeout)
            if mode in ('timeout','reap') and (timeout==45 or mode=='reap'):
                raise subprocess.TimeoutExpired(self.argv,timeout)
            return 4 if mode=='exit' else 0
        def kill(self):self.killed=True
    monkeypatch.setattr(native.subprocess,'Popen',FakeProcess)
    return native.NativeExecution(output),stage,helper,calls


def test_callback_reuses_worker_with_fresh_output_and_exact_bytes(monkeypatch,tmp_path):
    callback,stage,helper,calls=setup(monkeypatch,tmp_path)
    first=callback(stage,helper);second=callback(stage,helper)
    assert isinstance(first,ExecutionSuccess) and first.stdout==b'current stdout'
    assert second==first and calls[0].directory!=calls[1].directory
    assert all(c.waits==[45] and not c.killed for c in calls)
    assert stage.read_bytes()==b'staged' and helper.exists() # Caller owns staging.
    invocation=json.loads((calls[0].directory/'invocation.json').read_text())
    assert invocation['watchdog_seconds']==45 and invocation['kill_wait_seconds']==5


@pytest.mark.parametrize('mode,code',[('timeout',Code.TIMEOUT),('reap',Code.CLEANUP),
    ('exit',Code.EXIT),('failure',Code.TIMEOUT),('owner',Code.CLEANUP),('cleanup',Code.CLEANUP),
    ('missing',Code.WIN32),('json',Code.WIN32),('schema',Code.WIN32),('length',Code.WIN32)])
def test_failures_never_promoted(monkeypatch,tmp_path,mode,code):
    callback,stage,helper,calls=setup(monkeypatch,tmp_path,mode)
    result=callback(stage,helper)
    assert isinstance(result,ExecutionFailure) and result.issues[0].code is code
    assert not hasattr(result,'stdout') and result.diagnostic_prefixes_usable is False
    if mode in ('timeout','reap'):
        assert calls[0].waits==[45,5] and calls[0].killed
        assert result.evidence.cleanup_state=='unconfirmed'
    if mode=='failure': assert result.diagnostic_stdout_prefix==b'partial'


def test_non_windows_does_not_launch(monkeypatch,tmp_path):
    monkeypatch.setattr(native.sys,'platform','linux')
    def forbidden(*a,**kw):raise AssertionError('must not launch')
    monkeypatch.setattr(native.subprocess,'Popen',forbidden)
    result=native.NativeExecution(tmp_path)(tmp_path/'x',tmp_path/'y')
    assert isinstance(result,ExecutionFailure) and result.issues[0].code is Code.CAPABILITY
    assert not list(tmp_path.iterdir())


def test_launch_error_is_typed(monkeypatch,tmp_path):
    callback,stage,helper,calls=setup(monkeypatch,tmp_path)
    def fail(*a,**kw):raise OSError('launch failed')
    monkeypatch.setattr(native.subprocess,'Popen',fail)
    result=callback(stage,helper)
    assert isinstance(result,ExecutionFailure) and result.issues[0].code is Code.WIN32


def test_decoder_bounds_stdout(tmp_path):
    raw=b'x'*(2*1024**2+1)
    (tmp_path/'stdout.bin').write_bytes(raw);(tmp_path/'stderr.bin').write_bytes(b'')
    (tmp_path/'transport.json').write_text(json.dumps(dict(success=True,
        result=dict(evidence=asdict(evidence(raw))),caller_handle_usable=True,stage_unchanged=True,helper_temp_empty=True)))
    with pytest.raises(ValueError,match='budget'):native._decode(tmp_path)
