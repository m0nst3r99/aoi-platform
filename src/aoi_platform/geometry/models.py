"""Immutable coordinate values; frame metadata never implies a transformation."""

from dataclasses import dataclass
from enum import StrEnum

from .errors import ErrorCode, GeometryError, finite_number, require_text


class Unit(StrEnum):
    MM = "mm"
    INCH = "inch"
    PIXEL = "px"


class FrameKind(StrEnum):
    SOURCE = "source"
    PCB = "pcb"
    FOOTPRINT = "footprint"
    MACHINE = "machine"
    RAW_IMAGE = "raw_image"
    UNDISTORTED_IMAGE = "undistorted_image"
    DERIVED_IMAGE = "derived_image"


class AxisDirection(StrEnum):
    RIGHT = "right"
    LEFT = "left"
    UP = "up"
    DOWN = "down"

    @property
    def horizontal(self) -> bool:
        return self in (AxisDirection.RIGHT, AxisDirection.LEFT)


class Parity(StrEnum):
    PRESERVED = "preserved"
    REFLECTED = "reflected"


@dataclass(frozen=True, slots=True)
class Frame:
    """Named 2D datum. IDs must be scoped to their owning revision/machine/capture.

    Direction labels describe the declared view; arithmetic never auto-mirrors.
    Source frames can represent later panel/unit datums without changing Point2.
    """

    frame_id: str
    kind: FrameKind
    unit: Unit
    origin: str
    x_direction: AxisDirection
    y_direction: AxisDirection
    board_revision_id: str | None = None
    machine_id: str | None = None
    capture_id: str | None = None

    def __post_init__(self) -> None:
        require_text(self.frame_id, "frame.frame_id")
        require_text(self.origin, "frame.origin")
        for name, value, enum_type in (
            ("kind", self.kind, FrameKind),
            ("unit", self.unit, Unit),
            ("x_direction", self.x_direction, AxisDirection),
            ("y_direction", self.y_direction, AxisDirection),
        ):
            if not isinstance(value, enum_type):
                raise GeometryError(
                    ErrorCode.SCHEMA_INVALID, "Use a declared enum value.",
                    field_path=f"frame.{name}",
                )
        if self.x_direction.horizontal == self.y_direction.horizontal:
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Axes must be perpendicular.",
                field_path="frame.axis_directions",
            )
        for name in ("board_revision_id", "machine_id", "capture_id"):
            value = getattr(self, name)
            if value is not None:
                require_text(value, f"frame.{name}")
        if self.kind is FrameKind.PCB:
            require_text(self.board_revision_id, "frame.board_revision_id")
            if (self.unit, self.x_direction, self.y_direction) != (
                Unit.MM, AxisDirection.RIGHT, AxisDirection.UP
            ):
                raise GeometryError(
                    ErrorCode.SCHEMA_INVALID, "Canonical PCB is mm, X right, Y up.",
                    field_path="frame",
                )
        if self.kind is FrameKind.MACHINE:
            require_text(self.machine_id, "frame.machine_id")
            if self.unit is not Unit.MM:
                raise GeometryError(
                    ErrorCode.SCHEMA_INVALID, "Machine coordinates use mm.",
                    field_path="frame.unit",
                )
        if self.kind in (
            FrameKind.RAW_IMAGE, FrameKind.UNDISTORTED_IMAGE, FrameKind.DERIVED_IMAGE
        ):
            require_text(self.capture_id, "frame.capture_id")
            if (self.unit, self.x_direction, self.y_direction) != (
                Unit.PIXEL, AxisDirection.RIGHT, AxisDirection.DOWN
            ):
                raise GeometryError(
                    ErrorCode.SCHEMA_INVALID, "Image coordinates are px, u right, v down.",
                    field_path="frame",
                )


@dataclass(frozen=True, slots=True)
class Point2:
    x: float
    y: float
    frame: Frame

    def __post_init__(self) -> None:
        if not isinstance(self.frame, Frame):
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Supply the complete Frame record.",
                field_path="point.frame",
            )
        object.__setattr__(self, "x", finite_number(self.x, "point.x"))
        object.__setattr__(self, "y", finite_number(self.y, "point.y"))

    @property
    def frame_id(self) -> str:
        return self.frame.frame_id


def require_same_frame(actual: Frame, expected: Frame, field_path: str) -> None:
    """Match metadata/context too, so reusing an ID cannot bypass validation."""
    if actual != expected:
        raise GeometryError(
            ErrorCode.CONTEXT_MISMATCH,
            f"Expected frame {expected.frame_id!r} and its metadata; got {actual.frame_id!r}.",
            field_path=field_path,
        )
