"""API evidence for Sprint 1 diagnostics; no importer or camera required."""
from dataclasses import replace
from itertools import permutations
import json

import pytest

from aoi_platform.geometry import (
    ContractError, GeometryError, Transform2, TransformGraph, RectangleDomain,
    Point2, FrameKind, BoardCapacity, FixtureEnvelope, CameraTravelEnvelope,
    ValidationReport, validate_fit,
)


def frames(frame):
    a = replace(frame, frame_id="A", machine_id="m1", capture_id="cap1")
    return a, replace(a, frame_id="B"), replace(a, frame_id="C")


def resolve_error(a, c, edges=(), **limits):
    with pytest.raises(GeometryError) as caught:
        TransformGraph(tuple(edges), **limits).resolve(a, c, RectangleDomain(a, 0, 0, 10, 20))
    return caught.value


def adapted(error):
    return ContractError.from_geometry_error(error, remediation="Correct the declared geometry inputs.")


def serialized(error):
    return ValidationReport("r", "synthetic-path-consistency-v1", (adapted(error),), ()).to_json()


def test_missing_path_keeps_request_evidence_without_caller_reconstruction(mm_frame):
    a, _, c = frames(mm_frame)
    error = resolve_error(a, c)
    assert error.code == "TRANSFORM_MISSING" and error.field_path == "resolve.paths"
    issue = adapted(error)
    context = dict(issue.context)
    assert context["source.frame_id"] == "A"
    assert context["target.frame_id"] == "C"
    assert context["source.board_revision_id"] == a.board_revision_id
    assert context["source.machine_id"] == "m1" and context["target.capture_id"] == "cap1"
    assert context["policy.id"] == "synthetic-path-consistency-v1"
    assert context["policy.version"] == "1"
    assert json.loads(context["domain.bounds"]) == [0, 0, 10, 20]
    assert context["domain.frame.unit"] == "mm"


def test_unknown_metadata_is_not_invented(mm_frame):
    target = replace(mm_frame, frame_id="target")
    context = dict(adapted(resolve_error(mm_frame, target)).context)
    assert "source.machine_id" not in context and "target.capture_id" not in context


@pytest.mark.parametrize("field,actual", [("origin", "other"), ("machine_id", "m2"),
                                         ("board_revision_id", "rev2"), ("capture_id", "cap2")])
def test_full_source_mismatch_retains_expected_and_actual(mm_frame, field, actual):
    a, _, c = frames(mm_frame)
    edge = Transform2.translation(a, c, 0, 0, transform_id="ac")
    requested = replace(a, **{field: actual})
    error = resolve_error(requested, c, (edge,))
    issue = adapted(error)
    assert issue.code == "CONTEXT_MISMATCH"
    assert json.loads(issue.expected)[field] == actual
    assert json.loads(issue.actual)[field] == getattr(a, field)
    assert json.loads(dict(issue.context)["paths"])[0]["transform_ids"] == ["ac"]


@pytest.mark.parametrize("field", ["machine_id", "board_revision_id", "capture_id"])
def test_intermediate_blank_cannot_erase_conflicting_values(mm_frame, field):
    a, b, c = frames(mm_frame)
    a, b, c = replace(a, **{field: "left"}), replace(b, **{field: None}), replace(c, **{field: "right"})
    edges = (Transform2.translation(a, b, 0, 0, transform_id="ab"),
             Transform2.translation(b, c, 0, 0, transform_id="bc"))
    issue = adapted(resolve_error(a, c, edges))
    assert issue.expected == "left"
    assert json.loads(issue.actual) == ["left", "right"]
    assert dict(issue.context)[f"source.{field}"] == "left"
    assert dict(issue.context)[f"target.{field}"] == "right"


def test_unvalidated_edge_keeps_transform_and_path(mm_frame):
    a, _, c = frames(mm_frame)
    c = replace(c, origin="other")
    raw = Transform2("raw", a, c, ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    issue = adapted(resolve_error(a, c, (raw,)))
    assert issue.code == "MAPPING_UNVALIDATED"
    assert dict(issue.context)["transform_id"] == "raw"
    assert json.loads(dict(issue.context)["paths"])[0]["transform_ids"] == ["raw"]


def test_noncommuting_graph_has_independent_oracles(mm_frame):
    a, b, c = frames(mm_frame)
    rotate = Transform2.rotation(a, b, 90, transform_id="rotate")
    move = Transform2.translation(b, c, 10, 0, transform_id="move")
    result = TransformGraph((move, rotate)).resolve(a, c, RectangleDomain(a, 0, 0, 10, 20))
    point = result.transform.apply(Point2(1, 2, a))
    assert (point.x, point.y) == pytest.approx((8, 1), rel=0, abs=1e-12)
    reverse = (Transform2.translation(a, b, 10, 0, transform_id="move"),
               Transform2.rotation(b, c, 90, transform_id="rotate"))
    point = TransformGraph(reverse).resolve(a, c, RectangleDomain(a, 0, 0, 10, 20)).transform.apply(Point2(1, 2, a))
    assert (point.x, point.y) == pytest.approx((-2, 11), rel=0, abs=1e-12)


def test_origin_agreement_does_not_hide_corner_disagreement(mm_frame):
    a, _, c = frames(mm_frame)
    identity = Transform2.translation(a, c, 0, 0, transform_id="identity")
    shear = Transform2("shear", a, c, ((1, 0.01, 0), (0, 1, 0), (0, 0, 1)))
    assert identity.apply(Point2(0, 0, a)) == shear.apply(Point2(0, 0, a))
    issue = adapted(resolve_error(a, c, (identity, shear)))
    assert issue.code == "TRANSFORM_AMBIGUOUS"
    assert float(issue.actual) == pytest.approx(0.2, rel=0, abs=1e-12)
    assert float(issue.expected) == 1e-6
    assert json.loads(dict(issue.context)["paths"]) == [
        {"transform_ids": ["identity"], "omitted_transform_count": 0},
        {"transform_ids": ["shear"], "omitted_transform_count": 0}]
    assert serialized(resolve_error(a, c, (identity, shear))) == serialized(resolve_error(a, c, (shear, identity)))


@pytest.mark.parametrize("matrix,code", [
    (((1, 0, 0), (0, 1e-5, 0), (0, 0, 1)), "TRANSFORM_ILL_CONDITIONED"),
    (((1e-200, 0, 0), (0, 1e-200, 0), (0, 0, 1)), "TRANSFORM_SINGULAR"),
])
def test_valid_edges_can_have_invalid_product(mm_frame, matrix, code):
    a, b, c = frames(mm_frame)
    edges = (Transform2("ab", a, b, matrix), Transform2("bc", b, c, matrix))
    assert all(e.condition_number <= 1e8 for e in edges)
    issue = adapted(resolve_error(a, c, edges))
    assert issue.code == code
    assert json.loads(dict(issue.context)["paths"])[0]["transform_ids"] == ["ab", "bc"]


def test_budget_diagnostics_do_not_bypass_limits(mm_frame):
    a, b, c = frames(mm_frame)
    edges = (Transform2.translation(a, b, 0, 0, transform_id="ab"),
             Transform2.translation(b, c, 0, 0, transform_id="bc"))
    issue = adapted(resolve_error(a, c, edges, max_edges=1))
    assert issue.code == "TRANSFORM_RESOURCE_EXHAUSTED"
    assert (issue.expected, issue.actual) == ("1", "2")
    assert dict(issue.context)["registered.omitted_edge_count"] == "2"
    assert "registered.paths" not in dict(issue.context)


def test_large_ambiguity_evidence_is_bounded_and_explicit(mm_frame):
    a, _, c = frames(mm_frame)
    edges = tuple(Transform2.translation(a, c, i, 0, transform_id=f"edge-{i:03}") for i in range(40))
    context = dict(adapted(resolve_error(a, c, edges)).context)
    assert len(json.loads(context["paths"])) == 32
    assert context["omitted_path_count"] == "8" and context["path_count"] == "40"
    assert serialized(resolve_error(a, c, edges)) == serialized(resolve_error(a, c, tuple(reversed(edges))))


def test_comparison_budget_retains_known_paths(mm_frame):
    a, _, c = frames(mm_frame)
    edges = tuple(Transform2.translation(a, c, 0, 0, transform_id=str(i)) for i in range(3))
    issue = adapted(resolve_error(a, c, edges, max_comparisons=2))
    assert issue.code == "TRANSFORM_RESOURCE_EXHAUSTED"
    assert dict(issue.context)["path_count"] == "3"


def test_long_path_and_long_ids_have_explicit_diagnostic_omissions(mm_frame):
    a, _, _ = frames(mm_frame)
    nodes = [replace(a, frame_id=str(i)) for i in range(141)]
    nodes[-1] = replace(nodes[-1], origin="unvalidated-end")
    edges = [Transform2.translation(left, right, 0, 0, transform_id=f"e{i:03}")
             for i, (left, right) in enumerate(zip(nodes, nodes[1:]))]
    edges[-1] = Transform2("last", nodes[-2], nodes[-1], ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    context = dict(adapted(resolve_error(nodes[0], nodes[-1], edges)).context)
    summary = json.loads(context["paths"])[0]
    assert len(summary["transform_ids"]) == 128 and summary["omitted_transform_count"] == 12
    c = replace(a, frame_id="target")
    edges = (Transform2.translation(a, c, 0, 0, transform_id="a"*9000),
             Transform2.translation(a, c, 1, 0, transform_id="z"))
    summary = json.loads(dict(adapted(resolve_error(a, c, edges)).context)["paths"])
    assert summary[0] == {"transform_ids": [], "omitted_transform_count": 1}
    assert summary[1]["transform_ids"] == ["z"]


def test_conflicting_graph_metadata_reports_are_order_independent(mm_frame):
    a, b, c = frames(mm_frame)
    other = replace(b, origin="different")
    edges = (Transform2.translation(a, b, 0, 0, transform_id="ab"),
             Transform2.translation(other, c, 0, 0, transform_id="bc"))
    outputs = {serialized(resolve_error(a, c, order)) for order in permutations(edges)}
    assert len(outputs) == 1
    issue = adapted(resolve_error(a, c, edges))
    assert json.loads(issue.expected)["origin"] == b.origin
    assert json.loads(issue.actual)["origin"] == "different"


def test_error_diagnostics_are_immutable_and_adapter_cannot_overwrite(mm_frame):
    a, _, c = frames(mm_frame)
    error = resolve_error(a, c)
    for name in ("code", "field_path", "message", "context", "expected", "actual", "_diagnostic"):
        with pytest.raises(AttributeError):
            setattr(error, name, "replacement")
    with pytest.raises(AttributeError):
        del error._diagnostic
    with pytest.raises(GeometryError, match="SCHEMA_INVALID"):
        ContractError.from_geometry_error(error, remediation="Fix.", context=(("source.frame_id", "overwritten"),))
    issue = ContractError.from_geometry_error(error, remediation="Fix.", context=(("extra", "value"),))
    assert dict(issue.context)["source.frame_id"] == "A"


def fit_inputs(frame):
    from aoi_platform.geometry import Outline
    board = replace(frame, kind=FrameKind.PCB)
    machine = replace(board, frame_id="M", kind=FrameKind.MACHINE, machine_id="m1", origin="machine")
    outline = Outline.polygon("board-outline", tuple(Point2(x, y, board) for x, y in ((0, 0), (10, 0), (10, 10), (0, 10))))
    fixture = FixtureEnvelope("fixture-envelope", "v1", "m1", "fixture-1", "config-1", machine, None, (), None, None)
    return board, machine, outline, fixture


@pytest.mark.parametrize("failure", ["unvalidated", "wrong-target", "nonfinite", "wrong-source"])
def test_fit_pre_report_failures_keep_inputs(mm_frame, failure):
    board, machine, outline, fixture = fit_inputs(mm_frame)
    load = Transform2.translation(board, machine, 0, 0, transform_id="load")
    if failure == "unvalidated":
        load = Transform2("raw", board, machine, ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    if failure == "wrong-target":
        load = Transform2.translation(board, replace(machine, frame_id="other-M"), 0, 0, transform_id="load")
    if failure == "wrong-source":
        load = Transform2.translation(replace(board, origin="other"), machine, 0, 0, transform_id="load")
    with pytest.raises(GeometryError) as caught:
        validate_fit(outline, BoardCapacity("capacity", "v1"), rotation_deg=float("nan") if failure == "nonfinite" else 0,
                     report_id="fit-report", fixture=fixture, load_transform=load)
    issue = adapted(caught.value)
    context = dict(issue.context)
    assert context["outline_id"] == "board-outline"
    assert context["fixture.envelope_id"] == "fixture-envelope"
    assert context["fixture.configuration_id"] == "config-1"
    assert context["capacity.policy"] == "capacity-binary64-v1"
    assert context["transform_id"] == load.transform_id
    assert context["source.board_revision_id"] == board.board_revision_id
    if failure in ("wrong-target", "wrong-source"):
        assert issue.expected is not None and issue.actual is not None and issue.expected != issue.actual


def test_fit_conflicting_envelopes_keep_both_machine_values(mm_frame):
    _, machine, outline, fixture = fit_inputs(mm_frame)
    other = replace(machine, frame_id="other-M", machine_id="m2")
    travel = CameraTravelEnvelope("travel", "v2", "m2", "camera", "camera-config", other, "optical-axis", None, (), None)
    with pytest.raises(GeometryError) as caught:
        validate_fit(outline, BoardCapacity("capacity", "v1"), rotation_deg=0, report_id="report", fixture=fixture, travel=travel)
    issue = adapted(caught.value)
    assert issue.expected == "m1" and json.loads(issue.actual) == ["m1", "m2"]
    assert dict(issue.context)["fixture.machine_id"] == "m1"
    assert dict(issue.context)["travel.machine_id"] == "m2"


def test_invalid_report_identity_does_not_break_error_adapter(mm_frame):
    _, _, outline, fixture = fit_inputs(mm_frame)
    with pytest.raises(GeometryError) as caught:
        validate_fit(outline, BoardCapacity("capacity", "v1"), rotation_deg=0, report_id="", fixture=fixture)
    issue = adapted(caught.value)
    assert issue.field_path == "fit.report_id" and issue.code == "SCHEMA_INVALID"
    assert "report_id" not in dict(issue.context)
    assert dict(issue.context)["outline_id"] == "board-outline"


def test_duplicate_registry_id_retains_known_identity(mm_frame):
    a, _, c = frames(mm_frame)
    edge = Transform2.translation(a, c, 0, 0, transform_id="duplicate")
    with pytest.raises(GeometryError) as caught:
        TransformGraph((edge, edge))
    issue = adapted(caught.value)
    assert dict(issue.context)["transform_id"] == "duplicate"
    assert issue.actual == "duplicate"
