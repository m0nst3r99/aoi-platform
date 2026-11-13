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
                                      digest, 'synthetic-footprint-edges-v1', 'owned-stage'), limits)
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
    """Freeze detection oracle from authored items, not native outline/bbox."""
    text = ['(kicad_pcb (version 20240108) (generator "synthetic-evaluation")',
            '(general (thickness 1.6)) (paper "A4")',
            '(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (36 "B.SilkS" user)',
            '(37 "F.SilkS" user) (44 "Edge.Cuts" user))',
            '(setup (pad_to_mask_clearance 0))']
    expected = []
    for i, (side, origin, start, end) in enumerate([
            ('F', [10,10], [1,2], [4,3]), ('B', [30,20], [-2,1], [1,5])]):
        parent, uid = str(UUID(int=100+i)), str(UUID(int=400+i))
        expected.append(dict(uuid=uid, parent_footprint_uuid=parent, shape=0,
            primitive_type='segment', layer='Edge.Cuts', source_accessor='FOOTPRINT.GraphicalItems',
            coordinate_space='native-api-unclassified', endpoint_accessor='PCB_SHAPE.GetStart/GetEnd',
            file_local_start_mm=start, file_local_end_mm=end,
            file_parent_position_mm=origin, file_parent_angle_deg=90, file_parent_layer=side+'.Cu'))
        text += [f'(footprint "Synthetic:LocalEdge" (layer "{side}.Cu") (uuid "{parent}")',
                 f'(at {origin[0]} {origin[1]} 90) (attr smd)',
                 f'(fp_line (start {start[0]} {start[1]}) (end {end[0]} {end[1]}) '
                 f'(stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid}")))']
    board_ids = []
    for i, (a,b) in enumerate([((0,0),(40,0)),((40,0),(40,30)),((40,30),(0,30)),((0,30),(0,0))]):
        uid = str(UUID(int=300+i))
        board_ids.append(uid)
        text.append(f'(gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) '
                    f'(stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid}"))')
    pcb = out/'footprint-edges.kicad_pcb'
    pcb.write_text('\n'.join(text+[')'])+'\n', encoding='utf-8')
    local.save(out/'oracle.json', dict(expected_footprint_edges=expected, board_edge_uuids=board_ids,
        expected_count=2, board_rectangle_mm=[40,30],
        scope='Detection only. File-local endpoints are source declarations, NOT expected API endpoints. '
              'No coordinate equivalence, bottom transform, native outline validity or bbox inference. '
              'Open local segments may invalidate the combined native outline; retain actual.'))
    return pcb, expected, board_ids


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    pcb, expected, board_ids = fixture(out)
    frozen = {p.name: local.sha(p) for p in out.iterdir() if p.is_file()}
    local.save(out/'pre-run-hashes.json', frozen)
    checks = {k: False for k in ('transport','cleanup','schema','build','input_hash',
        'item_uuid_set','board_edges_separate','required_metadata','fixture_and_oracle_unchanged','staging_removed')}
    report = dict(passed=False, diagnostics=[], pre_run_hashes=frozen, checks=checks)
    report['dependencies_sha256'] = {str(p):local.sha(p) for p in
        [Path(__file__).resolve(),local.EXECUTABLE,HERE/'runner.py',HERE/'models.py',HERE/'winapi.py',
         HERE/'kicad_staged_helper.py',HERE/'kicad_local.py',local.READER/'probe.py',local.READER/'run.py', local.READER/'observation_schema.py']}
    owned = None
    try:
        with tempfile.TemporaryDirectory(prefix='footprint-edges-control-') as owned:
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
            actual = data['footprint_edges']
            local.save(out/'actual-expected.json',dict(actual=actual,expected=expected,
                native_outline_observation_only=data['outline']))
            ids = [e['uuid'] for e in actual]
            checks['item_uuid_set'] = len(ids)==2 and set(ids)=={e['uuid'] for e in expected}
            observed_board = [e['uuid'] for e in data['edges']]
            checks['board_edges_separate'] = len(observed_board)==4 and set(observed_board)==set(board_ids)
            keys = ('uuid','parent_footprint_uuid','shape','primitive_type','layer','source_accessor',
                    'coordinate_space','endpoint_accessor')
            checks['required_metadata'] = checks['item_uuid_set'] and all(
                all(next(a for a in actual if a['uuid']==e['uuid'])[k]==e[k] for k in keys) for e in expected)
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
