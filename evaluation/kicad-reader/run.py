"""Fail-closed evaluation harness; not a product adapter or security sandbox."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import runpy
from dataclasses import asdict
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
BIN = Path("C:/Program Files/KiCad/10.0/bin")
EXPECTED_HASH = "67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0"
REQUIRED = (
    "cli-version", "cli-pcb-help", "cli-export-help", "pcbnew-execution",
    "pcbnew-json", "observation_schema", "build", "format", "input_hash", "outline_valid",
    "outline_count", "outline_holes", "outline_bbox", "footprint_count",
    "unique_footprint_uuids", "unique_population_uuids", "uuid_set",
    "population_classifications", "population_fields", "positions_angles_sides",
    "R7_R8_presence", "R7_R8_values", "R7_pad_oracle", "edge_shapes",
    "malformed_rejection", "missing_rejection", "fixture_files_unchanged",
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


schema = runpy.run_path(str(ROOT / 'observation_schema.py'))['schema']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--allow-legacy-protocol", action="store_true",
                        help="Historical unversioned replay only; footprint edge coverage stays unknown")
    parser.add_argument("--output", type=Path, required=True,
                        help="New directory only; existing evidence is never overwritten")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    result = dict(observed_at=datetime.now(timezone.utc).isoformat(),
                  required_checks=list(REQUIRED), checks={k: False for k in REQUIRED},
                  diagnostics=[], runs=[], conflicts=[], outcome="failed",
                  outline_decision=None,
                  dependencies_sha256={str(p): sha(p) for p in
                      (ROOT / 'run.py', ROOT / 'observation_schema.py')})

    def issue(check, code, **evidence):
        result["diagnostics"].append(dict(check=check, code=code, **evidence))

    def check(name, predicate):
        try:
            passed = predicate() is True
            result["checks"][name] = passed
            if not passed:
                issue(name, "ORACLE_MISMATCH")
        except Exception as error:
            issue(name, "DATA_INVALID_OR_MISSING", exception=type(error).__name__, detail=str(error))

    def run(name, argv):
        argv = [str(a) for a in argv]
        try:
            proc = subprocess.run(argv, capture_output=True, timeout=30)
            stdout, stderr, status = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as error:
            stdout, stderr, status = error.stdout or b"", error.stderr or b"", "timeout"
        except OSError as error:
            stdout, stderr, status = b"", str(error).encode(), "launch-error"
        (out / (name + ".stdout.txt")).write_bytes(stdout)
        (out / (name + ".stderr.txt")).write_bytes(stderr)
        result["runs"].append(dict(name=name, argv=argv, status=status,
                                  stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                                  stderr_sha256=hashlib.sha256(stderr).hexdigest()))
        return stdout, status

    def negative(name, path, expected):
        raw, status = run(name, [BIN / "python.exe", "-u", ROOT / "probe.py", path])
        try:
            payload = json.loads(raw)
            passed = status == 2 and payload == {"outcome": "rejected", "code": expected}
        except (ValueError, TypeError):
            passed = False
        result["checks"][name + "_rejection"] = passed
        if not passed:
            issue(name + "_rejection", "WRONG_REJECTION", expected=expected, exit_status=status)

    try:
        fixture = args.fixture.resolve(strict=True)
        source = fixture / "source/Edgeberry.kicad_pcb"
        result["fixture_before"] = snapshot(fixture)
        for name, tail in (("cli-version", ["version"]), ("cli-pcb-help", ["pcb", "--help"]),
                           ("cli-export-help", ["pcb", "export", "--help"])):
            raw, status = run(name, [BIN / "kicad-cli.exe", *tail])
            check(name, lambda: status == 0 and bool(raw.strip()) and
                  (name != "cli-version" or raw.decode().strip() == "10.0.7"))
        raw, status = run("pcbnew", [BIN / "python.exe", "-u", ROOT / "probe.py", source])
        check("pcbnew-execution", lambda: status == 0)
        if status != 0:
            issue("pcbnew-execution", "PROBE_FAILED", exit_status=status)
        else:
            try:
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError("JSON object required")
                result["checks"]["pcbnew-json"] = True
            except (ValueError, TypeError) as error:
                issue("pcbnew-json", "JSON_INVALID", detail=str(error))
                data = {}
            historical = (args.allow_legacy_protocol
                          and result['checks']['pcbnew-json']
                          and not any(k in data for k in ('protocol_version', 'footprint_edges', 'geometry_coverage')))
            if historical:
                result['outline_decision'] = dict(status='not_applicable_historical_replay', diagnostics=[])
            else:
                result['dependencies_sha256'][str(ROOT / 'outline_decision.py')] = sha(ROOT / 'outline_decision.py')
                evaluate_outline = runpy.run_path(str(ROOT / 'outline_decision.py'))['evaluate_outline']
                decision = evaluate_outline(raw)
                result['outline_decision'] = asdict(decision)
                for diagnostic in decision.diagnostics:
                    details = asdict(diagnostic)
                    code = details.pop('code')
                    issue('outline_decision', code, **details)
            population = json.loads((fixture / "population.json").read_text(encoding="utf-8-sig"))
            check("observation_schema", lambda: schema(data, allow_legacy=args.allow_legacy_protocol))
            result["protocol_version"] = data.get("protocol_version", "legacy-unversioned")
            result["footprint_edge_coverage"] = (
                data.get("geometry_coverage") if data.get("protocol_version") == 2 else "unknown")
            check("build", lambda: data["build"] == "10.0.7")
            check("format", lambda: data["format_version"] == 20260206)
            check("input_hash", lambda: data["input_sha256"] == sha(source) == EXPECTED_HASH)
            check("outline_valid", lambda: data["outline"]["valid"] is True)
            check("outline_count", lambda: type(data["outline"]["count"]) is int and data["outline"]["count"] == 1)
            check("outline_holes", lambda: data["outline"]["holes"] == [0] and all(type(x) is int for x in data["outline"]["holes"]))
            check("outline_bbox", lambda: data["outline"]["origin_mm"] == [83.649, 51.772] and data["outline"]["size_mm"] == [135.0, 90.0])
            check("footprint_count", lambda: len(data["footprints"]) == 57)
            def unique(rows):
                ids = [r["uuid"] for r in rows]
                return all(isinstance(x, str) and bool(x) for x in ids) and len(ids) == len(set(ids))
            check("unique_footprint_uuids", lambda: unique(data["footprints"]))
            check("unique_population_uuids", lambda: unique(population))
            check("uuid_set", lambda: {f["uuid"] for f in data["footprints"]} == {p["uuid"] for p in population})
            if all(result["checks"][k] for k in ("unique_footprint_uuids", "unique_population_uuids", "uuid_set")):
                by_id = {f["uuid"]: f for f in data["footprints"]}
                check("population_classifications", lambda: sum(p["assembly_target_eligible"] is True for p in population) == 28 and sum(p["retain_fiducial_data"] is True for p in population) == 3)
                def fields():
                    for p in population:
                        for key in ("reference", "value", "footprint", "dnp", "exclude_from_bom", "exclude_from_position"):
                            actual = by_id[p["uuid"]][key]
                            if actual != p[key] or type(actual) is not type(p[key]):
                                result["conflicts"].append(dict(uuid=p["uuid"], field=key, declared=p[key], observed=actual))
                    return not result["conflicts"]
                check("population_fields", fields)
                check("positions_angles_sides", lambda: all(
                    by_id[p["uuid"]]["position_mm"] == [float(x) for x in p["at_raw"].split()[:2]] and
                    (by_id[p["uuid"]]["angle_deg"] - (float(p["at_raw"].split()[2]) if len(p["at_raw"].split()) > 2 else 0)) % 360 == 0 and
                    by_id[p["uuid"]]["layer"] == p["layer"].strip('"') for p in population))
            check("R7_R8_presence", lambda: all(sum(f["reference"] == ref for f in data["footprints"]) == 1 for ref in ("R7", "R8")))
            if result["checks"]["R7_R8_presence"]:
                check("R7_R8_values", lambda: all(f["value"] == "270R" for f in data["footprints"] if f["reference"] in ("R7", "R8")))
                def pad_oracle():
                    r7 = next(f for f in data["footprints"] if f["reference"] == "R7")
                    pads = [p for p in r7["pads"] if p["number"] == "1"]
                    return len(pads) == 1 and pads[0]["position_mm"] == [99.1615, 70.272]
                check("R7_pad_oracle", pad_oracle)
            check("edge_shapes", lambda: sorted(e["shape"] for e in data["edges"]) == [0] * 12 + [2] * 3)
        bad = out / "malformed.kicad_pcb"
        bad.write_text("(kicad_pcb (version 20260206) (generator pcbnew) (broken", encoding="utf-8")
        negative("malformed", bad, "NATIVE_LOAD_REJECTED")
        negative("missing", out / "missing.kicad_pcb", "SOURCE_NOT_FOUND")
        result["fixture_after"] = snapshot(fixture)
        check("fixture_files_unchanged", lambda: result["fixture_before"] == result["fixture_after"])
    except Exception as error:
        issue("harness", "HARNESS_ERROR", exception=type(error).__name__, detail=str(error))
    finally:
        for name in REQUIRED:
            if not result["checks"][name] and not any(d["check"] == name for d in result["diagnostics"]):
                issue(name, "NOT_COMPLETED")
        result["outcome"] = "passed" if all(result["checks"].values()) and not result["diagnostics"] else "failed"
        (out / "results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"outcome": result["outcome"], "checks": result["checks"]}, indent=2))
    return 0 if result["outcome"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
