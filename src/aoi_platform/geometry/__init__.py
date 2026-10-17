"""Public, hardware-independent 2D geometry API."""

from .angles import normalize_angle, signed_angular_difference
from .errors import ErrorCode, GeometryError
from .models import AxisDirection, Frame, FrameKind, Parity, Point2, Unit
from .transforms import Matrix3, Transform2, TransformKind
from .reports import ContractError, ReportStatus, Severity, SourceLocation, ValidationReport
from .resolver import PathConsistencyPolicy, RectangleDomain, ResolvedPath, TransformGraph

__all__ = [
    "AxisDirection", "ErrorCode", "Frame", "FrameKind", "GeometryError",
    "Parity", "Point2", "Unit", "normalize_angle", "signed_angular_difference",
    "Matrix3", "Transform2", "TransformKind",
    "ContractError", "ReportStatus", "Severity", "SourceLocation", "ValidationReport",
    "PathConsistencyPolicy", "RectangleDomain", "ResolvedPath", "TransformGraph",
]
