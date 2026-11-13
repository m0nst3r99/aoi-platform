"""Pinned real coverage plus private synthetic scanner / early-gate doubles."""
from hashlib import sha256
import json
import pytest
import c1_c2_source_membership as source
from test_c1_c2_footprint_fields import fixture_bytes
from test_c1_c2_boundary_binding import admitted_request
from test_c1_c2_source_membership import POLICY


def test_real_all_paths_layers_and_candidates():
    request,declarations,oracle,paths,raw=admitted_request()
    result=source.evaluate_source_boundaries(raw['pcb'],request,declarations,raw,POLICY)
    assert isinstance(result,source.SourceSuccess),result
    expected=set('''layer uuid at attr descr path sheetname sheetfile embedded_fonts
duplicate_pad_numbers_are_jumpers property property/at property/layer property/uuid
property/unlocked property/hide property/effects property/effects/font
property/effects/font/size property/effects/font/thickness
fp_line fp_line/start fp_line/end fp_line/stroke fp_line/stroke/width
fp_line/stroke/type fp_line/layer fp_line/uuid
fp_circle fp_circle/center fp_circle/end fp_circle/stroke fp_circle/stroke/width
fp_circle/stroke/type fp_circle/fill fp_circle/layer fp_circle/uuid
model model/offset model/offset/xyz model/scale model/scale/xyz model/rotate model/rotate/xyz'''.split())
    for record in result.records:
        nodes=record.footprint_nodes
        assert {'/'.join(n.path[2:]) for n in nodes}==expected
        assert all(n.path[:2]==('kicad_pcb','footprint') and 'pad' not in n.path for n in nodes)
        layers={}
        for n in nodes:
            a,b=n.span
            assert raw['pcb'][a:b].startswith(b'('+n.path[-1].encode())
            assert n.lines==(raw['pcb'][:a].count(b'\n')+1,raw['pcb'][:b].count(b'\n')+1)
            if n.path[2:] in (('uuid',),('at',),('layer',),('attr',)):
                assert n.semantics==n.category=='existing-semantic-gate'
            else:assert n.semantics=='semantics-unchecked'
            if n.graphics_layer_values is not None:
                assert n.category=='graphics/text' and n.graphics_layer_values==n.values
                key=(n.path[2],n.values)
                layers[key]=layers.get(key,0)+1
        assert layers=={('fp_line',('F.SilkS',)):14,('fp_line',('F.CrtYd',)):4,
                        ('fp_circle',('F.SilkS',)):1,('property',('F.SilkS',)):1,
                        ('property',('F.Fab',)):3}
        assert sum(n.path==('kicad_pcb','footprint','model') for n in nodes)==2
    assert len(result.artifact_result.binding.candidates)==4
    for candidate in result.artifact_result.binding.candidates:
        for i,j in enumerate((3,2,1,0)):
            x,y=oracle[candidate.pad_id][i]
            assert (candidate.vertices[j].x,candidate.vertices[j].y)==pytest.approx((x/1e6,-y/1e6),abs=1e-6,rel=0)
    assert paths['pcb'].read_bytes()==raw['pcb']


@pytest.mark.parametrize('child,path',[
    (b'(property "x" "y" (effects (font (unsupported_geometry 1))))',
     ('property','effects','font','unsupported_geometry')),
    (b'(model "x" (offset (xyz 0 0 0 (unknown 1))))',('model','offset','xyz','unknown')),
    (b'(fp_line (stroke (unknown 1)))',('fp_line','stroke','unknown')),
])
def test_unknown_descendant_before_binding(child,path,monkeypatch):
    parent='00000000-0000-0000-0000-00005bd482e1'
    marker=('(uuid "'+parent+'")').encode()
    data=fixture_bytes().replace(marker,marker+b' '+child,1)
    records=source._scan_checked(data)
    assert isinstance(records,tuple)
    assert source.check_footprint_fields(records,sha256(data).hexdigest()) is None
    result=source.check_footprint_coverage(records,sha256(data).hexdigest())
    assert isinstance(result,source.SourceFailure)
    assert result.diagnostic.code.value=='GEOMETRY_UNSUPPORTED'
    assert not hasattr(result,'candidates') and not hasattr(result,'artifact_result')
    ctx={k:json.loads(v) for k,v in result.diagnostic.context}
    assert ctx['parent_uuid']==parent and ctx['source_sha256']==sha256(data).hexdigest()
    assert ctx['ancestry_path']==['kicad_pcb','footprint',*path]
    a,b=ctx['node_span'];assert data[a:b].startswith(b'('+path[-1].encode())
    # Actual admission stays pinned; no synthetic success through scan_pinned.
    assert source.scan_pinned(data).diagnostic.field_path=='pcb.size'
    monkeypatch.setattr(source,'scan_pinned',lambda _:records)
    monkeypatch.setattr(source.artifacts,'preflight_boundary_evidence',lambda *a:pytest.fail('preflight reached'))
    monkeypatch.setattr(source.artifacts,'evaluate_artifact_boundaries',lambda *a:pytest.fail('binding reached'))
    actual=source.evaluate_source_boundaries(data,None,None,None,None)
    assert actual.diagnostic.code.value=='GEOMETRY_UNSUPPORTED'
    assert actual.diagnostic.field_path=='footprint.coverage'


def test_nonselected_footprint_excluded_and_eof_required():
    data=fixture_bytes()[:-1]+b'(footprint "other" (unknown (descendant 1))))'
    records=source._scan_checked(data)
    assert source.check_footprint_coverage(records,sha256(data).hexdigest()) is None
    result=source._scan_checked(data+b')')
    assert isinstance(result,source.SourceFailure) and result.diagnostic.code.value=='SCHEMA_INVALID'
