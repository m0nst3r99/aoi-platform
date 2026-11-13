"""Bounded four-corner correspondence only, not rectangle/candidate admission."""
from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from .boundary_evidence import BoundaryContour, BoundaryBindingPolicy, _policy, _Reject
from .geometry.models import Frame, FrameKind, Point2, require_same_frame
from .geometry.errors import ErrorCode, GeometryError
from .geometry.reports import ContractError


@dataclass(frozen=True, slots=True)
class Correspondence:
    # reference vertex i corresponds to observed vertex indices[i].
    indices: tuple[int, ...]
    max_component_error_mm: float
    status: str = 'within-synthetic-policy'


@dataclass(frozen=True, slots=True)
class CorrespondenceFailure:
    reason: str
    error: ContractError


def match_contours_in_p(reference: BoundaryContour, observed: BoundaryContour,
                        policy: BoundaryBindingPolicy) -> Correspondence | CorrespondenceFailure:
    """Require simple convex four-vertex topology; never infer rectangle support.

    Exact rational orientation on bounded binary coordinates avoids cancellation
    at large datums and underflow for tiny contours. This does not use tolerance
    to repair topology. Cyclic/reversed mappings preserve every edge adjacency.
    No transform, point sorting, mutation, candidate call or geometry is returned.
    """
    def reject(reason, field, code=ErrorCode.SOURCE_CONFLICT):
        raise GeometryError(code, reason, field_path=field)
    try:
        _policy(policy)
        frame = None
        for label, contour in (('reference', reference), ('observed', observed)):
            if type(contour) is not BoundaryContour or type(contour.vertices) is not tuple:
                reject('invalid_contour', label, ErrorCode.SCHEMA_INVALID)
            if type(contour.closed) is not bool or type(contour.hole_count) is not int:
                reject('invalid_topology_fields', label, ErrorCode.SCHEMA_INVALID)
            if len(contour.vertices) != 4 or not contour.closed or contour.hole_count != 0:
                reject('unsupported_topology', label, ErrorCode.GEOMETRY_UNSUPPORTED)
            points = []
            for point in contour.vertices:
                if type(point) is not Point2 or type(point.frame) is not Frame:
                    reject('invalid_point', label, ErrorCode.SCHEMA_INVALID)
                if point.frame.kind is not FrameKind.PCB:
                    reject('not_in_P', label, ErrorCode.CONTEXT_MISMATCH)
                if frame is None:
                    frame = point.frame
                require_same_frame(point.frame, frame, label + '.frame')
                for value in (point.x, point.y):
                    if type(value) not in (int, float) or not isfinite(value):
                        reject('nonfinite_or_invalid_coordinate', label, ErrorCode.SCHEMA_INVALID)
                    if abs(value) > policy.max_abs_coordinate_mm:
                        reject('coordinate_bound', label, ErrorCode.INPUT_LIMIT_EXCEEDED)
                points.append((Fraction(point.x), Fraction(point.y)))
            if len(set(points)) != 4:
                reject('duplicate_vertices', label)
            turns = []
            for i in range(4):
                a, b, c = points[i], points[(i+1)%4], points[(i+2)%4]
                turns.append((b[0]-a[0])*(c[1]-b[1]) - (b[1]-a[1])*(c[0]-b[0]))
            if not (all(t > 0 for t in turns) or all(t < 0 for t in turns)):
                reject('invalid_topology_or_adjacency', label)
        matches = []
        for direction in (1, -1):
            for start in range(4):
                indices = tuple((start + direction*i) % 4 for i in range(4))
                error = max(abs(getattr(reference.vertices[i], axis) -
                                getattr(observed.vertices[j], axis))
                            for i, j in enumerate(indices) for axis in ('x', 'y'))
                if error <= policy.comparison_abs_mm:
                    matches.append((indices, error))
        if not matches:
            reject('no_match', 'correspondence')
        if len(matches) != 1:
            reject('ambiguous_mapping', 'correspondence')
        return Correspondence(*matches[0])
    except _Reject as error:
        return CorrespondenceFailure('invalid_policy', ContractError(error.code,
            'Invalid synthetic policy.', error.field, 'Supply the exact policy.'))
    except GeometryError as error:
        return CorrespondenceFailure(error.message, ContractError.from_geometry_error(
            error, remediation='Correct the supplied contours; do not reorder or repair silently.'))
