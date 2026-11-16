"""Validate remediation-only scope and evidence reconstruction; no test execution."""
from pathlib import Path
import json
import re
import subprocess

from record_run import ROOT, HERE, digest, git, save


if __name__ == "__main__":
    before=json.loads((HERE/"pre-remediation/pre-hashes.json").read_text())
    changed=sorted(name for name,value in before.items() if digest(ROOT/name)!=value)
    expected=sorted(["src/aoi_platform/geometry/canonical_outline.py",
                     "tests/test_canonical_outline.py", "tests/test_outline_legacy_differential.py",
                     "HANDOFF.md", "openspec/changes/board-geometry-foundation/implementation-status.md",
                     "openspec/changes/board-geometry-foundation/verification-matrix.md"])
    assert changed==expected,changed
    reconstructed={}
    for label in ("pre-remediation","red-01","targeted-02","consolidated-03"):
        manifest=json.loads((HERE/label/"pre-hashes.json").read_text())
        assert all(digest(HERE/label/"snapshot"/name)==value for name,value in manifest.items())
        reconstructed[label]=len(manifest)
    final=json.loads((HERE/"consolidated-03/post-hashes.json").read_text())
    assert all(digest(ROOT/name)==value for name,value in final.items()
               if not name.endswith(".md"))
    historical=json.loads((HERE/"historical-hashes.json").read_text())
    assert all(digest(ROOT/name)==value for name,value in historical.items())
    matrix="openspec/changes/board-geometry-foundation/verification-matrix.md"
    rows=lambda text:[line for line in text.splitlines() if re.match(r'^\| [GP]\d\d \|',line)]
    previous=(HERE/"pre-remediation/snapshot"/matrix).read_text(encoding="utf-8")
    assert rows(previous)==rows((ROOT/matrix).read_text(encoding="utf-8"))
    assert len(rows(previous))==47
    oldhandoff=(HERE/"pre-remediation/snapshot/HANDOFF.md").read_text(encoding="utf-8").split("\n",2)[2]
    assert (ROOT/"HANDOFF.md").read_text(encoding="utf-8").endswith(oldhandoff)
    pre=json.loads((HERE/"git-preflight.json").read_text())
    untracked=set(git("ls-files","--others","--exclude-standard").splitlines())
    assert set(pre["untracked"])<=untracked
    assert all(name.startswith("evaluation/canonical-outline/evidence/slice-a-remediation-01/")
               for name in untracked-set(pre["untracked"]))
    assert not git("diff","--cached","--name-only").strip()
    check=subprocess.run(["git","diff","--check"],cwd=ROOT,capture_output=True,encoding="utf-8")
    assert check.returncode==0,check.stdout
    links=0
    for name in expected:
        data=(ROOT/name).read_text(encoding="utf-8")
        assert all(line==line.rstrip() for line in data.splitlines()),name
        if not name.endswith(".md"): continue
        snapshot=(HERE/"pre-remediation/snapshot"/name).read_text(encoding="utf-8")
        new=[line for line in data.splitlines() if line not in snapshot.splitlines()]
        for target in re.findall(r'\]\(([^)]+)\)',"\n".join(new)):
            assert ((ROOT/name).parent/target.split('#')[0]).exists(),target
            links+=1
    result={"changed_files":changed,"final_hashes":{name:digest(ROOT/name) for name in changed},
            "reconstructed_snapshot_files":reconstructed,"historical_hashes_preserved":len(historical),
            "scenario_rows_unchanged":47,"handoff_history_preserved":True,
            "new_link_targets_verified":links,"unrelated_untracked_paths_preserved":True,
            "index_empty":True,"git_diff_check_exit":check.returncode}
    save(HERE/"delivery-validation.json",result)
    print(json.dumps(result))
