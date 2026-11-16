"""Read-only delivery checks; write only a fresh validation manifest here."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, encoding="utf-8", stderr=subprocess.PIPE).strip()


def rows(text):
    return {parts[1].strip(): parts for line in text.splitlines()
            if re.match(r"^\| [GP]\d\d \|", line) for parts in [line.split("|")]}


if __name__ == "__main__":
    matrix = "openspec/changes/board-geometry-foundation/verification-matrix.md"
    a, b = rows(git("show", "HEAD:"+matrix)), rows((ROOT/matrix).read_text(encoding="utf-8"))
    assert len(a) == len(b) == 47 and a.keys() == b.keys()
    assert all(a[k][1:5] == b[k][1:5] and a[k][6:10] == b[k][6:10]
               and a[k][11:] == b[k][11:] for k in a)
    changed = git("diff", "--name-only").splitlines()
    assert set(changed) == {"HANDOFF.md", matrix,
                           "openspec/changes/board-geometry-foundation/implementation-status.md",
                           "src/aoi_platform/geometry/outlines.py"}, changed
    assert not git("diff", "--cached", "--name-only")
    history = git("show", "HEAD:HANDOFF.md").split("\n", 2)[2]
    assert (ROOT/"HANDOFF.md").read_text(encoding="utf-8").rstrip().endswith(history.rstrip())
    links = []
    for name in changed:
        if not name.endswith(".md"):
            continue
        additions = "\n".join(line[1:] for line in git("diff", "--", name).splitlines()
                              if line.startswith("+") and not line.startswith("+++"))
        for target in re.findall(r"\]\(([^)]+)\)", additions):
            if "://" in target:
                continue
            path = target.split("#")[0]
            dest = (ROOT/name).parent/path if path else ROOT/name
            assert dest.exists(), (name, target)
            links.append([name, target])
    check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, encoding="utf-8")
    assert check.returncode == 0, check.stdout
    hashes = json.loads((HERE/"exhaustion-05-post-hashes.json").read_text())
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == v["sha256"]
               for name, v in hashes.items())
    files = sorted(set(changed + [
        "src/aoi_platform/geometry/canonical_outline.py",
        "src/aoi_platform/geometry/_outline_exact.py",
        "src/aoi_platform/geometry/_contour_validation.py",
        "tests/test_canonical_outline.py", "tests/test_outline_legacy_differential.py",
    ] + [p.relative_to(ROOT).as_posix() for p in HERE.iterdir() if p.is_file()]))
    for name in files:
        if name.endswith((".py", ".md")):
            assert all(line == line.rstrip() for line in (ROOT/name).read_text(encoding="utf-8").splitlines()), name
    manifest = {name: {"size": (ROOT/name).stat().st_size,
                       "sha256": hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in files}
    result = {"scenario_count": 47, "scenario_identities_statuses_reuse_unchanged": True,
              "handoff_history_preserved": True, "added_link_targets_checked": len(links),
              "diff_check_exit": check.returncode, "index_empty": True,
              "verified_run_hashes_unchanged": len(hashes), "files": manifest}
    with (HERE/"delivery-validation.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "files"}))
