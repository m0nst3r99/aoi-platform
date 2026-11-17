"""Analytic geometric facts used by fixture checks, independent of fit policy.

These helpers report containment, overlap and Euclidean separation; they do
not decide whether touching or a particular margin is permitted. No sampled
chord replaces an arc. The bounded contour kernel's EPS guards apply.
"""

from dataclasses import dataclass
from enum import StrEnum
from math import atan2, cos, hypot, pi, sin, sqrt

from .errors import ErrorCode, GeometryError
from .models import Point2, require_same_frame
from .outlines import (
    EPS, CircularArc, Curve, LineSegment, Outline, checked_point,
    intersections, outline_bounds, point_curve_distance, point_line_distance, reject,
)
from .transforms import Transform2, TransformKind


class PointLocation(StrEnum):
    INSIDE = "inside"
    BOUNDARY = "boundary"
    OUTSIDE = "outside"


def locate_point(outline: Outline, point: Point2) -> PointLocation:
    """Ray crossing with arcs split at y extrema into y-monotone pieces."""
    checked_point(point)
    require_same_frame(point.frame, outline.frame, "fixture_geometry.point.frame")
    if any(point_curve_distance(point, edge) <= EPS for edge in outline.edges):
        return PointLocation.BOUNDARY
    crossings = 0
    for edge in outline.edges:
        if isinstance(edge, LineSegment):
            if (edge.start.y > point.y) != (edge.end.y > point.y):
                x = edge.start.x + (point.y-edge.start.y)*(edge.end.x-edge.start.x)/(edge.end.y-edge.start.y)
                crossings += x > point.x
            continue
        cuts = [0.0, 1.0]
        for angle in (pi/2, 3*pi/2):
            parameter = edge.parameter(angle)
            if 0 < parameter < 1:
                cuts.append(parameter)
        cuts.sort()
        for lo, hi in zip(cuts, cuts[1:]):
            a, b = edge.at(lo), edge.at(hi)
            if (a.y > point.y) == (b.y > point.y):
                continue
            # On a y-monotone circle piece the x root has constant sign
            # relative to the center, given by its interior angle.
            dy = point.y-edge.center.y
            root = sqrt(max(0.0, (edge.radius-abs(dy))*(edge.radius+abs(dy))))
            midpoint_angle = edge.start_angle + (lo+hi)/2*edge.sweep
            x = edge.center.x + (root if cos(midpoint_angle) >= 0 else -root)
            crossings += x > point.x
    return PointLocation.INSIDE if crossings % 2 else PointLocation.OUTSIDE


def curve_segment_distance(curve: Curve, segment: LineSegment) -> float:
    """Minimum distance, including interior arc extrema and edge crossings."""
    require_same_frame(segment.start.frame, curve.start.frame, "fixture_geometry.curves.frame")
    candidates = [point_line_distance(curve.start, segment), point_line_distance(curve.end, segment),
                  point_curve_distance(segment.start, curve), point_curve_distance(segment.end, curve)]
    # Handles coincident/overlapping lines without topology's overlap rejection.
    if min(candidates) <= EPS or intersections(curve, segment):
        return 0.0
    if isinstance(curve, CircularArc):
        dx, dy = segment.end.x-segment.start.x, segment.end.y-segment.start.y
        length = hypot(dx, dy)
        ux, uy = dx/length, dy/length
        along = (curve.center.x-segment.start.x)*ux + (curve.center.y-segment.start.y)*uy
        if 0 <= along <= length:
            normal = atan2(ux, -uy)
            for angle in (normal, normal+pi):
                if curve.includes(angle):
                    p = Point2(curve.center.x+curve.radius*cos(angle),
                               curve.center.y+curve.radius*sin(angle), curve.start.frame)
                    candidates.append(point_line_distance(p, segment))
    return min(candidates)


def transform_outline(outline: Outline, mapping: Transform2) -> Outline:
    """Apply a declared proper rigid load without inferring any frame mapping."""
    if not isinstance(outline, Outline) or not isinstance(mapping, Transform2):
        raise GeometryError(ErrorCode.SCHEMA_INVALID, "Supply Outline and Transform2 records.", field_path="fixture_geometry.load")
    mapping._require_validated_conventions()
    require_same_frame(mapping.from_frame, outline.frame, "fixture_geometry.load.from_frame")
    if mapping.kind is not TransformKind.RIGID:
        reject("Only proper rigid loads preserve supported outline geometry.", unsupported=True)
    edges = []
    for edge in outline.edges:
        start, end = mapping.apply(edge.start), mapping.apply(edge.end)
        if isinstance(edge, LineSegment):
            edges.append(LineSegment(start, end))
        else:
            edges.append(CircularArc(start, end, mapping.apply(edge.center), edge.clockwise))
    return Outline(outline.outline_id, tuple(edges))


def rectangle_bounds(region: Outline) -> tuple[float, float, float, float]:
    """Recognize an axis-aligned rectangle; do not use a polygon's bounding box."""
    if not isinstance(region, Outline) or len(region.edges) != 4 or any(type(edge) is not LineSegment for edge in region.edges):
        reject("This geometric operation requires a four-line axis-aligned rectangle.", unsupported=True)
    bounds = outline_bounds(region)
    xmin, ymin, xmax, ymax = bounds
    if any(edge.start.x != edge.end.x and edge.start.y != edge.end.y for edge in region.edges):
        reject("Slanted rectangle/polygon edges are not supported by this operation.", unsupported=True)
    if {(edge.start.x, edge.start.y) for edge in region.edges} != {
        (xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax)
    }:
        reject("Region must be the rectangle itself, not only have rectangular bounds.", unsupported=True)
    return bounds


@dataclass(frozen=True, slots=True)
class RectangleRelation:
    # Signed clearances to left, bottom, right, top rectangle boundaries.
    # Positive means the whole outline is inside that supporting half-plane.
    outer_clearances_mm: tuple[float, float, float, float]
    filled_overlap: bool
    separation_mm: float


def rectangle_relation(outline: Outline, region: Outline) -> RectangleRelation:
    """Whole filled-contour versus filled-rectangle geometric relation.

    Boundary distance plus both containment directions detects a rectangle
    wholly inside the board, as well as an edge crossing with outside vertices.
    """
    require_same_frame(region.frame, outline.frame, "fixture_geometry.region.frame")
    rx0, ry0, rx1, ry1 = rectangle_bounds(region)
    x0, y0, x1, y1 = outline_bounds(outline)
    clearances = (x0-rx0, y0-ry0, rx1-x1, ry1-y1)
    separation = min(curve_segment_distance(edge, boundary)
                     for edge in outline.edges for boundary in region.edges)
    first = outline.edges[0].start
    board_in_rectangle = rx0 <= first.x <= rx1 and ry0 <= first.y <= ry1
    rectangle_in_board = locate_point(outline, region.edges[0].start) is not PointLocation.OUTSIDE
    overlaps = separation <= EPS or board_in_rectangle or rectangle_in_board
    return RectangleRelation(clearances, overlaps, 0.0 if overlaps else separation)
