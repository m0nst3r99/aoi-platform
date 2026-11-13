"""Exercise probe control flow; fake accessors do not implement KiCad geometry."""
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace as NS

import pytest

PROBE = Path(__file__).with_name('probe.py')
EDGE = 25


def identity(n):
    return f'00000000-0000-0000-0000-{n:012x}'


def vector(x, y):
    return NS(x=x, y=y)


class Shape:
    def __init__(self, uid, parent, start, end):
        self.m_Uuid = NS(AsString=lambda: identity(uid))
        self.GetParentFootprint = lambda: parent
        self.GetLayer = lambda: EDGE
        self.GetShape = lambda: 0
        self.GetStart = lambda: vector(*start)
        self.GetEnd = lambda: vector(*end)


def footprint(uid):
    items = []
    # Constant accessor stubs only: no pads, transforms or geometry algorithms.
    return NS(items=items, m_Uuid=NS(AsString=lambda: identity(uid)),
              GraphicalItems=lambda: items, Pads=lambda: [],
              GetReference=lambda: f'FP{uid}', GetValue=lambda: 'fake',
              GetFPID=lambda: NS(GetUniStringLibId=lambda: 'Fake:Fixture'),
              GetPosition=lambda: vector(900, 800), GetOrientationDegrees=lambda: 90,
              GetLayer=lambda: 0, GetAttributes=lambda: 0, IsDNP=lambda: False,
              IsExcludedFromBOM=lambda: False, IsExcludedFromPosFiles=lambda: False)


def execute(monkeypatch, tmp_path, parents, drawings=()):
    box = NS(GetOrigin=lambda: vector(0, 0), GetSize=lambda: vector(0, 0))
    outline = NS(BBox=lambda: box, OutlineCount=lambda: 0)
    board = NS(GetFootprints=lambda: parents, GetDrawings=lambda: drawings,
               GetLayerName=lambda n: 'Edge.Cuts' if n == EDGE else 'F.Cu',
               GetBoardPolygonOutlines=lambda *args: False,
               GetFileFormatVersionAtLoad=lambda: 20240108)
    fake = NS(PCB_SHAPE=Shape, Edge_Cuts=EDGE, SHAPE_T_SEGMENT=0, SHAPE_T_ARC=2,
              ToMM=lambda n: n / 1000000, LoadBoard=lambda path: board,
              SHAPE_POLY_SET=lambda: outline, GetBuildVersion=lambda: 'fake-only')
    source = tmp_path / 'stub-input'
    source.write_bytes(b'opaque test bytes; fake LoadBoard does not parse')
    monkeypatch.setitem(sys.modules, 'pcbnew', fake)
    monkeypatch.setattr(sys, 'argv', [str(PROBE), str(source)])
    runpy.run_path(str(PROBE), run_name='__main__')


def test_empty_local_collection_is_incomplete(monkeypatch, tmp_path, capsys):
    execute(monkeypatch, tmp_path, [footprint(1)])
    data = json.loads(capsys.readouterr().out)
    assert data['footprint_edges'] == []
    assert data['geometry_coverage']['geometry_complete'] is False
    assert data['geometry_coverage']['footprint_edges_scope'] == 'footprint-graphical-items-only'


def test_two_parents_separate_edges_and_raw_endpoints(monkeypatch, tmp_path, capsys):
    first, second = footprint(1), footprint(2)
    first.items.append(Shape(11, first, (1250000, -2500000), (3750000, 4250000)))
    second.items.append(Shape(12, second, (-7250000, 8500000), (9250000, -10500000)))
    # Deliberately has no shape/parent/endpoint accessors: must skip by layer first.
    first.items.append(NS(GetLayer=lambda: 0))
    board_edge = Shape(20, None, (0, 0), (1000000, 0))
    execute(monkeypatch, tmp_path, [second, first], [board_edge])
    data = json.loads(capsys.readouterr().out)
    expected = []
    for uid, parent, start, end in [(11, 1, [1.25, -2.5], [3.75, 4.25]),
                                   (12, 2, [-7.25, 8.5], [9.25, -10.5])]:
        expected.append(dict(uuid=identity(uid), parent_footprint_uuid=identity(parent),
            shape=0, primitive_type='segment', layer='Edge.Cuts',
            source_accessor='FOOTPRINT.GraphicalItems', coordinate_space='native-api-unclassified',
            endpoint_accessor='PCB_SHAPE.GetStart/GetEnd', api_start_mm=start, api_end_mm=end))
    assert data['footprint_edges'] == expected
    assert data['edges'] == [dict(uuid=identity(20), shape=0, start_mm=[0, 0], end_mm=[1, 0])]
    assert data['geometry_coverage']['geometry_complete'] is False


@pytest.mark.parametrize('case,message', [
    ('not_shape', 'Unsupported footprint Edge.Cuts graphical item type'),
    ('no_parent', 'Footprint Edge.Cuts parent mismatch'),
    ('wrong_parent', 'Footprint Edge.Cuts parent mismatch'),
])
def test_invalid_local_item_fails_without_observation(case, message, monkeypatch, tmp_path, capsys):
    parent = footprint(1)
    if case == 'not_shape':
        item = NS(GetLayer=lambda: EDGE)
    else:
        item = Shape(11, None if case == 'no_parent' else footprint(2), (1, 2), (3, 4))
    parent.items.append(item)
    with pytest.raises(RuntimeError, match=message):
        execute(monkeypatch, tmp_path, [parent])
    captured = capsys.readouterr()
    assert captured.out == ''  # No partial or success-shaped JSON observation.
    assert 'loaded' in captured.err


def test_nonsegment_local_item_matches_schema(monkeypatch, tmp_path, capsys):
    parent = footprint(1)
    item = Shape(13, parent, (-1250000, 2750000), (4500000, -6250000))
    item.GetShape = lambda: 2  # Same enum as fake pcbnew.SHAPE_T_ARC; no arc algorithm.
    parent.items.append(item)
    execute(monkeypatch, tmp_path, [parent])
    data = json.loads(capsys.readouterr().out)
    assert data['footprint_edges'] == [dict(
        uuid=identity(13), parent_footprint_uuid=identity(1), shape=2,
        primitive_type='native-shape-2', layer='Edge.Cuts',
        source_accessor='FOOTPRINT.GraphicalItems',
        coordinate_space='native-api-unclassified',
        endpoint_accessor='PCB_SHAPE.GetStart/GetEnd',
        api_start_mm=[-1.25, 2.75], api_end_mm=[4.5, -6.25])]
    assert data['geometry_coverage']['geometry_complete'] is False
    # Validate the actual probe payload, not a separately assembled schema fixture.
    schema = runpy.run_path(str(PROBE.with_name('run.py')))['schema']
    assert schema(data) is True
