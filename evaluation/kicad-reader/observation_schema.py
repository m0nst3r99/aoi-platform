"""Existing evaluation v2 schema, shared without executing the entrypoint."""
import math
from uuid import UUID

def schema(data, *, allow_legacy=False):
    """Require the full observation protocol, including fields not used by oracles."""
    def fields(row, declarations):
        for name, kind in declarations.items():
            if type(row[name]) is not kind:
                raise ValueError(f"{name}: expected {kind.__name__}")
    def point(value):
        if type(value) is not list or len(value) != 2 or not all(type(n) in (int, float) and math.isfinite(n) for n in value):
            raise ValueError("finite 2D point required")
    def identity(row):
        UUID(row['uuid'])
    fields(data, dict(build=str, input_sha256=str, format_version=int, footprints=list, edges=list, outline=dict))
    fields(data['outline'], dict(valid=bool, count=int, holes=list, origin_mm=list, size_mm=list))
    point(data['outline']['origin_mm'])
    point(data['outline']['size_mm'])
    for f in data['footprints']:
        fields(f, dict(uuid=str, reference=str, value=str, footprint=str, position_mm=list,
                       layer=str, attributes=int, dnp=bool, exclude_from_bom=bool,
                       exclude_from_position=bool, pads=list))
        identity(f)
        point(f['position_mm'])
        point([f['angle_deg'], 0])
        for pad in f['pads']:
            fields(pad, dict(uuid=str, number=str, shape=int, attribute=int, layers=list, net=str))
            identity(pad)
            for key in ('position_mm', 'local_mm', 'size_mm', 'drill_mm'):
                point(pad[key])
            point([pad['angle_deg'], 0])
            if not all(type(n) is str for n in pad['layers']):
                raise ValueError('layer names required')
    for edge in data['edges']:
        fields(edge, dict(uuid=str, shape=int))
        identity(edge)
        point(edge['start_mm'])
        point(edge['end_mm'])
        if edge['shape'] == 2:
            point(edge['mid_mm'])
            point(edge['center_mm'])
            point([edge['radius_mm'], 0])
    if "protocol_version" not in data:
        if not allow_legacy or "footprint_edges" in data or "geometry_coverage" in data:
            raise ValueError("Unversioned protocol requires explicit historical replay")
        return True  # Legacy has UNKNOWN footprint Edge.Cuts coverage, never known-empty.
    if type(data["protocol_version"]) is not int or data["protocol_version"] != 2:
        raise ValueError("Unsupported observation protocol")
    fields(data, dict(footprint_edges=list, geometry_coverage=dict))
    coverage = data["geometry_coverage"]
    if (coverage.get("board_edges_scope") != "board-drawings-only"
            or coverage.get("footprint_edges_scope") != "footprint-graphical-items-only"
            or coverage.get("geometry_complete") is not False):
        raise ValueError("Incomplete or incorrect geometry coverage metadata")
    parents = [f["uuid"] for f in data["footprints"]]
    if len(parents) != len(set(parents)):
        raise ValueError("Duplicate footprint UUID")
    seen = {edge["uuid"] for edge in data["edges"]} | set(parents)
    for edge in data["footprint_edges"]:
        fields(edge, dict(uuid=str, parent_footprint_uuid=str, shape=int,
                          primitive_type=str, layer=str, source_accessor=str,
                          coordinate_space=str, endpoint_accessor=str,
                          api_start_mm=list, api_end_mm=list))
        identity(edge)
        UUID(edge["parent_footprint_uuid"])
        if edge["uuid"] in seen or edge["parent_footprint_uuid"] not in parents:
            raise ValueError("Duplicate item UUID or unknown parent")
        seen.add(edge["uuid"])
        expected_type = "segment" if edge["shape"] == 0 else "native-shape-" + str(edge["shape"])
        if (edge["primitive_type"] != expected_type or edge["layer"] != "Edge.Cuts"
                or edge["source_accessor"] != "FOOTPRINT.GraphicalItems"
                or edge["coordinate_space"] != "native-api-unclassified"
                or edge["endpoint_accessor"] != "PCB_SHAPE.GetStart/GetEnd"):
            raise ValueError("Incorrect footprint edge metadata")
        point(edge["api_start_mm"])
        point(edge["api_end_mm"])
    return True

