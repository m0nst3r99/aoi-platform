"""Portable v2 protocol checks. Historical observation bytes are never edited."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("reader_schema", HERE / "run.py")
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)

COVERAGE = {
    "board_edges_scope": "board-drawings-only",
    "footprint_edges_scope": "footprint-graphical-items-only",
    "geometry_complete": False,
}


def payload(with_item=False):
    data = json.loads((HERE / "pcbnew.stdout.txt").read_bytes())
    data.update(protocol_version=2, footprint_edges=[], geometry_coverage=copy.deepcopy(COVERAGE))
    if with_item:
        data["footprint_edges"].append(dict(
            uuid="90000000-0000-0000-0000-000000000001",
            parent_footprint_uuid=data["footprints"][0]["uuid"],
            shape=0, primitive_type="segment", layer="Edge.Cuts",
            source_accessor="FOOTPRINT.GraphicalItems",
            coordinate_space="native-api-unclassified",
            endpoint_accessor="PCB_SHAPE.GetStart/GetEnd",
            api_start_mm=[11, 7], api_end_mm=[14, 9],
        ))
    return data


def test_v2_no_footprint_edges_is_explicit():
    assert harness.schema(payload())


def test_v2_detected_item_metadata():
    assert harness.schema(payload(True))


@pytest.mark.parametrize("field", [
    "uuid", "parent_footprint_uuid", "shape", "primitive_type", "layer",
    "source_accessor", "coordinate_space", "endpoint_accessor", "api_start_mm", "api_end_mm",
])
def test_v2_missing_item_metadata_rejected(field):
    data = payload(True)
    del data["footprint_edges"][0][field]
    with pytest.raises((ValueError, KeyError, TypeError)):
        harness.schema(data)


@pytest.mark.parametrize("field,value", [
    ("uuid", "bad-uuid"), ("parent_footprint_uuid", "90000000-0000-0000-0000-000000000002"),
    ("shape", True), ("primitive_type", "arc"), ("layer", "F.Cu"),
    ("source_accessor", "BOARD.GetDrawings"), ("coordinate_space", "file-local"),
    ("endpoint_accessor", "guessed"), ("api_start_mm", [float("nan"), 0]),
])
def test_v2_incorrect_item_metadata_rejected(field, value):
    data = payload(True)
    data["footprint_edges"][0][field] = value
    with pytest.raises((ValueError, KeyError, TypeError)):
        harness.schema(data)


@pytest.mark.parametrize("mutation", [
    lambda d: d.pop("footprint_edges"),
    lambda d: d.pop("geometry_coverage"),
    lambda d: d.update(protocol_version=3),
    lambda d: d.update(protocol_version=True),
    lambda d: d["geometry_coverage"].update(geometry_complete=True),
    lambda d: d["footprint_edges"].append(copy.deepcopy(d["footprint_edges"][0])),
    lambda d: d["footprint_edges"][0].update(uuid=d["edges"][0]["uuid"]),
])
def test_v2_coverage_version_and_duplicate_rejection(mutation):
    data = payload(True)
    mutation(data)
    with pytest.raises((ValueError, KeyError, TypeError)):
        harness.schema(data)


def test_legacy_requires_explicit_replay_opt_in():
    old = json.loads((HERE / "pcbnew.stdout.txt").read_bytes())
    with pytest.raises(ValueError):
        harness.schema(old)
    assert harness.schema(old, allow_legacy=True)


def test_cannot_strip_version_to_downgrade():
    data = payload()
    del data["protocol_version"]
    with pytest.raises(ValueError):
        harness.schema(data, allow_legacy=True)
