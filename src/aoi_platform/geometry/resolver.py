"""Contextual resolution of registered, directed affine transform paths."""

from dataclasses import dataclass, field
from collections import deque
from math import hypot

from .errors import ErrorCode, GeometryError, finite_number, require_text
from .models import Frame, Point2, Unit
from .transforms import Transform2


@dataclass(frozen=True, slots=True)
class PathConsistencyPolicy:
    policy_id: str = "synthetic-path-consistency-v1"
    version: str = "1"
    tolerance_mm: float = 1e-6

    def __post_init__(self) -> None:
        require_text(self.policy_id, "policy.policy_id")
        require_text(self.version, "policy.version")
        tolerance = finite_number(self.tolerance_mm, "policy.tolerance_mm")
        if tolerance < 0:
            raise GeometryError(ErrorCode.POLICY_INVALID, "Tolerance must be nonnegative.", field_path="policy.tolerance_mm")
        object.__setattr__(self, "tolerance_mm", tolerance)


@dataclass(frozen=True, slots=True)
class RectangleDomain:
    frame: Frame
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def __post_init__(self) -> None:
        if not isinstance(self.frame, Frame):
            raise GeometryError(ErrorCode.DOMAIN_INVALID, "Supply the source Frame.", field_path="domain.frame")
        if self.frame.unit is Unit.PIXEL:
            raise GeometryError(ErrorCode.DOMAIN_INVALID, "Pixel domains are outside affine path resolution.", field_path="domain.frame.unit")
        values = tuple(finite_number(getattr(self, name), f"domain.{name}") for name in ("x_min", "y_min", "x_max", "y_max"))
        object.__setattr__(self, "x_min", values[0]); object.__setattr__(self, "y_min", values[1])
        object.__setattr__(self, "x_max", values[2]); object.__setattr__(self, "y_max", values[3])
        if not self.x_min < self.x_max or not self.y_min < self.y_max:
            raise GeometryError(ErrorCode.DOMAIN_INVALID, "Rectangle bounds must have positive extent.", field_path="domain")

    @property
    def corners(self) -> tuple[Point2, Point2, Point2, Point2]:
        return tuple(Point2(x, y, self.frame) for x, y in (
            (self.x_min, self.y_min), (self.x_min, self.y_max),
            (self.x_max, self.y_min), (self.x_max, self.y_max)))  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class ResolvedPath:
    transform: Transform2
    path_ids: tuple[tuple[str, ...], ...]
    policy: PathConsistencyPolicy
    domain: RectangleDomain
    max_deviation_mm: float
    representative_path: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        if not self.path_ids:
            raise GeometryError(ErrorCode.SCHEMA_INVALID, "Resolved path list cannot be empty.", field_path="result.path_ids")
        normalized = tuple(sorted(tuple(path) for path in self.path_ids))
        object.__setattr__(self, "path_ids", normalized)
        object.__setattr__(self, "representative_path", normalized[0])


class TransformGraph:
    """Registry following explicitly registered edges, with bounded resolution.

    max_edges bounds graph size, cycle processing, traversal edge visits and
    total candidate edge occurrences (separate phase budgets). max_comparisons
    bounds path pairs, each requiring four cached-corner distance calculations.
    Constructor validation is linear in supplied records; resolution checks size
    before metadata indexing, sorting or any graph search.
    """

    def __init__(self, edges: tuple[Transform2, ...] = (), *, max_paths: int = 10_000,
                 max_edges: int = 100_000, max_comparisons: int = 100_000) -> None:
        if not isinstance(edges, tuple) or any(not isinstance(edge, Transform2) for edge in edges):
            raise GeometryError(ErrorCode.SCHEMA_INVALID, "Edges must be an immutable Transform2 tuple.", field_path="graph.edges")
        if any(type(limit) is not int or limit < 1 for limit in (max_paths, max_edges, max_comparisons)):
            raise GeometryError(ErrorCode.SCHEMA_INVALID, "Resource limits must be positive integers.", field_path="graph.limits")
        ids: set[str] = set()
        for edge in edges:
            if edge.transform_id in ids:
                raise GeometryError(ErrorCode.SCHEMA_INVALID, "Transform ID must be unique in a graph.", field_path="graph.edge.transform_id")
            ids.add(edge.transform_id)
        self._edges = edges
        self.max_paths = max_paths
        self.max_edges = max_edges
        self.max_comparisons = max_comparisons

    @property
    def edges(self) -> tuple[Transform2, ...]:
        return self._edges

    def register(self, transform: Transform2) -> "TransformGraph":
        if not isinstance(transform, Transform2):
            raise GeometryError(ErrorCode.SCHEMA_INVALID, "Register a Transform2 edge.", field_path="graph.edge")
        return TransformGraph(self._edges + (transform,), max_paths=self.max_paths,
                              max_edges=self.max_edges, max_comparisons=self.max_comparisons)

    def resolve(self, source: Frame, target: Frame, domain: RectangleDomain, *,
                policy: PathConsistencyPolicy | None = None) -> ResolvedPath:
        if not isinstance(source, Frame) or not isinstance(target, Frame):
            raise GeometryError(ErrorCode.SCHEMA_INVALID, "Supply source and target Frames.", field_path="resolve.frames")
        if source.unit is Unit.PIXEL or target.unit is Unit.PIXEL:
            raise GeometryError(ErrorCode.DOMAIN_INVALID, "Pixel mappings are outside affine path resolution.", field_path="resolve.frames")
        if not isinstance(domain, RectangleDomain):
            raise GeometryError(ErrorCode.DOMAIN_INVALID, "Supply a finite RectangleDomain.", field_path="resolve.domain")
        if domain.frame != source:
            raise GeometryError(ErrorCode.CONTEXT_MISMATCH, "Domain must be expressed in the requested source frame.", field_path="resolve.domain.frame")
        selected = policy if policy is not None else PathConsistencyPolicy()
        if not isinstance(selected, PathConsistencyPolicy):
            raise GeometryError(ErrorCode.POLICY_INVALID, "Supply PathConsistencyPolicy.", field_path="resolve.policy")
        self._check_budget(len(self._edges), self.max_edges, "graph.edges")
        self._check_graph_contexts()
        adjacency: dict[str, list[Transform2]] = {}
        for edge in self._edges:
            adjacency.setdefault(edge.from_frame.frame_id, []).append(edge)
        for values in adjacency.values():
            values.sort(key=lambda edge: edge.transform_id)
        self._reject_cycles(adjacency)
        paths: list[tuple[Transform2, ...]] = []
        examined = 0
        candidate_edges = 0
        current: list[Transform2] = []
        # Iterator stack avoids Python recursion and copying every path prefix.
        stack = [iter(adjacency.get(source.frame_id, ()))] if source.frame_id != target.frame_id else []
        while stack:
            edge = next(stack[-1], None)
            if edge is None:
                stack.pop()
                if current:
                    current.pop()
                continue
            examined += 1
            self._check_budget(examined, self.max_edges, "resolve.traversal")
            current.append(edge)
            if edge.to_frame.frame_id == target.frame_id:
                self._check_budget(len(paths) + 1, self.max_paths, "resolve.paths")
                candidate_edges += len(current)
                self._check_budget(candidate_edges, self.max_edges, "resolve.candidate_edges")
                candidate = tuple(current)
                self._validate_path_context(candidate, source, target)
                paths.append(candidate)
                current.pop()
            else:
                stack.append(iter(adjacency.get(edge.to_frame.frame_id, ())))
        if not paths:
            raise GeometryError(ErrorCode.TRANSFORM_MISSING, "No registered directed path connects the requested frames.", field_path="resolve.paths")
        pair_count = len(paths) * (len(paths) - 1) // 2
        self._check_budget(pair_count, self.max_comparisons, "resolve.comparisons")
        composed = [self._compose_path(path) for path in paths]
        corners = domain.corners
        # Validate all candidates, including a sole path, and reuse each result.
        outputs = [tuple(mapping.apply(corner) for corner in corners) for mapping in composed]
        scale = 25.4 if target.unit is Unit.INCH else 1.0
        maximum = 0.0
        for left_index, left in enumerate(outputs):
            for right_index in range(left_index + 1, len(outputs)):
                for a, b in zip(left, outputs[right_index], strict=True):
                    maximum = max(maximum, hypot((a.x - b.x) * scale, (a.y - b.y) * scale))
        if maximum > selected.tolerance_mm:
            raise GeometryError(ErrorCode.TRANSFORM_AMBIGUOUS, f"Registered paths disagree by {maximum:g} mm.", field_path="resolve.paths")
        ordered = sorted(zip(paths, composed), key=lambda pair: tuple(edge.transform_id for edge in pair[0]))
        representative = ordered[0][1]
        return ResolvedPath(representative, tuple(tuple(edge.transform_id for edge in path) for path in paths), selected, domain, maximum)

    @staticmethod
    def _validate_path_context(path: tuple[Transform2, ...], source: Frame, target: Frame) -> None:
        if path and path[0].from_frame != source:
            raise GeometryError(ErrorCode.CONTEXT_MISMATCH, "Path start metadata does not match source.", field_path="resolve.source")
        frames = (source,) + tuple(edge.to_frame for edge in path)
        for field in ("board_revision_id", "machine_id", "capture_id"):
            values = {getattr(frame, field) for frame in frames if getattr(frame, field) is not None}
            if len(values) > 1:
                raise GeometryError(ErrorCode.CONTEXT_MISMATCH, f"Path contains conflicting {field} metadata.", field_path=f"resolve.context.{field}")
        if path and path[-1].to_frame != target:
            raise GeometryError(ErrorCode.CONTEXT_MISMATCH, "Path endpoint metadata does not match target.", field_path="resolve.target")

    def _compose_path(self, path: tuple[Transform2, ...]) -> Transform2:
        for edge in path:
            edge._require_validated_conventions()
        result = path[0]
        path_id = "path:" + "/".join(e.transform_id for e in path)
        for edge in path[1:]:
            result = edge.compose(result, transform_id=path_id)
        return result

    def _check_graph_contexts(self) -> None:
        by_id: dict[str, Frame] = {}
        for edge in self._edges:
            for frame in (edge.from_frame, edge.to_frame):
                prior = by_id.get(frame.frame_id)
                if prior is not None and prior != frame:
                    raise GeometryError(ErrorCode.CONTEXT_MISMATCH, "Frame ID has conflicting metadata in graph.", field_path="graph.frames")
                by_id[frame.frame_id] = frame

    @staticmethod
    def _check_budget(work: int, limit: int, phase: str) -> None:
        if work > limit:
            raise GeometryError(ErrorCode.TRANSFORM_RESOURCE_EXHAUSTED,
                                f"Required work {work} exceeds budget {limit}.", field_path=phase)

    def _reject_cycles(self, adjacency: dict[str, list[Transform2]]) -> None:
        # Kahn's algorithm includes disconnected components and parallel edges.
        indegree: dict[str, int] = {}
        indexed = 0
        for node, edges in adjacency.items():
            indegree.setdefault(node, 0)
            for edge in edges:
                indexed += 1
                self._check_budget(indexed, self.max_edges, "graph.cycle_index")
                target = edge.to_frame.frame_id
                indegree[target] = indegree.get(target, 0) + 1
        ready = deque(node for node, degree in indegree.items() if degree == 0)
        processed = 0
        visited = 0
        while ready:
            node = ready.popleft()
            visited += 1
            for edge in adjacency.get(node, ()):
                processed += 1
                self._check_budget(processed, self.max_edges, "graph.cycle_detection")
                target = edge.to_frame.frame_id
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target)
        if visited != len(indegree):
            raise GeometryError(ErrorCode.TRANSFORM_CYCLE_UNSUPPORTED,
                                "Transform graph must be acyclic.", field_path="graph.edges")
