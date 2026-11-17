"""Synthetic pointwise positional checks; never a physical accuracy certificate.

Only a held-out checkpoint at the exact caller-specified ROI coordinate covers
that point. No interpolation, extrapolation, ROI-area coverage or authentication
of reference observations is implied. Existing evidence remains unverified.
"""
from dataclasses import dataclass

from . import registration as reg
from . import _registration_numeric as num
from .models import Point2


@dataclass(frozen=True, slots=True)
class PositionalPolicy:
    maximum_error_mm: float = 0.01


@dataclass(frozen=True, slots=True)
class InspectionLocation:
    location_id: str
    position: Point2


@dataclass(frozen=True, slots=True)
class LocationAssessment:
    location: InspectionLocation
    checkpoint_residuals: tuple[reg.Residual, ...]
    numerical_assessment: reg.Assessment


@dataclass(frozen=True, slots=True)
class PositionalDraft:
    registration: reg.RegistrationDraft
    policy: PositionalPolicy
    locations: tuple[LocationAssessment, ...]
    numerical_assessment: reg.Assessment
    physical_accuracy: reg.Assessment = reg.Assessment.INDETERMINATE
    validation_state: str = "NOT_PERFORMED"
    state: str = "DRAFT"


def _combine(outcomes):
    if reg.Assessment.FAIL in outcomes:
        return reg.Assessment.FAIL
    if not outcomes or any(v is not reg.Assessment.PASS for v in outcomes):
        return reg.Assessment.INDETERMINATE
    return reg.Assessment.PASS


def assess_registration_positions(request, fit_policy, locations, positional_policy):
    """Fit once and compare returned coefficients against supplied checkpoints.

    Maximum point error is fixed at the owner-approved 0.01 mm. PASS refers only
    to numerical agreement with supplied, structurally held-out observations.
    Reference truth, measurement uncertainty and physical accuracy remain unknown.
    Invalid input or exhausted admission/output capacity returns failure atomically.
    """
    admission = reg._Admission()
    try:
        reg._require(type(positional_policy) is PositionalPolicy, "positional_policy", "EXACT_TYPE_REQUIRED")
        limit = getattr(positional_policy, "maximum_error_mm", None)
        admission.read(limit, float, "positional_policy.maximum_error_mm")
        reg._require(limit == 0.01, "positional_policy.maximum_error_mm", "FIXED_10_MICROMETRE_POLICY", reg.ErrorCode.POLICY_INVALID)
        reg._require(type(locations) is tuple, "locations", "IMMUTABLE_TUPLE_REQUIRED")
        reg._require(len(locations) <= 32, "locations", "COLLECTION_LIMIT", reg.ErrorCode.INPUT_LIMIT_EXCEEDED)
        admitted = []
        for location in locations:
            reg._require(type(location) is InspectionLocation, "locations", "EXACT_TYPE_REQUIRED")
            identity = getattr(location, "location_id", None)
            point = getattr(location, "position", None)
            admission.read(identity, str, "locations.location_id")
            admission.read(point, Point2, "locations.position")
            admitted.append(InspectionLocation(identity, reg._canonical(point)))
        locations = tuple(sorted(admitted, key=lambda item: item.location_id))
        reg._unique(locations, "location_id", "locations")
        # One shared admission total, before fitting. The original entry point
        # repeats its own validation; this is not another numerical solve.
        admission.read(request, reg.RegistrationRequest, "request")
        admission.read(fit_policy, reg.RegistrationPolicy, "policy")
        for location in locations:
            reg._require(location.position.frame == request.source_frame,
                         "locations:" + location.location_id, "ROI_FRAME_CONTEXT", reg.ErrorCode.CONTEXT_MISMATCH)
        draft = reg.fit_rigid_registration(request, fit_policy)
        if type(draft) is reg.RegistrationFailure:
            return draft
        req = draft.request
        fit_sets = {o.measurement_set_id for o in req.fit_observations}
        covered = set()
        for evidence, assessment in zip(req.independent_evidence, draft.evidence_assessments):
            if evidence.kind is reg.EvidenceKind.HELD_OUT_CHECKPOINTS and assessment.independence is reg.Assessment.PASS:
                for observation in req.checkpoint_observations:
                    if (observation.fiducial_id in evidence.checkpoint_ids
                            and observation.measurement_set_id in evidence.validation_measurement_set_ids
                            and observation.measurement_set_id not in fit_sets
                            and observation.calibration_reference_id in evidence.calibration_reference_ids
                            and evidence.artifact_reference_ids):
                        covered.add(observation.fiducial_id)
        results = []
        for location in locations:
            records = () if draft.checkpoints is None else tuple(
                residual for declaration, residual in zip(req.checkpoint_declarations, draft.checkpoints.records)
                if declaration.position == location.position and declaration.fiducial_id in covered)
            outcome = _combine(tuple(reg.Assessment(num.compare(r.norm_mm, limit, r.guard_mm)) for r in records))
            results.append(LocationAssessment(location, records, outcome))
        result = PositionalDraft(draft, PositionalPolicy(limit), tuple(results),
                                 _combine(tuple(r.numerical_assessment for r in results)))
        reg._output_size(result)  # bound the complete retained result before publication
        return result
    except reg._Reject as error:
        return reg.RegistrationFailure(error.diagnostic, reg.ResourceUsage(admission.text_bytes, admission.refs, 0))
