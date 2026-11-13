from dataclasses import replace, FrozenInstanceError
import pytest
import aoi_platform.boundary_binding as flow
from aoi_platform.boundary_evidence import BoundaryContour, PreflightFailure, CATEGORIES
from aoi_platform.geometry.models import Point2
from aoi_platform.geometry.transforms import Transform2, TransformKind
from test_boundary_preflight import fixture, P


def inputs():
    r,e=fixture();f=e.boundary_frame
    # Independent source corners: center (2,3), size 4x2. Map (-y+10,x+20).
    e=replace(e,contours=(BoundaryContour(tuple(Point2(x,y,f) for x,y in
        ((0,2),(4,2),(4,4),(0,4))),True,0),))
    return r,e


def counted(monkeypatch):
    calls=[];real=flow.candidate.build_rectangular_pad_candidates
    def call(r):calls.append(r);return real(r)
    monkeypatch.setattr(flow.candidate,'build_rectangular_pad_candidates',call)
    return calls


def test_independent_oracle_and_single_call(monkeypatch):
    calls=counted(monkeypatch);r,e=inputs();before=repr((r,e))
    e=replace(e,coverage=tuple(reversed(e.coverage)))
    result=flow.bind_pad_boundaries(r,(e,),P)
    assert isinstance(result,flow.BoundaryBindingSuccess),result
    assert len(calls)==1
    assert [(p.x,p.y) for p in result.candidates[0].vertices]==[(8,20),(8,24),(6,24),(6,20)]
    assert result.bindings[0].correspondence.indices==(0,1,2,3)
    assert result.bindings[0].evidence is e
    assert result.bindings[0].unknown_categories==CATEGORIES
    assert result.artifact_record_status=='supplied-declaration-unverified'
    assert result.source_membership_status=='not-verified'
    assert not result.import_ready and not result.targeting_authorized and not result.published
    with pytest.raises(FrozenInstanceError):result.candidates=()
    assert repr((r,replace(e,coverage=tuple(reversed(e.coverage)))))==before


def test_binding_failure_blocks_candidate(monkeypatch):
    calls=counted(monkeypatch);r,e=inputs()
    result=flow.bind_pad_boundaries(r,(replace(e,source_pad_id='wrong'),),P)
    assert isinstance(result,PreflightFailure) and calls==[]
    assert not hasattr(result,'candidates')


def pair():
    r,e=inputs();p=r.pads[0]
    p2=replace(p,pad_id='z',source_entity_id='source2',provenance=replace(p.provenance,source_entity_id='source2'))
    e2=replace(e,evidence_id='e2',canonical_pad_id='z',source_pad_id='source2',membership=replace(e.membership,source_pad_id='source2'))
    return replace(r,pads=(p,p2)),e,e2


@pytest.mark.parametrize('kind',['mismatch','ambiguity'])
def test_one_bad_pad_rejects_whole_batch(monkeypatch,kind):
    calls=counted(monkeypatch);r,e,e2=pair()
    if kind=='mismatch':
        e2=replace(e2,contours=(replace(e2.contours[0],vertices=tuple(replace(p,x=p.x+1) for p in e2.contours[0].vertices)),))
    else:
        # Exact zero-datum identity prevents translation roundoff obscuring tiny ambiguity.
        parent=replace(r.parents[0],source_to_p=Transform2('id',e.boundary_frame,r.target_frame,
            ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID))
        tiny=replace(r.pads[1],rectangle=replace(r.pads[1].rectangle,
            center=Point2(0,0,e.boundary_frame),width=1e-6,height=1e-6))
        r=replace(r,parents=(parent,),pads=(r.pads[0],tiny))
        e=replace(e,boundary_to_p=parent.source_to_p)
        e2=replace(e2,boundary_to_p=parent.source_to_p,contours=(BoundaryContour(tuple(
            Point2(x,y,e.boundary_frame) for x,y in ((-5e-7,-5e-7),(5e-7,-5e-7),(5e-7,5e-7),(-5e-7,5e-7))),True,0),))
    result=flow.bind_pad_boundaries(r,(e2,e),P)
    assert len(calls)==1 and isinstance(result,PreflightFailure)
    assert not hasattr(result,'candidates')
    assert result.report.errors[0].message==('no_match' if kind=='mismatch' else 'ambiguous_mapping')
    assert result.report.errors[0].entity_id=='z'


def test_convex_does_not_replace_candidate_admission(monkeypatch):
    calls=counted(monkeypatch);r,e=inputs()
    r=replace(r,pads=(replace(r.pads[0],side='bottom'),))
    result=flow.bind_pad_boundaries(r,(e,),P)
    assert len(calls)==1 and isinstance(result,PreflightFailure)
    assert not hasattr(result,'candidates')


@pytest.mark.parametrize('kind',['affine','unvalidated','bound'])
def test_explicit_boundary_transform_guards(kind):
    r,e=inputs()
    if kind=='affine':e=replace(e,boundary_to_p=replace(e.boundary_to_p,kind=TransformKind.AFFINE))
    elif kind=='unvalidated':
        f=replace(e.boundary_frame,origin='other')
        t=Transform2('unvalidated',f,r.target_frame,e.boundary_to_p.matrix,TransformKind.RIGID)
        e=replace(e,boundary_frame=f,boundary_to_p=t,contours=(replace(e.contours[0],vertices=tuple(replace(p,frame=f) for p in e.contours[0].vertices)),))
    else:e=replace(e,contours=(replace(e.contours[0],vertices=(replace(e.contours[0].vertices[0],x=1000001),)+e.contours[0].vertices[1:]),))
    result=flow.bind_pad_boundaries(r,(e,),P)
    assert isinstance(result,PreflightFailure) and not hasattr(result,'candidates')


def test_sorted_all_batch_success(monkeypatch):
    calls=counted(monkeypatch);r,e,e2=pair()
    result=flow.bind_pad_boundaries(replace(r,pads=tuple(reversed(r.pads))),(e2,e),P)
    assert isinstance(result,flow.BoundaryBindingSuccess) and len(calls)==1
    assert tuple(c.pad_id for c in result.candidates)==('pad','z')
    assert tuple(b.evidence.canonical_pad_id for b in result.bindings)==('pad','z')
