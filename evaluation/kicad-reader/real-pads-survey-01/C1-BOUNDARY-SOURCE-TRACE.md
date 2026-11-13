# C1 F.Cu rectangle boundary source trace

Read-only investigation, 2026-10-26. Scope: the two C1 SMD rectangles in
REAL-PCB-01-r2, identified in [C1-ORACLE.md](C1-ORACLE.md). No native execution,
test, candidate calculation or change to prior evidence. References use tag 10.0.7;
line numbers below are one-based GitHub source lines, not historical snapshots.

## Call path and parameter effects

1. [PAD::TransformShapeToPolygon, pad.cpp lines 2452-2496](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/pcbnew/pad.cpp#L2452)
   reads shape, size and ShapePos for the requested layer. RECTANGLE sets both
   trapezoid deltas to zero and passes orientation, clearance, error and error
   location to TransformTrapezoidToPolygon. Select F_Cu explicitly, clearance=0,
   aMaxError=1 IU, ERROR_INSIDE; use an initially empty output polyset.
2. [TransformTrapezoidToPolygon, lines 352-416](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/libs/kimath/src/convert_basic_shapes_to_polygon.cpp#L352)
   halves the integer size, constructs four corners, calls CornerListToPolygon,
   then rotates and translates the outline. With zero clearance it does not enter
   the negative-inflate branch. Nonzero C1 half-dimensions and zero deltas do not
   trigger duplicate-corner removal.
3. [ROUNDED_CORNER and CornerListToPolygon, lines 217-240](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/libs/kimath/src/convert_basic_shapes_to_polygon.cpp#L217)
   give these corners radius zero. Zero inflate plus zero radius takes the direct
   Append branch for every corner. The error-controlled arc branch is bypassed.

Conclusion from source: clearance=0, aMaxError=1 and ERROR_INSIDE do not shift,
shrink, inflate or round these rectangle corners. This is not a blanket claim
for roundrect, custom pads, positive clearance or other geometry.

## IU, exactness and coordinate space

[base_units.h lines 62-63 and 101-102](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/include/base_units.h#L62)
define PCB_IU_PER_MM=1e6 and pcbIUScale: 1 IU = 1 nm = 0.000001 mm.
Thus aMaxError=1 is 1 nm, not 1 mm. It is separate from the existing oracle's
1 nm comparison tolerance; it is not consumed by this direct-corner branch.

C1 dimensions 3.50012 x 2.4003 mm become 3500120 x 2400300 IU; both are even,
so integer halving gives 1750060 x 1200150 IU without truncation. The 90-degree
rotation maps (u,v) to (v,-u) using the exact cardinal branch in
[trigo.cpp lines 211-224](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/libs/kimath/src/trigo.cpp#L211).
The source-derived prediction is therefore sharp rectangle corners matching the
accepted analytic oracle, not a tessellated expansion like the D-outline case.

Rotation and movement happen inside the native polygon conversion. Treat returned
points as board-world IU, not footprint-local coordinates; do not apply parent
placement again. Normalize only with N(x,y)=(x,-y) after IU-to-mm conversion.
ShapePos is layer-aware and may include a shape offset: future native evidence
must check F_Cu shape/offset and actual vertices rather than assume center=bbox.

## Contour closure

CornerListToPolygon calls NewOutline once and appends the four corners once.
[SHAPE_POLY_SET::NewOutline, lines 228-236](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/libs/kimath/src/geometry/shape_poly_set.cpp#L228)
creates a SHAPE_LINE_CHAIN with SetClosed(true). Closure is represented by that
flag and the final-to-first edge, not by an explicit fifth duplicate vertex here.
Expected source behavior for each C1 call into an empty buffer: one closed outer
contour, four stored vertices, no hole. Preserve native order and record any
cyclic start/direction correspondence to the oracle; reflection reverses winding.

## Remaining limits

This closes the source-level uncertainty about error-policy displacement in the
selected rectangle branch. It does not prove the installed binary matches the tag,
SWIG execution succeeds, or native vertices match the oracle: no native call was
made. The online source was inspected, not archived or binary-attested. Previous
saved source snapshots are unchanged and may have different line numbering.

Only F_Cu pad geometry is covered. This does not establish per-layer override
coverage, other copper layers, Paste/Mask boundaries, or final copper unions with
tracks, zones and thermals. No publication, targeting or complete import claim.
Tasks 1.5/5.2 remain PARTIAL. The accepted oracle and tolerance remain unchanged.
