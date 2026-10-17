# board-geometry-foundation

Status: Geometry Core subset implemented under explicit user authorization on 2026-10-17; remaining change open. See implementation-status.md. Neither Foundation Prototype nor Foundation Complete is achieved.

## Why

The independent AOI platform needs trustworthy board geometry before inspection algorithms or motion integration can be designed. KiCad, Gerber Paste, placement exports, camera images, and machine coordinates may use different origins, units, axis directions, and bottom-side conventions. Silent assumptions here would place inspection regions or future motion targets at incorrect locations.

## What changes

- **GEO-001 — Board geometry:** define canonical millimeter PCB coordinates, individually identified source frames, camera pixel and machine XY frames, explicit transformation chains, side and rotation rules, fiducial registration, calibration records, typed contracts, errors, and synthetic acceptance tests.
- **PCB-001 — PCB data import:** define validated, revision-bound import of KiCad PCB, Gerber Paste, component placement, BOM, footprints, pads, and fiducials into immutable canonical board data, with source provenance and explicit conflict handling.

New capabilities: `board-geometry` and `pcb-data-import`. No existing capabilities are modified in this standalone workspace. Normative requirements are in `specs/<capability>/spec.md`; design decisions and shared model contracts are in `design.md`. `tasks.md` preserves implementation traceability; only completed Geometry Core tasks 4.1–4.4 are checked.

AOI Platform V0.1 initially targets **KiCad 10.0.7**. This is a development target, not verified compatibility. Exact tested builds, exporter settings, parser/library versions and test results remain TBD until real fixtures and tests establish evidence in `supported-inputs.md`.

## Implementation acceptance and sprint plan

`sprint-plan.md` defines five planned sprints: (1) typed geometry models and transformations, (2) real KiCad PCB import, (3) PyGerber/Gerbonara evaluation and Paste import, (4) placement/BOM reconciliation, and (5) camera geometry/calibration. It maps the original task IDs without renumbering them and carries an explicit open-requirement register.

**Foundation Prototype** is a proposed end-of-Sprint-4 milestone: tested typed geometry plus a bounded, provenance-preserving import/reconciliation path for the real V0.1 fixture, with explicit unsupported-input rejection and incomplete normative requirements still OPEN. It is not full GEO-001/PCB-001 conformance. **Foundation Complete** requires every normative requirement/scenario to have implementation and passing evidence, including camera/fiducial validation, lifecycle, machine isolation and failure handling. Sprint 5 is necessary but its completion alone does not establish this level. Neither level is currently achieved or represents hardware qualification. Detailed gates are in design.md section 9.

Sprint 2 requires the `REAL-PCB-01` bundle defined in `supported-inputs.md`: one actual board revision with `.kicad_pcb`, F.Paste Gerber, placement, BOM and exporter configuration. B.Paste is additionally required only for requested bottom-side SPI. Board identity, files and evidence are currently TBD; planning this prerequisite does not fulfill it.

## Platform boundaries

The machine is mechanically independent of AFARCO PnP V3.2. BoardCapacity is 280 x 550 mm, a PCB size requirement. FixtureEnvelope describes mounting space and exclusions in machine coordinates; CameraTravelEnvelope describes permitted camera-reference positions. Physical fixture and travel dimensions remain TBD until optics and mechanics are selected. Board size does not establish gantry travel or optical coverage. Phase 1 targets 2D solder paste inspection (SPI) and 2D post-placement AOI. These foundations supply geometry and data, not defect detection. A 2D SPI result cannot claim paste height or volume. Future 3D inspection and post-reflow AOI require separate proposals.

A custom ESP32-S3 board will eventually control motion, lighting, sensors, and triggering. Python/OpenCV on a PC or server will perform image processing. Neither controller firmware nor hardware is a dependency of these specifications or their tests. Records carry machine, camera, capture, and calibration identities so six machines can later share one processing server without sharing calibration accidentally. Server scheduling, transport, deployment, throughput, and controller protocols are outside this change. No ROS2, Kubernetes, or microservices are introduced.

## Scope and impact

The original review package is now accompanied by the first hardware-independent Python Geometry Core and synthetic unit tests. The import pipeline and remaining specification work are still open. No camera resolution or model is fixed. Existing inspection software may consume an adapter contract; Aman9y/open-aoi is a possible component, never a dependency of the canonical data model.

Excluded: hardware design, gantry travel design, motor commands, ESP32 firmware, image acquisition drivers, detection algorithms, production inspection tolerances, 3D reconstruction, reflow defect taxonomy, UI implementation, and distributed infrastructure.

## Review decisions

The canonical frame conventions and transform equations are preserved, with independent intermediate test oracles added. Calibration thresholds are configurable, versioned synthetic test policies, not verified production accuracy. Two metric fiducials can constrain a rigid pose; a planar homography requires four or more suitable points and independent validation evidence. Unvalidated mappings are rejected and cause REVIEW at the inspection boundary.

Before any Gerber parser is implemented from scratch, evaluate reuse of PyGerber or Gerbonara and record the decision and fixture evidence. Unsupported constructs must fail explicitly. `supported-inputs.md` records exact tested versions, constructs, formats and representative fixtures; all unverified support is TBD. Remaining tasks are split into independently testable deliverables and remain unchecked; implementation-status.md records the completed core subset.

Open decisions: the real PCB identity/export bundle, KiCad 10.0.7 build evidence and exporter settings, parser/library versions and verified input subset, synthetic policy approval, and Gerber reuse selection. Fixture geometry/margins, camera travel/coverage and production qualification remain future optics/mechanics decisions. Review approval does not certify hardware performance or authorize implementation automatically.
