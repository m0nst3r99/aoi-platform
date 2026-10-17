# Supported inputs and verification register

Status: specification planning only. No exact tested input/exporter/parser versions or executable fixture results are evidenced in this change. All unverified entries are **TBD**. Target formats and planned fixture names are not working-support claims. Do not infer versions from memory, presumed compatibility or advertised library features.

AOI Platform V0.1 initial target: **KiCad 10.0.7**. This target is selected; verified compatibility is not. Actual producer/build evidence, unverified exporter settings, parser/library versions, fixture hashes and test results remain TBD. A candidate profile may be exercised in isolated development tests to establish evidence; this does not add it to the released support allowlist. Foundation Prototype and Foundation Complete gates are defined in design.md section 9 and scheduled in sprint-plan.md.

## Evidence required for verified support

Record exact producer name/version/build (KiCad and exporter/plugin separately), board format version, export settings, units, origin, axes, angle/side conventions, artifact SHA-256, fixture ID/path, parser/library name and exact version, adapter/schema version, independent expected geometry/error, test command/result/date and relevant dependency/platform versions. Each positive fixture verifies only its declared combination. Negative fixtures establish rejection, not positive support. Update the supported-input allowlist and this evidence register together.

## KiCad and exporters

| Target | Initial KiCad target | Exact tested version/build | Exact exporter/plugin version and settings | Parser version | Planned fixtures | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `.kicad_pcb` s-expression board | 10.0.7 | TBD | Native writer/build evidence and saved format token TBD | TBD | REAL-PCB-01; KICAD-01..03 | TBD |
| F.Paste; B.Paste when bottom SPI requested | 10.0.7 | TBD | Plotter/version, units, format, origin and X2 options TBD | TBD | REAL-PCB-01; GERBER-01..08 | TBD |
| Component placement | 10.0.7 | TBD | Exporter/version, origin, units, side and angle options TBD | TBD | REAL-PCB-01; PLACE-01/02 | TBD |
| BOM | 10.0.7 board workflow | TBD | Native/plugin exporter/version, headers, grouping, population settings TBD | TBD | REAL-PCB-01; BOM-01/02 | TBD |

No KiCad major/minor/patch version is currently verified. Legacy `.brd`, ODB++, IPC-2581 and Gerber X3 placement remain deferred.

## REAL-PCB-01 — Sprint 2 prerequisite

Provide one actual PCB design revision, saved/exported using the KiCad 10.0.7 target workflow, before Sprint 2 import implementation begins. Board identity, owner/source, revision label, files and hashes are currently TBD. A synthetic board alone does not fulfill this prerequisite. Acquiring or exporting these files is future work, not performed by this amendment.

| Required bundle item | Entry evidence to record | Current evidence |
| --- | --- | --- |
| One `.kicad_pcb` | Actual filename/hash, board identity/revision, KiCad producer version/build and saved format version | TBD |
| F.Paste Gerber | Actual filename/hash, top-side Paste role, same-revision attestation and exact plot configuration | TBD |
| Component placement export | Filename/hash, selected sides, actual headers/dialect, units, origin, axes, rotation zero/direction and population/export options | TBD |
| BOM export | Filename/hash, exporter/plugin name/version, headers/dialect, grouping/quantity/population rules and same-revision attestation | TBD |
| Exporter configuration/manifest | Exact producer/build, settings snapshot or reproducible export procedure; per-source units/origin/side conventions; artifact hashes; selected inspection sides/profiles | TBD |
| B.Paste Gerber, conditional | Required only if bottom-side SPI is requested; record bottom role, hash, settings and same-revision evidence | TBD; bottom-side SPI request decision TBD |

Bundle acceptance checks presence, readable declared files, one identified revision, hashes and explicit exporter configuration for required artifacts. A top-only SPI request does not require B.Paste; a bottom SPI request without B.Paste blocks bundle acceptance. Bottom placement/AOI alone does not imply bottom SPI. Missing required exporter configuration also blocks Sprint 2 entry; TBD cells describe the current unfulfilled state, not permission to guess settings during import.

An independent review must identify expected outline dimensions, selected pad/footprint positions, known reference/component examples, side/origin relationships and any fiducial candidates. Record the reviewer/reference method for later oracles. Sprint 2 reads the KiCad file; Sprints 3 and 4 use the already collected Gerber/placement/BOM artifacts. Entry acceptance does not claim they have been parsed or tested. If the bundle changes, preserve the prior hashes/revision and revalidate consistency; do not mix exports from different revisions.

The seed board need not contain every normative edge case. Supplementary fixtures remain necessary for full side, construct, invalid-input and calibration coverage at Foundation Complete. In particular, conditional omission of B.Paste from a top-only seed bundle does not waive bottom-side import/geometry scenarios.

## Gerber constructs and reuse evaluation

Target RS-274X Paste; validate X2 metadata when present. Before from-scratch parsing, evaluate **PyGerber or Gerbonara**. Neither candidate is selected or verified here. Record pinned version, license, semantic precision, provenance/source locations, resource limits, fixture results and error behavior. If reuse is unsuitable, document observed gaps and a reviewed custom-parser scope first.

| Construct/interaction to evaluate | Planned fixture | Exact tested exporter/library versions | Verified result |
| --- | --- | --- | --- |
| Format specification, zero suppression, declared mm/inch units, coordinate modes | GERBER-01 | TBD | TBD |
| Standard circle/rectangle/obround/polygon apertures and flashes | GERBER-02 | TBD | TBD |
| Linear draws, CW/CCW arcs and quadrant modes | GERBER-03 | TBD | TBD |
| Regions, dark/clear polarity, holes and overlaps | GERBER-04 | TBD | TBD |
| Parameterized aperture macros and primitive exposure | GERBER-05 | TBD | TBD |
| File/aperture reflection, rotation, scale, offsets and step-repeat where encountered | GERBER-06 | TBD | TBD; evaluation does not expand panel-import scope |
| X2 attributes and manifest layer/side conflicts | GERBER-07 | TBD | TBD |
| Reduced/split paste windows, unmatched openings and pad links | GERBER-08 | TBD | TBD |
| Unsupported/malformed constructs and resource limits | GERBER-NEG | TBD | TBD; explicit rejection required |

Unsupported semantics must fail FORMAT_UNSUPPORTED with construct/source location; malformed supported syntax must fail PARSE_FAILED. Do not silently skip or substitute approximate geometry because a library accepts input.

## Placement and BOM formats

Fields below are proposed normalized logical fields, not actual exporter header claims. Exact headers and encoding/delimiter/quoting/decimal/null conventions must be recorded per tested profile. Units and origins cannot be guessed.

| Target format | Required normalized mapping | Exact tested dialect/exporter version | Planned fixtures | Status |
| --- | --- | --- | --- | --- |
| Placement CSV | reference, x, y, rotation, side; units/origin/axes/angles in metadata or manifest | TBD: headers, encoding, delimiter, quoting, decimal convention, exporter version | PLACE-01 | TBD |
| Placement TSV | Same; footprint/value optional with explicit authority | TBD: headers, encoding, tab/quoting/decimal rules, exporter version | PLACE-02 | TBD |
| BOM CSV | reference/group, quantity, population state or explicit manifest policy; optional value/part number | TBD: headers, encoding, delimiter, group syntax, exporter version | BOM-01 | TBD |
| BOM TSV | Same; DNP/unknown/populated tokens explicitly mapped | TBD: headers, encoding, delimiter, population tokens, exporter version | BOM-02 | TBD |
| Negative tabular cases | duplicate/unresolved references, invalid numbers, quantity conflicts, ambiguous decimals | TBD | TABULAR-NEG | TBD; rejection evidence required |

## Representative fixture inventory

All fixture IDs are planned, not files created by this proposal. Paths, hashes, exact producers/versions and executed results remain TBD. Expected outputs must be independently derived.

| Planned ID | Content and oracle | Artifact/hash/result |
| --- | --- | --- |
| REAL-PCB-01 | Actual KiCad 10.0.7-target board bundle with F.Paste, placement, BOM, exporter configuration and conditional B.Paste; Sprint 2 entry gate | TBD |
| GEO-STAGES | (1,2) inch -> (25.4,50.8) -> (25.4,-50.8) -> (50.8,25.4) -> (60.8,45.4) mm, plus inverse checkpoints | TBD |
| KICAD-01 | Outline arcs/cutout with known geometry | TBD |
| KICAD-02 | Rotated top/bottom footprints, repeated pad numbers and known local-to-P coordinates | TBD |
| KICAD-03 | Approved fiducials versus circular pads; invalid topology/version companions | TBD |
| GERBER-01..08 | Focused construct and interaction fixtures with independent filled-geometry/unit/topology oracles | TBD |
| GERBER-NEG | Unsupported/malformed/resource-bound cases with expected typed errors | TBD |
| PLACE-01/02 | Distinct origins, inch/mm and side/angle conventions with canonical expected placement | TBD |
| BOM-01/02 | Grouped references, per-reference DNP, population tokens and quantities | TBD |
| TABULAR-NEG | Expected row-level field/join errors | TBD |
| IMPORT-REV | Consistent and mixed revisions with expected digest/conflict behavior | TBD |
| FIT-SEPARATE | Capacity pass, fixture fail and unresolved camera travel without targeting claim | TBD |
| CAL-VALIDATION | Two-point rigid evidence, four-point fit without independent evidence, held-out checks and policy-purpose mismatch | TBD |
| MACHINE-06 | Six machine identities with colliding capture names and different calibrations | TBD |

## Open decisions and release gate

KiCad 10.0.7 is selected as the initial target. Remaining decisions: actual PCB/revision and requested sides, exact build/exporter evidence and settings, parser candidate/version, mandatory Gerber subset, tabular dialects and resource limits. Acquire the real bundle before Sprint 2; supplement fixtures and execute independent-oracle checks before changing TBD to verified. Release statements must name the evidence-backed subset and acceptance level. No executed tests, verified parser or production accuracy are asserted here.
