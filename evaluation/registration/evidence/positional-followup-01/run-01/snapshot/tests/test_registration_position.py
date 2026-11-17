"""Independent Decimal checks of represented coefficients at explicit ROI points."""
from dataclasses import replace
from decimal import Decimal as D
import math

import pytest

from aoi_platform.geometry import registration as reg
from aoi_platform.geometry import registration_position as pos
from aoi_platform.geometry.models import Point2
from test_registration import request, policy, oracle


def supported(req):
    evidence = reg.IndependentValidationEvidence("held-out", reg.EvidenceKind.HELD_OUT_CHECKPOINTS,
        "independent-synthetic-author", req.context, req.source_frame.frame_id, req.target_frame.frame_id,
        ("calibration",), ("fit-measurements",), ("check-measurements",),
        tuple(d.fiducial_id for d in req.checkpoint_declarations), ("artifact",),
        "Synthetic reference observations generated independently of fitted coefficients",
        reg.EvidenceState.DECLARED_UNVERIFIED)
    return replace(req, independent_evidence=(evidence,))


def assess(req, pol=None, locations=None):
    if locations is None:
        locations = tuple(pos.InspectionLocation(d.fiducial_id, d.position) for d in req.checkpoint_declarations)
    return pos.assess_registration_positions(req, pol or policy(), locations, pos.PositionalPolicy())


def check_decimal(req, result):
    assert type(result) is pos.PositionalDraft, result
    a = oracle(req, 100, result.registration.coefficients, checkpoints=True)
    b = oracle(req, 180, result.registration.coefficients, checkpoints=True)
    for x, y in zip(a[1], b[1]):
        assert abs(x-y) < D("1e-85")
    for record, exact in zip(result.registration.checkpoints.records, b[1]):
        assert abs(D.from_float(record.norm_mm)-exact) <= D.from_float(record.guard_mm)
    if result.numerical_assessment is reg.Assessment.PASS:
        assert max(b[1]) < D("0.01")
    assert result.physical_accuracy is reg.Assessment.INDETERMINATE
    assert result.state == "DRAFT" and result.validation_state == "NOT_PERFORMED"


def test_corners_far_from_fit_and_permutation():
    corners = ((-150.,-100.), (150.,-100.), (150.,100.), (-150.,100.))
    req = supported(request(checkpoints=corners, checkpoint_target=tuple((x+5,y+7) for x,y in corners)))
    result = assess(req)
    check_decimal(req, result)
    assert result.numerical_assessment is reg.Assessment.PASS
    assert assess(replace(req, fit_declarations=req.fit_declarations[::-1], fit_observations=req.fit_observations[::-1],
        checkpoint_declarations=req.checkpoint_declarations[::-1], checkpoint_observations=req.checkpoint_observations[::-1])) == result


@pytest.mark.parametrize("error,expected", [(0., "PASS"), (.009999, "PASS"), (.01, "INDETERMINATE"), (.010001, "FAIL"), (.1, "FAIL")])
def test_threshold_against_decimal(error, expected):
    req = supported(request(target=((0.,0.),(20.,0.)), checkpoints=((0.,0.),), checkpoint_target=((error,0.),)))
    result = assess(req)
    check_decimal(req, result)
    assert result.numerical_assessment.value == expected


@pytest.mark.parametrize("n", [3, 16, 64])
@pytest.mark.parametrize("rho", [1e-8, 2e-8, 5e-8, 1e-7, 1e-6])
def test_near_floor_independent_far_reference(n, rho):
    source = tuple((.01*math.cos(2*math.pi*i/n), .01*math.sin(2*math.pi*i/n)) for i in range(n))
    target = tuple((x+rho*(.6*x-.8*y), -y+rho*(.8*x+.6*y)) for x,y in source)
    base = request(source, target)
    # Decimal optimal transform is generated before calling the production fit.
    coefficients = oracle(base, 180)[0]
    corners = ((-150.,-100.), (150.,100.))
    c,s,tx,ty = coefficients
    reference = tuple((float(c*D(x)-s*D(y)+tx), float(s*D(x)+c*D(y)+ty)) for x,y in corners)
    req = supported(request(source, target, corners, reference))
    pol = policy(min_baseline_mm=.001, max_fit_rms_mm=.05, max_fit_error_mm=.05)
    result = assess(req, pol)
    if rho == 1e-8:
        assert type(result) is reg.RegistrationFailure
        assert result.diagnostic.reason == "NUMERICAL_AMBIGUITY"
    else:
        check_decimal(req, result)
        assert result.numerical_assessment is reg.Assessment.PASS


def test_fit_pass_does_not_establish_far_roi_accuracy():
    req = supported(request(checkpoints=((1000.,1000.),), checkpoint_target=((1005.02,1007.),)))
    result = assess(req)
    check_decimal(req, result)
    assert result.registration.fit.maximum_mm == 0.
    assert result.numerical_assessment is reg.Assessment.FAIL


@pytest.mark.parametrize("mode", ["missing", "nearby", "shared-measurements", "empty"])
def test_insufficient_coverage(mode):
    req = supported(request(checkpoints=((100.,100.),), checkpoint_target=((105.,107.),)))
    locations = None
    if mode == "missing":
        req = replace(req, independent_evidence=())
    elif mode == "nearby":
        locations = (pos.InspectionLocation("ROI", Point2(100.000001,100.,req.source_frame)),)
    elif mode == "shared-measurements":
        req = replace(req, checkpoint_observations=(replace(req.checkpoint_observations[0], measurement_set_id="fit-measurements"),),
            independent_evidence=(replace(req.independent_evidence[0], validation_measurement_set_ids=("fit-measurements",)),))
    else:
        locations = ()
    result = assess(req, locations=locations)
    assert result.numerical_assessment is reg.Assessment.INDETERMINATE
    assert result.physical_accuracy is reg.Assessment.INDETERMINATE


@pytest.mark.parametrize("mode", ["list", "duplicate", "nan", "frame", "oversize", "missing-slot", "count", "policy"])
def test_malformed_atomic(mode):
    req = request()
    location = pos.InspectionLocation("ROI", Point2(1.,2.,req.source_frame))
    locations = (location,)
    pol = pos.PositionalPolicy()
    if mode == "list": locations = [location]
    elif mode == "duplicate": locations = (location,location)
    elif mode == "nan":
        point = object.__new__(Point2)
        object.__setattr__(point, "x", float("nan"))
        object.__setattr__(point, "y", 0.)
        object.__setattr__(point, "frame", req.source_frame)
        locations = (replace(location, position=point),)
    elif mode == "frame": locations = (replace(location, position=Point2(1.,2.,req.target_frame)),)
    elif mode == "oversize": locations = (replace(location, location_id="x"*1000000),)
    elif mode == "missing-slot": locations = (object.__new__(pos.InspectionLocation),)
    elif mode == "count": locations = (location,)*33
    elif mode == "policy": pol = pos.PositionalPolicy(.02)
    result = pos.assess_registration_positions(req, policy(), locations, pol)
    assert type(result) is reg.RegistrationFailure
    assert not hasattr(result, "registration") and not hasattr(result, "locations")
