"""Admission/resource negatives do not infer limits from production counters."""

from dataclasses import replace
import math

import pytest

from aoi_platform.geometry import registration as reg
from aoi_platform.geometry.errors import ErrorCode
from test_registration import request, policy


@pytest.mark.parametrize("name",["load_id","station_id","machine_id"])
def test_wrong_observation_context(name):
    req = request()
    obs = replace(req.fit_observations[0],context=replace(req.context,**{name:"wrong"}))
    result = reg.fit_rigid_registration(replace(req,fit_observations=(obs,req.fit_observations[1])),policy())
    assert result.diagnostic.code is ErrorCode.CONTEXT_MISMATCH


@pytest.mark.parametrize("change",["revision","side","frame"])
def test_wrong_declaration_context(change):
    req = request()
    d = req.fit_declarations[0]
    if change == "revision":
        d = replace(d,revision=replace(d.revision,revision_id="wrong"))
    elif change == "side":
        d = replace(d,side=reg.Side.BOTTOM)
    else:
        d = replace(d,position=replace(d.position,frame=req.target_frame))
    result = reg.fit_rigid_registration(replace(req,fit_declarations=(d,req.fit_declarations[1])),policy())
    assert result.diagnostic.code is ErrorCode.CONTEXT_MISMATCH


@pytest.mark.parametrize("kind",["declaration","observation","artifact","calibration"])
def test_duplicate_ids(kind):
    req = request()
    fields = {"declaration":"fit_declarations","observation":"fit_observations","artifact":"artifact_references","calibration":"calibration_references"}
    field = fields[kind]
    items = getattr(req,field)
    result = reg.fit_rigid_registration(replace(req,**{field:items+(items[0],)}),policy())
    assert result.diagnostic.code is ErrorCode.DUPLICATE_ID


@pytest.mark.parametrize("kind",["counterpart","artifact","calibration"])
def test_missing_ids(kind):
    req = request(((0.,0.),(20.,0.),(0.,30.)))
    req = (replace(req,fit_observations=req.fit_observations[:-1]) if kind == "counterpart" else
           replace(req,artifact_references=()) if kind == "artifact" else replace(req,calibration_references=()))
    result = reg.fit_rigid_registration(req,policy())
    assert result.diagnostic.code is ErrorCode.SCHEMA_INVALID


@pytest.mark.parametrize("count,success",[(64,True),(65,False)])
def test_correspondence_count_boundary(count,success):
    req = request(tuple((float(i),float(i%3)) for i in range(count)))
    result = reg.fit_rigid_registration(req,policy())
    assert isinstance(result,reg.RegistrationDraft) is success
    if not success:
        assert result.diagnostic.code is ErrorCode.INPUT_LIMIT_EXCEEDED


@pytest.mark.parametrize("count,success",[(32,True),(33,False)])
def test_checkpoint_count_boundary(count,success):
    points = tuple((float(i),10.) for i in range(count))
    req = request(checkpoints=points,checkpoint_target=tuple((x+5,y+7) for x,y in points))
    result = reg.fit_rigid_registration(req,policy())
    assert isinstance(result,reg.RegistrationDraft) is success


@pytest.mark.parametrize("text,success",[("x"*128,True),("x"*129,False),("é"*64,True),("é"*64+"x",False),("\ud800",False)])
def test_utf8_id_boundaries(text,success):
    result = reg.fit_rigid_registration(replace(request(),request_id=text),policy())
    assert isinstance(result,reg.RegistrationDraft) is success


@pytest.mark.parametrize("value,success",[(2.**20,True),(math.nextafter(2.**20,math.inf),False)])
def test_coordinate_boundary(value,success):
    result = reg.fit_rigid_registration(request(((value,0.),(value-20.,0.)),((value,1.),(value-20.,1.))),policy())
    assert isinstance(result,reg.RegistrationDraft) is success


def test_oversized_metadata_rejected_before_solver(monkeypatch):
    def forbidden(*args):
        pytest.fail("solver invoked before admission")
    monkeypatch.setattr(reg.num,"solve",forbidden)
    result = reg.fit_rigid_registration(replace(request(),request_id="x"*129),policy())
    assert result.diagnostic.code is ErrorCode.INPUT_LIMIT_EXCEEDED


class Hostile:
    def __str__(self):
        raise AssertionError("formatted untrusted object")
    def __repr__(self):
        raise AssertionError("formatted untrusted object")
    def __iter__(self):
        raise AssertionError("traversed untrusted object")


@pytest.mark.parametrize("field",["request_id","fit_declarations","context"])
def test_untrusted_objects_not_consumed(field):
    result = reg.fit_rigid_registration(replace(request(),**{field:Hostile()}),policy())
    assert isinstance(result,reg.RegistrationFailure)


@pytest.mark.parametrize("changes",[{"purpose":"PRODUCTION"},{"max_fit_rms_mm":float("nan")},
    {"max_fit_rms_mm":-1.},{"max_fit_rms_mm":1.},{"min_baseline_mm":0.},
    {"require_off_baseline_checkpoint":True},{"required_evidence_kinds":(reg.EvidenceKind.SIDE_PARITY,)*2}])
def test_invalid_explicit_policy(changes):
    result = reg.fit_rigid_registration(request(),policy(**changes))
    assert result.diagnostic.code is ErrorCode.POLICY_INVALID


def test_caller_cannot_claim_verified_evidence():
    req = request()
    artifact = replace(req.artifact_references[0],state="VERIFIED")
    result = reg.fit_rigid_registration(replace(req,artifact_references=(artifact,)),policy())
    assert isinstance(result,reg.RegistrationFailure)


def test_zero_quality_threshold_is_not_silently_relaxed():
    result = reg.fit_rigid_registration(request(),policy(max_fit_rms_mm=0.,max_fit_error_mm=0.))
    assert result.diagnostic.reason == "NUMERICAL_AMBIGUITY"


def test_output_size_and_failure_atomicity(monkeypatch):
    req = request()
    result = reg.fit_rigid_registration(req,policy())
    serialized = "".join(reg._json_chunks(result)).encode("utf-8")
    assert result.resources.output_bytes == len(serialized)
    monkeypatch.setattr(reg,"OUTPUT_CAP",len(serialized))
    assert isinstance(reg.fit_rigid_registration(req,policy()),reg.RegistrationDraft)
    monkeypatch.setattr(reg,"OUTPUT_CAP",len(serialized)-1)
    failure = reg.fit_rigid_registration(req,policy())
    assert failure.diagnostic.reason == "OUTPUT_LIMIT"
    assert not hasattr(failure,"coefficients")
    assert len("".join(reg._json_chunks(failure)).encode()) <= 4096


def test_nonfinite_intermediate_is_atomic(monkeypatch):
    monkeypatch.setattr(reg.num,"hypot",lambda *args: float("inf"))
    result = reg.fit_rigid_registration(request(),policy())
    assert result.diagnostic.reason == "NUMERICAL_FAILURE"
