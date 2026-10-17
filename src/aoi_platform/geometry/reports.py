"""Structured diagnostics for the implemented geometry subset.

Ordering is an implementation convention: canonical JSON of each complete
issue, with sorted keys. It does not depend on discovery order, object identity,
or hash iteration. No issue is deduplicated. Producers must supply all safely
discoverable issues; this module does not parse or publish board revisions.
"""

from dataclasses import dataclass, field
from enum import StrEnum
import json
from typing import TypeAlias

from .errors import ErrorCode, GeometryError, require_text

Evidence: TypeAlias = tuple[tuple[str, str], ...]


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class ReportStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


def _invalid(message: str, path: str) -> None:
    raise GeometryError(ErrorCode.SCHEMA_INVALID, message, field_path=path)


def _evidence(value: Evidence, path: str) -> Evidence:
    if not isinstance(value, tuple):
        _invalid("Supply immutable key/value evidence.", path)
    keys = set()
    for pair in value:
        if not isinstance(pair, tuple) or len(pair) != 2:
            _invalid("Supply key/value string pairs.", path)
        key, text = pair
        require_text(key, path)
        require_text(text, path)
        if key in keys:
            _invalid("Duplicate evidence key; preserve conflicts as separate issues.", path)
        keys.add(key)
    return tuple(sorted(value))


@dataclass(frozen=True, slots=True)
class SourceLocation:
    source: str
    row: int | None = None
    column: int | None = None

    def __post_init__(self) -> None:
        require_text(self.source, "location.source")
        for name in ("row", "column"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 1):
                _invalid("Use a positive one-based index or None.", f"location.{name}")


@dataclass(frozen=True, slots=True)
class ContractError:
    code: ErrorCode
    message: str
    field_path: str
    remediation: str
    severity: Severity = Severity.ERROR
    artifact_id: str | None = None
    entity_id: str | None = None
    source_location: SourceLocation | None = None
    expected: str | None = None
    actual: str | None = None
    context: Evidence = ()

    def __post_init__(self) -> None:
        if not isinstance(self.code, ErrorCode) or not isinstance(self.severity, Severity):
            _invalid("Use declared code and severity enums.", "issue")
        # This subset has one warning code. Blocking codes cannot be downgraded.
        warning = self.code is ErrorCode.OPTIONAL_DATA_ABSENT
        if warning != (self.severity is Severity.WARNING):
            _invalid("Severity must match the code's mandatory gate semantics.", "issue.severity")
        for name in ("message", "field_path", "remediation"):
            require_text(getattr(self, name), f"issue.{name}")
        for name in ("artifact_id", "entity_id"):
            value = getattr(self, name)
            if value is not None:
                require_text(value, f"issue.{name}")
        for name in ("expected", "actual"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                _invalid("Supply diagnostic text or None.", f"issue.{name}")
        if self.source_location is not None and not isinstance(self.source_location, SourceLocation):
            _invalid("Supply SourceLocation or None.", "issue.source_location")
        object.__setattr__(self, "context", _evidence(self.context, "issue.context"))

    @classmethod
    def from_geometry_error(cls, error: GeometryError, *, remediation: str,
                            context: Evidence = (), artifact_id: str | None = None,
                            entity_id: str | None = None,
                            source_location: SourceLocation | None = None) -> "ContractError":
        return cls(error.code, error.message, error.field_path, remediation,
                   artifact_id=artifact_id, entity_id=entity_id,
                   source_location=source_location, context=context)

    def to_dict(self) -> dict:
        location = self.source_location
        return {
            "code": self.code.value, "message": self.message,
            "field_path": self.field_path, "remediation": self.remediation,
            "severity": self.severity.value, "artifact_id": self.artifact_id,
            "entity_id": self.entity_id, "expected": self.expected, "actual": self.actual,
            "context": dict(self.context),
            "source_location": None if location is None else {
                "source": location.source, "row": location.row, "column": location.column},
        }


def _json(value: dict) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class ValidationReport:
    report_id: str
    policy_id: str
    issues: tuple[ContractError, ...]
    checks: Evidence
    unresolved_fields: tuple[str, ...] = ()
    conflicting_fields: tuple[str, ...] = ()
    artifact_digests: Evidence = ()
    canonical_digest: str | None = None
    context: Evidence = ()
    schema_version: str = "geometry-report-v1"
    status: ReportStatus = field(init=False)

    def __post_init__(self) -> None:
        for name in ("report_id", "policy_id", "schema_version"):
            require_text(getattr(self, name), f"report.{name}")
        if not isinstance(self.issues, tuple) or any(not isinstance(i, ContractError) for i in self.issues):
            _invalid("Supply an immutable tuple of ContractError records.", "report.issues")
        object.__setattr__(self, "issues", tuple(sorted(self.issues, key=lambda i: _json(i.to_dict()))))
        for name in ("checks", "artifact_digests", "context"):
            object.__setattr__(self, name, _evidence(getattr(self, name), f"report.{name}"))
        for name in ("unresolved_fields", "conflicting_fields"):
            values = getattr(self, name)
            if not isinstance(values, tuple):
                _invalid("Supply an immutable tuple of field paths.", f"report.{name}")
            for value in values:
                require_text(value, f"report.{name}")
            object.__setattr__(self, name, tuple(sorted(values)))
        status = ReportStatus.REJECTED if self.errors else ReportStatus.ACCEPTED
        object.__setattr__(self, "status", status)
        if self.canonical_digest is not None:
            require_text(self.canonical_digest, "report.canonical_digest")
            if status is ReportStatus.REJECTED:
                _invalid("Rejected reports cannot carry an accepted canonical digest.", "report.canonical_digest")

    @property
    def errors(self) -> tuple[ContractError, ...]:
        return tuple(i for i in self.issues if i.severity is Severity.ERROR)

    @property
    def warnings(self) -> tuple[ContractError, ...]:
        return tuple(i for i in self.issues if i.severity is Severity.WARNING)

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version, "report_id": self.report_id,
            "policy_id": self.policy_id, "status": self.status.value,
            "errors": [i.to_dict() for i in self.errors],
            "warnings": [i.to_dict() for i in self.warnings],
            "checks": dict(self.checks), "context": dict(self.context),
            "unresolved_fields": list(self.unresolved_fields),
            "conflicting_fields": list(self.conflicting_fields),
            "artifact_digests": dict(self.artifact_digests),
            "canonical_digest": self.canonical_digest,
        }

    def to_json(self) -> str:
        return _json(self.to_dict())
