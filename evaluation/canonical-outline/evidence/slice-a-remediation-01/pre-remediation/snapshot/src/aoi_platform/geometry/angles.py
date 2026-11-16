"""Angles in degrees; positive is counterclockwise in canonical PCB XY."""

from .errors import finite_number


def normalize_angle(angle_deg: float) -> float:
    """Return [0, 360), including for negative and multiple-turn inputs."""
    value = finite_number(angle_deg, "angle_deg") % 360.0
    # Tiny negative inputs can round to exactly 360 during modulo.
    return 0.0 if value == 360.0 else value


def signed_angular_difference(target_deg: float, source_deg: float) -> float:
    """Return target - source in [-180, 180); the antipodal tie is -180."""
    delta = normalize_angle(target_deg) - normalize_angle(source_deg)
    return (delta + 180.0) % 360.0 - 180.0
