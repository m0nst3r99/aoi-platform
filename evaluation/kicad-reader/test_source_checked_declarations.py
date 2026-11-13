from dataclasses import replace
import pytest
import source_checked_declarations as phase
import source_checked_preflight as pre
from test_source_checked_bytes import real
from test_source_checked_preflight import failure


def test_real_positive_shared_ledger_no_binding(real,monkeypatch):
    def forbidden(*a,**k):pytest.fail('later phase called')
    monkeypatch.setattr(phase.source.artifacts,'evaluate_artifact_boundaries',forbidden)
    monkeypatch.setattr(pre.c,'build_rectangular_pad_candidates',forbidden)
    calls=[];original=pre.Ledger
    def ledger():
        value=original();calls.append(value);return value
    monkeypatch.setattr(pre,'Ledger',ledger)
    result=phase.check_source_declarations(*real)
    assert isinstance(result,phase.SourceDeclarationCheckSuccess),result
    assert len(calls)==1 and result.text_bytes==calls[0].text_bytes
    assert len(result.records)==len(result.poses)==4 and result.hashed_bytes==1117036
    from test_c1_c2_boundary_binding import replay
    oracle={uid:vertices for _,comp in replay.GROUPS for uid,vertices in comp.EXPECTED.items()}
    for record,pose in zip(result.records,result.poses):
        assert record.pad_type=='smd' and record.shape=='rect'
        assert all(m.status=='absent' for m in record.modifiers)
        assert record.nodes and record.footprint_nodes
        for vertex,(x,y) in zip(pose.p_vertices,oracle[record.pad_uuid]):
            assert float(vertex[0])==pytest.approx(x/1e6,abs=1e-6,rel=0)
            assert float(vertex[1])==pytest.approx(-y/1e6,abs=1e-6,rel=0)
    assert result.completeness==result.effective_copper_geometry=='not-verified'
    assert not hasattr(result,'candidates') and not hasattr(result,'source_check')


def test_c2_pose_conflict_stops_before_later_phase(real,monkeypatch):
    a=list(real);d=a[2];i=next(i for i,p in enumerate(d.pads) if p.footprint_id=='C2')
    pad=d.pads[i];bad=replace(pad,rectangle=replace(pad.rectangle,center=replace(pad.rectangle.center,x=pad.rectangle.center.x+.001)))
    a[2]=replace(d,pads=d.pads[:i]+(bad,)+d.pads[i+1:])
    monkeypatch.setattr(phase,'source_pose',lambda *_:pytest.fail('post-check result collection reached'))
    monkeypatch.setattr(phase.source.artifacts,'evaluate_artifact_boundaries',lambda *_:pytest.fail('binding flow called'))
    result=phase.check_source_declarations(*a);failure(result,'SOURCE_CONFLICT')
    issue=result.report.errors[0]
    assert issue.field_path=='request.center.x' and issue.expected!=issue.actual
    assert 'pose_field_spans' in dict(issue.context)


@pytest.mark.parametrize('artifact',[p.artifact_id for p in pre.PINS])
def test_any_hash_failure_stops_scanner(real,artifact,monkeypatch):
    a=list(real);a[0]=tuple(replace(x,data=bytes([x.data[0]^1])+x.data[1:]) if x.artifact_id==artifact else x for x in a[0])
    monkeypatch.setattr(phase.source,'_scan_checked',lambda *a,**k:pytest.fail('scanner called'))
    failure(phase.check_source_declarations(*a),'SOURCE_CONFLICT')


def test_budget_charge_precedes_source_record_storage(real,monkeypatch):
    original=pre._verify_bytes
    def full(*args):
        result=original(*args);args[-1].text_bytes=8388608;return result
    monkeypatch.setattr(pre,'_verify_bytes',full)
    monkeypatch.setattr(phase.source,'FootprintNodeDeclaration',lambda *a:pytest.fail('record stored before charge'))
    result=phase.check_source_declarations(*real)
    failure(result,'INPUT_LIMIT_EXCEEDED');assert result.truncation.occurred
