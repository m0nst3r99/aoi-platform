"""Canonical line-only outline with identified cutouts, independent of machines.

Declaration provenance is retained, NOT authenticated against source bytes here.
All topology decisions concern the supplied binary64 values exactly. The 1e-8
guard is numerical, not production accuracy. Legacy line/arc APIs are unchanged.
No implicit conversion to a filled legacy Outline is supplied (it would lose holes).
"""

from dataclasses import dataclass, replace
from math import isfinite
from typing import ClassVar

from . import _outline_exact as exact
from ._contour_validation import validate_contour
from .errors import ErrorCode as Code, GeometryError
from .models import AxisDirection, Frame, FrameKind, Parity, Point2, Unit
from .reports import ContractError, ValidationReport
from .transforms import Transform2, TransformKind


@dataclass(frozen=True, slots=True)
class CanonicalOutlinePolicy:
    """Fixed approved v1 limits; caller-selectable identity, not tunable budgets."""
    policy_id: str = "canonical-line-outline-v1"
    guard_hex: str = (1e-8).hex()
    max_coordinate_mm: ClassVar[float] = 1e6
    max_edges: ClassVar[int] = 512
    max_cutouts: ClassVar[int] = 32
    max_id_bytes: ClassVar[int] = 256
    max_detail_bytes: ClassVar[int] = 1024
    max_metadata_bytes: ClassVar[int] = 262144
    max_references: ClassVar[int] = 1024
    max_diagnostics: ClassVar[int] = 32
    diagnostic_bytes: ClassVar[int] = 4096
    max_diagnostic_bytes: ClassVar[int] = 131072
    arithmetic_bits: ClassVar[int] = 4382
    validation_primitives: ClassVar[int] = 1 << 26
    transform_primitives: ClassVar[int] = 1 << 27
    validation_pairs: ClassVar[int] = 130816
    transform_pairs: ClassVar[int] = 261632
    validation_containment_visits: ClassVar[int] = 16384
    transform_containment_visits: ClassVar[int] = 32768


POLICY = CanonicalOutlinePolicy()


@dataclass(frozen=True, slots=True)
class OutlineProvenance:
    """Synthetic or source-declared reference; no implied exact token span."""
    kind: str
    artifact_id: str
    sha256: str
    entity_id: str
    locator: str


@dataclass(frozen=True, slots=True)
class DeclaredLine:
    start: Point2
    end: Point2
    provenance: tuple[OutlineProvenance, ...]
    reversed_from_source: bool = False


@dataclass(frozen=True, slots=True)
class RingDeclaration:
    ring_id: str
    edges: tuple[DeclaredLine, ...]


@dataclass(frozen=True, slots=True)
class CanonicalOutlineDeclaration:
    outline_id: str
    frame: Frame
    exterior: RingDeclaration
    cutouts: tuple[RingDeclaration, ...] = ()


@dataclass(frozen=True, slots=True)
class OutlineTransform:
    transform_id: str
    from_frame: Frame
    to_frame: Frame
    matrix: tuple[tuple[float, ...], ...]
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CanonicalOutline:
    outline_id: str
    frame: Frame
    exterior: RingDeclaration
    cutouts: tuple[RingDeclaration, ...]
    policy: CanonicalOutlinePolicy
    transforms: tuple[OutlineTransform, ...] = ()


@dataclass(frozen=True, slots=True)
class CanonicalOutlineSuccess:
    outline: CanonicalOutline
    report: ValidationReport
    work: exact.Work


@dataclass(frozen=True, slots=True)
class CanonicalOutlineFailure:
    report: ValidationReport
    truncated: bool
    work: exact.Work


class _Invalid(Exception):
    def __init__(self, code, path, message):
        self.code, self.path, self.message = code, path, message


def _require(condition, code, path, message):
    if not condition:
        raise _Invalid(code, path, message)


class _Admission:
    def __init__(self):
        self.text_bytes = 0
        self.references = 0
        self.hashes = {}

    def text(self, value, path, limit=256):
        _require(type(value) is str, Code.SCHEMA_INVALID, path, "Supply text.")
        # Bound before UTF-8 allocation; every code point needs at least one byte.
        _require(len(value) <= limit, Code.INPUT_LIMIT_EXCEEDED, path, "Text limit exceeded.")
        try:
            size = len(value.encode("utf-8"))
        except UnicodeError:
            raise _Invalid(Code.SCHEMA_INVALID, path, "Invalid Unicode text.") from None
        _require(value.strip() != "", Code.SCHEMA_INVALID, path, "Supply nonempty text.")
        _require(size <= limit and self.text_bytes + size <= 262144,
                 Code.INPUT_LIMIT_EXCEEDED, path, "Metadata byte limit exceeded.")
        self.text_bytes += size

    def frame(self, frame):
        _require(type(frame) is Frame, Code.SCHEMA_INVALID, "frame", "Supply a Frame.")
        _require((frame.kind, frame.unit, frame.x_direction, frame.y_direction) ==
                 (FrameKind.PCB, Unit.MM, AxisDirection.RIGHT, AxisDirection.UP)
                 and frame.machine_id is None and frame.capture_id is None,
                 Code.CONTEXT_MISMATCH, "frame", "Require canonical PCB mm/right/up without machine/capture context.")
        for name in ("frame_id", "board_revision_id", "origin"):
            self.text(getattr(frame, name), "frame."+name, 1024 if name == "origin" else 256)

    def references_for(self, refs):
        _require(type(refs) is tuple and bool(refs), Code.SCHEMA_INVALID,
                 "provenance", "Supply immutable explicit provenance references.")
        _require(self.references+len(refs) <= 1024, Code.INPUT_LIMIT_EXCEEDED,
                 "provenance", "Reference occurrence limit exceeded.")
        self.references += len(refs)
        for ref in refs:
            _require(type(ref) is OutlineProvenance, Code.SCHEMA_INVALID,
                     "provenance", "Supply OutlineProvenance records.")
            _require(ref.kind in ("synthetic", "source-declared"), Code.SCHEMA_INVALID,
                     "provenance.kind", "Declare synthetic or source-declared evidence.")
            for name in ("kind", "artifact_id", "sha256", "entity_id", "locator"):
                self.text(getattr(ref, name), "provenance."+name, 1024 if name == "locator" else 256)
            _require(len(ref.sha256) == 64 and all(c in "0123456789abcdef" for c in ref.sha256),
                     Code.SCHEMA_INVALID, "provenance.sha256", "Supply lowercase SHA-256 text.")
            old = self.hashes.get(ref.artifact_id)
            _require(old is None or old == ref.sha256, Code.SOURCE_CONFLICT,
                     "provenance.sha256", "One artifact identity has conflicting declared hashes.")
            self.hashes[ref.artifact_id] = ref.sha256


class _Issues:
    """Reserve 4096 bytes per diagnostic BEFORE retention/report serialization.

Messages are static; bounded field paths contain only admitted ring IDs and edge
indices. Their worst-case JSON escaped representation is under 4096 bytes.
31 ordinary slots plus one reserved exhaustion slot, at most 128 KiB total.
"""
    def __init__(self):
        self.values = []
        self.truncated = False

    def add(self, code, path, message):
        if self.truncated:
            return
        if len(self.values) == 31:
            self.truncated = True
            code, path, message = Code.INPUT_LIMIT_EXCEEDED, "diagnostics", "Diagnostic limit exceeded; further issues omitted."
        self.values.append(ContractError(code, message, path, "Correct the declaration; no geometry was returned."))

    def report(self):
        return ValidationReport("canonical-outline", POLICY.policy_id, tuple(self.values),
                                (("assurance", "bounded-declared-binary64-topology"),))

    def exhausted(self, path):
        self.add(Code.INPUT_LIMIT_EXCEEDED, path, "Exact arithmetic/work budget exhausted; further checks omitted.")
        self.truncated = True


class _CanonicalContour:
    def __init__(self, ring, points, ledger, issues):
        self.ring, self.points, self.w, self.issues = ring, points, ledger, issues
        self.valid = True
        self.signed_area = 0

    def fail(self, message):
        self.valid = False
        self.issues.add(Code.OUTLINE_INVALID, "ring/"+self.ring.ring_id, message)

    def edge(self, i):
        self.w.charge(16)
        edge = self.ring.edges[i]
        if edge.end != self.ring.edges[(i+1) % len(self.points)].start:
            self.fail("Contour endpoints must match exactly.")
        a, b = self.points[i]
        delta = exact.vector(a, b, self.w)
        if exact.dot(delta, delta, self.w) <= self.w.mul(exact.D, exact.D):
            self.fail("Edge length must be strictly greater than the guard.")

    def pair(self, i, j):
        a, b = self.points[i]
        c, d = self.points[j]
        adjacent = j == i-1 or j == 0 and i == len(self.points)-1
        if adjacent:
            if b == c:
                valid = exact.adjacent_valid(a, b, d, self.w)
            elif d == a:
                valid = exact.adjacent_valid(c, d, b, self.w)
            else:
                self.w.charge(320, pairs=1)
                return  # closure already failed; no invented shared vertex
            if not valid:
                self.fail("Adjacent edges overlap or backtrack.")
        elif not exact.separated(a, b, c, d, self.w):
            self.fail("Nonadjacent edges intersect, touch or violate clearance.")

    def finish(self):
        self.signed_area = exact.area(tuple(a for a, _ in self.points), self.w)
        # abs(area), D*D, 2*(D*D), and the threshold comparison.
        self.w.charge(4)
        if abs(self.signed_area) <= self.w.mul(2, self.w.mul(exact.D, exact.D)):
            self.fail("Ring area must be strictly greater than guard squared.")
        return self


def _admit(declaration, admission, issues):
    _require(type(declaration) is CanonicalOutlineDeclaration, Code.SCHEMA_INVALID,
             "outline", "Supply CanonicalOutlineDeclaration.")
    admission.text(declaration.outline_id, "outline_id")
    admission.frame(declaration.frame)
    _require(type(declaration.cutouts) is tuple, Code.SCHEMA_INVALID, "cutouts", "Supply an immutable tuple.")
    _require(len(declaration.cutouts) <= 32, Code.INPUT_LIMIT_EXCEEDED, "cutouts", "At most 32 cutouts.")
    rings = (declaration.exterior,)+declaration.cutouts
    ids = set()
    for ring in rings:
        _require(type(ring) is RingDeclaration, Code.SCHEMA_INVALID, "rings", "Supply RingDeclaration.")
        admission.text(ring.ring_id, "ring_id")
        _require(ring.ring_id not in ids, Code.DUPLICATE_ID, "ring_id", "Ring IDs must be unique.")
        ids.add(ring.ring_id)
    rings = (declaration.exterior,)+tuple(sorted(declaration.cutouts, key=lambda r: r.ring_id))
    count = 0
    for ring in rings:
        _require(type(ring.edges) is tuple, Code.SCHEMA_INVALID, "edges", "Supply immutable edges.")
        count += len(ring.edges)
        _require(count <= 512, Code.INPUT_LIMIT_EXCEEDED, "edges", "Aggregate edge limit is 512.")
    for ring in rings:
        try:
            _admit_ring(ring, declaration.frame, admission)
        except _Invalid as error:
            issues.add(error.code, "ring/"+ring.ring_id+"/"+error.path, error.message)
    return rings


def _admit_ring(ring, frame, admission):
    _require(len(ring.edges) >= 3, Code.OUTLINE_INVALID, "edges", "At least three edges per ring.")
    for edge in ring.edges:
        _require(type(edge) is DeclaredLine, Code.GEOMETRY_UNSUPPORTED, "edges", "Only declared straight lines are supported.")
        _require(type(edge.reversed_from_source) is bool, Code.SCHEMA_INVALID, "edges.reversed_from_source", "Supply bool.")
        admission.references_for(edge.provenance)
        for p in (edge.start, edge.end):
            _require(type(p) is Point2, Code.SCHEMA_INVALID, "point", "Supply Point2.")
            _require(p.frame == frame, Code.CONTEXT_MISMATCH, "frame", "Every endpoint must have the full aggregate frame/revision.")
            for v in (p.x, p.y):
                _require(type(v) is float and isfinite(v), Code.SCHEMA_INVALID, "point", "Require finite binary64 coordinates.")
                _require(abs(v) <= 1e6, Code.INPUT_LIMIT_EXCEEDED, "point", "Coordinate magnitude exceeds 1e6 mm.")


def _normalize(ring, signed_area, exterior):
    edges = ring.edges
    if (signed_area > 0) != exterior:
        edges = tuple(DeclaredLine(e.end, e.start, e.provenance, not e.reversed_from_source) for e in reversed(edges))
    first = min(range(len(edges)), key=lambda i: (edges[i].start.x, edges[i].start.y))
    edges = edges[first:]+edges[:first]
    def point(p):
        return Point2(0.0 if p.x == 0 else p.x, 0.0 if p.y == 0 else p.y, p.frame)
    return RingDeclaration(ring.ring_id, tuple(replace(e, start=point(e.start), end=point(e.end)) for e in edges))


def _validate(declaration, policy, w, issues, admission):
    _require(type(policy) is CanonicalOutlinePolicy and policy == POLICY,
             Code.POLICY_INVALID, "policy", "Select canonical-line-outline-v1 unchanged.")
    rings = _admit(declaration, admission, issues)
    if issues.values:
        return None
    strategies = []
    for ring in rings:
        w.charge(8*len(ring.edges))  # four exact binary64-to-grid conversions per edge
        points = tuple(((exact.grid(e.start.x), exact.grid(e.start.y)),
                        (exact.grid(e.end.x), exact.grid(e.end.y))) for e in ring.edges)
        strategies.append(validate_contour(len(points), _CanonicalContour(ring, points, w, issues)))
    if any(not s.valid for s in strategies):
        return None
    for i, left in enumerate(strategies):
        for right in strategies[:i]:
            for a, b in left.points:
                for c, d in right.points:
                    if not exact.separated(a, b, c, d, w):
                        issues.add(Code.OUTLINE_INVALID, "ring/"+left.ring.ring_id, "Ring boundaries intersect, touch or violate clearance.")
    if issues.values:
        return None
    exterior = tuple(a for a, _ in strategies[0].points)
    for i, hole in enumerate(strategies[1:], 1):
        p = hole.points[0][0]
        if not exact.inside(p, exterior, w):
            issues.add(Code.OUTLINE_INVALID, "ring/"+hole.ring.ring_id, "Cutout is outside the exterior.")
        for j, other in enumerate(strategies[1:], 1):
            if i != j and exact.inside(p, tuple(a for a, _ in other.points), w):
                issues.add(Code.OUTLINE_INVALID, "ring/"+hole.ring.ring_id, "Nested cutouts are unsupported.")
    if issues.values:
        return None
    normalized = tuple(_normalize(s.ring, s.signed_area, i == 0) for i, s in enumerate(strategies))
    return CanonicalOutline(declaration.outline_id, declaration.frame, normalized[0], normalized[1:], policy)


def _result(outline, w, issues):
    report = issues.report()
    if outline is None or issues.values:
        return CanonicalOutlineFailure(report, issues.truncated, w.snapshot())
    return CanonicalOutlineSuccess(outline, report, w.snapshot())


def validate_canonical_outline(declaration, policy):
    """Atomic bounded validation. No source parsing, binding or publication."""
    w, issues = exact.Ledger(), _Issues()
    outline = None
    try:
        outline = _validate(declaration, policy, w, issues, _Admission())
    except _Invalid as error:
        issues.add(error.code, error.path, error.message)
    except exact.Exhausted as error:
        issues.exhausted(str(error))
    return _result(outline, w, issues)


def transform_canonical_outline(outline, mapping, policy):
    """Revalidate both ends; topology is exact on rounded binary64 results.

Uses Transform2's existing unit-isometry/convention contract, not exact trig.
Transform provenance remains declared metadata and never source authentication.
"""
    w, issues = exact.Ledger(2), _Issues()
    result = None
    try:
        _require(type(outline) is CanonicalOutline, Code.SCHEMA_INVALID, "outline", "Supply CanonicalOutline.")
        _require(outline.policy == policy, Code.POLICY_INVALID, "policy", "Preserve the outline policy.")
        # History must be bounded and structurally revalidated, not trusted merely
        # because the outer record is frozen.
        admission = _Admission()
        source = _validate(CanonicalOutlineDeclaration(outline.outline_id, outline.frame, outline.exterior, outline.cutouts), policy, w, issues, admission)
        if source is not None:
            _require(type(outline.transforms) is tuple, Code.SCHEMA_INVALID,
                     "transforms", "Supply immutable transform history.")
            _require(len(outline.transforms) < 1024, Code.INPUT_LIMIT_EXCEEDED,
                     "transforms", "Transform reference limit exceeded.")
            for history in outline.transforms:
                _require(type(history) is OutlineTransform, Code.SCHEMA_INVALID,
                         "transforms", "Supply OutlineTransform history.")
                admission.text(history.transform_id, "transforms.id")
                admission.frame(history.from_frame)
                admission.frame(history.to_frame)
                _require(history.from_frame.board_revision_id == source.frame.board_revision_id
                         and history.to_frame.board_revision_id == source.frame.board_revision_id,
                         Code.CONTEXT_MISMATCH, "transforms", "Preserve history revision.")
                _require(type(history.matrix) is tuple and len(history.matrix) == 3
                         and all(type(row) is tuple and len(row) == 3
                                 and all(type(v) is float and isfinite(v) for v in row) for row in history.matrix),
                         Code.SCHEMA_INVALID, "transforms.matrix", "Supply immutable finite matrix.")
                _require(type(history.provenance) is tuple and len(history.provenance) <= 1024,
                         Code.SCHEMA_INVALID, "transforms.provenance", "Supply bounded immutable provenance.")
                for entry in history.provenance:
                    admission.text(entry, "transforms.provenance", 1024)
            _require(admission.references+len(outline.transforms)+1 <= 1024,
                     Code.INPUT_LIMIT_EXCEEDED, "transforms", "Aggregate reference occurrence limit exceeded.")
            _require(type(mapping) is Transform2, Code.SCHEMA_INVALID, "mapping", "Supply Transform2.")
            # A frozen record is not an admission guarantee. In particular the
            # convention helper formats transform_id in its exception message.
            # Admit ALL metadata before invoking helpers (including apply).
            admission.text(mapping.transform_id, "mapping.transform_id")
            admission.frame(mapping.to_frame)
            admission.frame(mapping.from_frame)
            _require(type(mapping.provenance) is tuple and len(mapping.provenance) <= 1024,
                     Code.INPUT_LIMIT_EXCEEDED, "mapping.provenance", "Bounded immutable provenance required.")
            for entry in mapping.provenance:
                admission.text(entry, "mapping.provenance", 1024)
            _require(type(mapping.kind) is TransformKind and mapping.kind in (TransformKind.RIGID, TransformKind.REFLECTION),
                     Code.GEOMETRY_UNSUPPORTED, "mapping", "Only unit-scale rigid/reflection transforms.")
            _require(type(mapping.conventions_validated) is bool and type(mapping.parity) is Parity,
                     Code.SCHEMA_INVALID, "mapping", "Supply typed convention and parity fields.")
            _require(type(mapping.matrix) is tuple and len(mapping.matrix) == 3
                     and all(type(row) is tuple and len(row) == 3
                             and all(type(v) is float and isfinite(v) for v in row) for row in mapping.matrix),
                     Code.SCHEMA_INVALID, "mapping.matrix", "Supply an immutable finite binary64 matrix.")
            _require(mapping.from_frame == source.frame and mapping.to_frame.board_revision_id == source.frame.board_revision_id,
                     Code.CONTEXT_MISMATCH, "mapping", "Preserve full source frame and board revision.")
            # Fixed conservative envelope for _validate_isometry: column norms,
            # dot, five possible isclose comparisons, reflection involution and
            # parity decisions. Metadata/schema/bookkeeping are not primitives.
            w.charge(64)
            mapping._require_validated_conventions()
            mapping._validate_isometry()
            # Each apply evaluates two coordinates: four multiplies + four adds.
            # Both endpoints are mapped per edge, including repeated vertices.
            # Reserve the whole batch before any mapping or output allocation.
            point_count = 2 * sum(len(r.edges) for r in (source.exterior,)+source.cutouts)
            w.charge(8 * point_count)
            def mapped(ring):
                return RingDeclaration(ring.ring_id, tuple(replace(e, start=mapping.apply(e.start), end=mapping.apply(e.end)) for e in ring.edges))
            declaration = CanonicalOutlineDeclaration(source.outline_id, mapping.to_frame, mapped(source.exterior), tuple(mapped(r) for r in source.cutouts))
            result = _validate(declaration, policy, w, issues, _Admission())
            if result is not None:
                result = replace(result, transforms=outline.transforms+(OutlineTransform(mapping.transform_id, mapping.from_frame, mapping.to_frame, mapping.matrix, mapping.provenance),))
    except _Invalid as error:
        issues.add(error.code, error.path, error.message)
    except GeometryError:
        issues.add(Code.GEOMETRY_UNSUPPORTED, "mapping", "Transform does not satisfy validated conventions/isometry.")
    except exact.Exhausted as error:
        issues.exhausted(str(error))
    return _result(result, w, issues)
