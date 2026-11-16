# Slice A independent audit remediation — 2026-11-16

Baseline master `2ee201dfc62fd7363336a8b099e2886e039dd59a`; existing Slice A
working-tree edits preserved. No commit/push, normative specification change or
scenario-status/task-checkbox promotion. Independent audit was user-relayed FIX
REQUIRED; these are implementer results awaiting independent re-review.

## Findings and exact changes

- F1 HIGH: `transform_canonical_outline` in
  [canonical_outline.py](../../../../src/aoi_platform/geometry/canonical_outline.py)
  admits transform ID, target/source frames, provenance and bounded typed matrix/
  flags before convention/isometry/apply helpers. Static admission diagnostics do
  not format rejected input. Byte-limit tests use 129 two-byte characters for a
  256-byte ID limit, 513 for 1024-byte details, and a million-character ID, all
  paired with invalid conventions. Helper spies fail if any helper runs early.
- F2 MEDIUM: the same function reserves 64 primitives before isometry/convention
  helpers, then eight primitives per mapped endpoint, for the complete batch
  before mapping/output allocation. `_CanonicalContour.finish` reserves four,
  not two, for abs, two products and comparison. Global limits are unchanged.
- F3 LOW: every remediation test run has exact byte snapshots under its
  `snapshot/`, pre/post hashes, invocation/environment, JUnit, log, and results
  enumerating every test identity. [Recorder](record_run.py) refuses existing run
  directories. [Pre-remediation](pre-remediation/pre-hashes.json) captures the
  actual starting source/docs; no old evidence was rewritten.
- [Canonical tests](../../../../tests/test_canonical_outline.py) add F1/F2 spies
  and literal accounting oracles; the existing 512-edge reservation expectation
  changes by exactly +2 for the corrected area-finalization operations.
- [Legacy differential tests](../../../../tests/test_outline_legacy_differential.py)
  add an earlier edge-pair intersection competing with later frame and closure
  faults, and coincident-arc overlap through shared traversal. All compare full
  exception tuples with pinned pre-refactor source; expectations are not weakened.
  No legacy production code changed during remediation.

Only these three source/test files and the directly affected HANDOFF,
implementation-status and verification-matrix documents change relative to the
pre-remediation snapshot, plus this fresh evidence directory. Public signatures,
geometry limits, existing line/arc behavior and numerical policy are unchanged.

## Executed verification

| Run | Scope | Result | Pytest duration |
| --- | --- | --- | --- |
| [red-01](red-01/result.json) | New tests, `-k remediation`, before source fix | 10 FAIL / 3 PASS / 0 SKIP; 66 deselected | 0.31 s |
| [targeted-02](targeted-02/result.json) | Same selection after fix | 13 PASS / 0 FAIL / 0 SKIP; 66 deselected | 0.13 s |
| [consolidated-03](consolidated-03/result.json) | All four Slice A/legacy files; strengthened adversarial and phase spies | 179 PASS / 0 FAIL / 0 SKIP | 30.44 s |

The ten red failures reproduce five early-helper admissions and five accounting/
phase-boundary faults; all three added legacy cases pass even before remediation.
No failing run is deleted. Final composition: 58 canonical, 22 differential,
21 fixture and 78 envelope tests. No native KiCad, H249/H55 or unrelated suite.

[Final exact invocation](consolidated-03/invocation.json): Python 3.11.9,
pytest 9.1.1, Windows build 26300; `.venv/Scripts/python.exe -m pytest
tests/test_canonical_outline.py tests/test_outline_legacy_differential.py
tests/test_fixture_geometry.py tests/test_envelopes.py -q -p no:cacheprovider`,
with the recorded absolute JUnit destination and PYTHONDONTWRITEBYTECODE=1.
Final wall duration 31.125 s, exit 0. Commands for red/targeted runs are in their
respective invocation files. All run input pre/post hashes match.

## Independent accounting reconciliation

Counts are conservative mathematical primitive envelopes, not CPU instructions,
allocation or elapsed time. Schema, metadata and ledger bookkeeping are excluded,
as before. Numeric transform operations are now explicitly included.

| Operation | Reservation and independent derivation |
| --- | --- |
| Area finalization | 4: absolute value, D*D, 2*(D*D), threshold comparison |
| Transform isometry envelope | 64 fixed: two squared column norms (4 multiply/2 add), dot (2 multiply/1 add), reflection involution (4 multiply/4 add), up to five `isclose` evaluations, parity/branch comparisons; conservatively covers both transform kinds |
| One endpoint apply | 8: `a*x+b*y+tx`, `c*x+d*y+ty`, four multiply and four add |
| Mapping batch | 16*N: both endpoints per edge, no deduplication; prepaid before any apply |
| Rectangle source validation | 2084 = 6*320 + 4*(8+16+16) + 4 |
| Rectangle identity transform | 4296 = 2*2084 + 64 + 8*8 |

The rectangle oracle is authored from the expressions and literal edge count,
never computed from observed production counters. Spies require eight apply calls.
Seeded ledgers retain the public cap 134217728 and preconsume a known literal
amount, leaving 0/63/127/128 primitives after successful source validation.
Tests prove: no mapping/output validation before successful reservation; whole
batch fails with 63 of 64 needed mapping primitives; exactly 128 allows the
64+64 transform stage then exhausts before any output contour arithmetic.
Every failure has no outline and `truncated=True`. Source validation completion
and phase entry are directly observed, not inferred from counters alone.

512-edge validation now reserves 41881604 (formerly 41881602); a two-pass,
512-edge single-ring transform would reserve 83771464, below 2^27. This is a
formula, not a measured worst-case performance claim. Pair/containment caps,
4382-bit bound, coordinate/metadata caps and 2^26/2^27 global budgets are unchanged.

## Historical provenance and preservation

[Historical manifest](historical-hashes.json) inventories all 26 files from
slice-a-01 plus 32 tracked preparation evidence files. All 58 match before/after
every remediation run and at delivery. No historical source, fixtures, logs,
oracles or review artifacts were overwritten.

The original 164 PASS run and four-test follow-up describe different source
revisions. Their manifests recorded hashes, but did not save complete per-run
source snapshots/patches. They must not be presented as a single consolidated
verification of later source. The follow-up only exercised the selected exhaustion/
truncation/transform-failure cases; it did not rerun the original 164 tests.
This remediation's consolidated result is the evidence for the repaired revision.
Snapshots here establish reconstruction for these runs only, not retroactive
coverage or independent reviewer acceptance of historical revisions.

Remaining limits: declared provenance is not source authentication; rounded
binary64 transform output is revalidated, not exact trigonometry; no importer or
publication. No new performance guarantee. P07/P08 remain PARTIAL and all 47
scenario statuses unchanged. Verdict: READY FOR INDEPENDENT RE-REVIEW.
