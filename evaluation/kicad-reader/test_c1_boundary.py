"""Comparator tests only: no pcbnew import/load or simulated geometry algorithm."""
from copy import deepcopy
import pytest
from c1_boundary_probe import SOURCE_HASH,PARENT
from c1_boundary_compare import EXPECTED,compare


def payload():
    return dict(protocol='c1-boundary-diagnostic-v1',build='10.0.7',input_sha256=SOURCE_HASH,
        coordinate_space='board-world X-right/Y-down',iu_per_mm=1000000,clearance_iu=0,
        max_error_iu=1,error_location='ERROR_INSIDE',pads=[dict(uuid=u,parent_uuid=PARENT,
        layer='F.Cu',accessor='PAD.TransformShapeToPolygon',contours=[dict(closed=True,hole_count=0,
        vertices_iu=[list(v) for v in points])]) for u,points in EXPECTED.items()])


@pytest.mark.parametrize('start',range(4))
@pytest.mark.parametrize('direction',[1,-1])
def test_cyclic_and_reversed_contours(start,direction):
    p=payload()
    for row in p['pads']:
        v=row['contours'][0]['vertices_iu']
        row['contours'][0]['vertices_iu']=[v[(start+direction*i)%4] for i in range(4)]
    before=deepcopy(p);result=compare(p)
    assert result['passed'] and p==before
    for row in p['pads']:
        mapping=result['oracle_to_raw_indices'][row['uuid']]
        assert [tuple(row['contours'][0]['vertices_iu'][i]) for i in mapping]==list(EXPECTED[row['uuid']])


@pytest.mark.parametrize('case',['vertex','crossing','duplicate','open','hole','extra-contour','missing-pad','parent','layer','float','closing-vertex'])
def test_invalid_boundary_rejected_without_mutation(case):
    p=payload();r=p['pads'][0];c=r['contours'][0];v=c['vertices_iu']
    if case=='vertex': v[0][0]+=2
    elif case=='crossing': v[1],v[2]=v[2],v[1]
    elif case=='duplicate':v[1]=v[0][:]
    elif case=='open':c['closed']=False
    elif case=='hole':c['hole_count']=1
    elif case=='extra-contour':r['contours'].append(deepcopy(c))
    elif case=='missing-pad':p['pads'].pop()
    elif case=='parent':r['parent_uuid']='wrong'
    elif case=='layer':r['layer']='B.Cu'
    elif case=='float':v[0][0]=float(v[0][0])
    elif case=='closing-vertex':v.append(v[0][:])
    before=deepcopy(p)
    assert compare(p)['passed'] is False and p==before


def test_one_iu_boundary_allowed():
    p=payload();p['pads'][0]['contours'][0]['vertices_iu'][0][0]+=1
    assert compare(p)['passed']


@pytest.mark.parametrize('case', ['build', 'open', 'hole'])
def test_optimized_python_rejects_invalid_boundary(case):
    import json
    from pathlib import Path
    import subprocess
    import sys

    p = payload()
    assert compare(p)['passed'] is True
    if case == 'build':
        p['build'] = 'wrong-build'
    elif case == 'open':
        p['pads'][0]['contours'][0]['closed'] = False
    else:
        p['pads'][0]['contours'][0]['hole_count'] = 1
    completed = subprocess.run(
        [sys.executable, '-B', '-O', '-c',
         'import json,sys; from c1_boundary_compare import compare; '
         'print(json.dumps(dict(optimize=sys.flags.optimize, '
         'result=compare(json.load(sys.stdin)))))'],
        input=json.dumps(p), text=True, capture_output=True,
        cwd=Path(__file__).resolve().parent, timeout=10, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    actual = json.loads(completed.stdout)
    assert actual['optimize'] == 1
    assert actual['result']['passed'] is False
    assert actual['result']['code'] == 'C1_BOUNDARY_MISMATCH'
