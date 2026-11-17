"""Private binary64 draft fitting. No frame conversion or activation.

Guards are testable decision margins, not certified error/uncertainty bounds.
All inputs to this module must already have passed bounded admission.
"""

from dataclasses import dataclass
from math import fsum, hypot, isfinite, sqrt, ulp

EPS = 2.0 ** -52
RHO_FLOOR = 1e-8


class NumericalFailure(Exception):
    """An admitted computation could not produce finite usable numbers."""


def finite(*values):
    if not all(isfinite(x) for x in values):
        raise NumericalFailure


def guard(value, scale):
    result = 128 * EPS * max(1.0, scale) + 8 * ulp(value)
    finite(result)
    return result


def compare(value, limit, margin, *, lower=False):
    """Strict interior PASS; equality and overlapping margins are ambiguous."""
    finite(value, limit, margin)
    if lower:
        return "PASS" if value - margin > limit else (
            "FAIL" if value + margin < limit else "INDETERMINATE")
    return "PASS" if value + margin < limit else (
        "FAIL" if value - margin > limit else "INDETERMINATE")


def baseline(points):
    # Caller sorts by ID. First maximum wins, including exact ties.
    best = (-1.0, 0, 1)
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            distance = hypot(points[j][0] - points[i][0], points[j][1] - points[i][1])
            finite(distance)
            if distance > best[0]:
                best = (distance, i, j)
    return best


def _center(points):
    anchor = points[0]
    delta = tuple((x - anchor[0], y - anchor[1]) for x, y in points)
    mean = tuple(fsum(p[k] for p in delta) / len(points) for k in (0, 1))
    centered = tuple((x - mean[0], y - mean[1]) for x, y in delta)
    scale = max(abs(v) for p in centered for v in p)
    finite(*mean, scale, *(v for p in centered for v in p))
    if scale == 0:
        return anchor, mean, None
    normalized = tuple((x / scale, y / scale) for x, y in centered)
    finite(*(v for p in normalized for v in p))
    return anchor, mean, normalized


@dataclass(frozen=True, slots=True)
class Fit:
    coefficients: tuple[float, float, float, float] | None
    correlation: float
    correlation_guard: float
    conditioning: str


def solve(source, target):
    pa, pm, x = _center(source)
    qa, qm, y = _center(target)
    margin = 256 * len(source) * EPS
    if x is None or y is None:
        return Fit(None, 0.0, margin, "FAIL")
    a = fsum(v for p, q in zip(x, y) for v in (p[0] * q[0], p[1] * q[1]))
    b = fsum(v for p, q in zip(x, y) for v in (p[0] * q[1], -p[1] * q[0]))
    ep = fsum(v * v for p in x for v in p)
    eq = fsum(v * v for p in y for v in p)
    radius = hypot(a, b)
    finite(a, b, ep, eq, radius)
    if ep == 0 or eq == 0 or radius == 0:
        return Fit(None, 0.0, margin, "FAIL")
    rho = radius / (sqrt(ep) * sqrt(eq))
    finite(rho)
    if rho > 1 + margin:
        raise NumericalFailure
    status = compare(rho, RHO_FLOOR, margin, lower=True)
    if status != "PASS":
        return Fit(None, rho, margin, status)
    c, s = a / radius, b / radius
    tx = fsum((qa[0], qm[0], -c * pa[0], -c * pm[0], s * pa[1], s * pm[1]))
    ty = fsum((qa[1], qm[1], -s * pa[0], -s * pm[0], -c * pa[1], -c * pm[1]))
    finite(c, s, tx, ty)
    if abs(c) > 1 + 8 * EPS or abs(s) > 1 + 8 * EPS or abs(fsum((c*c, s*s, -1))) > 32 * EPS:
        raise NumericalFailure
    return Fit(tuple(0.0 if v == 0 else v for v in (c, s, tx, ty)), rho, margin, status)


def residuals(source, target, coefficients):
    c, s, tx, ty = coefficients
    result = []
    for (x, y), (u, v) in zip(source, target):
        dx = fsum((c*x, -s*y, tx, -u))
        dy = fsum((s*x, c*y, ty, -v))
        distance = hypot(dx, dy)
        finite(dx, dy, distance)
        result.append(tuple(0.0 if z == 0 else z for z in (dx, dy, distance)))
    rms = sqrt(fsum(p[2] * p[2] for p in result) / len(result))
    maximum = max(p[2] for p in result)
    finite(rms, maximum)
    return tuple(result), rms, maximum


def off_baseline(point, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    distance = hypot(dx, dy)
    if distance == 0:
        raise NumericalFailure
    value = abs(fsum((dx * (point[1] - start[1]), -dy * (point[0] - start[0])))) / distance
    finite(value)
    return value
