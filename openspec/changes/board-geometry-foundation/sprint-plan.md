# Foundation execution plan — existing board-geometry-foundation change

Sprint 1's selected affine/DAG and line/arc/rectangle subset now has numerical, fixture and structured diagnostic evidence, including the diagnostics slice from base 2980f65. Only tasks 4.1–4.4 are checked. Sprint 1 exit and further checkbox changes await evidence review; later import/camera/lifecycle obligations are not additional Sprint 1 implementation gates. See implementation-status.md for the per-task split. No Foundation acceptance level, parser compatibility or hardware accuracy is claimed achieved. This plan does not authorize later sprints.

## Acceptance levels and reporting

Design.md section 9 is the detailed acceptance contract. Foundation Prototype is proposed after Sprint 4: a bounded, tested geometry and real-board import/reconciliation path with explicit errors, context, immutable revisions and provenance. It must name its supported subset and every remaining OPEN requirement/scenario. Foundation Complete requires all normative scenarios, including camera/calibration and full machine isolation, to have passing implementation evidence. Sprint 5 is necessary but not sufficient if any requirement remains incomplete.

Status vocabulary: OPEN (not yet evidenced), PARTIAL (some evidence, still open), SATISFIED (all requirement scenarios evidenced). The initial plan set all status to OPEN; Geometry Core rows now record partial evidence below, with full conformance still open. Document validation cannot promote any status. Future sprint reviews must cite original task IDs, exact requirement/scenario titles, candidate version, fixtures/hashes, selected policies and test results. Never mark a whole task complete for a partial sprint slice.

## Sprint 1 — Typed geometry models and coordinate transformations

**Entry:** separate implementation authorization; agreed frame conventions and synthetic numeric policy for the coordinate subset. No PCB, Gerber, camera or firmware prerequisite.

**Deliverables:** typed finite point/frame/transform/context and error records; explicit units and source axes/origins; source-to-PCB and PCB-to-machine transformations with composition/inversion; rotation/parity; typed capacity/fixture/travel distinctions and unresolved physical-envelope reporting. Include contextual path rejection from the start; do not add camera projection or parsers in this sprint.

**Acceptance:** independently assert unit (25.4,50.8), reflection (25.4,-50.8), rotation (50.8,25.4), translation (60.8,45.4) mm and inverse checkpoints for (1,2) inch. Test noncommuting composition, round trips, angles/bottom parity, unknown origin, singular/ill-conditioned/ambiguous mappings, nonfinite values and wrong context. Test capacity independent of machine translation, explicit rotated fit, overrun, synthetic fixture exclusions and unresolved travel. Known errors must preserve identifiers/context, not return guessed points. Limits are versioned synthetic test criteria only.

**Exit:** coordinate subset has recorded test evidence; all not-yet-covered GEO-001 and PCB-001 requirements stay OPEN/PARTIAL. Sprint 1 alone does not reach Foundation Prototype.

## Sprint 2 — Import a real KiCad PCB fixture

**Entry:** Sprint 1 coordinate gates; task 7.1 real bundle accepted before Sprint 2 import implementation begins. REAL-PCB-01 is an actual same-revision KiCad 10.0.7-target board with `.kicad_pcb`, F.Paste, placement, BOM and recorded exporter configuration. Include B.Paste only for requested bottom-side SPI. Board identity/files/settings are presently TBD, so this entry gate is not met. Missing exports or required configuration block the sprint; synthetic files are not a replacement.

**Deliverables:** candidate version-profile evaluation; KiCad outline/cutout, footprint/component, pad and explicit fiducial import; artifact inventory, immutable geometry-only BoardRevision, source-transform and revision evidence. Collect Gerber/tabular export metadata now but parse them in their later sprints. A geometry-only revision must not advertise fulfilled SPI or post-placement profiles.

**Acceptance:** independently compare real-board dimensions and selected feature coordinates; preserve side/local transforms and source hashes; reject malformed/unsupported versions, invalid topology, duplicate identities and guessed origins. Verify deterministic revision identity, failed-import atomicity and same-label/different-content handling. KiCad 10.0.7 remains a target until exact-version fixture evidence supports a narrowly scoped compatibility entry. All parser/build/settings/results not yet evidenced remain TBD.

**Exit:** real KiCad geometry path is evidenced for the tested subset. Full Gerber, reconciliation and camera requirements remain explicitly OPEN. A passing real fixture is not proof of all KiCad constructs.

## Sprint 3 — Evaluate PyGerber/Gerbonara and import Paste Gerber

**Entry:** Sprint 2 geometry/provenance path and real F.Paste plus exact export configuration. The reuse evaluation comes before adapter implementation; a custom parser cannot bypass it.

**Deliverables:** evaluate pinned PyGerber or Gerbonara against the construct matrix; record license/API/provenance/resource findings, verified subset and rejection gaps. Select a reusable adapter where suitable. If reuse is insufficient, retain the work OPEN pending the documented reviewed custom-parser scope. Import the real Paste artifact into P with explicit per-file transforms and manufactured geometry distinct from copper. Retain split/unmatched pad associations.

**Acceptance:** independently check geometry, filled regions/polarity and source alignment for the real F.Paste and supported companion constructs. Verify unsupported constructs fail even if a dependency accepts them. Exercise B.Paste when bottom-side SPI is requested, without assuming a shared origin or auto-mirroring. Pin tested dependency versions and record fixtures/results; untested entries remain TBD. SPI profile acceptance is limited to evidenced requested sides.

**Exit:** bounded Paste import is evidenced; unimplemented construct/side scenarios remain OPEN, never silently waived. Unresolved library choice or mandatory seed constructs block this exit.

## Sprint 4 — Placement/BOM reconciliation

**Entry:** real geometry/Paste import and same-revision placement/BOM with explicit headers, dialect, origin, units, angles, side and population configuration.

**Deliverables:** placement/BOM normalization, reference/group expansion, quantities/population state, joins, reconciliation and reviewed field overrides. Finish combined-profile coverage gates, retaining earlier atomic revision and provenance guarantees.

**Acceptance:** real populated references reconcile; verify DNP/mechanical exclusions, duplicate/missing references, quantity/side conflicts, source offsets, mixed revisions and required-artifact failures. Unresolved required data blocks publication; no last-file-wins merge. Record the tested dialect/subset and failure evidence. Test context isolation for implemented transforms and rejection/REVIEW of unavailable camera paths at any exposed inspection boundary; full calibration isolation is still a Sprint 5 obligation.

**Exit:** assess task 7.2 against every Foundation Prototype criterion, not merely the happy-path import. Name all open normative scenarios and their tasks. Prototype may be accepted only with this explicit ledger and passing bounded-scope evidence; full capability conformance remains OPEN.

## Sprint 5 — Camera geometry and calibration

**Entry:** import/geometry milestones and explicit synthetic calibration policy approval. No real camera, controller or gantry is required. Fixture/travel dimensions and production qualification remain outside this change.

**Deliverables:** runtime-size planar projection and lens mapping, crop/resize/domain semantics; two-point metric rigid and four-or-more-point homography fitting with independent validation; calibration policy/purpose and lifecycle; machine/camera/load/revision/side isolation; typed rejection/REVIEW. Complete fake inspection-engine boundary, offline evidence matrix and remaining capability scenarios. Real open-aoi integration remains optional after evaluation.

**Acceptance:** independent camera/lens/raster oracles, held-out validation, insufficient/degenerate/poor-coverage fits, stale/wrong contexts, synthetic-versus-production mismatch, and six-machine collisions pass the specified tests. Full import/geometry scenario evidence and support records are reviewed. A four-point exact fit alone is not validation. Missing mappings never become identity, usable ROIs or GOOD.

**Exit:** assess Foundation Complete via task 7.3. Any unfinished normative scenario or failed test remains OPEN and blocks Complete, even if the five scheduled sprints have elapsed. Record follow-up under the original task ID; do not declare completion or silently reduce scope. Hardware accuracy and 3D work remain future boundaries.

## Original task traceability

IDs are stable and retain their acceptance meaning in tasks.md. Every original task has a primary sprint below; a primary sprint is an ownership target, not a completion claim. Task 7.1 is an entry prerequisite prepared before Sprint 2. Evidence tasks 6.3/6.4/6.6 accumulate in every sprint, with final closure in Sprint 5. Profile/revision foundations from Sprint 2 must be rechecked against the new sources introduced in Sprints 3 and 4. No task ID is renumbered or removed.

| Primary sprint/gate | Original task IDs | Closure meaning |
| --- | --- | --- |
| Sprint 1 | 1.1, 1.2, 3.1, 3.2, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 4.15, 4.16, 4.17 | Typed geometry, independent transformations, context errors and separate envelopes |
| Sprint 2 | 1.5, 3.4, 3.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.13, 5.15, 5.17, 5.18 | Real KiCad/provenance foundation; cross-source obligations remain partial until later imports exercise them |
| Sprint 3 | 2.1, 2.2, 2.3, 2.4, 2.5, 5.7, 5.8, 5.9 | Reuse evaluation and evidenced Gerber subset, explicit rejection, pad associations |
| Sprint 4 | 1.4, 1.6, 5.10, 5.11, 5.12, 5.14, 5.16 | Tabular normalization, joins/reconciliation and final requested-profile gates |
| Sprint 5 | 1.3, 3.3, 3.7, 4.6, 4.7, 4.8, 4.9, 4.10, 4.11, 4.12, 4.13, 4.14, 4.18, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6 | Camera/calibration, full isolation/failure behavior and all-scenario evidence closure |
| Before Sprint 2 | 7.1 | Real bundle acquisition and documented entry checks; not parser verification |
| After Sprint 4 | 7.2 | Foundation Prototype review with explicit open-requirement ledger |
| After Sprint 5 plus required closure | 7.3 | Foundation Complete review with no open in-scope normative requirement |

## Initial open normative-requirement register

Rows are OPEN or PARTIAL; partial Geometry Core evidence is recorded in implementation-status.md. Planned later coverage is not executed evidence. Exact scenario titles in the capability specs are the authoritative test checklist; tasks 6.4 and 7.2/7.3 must retain each incomplete scenario individually. Partial requirements remain open even if an earlier sprint or Prototype milestone is accepted.

| GEO-001 requirement | Planned coverage and original tasks | Current status |
| --- | --- | --- |
| Explicit coordinate frames and canonical units | S1: 3.1, 4.1–4.4; runtime image-size evidence S5: 4.6–4.8 | PARTIAL: core frames/units/oracles tested; runtime image geometry open |
| Explicit transform direction, composition, and inversion | S1: 4.4–4.5; contextual camera paths S5: 4.6–4.14 | PARTIAL: selected directed affine DAG paths, invalid products, four-corner ambiguity and context diagnostics tested; camera maps/lifecycle open |
| Rotations and bottom-side parity | S1: 4.2–4.4; real footprint evidence S2: 5.4 | PARTIAL: synthetic orientation/parity scenarios pass; imported footprint integration open |
| Planar camera mapping and pixel semantics | S5: 4.6–4.8, 4.12 | OPEN; deferred beyond Prototype |
| Fiducial registration quality | S2 candidate data: 5.6; validated fits S5: 4.9–4.11 | OPEN; validated fitting deferred beyond Prototype |
| Configurable synthetic calibration policies | S1 numeric contract subset; S5: 1.3, 3.3, 4.11–4.14 | OPEN; full policy enforcement deferred beyond Prototype |
| Calibration and registration lifecycle isolation | S5: 4.13–4.14, 4.18 | OPEN; full six-machine calibration evidence deferred beyond Prototype |
| Separate board capacity, fixture and camera travel | S1: 3.2, 4.15–4.17; complete hardware-free evidence S5: 6.5 | PARTIAL: capacity, selected rectangle fixture checks and unresolved travel tested; import integration open. Physical TBD is intentional, not a missing S1 implementation |

| PCB-001 requirement | Planned coverage and original tasks | Current status |
| --- | --- | --- |
| Verified input support evidence | S2–S4: 1.5, 5.2; final S5: 6.3 | OPEN; untested entries remain TBD at Prototype |
| Declared source formats and import profiles | S2–S4: 5.1–5.2, 5.16; complete fixture matrix S5: 6.4 | OPEN |
| Per-source units, origin, side, and revision evidence | S2–S4: 5.13–5.15 | OPEN |
| Canonical outline, footprints, components, pads, and fiducials | S2: 5.3–5.6; additional edge fixtures S5: 6.4 | OPEN |
| Gerber parser reuse evaluation | S3: 2.1–2.5 | OPEN |
| Manufactured paste geometry | S3: 5.7–5.9; untested positive/negative scenarios S5: 6.4 | OPEN |
| Placement and BOM joins with explicit authority | S4: 1.6, 5.10–5.12, 5.14 | OPEN |
| Immutable revisions and deterministic provenance | S2: 3.4–3.5, 5.15, 5.17–5.18; recheck combined sources S4 | OPEN |
| Independent data import and physical readiness | S1/S2: 4.15–4.17; mapping/REVIEW completion S5: 3.7, 4.12 | PARTIAL: standalone unresolved/no-targeting reporting tested; import/publication and inspection boundary open |
| Atomic contracts and actionable validation reports | S1/S2: 3.6, 5.17; real multi-source failures S4; full boundary S5: 3.7 | PARTIAL: immutable reports, stable ordering and resolver/fit diagnostic context tested; parser collection and atomic publication open |
| Optional inspection-engine interoperability | S5: 6.1–6.2, 6.5 | OPEN; adapter-boundary evidence deferred beyond Prototype |

## Remaining decisions

KiCad 10.0.7 is the selected initial target. Choose the actual REAL-PCB-01 board/revision, requested sides and exporter configuration; gather exact producer/build evidence. Select pinned parser/library candidates, supported construct/dialect subset, resource limits and synthetic policy details. Actual test results remain TBD. Physical fixture/travel/coverage and production calibration/accuracy await future optics/mechanics work and are not promised by either software acceptance level.
