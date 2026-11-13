"""Portable C1 boundary comparison against literal source-derived oracle.
Raw polygon order is not modified. Only cyclic/reversed contour correspondence allowed.
"""
from c1_boundary_probe import SOURCE_HASH, PARENT, PADS

# C1-ORACLE.md world corners converted exactly from mm to IU, not candidate math.
EXPECTED={
 'e2743daf-d278-4538-a77e-8f62f1b7978c':((191648850,63766060),(191648850,60265940),(194049150,60265940),(194049150,63766060)),
 '4e53dd71-4be4-4973-9c48-191e7b2e27bb':((191648850,70268460),(191648850,66768340),(194049150,66768340),(194049150,70268460)),
}


def _require(condition):
    if not condition:
        raise ValueError("C1 boundary validation failed")


def compare(payload):
    """Return diagnostic only; never usable geometry. Fixed tolerance 1 IU (1 nm)."""
    mappings={}
    try:
        _require(payload['protocol']=='c1-boundary-diagnostic-v1')
        _require(payload['build']=='10.0.7' and payload['input_sha256']==SOURCE_HASH)
        _require(payload['coordinate_space']=='board-world X-right/Y-down')
        for key,value in [('iu_per_mm',1000000),('clearance_iu',0),('max_error_iu',1)]:
            _require(type(payload[key]) is int and payload[key]==value)
        _require(payload['error_location']=='ERROR_INSIDE')
        rows=payload['pads'];_require(type(rows) is list and len(rows)==2)
        _require({r['uuid'] for r in rows}==PADS)
        for row in rows:
            _require(row['parent_uuid']==PARENT and row['layer']=='F.Cu')
            _require(row['accessor']=='PAD.TransformShapeToPolygon')
            contours=row['contours'];_require(type(contours) is list and len(contours)==1)
            c=contours[0];_require(c['closed'] is True)
            _require(type(c['hole_count']) is int and c['hole_count']==0)
            points=c['vertices_iu'];_require(type(points) is list and len(points)==4)
            _require(all(type(v) is list and len(v)==2 and all(type(x) is int for x in v) for v in points))
            _require(len({tuple(v) for v in points})==4)
            expected=EXPECTED[row['uuid']];matches=[]
            for direction in (1,-1):
                for start in range(4):
                    indices=[(start+direction*i)%4 for i in range(4)]
                    if all(max(abs(points[indices[i]][k]-expected[i][k]) for k in (0,1))<=1 for i in range(4)):
                        matches.append(indices)
            _require(len(matches)==1)  # Adjacency preserved; unordered point-set match is insufficient.
            mappings[row['uuid']]=matches[0]
        return dict(passed=True,oracle_to_raw_indices=mappings,tolerance_iu=1,
                    scope='C1 F_Cu only; no publication or candidate authority')
    except (KeyError,TypeError,ValueError):
        return dict(passed=False,code='C1_BOUNDARY_MISMATCH',scope='diagnostic only')
