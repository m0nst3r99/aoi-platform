## Approved verification inventory - 2026-11-14

The owner approved the complete 47-scenario inventory (24 GEO-001, 23 PCB-001)
as the official baseline. See [Verification & Acceptance Matrix](verification-matrix.md)
for original requirement/scenario mappings, historical evidence, reviewer decisions,
reuse limits and remaining gates. This approval is about inventory/scope, not
47 passing verifications or blanket acceptance. Existing bounded acceptance and
all task checkboxes are unchanged. No tests ran for this documentation update.
Future slices must consult the matrix before proposing tests and update evidence
mappings after verification. The historical implementation record below is retained.

## Current merged-master scope - 2026-11-13

Start with [HANDOFF](../../../HANDOFF.md#current-state--next-action) and
[AGENTS](../../../AGENTS.md). Authorized merge parents: master `350c1e3` and
checkpoint `3262563`; master remains the development branch, checkpoint is retained.
Verified merge commit: `5d5658bc1ac29a4100b0ada8dc0c33db70c52256`, exactly those
two parents. Post-commit verification retained all 7,098 local-only files with
matching size/SHA-256 and zero accidentally tracked. No push occurred.
This section supersedes historical branch-specific current/next instructions below.
The entire checkpoint technical-history baseline is preserved below unchanged.

| Area | Implementation and limits |
|---|---|
| Geometry / inventory | Existing core and bounded byte admission retained; aggregate tasks remain partial |
| KiCad reader / runner | Evaluation protocol v2, outline decisions, replay and native-control code integrated; not a complete supported product importer or complete containment |
| Pad candidates | Bounded synthetic top-SMD/F.Cu rectangles, explicit proper-rigid transforms, declaration-consistent association; no source-membership authority from inventory alone |
| Boundary pipeline | Preflight/declaration binding, contour correspondence and candidate orchestration implemented for bounded subsets |
| Source checking | Pinned C1+C2 preflight/hash/source-declarations/boundary-record phases implemented; shared ledger and intermediate results only |
| SourceCheckEvidence / PreparedRequest | Dataclass contracts exist; complete receipt construction and prepare_source_checked_pad_request API NOT IMPLEMENTED. Future construction is blocked on a reviewed bounded provenance/budget plan |
| Product importer / publication | NOT IMPLEMENTED as a complete product path; support/readiness remains blocked by open requirements |

Historical tests and user-relayed review acceptance retain their original scope;
file integration is not new acceptance. No checkboxes, support allowlist or PARTIAL
statuses are promoted. No full historical suite, native KiCad or expensive runner
suite is rerun for this integration. Local-only artifacts are inventoried outside
the repository and 7,098 files matched SHA-256/size after merge.
Integration checks: checkpoint non-document blobs match the index; no master files
lost, unmerged entries or conflict markers. Strict OpenSpec validation passed.
Default staged whitespace check exits 2 on immutable historical content; all 17,815
non-document findings also occur in the checkpoint baseline. New documentation
prefixes and AGENTS whitespace checks pass. This is not a claim of raw-check PASS.
Next proposal: review a bounded receipt/request construction plan using existing
source-checked results, preserving field provenance, one ledger and no execution
during preparation. Do not implement that next slice in the merge task.

## Preserved checkpoint implementation and evidence history

# Geometry Core implementation evidence

## Current bounded Windows runner evidence - 2026-10-19

Final checks: strict OpenSpec validation PASS; git diff --check PASS (only pre-existing LF/CRLF notices). New untracked runner code/docs whitespace check PASS. Raw commands/results are in runner evidence review-03/final-validation.json.

Runner implementation evidence at HEAD `4e59ad93cc9f753e5c84ca8df7a49868dfde2470`.
Existing uncommitted documentation/evaluation work is preserved. New evaluation-only
runner is in [evaluation/windows_runner](../../../evaluation/windows_runner/README.md).
The authorized ownership/transport/success contract was revised in design before
implementation. No product code, fixture, normative spec, checkbox or allowlist
changed by this runner slice; prior task/supported-inputs edits remain untouched.

Latest actual run: **491 passed, 1 skipped in 17.99s**, evidence
[evaluation/windows_runner/evidence/review-03](../../../evaluation/windows_runner/evidence/review-03/environment-command.json).
This includes 57 portable runner tests and 41 Windows cases, 23 existing harness
regressions and 370 product tests. Skip is the existing local-fixture opt-in.
Actual OS: Windows 10.0 build 26300 AMD64; CPython 3.11.9 MSC v.1938 AMD64.
Each native case has an independent watchdog. Fault-injected cases are distinguished
from real enforcement in the runner README. No KiCad/accepted fixture was run.
Earlier runner evidence is retained; review-03 supersedes review-01/02.

**New runner code/results await review; not accepted by the prior reviews.**
Errata/r2 metadata and harness acceptance below remain valid in their stated scope.
Tasks 1.5/5.2 stay PARTIAL. Synthetic memory/count/output/tree tests do not establish
parser compatibility or observation geometry. Slice remains incomplete for universal
runner-parent crash protection: native crash test covers an assigned Job, while
CreateProcess-suspended to Assign has an unprotected host-death window. Also not
native-proven: naturally incompatible enclosing Jobs and other OS/runtime versions.
Single-reader polling has no outstanding async I/O/thread to cancel; no claim of a
CancelIo failure test. Permanent cleanup errors return unconfirmed, not success.

Next: review transport code/evidence and resolve the non-atomic pre-assignment
host-death gap before treating the entire runner contract as complete. Do not start
KiCad adapter/bridge/protocol semantics from this evidence. Reproduction commands
are in the runner README; fresh collector IDs preserve earlier runs. Review ZIP
contains runner code/tests, raw results, contract, this handoff and SHA-256 manifest,
without the large accepted fixtures.

## Historical metadata acceptance / observation contract draft - 2026-10-19

The user reports direct ZIP review **accepted errata and REAL-PCB-01-r2 only for
population metadata correction**. Reviewer reran 23/23 regressions, verified
133/133 packaged hashes and 25/25 checksums per snapshot, checked all twelve UUID
DNP attributes against complete PCB source, confirmed exactly twelve dnp edits
and 23 byte-identical other files. Replay using saved subprocess output produced
r1 FAIL 26/27 and r2 PASS 27/27. Reviewer did not rerun KiCad native. These are
user-relayed review results, distinct from previous local agent native runs;
no third-party attestation or parser compatibility is asserted.

r1 and all snapshots/evidence are unchanged. The [errata](../../../evaluation/kicad-reader/population-errata-r2/ERRATA.md)
and parent-linked r2 manifest retain preparation history. Earlier pending-review
statements below are superseded for this metadata scope only.

The [observation contract in design](design.md#review-draft-native-observation-boundary-2026-10-19-tasks-1552-partial)
is a new **review draft**, not implemented/accepted. It binds inventory admission,
source hash, pinned backend and explicit limits; prevents usable observations on
failure; names native-loader coverage gaps and a Windows enforcement/test plan.
It proposes exactly one next slice: evaluation-internal bounded process runner
with synthetic helpers, leaving KiCad semantics and inventory bridge separate.
Windows containment and new geometry oracles are NOT RUN, not inferred from old
harness tests. Tasks 1.5/5.2 remain PARTIAL/open; no checkbox or allowlist edits.
No product code or fixture changes; no full pytest/native rerun for this docs turn.
Verification: strict OpenSpec validation passed and git diff --check passed
(LF/CRLF notices only). Prior uncommitted changes are preserved.

## Current harness acceptance and population errata - 2026-10-19

User reports direct ZIP v2 review accepted the harness fixes: reviewer reran
23/23 regressions, verified 44/44 manifest hashes and 14 unchanged old logs.
Reviewer did not have the full PCB source or rerun KiCad. No signature or
attestation is created. Earlier harness-review-pending text is historical.

[Population errata and derivation evidence](../../../evaluation/kicad-reader/population-errata-r2/ERRATA.md)
correct twelve descriptive DNP fields in new REAL-PCB-01-r2 only. r1 and prior
evidence remain unchanged. r2 manifest/inventory retain parent provenance and
pending-review status; no parent acceptance copied. All other population fields,
KiCad source and exports are unchanged. Earlier r1 population false declarations
for these UUIDs are superseded by the errata, retained as history.

Unmodified harness, fresh evidence directories: r1 FAIL 26/27 with 12 DNP
conflicts; r2 PASS 27/27 with none. Local regressions: 23 passed. These are new
agent observations; errata/r2 await review. Metadata consistency is not parser
compatibility or publication. Tasks 1.5/5.2 remain PARTIAL/open; checkboxes and
allowlist unchanged. No product adapter/code changes.

## Current reader evaluation - 2026-10-19 (1.5/5.2 PARTIAL)

The user authorized evaluation, superseding the historical inventory-only scope
and "next work is to evaluate" statements below. [Report and reproduction](../../../evaluation/kicad-reader/README.md)
and [machine-readable results](../../../evaluation/kicad-reader/results.json)
record native CLI/pcbnew 10.0.7 observations, official IPC/SWIG documentation and
a source-only kiutils assessment. No product reader, version allowlist, parser
compatibility claim or checkbox change. New findings are not yet reviewed;
prior gate/inventory/Sprint 1 review acceptance remains unchanged.

Nine of ten aggregate fixture checks pass; population equality fails for twelve
G*** DNP declarations (ledger false, API true). A representative source multiline
attribute block confirms dnp; full UUID/expected/actual evidence is preserved.
The harness exits 1 to expose the conflict. Snapshot hashes before/after agree.
Malformed native load and pre-load missing-file failures are recorded separately.
Full pytest is not rerun because shared code/tests are unchanged. Positive cutout
tests, complete pad semantics, unsupported-construct detection and containment
remain open. Next work is review and the proposed bounded observation adapter,
not geometry import/publication. Tasks 1.5/5.2 remain PARTIAL/open.

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


## Strict-v2 duplicate pad UUID evaluation (2026-10-22; pending review)

Shared observation_schema.py now rejects duplicate pad UUID identity across all
footprints in strict-v2 only. UUID objects are compared without changing source
strings, merging or dropping pads. Distinct UUIDs with repeated number string "1"
remain valid. Legacy replay returns before this new check; its behavior is unchanged.
Decision reports SCHEMA_INVALID; entrypoint fails with nonzero exit. No product
DUPLICATE_ID/publication/canonical geometry claim; Tasks 1.5/5.2 remain PARTIAL.

Portable evidence: evaluation/windows_runner/evidence/duplicate-pad-uuid-portable-01/.
Exactly test_harness.py and test_outline_decision.py executed: 64 passed in 2.44s,
exit 0. Raw repeated-pads stdout bytes match the accepted review ZIP. Negatives
are in-memory copies: same footprint, distinct valid parent UUIDs across footprints,
and equivalent UUID spelling. Before introducing collisions, schema-valid controls
are asserted. Schema does not mutate the payload. Replayed synthetic board passes
the outline decision only; unrelated real-board harness oracles still fail as expected.
Eight code/input hashes match before/after; argv/cwd/raw stdout/stderr recorded.
Implementer portable run only, no native/full-suite run or independent review yet.

Changes: shared schema, two portable test files, this status note and HANDOFF.
Probe, run.py decision routing, runner/helper, legacy protocol, historical evidence,
checkboxes and allowlist unchanged. Prior HANDOFF workflow edits retained.
Next: review the duplicate-pad UUID ZIP. No commit/push authorization for this slice.


## Duplicate pad UUID review acceptance (2026-10-23)

User reports duplicate-pad-uuid review ZIP PASS within evaluation-only scope:
independent rerun 64 passed; 28/28 manifest hashes and eight pre/post-run hashes
match; raw repeated-pads replay matches the previously accepted bytes. This
supersedes the pending-review and no-independent-review statements above for this
slice only. No native rerun is claimed. Historical evidence remains unchanged.
Tasks 1.5/5.2 remain PARTIAL; no product rejection/publication or canonical geometry
acceptance. No commit/push authorization has been given for this slice.

Next proposal for review, not implemented: strict-v2 duplicate board-level edge UUID
rejection. Current schema validates each UUID but constructs a set from board edges
without checking duplicates within that collection. Trace: task 3.4 and PCB-001
invalid-outline/nonfinite/duplicate-entity scenario. Portable replay with a single
in-memory UUID collision should reject SCHEMA_INVALID through decision and entrypoint;
valid distinct-edge replay and historical legacy behavior must remain unchanged.
No new native fixture/run, geometry normalization or publication implementation.


## Strict-v2 duplicate board-edge UUID evaluation (2026-10-23; pending review)

Observation schema now rejects duplicate UUID identity within board-level edges,
including identical and equivalent UUID strings. This is separate from accepted
pad UUID checks; no new cross-entity collision rule. Payloads are not changed,
merged or dropped. Legacy returns before the strict-v2 checks and is unchanged.
SCHEMA_INVALID propagates through decision and failed/nonzero entrypoint.

Evidence: evaluation/windows_runner/evidence/duplicate-board-edge-uuid-portable-01/.
Exactly test_harness.py and test_outline_decision.py: 71 passed in 3.06s, exit 0.
Seven new cases cover identity spellings, nonmutation and legacy behavior. Existing
accepted raw repeated-pads positive replay remains schema-valid/intermediate (not
import-ready). Negative copies change only one edge UUID after asserting a valid
control. Eight pre/post code/input hashes match; argv/cwd and raw outputs retained.
No native/full-suite run or historical evidence changes. Implementer evidence only;
new slice awaits review. Tasks 1.5/5.2 remain PARTIAL; no product/publication claim.

Only shared schema and its two portable test files changed, plus HANDOFF/status.
Git f77efa1 predates accepted pad-UUID work: Git diffs are cumulative. Review package
also includes exact pad-UUID ZIP baseline and separate diffs isolating new code/tests;
document diffs additionally include the intervening acceptance notes.
No commit/push. Next action: review board-edge UUID ZIP before any publishing.


## Duplicate board-edge UUID review acceptance (2026-10-23)

User reports duplicate-board-edge-uuid ZIP PASS within evaluation-only scope:
independent rerun 71 passed; 38/38 manifest hashes, eight pre/post-run hashes and
ten baseline/diffs match. Pad-UUID baseline matches the previously accepted version.
This supersedes pending-review statements for this slice only. No native rerun or
product/canonical/publication acceptance is inferred. Tasks 1.5/5.2 remain PARTIAL.
Historical evidence unchanged; no commit/push authorization.

Next proposal, not implemented: compare footprint UUID uniqueness by UUID identity
in strict-v2. Current schema compares footprint UUID strings, unlike accepted pad
and board-edge identity checks; equivalent spellings can evade that collection's
duplicate check. Trace task 3.4 and PCB-001 duplicate-entity scenario. Portable
controls should start with two valid distinct footprints and disjoint pad UUIDs,
then change only the second footprint UUID to an identical/equivalent first UUID.
Require SCHEMA_INVALID through decision and failed/nonzero entrypoint, nonmutation,
and unchanged legacy behavior. Scope excludes cross-entity collision and parent
reference matching policy. No native run or geometry normalization is proposed.


## Strict-v2 footprint UUID identity (2026-10-23; pending review)

Footprint uniqueness now compares UUID identity instead of strings. Parent list and
reference matching, cross-entity collision checks, pad/board-edge checks, probe and
runner are unchanged. No payload rewriting. Legacy behavior unchanged.
Evidence: evaluation/windows_runner/evidence/duplicate-footprint-uuid-portable-01/.
Only test_harness.py and test_outline_decision.py ran: 78 passed in 2.67s, exit 0.
Seven new cases use two valid distinct footprints with disjoint pad UUIDs and no
footprint_edges. Identical/equivalent footprint collisions reject SCHEMA_INVALID;
positive remains intermediate, entrypoint retains unrelated real-board oracles.
Nonmutation and legacy checked. Eight pre/post code/input hashes match. No native.
Tasks 1.5/5.2 remain PARTIAL; historical evidence retained. No commit/push.

Next proposal (not implemented): review a product-facing immutable canonical Pad
candidate contract for tasks 3.4/5.5 with explicit source artifact/hash/entity and
validated source-to-P transform, starting with synthetic rectangular copper pads.
Design.md Pad contract (line 410) requires geometry in P, identity/number/layers and
provenance; task 5.13 forbids guessed transforms. Define all required fields and
failure behavior before code, preserve repeated numbers, reject invalid/missing
provenance/context/unsupported geometry, and keep candidate non-published. No native
reader bridge, BoardRevision publication or targeting authority in that first slice.
This replaces a proposed continuing chain of evaluation-only UUID hardening.

Review packaging: exact Git f77efa1 baseline yields cumulative pad/edge/footprint
diff; accepted board-edge ZIP provides separate baseline/diff for this slice.
Documentation diff includes intervening acceptance notes. Await review authorization.


## Footprint UUID acceptance and Pad candidate contract (2026-10-23)

User reports footprint UUID ZIP review PASS within evaluation-only scope:
independent rerun 78 passed; 38/38 manifest hashes, eight pre/post-run hashes and
ten baseline/diffs match. Supersedes pending-review statements for this slice only;
no native rerun/product acceptance inferred. Historical evidence unchanged.
Tasks 1.5/5.2 remain PARTIAL; no commit/push authorization.

New review draft in design.md: immutable canonical Pad candidate, tasks 3.4/5.5/5.13.
Normative requirements separated from D1-D5 proposals: candidate revision scope,
identity/provenance binding, supported geometry/maps, output representation and
limits/numeric policy. Product implementation blocked on selection; no reader bridge,
BoardRevision creation, publication, targeting or native run. Next action: review
contract and select decisions, then authorize a bounded implementation separately.


## Pad candidate contract revision 2 (2026-10-23; documentation only)

D1-D4 and structural D5 selections recorded in design.md. Candidate scope is caller
supplied unpublished revision context, all source/target frames match it; no core
guards relaxed. Opaque canonical IDs retain exact strings; top SMD/F.Cu/mm proper
rigid subset supports explicit nonzero pad angle and indexed vertices.
Complete field/source/context table, parent declaration-versus-verification boundary,
proposed numeric budgets/diagnostic reservation and independent +90-degree pad oracle
added. O1-O4 remain for review: declaration-consistent association, empty pad number,
exact limits/numeric guard and source-entity alias policy. No product code/tests/native,
commit/push or historical evidence edits. Tasks 1.5/5.2 PARTIAL. Next: select remaining
contract decisions before implementation authorization.

## Canonical Pad candidate implementation (2026-10-24; review pending)

O1-O4 selected by user; this supersedes the earlier pending-contract entry.
`src/aoi_platform/pad_candidates.py` adds immutable bounded synthetic top-SMD/F.Cu
rectangle candidates from explicit mm/right/up proper-rigid maps. Input inventory
identity/hash and complete frame/scope are checked; repeated/empty pad numbers stay
unchanged. Source aliases reject; batch failure has no candidates. Association is
only declaration-consistent, not verified membership from source bytes. No reader,
BoardRevision, publication, targeting authority or native execution was added.

`tests/test_pad_candidates.py`: independent angle0/+90/45 corner oracles, context,
provenance, alias/identity, immutable/all-or-nothing behavior, malformed inputs,
exact/exceeded metadata/count/numeric limits and diagnostic reservation coverage.
Evidence: `evaluation/pad-candidate/evidence/canonical-pad-candidate-02/`.
Focused100 PASS (exit0); default full pytest470 PASS/1 skipped (exit0). The skip is
opt-in local REAL-PCB-01 inventory, not a passing real-fixture test. This default
suite uses testpaths=tests; historical evaluation/native suites were not rerun.
28 code/test/config hashes match before/after and current bytes; raw stdout/stderr
and argv/cwd/exit are preserved. Strict OpenSpec validation passed. Earlier run01
is retained as development evidence, not the final reviewed-code result. No rerun
was needed for packaging because the28 inputs still match. These are implementer
results; new candidate implementation awaits independent review.

Only a narrow `/evaluation/pad-candidate/** -text` attribute was added to preserve
new evidence bytes. No historical evidence or existing core guards were changed.
Tasks3.4/5.5/5.13 remain PARTIAL (this bounded candidate subset only); Tasks1.5/5.2
remain PARTIAL. General pad geometry, native association, full import/reconciliation,
canonical revision lifecycle and atomic publication remain open. InventorySuccess
is a trusted in-process result, not authentication or proof of design consistency.

Branch checkpoint/outline-inventory-repeated-pads; HEAD f77efa171cfb58e843e93ebbe6d16a0f30ab9358.
Index stays empty; pre-existing evaluation/document/untracked work is retained.
No native, commit or push. Next single action: review the canonical Pad candidate
ZIP and its isolated pre-implementation baseline/diffs before any further work.

## Canonical Pad candidate review accepted (2026-10-24)

User reports review PASS for the selected bounded candidate subset. Reviewer rerun:
470 passed, 1 skipped; 74/74 manifest hashes, 28/28 pre/post hashes and all six
baseline/diffs matched. Review package: aoi-canonical-pad-candidate-review-a3365c21c98c.zip.
This supersedes the review-pending status and review-next-action above; those entries
remain historical. These are reviewer results relayed by the user, not a new agent
rerun or an attestation.

Acceptance is limited to the selected synthetic top-SMD/F.Cu rectangle candidate
operation with explicit proper-rigid transforms and declaration-consistent association.
It does not verify native source membership, general geometry/parser compatibility,
BoardRevision publication, atomic publication, targeting or production accuracy.
The skipped local fixture test remains unverified by this rerun. Tasks 1.5/5.2 and
aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.

This update changes documentation only: no code/evidence edits, tests/native runs,
commit or push. Await explicit authorization for any next implementation or publishing.

## Repeated-pads replay bridge review accepted (2026-10-24; fixture-only)

User reports review PASS for aoi-repeated-pads-bridge-review-e3e1903f89b6.zip.
Reviewer rerun: 21 passed; 28/28 manifest hashes and 20/20 pre/post hashes matched.
These are reviewer results relayed by the user, not a new agent rerun or attestation.
The bridge's review-pending status is superseded by this fixture-only acceptance.
Evidence remains evaluation/kicad-reader/evidence/repeated-pads-bridge-01/.

Acceptance covers only the accepted repeated-pads replay: explicit normalization
N(x,y)=(x,-y), separate reflection evidence, caller-declared translation (0,20),
and inventory-bound PCB/raw observation hashes. Build/schema checks are value
checks, not backend authentication. Association remains declaration-consistent;
no general reader/geometry compatibility, native membership verification,
BoardRevision/publication, atomic publication, targeting or production accuracy
is established. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL.

Documentation-only acceptance update; no code/evidence changes, tests/native runs,
checkbox changes, commit or push. Await explicit authorization for further work.

## Portable Pad candidate control review accepted (2026-10-25)

User reports review PASS for aoi-pad-candidate-control-review-39b45b1cd14a.zip.
Reviewer rerun: 25 passed; 30/30 manifest hashes and 23/23 pre/post hashes matched.
These reviewer results were relayed by the user; no new agent rerun or attestation.
Evidence: evaluation/windows_runner/evidence/pad-candidate-control-portable-01/.

Acceptance covers portable orchestration with fake execution: forwarding the exact
execution stdout, no historical fallback, and blocking before bridge on transport
failure/timeout, unconfirmed cleanup or hash mismatch. It does not establish a
native runner/helper/probe-to-candidate end-to-end path or backend authenticity.
The repeated-pads fixture-only scope, declaration-consistent association and runner
host-crash gap remain. No general geometry/import compatibility, BoardRevision,
publication/atomic publication, targeting or production accuracy claim is made.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.

Documentation-only acceptance update; no code/evidence changes, tests/native runs,
commit or push. Further implementation or native execution requires authorization.

## Native callback review accepted (2026-10-25; portable only)

User reports PASS for aoi-pad-native-callback-review-74fa0a1b712d.zip: reviewer rerun
14 passed; 20/20 manifest hashes and 10/10 pre/post hashes matched. Tests used fake
Popen; native end-to-end execution, backend authenticity and complete containment
are not established. The existing host-crash gap remains open. Tasks 1.5/5.2 and
aggregate 3.4/5.5/5.13 remain PARTIAL. No geometry/publication scope expanded.

User explicitly authorized the related accepted checkpoint commit/push on the
current checkpoint branch, not master. Includes accepted UUID validation dependencies,
canonical Pad candidates, replay bridge, portable control/callback and reviewed evidence.
Unrelated historical evidence and agent integration files remain outside this checkpoint.
Two exact source/test -text rules preserve reviewed candidate bytes at staging.
No tests/native were rerun for this documentation/checkpoint operation.

## Native Pad candidate integration review accepted (2026-10-25; fixture-only)

User reports review PASS for aoi-pad-native-integration-review-f452dff5ba6c.zip.
Reviewer compared hashes, raw output, candidate oracle and cleanup evidence;
reviewer did not rerun native execution. This is user-relayed review acceptance,
not an independent native rerun or attestation.

Evidence: evaluation/windows_runner/evidence/pad-candidate-native-integration-01/.
Exactly one implementer native run connected NativeExecution -> control -> bridge
-> Pad candidates on the accepted repeated-pads fixture: 11/11 checks PASS,
root exit 0, transport 1750 ms, two candidates matching the oracle, input/output
hash binding, Job active_processes=0, cleanup cleaned and owned staging removed.
The earlier portable-only entries remain historical; this acceptance adds native
end-to-end evidence only for this pinned fixture and tested runtime.

Acceptance does not establish general geometry/parser compatibility, backend
authentication, independently verified source membership, BoardRevision publication,
atomic publication, targeting or production accuracy. Association remains
declaration-consistent. The suspended-CreateProcess-before-Job-assignment
host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL;
no checkbox changes. No code/evidence edits, tests/native reruns, commit or push
were performed for this acceptance update. Await authorization for further work.

## C1 portable rectangle review accepted (2026-10-26)

User reports review PASS for aoi-c1-rectangle-review-21f9943fc1a4.zip:
reviewer rerun 3 passed; 24/24 manifest hashes, 17/17 pre/post hashes and all
eight oracle corners matched. These are reviewer results relayed by the user,
not a new implementer rerun or attestation. Evidence remains
evaluation/kicad-reader/evidence/c1-rectangle-portable-03/.

Acceptance covers portable C1 rectangle candidate math from saved observation,
explicit same-datum P with translation (0,0), and reflection correspondence
(3,2,1,0). InventorySuccess is a trusted test double: PCB bytes_read and
actual_size are deliberately fake values of 1, not the source PCB size.
This does not verify real PCB byte admission, source membership/provenance,
native boundary vertices, strict-v2 import or real import. No publication or
targeting authority is established. The two earlier setup-failure runs remain
historical and unchanged. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL;
no checkbox changes. This acceptance update changes documentation only: no
code/evidence edits, tests/native runs, commit or push. Await further authorization.

## C1 real inventory integration review accepted (2026-10-26)

User reports review PASS for aoi-c1-real-inventory-review-d39b9d398bff.zip.
Reviewer obtained the PCB source with the recorded hash and reran 1 test PASS:
real inventory_artifacts byte admission, closed streams and all eight oracle
corners matched. All 26 manifest hashes and 19 inputs matched, including the
PCB supplied outside the ZIP. These are reviewer results relayed by the user,
not a new implementer rerun or attestation. Evidence remains
evaluation/kicad-reader/evidence/c1-real-inventory-portable-01/.

This separate integration uses actual PCB bytes (912379 bytes) and saved
observation bytes (196715 bytes), not the earlier inventory test double or fake
PCB size 1. The earlier portable acceptance and its limitations remain historical
and unchanged. Acceptance covers byte admission and the selected C1 candidate
math with explicit same-datum P, translation (0,0), and correspondence (3,2,1,0).
It does not establish source membership, backend authenticity, native boundary
vertices, strict-v2 observation/import, general real import, BoardRevision or
atomic publication, targeting, or production accuracy. Association remains
declaration-consistent; no native execution was part of this integration test.
The existing runner host-crash gap remains open. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL; no checkbox changes. This acceptance update changes
documentation only: no code/evidence edits, tests/native runs, commit or push.
Await explicit authorization for further work.


### 2026-10-26 - C1 comparator runtime-validation fix review accepted

User relayed review PASS for aoi-c1-boundary-fix-review-2e78c6182476.zip:
reviewer reran 23 portable tests successfully, including three Python -O
subprocess regressions (wrong build, open contour, and hole rejection).
All 18 manifest hashes and six pre/post-run hashes matched. Acceptance covers
explicit comparator runtime validation in place of assertions and its portable
regressions. These are reviewer results reported by the user, not a new
implementer rerun or an attestation. Evidence remains
`evaluation/kicad-reader/evidence/c1-boundary-portable-02/`.

The separate C1 boundary probe has NOT been run native. Portable comparator
acceptance does not establish native copper-boundary verification, backend
identity, general geometry/import support, publication or targeting authority.
Oracle, tolerance, probe and historical evidence remain unchanged. The runner
host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain
PARTIAL; no checkbox changes. This update changes documentation only: no
code/evidence edits, tests/native runs, commit or push. Await explicit
authorization for further work.


### 2026-10-26 - C1 native boundary review accepted (two C1/F.Cu pads only)

User relayed review PASS for aoi-c1-boundary-native-review-e2fa6c097b7f.zip.
Reviewer replayed saved raw output: all eight oracle corners matched exactly
(0 IU deviation); all 24 manifest hashes and 12 inputs matched. Reviewer did
NOT rerun native KiCad. These are reviewer results reported by the user, not
an additional implementer run or an attestation. Evidence remains
`evaluation/windows_runner/evidence/c1-boundary-native-01/`.

Acceptance covers only the two C1/F.Cu pad boundaries from the single recorded
native control, including raw polygon correspondence to the independent oracle.
The saved control reports successful transport, confirmed cleanup with Job
active processes 0, staging removal and unchanged fixture/input hashes.
The earlier statement that the probe had not run native is historical and is
superseded by this recorded control; no historical evidence is changed.

This does not establish other pads/layers, general geometry/import support,
backend authenticity or full dependency pinning, canonical publication,
targeting authority or production accuracy. The runner host-crash gap remains
open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
This acceptance update changes documentation only: no code/evidence edits,
tests/native runs, commit or push. Await explicit authorization for further work.


### 2026-10-27 - Pinned C1 replay flow review accepted

User relayed review PASS for aoi-c1-replay-flow-review-03f2cb9ff26b.zip.
Reviewer reran the portable tests with the real matching PCB: 25 passed.
All 31 manifest hashes and 24 inputs matched, including the PCB outside the
ZIP. These are reviewer results reported by the user, not a new implementer
rerun or an attestation. Evidence remains
`evaluation/kicad-reader/evidence/c1-replay-flow-portable-01/`.

Acceptance covers the evaluation-only pinned replay for exactly two C1/F.Cu
pads: real byte admission of PCB, legacy observation, boundary output and
report/transport; post-admission gates; candidate/oracle/boundary comparison.
The five hash/size pins remain fixed. Legacy is not upgraded to strict-v2.
Private post-admission gate tests deliberately use mutated in-memory payloads
with an unmodified positive inventory; these are test doubles, not evidence
that changed payloads pass the public hash gates. Candidate API failure also
uses a test double. Real hash-gate tests remain distinct.

No native execution was part of this replay test run. Hash binding establishes
consistency with pinned evidence, not backend authenticity or full dependency
pinning. Acceptance does not establish arbitrary-board import, other pads or
layers, general geometry, BoardRevision/publication or targeting authority.
Candidates remain unpublished with declaration-consistent association. The
runner host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13
remain PARTIAL; no checkbox changes. This update changes documentation only:
no code/evidence edits, tests/native runs, commit or push. Await explicit
authorization for further work.


### 2026-10-27 - C1 strict control identity-fix review accepted (fake execution)

User relayed review PASS for aoi-c1-strict-identity-review-be1c9bce130e.zip.
Reviewer reran 50 portable tests successfully; all 41 manifest hashes and 29
inputs matched. Each of the three current-execution identity mismatches
(artifact_id, source_id, policy_id) was blocked before observation gates.
These are reviewer results reported by the user, not a new implementer rerun
or an attestation. Final evidence remains
`evaluation/kicad-reader/evidence/c1-strict-control-portable-03/`.
Portable-02 remains historical evidence from before the patch was applied;
its 47-test result is not evidence for the identity fix.

Acceptance is evaluation-only and limited to fake execution: exact stdout
forwarding, strict-v2 validation without legacy opt-in, distinct current
observation versus historical boundary transports, and identity rejection
without candidates. No native end-to-end execution of this strict control has
been demonstrated. PCB and historical boundary pins, legacy replay, oracle
and normalization remain unchanged. No general import, complete geometry,
backend authenticity, BoardRevision/publication or targeting authority claim.
The runner host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13
remain PARTIAL; no checkbox changes. This acceptance update changes only
documentation: no code/evidence edits, tests/native runs, commit or push.
Await explicit authorization for further work.


### 2026-10-27 - C1 strict-v2 native control review accepted (C1/F.Cu only)

User relayed review PASS for aoi-c1-strict-native-review-a1d6b8e47ce8.zip.
Reviewer replayed offline through schema, inventory and boundary checks:
two candidates and all eight oracle corners matched. All 47 manifest hashes
and 33 inputs matched. Reviewer did NOT rerun native KiCad. These are reviewer
results reported by the user, not a new implementer rerun or an attestation.
Evidence remains `evaluation/windows_runner/evidence/c1-strict-native-01/`.

Acceptance covers only the recorded single native strict-v2 control for the
two pinned C1/F.Cu pads, with current observation transport kept separate from
historical boundary transport. No legacy fallback was used. The earlier
fake-execution-only limitation remains historical for those portable tests;
this recorded native control now provides limited end-to-end evidence for C1.
Historical code/evidence, PCB/boundary pins, oracle and tolerance are unchanged.

This does not establish arbitrary-board import, other pads/layers, complete
geometry, backend authenticity or full dependency pinning, BoardRevision or
atomic publication, targeting authority or production accuracy. Candidates
remain unpublished with declaration-consistent association. The runner
host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain
PARTIAL; no checkbox changes. This acceptance update changes documentation
only: no code/evidence edits, tests/native runs, commit or push. Await explicit
authorization for further work.

### 2026-10-27 - C2 real-inventory portable review accepted

User relayed review PASS for aoi-c2-real-inventory-review-75a44ae909cf.zip.
Reviewer reran with the real PCB: 1 passed; all eight oracle corners,
35 manifest hashes and 19 inputs matched. The strict-v2 observation matched
the previously accepted C1 native artifact at
`evaluation/windows_runner/evidence/c1-strict-native-01/stdout.bin`.
These are reviewer results reported by the user, not a new implementer run
or an attestation. Portable evidence remains
`evaluation/kicad-reader/evidence/c2-real-inventory-portable-02/`;
the initial encoding/collection failure in portable-01 remains historical.

Acceptance covers only the two C2 pads in the real-inventory portable test,
using the source-derived C2 oracle and saved strict-v2 observation. No legacy
payload upgrade or inventory test double is used. C2 native copper boundary
has NOT been verified; C1 native boundary acceptance does not extend to C2.
This does not establish general import, complete geometry, publication or
targeting authority. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL;
no checkbox changes. Historical evidence and existing limitations remain
unchanged. This update changes documentation only: no code/evidence edits,
tests/native runs, commit or push.

### 2026-10-27 - C2 boundary portable review accepted

User relayed review PASS for aoi-c2-boundary-review-0be117dff9b0.zip.
Reviewer reran 23 tests: all passed; 15 manifest hashes, six pre/post inputs
and all eight oracle IU corners matched. These are reviewer results reported
by the user, not a new implementer run or an attestation. Evidence remains
`evaluation/kicad-reader/evidence/c2-boundary-portable-01/`.

Acceptance covers the C2/F.Cu portable comparator subset, including
cyclic/reversed correspondence, invalid geometry/topology rejection and
Python -O rejection checks. The C2 probe has NOT run native; no C2 native
copper boundary verification is claimed. Existing C1 flows and historical
evidence remain unchanged. This does not establish general geometry/import,
publication or targeting authority. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13
remain PARTIAL; no checkbox changes. Documentation-only acceptance update:
no code/evidence edits, tests/native runs, commit or push.

### 2026-10-28 - C2 native boundary review accepted (C2/F.Cu only)

User relayed review PASS for aoi-c2-boundary-native-review-f1db1fab8c25.zip.
Reviewer replayed raw output and confirmed all eight oracle corners matched
exactly (0 IU difference); 24 manifest hashes and 12 inputs matched. Reviewer
did NOT rerun native KiCad. These are reviewer results reported by the user,
not a new implementer run or an attestation. Evidence remains
`evaluation/windows_runner/evidence/c2-boundary-native-01/`.

Acceptance is limited to the two pinned C2/F.Cu pad boundaries in the recorded
single native control. The earlier portable-review statement that the C2 probe
had not run native is historical and superseded only within this limited scope.
No general geometry/import, other pads/layers, canonical geometry, publication
or targeting authority is established. The runner host-crash gap remains open.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
C1 flows and historical evidence remain unchanged. Documentation-only update:
no code/evidence edits, tests/native runs, commit or push.

### 2026-10-28 - Pinned C2 replay review accepted

User relayed review PASS for aoi-c2-replay-flow-review-0004a68d1635.zip.
Reviewer reran with the real PCB: 26 passed; 34 manifest hashes and 26 inputs
matched. Observation and boundary matched the previously accepted artifacts.
These are reviewer results reported by the user, not a new implementer run or
an attestation. Evidence remains
`evaluation/kicad-reader/evidence/c2-replay-flow-portable-01/`.

Acceptance covers only the pinned two-pad C2/F.Cu evaluation replay with real
inventory, saved strict-v2 observation, historical C2 boundary/report/transport,
source-derived oracle and candidate comparison. Private-gate test doubles remain
distinct from actual byte-admission/hash-gate tests; they do not demonstrate
altered artifacts passing real admission. This is not a new native execution,
arbitrary-board import, publication or targeting authority. The runner
host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain
PARTIAL; no checkbox changes. C1 flows and historical evidence remain unchanged.
Documentation-only acceptance update: no code/evidence edits, tests/native
runs, commit or push.

### 2026-10-28 - Pinned C1+C2 replay batch review accepted

User relayed review PASS for aoi-c1-c2-batch-review-1c1ce42e15bb.zip.
Reviewer reran with the real PCB: 29 passed; 40 manifest hashes and 32 inputs
matched. Four pads, all 16 oracle corners and all-or-nothing behavior passed.
These are reviewer results reported by the user, not a new implementer run or
an attestation. Evidence remains
`evaluation/kicad-reader/evidence/c1-c2-replay-batch-portable-01/`.

Acceptance covers only the pinned C1+C2/F.Cu evaluation replay: eight artifacts,
two boundary gates and one candidate API call for four pads, using a common
normalized native-board datum, P translation (0,0) and one unpublished scope.
Private-gate test doubles remain distinct from real hash-admission tests.
This does not establish new native execution, arbitrary-board import, general
geometry, publication or targeting authority. The runner host-crash gap remains
open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.

Deferred documentation fix for the next authorized code turn:
`evaluation/kicad-reader/c1_c2_replay_batch.py` still opens with the stale
"Pinned C2 replay only" docstring. Its actual profile and behavior cover C1+C2.
Do not change these reviewed bytes in this acceptance-only update. Existing
flows and historical evidence remain unchanged. Only HANDOFF and implementation
status updated; no code/evidence edits, tests/native runs, commit or push.

### 2026-10-29 - Boundary preflight review accepted (preflight only)

User relayed review PASS for aoi-boundary-preflight-review-03b1c504fae4.zip.
Reviewer reran 60 tests: all passed; 37 manifest hashes and 18 inputs matched.
These are reviewer results reported by the user, not a new implementer run or
an attestation. Evidence remains
`evaluation/kicad-reader/evidence/boundary-preflight-portable-03/`;
historical runs 01/02 remain unchanged.

Acceptance covers immutable records, exact policy validation and joint bounded
preflight only. The result is preflight-only-not-bound, with no candidates;
geometry matching, artifact-to-record binding and candidate API execution are
not implemented by this slice. Source membership/construct coverage remain
unverified; no import readiness, publication or targeting authority is granted.
Budget primitive tests exercise counters/traversal boundaries; they are NOT
full-batch admission evidence for a complete valid maximum-size request.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Existing limitations, code and historical evidence remain unchanged. Only
HANDOFF and implementation status updated; no code/evidence edits, tests/native
runs, commit or push.

### 2026-10-29 - Boundary declaration binding review accepted

User relayed review PASS for aoi-boundary-whitespace-id-review-62d4c7ec6788.zip:
reviewer reran 114 tests, all passed; 37 manifest hashes and 19 inputs matched.
Review covers declaration binding, successful/consistent inventory validation,
nested-record validation and exact opaque-ID diagnostics, including whitespace.
These are reviewer results reported by the user, not a new implementer run or
an attestation. Evidence: evaluation/kicad-reader/evidence/boundary-binding-opaque-02/.
The six failures in opaque-01 were test setup errors; all historical logs remain
unchanged, including the earlier inventory/nested-record reproduction evidence.

This acceptance extends the earlier preflight-only milestone with identity,
artifact/hash and full-frame/context declaration binding. Status remains
`declaration-binding-only-no-geometry-check`; no candidates are returned.
Artifact-to-record association remains `supplied-declaration-unverified`;
source membership and construct coverage are not verified. Geometry matching
and candidate API execution remain unimplemented by this slice. No import
readiness, publication, targeting authority or complete geometry is established.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Only HANDOFF and implementation status updated. No code/evidence changes,
tests/native runs, commit or push.

### 2026-11-02 - Boundary correspondence review accepted (correspondence only)

User relayed review PASS for aoi-boundary-correspondence-review-65f5e272779d.zip:
reviewer reran 28 tests, all passed; 37 manifest hashes and 18 inputs matched.
These are reviewer results reported by the user, not a new implementer run or
an attestation. Evidence remains
`evaluation/kicad-reader/evidence/boundary-correspondence-portable-03/`.
Historical runs 01/02 and their test-data floating-point failures remain intact.

Acceptance is correspondence-only: bounded finite four-vertex contours in P,
topology/adjacency checks, raw order preserved and exactly one of eight
cyclic/reversed mappings within synthetic tolerance. No-match and ambiguous
mapping remain distinct. This is not rectangle admission or binding/candidate
execution; it grants no source verification, import readiness or targeting.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Only HANDOFF and implementation status updated; no code/evidence changes,
tests/native runs, commit or push.

### 2026-11-04 - Boundary orchestration static review accepted

User relayed static review PASS for aoi-boundary-orchestration-review-11041a814eb4.zip:
31 manifest hashes, 23 inputs and 21 baseline files matched. The 151 PASS result
is from the saved implementer log, not a reviewer rerun. Reviewer did not rerun
the tests. This records the user's report of review, not an attestation or a new
verification run. Evidence remains
`evaluation/kicad-reader/evidence/boundary-orchestration-portable-01/`.
The earlier orchestration "awaiting review" / "review is pending" statements
are historical and superseded by this scoped static-review acceptance.

Acceptance covers declaration binding followed by one candidate batch call,
explicit boundary transformation to P and per-pad correspondence, with no
candidates returned on failure. Assurance remains declaration-consistent;
coverage, source membership and artifact-to-record association are unverified.
No import readiness, publication, targeting authority or general import support
is established. Rectangle admission relies on the existing candidate API, not
convex-contour detection. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL;
no checkbox changes. Historical evidence remains unchanged.

Only HANDOFF and implementation status updated; diff --check run. No code/evidence
changes, tests/native runs, commit or push.

### 2026-11-04 - C1+C2 boundary integration static review accepted

User relayed static review PASS for aoi-c1-c2-binding-integration-review-3ea971408b22.zip:
43 manifest hashes and 36 inputs matched, including REAL-PCB-01-r2 PCB outside
that ZIP. The 2 PASS result is from the saved implementer log; reviewer has not
rerun the tests. This records review reported by the user, not an attestation
or a new verification run. Evidence remains
`evaluation/kicad-reader/evidence/c1-c2-binding-integration-01/`.

Acceptance is limited to the pinned C1+C2 portable integration: real artifact
inventory, four pads / 16 oracle corners, and all-or-nothing rejection when a C2
boundary declaration is changed in memory after hash admission. That negative
case does not change admitted artifact bytes or verify artifact-to-record
membership. Results remain declaration-consistent; source membership and
coverage remain unverified. No general import readiness, publication, targeting
authority or new native boundary verification is established.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Only HANDOFF and implementation status updated; diff --check run. Historical
code/evidence remain unchanged. No tests/native runs, commit or push.

### 2026-11-04 - C1+C2 artifact consistency static review accepted

User relayed static review PASS for aoi-c1-c2-artifact-binding-review-8bb969704d13.zip:
45 manifest hashes and 38 inputs matched, including the PCB outside the ZIP.
The 11 PASS result is from the saved implementer log; reviewer has not rerun
the tests. This records review reported by the user, not an attestation or a
new verification run. Evidence remains
`evaluation/kicad-reader/evidence/c1-c2-artifact-binding-portable-01/`.

Acceptance is limited to consistency with pinned C1+C2 observation/boundary
artifacts. The changed C2 vertex declaration is rejected before binding, with
no candidates and diagnostic artifact/hash, parent/pad UUID and expected/actual.
The negative case changes only a declaration in memory after hash admission;
original artifact bytes remain unchanged. Source membership and completeness
remain unverified. This does not establish general import readiness, publication,
targeting authority or new native execution evidence.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Only HANDOFF and implementation status updated; diff --check run. Historical
code/evidence remain unchanged. No tests/native runs, commit or push.


### 2026-11-05 - C1+C2 source membership scanner: blocked, not accepted

Added evaluation-only c1_c2_source_membership.py and its portable test file.
The iterative scanner checks the fixed r2 size/hash before parsing, enforces
128 nesting levels / 65536 token bytes / 500000 tokens, and scans through EOF.
It retains selected pad spans/lines and checks direct ownership and explicit fields.
No existing helper, product code, fixture or historical evidence was changed.

Implementer run: 29 passed, 5 failed (exit 1), with 40 pre/post input hashes
unchanged. Evidence: evaluation/kicad-reader/evidence/c1-c2-source-membership-portable-01/.
The five real-input cases are blocked before binding: the scanner's global UUID
uniqueness check encounters UUID 0ae7c3ce-ceb0-44ab-be65-2ff0efa576c2 twice in the
pinned PCB, at line 15576 (dimension) and line 15600 (its nested gr_text).
See source-duplicate-audit.json; source SHA-256 remains
67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0.
These are outside the four target pads. No expectation, source bytes or hash was
changed to obtain a pass. Full requested positive membership/binding evidence is
NOT established, and the changed-parent negative does not yet reach its intended
gate on the real PCB. Next single action: decide the UUID uniqueness namespace
(footprint/pad nodes versus all UUID-bearing nodes), then adjust only if authorized.
Completeness/effective copper geometry remain unverified; Tasks 1.5/5.2 and
aggregate geometry/import tasks remain PARTIAL. This is unreviewed work in progress.
No native/full suite, ZIP, commit or push. git diff --check passed.


### 2026-11-05 - C1+C2 source UUID namespace scoped; portable verification

User explicitly selected one shared UUID-identity uniqueness namespace: UUID
fields directly owned by every footprint directly under kicad_pcb and every pad
directly under those footprints. Nonselected footprints/pads are included. Other
UUID-bearing nodes (including dimension and its gr_text) are outside uniqueness;
syntax, direct UUID field validation, ancestry, EOF traversal and depth/token
limits remain enforced. This supersedes the pending scope decision above without
changing historical evidence or the pinned PCB.

Updated evaluation/kicad-reader/c1_c2_source_membership.py and its test file.
Regression covers cross-footprint pad collisions, footprint/pad collisions,
footprint/footprint collisions, equivalent UUID spelling, nonselected duplicates
at EOF, and dimension/gr_text shared UUID outside the namespace.
Implementer result: 37 passed in 1.82s, exit 0 (28 scanner/integration cases and
9 existing artifact-binding cases). Evidence:
`evaluation/kicad-reader/evidence/c1-c2-source-membership-portable-02/`.
All 40 pre/post input hashes match; portable-01 (29 PASS / 5 FAIL) remains
byte-identical. Real r2 positive reaches binding once, four candidates and all
16 oracle corners; changed-parent declaration returns SOURCE_CONFLICT before
the artifact/binding path, preserving expected/actual parent, pad UUID, source
hash and source span, without candidates. PCB pin remains unchanged.

This is implementer evidence, not independent review acceptance. Source membership
and explicit fields are checked only for the four pinned C1+C2 pads. Construct
completeness and effective copper geometry remain unverified; product assurances
are not upgraded. Tasks 1.5/5.2 and aggregate tasks remain PARTIAL. Next action:
review this scoped scanner change and new evidence. No native/full suite, ZIP,
commit or push. git diff --check passed.


### 2026-11-05 - C1+C2 source membership scanner static review accepted

User relayed static review PASS for aoi-c1-c2-source-membership-review-6c0de141bbe3.zip:
54 manifest hashes and 40 inputs matched, including the PCB outside the ZIP.
The 37 PASS result is from the saved implementer log; reviewer has not rerun
these tests. This records the review reported by the user, not an attestation
or a new verification run. It supersedes the review-pending wording above.
Evidence: evaluation/kicad-reader/evidence/c1-c2-source-membership-portable-02/.
The 29 PASS / 5 FAIL run and source-duplicate-audit.json in portable-01 remain
unchanged historical evidence of the earlier global-UUID scope.

Accepted uniqueness uses one shared namespace for direct UUID fields of every
footprint directly under kicad_pcb and every pad directly under those footprints,
including nonselected footprint/pad records. Dimension/gr_text and other nodes
are outside that uniqueness namespace; ancestry, syntax, EOF and scanner budgets
remain checked. The changed-parent declaration is rejected as SOURCE_CONFLICT
before binding, without candidates, retaining expected/actual parent, pad UUID,
source hash and span.

Acceptance covers source membership and explicit fields of only the four pinned
C1+C2 pads. Construct completeness and effective copper geometry remain unverified;
no general importer, import readiness, publication or targeting authority is
established. Product assurances remain unchanged. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Only HANDOFF and implementation status updated; git diff --check passed.
No code/evidence changes, tests/native runs, commit or push.


### 2026-11-05 - C1+C2 explicit modifier declaration screen (unreviewed)

Extended evaluation/kicad-reader/c1_c2_source_membership.py and its portable tests.
The fixed inspected paths, relative to a pad directly below a board-level
footprint, are: pad/drill, pad/offset, pad/drill/offset, pad/padstack,
pad/padstack/layer, pad/layer, pad/primitives and pad/options. These are a finite
presence screen, not a complete KiCad grammar or an assertion of effective values.
model/offset and zone_connect are excluded. Product code and prior flows unchanged.

Every selected pad records present/absent for each path, first half-open byte span,
one-based source lines when present, and occurrence count. Storage retains only
the first occurrence per path; traversal still observes all tokens through EOF
under the existing depth/token budgets. Any listed presence is rejected as
GEOMETRY_UNSUPPORTED before binding; failure contains diagnostic source records,
never candidates. The real entrypoint still checks exact PCB size/hash first.
Synthetic scanner diagnostics use the synthetic bytes' actual hash, not the pin.

Implementer evidence: evaluation/kicad-reader/evidence/c1-c2-modifiers-portable-01/.
49 passed in 1.96s, exit 0; all 40 pre/post hashes unchanged. Both the source
membership tests and existing artifact-binding tests ran. Real pinned r2 has all
eight paths absent in all four pads, reaches binding once and retains the four
candidates / 16-corner oracle check. Private synthetic drill-with-offset returns
GEOMETRY_UNSUPPORTED; a failure-only test double verifies early propagation before
binding. This does not admit synthetic bytes past the real pin (separate rejection
test). model/offset and zone_connect exclusion and EOF syntax rejection are tested.

Result concerns only presence of the listed explicit declarations. Completeness,
effective copper geometry and zone-fill effects remain unverified; product
assurances are unchanged. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL.
Historical evidence remains intact. Next action: review this modifier slice.
No native/full suite, ZIP, commit or push. git diff --check passed.


### 2026-11-05 - C1+C2 modifier declaration screen static review accepted

User relayed static review PASS for aoi-c1-c2-modifiers-review-306bbf8ac908.zip:
52 manifest hashes, 40 inputs (including the PCB outside the ZIP), two baseline
files and two diffs matched. The 49 PASS result is from the saved implementer
log; reviewer has not rerun the tests. This records user-relayed review, not an
attestation or a new verification run. Earlier unreviewed/review-pending wording
for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/c1-c2-modifiers-portable-01/.

Acceptance covers only presence of eight ancestry-specific paths in the four
pinned C1+C2 pads: pad/drill, pad/offset, pad/drill/offset, pad/padstack,
pad/padstack/layer, pad/layer, pad/primitives and pad/options. model/offset and
zone_connect remain separate from this screen.
The real pinned PCB case records all eight paths absent and passes binding with
four candidates / 16 oracle corners. Private-scanner synthetic drill/offset
bytes produce GEOMETRY_UNSUPPORTED. A failure-only test double checks propagation
before binding; it does not demonstrate admission of modified bytes through the
real hash gate or native execution. These evidence types remain distinct.

Construct completeness, effective copper geometry and zone-fill effects remain
unverified; no general import readiness, publication or targeting authority is
established. Product assurances are unchanged. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL; historical evidence and checkboxes remain unchanged.
Only HANDOFF and implementation status updated; git diff --check passed.
No code/evidence changes, tests/native runs, commit or push.


### 2026-11-05 - C1+C2 source pose/size gate (unreviewed)

Extended c1_c2_source_membership.py to retain direct footprint/at, pad/at and
pad/size literals, half-open byte spans and source lines (at most two occurrences
to detect duplicates). Added evaluation/kicad-reader/c1_c2_source_pose.py and
its portable tests. The gate runs before artifact/binding execution. Missing,
duplicate, nested/quoted numeric fields, malformed/nonfinite values, nonpositive
sizes and noncardinal angles reject explicitly. Evaluation numeric subset uses
plain decimal literals of at most 64 characters (no exponent), existing magnitude
bounds 1e6 and angle bound +/-360000 degrees. No source defaults are inferred.

Decimal cardinal arithmetic computes C=F+K(theta)*local once; pad alpha is world
orientation, not theta+alpha. Source corners use C+K(alpha)*q, then N(x,y)=(x,-y)
once. Existing normalized native-board datum / P translation (0,0) and source to
candidate correspondence (3,2,1,0) are retained. Expected geometry comes only from
source declarations; observation and candidate API do not generate the oracle.
Coordinates/size compare at 1 nm; raw angles compare exactly. This is synthetic
fixture evaluation, not a general import or production accuracy claim.

Evidence: evaluation/kicad-reader/evidence/c1-c2-source-pose-portable-01/.
Implementer result: 68 passed in 2.37s, exit 0; all 42 pre/post input hashes match.
Ran new pose tests plus membership/modifier and artifact-binding regression files.
Four source-derived centers/raw angles/sizes agree with strict-v2 observation;
16 Decimal corners agree with independent C1/C2 oracles within 1 nm. A memory-only
C2 request center.x increase of 0.001 mm returns SOURCE_CONFLICT before binding,
without candidates, preserving UUID/hash, pad and pose-field spans, expected/actual.
PCB and other artifact bytes remain unchanged. No native execution or full suite.

Scope is declared pose/size of the four pinned pads. Completeness, effective copper
geometry and zone-fill effects remain unverified; no publication or targeting
claim. Tasks 1.5/5.2 and aggregate tasks remain PARTIAL. Historical evidence intact.
Next action: review the pose gate and portable evidence. No ZIP, commit or push.
git diff --check passed.


### 2026-11-05 - C1+C2 source pose/size static review accepted

User relayed static review PASS for aoi-c1-c2-source-pose-review-11e7ef6d53b1.zip:
52 manifest hashes, 42 inputs (including the PCB outside the ZIP), the scanner
baseline and its diff matched. The 68 PASS result is from the saved implementer
log; reviewer has not rerun the tests. This records user-relayed review, not an
attestation or a new verification run. Earlier unreviewed/review-pending wording
for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/c1-c2-source-pose-portable-01/.

Acceptance is limited to declared pose/size of the four pinned C1+C2 pads, using
the bounded Decimal cardinal subset. Coordinate/size tolerance is 1 nm; raw angles
compare exactly. Footprint rotation places the local center once, pad angle is
world orientation, and Y normalization occurs once with correspondence (3,2,1,0).
The memory-only C2 center.x deviation is rejected before binding without candidates.

Construct completeness, effective copper geometry and zone-fill effects remain
unverified; no general import readiness, publication or targeting authority is
established. Product assurances are unchanged. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL; historical evidence and checkboxes remain unchanged.
Only HANDOFF and implementation status updated; git diff --check passed.
No code/evidence changes, tests/native runs, commit or push.

### 2026-11-05 - Selected C1+C2 pad ancestry coverage (review pending)

Evaluation-only change in c1_c2_source_membership.py and new
test_c1_c2_pad_coverage.py. Every child/descendant
of the four pinned pads is retained as an immutable path/value/span/line record.
The existing depth 128, token 64 KiB and 500,000-token limits bound traversal and
storage; the real source still requires exact PCB size/hash before scanning.
No footprint coverage or product importer changes.

Supported paths below are relative to kicad_pcb/footprint/pad and are LEAVES;
no known parent implicitly permits any descendant:
- uuid: one direct UUID value, existing UUID validation/uniqueness/membership.
- at: one direct field, three unquoted numeric literals; existing bounded Decimal
  cardinal gate, no nested values; required by the pose gate.
- size: one direct field, two positive unquoted numeric literals; existing pose gate.
- layers: one nonempty direct list of layer values, existing observation comparison.
- net, pintype, zone_connect: optional, at most one occurrence each, exactly one
  atom/string value, no descendants. Values/spans retained as semantics-unchecked;
  electrical and zone-fill behavior are NOT evaluated.
The eight existing modifier paths remain presence-blocked. All other paths fail
GEOMETRY_UNSUPPORTED before binding, retaining source hash, parent/pad UUID,
full ancestry path and offending node span/lines. Selected uuid/layers descendant
errors are deferred until EOF coverage can report the exact unsupported path;
nonselected structural rejection remains. No nested semantics are admitted.
Model 3D/offset outside the selected pads is not confused with pad modifiers.

Evidence: evaluation/kicad-reader/evidence/c1-c2-pad-coverage-portable-02/.
Implementer: 86 passed in 2.62s, exit 0; 43 pre/post input hashes unchanged.
Ran only coverage, source-pose, source-membership and artifact-binding test files.
The first run (portable-01: 84 passed) is preserved; portable-02 adds explicit
unknown-descendant regressions beneath uuid/layers and the diagnostic ordering fix.
Real PCB positive yields four candidates/16 oracle corners. Synthetic unknown-node
cases exercise the private scanner; real pin admission rejects synthetic bytes.
A failure-only test double proves early propagation before preflight/binding;
it is not evidence that altered PCB bytes pass hash admission.

This is implementer evidence, not review acceptance. Scope is declarations inside
four selected pads only. Footprint coverage, construct completeness, effective
copper and zone-fill semantics remain unverified. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL. No native/full suite, ZIP, commit or push.
Next action: review this coverage slice and its saved portable evidence.

### 2026-11-05 - C1+C2 pad coverage static review accepted

User relayed static review PASS for aoi-c1-c2-pad-coverage-review-5b271f9fd9d3.zip:
60 manifest hashes, 43 inputs (including the PCB outside the ZIP), the byte-exact
scanner baseline and its diff matched. The 86 PASS result is from the saved
implementer log; reviewer has not rerun the tests. This records user-relayed
review, not an attestation or a new verification run. Review-pending wording in
the preceding slice entry is historical and superseded by this acceptance.

Both evidence runs remain unchanged: c1-c2-pad-coverage-portable-01 records 84 PASS;
c1-c2-pad-coverage-portable-02 records 86 PASS. The two added cases cover unknown
descendants beneath uuid and layers, with the selected-pad diagnostic ordering
fix so coverage reports the unsupported ancestry path after EOF. Historical
recorded hashes and evidence have not been rewritten.

Acceptance covers descendants inside the four pinned C1+C2 pads only. net,
pintype and zone_connect retain values/spans with semantics-unchecked status.
Real PCB admission/binding, private synthetic scanner tests and failure-only
early-blocking test doubles remain distinct; doubles do not establish hash
admission for modified bytes. Footprint coverage, construct completeness,
effective copper geometry and zone-fill semantics remain unverified. No general
import readiness, publication or targeting authority is established.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; checkboxes unchanged.
Only HANDOFF and implementation status updated; no code/evidence changes,
tests/native runs, commit or push. Next implementation requires separate scope.

### 2026-11-06 - C1+C2 footprint layer/attr gate (review pending)

Evaluation scanner now retains direct footprint/layer and footprint/attr values,
raw literal bytes, byte spans and line spans for the two selected parents. Exactly
one leaf layer F.Cu and one leaf attr smd are required; missing/duplicate fields
fail SCHEMA_INVALID, unsupported values/extra attr flags/descendants fail
GEOMETRY_UNSUPPORTED before preflight/binding. At most two occurrences per field
are retained to detect duplicates, under existing scanner budgets. The source
layer is compared with the pinned observation footprint layer (SOURCE_CONFLICT
on disagreement). No inference from pad layers or native attribute integer.
Other footprint nodes are outside this gate; no whole-footprint coverage claim.

Changed c1_c2_source_membership.py; added test_c1_c2_footprint_fields.py.
Evidence: evaluation/kicad-reader/evidence/c1-c2-footprint-fields-portable-01/.
Implementer portable run: 98 passed in 3.30s, exit 0; 44 pre/post hashes unchanged.
Only footprint-fields, pad-coverage, source-pose, source-membership and
artifact-binding test files ran. Real r2 positive retains four candidates and
16 oracle corners. Synthetic B.Cu/extra attr, missing/duplicate/empty fields and
nested descendants reject. Scanner-record test doubles prove the downstream
field gate blocks before binding, not real hash admission; actual scan_pinned
rejects synthetic bytes. Nested model fields/unselected footprints are excluded.

Scope remains two declared fields of C1+C2 only. Broader footprint coverage,
construct completeness, effective copper and zone-fill semantics remain open.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. Existing evidence unchanged.
No native/full suite, ZIP, commit or push. Next action: review this slice/evidence.

### 2026-11-06 - C1+C2 footprint layer/attr static review accepted

User relayed static review PASS for aoi-c1-c2-footprint-fields-review-97e1d5568e82.zip:
54 manifest hashes, 44 inputs including the PCB outside the ZIP, the byte-exact
scanner baseline and its diff matched. The 98 PASS result comes from the saved
implementer log; reviewer has not rerun the tests. This records user-relayed
review, not an attestation or a new verification run. Earlier review-pending
wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/c1-c2-footprint-fields-portable-01/.

Acceptance covers only direct footprint/layer and footprint/attr of the two
pinned C1+C2 footprints. Real PCB admission with four candidates/16 oracle corners,
private synthetic scanner cases, and scanner-record test doubles remain distinct.
Test doubles demonstrate downstream early blocking, not real hash admission for
altered bytes. Broader footprint coverage, construct completeness, effective
copper geometry and zone-fill semantics remain unverified. No general import
readiness, publication or targeting authority is established.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; checkboxes unchanged.
Historical evidence is preserved. Only HANDOFF and implementation status updated;
no code/evidence changes, tests/native runs, commit or push.

### 2026-11-06 - C1+C2 non-pad footprint descendant coverage (review pending)

Updated evaluation scanner c1_c2_source_membership.py and added
test_c1_c2_footprint_coverage.py. Exact full ancestry paths from the two pinned
footprint source blocks are enumerated in FOOTPRINT_PATHS; known parents never
admit unknown children by prefix. Immutable records retain values, byte/line
spans, category and semantics status. Graphics/text layer values are separate
from footprint/pad layers. Direct pad subtrees retain their existing separate
gate. uuid/at/layer/attr gates are preserved; metadata, graphics/text and model-3d
remain semantics-unchecked. No model transform is applied to pads.

Post-EOF coverage rejects unclassified paths with GEOMETRY_UNSUPPORTED before
preflight/binding, including source hash, parent/pad UUID, full path and node span.
Existing depth/token-size/token-count budgets bound traversal and retained records.
Only selected footprint records survive scanning; unselected footprints are not
claimed covered. This is declaration-path coverage, not a KiCad semantic decoder.

Evidence: evaluation/kicad-reader/evidence/c1-c2-footprint-coverage-portable-01/.
Implementer run: 103 passed in 3.85s, exit 0; 45 pre/post input hashes unchanged.
Ran footprint-coverage, footprint-fields, pad-coverage, source-pose,
source-membership and artifact-binding portable test files only. Real PCB checks
all observed paths, graphics/text layer counts, four candidates and 16 corners.
Synthetic unknown nodes under property/effects/font, fp_line/stroke and
model/offset/xyz reject. Scanner-record doubles prove downstream blocking only;
real hash admission still rejects synthetic bytes. EOF rejection is retained.

Review pending. Construct completeness, effective copper geometry, graphics/text
and model semantics, electrical and zone-fill behavior remain unverified. No
import-ready/publication/targeting authority. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL. Historical evidence unchanged. No native/full suite,
ZIP, commit or push. Next action: review this slice and its portable evidence.

### 2026-11-06 - C1+C2 non-pad footprint coverage static review accepted

User relayed static review PASS for aoi-c1-c2-footprint-coverage-review-ca0d30c984e0.zip:
55 manifest hashes, 45 inputs including the PCB outside the ZIP, the byte-exact
scanner baseline and its diff matched. The 103 PASS result comes from the saved
implementer log; reviewer has not rerun the tests. This records user-relayed
review, not an attestation or a new verification run. Earlier review-pending
wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/c1-c2-footprint-coverage-portable-01/.

Acceptance covers declaration-path coverage of descendants outside pad subtrees
of exactly the two pinned C1+C2 footprints. Metadata, graphics/text and model 3D
remain semantics-unchecked; graphics/text layers are recorded separately. Real
PCB admission, private synthetic scanner cases and scanner-record early-blocking
test doubles remain distinct; doubles do not establish hash admission for altered
bytes. Construct completeness, effective copper geometry and zone-fill semantics
remain unverified. No general import readiness, publication or targeting authority
is established. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; checkboxes
and historical evidence unchanged. Only HANDOFF and implementation status updated;
no code/evidence changes, tests/native runs, commit or push.

### 2026-11-06 - C1+C2 graphics/text layer policy (review pending)

Updated evaluation scanner c1_c2_source_membership.py; added
test_c1_c2_graphics_layers.py. After existing field/coverage gates and before
preflight/binding, each fp_line/fp_circle requires exactly one direct layer in
F.SilkS/F.CrtYd. A property with any direct at/layer/effects requires exactly one
layer in F.SilkS/F.Fab; metadata-only properties may omit it. No inference from
hide or property name. Span-ordered traversal separates sibling instances in
linear work with at most two retained diagnostic layer records. Missing/duplicate
layers yield SCHEMA_INVALID; out-of-subset/malformed layer values yield
GEOMETRY_UNSUPPORTED, with parent UUID/hash/path and owner/layer spans.

Evidence: evaluation/kicad-reader/evidence/c1-c2-graphics-layers-portable-01/.
Implementer result: 124 passed in 4.35s, exit 0; 46 pre/post hashes unchanged.
Ran graphics-layers plus existing footprint-coverage/fields, pad-coverage,
source-pose/membership and artifact-binding portable tests only. Real r2 retains
four candidates/16 oracle corners. Synthetic F.Cu/Edge.Cuts, missing/duplicate
layers, display triggers and sibling isolation are checked. Metadata-only
properties pass without guessing from names/hide. Private scanner-record doubles
prove early blocking, not hash admission; real pin still rejects synthetic bytes.

This is the user-selected evaluation subset policy, not normative general KiCad
support. Graphics geometry/text rendering, effective copper, model, electrical
and zone-fill semantics remain unverified; recorded graphics/text semantics stay
unchecked beyond this layer declaration gate. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL. Review pending; historical evidence unchanged.
No native/full suite, ZIP, commit or push. Next action: review code/evidence.

### 2026-11-06 - C1+C2 graphics/text layer static review accepted

User relayed static review PASS for aoi-c1-c2-graphics-layers-review-b29a4d121826.zip:
56 manifest hashes, 46 inputs including the PCB outside the ZIP, the byte-exact
scanner baseline and its diff matched. The 124 PASS result is from the saved
implementer log; reviewer has not rerun the tests. This records user-relayed
review, not an attestation or a new verification run. Earlier review-pending
wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/c1-c2-graphics-layers-portable-01/.

Acceptance retains the agreed evaluation-only C1+C2 layer policy: each
fp_line/fp_circle has exactly one direct F.SilkS/F.CrtYd layer; a property with
any direct at/layer/effects requires exactly one F.SilkS/F.Fab layer. Metadata-only
properties may omit layer; neither hide nor property name determines display.
Real pinned PCB admission (four candidates/16 corners), synthetic scanner cases
and early-blocking test doubles remain distinct. Test doubles do not establish
hash admission for altered bytes. Graphics geometry/text rendering semantics,
effective copper, construct completeness and zone-fill semantics remain
unverified; this is not general import readiness, publication or targeting
authority. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; checkboxes and
historical evidence unchanged. Only HANDOFF and implementation status updated;
no code/evidence changes, tests/native runs, commit or push.

### 2026-11-06 - Source-checked request records/profile/preflight (review pending)

Implemented evaluation/kicad-reader/source_checked_preflight.py and its new
portable test_source_checked_preflight.py. Frozen/slotted records include the
contract input/output types; this slice only produces PreparationPreflightSuccess
or PreparationFailure. It never constructs PreparedRequest/SourceCheckEvidence,
scans PCB, performs geometry matching or calls binding/candidate execution.

Preflight checks exact record/nested types, the eight artifact IDs and declared
size/hash pins, four source pairs, exact policies/limits and internally consistent
successful inventory. One iterative ledger counts shared metadata nodes, UTF-8
bytes, reference occurrences and raw byte lengths. Fixed diagnostic fallback and
terminal budget reservation are reused. Existing geometry numeric fields retain
their integer-or-float behavior; integer policy limits reject bool. Success is
explicitly preflight-only-bytes-not-hash-verified: raw-byte digest recomputation
and source checks remain for the next phase, not implied by InventorySuccess.
Synthetic positive structural inputs intentionally have zero-filled bytes and
pinned metadata; they do not claim byte admission. A separate test uses real
inventory of the pinned PCB/artifacts. Exact/exceeded aggregate counter tests
exercise the ledger primitive, not full-profile admission at every aggregate cap.

Evidence: evaluation/kicad-reader/evidence/source-checked-preflight-portable-02/.
Implementer: 66 passed in 0.35s, exit 0; 74 pre/post input hashes unchanged and
rechecked against current files before this entry. Includes the external real PCB.
Only the new test file ran. Historical portable-01 retains 59 PASS/2 FAIL: the
PowerShell transfer converted the intended Unicode test literal to '?'; replacing
that setup literal with chr(0xE9) preserves the intended UTF-8 boundary assertion.
Five further focused tests were added for no hash-verification claim, shared refs,
depth, missing slots and rejected inventory. No old evidence was overwritten.

No production importer, source verification, receipt, candidates, publication or
new assurance is delivered by preflight. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13
remain PARTIAL. No native/full suite, ZIP, commit or push. Review pending; next
single action is review this preflight slice before enabling source preparation.

### 2026-11-06 - Source-checked preflight static review accepted

User relayed static review PASS for aoi-source-checked-preflight-review-6614d97ac74d.zip:
90 manifest hashes and 74 inputs matched SHA-256 and size, including the PCB outside
the ZIP. The 66 PASS result is from the saved implementer log; reviewer has not
rerun the tests. This records user-relayed review, not a new verification run or
attestation. Earlier review-pending wording for this slice is historical and
superseded by this acceptance. Evidence remains
 evaluation/kicad-reader/evidence/source-checked-preflight-portable-02/.

Acceptance is preflight-only: structural records, profile/pin declarations and
bounded metadata admission. No raw-byte hash verification, source scan, receipt
construction or binding/candidate execution is established. Synthetic zero-filled
inputs with pinned metadata are structural test doubles, not byte admission.
The separate real-inventory test uses the pinned PCB/artifacts. Ledger primitive
exact/exceeded tests do not establish full-profile admission at every budget cap.
Historical portable-01 (59 PASS/2 setup failures caused by Unicode literal transfer)
and its logs/hashes remain unchanged; the chr(0xE9) setup correction is documented.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. No source-verification,
import-ready, publication or targeting assurance is added. Only HANDOFF and
implementation status updated; no code/evidence changes, tests/native runs,
commit or push. Further preparation phases require a separately authorized slice.

### 2026-11-06 - Source-checked byte hash phase (review pending)

Added verify_source_checked_bytes in evaluation/kicad-reader/source_checked_preflight.py
and test_source_checked_bytes.py. The existing public structural preflight delegates
to a private checker accepting the operation-owned ledger. Byte verification creates
one ledger, runs that preflight, then hashes the exact eight immutable buffers in
artifact-ID order and compares digest/size against profile pins AND inventory.
Hash work is charged to a separate hashed_bytes counter on the same ledger (cap
1117036), and computed digest text consumes the existing shared metadata budget.
No source scan, receipt, prepared request, binding or candidate execution occurs.
Success status is bytes-match-pins-and-inventory-only; failures return no candidates.

Evidence: evaluation/kicad-reader/evidence/source-checked-bytes-portable-01/.
Implementer result: 81 passed in 0.61s, exit 0 (15 new byte tests plus 66 preflight
regressions); 75 pre/post input SHA-256/size records unchanged. Includes the real
external PCB and eight-artifact inventory case. Same-size one-byte mutations in
each artifact fail SOURCE_CONFLICT with actual/expected hash and artifact identity.
Spies prove rejected preflight blocks hashing and actual input buffer identity is
preserved. Synthetic zero-filled inputs still pass structural preflight and fail
hash verification. A private ledger test double demonstrates metadata-budget
exhaustion carries across phases; it is not real full-profile cap admission.

Review pending. Hash agreement does not prove source membership, source semantics,
backend authenticity, geometry completeness or import readiness. Tasks 1.5/5.2
and aggregate 3.4/5.5/5.13 remain PARTIAL. Historical evidence unchanged. No native,
full suite, ZIP, commit or push. Next action: review this byte-verification slice.

### 2026-11-07 - Source-checked byte hash phase static review accepted

User relayed static review PASS for aoi-source-checked-bytes-review-e30b2de76ca7.zip:
87 manifest hashes, 75 inputs matched by SHA-256 and size, and the byte-exact
preflight baseline and diff matched. The 81 PASS result comes from the saved
implementer log; reviewer has not rerun the tests. This records user-relayed
review, not an attestation or a new verification run. Earlier review-pending
wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/source-checked-bytes-portable-01/.

Acceptance is byte-verification-only: the exact eight immutable buffers match
profile pins and inventory computed hashes/sizes. One operation-owned ledger spans
structural preflight and hashing, retaining metadata and hash-work accounting.
Real pinned eight-artifact inventory tests, synthetic zero-filled buffers and the
private ledger-exhaustion test double remain distinct. Zero-filled buffers pass
structural preflight but fail hashing; the ledger double is not full-profile cap
admission evidence. Source scan, receipt construction and candidate execution are
later phases, not established here. Hash agreement does not establish source
membership, geometry completeness, backend authenticity or import readiness.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. Historical evidence and
checkboxes unchanged. Only HANDOFF and implementation status updated; no code or
evidence changes, tests/native runs, commit or push.

### 2026-11-07 - Source declarations phase (review pending)

Added evaluation/kicad-reader/source_checked_declarations.py and its portable tests.
Minimal shared helpers: source_checked_preflight._verify_bytes accepts the existing
operation-owned ledger; its public byte API still creates its own operation ledger.
c1_c2_source_membership.check_source_records holds the former source/observation/
request checks, reused by the unchanged evaluation binding flow. Optional private
scanner charge hook checks reconstructed record arguments before record construction
and retention; old callers keep the prior behavior. Transient scanner stack/tokens
retain their separate accepted depth/token bounds.

New check_source_declarations first completes all eight byte hash checks, then scans
the same PCB buffer to EOF, runs pad/modifier and footprint field/coverage/graphics
layer gates, compares strict-v2 observation and supplied declarations, and computes
four source Decimal poses. Shared ledger charges reconstructed metadata, including
repeated footprint occurrences, observation metadata and retained pose results.
SourceDeclarationCheckSuccess contains source records/poses and counters only: no
PreparedRequest, SourceCheckEvidence receipt, binding or candidates. Completeness,
effective copper, graphics/model and zone-fill semantics remain unverified.

Evidence: evaluation/kicad-reader/evidence/source-checked-declarations-portable-01/.
Implementer: 216 passed in 6.42s, exit 0; 77 pre/post SHA-256/size inputs unchanged.
11 new tests plus 81 preflight/hash and 124 affected C1+C2 regression tests. Real
pinned PCB positive checks four pads/16 oracle corners; supplied C2 center.x +0.001mm
fails SOURCE_CONFLICT with pose spans before later result collection/binding flow.
All eight artifact mutation cases prevent scanner entry. A private budget test
double fills the ledger after hashing and proves failure before reconstructed
footprint-record storage; it is not full-profile cap admission evidence.

Review pending; Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. Historical
evidence preserved. No native/full suite, ZIP, commit or push. Next action: review
the source-check intermediate slice before receipt/request preparation.

### 2026-11-07 - Source declarations phase static review accepted

User relayed static review PASS for aoi-source-checked-declarations-review-7fa6215e3cc9.zip:
93 manifest hashes, 77 inputs matched by SHA-256 and size (including the external
PCB), and both byte-exact baselines and their diffs matched. The 216 PASS result
comes from the saved implementer log; reviewer has not rerun the tests. This
records user-relayed review, not an attestation or a new verification run. Earlier
review-pending wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/source-checked-declarations-portable-01/.

Acceptance covers the source-check intermediate for the pinned C1+C2 four pads
and two footprints, with one shared ledger across preflight, byte verification
and reconstructed metadata accounting. Receipt/PreparedRequest construction and
binding/candidate execution remain later phases; no new publication or targeting
authority is established. Completeness and effective copper geometry remain
unverified, with graphics/model and zone-fill semantics still outside the checks.

Keep evidence categories distinct: the real pinned PCB case checks four pads and
16 oracle corners; the declaration-conflict case changes C2 center.x in memory
while preserving artifact bytes; hash-gate mutation cases block scanner entry;
the private budget test double demonstrates rejection before reconstructed record
storage, not real full-profile admission at the aggregate budget cap.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. Historical evidence and
checkboxes unchanged. Only HANDOFF and implementation status updated; no code or
evidence changes, tests/native runs, commit or push.


### 2026-11-07 - Boundary-record checks phase (review pending)

Added evaluation/kicad-reader/source_checked_boundaries.py and portable tests.
check_boundary_records uses one operation ledger across preflight, eight-buffer
hash verification, source declarations and boundary checks. Minimal extractions:
source_checked_declarations._check_source accepts that ledger; the public source
API still owns a fresh ledger. c1_c2_artifact_binding._records_from_verified is a
private reconstruction/comparison helper reused by the existing artifact flow;
its precondition is successful preflight and exact byte verification. Existing
artifact flow retains its hash admission and binding behavior.

The new phase checks pinned C1/C2 report stdout hashes and transport/cleanup
conditions, reconstructs exactly four boundary records by parent/pad UUID, retains
raw IU/order, normalizes Y once, and compares supplied boundary declarations
exactly. Parsed pinned metadata and reconstructed record/link arguments are charged
before retention/construction. JSON parsing remains bounded by exact artifact sizes;
this is not an arbitrary JSON decoder or runtime attestation. Budget rejection uses
the existing blocking diagnostic reservation and returns no partial records.
BoundaryRecordCheckSuccess contains source intermediate results, observed records,
artifact links and counters only: no receipt, PreparedRequest, binding or candidates.

Evidence: evaluation/kicad-reader/evidence/source-checked-boundaries-portable-01/.
Implementer run: 233 passed in 9.38s, exit 0; 79 pre/post inputs unchanged by SHA-256
and size. Includes 17 new tests plus the 216 affected preflight/hash/source/artifact
regressions. Real eight-artifact positive checks four raw records/16 literal oracle
corners and one ledger. A C2 vertex declaration mutation leaves artifacts unchanged
and yields SOURCE_CONFLICT with artifact/hash, parent/pad UUID and expected/actual.
Source conflict and hash failures block boundary checks; spies prohibit binding and
candidate calls in the new phase. Private report/transport mutation doubles exercise
link rejection without claiming byte admission; ledger exhaustion doubles prove
failure before record retention, not full-profile admission at the aggregate cap.

Review pending. Pinned C1+C2 only; completeness, effective copper, graphics/model
and zone-fill semantics remain unverified. Receipt/PreparedRequest and execution
remain later phases. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no
checkbox changes. Historical evidence preserved. No native/full suite, ZIP,
commit or push. Next action: review this intermediate boundary-record slice.


### 2026-11-13 - Boundary-record phase static review accepted

User relayed static review PASS for aoi-source-checked-boundaries-review-17e598edb8fe.zip:
95 manifest hashes, 79 inputs matched by SHA-256 and size (including the external
PCB), and both byte-exact baselines and their diffs matched. The 233 PASS result
is from the saved implementer log; reviewer has not rerun the tests. This records
user-relayed review, not an attestation or a new verification run. Earlier
review-pending wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/source-checked-boundaries-portable-01/.

Acceptance is limited to pinned C1+C2 boundary-record checks with one shared ledger
across preflight, byte hashing, source declarations and boundary checks. Raw IU/order,
single Y normalization and report/transport links remain explicit. Success is an
intermediate result only; receipt/PreparedRequest construction and binding/candidate
execution remain later phases. No import readiness or publication authority is implied.

Keep real eight-artifact evidence separate from the in-memory C2 vertex declaration
conflict, source/hash gating, spies prohibiting binding/candidate calls, and private
report/transport or budget test doubles. Completeness, effective copper geometry,
graphics/model and zone-fill semantics remain unverified. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL; checkboxes and historical evidence are unchanged.
Only HANDOFF and implementation status updated; no code/evidence changes,
tests/native runs, commit or push.
