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
                                      digest, 'synthetic-bottom-rotation-v1', 'owned-stage'), limits)
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
    """Expected values derived before launch; never derived from native output."""
    expected = []
    text = ['(kicad_pcb (version 20240108) (generator "synthetic-evaluation")',
            '(general (thickness 1.6)) (paper "A4")',
            '(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (34 "B.Paste" user)',
            '(35 "F.Paste" user) (36 "B.SilkS" user) (37 "F.SilkS" user)',
            '(38 "B.Mask" user) (39 "F.Mask" user) (44 "Edge.Cuts" user))',
            '(setup (pad_to_mask_clearance 0))']
    # Same asymmetric stored coordinates on both sides, deliberately no extra mirror.
    pads = [('1', [1, 2], 30, [2, 1]), ('2', [-3, 1], 60, [3, 1.5])]
    for index, (side, origin) in enumerate([('F', [10, 10]), ('B', [30, 20])]):
        uid = str(UUID(int=100+index))
        ref = 'TOP1' if side=='F' else 'BOT1'
        fp = dict(uuid=uid, reference=ref, value='SYNTHETIC', position_mm=origin,
                  angle_deg=90, layer=side+'.Cu', pads=[])
        text += [f'(footprint "Synthetic:Asymmetric" (layer "{side}.Cu") (uuid "{uid}")',
                 f'(at {origin[0]} {origin[1]} 90) (attr smd)',
                 f'(fp_text reference "{ref}" (at 0 0 90) (layer "{side}.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
                 f'(fp_text value "SYNTHETIC" (at 0 0 90) (layer "{side}.SilkS") (effects (font (size 1 1) (thickness 0.15))))']
        for j, (number, uv, angle, size) in enumerate(pads):
            padid = str(UUID(int=200+index*10+j))
            layers = [side+'.Cu', side+'.Paste', side+'.Mask']
            # R90(u,v)=(v,-u), native X-right/Y-down numerical coordinates.
            world = [origin[0]+uv[1], origin[1]-uv[0]]
            fp['pads'].append(dict(uuid=padid, number=number, local_mm=uv,
                                  position_mm=world, angle_deg=angle,
                                  size_mm=size, layers=layers))
            text.append(f'(pad "{number}" smd rect (at {uv[0]} {uv[1]} {angle}) '
                        f'(size {size[0]} {size[1]}) (layers "'+'" "'.join(layers)+
                        f'") (uuid "{padid}"))')
        text.append(')')
        expected.append(fp)
    for i, (a,b) in enumerate([((0,0),(40,0)),((40,0),(40,30)),((40,30),(0,30)),((0,30),(0,0))]):
        text.append(f'(gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) '
                    f'(stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{UUID(int=300+i)}"))')
    pcb = out/'bottom-rotation.kicad_pcb'
    pcb.write_text('\n'.join(text+[')'])+'\n')
    local.save(out/'oracle.json', dict(expected_footprints=expected, coordinate_tolerance_mm=1e-6,
        raw_angle_equality=True, modulo_comparison=False,
        formula='world=(X+u*cos(theta)+v*sin(theta), Y-u*sin(theta)+v*cos(theta)); theta=90: (X+v,Y-u). API relative is inverse rotation of world-origin, hence stored (u,v). No extra bottom mirror during this load.',
        angle_rule='Footprint raw=90. Pad file at-angle is API absolute orientation, raw 30/60, not 90+30/60. Derived relative angles would be -60/-30 but are not reader fields.',
        numeric_world_oracle={'TOP1':[[12,9],[11,13]],'BOT1':[[32,19],[31,23]]},
        precision='Source coordinates exact decimal mm; parser rounds to nm. Tolerance 1 nm=1e-6 mm, no angle tolerance/modulo needed for these positive integer angles.'))
    (out/'references.md').write_text("""# Pre-run oracle rationale (KiCad tag 10.0.7)

- [Parser](https://gitlab.com/kicad/code/kicad/-/raw/10.0.7/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp):
  parseBoardUnits (lines 185-197) converts mm to integer nm.
  Footprint layer is assigned directly (4829-4837), pose before pads (4856-4872).
  Pad at-position uses SetFPRelativePosition and its angle uses SetOrientation
  (5583-5598), not SetFPRelativeOrientation.
- [BOARD_ITEM](https://gitlab.com/kicad/code/kicad/-/raw/10.0.7/pcbnew/board_item.cpp):
  Get/SetFPRelativePosition (378-402) apply inverse/forward footprint rotation
  with translation, without a side-dependent mirror.
- [RotatePoint](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.7/libs/kimath/src/trigo.cpp):
  lines 210-243 give (u,v)->(v,-u) at +90 degrees. Numerically positive
  rotation is clockwise in Cartesian Y-up notation, visually counterclockwise
  with PCB display X-right/Y-down. We retain source-native coordinates.
- [PAD](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.7/pcbnew/pad.cpp):
  SetOrientation vs SetFPRelativeOrientation (1379-1399) distinguish raw angle
  from angle plus parent orientation; Flip is a separate mutation (1403 onward).
  Reading an already-stored bottom footprint does not authorize applying Flip again.

This fixture is authored directly as an already-stored board footprint, not
created by flipping a library footprint. It tests this file-loading convention
only. Oracle numbers are generated with elementary integer rotation before launch.
Layer membership compares sets (order is not semantic), with duplicate rejection.
Pad parent association is checked through the probe's nested footprint/pad UUIDs.
No canonical bottom transform, targeting geometry, or general support claim.
""", encoding='utf-8')
    return pcb, expected


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    pcb, expected = fixture(out)
    frozen = {p.name: local.sha(p) for p in out.iterdir() if p.is_file()}
    report = dict(passed=False, diagnostics=[], pre_run_hashes=frozen, checks={})
    report['dependencies_sha256'] = {str(p):local.sha(p) for p in
        [Path(__file__).resolve(), local.EXECUTABLE, HERE/'runner.py', HERE/'models.py',
         HERE/'winapi.py', HERE/'kicad_staged_helper.py', local.READER/'probe.py', local.READER/'run.py', local.READER/'observation_schema.py']}
    owned = None
    try:
        with tempfile.TemporaryDirectory(prefix='bottom-control-') as owned:
            stage = Path(owned)/'stage.pcb'
            stage.write_bytes(pcb.read_bytes())
            temp = Path(owned)/'helper'
            temp.mkdir()
            command = [sys._base_executable,str(Path(__file__).resolve()),'--worker',
                       str(out),str(stage),str(temp)]
            report.update(command=command, watchdog_seconds=45)
            with (out/'watchdog.stdout').open('wb') as a, (out/'watchdog.stderr').open('wb') as b:
                proc = subprocess.Popen(command, stdout=a, stderr=b, creationflags=0x08000000)
                try:
                    report['worker_exit'] = proc.wait(timeout=45)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
                    raise RuntimeError('watchdog timeout')
            if report['worker_exit']!=0:
                raise RuntimeError('worker failed')
            t = json.loads((out/'transport.json').read_text())
            report['checks']['transport'] = t['success']
            report['checks']['cleanup'] = (t['result']['evidence']['cleanup_state']=='cleaned'
                and t['result']['evidence']['active_processes']==0
                and all(t[k] for k in ('caller_handle_usable','stage_unchanged','helper_temp_empty')))
            if not t['success']:
                raise RuntimeError('transport failure; prefixes not parsed')
            data = json.loads((out/'stdout.bin').read_bytes())
            spec = importlib.util.spec_from_file_location('harness',local.READER/'run.py')
            harness = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(harness)
            report['checks']['schema'] = harness.schema(data)
            report['checks']['build'] = data['build']=='10.0.7'
            report['checks']['input_hash'] = data['input_sha256']==frozen[pcb.name]
            actual = data['footprints']
            local.save(out/'actual-expected.json', dict(actual=actual, expected=expected))
            checks = report['checks']
            ids = [f['uuid'] for f in actual]
            checks['footprint_uuid_set_unique'] = len(ids)==2 and set(ids)=={f['uuid'] for f in expected}
            for fp in expected:
                found = [f for f in actual if f['uuid']==fp['uuid']]
                if len(found)!=1:
                    checks[fp['reference']+'.present_once']=False
                    continue
                row = found[0]
                prefix = fp['reference']
                for key in ('reference','value','position_mm','angle_deg','layer'):
                    checks[prefix+'.'+key] = row[key]==fp[key]
                padids = [p['uuid'] for p in row['pads']]
                checks[prefix+'.pad_uuid_set_unique'] = len(padids)==2 and set(padids)=={p['uuid'] for p in fp['pads']}
                for pad in fp['pads']:
                    matches = [p for p in row['pads'] if p['uuid']==pad['uuid']]
                    tag = prefix+'.pad'+pad['number']
                    if len(matches)!=1:
                        checks[tag+'.parent_association']=False
                        continue
                    p = matches[0]
                    for key in ('local_mm','position_mm','size_mm'):
                        checks[tag+'.'+key] = all(abs(a-b)<=1e-6 for a,b in zip(p[key],pad[key]))
                    for key in ('number','angle_deg'):
                        checks[tag+'.'+key] = p[key]==pad[key]
                    checks[tag+'.layers'] = len(p['layers'])==3 and set(p['layers'])==set(pad['layers'])
    except Exception as error:
        report['diagnostics'].append(dict(type=type(error).__name__,message=str(error)))
    finally:
        report['checks']['fixture_and_oracle_unchanged'] = all(local.sha(out/n)==h for n,h in frozen.items())
        report['checks']['staging_removed'] = owned is not None and not Path(owned).exists()
        report['passed'] = all(report['checks'].values()) and not report['diagnostics']
        local.save(out/'report.json', report)
    print(json.dumps(dict(passed=report['passed'], checks=report['checks'], diagnostics=report['diagnostics']),indent=2))


if __name__=='__main__':
    if sys.argv[1]=='--worker':
        worker(*map(Path,sys.argv[2:5]))
    else:
        main(Path(sys.argv[1]).resolve())


