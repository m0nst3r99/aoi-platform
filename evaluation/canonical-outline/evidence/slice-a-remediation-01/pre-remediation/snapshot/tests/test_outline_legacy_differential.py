"""Pinned pre-refactor source is the compatibility oracle, not new expectations."""
import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

from aoi_platform.geometry import outlines as current
from aoi_platform.geometry.errors import GeometryError
from aoi_platform.geometry.models import Point2

BASE = Path(__file__).parents[1] / "evaluation/canonical-outline/evidence/slice-a-01/baseline_outlines.py"


@pytest.fixture(scope="module")
def old():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == "30f58e3d1368d1de01eeb1e304298baa057c0ec12a559c6e485dd0a010926240"
    name = "aoi_platform.geometry._pinned_outline_baseline"
    spec = importlib.util.spec_from_file_location(name, BASE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def outcome(module, frame, coords, holes=()):
    try:
        points = tuple(Point2(x, y, frame) for x, y in coords)
        obj = module.Outline.polygon("case", points)
        if holes:
            obj = module.Outline("case", obj.edges, holes)
        return module.outline_bounds(obj), tuple((e.start, e.end) for e in obj.edges)
    except GeometryError as e:
        return e.code, e.message, e.field_path, e.context, e.expected, e.actual


@pytest.mark.parametrize("coords,holes", [
    (((0,0),(20,0),(20,10),(0,10)), ()),
    (((0,0),(10,0),(10,2),(2,2),(2,10),(0,10)), ()),
    (((0,0),(2,2),(0,2),(2,0)), ()),
    (((0,0),(1,0),(2,0)), ()),
    (((0,0),(0,0),(1,1)), ()),
    (((0,0),(1e-8,0),(1,1)), ()),
    (((0,0),(1000001,0),(1,1)), ()),
    (((0,0),(1,0),(1,1)), ("hole",)),
    (((0,0),(1,0)), ()),
    (((0,0),(4,0),(2,0),(2,2),(0,2)), ()),
])
def test_polygon_differential(old, mm_frame, coords, holes):
    assert outcome(current, mm_frame, coords, holes) == outcome(old, mm_frame, coords, holes)


@pytest.mark.parametrize("clockwise", [True, False])
def test_two_arc_circle_differential(old, mm_frame, clockwise):
    def case(m):
        a,b,c = (Point2(x,0,mm_frame) for x in (10,-10,0))
        outline = m.Outline("circle", (m.CircularArc(a,b,c,clockwise), m.CircularArc(b,a,c,clockwise)))
        return m.outline_bounds(outline), tuple(e.sweep for e in outline.edges)
    assert case(current) == case(old)


@pytest.mark.parametrize("count", [512,513])
def test_capacity_differential(old, mm_frame, count):
    from math import cos, sin, tau
    coords = tuple((100*cos(tau*i/count),100*sin(tau*i/count)) for i in range(count))
    assert outcome(current,mm_frame,coords) == outcome(old,mm_frame,coords)


@pytest.mark.parametrize("case", ["open-and-frame", "wrong-type", "holes-before-count", "major-arc", "mixed"])
def test_first_error_and_mixed_arc_differential(old,mm_frame,case):
    from dataclasses import replace
    def run(m):
        p=lambda x,y: Point2(x,y,mm_frame)
        try:
            a,b,c=p(0,0),p(2,0),p(0,2)
            edges=(m.LineSegment(a,b),m.LineSegment(b,c),m.LineSegment(c,a))
            if case=="open-and-frame":
                other=replace(mm_frame,frame_id="other")
                edges=(m.LineSegment(a,c),m.LineSegment(Point2(2,0,other),Point2(0,2,other)),edges[2])
            elif case=="wrong-type": edges=(object(),object())
            elif case=="holes-before-count": return m.Outline("bad",edges*200,("hole",))
            elif case=="major-arc":
                edges=(m.CircularArc(p(2,0),p(0,2),a,True),m.LineSegment(p(0,2),p(2,0)))
            elif case=="mixed":
                edges=(m.LineSegment(p(-2,0),p(2,0)),m.CircularArc(p(2,0),p(-2,0),a,False))
            o=m.Outline("case",edges)
            return m.outline_bounds(o)
        except GeometryError as e:
            return e.code,e.message,e.field_path,e.context,e.expected,e.actual
    assert run(current)==run(old)
