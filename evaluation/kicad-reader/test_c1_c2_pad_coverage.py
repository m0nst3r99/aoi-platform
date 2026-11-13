"""Selected-pad coverage; synthetic scanning is not real hash admission."""
import json
from hashlib import sha256
import pytest
import c1_c2_source_membership as source
from test_c1_c2_source_membership import synthetic, POLICY
from test_c1_c2_boundary_binding import admitted_request

C2_PAD = '21e4d927-86ab-439d-8b84-9241bc089b89'


def inserted(child):
    marker = ('(uuid "' + C2_PAD + '")').encode()
    return synthetic().replace(marker, child + b' ' + marker, 1)


def test_real_coverage_four_candidates_sixteen_corners():
    request, declarations, oracle, paths, raw = admitted_request()
    result = source.evaluate_source_boundaries(raw['pcb'], request, declarations, raw, POLICY)
    assert isinstance(result, source.SourceSuccess), result
    assert len(result.artifact_result.binding.candidates) == 4
    nets = {'e2743daf-d278-4538-a77e-8f62f1b7978c': '+12V',
            '4e53dd71-4be4-4973-9c48-191e7b2e27bb': 'GND',
            C2_PAD: '+5V', 'fc38c22a-efcb-4dfc-b42c-80a66f75e1a4': 'GND'}
    for record in result.records:
        nodes = {n.path[-1]: n for n in record.nodes}
        expected = {'uuid','at','size','layers','net','pintype'}
        if record.pad_uuid.startswith('e2743daf'):
            expected.add('zone_connect')
            assert nodes['zone_connect'].values == ('2',)
        assert set(nodes) == expected and len(nodes) == len(record.nodes)
        assert nodes['net'].values == (nets[record.pad_uuid],)
        assert nodes['pintype'].values == ('passive',)
        for node in record.nodes:
            assert node.path == ('pad', node.path[-1]) and not node.has_children
            expected_status = ('semantics-unchecked' if node.path[-1] in
                               ('net','pintype','zone_connect') else 'existing-semantic-gate')
            assert node.coverage == expected_status
            a,b = node.span
            assert raw['pcb'][a:b].startswith(b'(' + node.path[-1].encode())
            assert node.lines == (raw['pcb'][:a].count(b'\n')+1,raw['pcb'][:b].count(b'\n')+1)
    for candidate in result.artifact_result.binding.candidates:
        for i,j in enumerate((3,2,1,0)):
            x,y = oracle[candidate.pad_id][i]
            assert (candidate.vertices[j].x,candidate.vertices[j].y) == pytest.approx(
                (x/1e6,-y/1e6), abs=1e-6, rel=0)
    assert paths['pcb'].read_bytes() == raw['pcb']
    assert result.completeness == result.effective_copper_geometry == 'not-verified'


@pytest.mark.parametrize('child,path', [
    (b'(unsupported_geometry 1)', ('pad','unsupported_geometry')),
    (b'(net "GND" (unexpected 1))', ('pad','net','unexpected')),
    (b'(at 0 0 0 (at 1 2 3))', ('pad','at','at')),
    (b'(size 1 2 (wrapper (size 3 4)))', ('pad','size','wrapper')),
])
def test_unknown_path_and_known_parent_do_not_admit_descendants(child, path, monkeypatch):
    data = inserted(child)
    result = source._scan_checked(data)
    assert isinstance(result, source.SourceFailure)
    assert result.diagnostic.code.value == 'GEOMETRY_UNSUPPORTED'
    assert not hasattr(result, 'candidates') and not hasattr(result, 'artifact_result')
    ctx = {k:json.loads(v) for k,v in result.diagnostic.context}
    assert ctx['ancestry_path'] == ['kicad_pcb','footprint',*path]
    assert ctx['pad_uuid'] == C2_PAD
    assert ctx['parent_uuid'] == '00000000-0000-0000-0000-00005bd482e1'
    assert ctx['artifact_id'] == 'pcb' and ctx['source_sha256'] == sha256(data).hexdigest()
    a,b = ctx['node_span']
    assert data[a:b].startswith(b'(' + path[-1].encode())
    assert ctx['node_lines'] == [data[:a].count(b'\n')+1,data[:b].count(b'\n')+1]
    # Real hash admission must still reject synthetic input BEFORE the scanner.
    with monkeypatch.context() as patch:
        patch.setattr(source, '_scan', lambda *a:pytest.fail('synthetic admitted'))
        assert source.scan_pinned(data).diagnostic.field_path == 'pcb.size'
    # Failure-only test double: prove early propagation, never fake admission.
    monkeypatch.setattr(source,'scan_pinned',lambda _:result)
    monkeypatch.setattr(source.artifacts,'preflight_boundary_evidence',lambda *a:pytest.fail('preflight reached'))
    monkeypatch.setattr(source.artifacts,'evaluate_artifact_boundaries',lambda *a:pytest.fail('binding reached'))
    assert source.evaluate_source_boundaries(data,None,None,None,None) is result


@pytest.mark.parametrize('name', ['net','pintype','zone_connect'])
@pytest.mark.parametrize('body', ['','a b','a) ({name} b'])
def test_metadata_structure(name, body):
    child = ('('+name+' '+body.format(name=name)+')').encode()
    result = source._scan_checked(inserted(child))
    assert isinstance(result,source.SourceFailure)
    assert result.diagnostic.code.value == 'SCHEMA_INVALID'


def test_unknown_outside_selected_pad_is_not_footprint_coverage():
    data = synthetic(b'(unsupported_geometry 1)')
    marker = ('(uuid "'+source.PAIRS[0][0]+'")').encode()
    data = data.replace(marker, marker+b' (model "x" (offset (xyz 1 2 3))) (unknown_fp 1)',1)
    assert len(source._scan_checked(data)) == 4


def test_unknown_still_scans_to_eof():
    result = source._scan_checked(inserted(b'(unsupported_geometry 1)') + b')')
    assert result.diagnostic.code.value == 'SCHEMA_INVALID'


@pytest.mark.parametrize('name', ['uuid','layers'])
def test_unknown_under_identity_or_layers_gets_exact_path(name):
    data = synthetic()
    marker = ('(uuid "'+C2_PAD+'")').encode()
    if name == 'uuid':
        data = data.replace(marker, marker[:-1]+b' (unexpected 1))',1)
    else:
        # Replace only the selected C2 pad's layers, retaining its UUID.
        position = data.index(marker)
        start = data.rfind(b'(layers ',0,position)
        end = data.index(b')',start)
        data = data[:end]+b' (unexpected 1)'+data[end:]
    result = source._scan_checked(data)
    assert isinstance(result,source.SourceFailure)
    assert result.diagnostic.code.value == 'GEOMETRY_UNSUPPORTED'
    context = {k:json.loads(v) for k,v in result.diagnostic.context}
    assert context['ancestry_path'] == ['kicad_pcb','footprint','pad',name,'unexpected']
    assert context['pad_uuid'] == C2_PAD
