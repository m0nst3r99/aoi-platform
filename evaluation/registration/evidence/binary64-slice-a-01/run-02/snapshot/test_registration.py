"""Independent literal and Decimal oracles for synthetic registration drafts.

Decimal oracle uses direct centroids and closed-form covariance; it does not
import the private solver, its centering, its guards, or its acceptance logic.
Inputs are exact Decimal.from_float values, not decimal approximations to them.
"""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal as D, localcontext
import ast
import inspect
import math

import pytest

from aoi_platform.geometry import registration as reg
from aoi_platform.geometry.errors import ErrorCode
from aoi_platform.geometry.models import AxisDirection, Frame, FrameKind, Point2, Unit


def policy(**changes):
    result = reg.RegistrationPolicy("synthetic-test", "1", reg.ALGORITHM, reg.Purpose.SYNTHETIC,
        10.0, 0.1, 0.05, 0.1, 0.05, 0.1, 0, False, 0.0, ())
    return replace(result, **changes)


def request(source=((0., 0.), (20., 0.)), target=None, checkpoints=(), checkpoint_target=()):
    revision = reg.RevisionKey("board", "revision", "0" * 64)
    context = reg.RegistrationContext(revision, reg.Side.TOP, "load", "station", "machine", "fixture", "fixture-v1")
    p = Frame("P", FrameKind.PCB, Unit.MM, "datum", AxisDirection.RIGHT, AxisDirection.UP, board_revision_id="revision")
    m = Frame("M", FrameKind.MACHINE, Unit.MM, "machine-datum", AxisDirection.RIGHT, AxisDirection.UP, machine_id="machine")
    artifact = reg.ArtifactReference("artifact", "1" * 64, "literal-fixture", "test-author", reg.EvidenceState.DECLARED_UNVERIFIED)
    calibration = reg.CalibrationReference("calibration", "1", artifact, "station", "machine", "M", "synthetic-config", reg.Purpose.SYNTHETIC)
    if target is None:
        target = tuple((x + 5, y + 7) for x, y in source)

    def pairs(points, measured, prefix):
        declarations = tuple(reg.FiducialDeclaration(f"{prefix}{i:02}", revision, reg.Side.TOP,
            Point2(float(x), float(y), p), "circle", (1., 1.), "artifact", ("artifact",)) for i, (x, y) in enumerate(points))
        observations = tuple(reg.MetricObservation(f"obs-{prefix}{i:02}", f"{prefix}{i:02}", context,
            Point2(float(x), float(y), m), prefix + "-measurements", "calibration", 1., None, ("artifact",))
            for i, (x, y) in enumerate(measured))
        return declarations, observations

    ds, obs = pairs(source, target, "fit")
    cds, cobs = pairs(checkpoints, checkpoint_target, "check")
    return reg.RegistrationRequest("request", context, p, m, ds, obs, cds, cobs, (calibration,), (artifact,), ())


def oracle(req, precision, coefficients=None, checkpoints=False):
    with localcontext() as ctx:
        ctx.prec = precision
        source = [(D.from_float(d.position.x), D.from_float(d.position.y)) for d in req.fit_declarations]
        target = [(D.from_float(o.position.x), D.from_float(o.position.y)) for o in req.fit_observations]
        n = D(len(source))
        px, py = (sum(p[k] for p in source) / n for k in (0, 1))
        qx, qy = (sum(p[k] for p in target) / n for k in (0, 1))
        a = sum((x-px)*(u-qx)+(y-py)*(v-qy) for (x,y),(u,v) in zip(source,target))
        b = sum((x-px)*(v-qy)-(y-py)*(u-qx) for (x,y),(u,v) in zip(source,target))
        radius = (a*a+b*b).sqrt()
        if coefficients is None:
            c, s = a/radius, b/radius
            tx, ty = qx-c*px+s*py, qy-s*px-c*py
        else:
            c, s, tx, ty = map(D.from_float, coefficients)
        if checkpoints:
            source = [(D.from_float(d.position.x), D.from_float(d.position.y)) for d in req.checkpoint_declarations]
            target = [(D.from_float(o.position.x), D.from_float(o.position.y)) for o in req.checkpoint_observations]
            n = D(len(source))
        vectors = [(c*x-s*y+tx-u, s*x+c*y+ty-v) for (x,y),(u,v) in zip(source,target)]
        norms = [(x*x+y*y).sqrt() for x,y in vectors]
        rms = (sum(z*z for z in norms)/n).sqrt()
        return (c, s, tx, ty), tuple(norms), rms, max(norms)


def assert_oracle(req, pol, result):
    """Guard contradiction is a STOP condition, not an adjustable tolerance."""
    assert isinstance(result, reg.RegistrationDraft), result
    exact100 = oracle(req, 100, result.coefficients)
    exact160 = oracle(req, 160, result.coefficients)
    for left, right in zip(exact100[1] + exact100[2:], exact160[1] + exact160[2:]):
        assert abs(left-right) < D("1e-85"), "ORACLE_NOT_CONVERGED"
    for record, true_norm in zip(result.fit.records, exact160[1]):
        assert abs(D.from_float(record.norm_mm)-true_norm) <= D.from_float(record.guard_mm), "GUARD_CONTRADICTION"
    assert abs(D.from_float(result.fit.rms_mm)-exact160[2]) <= D.from_float(result.fit.rms_guard_mm), "GUARD_CONTRADICTION"
    assert abs(D.from_float(result.fit.maximum_mm)-exact160[3]) <= D.from_float(result.fit.maximum_guard_mm), "GUARD_CONTRADICTION"
    assert exact160[2] <= D.from_float(pol.max_fit_rms_mm), "ACCEPTANCE_CONTRADICTION"
    assert exact160[3] <= D.from_float(pol.max_fit_error_mm), "ACCEPTANCE_CONTRADICTION"
    fitted = oracle(req, 160)[0]
    assert abs(D.from_float(result.coefficients[0])-fitted[0]) <= D("1e-12")
    assert abs(D.from_float(result.coefficients[1])-fitted[1]) <= D("1e-12")
    scale = max(1., *(abs(v) for d in req.fit_declarations for v in (d.position.x,d.position.y)),
                *(abs(v) for o in req.fit_observations for v in (o.position.x,o.position.y)),
                abs(result.coefficients[2]), abs(result.coefficients[3]))
    for actual, expected in zip(result.coefficients[2:], fitted[2:]):
        assert abs(D.from_float(actual)-expected) <= D.from_float(128 * 2.**-52 * scale)


@pytest.mark.parametrize("c,s", [(1.,0.), (0.,1.), (-1.,0.), (0.,-1.), (0.6,0.8)])
def test_literal_rotations_and_translation_decimal_oracle(c, s):
    source = ((0.,0.), (20.,0.), (0.,30.), (20.,30.))
    req = request(source, tuple((c*x-s*y+5, s*x+c*y+7) for x,y in source))
    result = reg.fit_rigid_registration(req, policy())
    assert_oracle(req, policy(), result)
    assert result.coefficients == pytest.approx((c,s,5.,7.), abs=1e-12)
    assert result.state == "DRAFT" and result.validation_state == "NOT_PERFORMED"


def test_noisy_fit_fixed_scale_independent_rational_oracle():
    source = ((-10.,-10.), (-10.,10.), (10.,-10.), (10.,10.))
    req = request(source, tuple((x*1025/1024+5, y*1025/1024+7) for x,y in source))
    result = reg.fit_rigid_registration(req, policy())
    assert_oracle(req, policy(), result)
    assert result.coefficients == (1.,0.,5.,7.)
    with localcontext() as ctx:
        ctx.prec = 160
        expected = D(10)*D(2).sqrt()/D(1024)
        assert abs(D.from_float(result.fit.rms_mm)-expected) < D("1e-17")


@pytest.mark.parametrize("offset", [0., 2.**19, 2.**20-1])
def test_large_offset_small_baseline(offset):
    req = request(((offset,0.), (offset+2.**-10,0.)), ((offset,1.), (offset+2.**-10,1.)))
    pol = policy(min_baseline_mm=2.**-11)
    result = reg.fit_rigid_registration(req, pol)
    assert_oracle(req, pol, result)
    assert result.coefficients == (1.,0.,0.,1.)


@pytest.mark.parametrize("delta,reason", [(0.,"DEGENERATE_CORRELATION"), (1e-9,"DEGENERATE_CORRELATION"),
                                         (2e-8,"NUMERICAL_AMBIGUITY")])
def test_near_degenerate_correlation(delta, reason):
    source = ((1.,0.),(-1.,0.),(0.,1.),(0.,-1.))
    req = request(source, ((1.,0.),(-1.,0.),(0.,-1.+delta),(0.,1.-delta)))
    pol = policy(min_baseline_mm=0.1, max_fit_rms_mm=3., max_fit_error_mm=3.)
    result = reg.fit_rigid_registration(req, pol)
    assert isinstance(result, reg.RegistrationFailure)
    assert result.diagnostic.reason == reason


def test_correlation_above_floor_has_finite_draft():
    source = ((1.,0.),(-1.,0.),(0.,1.),(0.,-1.))
    req = request(source, ((1.,0.),(-1.,0.),(0.,-1.+1e-6),(0.,1.-1e-6)))
    pol = policy(min_baseline_mm=0.1, max_fit_rms_mm=3., max_fit_error_mm=3.)
    assert_oracle(req, pol, reg.fit_rigid_registration(req, pol))


@pytest.mark.parametrize("source", [((0.,0.),(0.,0.)), ((2.**20,0.),(2.**20+2.**-40,0.))])
def test_coincident_and_precision_lost_inputs(source):
    result = reg.fit_rigid_registration(request(source, source), policy())
    assert isinstance(result, reg.RegistrationFailure)
    assert result.diagnostic.code is ErrorCode.FIDUCIAL_DEGENERATE


@pytest.mark.parametrize("mode", ["mirror", "wrong_correspondence", "outlier"])
def test_reflection_wrong_correspondence_and_outlier_fail_closed(mode):
    source = ((0.,0.),(20.,0.),(0.,30.),(25.,35.))
    target = tuple((x+5,y+7) for x,y in source)
    if mode == "mirror":
        target = tuple((-x+5,y+7) for x,y in source)
    elif mode == "wrong_correspondence":
        target = (target[1],target[0],target[2],target[3])
    else:
        target = target[:-1] + ((target[-1][0]+2,target[-1][1]),)
    result = reg.fit_rigid_registration(request(source,target), policy())
    assert isinstance(result, reg.RegistrationFailure)
    assert not hasattr(result, "coefficients") and not hasattr(result, "request")


@pytest.mark.parametrize("threshold", [math.nextafter(0.0625,0.), 0.0625, math.nextafter(0.0625,1.)])
def test_threshold_equality_and_adjacent_values_are_ambiguous(threshold):
    req = request(((0.,0.),(20.,0.)), ((0.,0.),(20.125,0.)))
    pol = policy(max_pair_distance_error_mm=1., max_fit_rms_mm=threshold, max_fit_error_mm=1.)
    result = reg.fit_rigid_registration(req,pol)
    assert isinstance(result,reg.RegistrationFailure)
    assert result.diagnostic.reason == "NUMERICAL_AMBIGUITY"


@pytest.mark.parametrize("threshold,success", [(0.0624,False),(0.0626,True)])
def test_clear_threshold_sides(threshold,success):
    req = request(((0.,0.),(20.,0.)), ((0.,0.),(20.125,0.)))
    pol = policy(max_pair_distance_error_mm=1.,max_fit_rms_mm=threshold,max_fit_error_mm=1.)
    result = reg.fit_rigid_registration(req,pol)
    if success:
        assert_oracle(req,pol,result)
    else:
        assert result.diagnostic.reason == "QUALITY_LIMIT"


def test_pair_alone_never_claims_verified_parity():
    req = request(((0.,0.),(20.,0.)), ((0.,0.),(-20.,0.)))
    result = reg.fit_rigid_registration(req,policy(required_evidence_kinds=(reg.EvidenceKind.SIDE_PARITY,)))
    assert isinstance(result,reg.RegistrationDraft)
    assert result.missing_evidence_kinds == (reg.EvidenceKind.SIDE_PARITY,)
    assert result.validation_state == "NOT_PERFORMED"


@pytest.mark.parametrize("offset,status", [(0.,reg.Assessment.PASS),(0.1,reg.Assessment.INDETERMINATE),(1.,reg.Assessment.FAIL)])
def test_checkpoint_assessment_does_not_refit(offset,status):
    req = request(checkpoints=((0.,10.),), checkpoint_target=((5.+offset,17.),))
    pol = policy(max_checkpoint_rms_mm=0.1,max_checkpoint_error_mm=0.1,
                 min_checkpoint_count=1,require_off_baseline_checkpoint=True,min_checkpoint_baseline_distance_mm=1.)
    result = reg.fit_rigid_registration(req,pol)
    assert isinstance(result,reg.RegistrationDraft)
    assert result.coefficients == (1.,0.,5.,7.)
    assert result.checkpoint_assessment is status
    true = oracle(req,160,result.coefficients,checkpoints=True)
    assert abs(D.from_float(result.checkpoints.rms_mm)-true[2]) <= D.from_float(result.checkpoints.rms_guard_mm), "GUARD_CONTRADICTION"


def test_evidence_is_declared_even_with_disjoint_checkpoint_sets():
    req = request(checkpoints=((0.,10.),),checkpoint_target=((5.,17.),))
    ev = reg.IndependentValidationEvidence("e",reg.EvidenceKind.HELD_OUT_CHECKPOINTS,"issuer",req.context,"P","M",
        ("calibration",),("fit-measurements",),("check-measurements",),("check00",),("artifact",),
        "independently declared observation",reg.EvidenceState.DECLARED_UNVERIFIED)
    result = reg.fit_rigid_registration(replace(req,independent_evidence=(ev,)),policy())
    assert result.evidence_assessments[0].independence is reg.Assessment.PASS
    assert result.evidence_assessments[0].state is reg.EvidenceState.DECLARED_UNVERIFIED
    assert result.validation_state == "NOT_PERFORMED"


def test_permutation_invariance_success_and_competing_errors():
    req = request(((0.,0.),(20.,0.),(0.,30.)))
    reversed_req = replace(req,fit_declarations=req.fit_declarations[::-1],fit_observations=req.fit_observations[::-1])
    assert reg.fit_rigid_registration(req,policy()) == reg.fit_rigid_registration(reversed_req,policy())
    bad = replace(req,fit_observations=tuple(replace(o,context=replace(o.context,load_id="wrong")) for o in req.fit_observations))
    assert reg.fit_rigid_registration(bad,policy()) == reg.fit_rigid_registration(replace(bad,fit_observations=bad.fit_observations[::-1]),policy())


def test_deep_immutability():
    result = reg.fit_rigid_registration(request(),policy())
    with pytest.raises(FrozenInstanceError):
        result.state = "ACTIVE"
    with pytest.raises(FrozenInstanceError):
        result.request.fit_declarations[0].position.x = 2.
    assert type(result.fit.records) is tuple


def test_no_resolver_camera_or_motion_dependencies(monkeypatch):
    from aoi_platform.geometry.resolver import TransformGraph
    def forbidden(*args,**kwargs):
        pytest.fail("integration boundary invoked")
    monkeypatch.setattr(TransformGraph,"__init__",forbidden)
    assert isinstance(reg.fit_rigid_registration(request(),policy()),reg.RegistrationDraft)
    for module in (reg, reg.num):
        tree = ast.parse(inspect.getsource(module))
        imported = [n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        assert not any(any(word in name for word in ("resolver","camera","motion","transforms")) for name in imported)


@pytest.mark.parametrize("case",range(12))
def test_bounded_adversarial_oracle_grid(case):
    # Deterministic literal geometries, no production solver used for expectations.
    c,s = ((1.,0.),(0.,1.),(0.6,0.8))[case%3]
    offset = (0.,2.**17,-2.**18)[case//4]
    source = tuple((offset+x,y) for x,y in ((0.,0.),(21.,2.),(-3.,31.),(22.,29.)))
    noise = 2.**-12
    target = tuple((c*x-s*y+5+noise*(i%2),s*x+c*y+7-noise*(i//2)) for i,(x,y) in enumerate(source))
    req = request(source,target)
    assert_oracle(req,policy(),reg.fit_rigid_registration(req,policy()))
