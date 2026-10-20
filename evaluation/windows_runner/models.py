"""Evaluation-only immutable transport contract. No geometry or protocol semantics."""
from dataclasses import dataclass
from enum import StrEnum


class Code(StrEnum):
    INVALID = 'INVALID_REQUEST'
    CAPABILITY = 'CAPABILITY_UNAVAILABLE'
    SOURCE = 'STAGED_INPUT_MISMATCH'
    WIN32 = 'WIN32_FAILURE'
    TIMEOUT = 'TIMEOUT'
    OUTPUT = 'OUTPUT_BUDGET'
    EXIT = 'NONZERO_EXIT'
    CLEANUP = 'CLEANUP_UNCONFIRMED'


@dataclass(frozen=True, slots=True)
class StagedInput:
    handle: int
    size: int
    sha256: str
    artifact_id: str
    source_id: str


@dataclass(frozen=True, slots=True)
class Limits:
    policy_id: str
    input_bytes: int
    stdout_bytes: int
    stderr_bytes: int
    combined_bytes: int
    chunk_bytes: int
    wall_ms: int
    cleanup_ms: int
    process_memory: int
    job_memory: int
    processes: int


@dataclass(frozen=True, slots=True)
class Request:
    executable: str
    argv: tuple[str, ...]
    cwd: str
    environment: tuple[tuple[str, str], ...]
    staged: StagedInput
    limits: Limits


@dataclass(frozen=True, slots=True)
class Issue:
    code: Code
    operation: str
    winerror: int | None = None


@dataclass(frozen=True, slots=True)
class Evidence:
    root_pid: int | None
    root_exit: int | None
    active_processes: int | None
    stdout_eof: bool
    stderr_eof: bool
    cleanup_state: str
    elapsed_ms: int
    observed_stdout: int
    observed_stderr: int
    limits_verified: bool
    resumed: bool
    artifact_id: str
    source_id: str
    policy_id: str


@dataclass(frozen=True, slots=True)
class ExecutionSuccess:
    stdout: bytes
    stderr: bytes
    evidence: Evidence


@dataclass(frozen=True, slots=True)
class ExecutionFailure:
    issues: tuple[Issue, ...]
    diagnostic_stdout_prefix: bytes
    diagnostic_stderr_prefix: bytes
    evidence: Evidence
    diagnostic_prefixes_usable: bool = False
