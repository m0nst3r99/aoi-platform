"""Record a fresh review run; never overwrites prior evidence or reads fixtures."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
output = ROOT/'evidence'/sys.argv[1]
output.mkdir(parents=True, exist_ok=False)
environment = os.environ.copy()
environment['RUNNER_EVIDENCE_DIR'] = str(output/'native')
environment.pop('AOI_REAL_PCB_01_ROOT', None)
command = [sys.executable, '-m', 'pytest', 'tests', 'evaluation/kicad-reader/test_harness.py',
           'evaluation/windows_runner/test_portable.py', 'evaluation/windows_runner/test_native.py',
           '-q', '--tb=short', '--junitxml='+str(output/'pytest.xml')]
metadata = dict(started_utc=datetime.now(timezone.utc).isoformat(), command=command, cwd=str(REPO),
                python=sys.version, executable=sys.executable, base_executable=sys._base_executable,
                platform=platform.platform(), architecture=platform.machine(),
                windows_build=list(sys.getwindowsversion()) if sys.platform=='win32' else None,
                note='Native helpers only; no KiCad, accepted fixtures or product imports by runner.')
metadata['code_sha256'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')}
with (output/'pytest.stdout.txt').open('wb') as stdout, (output/'pytest.stderr.txt').open('wb') as stderr:
    process = subprocess.Popen(command, cwd=REPO, env=environment, stdout=stdout, stderr=stderr)
    try:
        metadata['exit_code'] = process.wait(timeout=180)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
        metadata['exit_code'] = 'suite-watchdog-timeout'
metadata['finished_utc'] = datetime.now(timezone.utc).isoformat()
(output/'environment-command.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print((output/'pytest.stdout.txt').read_text(errors='replace'))
print('Evidence:',output)
raise SystemExit(0 if metadata['exit_code']==0 else 1)
