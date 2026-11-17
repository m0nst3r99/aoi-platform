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


def test_forged_frozen_frame_cannot_escape_atomic_failure():
    req = request()
    # A frozen constructor is not an admission certificate.
    object.__setattr__(req.source_frame,"board_revision_id",None)
    result = reg.fit_rigid_registration(req,policy())
    assert isinstance(result,reg.RegistrationFailure)
    assert result.diagnostic.code is ErrorCode.CONTEXT_MISMATCH


def test_missing_field_on_forged_record_is_bounded_failure():
    req = request()
    object.__delattr__(req.context,"station_id")
    result = reg.fit_rigid_registration(req,policy())
    assert isinstance(result,reg.RegistrationFailure)


@pytest.mark.parametrize("count,success",[(128,True),(129,False)])
def test_artifact_registry_boundary(count,success):
    req = request()
    original = req.artifact_references[0]
    artifacts = (original,) + tuple(replace(original,reference_id=f"extra{i}") for i in range(count-1))
    result = reg.fit_rigid_registration(replace(req,artifact_references=artifacts),policy())
    assert isinstance(result,reg.RegistrationDraft) is success


@pytest.mark.parametrize("count,success",[(16,True),(17,False)])
def test_calibration_registry_boundary(count,success):
    req = request()
    original = req.calibration_references[0]
    records = (original,) + tuple(replace(original,calibration_id=f"extra{i}") for i in range(count-1))
    result = reg.fit_rigid_registration(replace(req,calibration_references=records),policy())
    assert isinstance(result,reg.RegistrationDraft) is success


@pytest.mark.parametrize("length,success",[(512,True),(513,False)])
def test_locator_boundary(length,success):
    req = request()
    artifact = replace(req.artifact_references[0],locator="é"*(length//2)+"x"*(length%2))
    req = replace(req,artifact_references=(artifact,),calibration_references=(replace(req.calibration_references[0],artifact=artifact),))
    assert isinstance(reg.fit_rigid_registration(req,policy()),reg.RegistrationDraft) is success


def _text_bytes(value):
    # Independently authored input-size oracle; no production counter/helper.
    from dataclasses import fields,is_dataclass
    if type(value) is str:
        return len(value.encode("utf-8"))
    if type(value) is tuple:
        return sum(_text_bytes(v) for v in value)
    if is_dataclass(value):
        return sum(_text_bytes(getattr(value,f.name)) for f in fields(value))
    return 0


@pytest.mark.parametrize("over",[0,1])
def test_total_text_exact_boundary(over):
    req = request()
    original = req.artifact_references[0]
    extras = tuple(replace(original,reference_id=f"extra{i}",locator="x") for i in range(127))
    req = replace(req,artifact_references=(original,)+extras)
    remaining = 65536 + over - _text_bytes(req) - _text_bytes(policy())
    records = list(req.artifact_references)
    for i in range(1,len(records)):
        increment = min(511,remaining)
        records[i] = replace(records[i],locator="x"*(1+increment))
        remaining -= increment
    assert remaining == 0
    req = replace(req,artifact_references=tuple(records))
    assert _text_bytes(req)+_text_bytes(policy()) == 65536+over
    result = reg.fit_rigid_registration(req,policy())
    assert isinstance(result,reg.RegistrationDraft) is (over == 0)
    if over:
        assert result.diagnostic.reason == "TEXT_LIMIT"


@pytest.mark.parametrize("over",[0,1])
def test_total_reference_occurrences_boundary(over):
    req = request(tuple((float(i),float(i%3)) for i in range(64)))
    # 64 declarations x (approval + provenance) + 64 observations x
    # (calibration + provenance) + one calibration artifact = 257 occurrences.
    extra = 512 + over - 257
    declarations = []
    for d in req.fit_declarations:
        add = min(7,extra)
        declarations.append(replace(d,provenance_reference_ids=("artifact",)*(1+add)))
        extra -= add
    assert extra == 0
    result = reg.fit_rigid_registration(replace(req,fit_declarations=tuple(declarations)),policy())
    assert isinstance(result,reg.RegistrationDraft) is (over == 0)
    if over:
        assert result.diagnostic.reason == "REFERENCE_LIMIT"


def test_nonfinite_forged_point_is_rejected_before_sort():
    req = request()
    object.__setattr__(req.fit_declarations[0].position,"x",float("nan"))
    result = reg.fit_rigid_registration(req,policy())
    assert result.diagnostic.reason == "NONFINITE"


def test_actual_output_cap_with_json_escaping():
    req = request()
    original = req.artifact_references[0]
    # Input is within 65536 UTF-8 bytes, but JSON control escapes expand sixfold.
    extras = tuple(replace(original,reference_id=f"extra{i}",locator="\x01"*480) for i in range(110))
    req = replace(req,artifact_references=(original,)+extras)
    assert _text_bytes(req)+_text_bytes(policy()) < 65536
    result = reg.fit_rigid_registration(req,policy())
    assert result.diagnostic.reason == "OUTPUT_LIMIT"
    assert not hasattr(result,"request")


@pytest.mark.parametrize("count,success",[(8,True),(9,False)])
def test_per_record_reference_limit(count,success):
    req = request()
    d = replace(req.fit_declarations[0],provenance_reference_ids=("artifact",)*count)
    req = replace(req,fit_declarations=(d,req.fit_declarations[1]))
    assert isinstance(reg.fit_rigid_registration(req,policy()),reg.RegistrationDraft) is success


@pytest.mark.parametrize("count,success",[(16,True),(17,False)])
def test_evidence_record_limit(count,success):
    req = request()
    records = tuple(reg.IndependentValidationEvidence(f"e{i:02}",reg.EvidenceKind.SIDE_PARITY,"issuer",req.context,
        "P","M",("calibration",),("fit-measurements",),(),(),("artifact",),"declared",reg.EvidenceState.DECLARED_UNVERIFIED)
        for i in range(count))
    assert isinstance(reg.fit_rigid_registration(replace(req,independent_evidence=records),policy()),reg.RegistrationDraft) is success


def test_maximum_fit_and_checkpoint_collections_together():
    source = tuple((float(i),float(i%3)) for i in range(64))
    checkpoints = tuple((float(i),10.) for i in range(32))
    req = request(source,checkpoints=checkpoints,checkpoint_target=tuple((x+5,y+7) for x,y in checkpoints))
    result = reg.fit_rigid_registration(req,policy())
    assert isinstance(result,reg.RegistrationDraft)
    assert len(result.fit.records)+len(result.checkpoints.records) == 96


def test_result_snapshot_detached_from_caller_records():
    req = request()
    result = reg.fit_rigid_registration(req,policy())
    object.__setattr__(req.fit_declarations[0].position,"x",900.)
    object.__setattr__(req.context,"load_id","another-load")
    assert result.request.fit_declarations[0].position.x == 0.
    assert result.request.context.load_id == "load"
