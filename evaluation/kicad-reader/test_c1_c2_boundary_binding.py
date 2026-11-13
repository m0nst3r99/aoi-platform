"""Pinned real inventory integration; altered declaration is not altered admitted bytes."""
from dataclasses import replace
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import pytest
import c1_c2_replay_batch as replay
from aoi_platform.boundary_binding import bind_pad_boundaries, BoundaryBindingSuccess
from aoi_platform.boundary_evidence import (ArtifactRef, BoundaryEvidence, BoundaryContour,
    ConstructCoverage, MembershipEvidence, BoundaryBindingPolicy, CATEGORIES, _POLICY, PreflightFailure)

ROOT=Path(__file__).resolve().parents[2]


def admitted_request():
    source=os.environ.get('AOI_C2_R2_PCB')
    assert source, 'AOI_C2_R2_PCB required: no fake inventory fallback'
    paths={'pcb':Path(source),'observation':ROOT/'evaluation/windows_runner/evidence/c1-strict-native-01/stdout.bin'}
    for group in ('C1','C2'):
        folder=ROOT/('evaluation/windows_runner/evidence/'+group.lower()+'-boundary-native-01')
        for key,name in (('boundary','stdout.bin'),('report','report.json'),('transport','transport.json')):
            paths[group+'_'+key]=folder/name
    raw={}
    for key,digest,size in replay.PINS:
        with paths[key].open('rb') as stream:raw[key]=stream.read(size+1)
        assert len(raw[key])==size and hashlib.sha256(raw[key]).hexdigest()==digest
    streams=[]
    def opening(data):
        def open_stream():
            stream=BytesIO(data);streams.append(stream);return stream
        return open_stream
    inventory=replay.inventory_artifacts(replay.InventoryManifest('geometry',tuple(
        replay.ArtifactDeclaration(k,'kicad_pcb' if k=='pcb' else 'supporting',k,h,n,reference_only=k!='pcb')
        for k,h,n in replay.PINS),'REAL-PCB-01-r2','accepted-snapshot'),
        {k:opening(v) for k,v in raw.items()},replay.InventoryLimits(replay.PROFILE_ID,8,2*1024**2,4*1024**2,65536))
    assert isinstance(inventory,replay.InventorySuccess)
    assert len(streams)==8 and all(s.closed for s in streams)
    assert {a.declaration.artifact_id:(a.computed_sha256,a.actual_size) for a in inventory.inventory.artifacts}=={k:(h,n) for k,h,n in replay.PINS}
    # Reuse accepted replay gates/request construction, but intercept before its
    # candidate call: no candidates are built here and no historical result fallback.
    captured=[]
    class RequestCaptured(Exception):pass
    def capture(request):
        captured.append(request);raise RequestCaptured
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(replay,'build_rectangular_pad_candidates',capture)
        with pytest.raises(RequestCaptured):replay._evaluate_admitted(raw,inventory)
    assert len(captured)==1
    request=captured[0];evidence=[];expected={}
    hashes={k:h for k,h,n in replay.PINS}
    for group,comparator in replay.GROUPS:
        boundary=json.loads(raw[group+'_boundary'])
        parent=next(p for p in request.parents if p.footprint_id==group)
        def ref(key,locator):return ArtifactRef(key,hashes[key],locator)
        for pad in boundary['pads']:
            uid=pad['uuid'];expected[uid]=comparator.EXPECTED[uid]
            contour=pad['contours'][0]
            # Raw native order retained; explicit N(x,y)=(x,-y), IU to mm.
            vertices=tuple(replay.Point2(x/1e6,-y/1e6,parent.source_frame) for x,y in contour['vertices_iu'])
            evidence.append(BoundaryEvidence('boundary:'+uid,ref('pcb',uid),ref('observation',uid),
                ref(group+'_boundary',uid),tuple(ref(group+'_'+k,k) for k in ('report','transport')),
                group,uid,comparator.PARENT,uid,parent.source_frame,parent.source_to_p,
                'board-source-normalized',(BoundaryContour(vertices,True,contour['hole_count']),),
                'F.Cu','top','pcbnew','10.0.7','C1-C2-pinned-boundary',
                tuple(ConstructCoverage(c,'unknown','caller-declaration','',()) for c in CATEGORIES),
                MembershipEvidence(comparator.PARENT,uid,(),None,None)))
    assert len(evidence)==4
    return request,tuple(evidence),expected,paths,raw


@pytest.mark.parametrize('deviate_c2',[False,True])
def test_pinned_real_batch_binding(deviate_c2):
    request,evidence,oracle,paths,raw=admitted_request()
    if deviate_c2:
        # Supplied declaration mutation AFTER real pin admission, not a hash-gate
        # test or claim of verified artifact-to-record membership.
        index=next(i for i,e in enumerate(evidence) if e.canonical_parent_id=='C2')
        e=evidence[index];c=e.contours[0]
        changed=replace(e,contours=(replace(c,vertices=tuple(replace(p,x=p.x+0.01) for p in c.vertices)),))
        evidence=evidence[:index]+(changed,)+evidence[index+1:]
    before=repr((request,evidence))
    result=bind_pad_boundaries(request,evidence,BoundaryBindingPolicy(*_POLICY))
    assert repr((request,evidence))==before
    assert raw=={k:p.read_bytes() for k,p in paths.items()}
    if deviate_c2:
        assert isinstance(result,PreflightFailure),result
        assert not hasattr(result,'candidates')
        assert any(e.code.value=='SOURCE_CONFLICT' and e.message=='no_match' for e in result.report.errors)
    else:
        assert isinstance(result,BoundaryBindingSuccess),result
        assert len(result.candidates)==len(result.bindings)==4
        assert {c.pad_id for c in result.candidates}==set(oracle)
        for candidate in result.candidates:
            for i,j in enumerate((3,2,1,0)):
                x,y=oracle[candidate.pad_id][i]
                assert (candidate.vertices[j].x,candidate.vertices[j].y)==pytest.approx((x/1e6,-y/1e6),abs=1e-6,rel=0)
        assert all(b.unknown_categories==CATEGORIES for b in result.bindings)
        assert result.association_status=='declaration-consistent'
        assert result.source_membership_status=='not-verified'
        assert not result.import_ready and not result.published and not result.targeting_authorized
