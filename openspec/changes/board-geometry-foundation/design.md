# Board geometry foundation design

## 1. Context and decisions

This proposal defines the two capabilities GEO-001 and PCB-001 for an independent AOI platform. The separately authorized Geometry Core implementation is recorded in implementation-status.md; the remaining models/contracts and capability behavior remain open. A future implementation should run as ordinary Python modules on a PC/server, using OpenCV where appropriate, with no firmware, camera, or gantry requirement. One process may serve multiple machines; deployment topology is not prescribed.

The canonical board is planar in Phase 1. Keep its side, geometry, and provenance explicit so a later proposal can add surfaces, Z coordinates, height calibration, and post-reflow inspection profiles without reinterpreting existing 2D points. Do not add fictitious Z=0 measurements or use planar homography as a 3D model.

Decisions:

1. Physical canonical PCB coordinates use millimeters and a top-view right-handed XY frame; +Z points toward the top observer for orientation only.
2. Every source file owns a distinct frame. A shared filename, exporter, or similar extents never proves shared origin.
3. Import normalization, per-load registration, and camera calibration are separate immutable records.
4. Rigid transforms describe board placement. Explicit reflection describes side/export conventions; distortion and planar projection describe camera geometry. These operations are not interchangeable.
5. Required data is selected by a named import profile; unsupported or missing information cannot silently become an empty valid model.
6. Canonical data is independent of any inspection engine. Optional adapters preserve units, frames, and revision identity.

## 2. Coordinate frames and equations

Use column vectors. `T_B_A` maps coordinates from frame A into frame B. Composition is right to left: `T_C_A = T_C_B T_B_A`. Store both frame IDs; callers never infer matrix direction from context. For affine transforms, use homogeneous vector `[x,y,1]^T`; translation occupies the last column. A transform is invertible only when its linear block has nonzero determinant and passes the conditioning policy.

| Frame | Definition | Units and axes |
| --- | --- | --- |
| PCB `P` | Immutable board-revision datum, viewed from top. Default datum is the lower-left of the axis-aligned outline bounds **after** explicit KiCad-to-top-view axis normalization; manifest may select another documented datum. | mm; +X right, +Y up; top and bottom features use this same frame. |
| Source `S_i` | One KiCad, Gerber, or placement file's original numeric space, including exporter origin and side convention. | Declared mm/inch or format units; axes recorded individually. BOM has no geometric frame unless it actually supplies geometry. |
| Footprint `F_j` | Local origin and axes for one footprint instance, with source orientation preserved. | mm after conversion; normalized to P through a declared pose, including explicit bottom reflection when needed. |
| Machine `M_k` | Abstract work plane for machine k, fixed datum independent of board loading. | mm; +X/+Y defined in machine configuration; physical fixture and camera travel dimensions TBD in separate records. No steps or firmware axis signs. |
| Raw image `I_r` | Original capture pixel coordinates. | px; origin center of top-left pixel, u right, v down; valid centers `0..width-1`, `0..height-1`. |
| Undistorted image `I_u` | Output of an explicitly versioned lens model and rectification configuration. | px; same axis convention; dimensions and intrinsics may differ from raw. |
| Crop/engine `I_e` | Optional crop, resize, or rectified inspection raster. | px; separate frame with recorded mapping to its parent. |

Angles are degrees, normalized to `[0,360)` on stored component poses; signed differences use `[-180,180)`. Canonical positive rotation is counterclockwise viewed from the top. `R(theta) = [[cos(theta),-sin(theta)],[sin(theta),cos(theta)]]`; trig evaluation converts degrees to radians explicitly. Orientation of a reflected component is obtained from its transformed local +X direction, not by blindly negating an angle. Store parity separately because an angle cannot encode a reflection.

### Source normalization

`p_P = T_P_Si p_Si`, where `T_P_Si = Translate(tx,ty) R(theta) A s`. Here s is a declared unit conversion (inch to mm = 25.4, mm to mm = 1), A is a declared orthogonal axis permutation/reflection, and translation is in P millimeters. Any exporter transforms already applied to parsed geometry must be recorded; never apply them twice. Source profile includes origin meaning, units, axis mapping, rotation zero/direction, side semantics, and transform evidence. Resolve unknowns through manifest declarations or sufficient named correspondences, otherwise reject.

The top-view board datum is derived once from the authoritative KiCad outline and pinned in the revision record. Other sources align to that datum; they are not independently shifted to their own bounding-box minima. Scaling to make extents match is forbidden. If correspondence fitting estimates scale for diagnosis, compare with declared units and fail rather than publishing a scaled physical board.

Bottom-side records remain in P as viewed through the board from the top. Do not auto-mirror because a layer says bottom. A source explicitly declared as bottom-view about line x=c uses `x_top=2c-x_bottom, y_top=y_bottom`; the manifest must supply c in the appropriate source units/frame and any subsequent rotations/translations. A bottom-view presentation raster is a separate image transform. Maintain top/bottom layer tags independently of reflection parity. Polygon vertices and holes must be transformed consistently and winding normalized after reflection.

Example: source `(1,2)` inch, A=diag(1,-1), theta=90 degrees, t=(10,20) mm maps to `(60.8,45.4)` mm. This is a required nontrivial fixture, including its inverse. A 10 mm x 20 mm board mirrored about x=5 maps `(2,3)` to `(8,3)` and local +X to -X; applying the mirror twice restores both geometry and parity.

### Board loading and machine coordinates

Independent checkpoints for the preceding source-normalization example are mandatory. Compute each oracle directly, not using the composed transform under test:

| Stage | Independent arithmetic | Expected point |
| --- | --- | --- |
| Unit conversion | (1 x 25.4, 2 x 25.4) | (25.4, 50.8) mm |
| Reflection | (x, -y) | (25.4, -50.8) mm |
| 90-degree rotation | (-y, x) | (50.8, 25.4) mm |
| Translation | (x+10, y+20) | (60.8, 45.4) mm |

Inverse checkpoints are (50.8,25.4) after subtracting translation, (25.4,-50.8) after -90-degree rotation, (25.4,50.8) after reflection, and (1,2) inch after division by 25.4. Both independent forward checks and round trips must pass.

`p_M = T_M_P p_P`, with a proper rigid SE(2) transform (rotation plus translation, determinant +1, scale 1). An underside load is represented by a distinct declared load-side reflection frame followed by a proper rigid registration, never hidden in an SE(2) matrix. The frame path includes that reflection explicitly. Registration records bind to machine ID, board revision, load instance, side, and fixture configuration.

Keep three separate concepts:

| Concept | Meaning | Current status |
| --- | --- | --- |
| BoardCapacity | Maximum PCB dimensions 280 x 550 mm; compare complete outline extents after an explicitly declared capacity-test rotation, independent of translation in M. | Fixed board requirement, not a travel rectangle. |
| FixtureEnvelope | Usable mounting region in M, exclusions and required margins, bound to machine/fixture/configuration. Check the complete loaded outline, including arcs analytically or conservatively. | Physical geometry and margins TBD. |
| CameraTravelEnvelope | Permitted positions of a declared camera reference point in M, bound to machine/camera/mechanical configuration and exclusions. | Physical travel dimensions TBD until optics/mechanics selection. |

Exact 280 x 550 mm passes BoardCapacity; 550 x 280 mm may pass with an explicitly declared 90-degree capacity-test rotation. No implicit rotation is performed. Fixture fit and camera coverage do not follow from capacity acceptance. Synthetic tests may define a fixture rectangle `[0,280] x [0,550]` with zero margin, but it is not a physical default. A capacity-compliant board may fail fixture fit. Travel may extend beyond the board or be smaller depending on field of view, camera offsets and poses; no dimensions are inferred here.

Fit reports distinguish capacity, fixture fit and camera reachability, each pass/fail/unresolved. Missing physical envelopes do not block board import. Camera reachability remains unresolved in this foundation; a future optics/mechanics proposal must validate travel, field of view, working plane and coverage before physical targeting. Fixture/camera records are versioned and machine-scoped; a fit report never authorizes motion.

### Camera mapping

For a planar board at the calibrated plane, `lambda [u_u,v_u,1]^T = H_Iu_P [x_P,y_P,1]^T`. Normalize by the third coordinate; reject points near the horizon or outside the valid calibrated region. `p_Ir = D(p_Iu; lens_model, intrinsics, configuration)`; inverse uses the model's documented undistortion solver. D is nonlinear, not a homography. A no-distortion profile is an explicit identity model.

For a moving camera, H is specific to the capture pose. It may be composed as `H_Iu_P = H_Iu_M(capture_pose) T_M_P`. Captures must bind their effective H, registration, and calibration; a fixed transform from a different gantry position is invalid. Intrinsics alone cannot recover PCB coordinates. Camera resolution, model, intrinsics, lens distortion, crop, binning, focus/zoom configuration, and capture dimensions are inputs. Never silently scale calibration to a different resolution. A derived resize/crop calibration requires an explicit parent mapping and new identity.

Pixel centers use integer coordinates. Pixel area boundaries are half-integers; ROI bounds use half-open raster indices after an explicitly documented floor/ceil and clipping policy. Transform continuous polygon vertices before rasterization; do not round intermediate coordinates. An out-of-field ROI returns visibility status (inside/partial/outside); clipped results carry the original geometry and clipping report. General point conversion outside the declared valid domain fails rather than extrapolating silently.

## 3. Fiducials and calibration lifecycle

Design fiducials have stable IDs, side, center in P, shape, dimensions, and provenance. Observations carry fiducial ID, observation frame, measured point, confidence, and optional covariance. Correspondences use IDs rather than nearest-neighbor guesswork; duplicate IDs and side/revision mismatches fail.

- Rigid registration: two distinct, sufficiently separated, correctly identified fiducials constrain a proper SE(2) pose only when both point sets are in calibrated metric planes with known scale and handedness. Compare pair distances under policy; fit rotation and translation with scale fixed at one. Two points cannot establish a general camera homography or independently detect reflection/incorrect correspondence. Require independent side/correspondence/metric-mapping evidence or an additional held-out off-baseline fiducial under policy. Three or more are preferred for mismatch detection. Reject inadequate baseline, distance disagreement, excessive residuals or reflection indicated by independent evidence.
- Planar homography: four or more P-to-undistorted-pixel correspondences with full-rank geometry; a minimal four-point set must have no three collinear. Use an overdetermined fit when available. Reject poor spatial coverage, rank deficiency, excessive conditioning or reprojection error. Four points can interpolate incorrect measurements with near-zero residual; fitting residual alone is not validation. Require held-out checkpoints or a separately evidenced reference mapping under policy, including for overdetermined fits. Report inliers, rejected observations and independent validation evidence; do not silently discard data to pass a threshold.
- Intrinsic lens calibration: separately supplied or later estimated from a suitable multi-view calibration dataset; board fiducials at one plane do not determine a reliable general lens model. This change validates records and synthetic mappings, not a hardware calibration procedure.

Proposed `synthetic-geometry-v1` test policy: numerical affine/rigid round-trip <=1e-6 mm; distortion-free projective round-trip <=1e-6 mm and <=1e-6 px; nonlinear lens inverse <=1e-3 px under declared solver limits; fitted rigid fiducial RMS <=0.05 mm and maximum <=0.10 mm; projective reprojection RMS <=0.5 px and maximum <=1.0 px. Rigid baseline >=10 mm and pair-distance disagreement <=0.10 mm; homography fiducial convex-hull coverage >=10% of the intended board ROI. Condition number <=1e8 after coordinate normalization; projective denominator absolute value >1e-12 under the stored matrix normalization. Independent synthetic checkpoints use the corresponding rigid/projective RMS and maximum limits, in addition to known-transform numerical oracles. All calibration numbers in these documents refer to this synthetic policy unless another policy is explicitly selected. They are not production defaults, verified accuracy or a hardware error budget.

CalibrationPolicy is configurable, immutable data: policy ID/version, purpose synthetic/production, applicable model/algorithm, unit-bearing numerical/solver tolerances, minimum counts/baseline/coverage, pair-distance bound, conditioning/denominator limits, fit and independent-check residual limits, required independent evidence, valid domain, and evidence/approval references. Missing, nonfinite, negative or inconsistent limits fail POLICY_INVALID. Select a policy explicitly; no synthetic fallback for a production request. Changes create a new version and require revalidation before activation. Production policies and qualification evidence are TBD. Synthetic records remain visibly synthetic even when active for tests and cannot satisfy production context.

Unvalidated mappings return typed errors and no usable conversion or active mapping. At BuildInspectionInput, return blocked status with disposition REVIEW, reason codes and available machine/board/load/capture/policy context, without usable ROIs. REVIEW means uninspectable pending correction, not a defect judgment. Missing independent validation evidence yields MAPPING_UNVALIDATED. Never substitute identity, stale calibration or weaker policy; this condition cannot produce GOOD. Other geometry callers receive rejection rather than an inspection verdict.

Calibration and registration states: draft -> validated -> active -> invalidated; activation is explicit, immutable records are superseded rather than edited. Reject inactive, invalidated, expired (when expiry is configured), or incompatible records. A camera configuration or fixture change invalidates the relevant path. Board revision/load changes invalidate registration; machine/camera replacement invalidates that machine's calibration. Historical records remain readable for replay. No stale fallback to another machine, camera, side, revision, or load is permitted.

## 4. Typed data models

The following is a language-neutral schema proposal, not implementation code. All IDs are nonempty strings in their declared namespace; all numbers are finite binary64 values unless stated. Required means non-null. Versioned schema and validation policy IDs appear on every published aggregate. Unknown enum values fail schema validation. Optional fields distinguish unknown from empty/zero.

| Model | Required fields and constraints |
| --- | --- |
| Point2 / Polygon2 | x,y plus frame_id; polygon exterior and holes, closed topology, no self-intersection, positive area. Physical canonical values are mm. |
| Frame | frame_id, kind, unit enum mm/inch/px/source-unit, axis directions, origin description, board/machine/capture association as applicable. |
| Transform2 | transform_id, from_frame, to_frame, type rigid/affine/homography/reflection, normalized 3x3 matrix, unit declarations, parity, valid_domain, provenance, validation metrics; inverse is derived and checked. Distortion uses a separate model record. |
| BoardCapacity | capacity_id/version, width_mm=280, height_mm=550; explicit capacity-test orientation in request; no travel bounds. |
| FixtureEnvelope | envelope_id/version, machine_id, fixture_id/configuration, frame_id M, usable region/exclusions, margin_mm, evidence status synthetic/qualified; unresolved geometry is absent. |
| CameraTravelEnvelope | envelope_id/version, machine_id, camera_id, mechanical configuration, frame_id M, reference point definition, permitted region/exclusions, evidence status; physical dimensions TBD; does not itself prove optical coverage. |
| FitReport | Separate capacity/fixture/camera-reachability statuses pass/fail/unresolved; envelope IDs/versions, violations and unresolved reasons; no targeting authorization. |
| CalibrationPolicy | policy_id/version, purpose, model applicability, unit-bearing limits, required independent evidence, valid domain and evidence/approval references per section 3. |
| CameraCalibration | calibration_id, machine_id, camera_id, raw and undistorted sizes (positive integer width/height), intrinsics, lens_model_name/version and named parameters, configuration fingerprint, valid plane/domain, validation policy/results, state, created_at UTC, optional expires_at, parent calibration/mapping when derived. No fixed coefficient length for every lens model. |
| BoardRegistration | registration_id, board_revision_id, machine_id, load_id, load_side, fixture_id/configuration, frame path, fiducial observations, fit diagnostics, policy_id, state. |
| CaptureGeometry | capture_id, machine_id, camera_id, raw_image_size, configuration fingerprint, board_revision_id, load_id, side, calibration_id, registration_id, effective_homography_id, capture pose if relevant, timestamp UTC. |
| SourceArtifact | artifact_id, role, original filename, byte length, SHA-256, format/version, parser profile/version, source_frame_id if geometric, declared units/layer/side, source revision claim, provenance. |
| ImportManifest | schema_version, board_id, revision_label, profile, artifact list, role/side/layer assignments, source conventions/transforms and evidence, field mappings, authority decisions, fit policy, validation policy. |
| BoardRevision | board_id, immutable revision_id, human revision_label, content_digest, parent_revision_id optional, outline and cutouts in P, datum, side/layer map, artifact IDs, source transforms, component/pad/paste/fiducial collections, validation report, schema_version. Revision label alone is not identity. |
| FootprintInstance | footprint_id, reference, library_identifier optional, side, source local frame, transform to P, normalized orientation and parity, body/courtyard geometry optional, provenance. Footprint name does not imply known physical size. |
| Component | component_id, unique reference, footprint_id, position P, orientation_deg, side, value/part_number optional, assembly_state populated/DNP/unknown, placement provenance. DNP is distinct from missing placement. |
| Pad | pad_id, footprint_id, pad_number string (not globally unique), side/layers, copper geometry in P, drill optional, pad_type, net optional, source provenance. IDs stay unique when pad numbers repeat. |
| PasteFeature | paste_id, side, resolved filled geometry in P, source aperture/region provenance, optional linked pad IDs and match confidence. Many openings may map to one pad and some openings have no pad match. Paste geometry is not replaced with copper-pad geometry. |
| BomItem | bom_item_id, expanded unique references, quantity positive integer, value/part_number optional, raw fields, normalized population status, provenance. Group quantities must match expanded references under the manifest policy. |
| Fiducial | fiducial_id, side, position P, shape/size, source footprint/pad IDs optional, provenance, approved classification. Never identify every circular pad automatically as a fiducial. |
| ValidationReport | report_id, status accepted/rejected, errors, warnings, checks/results, policy_id, unresolved/conflicting fields, artifact digests, canonical digest if accepted. |
| ContractError | code enum, message, artifact/entity ID optional, field_path, expected/actual optional, source location optional, remediation, severity error/warning. Return all safely discoverable issues in stable order. |

Stable entity IDs are scoped to an immutable revision. Canonical serialization, deterministic ordering, source bytes, transform decisions, parser/schema versions, and policies contribute to the content digest; timestamps and filesystem paths do not. Same normalized inputs and manifest yield the same digest. Reusing a human label with different content creates a different revision with a conflict warning requiring acknowledgment; never overwrite a revision. Cross-revision equivalence of individual parts is not assumed.

## 5. Import pipeline and contracts

AOI Platform V0.1 initially targets KiCad 10.0.7. Target selection is not compatibility verification: actual producer/build evidence, exporter settings, parser versions and test results remain TBD. The real `REAL-PCB-01` bundle in supported-inputs.md is a Sprint 2 entry prerequisite; its export presence does not require Gerber or tabular import to be implemented before Sprints 3 and 4 respectively. Only evidence-backed combinations may enter a released support allowlist. Isolated evaluation may exercise a candidate input profile to establish that evidence, without publishing a supported-compatibility claim.

### Profiles and authority

Before implementing Gerber parsing from scratch, evaluate reuse of PyGerber or Gerbonara against the target construct/fixture matrix in supported-inputs.md. Record the exact evaluated version, license, API and geometry precision, polarity/region/macro/transform handling, source-location/provenance retention, bounded resource behavior, and positive/negative fixture results. Prefer an adapter to a suitable library. A from-scratch parser requires a documented evaluation explaining why reuse is insufficient and a separately reviewed scope; no such choice is made here. Library acceptance is not proof of semantic support: reject unsupported constructs explicitly with FORMAT_UNSUPPORTED and source location, never silently omit or approximate them. Candidate versions, evaluation results and selection are TBD.

Target input contract (verified support is recorded only in supported-inputs.md): KiCad `.kicad_pcb` s-expression boards through explicitly versioned parser profiles; Gerber RS-274X Paste with declared format/units and side/layer (X2 attributes, when present, must agree); CSV/TSV placement and BOM through named column/convention profiles or explicit manifest mappings. No exact tested versions are evidenced yet; they remain TBD in supported-inputs.md. Release claims require exact KiCad/exporter and parser/library versions, settings, fixture hashes, independent oracles and test results. Unrecognized versions, aperture macros, transformations, or polarity operations must fail if they cannot be interpreted correctly; do not skip them. Legacy KiCad `.brd`, Gerber X3 placement, ODB++, IPC-2581, panel expansion, and automatic file-convention guessing are deferred.

KiCad supplies authoritative outline, footprints, copper-pad geometry and design fiducial candidates. Gerber supplies authoritative manufactured paste openings after polarity/region/aperture processing. Placement supplies assembly positions and orientations, cross-checked with KiCad. BOM supplies assembly metadata and population state. Authority is field-specific; an override must name the field, reason, source and reviewer decision in the manifest. No automatic last-file-wins merge.

Import profiles:

- `geometry`: KiCad plus manifest; produces validated board geometry, explicitly marked as not yet inspection-ready.
- `spi-2d`: geometry plus Gerber Paste for every selected inspection side; pad-to-paste links may remain unresolved with warnings, but paste geometry and its transform must be valid.
- `post-placement-2d`: geometry plus placement and BOM for every selected assembly side. Every populated inspectable reference must resolve to one footprint and placement. Explicit BOM/DNP exclusions are retained. Mechanical/non-assembly footprints require explicit classification. Unknown population or unresolved references block this profile.
- A combined request must pass both profiles. Missing optional data remains absent with a capability/coverage report; it never appears as evidence of no components or no paste.

### Operations

| Operation | Input | Output and failure semantics |
| --- | --- | --- |
| ValidateImport | Manifest + byte-addressable source artifacts + policy | ValidationReport and a non-published candidate if parseable; errors prevent promotion. No persistent mutation of an existing revision. |
| NormalizeBoard | Fully resolved manifest, parsed artifacts, accepted validation decisions | Immutable BoardRevision + accepted report; atomic publication only after all requested profile gates pass. Failure returns report and no published revision. |
| ResolveTransform | from/to frame IDs + explicit revision/load/capture context | One validated frame path with provenance, or TRANSFORM_MISSING/CONTEXT_MISMATCH/TRANSFORM_AMBIGUOUS. Multiple paths must agree within tolerance or fail. |
| ConvertPoints | finite points, from/to frame IDs, path ID/context | Same ordered number of points + path/calibration IDs; fail the batch with indexed errors if any point is outside domain or not convertible. No mixed silent successes. |
| FitRegistration | expected fiducials + observations + fit type + explicit context/policy | Draft registration/calibration candidate + residuals/inlier IDs/quality report; validation/activation remains explicit. No movement or acquisition. |
| ValidateFit | BoardRevision outline + BoardCapacity + capacity-test orientation + optional load transform/FixtureEnvelope/CameraTravelEnvelope | FitReport with separate statuses, violations and unresolved inputs. Camera reachability unresolved pending future optics/mechanics validation; no controller action. |
| BuildInspectionInput | accepted revision + capture geometry + ROI feature IDs + selected CalibrationPolicy | Tagged ready result with engine-neutral identities, image reference/size, ROI polygons, mappings, side, units and visibility; or blocked result with disposition REVIEW, reasons and context, no usable ROIs, when required profile/mapping/context cannot be validated. |

### Contextual affine resolver policy (Sprint 1 decision)

The resolver implementation for this slice accepts only a directed acyclic graph of registered affine `Transform2` edges. It traverses registered edges in their declared direction; it never synthesizes inverse edges. Callers may register the result of the existing explicit `inverse()` operation as a separate edge, subject to the same DAG and validation rules. A cycle is rejected with the typed `TRANSFORM_CYCLE_UNSUPPORTED` error. This is an implementation limit of the current resolver. The normative transform contract's invalid-path and ambiguity requirements remain in force; any future cycle-capable resolver remains open work and does not get silently waived.

Every candidate path is checked end-to-end. All frame metadata on every intermediate node participates in context validation; a missing value at an intermediate frame cannot bridge conflicting nonempty revision, machine, or capture identities elsewhere on the path. Pixel/image frames, projective maps, and camera mappings are outside this resolver.

Path consistency uses the separately versioned `synthetic-path-consistency-v1` policy (default tolerance `1e-6 mm`), not the round-trip or production-accuracy tolerances. The caller must provide a finite, nonempty rectangular domain in the source frame, with declared coordinates and units. Each candidate is evaluated at all four rectangle vertices. Euclidean output differences are converted to millimeters using the target frame's declared physical unit; the largest difference across vertices and path pairs must be at most the selected policy tolerance. Missing/invalid domain or policy fails explicitly. Every eligible path is enumerated within the configured path/edge limit; resource exhaustion fails explicitly and never returns a partial result. If paths disagree, resolution fails with ambiguity/inconsistency. If they agree, a deterministic representative is selected by lexicographic transform-ID sequence and the result records all examined path IDs, policy ID/version and domain.

This policy distinguishes the newly decided consistency procedure from the existing normative requirement that ambiguous paths fail. It does not define camera calibration, physical accuracy, or import-report aggregation.

Sprint 1 diagnostic implementation convention: immutable GeometryError payloads retain known request evidence at resolver and ValidateFit boundaries and preserve mismatches as separate expected/actual diagnostic text. Frame contexts use role-prefixed keys, so conflicting source/target/envelope values cannot overwrite each other. The ContractError adapter automatically retains this evidence; conflicting caller additions reject rather than overwrite. Path evidence policy `path-evidence-v1` records a deterministic prefix bounded to 32 paths, 128 IDs total and 8192 UTF-8 bytes of encoded IDs per summary, with explicit omitted path/transform counts. Search budgets remain independent and binding. Oversized graphs report omitted edge counts without diagnostic enumeration. These are representation/resource conventions, not relaxed normative geometry checks or inferred missing metadata.

Artifact ingestion is read-only, bounded by configured byte/entity limits, and never executes source content. Decode settings, CSV delimiter, decimal convention, encoding, and header mapping are declared. Decimal comma requires a compatible delimiter and explicit profile; units cannot be inferred from magnitude. NaN/Inf, zero-scale transforms, invalid layer assignments, malformed outlines, or empty required collections fail.

Validation steps: inventory and hashes -> parse and source semantics -> source-frame resolution -> normalization -> outline/topology -> entity joins -> profile coverage -> cross-source reconciliation -> BoardCapacity feasibility -> accepted report. Staged source data remains available for diagnostics on failure but is not an accepted revision. Physical envelopes are not required for import. A load needs a separate fixture check; targeting needs future travel/coverage validation.

Proposed synthetic-import-v1 reconciliation test tolerance (not verified production accuracy or an operational default) is <=0.05 mm positional and <=0.1 degree angular disagreement, measured after transforms and declared component symmetry (default 360-degree period, never guessed). A mismatch fails unless a reviewed authority decision resolves it. Check placement references, sides, footprint identity, duplicate references, BOM quantity/reference expansion, missing/excess references, and paste alignment evidence. Known DNP entries may have a footprint without a populated placement; mechanical features need explicit exemption. Fiducial correspondences or declared exporter datum evidence establish source registration; matching extents alone is insufficient. Source revision labels and file hashes cannot prove that separate exports came from the same board. Record explicit revision attestation and geometric checks; reject contradictions, and block promotion when consistency cannot be established.

## 6. Errors

BOARD_CAPACITY_EXCEEDED means the declared capacity-test orientation exceeds BoardCapacity. BOARD_OUT_OF_ENVELOPE means a loaded outline violates an explicitly supplied FixtureEnvelope. Unresolved physical dimensions are FitReport states, not invented pass results. POLICY_INVALID rejects invalid/mismatched policy data; MAPPING_UNVALIDATED rejects missing independent validation evidence. Inspection-boundary mapping failures carry the underlying error codes and disposition REVIEW.

Blocking codes: SCHEMA_INVALID, FORMAT_UNSUPPORTED, PARSE_FAILED, INPUT_LIMIT_EXCEEDED, UNITS_UNKNOWN, SOURCE_CONVENTION_UNKNOWN, TRANSFORM_MISSING, TRANSFORM_AMBIGUOUS, TRANSFORM_SINGULAR, TRANSFORM_ILL_CONDITIONED, OUTSIDE_VALID_DOMAIN, POINT_AT_INFINITY, CONTEXT_MISMATCH, CALIBRATION_INVALID, CALIBRATION_STALE, IMAGE_SIZE_MISMATCH, FIDUCIAL_INSUFFICIENT, FIDUCIAL_DEGENERATE, REGISTRATION_QUALITY_FAILED, OUTLINE_INVALID, BOARD_CAPACITY_EXCEEDED, BOARD_OUT_OF_ENVELOPE, POLICY_INVALID, MAPPING_UNVALIDATED, DUPLICATE_REFERENCE, DUPLICATE_ID, REFERENCE_UNRESOLVED, BOM_QUANTITY_MISMATCH, SIDE_LAYER_MISMATCH, SOURCE_CONFLICT, REVISION_MISMATCH, REQUIRED_ARTIFACT_MISSING, PROFILE_INCOMPLETE. Warnings include OPTIONAL_DATA_ABSENT, PASTE_PAD_UNMATCHED, REVISION_LABEL_REUSED, and ACKNOWLEDGED_SOURCE_OVERRIDE. Warnings cannot downgrade a mandatory gate. Reports identify source rows/entities where possible and describe a concrete correction.

## 7. Optional inspection component and six-machine isolation

The [Aman9y/open-aoi README](https://github.com/Aman9y/open-aoi/blob/main/README.md), reviewed 2026-10-16, describes an OpenCV inspection/alignment pipeline and region-oriented comparisons. This motivates an optional adapter, not an assertion of native KiCad/Gerber import or API compatibility. Before reuse, pin a commit and review its license, data types, pixel conventions, and alignment behavior.

The proposed adapter accepts BuildInspectionInput and returns feature-linked observations with explicit output frame, revision/capture IDs, quality status, and the engine's applied alignment/crop transform. Pixel displacements cannot be relabeled millimeters without the validated local mapping. Missing/unknown engine transforms produce an unusable result, never an assumed identity. Image-aligned coordinates may be reported in I_e; machine/PCB coordinates are derived only through known paths. No engine result can mutate source geometry or calibration. Adapter absence leaves all foundation imports and geometry tests operational. Detector evaluation and decision thresholds are deferred.

Machine-scoped keys include machine_id and camera_id; captures also bind revision, side, load, and calibration identities. A synthetic six-machine test uses overlapping capture names and different transforms to prove isolation in one process. Queueing, networking, and throughput are deferred; these identities do not imply a distributed architecture.

## 8. Verification and remaining decisions

All proposed tests use file fixtures, synthetic images/points, and fake metadata. They need no physical camera, motion hardware, firmware, external inspection engine, or network. Capability specs carry the normative scenarios and tasks trace them into later work. Round-trip tests are paired with independently calculated forward values so equally wrong forward and inverse mappings cannot pass unnoticed.

Reviewer decisions: preserve the canonical conventions; approve configurable synthetic policies and independent validation evidence; identify the real PCB and record KiCad 10.0.7 producer/build evidence, exporter settings and parser versions; evaluate the Gerber reuse candidate. Fixture geometry/margins and camera travel/coverage await optics/mechanics selection. Unverified support and all production qualification remain TBD. Actual optical accuracy and board warp limits require later hardware evidence. No production readiness is claimed.

## 9. Implementation acceptance levels

These are future implementation acceptance gates, not statements of current completion. Both levels preserve every GEO-001 and PCB-001 requirement and the future 3D boundary. Numeric limits remain selected versioned synthetic policies. Neither level proves physical accuracy, travel/coverage, production calibration or inspection performance. OpenSpec document validation checks change structure only; it is not implementation acceptance evidence.

### Foundation Prototype

Target: after Sprint 4, subject to all gates below. A restricted import demonstration is permitted while full capability conformance remains explicitly open.

1. Typed frame/point/transform/context models and source-to-PCB/machine conversion pass independent stage oracles, composition/inversion, angle/parity, unit and invalid-path tests under the selected synthetic policy. The canonical equations and (1,2) inch -> (60.8,45.4) mm result remain unchanged.
2. One real KiCad 10.0.7 board bundle meets the Sprint 2 prerequisite. Its actual `.kicad_pcb` imports with independently checked outline, footprints, pads and explicitly classified fiducials. Producer/build/settings, artifact hashes and parser version are recorded. Missing real fixture evidence blocks this gate.
3. A documented pinned PyGerber or Gerbonara reuse evaluation precedes the Paste adapter. The real F.Paste imports with explicitly evidenced source alignment, independent filled-geometry checks and preserved provenance. B.Paste is tested when bottom-side SPI is requested. Unsupported constructs fail explicitly, even when the library accepts them.
4. The real placement/BOM reconcile with that same revision using declared origin/units/angles/sides, references, quantities and population states. Synthetic negative companions exercise duplicate/unresolved references, conflicting sources and missing required artifacts. The requested SPI/post-placement profile gates pass only for the evidenced subset; untested support stays TBD.
5. Accepted revisions are immutable and reproducible, carry artifact/transform/parser/policy provenance, and survive failed-import rollback. Same-label/different-content and mixed-revision cases are tested. Frame and machine context cannot silently cross namespaces; synthetic mismatched-context tests pass for the implemented transformations. Full six-machine camera/calibration isolation remains OPEN until Sprint 5 evidence exists.
6. BoardCapacity, FixtureEnvelope and CameraTravelEnvelope stay separate, with unresolved physical checks reported as unresolved. Missing/unvalidated camera mappings cannot yield usable inspection coordinates or GOOD: unavailable geometry operations reject, and any exposed inspection boundary returns blocked REVIEW. Unsupported paths are disabled or explicitly rejected, never approximated by identity/stale calibration.
7. An acceptance report states the exact implemented subset, fixture/test evidence and all incomplete requirement/scenario names with original task IDs and planned follow-up. `sprint-plan.md` is the initial OPEN register. Passing this milestone does not close the change, mark unimplemented requirements satisfied, or turn partial tasks into completed tasks.

### Foundation Complete

Target: after Sprint 5 and any remaining closure work; elapsed sprints alone are insufficient.

1. All Foundation Prototype gates remain satisfied. Every normative requirement and scenario in both capability specs has traceable implementation and executed passing evidence, including supported positive cases and required rejection cases. No incomplete in-scope normative requirement may remain OPEN. Partial implementation or deferred in-scope tests blocks this level; do not relabel them optional or remove them for acceptance.
2. Camera projection, lens mapping, raster transforms, runtime dimensions and domains pass independent synthetic oracles. Two-fiducial metric rigid registration and four-or-more-point homography pass their distinct fit and independent-validation gates; missing evidence produces typed rejection and REVIEW.
3. Calibration-policy version/purpose enforcement, activation/invalidation, historical context and six-machine isolation pass the complete specified scenarios. Synthetic results cannot qualify production context; no real camera or firmware is needed for these software tests.
4. All import scenarios, real-fixture coverage and additional representative positive/negative fixtures pass. Exact tested versions/settings/library/adapter versions and results are recorded in supported-inputs.md; unsupported combinations have explicit rejection evidence. One real fixture is a baseline, not proof of every construct or dialect. Valid profiles for both sides must be exercised where the normative scenarios require them; the seed fixture need not itself have bottom-side SPI.
5. Every original implementation task has evidence or an explicitly justified optional-path decision consistent with the specs; no normative behavior may be waived. A decision not to integrate open-aoi is permitted, but its evaluation and fake-engine boundary tests remain required. Every scenario maps to evidence; reruns are offline and reproducible. Only Geometry Core evidence currently exists; it does not establish complete capability conformance.
6. Future 3D, physical travel/coverage, production accuracy, firmware and deployment remain explicitly outside this change. The specification requires these boundaries to remain unresolved, not a hardware qualification project to be completed. Foundation Complete is software-foundation conformance only.

### Selected Sprint 1 fixture subset (user decision, 2026-10-17)

These implementation decisions supplement, and do not narrow, the original normative requirements. The user explicitly selected axis-aligned rectangles in machine frame M for usable regions and exclusions, and single closed board contours of lines and circular arcs. Holes, splines and nonrectangular envelopes reject with `GEOMETRY_UNSUPPORTED`; broader normative geometry support remains open in the implementation ledger.

The selected contact policy permits contact with the usable boundary at zero margin. Exclusions are closed: intersection, either direction of containment, and boundary contact all fail. Positive margin requires minimum Euclidean clearance at least the declared margin from both the usable boundary and exclusions; exclusion contact is always forbidden. Fixture evaluation uses the entire outline after an explicit validated proper-rigid load into the exact envelope frame. It does not infer a load from matching IDs, reuse capacity rotation as placement, or treat a bounding box or endpoint sample as the filled board. Rectangle outer containment uses analytic full-contour extrema; exclusion checking combines analytic curve/rectangle distance with both containment directions.

Implementation numerical policy `fixture-binary64-v1` uses the bounded contour kernel (coordinates/radii <=1e6 mm, <=512 edges) and a 1e-8 mm arithmetic guard. Outer signed clearance and positive-margin distance comparisons allow at most that guard for roundoff; exclusion contact/overlap predicates conservatively reject separation <=1e-8 mm. This is not manufacturing tolerance or qualification evidence. A 0.001 mm outer overrun or margin shortfall must fail. Exact margin is accepted unless exclusion contact is involved. Near-contact configurations within the guard can conservatively fail and are not certified physically clear.

Missing usable geometry, margin or explicit load leaves fixture status unresolved with reasons. Supplied unsupported geometry rejects even when another input is missing. Capacity remains independent of placement; camera reachability always remains unresolved, including with a travel rectangle. Fit results retain policy, context, record identities/versions and evidence IDs and never authorize motion or targeting. Synthetic evidence is never promoted to qualified evidence. Import integration, broader outline/envelope geometry and lifecycle qualification remain open.

### Evidence and status rules

Record level, candidate revision, fixture/source hashes, selected policy IDs, exact versions/settings, test identifiers/results, and per-requirement status OPEN/PARTIAL/SATISFIED. PARTIAL is still open for conformance. Only recorded passing evidence can promote a scenario; one passing scenario cannot close a requirement with other open scenarios. Prototype acceptance may coexist with OPEN requirements. Complete acceptance may not. Current state: Geometry Core has executed synthetic tests; only tasks 4.1–4.4 are completed. Neither acceptance level is achieved. Remaining implementation/fixture/calibration results stay open or TBD; see implementation-status.md. See sprint-plan.md for sprint entry/exit gates, original-task mapping and the initial open-requirement register.
