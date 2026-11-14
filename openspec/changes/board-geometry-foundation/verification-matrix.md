# Verification & Acceptance Matrix

## Approved baseline and authority

Recorded 2026-11-14 against local `master` at
`f9b2fbf51978cf59164f784007941a3ad7d2cb3b`. The project owner approves the
**47/47 normative scenario inventory: 24 GEO-001 and 23 PCB-001** as the official
verification and acceptance baseline for `board-geometry-foundation`.
This approves completeness of inventory and acceptance scope; it does **not**
certify that all scenarios passed verification or grant blanket acceptance.

This matrix persists the latest session verification audit and owner decision.
The audit was reported in the preceding conversation, not a pre-existing tracked
audit report. Original normative authority remains the
[GEO-001 specification](specs/board-geometry/spec.md),
[PCB-001 specification](specs/pcb-data-import/spec.md),
[design acceptance gates](design.md#9-implementation-acceptance-levels) and
[original tasks](tasks.md). Existing bounded-scope acceptance remains valid.
No historical test is invalidated solely by a session, merge or branch change.
No task checkbox, specification or historical evidence is changed by this matrix.

The specifications identify capabilities as GEO-001 and PCB-001 and requirements
by their exact titles; they do not assign separate numeric requirement IDs.
G01-G24/P01-P23 below are stable **matrix row identifiers**, not invented normative
requirement IDs. Each row preserves its original scenario title and parent
requirement. Linked scenario text supplies the full GIVEN/WHEN/THEN criteria;
row summaries do not narrow those criteria. Task references are related work,
not claims that an entire task is complete.

## Reading and maintaining the matrix

- Implementation: IMPLEMENTED for the recorded scenario subset, PARTIAL or
  NOT IMPLEMENTED. Verification: VERIFIED, PARTIAL, UNVERIFIED or BLOCKED.
- Acceptance: SATISFIED for the already accepted specified Sprint 1 scenario
  scope; PARTIAL for bounded evidence/acceptance with remaining obligations;
  OPEN where the normative acceptance claim is not established. PARTIAL is not
  a new reviewer approval. In particular P20 remains OPEN despite partial code.
- Reuse: REUSABLE within unchanged evidenced scope; INSUFFICIENT for the full
  scenario; UNVERIFIABLE when no applicable executed evidence can be established.
  REUSABLE / INSUFFICIENT explicitly distinguishes subset reuse from full coverage.
- Bundle IDs E-* resolve implementation, tests/oracles, execution evidence and
  reviewer decisions below. NONE means no implementing evidence, not a test pass.
  Metadata-only bundles cannot establish runtime behavior.
- Before proposing test execution for any future implementation slice, consult
  affected matrix rows, their dependency/gate and existing evidence mappings.
  Reuse verified evidence first. Justify each rerun by changed source, dependency,
  fixture, oracle, environment or an identified coverage/provenance gap; a new
  session or branch name is not a justification.
- After verification, update affected mappings with exact command/node IDs,
  source/environment/fixture identity, results, evidence location, reviewer role
  and limitations. Keep verification and acceptance separate; acceptance changes
  need supported decisions. Preserve historical entries and use fresh evidence
  directories. Do not promote checkboxes implicitly.

## Normative scenario matrix

The evidence-bundle and historical-execution tables are part of every row that
references them. No historical execution totals are added together. Sprint and
Foundation gate summaries follow the evidence register.

| ID | Original requirement (capability ID + title) | Original scenario | Related tasks | Implementation / evidence bundle | Implementation | Verification | Acceptance | Reuse classification | Remaining gap / acceptance scope | Sprint gate / next step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01 | [GEO-001: Explicit coordinate frames and canonical units](specs/board-geometry/spec.md#requirement-explicit-coordinate-frames-and-canonical-units) | [Unit and axis conversion has an independently verified result](specs/board-geometry/spec.md#scenario-unit-and-axis-conversion-has-an-independently-verified-result) | 4.1-4.3 | E-G | IMPLEMENTED | VERIFIED | SATISFIED | REUSABLE | Independent (1,2) inch to (60.8,45.4) mm, 1e-6 mm and IDs; accepted Sprint 1 subset. | S1 retained; reuse |
| G02 | [GEO-001: Explicit coordinate frames and canonical units](specs/board-geometry/spec.md#requirement-explicit-coordinate-frames-and-canonical-units) | [Independent intermediate transformation oracles](specs/board-geometry/spec.md#scenario-independent-intermediate-transformation-oracles) | 4.1-4.4 | E-G | IMPLEMENTED | VERIFIED | SATISFIED | REUSABLE | Four literal forward and inverse checkpoints; round trips alone are insufficient. | S1 retained; reuse |
| G03 | [GEO-001: Explicit coordinate frames and canonical units](specs/board-geometry/spec.md#requirement-explicit-coordinate-frames-and-canonical-units) | [Different image sizes remain data-driven](specs/board-geometry/spec.md#scenario-different-image-sizes-remain-data-driven) | 3.1, 4.6 | E-G models only | PARTIAL | UNVERIFIED | OPEN | INSUFFICIENT | Frame dimensions exist; 640x480 and 2048x1536 calibration/capture validation and IMAGE_SIZE_MISMATCH remain missing. | S5 implement |
| G04 | [GEO-001: Explicit transform direction, composition, and inversion](specs/board-geometry/spec.md#requirement-explicit-transform-direction-composition-and-inversion) | [Composition and round trips](specs/board-geometry/spec.md#scenario-composition-and-round-trips) | 4.4 | E-G | IMPLEMENTED | VERIFIED | SATISFIED | REUSABLE | Noncommuting transforms, independent forward values and inverse physical error <=1e-6 mm. | S1 retained; reuse |
| G05 | [GEO-001: Explicit transform direction, composition, and inversion](specs/board-geometry/spec.md#requirement-explicit-transform-direction-composition-and-inversion) | [Unknown origin is not guessed](specs/board-geometry/spec.md#scenario-unknown-origin-is-not-guessed) | 4.5, 5.13 | E-G, E-D | PARTIAL | PARTIAL | PARTIAL | REUSABLE / INSUFFICIENT | Core missing-path/convention rejection reusable; Gerber/placement undeclared-origin integration remains missing. | S2-S4 integrate |
| G06 | [GEO-001: Explicit transform direction, composition, and inversion](specs/board-geometry/spec.md#requirement-explicit-transform-direction-composition-and-inversion) | [Invalid transform paths](specs/board-geometry/spec.md#scenario-invalid-transform-paths) | 4.5 | E-D | IMPLEMENTED | VERIFIED | SATISFIED | REUSABLE | Singular, ill-conditioned and ambiguous affine/DAG paths reject without partial batch; broader lifecycle is outside this accepted subset. | S1 retained; reuse |
| G07 | [GEO-001: Rotations and bottom-side parity](specs/board-geometry/spec.md#requirement-rotations-and-bottom-side-parity) | [Bottom mirror and orientation](specs/board-geometry/spec.md#scenario-bottom-mirror-and-orientation) | 4.2-4.3 | E-G | IMPLEMENTED | VERIFIED | SATISFIED | REUSABLE | Explicit x=5 mirror gives (8,3), 180 degrees and reflected parity; inverse and already-top-view bottom remain correct. | S1 retained; reuse |
| G08 | [GEO-001: Rotations and bottom-side parity](specs/board-geometry/spec.md#requirement-rotations-and-bottom-side-parity) | [Rotation wraparound](specs/board-geometry/spec.md#scenario-rotation-wraparound) | 4.3 | E-G | IMPLEMENTED | VERIFIED | SATISFIED | REUSABLE | 359.95/0.02 difference magnitude 0.07 degrees. | S1 retained; reuse |
| G09 | [GEO-001: Planar camera mapping and pixel semantics](specs/board-geometry/spec.md#requirement-planar-camera-mapping-and-pixel-semantics) | [Known planar projection](specs/board-geometry/spec.md#scenario-known-planar-projection) | 4.6 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Need (3,4) to (130,160) px, inverse and independent non-affine projective oracle. | S5 implement |
| G10 | [GEO-001: Planar camera mapping and pixel semantics](specs/board-geometry/spec.md#requirement-planar-camera-mapping-and-pixel-semantics) | [Nonlinear distortion and derived raster](specs/board-geometry/spec.md#scenario-nonlinear-distortion-and-derived-raster) | 4.7-4.8 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Lens solver/domain and explicit crop/resize oracle; <=1e-3 px round trip absent. | S5 implement |
| G11 | [GEO-001: Planar camera mapping and pixel semantics](specs/board-geometry/spec.md#requirement-planar-camera-mapping-and-pixel-semantics) | [Invalid projection or missing crop mapping](specs/board-geometry/spec.md#scenario-invalid-projection-or-missing-crop-mapping) | 4.6, 4.8 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Horizon denominator <=1e-12 rejection, missing parent transform and ROI clipping metadata absent. | S5 implement |
| G12 | [GEO-001: Fiducial registration quality](specs/board-geometry/spec.md#requirement-fiducial-registration-quality) | [Valid rigid and projective fits](specs/board-geometry/spec.md#scenario-valid-rigid-and-projective-fits) | 4.9-4.11 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Fit baseline >=10 mm, projective coverage >=10%, independent validation and explicit activation absent. | S5 implement |
| G13 | [GEO-001: Fiducial registration quality](specs/board-geometry/spec.md#requirement-fiducial-registration-quality) | [Degenerate or mismatched fiducials](specs/board-geometry/spec.md#scenario-degenerate-or-mismatched-fiducials) | 4.9-4.11 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Degeneracy, coverage, duplicate/wrong-side IDs, insufficient points and residual rejection fit tests absent. | S5 implement |
| G14 | [GEO-001: Fiducial registration quality](specs/board-geometry/spec.md#requirement-fiducial-registration-quality) | [Two points do not validate a camera homography](specs/board-geometry/spec.md#scenario-two-points-do-not-validate-a-camera-homography) | 4.9-4.10 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Separate rigid/homography fitting and insufficient-observation rejection absent; a pair cannot prove reflection detection. | S5 implement |
| G15 | [GEO-001: Fiducial registration quality](specs/board-geometry/spec.md#requirement-fiducial-registration-quality) | [Exact fit without independent validation](specs/board-geometry/spec.md#scenario-exact-fit-without-independent-validation) | 4.11-4.12 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | MAPPING_UNVALIDATED, no activation, blocked REVIEW/no usable ROIs or GOOD not implemented at inspection boundary. | S5 implement |
| G16 | [GEO-001: Configurable synthetic calibration policies](specs/board-geometry/spec.md#requirement-configurable-synthetic-calibration-policies) | [Policy changes and invalid values](specs/board-geometry/spec.md#scenario-policy-changes-and-invalid-values) | 3.3, 4.13 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Versioned calibration policy, revalidation and POLICY_INVALID contract absent. | S5 implement |
| G17 | [GEO-001: Configurable synthetic calibration policies](specs/board-geometry/spec.md#requirement-configurable-synthetic-calibration-policies) | [Synthetic pass cannot certify production accuracy](specs/board-geometry/spec.md#scenario-synthetic-pass-cannot-certify-production-accuracy) | 4.14 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Production purpose/context rejection and blocked REVIEW without synthetic fallback absent. | S5 implement |
| G18 | [GEO-001: Configurable synthetic calibration policies](specs/board-geometry/spec.md#requirement-configurable-synthetic-calibration-policies) | [Invalid mapping at the inspection boundary](specs/board-geometry/spec.md#scenario-invalid-mapping-at-the-inspection-boundary) | 3.7, 4.12 | E-D | PARTIAL | PARTIAL | PARTIAL | INSUFFICIENT | Core typed rejection exists; BuildInspectionInput REVIEW/reasons/no ROIs and stale lifecycle coverage absent. | S5 integrate |
| G19 | [GEO-001: Calibration and registration lifecycle isolation](specs/board-geometry/spec.md#requirement-calibration-and-registration-lifecycle-isolation) | [Six machines share processing without sharing geometry](specs/board-geometry/spec.md#scenario-six-machines-share-processing-without-sharing-geometry) | 4.18 | E-G, E-D | PARTIAL | PARTIAL | PARTIAL | INSUFFICIENT | Context-bound frames exist; six camera/calibration/load namespaces with colliding capture names not implemented/verified. | S5 implement |
| G20 | [GEO-001: Calibration and registration lifecycle isolation](specs/board-geometry/spec.md#requirement-calibration-and-registration-lifecycle-isolation) | [Configuration or load changes](specs/board-geometry/spec.md#scenario-configuration-or-load-changes) | 4.13 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Activation/invalidation, stale mapping rejection and reproducible historical replay absent. | S5 implement |
| G21 | [GEO-001: Separate board capacity, fixture and camera travel](specs/board-geometry/spec.md#requirement-separate-board-capacity-fixture-and-camera-travel) | [Exact fit, rotation, and overrun](specs/board-geometry/spec.md#scenario-exact-fit-rotation-and-overrun) | 4.15 | E-F | IMPLEMENTED | VERIFIED | SATISFIED | REUSABLE | 280x550 at 0 and 550x280 at 90 pass; 280.001x550 fails; translation invariant. | S1 retained; reuse |
| G22 | [GEO-001: Separate board capacity, fixture and camera travel](specs/board-geometry/spec.md#requirement-separate-board-capacity-fixture-and-camera-travel) | [Synthetic fixture fit is independent of capacity](specs/board-geometry/spec.md#scenario-synthetic-fixture-fit-is-independent-of-capacity) | 4.16 | E-F | IMPLEMENTED | VERIFIED | SATISFIED | REUSABLE | Whole-outline synthetic rectangle contact/margin/exclusion checks; fixture failure independent of capacity and camera defaults. | S1 retained; reuse |
| G23 | [GEO-001: Separate board capacity, fixture and camera travel](specs/board-geometry/spec.md#requirement-separate-board-capacity-fixture-and-camera-travel) | [Unresolved mechanics does not invent readiness](specs/board-geometry/spec.md#scenario-unresolved-mechanics-does-not-invent-readiness) | 4.17 | E-F | PARTIAL | PARTIAL | PARTIAL | REUSABLE / INSUFFICIENT | Standalone unresolved fit/reachability verified; real import integration missing; rectangle alone never proves optical coverage. | S2 integrate; Prototype |
| G24 | [GEO-001: Separate board capacity, fixture and camera travel](specs/board-geometry/spec.md#requirement-separate-board-capacity-fixture-and-camera-travel) | [Complete coordinate verification without hardware](specs/board-geometry/spec.md#scenario-complete-coordinate-verification-without-hardware) | 6.5 | E-G, E-D, E-F | PARTIAL | PARTIAL | PARTIAL | INSUFFICIENT | Offline fixed-seed affine/rigid and independent oracles exist; complete projective cases and capability suite absent. | S5; Complete |
| P01 | [PCB-001: Verified input support evidence](specs/pcb-data-import/spec.md#requirement-verified-input-support-evidence) | [Unverified versions remain TBD](specs/pcb-data-import/spec.md#scenario-unverified-versions-remain-tbd) | 1.5, 5.2, 6.3 | E-A, E-N | PARTIAL | PARTIAL | PARTIAL | INSUFFICIENT | Register remains bounded/TBD; general product version allowlist and FORMAT_UNSUPPORTED gates not implemented. | S2 support gate |
| P02 | [PCB-001: Declared source formats and import profiles](specs/pcb-data-import/spec.md#requirement-declared-source-formats-and-import-profiles) | [Complete combined import](specs/pcb-data-import/spec.md#scenario-complete-combined-import) | 5.16-5.17 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | One immutable revision with both profile capabilities, hashes, mappings and accepted report absent. | S4; Prototype |
| P03 | [PCB-001: Declared source formats and import profiles](specs/pcb-data-import/spec.md#requirement-declared-source-formats-and-import-profiles) | [Missing or unsupported input](specs/pcb-data-import/spec.md#scenario-missing-or-unsupported-input) | 5.1-5.2, 5.16 | E-I | PARTIAL | PARTIAL | PARTIAL | REUSABLE / INSUFFICIENT | Byte inventory enforces required roles; parser/version/profile semantics and no-publication integration incomplete. | S2-S4 integrate |
| P04 | [PCB-001: Declared source formats and import profiles](specs/pcb-data-import/spec.md#requirement-declared-source-formats-and-import-profiles) | [Geometry-only import](specs/pcb-data-import/spec.md#scenario-geometry-only-import) | 3.5, 5.16-5.17 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Canonical geometry publication and later unfulfilled-profile inspection rejection absent. | S2 implement |
| P05 | [PCB-001: Per-source units, origin, side, and revision evidence](specs/pcb-data-import/spec.md#requirement-per-source-units-origin-side-and-revision-evidence) | [Independent Gerber and placement origins](specs/pcb-data-import/spec.md#scenario-independent-gerber-and-placement-origins) | 5.13 | E-G | PARTIAL | PARTIAL | PARTIAL | INSUFFICIENT | Transform math reusable; real Gerber (50,25) mm offset and inch-placement independent source alignment/removal tests absent. | S3-S4 integrate |
| P06 | [PCB-001: Per-source units, origin, side, and revision evidence](specs/pcb-data-import/spec.md#requirement-per-source-units-origin-side-and-revision-evidence) | [Contradictory units or side](specs/pcb-data-import/spec.md#scenario-contradictory-units-or-side) | 5.13 | E-G, E-P, E-S | PARTIAL | PARTIAL | PARTIAL | INSUFFICIENT | Pinned source conflicts/declarations checked; general import inch/mm and bottom/top metadata conflict integration absent. | S2-S4 integrate |
| P07 | [PCB-001: Canonical outline, footprints, components, pads, and fiducials](specs/pcb-data-import/spec.md#requirement-canonical-outline-footprints-components-pads-and-fiducials) | [Bottom footprint and repeated pad numbers](specs/pcb-data-import/spec.md#scenario-bottom-footprint-and-repeated-pad-numbers) | 5.3-5.5 | E-P, E-B, E-N, E-S | PARTIAL | PARTIAL | PARTIAL | INSUFFICIENT | Candidate repeated-number IDs/oracles and pinned boundary checks reusable; combined rotated-bottom/nonrectangular/cutout product import absent. | S2 implement |
| P08 | [PCB-001: Canonical outline, footprints, components, pads, and fiducials](specs/pcb-data-import/spec.md#requirement-canonical-outline-footprints-components-pads-and-fiducials) | [Invalid outline or nonfinite coordinate](specs/pcb-data-import/spec.md#scenario-invalid-outline-or-nonfinite-coordinate) | 5.3, 5.5 | E-F, E-P, E-N | PARTIAL | PARTIAL | PARTIAL | REUSABLE / INSUFFICIENT | Topology/numeric/duplicate controls exist for bounded subsets; complete source-entity diagnostics before product publication missing. | S2 integrate |
| P09 | [PCB-001: Canonical outline, footprints, components, pads, and fiducials](specs/pcb-data-import/spec.md#requirement-canonical-outline-footprints-components-pads-and-fiducials) | [Fiducial approval](specs/pcb-data-import/spec.md#scenario-fiducial-approval) | 5.6 | E-A metadata only | NOT IMPLEMENTED | UNVERIFIED | OPEN | INSUFFICIENT | Accepted fixture designation is not importer classification/approval retaining all fiducial fields; circular pads must not auto-promote. | S2 implement |
| P10 | [PCB-001: Gerber parser reuse evaluation](specs/pcb-data-import/spec.md#requirement-gerber-parser-reuse-evaluation) | [Reuse evaluation precedes a custom parser](specs/pcb-data-import/spec.md#scenario-reuse-evaluation-precedes-a-custom-parser) | 2.1-2.5 | NONE | NOT IMPLEMENTED | BLOCKED | OPEN | UNVERIFIABLE | Pinned PyGerber/Gerbonara license/API/geometry/provenance/resource/fixture evaluation must precede custom-parser decision. | S3 prerequisite |
| P11 | [PCB-001: Gerber parser reuse evaluation](specs/pcb-data-import/spec.md#requirement-gerber-parser-reuse-evaluation) | [Library cannot interpret a construct](specs/pcb-data-import/spec.md#scenario-library-cannot-interpret-a-construct) | 2.4, 5.8 | NONE | NOT IMPLEMENTED | BLOCKED | OPEN | UNVERIFIABLE | Dependency/support matrix absent; unsupported constructs need source-location FORMAT_UNSUPPORTED and no publication. | S3 after P10 |
| P12 | [PCB-001: Manufactured paste geometry](specs/pcb-data-import/spec.md#requirement-manufactured-paste-geometry) | [Paste reductions, split apertures, and clear regions](specs/pcb-data-import/spec.md#scenario-paste-reductions-split-apertures-and-clear-regions) | 5.7-5.9 | NONE | NOT IMPLEMENTED | BLOCKED | OPEN | UNVERIFIABLE | Filled-geometry oracle for two windows plus clear opening and unchanged copper absent; reuse gate first. | S3 after P10 |
| P13 | [PCB-001: Manufactured paste geometry](specs/pcb-data-import/spec.md#requirement-manufactured-paste-geometry) | [Unmatched paste feature](specs/pcb-data-import/spec.md#scenario-unmatched-paste-feature) | 5.9 | NONE | NOT IMPLEMENTED | BLOCKED | OPEN | UNVERIFIABLE | Retain unmatched feature/warning without fabricated ID; unresolved registration must block; adapter/reuse dependency absent. | S3 after P10 |
| P14 | [PCB-001: Placement and BOM joins with explicit authority](specs/pcb-data-import/spec.md#requirement-placement-and-bom-joins-with-explicit-authority) | [Valid grouped BOM and DNP](specs/pcb-data-import/spec.md#scenario-valid-grouped-bom-and-dnp) | 5.11-5.12 | E-A metadata only | NOT IMPLEMENTED | UNVERIFIED | OPEN | INSUFFICIENT | Fixture population metadata does not implement R1-R3 expansion/quantity/DNP coverage with geometry retained. | S4 implement |
| P15 | [PCB-001: Placement and BOM joins with explicit authority](specs/pcb-data-import/spec.md#requirement-placement-and-bom-joins-with-explicit-authority) | [Conflicting assembly records](specs/pcb-data-import/spec.md#scenario-conflicting-assembly-records) | 5.10-5.12 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Duplicate R1, unresolved U99, quantity 2 vs 3, wrong side and 0.2 mm disagreement require source-row rejection evidence. | S4 implement |
| P16 | [PCB-001: Placement and BOM joins with explicit authority](specs/pcb-data-import/spec.md#requirement-placement-and-bom-joins-with-explicit-authority) | [Reviewed field override](specs/pcb-data-import/spec.md#scenario-reviewed-field-override) | 5.14 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Field authority/source/reason/reviewer plus originals and warning absent; unrelated errors must remain blocking. | S4 implement |
| P17 | [PCB-001: Immutable revisions and deterministic provenance](specs/pcb-data-import/spec.md#requirement-immutable-revisions-and-deterministic-provenance) | [Reproducible import and reused labels](specs/pcb-data-import/spec.md#scenario-reproducible-import-and-reused-labels) | 3.5, 5.18 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Immutable content digest independent of paths/time, changed-transform identity and acknowledged reused label absent. | S2/S4 implement |
| P18 | [PCB-001: Immutable revisions and deterministic provenance](specs/pcb-data-import/spec.md#requirement-immutable-revisions-and-deterministic-provenance) | [Mixed board exports](specs/pcb-data-import/spec.md#scenario-mixed-board-exports) | 5.15 | E-I byte evidence only | NOT IMPLEMENTED | UNVERIFIED | OPEN | INSUFFICIENT | Matching hashes/names/dimensions do not establish cross-export revision attestation or semantic consistency. | S4 implement |
| P19 | [PCB-001: Independent data import and physical readiness](specs/pcb-data-import/spec.md#requirement-independent-data-import-and-physical-readiness) | [Valid board with unresolved physical envelopes](specs/pcb-data-import/spec.md#scenario-valid-board-with-unresolved-physical-envelopes) | 4.17, 5.17 | E-F | PARTIAL | PARTIAL | PARTIAL | INSUFFICIENT | Separate unresolved reports exist; immutable import publication/provenance integration absent; no targeting or production claim. | S2; Prototype |
| P20 | [PCB-001: Atomic contracts and actionable validation reports](specs/pcb-data-import/spec.md#requirement-atomic-contracts-and-actionable-validation-reports) | [Multiple errors and rollback](specs/pcb-data-import/spec.md#scenario-multiple-errors-and-rollback) | 3.6, 5.17 | E-D, E-I, E-P | PARTIAL | PARTIAL | OPEN | INSUFFICIENT | Stable diagnostics and bounded atomic results exist; BOM/placement multi-error collection and revision rollback absent. Explicitly OPEN in status ledger. | S2-S4 integrate |
| P21 | [PCB-001: Atomic contracts and actionable validation reports](specs/pcb-data-import/spec.md#requirement-atomic-contracts-and-actionable-validation-reports) | [Import bounds and parsing settings](specs/pcb-data-import/spec.md#scenario-import-bounds-and-parsing-settings) | 5.1, 1.6 | E-I, E-S | PARTIAL | PARTIAL | PARTIAL | REUSABLE / INSUFFICIENT | Byte/scanner shared-budget rejection reusable; full entity limits and ambiguous CSV decimal/delimiter rejection absent. | S2-S4 integrate |
| P22 | [PCB-001: Optional inspection-engine interoperability](specs/pcb-data-import/spec.md#requirement-optional-inspection-engine-interoperability) | [Adapter absent](specs/pcb-data-import/spec.md#scenario-adapter-absent) | 6.1, 6.5 | E-G, E-I, E-P, E-B | PARTIAL | PARTIAL | PARTIAL | INSUFFICIENT | Existing portable subsets run offline; complete GEO/PCB normative suite and optional-engine evaluation still absent. | S5; Complete |
| P23 | [PCB-001: Optional inspection-engine interoperability](specs/pcb-data-import/spec.md#requirement-optional-inspection-engine-interoperability) | [Engine changes image frame](specs/pcb-data-import/spec.md#scenario-engine-changes-image-frame) | 6.2, 4.8 | NONE | NOT IMPLEMENTED | UNVERIFIED | OPEN | UNVERIFIABLE | Fake-engine crop/alignment mapping, revision/capture mismatch and pixel-vs-mm checks absent. | S5 implement |

## Implementation, oracle and review bundles

These are bounded evidence mappings, not a claim that all tests in a file prove
every referencing scenario. Exact saved executions are in the next section.
Historical reviewer decisions are principally user-relayed; recording them does
not manufacture an independent reviewer attestation or a new execution.

| Bundle | Current implementation and test/oracle references | Execution mapping, review decision and limits |
| --- | --- | --- |
| E-G | [transforms](../../../src/aoi_platform/geometry/transforms.py), [angles](../../../src/aoi_platform/geometry/angles.py), [models](../../../src/aoi_platform/geometry/models.py); [transform tests](../../../tests/test_transforms.py): `test_required_chain_and_independent_inverse_checkpoints`, `test_bottom_reflection_preserves_angle_and_parity_semantics`, `test_bottom_named_source_is_not_automatically_mirrored`, `test_noncommuting_transforms_apply_inner_first`, `test_affine_shear_oracle_inverse_and_orientation`; [angle tests](../../../tests/test_angles.py): `test_signed_difference_has_explicit_order`. Literal stage/angle/mirror oracles and seeded cases (seed 1007) accompany round trips. | H268/H295/H370/H491; selected affine/DAG Sprint 1 exit and decisions 1.1/1.2 accepted in chat as relayed by owner. Frame types do not implement camera fitting, calibration lifecycle or complete projective verification. |
| E-D | [resolver](../../../src/aoi_platform/geometry/resolver.py), [reports](../../../src/aoi_platform/geometry/reports.py); [resolver tests](../../../tests/test_resolver.py): `test_disagreeing_path_fails_at_rectangle_vertex`, `test_missing_domain_policy_and_pixel_are_explicit`, `test_unvalidated_edge_is_rejected_and_resource_limit_never_returns_partial`; [diagnostics](../../../tests/test_diagnostics.py), [resolver regressions](../../../tests/test_resolver_review_regressions.py), [report tests](../../../tests/test_reports.py): `test_all_discoverable_numeric_failures_keep_source_and_context`, `test_order_and_serialization_are_independent_of_discovery_and_ties`. | H295/H370/H491; accepted core subset. Stable report ordering is not BOM parsing, ValidateImport rollback or BuildInspectionInput REVIEW. Task 3.6 and P20 remain open. |
| E-F | [envelopes](../../../src/aoi_platform/geometry/envelopes.py), [fixture geometry](../../../src/aoi_platform/geometry/fixture_geometry.py), [outlines](../../../src/aoi_platform/geometry/outlines.py); [envelope tests](../../../tests/test_envelopes.py): `test_capacity_required_oracles`, `test_machine_translation_does_not_affect_capacity`, `test_fixture_exact_outer_contact_and_small_violation`, `test_outer_margin_exact_and_one_micron_shortfall`, `test_missing_physical_envelopes_never_imply_readiness`, `test_supplied_camera_rectangle_still_unresolved_with_evidence`; [fixture tests](../../../tests/test_fixture_geometry.py). | H268/H295/H370/H491; accepted selected line/arc board-contour and rectangular fixture/exclusion subset. Physical dimensions remain TBD; broader holes/envelopes are not implied. Standalone unresolved report does not prove product import publication. |
| E-I | [inventory](../../../src/aoi_platform/inventory.py); [tests](../../../tests/test_inventory.py): `test_profile_minimums_and_multiple_artifacts_same_role`, `test_hash_and_size_mismatch_expected_actual_context_and_order`, `test_boundaries_streaming_short_reads_and_ownership`, `test_failure_after_successful_read_is_not_partial_success`; [local test](../../../tests/test_inventory_local.py): `test_real_pcb_01_r1_bytes`. | H370/H491; byte-admission slice accepted after direct ZIP review (user-relayed 370 PASS/1 SKIP and 1,200 independent cases). Local REAL-PCB-01-r1: 25 entries, 2,454,516 bytes; local 1 PASS was not rerun by reviewer. Hash/role checks do not certify geometry, revision equivalence or parser support. |
| E-P | [pad candidates](../../../src/aoi_platform/pad_candidates.py), [tests](../../../tests/test_pad_candidates.py): `test_independent_oracles`, `test_repeated_empty_numbers_and_lexical_order`, `test_mixed_batch_atomic_and_diagnostic_order`; independent 0/90/45-degree corner oracles, repeated/empty source numbers, atomic rejects. | H470/H30; accepted rectangular candidate subset via user-relayed review. 100 focused tests are included in the 470-pass full run. This is not a complete KiCad importer or effective-copper implementation. |
| E-B | [boundary evidence](../../../src/aoi_platform/boundary_evidence.py), [correspondence](../../../src/aoi_platform/boundary_correspondence.py), [binding](../../../src/aoi_platform/boundary_binding.py); [preflight](../../../tests/test_boundary_preflight.py), [binding tests](../../../tests/test_boundary_binding.py), [correspondence tests](../../../tests/test_boundary_correspondence.py), [orchestration](../../../tests/test_boundary_orchestration.py). Eight independent order oracles, exact/exceeded 1e-6 component tolerance, identity conflicts and one-call/atomic batch controls. | Bounded historical reviews in [implementation status](implementation-status.md), plus H30 smoke. Dataclass contracts `SourceCheckEvidence`/`PreparedRequest` exist; complete receipt/request construction API does not. Binding/candidate acceptance is not source provenance certification. |
| E-S | [source preflight/hash](../../../evaluation/kicad-reader/source_checked_preflight.py), [declarations](../../../evaluation/kicad-reader/source_checked_declarations.py), [boundaries](../../../evaluation/kicad-reader/source_checked_boundaries.py); [preflight tests](../../../evaluation/kicad-reader/test_source_checked_preflight.py), [byte tests](../../../evaluation/kicad-reader/test_source_checked_bytes.py), [declaration tests](../../../evaluation/kicad-reader/test_source_checked_declarations.py), [boundary tests](../../../evaluation/kicad-reader/test_source_checked_boundaries.py), plus seven C1/C2 modules in H233 invocation. | H233 and its earlier 66/81/216-test subsets. Latest reviewer performed static review of 95 manifest entries/79 inputs and saved 233 results, not a rerun. Positive four raw record links share one ledger; eight-artifact hash failures stop scanning, source conflicts stop later boundary checks, and link/record budgets charge before retention. C2 +0.001 conflict is a negative control. No receipt construction or general source semantics acceptance. |
| E-N | [KiCad reader evaluation](../../../evaluation/kicad-reader/), [Windows runner evidence](../../../evaluation/windows_runner/evidence/), source-checked and C1/C2 fixtures, saved outline/cutout controls. | Historical native evidence only; no native execution in this task. C1 strict saved success; C2 transport/cleanup/boundary success uses 1 IU tolerance and two pads. Cutout control: 8 checks/8 source segments and no footprints. Earlier `kicad-local-01` is a failed control (transport false, hash mismatch true), not a passing baseline. General copper/graphics/model/zone-fill semantics remain unverified. |
| E-R | [runner](../../../evaluation/windows_runner/runner.py), [portable tests](../../../evaluation/windows_runner/test_portable.py), [native runner tests](../../../evaluation/windows_runner/test_native.py), [provenance limitations](../../../evaluation/windows_runner/PROVENANCE-LIMITATIONS.md). | H491 includes 57 portable and 41 native-runner regression cases; no accepted real KiCad board executed in that regression run. Later bounded runner/harness review acceptance remains scoped in status. Pre-assignment host-death gap and unrecovered historical versions remain; do not substitute current source for missing historical source. |
| E-A | [supported inputs](supported-inputs.md), [implementation/review history](implementation-status.md), REAL-PCB-01-r1 gate 7.1 and r2 population metadata. | Fixture acquisition/metadata acceptance remains valid. The older r2 pending-review note is superseded by later metadata-only acceptance in status; neither establishes parser support. No fiducial classifier, BOM parser or DNP import acceptance follows from metadata. |

## Historical execution register and reuse limits

No tests were executed to persist this document. The latest read-only audit
checked saved reports, manifests, source ancestry and test inventories. Audit
checks described here are historical audit findings, not newly run tests.
Missing provenance reduces the strength of a new claim; it does not automatically
revoke an existing bounded reviewer decision.

| Execution | Recorded result / scope | Evidence and execution identity | Review / reuse limit |
| --- | --- | --- | --- |
| H268 | 268 PASS, 0.42 s, exit 0, 2026-10-17; geometry/fixture suite | [Status history](implementation-status.md): `.venv/Scripts/python.exe -m pytest -q`; capacity commit `2980f65`, earlier baseline `1132718`. | Documentary run report. Exact original node inventory/environment not recovered; later H491 supplies overlapping durable case evidence. Do not infer every H268 parameter from a modern suite. |
| H295 | 295 PASS, 0.55 s, exit 0, 2026-10-17; diagnostics/resolver follow-up | [Status history](implementation-status.md), commit `c459fc9`; same recorded full-suite command. | Existing 268 plus regressions; selected Sprint 1 review accepted subsequently. Source changed from H268: envelopes/errors/models/reports/resolver and diagnostics tests; do not label those two snapshots identical. |
| H370 | 370 PASS/1 SKIP, 0.66 s, exit 0; separate opt-in local 1 PASS, 0.20 s | [Inventory execution/review record](implementation-status.md), inventory commit `4e59ad9`; `.venv/Scripts/python.exe -m pytest -q`; separate `tests/test_inventory_local.py` with `AOI_REAL_PCB_01_ROOT` pointing at accepted r1 fixture. | 1,200 independent passing cases are user-relayed reviewer results; no independent node inventory recovered. Reviewer did not rerun local bundle test. Skip is local-fixture opt-in, not an inventory-contract waiver. |
| H470 | Focused 100 PASS, 4.38 s; full 470 PASS/1 SKIP, 4.98 s; exits 0 | [Focused invocation](../../../evaluation/pad-candidate/evidence/canonical-pad-candidate-02/focused/invocation.json), [focused result](../../../evaluation/pad-candidate/evidence/canonical-pad-candidate-02/focused/result.json), [full invocation](../../../evaluation/pad-candidate/evidence/canonical-pad-candidate-02/full/invocation.json), [full result](../../../evaluation/pad-candidate/evidence/canonical-pad-candidate-02/full/result.json), [review verification](../../../evaluation/pad-candidate/evidence/canonical-pad-candidate-review-02/verification.json). Review metadata Python 3.11.9, base `f77efa1` with working changes later committed as `0cb4a5d`. | User-relayed direct ZIP review accepted candidates; reviewer-reported 470/1, 74/74 manifest hashes, 28/28 pre/post hashes and six baselines. Focused 100 is a subset, not 100 additional full-run cases. Environment provenance is not complete for every patch execution. |
| H491 | 491 PASS/1 SKIP, 17.99 s; 492 JUnit cases | [Command/environment](../../../evaluation/windows_runner/evidence/review-03/environment-command.json), [stdout](../../../evaluation/windows_runner/evidence/review-03/pytest.stdout.txt), [JUnit](../../../evaluation/windows_runner/evidence/review-03/pytest.xml). Python 3.11.9, Windows 10.0.26300 AMD64, runner work against `4e59ad9`; pytest version not recorded there. | Saved implementer runner/product regression. JUnit verifies case-level results; 370 product passes, 23 harness, 57 portable runner, 41 native runner; one local skip. Earlier review-pending text is historical, later bounded reviewer decisions do not grant blanket runner or parser acceptance. |
| H233 | 233 PASS, 9.38 s, exit 0; source-checked boundary slice | [Exact invocation](../../../evaluation/kicad-reader/evidence/source-checked-boundaries-portable-01/invocation.json), [result](../../../evaluation/kicad-reader/evidence/source-checked-boundaries-portable-01/result.json), [stdout](../../../evaluation/kicad-reader/evidence/source-checked-boundaries-portable-01/stdout.txt), [input hashes](../../../evaluation/kicad-reader/evidence/source-checked-boundaries-portable-01/pre-run-hashes.json); checkpoint tip `3262563`. | Saved implementer output; latest reviewer static review did not rerun. Per-run OS/Python/pytest environment not fully recorded. Node cache needs saved result/stdout corroboration; it alone does not prove PASS. |
| H30 | 30 PASS, 0 FAIL, 0 SKIP, 0.23 s, exit 0; post-merge smoke at `f9b2fbf` | Prior session transcript only; Python 3.11.9, pytest 9.1.1, win32. `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -v --tb=short` with selections below. | Agent execution in earlier smoke task, not a durable repository log and not a rerun in this documentation task. Small integration smoke does not establish full import/Foundation acceptance. |

H491's exact command and JUnit retain parametrized test identities. Its module
case counts are: angles 19, diagnostics 27, envelopes 78, fixture geometry 21,
inventory 75, inventory-local 1, models 21, reports 16, resolver 9,
resolver-review regressions 24, transform-validation regressions 42, transforms
38, harness 23, runner-portable 57 and runner-native 41. One inventory-local case
is skipped. H470 full and H491 overlap in 371 case identities (370 PASS + 1 SKIP);
they are not independent additive coverage totals.

H233's eleven module case counts: artifact binding 9, footprint coverage 5,
footprint fields 12, graphics/layers 21, pad coverage 18, source membership 40,
source pose 19, source-checked boundaries 17, bytes 15, declarations 11 and
preflight 66. Earlier source-checked runs nest as 66 subset 81 subset 216 subset
233. Those are reused/regression cases, not 666 distinct validations.

H30 exact selected functions and expanded case counts:

| Test file | Selection | Cases |
| --- | --- | --- |
| [pad candidates](../../../tests/test_pad_candidates.py) | `test_independent_oracles` (0, 90, 45 degrees); `test_repeated_empty_numbers_and_lexical_order`; `test_mixed_batch_atomic_and_diagnostic_order` | 3 + 1 + 1 |
| [boundary preflight](../../../tests/test_boundary_preflight.py) | `test_preflight_only_immutable_no_candidate_call` | 1 |
| [boundary binding](../../../tests/test_boundary_binding.py) | `test_positive_declaration_only_nonmutation`; `test_conflicting_identity` (canonical pad/parent and source pad/parent IDs) | 1 + 4 |
| [boundary correspondence](../../../tests/test_boundary_correspondence.py) | `test_eight_independent_order_oracles` (0-7); `test_exact_and_exceeded_component_tolerance` (exact 1e-6 and next representable value) | 8 + 2 |
| [boundary orchestration](../../../tests/test_boundary_orchestration.py) | Entire module: `test_independent_oracle_and_single_call`, `test_binding_failure_blocks_candidate`, `test_one_bad_pad_rejects_whole_batch` (mismatch, ambiguity), `test_convex_does_not_replace_candidate_admission`, `test_explicit_boundary_transform_guards` (affine, unvalidated, bound), `test_sorted_all_batch_success` | 9 |

### Audit identity checks and unresolved provenance

- At the latest audit, current source/tests/evaluation matched checkpoint commit
  `3262563` (an ancestor), despite the checkpoint branch ref no longer appearing
  locally/remotely. Branch label absence does not erase reachable history.
  Geometry/inventory source and tests matched `4e59ad9`; merge ancestry alone was
  not used as proof of byte identity. Local `origin/master` equaled `f9b2fbf`;
  this is a local-ref observation, not a live remote query.
- [Candidate pre-run hashes](../../../evaluation/pad-candidate/evidence/canonical-pad-candidate-02/pre-run-hashes.json)
  matched current 28/28 inputs, with pre/post agreement. Source-boundary pre-run
  hashes matched 79/79 files by SHA-256 and size, including the external r2 board.
  Runner review-03 command/environment recorded 9/9 code hashes matching current
  files. These are the preceding audit's read-only checks, not new execution.
- Pinned external source:
  `C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r2/source/Edgeberry.kicad_pcb`,
  912,379 bytes, SHA-256
  `67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0`.
  Eight pinned artifacts total 1,117,036 bytes. External availability is required
  for the corresponding rerun; do not upload or copy fixtures automatically.
- Audit discovered 57 saved executions with result and sibling stdout: 43 reader,
  3 candidate, 11 runner. It did not fully audit every manifest/environment for
  all 57. This is a discovery count, not a total of accepted scenarios or unique
  tests. Broad execution/catalog provenance remains incomplete.
- Historical envelope, diagnostics and inventory review ZIPs contained source,
  tests and bytecode, but no recovered execution-metadata entries. A pytest
  version in a bytecode filename is not reliable execution environment proof.
  Preserve ZIPs and review acceptance; do not invent missing logs/node IDs.
- The [runner provenance limitations](../../../evaluation/windows_runner/PROVENANCE-LIMITATIONS.md)
  retain three unrecovered historical versions: review-01 native-case/test-native
  and review-02 test-native. Current files cannot stand in for those originals.
- Full `SourceCheckEvidence` receipt and `PreparedRequest` preparation API remain
  unimplemented. Intermediate declarations and raw boundary records do not
  establish complete field/span/normalization provenance automatically.
- Local-only evidence links can exist on this workstation without being tracked
  or portable after cloning. Link validation confirms present paths only.
  No local-only artifact is staged, uploaded, deleted or reclassified by this
  document. See the historical handoff for merge-time preservation manifests.

## Sprint gates and acceptance boundaries

These summaries retain the [sprint plan](sprint-plan.md) and
[design section 9](design.md#9-implementation-acceptance-levels); the originals
control if a summary is insufficient. Inventory approval waives no gate.

| Gate | Evidence retained | Remaining exit obligations / dependency |
| --- | --- | --- |
| Sprint 1 selected subset | Accepted affine/DAG, independent stage oracles, angle/parity and selected line/arc/rectangle capacity/fixture behavior; 1.1/1.2 reviewer acceptance retained. | Broader normative requirements remain open. SATISFIED scenario rows do not promote aggregate tasks or establish Foundation acceptance. |
| Sprint 2 KiCad geometry | Accepted fixture gate 7.1 and byte inventory; evaluated runner, rectangular candidates, bounded C1/C2 source/boundary checks. | Actual real KiCad geometry importer with independent outline/footprint/pad/approved-fiducial oracles, exact versions/settings/support/rejection evidence and provenance. Tasks 1.5/5.2 and 3.4/5.5/5.13 remain aggregate PARTIAL/open. Receipt preparation needs reviewed bounded plan. |
| Sprint 3 Gerber | No verified adapter/reuse baseline. | Pinned PyGerber/Gerbonara evaluation first; then real F.Paste, explicit alignment, filled-geometry oracles, rejection controls and B.Paste when requested. P10 dependency blocks P11-P13 implementation acceptance. |
| Sprint 4 reconciliation / Prototype | Existing geometry/byte/candidate evidence can be reused within scope. | Same-revision placement/BOM, declared origins, DNP/quantity/reference reconciliation, negative companions, overrides, immutable publication/digests and rollback. Combined profile and Prototype are not accepted. |
| Sprint 5 / Complete | Existing offline core tests retain value. | Camera/lens/raster/runtime dimensions, distinct rigid/projective fitting and independent validation, policy purpose/version, lifecycle/replay, six-machine isolation, optional-engine evaluation/fake boundary and all remaining normative scenarios. |

Foundation Prototype requires all seven design gates: (1) independent typed
transform evidence; (2) actual real KiCad 10.0.7 import and approved fiducials;
(3) pinned Gerber reuse/Paste evidence; (4) same-revision assembly reconciliation;
(5) immutable reproducible provenance, rollback and contextual separation;
(6) separate unresolved physical envelopes and blocked REVIEW for missing camera
geometry; (7) an exact subset acceptance report naming every remaining scenario
and original task. Full six-machine camera isolation remains a Sprint 5 obligation.

Foundation Complete requires all Prototype gates, every normative positive and
negative scenario, complete camera/registration/policy/lifecycle evidence,
representative supported and rejected import combinations, justified original
tasks and offline reproducibility. Choosing not to integrate open-aoi does not
waive its evaluation or fake-engine boundary tests. Future 3D, hardware travel,
production accuracy, firmware and deployment remain outside this software change;
keeping them unresolved is not permission to infer readiness or impose a new
hardware-qualification blocker.

## Next bounded action (proposal, not implementation authorization)

Review a receipt/PreparedRequest construction plan on top of the existing
source-checked boundary result. Consult P01/P06/P07/P08/P21 and E-B/E-S, with
related tasks 1.5/5.2 and 3.4/5.5/5.13. Reuse the current source preflight, hash,
declaration and boundary APIs; do not merge/cherry-pick historical work again.
Current evidence is sufficient to start this bounded design review; no new test
execution is needed solely to review the plan.

Candidate scope: [boundary evidence contracts](../../../src/aoi_platform/boundary_evidence.py)
and the [source-checked boundary layer](../../../evaluation/kicad-reader/source_checked_boundaries.py),
with a dedicated preparation module/test file only if the reviewed design needs
one. Input is admitted immutable bytes, explicit declarations and one operation
ledger; output is a complete immutable receipt/request or atomic diagnostics,
never a usable partial request. Preparation must not call binding or candidates.
Existing orchestration retains the one-candidate-call contract.

Acceptance for that future slice must cover complete field/span/normalization
provenance, four boundary pairs/16 corners, explicit unchecked categories,
shared-budget accounting, immutable outputs and failure ordering. Stop if the
existing intermediate results cannot supply provenance within current budgets,
if scope expands beyond pinned inputs, or if a receipt would require fabricated
claims. Review the plan before implementation; this matrix authorizes neither.

After an authorized implementation changes those contracts, a focused rerun may
be justified for the four source-checked preflight/bytes/declarations/boundaries
test files and boundary orchestration. Add precise receipt-positive/negative,
C2 +0.001 conflict, budget-boundary and atomicity tests only as part of that
separately authorized slice; new test node names do not yet exist. Do not run
native KiCad, historical evaluation suites or a full suite by default. Record
new results alongside, never over, preserved evidence and update this matrix.
