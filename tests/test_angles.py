from math import inf, nan

import pytest

from aoi_platform.geometry import GeometryError, normalize_angle, signed_angular_difference


@pytest.mark.parametrize("angle,expected", [
    (0, 0), (360, 0), (-360, 0), (720, 0), (-90, 270), (450, 90), (359.95, 359.95),
])
def test_normalize_independent_values(angle: float, expected: float) -> None:
    assert normalize_angle(angle) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("target,source,expected", [
    (0.02, 359.95, 0.07), (359.95, 0.02, -0.07),
    (180, 0, -180), (0, 180, -180), (450, -90, -180), (720, 0, 0),
])
def test_signed_difference_has_explicit_order(target: float, source: float, expected: float) -> None:
    assert signed_angular_difference(target, source) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("value", [nan, inf, -inf, True, "90"])
def test_angles_reject_nonfinite_or_coerced_input(value: object) -> None:
    with pytest.raises(GeometryError):
        normalize_angle(value)  # type: ignore[arg-type]
    with pytest.raises(GeometryError):
        signed_angular_difference(0, value)  # type: ignore[arg-type]


def test_extreme_finite_angles_do_not_overflow_and_ranges_are_half_open() -> None:
    assert 0 <= normalize_angle(-1e-20) < 360
    assert -180 <= signed_angular_difference(1e308, -1e308) < 180
