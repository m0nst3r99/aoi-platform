"""Byte phase, real pinned buffers; no native or source scanning."""
from dataclasses import replace
import hashlib
import os
import pytest
import source_checked_preflight as s
from test_source_checked_preflight import inputs, failure

@pytest.fixture
def real():
    if not os.environ.get('AOI_C2_R2_PCB'):pytest.skip('Pinned external PCB required; no synthetic fallback')
    from test_c1_c2_boundary_binding import admitted_request
    r,e,_,_,raw=admitted_request()
    return (tuple(s.AdmittedArtifactBytes(k,v) for k,v in raw.items()),r.inventory,
        s.SourceDeclarations(r.parents,r.pads,e),s.CallerContext(r.schema_version,r.board_id,
        r.candidate_scope_id,r.target_frame,s.C_POLICY,s.B_POLICY),s.PROFILE,s.LIMITS)


def test_real_eight_buffers_same_ledger(real,monkeypatch):
    baseline=s.preflight_source_checked_request(*real)
    ledgers=[];calls=[];original=s.Ledger;hashfn=s.sha256
    def ledger():
        value=original();ledgers.append(value);return value
    def digest(data):calls.append(data);return hashfn(data)
    monkeypatch.setattr(s,'Ledger',ledger);monkeypatch.setattr(s,'sha256',digest)
    result=s.verify_source_checked_bytes(*real)
    assert isinstance(result,s.ByteVerificationSuccess),result
    assert len(ledgers)==1 and len(calls)==8
    assert all(data is item.data for data,item in zip(calls,sorted(real[0],key=lambda x:x.artifact_id)))
    assert result.hashed_bytes==result.raw_bytes==1117036
    assert result.nodes==baseline.nodes and result.evidence_refs==baseline.evidence_refs
    assert result.text_bytes==baseline.text_bytes+8*64==ledgers[0].text_bytes
    assert result.status=='bytes-match-pins-and-inventory-only'
    for name in ('request','source_check','candidates'):assert not hasattr(result,name)
    assert s.verify_source_checked_bytes(tuple(reversed(real[0])),*real[1:])==result


@pytest.mark.parametrize('artifact',[p.artifact_id for p in s.PINS])
def test_each_same_size_single_byte_mutation(real,artifact):
    raw=tuple(replace(x,data=bytes([x.data[0]^1])+x.data[1:]) if x.artifact_id==artifact else x for x in real[0])
    assert isinstance(s.preflight_source_checked_request(raw,*real[1:]),s.PreparationPreflightSuccess)
    result=s.verify_source_checked_bytes(raw,*real[1:]);failure(result,'SOURCE_CONFLICT')
    issue=result.report.errors[0];assert issue.artifact_id==artifact
    item=next(x for x in raw if x.artifact_id==artifact)
    assert issue.actual==hashlib.sha256(item.data).hexdigest()
    assert issue.expected==next(p.sha256 for p in s.PINS if p.artifact_id==artifact)


@pytest.mark.parametrize('bad',['missing','policy','inventory_hash','inventory_size'])
def test_preflight_failure_blocks_hash(bad,monkeypatch):
    a=list(inputs())
    if bad=='missing':a[0]=a[0][:-1]
    elif bad=='policy':a[5]=replace(a[5],max_total_bytes=True)
    else:
        inv=a[1].inventory;obs=inv.artifacts[0]
        obs=replace(obs,**({'computed_sha256':'0'*64} if bad=='inventory_hash' else {'actual_size':1}))
        a[1]=replace(a[1],inventory=replace(inv,artifacts=(obs,)+inv.artifacts[1:]))
    monkeypatch.setattr(s,'sha256',lambda *_:pytest.fail('hash called after rejected preflight'))
    failure(s.verify_source_checked_bytes(*a))


def test_zero_filled_is_preflight_only():
    a=inputs();assert isinstance(s.preflight_source_checked_request(*a),s.PreparationPreflightSuccess)
    failure(s.verify_source_checked_bytes(*a),'SOURCE_CONFLICT')


def test_hash_phase_cannot_reset_metadata_budget(real,monkeypatch):
    original=s._preflight
    def at_limit(*args):
        result=original(*args);args[-1].text_bytes=8388608;return result
    monkeypatch.setattr(s,'_preflight',at_limit)
    result=s.verify_source_checked_bytes(*real)
    failure(result,'INPUT_LIMIT_EXCEEDED');assert result.truncation.occurred
