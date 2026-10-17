"""Explicit affine maps: T_B_A maps column-vector coordinates in A into B.

Only finite affine maps are implemented. No frame graph, camera calibration,
automatic datum inference or physical board rescaling is performed here.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from math import atan2, cos, degrees, isclose, radians, sin, sqrt
from typing import ClassVar, Literal, TypeAlias, cast

from .angles import normalize_angle
from .errors import ErrorCode, GeometryError, finite_number, require_text
from .models import Frame, Parity, Point2, Unit, require_same_frame

Row3: TypeAlias = tuple[float, float, float]
Matrix3: TypeAlias = tuple[Row3, Row3, Row3]


class TransformKind(StrEnum):
    AFFINE = "affine"
    RIGID = "rigid"
    REFLECTION = "reflection"


def _frames(source: Frame, target: Frame, *, same_units: bool = False) -> None:
    for name, value in (("from_frame", source), ("to_frame", target)):
        if not isinstance(value, Frame):
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Supply a Frame record.", field_path=name
            )
    if source.frame_id == target.frame_id:
        require_same_frame(source, target, "transform.frames")
    for name in ("board_revision_id", "machine_id", "capture_id"):
        left, right = getattr(source, name), getattr(target, name)
        if left is not None and right is not None and left != right:
            raise GeometryError(
                ErrorCode.CONTEXT_MISMATCH,
                f"Cannot map between conflicting {name}: {left!r}, {right!r}.",
                field_path=f"transform.{name}",
            )
    if (source.unit is Unit.PIXEL) != (target.unit is Unit.PIXEL):
        raise GeometryError(
            ErrorCode.SCHEMA_INVALID,
            "Pixel/physical conversion requires a calibrated mapping, outside this core.",
            field_path="transform.units",
        )
    if same_units and source.unit != target.unit:
        raise GeometryError(
            ErrorCode.SCHEMA_INVALID, "Convert units explicitly before this operation.",
            field_path="transform.units",
        )


@dataclass(frozen=True, slots=True)
class Transform2:
    """Numerically checked affine transform with explicit source and target.

    A supplied matrix operates directly on the declared units; no hidden unit
    factor is inserted. Translation entries are in the target frame's units.
    `outer.compose(inner)` means outer @ inner (apply inner first).
    Direction metadata is descriptive: callers explicitly supply axis changes.
    Raw maps across unit/axis/datum conventions remain unvalidated and cannot be used.
    Operation factories and validated compositions provide explicit evidence;
    arbitrary provenance strings never authorize a convention change.
    """

    transform_id: str
    from_frame: Frame
    to_frame: Frame
    matrix: Matrix3
    kind: TransformKind = TransformKind.AFFINE
    provenance: tuple[str, ...] = ("caller-supplied matrix",)
    parity: Parity = field(init=False)
    condition_number: float = field(init=False)
    conventions_validated: bool = field(init=False)

    # Numerical subset only, not a production CalibrationPolicy implementation.
    policy_id: ClassVar[str] = "synthetic-geometry-v1"
    max_condition_number: ClassVar[float] = 1e8
    valid_domain: ClassVar[Literal["finite-affine-plane"]] = "finite-affine-plane"

    def __post_init__(self) -> None:
        require_text(self.transform_id, "transform.transform_id")
        _frames(self.from_frame, self.to_frame)
        if not isinstance(self.kind, TransformKind):
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Use a supported TransformKind.",
                field_path="transform.kind",
            )
        if not isinstance(self.provenance, tuple) or not self.provenance:
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Supply immutable provenance entries.",
                field_path="transform.provenance",
            )
        for entry in self.provenance:
            require_text(entry, "transform.provenance")
        if not isinstance(self.matrix, tuple) or len(self.matrix) != 3 or any(
            not isinstance(row, tuple) or len(row) != 3 for row in self.matrix
        ):
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Supply three immutable rows of three numbers.",
                field_path="transform.matrix",
            )
        matrix = cast(Matrix3, tuple(
            tuple(finite_number(v, f"transform.matrix[{i}][{j}]") for j, v in enumerate(row))
            for i, row in enumerate(self.matrix)
        ))
        if matrix[2] != (0.0, 0.0, 1.0):
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID,
                "Affine bottom row must be (0, 0, 1); projective maps are not implemented.",
                field_path="transform.matrix[2]",
            )
        object.__setattr__(self, "matrix", matrix)
        a, b, c, d, _ = self._normalized_linear()
        det = a * d - b * c
        if det == 0.0:
            raise GeometryError(
                ErrorCode.TRANSFORM_SINGULAR, "Linear block has zero determinant.",
                field_path="transform.matrix",
            )
        # Spectral condition number using a max-entry-normalized 2x2 block.
        # s_max^2 / |det| avoids cancellation in calculating s_min.
        trace = a*a + b*b + c*c + d*d
        largest = (trace + sqrt(max(0.0, trace*trace - 4.0*det*det))) / 2.0
        condition = largest / abs(det)
        if condition > self.max_condition_number:
            raise GeometryError(
                ErrorCode.TRANSFORM_ILL_CONDITIONED,
                f"Normalized linear condition {condition:g} exceeds {self.max_condition_number:g}.",
                field_path="transform.matrix",
            )
        object.__setattr__(self, "condition_number", condition)
        object.__setattr__(self, "parity", Parity.PRESERVED if det > 0 else Parity.REFLECTED)
        if self.kind is not TransformKind.AFFINE:
            self._validate_isometry()
        object.__setattr__(self, "conventions_validated", (
            self.from_frame.unit == self.to_frame.unit
            and self.from_frame.origin == self.to_frame.origin
            and self.from_frame.x_direction == self.to_frame.x_direction
            and self.from_frame.y_direction == self.to_frame.y_direction
        ))

    def _require_validated_conventions(self) -> None:
        if not self.conventions_validated:
            raise GeometryError(
                ErrorCode.MAPPING_UNVALIDATED,
                f"Transform {self.transform_id!r} has no validated unit/axis/datum mapping. "
                "Use explicit unit conversion, translation and rotation/reflection operations, "
                "then compose validated transforms.",
                field_path="transform.conventions_validated",
            )

    def _normalized_linear(self) -> tuple[float, float, float, float, float]:
        a, b, _ = self.matrix[0]
        c, d, _ = self.matrix[1]
        scale = max(abs(a), abs(b), abs(c), abs(d))
        if scale == 0:
            raise GeometryError(
                ErrorCode.TRANSFORM_SINGULAR, "Linear block is zero.",
                field_path="transform.matrix",
            )
        return a/scale, b/scale, c/scale, d/scale, scale

    def _validate_isometry(self) -> None:
        _frames(self.from_frame, self.to_frame, same_units=True)
        a, b, tx = self.matrix[0]
        c, d, ty = self.matrix[1]
        def close(x: float, y: float) -> bool:
            return isclose(x, y, rel_tol=0.0, abs_tol=1e-12)

        orthogonal = close(a*a + c*c, 1) and close(b*b + d*d, 1) and close(a*b + c*d, 0)
        proper = self.parity is Parity.PRESERVED
        if not orthogonal or (self.kind is TransformKind.RIGID and not proper):
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Kind does not match a unit-scale isometry.",
                field_path="transform.kind",
            )
        if self.kind is TransformKind.REFLECTION and (
            proper or not close(a*tx + b*ty + tx, 0) or not close(c*tx + d*ty + ty, 0)
        ):
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Reflection must reverse parity and be self-inverse.",
                field_path="transform.kind",
            )

    def apply(self, point: Point2) -> Point2:
        self._require_validated_conventions()
        if not isinstance(point, Point2):
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Supply a Point2.", field_path="point"
            )
        require_same_frame(point.frame, self.from_frame, "point.frame")
        a, b, tx = self.matrix[0]
        c, d, ty = self.matrix[1]
        return Point2(a*point.x + b*point.y + tx, c*point.x + d*point.y + ty, self.to_frame)

    def compose(self, before: "Transform2", *, transform_id: str) -> "Transform2":
        """Return self @ before; mismatched intermediate frame metadata fails."""
        if not isinstance(before, Transform2):
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Supply a Transform2.", field_path="before"
            )
        self._require_validated_conventions()
        before._require_validated_conventions()
        require_same_frame(before.to_frame, self.from_frame, "composition.intermediate_frame")
        matrix = cast(Matrix3, tuple(
            tuple(sum(self.matrix[i][k] * before.matrix[k][j] for k in range(3)) for j in range(3))
            for i in range(3)
        ))
        kind = (
            TransformKind.RIGID
            if self.kind is TransformKind.RIGID and before.kind is TransformKind.RIGID
            else TransformKind.AFFINE
        )
        result = Transform2(
            transform_id, before.from_frame, self.to_frame, matrix,
            kind=kind,
            provenance=before.provenance + (before.transform_id,) + self.provenance + (self.transform_id,),
        )
        # Evidence comes from both validated operands, never endpoint labels.
        object.__setattr__(result, "conventions_validated", True)
        return result

    def inverse(self, *, transform_id: str) -> "Transform2":
        self._require_validated_conventions()
        a, b, c, d, scale = self._normalized_linear()
        det = a*d - b*c
        ia, ib, ic, id_ = d/det/scale, -b/det/scale, -c/det/scale, a/det/scale
        tx, ty = self.matrix[0][2], self.matrix[1][2]
        result = Transform2(
            transform_id, self.to_frame, self.from_frame,
            ((ia, ib, -(ia*tx + ib*ty)), (ic, id_, -(ic*tx + id_*ty)), (0, 0, 1)),
            kind=self.kind, provenance=self.provenance + (f"inverse:{self.transform_id}",),
        )
        object.__setattr__(result, "conventions_validated", True)
        return result

    def map_orientation(
        self, angle_deg: float, parity: Parity = Parity.PRESERVED
    ) -> tuple[float, Parity]:
        """Map the local +X direction and combine parity; translation is ignored.

        Input orientation is expressed in from_frame, output in to_frame.
        The returned angle alone cannot represent a reflected footprint.
        """
        self._require_validated_conventions()
        if not isinstance(parity, Parity):
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Supply a Parity enum.", field_path="orientation.parity"
            )
        theta = radians(normalize_angle(angle_deg))
        a, b, c, d, _ = self._normalized_linear()
        x, y = a*cos(theta) + b*sin(theta), c*cos(theta) + d*sin(theta)
        result_parity = Parity.PRESERVED if parity is self.parity else Parity.REFLECTED
        return normalize_angle(degrees(atan2(y, x))), result_parity

    @classmethod
    def unit_conversion(cls, source: Frame, target: Frame, *, transform_id: str) -> "Transform2":
        """Change physical units only; shared datum/directions must be declared."""
        _frames(source, target)
        if (source.origin, source.x_direction, source.y_direction) != (
            target.origin, target.x_direction, target.y_direction
        ):
            raise GeometryError(
                ErrorCode.CONTEXT_MISMATCH, "Unit-only conversion requires the same declared datum/axes.",
                field_path="transform.frames",
            )
        if source.unit is Unit.PIXEL:
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Pixels have no physical unit conversion.",
                field_path="transform.units",
            )
        mm_per_unit = {Unit.MM: 1.0, Unit.INCH: 25.4}
        factor = mm_per_unit[source.unit] / mm_per_unit[target.unit]
        result = cls(
            transform_id, source, target, ((factor, 0, 0), (0, factor, 0), (0, 0, 1)),
            provenance=(f"declared-unit-conversion:{source.unit}->{target.unit}",),
        )
        object.__setattr__(result, "conventions_validated", True)
        return result

    @classmethod
    def rotation(
        cls, source: Frame, target: Frame, angle_deg: float, *, transform_id: str
    ) -> "Transform2":
        """Declare an axis rotation about a shared datum; translate datums separately."""
        _frames(source, target, same_units=True)
        theta = radians(normalize_angle(angle_deg))
        c, s = cos(theta), sin(theta)
        result = cls(
            transform_id, source, target, ((c, -s, 0), (s, c, 0), (0, 0, 1)),
            kind=TransformKind.RIGID, provenance=(f"explicit-rotation-deg:{angle_deg}",),
        )
        object.__setattr__(result, "conventions_validated", source.origin == target.origin)
        return result

    @classmethod
    def translation(
        cls, source: Frame, target: Frame, dx: float, dy: float, *, transform_id: str
    ) -> "Transform2":
        """Declare the source origin's target coordinates, with matching units/axes.

        Explicit zero offsets assert coincident datums; labels never imply this.
        """
        _frames(source, target, same_units=True)
        dx, dy = finite_number(dx, "translation.dx"), finite_number(dy, "translation.dy")
        result = cls(
            transform_id, source, target, ((1, 0, dx), (0, 1, dy), (0, 0, 1)),
            kind=TransformKind.RIGID, provenance=(f"explicit-translation:{dx},{dy} {target.unit}",),
        )
        object.__setattr__(result, "conventions_validated", (
            source.x_direction == target.x_direction and source.y_direction == target.y_direction
        ))
        return result

    @classmethod
    def reflection(
        cls, source: Frame, target: Frame, *, axis: Literal["x", "y"],
        offset: float = 0.0, transform_id: str,
    ) -> "Transform2":
        """Mirror x or y about offset in a shared datum.

        The mirror-line offset does not declare a relationship between datums.
        """
        _frames(source, target, same_units=True)
        offset = finite_number(offset, "reflection.offset")
        if axis == "x":
            matrix: Matrix3 = ((-1, 0, 2*offset), (0, 1, 0), (0, 0, 1))
        elif axis == "y":
            matrix = ((1, 0, 0), (0, -1, 2*offset), (0, 0, 1))
        else:
            raise GeometryError(
                ErrorCode.SCHEMA_INVALID, "Reflection axis must be 'x' or 'y'.",
                field_path="reflection.axis",
            )
        result = cls(
            transform_id, source, target, matrix, kind=TransformKind.REFLECTION,
            provenance=(f"explicit-reflection:{axis}={offset} {target.unit}",),
        )
        object.__setattr__(result, "conventions_validated", source.origin == target.origin)
        return result
