"""Windows x64 evaluation transport. Trusted local handles; NOT a security sandbox."""
import ctypes as C
import hashlib
import ntpath
import platform
import re
import subprocess
import sys
import sysconfig
import time

from models import Code, Evidence, ExecutionFailure, ExecutionSuccess, Issue, Limits, Request, StagedInput


def supported():
    return (sys.platform == 'win32' and platform.python_implementation() == 'CPython'
            and C.sizeof(C.c_void_p) == 8 and sysconfig.get_platform() == 'win-amd64')


def validate(request):
    if type(request) is not Request or type(request.limits) is not Limits or type(request.staged) is not StagedInput:
        return False
    limits, staged = request.limits, request.staged
    for name in ('policy_id',):
        if type(getattr(limits, name)) is not str or not 1 <= len(getattr(limits, name)) <= 256:
            return False
    for name in ('input_bytes', 'stdout_bytes', 'stderr_bytes', 'combined_bytes', 'chunk_bytes',
                 'wall_ms', 'cleanup_ms', 'process_memory', 'job_memory', 'processes'):
        value = getattr(limits, name)
        maximum = (2**32-2 if name in ('wall_ms', 'cleanup_ms', 'processes') else 2**63-1)
        if type(value) is not int or not 1 <= value <= maximum:
            return False
    if limits.chunk_bytes > 1024*1024 or limits.process_memory > limits.job_memory:
        return False
    if type(staged.handle) is not int or not 0 < staged.handle < 2**64-1:
        return False
    if type(staged.size) is not int or not 0 <= staged.size <= limits.input_bytes:
        return False
    if type(staged.sha256) is not str or not re.fullmatch('[a-f0-9]{64}', staged.sha256):
        return False
    if not all(type(s) is str and 1 <= len(s) <= 256 for s in (staged.artifact_id, staged.source_id)):
        return False
    if not all(type(p) is str and len(p) <= 32767 and ntpath.isabs(p) and ntpath.splitdrive(p)[0] and '\0' not in p
               for p in (request.executable, request.cwd)):
        return False
    if type(request.argv) is not tuple or len(request.argv) > 1024 or not all(type(a) is str and len(a) <= 32767 and '\0' not in a for a in request.argv):
        return False
    if sum(map(len, request.argv)) + len(request.executable) > 32000:
        return False
    if type(request.environment) is not tuple or len(request.environment) > 1024:
        return False
    names = []
    for row in request.environment:
        if type(row) is not tuple or len(row) != 2 or not all(type(s) is str and len(s) <= 32767 and '\0' not in s for s in row):
            return False
        key, value = row
        if not key or '=' in key:
            return False
        names.append(key.upper())
    if len(names) != len(set(names)):
        return False
    if sum(len(k)+len(v)+2 for k, v in request.environment) > 32765:
        return False
    try:
        command = subprocess.list2cmdline((request.executable, *request.argv))
        env = '\0'.join(k+'='+v for k, v in request.environment)+'\0\0'
        return len(command.encode('utf-16-le'))//2 < 32000 and len(env.encode('utf-16-le'))//2 < 32767
    except UnicodeError:
        return False


def run_bounded_worker(request: Request) -> ExecutionSuccess | ExecutionFailure:
    start = time.monotonic()
    issues = []
    buffers = [bytearray(), bytearray()]
    counts = [0, 0]
    eof = [False, False]
    root_pid = root_exit = active = None
    resumed = verified = False
    cleanup_state = 'not-started'
    owned = {}
    view = None
    attributes = None
    assigned = False
    api = None

    def issue(code, operation, error=None):
        if len(issues) < 16:
            issues.append(Issue(code, operation[:64], getattr(error, 'winerror', None)))

    def finish():
        valid = type(request) is Request
        def text(value):
            return value[:256] if type(value) is str else ''
        evidence = Evidence(root_pid, root_exit, active, *eof, cleanup_state,
                            int((time.monotonic()-start)*1000), *counts, verified, resumed,
                            text(request.staged.artifact_id) if valid and type(request.staged) is StagedInput else '',
                            text(request.staged.source_id) if valid and type(request.staged) is StagedInput else '',
                            text(request.limits.policy_id) if valid and type(request.limits) is Limits else '')
        if issues:
            return ExecutionFailure(tuple(issues), bytes(buffers[0]), bytes(buffers[1]), evidence)
        return ExecutionSuccess(bytes(buffers[0]), bytes(buffers[1]), evidence)

    if not validate(request):
        issue(Code.INVALID, 'request')
        return finish()
    if not supported():
        issue(Code.CAPABILITY, 'Windows-x64-required')
        return finish()
    limits = request.limits
    deadline = start + limits.wall_ms/1000

    class Stop(Exception):
        pass

    def timecheck():
        if time.monotonic() >= deadline:
            issue(Code.TIMEOUT, 'entry-deadline')
            raise Stop()

    def keep(name, handle):
        if not handle or handle == 2**64-1:
            api.error(name)
        owned[name] = handle
        return handle

    def close(name):
        if name in owned:
            api.require(api.CloseHandle(owned[name]), 'CloseHandle.'+name)
            del owned[name]

    try:
        from winapi import Api, H, D, S, SA, ExtendedLimits, Accounting, StartupEx, ProcessInfo
        api = Api()
        timecheck()
        process = api.GetCurrentProcess()
        duplicate = H()
        api.require(api.DuplicateHandle(process, request.staged.handle, process, C.byref(duplicate),
                                        0x80000000, True, 0), 'DuplicateHandle.staged')
        stage = keep('stage', duplicate.value)
        if api.GetFileType(stage) != 1:
            issue(Code.CAPABILITY, 'local-disk-handle-required')
            raise Stop()
        length = C.c_int64()
        api.require(api.GetFileSizeEx(stage, C.byref(length)), 'GetFileSizeEx')
        if length.value != request.staged.size:
            issue(Code.SOURCE, 'size')
            raise Stop()
        digest = hashlib.sha256()
        if length.value:
            mapping = keep('mapping', api.CreateFileMappingW(stage, None, 2, 0, 0, None))
            view = api.require(api.MapViewOfFile(mapping, 4, 0, 0, length.value), 'MapViewOfFile')
            for offset in range(0, length.value, limits.chunk_bytes):
                timecheck()
                digest.update(C.string_at(view+offset, min(limits.chunk_bytes, length.value-offset)))
            api.require(api.UnmapViewOfFile(view), 'UnmapViewOfFile')
            view = None
            close('mapping')
        if digest.hexdigest() != request.staged.sha256:
            issue(Code.SOURCE, 'sha256')
            raise Stop()
        timecheck()
        job = keep('job', api.CreateJobObjectW(None, None))
        configuration = ExtendedLimits()
        configuration.basic.flags = 0x2000 | 0x100 | 0x200 | 0x8  # kill, process/job commit, count
        configuration.basic.processes = limits.processes
        configuration.process_memory = limits.process_memory
        configuration.job_memory = limits.job_memory
        api.require(api.SetInformationJobObject(job, 9, C.byref(configuration), C.sizeof(configuration)), 'SetJobLimits')
        observed = ExtendedLimits()
        api.require(api.QueryInformationJobObject(job, 9, C.byref(observed), C.sizeof(observed), None), 'QueryJobLimits')
        if (observed.basic.flags, observed.basic.processes, observed.process_memory, observed.job_memory) != (
                configuration.basic.flags, limits.processes, limits.process_memory, limits.job_memory):
            issue(Code.CAPABILITY, 'job-limits-not-installed')
            raise Stop()
        verified = True
        security = SA(C.sizeof(SA), None, 1)
        for prefix in ('out', 'err'):
            read, write = H(), H()
            api.require(api.CreatePipe(C.byref(read), C.byref(write), C.byref(security), 4096), 'CreatePipe')
            keep(prefix+'-read', read.value)
            keep(prefix+'-write', write.value)
            api.require(api.SetHandleInformation(read, 1, 0), 'SetHandleInformation')
        null = keep('null', api.CreateFileW('NUL', 0x80000000, 3, C.byref(security), 3, 0, None))
        size = S()
        api.InitializeProcThreadAttributeList(None, 1, 0, C.byref(size))
        if size.value == 0 or size.value > 65536:
            issue(Code.CAPABILITY, 'attribute-list-size')
            raise Stop()
        attribute_buffer = C.create_string_buffer(size.value)
        api.require(api.InitializeProcThreadAttributeList(attribute_buffer, 1, 0, C.byref(size)), 'InitializeAttributes')
        attributes = attribute_buffer
        inherited = (H*4)(stage, null, owned['out-write'], owned['err-write'])
        api.require(api.UpdateProcThreadAttribute(attributes, 0, 0x20002, inherited, C.sizeof(inherited), None, None), 'HandleAllowlist')
        startup = StartupEx()
        startup.startup.cb = C.sizeof(startup)
        startup.startup.flags = 0x100 | 1
        startup.startup.show = 0
        startup.startup.stdin, startup.startup.stdout, startup.startup.stderr = null, owned['out-write'], owned['err-write']
        startup.attributes = C.cast(attributes, C.c_void_p)
        argv = [str(stage) if value == '{staged_handle}' else value for value in request.argv]
        command_text = subprocess.list2cmdline([request.executable, *argv])
        if len(command_text.encode('utf-16-le'))//2 >= 32767:
            issue(Code.INVALID, 'expanded-command-length')
            raise Stop()
        command = C.create_unicode_buffer(command_text)
        environment = C.create_unicode_buffer('\0'.join(k+'='+v for k, v in sorted(request.environment, key=lambda row: row[0].upper()))+'\0\0')
        info = ProcessInfo()
        timecheck()
        api.require(api.CreateProcessW(request.executable, command, None, None, True,
                                        0x4 | 0x80000 | 0x400 | 0x8000000,
                                        environment, request.cwd, C.byref(startup), C.byref(info)), 'CreateProcessW')
        keep('root', info.process)
        keep('thread', info.thread)
        root_pid = info.pid
        api.require(api.AssignProcessToJobObject(job, info.process), 'AssignProcessToJobObject')
        assigned = True
        timecheck()
        if api.ResumeThread(info.thread) == 0xffffffff:
            api.error('ResumeThread')
        resumed = True
        close('thread')
        close('out-write')
        close('err-write')
        close('null')
        close('stage')
        # Single owner/reader; bytes peeked cannot be consumed by another reader.
        while True:
            timecheck()
            for index, prefix in enumerate(('out', 'err')):
                if eof[index]:
                    continue
                available = D()
                handle = owned[prefix+'-read']
                if not api.PeekNamedPipe(handle, None, 0, None, C.byref(available), None):
                    if C.get_last_error() == 109:  # ERROR_BROKEN_PIPE is EOF
                        eof[index] = True
                        continue
                    api.error('PeekNamedPipe.'+prefix)
                if available.value:
                    amount = min(available.value, limits.chunk_bytes)
                    buffer, read = C.create_string_buffer(amount), D()
                    api.require(api.ReadFile(handle, buffer, amount, C.byref(read), None), 'ReadFile.'+prefix)
                    if not 0 < read.value <= amount:
                        issue(Code.WIN32, 'ReadFile.invalid-count')
                        raise Stop()
                    counts[index] += read.value
                    cap = (limits.stdout_bytes, limits.stderr_bytes)[index]
                    remaining = min(cap-len(buffers[index]), limits.combined_bytes-sum(map(len, buffers)))
                    buffers[index].extend(buffer.raw[:min(read.value, remaining)])
                    if counts[index] > cap or sum(counts) > limits.combined_bytes:
                        issue(Code.OUTPUT, prefix+'-or-combined')
                        raise Stop()
            wait = api.WaitForSingleObject(owned['root'], 0)
            if wait == 0:
                exit_code = D()
                api.require(api.GetExitCodeProcess(owned['root'], C.byref(exit_code)), 'GetExitCodeProcess')
                root_exit = exit_code.value
                if root_exit != 0:
                    issue(Code.EXIT, 'root-exit')
                    raise Stop()
            elif wait != 258:
                api.error('WaitForSingleObject')
            accounting = Accounting()
            api.require(api.QueryInformationJobObject(job, 1, C.byref(accounting), C.sizeof(accounting), None), 'QueryActiveProcesses')
            active = accounting.active
            if root_exit == 0 and active == 0 and all(eof):
                timecheck()
                break
            time.sleep(min(0.002, max(0, deadline-time.monotonic())))
    except Stop:
        pass
    except (OSError, AttributeError, ImportError) as error:
        issue(Code.WIN32 if api else Code.CAPABILITY, str(error)[:64], error)
    finally:
        cleanup_deadline = time.monotonic() + limits.cleanup_ms/1000
        proven = True
        if api:
            if issues and 'job' in owned:
                try:
                    api.require(api.TerminateJobObject(owned['job'], 0xE0000001), 'TerminateJobObject')
                except OSError as error:
                    issue(Code.CLEANUP, 'TerminateJobObject', error)
                    proven = False
            if 'root' in owned:
                try:
                    if not assigned:
                        api.require(api.TerminateProcess(owned['root'], 0xE0000002), 'TerminateSuspendedProcess')
                    while api.WaitForSingleObject(owned['root'], 0) != 0:
                        if time.monotonic() >= cleanup_deadline:
                            raise TimeoutError()
                        time.sleep(0.001)
                    exit_code = D()
                    api.require(api.GetExitCodeProcess(owned['root'], C.byref(exit_code)), 'GetExitCode.cleanup')
                    root_exit = exit_code.value
                except OSError as error:
                    issue(Code.CLEANUP, 'root-termination-unconfirmed', error)
                    proven = False
            if 'job' in owned:
                try:
                    while True:
                        accounting = Accounting()
                        api.require(api.QueryInformationJobObject(owned['job'], 1, C.byref(accounting), C.sizeof(accounting), None), 'QueryJob.cleanup')
                        active = accounting.active
                        if active == 0:
                            break
                        if time.monotonic() >= cleanup_deadline:
                            raise TimeoutError()
                        time.sleep(0.001)
                except OSError as error:
                    issue(Code.CLEANUP, 'job-empty-unconfirmed', error)
                    proven = False
            if view:
                if not api.UnmapViewOfFile(view):
                    issue(Code.CLEANUP, 'UnmapViewOfFile')
                    proven = False
            if attributes is not None:
                api.DeleteProcThreadAttributeList(attributes)
            # No reader threads or pending I/O to cancel; close pipe read handles.
            for name in list(owned):
                try:
                    close(name)
                except OSError as error:
                    issue(Code.CLEANUP, 'CloseHandle.'+name, error)
                    proven = False
                    # One best-effort retry; retain failure even if retry succeeds.
                    try:
                        close(name)
                    except OSError:
                        pass
        if time.monotonic() >= cleanup_deadline:
            issue(Code.CLEANUP, 'cleanup-deadline')
            proven = False
        cleanup_state = 'cleaned' if proven and not owned else 'unconfirmed'
        if cleanup_state != 'cleaned' and not issues:
            issue(Code.CLEANUP, 'resources')
    return finish()
