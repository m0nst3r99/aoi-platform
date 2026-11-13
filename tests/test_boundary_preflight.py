from dataclasses import replace, fields, FrozenInstanceError
import pytest
import aoi_platform.boundary_evidence as b
from test_pad_candidates import request, HASH

P=b.BoundaryBindingPolicy(*b._POLICY)
def fixture():
    r=request();pad=r.pads[0];ref=b.ArtifactRef('pcb',HASH,'declared')
    e=b.BoundaryEvidence('e',ref,ref,ref,(),'parent','pad','parent-source','pad-source',pad.source_frame,r.parents[0].source_to_p,'board-source-normalized',(b.BoundaryContour((pad.rectangle.center,)*4,True,0),),'F.Cu','top','synthetic','1','1',tuple(b.ConstructCoverage(c,'unknown','caller-declaration','',()) for c in b.CATEGORIES),b.MembershipEvidence('parent-source','pad-source',(),None,None))
    return r,e

def run(r,e):return b.preflight_boundary_evidence(r,(e,),P)
def reject(result,code):
    assert isinstance(result,b.PreflightFailure)
    assert result.report.errors[0].code.value==code
    assert not hasattr(result,'candidates')

def test_preflight_only_immutable_no_candidate_call(monkeypatch):
    r,e=fixture()
    monkeypatch.setattr(b.candidate,'build_rectangular_pad_candidates',lambda *a:pytest.fail('candidate called'))
    result=run(r,e);assert isinstance(result,b.PreflightSuccess)
    assert result.status=='preflight-only-not-bound'
    assert result.source_membership_status=='not-verified' and not result.import_ready
    assert not hasattr(result,'candidates')
    with pytest.raises((FrozenInstanceError,TypeError)):result.import_ready=True
    with pytest.raises(FrozenInstanceError):e.evidence_id='x'
    with pytest.raises(FrozenInstanceError):e.source.locator='x'

@pytest.mark.parametrize('field',fields(b.BoundaryBindingPolicy),ids=lambda f:f.name)
def test_each_policy_field_exact(field):
    r,e=fixture();v=getattr(P,field.name)
    bad='wrong' if type(v) is str else v+1
    reject(b.preflight_boundary_evidence(r,(e,),replace(P,**{field.name:bad})),'POLICY_INVALID')

@pytest.mark.parametrize('bad',[True,False,float('nan'),float('inf'),-1,0,'4096',None])
def test_invalid_numeric_policy(bad):
    r,e=fixture();reject(b.preflight_boundary_evidence(r,(e,),replace(P,max_pads=bad)),'POLICY_INVALID')

@pytest.mark.parametrize('which',['list','generator','dict','empty','category','duplicate','unsupported','mutable_refs'])
def test_malformed(which):
    r,e=fixture()
    if which in ('list','generator','dict'):
        value={'list':[e],'generator':iter((e,)),'dict':{}}[which]
        reject(b.preflight_boundary_evidence(r,value,P),'SCHEMA_INVALID');return
    if which=='empty':reject(b.preflight_boundary_evidence(replace(r,pads=()),(),P),'SCHEMA_INVALID');return
    if which=='category':e=replace(e,coverage=e.coverage[:-1])
    if which=='duplicate':e=replace(e,coverage=e.coverage[:-1]+(e.coverage[0],))
    if which=='unsupported':e=replace(e,coverage=(replace(e.coverage[0],status='observed-unsupported'),)+e.coverage[1:])
    if which=='mutable_refs':e=replace(e,auxiliary_evidence=[])
    reject(run(r,e),'GEOMETRY_UNSUPPORTED' if which=='unsupported' else 'SCHEMA_INVALID')

@pytest.mark.parametrize('name,cap',[('evidence_id',256),('producer_identity',256)])
def test_id_exact_and_exceeded(name,cap):
    r,e=fixture();assert isinstance(run(r,replace(e,**{name:'x'*cap})),b.PreflightSuccess)
    reject(run(r,replace(e,**{name:'x'*(cap+1)})),'INPUT_LIMIT_EXCEEDED')

def test_multibyte_text_boundaries():
    r,e=fixture();x=replace(e.coverage[0],detail=chr(0xE9)*512)
    assert isinstance(run(r,replace(e,coverage=(x,)+e.coverage[1:])),b.PreflightSuccess)
    reject(run(r,replace(e,coverage=(replace(x,detail=x.detail+'x'),)+e.coverage[1:])),'INPUT_LIMIT_EXCEEDED')

def test_collection_limit():
    r,e=fixture();assert isinstance(run(r,replace(e,auxiliary_evidence=(e.source,)*16)),b.PreflightSuccess)
    reject(run(r,replace(e,auxiliary_evidence=(e.source,)*17)),'INPUT_LIMIT_EXCEEDED')

def test_joint_accounting_occurrences():
    r,e=fixture();a=run(r,e);c=run(r,replace(e,auxiliary_evidence=(e.source,)*2))
    assert c.evidence_refs==a.evidence_refs+2
    assert c.text_bytes==a.text_bytes+2*(len('pcb')+64+len('declared'))
    assert a.evidence_refs>3  # request and boundary share the same counters

@pytest.mark.parametrize('kind,limit',[('nodes',2686976),('text_bytes',8388608),('refs',32768)])
def test_exact_total_counter_boundaries(kind,limit):
    # Unit test of the actual counter primitive; does not lower production policy.
    budget=b._Budget(P);budget.take(kind,limit,limit);assert getattr(budget,kind)==limit
    with pytest.raises(b._Reject) as ex:budget.take(kind,1,limit)
    assert ex.value.code.value=='INPUT_LIMIT_EXCEEDED'

def test_joint_total_refs_exceeded():
    r,e=fixture();e=replace(e,auxiliary_evidence=(e.source,)*16)
    # 19 refs per binding, plus original request refs; sharing objects still counts.
    n=1725
    result=b.preflight_boundary_evidence(replace(r,pads=r.pads*n),(e,)*n,P)
    reject(result,'INPUT_LIMIT_EXCEEDED');assert result.truncation.occurred

def test_depth_exact_exceeded():
    # Structural traversal primitive: roots depth 0; no semantic admission claimed.
    v=None
    for _ in range(32):v=(v,)
    assert b._walk(v,(),P).nodes>32
    with pytest.raises(b._Reject):b._walk((v,),(),P)

def test_large_tuple_rejected_before_traversal():
    r,e=fixture();reject(b.preflight_boundary_evidence(r,(e,)*4097,P),'INPUT_LIMIT_EXCEEDED')

@pytest.mark.parametrize('kind',['text','refs'])
def test_joint_walk_exact_and_exceeded_totals(kind):
    # Actual joint traversal, not semantic input admission; no policy override.
    if kind=='text':
        left=('x'*256,)*16384;right=('x'*256,)*16384
        result=b._walk((left,right),(),P)
        assert result.text_bytes==8388608
        right=right+('x',)
    else:
        ref=b.ArtifactRef('p',HASH,'l')
        left=(ref,)*16384;right=(ref,)*16384
        result=b._walk((left,right),(),P)
        assert result.refs==32768
        right=right+(ref,)
    with pytest.raises(b._Reject) as ex:b._walk((left,right),(),P)
    assert ex.value.code.value=='INPUT_LIMIT_EXCEEDED'
