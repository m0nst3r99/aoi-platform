# PCB-001 — PCB data import

## ADDED Requirements

### Requirement: Verified input support evidence

`supported-inputs.md` SHALL be the support evidence register. Exact tested KiCad/exporter/parser/library versions, settings, Gerber constructs, BOM/placement dialects and representative fixtures SHALL be recorded before support is claimed. Unverified entries SHALL be TBD. Each verified entry SHALL cite fixture IDs/hashes, independent expected results and actual test evidence.

#### Scenario: Unverified versions remain TBD
- **GIVEN** a target format with no exact-version fixture evidence
- **WHEN** release support is determined
- **THEN** its tested version/result SHALL remain TBD and SHALL NOT enter the support allowlist; unsupported runtime inputs SHALL fail FORMAT_UNSUPPORTED.

### Requirement: Declared source formats and import profiles
The system SHALL ingest version-profiled KiCad PCB, Gerber RS-274X Paste, component-placement CSV/TSV, and BOM CSV/TSV through an explicit manifest. It SHALL declare supported versions/features and reject unsupported content rather than skip it. The `geometry`, `spi-2d`, `post-placement-2d`, and combined profiles SHALL enforce the artifact and completeness rules in design.md. No profile SHALL require ESP32 firmware, a camera, or gantry hardware.

#### Scenario: Complete combined import
- **GIVEN** a supported KiCad board, top/bottom Paste Gerbers for requested sides, placement, BOM, and a fully resolved manifest
- **WHEN** both inspection profiles are requested and all validation gates pass
- **THEN** one immutable canonical revision SHALL be published with both capabilities, artifact hashes, source mappings, and an accepted report.

#### Scenario: Missing or unsupported input
- **GIVEN** an SPI request without the selected side's Paste Gerber, a post-placement request without BOM, or an unsupported KiCad version/Gerber construct
- **WHEN** import is validated
- **THEN** it SHALL fail REQUIRED_ARTIFACT_MISSING or FORMAT_UNSUPPORTED, identify the source or required role, and SHALL NOT publish an apparently complete empty dataset.

#### Scenario: Geometry-only import
- **GIVEN** valid KiCad plus manifest and no inspection exports
- **WHEN** the geometry profile is requested
- **THEN** it SHALL publish geometry with absent optional artifacts reported and SHALL reject a later inspection-input request that requires an unfulfilled profile.

### Requirement: Per-source units, origin, side, and revision evidence
Every geometric source SHALL have an explicit source frame and transform into canonical P as specified by GEO-001. Units, coordinate format, axis convention, angle convention and side/layer SHALL be declared or unambiguously established by supported file metadata plus manifest. Conflicting metadata SHALL fail. The system SHALL preserve source coordinates and evidence; it SHALL NOT assume common origin or recenter sources independently.

#### Scenario: Independent Gerber and placement origins
- **GIVEN** equivalent features exported with a Gerber offset of (50,25) mm and placement in inches at a different origin
- **WHEN** declared unit conversions and independently evidenced transforms are applied
- **THEN** their canonical geometry SHALL agree with the KiCad oracle within policy; removing either origin declaration SHALL fail rather than retain apparent alignment.

#### Scenario: Contradictory units or side
- **GIVEN** metadata declaring inches but a manifest claiming mm, or a bottom Paste layer assigned as top
- **WHEN** validated
- **THEN** it SHALL fail SOURCE_CONFLICT or SIDE_LAYER_MISMATCH and point to the conflicting declarations.

### Requirement: Canonical outline, footprints, components, pads, and fiducials
The system SHALL retain board outline/cutouts, footprint instances, component positions/orientations/sides, copper pads and their local-to-board transforms, and approved fiducials using the typed models in design.md. It SHALL preserve nonrectangular geometry and source provenance. It SHALL NOT derive body dimensions solely from a footprint name or classify every circular pad as a fiducial.

#### Scenario: Bottom footprint and repeated pad numbers
- **GIVEN** a supported KiCad fixture with a rotated bottom footprint, repeated pad numbers, a nonrectangular outline and a cutout
- **WHEN** normalized
- **THEN** geometry and orientation SHALL match independently calculated top-view coordinates, every pad SHALL have a unique pad ID, repeated source numbers SHALL remain strings, and topology SHALL be preserved.

#### Scenario: Invalid outline or nonfinite coordinate
- **GIVEN** an open/self-intersecting outline, nonfinite coordinate, or duplicate entity ID
- **WHEN** validated
- **THEN** it SHALL fail OUTLINE_INVALID, SCHEMA_INVALID, or DUPLICATE_ID before publication, identifying the source entity where available.

#### Scenario: Fiducial approval
- **GIVEN** designated fiducial footprints and unrelated circular pads
- **WHEN** candidates are imported
- **THEN** only explicitly classified/approved entities SHALL become registration fiducials, with side, dimensions, IDs and provenance retained.

### Requirement: Gerber parser reuse evaluation

Before implementing Gerber parsing from scratch, the project SHALL evaluate reuse of PyGerber or Gerbonara. The decision SHALL record exact candidate version, licensing, geometry/provenance behavior, construct coverage and fixture results. A from-scratch decision SHALL document why reuse is insufficient and a reviewed scope. Dependency acceptance of a file SHALL NOT excuse lost or approximated semantics.

#### Scenario: Reuse evaluation precedes a custom parser
- **GIVEN** proposed Gerber implementation work
- **WHEN** its dependency gate is reviewed
- **THEN** a documented PyGerber or Gerbonara evaluation SHALL precede from-scratch parsing; missing evaluation SHALL leave that work blocked. Candidate support SHALL require pinned-version fixture evidence.

#### Scenario: Library cannot interpret a construct
- **GIVEN** a construct outside the verified adapter/library support matrix, even if a library accepts the file
- **WHEN** import is validated
- **THEN** it SHALL fail FORMAT_UNSUPPORTED with construct/source-location details and publish no revision rather than omit or approximate geometry.

### Requirement: Manufactured paste geometry
Gerber Paste SHALL be resolved into filled geometry with aperture definitions/macros, flashes, draws, regions, polarity and file transforms honored when supported. Unsupported semantics SHALL fail. The system SHALL retain manufactured paste openings independently of copper pad geometry, with optional many-to-many links and reported unmatched features.

#### Scenario: Paste reductions, split apertures, and clear regions
- **GIVEN** a fixture with two reduced paste windows for one copper pad and a dark region containing a clear opening
- **WHEN** interpreted and normalized
- **THEN** resolved geometry SHALL match an independent geometry oracle including the clear opening; two windows SHALL remain distinct and linked to the one pad. Copper geometry SHALL remain unchanged.

#### Scenario: Unmatched paste feature
- **GIVEN** a correctly registered Paste feature without a reliable pad association
- **WHEN** SPI import passes its other gates
- **THEN** the feature SHALL be retained with PASTE_PAD_UNMATCHED warning and no fabricated pad ID. Unresolved source registration SHALL still block import.

### Requirement: Placement and BOM joins with explicit authority
The system SHALL normalize declared placement columns, angle direction/zero, units, sides, references, and BOM reference groups/population status. It SHALL check reference uniqueness, quantities, footprint/side agreement and positional/angular consistency against KiCad under the versioned reconciliation policy. Field-level overrides SHALL require a recorded authority decision and warning; silent overwrite is prohibited.

#### Scenario: Valid grouped BOM and DNP
- **GIVEN** BOM group R1-R3 with quantity 3 under a declared range-expansion profile, and R3 marked DNP with a footprint but no populated placement
- **WHEN** post-placement validation runs
- **THEN** references SHALL expand deterministically and R3 SHALL remain explicitly DNP, excluded from populated inspection coverage while retaining its geometry.

#### Scenario: Conflicting assembly records
- **GIVEN** respectively duplicate placement R1, unresolved populated reference U99, BOM quantity 2 for three references, wrong component side, or an unapproved 0.2 mm placement disagreement
- **WHEN** validated
- **THEN** it SHALL fail DUPLICATE_REFERENCE, REFERENCE_UNRESOLVED, BOM_QUANTITY_MISMATCH, SIDE_LAYER_MISMATCH, or SOURCE_CONFLICT respectively with source-row evidence.

#### Scenario: Reviewed field override
- **GIVEN** a placement disagreement resolved by an explicit field-specific authority decision naming source, reason, and reviewer
- **WHEN** imported
- **THEN** the chosen value and original conflicting values SHALL remain traceable, with ACKNOWLEDGED_SOURCE_OVERRIDE warning. Unrelated profile/schema failures SHALL remain blocking.

### Requirement: Immutable revisions and deterministic provenance
Accepted imports SHALL create immutable board revisions with board identity, human revision label, content identity, optional parent, source byte hashes, manifest decisions, policies, and parser/schema versions. Revision labels alone SHALL NOT establish equivalence. Cross-export revision evidence SHALL include attestation and geometric consistency checks; contradictions or unestablished required consistency SHALL block promotion.

#### Scenario: Reproducible import and reused labels
- **GIVEN** identical source bytes, manifest and policy, imported twice with different timestamps/paths
- **WHEN** canonical content identity is calculated
- **THEN** the same digest SHALL result. Changing geometry or a transform decision SHALL produce a new digest; reusing the label SHALL warn REVISION_LABEL_REUSED and require acknowledgment without overwriting the prior revision.

#### Scenario: Mixed board exports
- **GIVEN** KiCad revision B and placement/Paste from revision A with contradictory references or geometry
- **WHEN** combined import is validated
- **THEN** it SHALL fail REVISION_MISMATCH or SOURCE_CONFLICT even if filenames and nominal board dimensions match.

### Requirement: Independent data import and physical readiness

Import SHALL check BoardCapacity independently of physical FixtureEnvelope and CameraTravelEnvelope. Unresolved physical envelopes SHALL NOT block otherwise valid canonical data import or be treated as passes. BuildInspectionInput SHALL return blocked REVIEW with reasons/context and no usable ROIs when its required mapping/profile cannot be validated. Synthetic reconciliation limits SHALL NOT imply production accuracy.

#### Scenario: Valid board with unresolved physical envelopes
- **GIVEN** a valid capacity-compliant import and TBD fixture/travel dimensions
- **WHEN** canonical revision publication is requested
- **THEN** revision/provenance guarantees SHALL remain intact and physical fit/reachability SHALL remain unresolved without motion-readiness or production-accuracy claims.

### Requirement: Atomic contracts and actionable validation reports
ValidateImport, NormalizeBoard, and BuildInspectionInput SHALL follow the input/output and typed-error contracts in design.md. Required-profile failure SHALL yield no published revision. Reports SHALL retain safely discoverable errors/warnings, field/source locations, policy results and remediation. File content SHALL be treated as data with configured resource limits.

#### Scenario: Multiple errors and rollback
- **GIVEN** malformed numeric placement cells and a BOM reference conflict in independently parseable inputs
- **WHEN** validated
- **THEN** all safely discoverable issues SHALL be reported in stable order; an earlier accepted revision SHALL remain unchanged and no partial new revision SHALL be published.

#### Scenario: Import bounds and parsing settings
- **GIVEN** an artifact exceeding configured byte/entity limits or a CSV with ambiguous undeclared decimal/delimiter rules
- **WHEN** ingested
- **THEN** it SHALL fail INPUT_LIMIT_EXCEEDED or PARSE_FAILED without executing source content or guessing conventions.

### Requirement: Optional inspection-engine interoperability
Canonical board geometry and imports SHALL function without Aman9y/open-aoi. An optional adapter SHALL exchange revision/capture-bound image references and feature-linked ROIs/observations with explicit frame mappings, side, units and quality status. Cropping, resizing or alignment performed by an engine SHALL be represented by returned transforms. No assumed open-aoi API or deployment dependency is introduced.

#### Scenario: Adapter absent
- **GIVEN** no open-aoi installation and only synthetic/file fixtures
- **WHEN** foundation acceptance tests execute
- **THEN** all GEO-001 and PCB-001 import/geometry tests SHALL remain executable and no network or inspection-engine service SHALL be required.

#### Scenario: Engine changes image frame
- **GIVEN** an optional fake engine returning observations in a cropped/aligned raster
- **WHEN** an adapter maps observations to P
- **THEN** known transforms SHALL recover independently expected physical coordinates; absent transforms or mismatched revision/capture IDs SHALL fail TRANSFORM_MISSING or CONTEXT_MISMATCH. Pixel distances SHALL NOT be relabeled as mm.
