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
                                      digest, 'synthetic-d-outline-v1', 'owned-stage'), limits)
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



def fixture(out):
    """Analytic semicircle oracle authored before native execution."""
    arc = '00000000-0000-0000-0000-000000000501'
    line = '00000000-0000-0000-0000-000000000502'
    pcb = out/'d-outline.kicad_pcb'
    pcb.write_text(f'''(kicad_pcb (version 20240108) (generator "synthetic-evaluation")
(general (thickness 1.6)) (paper "A4")
(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (44 "Edge.Cuts" user))
(setup (pad_to_mask_clearance 0))
(gr_arc (start 10 0) (mid 15 5) (end 10 10)
(stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{arc}"))
(gr_line (start 10 10) (end 10 0)
(stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{line}"))
)
''',encoding='utf-8')
    expected = dict(tolerance_mm=0.000001,
        rationale='Circle (x-10)^2+(y-5)^2=25; midpoint (15,5) selects right semicircle x>=10. '
                  'Extrema x=10..15, y=0..10. Diameter closes one contour with no holes. '
                  'Oracle is analytic source geometry, not native output. No winding claim.',
        edges=[dict(uuid=arc,shape=2,start_mm=[10,0],mid_mm=[15,5],end_mm=[10,10],center_mm=[10,5],radius_mm=5),
               dict(uuid=line,shape=0,start_mm=[10,10],end_mm=[10,0])],
        outline=dict(valid=True,count=1,holes=[0],origin_mm=[10,0],size_mm=[5,10]))
    local.save(out/'oracle.json',expected)
    return pcb, expected


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    pcb, expected = fixture(out)
    frozen = {p.name: local.sha(p) for p in out.iterdir() if p.is_file()}
    local.save(out/'pre-run-hashes.json', frozen)
    checks = {k: False for k in ('transport','cleanup','schema','build','input_hash',
        'primitive_checks_complete','fixture_and_oracle_unchanged','staging_removed')}
    report = dict(passed=False, diagnostics=[], pre_run_hashes=frozen, checks=checks)
    report['dependencies_sha256'] = {str(p):local.sha(p) for p in
        [Path(__file__).resolve(),local.EXECUTABLE,HERE/'runner.py',HERE/'models.py',HERE/'winapi.py',
         HERE/'kicad_staged_helper.py',HERE/'kicad_local.py',local.READER/'probe.py',local.READER/'run.py', local.READER/'observation_schema.py']}
    owned = None
    try:
        with tempfile.TemporaryDirectory(prefix='d-outline-control-') as owned:
            stage = Path(owned)/'stage.pcb'
            stage.write_bytes(pcb.read_bytes())
            if local.sha(stage)!=frozen[pcb.name]:
                raise RuntimeError('stage hash mismatch; no launch')
            temp = Path(owned)/'helper'
            temp.mkdir()
            command = [sys._base_executable,str(Path(__file__).resolve()),'--worker',str(out),str(stage),str(temp)]
            report.update(command=command,watchdog_seconds=45)
            with (out/'watchdog.stdout').open('wb') as a, (out/'watchdog.stderr').open('wb') as b:
                proc = subprocess.Popen(command,stdout=a,stderr=b,creationflags=0x08000000)
                try:
                    report['worker_exit'] = proc.wait(timeout=45)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
                    raise RuntimeError('watchdog timeout; cleanup not assumed')
            if report['worker_exit']!=0:
                raise RuntimeError('worker failed')
            t = json.loads((out/'transport.json').read_text())
            checks['transport'] = t['success']
            checks['cleanup'] = (t['result']['evidence']['cleanup_state']=='cleaned'
                and t['result']['evidence']['active_processes']==0
                and all(t[k] for k in ('caller_handle_usable','stage_unchanged','helper_temp_empty')))
            if not t['success']:
                raise RuntimeError('transport failure; diagnostic prefixes not parsed')
            data = json.loads((out/'stdout.bin').read_bytes())
            spec = importlib.util.spec_from_file_location('harness',local.READER/'run.py')
            harness = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(harness)
            checks['schema'] = harness.schema(data)
            checks['build'] = data['build']=='10.0.7'
            checks['input_hash'] = data['input_sha256']==frozen[pcb.name]
            local.save(out/'actual-expected.json',dict(actual=data,expected=expected))
            comparisons = []
            def compare(name, actual, wanted, numeric=False):
                if numeric:
                    aa = actual if isinstance(actual,list) else [actual]
                    ww = wanted if isinstance(wanted,list) else [wanted]
                    delta = [abs(x-y) for x,y in zip(aa,ww)]
                    passed = len(aa)==len(ww) and all(d<=expected['tolerance_mm'] for d in delta)
                else:
                    delta = None
                    passed = actual==wanted
                checks[name] = passed
                comparisons.append(dict(name=name,actual=actual,expected=wanted,
                    absolute_error_mm=delta,passed=passed))
            ids = [e['uuid'] for e in data['edges']]
            compare('edge_uuid_set',sorted(ids),sorted(e['uuid'] for e in expected['edges']))
            for e in expected['edges']:
                matches = [v for v in data['edges'] if v['uuid']==e['uuid']]
                compare(e['uuid']+'.count',len(matches),1)
                if len(matches)!=1:
                    continue
                for key,value in e.items():
                    compare(e['uuid']+'.'+key,matches[0].get(key),value,key.endswith('_mm'))
            for key,value in expected['outline'].items():
                compare('outline.'+key,data['outline'].get(key),value,key.endswith('_mm'))
            local.save(out/'comparisons.json',comparisons)
            checks['primitive_checks_complete'] = all(len([v for v in data['edges'] if v['uuid']==e['uuid']])==1 for e in expected['edges'])
    except Exception as error:
        report['diagnostics'].append(dict(type=type(error).__name__,message=str(error)))
    finally:
        checks['fixture_and_oracle_unchanged'] = all(local.sha(out/n)==h for n,h in frozen.items())
        checks['staging_removed'] = owned is not None and not Path(owned).exists()
        report['passed'] = all(checks.values()) and not report['diagnostics']
        local.save(out/'report.json',report)
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    if sys.argv[1]=='--worker':
        worker(*map(Path,sys.argv[2:5]))
    else:
        sys.exit(main(Path(sys.argv[1]).resolve()))
