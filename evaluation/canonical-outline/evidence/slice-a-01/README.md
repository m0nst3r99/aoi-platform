# Slice A implementer evidence — 2026-11-16

Baseline: master `2ee201dfc62fd7363336a8b099e2886e039dd59a`. No commit/push.
This is bounded synthetic geometry evidence, not KiCad importer acceptance.

## Executed scope

All commands used `.venv/Scripts/python.exe -m pytest`, `-q -p no:cacheprovider`,
`PYTHONDONTWRITEBYTECODE=1`, repository cwd, and a distinct `--junitxml` file here.
No native KiCad, Windows runner, H249/H55 suite or full repository suite ran.

| Run | Test selection | Result | Pytest duration |
| --- | --- | --- | --- |
| [legacy-01](legacy-01.log) | `tests/test_outline_legacy_differential.py tests/test_fixture_geometry.py tests/test_envelopes.py` | 113 PASS, 0 FAIL/SKIP | 0.31 s |
| [canonical-01](canonical-01.log) | `tests/test_canonical_outline.py` | 39 PASS, 0 FAIL/SKIP | 26.46 s |
| [targeted-02](targeted-02.log) | `tests/test_canonical_outline.py tests/test_outline_legacy_differential.py` after added boundary/admission/differential cases | 65 PASS, 0 FAIL/SKIP | 26.10 s |
| [final-03](final-03.log) | Four files above; 46 canonical, 19 differential, 21 fixture, 78 envelope | 164 PASS, 0 FAIL/SKIP | 26.21 s |
| [exhaustion-04](exhaustion-04.log) | Canonical file, `-k 'work_exhaustion or truncation or transform_rejection'`, after making omitted-work truncation explicit | 3 PASS, 43 deselected, 0 FAIL/SKIP | 0.13 s |
| [exhaustion-05](exhaustion-05.log) | Same selection; added transform's two-pass exhaustion case | 4 PASS, 43 deselected, 0 FAIL/SKIP | 0.11 s |

Counts overlap; do not sum them as distinct tests. No failed test attempts occurred.
All intermediate logs/JUnit are preserved. Early runs are development checkpoints;
the final two recorded source states have explicit manifests, not retrospectively
claimed hashes for early development states.

[Main invocation](invocation.json) and [follow-up invocation](exhaustion-05-invocation.json)
contain exact argv/environment. Python 3.11.9, pytest 9.1.1, Windows build 26300.
Wall durations are 26.629 s and 0.465 s respectively; both exit 0.
[Main results](result.json) and [follow-up results](exhaustion-05-result.json)
list every parameterized test identity. Follow-up changes affect exhaustion
diagnostics only; unaffected main-run evidence remains applicable.

## Inputs, independent oracles and compatibility

[Before](pre-hashes.json)/[after](post-hashes.json) and follow-up
[before](exhaustion-05-pre-hashes.json)/[after](exhaustion-05-post-hashes.json)
each verify 16 source/test/config/baseline inputs plus 32 tracked historical
preparation evidence files unchanged during their run. These manifests do not
claim a pre-session hash inventory of every unrelated local-only artifact.
No existing historical evidence or fixture was edited. All new evidence is here.

- [Pinned baseline](baseline_outlines.py) is a byte copy of the pre-refactor
  outline source. SHA-256 `30f58e3d1368d1de01eeb1e304298baa057c0ec12a559c6e485dd0a010926240`.
  Differential tests load that source in a separate module, construct equivalent
  inputs independently, and compare bounds/curves or complete typed first failures.
  Cases include both circle directions, mixed/major arcs, invalid/open/overlapping
  polygons, frame/closure precedence, wrong types, holes and 512/513 edges.
- [Canonical tests](../../../../tests/test_canonical_outline.py) author literal
  outer/hole coordinates: net areas 200/192/188, perimeter 72 for one hole,
  concave L area 36; explicit transformed vertices for exterior and both holes.
  Test-only Fraction shoelace, orientation and projection-distance oracles are
  independent of production fixed-grid predicates. No Fraction in production.
- Topology controls include crossing holes without vertex containment, touching,
  nesting, overlapping, outside, repeated/open/degenerate rings; binary64
  nextafter values below/at/above clearance, edge and area thresholds.
- Immutability, source-reference preservation, reflection reversal, frame/revision,
  exact/over metadata/reference budgets, deterministic diagnostics, truncation,
  one-pass and two-pass atomic exhaustion are covered.

## Arithmetic and work interpretation

Q=2^1074; |coordinate|<=1e6 gives grid magnitude <2^1094 and differences
<2^1095. Determinants/dots/norms are <2^2191; squared determinants <2^4382.
Anchored doubled area over <=512 edges is <2^2200. D=binary64(1e-8)*Q
is <2^1048, so D²*length² <2^4287. Every predicate sum/product checks
magnitude before evaluation; 4382 bits is never raised.

Kernel accounting reserves conservative mathematical primitive envelopes before
execution, not measured CPU instructions: pair 320 (64 multiply, 128 add/sub,
128 compare), containment edge 16, grid conversion 8/edge, edge 16, area 16/edge
plus 2/ring. Accounting/bit checks and Python allocation are not CPU/RSS guarantees.
No retained all-pairs list. At 512 edges the independent oracle requires 130816
pair visits and 41881602 reserved primitives. At 32 rectangular holes and one
exterior: 8646 pair visits and 4096 containment visits. Limits remain 130816 pairs,
16384 containment visits and 2^26 primitives per validation; transform uses one
ledger for two passes with exactly doubled caps. Exhaustion fails atomically and
marks diagnostics truncated because further checks are omitted.

Metadata: IDs 256 UTF-8 bytes, details 1024, aggregate 256 KiB, references 1024
occurrences. Diagnostic retention reserves 4096 bytes/slot, 31 ordinary slots
plus one exhaustion slot (128 KiB maximum). Output size is bounded by admitted
ring/edge/reference/metadata counts; no general-purpose output serializer is added.

## Assurance limits

Line-only, one exterior and <=32 cutouts, <=512 total edges. No repair/snap or
hole loss. Canonical winding CCW exterior/CW holes; cutouts sorted by ID and ring
starts lexicographically normalized. Source references are declared, not file
authentication. Transform2's existing unit-isometry/convention check is reused;
topology is revalidated exactly on rounded binary64 outputs, not exact trigonometry.
Legacy public constructors, arc semantics, fixture/capacity behavior and transform
APIs are preserved. No implicit adapter that discards holes is exposed.

Ready for independent audit of this bounded slice, not acceptance of all P07/P08.
All 47 scenario statuses and normative task checkboxes remain unchanged.
