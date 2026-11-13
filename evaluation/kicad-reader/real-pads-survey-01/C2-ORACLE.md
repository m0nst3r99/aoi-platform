# C2 independent rectangular-pad oracle - REAL-PCB-01-r2

Documentary oracle only. Expected centers, corners and correspondence below were
computed with Python decimal.Decimal from source literals and written before
reading saved observation for comparison. No Transform2, candidate API, KiCad API
or observation values were used to generate expected geometry.

## Source identity and declarations

Source: `C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r2/source/Edgeberry.kicad_pcb`

SHA-256: `67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0` (912379 bytes).

- Lines 379-382: `Capacitors_SMD:c_elec_8x10`, top F.Cu;
  parent UUID `00000000-0000-0000-0000-00005bd482e1` (line 381);
  footprint `(at 155.956 68.072 -90)` (line 382).
- Pad 1, lines 629-636: UUID `21e4d927-86ab-439d-8b84-9241bc089b89`
  (line 635); `(at 3.2512 0 270)` (630); `(size 3.50012 2.4003)` (631).
- Pad 2, lines 637-644: UUID `fc38c22a-efcb-4dfc-b42c-80a66f75e1a4`
  (643); `(at -3.2512 0 270)` (638); same size (639).
- Both declarations are `smd rect`, layers F.Cu/F.Mask/F.Paste (632, 640).
  Neither pad block declares drill, shape offset or per-layer padstack override.
  Declaration absence is not independent native boundary verification.

## Convention and independent calculation

Reuse the documented tag-10.0.7 source trace in [C1-ORACLE.md](C1-ORACLE.md):
[parser](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp#L5583)
sets footprint-relative XY and pad orientation separately;
[relative placement](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/pcbnew/board_item.cpp#L391)
applies parent placement once;
[rotation](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/libs/kimath/src/trigo.cpp#L210)
uses the native X-right/Y-down convention. These existing source references were
not fetched again for this documentary calculation.

Native K(theta) = [[cos(theta), sin(theta)], [-sin(theta), cos(theta)]].
Footprint theta=-90 degrees; pad source angle alpha=270 degrees is world
orientation, NOT an extra relative rotation to add to theta. Preserve the raw
-90 and 270 values; their matrices are equivalent modulo 360 for this calculation.

- F=(155.956,68.072) mm; C=F+K(-90)*(u,0).
- K(-90)*(u,v)=(-v,u); therefore C=(155.956,68.072+u).
- Half dimensions a=1.75006, b=1.20015 mm.
- q0=(-a,-b), q1=(a,-b), q2=(a,b), q3=(-a,b).
- W_i=C+K(270)*q_i=C+(-q_i.y,q_i.x).
- Normalize N(x,y)=(x,-y). No origin inferred from bounding boxes; no additional
  translation or canonical P datum is established by this document.

All arithmetic is exact decimal at cardinal angles; no trigonometric floating
point or intermediate rounding. Coordinate/size comparison tolerance is declared
as 1 nm (0.000001 mm); expected raw footprint angle -90 and pad angle 270 degrees.

## Correspondence fixed before observation comparison

For a future proper-rigid rectangle candidate using the normalized center and
standard Cartesian CCW angle +270 degrees, define candidate offsets q0..q3 as
above. N*K(alpha)=R(alpha)*N, so source indexed corners 0,1,2,3 correspond to
candidate indices **3,2,1,0**. Reflection reverses winding. This does not prescribe
native polygon vertex order; a later boundary check must establish cyclic/reversed
correspondence while preserving native raw order. Do not add footprint pose twice.

## Independent centers (mm)

| Pad | Native world center | Normalized center |
|---|---|---|
| 1 | (155.956, 71.3232) | (155.956, -71.3232) |
| 2 | (155.956, 64.8208) | (155.956, -64.8208) |

## Independent eight corners (mm)

| Pad | Source corner | World X | World Y | Normalized X | Normalized Y |
|---|---|---|---|---|---|
| 1 | 0 | 157.15615 | 69.57314 | 157.15615 | -69.57314 |
| 1 | 1 | 157.15615 | 73.07326 | 157.15615 | -73.07326 |
| 1 | 2 | 154.75585 | 73.07326 | 154.75585 | -73.07326 |
| 1 | 3 | 154.75585 | 69.57314 | 154.75585 | -69.57314 |
| 2 | 0 | 157.15615 | 63.07074 | 157.15615 | -63.07074 |
| 2 | 1 | 157.15615 | 66.57086 | 157.15615 | -66.57086 |
| 2 | 2 | 154.75585 | 66.57086 | 154.75585 | -66.57086 |
| 2 | 3 | 154.75585 | 63.07074 | 154.75585 | -63.07074 |

## Saved observation cross-check (after oracle was written)

Pre-comparison document SHA-256: `54f58818d64e47641f546cbeb499456f94a7f49e7dfd884ec7e0c6fe9c97ffa4` (prefix before this section).
Observation: `evaluation/windows_runner/evidence/c1-strict-native-01/stdout.bin`
SHA-256: `cd3734ece758d2611b44dc89cec2c88e439ba2d5585024d484671645ed7725b9`.
This is already recorded full-board strict-v2 output from the C1 control, not a
new C2 run or extension of the accepted C1 candidate scope.

Checked source hash/build, parent identity/pose/side, two distinct pad UUIDs,
numbers, local/world centers, raw angles, size, shape/attribute, drill and layers.
Footprint raw angle is -90; each pad raw angle is 270.

| Pad | API local mm | API world mm | API raw angle | Selected fields |
|---|---|---|---|---|
| 1 | (3.2512, 0) | (155.956, 71.3232) | 270 | MATCH |
| 2 | (-3.2512, 0) | (155.956, 64.8208) | 270 | MATCH |

Checks: `{'source_hash': True, 'build': True, 'parent_pose': True, 'pad_count': True, 'pad_1': True, 'pad_2': True}`.

No mismatch observed in these checked fields. Centers and sizes match exactly
at their represented decimal values. Eight corners above remain independent
source-derived expectations: saved observation has no C2 copper-boundary vertices.

## Limits

No C2 native boundary run, native contour ordering, per-layer effective shape or
offset, canonical P mapping or candidate flow has been verified. This does not
establish backend authenticity, general import, publication or targeting authority.
Source references reuse the existing trace; they were not fetched again. No tests
or native execution occurred. C1 flows/evidence remain unchanged; Tasks 1.5/5.2
and aggregate tasks remain PARTIAL.
