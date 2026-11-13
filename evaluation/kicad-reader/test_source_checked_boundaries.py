"""Real admitted buffers; private budget/link doubles are labelled separately."""
from dataclasses import replace, FrozenInstanceError
import json
import pytest
import source_checked_boundaries as phase
import source_checked_preflight as pre
from test_source_checked_bytes import real
from test_source_checked_preflight import failure


@pytest.fixture
def no_execution(monkeypatch):
    import aoi_platform.boundary_binding as binding
    import c1_c2_replay_batch as replay
    def forbidden(*a,**k):pytest.fail('binding/candidate execution must not run')
    monkeypatch.setattr(phase.artifacts,'bind_pad_boundaries',forbidden)
    monkeypatch.setattr(phase.artifacts,'evaluate_artifact_boundaries',forbidden)
    monkeypatch.setattr(binding,'bind_pad_boundaries',forbidden)
    monkeypatch.setattr(binding.candidate,'build_rectangular_pad_candidates',forbidden)
    monkeypatch.setattr(pre.c,'build_rectangular_pad_candidates',forbidden)
    monkeypatch.setattr(replay,'build_rectangular_pad_candidates',forbidden)


def test_real_positive_four_raw_records_links_shared_ledger(real,no_execution,monkeypatch):
    ledgers=[];original=pre.Ledger
    def ledger():
        value=original();ledgers.append(value);return value
    monkeypatch.setattr(pre,'Ledger',ledger)
    before=repr(real)
    result=phase.check_boundary_records(*real)
    assert isinstance(result,phase.BoundaryRecordCheckSuccess),result
    assert len(ledgers)==1 and result.hashed_bytes==1117036
    assert result.nodes==ledgers[0].nodes>result.source_result.nodes
    assert result.text_bytes==ledgers[0].text_bytes>result.source_result.text_bytes
    assert result.evidence_refs==ledgers[0].refs
    assert len(result.records)==4 and len(result.links)==2
    raw={a.artifact_id:a.data for a in real[0]}
    oracle={uid:points for _,comp in phase.artifacts.profile.GROUPS for uid,points in comp.EXPECTED.items()}
    for record in result.records:
        payload=json.loads(raw[record.artifact_id])
        row=next(p for p in payload['pads'] if p['uuid']==record.pad_uuid)
        assert record.parent_uuid==row['parent_uuid']
        assert record.raw_vertices_iu==tuple(map(tuple,row['contours'][0]['vertices_iu']))
        assert record.normalized_vertices_mm==tuple((x/1e6,-y/1e6) for x,y in record.raw_vertices_iu)
        # This pinned raw order matches the separately authored literal oracle.
        assert record.raw_vertices_iu==tuple(map(tuple,oracle[record.pad_uuid]))
        assert record.layer=='F.Cu' and record.closed and record.hole_count==0
    pins={p.artifact_id:p.sha256 for p in pre.PINS}
    for link in result.links:
        assert link.boundary_sha256==pins[link.boundary_id]
        assert link.report_sha256==pins[link.report_id]
        assert link.transport_sha256==pins[link.transport_id]
        assert link.source_sha256==pins['pcb']
    assert repr(real)==before
    assert result.completeness==result.effective_copper_geometry=='not-verified'
    for name in ('request','source_check','candidates','binding'):assert not hasattr(result,name)
    with pytest.raises(FrozenInstanceError):result.records=()
    with pytest.raises(FrozenInstanceError):result.records[0].raw_vertices_iu=()


def test_c2_vertex_declaration_conflict_artifacts_unchanged(real,no_execution):
    args=list(real);d=args[2]
    i=next(i for i,b in enumerate(d.boundaries) if b.canonical_parent_id=='C2')
    item=d.boundaries[i];contour=item.contours[0];point=contour.vertices[0]
    changed=replace(point,x=point.x+.001)
    altered=replace(item,contours=(replace(contour,vertices=(changed,)+contour.vertices[1:]),))
    args[2]=replace(d,boundaries=d.boundaries[:i]+(altered,)+d.boundaries[i+1:])
    result=phase.check_boundary_records(*args);failure(result,'SOURCE_CONFLICT')
    issue=result.report.errors[0];context={k:json.loads(v) for k,v in issue.context}
    assert issue.field_path=='contours[0].vertices[0]'
    assert issue.expected==repr((point.x,point.y)) and issue.actual==repr((changed.x,changed.y))
    assert context['artifact_id_json']=='C2_boundary'
    assert context['artifact_sha256']==item.boundary.computed_sha256
    assert context['parent_uuid']==item.source_parent_id and context['pad_uuid']==item.source_pad_id
    assert args[0] is real[0]


def test_source_conflict_stops_all_boundary_checks(real,no_execution,monkeypatch):
    args=list(real);d=args[2];i=next(i for i,p in enumerate(d.pads) if p.footprint_id=='C2')
    pad=d.pads[i]
    altered=replace(pad,rectangle=replace(pad.rectangle,center=replace(pad.rectangle.center,x=pad.rectangle.center.x+.001)))
    args[2]=replace(d,pads=d.pads[:i]+(altered,)+d.pads[i+1:])
    monkeypatch.setattr(phase,'_links_from_verified',lambda *a:pytest.fail('boundary links reached'))
    monkeypatch.setattr(phase.artifacts,'_records_from_verified',lambda *a,**k:pytest.fail('boundary records reached'))
    failure(phase.check_boundary_records(*args),'SOURCE_CONFLICT')


@pytest.mark.parametrize('artifact',[p.artifact_id for p in pre.PINS])
def test_hash_failure_stops_boundary_phase(real,no_execution,monkeypatch,artifact):
    args=list(real)
    args[0]=tuple(replace(a,data=bytes([a.data[0]^1])+a.data[1:]) if a.artifact_id==artifact else a for a in args[0])
    monkeypatch.setattr(phase,'_links_from_verified',lambda *a:pytest.fail('boundary after hash failure'))
    failure(phase.check_boundary_records(*args),'SOURCE_CONFLICT')


@pytest.mark.parametrize('target',['links','records'])
def test_shared_budget_blocks_before_retained_record(real,no_execution,monkeypatch,target):
    # Private ledger exhaustion double, not full-profile admission at the cap.
    if target=='links':
        original=phase.source._check_source
        def fill(*args):
            result=original(*args);args[-1].text_bytes=8388608;return result
        monkeypatch.setattr(phase.source,'_check_source',fill)
        monkeypatch.setattr(phase,'BoundaryArtifactLink',lambda *a:pytest.fail('unbudgeted link'))
    else:
        original=phase._links_from_verified
        def fill(raw,ledger):
            result=original(raw,ledger);ledger.text_bytes=8388608;return result
        monkeypatch.setattr(phase,'_links_from_verified',fill)
        monkeypatch.setattr(phase.artifacts,'ObservedBoundaryRecord',lambda *a:pytest.fail('unbudgeted record'))
    result=phase.check_boundary_records(*real)
    failure(result,'INPUT_LIMIT_EXCEEDED');assert result.truncation.occurred


@pytest.mark.parametrize('case',['report_hash','transport_cleanup','transport_exit','stdout_size'])
def test_private_link_mismatch_double(real,case):
    # Bypasses byte gate ONLY to exercise link semantics; not admitted mutation.
    raw={a.artifact_id:a.data for a in real[0]}
    key='C2_report' if case=='report_hash' else 'C2_transport'
    payload=json.loads(raw[key])
    if case=='report_hash':payload['output_hashes']['stdout.bin']='0'*64
    elif case=='transport_cleanup':payload['result']['evidence']['cleanup_state']='unknown'
    elif case=='transport_exit':payload['result']['evidence']['root_exit']=False
    else:payload['result']['evidence']['observed_stdout']-=1
    raw[key]=json.dumps(payload).encode()
    failure(phase._links_from_verified(raw,pre.Ledger()),'SOURCE_CONFLICT')
