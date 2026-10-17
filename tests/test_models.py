from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import pytest

from aoi_platform.geometry import (
    AxisDirection, ErrorCode, Frame, FrameKind, GeometryError, Point2, Unit,
)


def test_point_is_finite_immutable_and_retains_full_frame(mm_frame: Frame) -> None:
    point = Point2(1, -2, mm_frame)
    assert point.frame_id == mm_frame.frame_id
    assert (point.x, point.y) == (1.0, -2.0)
    with pytest.raises(FrozenInstanceError):
        point.x = 7  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        mm_frame.unit = Unit.INCH  # type: ignore[misc]


@pytest.mark.parametrize("value", [nan, inf, -inf, True, "1", 10**400])
def test_point_rejects_invalid_numbers(mm_frame: Frame, value: object) -> None:
    with pytest.raises(GeometryError) as caught:
        Point2(value, 0, mm_frame)  # type: ignore[arg-type]
    assert caught.value.code is ErrorCode.SCHEMA_INVALID
    assert caught.value.field_path == "point.x"


def test_point_rejects_a_bare_frame_id() -> None:
    with pytest.raises(GeometryError, match="point.frame"):
        Point2(0, 0, "unknown")  # type: ignore[arg-type]


@pytest.mark.parametrize("updates", [
    {"frame_id": ""}, {"origin": " "}, {"unit": "mm"}, {"kind": "panel"},
    {"x_direction": "right"}, {"y_direction": AxisDirection.LEFT},
    {"machine_id": ""}, {"board_revision_id": ""}, {"capture_id": " "},
])
def test_frame_rejects_ambiguous_metadata(mm_frame: Frame, updates: dict) -> None:
    with pytest.raises(GeometryError) as caught:
        replace(mm_frame, **updates)
    assert caught.value.code is ErrorCode.SCHEMA_INVALID


def test_pcb_frame_requires_revision_and_canonical_convention(mm_frame: Frame) -> None:
    pcb = replace(mm_frame, kind=FrameKind.PCB)
    assert pcb.unit is Unit.MM
    for updates in (
        {"board_revision_id": None}, {"unit": Unit.INCH},
        {"y_direction": AxisDirection.DOWN},
    ):
        with pytest.raises(GeometryError):
            replace(pcb, **updates)


def test_machine_frame_has_explicit_identity_without_fixed_machine_count(mm_frame: Frame) -> None:
    for machine_id in ("one-off-machine", "factory-b/machine-273"):
        machine = replace(mm_frame, kind=FrameKind.MACHINE, machine_id=machine_id)
        assert machine.machine_id == machine_id
    with pytest.raises(GeometryError):
        replace(mm_frame, kind=FrameKind.MACHINE)
    with pytest.raises(GeometryError):
        replace(mm_frame, kind=FrameKind.MACHINE, machine_id="m", unit=Unit.INCH)


def test_image_frame_metadata_does_not_supply_a_calibration(mm_frame: Frame) -> None:
    image = replace(
        mm_frame, kind=FrameKind.RAW_IMAGE, unit=Unit.PIXEL,
        y_direction=AxisDirection.DOWN, capture_id="capture-1",
    )
    assert Point2(0, 0, image).frame.unit is Unit.PIXEL
    for updates in ({"capture_id": None}, {"unit": Unit.MM}):
        with pytest.raises(GeometryError):
            replace(image, **updates)


def test_source_axes_can_be_explicitly_permuted(mm_frame: Frame) -> None:
    permuted = replace(mm_frame, x_direction=AxisDirection.UP, y_direction=AxisDirection.LEFT)
    assert Point2(2, 3, permuted).x == 2  # Metadata does not transform coordinates.
