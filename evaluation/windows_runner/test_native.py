"""Actual Windows cases each have an independent 20-second process watchdog."""
import ctypes as C
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

pytestmark = pytest.mark.skipif(sys.platform != 'win32' or C.sizeof(C.c_void_p)!=8, reason='Windows x64 native evidence unavailable')
HERE = Path(__file__).resolve().parent


def dead(pid):
    k = C.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes = [C.c_uint32,C.c_int,C.c_uint32]
    k.OpenProcess.restype = C.c_void_p
    k.WaitForSingleObject.argtypes = [C.c_void_p,C.c_uint32]
    k.WaitForSingleObject.restype = C.c_uint32
    k.CloseHandle.argtypes = [C.c_void_p]
    handle = k.OpenProcess(0x100000, False, pid)
    if not handle:
        return C.get_last_error()==87
    try:
        return k.WaitForSingleObject(handle, 0)==0
    finally:
        k.CloseHandle(handle)


CASES = ['empty','binary','json','exit','crash','out-exact','out-over','err-exact','err-over',
         'combined-exact','combined-over','flood','timeout','tree','stage','memory','aggregate','count',
         'fault-assign','fault-setup','fault-resume','fault-read','fault-peek','fault-close','fault-query',
         'cleanup-timeout','launch','hash','size','capability','parent-crash',
         'tree-no-pipe','job-handle','stage-readonly','fault-close-cleanup','nested-compatible',
         'assign-native-reject','fault-verify','memory-control','aggregate-control','balanced']


@pytest.mark.parametrize('case', CASES)
def test_native(case, tmp_path):
    directory = tmp_path/case
    directory.mkdir()
    with (directory/'watchdog.stdout').open('wb') as out, (directory/'watchdog.stderr').open('wb') as err:
        # Supervise the real interpreter, not the venv redirector (which may
        # spawn another process and would make kill() target the wrong parent).
        proc = subprocess.Popen([sys._base_executable, str(HERE/'native_case.py'), case, str(directory)],
                                stdout=out, stderr=err, creationflags=0x08000000)
        try:
            status = proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
            pytest.fail('Independent watchdog killed hung runner; native case not PASS')
    evidence_root = os.environ.get('RUNNER_EVIDENCE_DIR')
    if evidence_root:
        import shutil
        shutil.copytree(directory, Path(evidence_root)/case)
    if case == 'parent-crash':
        assert status != 0
    else:
        assert status == 0, (directory/'watchdog.stderr').read_text(errors='replace')
        record = json.loads((directory/'result.json').read_text())
        result = record['result']
        success = case in ('empty','binary','json','out-exact','err-exact','combined-exact','stage','stage-readonly','job-handle','nested-compatible','balanced')
        assert (record['kind']=='ExecutionSuccess') == success, record
        assert record['caller_ownership']
        assert record['reader_threads_unchanged']
        assert record['handles_before']==record['handles_after'], record
        if not success:
            assert result['diagnostic_prefixes_usable'] is False
            assert len(bytes.fromhex(result['diagnostic_stdout_prefix'])) <= record['limits']['stdout_bytes']
            assert len(bytes.fromhex(result['diagnostic_stderr_prefix'])) <= record['limits']['stderr_bytes']
            assert sum(len(bytes.fromhex(result[k])) for k in ('diagnostic_stdout_prefix','diagnostic_stderr_prefix')) <= record['limits']['combined_bytes']
        if case in ('out-over','err-over','combined-over','flood'):
            assert any(i['code']=='OUTPUT_BUDGET' for i in result['issues'])
        if case in ('timeout','tree','tree-no-pipe'):
            assert any(i['code']=='TIMEOUT' for i in result['issues'])
        if case in ('out-exact','err-exact','combined-exact'):
            sizes={'out-exact':(64,0),'err-exact':(0,64),'combined-exact':(48,48)}[case]
            assert tuple(len(bytes.fromhex(result[k])) for k in ('stdout','stderr'))==sizes
        if success:
            assert result['evidence']['root_exit']==0
            assert result['evidence']['active_processes']==0
            assert result['evidence']['stdout_eof'] and result['evidence']['stderr_eof']
            assert result['evidence']['cleanup_state']=='cleaned'
        if case=='json':
            assert bytes.fromhex(result['stdout'])==b'{invalid'
        if case=='binary':
            assert bytes.fromhex(result['stdout'])==bytes(range(256))
            assert bytes.fromhex(result['stderr'])==b'\x00\xfferr'
        if case in ('fault-assign','fault-setup','fault-resume','fault-query','capability','hash','size','launch','assign-native-reject','fault-verify'):
            assert not result['evidence']['resumed']
        if case in ('memory','aggregate','count','memory-control','aggregate-control'):
            prefix = bytes.fromhex(result['diagnostic_stdout_prefix'])
            assert (b'SPAWN_DENIED' if case=='count' else b'ALLOCATION_DENIED') in prefix, record
            assert all(i['code']!='MEMORY_BUDGET' for i in result['issues'])
            if case!='count':
                allocated=int(prefix.split(b':')[1])
                if case=='memory':
                    assert allocated <= 64*1024*1024
                elif case=='memory-control':
                    assert allocated > 64*1024*1024
                elif case=='aggregate':
                    assert allocated <= 112*1024*1024
                elif case=='aggregate-control':
                    assert allocated >= 128*1024*1024
        if case=='balanced':
            assert len(bytes.fromhex(result['stdout'])) == len(bytes.fromhex(result['stderr'])) == 65536
        if case in ('cleanup-timeout','fault-close-cleanup'):
            assert result['evidence']['cleanup_state']=='unconfirmed'
        if case=='job-handle':
            assert bytes.fromhex(result['stdout'])==b'NO_INHERITED_JOB'
        if case=='stage-readonly':
            assert bytes.fromhex(result['stdout'])==b'WRITE_DENIED'
    if case in ('tree','tree-no-pipe','parent-crash'):
        pids = [int(p) for p in (directory/'pids.txt').read_text().splitlines()]
        assert len(pids)>=(3 if case!='parent-crash' else 2)
        until=time.monotonic()+3
        while not all(dead(pid) for pid in pids) and time.monotonic()<until:
            time.sleep(0.01)
        assert all(dead(pid) for pid in pids), pids
    verification = dict(case=case, watchdog_root_exit=status, assertions_passed=True,
                        process_tree_verified_dead=case in ('tree','tree-no-pipe','parent-crash'),
                        watchdog_timeout_seconds=20)
    (directory/'verification.json').write_text(json.dumps(verification,indent=2))
    if evidence_root:
        import shutil
        shutil.copyfile(directory/'verification.json', Path(evidence_root)/case/'verification.json')
