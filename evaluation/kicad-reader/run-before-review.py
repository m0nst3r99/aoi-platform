"""Local evaluation harness, not an application reader or security sandbox."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
FIXTURE = Path(sys.argv[1]).resolve(strict=True)
BIN = Path("C:/Program Files/KiCad/10.0/bin")
SOURCE = FIXTURE / "source/Edgeberry.kicad_pcb"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


before = {str(p.relative_to(FIXTURE)): sha(p) for p in FIXTURE.rglob("*") if p.is_file()}
runs = []


def run(name, argv):
    try:
        r = subprocess.run([str(a) for a in argv], capture_output=True, timeout=30)
        stdout, stderr, status = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, status = error.stdout or b"", error.stderr or b"", "timeout-30s"
    (ROOT / (name + ".stdout.txt")).write_bytes(stdout)
    (ROOT / (name + ".stderr.txt")).write_bytes(stderr)
    runs.append(dict(name=name, argv=[str(a) for a in argv], status=status,
                     stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                     stderr_sha256=hashlib.sha256(stderr).hexdigest()))
    return stdout, status


run("cli-version", [BIN / "kicad-cli.exe", "version"])
run("cli-pcb-help", [BIN / "kicad-cli.exe", "pcb", "--help"])
run("cli-export-help", [BIN / "kicad-cli.exe", "pcb", "export", "--help"])
raw, status = run("pcbnew", [BIN / "python.exe", "-u", ROOT / "probe.py", SOURCE])
checks = {}
conflicts = []
if status == 0:
    data = json.loads(raw)
    population = json.loads((FIXTURE / "population.json").read_text(encoding="utf-8-sig"))
    by_id = {f["uuid"]: f for f in data["footprints"]}
    for declaration in population:
        for field in ("reference", "value", "footprint", "dnp", "exclude_from_bom", "exclude_from_position"):
            actual = by_id[declaration["uuid"]][field]
            if actual != declaration[field]:
                conflicts.append(dict(uuid=declaration["uuid"], field=field,
                                      declared=declaration[field], observed=actual))
    checks["input_hash"] = data["input_sha256"] == "67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0"
    checks["outline_135x90"] = data["outline"]["size_mm"] == [135.0, 90.0]
    checks["57_footprints"] = len(by_id) == 57
    checks["28_assembly_3_fiducials"] = (sum(p["assembly_target_eligible"] for p in population) == 28 and sum(p["retain_fiducial_data"] for p in population) == 3)
    checks["all_population_uuid_fields"] = all(
        p["uuid"] in by_id and all(by_id[p["uuid"]][k] == p[k] for k in
                                  ("reference", "value", "footprint", "dnp", "exclude_from_bom", "exclude_from_position"))
        for p in population)
    checks["all_population_positions_angles_sides"] = all(
        by_id[p["uuid"]]["position_mm"] == [float(x) for x in p["at_raw"].split()[:2]]
        and (by_id[p["uuid"]]["angle_deg"] - (float(p["at_raw"].split()[2]) if len(p["at_raw"].split()) > 2 else 0)) % 360 == 0
        and by_id[p["uuid"]]["layer"] == p["layer"].strip('"') for p in population)
    checks["R7_R8_270R"] = all(f["value"] == "270R" for f in by_id.values() if f["reference"] in ("R7", "R8"))
    r7 = next(f for f in by_id.values() if f["reference"] == "R7")
    checks["R7_pad1_independent_world_oracle"] = next(p for p in r7["pads"] if p["number"] == "1")["position_mm"] == [99.1615, 70.272]
    checks["12_lines_3_arcs"] = sorted(e["shape"] for e in data["edges"]) == [0] * 12 + [2] * 3
bad = ROOT / "malformed.kicad_pcb"
bad.write_text("(kicad_pcb (version 20260206) (generator pcbnew) (broken", encoding="utf-8")
run("malformed", [BIN / "python.exe", "-u", ROOT / "probe.py", bad])
run("missing", [BIN / "python.exe", "-u", ROOT / "probe.py", ROOT / "missing.kicad_pcb"])
after = {str(p.relative_to(FIXTURE)): sha(p) for p in FIXTURE.rglob("*") if p.is_file()}
checks["fixture_files_unchanged"] = before == after
result = dict(observed_at=datetime.now(timezone.utc).isoformat(), runs=runs, checks=checks,
              conflicts=conflicts, fixture_before=before, fixture_after=after)
(ROOT / "results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(dict(checks=checks, statuses={r["name"]: r["status"] for r in runs}), indent=2))
sys.exit(0 if checks and all(checks.values()) else 1)
