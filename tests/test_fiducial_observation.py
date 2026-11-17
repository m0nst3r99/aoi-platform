"""Synthetic ID-based observation contract tests; no image or hardware inputs."""
from dataclasses import FrozenInstanceError, replace

import pytest

from aoi_platform.geometry import fiducial_observation as obs
from aoi_platform.geometry import registration as reg
from aoi_platform.geometry.models import Point2, Unit
from test_registration import request, policy


def mapping(count=2):
    req = request(tuple((float(i*20), float(i%2)*10) for i in range(count)))
    values = tuple(obs.FiducialObservation(o.observation_id, o.fiducial_id, o.context,
        "camera", "calibration", "1", "image", "artifact", o.measurement_set_id,
        obs.CoordinateSpace.CALIBRATED_MM, o.position, obs.DetectionStatus.DETECTED,
        obs.DetectionQuality(.9, .001), ("artifact",), reg.EvidenceState.DECLARED_UNVERIFIED)
        for o in req.fit_observations)
    return obs.ObservationMappingInput(req.request_id, req.context, "camera", req.source_frame,
        req.target_frame, req.calibration_references[0], req.artifact_references, req.fit_declarations, values)


def change(data, **changes):
    return replace(data, observations=(replace(data.observations[0], **changes),)+data.observations[1:])


def failure(data, reason=None):
    result = obs.map_fiducial_observations(data)
    assert type(result) is reg.RegistrationFailure, result
    assert not hasattr(result, "request") and result.resources.output_bytes == 0
    if reason: assert result.diagnostic.reason == reason
    return result


@pytest.mark.parametrize("count", [2,3,16,64])
def test_valid_mapping_explicit_ids_and_registration(count):
    data = mapping(count)
    result = obs.map_fiducial_observations(data)
    assert type(result) is obs.ObservationMapping
    assert result.state == "UNVALIDATED"
    assert result.physical_verification is reg.Assessment.INDETERMINATE
    assert result.numerical_eligibility is reg.Assessment.NOT_PERFORMED
    assert [(o.fiducial_id,o.position.x,o.position.y) for o in result.request.fit_observations] == [
        (d.fiducial_id,d.position.x+5,d.position.y+7) for d in result.request.fit_declarations]
    assert type(reg.fit_rigid_registration(result.request, policy())) is reg.RegistrationDraft
    assert obs.map_fiducial_observations(replace(data, declarations=data.declarations[::-1],
        observations=data.observations[1:]+data.observations[:1])) == result
    with pytest.raises(FrozenInstanceError): result.state = "ACTIVE"
    assert result.admitted_input is not data and result.admitted_input.observations[0] is not data.observations[0]


def test_no_fit_during_mapping(monkeypatch):
    def forbidden(*args): raise AssertionError("fit invoked")
    monkeypatch.setattr(reg, "fit_rigid_registration", forbidden)
    assert type(obs.map_fiducial_observations(mapping())) is obs.ObservationMapping


@pytest.mark.parametrize("kind", ["observation", "fiducial", "declaration", "artifact"])
def test_duplicates_atomic(kind):
    data = mapping()
    if kind == "observation": data = change(data, observation_id=data.observations[1].observation_id)
    elif kind == "fiducial": data = change(data, fiducial_id=data.observations[1].fiducial_id)
    elif kind == "declaration": data = replace(data, declarations=data.declarations+(data.declarations[0],))
    else: data = replace(data, artifacts=data.artifacts+data.artifacts)
    assert failure(data).diagnostic.code is reg.ErrorCode.DUPLICATE_ID


@pytest.mark.parametrize("field", ["load_id","station_id","machine_id","side","revision"])
def test_context_mismatch(field):
    data = mapping()
    value = {"side":reg.Side.BOTTOM,"revision":replace(data.context.revision, revision_id="other")}.get(field,"other")
    failure(change(data, context=replace(data.context, **{field:value})), "OBSERVATION_CONTEXT")


@pytest.mark.parametrize("field", ["camera_id","calibration_id","calibration_version"])
def test_camera_calibration_mismatch(field):
    failure(change(mapping(), **{field:"other"}), "OBSERVATION_CONTEXT")


@pytest.mark.parametrize("space", [obs.CoordinateSpace.RAW_PIXEL, obs.CoordinateSpace.INDEPENDENT_REFERENCE_MM])
def test_pixel_and_reference_are_not_fit_observations(space):
    failure(change(mapping(), space=space), "CALIBRATED_OBSERVATION_REQUIRED")


def test_mixed_units_and_frame():
    data = mapping()
    point = data.observations[0].center
    # Forge frame to avoid constructor rejection before the API under test.
    frame = object.__new__(type(point.frame))
    for name in point.frame.__dataclass_fields__: object.__setattr__(frame,name,getattr(point.frame,name))
    object.__setattr__(frame,"unit", next(u for u in Unit if u is not Unit.MM))
    point2 = object.__new__(Point2)
    for name,value in (("x",point.x),("y",point.y),("frame",frame)): object.__setattr__(point2,name,value)
    failure(change(data, center=point2), "OBSERVATION_CONTEXT")
    failure(change(data, center=Point2(point.x,point.y,data.source_frame)), "OBSERVATION_CONTEXT")


@pytest.mark.parametrize("status", [obs.DetectionStatus.NOT_FOUND,obs.DetectionStatus.AMBIGUOUS])
def test_unusable_detection(status):
    failure(change(mapping(), status=status), "DETECTION_NOT_UNAMBIGUOUS")


@pytest.mark.parametrize("mode", ["missing-design","extra-design","insufficient","missing-time","missing-provenance","image-conflict"])
def test_missing_or_inconsistent_references(mode):
    data = mapping(3)
    if mode == "missing-design": data = replace(data,declarations=data.declarations[1:])
    elif mode == "extra-design": data = replace(data,observations=data.observations[1:])
    elif mode == "insufficient": data = mapping(1)
    elif mode == "missing-time": data = change(data,acquisition_time_reference_id="missing")
    elif mode == "missing-provenance": data = change(data,provenance_reference_ids=())
    else: data = change(data,measurement_set_id="other")
    failure(data)


@pytest.mark.parametrize("confidence,valid", [(0.,True),(1.,True),(-.001,False),(1.001,False),(float('nan'),False),(float('inf'),False)])
def test_quality_boundaries(confidence,valid):
    data = change(mapping(),quality=obs.DetectionQuality(confidence,0.))
    result = obs.map_fiducial_observations(data)
    assert (type(result) is obs.ObservationMapping) is valid


@pytest.mark.parametrize("sigma", [-.001,float('nan'),float('inf')])
def test_invalid_sigma(sigma):
    failure(change(mapping(),quality=obs.DetectionQuality(.5,sigma)))


def test_absent_quality_retained_not_invented():
    result = obs.map_fiducial_observations(change(mapping(),quality=None))
    assert result.admitted_input.observations[0].quality is None
    assert result.request.fit_observations[0].confidence == 0.


@pytest.mark.parametrize("mode", ["nan","infinity","missing-slot","oversize","list","count","verified","calibration-verified"])
def test_malformed_and_provenance_atomic(mode):
    data = mapping()
    if mode in ("nan","infinity"):
        point = object.__new__(Point2)
        for name,value in (("x",float('nan') if mode=='nan' else float('inf')),("y",0.),("frame",data.target_frame)):
            object.__setattr__(point,name,value)
        data = change(data,center=point)
    elif mode == "missing-slot": data = replace(data,observations=(object.__new__(obs.FiducialObservation),))
    elif mode == "oversize": data = change(data,camera_id="x"*1000000)
    elif mode == "list": data = replace(data,observations=list(data.observations))
    elif mode == "count": data = mapping(65)
    elif mode == "verified": data = change(data,verification_state="VERIFIED")
    else: data = replace(data,calibration=replace(data.calibration,artifact=replace(data.calibration.artifact,state="VERIFIED")))
    failure(data)


def test_competing_semantic_errors_deterministic():
    data = mapping()
    data = replace(data,observations=tuple(replace(o,camera_id="other") for o in data.observations))
    assert failure(data) == failure(replace(data,observations=data.observations[::-1]))
