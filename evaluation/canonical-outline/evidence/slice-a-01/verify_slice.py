"""Record final targeted verification without overwriting prior runs."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
FILES = [
    "src/aoi_platform/geometry/canonical_outline.py",
    "src/aoi_platform/geometry/_outline_exact.py",
    "src/aoi_platform/geometry/_contour_validation.py",
    "src/aoi_platform/geometry/outlines.py",
    "src/aoi_platform/geometry/models.py",
    "src/aoi_platform/geometry/transforms.py",
    "src/aoi_platform/geometry/reports.py",
    "src/aoi_platform/geometry/fixture_geometry.py",
    "src/aoi_platform/geometry/envelopes.py",
    "tests/test_canonical_outline.py",
    "tests/test_outline_legacy_differential.py",
    "tests/test_fixture_geometry.py",
    "tests/test_envelopes.py",
    "tests/conftest.py", "pyproject.toml",
    "evaluation/canonical-outline/evidence/slice-a-01/baseline_outlines.py",
]
HISTORICAL = subprocess.check_output(
    ["git", "ls-files", "evaluation/kicad-reader/evidence/source-checked-preparation*"],
    cwd=ROOT, text=True).splitlines()


def hashes(names):
    result = {}
    for name in names:
        data = (ROOT / name).read_bytes()
        result[name] = {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    return result


def save(name, value):
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


if __name__ == "__main__":
    import pytest
    label = sys.argv[1] if len(sys.argv)>1 else "final-03"
    selection = sys.argv[2:] or ["tests/test_canonical_outline.py",
               "tests/test_outline_legacy_differential.py", "tests/test_fixture_geometry.py",
               "tests/test_envelopes.py"]
    command = [sys.executable, "-m", "pytest", *selection, "-q", "-p", "no:cacheprovider",
               "--junitxml=evaluation/canonical-outline/evidence/slice-a-01/"+label+".xml"]
    prefix = "" if label == "final-03" else label+"-"
    for name in (label+".xml", label+".log", *(prefix+n for n in ("invocation.json", "pre-hashes.json", "post-hashes.json", "result.json"))):
        if (HERE/name).exists():
            raise SystemExit("Refusing to overwrite " + name)
    save(prefix+"invocation.json", {"command": command, "cwd": str(ROOT), "python": sys.version,
                             "pytest": pytest.__version__, "platform": platform.platform(),
                             "env": {"PYTHONDONTWRITEBYTECODE": "1"},
                             "head": subprocess.check_output(["git", "rev-parse", "HEAD"],cwd=ROOT,text=True).strip()})
    before = hashes(FILES+HISTORICAL)
    save(prefix+"pre-hashes.json", before)
    start = time.perf_counter()
    with (HERE/(label+".log")).open("xb") as stream:
        run = subprocess.run(command,cwd=ROOT,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"},stdout=stream,stderr=subprocess.STDOUT)
    elapsed = time.perf_counter()-start
    after = hashes(FILES+HISTORICAL)
    save(prefix+"post-hashes.json",after)
    tree = ET.parse(HERE/(label+".xml"))
    cases = [{"class":c.get("classname"),"name":c.get("name"),
              "status":"FAIL" if c.find("failure") is not None or c.find("error") is not None else "SKIP" if c.find("skipped") is not None else "PASS"}
             for c in tree.iter("testcase")]
    result = {"exit":run.returncode,"duration_seconds":elapsed,"unchanged":before==after,
              "inputs":len(FILES),"historical_files":len(HISTORICAL),
              "counts":{s:sum(c["status"]==s for c in cases) for s in ("PASS","FAIL","SKIP")},"tests":cases}
    save(prefix+"result.json",result)
    print(json.dumps({k:v for k,v in result.items() if k!="tests"}))
    raise SystemExit(run.returncode or (0 if before==after else 1))
