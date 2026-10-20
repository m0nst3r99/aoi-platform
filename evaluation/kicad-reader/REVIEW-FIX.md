# Evaluation harness review fixes

Historical report; update 2026-10-19: user reports direct ZIP v2 review accepted
these fixes (23/23 regressions, 44/44 hashes, 14 logs unchanged). Reviewer did
not have complete PCB source or rerun KiCad. The closing awaiting-review wording
below is superseded for harness fixes only. [Errata/r2](population-errata-r2/ERRATA.md)
is new and pending review; r1 DNP=false descriptions for the twelve UUIDs are
superseded there without changing the old evidence.

Scope: evaluation only. No accepted fixture, product source/tests, checkbox,
allowlist or agent configuration changes. No commit/push. Prior review ZIP and
root raw evidence retained. Initial scripts archived as
[run-before-review.py](run-before-review.py) and [probe-before-review.py](probe-before-review.py).
The initial [README](README.md) is historical where it describes the old harness.

## Regressions and behavior

Before changing the scripts, [regressions](regression-before.txt) reported 11 failed,
1 control passed. Three review groups: skipped positive work could pass; arbitrary
negative crashes ignored; invalid outline and duplicate UUIDs could hide behind
bbox/dictionary checks. JSON failures also lost diagnostics.

The new [runner](run.py) enumerates all 27 required checks up front, defaults them
false and reports NOT_COMPLETED for blocked checks. Success requires every check
and no diagnostics. JSON/schema failures retain a report; launch/timeout failures
retain process evidence. Missing input data fails. Output directory must be new.
An inability to create/write the output directory itself necessarily fails at
the filesystem boundary; it cannot promise persistence on unwritable storage.

Negative probes require **exit 2 AND exact JSON**: malformed native LoadBoard=None
must yield NATIVE_LOAD_REJECTED; missing source must yield SOURCE_NOT_FOUND at
hash/open. Native exceptions, crash exit codes, timeout, exit 0, malformed JSON
and another rejection kind do not pass. Missing-file probe does not claim to
exercise native LoadBoard's missing-file handling.

Outline valid/count/holes/bbox checked independently. Duplicate footprint and
population UUIDs are rejected before dictionary mapping; the complete UUID sets
must agree. Both R7 and R8 must each exist once before value/pad comparison.
Full emitted observation schema is required, including fields not used by the
numeric oracles. These are bounded fixture-specific assertions, not proof of all
geometry or a general KiCad construct allowlist.

[Expanded tests](test_harness.py): **23 passed**, including positive fail/timeout,
negative crash/wrong code/JSON/timeout, missing fields, nonfinite bbox,
invalid outline/count/holes, duplicate/substituted UUID, absent R7/R8, CLI failure
and control success. Tests mock processes and derive portable data from the saved
observation JSON; no KiCad install or external accepted bundle is required.
They are harness regressions, not independent validation of every geometry value.

## New local run

[results.json](runs/review-fix-01/results.json): 26/27 pass, **evaluation failed,
exit 1** because population_fields retains the 12 known DNP conflicts. Both exact
negative contracts pass. Fixture hashes before/after unchanged. Raw stdout/stderr,
commands and hashes are saved under the new run directory; old evidence untouched.

[audit_dnp.py](audit_dnp.py) checks only the exact source hash/layout using numbered
text excerpts, not a general S-expression parser. [Audit evidence](runs/review-fix-01/dnp-source-audit.json)
includes all 12 UUIDs, entire raw attr blocks, line positions and source hash
`67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0`.
All twelve source blocks contain dnp; API=true, population=false. Population and
report hashes bind the comparison. Accepted r1 remains unchanged.

## Reproduction and limitations

```powershell
.\.venv\Scripts\python.exe -m pytest evaluation/kicad-reader/test_harness.py -q
.\.venv\Scripts\python.exe evaluation/kicad-reader/run.py 'C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1' --output evaluation/kicad-reader/runs/NEW-ID
.\.venv\Scripts\python.exe evaluation/kicad-reader/audit_dnp.py 'C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/source/Edgeberry.kicad_pcb' 'C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/population.json' evaluation/kicad-reader/runs/NEW-ID/results.json evaluation/kicad-reader/runs/NEW-ID/dnp-source-audit.json
git -c safe.directory=C:/dev/aoi-platform diff --check
```

Local native run executed outside sandbox using the previously observed working
environment; no claim sandbox timeout cause was fixed. Still no process memory/
output cap or full process-tree sandbox. No product adapter or full geometry
verification. The DNP conflict remains a failure, not a waived check.
Full pytest not rerun: no shared product code changes. Regression and whitespace
checks pass. Existing OpenSpec changes are retained; no new normative/task edits.
New evidence is awaiting review.
