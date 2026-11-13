from dataclasses import replace, FrozenInstanceError
from math import nextafter, inf
import pytest
from aoi_platform.boundary_evidence import BoundaryContour, BoundaryBindingPolicy, _POLICY
from aoi_platform.boundary_correspondence import match_contours_in_p, Correspondence, CorrespondenceFailure
from aoi_platform.geometry.models import Frame, FrameKind, Unit, AxisDirection, Point2

P = Frame('P', FrameKind.PCB, Unit.MM, 'datum', AxisDirection.RIGHT, AxisDirection.UP, 'scope')
POLICY = BoundaryBindingPolicy(*_POLICY)
XY = ((0,0),(4,0),(4,2),(0,2))

def contour(xy=XY):
    return BoundaryContour(tuple(Point2(x,y,P) for x,y in xy), True, 0)

def failure(a,b,reason):
    result=match_contours_in_p(a,b,POLICY)
    assert isinstance(result,CorrespondenceFailure)
    assert result.reason==reason
    assert not hasattr(result,'candidates')
    return result

@pytest.mark.parametrize('indices',[(0,1,2,3),(1,2,3,0),(2,3,0,1),(3,0,1,2),
                                    (0,3,2,1),(1,0,3,2),(2,1,0,3),(3,2,1,0)])
def test_eight_independent_order_oracles(indices):
    a=contour();b=contour(tuple(XY[i] for i in indices));before=repr((a,b))
    result=match_contours_in_p(a,b,POLICY)
    assert isinstance(result,Correspondence)
    assert result.indices==tuple(indices.index(i) for i in range(4))
    assert result.max_component_error_mm==0 and repr((a,b))==before
    assert not hasattr(result,'candidates')
    with pytest.raises(FrozenInstanceError):result.indices=()

def test_rotated_rectangle_large_datum():
    # Orthogonal vectors (3,4), (-8,6), independently translated by (900000,900000).
    xy=((900000,900000),(900003,900004),(899995,900010),(899992,900006))
    result=match_contours_in_p(contour(xy),contour(xy[2:]+xy[:2]),POLICY)
    assert result.indices==(2,3,0,1)

@pytest.mark.parametrize('delta,accepted',[(1e-6,True),(nextafter(1e-6,inf),False)])
def test_exact_and_exceeded_component_tolerance(delta,accepted):
    xy=((0,0),(1,0),(1,2),(0,2))
    a=contour(xy);b=contour(tuple((-delta if x==0 else x,y) for x,y in xy))
    result=match_contours_in_p(a,b,POLICY)
    if accepted:
        assert isinstance(result,Correspondence)
        assert result.max_component_error_mm==1e-6
    else:assert result.reason=='no_match'

def test_tiny_pad_ambiguity_not_first_match():
    a=contour(((0,0),(1e-6,0),(1e-6,1e-6),(0,1e-6)))
    assert failure(a,a,'ambiguous_mapping').error.code.value=='SOURCE_CONFLICT'

@pytest.mark.parametrize('xy,reason',[
    (((0,0),(4,2),(4,0),(0,2)),'invalid_topology_or_adjacency'),
    (((0,0),(4,0),(1,1),(0,2)),'invalid_topology_or_adjacency'),
    (((0,0),(2,0),(4,0),(0,2)),'invalid_topology_or_adjacency'),
    (((0,0),(4,0),(4,0),(0,2)),'duplicate_vertices'),
    (((0,0),(5,0),(4,2),(0,2)),'no_match')])
def test_wrong_edges_vertices_topology(xy,reason):
    failure(contour(),contour(xy),reason)

@pytest.mark.parametrize('change',[{'closed':False},{'hole_count':1},{'vertices':()},
                                  {'vertices':contour().vertices+(contour().vertices[0],)}])
def test_unsupported_topology(change):
    failure(contour(),replace(contour(),**change),'unsupported_topology')

@pytest.mark.parametrize('value',[float('nan'),float('inf'),-float('inf'),True])
def test_malformed_nonfinite(value):
    point=Point2(0,0,P);object.__setattr__(point,'x',value)
    failure(contour(),replace(contour(),vertices=(point,)+contour().vertices[1:]),'nonfinite_or_invalid_coordinate')

def test_coordinate_bound_exact_and_exceeded():
    xy=((999999,0),(1000000,0),(1000000,2),(999999,2))
    assert isinstance(match_contours_in_p(contour(xy),contour(xy),POLICY),Correspondence)
    bad=contour(((999999,0),(nextafter(1e6,inf),0),(1e6,2),(999999,2)))
    failure(contour(xy),bad,'coordinate_bound')

def test_full_context():
    a=contour();b=replace(a,vertices=tuple(replace(p,frame=replace(P,origin='other')) for p in a.vertices))
    assert match_contours_in_p(a,b,POLICY).error.code.value=='CONTEXT_MISMATCH'

def test_invalid_policy():
    a=contour()
    assert match_contours_in_p(a,a,replace(POLICY,comparison_abs_mm=2e-6)).reason=='invalid_policy'
