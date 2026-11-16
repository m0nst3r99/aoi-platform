"""Fresh per-run byte snapshots, commands, hashes, logs and test identities."""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, encoding="utf-8")


def digest(path):
    raw = path.read_bytes()
    return {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)


def inputs():
    paths = list((ROOT/"src/aoi_platform/geometry").glob("*.py"))
    paths += [ROOT/"tests"/name for name in ("conftest.py", "test_canonical_outline.py",
              "test_outline_legacy_differential.py", "test_fixture_geometry.py", "test_envelopes.py")]
    paths += [ROOT/"pyproject.toml", ROOT/"AGENTS.md", ROOT/"HANDOFF.md",
              ROOT/"evaluation/canonical-outline/evidence/slice-a-01/baseline_outlines.py"]
    paths += list((ROOT/"openspec/changes/board-geometry-foundation").rglob("*.md"))
    return sorted(set(p.relative_to(ROOT).as_posix() for p in paths))


if __name__ == "__main__":
    label, *selection = sys.argv[1:]
    run = HERE/label
    run.mkdir()  # Never overwrite a run.
    if label == "pre-remediation":
        preserved = list((ROOT/"evaluation/canonical-outline/evidence/slice-a-01").rglob("*"))
        preserved += [ROOT/p for p in git("ls-files", "evaluation/kicad-reader/evidence/source-checked-preparation*").splitlines()]
        save(HERE/"historical-hashes.json", {p.relative_to(ROOT).as_posix():digest(p) for p in preserved if p.is_file()})
        save(HERE/"git-preflight.json", {"head":git("rev-parse","HEAD").strip(),
             "branch":git("branch","--show-current").strip(),"status":git("status","--short"),
             "untracked":git("ls-files","--others","--exclude-standard").splitlines()})
    names = inputs()
    before = {name:digest(ROOT/name) for name in names}
    for name in names:
        target = run/"snapshot"/name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write((ROOT/name).read_bytes())
    save(run/"pre-hashes.json", before)
    if not selection:
        print("Saved pre-remediation source/document snapshots")
        raise SystemExit(0)
    import pytest
    command = [sys.executable,"-m","pytest",*selection,"-q","-p","no:cacheprovider",
               "--junitxml="+str(run/"pytest.xml")]
    save(run/"invocation.json", {"command":command,"cwd":str(ROOT),"python":sys.version,
          "pytest":pytest.__version__,"platform":platform.platform(),"env":{"PYTHONDONTWRITEBYTECODE":"1"}})
    start = time.perf_counter()
    with (run/"pytest.log").open("xb") as stream:
        process = subprocess.run(command,cwd=ROOT,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"},stdout=stream,stderr=subprocess.STDOUT)
    elapsed = time.perf_counter()-start
    after = {name:digest(ROOT/name) for name in names}
    save(run/"post-hashes.json",after)
    historical=json.loads((HERE/"historical-hashes.json").read_text())
    unchanged=all(digest(ROOT/name)==value for name,value in historical.items())
    cases=[]
    if (run/"pytest.xml").exists():
        for case in ET.parse(run/"pytest.xml").iter("testcase"):
            status="FAIL" if case.find("failure") is not None or case.find("error") is not None else "SKIP" if case.find("skipped") is not None else "PASS"
            cases.append({"class":case.get("classname"),"name":case.get("name"),"status":status})
    result={"exit":process.returncode,"wall_seconds":elapsed,"inputs_unchanged":before==after,
            "historical_unchanged":unchanged,"historical_files":len(historical),
            "counts":{s:sum(c['status']==s for c in cases) for s in ('PASS','FAIL','SKIP')},"tests":cases}
    save(run/"result.json",result)
    print(json.dumps({k:v for k,v in result.items() if k!='tests'}))
    raise SystemExit(process.returncode or (0 if before==after and unchanged else 1))
