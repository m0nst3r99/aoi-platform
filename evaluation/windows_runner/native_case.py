"""One integration case per process, supervised by an external pytest watchdog."""
import ctypes as C
from dataclasses import asdict, replace
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import sys
import time
import threading

from models import ExecutionFailure, ExecutionSuccess, Request, StagedInput
from policy import TEST_LIMITS
import runner
import winapi
REAL_API = winapi.Api

case, directory = sys.argv[1], Path(sys.argv[2])
directory.mkdir(exist_ok=True)
stage = directory/'input.bin'
stage.write_bytes(b'caller-owned-stage\x00\xff')
source = stage.open('rb')
handle = msvcrt.get_osfhandle(source.fileno())
limits = TEST_LIMITS
helper = str(Path(__file__).with_name('helper.py').resolve())
argv = (helper, case)
marker = directory/'pids.txt'
faults = []
if case in ('out-exact', 'out-over', 'err-exact', 'err-over', 'combined-exact', 'combined-over', 'flood'):
    limits = replace(limits, stdout_bytes=64, stderr_bytes=64, combined_bytes=96, chunk_bytes=16)
    sizes = {'out-exact':(64,0), 'out-over':(65,0), 'err-exact':(0,64), 'err-over':(0,65),
             'combined-exact':(48,48), 'combined-over':(48,49), 'flood':(1000000,1000000)}[case]
    argv = (helper, 'emit', *map(str, sizes))
elif case == 'timeout':
    limits = replace(limits, wall_ms=300)
    argv = (helper, 'sleep')
elif case in ('tree','tree-no-pipe'):
    limits = replace(limits, wall_ms=1200)
    argv = (helper, case, str(marker))
elif case == 'parent-crash':
    argv = (helper, 'kill-parent', str(marker), str(os.getpid()))
elif case in ('stage','stage-readonly'):
    argv = (helper, case, '{staged_handle}')
elif case == 'job-handle':
    job_marker = directory/'job-handle.txt'
    argv = (helper, 'job-handle', str(job_marker))
    base = winapi.Api
    class ObserveJob(base):
        def __init__(self):
            super().__init__()
            original = self.CreateJobObjectW
            def observe(*args):
                handle = original(*args)
                job_marker.write_text(str(handle))
                return handle
            self.CreateJobObjectW = observe
    winapi.Api = ObserveJob
elif case == 'fault-close-cleanup':
    argv = (helper, 'empty')
    base = winapi.Api
    class CloseFailure(base):
        def __init__(self):
            super().__init__()
            pipes = []
            original_pipe, original_close = self.CreatePipe, self.CloseHandle
            def pipe(read, *args):
                result = original_pipe(read,*args)
                if result:
                    pipes.append(C.cast(read,C.POINTER(C.c_void_p)).contents.value)
                return result
            def close(handle):
                if pipes and handle==pipes[0] and not faults:
                    faults.append('CloseHandle.pipe-read')
                    C.set_last_error(5)
                    return 0
                return original_close(handle)
            self.CreatePipe, self.CloseHandle = pipe, close
    winapi.Api = CloseFailure
elif case == 'nested-compatible':
    outer = winapi.Api()
    outer_job = outer.require(outer.CreateJobObjectW(None,None),'outer-job')
    restrictions = C.c_uint32(1)  # Test the actual platform's nested-job behavior.
    outer.require(outer.SetInformationJobObject(outer_job,4,C.byref(restrictions),4),'outer-UI-limit')
    outer.require(outer.AssignProcessToJobObject(outer_job,outer.GetCurrentProcess()),'outer-assign')
    argv = (helper,'empty')
elif case == 'assign-native-reject':
    argv = (helper,'empty')
    base = winapi.Api
    class InvalidJobApi(base):
        def __init__(self):
            super().__init__()
            original = self.AssignProcessToJobObject
            self.AssignProcessToJobObject = lambda job, process: original(None, process)
    winapi.Api = InvalidJobApi
elif case == 'fault-verify':
    argv = (helper,'empty')
    base = winapi.Api
    class VerifyFailure(base):
        def __init__(self):
            super().__init__()
            original = self.QueryInformationJobObject
            def query(job, kind, data, *args):
                result = original(job,kind,data,*args)
                if result and kind==9:
                    C.cast(data,C.POINTER(winapi.ExtendedLimits)).contents.basic.processes += 1
                return result
            self.QueryInformationJobObject = query
    winapi.Api = VerifyFailure
elif case == 'memory':
    limits = replace(limits, process_memory=64*1024*1024)
elif case == 'memory-control':
    argv = (helper,'memory')
elif case == 'aggregate':
    limits = replace(limits, process_memory=192*1024*1024, job_memory=192*1024*1024)
    argv = (helper, 'aggregate', str(directory/'ready.txt'))
elif case == 'aggregate-control':
    limits = replace(limits, process_memory=192*1024*1024)
    argv = (helper,'aggregate',str(directory/'ready.txt'))
elif case == 'balanced':
    limits = replace(limits, combined_bytes=128*1024)
    argv = (helper,'emit',str(64*1024),str(64*1024))
elif case == 'count':
    limits = replace(limits, processes=1)
elif case.startswith('fault-'):
    argv = (helper, 'emit', '32', '32')
    operation = {'fault-assign':'AssignProcessToJobObject', 'fault-setup':'SetInformationJobObject',
                 'fault-resume':'ResumeThread', 'fault-read':'ReadFile', 'fault-peek':'PeekNamedPipe',
                 'fault-close':'CloseHandle', 'fault-query':'QueryInformationJobObject'}[case]
    base = winapi.Api
    class FaultApi(base):
        def __init__(self):
            super().__init__()
            original = getattr(self, operation)
            def fail(*args):
                if not faults:
                    faults.append(operation)
                    C.set_last_error(5)
                    return 0xffffffff if operation == 'ResumeThread' else 0
                return original(*args)
            setattr(self, operation, fail)
    winapi.Api = FaultApi
elif case == 'cleanup-timeout':
    argv = (helper, 'sleep')
    limits = replace(limits, wall_ms=100, cleanup_ms=10)
    base = winapi.Api
    class DelayApi(base):
        def __init__(self):
            super().__init__()
            original = self.TerminateJobObject
            def delay(*args):
                value = original(*args)
                time.sleep(0.03)
                return value
            self.TerminateJobObject = delay
    winapi.Api = DelayApi

environment = tuple((k, v) for k, v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP'))
request = Request(sys._base_executable, tuple(argv), str(directory.resolve()), environment,
                  StagedInput(handle, stage.stat().st_size, hashlib.sha256(stage.read_bytes()).hexdigest(), 'test-artifact','test-source'), limits)
if case == 'launch':
    request = replace(request, executable=str(directory/'absent.exe'))
elif case == 'hash':
    request = replace(request, staged=replace(request.staged, sha256='0'*64))
elif case == 'size':
    request = replace(request, staged=replace(request.staged, size=request.staged.size+1))
elif case == 'capability':
    runner.supported = lambda: False

counter = winapi.Api()
counter.dll.GetProcessHandleCount.argtypes = [C.c_void_p,C.c_void_p]
counter.dll.GetProcessHandleCount.restype = C.c_int
def handles():
    value = C.c_uint32()
    assert counter.dll.GetProcessHandleCount(counter.GetCurrentProcess(),C.byref(value))
    return value.value
initial_handles = handles()
# First CreatePipe/CreateProcessW initialize process-wide Windows handles on this
# build (+1/+2 observed). Warm up using the unmodified API, then require no handle
# growth on a second control and on the actual case. Never relax close results.
warmup_deltas = []
if case != 'capability':
    selected_api = winapi.Api
    winapi.Api = REAL_API
    warm_request = replace(request, executable=sys._base_executable, argv=(helper,'empty'),
        staged=StagedInput(handle, stage.stat().st_size, hashlib.sha256(stage.read_bytes()).hexdigest(), 'warmup','warmup'),
        limits=TEST_LIMITS)
    for _ in range(2):
        count_before = handles()
        warm = runner.run_bounded_worker(warm_request)
        assert isinstance(warm,ExecutionSuccess), warm
        warmup_deltas.append(handles()-count_before)
    assert warmup_deltas[1]==0, warmup_deltas
    if case == 'launch':
        # Windows' first missing-image launch also initializes cached system
        # handles; require its second execution to have zero growth.
        for _ in range(2):
            count_before = handles()
            missing = runner.run_bounded_worker(replace(warm_request, executable=request.executable))
            assert isinstance(missing,ExecutionFailure)
            warmup_deltas.append(handles()-count_before)
        assert warmup_deltas[-1]==0, warmup_deltas
    winapi.Api = selected_api
handles_before = handles()
threads_before = {t.ident for t in threading.enumerate()}
result = runner.run_bounded_worker(request)
handles_after = handles()
threads_unchanged = {t.ident for t in threading.enumerate()} == threads_before
source.seek(0)
unchanged = source.read() == b'caller-owned-stage\x00\xff' and stage.read_bytes() == b'caller-owned-stage\x00\xff'
source.close()
record = dict(case=case, kind=type(result).__name__, result=asdict(result), caller_ownership=unchanged,
              faults=faults, limits=asdict(limits), reader_threads_unchanged=threads_unchanged,
              executable=request.executable, handles_before=handles_before, handles_after=handles_after,
              initial_handles=initial_handles, warmup_deltas=warmup_deltas)
for key, value in list(record['result'].items()):
    if isinstance(value, bytes):
        record['result'][key] = value.hex()
(directory/'result.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
