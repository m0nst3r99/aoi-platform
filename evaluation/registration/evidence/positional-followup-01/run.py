"""Preserve exact inputs and each verification attempt without overwriting history."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

root = Path(__file__).resolve().parents[4]
here = Path(__file__).parent
attempt = here / sys.argv[1]
attempt.mkdir()
files = list((root/'src/aoi_platform/geometry').glob('*.py')) + list((root/'tests').glob('test_registration*.py'))
historical = [p for p in (root/'evaluation/registration/evidence').rglob('*') if p.is_file() and here not in p.parents]
def hashes(paths):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before = hashes(files + historical)
(attempt/'pre-hashes.json').write_text(json.dumps(before, indent=2))
for path in files:
    dest = attempt/'snapshot'/path.relative_to(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(path.read_bytes())
command = [sys.executable, '-m', 'pytest', 'tests/test_registration_position.py', 'tests/test_registration.py',
           'tests/test_registration_limits.py', '-q', '--junitxml='+str(attempt/'junit.xml')]
(attempt/'command.json').write_text(json.dumps(command, indent=2))
run = subprocess.run(command, cwd=root, capture_output=True)
(attempt/'stdout.bin').write_bytes(run.stdout)
(attempt/'stderr.bin').write_bytes(run.stderr)
after = hashes(files + historical)
(attempt/'post-hashes.json').write_text(json.dumps(after, indent=2))
(attempt/'result.json').write_text(json.dumps({'exit':run.returncode, 'unchanged':before==after,
    'historical_files':len(historical)}, indent=2))
print(run.stdout.decode(errors='replace'))
print('exit', run.returncode, 'unchanged', before==after)
sys.exit(run.returncode)
