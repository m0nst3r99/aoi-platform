"""Pinned preparation: literal oracles, real buffers; private fault doubles labelled."""
from dataclasses import fields, is_dataclass, replace, FrozenInstanceError
from enum import Enum
import hashlib
import json
import pytest

import source_checked_preparation as phase
import source_checked_preflight as pre
from test_source_checked_bytes import real
from test_source_checked_boundaries import no_execution
from test_source_checked_preflight import failure


def prepare(args): return phase.prepare_source_checked_pad_request(*args)


def test_complete_receipt_request_and_independent_corners(real,no_execution):
    before=repr(real)
    out=prepare(real)
    assert isinstance(out,pre.PreparedRequest),out
    assert repr(real)==before
    receipt=out.source_check
    assert receipt.status=='selected-source-declarations-checked'
    assert receipt.verifier_id=='c1-c2-source-declaration-checker' and receipt.verifier_version=='1'
    assert len(receipt.artifacts)==8 and len(receipt.pairs)==4
    assert {a.artifact_id:(a.size_bytes,a.sha256) for a in receipt.artifacts}=={
        a.artifact_id:(len(a.data),hashlib.sha256(a.data).hexdigest()) for a in real[0]}
    assert len(out.request.parents)==2 and len(out.request.pads)==len(out.boundary_declarations)==4
    assert out.request.inventory is real[1]
    assert tuple(p.pad_id for p in out.request.pads)==tuple(sorted(p.pad_id for p in out.request.pads))
    oracle={uid:points for _,comp in phase.boundaries.artifacts.profile.GROUPS for uid,points in comp.EXPECTED.items()}
    for b in out.boundary_declarations:
        assert tuple((p.x,p.y) for p in b.contours[0].vertices)==tuple((x/1_000_000,-y/1_000_000) for x,y in oracle[b.source_pad_id])
        assert all(x.status=='unknown' for x in b.coverage)
    raw={a.artifact_id:a.data for a in real[0]}
    for check in receipt.checks:
        assert check.source_pair in pre.PAIRS and check.spans
        json.loads(check.expected_json);json.loads(check.actual_json)
        data=raw[check.artifact_id]
        for span in check.spans:
            assert 0<=span.start_byte<span.end_byte<=len(data)
            assert span.first_line==data[:span.start_byte].count(b'\n')+1
            assert span.last_line==data[:span.end_byte-1].count(b'\n')+1
        if check.artifact_id!='pcb':
            assert check.path[0]=='json-enclosing-pointer:'
            assert check.spans[0].start_byte==0 and check.spans[0].end_byte==len(data)
    assert any(c.path==('source-comparison','request.center.x') for c in receipt.checks)
    assert any(c.result=='semantics-unchecked' for c in receipt.checks)
    assert receipt.normalization and 'effective-copper-geometry' in receipt.unchecked_categories
    assert not hasattr(out,'candidates')


def test_no_duplicate_parse_one_ledger(real,no_execution,monkeypatch):
    ledgers=[];loads=[];original_ledger=pre.Ledger;original_loads=json.loads
    def ledger():
        value=original_ledger();ledgers.append(value);return value
    def load(data,*a,**k):
        loads.append(data);return original_loads(data,*a,**k)
    monkeypatch.setattr(pre,'Ledger',ledger);monkeypatch.setattr(json,'loads',load)
    out=prepare(real)
    assert isinstance(out,pre.PreparedRequest),out
    assert len(ledgers)==1 and ledgers[0].hashed_bytes==1117036
    assert len(loads)==7
    assert sorted(hashlib.sha256(x).hexdigest() for x in loads)==sorted(
        x.sha256 for x in pre.PINS if x.artifact_id!='pcb')
    assert ledgers[0].refs>60


def test_c2_center_conflict_atomic(real,no_execution):
    args=list(real);d=args[2];i=next(i for i,p in enumerate(d.pads) if p.footprint_id=='C2')
    p=d.pads[i]
    changed=replace(p,rectangle=replace(p.rectangle,center=replace(p.rectangle.center,x=p.rectangle.center.x+.001)))
    args[2]=replace(d,pads=d.pads[:i]+(changed,)+d.pads[i+1:])
    out=prepare(args);failure(out,'SOURCE_CONFLICT')
    issue=out.report.errors[0]
    assert issue.field_path=='request.center.x'
    assert 'pose_field_spans' in dict(issue.context)
    assert issue.expected!=issue.actual and args[0] is real[0]


@pytest.mark.parametrize('fault',['missing','lines','bounds','literal'])
def test_internal_span_fault_is_atomic(real,no_execution,monkeypatch,fault):
    # Private malformed scanner metadata, NOT modified PCB admitted through pins.
    original=phase._Receipt.source_check
    def bad(self,r,*args):
        if fault=='missing':r=replace(r,footprint_at=(),pad_at=(),pad_size=())
        else:
            f=r.footprint_at[0]
            r=replace(r,footprint_at=((('999',)+f[0][1:] if fault=='literal' else f[0],(-1,f[1][1]) if fault=='bounds' else f[1],
                                      (0,0) if fault=='lines' else f[2],f[3]),))
        return original(self,r,*args)
    monkeypatch.setattr(phase._Receipt,'source_check',bad)
    failure(prepare(real),'SCHEMA_INVALID')


@pytest.mark.parametrize('resource',['nodes','text_bytes','refs'])
def test_shared_ledger_exact_and_over_budget_private_cap(real,no_execution,monkeypatch,resource):
    # Smaller private cap equals measured operation use; public fixed policy is unchanged.
    ledgers=[];original=pre.Ledger
    def capture():
        l=original();ledgers.append(l);return l
    monkeypatch.setattr(pre,'Ledger',capture)
    assert isinstance(prepare(real),pre.PreparedRequest)
    exact=getattr(ledgers[0],resource)
    field={'nodes':'max_nodes','text_bytes':'max_total_input_utf8_bytes','refs':'max_total_evidence_refs'}[resource]
    for cap,success in ((exact,True),(exact-1,False)):
        def limited():
            l=original();l.p=replace(l.p,**{field:cap});return l
        monkeypatch.setattr(pre,'Ledger',limited)
        out=prepare(real)
        if success:assert isinstance(out,pre.PreparedRequest),out
        else:
            failure(out,'INPUT_LIMIT_EXCEEDED')
            assert out.truncation.occurred and out.truncation.omitted_count is None


def test_determinism_and_deep_immutability(real,no_execution):
    out=prepare(real);assert isinstance(out,pre.PreparedRequest),out
    args=list(real);d=args[2]
    args[0]=tuple(reversed(args[0]));args[2]=replace(d,parents=tuple(reversed(d.parents)),pads=tuple(reversed(d.pads)),boundaries=tuple(reversed(d.boundaries)))
    assert prepare(args)==out
    def walk(v):
        assert not isinstance(v,(list,dict,set,bytearray))
        if is_dataclass(v):
            assert v.__dataclass_params__.frozen
            for f in fields(v):walk(getattr(v,f.name))
        elif isinstance(v,tuple):
            for x in v:walk(x)
    walk(out)
    with pytest.raises(FrozenInstanceError):out.source_check.checks=()


@pytest.mark.parametrize('fault',['scope','translation','side','reference','empty-contours','coverage','membership'])
def test_context_conflicts_no_execution(real,no_execution,fault):
    args=list(real);d=args[2]
    if fault=='scope':args[3]=replace(args[3],candidate_scope_id='other')
    elif fault=='translation':
        p=d.parents[0];t=replace(p.source_to_p,matrix=((1.,0.,1.),(0.,1.,0.),(0.,0.,1.)))
        args[2]=replace(d,parents=(replace(p,source_to_p=t),)+d.parents[1:])
    elif fault=='side':args[2]=replace(d,pads=(replace(d.pads[0],side='bottom'),)+d.pads[1:])
    elif fault=='reference':
        e=d.boundaries[0];args[2]=replace(d,boundaries=(replace(e,auxiliary_evidence=(replace(e.auxiliary_evidence[0],computed_sha256='0'*64),)),)+d.boundaries[1:])
    else:
        e=d.boundaries[0]
        e=(replace(e,contours=()) if fault=='empty-contours' else replace(e,coverage=()) if fault=='coverage'
           else replace(e,membership=replace(e.membership,source_pad_id='wrong')))
        args[2]=replace(d,boundaries=(e,)+d.boundaries[1:])
    out=prepare(args);failure(out)
    assert prepare(args)==out


def test_existing_orchestration_one_candidate_call(real,monkeypatch):
    from aoi_platform import boundary_binding as binding
    out=prepare(real);assert isinstance(out,pre.PreparedRequest),out
    calls=[];original=pre.c.build_rectangular_pad_candidates
    def candidate(request):calls.append(request);return original(request)
    monkeypatch.setattr(pre.c,'build_rectangular_pad_candidates',candidate)
    result=binding.bind_pad_boundaries(out.request,out.boundary_declarations,real[3].boundary_policy)
    assert isinstance(result,binding.BoundaryBindingSuccess),result
    assert len(calls)==1 and len(result.candidates)==4
    assert result.source_membership_status=='not-verified' and not result.import_ready


@pytest.mark.parametrize('value',['\x00\x7f\n"\\','é中😀',{'a':(True,None,-0.0,1e-9)}])
def test_serialization_charge_size_independent(value):
    assert phase._json_size(value)==len(json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':')).encode('ascii'))


def test_duplicate_boundary_evidence_ids_atomic(real,no_execution):
    args=list(real);d=args[2]
    changed=tuple(replace(e,evidence_id='duplicate') for e in d.boundaries)
    args[2]=replace(d,boundaries=changed)
    out=prepare(args);failure(out,'DUPLICATE_ID')
    assert out.report.errors[0].field_path=='evidence_id'
    args[2]=replace(d,boundaries=tuple(reversed(changed)))
    assert prepare(args)==out
    assert not hasattr(out,'source_check') and not hasattr(out,'request')


def test_boundary_vertex_conflict_provenance(real,no_execution):
    args=list(real);d=args[2];e=d.boundaries[0];contour=e.contours[0]
    point=replace(contour.vertices[0],x=contour.vertices[0].x+.001)
    changed=replace(e,contours=(replace(contour,vertices=(point,)+contour.vertices[1:]),))
    args[2]=replace(d,boundaries=(changed,)+d.boundaries[1:])
    out=prepare(args);failure(out,'SOURCE_CONFLICT');assert prepare(args)==out
    issue=out.report.errors[0];context=dict(issue.context)
    raw=next(a.data for a in real[0] if a.artifact_id==e.boundary.artifact_id)
    assert issue.artifact_id==e.boundary.artifact_id and issue.entity_id==e.source_pad_id
    assert context['artifact_sha256']==hashlib.sha256(raw).hexdigest()
    assert context['parent_uuid']==e.source_parent_id and context['pad_uuid']==e.source_pad_id
    assert context['span_kind']=='json-document-enclosing' and context['json_pointer']=='""'
    assert context['comparison_locator']==issue.field_path=='contours[0].vertices[0]'
    assert json.loads(context['enclosing_span'])==[0,len(raw)]
    assert json.loads(context['line_range'])==[1,raw[:-1].count(b'\n')+1]
    assert json.loads(issue.expected)==[contour.vertices[0].x,contour.vertices[0].y]
    assert json.loads(issue.actual)==[point.x,point.y]
    assert not hasattr(out,'source_check') and not hasattr(out,'request')


def test_two_invalid_parents_canonical_diagnostic(real,no_execution):
    args=list(real);d=args[2]
    # Different errors ensure a changed first parent really changes the diagnostic.
    parents=tuple(replace(p,coordinate_basis='footprint-local' if p.footprint_id=='C1' else p.coordinate_basis,
        source_to_p=replace(p.source_to_p,matrix=((1.,0.,1.),(0.,1.,0.),(0.,0.,1.)))
        if p.footprint_id=='C2' else p.source_to_p) for p in d.parents)
    args[2]=replace(d,parents=parents)
    out=prepare(args);failure(out)
    assert out.report.errors[0].field_path=='parent.coordinate_basis'
    args[2]=replace(d,parents=tuple(reversed(parents)))
    assert prepare(args)==out
    args[2]=replace(d,parents=tuple(p if p.footprint_id=='C2' else original
        for p,original in zip(parents,d.parents)))
    other=prepare(args);failure(other)
    assert other.report.errors[0].field_path=='parent.normalized-datum'


def test_independent_artifact_accounting(real,monkeypatch):
    # Isolate byte verification from admission. Eight records each retain one
    # dataclass + three fields; IDs total 78 ASCII bytes; two hashes per record.
    monkeypatch.setattr(pre,'_preflight',lambda *a:None)
    ledger=pre.Ledger();out=pre._verify_bytes(*real,ledger)
    assert isinstance(out,pre.ByteVerificationSuccess)
    assert (ledger.nodes,ledger.text_bytes,ledger.refs)==(32,1102,0)
    assert ledger.hashed_bytes==1117036 and len(ledger.artifacts)==8


def test_independent_reference_accounting():
    # Tuple node + three (record + three string fields); occurrences, not identity.
    ref=pre.c.EvidenceReference('pcb','0'*64,'x')
    other=pre.b.ArtifactRef('pcb','0'*64,'x');ledger=pre.Ledger()
    phase.source._charge(ledger,(ref,other,ref))
    assert (ledger.nodes,ledger.text_bytes,ledger.refs)==(13,204,3)


def test_independent_serialization_accounting(monkeypatch):
    ledger=pre.Ledger();receipt=phase._Receipt(ledger);dump=json.dumps
    def guarded(value,**kwargs):
        # Tuple + 3 scalar nodes; one source byte + 15 serialized ASCII bytes.
        assert (ledger.nodes,ledger.text_bytes,ledger.refs)==(4,16,0)
        return dump(value,**kwargs)
    monkeypatch.setattr(json,'dumps',guarded)
    assert receipt._json(('a',True,None))=='["a",true,null]'


def test_independent_failure_diagnostic_reservation():
    # Independent wire envelope oracle, not _Issues.used or a measured ledger.
    envelope=dict(code='SOURCE_CONFLICT',message='m',field_path='f',remediation='r',
        severity='error',artifact_id=None,entity_id=None,expected='',actual=None,
        context={},source_location=None)
    overhead=len(json.dumps(envelope,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
    for size in (4096,4097):
        issue=pre.ContractError(pre.ErrorCode.SOURCE_CONFLICT,'m','f','r',expected='x'*(size-overhead))
        out=phase.source._failure(issue)
        if size==4096:
            assert out.report.errors==(issue,) and not out.truncation.occurred
        else:
            failure(out,'INPUT_LIMIT_EXCEEDED')
            assert out.truncation.occurred and out.truncation.reason=='issue_bytes'
