"""Typed failures for the geometry-core subset of GEO-001."""

from enum import StrEnum
from math import isfinite
from dataclasses import dataclass
import json


def diagnostic_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def merge_evidence(*groups: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    result = {}
    for group in groups:
        for key, value in group:
            if not isinstance(key, str) or not key or not isinstance(value, str):
                raise ValueError("Diagnostic evidence requires string pairs.")
            if key in result and result[key] != value:
                raise ValueError(f"Conflicting diagnostic evidence: {key}")
            result[key] = value
    return tuple(sorted(result.items()))


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: "ErrorCode"
    message: str
    field_path: str
    context: tuple[tuple[str, str], ...] = ()
    expected: str | None = None
    actual: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, ErrorCode) or any(not isinstance(value, str) for value in (self.message, self.field_path)):
            raise ValueError("Diagnostic code/message/field must be typed values.")
        if any(value is not None and not isinstance(value, str) for value in (self.expected, self.actual)):
            raise ValueError("Expected/actual diagnostic values must be text or None.")
        object.__setattr__(self, "context", merge_evidence(self.context))


class ErrorCode(StrEnum):
    SCHEMA_INVALID = "SCHEMA_INVALID"
    FORMAT_UNSUPPORTED = "FORMAT_UNSUPPORTED"
    REQUIRED_ARTIFACT_MISSING = "REQUIRED_ARTIFACT_MISSING"
    DUPLICATE_ID = "DUPLICATE_ID"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    INPUT_LIMIT_EXCEEDED = "INPUT_LIMIT_EXCEEDED"
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    SOURCE_IO_ERROR = "SOURCE_IO_ERROR"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    TRANSFORM_SINGULAR = "TRANSFORM_SINGULAR"
    TRANSFORM_ILL_CONDITIONED = "TRANSFORM_ILL_CONDITIONED"
    MAPPING_UNVALIDATED = "MAPPING_UNVALIDATED"
    TRANSFORM_MISSING = "TRANSFORM_MISSING"
    TRANSFORM_AMBIGUOUS = "TRANSFORM_AMBIGUOUS"
    TRANSFORM_CYCLE_UNSUPPORTED = "TRANSFORM_CYCLE_UNSUPPORTED"
    TRANSFORM_RESOURCE_EXHAUSTED = "TRANSFORM_RESOURCE_EXHAUSTED"
    POLICY_INVALID = "POLICY_INVALID"
    DOMAIN_INVALID = "DOMAIN_INVALID"
    OPTIONAL_DATA_ABSENT = "OPTIONAL_DATA_ABSENT"
    OUTLINE_INVALID = "OUTLINE_INVALID"
    GEOMETRY_UNSUPPORTED = "GEOMETRY_UNSUPPORTED"
    BOARD_CAPACITY_EXCEEDED = "BOARD_CAPACITY_EXCEEDED"
    BOARD_OUT_OF_ENVELOPE = "BOARD_OUT_OF_ENVELOPE"


class GeometryError(ValueError):
    """A rejected operation, with a stable code and actionable field location."""

    def __init__(self, code: ErrorCode, message: str, *, field_path: str,
                 context: tuple[tuple[str, str], ...] = (), expected: str | None = None,
                 actual: str | None = None) -> None:
        self._diagnostic = Diagnostic(code, message, field_path, context, expected, actual)
        super().__init__(f"{code}: {field_path}: {message}")

    def __setattr__(self, name, value):
        if name == "_diagnostic" and hasattr(self, "_diagnostic"):
            raise AttributeError("Diagnostic is immutable.")
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if name == "_diagnostic":
            raise AttributeError("Diagnostic is immutable.")
        super().__delattr__(name)

    code = property(lambda self: self._diagnostic.code)
    message = property(lambda self: self._diagnostic.message)
    field_path = property(lambda self: self._diagnostic.field_path)
    context = property(lambda self: self._diagnostic.context)
    expected = property(lambda self: self._diagnostic.expected)
    actual = property(lambda self: self._diagnostic.actual)

    def with_context(self, context: tuple[tuple[str, str], ...]) -> "GeometryError":
        return GeometryError(self.code, self.message, field_path=self.field_path,
                             context=merge_evidence(self.context, context),
                             expected=self.expected, actual=self.actual)


def require_text(value: object, field_path: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise GeometryError(
            ErrorCode.SCHEMA_INVALID, "Supply a nonempty string.", field_path=field_path
        )


def finite_number(value: object, field_path: str) -> float:
    """Accept real Python int/float inputs, never bools or string coercions."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GeometryError(
            ErrorCode.SCHEMA_INVALID, "Supply a finite number.", field_path=field_path
        )
    try:
        result = float(value)
    except OverflowError as exc:
        raise GeometryError(
            ErrorCode.SCHEMA_INVALID, "Number exceeds binary64 range.", field_path=field_path
        ) from exc
    if not isfinite(result):
        raise GeometryError(
            ErrorCode.SCHEMA_INVALID, "NaN/infinity or numeric overflow.", field_path=field_path
        )
    return result
