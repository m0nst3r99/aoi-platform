"""C1 strict-v2 control with injected execution; no native launch in this module.

Trusted execute(stage_path, helper_temp) returns existing runner result types.
Historical boundary transport and current observation transport remain distinct.
"""
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import tempfile
from models import ExecutionSuccess
from aoi_platform.inventory import ArtifactDeclaration, InventoryManifest, InventoryLimits, InventorySuccess, inventory_artifacts
from c1_replay_flow import PINS, ReplaySuccess, ReplayFailure, _evaluate_admitted

@dataclass(frozen=True)
class ControlSuccess:
    replay: ReplaySuccess
    observation_transport: ExecutionSuccess
    observation_sha256: str
    staging_removed: bool


def _admit(raw, *, current=False):
    entries=[]
    for key,digest,size in PINS:
        if key=='observation':
            if not current:continue
            digest=sha256(raw[key]).hexdigest();size=len(raw[key])
        entries.append(ArtifactDeclaration(key,'kicad_pcb' if key=='pcb' else 'supporting',key,digest,size,reference_only=key!='pcb'))
    return inventory_artifacts(InventoryManifest('geometry',tuple(entries),'REAL-PCB-01-r2','accepted-snapshot'),
        {k:(lambda data=data:BytesIO(data)) for k,data in raw.items()},
        InventoryLimits('c1-strict-control-v1',5,2*1024**2,4*1024**2,65536))


def run_control(paths, *, execute, staging_root):
    """Paths contain pinned pcb/boundary/report/transport, never old observation.

    Captured bytes are bounded and reused for inventory and interpretation.
    New stdout hash is measured evidence, not a preaccepted replay pin.
    """
    raw={};owned=None
    try:
        expected={k for k,_,_ in PINS if k!='observation'}
        if set(paths)!=expected:raise ValueError('Exactly four historical inputs required')
        for key,_,size in PINS:
            if key=='observation':continue
            p=Path(paths[key])
            if not p.is_absolute():raise ValueError('Explicit absolute path required')
            with p.open('rb') as stream:raw[key]=stream.read(size+1)
            if len(raw[key])!=size:raise ValueError('Pinned size mismatch: '+key)
        admitted=_admit(raw)
        if not isinstance(admitted,InventorySuccess):return ReplayFailure('inventory','BYTE_ADMISSION_FAILED',str(admitted.report))
        with tempfile.TemporaryDirectory(prefix='c1-strict-',dir=staging_root) as directory:
            owned=Path(directory);stage=owned/'input.kicad_pcb';temp=owned/'helper';temp.mkdir()
            stage.write_bytes(raw['pcb'])
            if sha256(stage.read_bytes()).hexdigest()!=PINS[0][1]:raise ValueError('Staging hash mismatch')
            try:
                transport=execute(stage,temp)
            except TimeoutError:
                return ReplayFailure('observation-transport','TIMEOUT','No stdout fallback')
            if not isinstance(transport,ExecutionSuccess):
                return ReplayFailure('observation-transport','EXECUTION_FAILED','Diagnostic prefixes are not observations')
            ev=transport.evidence
            # Fixed current invocation identities, never historical boundary transport.
            for field, expected_identity in (
                    ('artifact_id', 'REAL-PCB-01-r2-pcb'),
                    ('source_id', 'owned-stage'),
                    ('policy_id', 'kicad-local-test-v1')):
                actual_identity = getattr(ev, field)
                if actual_identity != expected_identity:
                    return ReplayFailure('observation-identity', 'EXECUTION_IDENTITY_MISMATCH',
                        f'{field}: expected {expected_identity!r}, actual {actual_identity!r}')
            if not (type(ev.root_exit) is int and ev.root_exit==0 and type(ev.active_processes) is int and ev.active_processes==0
                    and ev.cleanup_state=='cleaned' and ev.stdout_eof is True and ev.stderr_eof is True
                    and ev.limits_verified is True and ev.resumed is True):
                return ReplayFailure('observation-cleanup','CLEANUP_UNCONFIRMED','Current execution evidence incomplete')
            if any(temp.iterdir()) or stage.read_bytes()!=raw['pcb']:
                return ReplayFailure('observation-cleanup','SOURCE_OR_CLEANUP_MISMATCH','Owned staging changed or helper temp not empty')
            if (type(transport.stdout) is not bytes or type(transport.stderr) is not bytes or
                not 0<len(transport.stdout)<=2*1024**2 or len(transport.stderr)>256*1024 or
                ev.observed_stdout!=len(transport.stdout) or ev.observed_stderr!=len(transport.stderr)):
                return ReplayFailure('observation-output','OUTPUT_INVALID','Bounded bytes/counts required')
            raw['observation']=transport.stdout
            admitted=_admit(raw,current=True)
            if not isinstance(admitted,InventorySuccess):return ReplayFailure('inventory','BYTE_ADMISSION_FAILED',str(admitted.report))
            outcome=_evaluate_admitted(raw,admitted,strict_v2=True)
        if owned.exists():return ReplayFailure('owner-cleanup','CLEANUP_UNCONFIRMED','Staging removal unconfirmed')
        if not isinstance(outcome,ReplaySuccess):return outcome
        return ControlSuccess(outcome,transport,sha256(transport.stdout).hexdigest(),True)
    except (OSError,ValueError,TypeError) as error:
        return ReplayFailure('control','CONTROL_FAILED',str(error))
