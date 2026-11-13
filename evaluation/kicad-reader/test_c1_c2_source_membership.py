"""Real pin integration plus private lexical tests, not a pin bypass in the flow."""
from dataclasses import replace, FrozenInstanceError
from hashlib import sha256
import json
import pytest
import c1_c2_source_membership as source
from test_c1_c2_boundary_binding import admitted_request
from aoi_platform.boundary_evidence import BoundaryBindingPolicy, _POLICY

POLICY = BoundaryBindingPolicy(*_POLICY)


def synthetic(extra=b'', missing=False):
    groups = {}
    for parent, pad in source.PAIRS:
        groups.setdefault(parent, []).append(pad)
    result = b'(kicad_pcb\n' + extra
    for parent, pads in groups.items():
        result += ('(footprint "test" (uuid "'+parent+'")\n').encode()
        for i, pad in enumerate(pads):
            if missing and pad == source.PAIRS[0][1]:
                continue
            result += ('(pad "'+str(i+1)+'" smd rect (layers "F.Cu" "F.Mask" "F.Paste") '
                       '(uuid "'+pad+'"))\n').encode()
        result += b')\n'
    return result + b')'


@pytest.fixture
def admitted():
    return admitted_request()


def test_real_four_memberships_and_binding(admitted, monkeypatch):
    request, declarations, oracle, paths, raw = admitted
    calls = []
    real = source.artifacts.bind_pad_boundaries
    def bind(*args):
        calls.append(args)
        return real(*args)
    monkeypatch.setattr(source.artifacts, 'bind_pad_boundaries', bind)
    before = repr((request, declarations, raw))
    result = source.evaluate_source_boundaries(raw['pcb'], request, declarations, raw, POLICY)
    assert isinstance(result, source.SourceSuccess), result
    assert len(result.records) == len(calls[0][0].pads) == 4 and len(calls) == 1
    # Source line oracles from independently documented C1/C2 declarations.
    lines = {'e2743daf-d278-4538-a77e-8f62f1b7978c':338,
             '4e53dd71-4be4-4973-9c48-191e7b2e27bb':347,
             '21e4d927-86ab-439d-8b84-9241bc089b89':629,
             'fc38c22a-efcb-4dfc-b42c-80a66f75e1a4':637}
    numbers = dict(zip(lines, ('1', '2', '1', '2')))
    assert {(r.parent_uuid, r.pad_uuid) for r in result.records} == set(source.PAIRS)
    for r in result.records:
        assert tuple(m.path for m in r.modifiers) == source.MODIFIER_PATHS
        assert all((m.status, m.first_span, m.first_lines, m.occurrences) ==
                   ('absent', None, None, 0) for m in r.modifiers)
        assert r.number == numbers[r.pad_uuid]
        assert (r.pad_type, r.shape, r.layers) == ('smd', 'rect', ('F.Cu', 'F.Mask', 'F.Paste'))
        a, b = r.span
        assert raw['pcb'][a:b].startswith(b'(pad "'+r.number.encode()+b'" smd rect')
        assert raw['pcb'][a:b].endswith(b')')
        assert r.lines[0] == lines[r.pad_uuid] == raw['pcb'][:a].count(b'\n') + 1
        assert r.lines[1] == raw['pcb'][:b].count(b'\n') + 1
    for c in result.artifact_result.binding.candidates:
        for i, j in enumerate((3, 2, 1, 0)):
            x, y = oracle[c.pad_id][i]
            assert (c.vertices[j].x, c.vertices[j].y) == pytest.approx((x/1e6, -y/1e6), abs=1e-6, rel=0)
    assert result.completeness == result.effective_copper_geometry == 'not-verified'
    assert result.artifact_result.binding.source_membership_status == 'not-verified'
    assert repr((request, declarations, raw)) == before
    assert paths['pcb'].read_bytes() == raw['pcb']
    with pytest.raises(FrozenInstanceError):
        result.records = ()


def test_wrong_record_parent_before_binding_unchanged_source(admitted, monkeypatch):
    request, declarations, _, paths, raw = admitted
    item = declarations[0]
    wrong = next(e.source_parent_id for e in declarations if e.source_parent_id != item.source_parent_id)
    declarations = (replace(item, source_parent_id=wrong),) + declarations[1:]
    monkeypatch.setattr(source.artifacts, 'evaluate_artifact_boundaries', lambda *a:pytest.fail('binding path reached'))
    result = source.evaluate_source_boundaries(raw['pcb'], request, declarations, raw, POLICY)
    assert isinstance(result, source.SourceFailure)
    assert not hasattr(result, 'candidates') and not hasattr(result, 'artifact_result')
    d = result.diagnostic
    assert d.code.value == 'SOURCE_CONFLICT' and d.field_path == 'declaration.parent_uuid'
    assert d.expected == repr(item.source_parent_id) and d.actual == repr(wrong)
    ctx = {k:json.loads(v) for k,v in d.context}
    assert ctx['pad_uuid'] == item.source_pad_id and ctx['source_sha256'] == source.PCB_HASH
    assert ctx['parent_uuid'] == item.source_parent_id
    a,b = ctx['byte_span']
    assert item.source_pad_id.encode() in raw['pcb'][a:b]
    assert paths['pcb'].read_bytes() == raw['pcb']


@pytest.mark.parametrize('field,value', [('pad_number','wrong'),('pad_type','thru_hole'),('copper_layers',('B.Cu',))])
def test_explicit_request_fields_conflict(admitted, monkeypatch, field, value):
    request, declarations, _, _, raw = admitted
    request = replace(request, pads=(replace(request.pads[0], **{field:value}),)+request.pads[1:])
    monkeypatch.setattr(source.artifacts, 'evaluate_artifact_boundaries', lambda *a:pytest.fail('binding reached'))
    result = source.evaluate_source_boundaries(raw['pcb'], request, declarations, raw, POLICY)
    assert isinstance(result, source.SourceFailure) and result.diagnostic.code.value == 'SOURCE_CONFLICT'


@pytest.mark.parametrize('change', ['size', 'hash'])
def test_pin_before_parse(admitted, monkeypatch, change):
    data = admitted[-1]['pcb']
    changed = data+b' ' if change == 'size' else b'!'+data[1:]
    monkeypatch.setattr(source, '_scan', lambda *a:pytest.fail('parse before pin'))
    result = source.scan_pinned(changed)
    assert isinstance(result, source.SourceFailure)
    assert result.diagnostic.field_path == 'pcb.'+('size' if change=='size' else 'sha256')


def test_quoted_parentheses_escapes_and_eof():
    data = synthetic(b'(property "() (uuid fake)" "quote: \\" slash: \\\\ newline: \\n")\n')
    records = source._scan(data)
    assert len(records) == 4
    with pytest.raises(source.ScanError):source._scan(data+b')')
    with pytest.raises(source.ScanError):source._scan(data+b' (other)')


@pytest.mark.parametrize('suffix', [b'\\q', b'\\x41', b'\\u0041'])
def test_unsupported_escape(suffix):
    with pytest.raises(source.ScanError, match='escape'):
        source._scan(synthetic(b'(property "x" "'+suffix+b'")'))


@pytest.mark.parametrize('case', ['same', 'equivalent', 'footprint_pad', 'footprint_footprint'])
def test_duplicate_uuid_identity(case):
    uid = source.PAIRS[0][1]
    other = uid.upper() if case == 'equivalent' else uid
    if case == 'footprint_pad':
        extra = ('(footprint "extra" (uuid "'+uid+'"))').encode()
    elif case == 'footprint_footprint':
        extra = ('(footprint "extra" (uuid "'+source.PAIRS[0][0]+'"))').encode()
    else:
        # Duplicate pad in a different, nonselected footprint.
        extra = ('(footprint "extra" (uuid "11111111-1111-1111-1111-111111111111") '
                 '(pad "9" smd rect (layers "F.Cu") (uuid "'+other+'")))').encode()
    with pytest.raises(source.ScanError, match='duplicate UUID'):
        source._scan(synthetic(extra))


def test_dimension_text_shared_uuid_outside_namespace():
    # Also deliberately shares a selected pad UUID: cross-namespace is excluded.
    uid = source.PAIRS[0][1]
    extra = ('(dimension (uuid "'+uid+'") (gr_text "()" (uuid "'+uid+'")))').encode()
    assert len(source._scan(synthetic(extra))) == 4


def test_duplicate_nonselected_pads_after_selected_records():
    uid = '22222222-2222-2222-2222-222222222222'
    extra = ('(footprint "extra" (uuid "11111111-1111-1111-1111-111111111111") '
             '(pad "1" smd rect (uuid "'+uid+'")) (pad "2" smd rect (uuid "'+uid+'")))').encode()
    with pytest.raises(source.ScanError, match='duplicate UUID'):
        source._scan(synthetic()[:-1]+extra+b')')


@pytest.mark.parametrize('case', ['missing', 'nested_pad', 'nested_uuid', 'wrong_parent', 'unclosed', 'quote', 'empty'])
def test_membership_and_syntax_failures(case):
    data = synthetic(missing=case=='missing')
    if case == 'nested_pad':data = data.replace(b'(pad ', b'(wrapper (pad ',1).replace(b'))\n', b')))\n',1)
    if case == 'nested_uuid':
        u = ('(uuid "'+source.PAIRS[0][1]+'")').encode()
        data = data.replace(u, b'(wrapper '+u+b')')
    if case == 'wrong_parent':data = data.replace(source.PAIRS[0][0].encode(),b'11111111-1111-1111-1111-111111111111')
    if case == 'unclosed':data = data[:-1]
    if case == 'quote':data = b'(kicad_pcb (property "unterminated)'
    if case == 'empty':data = synthetic(b'()')
    with pytest.raises(source.ScanError):source._scan(data)


def test_depth_exact_and_exceeded():
    assert len(source._scan(synthetic(b'(x '*127+b')'*127))) == 4
    with pytest.raises(source.ScanError, match='depth limit'):
        source._scan(synthetic(b'(x '*128+b')'*128))


@pytest.mark.parametrize('quoted', [False, True])
def test_token_size_exact_and_exceeded(quoted):
    for extra in (0, 1):
        token = b'a'*(65536 - (2 if quoted else 0) + extra)
        if quoted:token = b'"'+token+b'"'
        data = synthetic(b'(property '+token+b')')
        if extra:
            with pytest.raises(source.ScanError, match='token-byte limit'):source._scan(data)
        else:assert len(source._scan(data)) == 4


def test_total_tokens_exact_and_exceeded():
    base = synthetic(b'(property )')
    remaining = 500000 - sum(1 for _ in source._tokens(base))
    data = base.replace(b'(property )', b'(property '+b'a '*remaining+b')')
    assert len(source._scan(data)) == 4
    with pytest.raises(source.ScanError, match='token-count limit'):
        source._scan(data.replace(b'(property ',b'(property a ',1))


def with_pad_modifier(modifier):
    # Insert directly in the first selected pad, before UUID (UUID may be last).
    uid = source.PAIRS[0][1]
    marker = ('(uuid "'+uid+'")').encode()
    return synthetic().replace(marker, modifier+b' '+marker, 1)


@pytest.mark.parametrize('modifier,path', [
    (b'(drill 1)', ('pad','drill')),
    (b'(offset 1 2)', ('pad','offset')),
    (b'(drill 1 (offset 1 2))', ('pad','drill','offset')),
    (b'(padstack (mode custom))', ('pad','padstack')),
    (b'(padstack (layer "F.Cu" (shape rect)))', ('pad','padstack','layer')),
    (b'(layer "F.Cu" (shape rect))', ('pad','layer')),
    (b'(primitives (gr_line (start 0 0) (end 1 1)))', ('pad','primitives')),
    (b'(options (anchor rect))', ('pad','options')),
])
def test_listed_modifier_presence_span_and_rejection(modifier, path):
    data = with_pad_modifier(modifier)
    result = source._scan_checked(data)
    assert isinstance(result, source.SourceFailure)
    assert result.diagnostic.code.value == 'GEOMETRY_UNSUPPORTED'
    assert not hasattr(result,'candidates') and not hasattr(result,'artifact_result')
    record = next(r for r in result.modifier_records if r.pad_uuid == source.PAIRS[0][1])
    declaration = next(m for m in record.modifiers if m.path == path)
    assert declaration.status == 'present' and declaration.occurrences == 1
    a,b = declaration.first_span
    assert data[a:b].startswith(b'('+path[-1].encode()) and data[b-1:b] == b')'
    assert declaration.first_lines == (data[:a].count(b'\n')+1,data[:b].count(b'\n')+1)
    assert json.loads(dict(result.diagnostic.context)['source_sha256']) == sha256(data).hexdigest()


def test_synthetic_drill_offset_failure_propagates_before_binding(monkeypatch):
    data = with_pad_modifier(b'(drill 1 (offset 0.1 0.2))')
    result = source._scan_checked(data)
    assert isinstance(result, source.SourceFailure)
    assert result.diagnostic.code.value == 'GEOMETRY_UNSUPPORTED'
    present = {m.path for r in result.modifier_records for m in r.modifiers if m.status=='present'}
    assert present == {('pad','drill'),('pad','drill','offset')}
    # Transport an already rejected private-scanner result; never mock admission
    # success for altered bytes. Real pin rejection is asserted separately below.
    monkeypatch.setattr(source,'scan_pinned',lambda _:result)
    monkeypatch.setattr(source.artifacts,'preflight_boundary_evidence',lambda *a:pytest.fail('preflight reached'))
    monkeypatch.setattr(source.artifacts,'evaluate_artifact_boundaries',lambda *a:pytest.fail('binding reached'))
    assert source.evaluate_source_boundaries(data,None,None,None,None) is result


def test_synthetic_modifier_cannot_bypass_real_pin():
    result = source.scan_pinned(with_pad_modifier(b'(drill 1 (offset 1 2))'))
    assert isinstance(result,source.SourceFailure) and result.diagnostic.field_path=='pcb.size'


def test_model_offset_and_zone_connect_excluded():
    data = synthetic(b'(model "board-model" (offset (xyz 1 2 3)))')
    # Footprint-owned model and pad zone_connect are also excluded.
    marker = ('(uuid "'+source.PAIRS[0][0]+'")').encode()
    data = data.replace(marker,marker+b' (model "fp-model" (offset (xyz 4 5 6)))',1)
    marker = ('(uuid "'+source.PAIRS[0][1]+'")').encode()
    data = data.replace(marker,b'(zone_connect 2) '+marker,1)
    records = source._scan_checked(data)
    assert isinstance(records,tuple) and len(records)==4
    assert all(m.status=='absent' for r in records for m in r.modifiers)


def test_modifier_screen_still_reads_to_eof():
    data = with_pad_modifier(b'(drill 1)')+b')'
    result = source._scan_checked(data)
    assert isinstance(result,source.SourceFailure)
    assert result.diagnostic.code.value=='SCHEMA_INVALID'
