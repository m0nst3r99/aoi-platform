# Evaluation observation protocol v2: footprint-local Edge.Cuts

The native probe adds mandatory `protocol_version: 2`, `footprint_edges` and
`geometry_coverage`. This is evaluation-only, not a product adapter.

`edges` remains BOARD.GetDrawings-only. Consumers MUST NOT treat that collection
alone as complete board geometry. `footprint_edges` separately enumerates
FOOTPRINT.GraphicalItems whose GetLayer equals pcbnew.Edge_Cuts. Each record has
item UUID, verified parent footprint UUID, native shape enum, primitive type,
layer name and source accessor. Segment enum 0 was checked in bundled 10.0.7.
Other PCB_SHAPE enums are labelled native-shape-N; endpoints do not fully describe
arcs, circles, polygons or other shapes. A non-PCB_SHAPE Edge.Cuts graphical item
raises an explicit error instead of silently disappearing.

`api_start_mm`/`api_end_mm` are PCB_SHAPE.GetStart/GetEnd divided by native IU/mm.
Their coordinate_space is deliberately native-api-unclassified. They are NOT
labelled file-local, nor converted to canonical geometry. File-local endpoints
in the synthetic oracle are independently authored source declarations and are
not copied from these API outputs. No bottom reflection or transform is added.

Coverage is explicitly geometry_complete=false, board_edges_scope=
board-drawings-only, footprint_edges_scope=footprint-graphical-items-only.
Native-loader omissions/normalization are not detected generally. This control
only establishes identity/type/layer detection of two stored segments on rotated
top/bottom footprints. It does not validate general topology, custom primitives,
full shape parameters, canonical coordinates, import or targeting readiness.
A valid board-level rectangle can coexist with native outline.valid=false after
adding open footprint segments. Detection is not inferred from outline or bbox.

## Compatibility

New schema validation requires v2 fields even when footprint_edges is empty.
Missing/incorrect metadata, unknown protocol, duplicate identity and unknown
parent fail. Unversioned historical replay requires explicit allow_legacy=True
(or run.py --allow-legacy-protocol); footprint-edge coverage then stays UNKNOWN,
not known-empty. Versioned malformed payloads cannot downgrade through that flag.
The existing 23 harness regressions replay immutable historical output with this
explicit opt-in. Old exact-JSON baseline comparisons are not v2 compatibility
checks; do not strip new fields to manufacture equality. Historical logs remain
unchanged. Tests require the baseline repository, not just the small review ZIP.

## Reproduction (Windows, installed bundled KiCad 10.0.7)

Run from repository root, using a NEW evidence directory for each native run:

    .venv/Scripts/python.exe -B -m pytest evaluation/kicad-reader/test_harness.py evaluation/kicad-reader/test_footprint_edges.py -q -p no:cacheprovider
    .venv/Scripts/python.exe -B evaluation/windows_runner/footprint_edges_control.py evaluation/windows_runner/evidence/NEW-DIRECTORY

The control writes fixture/oracle and their hashes before launching; no Git commit
is made. Existing helper, wx stderr logging, runner budgets and 45-second outer
watchdog are reused unchanged. No real PCB is accessed. Host-death between
CreateProcess suspended and Job assignment remains a containment gap.
