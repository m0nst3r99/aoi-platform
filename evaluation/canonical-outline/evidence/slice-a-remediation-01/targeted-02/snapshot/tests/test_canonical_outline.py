"""Independent literal and Fraction oracles; synthetic, not source authentication."""
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from math import nextafter, inf

import pytest

from aoi_platform.geometry.canonical_outline import (
    CanonicalOutlineDeclaration, CanonicalOutlineFailure, CanonicalOutlineSuccess,
    DeclaredLine, OutlineProvenance, POLICY, RingDeclaration,
    transform_canonical_outline, validate_canonical_outline,
)
from aoi_platform.geometry import _outline_exact as ex
from aoi_platform.geometry.errors import ErrorCode
from aoi_platform.geometry.models import FrameKind, Point2
from aoi_platform.geometry.transforms import Transform2, TransformKind

OUTER = ((0,0),(20,0),(20,10),(0,10))
HOLE = ((2,2),(6,2),(6,4),(2,4))
HOLE2 = ((12,6),(14,6),(14,8),(12,8))
REF = OutlineProvenance("synthetic", "literal-fixture", "0"*64, "edge", "test-only literal coordinates")


@pytest.fixture
def pcb(mm_frame):
    return replace(mm_frame, kind=FrameKind.PCB)


def ring(frame, coords, name="exterior"):
    points = tuple(Point2(x,y,frame) for x,y in coords)
    return RingDeclaration(name, tuple(DeclaredLine(a,b,(replace(REF,entity_id=f"{name}/{i}"),))
                                     for i,(a,b) in enumerate(zip(points,points[1:]+points[:1]))))


def declaration(frame, holes=(), outer=OUTER):
    return CanonicalOutlineDeclaration("board",frame,ring(frame,outer),
                                       tuple(ring(frame,coords,f"hole-{i}") for i,coords in enumerate(holes)))


def accepted(d):
    result = validate_canonical_outline(d,POLICY)
    assert isinstance(result,CanonicalOutlineSuccess), result
    return result


def rejected(d, code=ErrorCode.OUTLINE_INVALID):
    result = validate_canonical_outline(d,POLICY)
    assert isinstance(result,CanonicalOutlineFailure)
    assert not hasattr(result,"outline")
    assert code in [e.code for e in result.report.errors]
    return result


def rational_area(r):
    # Independent unanchored shoelace; production uses anchored fixed-grid sums.
    return sum(Fraction(e.start.x)*Fraction(e.end.y)-Fraction(e.start.y)*Fraction(e.end.x)
               for e in r.edges)/2


@pytest.mark.parametrize("holes,net", [((),200),((HOLE,),192),((HOLE,HOLE2),188)])
def test_literal_area_bounds_perimeter_and_winding(pcb,holes,net):
    result = accepted(declaration(pcb,holes))
    o = result.outline
    assert rational_area(o.exterior) == 200
    assert all(rational_area(h)<0 for h in o.cutouts)
    assert sum(rational_area(r) for r in (o.exterior,)+o.cutouts) == net
    coords = [(e.start.x,e.start.y) for e in o.exterior.edges]
    assert (min(x for x,y in coords),min(y for x,y in coords),max(x for x,y in coords),max(y for x,y in coords)) == (0,0,20,10)
    if len(holes)==1:
        assert sum(abs(e.end.x-e.start.x)+abs(e.end.y-e.start.y) for r in (o.exterior,)+o.cutouts for e in r.edges)==72


@pytest.mark.parametrize("holes", [
    (((19,2),(21,2),(21,4),(19,4)),),
    (((20,2),(22,2),(22,4),(20,4)),),
    (((20,10),(21,10),(21,11),(20,11)),),
    (HOLE,((3,2.5),(4,2.5),(4,3),(3,3))),
    (HOLE,HOLE),
    (((3,1),(5,1),(5,8),(3,8)),((1,3),(8,3),(8,5),(1,5))),
    (((30,30),(31,30),(31,31),(30,31)),),
])
def test_topology_negative_literals(pcb,holes):
    rejected(declaration(pcb,holes))


def test_concavity_preserved(pcb):
    outer=((0,0),(10,0),(10,2),(2,2),(2,10),(0,10))
    assert rational_area(accepted(declaration(pcb,outer=outer)).outline.exterior)==36
    rejected(declaration(pcb,(((4,4),(6,4),(6,6),(4,6)),),outer))


@pytest.mark.parametrize("coords", [
    ((0,0),(2,2),(0,2),(2,0)),
    ((0,0),(1,0),(2,0)),
    ((0,0),(0,0),(1,1)),
    ((0,0),(4,0),(2,0),(2,2),(0,2)),
    ((0,0),(4,0),(4,4),(2,2),(0,4),(2,2)),
])
def test_malformed_rings(pcb,coords):
    rejected(declaration(pcb,outer=coords))


def test_open_duplicate_frame_nonfinite_atomic(pcb):
    d=declaration(pcb,(HOLE,))
    edge=replace(d.exterior.edges[0],end=Point2(19,0,pcb))
    rejected(replace(d,exterior=replace(d.exterior,edges=(edge,)+d.exterior.edges[1:])))
    rejected(replace(d,cutouts=(replace(d.cutouts[0],ring_id="exterior"),)),ErrorCode.DUPLICATE_ID)
    wrong=replace(pcb,board_revision_id="other")
    rejected(replace(d,frame=wrong),ErrorCode.CONTEXT_MISMATCH)
    p=object.__new__(Point2)
    object.__setattr__(p,"x",float("nan")); object.__setattr__(p,"y",0.0); object.__setattr__(p,"frame",pcb)
    bad=replace(d.exterior.edges[0],start=p)
    rejected(replace(d,exterior=replace(d.exterior,edges=(bad,)+d.exterior.edges[1:])),ErrorCode.SCHEMA_INVALID)


@pytest.mark.parametrize("gap,valid", [(nextafter(1e-8,0),False),(1e-8,False),(nextafter(1e-8,inf),True),(.001,True)])
def test_exact_clearance_guard(pcb,gap,valid):
    d=declaration(pcb,(((gap,2),(1,2),(1,4),(gap,4)),))
    (accepted if valid else rejected)(d)


@pytest.mark.parametrize("length,valid", [(nextafter(1e-8,0),False),(1e-8,False),(nextafter(1e-8,inf),True)])
def test_exact_edge_guard(pcb,length,valid):
    # A narrow triangle avoids a separate nonadjacent-edge guard.
    d=declaration(pcb,outer=((0,0),(length,0),(0,1)))
    (accepted if valid else rejected)(d)


@pytest.mark.parametrize("matrix,expected", [
    (((1.,0.,7.),(0.,1.,-3.),(0.,0.,1.)),((7,-3),(27,-3),(27,7),(7,7))),
    (((0.,-1.,0.),(1.,0.,0.),(0.,0.,1.)),((-10,0),(0,0),(0,20),(-10,20))),
    (((-1.,0.,20.),(0.,1.,0.),(0.,0.,1.)),((0,0),(20,0),(20,10),(0,10))),
])
def test_literal_transform_oracles_and_provenance(pcb,matrix,expected):
    original=accepted(declaration(pcb,(HOLE,HOLE2))).outline
    kind=TransformKind.REFLECTION if matrix[0][0]<0 else TransformKind.RIGID
    mapping=Transform2("operation",pcb,pcb,matrix,kind)
    result=transform_canonical_outline(original,mapping,POLICY)
    assert isinstance(result,CanonicalOutlineSuccess),result
    out=result.outline
    assert tuple((e.start.x,e.start.y) for e in out.exterior.edges)==expected
    assert sum(rational_area(r) for r in (out.exterior,)+out.cutouts)==188
    assert {e.provenance for r in (out.exterior,)+out.cutouts for e in r.edges} == {e.provenance for r in (original.exterior,)+original.cutouts for e in r.edges}
    assert out.frame==pcb and out.transforms[0].matrix==matrix
    literal_holes = {
        "translation": ({(9,-1),(13,-1),(13,1),(9,1)}, {(19,3),(21,3),(21,5),(19,5)}),
        "rotation": ({(-2,2),(-2,6),(-4,6),(-4,2)}, {(-6,12),(-6,14),(-8,14),(-8,12)}),
        "reflection": ({(18,2),(14,2),(14,4),(18,4)}, {(8,6),(6,6),(6,8),(8,8)}),
    }
    key = "reflection" if kind is TransformKind.REFLECTION else "rotation" if matrix[0][0]==0 else "translation"
    assert tuple({(e.start.x,e.start.y) for e in h.edges} for h in out.cutouts)==literal_holes[key]
    if kind is TransformKind.REFLECTION:
        xs=[e.start.x for e in out.cutouts[0].edges]
        assert (min(xs),max(xs))==(14,18)
    assert isinstance(transform_canonical_outline(out,mapping,POLICY),CanonicalOutlineSuccess)


def test_ordering_immutability_and_reversal(pcb):
    d=declaration(pcb,(HOLE,HOLE2))
    a=accepted(d)
    b=accepted(replace(d,cutouts=tuple(reversed(d.cutouts))))
    assert a==b
    with pytest.raises(FrozenInstanceError): a.outline.cutouts=()
    with pytest.raises(FrozenInstanceError): a.outline.cutouts[0].edges[0].start.x=7
    invalid=replace(d,cutouts=tuple(replace(h,edges=(replace(h.edges[0],end=Point2(9,9,pcb)),)+h.edges[1:]) for h in d.cutouts))
    assert rejected(invalid).report==rejected(replace(invalid,cutouts=tuple(reversed(invalid.cutouts)))).report
    assert a.outline.cutouts[0].edges[0].reversed_from_source


def test_limits_and_hash_conflicts(pcb):
    d=declaration(pcb)
    accepted(replace(d,outline_id="x"*256))
    rejected(replace(d,outline_id="x"*257),ErrorCode.INPUT_LIMIT_EXCEEDED)
    rejected(replace(d,outline_id="é"*129),ErrorCode.INPUT_LIMIT_EXCEEDED)
    rejected(replace(d,cutouts=tuple(ring(pcb,HOLE,str(i)) for i in range(33))),ErrorCode.INPUT_LIMIT_EXCEEDED)
    rejected(declaration(pcb,outer=((0,0),(1000001,0),(0,1))),ErrorCode.INPUT_LIMIT_EXCEEDED)
    accepted(declaration(pcb,outer=((0,0),(1000000,0),(0,1))))
    bad=replace(d.exterior.edges[0],provenance=(REF,replace(REF,sha256="1"*64)))
    rejected(replace(d,exterior=replace(d.exterior,edges=(bad,)+d.exterior.edges[1:])),ErrorCode.SOURCE_CONFLICT)


def test_32_cutouts_and_512_edges_exact_work_oracle(pcb):
    # 128 segments along each side of a rectangle: 512 edges, no simplification.
    coords=tuple([(i,0) for i in range(128)]+[(128,i) for i in range(128)]+[(128-i,128) for i in range(128)]+[(0,128-i) for i in range(128)])
    result=accepted(declaration(pcb,outer=coords))
    assert len(result.outline.exterior.edges)==512
    assert result.work.edge_pairs==130816  # 512*511/2, independent combinatorial oracle
    assert result.work.primitives==130816*320+512*(8+16+16)+4
    rejected(declaration(pcb,outer=coords+((0,.5),)),ErrorCode.INPUT_LIMIT_EXCEEDED)
    holes=tuple(((1+i*.5,1),(1.2+i*.5,1),(1.2+i*.5,1.2),(1+i*.5,1.2)) for i in range(32))
    result=accepted(declaration(pcb,holes))
    assert result.work.edge_pairs==8646  # 132*131/2
    assert result.work.containment_visits==4096  # 32*4 + 32*31*4


def test_independent_budget_boundary_and_arithmetic():
    w=ex.Ledger()
    w.charge(1<<26,130816,16384)
    assert w.snapshot().primitives==67108864
    for kwargs in ({"primitives":1},{"pairs":1},{"visits":1}):
        with pytest.raises(ex.Exhausted): w.charge(**kwargs)
    assert w.snapshot().edge_pairs==130816
    assert w.mul((1<<2191)-1,(1<<2191)-1).bit_length()==4382
    with pytest.raises(ex.Exhausted): w.mul(1<<2191,1<<2191)
    with pytest.raises(ex.Exhausted): w.add((1<<4382)-1,1)


@pytest.mark.parametrize("coords", [
    ((0.,0.),(1e6,1e6),(nextafter(1e6,0),1e6)),
    ((-1e6,-1e6),(1e6,1e6),(1e6,nextafter(1e6,0))),
    ((0.,0.),(5e-324,0.),(0.,5e-324)),
    ((0.,0.),(1.,1e-300),(2.,nextafter(2e-300,inf))),
])
def test_rational_orientation_oracle(coords):
    a,b,c=[tuple(map(Fraction,p)) for p in coords]
    expected=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    w=ex.Ledger(); w.charge(16)
    actual=ex.orient(*(tuple(ex.grid(v) for v in p) for p in coords),w)
    assert Fraction(actual,1<<2148)==expected
    assert w.max_bits<=4382


@pytest.mark.parametrize("p,a,b", [((.5,1e-8),(0.,0.),(1.,0.)), ((-1e-8,0.),(0.,0.),(1.,0.)),((1.+1e-8,0.),(0.,0.),(1.,0.)),((.5,nextafter(1e-8,inf)),(0.,0.),(1.,0.))])
def test_rational_distance_oracle(p,a,b):
    pp,aa,bb=[tuple(map(Fraction,v)) for v in (p,a,b)]
    v=tuple(y-x for x,y in zip(aa,bb)); u=tuple(y-x for x,y in zip(aa,pp))
    t=max(Fraction(0),min(Fraction(1),sum(x*y for x,y in zip(u,v))/sum(x*x for x in v)))
    expected=sum((pp[i]-aa[i]-t*v[i])**2 for i in range(2))<=Fraction(1e-8)**2
    w=ex.Ledger(); w.charge(320)
    assert ex.near_point(*(tuple(ex.grid(x) for x in v) for v in (p,a,b)),w)==expected


def test_metadata_reference_and_diagnostic_exact_limits(pcb):
    from aoi_platform.geometry.canonical_outline import _Admission, _Invalid, _Issues
    a=_Admission()
    for _ in range(256): a.text("x"*1024,"detail",1024)
    assert a.text_bytes==262144
    with pytest.raises(_Invalid): a.text("x","detail",1024)
    b=_Admission(); b.text("x"*1024,"detail",1024)
    with pytest.raises(_Invalid): b.text("x"*1025,"detail",1024)
    d=declaration(pcb)
    edges=tuple(replace(e,provenance=(REF,)*256) for e in d.exterior.edges)
    accepted(replace(d,exterior=replace(d.exterior,edges=edges)))
    edges=(replace(edges[0],provenance=edges[0].provenance+(REF,)),)+edges[1:]
    rejected(replace(d,exterior=replace(d.exterior,edges=edges)),ErrorCode.INPUT_LIMIT_EXCEEDED)
    sink=_Issues()
    for _ in range(31): sink.add(ErrorCode.OUTLINE_INVALID,"ring/"+"\x01"*256,"Invalid ring.")
    assert len(sink.values)==31 and not sink.truncated
    sink.add(ErrorCode.OUTLINE_INVALID,"ring","Invalid ring.")
    sink.add(ErrorCode.OUTLINE_INVALID,"ring","Invalid ring.")
    assert len(sink.values)==32 and sink.truncated
    import json
    sizes=[len(json.dumps(e.to_dict(),ensure_ascii=False).encode()) for e in sink.values]
    assert max(sizes)<=4096 and sum(sizes)<=131072


@pytest.mark.parametrize("transform", [False, True])
def test_work_exhaustion_is_atomic_without_limit_changes(pcb,monkeypatch,transform):
    outline=accepted(declaration(pcb)).outline if transform else None
    original=ex.Ledger
    def exhausted_ledger(passes=1):
        w=original(passes)
        w.charge((1<<26)*passes)
        return w
    monkeypatch.setattr(ex,"Ledger",exhausted_ledger)
    if transform:
        mapping=Transform2("identity",pcb,pcb,((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID)
        result=transform_canonical_outline(outline,mapping,POLICY)
        assert isinstance(result,CanonicalOutlineFailure) and not hasattr(result,"outline")
        assert result.report.errors[0].code==ErrorCode.INPUT_LIMIT_EXCEEDED
    else:
        result=rejected(declaration(pcb),ErrorCode.INPUT_LIMIT_EXCEEDED)
    assert result.work.primitives==67108864*(2 if transform else 1)
    assert result.truncated


def test_truncation_and_two_invalid_rings_order(pcb):
    d=declaration(pcb,(HOLE,HOLE2))
    bad=tuple(replace(h,edges=h.edges[:2]) for h in d.cutouts)
    a=rejected(replace(d,cutouts=bad))
    b=rejected(replace(d,cutouts=tuple(reversed(bad))))
    assert a==b and len(a.report.errors)==2
    points=((0,0),)*40
    result=rejected(declaration(pcb,outer=points))
    assert result.truncated and len(result.report.errors)==32


def test_transform_rejection_and_policy(pcb):
    o=accepted(declaration(pcb,(HOLE,))).outline
    scale=Transform2("scale",pcb,pcb,((2.,0.,0.),(0.,2.,0.),(0.,0.,1.)))
    failure=transform_canonical_outline(o,scale,POLICY)
    assert isinstance(failure,CanonicalOutlineFailure) and not hasattr(failure,"outline")
    moved=Transform2("large",pcb,pcb,((1.,0.,1e6),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID)
    assert isinstance(transform_canonical_outline(o,moved,POLICY),CanonicalOutlineFailure)
    other=replace(pcb,frame_id="other",board_revision_id="other-rev")
    mapping=Transform2("identity",other,other,((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID)
    failure=transform_canonical_outline(o,mapping,POLICY)
    assert failure.report.errors[0].code==ErrorCode.CONTEXT_MISMATCH
    wrong=validate_canonical_outline(declaration(pcb),replace(POLICY,guard_hex="changed"))
    assert wrong.report.errors[0].code==ErrorCode.POLICY_INVALID


@pytest.mark.parametrize("height,valid",[(nextafter(1e-8,0),False),(1e-8,False),(nextafter(1e-8,inf),True)])
def test_exact_area_guard(pcb,height,valid):
    # Base 2*guard makes area exactly guard*height. Other edges exceed guard.
    (accepted if valid else rejected)(declaration(pcb,outer=((0,0),(2e-8,0),(1e-8,height))))


@pytest.mark.parametrize("field", ["transform_id", "target_id", "target_origin", "provenance", "source_id"])
def test_remediation_metadata_before_helpers(pcb,monkeypatch,field):
    o=accepted(declaration(pcb)).outline
    m=Transform2("identity",pcb,pcb,((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID)
    # Deliberately untrusted frozen record: no constructor assurance at admission.
    object.__setattr__(m,"conventions_validated",False)
    if field=="transform_id": object.__setattr__(m,"transform_id","é"*129)
    if field=="target_id": object.__setattr__(m,"to_frame",replace(pcb,frame_id="é"*129))
    if field=="target_origin": object.__setattr__(m,"to_frame",replace(pcb,origin="é"*513))
    if field=="provenance": object.__setattr__(m,"provenance",("é"*513,))
    if field=="source_id": object.__setattr__(m,"from_frame",replace(pcb,frame_id="é"*129))
    def forbidden(*args): pytest.fail("helper consumed transform before bounded admission")
    monkeypatch.setattr(Transform2,"_require_validated_conventions",forbidden)
    monkeypatch.setattr(Transform2,"_validate_isometry",forbidden)
    monkeypatch.setattr(Transform2,"apply",forbidden)
    result=transform_canonical_outline(o,m,POLICY)
    assert isinstance(result,CanonicalOutlineFailure) and not hasattr(result,"outline")
    assert result.report.errors[0].code==ErrorCode.INPUT_LIMIT_EXCEEDED


def test_remediation_transform_work_literal_oracle(pcb,monkeypatch):
    o=accepted(declaration(pcb)).outline
    m=Transform2("identity",pcb,pcb,((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID)
    calls=[]
    apply=Transform2.apply
    def spy(self,point):
        calls.append(point)
        return apply(self,point)
    monkeypatch.setattr(Transform2,"apply",spy)
    result=transform_canonical_outline(o,m,POLICY)
    assert isinstance(result,CanonicalOutlineSuccess)
    assert len(calls)==8  # two endpoints for each of four edges; no identity dedup
    # Per pass: 6 pairs*320 + 4 edges*(8 conversion+16 edge+16 area)
    # + 4 finalization (abs, two products, compare) = 2084.
    # One isometry envelope 64; eight points * (4 products + 4 adds) = 64.
    assert result.work.primitives==4296  # 2*2084+64+64; never from observed counters


@pytest.mark.parametrize("remaining,mapped,contours,spent",[(0,0,1,0),(63,0,1,0),(127,0,1,64),(128,8,1,128)])
def test_remediation_exhaustion_after_source(pcb,monkeypatch,remaining,mapped,contours,spent):
    import aoi_platform.geometry.canonical_outline as module
    o=accepted(declaration(pcb)).outline
    m=Transform2("identity",pcb,pcb,((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID)
    Ledger=ex.Ledger
    def seeded(passes=1):
        w=Ledger(passes)
        w.charge(134217728-2084-remaining)
        return w
    calls=[]; rings=[]
    apply=Transform2.apply; contour=module.validate_contour
    def spy(self,p): calls.append(p); return apply(self,p)
    def ring_spy(*args): rings.append(1); return contour(*args)
    monkeypatch.setattr(ex,"Ledger",seeded)
    monkeypatch.setattr(Transform2,"apply",spy)
    monkeypatch.setattr(module,"validate_contour",ring_spy)
    result=transform_canonical_outline(o,m,POLICY)
    assert isinstance(result,CanonicalOutlineFailure) and not hasattr(result,"outline")
    assert result.truncated and result.report.errors[0].code==ErrorCode.INPUT_LIMIT_EXCEEDED
    assert len(calls)==mapped and len(rings)==contours
    assert result.work.primitives==134217728-remaining+spent
