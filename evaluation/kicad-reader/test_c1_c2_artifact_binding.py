"""Real pinned bytes; memory-only declaration mismatch is checked before binding."""
from dataclasses import replace, FrozenInstanceError
import json
import pytest
import c1_c2_artifact_binding as gate
from test_c1_c2_boundary_binding import admitted_request
from aoi_platform.boundary_evidence import BoundaryBindingPolicy, _POLICY

POLICY=BoundaryBindingPolicy(*_POLICY)

@pytest.fixture
def admitted():
    request,evidence,oracle,paths,raw=admitted_request()
    return request,evidence,oracle,{k:raw[k] for k in ('observation','C1_boundary','C2_boundary')}


def test_positive_exact_records_and_sixteen_oracle_corners(admitted,monkeypatch):
    request,evidence,oracle,raw=admitted;calls=[];real=gate.bind_pad_boundaries
    def bind(*args):calls.append(args);return real(*args)
    monkeypatch.setattr(gate,'bind_pad_boundaries',bind)
    before=repr((request,evidence,raw));result=gate.evaluate_artifact_boundaries(request,evidence,raw,POLICY)
    assert isinstance(result,gate.ArtifactBindingSuccess),result
    assert len(calls)==1 and len(result.records)==len(result.binding.candidates)==4
    for record in result.records:
        row=next(r for r in json.loads(raw[record.artifact_id])['pads'] if r['uuid']==record.pad_uuid)
        assert record.raw_vertices_iu==tuple(tuple(v) for v in row['contours'][0]['vertices_iu'])
        assert record.parent_uuid==row['parent_uuid']
        assert record.native_protocol in ('c1-boundary-diagnostic-v1','c2-boundary-diagnostic-v1')
        assert record.native_protocol!='C1-C2-pinned-boundary' # caller label remains separate
        assert record.normalized_vertices_mm==tuple((x/1e6,-y/1e6) for x,y in record.raw_vertices_iu)
    for c in result.binding.candidates:
        for i,j in enumerate((3,2,1,0)):
            x,y=oracle[c.pad_id][i]
            assert (c.vertices[j].x,c.vertices[j].y)==pytest.approx((x/1e6,-y/1e6),abs=1e-6,rel=0)
    assert result.source_membership_status=='not-verified'
    assert not result.binding.import_ready and not result.binding.published
    assert repr((request,evidence,raw))==before
    with pytest.raises(FrozenInstanceError):result.records=()


def test_one_c2_vertex_declaration_conflict_before_binding(admitted,monkeypatch):
    request,evidence,_,raw=admitted;before=dict(raw)
    index=next(i for i,e in enumerate(evidence) if e.canonical_parent_id=='C2')
    item=evidence[index];contour=item.contours[0];point=contour.vertices[0]
    changed=replace(point,x=point.x+0.01)
    altered=replace(item,contours=(replace(contour,vertices=(changed,)+contour.vertices[1:]),))
    evidence=evidence[:index]+(altered,)+evidence[index+1:]
    monkeypatch.setattr(gate,'bind_pad_boundaries',lambda *a:pytest.fail('binding called before artifact gate'))
    result=gate.evaluate_artifact_boundaries(request,evidence,raw,POLICY)
    assert isinstance(result,gate.ArtifactBindingFailure),result
    assert not hasattr(result,'candidates') and not hasattr(result,'binding')
    d=result.diagnostic;context={k:json.loads(v) for k,v in d.context}
    assert d.code.value=='SOURCE_CONFLICT' and d.field_path=='contours[0].vertices[0]'
    assert d.expected==repr((point.x,point.y)) and d.actual==repr((changed.x,changed.y))
    assert context['artifact_id_json']=='C2_boundary'
    assert context['artifact_sha256']==item.boundary.computed_sha256
    assert context['parent_uuid']==item.source_parent_id and context['pad_uuid']==item.source_pad_id
    assert raw==before


@pytest.mark.parametrize('case',['missing','extra','duplicate','wrong_parent'])
def test_exact_four_pair_set(admitted,monkeypatch,case):
    request,evidence,_,raw=admitted
    if case=='missing':evidence=evidence[:-1]
    elif case=='extra':evidence=evidence+(evidence[0],)
    elif case=='duplicate':evidence=evidence[:-1]+(evidence[0],)
    else:evidence=(replace(evidence[0],source_parent_id='wrong'),)+evidence[1:]
    monkeypatch.setattr(gate,'bind_pad_boundaries',lambda *a:pytest.fail('unexpected binding'))
    result=gate.evaluate_artifact_boundaries(request,evidence,raw,POLICY)
    assert not isinstance(result,gate.ArtifactBindingSuccess)
    assert not hasattr(result,'candidates') and not hasattr(result,'binding')


@pytest.mark.parametrize('artifact',['observation','C1_boundary','C2_boundary'])
def test_raw_hash_pin_failure(admitted,monkeypatch,artifact):
    request,evidence,_,raw=admitted;raw=dict(raw)
    raw[artifact]=b'!'+raw[artifact][1:]
    monkeypatch.setattr(gate,'bind_pad_boundaries',lambda *a:pytest.fail('unexpected binding'))
    result=gate.evaluate_artifact_boundaries(request,evidence,raw,POLICY)
    assert isinstance(result,gate.ArtifactBindingFailure)
    assert result.diagnostic.field_path=='raw.sha256'
