"""Trusted synthetic workers. No KiCad, fixture or product imports."""
import ctypes as C
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

mode = sys.argv[1]
if mode == 'empty':
    pass
elif mode == 'binary':
    os.write(1, bytes(range(256)))
    os.write(2, b'\x00\xfferr')
elif mode == 'json':
    os.write(1, b'{invalid')
elif mode == 'emit':
    size_out, size_err = map(int, sys.argv[2:4])
    def emit(fd, size):
        while size:
            count = min(size, 4096)
            os.write(fd, b'x'*count)
            size -= count
    thread = threading.Thread(target=emit, args=(2, size_err))
    thread.start()
    emit(1, size_out)
    thread.join()
elif mode == 'exit':
    raise SystemExit(7)
elif mode == 'crash':
    k = C.WinDLL('kernel32')
    k.GetCurrentProcess.restype = C.c_void_p
    k.TerminateProcess.argtypes = [C.c_void_p, C.c_uint32]
    k.TerminateProcess(k.GetCurrentProcess(), 0xC0000005)
elif mode == 'sleep':
    time.sleep(60)
elif mode == 'stage':
    import msvcrt
    with os.fdopen(msvcrt.open_osfhandle(int(sys.argv[2]), os.O_RDONLY), 'rb') as stream:
        os.write(1, stream.read())
elif mode == 'stage-readonly':
    k = C.WinDLL('kernel32', use_last_error=True)
    k.WriteFile.argtypes = [C.c_void_p, C.c_void_p, C.c_uint32, C.c_void_p, C.c_void_p]
    count = C.c_uint32()
    result = k.WriteFile(int(sys.argv[2]), C.create_string_buffer(b'overwrite'), 9, C.byref(count), None)
    if result or C.get_last_error()!=5:
        raise SystemExit(22)
    os.write(1,b'WRITE_DENIED')
elif mode == 'job-handle':
    k = C.WinDLL('kernel32', use_last_error=True)
    k.QueryInformationJobObject.argtypes = [C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.c_void_p]
    data = C.create_string_buffer(48)
    handle = int(Path(sys.argv[2]).read_text())
    if k.QueryInformationJobObject(handle,1,data,48,None):
        raise SystemExit(25)
    os.write(1,b'NO_INHERITED_JOB')
elif mode in ('tree', 'tree-no-pipe', 'branch'):
    marker = Path(sys.argv[2])
    with marker.open('a') as stream:
        stream.write(str(os.getpid())+'\n')
    if mode in ('tree','tree-no-pipe'):
        extras = dict(stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) if mode=='tree-no-pipe' else {}
        subprocess.Popen([sys.executable, __file__, 'branch', str(marker)], close_fds=False, **extras)
    else:
        subprocess.Popen([sys.executable, __file__, 'leaf', str(marker)], close_fds=False)
        time.sleep(60)
elif mode == 'leaf':
    with Path(sys.argv[2]).open('a') as stream:
        stream.write(str(os.getpid())+'\n')
    time.sleep(60)
elif mode == 'kill-parent':
    marker = Path(sys.argv[2])
    subprocess.Popen([sys.executable, __file__, 'leaf', str(marker)], close_fds=False)
    with marker.open('a') as stream:
        stream.write(str(os.getpid())+'\n')
    time.sleep(0.4)
    os.kill(int(sys.argv[3]), 9)
    time.sleep(60)
elif mode in ('memory', 'aggregate', 'holder'):
    k = C.WinDLL('kernel32', use_last_error=True)
    k.VirtualAlloc.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.c_uint32]
    k.VirtualAlloc.restype = C.c_void_p
    allocations = []
    if mode == 'aggregate':
        child = subprocess.Popen([sys.executable, __file__, 'holder', sys.argv[2]], close_fds=False)
        deadline = time.monotonic()+3
        while not Path(sys.argv[2]).exists() and time.monotonic()<deadline:
            time.sleep(0.01)
        if not Path(sys.argv[2]).exists():
            raise SystemExit(9)
    for _ in range(128 if mode != 'holder' else 5):
        block = k.VirtualAlloc(None, 16*1024*1024, 0x3000, 4)
        if not block:
            os.write(1, ('ALLOCATION_DENIED:'+str(len(allocations)*16*1024*1024)).encode())
            raise SystemExit(23)
        allocations.append(block)
    if mode == 'holder':
        Path(sys.argv[2]).write_text('allocated-80MiB')
        time.sleep(60)
    raise SystemExit(8)
elif mode == 'count':
    try:
        subprocess.Popen([sys.executable, __file__, 'sleep'])
    except OSError:
        os.write(1, b'SPAWN_DENIED')
        raise SystemExit(24)
    raise SystemExit(8)
else:
    raise SystemExit(99)
