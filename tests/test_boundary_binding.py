from dataclasses import replace, FrozenInstanceError
import pytest
import aoi_platform.boundary_evidence as b
from test_boundary_preflight import fixture, P


def bind(r,e):return b.bind_boundary_declarations(r,(e,),P)
def failed(result,code):
    assert isinstance(result,b.PreflightFailure),result
    assert code in [x.code.value for x in result.report.errors]
    assert not hasattr(result,'candidates')

def test_positive_declaration_only_nonmutation(monkeypatch):
    r,e=fixture();before=repr((r,e))
    monkeypatch.setattr(b.candidate,'build_rectangular_pad_candidates',lambda *a:pytest.fail('candidate invoked'))
    result=bind(r,e)
    assert isinstance(result,b.DeclarationBindingSuccess),result
    assert result.bindings==(e,) and repr((r,e))==before
    assert result.status=='declaration-binding-only-no-geometry-check'
    assert result.artifact_record_status=='supplied-declaration-unverified'
    assert not result.import_ready and not hasattr(result,'candidates')
    with pytest.raises(FrozenInstanceError):result.bindings=()
    # Repeated vertices intentionally pass: geometry matching is NOT implemented.

@pytest.mark.parametrize('field',['canonical_pad_id','canonical_parent_id','source_pad_id','source_parent_id'])
def test_conflicting_identity(field):
    r,e=fixture();failed(bind(r,replace(e,**{field:'wrong'})),'SOURCE_CONFLICT')

@pytest.mark.parametrize('role',['source','observation','boundary','auxiliary','coverage','membership'])
@pytest.mark.parametrize('kind',['id','hash'])
def test_every_artifact_reference(role,kind):
    r,e=fixture();ref=replace(e.source,**({'artifact_id':'missing'} if kind=='id' else {'computed_sha256':'0'*64}))
    if role=='auxiliary':e=replace(e,auxiliary_evidence=(ref,))
    elif role=='coverage':e=replace(e,coverage=(replace(e.coverage[0],evidence=(ref,)),)+e.coverage[1:])
    elif role=='membership':e=replace(e,membership=replace(e.membership,audit_refs=(ref,)))
    else:e=replace(e,**{role:ref})
    failed(bind(r,e),'SOURCE_CONFLICT')

def pair():
    r,e=fixture();pad=replace(r.pads[0],pad_id='pad2',source_entity_id='source2',provenance=replace(r.pads[0].provenance,source_entity_id='source2'))
    e2=replace(e,evidence_id='e2',canonical_pad_id='pad2',source_pad_id='source2',membership=replace(e.membership,source_pad_id='source2'))
    return replace(r,pads=r.pads+(pad,)),e,e2

@pytest.mark.parametrize('case',['missing','extra','duplicate','duplicate_evidence','mixed'])
def test_no_partial_results(case):
    r,e,e2=pair();es=(e,e2);code='SOURCE_CONFLICT'
    if case=='missing':es=(e,);code='SCHEMA_INVALID'
    elif case=='extra':es=(e,e2,e2);code='SCHEMA_INVALID'
    elif case=='duplicate':es=(e,replace(e,evidence_id='other'));code='DUPLICATE_ID'
    elif case=='duplicate_evidence':es=(e,replace(e2,evidence_id=e.evidence_id));code='DUPLICATE_ID'
    else:es=(e,replace(e2,source_pad_id='wrong'))
    failed(b.bind_boundary_declarations(r,es,P),code)

def test_ordering_repeated_numbers():
    r,e,e2=pair()
    a=b.bind_boundary_declarations(r,(e,e2),P)
    assert isinstance(a,b.DeclarationBindingSuccess)
    assert a==b.bind_boundary_declarations(replace(r,pads=tuple(reversed(r.pads))),(e2,e),P)

@pytest.mark.parametrize('change',[{'origin':'other'},{'machine_id':'machine'},{'capture_id':'capture'},{'board_revision_id':'other'}])
def test_full_vertex_frame(change):
    r,e=fixture();frame=replace(e.boundary_frame,**change)
    c=e.contours[0];e=replace(e,contours=(replace(c,vertices=(replace(c.vertices[0],frame=frame),)+c.vertices[1:]),))
    failed(bind(r,e),'CONTEXT_MISMATCH')

@pytest.mark.parametrize('which',['source','target','pad','membership','provenance'])
def test_binding_edges(which):
    r,e=fixture()
    if which=='source':e=replace(e,boundary_frame=replace(e.boundary_frame,origin='other'))
    elif which=='target':r=replace(r,target_frame=replace(r.target_frame,origin='other'))
    elif which=='pad':r=replace(r,pads=(replace(r.pads[0],source_frame=replace(r.pads[0].source_frame,origin='other')),))
    elif which=='membership':e=replace(e,membership=replace(e.membership,source_pad_id='wrong'))
    else:r=replace(r,pads=(replace(r.pads[0],provenance=replace(r.pads[0].provenance,computed_sha256='0'*64)),))
    failed(bind(r,e),'CONTEXT_MISMATCH' if which in ('source','target','pad') else 'SOURCE_CONFLICT')


@pytest.mark.parametrize('case',['rejected_report','inventory_none','artifact_inventory_none','provenance_none','frame_none','transform_none','manifest_none','observation_none','declaration_none','digest','size','eof','manifest_conflict'])
def test_malformed_nested_inventory_and_records(case):
    r,e=fixture();inv=r.inventory;data=inv.inventory;obs=data.artifacts[0]
    if case=='rejected_report':
        issue=b.ContractError(b.ErrorCode.SOURCE_CONFLICT,'Rejected.','inventory','Fix input.')
        r=replace(r,inventory=replace(inv,report=b.ValidationReport('bad','test',(issue,),())))
    elif case=='inventory_none':r=replace(r,inventory=None)
    elif case=='artifact_inventory_none':r=replace(r,inventory=replace(inv,inventory=None))
    elif case=='provenance_none':r=replace(r,pads=(replace(r.pads[0],provenance=None),))
    elif case=='frame_none':r=replace(r,pads=(replace(r.pads[0],source_frame=None),))
    elif case=='transform_none':r=replace(r,parents=(replace(r.parents[0],source_to_p=None),))
    elif case=='manifest_none':r=replace(r,inventory=replace(inv,inventory=replace(data,manifest=None)))
    elif case=='manifest_conflict':r=replace(r,inventory=replace(inv,inventory=replace(data,manifest=replace(data.manifest,artifacts=()))))
    else:
        changed=None if case=='observation_none' else replace(obs,**{'declaration_none':{'declaration':None},'digest':{'computed_sha256':'0'*64},'size':{'actual_size':4},'eof':{'eof':False}}[case])
        r=replace(r,inventory=replace(inv,inventory=replace(data,artifacts=(changed,))))
    result=bind(r,e)
    assert isinstance(result,b.PreflightFailure),result
    assert not hasattr(result,'candidates')


@pytest.mark.parametrize('kind',['entity','artifact','both'])
@pytest.mark.parametrize('conflict',[None,'identity','frame'])
def test_opaque_whitespace_ids_preserved(kind,conflict):
    import json
    r,e=fixture();opaque=' \t\n'.encode().decode('unicode_escape')
    if kind in ('entity','both'):
        r=replace(r,pads=(replace(r.pads[0],pad_id=opaque),))
        e=replace(e,canonical_pad_id=opaque)
    if kind in ('artifact','both'):
        data=r.inventory.inventory;obs=data.artifacts[0]
        decl=replace(obs.declaration,artifact_id=opaque)
        inv=replace(r.inventory,inventory=replace(data,
            manifest=replace(data.manifest,artifacts=(decl,)),
            artifacts=(replace(obs,declaration=decl),)))
        def refs(items):return tuple(replace(x,artifact_id=opaque) for x in items)
        def prov(x):return replace(x,artifact_id=opaque,evidence=refs(x.evidence))
        parent=r.parents[0];pad=r.pads[0]
        r=replace(r,inventory=inv,
            parents=(replace(parent,artifact_id=opaque,convention_evidence=refs(parent.convention_evidence),provenance=prov(parent.provenance)),),
            pads=(replace(pad,artifact_id=opaque,provenance=prov(pad.provenance)),))
        e=replace(e,source=replace(e.source,artifact_id=opaque),
            observation=replace(e.observation,artifact_id=opaque),boundary=replace(e.boundary,artifact_id=opaque))
    assert isinstance(bind(r,e),b.DeclarationBindingSuccess)
    if conflict=='identity':e=replace(e,source_pad_id='conflict')
    elif conflict=='frame':e=replace(e,boundary_frame=replace(e.boundary_frame,origin='conflict'))
    before=repr((r,e));result=bind(r,e)
    assert repr((r,e))==before
    assert not hasattr(result,'candidates')
    if conflict is None:
        assert isinstance(result,b.DeclarationBindingSuccess)
        assert result.bindings==(e,)
    else:
        failed(result,'SOURCE_CONFLICT' if conflict=='identity' else 'CONTEXT_MISMATCH')
        issue=result.report.errors[0];context=dict(issue.context)
        for name,value in (('entity_id',e.canonical_pad_id),('artifact_id',e.source.artifact_id)):
            if value==opaque:
                assert getattr(issue,name) is None
                assert json.loads(context[name+'_json'])==opaque
            else:assert getattr(issue,name)==value
