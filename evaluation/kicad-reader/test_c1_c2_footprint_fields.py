"""Two pinned footprint fields; synthetic scanning is not hash admission."""
from hashlib import sha256
import json
import pytest
import c1_c2_source_membership as source
from test_c1_c2_source_membership import synthetic, POLICY
from test_c1_c2_boundary_binding import admitted_request


def fixture_bytes(layer=b'(layer "F.Cu")', attr=b'(attr smd)'):
    data = synthetic()
    for parent in sorted({p for p,_ in source.PAIRS}):
        marker = ('(uuid "'+parent+'")').encode()
        data = data.replace(marker, marker+b' '+layer+b' '+attr, 1)
    return data


def test_real_fields_four_candidates_sixteen_corners():
    request,declarations,oracle,paths,raw = admitted_request()
    result = source.evaluate_source_boundaries(raw['pcb'],request,declarations,raw,POLICY)
    assert isinstance(result,source.SourceSuccess),result
    assert len(result.artifact_result.binding.candidates)==4
    observation=json.loads(raw['observation'])
    for record in result.records:
        fields={f.name:f for f in record.footprint_fields}
        assert len(record.footprint_fields)==2
        assert fields['layer'].values==('F.Cu',) and fields['attr'].values==('smd',)
        assert fields['layer'].literal==b'(layer "F.Cu")'
        assert fields['attr'].literal==b'(attr smd)'
        assert next(f for f in observation['footprints'] if f['uuid']==record.parent_uuid)['layer']=='F.Cu'
        for f in fields.values():
            a,b=f.span
            assert raw['pcb'][a:b]==f.literal and not f.has_children
            assert f.lines==(raw['pcb'][:a].count(b'\n')+1,raw['pcb'][:b].count(b'\n')+1)
    for candidate in result.artifact_result.binding.candidates:
        for i,j in enumerate((3,2,1,0)):
            x,y=oracle[candidate.pad_id][i]
            assert (candidate.vertices[j].x,candidate.vertices[j].y)==pytest.approx((x/1e6,-y/1e6),abs=1e-6,rel=0)
    assert paths['pcb'].read_bytes()==raw['pcb']


@pytest.mark.parametrize('name', ['layer','attr'])
@pytest.mark.parametrize('case', ['missing','duplicate','unsupported','descendant','empty'])
def test_rejection_before_binding(name,case,monkeypatch):
    leaf=b'(layer "F.Cu")' if name=='layer' else b'(attr smd)'
    value={'missing':b'', 'duplicate':leaf+b' '+leaf,
           'unsupported':b'(layer "B.Cu")' if name=='layer' else b'(attr smd exclude_from_bom)',
           'descendant':leaf[:-1]+b' (unexpected (nested 1)))',
           'empty':('('+name+')').encode()}[case]
    data=fixture_bytes(**{name:value})
    records=source._scan_checked(data)
    assert isinstance(records,tuple)
    result=source.check_footprint_fields(records,sha256(data).hexdigest())
    assert isinstance(result,source.SourceFailure)
    assert result.diagnostic.code.value==('SCHEMA_INVALID' if case in ('missing','duplicate') else 'GEOMETRY_UNSUPPORTED')
    assert not hasattr(result,'candidates') and not hasattr(result,'artifact_result')
    ctx={k:json.loads(v) for k,v in result.diagnostic.context}
    assert ctx['source_sha256']==sha256(data).hexdigest()
    assert ctx['parent_uuid'] in {p for p,_ in source.PAIRS}
    assert ctx['ancestry_path']==['kicad_pcb','footprint',name]
    assert len(ctx['field_spans'])== (0 if case=='missing' else 2 if case=='duplicate' else 1)
    # Actual pin rejects altered bytes; no successful synthetic hash admission.
    assert source.scan_pinned(data).diagnostic.field_path=='pcb.size'
    # Scanner-record test double isolates the downstream field gate only.
    monkeypatch.setattr(source,'scan_pinned',lambda _:records)
    monkeypatch.setattr(source.artifacts,'preflight_boundary_evidence',lambda *a:pytest.fail('preflight reached'))
    monkeypatch.setattr(source.artifacts,'evaluate_artifact_boundaries',lambda *a:pytest.fail('binding reached'))
    actual=source.evaluate_source_boundaries(data,None,None,None,None)
    assert isinstance(actual,source.SourceFailure) and actual.diagnostic.field_path=='footprint.'+name


def test_direct_ancestry_and_unselected_fields():
    data=fixture_bytes()
    marker=('(uuid "'+source.PAIRS[0][0]+'")').encode()
    data=data.replace(marker,marker+b' (model "x" (layer "B.Cu") (attr other))',1)
    data=data[:-1]+b'(footprint "other" (layer "B.Cu") (attr through_hole)))'
    records=source._scan_checked(data)
    assert source.check_footprint_fields(records,sha256(data).hexdigest()) is None
