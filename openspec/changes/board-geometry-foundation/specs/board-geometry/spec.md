# GEO-001 — Board geometry

## ADDED Requirements

### Requirement: Explicit coordinate frames and canonical units
The system SHALL represent canonical physical PCB geometry in millimeters in revision-bound frame P, top-view +X right and +Y up. Every geometric source, footprint, machine, raw/undistorted image, and derived raster SHALL have a distinct frame identity, declared units, origin, axes, and context. Image dimensions SHALL be runtime positive integers; no camera model or resolution SHALL be hardcoded. Both board sides SHALL retain the same top-view canonical P frame with independent side tags.

#### Scenario: Unit and axis conversion has an independently verified result
- **GIVEN** a source point (1,2) inch, axis mapping diag(1,-1), 90-degree CCW rotation, and translation (10,20) mm
- **WHEN** it is normalized to P
- **THEN** it SHALL equal (60.8,45.4) mm within 1e-6 mm and retain the source and transform IDs.

#### Scenario: Independent intermediate transformation oracles
- **GIVEN** the same source example and independently calculated checkpoints
- **WHEN** each stage and its inverse are checked under synthetic-geometry-v1
- **THEN** unit conversion SHALL yield (25.4,50.8) mm, reflection (25.4,-50.8) mm, rotation (50.8,25.4) mm, and translation (60.8,45.4) mm. Inverse stages SHALL yield (50.8,25.4), (25.4,-50.8), (25.4,50.8) mm and finally (1,2) inch. A passing round trip SHALL NOT replace these forward oracles.

#### Scenario: Different image sizes remain data-driven
- **GIVEN** two synthetic calibrations with raw sizes 640 x 480 and 2048 x 1536
- **WHEN** matching captures are validated
- **THEN** both SHALL be accepted without a code/configuration default overriding dimensions; a capture with incompatible dimensions SHALL fail IMAGE_SIZE_MISMATCH.

### Requirement: Explicit transform direction, composition, and inversion
The system SHALL use column-vector transforms T_B_A from A to B, composed right to left, and record type, endpoints, units, domain, parity, and provenance. Source normalization SHALL explicitly declare unit conversion, axes/reflection, rotation, and translation. Unknown origin or side conventions SHALL block conversion. Singular, ill-conditioned, ambiguous, or context-incompatible paths SHALL fail with typed errors. Finite points SHALL be converted without intermediate rounding.

#### Scenario: Composition and round trips
- **GIVEN** a source-to-PCB transform and PCB-to-machine rigid transform with nonzero translations and noncommuting rotations
- **WHEN** a point is mapped by the composed and sequential paths and then inverted
- **THEN** both forward results SHALL agree with independently calculated expected coordinates, and returned source coordinates SHALL differ by at most 1e-6 in their physical mm equivalent.

#### Scenario: Unknown origin is not guessed
- **GIVEN** a Gerber and placement file with similar extents but undeclared relative origins
- **WHEN** a path between their frames is requested
- **THEN** it SHALL fail TRANSFORM_MISSING or SOURCE_CONVENTION_UNKNOWN and SHALL NOT align their bounding-box minima automatically.

#### Scenario: Invalid transform paths
- **GIVEN** respectively a zero-scale matrix, a normalized matrix over the condition limit, and two disagreeing paths between the same contextual frames
- **WHEN** paths are validated
- **THEN** they SHALL fail TRANSFORM_SINGULAR, TRANSFORM_ILL_CONDITIONED, and TRANSFORM_AMBIGUOUS respectively, with no converted batch returned.

### Requirement: Rotations and bottom-side parity
The system SHALL store canonical component angles in degrees in [0,360), positive CCW viewed from top, and signed differences in [-180,180). It SHALL transform component direction vectors and parity consistently with their geometry. Bottom mirroring SHALL require an explicit source convention and reflection axis; layer side alone SHALL NOT cause reflection. Angle comparison SHALL use an explicitly declared symmetry period, default 360 degrees.

#### Scenario: Bottom mirror and orientation
- **GIVEN** a bottom-view source with reflection about x=5 mm and point (2,3), local +X orientation
- **WHEN** mapped to top-view P
- **THEN** point SHALL be (8,3), orientation SHALL be 180 degrees, and parity SHALL be reflected; applying the inverse SHALL recover position, direction, and parity. A bottom layer already expressed in top-view P SHALL remain unmirrored.

#### Scenario: Rotation wraparound
- **GIVEN** component orientations 359.95 and 0.02 degrees
- **WHEN** their signed angular difference is compared
- **THEN** its magnitude SHALL be 0.07 degrees and SHALL NOT be treated as a nearly full rotation.

### Requirement: Planar camera mapping and pixel semantics
The system SHALL separate lens distortion D from planar homography H. It SHALL bind each mapping to its plane, machine/camera configuration, capture pose, raw/undistorted dimensions, and valid domain. Integer pixel coordinates SHALL denote centers; derived crops/resizes SHALL have explicit frame mappings. Out-of-domain points and projective horizon points SHALL fail. ROI clipping SHALL report inside/partial/outside visibility without silently changing the requested physical geometry.

#### Scenario: Known planar projection
- **GIVEN** undistorted projection u=10x+100, v=-10y+200 and no distortion
- **WHEN** PCB point (3,4) mm is converted
- **THEN** it SHALL yield (130,160) px, and the inverse SHALL recover (3,4) within 1e-6 mm. Tests SHALL also cover a non-affine projective mapping with an independently calculated oracle.

#### Scenario: Nonlinear distortion and derived raster
- **GIVEN** a synthetic invertible nonzero lens distortion profile within its valid domain and an explicitly declared crop/resize mapping
- **WHEN** raw -> undistorted -> PCB -> undistorted -> raw round trips are evaluated
- **THEN** raw pixel error SHALL be <=1e-3 px under recorded solver limits, and the engine-raster path SHALL agree with its independently computed crop/resize oracle.

#### Scenario: Invalid projection or missing crop mapping
- **GIVEN** a point with normalized homography denominator <=1e-12 in magnitude, or an engine raster lacking its parent transform
- **WHEN** conversion is requested
- **THEN** it SHALL fail POINT_AT_INFINITY or TRANSFORM_MISSING respectively. A partially visible ROI SHALL instead return explicit clipping and visibility metadata under the ROI contract.

### Requirement: Fiducial registration quality
The system SHALL fit proper rigid poses from at least two calibrated metric correspondences and planar homographies from at least four full-rank correspondences. It SHALL preserve fiducial identity/revision/side, fixed physical scale, fit diagnostics and independent validation evidence, enforcing the selected CalibrationPolicy in design.md. Failed or unvalidated fits SHALL NOT activate.

#### Scenario: Valid rigid and projective fits
- **GIVEN** synthetic exact rigid observations with baseline >=10 mm and independent handedness/correspondence evidence, and a separate full-rank projective set covering >=10% of the ROI with independent known-transform checkpoints
- **WHEN** fitted under the proposed policy
- **THEN** the proper rigid pose and projective mapping SHALL be recovered within numerical tolerances and reported as validated candidates; activation SHALL require an explicit operation.

#### Scenario: Degenerate or mismatched fiducials
- **GIVEN** coincident rigid points, collinear projective points, insufficient coverage, duplicate IDs, wrong-side IDs, or residuals above the RMS/maximum limits
- **WHEN** registration is evaluated
- **THEN** it SHALL fail with the relevant FIDUCIAL_DEGENERATE, DUPLICATE_ID, CONTEXT_MISMATCH, or REGISTRATION_QUALITY_FAILED error. Too few observations SHALL fail FIDUCIAL_INSUFFICIENT.

#### Scenario: Two points do not validate a camera homography
- **GIVEN** two valid metric correspondences and independent rigid-model evidence
- **WHEN** rigid fitting and general homography fitting are requested separately
- **THEN** rigid fitting MAY validate under policy, but homography fitting SHALL fail FIDUCIAL_INSUFFICIENT. Reflection SHALL NOT be claimed detectable from the pair alone.

#### Scenario: Exact fit without independent validation
- **GIVEN** four homography fit points with near-zero fitting residual and no independent checkpoints or evidenced reference mapping
- **WHEN** validation and inspection input construction are requested
- **THEN** validation SHALL reject MAPPING_UNVALIDATED, no mapping SHALL activate, and inspection input SHALL be blocked with disposition REVIEW, reasons/context and no usable ROIs; GOOD SHALL NOT be emitted.

### Requirement: Configurable synthetic calibration policies
CalibrationPolicy SHALL be immutable, versioned, explicitly selected, unit-bearing and configurable as defined in design.md. The numerical values in this specification SHALL denote proposed synthetic-geometry-v1 test limits, not verified production accuracy or production defaults. Synthetic and production contexts SHALL remain distinct. Production qualification and policy values are TBD.

#### Scenario: Policy changes and invalid values
- **GIVEN** a changed residual limit or missing/nonfinite/negative/inconsistent policy parameter
- **WHEN** validation is requested
- **THEN** a valid change SHALL create a new policy version and require mapping revalidation; invalid parameters SHALL fail POLICY_INVALID without activation.

#### Scenario: Synthetic pass cannot certify production accuracy
- **GIVEN** a mapping active for synthetic tests under synthetic-geometry-v1
- **WHEN** a production-context request attempts to use it without production qualification
- **THEN** the request SHALL reject the policy/context mismatch and the inspection boundary SHALL return REVIEW, never an accuracy certification or synthetic-policy fallback.

#### Scenario: Invalid mapping at the inspection boundary
- **GIVEN** a missing, stale, degenerate, out-of-domain or context-incompatible mapping
- **WHEN** conversion and inspection input construction are requested
- **THEN** conversion SHALL return the relevant typed error with no usable results; inspection input SHALL return blocked REVIEW with underlying reasons/context, no usable ROIs and no identity/stale/relaxed-policy substitution.

### Requirement: Calibration and registration lifecycle isolation
Calibration and registration SHALL be immutable, versioned and context-bound, with explicit draft/validated/active/invalidated states. Conversion for inspection SHALL require active compatible records. Configuration, load, fixture, revision, side, or machine changes SHALL invalidate affected mappings; historical records SHALL remain replayable with historical context. No fallback to another machine's calibration is allowed.

#### Scenario: Six machines share processing without sharing geometry
- **GIVEN** six machine identities, each with a camera, different calibration and registration, and colliding local capture names
- **WHEN** all are resolved in one process
- **THEN** each SHALL resolve only its own contextual mapping; a request mixing machine 1's capture with machine 2's calibration SHALL fail CONTEXT_MISMATCH.

#### Scenario: Configuration or load changes
- **GIVEN** an active mapping followed by a camera configuration change or new board load
- **WHEN** the old mapping is requested for the new context
- **THEN** it SHALL fail CALIBRATION_STALE or CONTEXT_MISMATCH; a historical replay with its original context SHALL remain identifiable and reproducible.

### Requirement: Separate board capacity, fixture and camera travel
The system SHALL distinguish BoardCapacity (280 x 550 mm), FixtureEnvelope (mounting region/margins in M) and CameraTravelEnvelope (camera-reference positions in M). Physical envelope dimensions SHALL remain TBD until optics/mechanics selection. FitReport SHALL keep capacity, fixture and camera-reachability statuses separate; unknowns SHALL remain unresolved. Pure-data checks SHALL NOT infer travel from board size or authorize targeting.

#### Scenario: Exact fit, rotation, and overrun
- **GIVEN** valid rectangular outlines and declared capacity-test orientations
- **WHEN** a 280 x 550 board is tested at zero rotation, a 550 x 280 board at 90 degrees, and a 280.001 x 550 board at zero rotation
- **THEN** the first two SHALL pass capacity and the last SHALL fail BOARD_CAPACITY_EXCEEDED. Machine translation SHALL NOT change capacity results.

#### Scenario: Synthetic fixture fit is independent of capacity
- **GIVEN** a capacity-compliant board and an explicitly synthetic fixture [0,280] x [0,550] with zero margin
- **WHEN** the outline is translated outside the fixture or a positive fixture margin excludes it
- **THEN** fixture fit SHALL fail BOARD_OUT_OF_ENVELOPE while capacity remains passed; the fixture SHALL NOT become a physical camera-travel default.

#### Scenario: Unresolved mechanics does not invent readiness
- **GIVEN** a capacity-compliant board with no selected fixture or camera-travel geometry
- **WHEN** import and fit reporting run
- **THEN** import MAY pass its data gates, fixture/camera statuses SHALL remain unresolved, and no physical targeting readiness SHALL be claimed. A supplied camera-travel rectangle alone SHALL NOT prove optical coverage.

#### Scenario: Complete coordinate verification without hardware
- **GIVEN** synthetic corner, edge, interior, negative-coordinate, mirrored, and randomized well-conditioned frame cases with fixed seed
- **WHEN** acceptance tests execute on a PC
- **THEN** affine/rigid and distortion-free projective round trips SHALL meet the proposed 1e-6 mm/px bounds, independently calculated forward values SHALL pass, and no firmware, camera, gantry, external engine, or network SHALL be required.
