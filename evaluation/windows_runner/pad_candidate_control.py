"""Evaluation orchestration for repeated-pads; no historical stdout fallback.

Execution is injected: a supervised runner invocation must return its actual
ExecutionSuccess/Failure. This portable slice does not launch a native process.
The existing runner/helper/probe remain responsible for native execution; a future
native control still requires the independent watchdog and current test budgets.
"""
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import runpy
import tempfile

from models import ExecutionSuccess, ExecutionFailure
from aoi_platform.inventory import (ArtifactDeclaration, InventoryManifest,
    InventoryLimits, InventorySuccess, inventory_artifacts)
from aoi_platform.pad_candidates import PadBatchFailure

HERE = Path(__file__).resolve().parent
BRIDGE = runpy.run_path(str(HERE.parent/'kicad-reader/repeated_pads_bridge.py'))
PCB_HASH = BRIDGE['PCB_HASH']
INPUT_LIMIT = 16*1024**2
OUTPUT_LIMIT = 2*1024**2
STDERR_LIMIT = 256*1024


@dataclass(frozen=True)
class ControlFailure:
    phase: str
    code: str
    transport: object = None
    diagnostic: object = None


@dataclass(frozen=True)
class ControlSuccess:
    replay: object
    transport: ExecutionSuccess
    pcb_sha256: str
    staged_sha256: str
    observation_sha256: str
    staging_removed: bool
    helper_temp_empty: bool


def _inventory(pcb, raw=None):
    entries = [('pcb', 'kicad_pcb', 'owned-stage', pcb, False)]
    if raw is not None:
        entries.append(('observation', 'supporting', 'current-execution-stdout', raw, True))
    manifest = InventoryManifest('geometry', tuple(ArtifactDeclaration(identity, role, source,
        sha256(content).hexdigest(), len(content), reference_only=reference)
        for identity,role,source,content,reference in entries), 'repeated-pads-01', 'accepted-snapshot')
    sources = {source: (lambda content=content: BytesIO(content)) for _,_,source,content,_ in entries}
    return inventory_artifacts(manifest, sources,
        InventoryLimits('repeated-pads-control-v1',2,INPUT_LIMIT,INPUT_LIMIT+OUTPUT_LIMIT,65536))


def run_control(pcb: bytes, declarations: dict, *, execute, staging_root: Path):
    """execute(stage_path, helper_temp) is trusted and returns native runner types.

    It owns the runner call/handles; this control owns only its fresh staging
    directory. Caller declarations supply candidate IDs/frames/policy, not raw
    bytes/inventory. No success is returned until owner cleanup is confirmed.
    """
    if type(pcb) is not bytes or not 0 < len(pcb) <= INPUT_LIMIT:
        return ControlFailure('input','INPUT_LIMIT_EXCEEDED')
    if sha256(pcb).hexdigest() != PCB_HASH:
        return ControlFailure('input','SOURCE_CONFLICT')
    admitted = _inventory(pcb)
    if not isinstance(admitted,InventorySuccess):
        return ControlFailure('input','INVENTORY_FAILED',diagnostic=admitted.report)
    allowed = {'board_id','scope_id','parent_id','pad_ids','native_frame','normalized_frame',
               'target_frame','normalization','translation_mm','policy'}
    if type(declarations) is not dict or set(declarations) != allowed:
        return ControlFailure('declarations','SCHEMA_INVALID')
    transport = None
    outcome = None
    root = None
    try:
        with tempfile.TemporaryDirectory(prefix='pad-control-',dir=staging_root) as directory:
            root = Path(directory)
            stage = root/'input.kicad_pcb'; helper_temp = root/'helper-temp'; helper_temp.mkdir()
            with stage.open('xb') as f: f.write(pcb)
            staged_hash = sha256(stage.read_bytes()).hexdigest()
            if staged_hash != admitted.inventory.artifacts[0].computed_sha256:
                outcome = ControlFailure('staging','SOURCE_CONFLICT')
            else:
                try:
                    transport = execute(stage,helper_temp)
                except TimeoutError:
                    outcome = ControlFailure('transport','TIMEOUT')
                except OSError:
                    outcome = ControlFailure('transport','EXECUTION_IO_ERROR')
                if outcome is None:
                    outcome = _after_execution(pcb,stage,helper_temp,transport,declarations)
        if root is None or root.exists():
            return ControlFailure('cleanup','CLEANUP_UNCONFIRMED',transport)
    except OSError:
        return ControlFailure('cleanup','CLEANUP_UNCONFIRMED',transport)
    if isinstance(outcome,ControlFailure):
        return outcome
    raw, admitted = outcome
    replay = BRIDGE['replay_repeated_pads'](pcb,raw,admitted,
        pcb_artifact_id='pcb',observation_artifact_id='observation',
        max_pcb_bytes=INPUT_LIMIT,max_observation_bytes=OUTPUT_LIMIT,**declarations)
    if isinstance(replay,PadBatchFailure):
        return ControlFailure('candidate','CANDIDATE_REJECTED',transport,replay)
    if not isinstance(replay,BRIDGE['ReplaySuccess']):
        return ControlFailure('candidate','INVALID_BRIDGE_RESULT',transport)
    return ControlSuccess(replay,transport,PCB_HASH,staged_hash,sha256(raw).hexdigest(),True,True)


def _after_execution(pcb,stage,helper_temp,transport,declarations):
    if isinstance(transport,ExecutionFailure):
        code = transport.issues[0].code.value if transport.issues else 'TRANSPORT_FAILED'
        return ControlFailure('transport',code,transport)
    if type(transport) is not ExecutionSuccess:
        return ControlFailure('transport','INVALID_EXECUTION_RESULT')
    e = transport.evidence
    if not (e.cleanup_state == 'cleaned' and type(e.active_processes) is int and e.active_processes == 0
            and type(e.root_exit) is int and e.root_exit == 0 and e.stdout_eof is True
            and e.stderr_eof is True and e.limits_verified is True and e.resumed is True):
        return ControlFailure('cleanup','CLEANUP_UNCONFIRMED',transport)
    if e.artifact_id != 'synthetic-repeated-pads-v1' or e.source_id != 'owned-stage' or e.policy_id != 'kicad-local-test-v1':
        return ControlFailure('transport','SOURCE_CONFLICT',transport)
    if any(helper_temp.iterdir()):
        return ControlFailure('cleanup','CLEANUP_UNCONFIRMED',transport)
    with stage.open('rb') as f:
        after = f.read(INPUT_LIMIT+1)
    if len(after) != len(pcb) or sha256(after).hexdigest() != PCB_HASH:
        return ControlFailure('staging','SOURCE_CONFLICT',transport)
    raw = transport.stdout  # Only success bytes, never diagnostic prefixes or files.
    if (type(raw) is not bytes or type(transport.stderr) is not bytes or len(raw) > OUTPUT_LIMIT
            or len(transport.stderr) > STDERR_LIMIT or type(e.observed_stdout) is not int
            or type(e.observed_stderr) is not int or e.observed_stdout != len(raw)
            or e.observed_stderr != len(transport.stderr)):
        return ControlFailure('transport','OUTPUT_BUDGET_OR_LENGTH',transport)
    try:
        payload = json.loads(raw)
        if type(payload) is not dict or payload.get('input_sha256') != PCB_HASH:
            return ControlFailure('binding','SOURCE_CONFLICT',transport)
    except (ValueError,TypeError,RecursionError):
        return ControlFailure('binding','SCHEMA_INVALID',transport)
    admitted = _inventory(pcb,raw)
    if not isinstance(admitted,InventorySuccess):
        return ControlFailure('output-inventory','INVENTORY_FAILED',transport,admitted.report)
    return raw, admitted
