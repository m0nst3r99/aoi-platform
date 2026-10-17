"""Adversarial regressions for the Geometry Core review (no new capability)."""

from dataclasses import FrozenInstanceError, replace

import pytest

from aoi_platform.geometry import (
    AxisDirection, Frame, GeometryError, Parity, Point2, Transform2, TransformKind,
)

IDENTITY = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


@pytest.mark.parametrize("reverse", [False, True])
def test_raw_identity_cannot_normalize_different_units(
    mm_frame: Frame, inch_frame: Frame, reverse: bool
) -> None:
    source, target = (mm_frame, inch_frame) if reverse else (inch_frame, mm_frame)
    raw = Transform2("undeclared-unit-change", source, target, IDENTITY)
    assert not raw.conventions_validated
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        raw.apply(Point2(1, 2, source))


@pytest.mark.parametrize("directions", [
    (AxisDirection.RIGHT, AxisDirection.DOWN),
    (AxisDirection.LEFT, AxisDirection.UP),
    (AxisDirection.UP, AxisDirection.RIGHT),
])
def test_raw_identity_cannot_normalize_different_axes(mm_frame: Frame, directions: tuple) -> None:
    source = replace(
        mm_frame, frame_id="incompatible-axes", x_direction=directions[0], y_direction=directions[1]
    )
    raw = Transform2("undeclared-axis-change", source, mm_frame, IDENTITY)
    assert not raw.conventions_validated
    assert raw.matrix == IDENTITY  # Labels do not cause an inferred reflection.
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        raw.apply(Point2(1, 2, source))


def test_rigid_composition_retains_kind_and_inverse_kind(mm_frame: Frame) -> None:
    rotation = Transform2.rotation(mm_frame, mm_frame, 90, transform_id="rotation")
    move = Transform2.translation(mm_frame, mm_frame, 10, -3, transform_id="move")
    composed = move.compose(rotation, transform_id="proper-pose")
    assert composed.kind is TransformKind.RIGID
    assert composed.inverse(transform_id="inverse-pose").kind is TransformKind.RIGID
    result = composed.apply(Point2(1, 2, mm_frame))
    assert (result.x, result.y) == pytest.approx((8, -2), abs=1e-12)
    assert composed.parity is Parity.PRESERVED
    assert composed.conventions_validated


@pytest.mark.parametrize("operation", ["orientation", "inverse", "outer", "inner"])
def test_unvalidated_units_cannot_be_laundered_by_other_operations(
    mm_frame: Frame, inch_frame: Frame, operation: str
) -> None:
    raw = Transform2("unvalidated", inch_frame, mm_frame, IDENTITY)
    back = Transform2.unit_conversion(mm_frame, inch_frame, transform_id="back")
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        if operation == "orientation":
            raw.map_orientation(30)
        elif operation == "inverse":
            raw.inverse(transform_id="inverse")
        elif operation == "outer":
            # Endpoints would have identical units; the bad intermediate must still fail.
            raw.compose(back, transform_id="same-mm-endpoints")
        else:
            back.compose(raw, transform_id="same-inch-endpoints")


@pytest.mark.parametrize("provenance", [
    ("caller-supplied matrix",), ("declared-unit-conversion:inch->mm",),
    ("explicit-reflection:y=0.0 mm",),
])
def test_provenance_text_does_not_authorize_normalization(
    mm_frame: Frame, inch_frame: Frame, provenance: tuple[str, ...]
) -> None:
    raw = Transform2("forged-description", inch_frame, mm_frame, IDENTITY, provenance=provenance)
    assert not raw.conventions_validated
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        raw.apply(Point2(1, 2, inch_frame))


def test_correct_raw_matrix_still_requires_explicit_unit_operation(
    mm_frame: Frame, inch_frame: Frame
) -> None:
    raw = Transform2("raw-factor", inch_frame, mm_frame, ((25.4, 0, 0), (0, 25.4, 0), (0, 0, 1)))
    assert not raw.conventions_validated
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        raw.apply(Point2(1, 2, inch_frame))
    conversion = Transform2.unit_conversion(inch_frame, mm_frame, transform_id="explicit-units")
    assert conversion.conventions_validated
    result = conversion.apply(Point2(1, 2, inch_frame))
    assert (result.x, result.y) == pytest.approx((25.4, 50.8), abs=1e-12)


def test_axis_evidence_is_from_explicit_operation_not_raw_matrix(mm_frame: Frame) -> None:
    down = replace(mm_frame, frame_id="downward", y_direction=AxisDirection.DOWN)
    mirror_matrix = ((1, 0, 0), (0, -1, 0), (0, 0, 1))
    raw = Transform2("raw-mirror", down, mm_frame, mirror_matrix, kind=TransformKind.REFLECTION)
    assert not raw.conventions_validated
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        raw.map_orientation(30)
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        raw.inverse(transform_id="not-evidence")

    mirror = Transform2.reflection(down, mm_frame, axis="y", transform_id="declared-mirror")
    assert mirror.conventions_validated
    result = mirror.apply(Point2(25.4, 50.8, down))
    assert (result.x, result.y) == (25.4, -50.8)
    back = mirror.inverse(transform_id="back")
    assert back.conventions_validated
    assert back.apply(result) == Point2(25.4, 50.8, down)
    assert back.compose(mirror, transform_id="two-mirrors").conventions_validated


def test_translation_is_not_axis_mapping_evidence(mm_frame: Frame) -> None:
    other = replace(mm_frame, frame_id="other-axes", y_direction=AxisDirection.DOWN)
    translation = Transform2.translation(other, mm_frame, 0, 0, transform_id="not-an-axis-map")
    assert not translation.conventions_validated
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        translation.apply(Point2(1, 2, other))


def test_replacement_cannot_reuse_validation_for_a_different_matrix(
    mm_frame: Frame, inch_frame: Frame
) -> None:
    scale = Transform2.unit_conversion(inch_frame, mm_frame, transform_id="units")
    altered = replace(scale, matrix=IDENTITY)
    assert not altered.conventions_validated
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        altered.apply(Point2(1, 2, inch_frame))
    down = replace(mm_frame, frame_id="down", y_direction=AxisDirection.DOWN)
    mirror = Transform2.reflection(down, mm_frame, axis="y", transform_id="mirror")
    altered_mirror = replace(mirror, matrix=IDENTITY, kind=TransformKind.AFFINE)
    assert not altered_mirror.conventions_validated
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        altered_mirror.apply(Point2(1, 2, down))
    with pytest.raises(FrozenInstanceError):
        altered.conventions_validated = True  # type: ignore[misc]


def test_validated_units_compose_with_general_affine_and_invert(
    mm_frame: Frame, inch_frame: Frame
) -> None:
    units = Transform2.unit_conversion(inch_frame, mm_frame, transform_id="units")
    affine = Transform2("shear", mm_frame, mm_frame, ((1, 2, 3), (0, 1, -4), (0, 0, 1)))
    combined = affine.compose(units, transform_id="explicit-composition")
    assert combined.conventions_validated
    assert combined.kind is TransformKind.AFFINE
    result = combined.apply(Point2(1, 2, inch_frame))
    assert (result.x, result.y) == pytest.approx((130, 46.8), abs=1e-12)
    inverse = combined.inverse(transform_id="inverse")
    assert inverse.conventions_validated
    original = inverse.apply(result)
    assert (original.x, original.y) == pytest.approx((1, 2), abs=1e-12)


@pytest.mark.parametrize("operand", ["reflection", "general", "affine-identity"])
@pytest.mark.parametrize("reverse", [False, True])
def test_composition_does_not_promote_reflection_or_affine_to_rigid(
    mm_frame: Frame, operand: str, reverse: bool
) -> None:
    rigid = Transform2.rotation(mm_frame, mm_frame, 90, transform_id="rigid")
    if operand == "reflection":
        other = Transform2.reflection(mm_frame, mm_frame, axis="x", transform_id="mirror")
    else:
        matrix = IDENTITY if operand == "affine-identity" else ((1, 2, 0), (0, 1, 0), (0, 0, 1))
        other = Transform2("general", mm_frame, mm_frame, matrix)
    outer, inner = (other, rigid) if reverse else (rigid, other)
    result = outer.compose(inner, transform_id="composition")
    assert result.kind is TransformKind.AFFINE
    assert result.conventions_validated
    expected_parity = Parity.REFLECTED if operand == "reflection" else Parity.PRESERVED
    assert result.parity is expected_parity


def test_two_reflections_remain_conservatively_affine(mm_frame: Frame) -> None:
    mirror = Transform2.reflection(mm_frame, mm_frame, axis="x", offset=5, transform_id="mirror")
    result = mirror.compose(mirror, transform_id="two-reflections")
    assert result.kind is TransformKind.AFFINE
    assert result.parity is Parity.PRESERVED
    assert result.apply(Point2(2, 3, mm_frame)) == Point2(2, 3, mm_frame)


def test_kind_declaration_alone_cannot_launder_axis_change(mm_frame: Frame) -> None:
    other = replace(mm_frame, frame_id="other-axes", y_direction=AxisDirection.DOWN)
    raw_rigid = Transform2("raw-rigid", other, mm_frame, IDENTITY, kind=TransformKind.RIGID)
    known_rigid = Transform2.rotation(mm_frame, mm_frame, 90, transform_id="known-rigid")
    assert not raw_rigid.conventions_validated
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        known_rigid.compose(raw_rigid, transform_id="not-a-validated-rigid-pose")


@pytest.mark.parametrize("matrix", [IDENTITY, ((1, 0, -90), (0, 1, 50), (0, 0, 1))])
@pytest.mark.parametrize("provenance", [
    ("caller-supplied matrix",), ("explicit-translation:-90,50 mm",),
])
def test_raw_mapping_cannot_assert_a_datum_relationship(
    mm_frame: Frame, matrix: tuple, provenance: tuple[str, ...]
) -> None:
    # Independent world datums: source=(10,20), target=(100,-30).
    # Source (2,3) is world (12,23), hence target (-88,53), not (2,3).
    source = replace(mm_frame, frame_id="source-datum", origin="world position (10,20)")
    target = replace(mm_frame, frame_id="target-datum", origin="world position (100,-30)")
    raw = Transform2("raw-datum", source, target, matrix, provenance=provenance)
    assert not raw.conventions_validated
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        raw.apply(Point2(2, 3, source))


@pytest.mark.parametrize("operation", ["rotation-zero", "rotation", "reflection", "offset-reflection"])
def test_axis_factories_do_not_supply_missing_datum_evidence(mm_frame: Frame, operation: str) -> None:
    target = replace(mm_frame, frame_id="offset-datum", origin="distinct datum at (100,-30)")
    if operation.startswith("rotation"):
        mapping = Transform2.rotation(
            mm_frame, target, 0 if operation == "rotation-zero" else 90, transform_id="rotation"
        )
    else:
        mapping = Transform2.reflection(
            mm_frame, target, axis="x", offset=5 if operation == "offset-reflection" else 0,
            transform_id="reflection",
        )
    assert not mapping.conventions_validated
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        mapping.apply(Point2(2, 3, mm_frame))


@pytest.mark.parametrize("operation", ["orientation", "inverse", "outer", "inner"])
def test_unvalidated_datum_cannot_be_laundered(mm_frame: Frame, operation: str) -> None:
    target = replace(mm_frame, frame_id="distinct-datum", origin="offset datum")
    raw = Transform2("raw-datum", mm_frame, target, IDENTITY)
    back = Transform2.translation(target, mm_frame, 90, -50, transform_id="back")
    with pytest.raises(GeometryError, match="MAPPING_UNVALIDATED"):
        if operation == "orientation":
            raw.map_orientation(0)
        elif operation == "inverse":
            raw.inverse(transform_id="inverse")
        elif operation == "outer":
            raw.compose(back, transform_id="outer")
        else:
            back.compose(raw, transform_id="inner")


def test_explicit_datum_translation_and_inverse_match_world_oracles(mm_frame: Frame) -> None:
    source = replace(mm_frame, frame_id="source-datum", origin="world position (10,20)")
    target = replace(mm_frame, frame_id="target-datum", origin="world position (100,-30)")
    move = Transform2.translation(source, target, -90, 50, transform_id="declared-datums")
    assert move.conventions_validated
    assert move.apply(Point2(2, 3, source)) == Point2(-88, 53, target)
    assert move.inverse(transform_id="back").apply(Point2(-88, 53, target)) == Point2(2, 3, source)
    assert not replace(move, matrix=IDENTITY).conventions_validated


def test_zero_translation_explicitly_declares_coincident_named_datums(mm_frame: Frame) -> None:
    alias = replace(mm_frame, frame_id="datum-alias", origin="explicitly coincident alias")
    move = Transform2.translation(mm_frame, alias, 0, 0, transform_id="declared-coincidence")
    assert move.conventions_validated
    assert move.apply(Point2(2, 3, mm_frame)) == Point2(2, 3, alias)


@pytest.mark.parametrize("operation", ["rotation", "reflection"])
def test_explicit_axis_operation_then_datum_translation(mm_frame: Frame, operation: str) -> None:
    source = replace(mm_frame, frame_id="source-datum", origin="world position (10,20)")
    target = replace(mm_frame, frame_id="target-datum", origin="world position (100,-30)")
    if operation == "rotation":
        axis_map = Transform2.rotation(source, source, 90, transform_id="rotate")
        # Rotate (2,3) to (-3,2) about world (10,20): world (7,22).
        expected = (-93, 52)
        parity = Parity.PRESERVED
    else:
        axis_map = Transform2.reflection(source, source, axis="x", offset=5, transform_id="mirror")
        # Reflect about world x=15: world (12,23) -> (18,23).
        expected = (-82, 53)
        parity = Parity.REFLECTED
    move = Transform2.translation(source, target, -90, 50, transform_id="datum-shift")
    combined = move.compose(axis_map, transform_id="declared-combination")
    result = combined.apply(Point2(2, 3, source))
    assert (result.x, result.y) == pytest.approx(expected, abs=1e-12)
    assert combined.parity is parity
    recovered = combined.inverse(transform_id="back").apply(Point2(*expected, target))
    assert (recovered.x, recovered.y) == pytest.approx((2, 3), abs=1e-6)
