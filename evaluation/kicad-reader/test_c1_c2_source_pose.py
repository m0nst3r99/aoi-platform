"""Source-only Decimal expected geometry; real pin and memory-only request conflict."""
from dataclasses import replace
from decimal import Decimal
import json
import pytest
import c1_c2_source_membership as source
import c1_c2_source_pose as pose
from test_c1_c2_boundary_binding import admitted_request
from aoi_platform.boundary_evidence import BoundaryBindingPolicy,_POLICY


def test_real_source_pose_oracles_and_binding():
    request,evidence,oracle,paths,raw = admitted_request()
    records = source.scan_pinned(raw['pcb'])
    centers = {
        'e2743daf-d278-4538-a77e-8f62f1b7978c':('192.849','-62.0160'),
        '4e53dd71-4be4-4973-9c48-191e7b2e27bb':('192.849','-68.5184'),
        '21e4d927-86ab-439d-8b84-9241bc089b89':('155.956','-71.3232'),
        'fc38c22a-efcb-4dfc-b42c-80a66f75e1a4':('155.956','-64.8208'),
    }
    for r in records:
        result = pose.source_pose(r)
        assert result.p_center == tuple(map(Decimal,centers[r.pad_uuid]))
        assert result.size == (Decimal('3.50012'),Decimal('2.4003'))
        assert result.pad_at[2] == (90 if r.parent_uuid.endswith('82c8') else 270)
        assert result.footprint_at[2] == (90 if r.parent_uuid.endswith('82c8') else -90)
        assert result.correspondence == (3,2,1,0)
        for actual,(x,y) in zip(result.p_vertices,oracle[r.pad_uuid]):
            expected = (Decimal(x)/1000000,-Decimal(y)/1000000)
            assert max(abs(a-b) for a,b in zip(actual,expected)) <= Decimal('0.000001')
        for name,fields in (('at',r.footprint_at),('at',r.pad_at),('size',r.pad_size)):
            literals,span,lines,nested = fields[0]
            assert not nested
            assert raw['pcb'][span[0]:span[1]] == ('('+name+' '+' '.join(literals)+')').encode()
            assert lines[0]==raw['pcb'][:span[0]].count(b'\n')+1
    result = source.evaluate_source_boundaries(raw['pcb'],request,evidence,raw,BoundaryBindingPolicy(*_POLICY))
    assert isinstance(result,source.SourceSuccess),result
    assert len(result.artifact_result.binding.candidates)==4
    assert paths['pcb'].read_bytes()==raw['pcb']


def test_changed_c2_request_pose_blocks_binding(monkeypatch):
    request,evidence,_,paths,raw = admitted_request()
    index=next(i for i,p in enumerate(request.pads) if p.footprint_id=='C2')
    pad=request.pads[index];point=pad.rectangle.center
    changed=replace(pad,rectangle=replace(pad.rectangle,center=replace(point,x=point.x+0.001)))
    request=replace(request,pads=request.pads[:index]+(changed,)+request.pads[index+1:])
    monkeypatch.setattr(source.artifacts,'evaluate_artifact_boundaries',lambda *a:pytest.fail('binding reached'))
    result=source.evaluate_source_boundaries(raw['pcb'],request,evidence,raw,BoundaryBindingPolicy(*_POLICY))
    assert isinstance(result,source.SourceFailure)
    assert not hasattr(result,'candidates') and not hasattr(result,'artifact_result')
    d=result.diagnostic
    assert d.code.value=='SOURCE_CONFLICT' and d.field_path=='request.center.x'
    assert Decimal(d.expected.strip("'"))==Decimal('155.956')
    assert Decimal(d.actual.strip("'"))==Decimal(str(changed.rectangle.center.x))
    ctx={k:json.loads(v) for k,v in d.context}
    assert ctx['pad_uuid']==pad.source_entity_id and ctx['source_sha256']==source.PCB_HASH
    assert ctx['pose_field_spans'] and ctx['byte_span']
    assert all(paths[k].read_bytes()==v for k,v in raw.items())


@pytest.mark.parametrize('field',['footprint_at','pad_at','pad_size'])
@pytest.mark.parametrize('case',['missing','duplicate','invalid','nonfinite','noncardinal_or_zero'])
def test_bad_direct_fields_rejected(field,case):
    from test_c1_c2_source_membership import synthetic
    data=synthetic()
    # Private scanner, independent synthetic fields, no real pin bypass.
    parent=source.PAIRS[0][0];pad=source.PAIRS[0][1]
    data=data.replace(('(uuid "'+parent+'")').encode(),b'(at 10 20 90) '+('(uuid "'+parent+'")').encode())
    data=data.replace(('(uuid "'+pad+'")').encode(),b'(at 1 2 90) (size 4 2) '+('(uuid "'+pad+'")').encode())
    record=next(r for r in source._scan(data) if r.pad_uuid==pad)
    fields=getattr(record,field)
    if case=='missing':fields=()
    elif case=='duplicate':fields=fields+fields
    else:
        literals,span,lines,nested=fields[0];values=list(literals)
        if case=='invalid':values[0]='abc'
        elif case=='nonfinite':values[0]='NaN'
        else:values[-1]='0' if field=='pad_size' else '45'
        fields=((tuple(values),span,lines,nested),)
    with pytest.raises(pose.PoseError):pose.source_pose(replace(record,**{field:fields}))


def test_scanner_retains_duplicate_and_ignores_nested_fields():
    from test_c1_c2_source_membership import synthetic
    uid=source.PAIRS[0][1];marker=('(uuid "'+uid+'")').encode()
    data=synthetic().replace(marker,b'(at 1 2 90) (at 3 4 90) (wrapper (size 4 2)) '+marker)
    r=next(r for r in source._scan(data) if r.pad_uuid==uid)
    assert len(r.pad_at)==2 and r.pad_size==()


def test_quoted_numeric_not_a_numeric_literal():
    from test_c1_c2_source_membership import synthetic
    uid=source.PAIRS[0][1];marker=('(uuid "'+uid+'")').encode()
    data=synthetic().replace(marker,b'(at "1" 2 90) '+marker)
    r=next(r for r in source._scan(data) if r.pad_uuid==uid)
    assert r.pad_at[0][3] is True
