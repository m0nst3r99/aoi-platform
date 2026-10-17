from dataclasses import FrozenInstanceError, replace
from math import inf, nan, sqrt

import pytest

from aoi_platform.geometry import (
    AxisDirection, BoardCapacity, CameraTravelEnvelope, CircularArc, EnvelopeEvidence,
    ErrorCode, EvidenceKind, FitCheck, FitReport, FitStatus, FixtureEnvelope, Frame,
    FrameKind, GeometryError, LineSegment, Outline, Point2, Transform2, Unit,
    check_capacity, validate_fit,
)


@pytest.fixture
def board(mm_frame):
    return replace(mm_frame, kind=FrameKind.PCB)


@pytest.fixture
def machine(board):
    return replace(board, kind=FrameKind.MACHINE, frame_id="machine/m1", machine_id="m1", origin="machine datum")


def rectangle(frame, width, height, *, x=0, y=0, name="board-outline"):
    return Outline.polygon(name, tuple(Point2(px, py, frame) for px, py in
                                       ((x, y), (x+width, y), (x+width, y+height), (x, y+height))))


@pytest.mark.parametrize("width,height,rotation,status,extents", [
    (280, 550, 0, FitStatus.PASS, (280, 550)),
    (550, 280, 90, FitStatus.PASS, (280, 550)),
    (550, 280, 0, FitStatus.FAIL, (550, 280)),
    (280.001, 550, 0, FitStatus.FAIL, (280.001, 550)),
    (280, 550.001, 0, FitStatus.FAIL, (280, 550.001)),
    (550, 280, -90, FitStatus.PASS, (280, 550)),
    (280, 550, 180, FitStatus.PASS, (280, 550)),
])
def test_capacity_required_oracles(board, width, height, rotation, status, extents):
    result = check_capacity(rectangle(board, width, height), BoardCapacity("capacity", "1"), rotation_deg=rotation)
    assert result.check.status is status
    assert (result.width_mm, result.height_mm) == pytest.approx(extents, abs=1e-10)
    assert result.arithmetic_guard_mm <= 1e-8
    assert result.check.record_ids == (("capacity", "1"),)
    if status is FitStatus.FAIL:
        assert result.check.violations[0].code is ErrorCode.BOARD_CAPACITY_EXCEEDED
        assert dict(result.check.violations[0].context)["board_revision_id"] == board.board_revision_id


def test_capacity_general_rotation_and_negative_coordinates(board):
    outline = rectangle(board, 10, 20, x=-50, y=-30)
    result = check_capacity(outline, BoardCapacity("capacity", "1"), rotation_deg=45)
    assert result.width_mm == pytest.approx(15*sqrt(2), abs=1e-12)
    assert result.height_mm == pytest.approx(15*sqrt(2), abs=1e-12)


def test_machine_translation_does_not_affect_capacity(board, machine):
    outline = rectangle(board, 280, 550)
    results = []
    for dx, dy in ((0, 0), (1000, -900), (-23, 12)):
        load = Transform2.translation(board, machine, dx, dy, transform_id=f"load:{dx}")
        report = validate_fit(outline, BoardCapacity("capacity", "1"), rotation_deg=0,
                              report_id="fit", load_transform=load)
        results.append(report.capacity)
    assert results[0] == results[1] == results[2]


def semicircle(board, radius, clockwise=False):
    a, b, center = Point2(radius, 0, board), Point2(-radius, 0, board), Point2(0, 0, board)
    return Outline("semicircle", (CircularArc(a, b, center, clockwise), LineSegment(b, a)))


@pytest.mark.parametrize("clockwise", [False, True])
def test_arc_extremum_between_endpoints_is_included(board, clockwise):
    # Rotating a radius-281 semicircle by 90 degrees gives width 281,
    # although both arc endpoints have x=0 after rotation.
    result = check_capacity(semicircle(board, 281, clockwise), BoardCapacity("capacity", "1"), rotation_deg=90)
    assert (result.width_mm, result.height_mm) == pytest.approx((281, 562), abs=1e-10)
    assert result.check.status is FitStatus.FAIL


def test_two_arc_circle_has_complete_bounds(board):
    p, q, c = Point2(10, 0, board), Point2(-10, 0, board), Point2(0, 0, board)
    circle = Outline("circle", (CircularArc(p, q, c, False), CircularArc(q, p, c, False)))
    result = check_capacity(circle, BoardCapacity("capacity", "1"), rotation_deg=33)
    assert (result.width_mm, result.height_mm) == pytest.approx((20, 20), abs=1e-12)


def test_arc_bulge_exceeds_capacity_while_every_endpoint_fits(board):
    a, b, center = Point2(200, 500, board), Point2(0, 500, board), Point2(100, 500, board)
    c, d = Point2(0, 0, board), Point2(200, 0, board)
    outline = Outline("arched-board", (CircularArc(a, b, center, False), LineSegment(b, c),
                                        LineSegment(c, d), LineSegment(d, a)))
    assert max(edge.start.y for edge in outline.edges) == 500
    result = check_capacity(outline, BoardCapacity("capacity", "1"), rotation_deg=0)
    assert (result.width_mm, result.height_mm) == pytest.approx((200, 600), abs=1e-12)
    assert result.check.status is FitStatus.FAIL
    assert result.check.violations[0].code is ErrorCode.BOARD_CAPACITY_EXCEEDED


def test_major_arc_extrema_and_wrapped_angles(board):
    p, q, c = Point2(10, 0, board), Point2(0, 10, board), Point2(0, 0, board)
    outline = Outline("major-arc", (CircularArc(p, q, c, True), LineSegment(q, p)))
    result = check_capacity(outline, BoardCapacity("capacity", "1"), rotation_deg=0)
    assert (result.width_mm, result.height_mm) == pytest.approx((20, 20), abs=1e-12)


@pytest.mark.parametrize("coordinates", [
    ((0, 0), (2, 2), (0, 2), (2, 0)),  # bow tie
    ((0, 0), (1, 0), (2, 0)),          # zero area / overlapping closure
    ((0, 0), (2, 0), (1, 0), (1, 1)), # retraced edge
    ((0, 0), (2, 0), (2, 2), (1, 0), (0, 2)),  # nonadjacent touch
])
def test_invalid_polygon_topology_rejected(board, coordinates):
    with pytest.raises(GeometryError) as caught:
        Outline.polygon("invalid", tuple(Point2(x, y, board) for x, y in coordinates))
    assert caught.value.code is ErrorCode.OUTLINE_INVALID


def test_open_contour_and_arc_radius_mismatch_rejected(board):
    a, b, c = Point2(0, 0, board), Point2(1, 0, board), Point2(1, 1, board)
    with pytest.raises(GeometryError, match="OUTLINE_INVALID"):
        Outline("open", (LineSegment(a, b), LineSegment(b, c)))
    with pytest.raises(GeometryError, match="OUTLINE_INVALID"):
        CircularArc(b, Point2(0, 2, board), a, False)


def test_arc_crosses_nonadjacent_edge(board):
    p, q, c = Point2(10, 0, board), Point2(-10, 0, board), Point2(0, 0, board)
    a, b = Point2(-10, 5, board), Point2(10, 5, board)
    with pytest.raises(GeometryError, match="OUTLINE_INVALID"):
        Outline("crossing", (CircularArc(p, q, c, False), LineSegment(q, a), LineSegment(a, b), LineSegment(b, p)))


@pytest.mark.parametrize("value", [nan, inf, -inf, True, "0"])
def test_capacity_rotation_rejects_nonfinite_or_coerced(board, value):
    with pytest.raises(GeometryError, match="SCHEMA_INVALID"):
        check_capacity(rectangle(board, 1, 1), BoardCapacity("capacity", "1"), rotation_deg=value)


def test_unsupported_geometry_and_units_are_not_guessed(board):
    outline = rectangle(board, 10, 10)
    with pytest.raises(GeometryError, match="GEOMETRY_UNSUPPORTED"):
        replace(outline, holes=("cutout",))
    with pytest.raises(GeometryError, match="GEOMETRY_UNSUPPORTED"):
        Outline("spline", ("spline", "closing line"))
    inch = replace(board, kind=FrameKind.SOURCE, unit=Unit.INCH)
    with pytest.raises(GeometryError, match="GEOMETRY_UNSUPPORTED"):
        rectangle(inch, 1, 1)
    with pytest.raises(GeometryError, match="GEOMETRY_UNSUPPORTED"):
        rectangle(board, 1, 1, x=1e7)


def test_capacity_records_are_fixed_and_immutable():
    capacity = BoardCapacity("requirement", "1")
    assert (capacity.width_mm, capacity.height_mm) == (280, 550)
    with pytest.raises(FrozenInstanceError):
        capacity.width_mm = 281
    with pytest.raises(ValueError):
        replace(capacity, width_mm=281)
    with pytest.raises(GeometryError):
        BoardCapacity("", "1")


def evidence():
    return EnvelopeEvidence(EvidenceKind.SYNTHETIC, ("synthetic-fixture-01",))


def fixture_record(machine, **changes):
    values = dict(envelope_id="fixture-envelope", version="1", machine_id="m1", fixture_id="fixture-1",
                  configuration_id="fixture-config-1", frame=machine, usable_region=None, exclusions=(),
                  margin_mm=None, evidence=None)
    values.update(changes)
    return FixtureEnvelope(**values)


def travel_record(machine, **changes):
    values = dict(envelope_id="travel-envelope", version="2", machine_id="m1", camera_id="cam1",
                  configuration_id="mechanical-config-1", frame=machine, reference_point="camera optical axis reference",
                  permitted_region=None, exclusions=(), evidence=None)
    values.update(changes)
    return CameraTravelEnvelope(**values)


def test_missing_physical_envelopes_never_imply_readiness(board, machine):
    for fixture, travel in ((None, None), (fixture_record(machine), travel_record(machine))):
        report = validate_fit(rectangle(board, 280, 550), BoardCapacity("capacity", "1"),
                              rotation_deg=0, report_id="fit", fixture=fixture, travel=travel)
        assert report.capacity.check.status is FitStatus.PASS
        assert report.fixture.status is report.camera_reachability.status is FitStatus.UNRESOLVED
        assert not report.motion_authorized and not report.targeting_ready
        assert report.fixture.reasons and report.camera_reachability.reasons


def test_supplied_camera_rectangle_still_unresolved_with_evidence(board, machine):
    travel = travel_record(machine, permitted_region=rectangle(machine, 280, 550, name="travel-region"), evidence=evidence())
    report = validate_fit(rectangle(board, 280, 550), BoardCapacity("capacity", "1"),
                          rotation_deg=0, report_id="fit", travel=travel)
    assert report.camera_reachability.status is FitStatus.UNRESOLVED
    assert report.camera_reachability.record_ids == (("travel-envelope", "2"),)
    assert report.camera_reachability.evidence_ids == ("synthetic-fixture-01",)
    assert dict(report.context)["camera_reference_point"] == "camera optical axis reference"
    assert dict(report.context)["camera_configuration_id"] == "mechanical-config-1"
    with pytest.raises(GeometryError):
        replace(report, camera_reachability=FitCheck(FitStatus.PASS, ("rectangle exists",)))


def test_envelope_records_preserve_geometry_margin_and_synthetic_evidence(machine):
    region = rectangle(machine, 280, 550, name="usable")
    exclusion = rectangle(machine, 3, 4, name="keepout")
    fixture = fixture_record(machine, usable_region=region, exclusions=(exclusion,), margin_mm=0.2, evidence=evidence())
    assert fixture.usable_region == region and fixture.exclusions == (exclusion,)
    assert fixture.margin_mm == 0.2
    assert fixture.evidence.kind is EvidenceKind.SYNTHETIC
    with pytest.raises(GeometryError):
        replace(fixture.evidence, kind=EvidenceKind.QUALIFIED)
    with pytest.raises(FrozenInstanceError):
        fixture.margin_mm = 0


@pytest.mark.parametrize("changes", [
    {"machine_id": "other"}, {"configuration_id": ""}, {"fixture_id": ""},
    {"margin_mm": -1}, {"margin_mm": nan}, {"usable_region": "rectangle"},
    {"exclusions": []},
])
def test_invalid_fixture_records_fail(machine, changes):
    with pytest.raises(GeometryError):
        fixture_record(machine, **changes)


def test_wrong_frame_geometry_and_missing_evidence_fail(board, machine):
    with pytest.raises(GeometryError, match="CONTEXT_MISMATCH"):
        fixture_record(machine, usable_region=rectangle(board, 1, 1), evidence=evidence())
    with pytest.raises(GeometryError, match="SCHEMA_INVALID"):
        fixture_record(machine, usable_region=rectangle(machine, 1, 1))


@pytest.mark.parametrize("name", ["machine_id", "board_revision_id", "capture_id"])
def test_fit_inputs_cannot_mix_contexts(board, machine, name):
    fixture = fixture_record(machine)
    other_frame = replace(machine, frame_id="other-frame", **{name: "other"})
    if name == "capture_id":
        fixture = fixture_record(replace(machine, capture_id="original"))
    travel = travel_record(other_frame, machine_id=other_frame.machine_id)
    with pytest.raises(GeometryError, match="CONTEXT_MISMATCH"):
        validate_fit(rectangle(board, 1, 1), BoardCapacity("capacity", "1"), rotation_deg=0,
                     report_id="fit", fixture=fixture, travel=travel)


def test_wrong_source_and_unvalidated_load_are_rejected(board, machine):
    outline = rectangle(board, 10, 10)
    raw = Transform2("raw", board, machine, ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        validate_fit(outline, BoardCapacity("capacity", "1"), rotation_deg=0, report_id="fit", load_transform=raw)
    other = replace(board, origin="another datum")
    load = Transform2.translation(other, machine, 0, 0, transform_id="declared")
    with pytest.raises(GeometryError, match="CONTEXT_MISMATCH"):
        validate_fit(outline, BoardCapacity("capacity", "1"), rotation_deg=0, report_id="fit", load_transform=load)


def test_supplied_fixture_cannot_be_reported_pass_without_explicit_load(board, machine):
    fixture = fixture_record(machine, usable_region=rectangle(machine, 280, 550), margin_mm=0, evidence=evidence())
    report = validate_fit(rectangle(board, 280, 550), BoardCapacity("capacity", "1"),
                          rotation_deg=0, report_id="fit", fixture=fixture)
    assert report.fixture.status is FitStatus.UNRESOLVED
    assert report.fixture.reasons == ("LOAD_TRANSFORM_MISSING",)


def test_qualified_record_requires_explicit_separate_references():
    qualified = EnvelopeEvidence(EvidenceKind.QUALIFIED, ("measurement-1",), ("qualification-1",))
    assert qualified.qualification_ids == ("qualification-1",)
    with pytest.raises(GeometryError):
        EnvelopeEvidence(EvidenceKind.SYNTHETIC, ("simulation-1",), ("qualification-1",))


@pytest.mark.parametrize("value", [nan, inf, -inf])
def test_outline_coordinates_reject_nonfinite(board, value):
    with pytest.raises(GeometryError, match="SCHEMA_INVALID"):
        rectangle(board, value, 10)


def test_refuse_load_scaling_even_if_raw_conventions_match(board):
    machine = replace(board, kind=FrameKind.MACHINE, frame_id="M", machine_id="m1")
    scale = Transform2("scale", board, machine, ((2, 0, 0), (0, 2, 0), (0, 0, 1)))
    assert scale.conventions_validated
    with pytest.raises(GeometryError, match="GEOMETRY_UNSUPPORTED"):
        validate_fit(rectangle(board, 10, 10), BoardCapacity("capacity", "1"), rotation_deg=0,
                     report_id="fit", load_transform=scale)


def fitted(outline, machine, *, usable=None, exclusions=(), margin=0, dx=0, dy=0, travel=None):
    fixture = fixture_record(machine, usable_region=usable or rectangle(machine, 280, 550, name="usable"),
                             exclusions=exclusions, margin_mm=margin, evidence=evidence())
    load = Transform2.translation(outline.frame, machine, dx, dy, transform_id="load")
    return validate_fit(outline, BoardCapacity("capacity", "1"), rotation_deg=0,
                        report_id="fit", fixture=fixture, travel=travel, load_transform=load)


@pytest.mark.parametrize("dx,margin,status", [
    (0, 0, FitStatus.PASS), (0.001, 0, FitStatus.FAIL),
    (0, 0.001, FitStatus.FAIL),
])
def test_fixture_exact_outer_contact_and_small_violation(board, machine, dx, margin, status):
    report = fitted(rectangle(board, 280, 550), machine, dx=dx, margin=margin)
    assert report.capacity.check.status is FitStatus.PASS
    assert report.fixture.status is status
    assert report.camera_reachability.status is FitStatus.UNRESOLVED
    assert not report.targeting_ready and not report.motion_authorized
    if status is FitStatus.FAIL:
        issue = report.fixture.violations[0]
        assert issue.code is ErrorCode.BOARD_OUT_OF_ENVELOPE
        context = dict(issue.context)
        assert context["load_transform_id"] == "load"
        assert context["board_revision_id"] == board.board_revision_id
        assert context["machine_id"] == machine.machine_id
        assert context["numerical_policy_id"] == "fixture-binary64-v1"


@pytest.mark.parametrize("x,y,w,h", [
    (10, 2, 2, 2),  # shared edge contact
    (10, 10, 2, 2),  # shared corner contact
    (4, -2, 2, 14),  # edge crossing, every board vertex outside
    (4, 4, 2, 2),  # exclusion completely contained by board
    (-1, -1, 12, 12),  # board completely contained by exclusion
])
def test_exclusion_closed_filled_region_contract(board, machine, x, y, w, h):
    exclusion = rectangle(machine, w, h, x=x, y=y, name="exclusion")
    report = fitted(rectangle(board, 10, 10), machine, exclusions=(exclusion,))
    assert report.capacity.check.status is FitStatus.PASS
    assert report.fixture.status is FitStatus.FAIL
    assert dict(report.fixture.violations[0].context)["region_id"] == "exclusion"


@pytest.mark.parametrize("clearance,status", [(2, FitStatus.PASS), (1.999, FitStatus.FAIL)])
def test_outer_margin_exact_and_one_micron_shortfall(board, machine, clearance, status):
    report = fitted(rectangle(board, 10, 10), machine, margin=2, dx=clearance, dy=2)
    assert report.fixture.status is status


@pytest.mark.parametrize("gap,status", [(5, FitStatus.PASS), (4.999, FitStatus.FAIL)])
def test_exclusion_margin_exact_and_one_micron_shortfall(board, machine, gap, status):
    exclusion = rectangle(machine, 2, 2, x=30+gap, y=20, name="exclusion")
    report = fitted(rectangle(board, 10, 10), machine, dx=20, dy=20, margin=5, exclusions=(exclusion,))
    assert report.fixture.status is status


def test_exclusion_margin_uses_euclidean_corner_distance(board, machine):
    # Loaded board max corner (30,30), exclusion min corner (33,34): distance 5.
    exclusion = rectangle(machine, 2, 2, x=33, y=34, name="exclusion")
    report = fitted(rectangle(board, 10, 10), machine, dx=20, dy=20, margin=5, exclusions=(exclusion,))
    assert report.fixture.status is FitStatus.PASS


def test_fixture_arc_extremum_not_endpoint_bounds(board, machine):
    outline = semicircle(board, 10)
    report = fitted(outline, machine, dx=20, dy=20,
                    usable=rectangle(machine, 50, 29.999, name="usable"))
    # Arc endpoints load to y=20, but its interior reaches y=30.
    assert report.capacity.check.status is FitStatus.PASS
    assert report.fixture.status is FitStatus.FAIL
    exclusion = rectangle(machine, 2, 2, x=19, y=29, name="exclusion")
    assert fitted(outline, machine, dx=20, dy=20, exclusions=(exclusion,)).fixture.status is FitStatus.FAIL


def test_arc_tangent_exclusion_is_forbidden(board, machine):
    exclusion = rectangle(machine, 2, 2, x=19, y=30, name="exclusion")
    assert fitted(semicircle(board, 10), machine, dx=20, dy=20,
                  exclusions=(exclusion,)).fixture.status is FitStatus.FAIL


def test_missing_margin_unresolved_and_camera_rectangle_cannot_authorize(board, machine):
    travel = travel_record(machine, permitted_region=rectangle(machine, 400, 600, name="travel"), evidence=evidence())
    report = fitted(rectangle(board, 10, 10), machine, margin=None, travel=travel)
    assert report.fixture.status is FitStatus.UNRESOLVED
    assert report.fixture.reasons == ("FIXTURE_MARGIN_MISSING",)
    report = fitted(rectangle(board, 10, 10), machine, travel=travel)
    assert report.fixture.status is FitStatus.PASS
    assert report.camera_reachability.status is FitStatus.UNRESOLVED
    assert not report.motion_authorized and not report.targeting_ready
    assert report.fixture.evidence_ids == ("synthetic-fixture-01",)


@pytest.mark.parametrize("as_exclusion", [False, True])
def test_nonrectangular_envelope_rejected_even_with_missing_inputs(machine, as_exclusion):
    triangle = Outline.polygon("triangle", tuple(Point2(x, y, machine) for x, y in ((0, 0), (10, 0), (0, 10))))
    with pytest.raises(GeometryError, match="GEOMETRY_UNSUPPORTED"):
        fixture_record(machine, usable_region=None if as_exclusion else triangle,
                       exclusions=(triangle,) if as_exclusion else (), evidence=evidence())


@pytest.mark.parametrize("change", [
    {"frame_id": "other-M"}, {"origin": "other-origin"}, {"machine_id": "other-machine"},
    {"board_revision_id": "other-revision"}, {"capture_id": "other-capture"},
])
def test_known_geometry_requires_full_load_target_match(board, machine, change):
    target = replace(machine, **change)
    fixture = fixture_record(target, machine_id=target.machine_id,
                             usable_region=rectangle(target, 280, 550, name="usable"),
                             margin_mm=0, evidence=evidence())
    load = Transform2.translation(board, machine, 0, 0, transform_id="load")
    with pytest.raises(GeometryError, match="CONTEXT_MISMATCH"):
        validate_fit(rectangle(board, 10, 10), BoardCapacity("capacity", "1"), rotation_deg=0,
                     report_id="fit", fixture=fixture, load_transform=load)


def test_known_fixture_rejects_unvalidated_mapping(board, machine):
    fixture = fixture_record(machine, usable_region=rectangle(machine, 280, 550, name="usable"),
                             margin_mm=0, evidence=evidence())
    raw = Transform2("raw", board, machine, ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        validate_fit(rectangle(board, 10, 10), BoardCapacity("capacity", "1"), rotation_deg=0,
                     report_id="fit", fixture=fixture, load_transform=raw)


def test_fixture_diagnostics_are_independent_of_exclusion_input_order(board, machine):
    a = rectangle(machine, 1, 1, x=2, y=2, name="a")
    z = rectangle(machine, 1, 1, x=4, y=4, name="z")
    first = fitted(rectangle(board, 10, 10), machine, exclusions=(z, a))
    second = fitted(rectangle(board, 10, 10), machine, exclusions=(a, z))
    assert first == second
    assert [dict(v.context)["region_id"] for v in first.fixture.violations] == ["a", "z"]


@pytest.mark.parametrize("gap,status", [(3, FitStatus.PASS), (2.999, FitStatus.FAIL)])
def test_arc_interior_exclusion_clearance_through_api(board, machine, gap, status):
    exclusion = rectangle(machine, 2, 2, x=19, y=30+gap, name="exclusion")
    report = fitted(semicircle(board, 10), machine, dx=20, dy=20, margin=3, exclusions=(exclusion,))
    assert report.fixture.status is status


def test_loaded_rotation_is_separate_from_capacity_test_rotation(board, machine):
    outline = semicircle(board, 10)
    rotation = Transform2.rotation(board, board, 90, transform_id="rotation")
    shift = Transform2.translation(board, machine, 20, 20, transform_id="shift")
    load = shift.compose(rotation, transform_id="load")
    fixture = fixture_record(machine,
                             usable_region=rectangle(machine, 20, 50, x=10.001, name="usable"),
                             margin_mm=0, evidence=evidence())
    report = validate_fit(outline, BoardCapacity("capacity", "1"), rotation_deg=0,
                          report_id="fit", fixture=fixture, load_transform=load)
    assert (report.capacity.width_mm, report.capacity.height_mm) == pytest.approx((20, 10))
    # Loaded arc reaches x=10, outside the usable region, while both endpoints x=20 fit.
    assert report.fixture.status is FitStatus.FAIL


def test_concave_board_does_not_collide_via_bounding_box(board, machine):
    outline = Outline.polygon("L", tuple(Point2(x, y, board) for x, y in
                                        ((0, 0), (10, 0), (10, 2), (2, 2), (2, 10), (0, 10))))
    exclusion = rectangle(machine, 2, 2, x=4, y=4, name="exclusion")
    assert fitted(outline, machine, exclusions=(exclusion,)).fixture.status is FitStatus.PASS


def test_successful_fit_retains_capture_and_synthetic_evidence(board, machine):
    captured_machine = replace(machine, capture_id="capture-7")
    report = fitted(rectangle(board, 10, 10), captured_machine)
    assert report.fixture.status is FitStatus.PASS
    assert dict(report.context)["capture_id"] == "capture-7"
    assert report.fixture.record_ids == (("fixture-envelope", "1"),)
    assert report.fixture.evidence_ids == ("synthetic-fixture-01",)
    assert not report.targeting_ready
