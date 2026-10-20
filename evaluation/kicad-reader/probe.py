"""Evaluation only: native KiCad API observations; never saves the board."""
import hashlib
import json
import sys

import pcbnew as p


def point(v):
    return [p.ToMM(v.x), p.ToMM(v.y)]


path = sys.argv[1]
try:
    with open(path, "rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
except FileNotFoundError:
    print(json.dumps(dict(outcome="rejected", code="SOURCE_NOT_FOUND")))
    raise SystemExit(2)
print("loading " + digest, file=sys.stderr, flush=True)
b = p.LoadBoard(path)
print("loaded", file=sys.stderr, flush=True)
if b is None:
    print(json.dumps(dict(outcome="rejected", code="NATIVE_LOAD_REJECTED")))
    raise SystemExit(2)
records = []
for f in b.GetFootprints():
    pads = []
    for pad in f.Pads():
        pads.append(dict(uuid=pad.m_Uuid.AsString(), number=pad.GetNumber(),
                         position_mm=point(pad.GetPosition()),
                         local_mm=point(pad.GetFPRelativePosition()),
                         angle_deg=pad.GetOrientationDegrees(),
                         shape=int(pad.GetShape()), attribute=int(pad.GetAttribute()),
                         size_mm=point(pad.GetSize()), drill_mm=point(pad.GetDrillSize()),
                         layers=[b.GetLayerName(n) for n in pad.GetLayerSet().Seq()],
                         net=pad.GetNetname()))
    records.append(dict(uuid=f.m_Uuid.AsString(), reference=f.GetReference(), value=f.GetValue(),
                        footprint=f.GetFPID().GetUniStringLibId(), position_mm=point(f.GetPosition()),
                        angle_deg=f.GetOrientationDegrees(), layer=b.GetLayerName(f.GetLayer()),
                        attributes=f.GetAttributes(), dnp=f.IsDNP(),
                        exclude_from_bom=f.IsExcludedFromBOM(),
                        exclude_from_position=f.IsExcludedFromPosFiles(),
                        pads=sorted(pads, key=lambda x: x["uuid"])))
edges = []
for d in b.GetDrawings():
    if d.GetLayer() != p.Edge_Cuts:
        continue
    row = dict(uuid=d.m_Uuid.AsString(), shape=int(d.GetShape()),
               start_mm=point(d.GetStart()), end_mm=point(d.GetEnd()))
    if d.GetShape() == p.SHAPE_T_ARC:
        row.update(mid_mm=point(d.GetArcMid()), center_mm=point(d.GetCenter()),
                   radius_mm=p.ToMM(d.GetRadius()))
    edges.append(row)
outline = p.SHAPE_POLY_SET()
ok = b.GetBoardPolygonOutlines(outline, False, None, True, False)
box = outline.BBox()
result = dict(build=p.GetBuildVersion(), input_sha256=digest,
              format_version=b.GetFileFormatVersionAtLoad(),
              footprints=sorted(records, key=lambda x: x["uuid"]),
              edges=sorted(edges, key=lambda x: x["uuid"]),
              outline=dict(valid=ok, count=outline.OutlineCount(),
                           holes=[outline.HoleCount(i) for i in range(outline.OutlineCount())],
                           origin_mm=point(box.GetOrigin()), size_mm=point(box.GetSize())))
print(json.dumps(result, indent=2, sort_keys=True))
