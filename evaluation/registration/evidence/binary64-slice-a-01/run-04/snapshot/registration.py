"""Bounded synthetic registration drafts; never an active coordinate mapping.

Only ``fit_rigid_registration`` admits caller data. Frozen constructors are not
validation certificates. Evidence is declared/unverified, including SHA-256s.
No artifact IO, clock, calibration, resolver or motion dependency exists here.
Threshold equality is intentionally indeterminate under binary64 guard margins.
"""

from dataclasses import dataclass, fields, replace
from enum import StrEnum
import json
from math import hypot, isfinite

from . import _registration_numeric as num
from .errors import ErrorCode
from .models import AxisDirection, Frame, FrameKind, Point2, Unit

ALGORITHM = "proper-rigid-binary64-v1"
COORDINATE_CAP = float(2**20)
TEXT_CAP = 65536
REFERENCE_CAP = 512
OUTPUT_CAP = 262144


class Side(StrEnum):
    TOP = "TOP"
    BOTTOM = "BOTTOM"


class Purpose(StrEnum):
    SYNTHETIC = "SYNTHETIC"


class EvidenceState(StrEnum):
    DECLARED_UNVERIFIED = "DECLARED_UNVERIFIED"


class EvidenceKind(StrEnum):
    HELD_OUT_CHECKPOINTS = "HELD_OUT_CHECKPOINTS"
    CALIBRATION_REFERENCE = "CALIBRATION_REFERENCE"
    SIDE_PARITY = "SIDE_PARITY"
    CORRESPONDENCE_APPROVAL = "CORRESPONDENCE_APPROVAL"
    REFERENCE_MAPPING = "REFERENCE_MAPPING"


class Assessment(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    INDETERMINATE = "INDETERMINATE"
    INSUFFICIENT = "INSUFFICIENT"
    NOT_PERFORMED = "NOT_PERFORMED"


@dataclass(frozen=True, slots=True)
class RevisionKey:
    board_id: str
    revision_id: str
    content_sha256: str


@dataclass(frozen=True, slots=True)
class RegistrationContext:
    revision: RevisionKey
    side: Side
    load_id: str
    station_id: str
    machine_id: str
    fixture_id: str
    fixture_configuration_id: str


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    reference_id: str
    artifact_sha256: str
    locator: str
    issuer_id: str
    state: EvidenceState


@dataclass(frozen=True, slots=True)
class CalibrationReference:
    calibration_id: str
    calibration_version: str
    artifact: ArtifactReference
    station_id: str
    machine_id: str
    measurement_frame_id: str
    configuration_id: str
    purpose: Purpose


@dataclass(frozen=True, slots=True)
class FiducialDeclaration:
    fiducial_id: str
    revision: RevisionKey
    side: Side
    position: Point2
    shape_id: str
    size_mm: tuple[float, float]
    approval_reference_id: str
    provenance_reference_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MetricObservation:
    observation_id: str
    fiducial_id: str
    context: RegistrationContext
    position: Point2
    measurement_set_id: str
    calibration_reference_id: str
    confidence: float
    uncertainty_reference_id: str | None
    provenance_reference_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IndependentValidationEvidence:
    evidence_id: str
    kind: EvidenceKind
    issuer_id: str
    context: RegistrationContext
    source_frame_id: str
    target_frame_id: str
    calibration_reference_ids: tuple[str, ...]
    fit_measurement_set_ids: tuple[str, ...]
    validation_measurement_set_ids: tuple[str, ...]
    checkpoint_ids: tuple[str, ...]
    artifact_reference_ids: tuple[str, ...]
    independence_claim: str
    state: EvidenceState


@dataclass(frozen=True, slots=True)
class RegistrationRequest:
    request_id: str
    context: RegistrationContext
    source_frame: Frame
    target_frame: Frame
    fit_declarations: tuple[FiducialDeclaration, ...]
    fit_observations: tuple[MetricObservation, ...]
    checkpoint_declarations: tuple[FiducialDeclaration, ...]
    checkpoint_observations: tuple[MetricObservation, ...]
    calibration_references: tuple[CalibrationReference, ...]
    artifact_references: tuple[ArtifactReference, ...]
    independent_evidence: tuple[IndependentValidationEvidence, ...]


@dataclass(frozen=True, slots=True)
class RegistrationPolicy:
    policy_id: str
    version: str
    algorithm: str
    purpose: Purpose
    min_baseline_mm: float
    max_pair_distance_error_mm: float
    max_fit_rms_mm: float
    max_fit_error_mm: float
    max_checkpoint_rms_mm: float
    max_checkpoint_error_mm: float
    min_checkpoint_count: int
    require_off_baseline_checkpoint: bool
    min_checkpoint_baseline_distance_mm: float
    required_evidence_kinds: tuple[EvidenceKind, ...]


@dataclass(frozen=True, slots=True)
class Residual:
    fiducial_id: str
    observation_id: str
    dx_mm: float
    dy_mm: float
    norm_mm: float
    guard_mm: float


@dataclass(frozen=True, slots=True)
class ResidualSummary:
    records: tuple[Residual, ...]
    rms_mm: float
    maximum_mm: float
    maximum_fiducial_id: str
    rms_guard_mm: float
    maximum_guard_mm: float


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    evidence_id: str
    structural_checks: Assessment
    independence: Assessment
    state: EvidenceState


@dataclass(frozen=True, slots=True)
class ResourceUsage:
    input_text_bytes: int
    reference_occurrences: int
    output_bytes: int


@dataclass(frozen=True, slots=True)
class RegistrationDraft:
    draft_id: str
    algorithm: str
    request: RegistrationRequest
    policy: RegistrationPolicy
    coefficients: tuple[float, float, float, float]
    correlation: float
    correlation_guard: float
    fit: ResidualSummary
    checkpoints: ResidualSummary | None
    checkpoint_assessment: Assessment
    evidence_assessments: tuple[EvidenceAssessment, ...]
    missing_evidence_kinds: tuple[EvidenceKind, ...]
    resources: ResourceUsage
    state: str = "DRAFT"
    validation_state: str = "NOT_PERFORMED"
    purpose: Purpose = Purpose.SYNTHETIC


@dataclass(frozen=True, slots=True)
class RegistrationDiagnostic:
    code: ErrorCode
    field_path: str
    reason: str


@dataclass(frozen=True, slots=True)
class RegistrationFailure:
    diagnostic: RegistrationDiagnostic
    resources: ResourceUsage
    algorithm: str = ALGORITHM
    truncated: bool = False


class _Reject(Exception):
    def __init__(self, code, path, reason):
        self.diagnostic = RegistrationDiagnostic(code, path, reason)


def _require(condition, path, reason, code=ErrorCode.SCHEMA_INVALID):
    if not condition:
        raise _Reject(code, path, reason)


# Fixed acyclic schemas: unknown classes/subclasses cannot execute iteration,
# string conversion, equality, dataclass hooks or arbitrary serialization.
_SCHEMAS = {
    RevisionKey: (str, str, str),
    RegistrationContext: (RevisionKey, Side, str, str, str, str, str),
    ArtifactReference: (str, str, str, str, EvidenceState),
    CalibrationReference: (str, str, ArtifactReference, str, str, str, str, Purpose),
    Frame: (str, FrameKind, Unit, str, AxisDirection, AxisDirection, (str, None), (str, None), (str, None)),
    Point2: (float, float, Frame),
    FiducialDeclaration: (str, RevisionKey, Side, Point2, str, (float, 2), str, (str, 8)),
    MetricObservation: (str, str, RegistrationContext, Point2, str, str, float, (str, None), (str, 8)),
    IndependentValidationEvidence: (str, EvidenceKind, str, RegistrationContext, str, str,
        (str, 8), (str, 8), (str, 8), (str, 8), (str, 8), str, EvidenceState),
    RegistrationRequest: (str, RegistrationContext, Frame, Frame, (FiducialDeclaration, 64),
        (MetricObservation, 64), (FiducialDeclaration, 32), (MetricObservation, 32),
        (CalibrationReference, 16), (ArtifactReference, 128), (IndependentValidationEvidence, 16)),
    RegistrationPolicy: (str, str, str, Purpose, float, float, float, float, float, float,
        int, bool, float, (EvidenceKind, 5)),
}
_REFERENCE_FIELDS = frozenset(("approval_reference_id", "provenance_reference_ids",
    "calibration_reference_id", "uncertainty_reference_id", "calibration_reference_ids",
    "fit_measurement_set_ids", "validation_measurement_set_ids", "checkpoint_ids", "artifact_reference_ids"))


class _Admission:
    def __init__(self):
        self.text_bytes = 0
        self.refs = 0

    def read(self, value, schema, path, name=""):
        if type(schema) is tuple:
            item, cap = schema
            if cap is None:
                if value is not None:
                    self.read(value, item, path, name)
                return
            _require(type(value) is tuple, path, "IMMUTABLE_TUPLE_REQUIRED")
            _require(len(value) <= cap, path, "COLLECTION_LIMIT", ErrorCode.INPUT_LIMIT_EXCEEDED)
            for index, entry in enumerate(value):
                self.read(entry, item, f"{path}[{index}]", name)
            return
        _require(type(value) is schema, path, "EXACT_TYPE_REQUIRED")
        if schema is str:
            cap = 512 if name in ("locator", "independence_claim") else 128
            _require(len(value) <= cap, path, "TEXT_LIMIT", ErrorCode.INPUT_LIMIT_EXCEEDED)
            _require(bool(value), path, "EMPTY_TEXT")
            try:
                size = len(value.encode("utf-8"))
            except UnicodeEncodeError:
                raise _Reject(ErrorCode.SCHEMA_INVALID, path, "INVALID_UTF8") from None
            _require(size <= cap and self.text_bytes + size <= TEXT_CAP, path,
                     "TEXT_LIMIT", ErrorCode.INPUT_LIMIT_EXCEEDED)
            self.text_bytes += size
            if name in _REFERENCE_FIELDS:
                self.refs += 1
                _require(self.refs <= REFERENCE_CAP, path, "REFERENCE_LIMIT", ErrorCode.INPUT_LIMIT_EXCEEDED)
            if name.endswith("sha256"):
                _require(len(value) == 64 and all(c in "0123456789abcdef" for c in value), path, "INVALID_SHA256")
        elif schema is float:
            _require(isfinite(value), path, "NONFINITE")
            _require(abs(value) <= COORDINATE_CAP, path, "NUMERIC_LIMIT", ErrorCode.INPUT_LIMIT_EXCEEDED)
        elif schema is int:
            _require(0 <= value <= 32, path, "COUNT_LIMIT", ErrorCode.POLICY_INVALID)
        elif schema in _SCHEMAS:
            for field, spec in zip(fields(schema), _SCHEMAS[schema]):
                try:
                    member = getattr(value, field.name)
                except AttributeError:
                    raise _Reject(ErrorCode.SCHEMA_INVALID, path + "." + field.name, "MISSING_FIELD") from None
                self.read(member, spec, f"{path}.{field.name}", field.name)
            if schema is CalibrationReference:
                self.refs += 1  # embedded artifact reference occurrence
                _require(self.refs <= REFERENCE_CAP, path, "REFERENCE_LIMIT", ErrorCode.INPUT_LIMIT_EXCEEDED)


def _policy(policy):
    bad = ErrorCode.POLICY_INVALID
    _require(policy.algorithm == ALGORITHM, "policy.algorithm", "UNSUPPORTED_ALGORITHM", bad)
    for name in ("min_baseline_mm", "max_pair_distance_error_mm", "max_fit_rms_mm", "max_fit_error_mm",
                 "max_checkpoint_rms_mm", "max_checkpoint_error_mm", "min_checkpoint_baseline_distance_mm"):
        _require(getattr(policy, name) >= 0, "policy." + name, "NEGATIVE_LIMIT", bad)
    _require(policy.min_baseline_mm > 0, "policy.min_baseline_mm", "POSITIVE_BASELINE_REQUIRED", bad)
    _require(policy.max_fit_rms_mm <= policy.max_fit_error_mm and
             policy.max_checkpoint_rms_mm <= policy.max_checkpoint_error_mm, "policy", "INCONSISTENT_LIMITS", bad)
    _require(not policy.require_off_baseline_checkpoint or
             (policy.min_checkpoint_count >= 1 and policy.min_checkpoint_baseline_distance_mm > 0),
             "policy", "INCONSISTENT_CHECKPOINT_POLICY", bad)
    _require(len(set(policy.required_evidence_kinds)) == len(policy.required_evidence_kinds),
             "policy.required_evidence_kinds", "DUPLICATE_KIND", bad)


def _canonical(value):
    if type(value) is tuple:
        items = tuple(_canonical(v) for v in value)
        if not items:
            return items
        keys = {FiducialDeclaration: "fiducial_id", MetricObservation: "fiducial_id",
                ArtifactReference: "reference_id", CalibrationReference: "calibration_id",
                IndependentValidationEvidence: "evidence_id"}
        if type(items[0]) in keys:
            if type(items[0]) is MetricObservation:
                return tuple(sorted(items, key=lambda v: (v.fiducial_id, v.observation_id)))
            return tuple(sorted(items, key=lambda v: getattr(v, keys[type(v)])))
        if type(items[0]) is str or isinstance(items[0], StrEnum):
            return tuple(sorted(items))
        return items  # numeric pair order is meaningful
    if type(value) in _SCHEMAS:
        members = {f.name: _canonical(getattr(value, f.name)) for f in fields(value)}
        if type(value) in (Frame, Point2):
            # Detach an admitted snapshot without invoking legacy constructors
            # before this API's ordered context validation. No public constructor
            # behavior changes; _context checks all accepted frame conventions.
            snapshot = object.__new__(type(value))
            for name, member in members.items():
                object.__setattr__(snapshot, name, member)
            return snapshot
        return replace(value, **members)
    return value


def _context(req):
    code = ErrorCode.CONTEXT_MISMATCH
    for frame, kind in ((req.source_frame, FrameKind.PCB), (req.target_frame, FrameKind.MACHINE)):
        _require(frame.kind is kind and frame.unit is Unit.MM and frame.x_direction is AxisDirection.RIGHT
                 and frame.y_direction is AxisDirection.UP, "request.frames", "CANONICAL_METRIC_FRAME_REQUIRED", code)
        _require(frame.capture_id is None, "request.frames", "CAPTURE_FRAME_UNSUPPORTED", code)
        _require(frame.board_revision_id in (None, req.context.revision.revision_id)
                 and frame.machine_id in (None, req.context.machine_id), "request.frames", "FRAME_CONTEXT", code)
    _require(req.source_frame.board_revision_id == req.context.revision.revision_id
             and req.target_frame.machine_id == req.context.machine_id
             and req.source_frame.frame_id != req.target_frame.frame_id, "request.frames", "FRAME_CONTEXT", code)
    for decl in req.fit_declarations + req.checkpoint_declarations:
        _require(decl.revision == req.context.revision and decl.side is req.context.side
                 and decl.position.frame == req.source_frame, "fiducial:" + decl.fiducial_id, "DECLARATION_CONTEXT", code)
        _require(len(decl.size_mm) == 2 and all(v > 0 for v in decl.size_mm),
                 "fiducial:" + decl.fiducial_id, "INVALID_SIZE")
    for obs in req.fit_observations + req.checkpoint_observations:
        _require(obs.context == req.context and obs.position.frame == req.target_frame,
                 "observation:" + obs.observation_id, "OBSERVATION_CONTEXT", code)
        _require(0 <= obs.confidence <= 1, "observation:" + obs.observation_id, "INVALID_CONFIDENCE")
    for cal in req.calibration_references:
        _require((cal.station_id, cal.machine_id, cal.measurement_frame_id) ==
                 (req.context.station_id, req.context.machine_id, req.target_frame.frame_id),
                 "calibration:" + cal.calibration_id, "CALIBRATION_CONTEXT", code)
    for ev in req.independent_evidence:
        _require(ev.context == req.context and ev.source_frame_id == req.source_frame.frame_id
                 and ev.target_frame_id == req.target_frame.frame_id, "evidence:" + ev.evidence_id,
                 "EVIDENCE_CONTEXT", code)


def _unique(items, attr, path):
    ids = sorted(getattr(v, attr) for v in items)
    for left, right in zip(ids, ids[1:]):
        _require(left != right, path + ":" + left, "DUPLICATE_ID", ErrorCode.DUPLICATE_ID)


def _references(req):
    decls = req.fit_declarations + req.checkpoint_declarations
    observations = req.fit_observations + req.checkpoint_observations
    for items, attr, path in ((decls, "fiducial_id", "fiducials"), (observations, "observation_id", "observations"),
            (observations, "fiducial_id", "observation_fiducials"), (req.artifact_references, "reference_id", "artifacts"),
            (req.calibration_references, "calibration_id", "calibrations"), (req.independent_evidence, "evidence_id", "evidence")):
        _unique(items, attr, path)
    _require(len(req.fit_declarations) >= 2 and len(req.fit_observations) >= 2,
             "request.fit", "TOO_FEW_POINTS", ErrorCode.FIDUCIAL_INSUFFICIENT)
    for declarations, observed in ((req.fit_declarations, req.fit_observations),
                                  (req.checkpoint_declarations, req.checkpoint_observations)):
        _require(tuple(d.fiducial_id for d in declarations) == tuple(o.fiducial_id for o in observed),
                 "request.correspondences", "MISSING_COUNTERPART")
    artifacts = {a.reference_id: a for a in req.artifact_references}
    calibrations = {a.calibration_id: a for a in req.calibration_references}
    for cal in req.calibration_references:
        _require(artifacts.get(cal.artifact.reference_id) == cal.artifact,
                 "calibration:" + cal.calibration_id, "MISSING_OR_CONFLICTING_ARTIFACT")
    for decl in decls:
        for ref in (decl.approval_reference_id,) + decl.provenance_reference_ids:
            _require(ref in artifacts, "fiducial:" + decl.fiducial_id, "MISSING_ARTIFACT")
    for obs in observations:
        _require(obs.calibration_reference_id in calibrations, "observation:" + obs.observation_id, "MISSING_CALIBRATION")
        refs = obs.provenance_reference_ids + (() if obs.uncertainty_reference_id is None else (obs.uncertainty_reference_id,))
        for ref in refs:
            _require(ref in artifacts, "observation:" + obs.observation_id, "MISSING_ARTIFACT")
    fit_sets = {o.measurement_set_id for o in req.fit_observations}
    check_sets = {o.measurement_set_id for o in req.checkpoint_observations}
    check_ids = {o.fiducial_id for o in req.checkpoint_observations}
    assessments = []
    for ev in req.independent_evidence:
        for references, registry in ((ev.artifact_reference_ids, artifacts), (ev.calibration_reference_ids, calibrations),
                (ev.fit_measurement_set_ids, fit_sets), (ev.validation_measurement_set_ids, check_sets), (ev.checkpoint_ids, check_ids)):
            _require(all(ref in registry for ref in references), "evidence:" + ev.evidence_id, "MISSING_REFERENCE")
        independent = bool(ev.fit_measurement_set_ids and ev.validation_measurement_set_ids and ev.checkpoint_ids)
        independent = independent and not (fit_sets & check_sets)
        assessments.append(EvidenceAssessment(ev.evidence_id, Assessment.PASS,
            Assessment.PASS if independent else Assessment.INSUFFICIENT, EvidenceState.DECLARED_UNVERIFIED))
    return tuple(assessments)


def _points(records):
    return tuple((r.position.x, r.position.y) for r in records)


def _gate(value, threshold, margin, path, *, lower=False, code=ErrorCode.REGISTRATION_QUALITY_FAILED):
    outcome = num.compare(value, threshold, margin, lower=lower)
    _require(outcome == "PASS", path, "NUMERICAL_AMBIGUITY" if outcome == "INDETERMINATE" else "QUALITY_LIMIT", code)


def _summary(declarations, observations, coefficients, scale):
    values, rms, maximum = num.residuals(_points(declarations), _points(observations), coefficients)
    records = tuple(Residual(d.fiducial_id, o.observation_id, *v, num.guard(v[2], scale))
                    for d, o, v in zip(declarations, observations, values))
    max_id = next(r.fiducial_id for r in records if r.norm_mm == maximum)
    return ResidualSummary(records, rms, maximum, max_id, num.guard(rms, scale), num.guard(maximum, scale))


def _json_chunks(value):
    # Admitted, fixed-schema objects only; no asdict/deepcopy or giant document.
    if type(value) is tuple:
        yield "["
        for index, item in enumerate(value):
            if index:
                yield ","
            yield from _json_chunks(item)
        yield "]"
    elif hasattr(type(value), "__dataclass_fields__"):
        yield "{"
        for index, field in enumerate(fields(value)):
            if index:
                yield ","
            yield json.dumps(field.name) + ":"
            yield from _json_chunks(getattr(value, field.name))
        yield "}"
    else:
        yield json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _output_size(value):
    size = 0
    for chunk in _json_chunks(value):
        increment = len(chunk.encode("utf-8"))
        _require(size + increment <= OUTPUT_CAP, "output", "OUTPUT_LIMIT", ErrorCode.INPUT_LIMIT_EXCEEDED)
        size += increment
    return size


def fit_rigid_registration(request: RegistrationRequest, policy: RegistrationPolicy) -> RegistrationDraft | RegistrationFailure:
    """Return an atomic synthetic draft, or one bounded terminal diagnostic.

    Checkpoint numerical failures are assessments, never fit-point removal.
    Structural/context failures are terminal. No evidence becomes verified.
    Counts/bytes bound work; there is no primitive-operation or integer ledger.
    """
    admission = _Admission()
    try:
        admission.read(request, RegistrationRequest, "request")
        try:
            admission.read(policy, RegistrationPolicy, "policy")
        except _Reject as error:
            if error.diagnostic.code is ErrorCode.SCHEMA_INVALID:
                raise _Reject(ErrorCode.POLICY_INVALID, error.diagnostic.field_path, error.diagnostic.reason) from None
            raise
        _policy(policy)
        req, pol = _canonical(request), _canonical(policy)
        _context(req)
        evidence = _references(req)
        source, target = _points(req.fit_declarations), _points(req.fit_observations)
        scale = max(1.0, *(abs(v) for p in source + target for v in p))
        distance, i, j = num.baseline(source)
        target_distance = hypot(target[j][0] - target[i][0], target[j][1] - target[i][1])
        for name, value in (("source", distance), ("target", target_distance)):
            _gate(value, pol.min_baseline_mm, num.guard(value, scale), "baseline." + name,
                  lower=True, code=ErrorCode.FIDUCIAL_DEGENERATE)
        if len(source) == 2:
            difference = abs(distance - target_distance)
            _gate(difference, pol.max_pair_distance_error_mm, num.guard(distance, scale) + num.guard(target_distance, scale), "pair_distance")
        solved = num.solve(source, target)
        _require(solved.coefficients is not None, "conditioning",
                 "NUMERICAL_AMBIGUITY" if solved.conditioning == "INDETERMINATE" else "DEGENERATE_CORRELATION",
                 ErrorCode.FIDUCIAL_DEGENERATE)
        coefficients = solved.coefficients
        scale = max(scale, abs(coefficients[2]), abs(coefficients[3]))
        summary = _summary(req.fit_declarations, req.fit_observations, coefficients, scale)
        _gate(summary.rms_mm, pol.max_fit_rms_mm, summary.rms_guard_mm, "fit.rms")
        _gate(summary.maximum_mm, pol.max_fit_error_mm, summary.maximum_guard_mm, "fit.maximum")
        checks = None
        check_status = Assessment.NOT_PERFORMED
        if req.checkpoint_declarations:
            check_scale = max(scale, *(abs(v) for p in _points(req.checkpoint_declarations) + _points(req.checkpoint_observations) for v in p))
            checks = _summary(req.checkpoint_declarations, req.checkpoint_observations, coefficients, check_scale)
            outcomes = [num.compare(checks.rms_mm, pol.max_checkpoint_rms_mm, checks.rms_guard_mm),
                        num.compare(checks.maximum_mm, pol.max_checkpoint_error_mm, checks.maximum_guard_mm)]
            if pol.require_off_baseline_checkpoint:
                separation = max(num.off_baseline(p, source[i], source[j]) for p in _points(req.checkpoint_declarations))
                outcomes.append(num.compare(separation, pol.min_checkpoint_baseline_distance_mm,
                                            num.guard(separation, check_scale), lower=True))
            check_status = Assessment.FAIL if "FAIL" in outcomes else (
                Assessment.INDETERMINATE if "INDETERMINATE" in outcomes else Assessment.PASS)
        if len(req.checkpoint_declarations) < pol.min_checkpoint_count:
            check_status = Assessment.INSUFFICIENT
        present = {e.kind for e in req.independent_evidence}
        missing = tuple(k for k in pol.required_evidence_kinds if k not in present)
        draft = RegistrationDraft(req.request_id, ALGORITHM, req, pol, coefficients, solved.correlation,
            solved.correlation_guard, summary, checks, check_status, evidence, missing,
            ResourceUsage(admission.text_bytes, admission.refs, 0))
        # Count before publication, including the decimal digits of the count.
        size = _output_size(draft)
        for _ in range(8):
            candidate = replace(draft, resources=ResourceUsage(admission.text_bytes, admission.refs, size))
            next_size = _output_size(candidate)
            if next_size == size:
                return candidate
            size = next_size
        raise _Reject(ErrorCode.INPUT_LIMIT_EXCEEDED, "output", "OUTPUT_SIZE_UNSTABLE")
    except _Reject as error:
        return RegistrationFailure(error.diagnostic, ResourceUsage(admission.text_bytes, admission.refs, 0))
    except (num.NumericalFailure, OverflowError, ZeroDivisionError):
        return RegistrationFailure(RegistrationDiagnostic(ErrorCode.REGISTRATION_QUALITY_FAILED,
            "numerical", "NUMERICAL_FAILURE"), ResourceUsage(admission.text_bytes, admission.refs, 0))
