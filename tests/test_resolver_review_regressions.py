"""Regressions for the four reproduced resolver review failures."""

from dataclasses import replace

import pytest

from aoi_platform.geometry import (
    AxisDirection, ErrorCode, GeometryError, Point2, RectangleDomain,
    Transform2, TransformGraph, Unit,
)


@pytest.mark.parametrize("change", [
    {"origin": "other datum"}, {"unit": Unit.INCH},
    {"y_direction": AxisDirection.DOWN},
    {"board_revision_id": "other-revision"}, {"machine_id": "other-machine"},
    {"capture_id": "other-capture"},
])
def test_requested_source_matches_complete_registered_frame(mm_frame, change):
    target = replace(mm_frame, frame_id="target", board_revision_id=None)
    mapping = Transform2.translation(mm_frame, target, 1, 2, transform_id="edge")
    requested = replace(mm_frame, **change)
    with pytest.raises(GeometryError) as caught:
        TransformGraph((mapping,)).resolve(requested, target, RectangleDomain(requested, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.CONTEXT_MISMATCH
    assert caught.value.field_path == "resolve.source"


@pytest.mark.parametrize("same_record", [True, False])
def test_constructor_and_register_reject_duplicate_ids(mm_frame, same_record):
    target = replace(mm_frame, frame_id="target")
    first = Transform2.translation(mm_frame, target, 1, 0, transform_id="duplicate")
    second = first if same_record else Transform2.translation(mm_frame, target, 2, 0, transform_id="duplicate")
    for create in (lambda: TransformGraph((first, second)),
                   lambda: TransformGraph((first,)).register(second)):
        with pytest.raises(GeometryError) as caught:
            create()
        assert caught.value.code is ErrorCode.SCHEMA_INVALID
        assert caught.value.field_path == "graph.edge.transform_id"


def chain(mm_frame, size=1100):
    frames = [replace(mm_frame, frame_id=f"frame-{i}") for i in range(size + 1)]
    edges = tuple(Transform2.translation(a, b, 1, 0, transform_id=f"edge-{i}")
                  for i, (a, b) in enumerate(zip(frames, frames[1:])))
    return frames[0], frames[-1], edges


def test_long_chain_small_budget_is_typed_resource_failure(mm_frame):
    source, target, edges = chain(mm_frame)
    with pytest.raises(GeometryError) as caught:
        TransformGraph(edges, max_edges=1).resolve(source, target, RectangleDomain(source, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.TRANSFORM_RESOURCE_EXHAUSTED


def test_long_chain_with_budget_uses_no_python_recursion(mm_frame):
    source, target, edges = chain(mm_frame)
    result = TransformGraph(edges, max_edges=1100).resolve(source, target, RectangleDomain(source, 0, 0, 1, 1))
    assert result.transform.apply(Point2(2, 3, source)) == Point2(1102, 3, target)
    assert len(result.representative_path) == 1100


def test_pair_budget_exhaustion_does_not_accept_agreeing_prefix(mm_frame):
    target = replace(mm_frame, frame_id="target")
    edges = tuple(Transform2.translation(mm_frame, target, 0, 0, transform_id=f"edge-{i}") for i in range(3))
    domain = RectangleDomain(mm_frame, 0, 0, 1, 1)
    with pytest.raises(GeometryError) as caught:
        TransformGraph(edges, max_comparisons=2).resolve(mm_frame, target, domain)
    assert caught.value.code is ErrorCode.TRANSFORM_RESOURCE_EXHAUSTED
    assert len(TransformGraph(edges, max_comparisons=3).resolve(mm_frame, target, domain).path_ids) == 3


def test_single_path_checks_corners_for_overflow(mm_frame):
    target = replace(mm_frame, frame_id="target")
    mapping = Transform2.translation(mm_frame, target, 1e308, 0, transform_id="huge")
    with pytest.raises(GeometryError) as caught:
        TransformGraph((mapping,)).resolve(mm_frame, target, RectangleDomain(mm_frame, 1e308, 0, 1.5e308, 1))
    assert caught.value.code is ErrorCode.SCHEMA_INVALID


@pytest.mark.parametrize("count", [1, 3])
def test_corner_outputs_are_evaluated_once_per_candidate(mm_frame, monkeypatch, count):
    target = replace(mm_frame, frame_id="target")
    edges = tuple(Transform2.translation(mm_frame, target, 0, 0, transform_id=f"edge-{i}") for i in range(count))
    calls = []
    original = Transform2.apply

    def track(self, point):
        calls.append((self.transform_id, point.x, point.y))
        return original(self, point)

    monkeypatch.setattr(Transform2, "apply", track)
    TransformGraph(edges).resolve(mm_frame, target, RectangleDomain(mm_frame, -2, -3, 5, 7))
    assert sorted(calls) == sorted((edge.transform_id, x, y) for edge in edges
                                  for x, y in ((-2, -3), (-2, 7), (5, -3), (5, 7)))


def test_long_cycle_is_typed_even_with_sufficient_budget(mm_frame):
    source, target, edges = chain(mm_frame)
    closing = Transform2.translation(target, source, -1100, 0, transform_id="close-cycle")
    with pytest.raises(GeometryError) as caught:
        TransformGraph(edges + (closing,), max_edges=1101).resolve(source, target, RectangleDomain(source, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.TRANSFORM_CYCLE_UNSUPPORTED


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_invalid_comparison_limits_fail_schema_validation(limit):
    with pytest.raises(GeometryError) as caught:
        TransformGraph(max_comparisons=limit)
    assert caught.value.code is ErrorCode.SCHEMA_INVALID


def test_register_preserves_comparison_limit(mm_frame):
    target = replace(mm_frame, frame_id="target")
    graph = TransformGraph(max_comparisons=2)
    for i in range(3):
        graph = graph.register(Transform2.translation(mm_frame, target, 0, 0, transform_id=str(i)))
    assert graph.max_comparisons == 2
    with pytest.raises(GeometryError) as caught:
        graph.resolve(mm_frame, target, RectangleDomain(mm_frame, 0, 0, 1, 1))
    assert caught.value.field_path == "resolve.comparisons"


def test_default_comparison_budget_rejects_large_pair_work_before_evaluation(mm_frame, monkeypatch):
    target = replace(mm_frame, frame_id="target")
    edges = tuple(Transform2.translation(mm_frame, target, 0, 0, transform_id=str(i)) for i in range(450))

    def should_not_apply(*args):
        pytest.fail("Comparison budget must be checked before candidate evaluation")

    monkeypatch.setattr(Transform2, "apply", should_not_apply)
    with pytest.raises(GeometryError) as caught:
        TransformGraph(edges).resolve(mm_frame, target, RectangleDomain(mm_frame, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.TRANSFORM_RESOURCE_EXHAUSTED
    assert caught.value.field_path == "resolve.comparisons"


def test_shared_prefix_candidate_work_is_bounded(mm_frame):
    a, b, c, d = (replace(mm_frame, frame_id=name) for name in "abcd")
    edges = tuple(Transform2.translation(source, target, 0, 0, transform_id=name)
                  for source, target, name in ((a, b, "ab"), (b, c, "bc"), (c, d, "cd"), (b, d, "bd")))
    # Four graph edges / traversal visits, but five candidate edge occurrences.
    with pytest.raises(GeometryError) as caught:
        TransformGraph(edges, max_edges=4).resolve(a, d, RectangleDomain(a, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.TRANSFORM_RESOURCE_EXHAUSTED
    assert caught.value.field_path == "resolve.candidate_edges"


def test_shared_suffix_traversal_work_is_bounded(mm_frame):
    a, b, c, d = (replace(mm_frame, frame_id=name) for name in "abcd")
    edges = tuple(Transform2.translation(source, target, 0, 0, transform_id=name)
                  for source, target, name in ((a, b, "ab"), (a, c, "ac"), (b, c, "bc"), (c, d, "cd")))
    with pytest.raises(GeometryError) as caught:
        TransformGraph(edges, max_edges=4).resolve(a, d, RectangleDomain(a, 0, 0, 1, 1))
    assert caught.value.code is ErrorCode.TRANSFORM_RESOURCE_EXHAUSTED
    assert caught.value.field_path == "resolve.traversal"


def test_overflow_at_later_corner_also_rejects_single_path(mm_frame):
    target = replace(mm_frame, frame_id="target")
    mapping = Transform2.translation(mm_frame, target, 1e308, 0, transform_id="huge")
    # The two x=0 corners are finite; both x=1e308 corners overflow.
    with pytest.raises(GeometryError) as caught:
        TransformGraph((mapping,)).resolve(mm_frame, target, RectangleDomain(mm_frame, 0, 0, 1e308, 1))
    assert caught.value.code is ErrorCode.SCHEMA_INVALID
