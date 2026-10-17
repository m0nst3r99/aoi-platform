"""Bounded analytic line/circular-arc outlines; no chord approximation.

The initial kernel accepts one simple closed contour in mm, without holes.
Predicate epsilon is 1e-8 mm, a numerical guard, not a physical fit margin.
Coordinates/radii above 1e6 mm and contours above 512 edges are unsupported.
Ambiguous near-degenerate topology is rejected rather than repaired.
"""

from dataclasses import dataclass
from math import atan2, cos, fsum, hypot, pi, sin, sqrt, tau

from .errors import ErrorCode, GeometryError, finite_number, require_text
from .models import Frame, Point2, Unit, require_same_frame

EPS = 1e-8
MAX_COORDINATE = 1e6
MAX_EDGES = 512


def reject(message: str, path: str = "outline", *, unsupported: bool = False) -> None:
    raise GeometryError(ErrorCode.GEOMETRY_UNSUPPORTED if unsupported else ErrorCode.OUTLINE_INVALID,
                        message, field_path=path)


def checked_point(point: Point2) -> None:
    if not isinstance(point, Point2):
        reject("Supply Point2 records.")
    if point.frame.unit is not Unit.MM:
        reject("Normalize geometry to mm explicitly before outline checks.", unsupported=True)
    if max(abs(point.x), abs(point.y)) > MAX_COORDINATE:
        reject("Coordinates exceed the supported numerical domain (1e6 mm).", unsupported=True)


def distance(a: Point2, b: Point2) -> float:
    return hypot(a.x - b.x, a.y - b.y)


@dataclass(frozen=True, slots=True)
class LineSegment:
    start: Point2
    end: Point2

    def __post_init__(self) -> None:
        checked_point(self.start)
        checked_point(self.end)
        require_same_frame(self.end.frame, self.start.frame, "line.frame")
        if distance(self.start, self.end) <= EPS:
            reject("Zero-length or numerically degenerate line.")


@dataclass(frozen=True, slots=True)
class CircularArc:
    start: Point2
    end: Point2
    center: Point2
    clockwise: bool

    def __post_init__(self) -> None:
        for point in (self.start, self.end, self.center):
            checked_point(point)
            require_same_frame(point.frame, self.start.frame, "arc.frame")
        if type(self.clockwise) is not bool:
            reject("Declare clockwise as bool.")
        if distance(self.start, self.end) <= EPS:
            reject("Arc endpoints must be distinct; split a full circle into arcs.")
        if self.radius <= EPS or abs(self.radius - distance(self.end, self.center)) > EPS:
            reject("Arc endpoints must lie on the same nonzero circle.")
        if self.radius > MAX_COORDINATE:
            reject("Radius exceeds supported numerical domain.", unsupported=True)

    @property
    def radius(self) -> float:
        return distance(self.start, self.center)

    @property
    def start_angle(self) -> float:
        return atan2(self.start.y - self.center.y, self.start.x - self.center.x)

    @property
    def sweep(self) -> float:
        end = atan2(self.end.y - self.center.y, self.end.x - self.center.x)
        return -((self.start_angle - end) % tau) if self.clockwise else (end - self.start_angle) % tau

    def parameter(self, angle: float) -> float:
        delta = (self.start_angle - angle) % tau if self.clockwise else (angle - self.start_angle) % tau
        return delta / abs(self.sweep)

    def includes(self, angle: float) -> bool:
        # Endpoints may round across the 2*pi branch cut.
        delta = (self.start_angle - angle) % tau if self.clockwise else (angle - self.start_angle) % tau
        angular_guard = EPS / self.radius
        return delta <= abs(self.sweep) + angular_guard or tau - delta <= angular_guard

    def at(self, fraction: float) -> Point2:
        if fraction == 0:
            return self.start
        if fraction == 1:
            return self.end
        angle = self.start_angle + fraction * self.sweep
        return Point2(self.center.x + self.radius*cos(angle), self.center.y + self.radius*sin(angle), self.start.frame)


Curve = LineSegment | CircularArc


def point_line_distance(point: Point2, line: LineSegment) -> float:
    dx, dy = line.end.x-line.start.x, line.end.y-line.start.y
    t = max(0.0, min(1.0, ((point.x-line.start.x)*dx + (point.y-line.start.y)*dy)/(dx*dx+dy*dy)))
    return hypot(point.x-line.start.x-t*dx, point.y-line.start.y-t*dy)


def point_curve_distance(point: Point2, curve: Curve) -> float:
    if isinstance(curve, LineSegment):
        return point_line_distance(point, curve)
    angle = atan2(point.y-curve.center.y, point.x-curve.center.x)
    candidates = [distance(point, curve.start), distance(point, curve.end)]
    if curve.includes(angle):
        candidates.append(abs(distance(point, curve.center)-curve.radius))
    return min(candidates)


def intersections(a: Curve, b: Curve) -> tuple[Point2, ...]:
    """Analytic intersections; overlapping boundaries are invalid topology."""
    if isinstance(a, CircularArc) and isinstance(b, LineSegment):
        return intersections(b, a)
    if isinstance(a, LineSegment) and isinstance(b, LineSegment):
        dx, dy = a.end.x-a.start.x, a.end.y-a.start.y
        ex, ey = b.end.x-b.start.x, b.end.y-b.start.y
        qx, qy = b.start.x-a.start.x, b.start.y-a.start.y
        cross = dx*ey-dy*ex
        if cross == 0:
            if abs(qx*dy-qy*dx) > EPS*hypot(dx, dy):
                return ()
            points = tuple(p for p in (a.start, a.end, b.start, b.end)
                           if point_line_distance(p, a) <= EPS and point_line_distance(p, b) <= EPS)
            if points and any(distance(points[0], p) > EPS for p in points):
                reject("Overlapping collinear boundary segments.")
            return points[:1]
        t, u = (qx*ey-qy*ex)/cross, (qx*dy-qy*dx)/cross
        if -EPS/hypot(dx, dy) <= t <= 1+EPS/hypot(dx, dy) and -EPS/hypot(ex, ey) <= u <= 1+EPS/hypot(ex, ey):
            return (Point2(a.start.x+t*dx, a.start.y+t*dy, a.start.frame),)
        return ()
    if isinstance(a, LineSegment):
        assert isinstance(b, CircularArc)
        length = distance(a.start, a.end)
        ux, uy = (a.end.x-a.start.x)/length, (a.end.y-a.start.y)/length
        along = (b.center.x-a.start.x)*ux + (b.center.y-a.start.y)*uy
        normal = (b.center.x-a.start.x)*uy - (b.center.y-a.start.y)*ux
        if abs(normal) > b.radius + EPS:
            return ()
        offset = sqrt(max(0.0, (b.radius-abs(normal))*(b.radius+abs(normal))))
        points = []
        for t in (along-offset, along+offset):
            if -EPS <= t <= length+EPS:
                p = Point2(a.start.x+t*ux, a.start.y+t*uy, a.start.frame)
                if b.includes(atan2(p.y-b.center.y, p.x-b.center.x)):
                    points.append(p)
        return tuple(points)
    assert isinstance(a, CircularArc) and isinstance(b, CircularArc)
    d = distance(a.center, b.center)
    if d <= EPS:
        if abs(a.radius-b.radius) > EPS:
            return ()
        for left, right in ((a, b), (b, a)):
            for p in (left.start, left.at(0.5), left.end):
                if right.includes(atan2(p.y-right.center.y, p.x-right.center.x)) and min(distance(p, right.start), distance(p, right.end)) > EPS:
                    reject("Overlapping circular arcs.")
        return tuple(p for p in (a.start, a.end) if min(distance(p, b.start), distance(p, b.end)) <= EPS)
    if d > a.radius+b.radius+EPS or d < abs(a.radius-b.radius)-EPS:
        return ()
    along = (a.radius*a.radius-b.radius*b.radius+d*d)/(2*d)
    height = sqrt(max(0.0, (a.radius-along)*(a.radius+along)))
    ux, uy = (b.center.x-a.center.x)/d, (b.center.y-a.center.y)/d
    points = []
    for sign in (-1, 1):
        p = Point2(a.center.x+along*ux-sign*height*uy, a.center.y+along*uy+sign*height*ux, a.start.frame)
        if a.includes(atan2(p.y-a.center.y, p.x-a.center.x)) and b.includes(atan2(p.y-b.center.y, p.x-b.center.x)):
            points.append(p)
    return tuple(points)


@dataclass(frozen=True, slots=True)
class Outline:
    outline_id: str
    edges: tuple[Curve, ...]
    holes: tuple = ()

    def __post_init__(self) -> None:
        require_text(self.outline_id, "outline.outline_id")
        if not isinstance(self.edges, tuple) or len(self.edges) < 2:
            reject("Supply an immutable closed contour of at least two edges.")
        if self.holes != () or not isinstance(self.holes, tuple):
            reject("Holes are not supported by this outline kernel.", unsupported=True)
        if len(self.edges) > MAX_EDGES:
            reject("Contour edge limit exceeded (512).", unsupported=True)
        if any(type(edge) not in (LineSegment, CircularArc) for edge in self.edges):
            reject("Only line segments and circular arcs are supported.", unsupported=True)
        for i, edge in enumerate(self.edges):
            require_same_frame(edge.start.frame, self.frame, "outline.frame")
            if edge.end != self.edges[(i+1) % len(self.edges)].start:
                reject("Contour is open; adjacent endpoints must match exactly.")
            for j in range(i):
                other = self.edges[j]
                allowed = []
                if j == i-1:
                    allowed.append(edge.start)
                if j == 0 and i == len(self.edges)-1:
                    allowed.append(edge.end)
                for p in intersections(edge, other):
                    if not any(distance(p, shared) <= EPS for shared in allowed):
                        reject("Contour self-intersects or touches a nonadjacent edge.")
        # Translate area arithmetic to a contour anchor to reduce cancellation.
        anchor = self.edges[0].start
        terms = []
        for edge in self.edges:
            ax, ay = edge.start.x-anchor.x, edge.start.y-anchor.y
            bx, by = edge.end.x-anchor.x, edge.end.y-anchor.y
            if isinstance(edge, LineSegment):
                terms.append(ax*by-ay*bx)
            else:
                cx, cy = edge.center.x-anchor.x, edge.center.y-anchor.y
                terms.append(cx*(by-ay)-cy*(bx-ax)+edge.radius**2*edge.sweep)
        if abs(fsum(terms)) <= EPS*EPS:
            reject("Contour has zero or numerically degenerate area.")

    @property
    def frame(self) -> Frame:
        return self.edges[0].start.frame

    @classmethod
    def polygon(cls, outline_id: str, vertices: tuple[Point2, ...]) -> "Outline":
        if not isinstance(vertices, tuple) or len(vertices) < 3:
            reject("Supply at least three polygon vertices without a repeated closing vertex.")
        return cls(outline_id, tuple(LineSegment(a, b) for a, b in zip(vertices, vertices[1:]+vertices[:1])))


def rotation_components(degrees: float) -> tuple[float, float]:
    angle = finite_number(degrees, "capacity.rotation_deg") % 360
    exact = {0: (1.0, 0.0), 90: (0.0, 1.0), 180: (-1.0, 0.0), 270: (0.0, -1.0)}
    return exact[angle] if angle in exact else (cos(angle*pi/180), sin(angle*pi/180))


def projected_bounds(outline: Outline, ux: float, uy: float) -> tuple[float, float]:
    values = []
    for edge in outline.edges:
        values.extend((ux*edge.start.x+uy*edge.start.y, ux*edge.end.x+uy*edge.end.y))
        if isinstance(edge, CircularArc):
            angle = atan2(uy, ux)
            for candidate in (angle, angle+pi):
                if edge.includes(candidate):
                    values.append(ux*edge.center.x+uy*edge.center.y + edge.radius*(ux*cos(candidate)+uy*sin(candidate)))
    return min(values), max(values)


def outline_bounds(outline: Outline, rotation_deg: float = 0) -> tuple[float, float, float, float]:
    if not isinstance(outline, Outline):
        reject("Supply a validated Outline record.", unsupported=True)
    c, s = rotation_components(rotation_deg)
    xmin, xmax = projected_bounds(outline, c, -s)
    ymin, ymax = projected_bounds(outline, s, c)
    return xmin, ymin, xmax, ymax
