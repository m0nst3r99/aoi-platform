"""Evaluation-only decision on v2 JSON bytes; no geometry/revision/publication output."""
from dataclasses import dataclass
from pathlib import Path
import json
import runpy

_schema = runpy.run_path(str(Path(__file__).with_name('observation_schema.py')))['schema']


@dataclass(frozen=True)
class Diagnostic:
    code: str
    field: str
    input_sha256: str | None = None
    build: str | None = None


@dataclass(frozen=True)
class Decision:
    status: str
    diagnostics: tuple[Diagnostic, ...] = ()


def evaluate_outline(raw: bytes) -> Decision:
    """Schema validation is not provenance authentication or complete geometry validation."""
    try:
        if type(raw) is not bytes:
            raise TypeError('JSON bytes required')
        data = json.loads(raw)
        _schema(data)  # Strict v2; never enable historical legacy replay.
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        return Decision('rejected', (Diagnostic('SCHEMA_INVALID', 'payload'),))
    if data['outline']['valid'] is False:
        return Decision('rejected', (Diagnostic('OUTLINE_INVALID', 'outline.valid',
                        data['input_sha256'], data['build']),))
    return Decision('not_rejected_by_outline_check')
