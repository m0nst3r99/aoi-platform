"""Trusted local evaluation helper; loader sees only a private staged copy."""
import hashlib
import msvcrt
import os
from pathlib import Path
import runpy
import sys
import tempfile
import time


handle, size, digest, directory, probe = sys.argv[1:]
size = int(size)
if not 0 < size <= 16 * 1024 * 1024:
    raise ValueError('input budget')
fd = msvcrt.open_osfhandle(int(handle), os.O_RDONLY | os.O_BINARY)
with os.fdopen(fd, 'rb') as source, tempfile.TemporaryDirectory(prefix='loader-', dir=directory) as temp:
    target = Path(temp)/'input.kicad_pcb'
    actual, count = hashlib.sha256(), 0
    with target.open('xb') as output:
        while True:
            chunk = source.read(min(65536, size-count+1))
            if not chunk:
                break
            count += len(chunk)
            if count > size:
                raise ValueError('actual input exceeds declared size')
            actual.update(chunk)
            output.write(chunk)
    if count != size or actual.hexdigest() != digest:
        raise ValueError('staged input mismatch')
    def milestone(name):
        print(f'milestone {name} monotonic={time.monotonic():.6f}', file=sys.stderr, flush=True)
    milestone('before-import-pcbnew')
    import pcbnew
    milestone('after-import-pcbnew')
    # Verified in bundled wx 4.3.1 / wxWidgets 3.3.3. Keep both targets alive;
    # redirect rather than disable logging or dismiss native warning dialogs.
    import wx
    stderr_log_target = wx.LogStderr()
    previous_log_target = wx.Log.SetActiveTarget(stderr_log_target)
    native_load = pcbnew.LoadBoard
    def observed_load(*args, **kwargs):
        milestone('before-LoadBoard')
        result = native_load(*args, **kwargs)
        milestone('after-LoadBoard')
        return result
    pcbnew.LoadBoard = observed_load
    sys.argv = [probe, str(target)]
    runpy.run_path(probe, run_name='__main__')
