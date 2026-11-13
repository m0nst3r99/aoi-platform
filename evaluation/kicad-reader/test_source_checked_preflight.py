"""Structural test doubles are NOT real byte admission or source verification."""
from dataclasses import replace, fields, FrozenInstanceError
from pathlib import Path
import sys
import pytest
import source_checked_preflight as s
from aoi_platform.inventory import ArtifactDeclaration, ArtifactObservation, ArtifactInventory, InventoryManifest, InventorySuccess
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tests'))
from test_boundary_preflight import fixture


def inputs():
    r,e=fixture(); parents=[]; pads=[]; boundaries=[]
    for i,pair in enumerate(s.PAIRS):
        parent_id='C1' if i<2 else 'C2'
        prov=replace(r.pads[0].provenance,source_id='pcb',computed_sha256=s.PINS[0].sha256)
        if i%2==0:
            parents.append(replace(r.parents[0],footprint_id=parent_id,source_entity_id=pair.parent_uuid,
                provenance=replace(prov,source_entity_id=pair.parent_uuid)))
        pads.append(replace(r.pads[0],pad_id=pair.pad_uuid,footprint_id=parent_id,
            source_entity_id=pair.pad_uuid,source_parent_entity_id=pair.parent_uuid,
            provenance=replace(prov,source_entity_id=pair.pad_uuid)))
        boundaries.append(replace(e,evidence_id=str(i),canonical_parent_id=parent_id,
            canonical_pad_id=pair.pad_uuid,source_parent_id=pair.parent_uuid,source_pad_id=pair.pad_uuid))
    decls=tuple(ArtifactDeclaration(p.artifact_id,'kicad_pcb' if p.artifact_id=='pcb' else 'supporting',
        p.artifact_id,p.sha256,p.size_bytes,reference_only=p.artifact_id!='pcb') for p in s.PINS)
    inv=InventorySuccess(ArtifactInventory(InventoryManifest('geometry',decls,'synthetic-r1','snapshot'),
        tuple(ArtifactObservation(d,d.declared_size,True,d.declared_size,d.declared_sha256) for d in decls)),r.inventory.report)
    raw=tuple(s.AdmittedArtifactBytes(p.artifact_id,bytes(p.size_bytes)) for p in s.PINS)
    context=s.CallerContext(r.schema_version,r.board_id,r.candidate_scope_id,r.target_frame,s.C_POLICY,s.B_POLICY)
    return raw,inv,s.SourceDeclarations(tuple(parents),tuple(pads),tuple(boundaries)),context,s.PROFILE,s.LIMITS


def run(args): return s.preflight_source_checked_request(*args)
def failure(result,code=None):
    assert isinstance(result,s.PreparationFailure),result
    if code: assert result.report.errors[0].code.value==code
    for name in ('candidates','request','source_check','boundary_declarations'): assert not hasattr(result,name)


def test_positive_profile_no_execution(monkeypatch):
    a=inputs()
    def forbidden(*args): pytest.fail('execution forbidden')
    monkeypatch.setattr(s.c,'build_rectangular_pad_candidates',forbidden)
    monkeypatch.setattr(s.b,'bind_boundary_declarations',forbidden)
    monkeypatch.setattr(s.b,'preflight_boundary_evidence',forbidden)
    result=run(a)
    assert isinstance(result,s.PreparationPreflightSuccess),result
    assert result.raw_bytes==1117036
    assert result.status=='preflight-only-bytes-not-hash-verified'
    assert not hasattr(result,'source_check')
    with pytest.raises(FrozenInstanceError):result.raw_bytes=0
    with pytest.raises(FrozenInstanceError):a[0][0].artifact_id='changed'
    assert run((tuple(reversed(a[0])),a[1],a[2],a[3],replace(a[4],pins=tuple(reversed(s.PINS)),pairs=tuple(reversed(s.PAIRS))),a[5]))==result


@pytest.mark.parametrize('which',range(6))
@pytest.mark.parametrize('bad',[None,[],{},True])
def test_top_level_malformed(which,bad):
    a=list(inputs());a[which]=bad;failure(run(a))


@pytest.mark.parametrize('which',['provenance','rectangle','frame','transform','inventory','metadata','membership','contour','coverage','mutable_bytes'])
def test_nested_malformed(which):
    a=list(inputs());d=a[2]
    if which in ('provenance','rectangle','frame'):
        key={'frame':'source_frame'}.get(which,which)
        a[2]=replace(d,pads=(replace(d.pads[0],**{key:None}),)+d.pads[1:])
    elif which=='transform':a[2]=replace(d,parents=(replace(d.parents[0],source_to_p=None),)+d.parents[1:])
    elif which=='inventory':a[1]=replace(a[1],inventory=None)
    elif which=='metadata':
        inv=a[1].inventory; decl=replace(inv.manifest.artifacts[0],metadata=((None,'x'),))
        a[1]=replace(a[1],inventory=replace(inv,manifest=replace(inv.manifest,artifacts=(decl,)+inv.manifest.artifacts[1:])))
    elif which=='mutable_bytes':a[0]=(replace(a[0][0],data=bytearray(1)),)+a[0][1:]
    else:
        key={'contour':'contours','coverage':'coverage','membership':'membership'}[which]
        value=None if which=='membership' else (None,)
        a[2]=replace(d,boundaries=(replace(d.boundaries[0],**{key:value}),)+d.boundaries[1:])
    failure(run(a),'SCHEMA_INVALID')


@pytest.mark.parametrize('which',['missing','extra','duplicate','unknown','pin','pair','pair_duplicate','size','hash_inventory'])
def test_identity_and_pins(which):
    a=list(inputs())
    if which=='missing':a[0]=a[0][:-1]
    if which=='extra':a[0]+= (a[0][0],)
    if which=='duplicate':a[0]=a[0][:-1]+(a[0][0],)
    if which=='unknown':a[0]=(replace(a[0][0],artifact_id='unknown'),)+a[0][1:]
    if which=='pin':a[4]=replace(a[4],pins=(replace(s.PINS[0],sha256='0'*64),)+s.PINS[1:])
    if which=='pair':a[4]=replace(a[4],pairs=(replace(s.PAIRS[0],parent_uuid='wrong'),)+s.PAIRS[1:])
    if which=='pair_duplicate':a[4]=replace(a[4],pairs=s.PAIRS[:-1]+(s.PAIRS[0],))
    if which=='size':a[0]=(replace(a[0][0],data=a[0][0].data[:-1]),)+a[0][1:]
    if which=='hash_inventory':
        inv=a[1].inventory;a[1]=replace(a[1],inventory=replace(inv,artifacts=(replace(inv.artifacts[0],computed_sha256='0'*64),)+inv.artifacts[1:]))
    failure(run(a))


@pytest.mark.parametrize('field',fields(s.PreparationLimits),ids=lambda f:f.name)
def test_exact_limits(field):
    a=list(inputs());value=getattr(a[5],field.name)
    a[5]=replace(a[5],**{field.name: True if type(value) is int else None})
    failure(run(a),'POLICY_INVALID')


@pytest.mark.parametrize('policy,expected', [('candidate_policy',s.C_POLICY),('boundary_policy',s.B_POLICY)])
def test_every_policy_field(policy,expected):
    for f in fields(expected):
        a=list(inputs());v=getattr(expected,f.name)
        bad='wrong' if type(v) is str else (True if type(v) is int else v+1.)
        a[3]=replace(a[3],**{policy:replace(expected,**{f.name:bad})})
        failure(run(a),'POLICY_INVALID')


@pytest.mark.parametrize('field,cap',[('nodes',2686976),('text_bytes',8388608),('refs',32768),('raw_bytes',1117036)])
def test_exact_exceeded_ledger_primitive(field,cap):
    # Counter primitive, not a claim that a full profile reaches this exact budget.
    ledger=s.Ledger();ledger.take(field,cap,cap)
    with pytest.raises(s.b._Reject) as error:ledger.take(field,1,cap)
    assert error.value.code is s.ErrorCode.INPUT_LIMIT_EXCEEDED


def test_joint_text_and_unicode_boundary():
    ledger=s.Ledger();ledger.walk(((chr(0xE9)*128,str,'id'),))
    assert ledger.text_bytes==256
    with pytest.raises(s.b._Reject):ledger.walk((('x'*257,str,'id'),))
    ledger=s.Ledger();ledger.take('text_bytes',8388607,8388608)
    ledger.walk((('x',str,'id'),))
    with pytest.raises(s.b._Reject):ledger.walk((('x',str,'id'),))


def test_full_preflight_raw_overflow_terminal_failure():
    a=list(inputs());a[0]=(replace(a[0][0],data=a[0][0].data+b'x'),)+a[0][1:]
    result=run(a);failure(result,'INPUT_LIMIT_EXCEEDED')
    assert result.truncation.occurred
    assert len(result.report.errors)==1
    assert len(result.report.to_json().encode())<4096


def test_full_preflight_metadata_boundary():
    a=list(inputs());a[3]=replace(a[3],board_id=chr(0xE9)*128)
    assert isinstance(run(a),s.PreparationPreflightSuccess)
    a[3]=replace(a[3],board_id=a[3].board_id+'x');failure(run(a),'INPUT_LIMIT_EXCEEDED')


def test_real_admission_optional():
    import os
    if not os.environ.get('AOI_C2_R2_PCB'):pytest.skip('External pinned PCB not supplied; no fake admission fallback')
    from test_c1_c2_boundary_binding import admitted_request
    r,e,_,_,raw=admitted_request()
    result=run((tuple(s.AdmittedArtifactBytes(k,v) for k,v in raw.items()),r.inventory,
        s.SourceDeclarations(r.parents,r.pads,e),s.CallerContext(r.schema_version,r.board_id,
        r.candidate_scope_id,r.target_frame,s.C_POLICY,s.B_POLICY),s.PROFILE,s.LIMITS))
    assert isinstance(result,s.PreparationPreflightSuccess),result


def test_declared_hashes_are_not_byte_verification():
    # Zero-filled bytes have pinned lengths, NOT pinned digests. Preflight is structural.
    a=inputs();result=run(a)
    assert isinstance(result,s.PreparationPreflightSuccess)
    import hashlib
    assert hashlib.sha256(a[0][0].data).hexdigest()!=s.PINS[0].sha256
    assert not hasattr(result,'request') and not hasattr(result,'source_check')


def test_shared_reference_ledger():
    ref=s.b.ArtifactRef('pcb',s.PINS[0].sha256,'locator')
    ledger=s.Ledger()
    ledger.walk(((ref,s.b.ArtifactRef,'ref'),(ref,s.b.ArtifactRef,'ref')))
    assert ledger.refs==2
    assert ledger.text_bytes==2*(3+64+7)
    ledger.take('refs',32766,32768)
    with pytest.raises(s.b._Reject):ledger.walk(((ref,s.b.ArtifactRef,'ref'),))


def test_depth_boundary():
    value=None; annotation=type(None)
    for _ in range(32):value=(value,);annotation=tuple[annotation]
    s.Ledger().walk(((value,annotation,'nested'),))
    with pytest.raises(s.b._Reject):s.Ledger().walk((((value,),tuple[annotation],'nested'),))


def test_missing_slot_fails_structurally():
    a=list(inputs());record=object.__new__(s.SourceDeclarations);a[2]=record
    failure(run(a),'SCHEMA_INVALID')


def test_rejected_inventory():
    a=list(inputs())
    issue=s.ContractError(s.ErrorCode.SOURCE_CONFLICT,'Rejected inventory.','inventory','Correct inventory.')
    a[1]=replace(a[1],report=s.ValidationReport('inventory','test',(issue,),()))
    failure(run(a),'SOURCE_CONFLICT')
