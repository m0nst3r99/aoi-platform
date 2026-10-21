"""Read-only roundrect parameter diagnostic; no geometry construction."""
import contextlib,io,json,runpy
from pathlib import Path
with contextlib.redirect_stdout(io.StringIO()) as captured:
    state=runpy.run_path(str(Path(__file__).resolve().parent.parent/'kicad-reader/probe.py'),run_name='__main__')
data=json.loads(captured.getvalue())
b,p=state['b'],state['p']
rows=[]
for f in b.GetFootprints():
    for pad in f.Pads():
        size=pad.GetSize(p.F_Cu)
        rows.append(dict(uuid=pad.m_Uuid.AsString(),parent_uuid=pad.GetParentFootprint().m_Uuid.AsString(),
            shape=int(pad.GetShape(p.F_Cu)),size_mm=[p.ToMM(size.x),p.ToMM(size.y)],
            ratio=pad.GetRoundRectRadiusRatio(p.F_Cu),radius_mm=p.ToMM(pad.GetRoundRectCornerRadius(p.F_Cu)),
            layers=sorted(b.GetLayerName(n) for n in pad.GetLayerSet().Seq()),accessor_layer='F.Cu'))
data['roundrect_diagnostic']=rows
print(json.dumps(data,indent=2,sort_keys=True))
