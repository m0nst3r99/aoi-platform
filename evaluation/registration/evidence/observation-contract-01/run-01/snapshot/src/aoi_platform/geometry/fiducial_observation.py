"""Synthetic observation admission, without acquisition, calibration or fitting.

Constructors are not validation certificates. A mapped request is structurally
admitted only, remains unvalidated, and cannot establish physical accuracy.
"""
from dataclasses import dataclass, fields
from enum import StrEnum

from . import registration as reg
from .models import Frame, Point2


class CoordinateSpace(StrEnum):
    RAW_PIXEL = "RAW_PIXEL"
    CALIBRATED_MM = "CALIBRATED_MM"
    INDEPENDENT_REFERENCE_MM = "INDEPENDENT_REFERENCE_MM"


class DetectionStatus(StrEnum):
    DETECTED = "DETECTED"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class DetectionQuality:
    confidence: float  # dimensionless [0, 1]; not positional uncertainty
    localization_sigma_mm: float | None  # detector claim, not certified accuracy


@dataclass(frozen=True, slots=True)
class FiducialObservation:
    observation_id: str
    fiducial_id: str
    context: reg.RegistrationContext
    camera_id: str
    calibration_id: str
    calibration_version: str
    image_id: str
    acquisition_time_reference_id: str
    measurement_set_id: str
    space: CoordinateSpace
    center: Point2  # units and frame identity are explicit in center.frame
    status: DetectionStatus
    quality: DetectionQuality | None
    provenance_reference_ids: tuple[str, ...]
    verification_state: reg.EvidenceState


@dataclass(frozen=True, slots=True)
class ObservationMappingInput:
    request_id: str
    context: reg.RegistrationContext
    camera_id: str
    source_frame: Frame
    target_frame: Frame
    calibration: reg.CalibrationReference
    artifacts: tuple[reg.ArtifactReference, ...]
    declarations: tuple[reg.FiducialDeclaration, ...]
    observations: tuple[FiducialObservation, ...]


@dataclass(frozen=True, slots=True)
class ObservationMapping:
    request: reg.RegistrationRequest
    admitted_input: ObservationMappingInput
    structural_assessment: reg.Assessment = reg.Assessment.PASS
    numerical_eligibility: reg.Assessment = reg.Assessment.NOT_PERFORMED
    physical_verification: reg.Assessment = reg.Assessment.INDETERMINATE
    state: str = "UNVALIDATED"


_SCHEMAS = {
    DetectionQuality: (float, (float, None)),
    FiducialObservation: (str, str, reg.RegistrationContext, str, str, str, str, str, str,
        CoordinateSpace, Point2, DetectionStatus, (DetectionQuality, None), (str, 8), reg.EvidenceState),
    ObservationMappingInput: (str, reg.RegistrationContext, str, Frame, Frame, reg.CalibrationReference,
        (reg.ArtifactReference, 128), (reg.FiducialDeclaration, 64), (FiducialObservation, 64)),
}


class _Admission(reg._Admission):
    def read(self, value, schema, path, name=""):
        if isinstance(schema, type) and schema in _SCHEMAS:
            reg._require(type(value) is schema, path, "EXACT_TYPE_REQUIRED")
            for field, item in zip(fields(schema), _SCHEMAS[schema]):
                reg._require(hasattr(value, field.name), path + "." + field.name, "MISSING_FIELD")
                self.read(getattr(value, field.name), item, path + "." + field.name, field.name)
        else:
            super().read(value, schema, path, name)
            if schema is str and name in ("acquisition_time_reference_id", "calibration_id"):
                self.refs += 1
                reg._require(self.refs <= reg.REFERENCE_CAP, path, "REFERENCE_LIMIT", reg.ErrorCode.INPUT_LIMIT_EXCEEDED)


def _snapshot(value):
    if type(value) in _SCHEMAS:
        return type(value)(*(_snapshot(getattr(value, f.name)) for f in fields(value)))
    if type(value) is tuple:
        values = tuple(_snapshot(v) for v in value)
        if values and type(values[0]) is FiducialObservation:
            return tuple(sorted(values, key=lambda v: (v.fiducial_id, v.observation_id)))
        return reg._canonical(values)
    return reg._canonical(value)


def map_fiducial_observations(value: ObservationMappingInput) -> ObservationMapping | reg.RegistrationFailure:
    """Map all explicit ID correspondences, or return one atomic typed failure.

    Only CALIBRATED_MM/DETECTED observations may enter a fit request. Pixel and
    independent-reference records are distinguished but not converted or fitted.
    Calibration artifacts and observations remain DECLARED_UNVERIFIED; no caller
    can assert trusted verification through this API. Missing detector quality
    maps to confidence 0 (unknown), retained as None in admitted_input. Confidence
    is not a weight and no detection is selected, averaged, removed or downweighted.
    """
    admission = _Admission()
    try:
        admission.read(value, ObservationMappingInput, "mapping")
        data = _snapshot(value)
        reg._unique(data.observations, "observation_id", "observations")
        reg._unique(data.observations, "fiducial_id", "observation_fiducials")
        reg._unique(data.declarations, "fiducial_id", "declarations")
        artifacts = {a.reference_id for a in data.artifacts}
        for observation in data.observations:
            path = "observation:" + observation.observation_id
            reg._require(observation.space is CoordinateSpace.CALIBRATED_MM, path, "CALIBRATED_OBSERVATION_REQUIRED", reg.ErrorCode.MAPPING_UNVALIDATED)
            reg._require(observation.status is DetectionStatus.DETECTED, path, "DETECTION_NOT_UNAMBIGUOUS", reg.ErrorCode.MAPPING_UNVALIDATED)
            reg._require(observation.context == data.context and observation.camera_id == data.camera_id
                and observation.calibration_id == data.calibration.calibration_id
                and observation.calibration_version == data.calibration.calibration_version
                and observation.center.frame == data.target_frame,
                path, "OBSERVATION_CONTEXT", reg.ErrorCode.CONTEXT_MISMATCH)
            reg._require(observation.acquisition_time_reference_id in artifacts
                and bool(observation.provenance_reference_ids)
                and all(ref in artifacts for ref in observation.provenance_reference_ids), path, "MISSING_PROVENANCE")
            if observation.quality is not None:
                quality = observation.quality
                reg._require(0 <= quality.confidence <= 1 and
                    (quality.localization_sigma_mm is None or quality.localization_sigma_mm >= 0), path, "INVALID_QUALITY")
        # An image identity cannot name inconsistent acquisition/time metadata.
        images = {}
        for observation in data.observations:
            signature = (observation.acquisition_time_reference_id, observation.measurement_set_id)
            reg._require(observation.image_id not in images or images[observation.image_id] == signature,
                         "image:" + observation.image_id, "CONFLICTING_IMAGE_CONTEXT", reg.ErrorCode.CONTEXT_MISMATCH)
            images[observation.image_id] = signature
        observations = tuple(reg.MetricObservation(o.observation_id, o.fiducial_id, o.context, o.center,
            o.measurement_set_id, o.calibration_id, 0.0 if o.quality is None else o.quality.confidence,
            None, o.provenance_reference_ids) for o in data.observations)
        request = reg.RegistrationRequest(data.request_id, data.context, data.source_frame, data.target_frame,
            data.declarations, observations, (), (), (data.calibration,), data.artifacts, ())
        # Validate the generated request's own bounds as well as its context and
        # references. No solver, positional assessment or resolver is invoked.
        reg._Admission().read(request, reg.RegistrationRequest, "request")
        request = reg._canonical(request)
        reg._context(request)
        reg._references(request)
        result = ObservationMapping(request, data)
        reg._output_size(result)
        return result
    except reg._Reject as error:
        return reg.RegistrationFailure(error.diagnostic, reg.ResourceUsage(admission.text_bytes, admission.refs, 0))
