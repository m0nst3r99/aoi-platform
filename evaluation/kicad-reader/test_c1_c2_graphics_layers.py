"""Evaluation layer policy; synthetic records never establish hash admission."""
import json
from hashlib import sha256
import pytest
import c1_c2_source_membership as source
from test_c1_c2_footprint_fields import fixture_bytes
from test_c1_c2_boundary_binding import admitted_request
from test_c1_c2_source_membership import POLICY

PARENT='00000000-0000-0000-0000-00005bd482e1'


def records_for(child):
    marker=('(uuid "'+PARENT+'")').encode()
    data=fixture_bytes().replace(marker,marker+b' '+child,1)
    records=source._scan_checked(data)
    assert isinstance(records,tuple)
    assert source.check_footprint_fields(records,sha256(data).hexdigest()) is None
    assert source.check_footprint_coverage(records,sha256(data).hexdigest()) is None
    return data,records


def test_real_four_candidates_sixteen_corners():
    request,declarations,oracle,paths,raw=admitted_request()
    result=source.evaluate_source_boundaries(raw['pcb'],request,declarations,raw,POLICY)
    assert isinstance(result,source.SourceSuccess),result
    assert len(result.artifact_result.binding.candidates)==4
    for candidate in result.artifact_result.binding.candidates:
        for i,j in enumerate((3,2,1,0)):
            x,y=oracle[candidate.pad_id][i]
            assert (candidate.vertices[j].x,candidate.vertices[j].y)==pytest.approx((x/1e6,-y/1e6),abs=1e-6,rel=0)
    assert paths['pcb'].read_bytes()==raw['pcb']
    assert all(n.semantics=='semantics-unchecked' for r in result.records
               for n in r.footprint_nodes if n.category=='graphics/text')


@pytest.mark.parametrize('kind',['fp_line','fp_circle','property'])
@pytest.mark.parametrize('layer',['F.Cu','Edge.Cuts','missing','duplicate'])
def test_invalid_layer_blocks_before_binding(kind,layer,monkeypatch):
    header=b'property "arbitrary" "value" (at 0 0 0)' if kind=='property' else kind.encode()
    fields=(b'' if layer=='missing' else b'(layer "F.SilkS") (layer "F.SilkS")'
            if layer=='duplicate' else ('(layer "'+layer+'")').encode())
    data,records=records_for(b'('+header+b' '+fields+b')')
    result=source.check_graphics_layers(records,sha256(data).hexdigest())
    assert isinstance(result,source.SourceFailure)
    assert result.diagnostic.code.value==('SCHEMA_INVALID' if layer in ('missing','duplicate') else 'GEOMETRY_UNSUPPORTED')
    assert not hasattr(result,'candidates')
    ctx={k:json.loads(v) for k,v in result.diagnostic.context}
    assert ctx['parent_uuid']==PARENT and ctx['source_sha256']==sha256(data).hexdigest()
    assert ctx['ancestry_path']==['kicad_pcb','footprint',kind,'layer']
    a,b=ctx['owner_span'];assert data[a:b].startswith(b'('+kind.encode())
    assert source.scan_pinned(data).diagnostic.field_path=='pcb.size'
    # Private scanner-record double isolates gate ordering, not hash admission.
    monkeypatch.setattr(source,'scan_pinned',lambda _:records)
    monkeypatch.setattr(source.artifacts,'preflight_boundary_evidence',lambda *a:pytest.fail('preflight reached'))
    monkeypatch.setattr(source.artifacts,'evaluate_artifact_boundaries',lambda *a:pytest.fail('binding reached'))
    actual=source.evaluate_source_boundaries(data,None,None,None,None)
    assert actual.diagnostic.field_path=='footprint.graphics.layer'
    assert not hasattr(actual,'candidates') and not hasattr(actual,'artifact_result')


@pytest.mark.parametrize('body',[
    b'(property "Reference" "x")',
    b'(property "Reference" "x" (hide yes))',
    b'(property "anything" "x" (layer "F.Fab"))',
    b'(property "anything" "x" (effects (font (size 1 1))) (layer "F.SilkS"))',
    b'(fp_line (layer "F.CrtYd")) (fp_circle (layer "F.SilkS"))',
])
def test_allowed_and_metadata_only(body):
    data,records=records_for(body)
    assert source.check_graphics_layers(records,sha256(data).hexdigest()) is None


@pytest.mark.parametrize('trigger',[b'(at 0 0 0)',b'(effects (font (size 1 1)))'])
def test_display_trigger_ignores_hide_and_name(trigger):
    data,records=records_for(b'(property "ki_fp_filters" "x" (hide yes) '+trigger+b')')
    assert source.check_graphics_layers(records,sha256(data).hexdigest()).diagnostic.code.value=='SCHEMA_INVALID'


def test_sibling_layer_not_borrowed():
    data,records=records_for(b'(fp_line (layer "F.SilkS")) (fp_line (start 0 0))')
    result=source.check_graphics_layers(records,sha256(data).hexdigest())
    assert result.diagnostic.code.value=='SCHEMA_INVALID'
    ctx={k:json.loads(v) for k,v in result.diagnostic.context}
    a,b=ctx['owner_span'];assert data[a:b]==b'(fp_line (start 0 0))'
