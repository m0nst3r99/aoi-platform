# Geometry Core implementation evidence

## Current review acceptance - 2026-10-19

The user relayed acceptance of the inventory byte-admission slice after direct code review from the inventory ZIP: reviewer results were 370 passed, 1 skipped plus 1,200 independent cases passing. These are reviewer-reported results conveyed by the user, not new agent executions or an agent verification of the independent cases. The reviewer did not rerun the REAL-PCB-01-r1 bundle test; the earlier local agent result remains separate evidence.

Review of Sprint 1 exit for the agreed affine/DAG and line/arc/rectangle subset, and review of decisions 1.1/1.2, are accepted in chat as reported by the user. Distinguish that review acceptance from the user's confirmation/instruction to record it; no signature, attestation or blanket normative-conformance approval is created. Earlier review-pending statements are historical and superseded by this section. Checkboxes are unchanged by this documentation-only update; 1.1/1.2 review is no longer a blocker. Aggregate tasks with outstanding obligations, including 3.4/5.1, stay PARTIAL/open. Neither Foundation acceptance level nor parser compatibility is achieved.

Next work is to propose/evaluate KiCad reader reuse under 1.5/5.2, before choosing a reader; no parser implementation or new evaluation is performed in this documentation update.

## Artifact inventory slice - 2026-10-19 (tasks 3.4/5.1 PARTIAL)

The user explicitly authorized only byte inventory, with the accepted gate 7.1 left intact. [inventory.py](../../../src/aoi_platform/inventory.py) implements `inventory_artifacts(InventoryManifest, ByteSources, InventoryLimits)`. Frozen declaration/observation records separate claimed metadata and provenance from measured bytes/EOF/full SHA-256. Success has an inventory and scoped report; failure has only diagnostics and non-usable observation evidence. Geometry/profile semantics, revision equivalence and inspection readiness are never inferred from a matching hash.

Profile/side role coverage follows design.md: geometry needs PCB; SPI needs Paste per requested SPI side; post-placement needs BOM/placement per assembly side; combined needs both. Multiple artifacts per role are allowed with unique IDs. Reference-only artifacts are hashed but cannot fulfill roles. Metadata key conflicts, schema/digest errors, duplicate IDs, missing roles/sources, I/O errors and hash/size conflicts reject. Diagnostics reuse ContractError/ValidationReport without changing geometry behavior; import/I/O ErrorCode members are additive. Artifact-ID traversal and report serialization are deterministic under input reordering, and repeated meaningful errors remain present.

Sources are explicit trusted binary-stream factories; ownership transfers to inventory for one close attempt. Streaming SHA-256 uses explicit count/per-file/total/chunk limits, with at most one sentinel byte beyond a byte budget to distinguish EOF. All returned bytes from failed reads count; unsafe resource/protocol/close failures stop further I/O. Partial evidence never supplies a full digest. No filesystem/URL/archive adapter, reader/parser, reconciliation or publication is implemented.

Executed evidence:

- [test_inventory.py](../../../tests/test_inventory.py): 75 portable synthetic cases, literal known SHA-256 oracles, all profile coverage combinations, reference-only, schema/source/hash/size failures, exact/exceeded budgets and chunk ceiling, short reads, ownership, independent errors, determinism and failure without inventory.
- Full `.venv/Scripts/python.exe -m pytest -q`: **370 passed, 1 skipped in 0.66s**, exit 0. All 295 prior tests remain. The single skip is the opt-in local fixture test, not a skipped inventory contract case.
- [test_inventory_local.py](../../../tests/test_inventory_local.py), with `AOI_REAL_PCB_01_ROOT` pointing to the accepted REAL-PCB-01-r1: **1 passed in 0.20s**, exit 0. The API streamed all 25 SHA256SUMS entries (2,454,516 bytes), matched declared hashes, retained reference-only B.Paste, and read population evidence (57 footprints, 28 assembly references, 3 retained fiducials). These are byte/declaration checks, not renewed acquisition review or parser evidence. No fixture bytes copied or edited; the normal suite has no C:/dev dependency. Root-checked, explicit path factories exist only in this opt-in test.
- `openspec validate board-geometry-foundation --strict`: valid, exit 0. `git diff --check`: exit 0, no whitespace errors (LF/CRLF notices only); the three new code/test files were also checked for trailing whitespace. The editor test tool did not discover pytest tests, so the repository virtual-environment pytest command supplied the executed test evidence.

Task 3.4 remains PARTIAL: artifact/provenance admission is evidenced; parsed entity records and entity-level identities remain open. Task 5.1 remains PARTIAL at the full import boundary: bounded byte inventory/required-role/profile declarations are evidenced; integration with parsed candidates, complete ImportManifest semantic validation and later profile coverage/publication remain open. No checkbox changed. Reader/API evaluation, format support and geometry work are outside this authorization. Trusted factory blocking/timeouts and process-level memory enforcement are not provided by this synchronous byte API; factories must honor the protocol. SHA-256 is observation evidence, not a trusted-source signature.

## Historical gate 7.1 closure - accepted REAL-PCB-01-r1, 2026-10-18

Task 7.1 alone is promoted in this update. The local agent inspected files/export commands and reverified all 25 SHA-256 entries. The user confirmed external review of the forwarded preparation report and authorized acceptance. External reviewers did not directly verify bundle bytes; no third-party signature/attestation is created. See [supported-inputs.md](supported-inputs.md) for snapshot, authority, UUID population, conventions, warnings and hashes. The fixture is untouched; its pre-acceptance review-pending text remains historical.

This supersedes acquisition-TBD/report-review-pending statements only. It does not close Sprint 1 decisions 1.1/1.2, accept Sprint 1 exit, verify parser compatibility or authorize Sprint 2 implementation. All other open tasks remain open to their full contracts. Existing diagnostics test results below are historical evidence, not rerun by this documentation update.

Closure verification: all 25 bundle SHA-256 entries match; strict OpenSpec validation passes; git diff --check has no whitespace errors (working-copy LF/CRLF notices only). Only documentation changed, so pytest was not rerun. See sprint-plan.md for the proposed bounded-inventory API and KiCad API reuse assessment; neither is implemented.

## Diagnostics/evidence slice from 2980f65 — historical pre-review report

The user authorized only Sprint 1 diagnostics/resolver evidence and documentation reconciliation. The existing 268-test baseline passed before adding regression cases. No normative capability requirement or task checkbox was changed. The sections below the historical divider are retained as history and must not be read as the current missing-work list.

Implemented:

- [errors.py](../../../src/aoi_platform/geometry/errors.py) retains an immutable diagnostic payload behind the compatible GeometryError/ValueError interface: code, message, field_path, sorted immutable context and separate expected/actual values. Exception traceback mechanics remain available. [models.py](../../../src/aoi_platform/geometry/models.py) supplies full frame mismatch snapshots and role-prefixed known metadata.
- [resolver.py](../../../src/aoi_platform/geometry/resolver.py) retains source/target/domain/policy and graph budget evidence on failures. Known candidate paths and failing unvalidated transform IDs are carried where available. Graph metadata conflicts use stable transform-ID ordering; source/target mismatches preserve both records, and nonadjacent context conflicts retain all conflicting known values. No guessed identity or usable result is returned on failure.
- Path diagnostics have their own explicit bound: 32 path entries, 128 IDs total, 8192 UTF-8 encoded-ID bytes per summary. Omitted counts are explicit; registry inventories are labeled as inventories, not inferred paths. If graph size already exceeds the resolution budget, diagnostics report omitted edge count without scanning/sorting the registry. Search/comparison limits are unchanged; bounded diagnostics do not imply partial resolution success.
- [envelopes.py](../../../src/aoi_platform/geometry/envelopes.py) enriches errors before FitReport creation with known outline/report/capacity, source/load/target, envelope/configuration and numerical policy evidence. Role prefixes preserve conflicting machine/frame values. Unknown metadata is absent, not manufactured.
- [reports.py](../../../src/aoi_platform/geometry/reports.py) automatically adapts retained evidence and expected/actual values without caller reconstruction. Additional caller evidence is validated; conflicting values reject rather than overwrite. Existing deterministic issue sorting/serialization and failure codes/field paths are preserved.

New [test_diagnostics.py](../../../tests/test_diagnostics.py) has 27 cases: missing paths; absent metadata; full source mismatches; nonadjacent machine/revision/capture conflicts; unvalidated mapping; literal noncommuting graph oracles (8,1) versus (-2,11); origin-equal/corner-disagreeing affine paths; individually valid edges producing ill-conditioned or underflow-singular products; graph/comparison budget failures; large path/long-ID diagnostic omissions; stable reports under reordered registrations, including conflicting metadata; immutable errors and adapter overwrite rejection; pre-report fit failures and conflicting fixture/travel contexts; invalid report identity adaptation and duplicate registry ID retention. Tests call the public APIs and adapt errors without resupplying context. All prior tests remain intact.

Executed full suite after final code/tests: `.venv/Scripts/python.exe -m pytest -q` **295 passed in 0.55s**, exit 0. `openspec validate board-geometry-foundation --strict` reported **valid**, exit 0; `git diff --check` passed, exit 0, with only LF/CRLF working-copy warnings. Passing tests do not declare Sprint 1 exit or either Foundation acceptance level.

### Per-task review ledger: Sprint 1 evidence versus later obligations

| Task | Sprint 1 evidence now available | Still open / later obligation |
| --- | --- | --- |
| 1.1 | Preserved conventions and four literal forward plus four inverse checkpoints in test_transforms; review accepted in chat per user update | Review is no longer pending; checkbox unchanged in this status-only update |
| 1.2 | Separate contracts and agreed subset review accepted in chat per user update | Physical dimensions/qualification remain TBD, not a missing Sprint 1 review; checkbox unchanged |
| 3.1 | Finite immutable point/frame/affine records; explicit units/origin/axes and required context by frame kind | Broader image/projective/calibration/load models belong to S5; imported source metadata to S2–4 |
| 3.2 | Capacity, fixture and camera-travel identities/versions/context/evidence; standalone unknown geometry remains unresolved | Narrow standalone record checklist has evidence; broader geometry/import integration is not automatically a missing record requirement |
| 3.6 | Immutable structured diagnostics, automatic resolver/fit evidence retention, expected/actual conflicts, source-location and stable multi-issue report tests | Parser collection and publication rollback S2–4; inspection boundary S5. No claim of an implemented import collector |
| 4.1 | Independent inch/mm and reverse conversion oracles | Already checked; imported normalization integration remains separate |
| 4.2 | Reflection, bottom orientation/parity and explicit no-auto-mirror tests | Already checked; real footprint integration S2 |
| 4.3 | Rotation/translation stage oracles, vector orientation, angle wrapping | Already checked; component import integration later |
| 4.4 | Noncommuting composition, literal inverse checkpoints, seed-1007 scalar oracles/round trips | Already checked; projective/lens round trips S5 |
| 4.5 | Directed affine DAG, all candidate corners/pairs, exact path context, budgets, invalid products and structured failure evidence | Camera/projective/active-stale-load lifecycle S5; cycle-capable graphs outside selected resolver subset |
| 4.15 | Exact 280x550, explicit rotated 550x280, 0.001 mm overrun, placement independence and analytic arc bounds | Selected S1 acceptance evidenced; broader imported outline/cutout support remains open in import/general geometry scope |
| 4.16 | Selected rectangle/line/arc fit, contact, margins, crossings/containment, arc extrema and capacity-pass/fixture-fail | Wider geometry not silently supported; physical qualification not claimed |
| 4.17 | Standalone missing envelopes and camera rectangle remain unresolved, no motion/targeting | Import-success/publication scenario still requires S2 integration; REVIEW construction S5 |

Status distinction: only 4.1–4.4 remain checked (4/63). Other rows can have sufficient selected Sprint 1 evidence without closing their complete task/capability obligations. This ledger is submitted for review, not an exit declaration. No parser, camera/calibration lifecycle, new geometry subset, commit/push, ZIP review or agent configuration modification was introduced.

## Historical implementation entries — superseded as current status

All following sections are historical snapshots. Their test counts, “pending” statements and “current/latest/remaining” headings describe their original deliveries only. In particular, resolver absence, pending fixture policy, missing fixture API and missing report-container statements no longer describe HEAD plus this slice. Their broader normative open obligations remain in force; use the per-task ledger above for current scope.

## Current result: selected fixture-fit subset implemented (base 1132718)

This section supersedes the pending-policy and incomplete fixture-API statements in the historical entries below. The user selected both contact/margin semantics and the initial supported geometry set. Those decisions were written to [design.md](design.md) before connecting the kernel to the API. Normative capability specs and original task descriptions were not changed.

- [envelopes.py](../../../src/aoi_platform/geometry/envelopes.py) now evaluates full loaded outlines through `validate_fit`. The usable region and all exclusions must be axis-aligned rectangles in the exact M frame; nonrectangular supplied regions reject with `GEOMETRY_UNSUPPORTED` during record validation even if load/margin/usable geometry is missing. Board contours remain the bounded line/circular-arc subset. Missing geometry, margin or explicit load yields separate unresolved reasons instead of a guessed pass.
- Outer contact at zero margin passes. Exclusion crossing, touching and either direction of containment fail. Positive margins use minimum Euclidean clearance to both boundaries. The kernel uses analytic full-contour extrema and curve distance/intersection plus containment tests; no chord approximation, vertex-only exclusion check or board bounding-box substitution is used. Only validated proper-rigid loads with exact source/target frames and compatible revision/machine/capture context can reach evaluation. Capacity-test orientation remains independent of load rotation/translation.
- `fixture-binary64-v1` records a 1e-8 mm arithmetic guard in report context. Outer clearance and margin checks allow at most this guard; exclusion separation <=1e-8 mm is conservatively treated as contact. Tests demonstrate that 0.001 mm overrun/shortfall is not lost. This is synthetic numerical evidence, not physical clearance certification or manufacturing tolerance.
- Fixture failures return structured `BOARD_OUT_OF_ENVELOPE` violations with outline, region, envelope/version, fixture/configuration, machine/frame, load, policy/margin and available revision/capture context. Violations are ordered by usable region first, then exclusion ID; evidence IDs are sorted. Reordering exclusions produces an identical report. Passes retain record versions/evidence and known capture context. Camera reachability remains unresolved even with a travel rectangle; motion/targeting remain false and synthetic evidence is not promoted to qualification.

Executed evidence: 30 additional API cases in [test_envelopes.py](../../../tests/test_envelopes.py), retaining the previous suite and updating the obsolete pending-policy test to require unresolved status without a load. Cases cover exact outer contact; translation and positive-margin fixture failures with capacity pass; exclusion edge/corner contact, crossing with outside vertices and both containment directions; exact/0.001 mm-short outer and exclusion margins; 3-4-5 corner clearance; interior arc extrema, tangent exclusion and arc margin; composed rotation plus translation independent of capacity rotation; concavity; wrong full frame/machine/revision/capture; unvalidated load; unsupported region rejection; missing margin; supplied travel/no targeting; preserved evidence and deterministic diagnostics. Earlier tests retain missing geometry, invalid topology, nonfinite input, unsupported holes/splines and required capacity oracles.

Validation after code/tests: `.venv/Scripts/python.exe -m pytest -q` **268 passed in 0.42s**, exit 0. After documentation updates, `openspec validate board-geometry-foundation --strict` reported **Change 'board-geometry-foundation' is valid**, exit 0; `git diff --check` exited **0**, with only LF-to-CRLF working-copy warnings. No existing tests were removed; no commit/push, ZIP review or agent configuration change was made.

Ledger: **3.2, 4.15, 4.16 and 4.17 remain PARTIAL/open**. The selected standalone record/capacity/fixture scenarios now have evidence; broader normative outline/envelope support (holes, other curve/region types, general imported geometry) remains unsupported with typed rejection, not waived. Task 4.17 import-success integration is not implemented. Physical qualification, calibration and camera reachability remain unresolved/out of this slice; synthetic fixture pass does not establish readiness. All four original checkboxes remain unchecked; overall task count stays **4/63**, and neither Foundation acceptance level is achieved.

## Resumed capacity slice: independent fixture geometry, still incomplete

Existing work from base `1132718` was preserved. On resumption the capacity/record suite passed 217 tests. Added [fixture_geometry.py](../../../src/aoi_platform/geometry/fixture_geometry.py) as an internal policy-independent kernel: analytic point location for line/arc contours, curve-to-line Euclidean minimum distance, validated proper-rigid outline loading, exact recognition of axis-aligned rectangles, and whole filled-outline/rectangle overlap and separation. Arc extrema are evaluated analytically, without chord sampling. Rectangle recognition rejects other polygons rather than substituting their bounding boxes. These helpers inherit the bounded outline kernel and its 1e-8 mm numerical boundary guard; they do not select physical contact or margin semantics.

The 21 cases in [test_fixture_geometry.py](../../../tests/test_fixture_geometry.py) use independent geometric oracles: clockwise/counterclockwise circle containment, concavity, edge crossing with all vertices outside the rectangle, a rectangle completely enclosed by a board, interior arc overlap and minimum distance, 3-4-5 and circular corner distances, overlapping boundaries, loaded arc extrema after translation/rotation, unsupported nonrectangular regions, wrong full-frame context and unvalidated mapping rejection. These establish helper behavior, not a completed fixture-fit check. One newly added guard test initially failed during test setup because it reused a frame ID with conflicting metadata; giving its intended target a distinct ID allowed the test to exercise the unvalidated-mapping gate as intended.

Final executed checks after adding the helpers: `.venv/Scripts/python.exe -m pytest -q` **238 passed in 0.38s**, exit 0; `openspec validate board-geometry-foundation --strict` **valid**, exit 0. The editor test runner found no tests, so verification used the repository virtual environment directly. All existing tests were retained. `git diff --check` was run after documentation updates; see delivery for its result.

Still pending: contact/margin semantics and approval of the proposed initial fixture geometry support matrix, described below. `validate_fit` still rejects supplied fixture geometry with `POLICY_INVALID`; there is no completed capacity-pass/fixture-fail path yet. No API policy, normative requirement or task checkbox was changed on the basis of these helper tests. Tasks 3.2/4.15/4.17 remain PARTIAL; 4.16 remains OPEN with preparatory kernel evidence only; overall completion remains 4/63. Import integration and all camera reachability remain open. No commit/push, ZIP review or agent-configuration modification was performed.

## Current slice from 1132718 — capacity and envelope records; fixture decisions pending

User-authorized tasks: 3.2, 4.15, 4.16, 4.17. Starting HEAD verified as `1132718`; tracked worktree was clean. No repository AGENTS.md was found; the existing apply skill and OpenSpec context were read. Change schema is spec-driven, apply state ready, initially 4/63 tasks complete. No normative requirement, ZIP review or agent configuration was edited. No commit/push or parser/import implementation was performed.

Implemented independent subset:

- [outlines.py](../../../src/aoi_platform/geometry/outlines.py): immutable line/circular-arc primitives and one simple closed mm contour; exact endpoint connectivity, finite point/context checks, analytic line/arc intersections for self-intersection rejection, positive absolute enclosed area, analytic directional extrema including points inside an arc. Full circles may be represented with two arcs. Holes/multiple contours, unsupported primitive types, >512 edges and coordinates/radii >1e6 mm explicitly reject. This is a bounded standalone kernel, not a full imported Polygon2/hole model.
- [envelopes.py](../../../src/aoi_platform/geometry/envelopes.py): BoardCapacity identity/version with fixed 280 x 550 mm; explicit capacity-test rotation and complete contour extents; separate FixtureEnvelope and CameraTravelEnvelope records with identities/configuration/frame/region/exclusions/evidence; immutable synthetic/qualified evidence declarations with separate qualification references required for qualified data. None is used for unknown geometry/margin, never a manufactured physical default.
- `check_capacity` returns structured `BOARD_CAPACITY_EXCEEDED` violations with outline/revision/frame/capacity identity and orientation. Exact quarter-turns use signed permutations. Other angles use analytic projection. Numerical policy `capacity-binary64-v1` records an arithmetic guard `min(1e-8,16*ulp(max(550,abs(projected bounds))))` mm, not a production or hardware tolerance. Topology predicates use a separate 1e-8 mm numerical guard. The tested 0.001 mm overrun cannot be swallowed by either guard.
- `validate_fit` currently computes capacity and reports missing fixture geometry and all camera reachability as unresolved. Supplied travel geometry still does not prove reachability. It checks supplied load conventions, rigid kind, exact source/target frames and known revision/machine/capture conflicts. FitReport retains reasons, evidence IDs, record IDs/versions and available context; motion_authorized and targeting_ready remain false. It does not run import gates or certify production evidence.
- Known fixture geometry is deliberately rejected with `POLICY_INVALID` while fixture policy is pending. This is an incomplete operation, not a fixture-fit implementation. It does not return a guessed pass or hide missing checking as successful geometry validation.

Decisions asked of the user and still pending at this handoff:

1. Contact/margin semantics: proposed usable boundary contact allowed at zero margin; exclusions closed (touch fails); Euclidean minimum margin from both outer boundary and exclusions. Existing specs mention margins/exclusions but do not specify these contact semantics. No such policy has been installed as normative or silently assumed.
2. Initial supported fixture region set: proposed rectangles aligned with machine frame axes, with rectangular exclusions and line/circular-arc board outlines; wider polygon envelopes, holes and other curves would require further kernel work. This proposed fixture subset has not been accepted or implemented. The independent outline/capacity code above must not be mistaken for an approved fixture support matrix.

Evidence in [test_envelopes.py](../../../tests/test_envelopes.py), 48 new cases:

- Required capacity oracles: 280 x 550 at 0 degrees passes; 550 x 280 at 90 degrees passes and at 0 fails; 280.001 x 550 fails; additional height overrun, negative/180-degree orientations and independent 45-degree square-root oracle.
- Machine load translations (0,0), (1000,-900), (-23,12) leave the entire capacity result unchanged.
- Arc oracles: semicircle extrema, two-arc circle, clockwise major arc, and an arched outline with every endpoint below y=500 but actual y maximum 600; capacity correctly fails against 550. No endpoint-only sampling.
- Invalid open/self-crossing/retraced/touching contours, inconsistent arc radii, arc/line intersection, nonfinite coordinates/angles, unsupported primitive/hole/unit/numeric-domain cases reject.
- Missing physical records/geometry remain unresolved; supplied travel rectangle remains unresolved with identity/evidence/context retained; synthetic evidence is not promoted; malformed records, conflicting machine/revision/capture, wrong load source, unvalidated map and affine scale-as-load reject.

Baseline: `.venv/Scripts/python.exe -m pytest -q` reported **169 passed in 0.35s**, exit 0. After this independent subset: **217 passed in 0.46s**, exit 0 (all prior tests unchanged, 48 new cases, no skips/failures). Strict validation reported **Change 'board-geometry-foundation' is valid**, exit 0. Final `git diff --check` is recorded in the delivery.

Task evidence/status: **3.2 PARTIAL** (records and unresolved states evidenced, fixture-region support decision pending); **4.15 PARTIAL** (listed capacity oracles evidenced for the bounded contour subset, not full outline/hole support); **4.16 OPEN** (no fixture fit algorithm yet); **4.17 PARTIAL** (standalone unresolved/no-readiness behavior evidenced; import-success integration explicitly out of scope and open). All four checkboxes remain open; count remains **4/63**. Missing mandatory fixture tests: capacity-pass/fixture-fail by translation/margin/exclusion; edge crossing exclusion with exterior vertices; full loaded-arc fixture checking. Passing capacity/model tests does not establish those behaviors or complete Sprint 1/Foundation milestones.

## Latest review corrections — four resolver defects

The previous resolver delivery's claims about complete source matching, resource-bounded graph processing and validating every candidate's corners were incomplete. This review correction supersedes those claims with the following executed evidence; earlier sections are historical snapshots.

Only [resolver.py](../../../src/aoi_platform/geometry/resolver.py), new [test_resolver_review_regressions.py](../../../tests/test_resolver_review_regressions.py), and this report were changed in this correction. Existing numerical transform logic, report implementation, normative specs and selected consistency policy were preserved.

- A candidate's first `from_frame` must equal the complete requested source record, with `CONTEXT_MISMATCH` at `resolve.source` on failure. Regression variants cover same ID with different origin, units, axes, revision, machine and capture. Target matching and path-wide context checks remain active.
- Constructor input now rejects duplicate transform IDs, including repeated identical records. `register()` uses the same constructor validation and preserves all resource limits.
- Cycle detection uses iterative Kahn processing over the whole graph, including disconnected components. Path enumeration uses an explicit iterator stack and mutable prefix, without recursive Python calls or copying every prefix. A 1,100-edge chain with `max_edges=1` fails with `TRANSFORM_RESOURCE_EXHAUSTED`; at 1,100 it resolves to the independent translation oracle (2,3) -> (1102,3). A 1,101-edge cycle returns `TRANSFORM_CYCLE_UNSUPPORTED` with sufficient budget.
- Resolution checks graph size before metadata indexing, sorting or cycle detection. `max_edges` bounds graph size, cycle-edge passes, traversal edge visits and total candidate edge occurrences as separate per-phase budgets. Thus metadata/indexing work is bounded by graph size and context/composition work by candidate edge occurrences. Constructor record/type/ID validation remains linear in supplied input records; it does not perform graph search. Oversized registries may be constructed but cannot resolve.
- New `max_comparisons` (positive integer, default 100,000) bounds unordered candidate pairs. The exact required pair count is checked before composition/corner evaluation/comparison. Each pair uses four cached-corner distances; 10,000 paths would require 49,995,000 pairs and therefore fail under the default budget. Tests cover two-pair rejection/three-pair acceptance, invalid limits, preservation through registration, and default-budget rejection for 450 paths (101,025 pairs). Separate shared-prefix and shared-suffix tests prove candidate and traversal work exhaustion cannot return partial results.
- Every candidate is evaluated at all four source rectangle vertices once, including a sole path; comparison reuses those outputs. A translation of 1e308 over x=[1e308,1.5e308] fails with the existing typed numeric `SCHEMA_INVALID`, as does overflow that occurs only at later corners. Instrumented one-path and three-path tests verify exactly four evaluations per candidate, with all four distinct vertices.

Regression-first evidence: before implementation changes, the initial new regression file reported **13 failed in 2.49s**, exit 1. Failures included six unreported source mismatches, two accepted duplicate-ID cases, two `RecursionError` cases, missing comparison-budget API, accepted single-path overflow, and repeated corner evaluation. After fixes and added budget boundary/deep-cycle regressions, all **24 new cases passed**. All 145 prior cases remain unchanged.

Final verification: `.venv/Scripts/python.exe -m pytest -q` reported **169 passed in 0.37s**, exit 0, no failures/skips. `openspec validate board-geometry-foundation --strict` reported **Change 'board-geometry-foundation' is valid**, exit 0. `git diff --check` passed; Git emitted only existing LF/CRLF normalization notices. These are actual executed results, not full requirement acceptance.

Tasks **3.6 and 4.5 remain unchecked/PARTIAL**; the four corrections do not close the outstanding original-task evidence or import/calibration contracts recorded below. No normative scope was weakened; no commit/push, agent configuration or review ZIP edit was performed. Foundation Prototype and Foundation Complete remain unachieved.

## Historical slice — structured reports; resolver pending clarification

2026-10-17, starting HEAD `df9e0a0`. User authorized tasks 4.5 and 3.6 only; envelope/capacity, parsers, camera/calibration and Sprint 2 remain outside this slice. No commit or push performed. No normative requirement was changed.

- Added [reports.py](../../../src/aoi_platform/geometry/reports.py): immutable ContractError, SourceLocation and ValidationReport, explicit identifiers/context, diagnostic expected/actual text, source coordinates, remediation, policy/check evidence and deterministic serialization. Existing GeometryError now retains its raw message for lossless adaptation; previous exception signature/string and numeric behavior remain unchanged.
- Added [test_reports.py](../../../tests/test_reports.py): 16 cases, including two independently discoverable invalid numeric rows, source/entity/context retention, all permutations of three issues with a sort-key tie, duplicate retention, evidence ordering, warning/blocking separation, rejected digest protection and immutable/invalid metadata.
- Updated public exports and [README.md](../../../README.md) with the implemented subset and producer responsibilities. Report order is a documented implementation convention, not a previously specified normative key: canonical JSON of each complete issue with sorted keys; all issues retained. This does not define import digest serialization.
- Baseline full pytest actually reported **120 passed in 0.14s**, exit 0 (the historical 104 count below is not the current baseline). After this slice: **136 passed in 0.20s**, exit 0. All existing tests remain unchanged. Strict validation: `openspec validate board-geometry-foundation --strict` reported **Change 'board-geometry-foundation' is valid**, exit 0.

**3.6 remains PARTIAL/open.** Geometry report containers and deterministic ordering are implemented, but the complete design section 6 error vocabulary, typed policy/check results and collection/integration for ValidateImport/NormalizeBoard/BuildInspectionInput are not implemented. The report preserves supplied errors; it does not discover parser errors or publish revisions. Its accepted status means no blocking issue was supplied, not that all import gates ran. Expected/actual payloads are diagnostic text in this subset. The normative "Multiple errors and rollback" scenario remains OPEN; the synthetic numeric-row test does not establish BOM parsing or atomic rollback.

**4.5 remains OPEN.** No graph resolver was added. Design section 5 requires multiple paths to agree "within tolerance" but does not define the metric, comparison domain, or numerical threshold for affine-path equivalence. Round-trip tolerance is not automatically a bound on disagreement of two maps over an unbounded plane. Neither capability spec nor design specifies whether identity cycles are allowed, the treatment/error code for nonidentity cycles, or whether resolution synthesizes inverse edges versus traversing registered directed edges only. These affect which requests succeed and were asked of the user before implementation. No first-path selection, identity fallback, invented cycle rejection rule or implicit inverse policy was added. Requested new resolver tests (multistep direction/order, missing/ambiguous path, intermediate context, cycles and unvalidated edges) await that contract; existing direct-operation regressions still pass and are not claimed as graph evidence.

Task count remains **4/63 complete, 59 open**. Existing units/axes/origin/context/conventions_validated logic was untouched. No ZIP review or agent configuration content was edited. Foundation Prototype and Foundation Complete remain unachieved. Sections below retain the earlier implementation history.

## Resolver continuation — 2026-10-17

The user then selected the missing resolver policy. [resolver.py](../../../src/aoi_platform/geometry/resolver.py) adds immutable `PathConsistencyPolicy` (`synthetic-path-consistency-v1`, version `1`, default `1e-6 mm`), finite physical `RectangleDomain`, `TransformGraph`, and `ResolvedPath`. The graph accepts only explicitly registered directed affine edges; no inverse edge is synthesized. A caller may register an explicit `Transform2.inverse()` result. The graph is required to be acyclic and returns `TRANSFORM_CYCLE_UNSUPPORTED` for any cycle. It enumerates all eligible paths, rejects `TRANSFORM_MISSING`, `TRANSFORM_AMBIGUOUS`, `TRANSFORM_RESOURCE_EXHAUSTED`, invalid domain/policy, and unvalidated edges; it never returns a partial search.

Each path composes in declared direction and is checked with every source-domain rectangle corner. Pairwise output Euclidean differences are converted from target mm/inch to mm and compared to the selected policy tolerance. The representative is the lexicographically smallest transform-ID sequence; `ResolvedPath` records all examined path IDs, policy and domain. Context is checked across every frame in each candidate path, including blank intermediate metadata, so conflicting machine/revision/capture identities cannot be bridged. Pixel/image frames remain outside this resolver.

New independent tests in [test_resolver.py](../../../tests/test_resolver.py) cover multi-step order, two agreeing paths, disagreement at a bounded corner domain, target-unit-to-mm consistency, missing domain/policy/pixel, cycle rejection, no implicit inverse, explicit registered inverse, blank intermediate context conflicts, unvalidated edges and resource exhaustion. Full suite now reports **145 passed in 0.16s**, exit 0; strict OpenSpec validation remains **valid**, exit 0.

**Task 4.5 remains PARTIAL/open:** this slice evidences the newly selected resolver policy and directed affine path behavior. The original normative requirement still names singular/ill-conditioned path rejection and broader transform lifecycle/context contracts; camera/projective paths, calibration/load lifecycle and other later tasks remain open. The current resolver does not claim those later capabilities or alter their requirements. **Task 3.6 remains PARTIAL/open** as previously documented; report integration with import parsers and atomic revision rollback is not implemented.

Date: 2026-10-17 (Asia/Bangkok). Workspace: `C:\dev\aoi-platform`, verified by creating, reading and removing a dedicated write probe there before implementation. The user authorized only the first Geometry Core subset, not the full Sprint 1 plan or all 63 tasks. Neither Foundation Prototype nor Foundation Complete is achieved.

## Delivered files and behavior

- `pyproject.toml`: Python >=3.11 package metadata, standard-library runtime, pytest test extra and src-layout test configuration.
- `README.md`: API conventions, test commands, numerical limits and explicit remaining scope.
- `src/aoi_platform/__init__.py`, `src/aoi_platform/py.typed`: package and typing marker.
- `src/aoi_platform/geometry/{__init__,errors,models,angles,transforms}.py`: public exports, typed errors, immutable Point2/Frame, angles and immutable affine Transform2.
- `tests/conftest.py`, `tests/test_models.py`, `tests/test_angles.py`, `tests/test_transforms.py`: synthetic fixtures, independent expected values and negative cases.
- This evidence document plus proposal/design/sprint-plan/tasks status updates. Normative capability requirements and transform equations are unchanged.

The core checks complete intermediate Frame records, rejects conflicting known revision/machine/capture metadata, and never infers a source origin from metadata names. Source frames may represent future panel/unit datums without a new subsystem. This does not implement a frame registry, path search, load/calibration lifecycle, board revision storage or cross-machine processing service.

Affine transforms retain IDs, endpoints, units via frames, immutable matrix, kind, derived parity, condition metric and provenance. Composition/inversion record their parent IDs. Physical-to-pixel mapping and projective matrices reject explicitly. Direct affine algebra is available for declared matrices; there is no board-import fitting or automatic scale-to-extents behavior. Bounded valid regions and full Transform2/calibration contracts remain partial.

## Executed tests

Runtime observed: Python 3.11.9; pytest 9.1.1 in the existing project `.venv`. No runtime/test packages were installed or upgraded.

Command, executed from the workspace:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Initial implementation result: **78 passed in 0.13s**, exit code 0. No failed or skipped tests. Earlier incremental runs passed 40 model/angle tests, then 77 tests before adding the condition-threshold boundary case. These are software synthetic tests only. The review-correction results and available line-coverage check are recorded below; no static-type-checker result or branch coverage is claimed. Editable installation/wheel distribution was not tested.

| Behavior / specification scenario | Independent evidence | Task status |
| --- | --- | --- |
| Point/frame validation | `test_models.py`: finite numbers, immutable records, explicit enum/datum/context checks, PCB/machine/image conventions | 3.1 PARTIAL; full models/contracts open |
| Unit conversion and intermediate oracles | `test_required_chain_and_independent_inverse_checkpoints`: literals (25.4,50.8), (25.4,-50.8), (50.8,25.4), (60.8,45.4), inverse checkpoints; independent mm-to-inch test | 4.1 DONE |
| Bottom reflection and direction/parity | `test_bottom_reflection_preserves_angle_and_parity_semantics`: x=5 maps (2,3) to (8,3), 0 degrees to 180/reflected, 30 to 150, inverse restores angle/parity; bottom-name identity test | 4.2 DONE |
| Rotation, translation, angle wrapping | `test_angles.py`, required chain, direction-vector checks; 359.95 -> 0.02 gives +0.07; antipodal tie -180 | 4.3 DONE |
| Composition/inversion order | `test_noncommuting_transforms_apply_inner_first`: rotate-then-translate gives (8,1), reverse order (-2,11); shear oracle gives (20,2), inverse (5,6) | 4.4 DONE |
| Affine round trips and known forward values | `test_seeded_forward_oracles_and_round_trips`: seed 1007, five explicit corner/origin/negative points plus 200 samples; independent scalar forward formulas, recovered physical error <=1e-6 mm | 4.4 DONE |
| Singular/ill-conditioned/nonfinite/type failures | Parameterized invalid matrices, explicit enum/kind checks, normalized condition threshold, extreme representable scales and overflow rejection | 4.5 PARTIAL; no path resolver |
| Frame incompatibility | Exact intermediate record checks, same-ID/different-metadata collisions, conflicting revision/machine/capture endpoints, explicit units/datum rejection | 3.1/4.5 PARTIAL; not full machine/calibration isolation |

Numeric policy: proposed `synthetic-geometry-v1` affine subset. Round-trip bound <=1e-6 mm; normalized 2x2 spectral condition <=1e8. Unit-scale isometry checks use absolute 1e-12 binary64 shape tolerance. These bounds are not verified hardware accuracy or a general guarantee for arbitrarily large coordinates. The full configurable policy and production-purpose qualification remain unimplemented.

## OpenSpec validation

Command: `openspec validate board-geometry-foundation --strict` from `C:\dev\aoi-platform`. Actual result: "Change 'board-geometry-foundation' is valid", exit code 0. OpenSpec validation does not replace implementation tests or complete any remaining task.

## Remaining work — intentionally open for review

Only original tasks **4.1, 4.2, 4.3, 4.4** are checked; **59 remain unchecked**. Task 3.1 remains open for the complete typed-model contract, despite the tested point/frame/affine subset. Task 3.6 remains open: individual GeometryError is not the multi-error report/ordering contract. Task 4.5 remains open: explicit pairwise frame checks are not graph resolution, missing-path detection or ambiguous-path validation.

Further Sprint 1 work includes capacity/fixture/travel records and checks (3.2, 4.15–4.17), full error reports, and contextual path resolution. No normative requirement is removed or weakened by limiting this implementation slice. Later import, real PCB fixture, Gerber evaluation, BOM/placement, fiducial registration, camera/lens calibration, REVIEW inspection boundary, six-machine lifecycle validation and optional engine work remain open. Source provenance/immutable board revision persistence is specified but not implemented by immutable numerical records alone. Future 3D and physical travel/coverage remain outside this slice.

KiCad 10.0.7 is still an unverified target; no parser compatibility, real fixture test or production accuracy is claimed. No project files were created under Codex outputs. `C:\dev\aoi-reference` was not modified. No push or deployment was performed. Existing untracked `.agents/` and `.claude/` content was left untouched.

## Geometry Core review corrections — 2026-10-17

Scoped fixes only; no additional task is completed. Original method/constructor signatures are unchanged. `Transform2.conventions_validated` is a derived, read-only attribute. A raw map across different units or axis directions remains unvalidated and cannot be applied, inverted, composed or used for orientation mapping: those operations return `MAPPING_UNVALIDATED`. Provenance text is not authorization. Explicit unit/rotation/reflection factories and compositions/inverses of validated operands retain the needed evidence. Translation alone does not declare an axis mapping. Dataclass replacement recomputes validation, preventing a changed matrix from inheriting that evidence. This flag concerns declared numerical conventions, not hardware/source calibration or production accuracy.

Composition now preserves RIGID only when both operands are validated RIGID maps, and rechecks the product's isometry. Reflection/general-affine operands conservatively produce AFFINE, with independently computed parity; a positive determinant alone never promotes a map to RIGID. All prior source-frame, matrix and context checks remain active.

Changed in this correction: `src/aoi_platform/geometry/transforms.py`, `src/aoi_platform/geometry/errors.py`, new `tests/test_transform_validation_regressions.py`, `README.md`, and this status document. Existing tests and normative requirements are unchanged; existing unrelated workspace files were left untouched.

Regression evidence:

- Before the fix, six regression cases failed as expected: both directions of raw inch/mm identity, three incompatible axis conventions with raw identity, and loss of RIGID classification on composition.
- After the fix, `.venv/Scripts/python.exe -m pytest -q` reported **104 passed in 0.14s**, exit code 0: all 78 existing cases plus 26 new regression cases, no final failures/skips.
- Additional adversarial cases cover forged provenance, replacing a validated matrix, blocking all computational entry points, cancellation through composition, preserving explicit unit/shear/inverse workflows, and conservative reflection/general-affine kind handling.
- `coverage` and `pytest-cov` are not installed in the existing environment. Python's available standard-library `trace` line-coverage check ran the same suite: **104 passed in 0.86s**, exit code 0. It reported **100% executable-line coverage** for the four measured modules: angles (8 lines), errors (33), models (101), transforms (245). This is the standard-library trace metric, not branch coverage or a pytest-cov result. Annotated reports are local under ignored `.pytest_cache/geometry-coverage/`.

Reproduce the available coverage check from the workspace without installing packages:

```powershell
@'
from pathlib import Path
import sys
import trace
import pytest
source = Path('src/aoi_platform').resolve()
tracer = trace.Trace(count=True, trace=False, ignoredirs=[sys.base_prefix, sys.prefix, str(Path('tests').resolve())])
exit_code = tracer.runfunc(pytest.main, ['-q'])
counts = {key: count for key, count in tracer.results().counts.items() if Path(key[0]).resolve().is_relative_to(source)}
trace.CoverageResults(counts=counts).write_results(show_missing=True, summary=True, coverdir='.pytest_cache/geometry-coverage')
raise SystemExit(exit_code)
'@ | ./.venv/Scripts/python.exe -
```

Strict OpenSpec validation is run after these corrections; its result is reported in delivery. The same 59 tasks remain open, including full contextual path resolution, envelope checks, calibration and imports. No new inspection validation workflow, source parser, hardware qualification or other OpenSpec task was implemented. No commit or push was performed.
