"""Diagnostic extension only; one LoadBoard through unchanged observation probe."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import sys

original = Path(__file__).resolve().parent.parent/'kicad-reader/probe.py'
# Preserve probe stderr/milestones, and extend its one successful JSON payload.
with contextlib.redirect_stdout(io.StringIO()) as captured:
    state = runpy.run_path(str(original), run_name='__main__')
data = json.loads(captured.getvalue())
b, outline, p = state['b'], state['outline'], state['p']
contours = []
for i in range(outline.OutlineCount()):
    chain = outline.Outline(i)
    points = [[chain.CPoint(j).x, chain.CPoint(j).y] for j in range(chain.PointCount())]
    contours.append(dict(index=i, vertices_iu=points,
        vertices_mm=[[p.ToMM(x),p.ToMM(y)] for x,y in points]))
data['bbox_diagnostic'] = dict(max_error_iu=b.GetDesignSettings().m_MaxError, contours=contours)
print(json.dumps(data,indent=2,sort_keys=True))
