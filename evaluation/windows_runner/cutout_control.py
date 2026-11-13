"""Single synthetic native control; explicit source geometry, no geometry parser."""
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from uuid import UUID

import kicad_local as local

HERE = Path(__file__).resolve().parent
# Source-native mm. Outer [0,20]x[0,10], inner [8,12]x[4,6].
SEGMENTS = [
    ([0, 0], [20, 0]), ([20, 0], [20, 10]),
    ([20, 10], [0, 10]), ([0, 10], [0, 0]),
    ([8, 4], [8, 6]), ([8, 6], [12, 6]),
    ([12, 6], [12, 4]), ([12, 4], [8, 4]),
]
EXPECTED = {
    "edges": [{"uuid": str(UUID(int=i+1)), "shape": 0, "start_mm": a, "end_mm": b}
              for i, (a, b) in enumerate(SEGMENTS)],
    "outline": {"valid": True, "count": 1, "holes": [1],
                "origin_mm": [0, 0], "size_mm": [20, 10]},
}


def worker(out, stage, temp):
    import msvcrt
    from models import Limits, Request, StagedInput, ExecutionSuccess
    from runner import run_bounded_worker
    limits = Limits('kicad-local-test-v1', 16*1024**2, 2*1024**2, 256*1024,
                    2*1024**2+256*1024, 65536, 30000, 5000,
                    1024**3, 1536*1024**2, 4)
    env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR') if k in os.environ}
    env.update(TEMP=str(temp), TMP=str(temp))
    digest = local.sha(stage)
    argv = ('-u', str(HERE/'kicad_staged_helper.py'), '{staged_handle}',
            str(stage.stat().st_size), digest, str(temp), str(local.READER/'probe.py'))
    with stage.open('rb') as stream:
        request = Request(str(local.EXECUTABLE), argv, str(temp), tuple(env.items()),
                          StagedInput(msvcrt.get_osfhandle(stream.fileno()), stage.stat().st_size,
                                      digest, 'synthetic-rectangular-cutout-v1', 'owned-stage'), limits)
        result = run_bounded_worker(request)
        handle_ok = os.fstat(stream.fileno()).st_size == stage.stat().st_size
    success = isinstance(result, ExecutionSuccess)
    record = asdict(result)
    for key in ('stdout', 'stderr', 'diagnostic_stdout_prefix', 'diagnostic_stderr_prefix'):
        if key in record:
            (out/(key+'.bin')).write_bytes(record.pop(key))
    local.save(out/'transport.json', dict(success=success, result=record, limits=asdict(limits),
               argv=argv, caller_handle_usable=handle_ok, stage_unchanged=local.sha(stage)==digest,
               helper_temp_empty=not any(temp.iterdir())))


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    pcb = out/'rectangular-cutout.kicad_pcb'
    text = ['(kicad_pcb (version 20240108) (generator "synthetic-evaluation")',
            '(general (thickness 1.6)) (paper "A4")',
            '(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (44 "Edge.Cuts" user))',
            '(setup (pad_to_mask_clearance 0))']
    for edge in EXPECTED['edges']:
        a, b = edge['start_mm'], edge['end_mm']
        text.append(f'(gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) '
                    f'(stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{edge["uuid"]}"))')
    pcb.write_text('\n'.join(text+[')'])+'\n', encoding='utf-8')
    local.save(out/'oracle.json', dict(expected=EXPECTED,
        rationale='Two disjoint closed axis-aligned loops, inner strictly inside outer: API outer count 1, HoleCount(0)=1. Centerline bbox, not stroke width.',
        scope='Board-level line primitives only; no footprints or generalized topology claim.'))
    digest = local.sha(pcb)
    report = dict(passed=False, diagnostics=[], source_sha256=digest, command=sys.argv,
                  watchdog_seconds=45, required_checks=['schema', 'build', 'input_hash',
                  'eight_source_segments', 'outline', 'no_footprints', 'cleanup', 'fixture_unchanged'])
    report['dependencies_sha256'] = {str(p): local.sha(p) for p in
        (Path(__file__).resolve(), local.EXECUTABLE, HERE/'runner.py', HERE/'winapi.py',
         HERE/'models.py', HERE/'kicad_staged_helper.py', local.READER/'probe.py', local.READER/'run.py', local.READER/'observation_schema.py')}
    owned = None
    try:
        with tempfile.TemporaryDirectory(prefix='cutout-control-') as owned:
            stage = Path(owned)/'stage.pcb'
            stage.write_bytes(pcb.read_bytes())
            temp = Path(owned)/'helper'
            temp.mkdir()
            command = [sys._base_executable, str(Path(__file__).resolve()), '--worker',
                       str(out), str(stage), str(temp)]
            report['worker_command'] = command
            with (out/'watchdog.stdout').open('wb') as a, (out/'watchdog.stderr').open('wb') as b:
                proc = subprocess.Popen(command, stdout=a, stderr=b, creationflags=0x08000000)
                try:
                    report['worker_exit'] = proc.wait(timeout=45)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
                    raise RuntimeError('watchdog timeout; cleanup unconfirmed')
            if report['worker_exit'] != 0:
                raise RuntimeError('worker failed')
            transport = json.loads((out/'transport.json').read_text())
            report['transport_success'] = transport['success']
            if not transport['success']:
                raise RuntimeError('transport failure; prefixes not parsed')
            data = json.loads((out/'stdout.bin').read_bytes())
            spec = importlib.util.spec_from_file_location('harness', local.READER/'run.py')
            harness = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(harness)
            actual = {'edges': data.get('edges'), 'outline': data.get('outline')}
            local.save(out/'actual-expected.json', dict(actual=actual, expected=EXPECTED))
            report['checks'] = dict(schema=harness.schema(data), build=data['build']=='10.0.7',
                input_hash=data['input_sha256']==digest,
                eight_source_segments=data['edges']==EXPECTED['edges'],
                outline=data['outline']==EXPECTED['outline'], no_footprints=data['footprints']==[],
                cleanup=transport['result']['evidence']['cleanup_state']=='cleaned'
                    and transport['result']['evidence']['active_processes']==0
                    and all(transport[k] for k in ('caller_handle_usable','stage_unchanged','helper_temp_empty')))
    except Exception as error:
        report['diagnostics'].append(dict(type=type(error).__name__, message=str(error)))
    finally:
        report['owner_staging_removed'] = owned is not None and not Path(owned).exists()
        report.setdefault('checks', {})['fixture_unchanged'] = local.sha(pcb)==digest
        report['passed'] = (all(report['checks'].get(k) is True for k in report['required_checks'])
                            and report['owner_staging_removed'] and not report['diagnostics'])
        local.save(out/'report.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    if sys.argv[1]=='--worker':
        worker(*map(Path, sys.argv[2:5]))
    else:
        main(Path(sys.argv[1]).resolve())
