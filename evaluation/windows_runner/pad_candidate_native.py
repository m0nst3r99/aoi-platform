"""Native execution callback for the fixture control; no geometry semantics.

Reuses repeated_pads_control.py --worker (runner/helper/probe and exact budgets).
Watchdog matches existing controls:45s wait, kill worker,5s reap. A killed worker
never proves Job cleanup; the existing suspended-before-assign host-crash gap remains.
"""
from dataclasses import fields
from pathlib import Path
import json
import subprocess
import sys
import uuid
from models import Code, Evidence, ExecutionFailure, ExecutionSuccess, Issue

HERE = Path(__file__).resolve().parent


def _failure(code, operation):
    return ExecutionFailure((Issue(code,operation),),b'',b'',
        Evidence(None,None,None,False,False,'unconfirmed',0,0,0,False,False,
                 'synthetic-repeated-pads-v1','owned-stage','kicad-local-test-v1'))


def _read(path, limit):
    with path.open('rb') as f:
        data=f.read(limit+1)
    if len(data)>limit: raise ValueError('Worker output budget exceeded')
    return data


def _decode(directory):
    record=json.loads(_read(directory/'transport.json',65536))
    if type(record['success']) is not bool: raise ValueError('success must be boolean')
    result=record['result']; ev=result['evidence']
    if set(ev)!={f.name for f in fields(Evidence)}: raise ValueError('Unexpected evidence fields')
    for key in ('stdout_eof','stderr_eof','limits_verified','resumed'):
        if type(ev[key]) is not bool: raise ValueError('Invalid evidence boolean')
    for key in ('root_pid','root_exit','active_processes'):
        if ev[key] is not None and type(ev[key]) is not int: raise ValueError('Invalid evidence integer')
    for key in ('elapsed_ms','observed_stdout','observed_stderr'):
        if type(ev[key]) is not int or ev[key]<0: raise ValueError('Invalid evidence count')
    for key in ('cleanup_state','artifact_id','source_id','policy_id'):
        if type(ev[key]) is not str: raise ValueError('Invalid evidence text')
    evidence=Evidence(**ev)
    if not record['success']:
        issues=tuple(Issue(Code(i['code']),i['operation'],i.get('winerror')) for i in result['issues'])
        return ExecutionFailure(issues,_read(directory/'diagnostic_stdout_prefix.bin',2*1024**2),
            _read(directory/'diagnostic_stderr_prefix.bin',256*1024),evidence)
    if not all(record.get(k) is True for k in ('caller_handle_usable','stage_unchanged','helper_temp_empty')):
        return _failure(Code.CLEANUP,'worker-owner-checks')
    if not (evidence.root_exit==0 and evidence.active_processes==0 and evidence.cleanup_state=='cleaned'
            and evidence.stdout_eof and evidence.stderr_eof and evidence.limits_verified and evidence.resumed):
        return _failure(Code.CLEANUP,'worker-cleanup-proof')
    raw=_read(directory/'stdout.bin',2*1024**2); err=_read(directory/'stderr.bin',256*1024)
    if len(raw)!=evidence.observed_stdout or len(err)!=evidence.observed_stderr:
        raise ValueError('Worker byte counts differ')
    return ExecutionSuccess(raw,err,evidence)


class NativeExecution:
    """Pass instance as run_control(execute=...). Evidence root must already exist.

    Unique output directory per invocation prevents stale output fallback. No
    executable search: use the current absolute host Python and the existing
    worker's fixed bundled KiCad executable. No native call occurs on import.
    """
    def __init__(self,evidence_root):
        self.evidence_root=Path(evidence_root).resolve()

    def __call__(self,stage,helper_temp):
        if sys.platform!='win32':
            return _failure(Code.CAPABILITY,'windows-required')
        directory=self.evidence_root/('native-execution-'+uuid.uuid4().hex)
        try:
            directory.mkdir(exist_ok=False)
            command=[str(Path(sys._base_executable).resolve()),str(HERE/'repeated_pads_control.py'),
                     '--worker',str(directory),str(Path(stage).resolve()),str(Path(helper_temp).resolve())]
            (directory/'invocation.json').write_text(json.dumps(dict(argv=command,watchdog_seconds=45,
                kill_wait_seconds=5,scope='fixture-only; cleanup not assumed after watchdog kill'),indent=2)+'\n')
            with (directory/'watchdog.stdout').open('xb') as out,(directory/'watchdog.stderr').open('xb') as err:
                proc=subprocess.Popen(command,stdout=out,stderr=err,creationflags=0x08000000,shell=False)
                try:
                    status=proc.wait(timeout=45)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    try: proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        return _failure(Code.CLEANUP,'watchdog-reap-unconfirmed')
                    return _failure(Code.TIMEOUT,'independent-watchdog; cleanup-unconfirmed')
            if status!=0: return _failure(Code.EXIT,'worker-nonzero-exit')
            return _decode(directory)
        except (OSError,ValueError,TypeError,KeyError,AttributeError,RecursionError):
            return _failure(Code.WIN32,'worker-launch-or-result-invalid; cleanup-unconfirmed')
