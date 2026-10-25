"""Portable evaluation decisions, not a product publication gate."""
import json
from pathlib import Path
import pytest
from outline_decision import evaluate_outline, Decision, Diagnostic

RAW = (Path(__file__).resolve().parents[1] / 'windows_runner/evidence/bow-tie-01/stdout.bin').read_bytes()


def test_replay_original_bytes():
    result = evaluate_outline(RAW)
    assert result == Decision('rejected', (Diagnostic('OUTLINE_INVALID', 'outline.valid',
        '627bdf46445d81e8d3bf6ae45f2adf028d7107483b5fa6456787aeefe5cc397b', '10.0.7'),))
    assert set(vars(result)) == {'status', 'diagnostics'}
    assert set(vars(result.diagnostics[0])) == {'code', 'field', 'input_sha256', 'build'}


@pytest.mark.parametrize('value', ['missing', None, 0, 1, 'false', [], {}])
def test_missing_or_nonboolean_valid(value):
    data = json.loads(RAW)
    if value == 'missing':
        del data['outline']['valid']
    else:
        data['outline']['valid'] = value
    assert evaluate_outline(json.dumps(data).encode()) == Decision('rejected', (Diagnostic('SCHEMA_INVALID', 'payload'),))


def test_true_is_only_intermediate():
    data = json.loads(RAW)
    data['outline']['valid'] = True
    assert evaluate_outline(json.dumps(data).encode()) == Decision('not_rejected_by_outline_check')


@pytest.mark.parametrize('raw', [b'{broken', b'\xff', b'null', b'[]'])
def test_bad_json_or_root(raw):
    assert evaluate_outline(raw) == Decision('rejected', (Diagnostic('SCHEMA_INVALID', 'payload'),))


@pytest.mark.parametrize('field', ['build', 'input_sha256', 'protocol_version'])
def test_required_metadata_missing(field):
    data = json.loads(RAW)
    del data[field]
    assert evaluate_outline(json.dumps(data).encode()).diagnostics == (Diagnostic('SCHEMA_INVALID', 'payload'),)


def test_bad_required_nested_type():
    data = json.loads(RAW)
    data['edges'][0]['uuid'] = 123
    assert evaluate_outline(json.dumps(data).encode()).diagnostics == (Diagnostic('SCHEMA_INVALID', 'payload'),)


REPEATED_RAW = (Path(__file__).resolve().parents[1] /
    'windows_runner/evidence/repeated-pads-01/stdout.bin').read_bytes()


def test_accepted_repeated_numbers_original_bytes():
    from observation_schema import schema
    data = json.loads(REPEATED_RAW)
    before = json.dumps(data, sort_keys=True)
    pads = data['footprints'][0]['pads']
    assert [p['number'] for p in pads] == ['1', '1']
    assert len({p['uuid'] for p in pads}) == 2
    assert schema(data) is True
    assert json.dumps(data, sort_keys=True) == before
    assert evaluate_outline(REPEATED_RAW) == Decision('not_rejected_by_outline_check')


@pytest.mark.parametrize('across_footprints', [False, True])
def test_duplicate_pad_uuid_is_schema_invalid(across_footprints):
    import copy
    from observation_schema import schema
    data = json.loads(REPEATED_RAW)
    first, second = data['footprints'][0]['pads']
    if across_footprints:
        other = copy.deepcopy(data['footprints'][0])
        other.update(uuid='00000000-0000-0000-0000-000000009999', reference='U2', pads=[second])
        data['footprints'][0]['pads'] = [first]
        data['footprints'].append(other)
        assert len({f['uuid'] for f in data['footprints']}) == 2
    # All other fields, including different parent UUIDs, pass before collision.
    assert schema(data) is True
    second['uuid'] = first['uuid']
    before = json.dumps(data, sort_keys=True)
    with pytest.raises(ValueError, match='^Duplicate pad UUID$'):
        schema(data)
    assert json.dumps(data, sort_keys=True) == before
    assert evaluate_outline(json.dumps(data).encode()) == Decision(
        'rejected', (Diagnostic('SCHEMA_INVALID', 'payload'),))


def test_equivalent_uuid_spelling_cannot_hide_duplicate():
    from observation_schema import schema
    data = json.loads(REPEATED_RAW)
    pads = data['footprints'][0]['pads']
    pads[1]['uuid'] = '{' + pads[0]['uuid'] + '}'
    with pytest.raises(ValueError, match='^Duplicate pad UUID$'):
        schema(data)
    assert evaluate_outline(json.dumps(data).encode()).diagnostics == (
        Diagnostic('SCHEMA_INVALID', 'payload'),)


@pytest.mark.parametrize('equivalent', [False, True])
def test_duplicate_board_edge_identity_rejected_without_mutation(equivalent):
    import copy
    from observation_schema import schema
    data = json.loads(REPEATED_RAW)
    assert schema(data) is True
    assert evaluate_outline(REPEATED_RAW) == Decision('not_rejected_by_outline_check')
    original = copy.deepcopy(data)
    edge_id = data['edges'][0]['uuid']
    data['edges'][1]['uuid'] = '{' + edge_id + '}' if equivalent else edge_id
    # The only source change is one board-edge UUID.
    restored = copy.deepcopy(data)
    restored['edges'][1]['uuid'] = original['edges'][1]['uuid']
    assert restored == original
    before = copy.deepcopy(data)
    with pytest.raises(ValueError, match='^Duplicate board edge UUID$'):
        schema(data)
    assert data == before
    assert evaluate_outline(json.dumps(data).encode()) == Decision(
        'rejected', (Diagnostic('SCHEMA_INVALID', 'payload'),))
    assert data == before


@pytest.mark.parametrize('equivalent', [False, True])
def test_legacy_board_edge_collision_behavior_unchanged(equivalent):
    import copy
    from observation_schema import schema
    data = json.loads(REPEATED_RAW)
    for key in ('protocol_version', 'footprint_edges', 'geometry_coverage'):
        del data[key]
    edge_id = data['edges'][0]['uuid']
    data['edges'][1]['uuid'] = '{' + edge_id + '}' if equivalent else edge_id
    before = copy.deepcopy(data)
    assert schema(data, allow_legacy=True) is True
    assert data == before


@pytest.mark.parametrize('variant', ['positive', 'identical', 'equivalent'])
def test_footprint_uuid_identity_and_nonmutation(variant):
    import copy
    from observation_schema import schema
    data = json.loads(REPEATED_RAW)
    assert data['footprint_edges'] == []
    first, second = data['footprints'][0]['pads']
    other = copy.deepcopy(data['footprints'][0])
    other.update(uuid='00000000-0000-0000-0000-000000009999', reference='U2', pads=[second])
    data['footprints'][0]['pads'] = [first]
    data['footprints'].append(other)
    assert len({p['uuid'] for f in data['footprints'] for p in f['pads']}) == 2
    assert schema(data) is True
    original = copy.deepcopy(data)
    if variant != 'positive':
        value = data['footprints'][0]['uuid']
        other['uuid'] = '{' + value + '}' if variant == 'equivalent' else value
        restored = copy.deepcopy(data)
        restored['footprints'][1]['uuid'] = original['footprints'][1]['uuid']
        assert restored == original
    before = copy.deepcopy(data)
    if variant == 'positive':
        assert schema(data) is True
        assert evaluate_outline(json.dumps(data).encode()) == Decision('not_rejected_by_outline_check')
    else:
        with pytest.raises(ValueError, match='^Duplicate footprint UUID$'):
            schema(data)
        assert evaluate_outline(json.dumps(data).encode()) == Decision(
            'rejected', (Diagnostic('SCHEMA_INVALID', 'payload'),))
    assert data == before


def test_equivalent_footprint_uuid_legacy_behavior_unchanged():
    import copy
    from observation_schema import schema
    data = json.loads(REPEATED_RAW)
    assert data['footprint_edges'] == []
    first, second = data['footprints'][0]['pads']
    other = copy.deepcopy(data['footprints'][0])
    other.update(uuid='00000000-0000-0000-0000-000000009999', reference='U2', pads=[second])
    data['footprints'][0]['pads'] = [first]
    data['footprints'].append(other)
    assert len({p['uuid'] for f in data['footprints'] for p in f['pads']}) == 2
    assert schema(data) is True
    other['uuid'] = '{' + data['footprints'][0]['uuid'] + '}'
    for key in ('protocol_version', 'footprint_edges', 'geometry_coverage'):
        del data[key]
    before = copy.deepcopy(data)
    assert schema(data, allow_legacy=True) is True
    assert data == before
