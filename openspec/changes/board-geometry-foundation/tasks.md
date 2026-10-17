# Future tasks — board-geometry-foundation

Geometry Core was explicitly authorized and implemented on 2026-10-17. Only tasks 4.1–4.4 are completed; all other tasks remain open. See implementation-status.md for executed tests, partial model/error work and remaining scope. Synthetic fixture evaluation is evidenced only for the selected rectangle/line/arc subset. No importer, camera calibration or hardware accuracy is claimed verified.

Execution order, entry/exit gates and original-task assignments are in `sprint-plan.md`; acceptance levels are in design.md section 9. IDs 1.1–6.6 below are preserved. A sprint may deliver part of a task, but that task and its incomplete normative requirements remain open until all acceptance checks have evidence. Foundation Prototype does not close the change; Foundation Complete requires full in-scope conformance. Both levels are currently unachieved.

Latest authorized slice: 3.6 PARTIAL (structured geometry reports with deterministic serialization and source/context tests); 4.5 PARTIAL (directed DAG resolver, explicit finite-domain four-corner consistency, full-path context checks, deterministic selection and resource rejection are evidenced; broader normative path lifecycle remains open). See [implementation-status.md](implementation-status.md) for evidence and exact gaps. Neither checkbox is promoted by the passing tests.

Current capacity/envelope slice from `1132718`: 3.2/4.15/4.16/4.17 PARTIAL for typed records, bounded line/arc capacity, selected rectangle fixture evaluation and standalone unresolved reporting. User-selected contact/margin and support decisions are recorded in [design.md](design.md). Broader outline/envelope geometry and import integration remain open; see [implementation-status.md](implementation-status.md). The original task descriptions and checkboxes below are preserved.

Resumption added 21 independent kernel tests, followed by 30 public-API fixture tests after the user selected the policy (268 total tests passing). Loaded arc extrema, filled-region exclusion overlap, Euclidean margins including 0.001 mm shortfalls, exact boundary contact, context/validation guards and unresolved/no-targeting states have executed evidence. These subset checks do not close broader normative geometry or import scenarios; no task checkbox was promoted.

## 1. Decisions and evidence
- [ ] 1.1 Review preserved frame conventions and stage oracles; accept all four forward and four inverse expected checkpoints.
- [ ] 1.2 Review separate capacity, fixture and travel contracts; confirm unknown physical dimensions remain TBD without targeting readiness.
- [ ] 1.3 Define synthetic-geometry-v1 policy; check units, configurable limits, independent evidence and synthetic/production separation.
- [ ] 1.4 Define synthetic-import-v1 reconciliation policy; check explicit selection and no production accuracy claim.
- [ ] 1.5 Use KiCad 10.0.7 as the AOI Platform V0.1 initial target; record actual build/exporter versions/settings to evaluate, keeping compatibility/results TBD until verified.
- [ ] 1.6 Select tabular header/dialect profiles; document units/origin/angle/population mappings without guessing.

## 2. Gerber reuse gate — before custom parsing
- [ ] 2.1 Evaluate pinned PyGerber or Gerbonara; document license, API, provenance and resource behavior.
- [ ] 2.2 Evaluate aperture/flash/coordinate fixtures; record independent geometry comparisons and exact versions.
- [ ] 2.3 Evaluate draw/arc/region/polarity fixtures; compare filled regions and holes with independent oracles.
- [ ] 2.4 Evaluate macros/transforms/attributes and unsupported constructs; record explicit support/rejection results.
- [ ] 2.5 Record reuse choice/subset; if insufficient, document observed gaps and obtain reviewed scope before from-scratch parsing.

## 3. Shared contracts
- [ ] 3.1 Define typed point/frame/transform records; reject nonfinite values and missing unit/context IDs.
- [ ] 3.2 Define BoardCapacity and separate fixture/travel records; verify unknown geometry stays unresolved.
- [ ] 3.3 Define CalibrationPolicy serialization; reject invalid limits and require revalidation on version changes.
- [ ] 3.4 Define artifact/provenance/entity records; verify duplicate IDs and missing hashes yield actionable errors.
- [ ] 3.5 Define immutable revision serialization; verify deterministic digests and changed-input identities.
- [ ] 3.6 Define validation reports/error ordering; verify source locations and multiple discoverable errors.
- [ ] 3.7 Define ready versus blocked REVIEW inspection input; verify blocked results retain reasons/context but no usable ROIs.

## 4. GEO-001 independently testable deliverables
- [x] 4.1 Add unit conversion; test (1,2) inch -> (25.4,50.8) mm independently.
- [x] 4.2 Add reflection/parity; test (25.4,-50.8) and bottom-mirror checkpoints.
- [x] 4.3 Add rotation/translation; test (50.8,25.4) then (60.8,45.4), direction vectors and angle wrapping.
- [x] 4.4 Add composition/inversion; test noncommuting transforms, inverse checkpoints and fixed-seed round trips.
- [ ] 4.5 Add contextual path resolution; reject missing, ambiguous, singular and ill-conditioned mappings.
- [ ] 4.6 Add distortion-free projection; verify affine/non-affine oracles, domain/horizon errors and runtime dimensions.
- [ ] 4.7 Add selected lens-model inverse contract; verify nonlinear synthetic limits and no silent resolution scaling.
- [ ] 4.8 Add crop/resize/pixel-center mapping; verify independent raster oracles and explicit clipping/visibility.
- [ ] 4.9 Add two-point metric rigid fitting; verify baseline/pair-distance, fixed scale and independent side/correspondence evidence.
- [ ] 4.10 Add four-or-more-point homography fitting; reject insufficient, rank-deficient and poor-coverage cases.
- [ ] 4.11 Add independent mapping validation; reject exact four-point fits without evidence and test held-out checkpoints.
- [ ] 4.12 Add failure propagation; test typed rejection and REVIEW without identity/stale/weaker-policy fallback.
- [ ] 4.13 Add calibration/registration lifecycle; test configuration/revision/load changes and historical replay context.
- [ ] 4.14 Add policy-purpose enforcement; verify synthetic passes cannot validate production requests.
- [ ] 4.15 Add capacity checks; verify exact fit, explicit 90-degree orientation and 0.001 mm overrun independently of translation.
- [ ] 4.16 Add fixture-outline checks; verify synthetic boundaries, arcs, margins/exclusions and capacity-pass/fixture-fail.
- [ ] 4.17 Add unresolved physical-envelope reporting; verify import succeeds without invented camera reachability/targeting readiness.
- [ ] 4.18 Add six-machine isolation checks; reject cross-machine calibration reuse with colliding capture names.

## 5. PCB-001 independently testable deliverables
- [ ] 5.1 Add manifest inventory/hashing/limits; reject missing roles, unknown profiles and oversized input.
- [ ] 5.2 Add evidence-based supported-version gates; reject unverified formats/constructs explicitly.
- [ ] 5.3 Add tested KiCad outline/cutout import; verify independent topology and malformed-outline errors.
- [ ] 5.4 Add footprint/component normalization; test rotated top/bottom coordinate oracles.
- [ ] 5.5 Add pad records; preserve repeated number strings with unique IDs and provenance.
- [ ] 5.6 Add explicit fiducial classification; verify circular pads are not auto-approved references.
- [ ] 5.7 Add Gerber library adapter after section 2 decision; verify basic construct fixtures and provenance.
- [ ] 5.8 Add declared complex Gerber constructs; verify filled-geometry oracles and explicit unsupported rejection.
- [ ] 5.9 Add paste-to-pad associations; verify split windows/unmatched warnings without copper substitution.
- [ ] 5.10 Add placement dialect normalization; test units/origins/angles/sides and row-level numeric errors.
- [ ] 5.11 Add BOM dialect/reference expansion; test quantities, population states and group syntax.
- [ ] 5.12 Add entity joins; reject duplicates/unresolved populated references while retaining explicit DNP/mechanical exclusions.
- [ ] 5.13 Add source-transform evidence checks; reject guessed common origins and extent-based alignment.
- [ ] 5.14 Add reconciliation/field overrides; preserve conflicting values and reviewed decision provenance.
- [ ] 5.15 Add revision attestation checks; reject mixed exports despite matching filenames/dimensions.
- [ ] 5.16 Add requested-profile gates; verify missing required artifacts block publication and optional data stays absent.
- [ ] 5.17 Add atomic publication; verify rejected candidates cannot partially replace accepted revisions.
- [ ] 5.18 Add reused-label handling; verify changed content creates a new revision with acknowledgment, never overwrite.

## 6. Compatibility and evidence completion
- [ ] 6.1 Evaluate pinned Aman9y/open-aoi commit/license and actual image/alignment contracts; record optional adapter suitability.
- [ ] 6.2 Test fake engine boundary; verify crop/alignment mapping and missing-transform/wrong-context rejection.
- [ ] 6.3 Populate supported-inputs.md only with exact versions, fixture paths/hashes and executed evidence; retain TBD elsewhere.
- [ ] 6.4 Trace every capability scenario to a test and independent oracle; report unexecuted cases explicitly.
- [ ] 6.5 Run foundation acceptance offline with synthetic/file fixtures and no camera, gantry, ESP32 or external engine.
- [ ] 6.6 Review future boundaries: no fabricated Z/volume, physical travel dimensions, production accuracy, motion output or distributed infrastructure; retain provenance/context/revision/machine isolation.

## 7. Additional planning gates (original IDs preserved)
- [ ] 7.1 Acquire and document REAL-PCB-01 before Sprint 2: actual `.kicad_pcb`, F.Paste, placement, BOM and exporter configuration from one revision; B.Paste only for requested bottom-side SPI. Check hashes, producer evidence and declared conventions; current evidence TBD.
- [ ] 7.2 Assess Foundation Prototype against design.md section 9 after Sprint 4; attach evidence and explicitly retain every incomplete requirement/scenario and partial original task as OPEN.
- [ ] 7.3 Assess Foundation Complete after Sprint 5 and any remaining closure work; require evidence for every normative scenario and no unresolved in-scope requirement. Do not substitute document validation or sprint completion for implementation evidence.
