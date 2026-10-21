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
