"""Report evidence, independent of future file parsers and graph policies."""

from dataclasses import FrozenInstanceError, replace
from itertools import permutations
import json

import pytest

from aoi_platform.geometry import (
    ContractError, ErrorCode, GeometryError, Point2, ReportStatus, Severity,
    SourceLocation, ValidationReport,
)


def issue(**changes):
    values = dict(code=ErrorCode.SCHEMA_INVALID, message="Invalid numeric cell",
                  field_path="placement.x", remediation="Supply a finite coordinate.",
                  artifact_id="placement-1", entity_id="R1",
                  source_location=SourceLocation("placement.csv", 2, 3),
                  expected="finite number", actual="NaN",
                  context=(("machine_id", "m1"), ("board_revision_id", "rev1"),
                           ("capture_id", "capture1"), ("transform_id", "t1")))
    values.update(changes)
    return ContractError(**values)


def report(issues, **changes):
    values = dict(report_id="report-1", policy_id="synthetic-geometry-v1",
                  issues=tuple(issues), checks=(("numeric", "failed"),))
    values.update(changes)
    return ValidationReport(**values)


def test_all_discoverable_numeric_failures_keep_source_and_context(mm_frame):
    discovered = []
    for row, value in ((2, float("nan")), (10, float("inf"))):
        try:
            Point2(value, 0, mm_frame)
        except GeometryError as error:
            discovered.append(ContractError.from_geometry_error(
                error, remediation="Correct this numeric cell.", artifact_id="placement",
                entity_id=f"row-{row}", source_location=SourceLocation("input.csv", row, 3),
                context=(("board_revision_id", "rev1"), ("machine_id", "m1"))))
    result = report(discovered)
    assert result.status is ReportStatus.REJECTED
    assert len(result.errors) == 2
    assert {e.source_location.row for e in result.errors} == {2, 10}
    assert {e.entity_id for e in result.errors} == {"row-2", "row-10"}
    assert all(dict(e.context) == {"board_revision_id": "rev1", "machine_id": "m1"}
               and e.field_path == "point.x" for e in result.errors)


def test_order_and_serialization_are_independent_of_discovery_and_ties():
    # Expected order is literal: actual text is the first differing canonical key.
    cases = [issue(actual="B"), issue(actual="A"), issue(actual="A", entity_id="R2")]
    outputs = {report(order).to_json() for order in permutations(cases)}
    assert len(outputs) == 1
    payload = json.loads(outputs.pop())
    assert [(e["actual"], e["entity_id"]) for e in payload["errors"]] == [
        ("A", "R1"), ("A", "R2"), ("B", "R1")]
    assert payload["errors"][0]["source_location"] == {
        "source": "placement.csv", "row": 2, "column": 3}
    assert payload["errors"][0]["context"]["transform_id"] == "t1"
    assert len(report([cases[0], cases[0]]).errors) == 2
    assert report(cases, context=(("z", "2"), ("a", "1"))).to_json() == report(
        cases, context=(("a", "1"), ("z", "2"))).to_json()


def test_warning_cannot_downgrade_a_gate_or_expose_rejected_digest():
    warning = issue(code=ErrorCode.OPTIONAL_DATA_ABSENT, severity=Severity.WARNING)
    assert report([warning], checks=()).status is ReportStatus.ACCEPTED
    mixed = report([warning, issue()])
    assert mixed.status is ReportStatus.REJECTED
    assert len(mixed.errors) == len(mixed.warnings) == 1
    with pytest.raises(GeometryError):
        issue(severity=Severity.WARNING)
    with pytest.raises(GeometryError):
        report([issue()], canonical_digest="not-published")


def test_report_retains_optional_evidence_and_is_immutable():
    result = report([issue()], unresolved_fields=("origin",), conflicting_fields=("units",),
                    artifact_digests=(("placement-1", "abc"),))
    payload = result.to_dict()
    assert payload["unresolved_fields"] == ["origin"]
    assert payload["conflicting_fields"] == ["units"]
    assert payload["artifact_digests"] == {"placement-1": "abc"}
    payload["errors"].clear()
    assert len(result.errors) == 1
    with pytest.raises(FrozenInstanceError):
        result.issues = ()


@pytest.mark.parametrize("changes", [
    {"context": [("machine_id", "m1")]},
    {"context": (("machine_id", "m1"), ("machine_id", "m2"))},
    {"source_location": "input:2"}, {"code": "SCHEMA_INVALID"},
    {"artifact_id": ""}, {"actual": {}}, {"remediation": ""},
])
def test_invalid_issue_metadata_is_rejected(changes):
    with pytest.raises(GeometryError):
        issue(**changes)


@pytest.mark.parametrize("row", [0, -1, True, 1.5])
def test_source_location_requires_one_based_integer(row):
    with pytest.raises(GeometryError):
        SourceLocation("input.csv", row)


def test_reports_reject_mutable_collections_and_invalid_evidence():
    result = report([issue()])
    for changes in ({"issues": []}, {"issues": ("error",)}, {"checks": (("", "pass"),)},
                    {"unresolved_fields": []}, {"policy_id": ""}):
        with pytest.raises(GeometryError):
            replace(result, **changes)
