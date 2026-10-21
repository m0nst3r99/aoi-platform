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
                                      digest, 'synthetic-repeated-pads-v1', 'owned-stage'), limits)
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
    """Independent translation oracle fixed before native execution."""
    parent = str(UUID(int=2100))
    pads = [dict(uuid=str(UUID(int=2101+i)), number="1", local_mm=uv,
                 position_mm=world, size_mm=[2,1], layers=['F.Cu','F.Paste','F.Mask'])
            for i,(uv,world) in enumerate([([1,2],[11,12]),([4,3],[14,13])])]
    text = ['(kicad_pcb (version 20240108) (generator "synthetic-evaluation")',
        '(general (thickness 1.6)) (paper "A4")',
        '(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (35 "F.Paste" user)',
        '(37 "F.SilkS" user) (39 "F.Mask" user) (44 "Edge.Cuts" user))',
        '(setup (pad_to_mask_clearance 0))',
        f'(footprint "Synthetic:RepeatedNumbers" (layer "F.Cu") (uuid "{parent}")',
        '(at 10 10 0) (attr smd)',
        '(fp_text reference "U1" (at 0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
        '(fp_text value "SYNTHETIC" (at 0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))']
    for pad in pads:
        u,v=pad['local_mm']
        text.append(f'(pad "1" smd rect (at {u} {v} 0) (size 2 1) '
                    f'(layers "F.Cu" "F.Paste" "F.Mask") (uuid "{pad["uuid"]}"))')
    text.append(')')
    for i,(a,b) in enumerate([((0,0),(20,0)),((20,0),(20,20)),((20,20),(0,20)),((0,20),(0,0))]):
        text.append(f'(gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) '
                    f'(stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{UUID(int=2110+i)}"))')
    pcb=out/'repeated-pads.kicad_pcb'
    pcb.write_text('\n'.join(text+[')'])+'\n',encoding='utf-8')
    expected=dict(tolerance_mm=0.000001,parent_uuid=parent,reference='U1',
        footprint_position_mm=[10,10],footprint_angle_deg=0,footprint_layer='F.Cu',pads=pads,
        formula='Top unrotated footprint: world=(10+u,10+v). (1,2)->(11,12); (4,3)->(14,13). No rotation/mirror normalization.',
        parent_association='Pad is nested under the expected footprint UUID in probe output; not an independent parent accessor.',
        scope='Two distinct source pad UUIDs with identical string number 1 must both survive; not canonical pad records or publication.')
    local.save(out/'oracle.json',expected)
    return pcb,expected


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
    local.save(out/'dependencies-pre-run.json',report['dependencies_sha256'])
    owned = None
    try:
        with tempfile.TemporaryDirectory(prefix='repeated-pads-control-') as owned:
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
            checks['root_exit_zero'] = t['result']['evidence']['root_exit']==0
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
            compare('footprint_edges_empty',data['footprint_edges'],[])
            compare('footprint_count',len(data['footprints']),1)
            fps=[f for f in data['footprints'] if f['uuid']==expected['parent_uuid']]
            compare('parent_uuid_count',len(fps),1)
            if len(fps)!=1:
                raise ValueError('Missing or duplicate expected parent footprint')
            fp=fps[0]
            compare('reference',fp['reference'],expected['reference'])
            compare('footprint_position',fp['position_mm'],expected['footprint_position_mm'],True)
            compare('footprint_angle',fp['angle_deg'],expected['footprint_angle_deg'])
            compare('footprint_layer',fp['layer'],expected['footprint_layer'])
            rows=fp['pads']
            compare('pad_count',len(rows),2)
            compare('pad_uuid_set',sorted(p['uuid'] for p in rows),sorted(p['uuid'] for p in expected['pads']))
            compare('numbers_are_strings',all(isinstance(p['number'],str) for p in rows),True)
            compare('repeated_numbers_preserved',[p['number'] for p in rows],['1','1'])
            for pad in expected['pads']:
                matches=[v for v in rows if v['uuid']==pad['uuid']]
                compare(pad['uuid']+'.count',len(matches),1)
                if len(matches)!=1:
                    continue
                for key,value in pad.items():
                    actual=matches[0].get(key)
                    if key=='layers':
                        actual=sorted(actual);value=sorted(value)
                    compare(pad['uuid']+'.'+key,actual,value,key.endswith('_mm'))
            compare('outline.valid',data['outline']['valid'],True)
            local.save(out/'comparisons.json',comparisons)
            checks['primitive_checks_complete'] = len(rows)==2 and all(
                len([v for v in rows if v['uuid']==p['uuid']])==1 for p in expected['pads'])

    except Exception as error:
        report['diagnostics'].append(dict(type=type(error).__name__,message=str(error)))
    finally:
        checks['fixture_and_oracle_unchanged'] = all(local.sha(out/n)==h for n,h in frozen.items())
        checks['dependencies_unchanged'] = all(local.sha(Path(n))==h for n,h in report['dependencies_sha256'].items())
        checks['staging_removed'] = owned is not None and not Path(owned).exists()
        report['passed'] = all(checks.values()) and not report['diagnostics']
        report['control_outcome'] = 'repeated_pad_numbers_preserved' if report['passed'] else 'control_failed'
        local.save(out/'report.json',report)
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    if sys.argv[1]=='--worker':
        worker(*map(Path,sys.argv[2:5]))
    else:
        sys.exit(main(Path(sys.argv[1]).resolve()))
