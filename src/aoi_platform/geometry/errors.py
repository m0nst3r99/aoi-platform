"""Typed failures for the geometry-core subset of GEO-001."""

from enum import StrEnum
from math import isfinite


class ErrorCode(StrEnum):
    SCHEMA_INVALID = "SCHEMA_INVALID"
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

    def __init__(self, code: ErrorCode, message: str, *, field_path: str) -> None:
        self.code = code
        self.message = message
        self.field_path = field_path
        super().__init__(f"{code}: {field_path}: {message}")


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
