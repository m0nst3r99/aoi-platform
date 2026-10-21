"""Portable regressions: subprocesses are faked, no KiCad or C:/dev fixture needed."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent


def execute(tmp_path, monkeypatch, mutation=None, status=0, negative=None, raw=None,
            negative_payload=None, cli_status=0, v2=False, legacy=True):
    sandbox = tmp_path / "harness"
    sandbox.mkdir()
    for name in ("run.py", "observation_schema.py", "outline_decision.py"):
        shutil.copyfile(HERE / name, sandbox / name)
    fixture = tmp_path / "fixture"
    (fixture / "source").mkdir(parents=True)
    (fixture / "source/Edgeberry.kicad_pcb").write_text("synthetic")
    data = json.loads((HERE / "pcbnew.stdout.txt").read_bytes())
    population = [dict(uuid=f["uuid"], reference=f["reference"], value=f["value"],
                       footprint=f["footprint"], dnp=f["dnp"],
                       exclude_from_bom=f["exclude_from_bom"],
                       exclude_from_position=f["exclude_from_position"],
                       at_raw=" ".join(map(str, f["position_mm"] + [f["angle_deg"]])),
                       layer=f['layer'], assembly_target_eligible=i < 28,
                       retain_fiducial_data=28 <= i < 31) for i, f in enumerate(data['footprints'])]
    (fixture / "population.json").write_text(json.dumps(population))
    original_digest = hashlib.file_digest
    def digest(stream, algorithm):
        if Path(stream.name).name == 'Edgeberry.kicad_pcb':
            class Fixed:
                def hexdigest(self):
                    return data['input_sha256']
            return Fixed()
        return original_digest(stream, algorithm)
    monkeypatch.setattr(hashlib, 'file_digest', digest)
    if v2:
        data.update(protocol_version=2, footprint_edges=[], geometry_coverage=dict(
            board_edges_scope='board-drawings-only',
            footprint_edges_scope='footprint-graphical-items-only', geometry_complete=False))
    if mutation:
        mutation(data)
    def fake(argv, **kwargs):
        name = str(argv[-1])
        if name.endswith('Edgeberry.kicad_pcb'):
            if status == 'timeout':
                raise subprocess.TimeoutExpired(argv, 30, output=raw)
            return subprocess.CompletedProcess(argv, status, raw if raw is not None else json.dumps(data).encode(), b'')
        if name.endswith('malformed.kicad_pcb') or name.endswith('missing.kicad_pcb'):
            if negative == 'timeout':
                raise subprocess.TimeoutExpired(argv, 30)
            kind = 'NATIVE_LOAD_REJECTED' if name.endswith('malformed.kicad_pcb') else 'SOURCE_NOT_FOUND'
            return subprocess.CompletedProcess(argv, negative if negative is not None else 2,
                negative_payload if negative_payload is not None else json.dumps({'outcome': 'rejected', 'code': kind}).encode(), b'')
        return subprocess.CompletedProcess(argv, cli_status, b'10.0.7\n', b'')
    monkeypatch.setattr(subprocess, 'run', fake)
    # The preserved baseline is unversioned; replay is deliberately explicit.
    monkeypatch.setattr(sys, 'argv', [str(sandbox / 'run.py'), str(fixture),
                                    *(['--allow-legacy-protocol'] if legacy else []),
                                    '--output', str(sandbox / 'new')])
    try:
        runpy.run_path(str(sandbox / 'run.py'), run_name='__main__')
    except SystemExit as error:
        code = error.code
    else:
        code = 0
    reports = list(sandbox.rglob('results.json'))
    assert reports, 'failure must still persist diagnostics'
    return code, json.loads(reports[0].read_text())


@pytest.mark.parametrize('status', [1, 'timeout'])
def test_positive_probe_failure_never_passes(tmp_path, monkeypatch, status):
    code, report = execute(tmp_path, monkeypatch, status=status)
    assert code != 0
    assert report.get('diagnostics')


@pytest.mark.parametrize('negative', [0, 1, -1073741819, 'timeout'])
def test_negative_probe_requires_exact_rejection(tmp_path, monkeypatch, negative):
    code, _ = execute(tmp_path, monkeypatch, negative=negative)
    assert code != 0


@pytest.mark.parametrize('mutation', [
    lambda d: d['outline'].update(valid=False),
    lambda d: d['outline'].update(count=2),
    lambda d: d['outline'].update(holes=[1]),
    lambda d: d['footprints'].append(copy.deepcopy(d['footprints'][0])),
    lambda d: d['footprints'][0].update(uuid='11111111-1111-1111-1111-111111111111'),
    lambda d: next(f for f in d['footprints'] if f['reference']=='R8').update(reference='missing-R8'),
    lambda d: next(f for f in d['footprints'] if f['reference']=='R7').update(reference='missing-R7'),
    lambda d: d['footprints'][0].pop('attributes'),
    lambda d: d['footprints'][0]['pads'][0].pop('local_mm'),
    lambda d: d['outline'].update(size_mm=[float('nan'), 90]),
])
def test_geometry_and_identity_not_bbox_or_dict_only(tmp_path, monkeypatch, mutation):
    code, _ = execute(tmp_path, monkeypatch, mutation=mutation)
    assert code != 0


@pytest.mark.parametrize('raw', [b'{', b'{}'])
def test_bad_json_persists_failure(tmp_path, monkeypatch, raw):
    code, report = execute(tmp_path, monkeypatch, raw=raw)
    assert code != 0
    assert report.get('diagnostics')


def test_control_success(tmp_path, monkeypatch):
    code, report = execute(tmp_path, monkeypatch)
    assert code == 0
    assert set(report['required_checks']) == set(report['checks'])
    assert all(report['checks'].values())


@pytest.mark.parametrize('payload', [b'{', b'{}', b'{"outcome":"rejected","code":"OTHER"}'])
def test_negative_invalid_diagnostic(tmp_path, monkeypatch, payload):
    code, report = execute(tmp_path, monkeypatch, negative_payload=payload)
    assert code != 0
    assert not report['checks']['malformed_rejection']


def test_cli_failure_is_required(tmp_path, monkeypatch):
    code, report = execute(tmp_path, monkeypatch, cli_status=1)
    assert code != 0
    assert not report['checks']['cli-version']


def test_v2_outline_rejection_is_typed(tmp_path, monkeypatch):
    code, report = execute(tmp_path, monkeypatch, v2=True, legacy=False,
                           mutation=lambda d: d['outline'].update(valid=False))
    assert code != 0 and report['outcome'] == 'failed'
    decision = report['outline_decision']
    assert decision['status'] == 'rejected'
    diagnostic = decision['diagnostics'][0]
    assert diagnostic == dict(code='OUTLINE_INVALID', field='outline.valid', build='10.0.7',
        input_sha256='67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0')
    assert any(d['code']=='OUTLINE_INVALID' for d in report['diagnostics'])
    assert not report['checks']['outline_valid']
    assert report['checks']['outline_count']  # Existing checks still run.


@pytest.mark.parametrize('raw', [b'{broken', b'[]'])
def test_entrypoint_json_rejected_by_decision(tmp_path, monkeypatch, raw):
    code, report = execute(tmp_path, monkeypatch, raw=raw)
    assert code != 0
    assert report['outline_decision']['diagnostics'][0]['code'] == 'SCHEMA_INVALID'


@pytest.mark.parametrize('mutation', [
    lambda d: d['outline'].pop('valid'),
    lambda d: d['outline'].update(valid=1),
    lambda d: d.pop('footprint_edges'),
    lambda d: d.pop('protocol_version'),
])
def test_v2_malformed_never_legacy_bypass(tmp_path, monkeypatch, mutation):
    code, report = execute(tmp_path, monkeypatch, v2=True, legacy=True, mutation=mutation)
    assert code != 0 and report['outcome']=='failed'
    assert report['outline_decision']['status']=='rejected'
    assert report['outline_decision']['diagnostics'][0]['code']=='SCHEMA_INVALID'


def test_v2_intermediate_does_not_override_oracle(tmp_path, monkeypatch):
    code, report = execute(tmp_path, monkeypatch, v2=True, legacy=False,
                           mutation=lambda d: d['outline'].update(count=2))
    assert code != 0 and report['outcome']=='failed'
    assert report['outline_decision']==dict(status='not_rejected_by_outline_check',diagnostics=[])
    assert not report['checks']['outline_count']


@pytest.mark.parametrize('status', [1, 'timeout'])
def test_transport_partial_output_is_not_observation(tmp_path, monkeypatch, status):
    raw=(HERE.parent/'windows_runner/evidence/bow-tie-01/stdout.bin').read_bytes()
    code, report = execute(tmp_path, monkeypatch, status=status, raw=raw, v2=True)
    assert code != 0
    assert report['outline_decision'] is None
    assert any(d['code']=='PROBE_FAILED' for d in report['diagnostics'])
    assert not any(d['code']=='OUTLINE_INVALID' for d in report['diagnostics'])


def test_legacy_explicit_not_applicable(tmp_path, monkeypatch):
    code, report = execute(tmp_path, monkeypatch)
    assert code==0
    assert report['outline_decision']==dict(status='not_applicable_historical_replay',diagnostics=[])
    assert report['footprint_edge_coverage']=='unknown'


def test_legacy_without_optin_is_rejected(tmp_path, monkeypatch):
    code, report = execute(tmp_path, monkeypatch, legacy=False)
    assert code != 0
    assert report['outline_decision']['diagnostics'][0]['code']=='SCHEMA_INVALID'


def test_v2_all_checks_still_required(tmp_path, monkeypatch):
    code, report = execute(tmp_path, monkeypatch, v2=True, legacy=False)
    assert code==0 and all(report['checks'].values())
    assert report['outline_decision']['status']=='not_rejected_by_outline_check'


@pytest.mark.parametrize('v2,status,decision_used', [(True, 0, True), (False, 0, False), (True, 'timeout', False)])
def test_dependency_hashes_follow_executed_path(tmp_path, monkeypatch, v2, status, decision_used):
    _, report = execute(tmp_path, monkeypatch, v2=v2, status=status)
    hashes = report['dependencies_sha256']
    expected = {'run.py', 'observation_schema.py'}
    if decision_used:
        expected.add('outline_decision.py')
    assert {Path(p).name for p in hashes} == expected
    for path, digest in hashes.items():
        assert digest == hashlib.sha256(Path(path).read_bytes()).hexdigest()
