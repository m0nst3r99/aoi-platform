# Supported inputs and verification register

Status: REAL-PCB-01-r1 acquisition gate 7.1 accepted on 2026-10-18. File/export/hash checks are evidenced; importer/parser compatibility is not verified. All unverified entries are **TBD**. Target formats and planned fixture names are not working-support claims. Do not infer versions from memory, presumed compatibility or advertised library features.

AOI Platform V0.1 initial target: **KiCad 10.0.7**. This target is selected; verified compatibility is not. Producer/export execution and hashes for REAL-PCB-01-r1 are recorded below. Parser/library versions, compatibility results and other unverified settings remain TBD. A candidate profile may be exercised in isolated development tests to establish evidence; this does not add it to the released support allowlist. Foundation Prototype and Foundation Complete gates are defined in design.md section 9 and scheduled in sprint-plan.md.

## Evidence required for verified support

Record exact producer name/version/build (KiCad and exporter/plugin separately), board format version, export settings, units, origin, axes, angle/side conventions, artifact SHA-256, fixture ID/path, parser/library name and exact version, adapter/schema version, independent expected geometry/error, test command/result/date and relevant dependency/platform versions. Each positive fixture verifies only its declared combination. Negative fixtures establish rejection, not positive support. Update the supported-input allowlist and this evidence register together.

## KiCad and exporters

| Target | Initial KiCad target | Exact tested version/build | Exact exporter/plugin version and settings | Parser version | Planned fixtures | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `.kicad_pcb` s-expression board | 10.0.7 | TBD | Source format 20260206, pcbnew 10.0; original writer patch not asserted; export CLI 10.0.7 below | TBD | REAL-PCB-01; KICAD-01..03 | TBD |
| F.Paste; B.Paste when bottom SPI requested | 10.0.7 | TBD | Acquisition: Pcbnew 10.0.7, mm 4.6 absolute, no X2/netlist; r1 manifest below | TBD | REAL-PCB-01; GERBER-01..08 | TBD |
| Component placement | 10.0.7 | TBD | Acquisition: CLI 10.0.7, both sides, mm, absolute, no bottom X negation; r1 manifest | TBD | REAL-PCB-01; PLACE-01/02 | TBD |
| BOM | 10.0.7 board workflow | TBD | Acquisition: CLI 10.0.7 native BOM, Value+DNP grouping; r1 manifest | TBD | REAL-PCB-01; BOM-01/02 | TBD |

No KiCad major/minor/patch version is currently verified for importer compatibility. Legacy `.brd`, ODB++, IPC-2581 and Gerber X3 placement remain deferred.

## REAL-PCB-01 — Sprint 2 prerequisite

**ACCEPTED: acquisition gate 7.1, REAL-PCB-01-r1, 2026-10-18.** Supersedes the former acquisition-TBD status, not the unverified parser support tables. The user confirmed external review of the forwarded preparation report and authorized acceptance.

Review method: the local agent inspected files, export commands/results and hashes, and reverified all 25 inventory hashes at closure. External review relied on the report forwarded by the user; reviewers did **not** directly verify bundle bytes. No third-party signature or attestation is generated. The fixed manifest's earlier review-pending text is historical preparation status, superseded for gate 7.1 by this repository record. The fixture is not edited.

Fixed [bundle](../../../../aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1): [source snapshot](../../../../aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/source), [new exports](../../../../aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/exports), [manifest and authority/export ledger](../../../../aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/manifest.json), [population ledger](../../../../aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/population.json), [SHA-256 inventory](../../../../aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/SHA256SUMS.txt). Inventory SHA-256: `2682d7558b9dbae62d6e78d7255d32e0007cdb001b0f888e9fed1ac9b719f259`. Use revision source/exports, not mutable working files or historical before/exports. CLI-created source/Edgeberry.kicad_prl is hashed session state, not design authority.

Source: Edgeberry Baseboard, preserved CERN OHL-W license in source/LICENSE.txt. User-declared upstream commit: `f88d9adabefffb9dd2a6909d15d14b1965cca943`; byte equivalence to upstream is not asserted. Fixture revision is distinct from schematic title revision 1.5 and Gerber rev? labels, which were not rewritten.

| Required item | Acquisition evidence / result |
| --- | --- |
| PCB and schematic | Present/readable; PCB format 20260206, pcbnew 10.0; schematic 20260306, eeschema 10.0. Original writer patch is not fabricated from those tokens. PASS |
| F.Paste | New top Paste, 56 flashes; non-G04 commands equal prior export. PASS |
| Placement | New both-side CSV, 32 rows; all positions/angles/sides compared to PCB and all rows equal prior CSV. PASS |
| BOM | New CSV, 28 unique assembly refs, 18 groups, quantities checked. PASS |
| Configuration/provenance | CLI 10.0.7 version/help, executable hash, exact argv/cwd/times/exit codes/output/warnings in manifest; outputs from one fixed snapshot, source hashes checked after export. PASS |
| Conditional B.Paste | SPI top only; historical B.Paste retained reference-only in before/exports/gerber, not newly exported r1 inspection data. Not required |

Key hashes (paths relative to fixed bundle):

| Artifact | SHA-256 |
| --- | --- |
| `source/Edgeberry.kicad_pcb` | `67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0` |
| `source/Edgeberry.kicad_sch` | `662de42821e25cef31f67f5373aa7e3bdf2c377d1f1339ccc25b73d48688815c` |
| `exports/gerber/Edgeberry-F_Paste.gbr` | `fb96fd6e9764b00637a45f8fcad5974fb4d1a525cfe0ec906f0c9dcefce0af5c` |
| `exports/placement/Edgeberry-all-pos.csv` | `80c2df9ccc73a98febc6f6abe359235eb60b088c3c855972e8d9ce1612642738` |
| `exports/bom/Edgeberry-bom.csv` | `dfd5e23c2613225074604adf22805a7fd8e6fbdb2931ea1d91ab6f244c52446f` |

Authority: PCB value 270R for R7/R8 was selected for fixture data, not electrical-design validation. Original schematic/BOM values were 22R; PCB/placement were 270R. Only two working schematic Value fields changed; nets, pads, footprints, positions and flags stayed unchanged; no bulk schematic-to-PCB update. Before/after hashes and originals are preserved. BOM groups fell from 19 to 18 because R1 Qty1 and R7,R8 Qty2 merged into R1,R7,R8 Qty3; 28 references remain.

| Full UUID | Classification | Inspection treatment |
| --- | --- | --- |
| 00000000-0000-0000-0000-00005b7adb04 | non-assembly-electrical-via | Retain source data; no assembly target |
| 00000000-0000-0000-0000-00005c9e4f14 | unresolved-empty-placeholder | Retain source data; no assembly target |
| 00000000-0000-0000-0000-00005ccbd5ac | unresolved-empty-placeholder | Retain source data; no assembly target |
| 00000000-0000-0000-0000-00005ccbd5d8 | unresolved-empty-placeholder | Retain source data; no assembly target |

All 57 footprints and flags remain. The 25 position exclusions are 7 DNP mechanical holes, 3 fiducial candidates and 15 G*** objects, individually identified in population.json. Four listed REF** remain in placement; absence from schematic BOM is not a PCB exclusion flag. Three fiducial candidates (UUID suffixes 00005ccf2ec8, 00005ccf2ed3, 00005ccf2ede; full IDs/coordinates in ledger) remain separate, not discarded or promoted to calibrated references. Assembly exclusions never filter Paste geometry.

Source conventions: PCB coordinates in mm at the absolute sheet origin, +X right/+Y down. Auxiliary origin (81.649,141.772) not selected. For all 32 placement rows x_csv=x_pcb, y_csv=-y_pcb, rotation equals saved PCB at-angle modulo 360, F.Cu=top/B.Cu=bottom; no bottom X negation. Rotation is the saved KiCad footprint-local orientation, not an inferred body axis; canonical angle/parity conversion still needs independent import tests. Gerbers declare mm/absolute/4.6/leading-zero omission, positive top Paste; X2/netlist disabled, macros enabled, no zone refill requested. TF comments are not misrepresented as enabled X2. CSV uses decimal point, comma delimiter and double-quoted strings. BOM headers Reference,Value,Footprint,Qty,DNP; comma-separated refs without ranges, Value+DNP grouping, default variant, no exclude-dnp. Placement headers Ref,Val,Package,PosX,PosY,Rot,Side. CSV producer evidence comes from manifest, not edited headers.

Reference method: direct saved-source inspection and cross-file comparisons, independent of any future importer. Outline centerline x=83.649..218.649, y=51.772..141.772 mm gives 135 x 90 mm; job size 135.15 x 90.15 is not used as centerline dimensions. R7 PCB=(98.249,70.272,180deg), placement=(98.249,-70.272,180deg); R8 PCB=(98.249,75.372,180deg), placement=(98.249,-75.372,180deg); both top. Schematic pin/wire and PCB pad mapping agree: R7.1-Q3.E, R7.2-D1.A1, R8.1-Q2.E, R8.2-D1.A2. These references are not full electrical or parser validation.

Warnings: Lato Black/Heavy substituted with DejaVu Sans Bold; F.Paste/Edge.Cuts non-comment commands equal prior artifacts. First BOM invocation failed std::bad_any_cast; adjusted invocation succeeded and expanded contents were checked. Both argv/results are retained; no isolated root cause is claimed. No external reviewer signature is fabricated.

Bundle acceptance checks presence, readable declared files, one identified revision, hashes and explicit exporter configuration for required artifacts. A top-only SPI request does not require B.Paste; a bottom SPI request without B.Paste blocks bundle acceptance. Bottom placement/AOI alone does not imply bottom SPI. Missing required exporter configuration also blocks Sprint 2 entry; untested profile/compatibility TBD cells are not permission to guess settings during import.

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
| REAL-PCB-01 | Actual KiCad 10.0.7-target board bundle with F.Paste, placement, BOM, exporter configuration and conditional B.Paste; Sprint 2 entry gate | Acquisition accepted for REAL-PCB-01-r1 above; importer results TBD |
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

KiCad 10.0.7 is selected as the initial target. REAL-PCB-01-r1 acquisition, top SPI and exporter settings are accepted. Remaining decisions: parser candidate/version, verified construct/dialect subset and resource limits. Sprint 1 agreed-subset exit review is accepted in chat; inventory byte-admission passed ZIP code review per user-relayed results, with no reviewer rerun of the local bundle; supplement fixtures and execute independent-oracle checks before changing TBD to verified. Release statements must name the evidence-backed subset and acceptance level. No executed tests, verified parser or production accuracy are asserted here.
