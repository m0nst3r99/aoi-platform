"""Independent geometric oracles; no selected fixture contact policy implied."""

from dataclasses import replace
from math import sqrt

import pytest

from aoi_platform.geometry import CircularArc, FrameKind, GeometryError, LineSegment, Outline, Point2, Transform2
from aoi_platform.geometry.fixture_geometry import (
    PointLocation, curve_segment_distance, locate_point, rectangle_bounds,
    rectangle_relation, transform_outline,
)


def polygon(frame, coords, name="outline"):
    return Outline.polygon(name, tuple(Point2(x, y, frame) for x, y in coords))


def rect(frame, x0, y0, x1, y1):
    return polygon(frame, ((x0, y0), (x1, y0), (x1, y1), (x0, y1)), "rectangle")


def disk(frame, radius=10):
    a, b, c = Point2(radius, 0, frame), Point2(-radius, 0, frame), Point2(0, 0, frame)
    return Outline("disk", (CircularArc(a, b, c, False), CircularArc(b, a, c, False)))


@pytest.mark.parametrize("x,y,expected", [
    (0, 0, PointLocation.INSIDE), (0, 9, PointLocation.INSIDE),
    (0, -9, PointLocation.INSIDE), (0, 10, PointLocation.BOUNDARY),
    (10, 0, PointLocation.BOUNDARY), (11, 0, PointLocation.OUTSIDE),
    (-11, 0, PointLocation.OUTSIDE), (0, 11, PointLocation.OUTSIDE),
])
def test_circle_point_location_has_independent_oracles(mm_frame, x, y, expected):
    outline = disk(mm_frame)
    assert locate_point(outline, Point2(x, y, mm_frame)) is expected
    reverse = Outline("reverse", tuple(CircularArc(e.end, e.start, e.center, True) for e in reversed(outline.edges)))
    assert locate_point(reverse, Point2(x, y, mm_frame)) is expected


def test_concavity_is_not_filled_by_bounding_box(mm_frame):
    outline = polygon(mm_frame, ((0, 0), (10, 0), (10, 2), (2, 2), (2, 10), (0, 10)))
    assert locate_point(outline, Point2(5, 5, mm_frame)) is PointLocation.OUTSIDE
    assert not rectangle_relation(outline, rect(mm_frame, 4, 4, 6, 6)).filled_overlap
    assert rectangle_relation(outline, rect(mm_frame, 4, 4, 6, 6)).separation_mm == 2


def test_edge_crosses_rectangle_with_all_vertices_outside(mm_frame):
    board = rect(mm_frame, 0, 4, 10, 6)
    exclusion = rect(mm_frame, 4, 0, 6, 10)
    assert all(not (4 <= edge.start.x <= 6) for edge in board.edges)
    relation = rectangle_relation(board, exclusion)
    assert relation.filled_overlap
    assert relation.separation_mm == 0


def test_enclosed_rectangle_overlap_without_boundary_intersections(mm_frame):
    relation = rectangle_relation(rect(mm_frame, 0, 0, 10, 10), rect(mm_frame, 4, 4, 6, 6))
    assert relation.filled_overlap
    assert relation.separation_mm == 0


def test_arc_bulge_overlaps_exclusion_while_endpoints_do_not(mm_frame):
    outline = disk(mm_frame)
    region = rect(mm_frame, -1, 9, 1, 11)
    assert all(edge.start.y == 0 for edge in outline.edges)
    assert rectangle_relation(outline, region).filled_overlap


def test_arc_distance_uses_interior_extremum(mm_frame):
    curve = disk(mm_frame).edges[0]
    line = LineSegment(Point2(-2, 13, mm_frame), Point2(2, 13, mm_frame))
    assert curve_segment_distance(curve, line) == pytest.approx(3, abs=1e-12)
    assert rectangle_relation(disk(mm_frame), rect(mm_frame, -2, 13, 2, 14)).separation_mm == pytest.approx(3)


def test_diagonal_corner_distance_is_euclidean(mm_frame):
    relation = rectangle_relation(rect(mm_frame, 0, 0, 1, 1), rect(mm_frame, 4, 5, 6, 7))
    assert not relation.filled_overlap
    assert relation.separation_mm == 5  # independent 3-4-5 triangle
    circle_relation = rectangle_relation(disk(mm_frame), rect(mm_frame, 12, 12, 13, 13))
    assert circle_relation.separation_mm == pytest.approx(12*sqrt(2)-10, abs=1e-12)


def test_boundary_overlap_is_geometric_fact_not_invalid_topology(mm_frame):
    relation = rectangle_relation(rect(mm_frame, 0, 0, 10, 10), rect(mm_frame, 10, 0, 20, 10))
    assert relation.filled_overlap and relation.separation_mm == 0


def test_proper_rigid_load_preserves_arc_and_independent_bounds(mm_frame):
    machine = replace(mm_frame, kind=FrameKind.MACHINE, frame_id="M", machine_id="m1")
    mapping = Transform2.translation(mm_frame, machine, 20, 30, transform_id="load")
    loaded = transform_outline(disk(mm_frame), mapping)
    relation = rectangle_relation(loaded, rect(machine, 0, 0, 50, 60))
    assert relation.outer_clearances_mm == pytest.approx((10, 20, 20, 20))
    assert all(isinstance(edge, CircularArc) for edge in loaded.edges)


def test_arbitrary_polygon_is_not_silently_replaced_with_rectangle(mm_frame):
    triangle = polygon(mm_frame, ((0, 0), (10, 0), (0, 10)))
    with pytest.raises(GeometryError, match="GEOMETRY_UNSUPPORTED"):
        rectangle_bounds(triangle)


def test_rotated_semicircle_checks_loaded_interior_extrema(mm_frame):
    a, b, c = Point2(10, 0, mm_frame), Point2(-10, 0, mm_frame), Point2(0, 0, mm_frame)
    board = Outline("semicircle", (CircularArc(a, b, c, False), LineSegment(b, a)))
    load = Transform2.rotation(mm_frame, mm_frame, 90, transform_id="quarter-turn")
    loaded = transform_outline(board, load)
    relation = rectangle_relation(loaded, rect(mm_frame, -9, -11, 1, 11))
    # Both rotated arc endpoints have x=0; the interior arc reaches x=-10.
    assert relation.outer_clearances_mm == pytest.approx((-1, 1, 1, 1), abs=1e-12)


def test_load_helper_rejects_unvalidated_datum_mapping(mm_frame):
    other = replace(mm_frame, frame_id="other-frame", origin="another origin")
    load = Transform2("raw", mm_frame, other, ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        transform_outline(disk(mm_frame), load)


def test_load_helper_rejects_same_id_different_source_context(mm_frame):
    other = replace(mm_frame, board_revision_id="different-revision")
    load = Transform2.translation(other, other, 0, 0, transform_id="wrong-source")
    with pytest.raises(GeometryError, match="CONTEXT_MISMATCH"):
        transform_outline(disk(mm_frame), load)


def test_rectangle_relation_rejects_wrong_frame(mm_frame):
    other = replace(mm_frame, origin="different-origin")
    with pytest.raises(GeometryError, match="CONTEXT_MISMATCH"):
        rectangle_relation(disk(mm_frame), rect(other, -20, -20, 20, 20))
