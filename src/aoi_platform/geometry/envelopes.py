"""Separate capacity, fixture and travel records; no physical defaults or motion."""

from dataclasses import dataclass, field
from enum import StrEnum
from math import ulp
from typing import ClassVar

from .errors import ErrorCode, GeometryError, finite_number, require_text
from .fixture_geometry import rectangle_bounds, rectangle_relation, transform_outline
from .models import Frame, FrameKind, require_same_frame
from .outlines import EPS, Outline, outline_bounds
from .reports import ContractError, Evidence, _evidence
from .transforms import Transform2, TransformKind


def _schema(message: str, path: str) -> None:
    raise GeometryError(ErrorCode.SCHEMA_INVALID, message, field_path=path)


def _ids(values: tuple[str, ...], path: str) -> None:
    if not isinstance(values, tuple):
        _schema("Supply immutable identity/reference tuples.", path)
    for value in values:
        require_text(value, path)
    if len(set(values)) != len(values):
        _schema("Duplicate identity/reference.", path)


class EvidenceKind(StrEnum):
    SYNTHETIC = "synthetic"
    QUALIFIED = "qualified"


@dataclass(frozen=True, slots=True)
class EnvelopeEvidence:
    kind: EvidenceKind
    evidence_ids: tuple[str, ...]
    qualification_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, EvidenceKind):
            _schema("Declare evidence kind explicitly.", "evidence.kind")
        _ids(self.evidence_ids, "evidence.evidence_ids")
        _ids(self.qualification_ids, "evidence.qualification_ids")
        if not self.evidence_ids:
            _schema("Evidence needs traceable references.", "evidence.evidence_ids")
        if (self.kind is EvidenceKind.QUALIFIED) != bool(self.qualification_ids):
            _schema("Qualified declarations require separate qualification references; synthetic evidence cannot qualify.", "evidence.qualification_ids")


@dataclass(frozen=True, slots=True)
class BoardCapacity:
    capacity_id: str
    version: str
    width_mm: float = field(default=280.0, init=False)
    height_mm: float = field(default=550.0, init=False)

    def __post_init__(self) -> None:
        require_text(self.capacity_id, "capacity.capacity_id")
        require_text(self.version, "capacity.version")


def _machine_frame(frame: Frame, machine_id: str) -> None:
    if not isinstance(frame, Frame) or frame.kind is not FrameKind.MACHINE:
        _schema("Supply the complete machine Frame M.", "envelope.frame")
    if frame.machine_id != machine_id:
        raise GeometryError(ErrorCode.CONTEXT_MISMATCH, "Envelope machine differs from its frame.", field_path="envelope.machine_id")


def _regions(frame: Frame, region: Outline | None, exclusions: tuple[Outline, ...], evidence: EnvelopeEvidence | None) -> None:
    if region is not None and not isinstance(region, Outline):
        raise GeometryError(ErrorCode.GEOMETRY_UNSUPPORTED, "Supply a supported Outline region or None.", field_path="envelope.region")
    if not isinstance(exclusions, tuple) or any(not isinstance(r, Outline) for r in exclusions):
        raise GeometryError(ErrorCode.GEOMETRY_UNSUPPORTED, "Supply an immutable tuple of supported exclusion regions.", field_path="envelope.exclusions")
    ids = []
    for shape in ((region,) if region is not None else ()) + exclusions:
        require_same_frame(shape.frame, frame, "envelope.geometry.frame")
        rectangle_bounds(shape)
        ids.append(shape.outline_id)
    _ids(tuple(ids), "envelope.geometry_ids")
    if evidence is not None and not isinstance(evidence, EnvelopeEvidence):
        _schema("Supply EnvelopeEvidence or None.", "envelope.evidence")
    if (region is not None or exclusions) and evidence is None:
        _schema("Supplied geometry requires explicit evidence.", "envelope.evidence")


@dataclass(frozen=True, slots=True)
class FixtureEnvelope:
    envelope_id: str
    version: str
    machine_id: str
    fixture_id: str
    configuration_id: str
    frame: Frame
    usable_region: Outline | None
    exclusions: tuple[Outline, ...]
    margin_mm: float | None
    evidence: EnvelopeEvidence | None

    def __post_init__(self) -> None:
        for name in ("envelope_id", "version", "machine_id", "fixture_id", "configuration_id"):
            require_text(getattr(self, name), f"fixture.{name}")
        _machine_frame(self.frame, self.machine_id)
        _regions(self.frame, self.usable_region, self.exclusions, self.evidence)
        if self.margin_mm is not None:
            margin = finite_number(self.margin_mm, "fixture.margin_mm")
            if margin < 0:
                _schema("Margin must be nonnegative.", "fixture.margin_mm")
            object.__setattr__(self, "margin_mm", margin)


@dataclass(frozen=True, slots=True)
class CameraTravelEnvelope:
    envelope_id: str
    version: str
    machine_id: str
    camera_id: str
    configuration_id: str
    frame: Frame
    reference_point: str
    permitted_region: Outline | None
    exclusions: tuple[Outline, ...]
    evidence: EnvelopeEvidence | None

    def __post_init__(self) -> None:
        for name in ("envelope_id", "version", "machine_id", "camera_id", "configuration_id", "reference_point"):
            require_text(getattr(self, name), f"travel.{name}")
        _machine_frame(self.frame, self.machine_id)
        _regions(self.frame, self.permitted_region, self.exclusions, self.evidence)


class FitStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class FitCheck:
    status: FitStatus
    reasons: tuple[str, ...]
    record_ids: tuple[tuple[str, str], ...] = ()
    evidence_ids: tuple[str, ...] = ()
    violations: tuple[ContractError, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, FitStatus):
            _schema("Supply FitStatus.", "fit.status")
        _ids(self.reasons, "fit.reasons")
        _ids(self.evidence_ids, "fit.evidence_ids")
        if not self.reasons:
            _schema("Fit states must retain reasons.", "fit.reasons")
        if not isinstance(self.record_ids, tuple):
            _schema("Supply immutable (identity, version) pairs.", "fit.record_ids")
        for pair in self.record_ids:
            if not isinstance(pair, tuple) or len(pair) != 2:
                _schema("Supply (identity, version) pairs.", "fit.record_ids")
            for value in pair:
                require_text(value, "fit.record_ids")
        if not isinstance(self.violations, tuple) or any(not isinstance(v, ContractError) for v in self.violations):
            _schema("Supply structured violations.", "fit.violations")
        if (self.status is FitStatus.FAIL) != bool(self.violations):
            _schema("Only failed checks carry mandatory violations.", "fit.violations")


@dataclass(frozen=True, slots=True)
class CapacityResult:
    check: FitCheck
    outline_id: str
    frame: Frame
    rotation_deg: float
    width_mm: float
    height_mm: float
    arithmetic_guard_mm: float
    numerical_policy_id: ClassVar[str] = "capacity-binary64-v1"

    def __post_init__(self) -> None:
        require_text(self.outline_id, "capacity_result.outline_id")
        if not isinstance(self.check, FitCheck) or not isinstance(self.frame, Frame):
            _schema("Supply typed check and frame records.", "capacity_result")
        for name in ("rotation_deg", "width_mm", "height_mm", "arithmetic_guard_mm"):
            value = finite_number(getattr(self, name), f"capacity_result.{name}")
            if name != "rotation_deg" and value < 0:
                _schema("Extents and arithmetic guard must be nonnegative.", f"capacity_result.{name}")


def check_capacity(outline: Outline, capacity: BoardCapacity, *, rotation_deg: float) -> CapacityResult:
    if not isinstance(outline, Outline) or not isinstance(capacity, BoardCapacity):
        _schema("Supply Outline and BoardCapacity records.", "capacity.request")
    if outline.frame.kind is not FrameKind.PCB:
        raise GeometryError(ErrorCode.CONTEXT_MISMATCH, "Capacity uses the canonical board outline in frame P.", field_path="capacity.frame")
    rotation = finite_number(rotation_deg, "capacity.rotation_deg")
    bounds = outline_bounds(outline, rotation)
    width, height = bounds[2]-bounds[0], bounds[3]-bounds[1]
    # Exact multiples of 90 degrees use signed coordinate permutations. For
    # other angles allow only bounded binary64 arithmetic error, never a fit
    # tolerance: <=1e-8 mm, five orders below the mandatory 0.001 mm overrun.
    guard = min(1e-8, 16*ulp(max(550.0, *(abs(v) for v in bounds))))
    violations = ()
    if width > capacity.width_mm+guard or height > capacity.height_mm+guard:
        context: Evidence = (("board_revision_id", outline.frame.board_revision_id),
                             ("frame_id", outline.frame.frame_id), ("capacity_id", capacity.capacity_id),
                             ("capacity_version", capacity.version), ("rotation_deg", str(rotation)))
        violations = (ContractError(ErrorCode.BOARD_CAPACITY_EXCEEDED,
            "Declared orientation exceeds the board size requirement.", "capacity.extents_mm",
            "Use a compliant outline or explicitly request another permitted orientation.",
            entity_id=outline.outline_id, expected="width <= 280 mm; height <= 550 mm",
            actual=f"width={width!r}; height={height!r}", context=context),)
    check = FitCheck(FitStatus.FAIL if violations else FitStatus.PASS,
                     ("BOARD_CAPACITY_EXCEEDED" if violations else "DECLARED_ORIENTATION_FITS",),
                     ((capacity.capacity_id, capacity.version),), violations=violations)
    return CapacityResult(check, outline.outline_id, outline.frame, rotation, width, height, guard)


@dataclass(frozen=True, slots=True)
class FitReport:
    report_id: str
    capacity: CapacityResult
    fixture: FitCheck
    camera_reachability: FitCheck
    context: Evidence = ()
    motion_authorized: bool = field(default=False, init=False)
    targeting_ready: bool = field(default=False, init=False)
    schema_version: ClassVar[str] = "fit-report-v1"

    def __post_init__(self) -> None:
        require_text(self.report_id, "fit.report_id")
        if not isinstance(self.capacity, CapacityResult) or not isinstance(self.fixture, FitCheck) or not isinstance(self.camera_reachability, FitCheck):
            _schema("Supply separate capacity/fixture/camera results.", "fit")
        if self.camera_reachability.status is not FitStatus.UNRESOLVED:
            _schema("Camera reachability remains unresolved in this foundation.", "fit.camera_reachability")
        object.__setattr__(self, "context", _evidence(self.context, "fit.context"))


def _fixture_check(outline: Outline, fixture: FixtureEnvelope | None,
                   load: Transform2 | None) -> FitCheck:
    records = () if fixture is None else ((fixture.envelope_id, fixture.version),)
    evidence = () if fixture is None or fixture.evidence is None else tuple(sorted(fixture.evidence.evidence_ids))
    missing = []
    if fixture is None or fixture.usable_region is None:
        missing.append("FIXTURE_GEOMETRY_MISSING")
    if fixture is not None and fixture.margin_mm is None:
        missing.append("FIXTURE_MARGIN_MISSING")
    if load is None:
        missing.append("LOAD_TRANSFORM_MISSING")
    if missing:
        return FitCheck(FitStatus.UNRESOLVED, tuple(missing), records, evidence)

    loaded = transform_outline(outline, load)
    context = [("outline_id", outline.outline_id), ("source_frame_id", outline.frame.frame_id),
               ("frame_id", fixture.frame.frame_id), ("machine_id", fixture.machine_id),
               ("fixture_id", fixture.fixture_id), ("configuration_id", fixture.configuration_id),
               ("envelope_id", fixture.envelope_id), ("envelope_version", fixture.version),
               ("load_transform_id", load.transform_id), ("margin_mm", str(fixture.margin_mm)),
               ("numerical_policy_id", "fixture-binary64-v1"), ("arithmetic_guard_mm", str(EPS)),
               ("evidence_kind", fixture.evidence.kind.value)]
    for name in ("board_revision_id", "capture_id"):
        value = getattr(outline.frame, name) or getattr(fixture.frame, name)
        if value is not None:
            context.append((name, value))
    violations = []

    def violation(reason: str, region: Outline, actual: str) -> None:
        violations.append(ContractError(
            ErrorCode.BOARD_OUT_OF_ENVELOPE, reason, "fixture.geometry",
            "Change the declared load or supply a compliant fixture configuration and outline.",
            entity_id=outline.outline_id, expected=f"clearance >= {fixture.margin_mm!r} mm; no exclusion contact",
            actual=actual, context=tuple(context) + (("region_id", region.outline_id),)))

    outer = rectangle_relation(loaded, fixture.usable_region)
    if min(outer.outer_clearances_mm) + EPS < fixture.margin_mm:
        violation("Loaded outline violates usable region or its margin.", fixture.usable_region,
                  f"signed_clearances_mm={outer.outer_clearances_mm!r}")
    for exclusion in sorted(fixture.exclusions, key=lambda region: region.outline_id):
        relation = rectangle_relation(loaded, exclusion)
        if relation.filled_overlap or relation.separation_mm + EPS < fixture.margin_mm:
            violation("Loaded outline intersects, touches, contains or is too close to an exclusion.", exclusion,
                      f"filled_overlap={relation.filled_overlap}; separation_mm={relation.separation_mm!r}")
    return FitCheck(FitStatus.FAIL if violations else FitStatus.PASS,
                    ("BOARD_OUT_OF_ENVELOPE" if violations else "LOADED_OUTLINE_FITS",),
                    records, evidence, tuple(violations))


def validate_fit(outline: Outline, capacity: BoardCapacity, *, rotation_deg: float,
                 report_id: str, fixture: FixtureEnvelope | None = None,
                 travel: CameraTravelEnvelope | None = None,
                 load_transform: Transform2 | None = None) -> FitReport:
    """Evaluate capacity and selected rectangle fixture subset; never authorize motion."""
    result = check_capacity(outline, capacity, rotation_deg=rotation_deg)
    if fixture is not None and not isinstance(fixture, FixtureEnvelope):
        _schema("Supply FixtureEnvelope or None.", "fit.fixture")
    if travel is not None and not isinstance(travel, CameraTravelEnvelope):
        _schema("Supply CameraTravelEnvelope or None.", "fit.travel")
    frames = [outline.frame]
    if load_transform is not None:
        if not isinstance(load_transform, Transform2):
            _schema("Supply a declared Transform2 load.", "fit.load_transform")
        load_transform._require_validated_conventions()
        if load_transform.kind is not TransformKind.RIGID:
            raise GeometryError(ErrorCode.GEOMETRY_UNSUPPORTED,
                                "Load requires a declared proper rigid registration; affine scaling is not placement.",
                                field_path="fit.load_transform.kind")
        require_same_frame(load_transform.from_frame, outline.frame, "fit.load_transform.from_frame")
        if load_transform.to_frame.kind is not FrameKind.MACHINE:
            raise GeometryError(ErrorCode.CONTEXT_MISMATCH, "Load target must be frame M.", field_path="fit.load_transform.to_frame")
        frames.append(load_transform.to_frame)
    for envelope in (fixture, travel):
        if envelope is not None:
            frames.append(envelope.frame)
            if load_transform is not None:
                require_same_frame(envelope.frame, load_transform.to_frame, "fit.envelope.frame")
    for name in ("board_revision_id", "machine_id", "capture_id"):
        values = {getattr(frame, name) for frame in frames if getattr(frame, name) is not None}
        if len(values) > 1:
            raise GeometryError(ErrorCode.CONTEXT_MISMATCH, f"Conflicting {name} in fit inputs.", field_path=f"fit.{name}")
    fixture_check = _fixture_check(outline, fixture, load_transform)
    camera_check = FitCheck(FitStatus.UNRESOLVED, ("OPTICAL_COVERAGE_AND_REACHABILITY_NOT_VALIDATED",),
                           () if travel is None else ((travel.envelope_id, travel.version),),
                           () if travel is None or travel.evidence is None else travel.evidence.evidence_ids)
    context = [("outline_id", outline.outline_id), ("board_revision_id", outline.frame.board_revision_id),
               ("source_frame_id", outline.frame.frame_id)]
    if fixture is not None:
        context.extend((("fixture_id", fixture.fixture_id), ("fixture_configuration_id", fixture.configuration_id),
                        ("fixture_machine_id", fixture.machine_id), ("fixture_frame_id", fixture.frame.frame_id),
                        ("fixture_numerical_policy_id", "fixture-binary64-v1"),
                        ("fixture_arithmetic_guard_mm", str(EPS))))
    if travel is not None:
        context.extend((("camera_id", travel.camera_id), ("camera_configuration_id", travel.configuration_id),
                        ("camera_reference_point", travel.reference_point), ("travel_machine_id", travel.machine_id),
                        ("travel_frame_id", travel.frame.frame_id)))
    if load_transform is not None:
        context.extend((("load_transform_id", load_transform.transform_id), ("load_target_frame_id", load_transform.to_frame.frame_id)))
    for name in ("machine_id", "capture_id"):
        value = next((getattr(frame, name) for frame in frames if getattr(frame, name) is not None), None)
        if value is not None:
            context.append((name, value))
    return FitReport(report_id, result, fixture_check, camera_check, tuple(context))
