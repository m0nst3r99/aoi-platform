"""Bounded fixed-grid predicates; no floating topology or rational accumulation.

Each kernel reserves its conservative primitive envelope before doing work.
Bookkeeping and bit-length checks are not mathematical predicate primitives.
All products/sums are magnitude-checked before evaluation. Q is 2**1074.
"""

from dataclasses import dataclass

Q = 1 << 1074
D = (1e-8).as_integer_ratio()[0] * (Q // (1e-8).as_integer_ratio()[1])
MAX_INTEGER = (1 << 4382) - 1


class Exhausted(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Work:
    primitives: int
    edge_pairs: int
    containment_visits: int
    max_bits: int


class Ledger:
    def __init__(self, passes=1):
        self.limit = (1 << 26) * passes
        self.pair_limit = 130816 * passes
        self.visit_limit = 16384 * passes
        self.primitives = self.edge_pairs = self.containment_visits = self.max_bits = 0

    def charge(self, primitives=0, pairs=0, visits=0):
        if (self.primitives + primitives > self.limit
                or self.edge_pairs + pairs > self.pair_limit
                or self.containment_visits + visits > self.visit_limit):
            raise Exhausted("work")
        self.primitives += primitives
        self.edge_pairs += pairs
        self.containment_visits += visits

    def checked(self, value):
        bits = abs(value).bit_length()
        if bits > 4382:
            raise Exhausted("arithmetic")
        self.max_bits = max(self.max_bits, bits)
        return value

    def add(self, a, b):
        self.checked(a)
        self.checked(b)
        if (a >= 0 and b >= 0 and a > MAX_INTEGER-b
                or a < 0 and b < 0 and -a > MAX_INTEGER+b):
            raise Exhausted("arithmetic")
        return self.checked(a+b)

    def sub(self, a, b):
        return self.add(a, -b)

    def mul(self, a, b):
        self.checked(a)
        self.checked(b)
        if b and abs(a) > MAX_INTEGER // abs(b):
            raise Exhausted("arithmetic")
        return self.checked(a*b)

    def snapshot(self):
        return Work(self.primitives, self.edge_pairs, self.containment_visits, self.max_bits)


def grid(value):
    # Caller has admitted a finite bounded binary64, including subnormals.
    numerator, denominator = value.as_integer_ratio()
    return numerator * (Q // denominator)


def vector(a, b, w):
    return w.sub(b[0], a[0]), w.sub(b[1], a[1])


def dot(a, b, w):
    return w.add(w.mul(a[0], b[0]), w.mul(a[1], b[1]))


def cross(a, b, w):
    return w.sub(w.mul(a[0], b[1]), w.mul(a[1], b[0]))


def orient(a, b, c, w):
    return cross(vector(a, b, w), vector(a, c, w), w)


def on_segment(p, a, b):
    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def intersects(a, b, c, d, w):
    ab_c, ab_d = orient(a, b, c, w), orient(a, b, d, w)
    cd_a, cd_b = orient(c, d, a, w), orient(c, d, b, w)
    return ((ab_c == 0 and on_segment(c, a, b))
            or (ab_d == 0 and on_segment(d, a, b))
            or (cd_a == 0 and on_segment(a, c, d))
            or (cd_b == 0 and on_segment(b, c, d))
            or ((ab_c > 0) != (ab_d > 0) and (cd_a > 0) != (cd_b > 0)
                and ab_c != 0 and ab_d != 0 and cd_a != 0 and cd_b != 0))


def near_point(p, a, b, w):
    """Squared distance <= binary64(1e-8)**2, including projection endpoints."""
    v, u = vector(a, b, w), vector(a, p, w)
    length, projection = dot(v, v, w), dot(u, v, w)
    guard = w.mul(D, D)
    if projection <= 0:
        return dot(u, u, w) <= guard
    if projection >= length:
        end = vector(b, p, w)
        return dot(end, end, w) <= guard
    determinant = cross(v, u, w)
    return w.mul(determinant, determinant) <= w.mul(guard, length)


def separated(a, b, c, d, w):
    # <=64 products, <=128 additions/subtractions, <=128 comparisons.
    w.charge(320, pairs=1)
    return not (intersects(a, b, c, d, w)
                or near_point(a, c, d, w) or near_point(b, c, d, w)
                or near_point(c, a, b, w) or near_point(d, a, b, w))


def adjacent_valid(a, shared, b, w):
    w.charge(320, pairs=1)
    # Collinear continuation is valid; retracing a positive segment is not.
    return orient(a, shared, b, w) != 0 or dot(vector(shared, a, w), vector(shared, b, w), w) < 0


def inside(p, vertices, w):
    """Half-open ray. Only called after strict boundary separation."""
    odd = False
    for i, a in enumerate(vertices):
        w.charge(16, visits=1)
        b = vertices[(i+1) % len(vertices)]
        if (a[1] > p[1]) != (b[1] > p[1]):
            determinant = orient(a, b, p, w)
            if (determinant > 0) == (b[1] > a[1]):
                odd = not odd
    return odd


def area(vertices, w):
    total = 0
    for i, a in enumerate(vertices):
        w.charge(16)
        total = w.add(total, orient(vertices[0], a, vertices[(i+1) % len(vertices)], w))
    return total
