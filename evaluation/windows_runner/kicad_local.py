"""One supervised local r2 evaluation, not an adapter. Run with a fresh output path."""
from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
READER = HERE.parent/'kicad-reader'
FIXTURE = Path('C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r2')
EXECUTABLE = Path('C:/Program Files/KiCad/10.0/bin/python.exe')
EXPECTED = '67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True)+'\n', encoding='utf-8')


def snapshot():
    return {p.relative_to(FIXTURE).as_posix(): sha(p) for p in sorted(FIXTURE.rglob('*')) if p.is_file()}


def worker(case, directory, stage, temp):
    import msvcrt
    from models import Limits, Request, StagedInput, ExecutionSuccess
    from runner import run_bounded_worker
    # Explicit supervised test policy; never loosened automatically.
    limits = Limits('kicad-local-test-v1', 16*1024**2, 2*1024**2, 256*1024,
                    2*1024**2+256*1024, 65536, 30000, 5000,
                    1024**3, 1536*1024**2, 4)
    digest = sha(stage)
    env = {key: os.environ[key] for key in ('SystemRoot', 'WINDIR') if key in os.environ}
    minimal = dict(env)
    if case == 'B':
        env = dict(os.environ)
    env.update(TEMP=str(temp), TMP=str(temp))
    minimal.update(TEMP=str(temp), TMP=str(temp))
    argv = ('-u', str(HERE/'kicad_staged_helper.py'), '{staged_handle}',
            str(stage.stat().st_size), digest, str(temp), str(READER/'probe.py'))
    with stage.open('rb') as source:
        request = Request(str(EXECUTABLE), argv, str(temp), tuple(sorted(env.items())),
                          StagedInput(msvcrt.get_osfhandle(source.fileno()), stage.stat().st_size,
                                      '0'*64 if case == 'hash-mismatch' else digest,
                                      'REAL-PCB-01-r2-pcb', 'explicit-local-stage'), limits)
        result = run_bounded_worker(request)
        caller_handle_usable = not source.closed and os.fstat(source.fileno()).st_size == request.staged.size
    good = isinstance(result, ExecutionSuccess)
    stdout = result.stdout if good else result.diagnostic_stdout_prefix
    stderr = result.stderr if good else result.diagnostic_stderr_prefix
    prefix = 'success' if good else 'unusable-diagnostic'
    (directory/(prefix+'.stdout')).write_bytes(stdout)
    (directory/(prefix+'.stderr')).write_bytes(stderr)
    record = asdict(result)
    for key in ('stdout', 'stderr', 'diagnostic_stdout_prefix', 'diagnostic_stderr_prefix'):
        record.pop(key, None)
    save(directory/'transport.json', dict(success=good, result=record, limits=asdict(limits),
         argv=argv, environment_mode='host' if case=='B' else 'minimal',
         environment_different_names=sorted(k for k in set(env)|set(minimal) if env.get(k)!=minimal.get(k)),
         executable=str(EXECUTABLE), cwd=str(temp),
         caller_handle_usable=caller_handle_usable, stage_unchanged=sha(stage)==digest,
         helper_temp_empty=not any(temp.iterdir())))


def compare(raw):
    spec = importlib.util.spec_from_file_location('existing_reader_harness', READER/'run.py')
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    data = json.loads(raw)
    harness.schema(data)
    accepted = json.loads((READER/'runs/errata-r2-01/pcbnew.stdout.txt').read_bytes())
    old_report = json.loads((READER/'runs/errata-r2-01/results.json').read_bytes())
    population = json.loads((FIXTURE/'population.json').read_text(encoding='utf-8-sig'))
    rows = data['footprints']
    ids = [row['uuid'] for row in rows]
    by_id = {row['uuid']: row for row in rows}
    checks = dict(schema=True, accepted_baseline_passed=old_report['outcome']=='passed',
                  source_hash=data['input_sha256']==EXPECTED, build=data['build']=='10.0.7',
                  format=data['format_version']==20260206,
                  outline_valid=data['outline']['valid'] is True,
                  outline_count=data['outline']['count']==1,
                  outline_holes=data['outline']['holes']==[0],
                  outline_bbox=data['outline']['origin_mm']==[83.649,51.772] and data['outline']['size_mm']==[135.,90.],
                  footprint_count=len(rows)==57, unique_uuid=len(ids)==len(set(ids)),
                  uuid_set=set(ids)=={p['uuid'] for p in population},
                  population_fields=all(by_id[p['uuid']][k]==p[k] for p in population for k in
                      ('reference','value','footprint','dnp','exclude_from_bom','exclude_from_position')),
                  pose_side=all(by_id[p['uuid']]['position_mm']==[float(x) for x in p['at_raw'].split()[:2]]
                      and (by_id[p['uuid']]['angle_deg']-(float(p['at_raw'].split()[2]) if len(p['at_raw'].split())>2 else 0))%360==0
                      and by_id[p['uuid']]['layer']==p['layer'].strip('"') for p in population),
                  R7_R8_presence=all(sum(f['reference']==ref for f in rows)==1 for ref in ('R7','R8')),
                  R7_R8_values=all(f['value']=='270R' for f in rows if f['reference'] in ('R7','R8')),
                  all_observations_equal_accepted=data==accepted)
    pads = [p for f in rows if f['reference']=='R7' for p in f['pads'] if p['number']=='1']
    checks['R7_pad_oracle'] = len(pads)==1 and pads[0]['position_mm']==[99.1615,70.272]
    return dict(checks=checks, passed=all(checks.values()), observed_build=data['build'])


def ab(output):
    """Exactly two sequential native runs; same cwd, budgets and executable."""
    import shutil
    output.mkdir(parents=True, exist_ok=False)
    before = snapshot()
    report = dict(cases={}, diagnostics=[], fixture_before=before, watchdog_seconds=45,
                  sequential_not_simultaneous=True, command=sys.argv)
    paths = [EXECUTABLE, HERE/'kicad_staged_helper.py', HERE/'kicad_local.py',
             HERE/'runner.py', HERE/'models.py', HERE/'winapi.py', READER/'probe.py']
    report['dependencies_sha256'] = {str(p):sha(p) for p in paths}
    root = None
    try:
        with tempfile.TemporaryDirectory(prefix='kicad-ab-') as owned:
            root = Path(owned)
            stage = root/'stage.pcb'
            source = FIXTURE/'source/Edgeberry.kicad_pcb'
            assert source.stat().st_size <= 16*1024**2 and sha(source)==EXPECTED
            with source.open('rb') as src, stage.open('xb') as dst:
                count = 0
                while chunk := src.read(65536):
                    count += len(chunk)
                    if count > 16*1024**2: raise ValueError('staging budget')
                    dst.write(chunk)
            assert sha(stage)==EXPECTED
            report['source'] = dict(sha256=sha(stage), size=stage.stat().st_size)
            temp = root/'work'
            for case in ('A','B'):
                temp.mkdir()
                directory = output/case
                directory.mkdir()
                command = [sys._base_executable, str(Path(__file__).resolve()), '--worker',
                           case, str(directory), str(stage), str(temp)]
                with (directory/'watchdog.stdout').open('wb') as out, (directory/'watchdog.stderr').open('wb') as err:
                    proc = subprocess.Popen(command, stdout=out, stderr=err, creationflags=0x08000000)
                    try:
                        status = proc.wait(timeout=45)
                    except subprocess.TimeoutExpired:
                        proc.kill(); proc.wait(timeout=5)
                        raise RuntimeError('watchdog timeout; no further native runs')
                if status: raise RuntimeError(f'worker {case} exit {status}')
                record = json.loads((directory/'transport.json').read_text())
                report['cases'][case] = dict(transport=record['success'],
                    runner_cleanup=record['result']['evidence']['cleanup_state'],
                    helper_temp_empty=record['helper_temp_empty'], comparison='not-run')
                if record['success']:
                    comparison = compare((directory/'success.stdout').read_bytes())
                    save(directory/'comparison.json', comparison)
                    report['cases'][case]['comparison'] = comparison['passed']
                if record['result']['evidence']['cleanup_state']!='cleaned':
                    raise RuntimeError('runner cleanup unconfirmed; stop')
                # Only this explicitly owned directory, restored to empty at the same path.
                assert temp.resolve().parent==root.resolve() and temp.name=='work'
                shutil.rmtree(temp)
                report['cases'][case]['owner_temp_removed'] = not temp.exists()
    except Exception as error:
        report['diagnostics'].append(dict(type=type(error).__name__, message=str(error)))
    finally:
        report['staging_removed'] = root is not None and not root.exists()
        report['fixture_after'] = snapshot()
        report['fixture_unchanged'] = before==report['fixture_after']
        save(output/'report.json', report)
    print(json.dumps(report['cases']))


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(passed=False, diagnostics=[], command=sys.argv, python=sys.version,
                  platform=platform.platform(), cases={}, watchdog_seconds=45)
    before = snapshot()
    report['fixture_before'] = before
    paths = [EXECUTABLE, HERE/'kicad_staged_helper.py', HERE/'kicad_local.py', READER/'probe.py',
             READER/'run.py', READER/'runs/errata-r2-01/pcbnew.stdout.txt', READER/'runs/errata-r2-01/results.json',
             HERE/'runner.py', HERE/'winapi.py', HERE/'models.py']
    try:
        report['dependencies_sha256'] = {str(p):sha(p) for p in paths}
        source = FIXTURE/'source/Edgeberry.kicad_pcb'
        assert sha(source)==EXPECTED
        assert 0 < source.stat().st_size <= 16*1024**2
        with tempfile.TemporaryDirectory(prefix='kicad-local-') as owned:
            root = Path(owned)
            stage = root/'stage.pcb'
            with source.open('rb') as original, stage.open('xb') as target:
                count = 0
                while chunk := original.read(65536):
                    count += len(chunk)
                    if count > 16*1024**2: raise ValueError('staging budget')
                    target.write(chunk)
            assert sha(stage)==EXPECTED and stage.stat().st_size==source.stat().st_size
            report['staged'] = dict(size=stage.stat().st_size, sha256=sha(stage))
            for case in ('hash-mismatch', 'control'):
                directory = output/case
                directory.mkdir()
                temp = root/case
                temp.mkdir()
                command = [sys._base_executable, str(Path(__file__).resolve()), '--worker', case,
                           str(directory), str(stage), str(temp)]
                with (directory/'watchdog.stdout').open('wb') as out, (directory/'watchdog.stderr').open('wb') as err:
                    proc = subprocess.Popen(command, stdout=out, stderr=err, creationflags=0x08000000)
                    try:
                        status = proc.wait(timeout=45)
                    except subprocess.TimeoutExpired:
                        proc.kill(); proc.wait(timeout=5)
                        raise RuntimeError('independent watchdog timeout; cleanup not proven')
                if status != 0: raise RuntimeError(f'{case}: worker exit {status}')
                record = json.loads((directory/'transport.json').read_text())
                ev = record['result']['evidence']
                cleanup = ev['cleanup_state']=='cleaned' and all(record[k] for k in
                    ('caller_handle_usable','stage_unchanged','helper_temp_empty'))
                if case == 'hash-mismatch':
                    passed = not record['success'] and ev['root_pid'] is None and not ev['resumed'] and any(
                        x['code']=='STAGED_INPUT_MISMATCH' for x in record['result']['issues'])
                    report['cases'][case] = dict(passed=passed, cleanup=cleanup, no_launch=ev['root_pid'] is None)
                else:
                    report['cases'][case] = dict(transport=record['success'], cleanup=cleanup, protocol_comparison=False)
                    if not record['success']: raise RuntimeError('transport failure; diagnostic prefixes not parsed')
                    comparison = compare((directory/'success.stdout').read_bytes())
                    save(directory/'comparison.json', comparison)
                    report['cases'][case]['protocol_comparison'] = comparison['passed']
                if not cleanup: raise RuntimeError('cleanup or ownership unconfirmed')
        report['staging_removed'] = not root.exists()
        report['passed'] = (report['cases']['hash-mismatch']['passed'] and
                            report['cases']['control']['protocol_comparison'] and report['staging_removed'])
    except Exception as error:
        report['diagnostics'].append(dict(type=type(error).__name__, message=str(error)))
    finally:
        report['fixture_after'] = snapshot()
        report['fixture_unchanged'] = before==report['fixture_after']
        report['passed'] = report['passed'] and report['fixture_unchanged']
        save(output/'report.json', report)
    print(json.dumps(dict(passed=report['passed'], cases=report['cases'], diagnostics=report['diagnostics'])))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    if sys.argv[1]=='--worker':
        worker(sys.argv[2], *map(Path, sys.argv[3:6]))
    elif sys.argv[1]=='--ab':
        ab(Path(sys.argv[2]).resolve())
    else:
        raise SystemExit(main(Path(sys.argv[1]).resolve()))
