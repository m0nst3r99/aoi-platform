from dataclasses import replace

import pytest

from aoi_platform.geometry import (
    AxisDirection, ErrorCode, Frame, FrameKind, GeometryError, PathConsistencyPolicy,
    Point2, RectangleDomain, Transform2, TransformGraph, Unit,
)


IDENTITY = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def frames(mm_frame: Frame):
    a = replace(mm_frame, frame_id="a", origin="shared")
    b = replace(mm_frame, frame_id="b", origin="shared")
    c = replace(mm_frame, frame_id="c", origin="shared")
    return a, b, c


def edge(source, target, transform_id, dx=0):
    return Transform2.translation(source, target, dx, 0, transform_id=transform_id)


def test_multistep_path_direction_and_composition_order(mm_frame):
    a, b, c = frames(mm_frame)
    graph = TransformGraph().register(edge(a, b, "a-b", 10)).register(edge(b, c, "b-c", 20))
    domain = RectangleDomain(a, 0, 0, 10, 20)
    result = graph.resolve(a, c, domain)
    assert result.representative_path == ("a-b", "b-c")
    assert result.transform.apply(Point2(2, 3, a)).x == 32
    assert result.policy.policy_id == "synthetic-path-consistency-v1"
    assert result.domain == domain


def test_all_agreeing_paths_are_examined_and_deterministic(mm_frame):
    a, b, c = frames(mm_frame)
    direct = edge(a, c, "z-direct", 30)
    graph = TransformGraph().register(edge(a, b, "a-b", 10)).register(edge(b, c, "b-c", 20)).register(direct)
    result = graph.resolve(a, c, RectangleDomain(a, -1, -2, 3, 4))
    assert result.path_ids == (("a-b", "b-c"), ("z-direct",))


def test_target_unit_is_converted_to_mm_for_consistency(mm_frame):
    a, b, c = frames(mm_frame)
    inch_target = replace(c, unit=Unit.INCH)
    # 1e-4 inch is above the 1e-6 mm policy tolerance after conversion.
    d = replace(inch_target, frame_id="d")
    graph = TransformGraph().register(Transform2.unit_conversion(a, d, transform_id="small")).register(
        edge(d, inch_target, "small-shift", 1e-4)).register(
        edge(a, b, "metric-leg")).register(Transform2.unit_conversion(b, inch_target, transform_id="large"))
    with pytest.raises(GeometryError) as caught:
        graph.resolve(a, inch_target, RectangleDomain(a, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.TRANSFORM_AMBIGUOUS


def test_explicit_registered_inverse_is_supported_as_its_own_edge(mm_frame):
    a, b, _ = frames(mm_frame)
    forward = edge(a, b, "forward", 7)
    inverse = forward.inverse(transform_id="registered-inverse")
    # Registering both directions would itself be a cycle; the resolver only
    # accepts the explicitly requested direction in this graph.
    graph = TransformGraph().register(inverse)
    result = graph.resolve(b, a, RectangleDomain(b, 0, 0, 1, 1))
    assert result.representative_path == ("registered-inverse",)


def test_disagreeing_path_fails_at_rectangle_vertex(mm_frame):
    a, b, c = frames(mm_frame)
    graph = TransformGraph().register(edge(a, b, "a-b", 10)).register(edge(b, c, "b-c", 20)).register(edge(a, c, "direct", 30.00001))
    with pytest.raises(GeometryError) as caught:
        graph.resolve(a, c, RectangleDomain(a, -10, -20, 30, 40))
    assert caught.value.code is ErrorCode.TRANSFORM_AMBIGUOUS


def test_missing_domain_policy_and_pixel_are_explicit(mm_frame):
    a, b, _ = frames(mm_frame)
    graph = TransformGraph().register(edge(a, b, "a-b"))
    with pytest.raises(GeometryError) as caught:
        graph.resolve(a, b, None)  # type: ignore[arg-type]
    assert caught.value.code is ErrorCode.DOMAIN_INVALID
    with pytest.raises(GeometryError) as caught:
        PathConsistencyPolicy(tolerance_mm=-1)
    assert caught.value.code is ErrorCode.POLICY_INVALID
    pixel = replace(a, frame_id="pixel", unit=Unit.PIXEL, y_direction=AxisDirection.DOWN,
                    kind=FrameKind.RAW_IMAGE, capture_id="cap")
    with pytest.raises(GeometryError) as caught:
        RectangleDomain(pixel, 0, 0, 1, 1)
    assert caught.value.code is ErrorCode.DOMAIN_INVALID


def test_cycle_is_rejected_and_inverse_is_not_synthesized(mm_frame):
    a, b, c = frames(mm_frame)
    cyclic = TransformGraph().register(edge(a, b, "a-b")).register(edge(b, a, "b-a"))
    with pytest.raises(GeometryError) as caught:
        cyclic.resolve(a, b, RectangleDomain(a, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.TRANSFORM_CYCLE_UNSUPPORTED
    one_way = TransformGraph().register(edge(a, b, "a-b"))
    with pytest.raises(GeometryError) as caught:
        one_way.resolve(b, a, RectangleDomain(b, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.TRANSFORM_MISSING
    with pytest.raises(GeometryError) as caught:
        TransformGraph().resolve(a, a, RectangleDomain(a, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.TRANSFORM_MISSING


def test_blank_intermediate_context_cannot_bridge_conflicts(mm_frame):
    a = replace(mm_frame, frame_id="a", origin="shared", machine_id="m1")
    middle = replace(mm_frame, frame_id="middle", origin="shared", machine_id=None)
    c = replace(mm_frame, frame_id="c", origin="shared", machine_id="m2")
    graph = TransformGraph().register(edge(a, middle, "a-middle")).register(edge(middle, c, "middle-c"))
    with pytest.raises(GeometryError) as caught:
        graph.resolve(a, c, RectangleDomain(a, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.CONTEXT_MISMATCH


def test_unvalidated_edge_is_rejected_and_resource_limit_never_returns_partial(mm_frame):
    a, b, c = frames(mm_frame)
    other = replace(b, origin="different")
    raw = Transform2("raw", a, other, IDENTITY)
    with pytest.raises(GeometryError) as caught:
        TransformGraph((raw,)).resolve(a, other, RectangleDomain(a, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.MAPPING_UNVALIDATED
    limited = TransformGraph((edge(a, b, "a-b"), edge(b, c, "b-c")), max_edges=1)
    with pytest.raises(GeometryError) as caught:
        limited.resolve(a, c, RectangleDomain(a, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.TRANSFORM_RESOURCE_EXHAUSTED
