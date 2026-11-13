"""C1-only native boundary diagnostic; execute via existing staged helper.
No import-time native call. Separate protocol, not strict-v2 observations.
"""
import hashlib
import json
from pathlib import Path
import sys

SOURCE_HASH='67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0'
PARENT='00000000-0000-0000-0000-00005bd482c8'
PADS={'e2743daf-d278-4538-a77e-8f62f1b7978c','4e53dd71-4be4-4973-9c48-191e7b2e27bb'}


def main(path):
    source=Path(path)
    with source.open('rb') as f: raw=f.read(16*1024**2+1)
    if len(raw)>16*1024**2 or hashlib.sha256(raw).hexdigest()!=SOURCE_HASH:
        raise ValueError('C1 source hash/size mismatch; no load')
    import pcbnew as p
    if p.GetBuildVersion()!='10.0.7': raise ValueError('Unverified build')
    b=p.LoadBoard(str(source))
    parents=[f for f in b.GetFootprints() if f.m_Uuid.AsString()==PARENT]
    if len(parents)!=1: raise ValueError('C1 parent missing/duplicate')
    rows=[];seen=set()
    for pad in parents[0].Pads():
        uid=pad.m_Uuid.AsString()
        parent=pad.GetParentFootprint()
        if uid not in PADS or uid in seen or parent is None or parent.m_Uuid.AsString()!=PARENT:
            raise ValueError('C1 pad identity/association mismatch')
        seen.add(uid)
        if not pad.IsOnLayer(p.F_Cu) or pad.GetShape(p.F_Cu)!=p.PAD_SHAPE_RECT:
            raise ValueError('C1 F_Cu rectangle required')
        poly=p.SHAPE_POLY_SET()
        pad.TransformShapeToPolygon(poly,p.F_Cu,0,1,p.ERROR_INSIDE,False)
        contours=[]
        if poly.OutlineCount()>16: raise ValueError('Diagnostic contour limit')
        for i in range(poly.OutlineCount()):
            chain=poly.Outline(i)
            if chain.PointCount()>64: raise ValueError('Diagnostic vertex limit')
            contours.append(dict(closed=bool(chain.IsClosed()),hole_count=poly.HoleCount(i),
                vertices_iu=[[chain.CPoint(j).x,chain.CPoint(j).y] for j in range(chain.PointCount())]))
        rows.append(dict(uuid=uid,parent_uuid=parent.m_Uuid.AsString(),layer='F.Cu',
            accessor='PAD.TransformShapeToPolygon',contours=contours))
    if seen!=PADS: raise ValueError('C1 pads missing')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_HASH: raise ValueError('Input changed')
    print(json.dumps(dict(protocol='c1-boundary-diagnostic-v1',build=p.GetBuildVersion(),
        input_sha256=SOURCE_HASH,coordinate_space='board-world X-right/Y-down',iu_per_mm=1000000,
        clearance_iu=0,max_error_iu=1,error_location='ERROR_INSIDE',pads=rows),sort_keys=True,indent=2))


if __name__=='__main__': main(sys.argv[1])
