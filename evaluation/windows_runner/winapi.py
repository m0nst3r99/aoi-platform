"""Explicit x64 Win32 bindings. Import only after platform capability check."""
import ctypes as C

D = C.c_uint32
Q = C.c_uint64
S = C.c_size_t
H = C.c_void_p
B = C.c_int32
P = C.c_void_p
W = C.c_wchar_p


class SA(C.Structure):
    _fields_ = [('length', D), ('descriptor', P), ('inherit', B)]


class BasicLimits(C.Structure):
    _fields_ = [('process_time', C.c_int64), ('job_time', C.c_int64), ('flags', D),
                ('min_working', S), ('max_working', S), ('processes', D),
                ('affinity', S), ('priority', D), ('scheduling', D)]


class IO(C.Structure):
    _fields_ = [(n, Q) for n in ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]


class ExtendedLimits(C.Structure):
    _fields_ = [('basic', BasicLimits), ('io', IO), ('process_memory', S),
                ('job_memory', S), ('peak_process', S), ('peak_job', S)]


class Accounting(C.Structure):
    _fields_ = [(n, C.c_int64) for n in ('user', 'kernel', 'period_user', 'period_kernel')] + [
        ('page_faults', D), ('total', D), ('active', D), ('terminated', D)]


class Startup(C.Structure):
    _fields_ = [('cb', D), ('reserved', W), ('desktop', W), ('title', W),
                ('x', D), ('y', D), ('xsize', D), ('ysize', D), ('xchars', D),
                ('ychars', D), ('fill', D), ('flags', D), ('show', C.c_uint16),
                ('reserved_size', C.c_uint16), ('reserved_bytes', P),
                ('stdin', H), ('stdout', H), ('stderr', H)]


class StartupEx(C.Structure):
    _fields_ = [('startup', Startup), ('attributes', P)]


class ProcessInfo(C.Structure):
    _fields_ = [('process', H), ('thread', H), ('pid', D), ('tid', D)]


class Api:
    def __init__(self):
        self.dll = C.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'CreateJobObjectW': (H, [P, W]),
            'SetInformationJobObject': (B, [H, D, P, D]),
            'QueryInformationJobObject': (B, [H, D, P, D, P]),
            'AssignProcessToJobObject': (B, [H, H]),
            'TerminateJobObject': (B, [H, D]),
            'TerminateProcess': (B, [H, D]),
            'GetCurrentProcess': (H, []),
            'DuplicateHandle': (B, [H, H, H, P, D, B, D]),
            'GetFileType': (D, [H]),
            'GetFileSizeEx': (B, [H, P]),
            'CreateFileMappingW': (H, [H, P, D, D, D, W]),
            'MapViewOfFile': (P, [H, D, D, D, S]),
            'UnmapViewOfFile': (B, [P]),
            'CreatePipe': (B, [P, P, P, D]),
            'SetHandleInformation': (B, [H, D, D]),
            'PeekNamedPipe': (B, [H, P, D, P, P, P]),
            'ReadFile': (B, [H, P, D, P, P]),
            'CreateFileW': (H, [W, D, D, P, D, D, H]),
            'InitializeProcThreadAttributeList': (B, [P, D, D, P]),
            'UpdateProcThreadAttribute': (B, [P, D, S, P, S, P, P]),
            'DeleteProcThreadAttributeList': (None, [P]),
            'CreateProcessW': (B, [W, P, P, P, B, D, P, W, P, P]),
            'ResumeThread': (D, [H]),
            'WaitForSingleObject': (D, [H, D]),
            'GetExitCodeProcess': (B, [H, P]),
            'CloseHandle': (B, [H]),
        }
        for name, (result, args) in signatures.items():
            function = getattr(self.dll, name)
            function.restype, function.argtypes = result, args
            setattr(self, name, function)
        if (C.sizeof(ExtendedLimits), C.sizeof(StartupEx), C.sizeof(Accounting)) != (144, 112, 48):
            raise OSError('unsupported Win32 ABI')

    @staticmethod
    def error(operation):
        error = C.get_last_error()
        result = OSError(error, operation)
        result.winerror = error
        raise result

    def require(self, value, operation):
        if not value:
            self.error(operation)
        return value
