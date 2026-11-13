"""Declaration-consistent boundary/candidate orchestration; never source verification."""
from dataclasses import dataclass
from . import pad_candidates as candidate
from .boundary_evidence import (Assurance, BoundaryEvidence, BoundaryContour,
    PreflightFailure, bind_boundary_declarations, CATEGORIES)
from .boundary_correspondence import Correspondence, CorrespondenceFailure, match_contours_in_p
from .geometry.errors import GeometryError, ErrorCode, diagnostic_json
from .geometry.models import Unit, AxisDirection, frame_evidence
from .geometry.transforms import TransformKind
from .geometry.reports import ValidationReport


@dataclass(frozen=True, slots=True)
class BoundaryMatch:
    evidence: BoundaryEvidence
    correspondence: Correspondence
    @property
    def coverage(self):
        return tuple(next(c for c in self.evidence.coverage if c.category == name) for name in CATEGORIES)
    @property
    def unknown_categories(self):
        return tuple(c.category for c in self.coverage if c.status == 'unknown')


@dataclass(frozen=True, slots=True)
class BoundaryBindingSuccess(Assurance):
    candidates: tuple[candidate.CanonicalPadCandidate, ...]
    bindings: tuple[BoundaryMatch, ...]
    report: ValidationReport
    policy_id: str
    policy_version: str
    @property
    def status(self): return 'declaration-consistent-geometry-binding'


def bind_pad_boundaries(request, evidence, policy):
    """Joint preflight/binding, one candidate batch, then bounded correspondence.

    Fail at the first unsuccessful phase: no candidate diagnostics are merged
    into another fresh budget, and no partial candidates escape. Rectangle
    admission is performed by the candidate API, not convex-contour detection.
    """
    declared = bind_boundary_declarations(request, evidence, policy)
    if isinstance(declared, PreflightFailure):
        return declared
    built = candidate.build_rectangular_pad_candidates(request)
    if isinstance(built, candidate.PadBatchFailure):
        return PreflightFailure(built.report, built.truncation)
    # Successful prior phases produce no issues; one reserved sink for this phase.
    sink = candidate._Issues(request.policy)
    matches = []
    comparisons = 0
    for pad, item in zip(built.candidates, declared.bindings):
        sink.entity, sink.artifact = pad.pad_id, item.source.artifact_id
        sink.context = (
            ('policy_id', policy.policy_id), ('policy_version', policy.version),
            ('canonical_parent_id_json', diagnostic_json(item.canonical_parent_id)),
            ('source_parent_id_json', diagnostic_json(item.source_parent_id)),
            ('source_pad_id_json', diagnostic_json(item.source_pad_id)),
            ('evidence_id_json', diagnostic_json(item.evidence_id)),
            ('source_sha256', item.source.computed_sha256),
            ('observation_artifact_json', diagnostic_json(item.observation.artifact_id)),
            ('observation_sha256', item.observation.computed_sha256),
            ('boundary_artifact_json', diagnostic_json(item.boundary.artifact_id)),
            ('boundary_sha256', item.boundary.computed_sha256),
            ('transform_id', item.boundary_to_p.transform_id),
        ) + frame_evidence('boundary', item.boundary_frame) + frame_evidence('target', request.target_frame)
        try:
            transform = item.boundary_to_p
            candidate._require(transform.kind is TransformKind.RIGID, 'boundary.transform.kind',
                'Proper rigid transform required.', ErrorCode.GEOMETRY_UNSUPPORTED)
            candidate._require((item.boundary_frame.unit, item.boundary_frame.x_direction,
                item.boundary_frame.y_direction) == (Unit.MM, AxisDirection.RIGHT, AxisDirection.UP),
                'boundary.frame', code=ErrorCode.GEOMETRY_UNSUPPORTED)
            transform._require_validated_conventions()
            transform._validate_isometry()
            for row in transform.matrix[:2]:
                candidate._coordinate(row[2], request.policy, 'boundary.transform.translation')
            vertices = []
            for point in item.contours[0].vertices:
                candidate._coordinate(point.x, request.policy, 'boundary.x')
                candidate._coordinate(point.y, request.policy, 'boundary.y')
                mapped = transform.apply(point)
                candidate._coordinate(mapped.x, request.policy, 'boundary.P.x')
                candidate._coordinate(mapped.y, request.policy, 'boundary.P.y')
                vertices.append(mapped)
            comparisons += policy.component_comparisons_per_pad
            candidate._require(comparisons <= policy.component_comparisons_total,
                'correspondence.budget', code=ErrorCode.INPUT_LIMIT_EXCEEDED)
            result = match_contours_in_p(BoundaryContour(pad.vertices, True, 0),
                BoundaryContour(tuple(vertices), True, 0), policy)
            if isinstance(result, CorrespondenceFailure):
                issue = result.error
                raise GeometryError(issue.code, result.reason, field_path=issue.field_path,
                    expected=issue.expected, actual=issue.actual, context=issue.context)
            matches.append(BoundaryMatch(item, result))
        except GeometryError as error:
            try:
                sink.add(error)
            except candidate._Stop:
                pass
            return PreflightFailure(ValidationReport('boundary-binding', policy.policy_id,
                tuple(sink.issues), ()), sink.truncation)
    return BoundaryBindingSuccess(built.candidates, tuple(matches),
        ValidationReport('boundary-binding', policy.policy_id, (), (),
            context=(('assurance', 'declaration-consistent-only'),)), policy.policy_id, policy.version)
