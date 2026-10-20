# Pre-run oracle rationale (KiCad tag 10.0.7)

- [Parser](https://gitlab.com/kicad/code/kicad/-/raw/10.0.7/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp):
  parseBoardUnits (lines 185-197) converts mm to integer nm.
  Footprint layer is assigned directly (4829-4837), pose before pads (4856-4872).
  Pad at-position uses SetFPRelativePosition and its angle uses SetOrientation
  (5583-5598), not SetFPRelativeOrientation.
- [BOARD_ITEM](https://gitlab.com/kicad/code/kicad/-/raw/10.0.7/pcbnew/board_item.cpp):
  Get/SetFPRelativePosition (378-402) apply inverse/forward footprint rotation
  with translation, without a side-dependent mirror.
- [RotatePoint](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.7/libs/kimath/src/trigo.cpp):
  lines 210-243 give (u,v)->(v,-u) at +90 degrees. Numerically positive
  rotation is clockwise in Cartesian Y-up notation, visually counterclockwise
  with PCB display X-right/Y-down. We retain source-native coordinates.
- [PAD](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.7/pcbnew/pad.cpp):
  SetOrientation vs SetFPRelativeOrientation (1379-1399) distinguish raw angle
  from angle plus parent orientation; Flip is a separate mutation (1403 onward).
  Reading an already-stored bottom footprint does not authorize applying Flip again.

This fixture is authored directly as an already-stored board footprint, not
created by flipping a library footprint. It tests this file-loading convention
only. Oracle numbers are generated with elementary integer rotation before launch.
Layer membership compares sets (order is not semantic), with duplicate rejection.
Pad parent association is checked through the probe's nested footprint/pad UUIDs.
No canonical bottom transform, targeting geometry, or general support claim.
