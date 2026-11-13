# C1 independent rectangular-pad oracle ? REAL-PCB-01-r2

Scope: documentary oracle only. No Transform2, reader API, native run, candidate generation or tests used. Expected values below were calculated from source decimals before loading observation for comparison.

Source: `C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r2/source/Edgeberry.kicad_pcb`
Source SHA-256: `67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0`
Observation: `evaluation/kicad-reader/runs/errata-r2-01/pcbnew.stdout.txt`
Observation SHA-256: `10f57cac75d8d998e450cf91d2aaf748e289fd512f1c1568b5ca9298a9494b9c`

## Source declarations
- Lines 88?93: top F.Cu footprint C1, UUID `00000000-0000-0000-0000-00005bd482c8`; `(at 192.849 65.2672 90)` at line 91.
- Pad 1, lines 338?346: UUID `e2743daf-d278-4538-a77e-8f62f1b7978c`; `(at 3.2512 0 90)`; `(size 3.50012 2.4003)`; smd rect; F.Cu/F.Mask/F.Paste.
- Pad 2, lines 347?354: UUID `4e53dd71-4be4-4973-9c48-191e7b2e27bb`; `(at -3.2512 0 90)`; same size/type/layers.
- Units mm. Local positions are footprint-relative. The angle token is NOT a relative angle to be added to the footprint angle.

## Convention evidence (KiCad source tag 10.0.7, inspected online)
- [Parser, lines 5583?5592](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp#L5583): pad XY uses SetFPRelativePosition; angle uses SetOrientation directly.
- [BOARD_ITEM, lines 391?401](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/pcbnew/board_item.cpp#L391): relative position is rotated by parent orientation and translated once.
- [RotatePoint, lines 210?238](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/libs/kimath/src/trigo.cpp#L210): +90 degrees maps (u,v) to (v,-u).

## Independent calculation and corner correspondence
Native world is X-right/Y-down. Let K(theta)=[[cos(theta),sin(theta)],[-sin(theta),cos(theta)]].
Center C=F+K(90)*(u,0). Pad world corners W_i=C+K(alpha)*q_i, alpha=90 from pad declaration, NOT 90+90. Equivalently F+K(90)*[(u,0)+K(alpha-90)*q_i]. Footprint placement is applied once.
Half sizes a=1.75006, b=1.20015. Indexed pad-shape offsets: q0=(-a,-b), q1=(a,-b), q2=(a,b), q3=(-a,b).
Normalize each world point N(x,y)=(x,-y). No translation to canonical P is declared here; no auxiliary/grid origin subtraction and no reuse of the synthetic (0,20) translation.
Normalized angle is +90 degrees in standard Cartesian CCW notation: N*K(alpha)=R(alpha)*N. Reflection reverses indexed winding; retain correspondence, do not silently reorder corners.
All arithmetic below is exact decimal at these cardinal angles. Comparison tolerance for source/API positions and size: 1 nm = 0.000001 mm; raw angle expectation exactly 90 degrees for this case.

| Pad | Center native world mm | Center normalized mm |
|---|---|---|
| 1 | (192.849, 62.0160) | (192.849, -62.0160) |
| 2 | (192.849, 68.5184) | (192.849, -68.5184) |

| Pad | Corner | World X | World Y | Normalized X | Normalized Y |
|---|---|---|---|---|---|
| 1 | 0 | 191.64885 | 63.76606 | 191.64885 | -63.76606 |
| 1 | 1 | 191.64885 | 60.26594 | 191.64885 | -60.26594 |
| 1 | 2 | 194.04915 | 60.26594 | 194.04915 | -60.26594 |
| 1 | 3 | 194.04915 | 63.76606 | 194.04915 | -63.76606 |
| 2 | 0 | 191.64885 | 70.26846 | 191.64885 | -70.26846 |
| 2 | 1 | 191.64885 | 66.76834 | 191.64885 | -66.76834 |
| 2 | 2 | 194.04915 | 66.76834 | 194.04915 | -66.76834 |
| 2 | 3 | 194.04915 | 70.26846 | 194.04915 | -70.26846 |

## Saved observation comparison (not a new execution)

Observed build `10.0.7`; source hash binding matches. Historical payload has no strict-v2 protocol field.

Observed footprint pose: [192.849, 65.2672], raw angle 90.0, layer F.Cu. Source expectation: [192.849,65.2672], 90, F.Cu.

| Pad | API local mm | API world mm | API raw angle | API size mm | Result for these fields |
|---|---|---|---|---|---|
| 1 | [3.2512, 0.0] | [192.849, 62.016] | 90.0 | [3.50012, 2.4003] | MATCH |
| 2 | [-3.2512, 0.0] | [192.849, 68.5184] | 90.0 | [3.50012, 2.4003] | MATCH |

## Evidence limits
Saved observation contains centers, size and angle, not four boundary vertices: the eight expected corners are NOT independently compared to native boundary output. No full copper boundary, per-layer override, canonical P mapping, backend authentication or general geometry support is established. Source tag behavior is evidence of semantics, not proof the installed executable was built from those exact bytes. No bottom convention is inferred. Tasks 1.5/5.2 remain PARTIAL.
