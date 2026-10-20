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
            negative_payload=None, cli_status=0):
    sandbox = tmp_path / "harness"
    sandbox.mkdir()
    shutil.copyfile(HERE / "run.py", sandbox / "run.py")
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
    if mutation:
        mutation(data)
    def fake(argv, **kwargs):
        name = str(argv[-1])
        if name.endswith('Edgeberry.kicad_pcb'):
            if status == 'timeout':
                raise subprocess.TimeoutExpired(argv, 30)
            return subprocess.CompletedProcess(argv, status, raw if raw is not None else json.dumps(data).encode(), b'')
        if name.endswith('malformed.kicad_pcb') or name.endswith('missing.kicad_pcb'):
            if negative == 'timeout':
                raise subprocess.TimeoutExpired(argv, 30)
            kind = 'NATIVE_LOAD_REJECTED' if name.endswith('malformed.kicad_pcb') else 'SOURCE_NOT_FOUND'
            return subprocess.CompletedProcess(argv, negative if negative is not None else 2,
                negative_payload if negative_payload is not None else json.dumps({'outcome': 'rejected', 'code': kind}).encode(), b'')
        return subprocess.CompletedProcess(argv, cli_status, b'10.0.7\n', b'')
    monkeypatch.setattr(subprocess, 'run', fake)
    monkeypatch.setattr(sys, 'argv', [str(sandbox / 'run.py'), str(fixture), '--output', str(sandbox / 'new')])
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
