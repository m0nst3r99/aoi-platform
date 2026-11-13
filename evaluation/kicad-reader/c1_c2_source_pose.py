"""Four pinned pads: source-decimal pose, not effective copper geometry.

P is explicitly the existing normalized native-board datum, translation (0,0).
K rotates local center by footprint angle ONCE; pad angle is world orientation.
Numeric work is bounded before Decimal construction; existing candidate magnitude
bounds are retained. No trigonometric floats or observation-generated expecteds.
"""
from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
import re
from aoi_platform.geometry.errors import ErrorCode, diagnostic_json

TOLERANCE = Decimal('0.000001')
CORRESPONDENCE = (3, 2, 1, 0)
NUMBER = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\Z')


@dataclass(frozen=True)
class SourcePose:
    footprint_at: tuple
    pad_at: tuple
    size: tuple
    world_center: tuple
    p_center: tuple
    p_vertices: tuple
    correspondence: tuple = CORRESPONDENCE


class PoseError(ValueError):
    def __init__(self, field, expected, actual):
        self.field, self.expected, self.actual = field, expected, actual


def _values(fields, count, name):
    if len(fields) != 1:
        raise PoseError(name, 'exactly one direct field', len(fields))
    literals, span, lines, nested = fields[0]
    if nested or len(literals) != count:
        raise PoseError(name, f'{count} numeric literals, no children', 'invalid field structure')
    values = []
    for literal in literals:
        if len(literal) > 64 or not NUMBER.fullmatch(literal):
            raise PoseError(name, 'bounded finite decimal literal (no exponent)', literal[:64])
        value = Decimal(literal)
        if abs(value) > Decimal('1000000'):
            raise PoseError(name, 'absolute value <= 1000000', literal)
        values.append(value)
    if count == 3 and (abs(values[2]) > 360000 or values[2] % 90):
        raise PoseError(name, 'cardinal angle within +/-360000 degrees', literals[2])
    if count == 2 and any(v <= 0 for v in values):
        raise PoseError(name, 'positive size', literals)
    return tuple(values)


def _rotate(x, y, angle):
    quadrant = int(angle / 90) % 4
    return ((x,y), (y,-x), (-x,-y), (-y,x))[quadrant]


def source_pose(record):
    with localcontext() as context:
        context.prec = 160  # bounded 64-character literals; cardinal arithmetic exact
        f = _values(record.footprint_at, 3, 'footprint.at')
        p = _values(record.pad_at, 3, 'pad.at')
        size = _values(record.pad_size, 2, 'pad.size')
        dx,dy = _rotate(p[0],p[1],f[2])
        center = (f[0]+dx,f[1]+dy)
        a,b = size[0]/2,size[1]/2
        vertices = []
        for x,y in ((-a,-b),(a,-b),(a,b),(-a,b)):
            x,y = _rotate(x,y,p[2])
            vertices.append((center[0]+x,-(center[1]+y)))
        return SourcePose(f,p,size,center,(center[0],-center[1]),tuple(vertices))


def check_pose(record, pad, footprint, observation):
    # Local import avoids reexecuting entrypoints or a module import cycle.
    from c1_c2_source_membership import _failure
    try:
        pose = source_pose(record)
        comparisons = (
            ('request.center.x', pose.p_center[0], pad.rectangle.center.x),
            ('request.center.y', pose.p_center[1], pad.rectangle.center.y),
            ('request.width', pose.size[0], pad.rectangle.width),
            ('request.height', pose.size[1], pad.rectangle.height),
            ('request.angle', pose.pad_at[2], pad.rectangle.angle_deg),
            ('observation.footprint.x',pose.footprint_at[0],footprint['position_mm'][0]),
            ('observation.footprint.y',pose.footprint_at[1],footprint['position_mm'][1]),
            ('observation.footprint.angle',pose.footprint_at[2],footprint['angle_deg']),
            ('observation.local.x',pose.pad_at[0],observation['local_mm'][0]),
            ('observation.local.y',pose.pad_at[1],observation['local_mm'][1]),
            ('observation.center.x',pose.world_center[0],observation['position_mm'][0]),
            ('observation.center.y',pose.world_center[1],observation['position_mm'][1]),
            ('observation.width',pose.size[0],observation['size_mm'][0]),
            ('observation.height',pose.size[1],observation['size_mm'][1]),
            ('observation.angle',pose.pad_at[2],observation['angle_deg']),
        )
        for name, expected, actual in comparisons:
            if type(actual) not in (int,float):
                raise PoseError(name,str(expected),'invalid numeric type')
            value = Decimal(str(actual))
            tolerance = Decimal(0) if name.endswith('angle') else TOLERANCE
            if not value.is_finite() or abs(value-expected) > tolerance:
                raise PoseError(name,str(expected),str(actual))
    except PoseError as error:
        result = _failure(error.field,error.expected,error.actual,record,ErrorCode.SOURCE_CONFLICT)
        spans = tuple((name, tuple(field[1] for field in fields)) for name,fields in (
            ('footprint.at',record.footprint_at),('pad.at',record.pad_at),('pad.size',record.pad_size)))
        return replace(result,diagnostic=replace(result.diagnostic,
            context=result.diagnostic.context+(('pose_field_spans',diagnostic_json(spans)),)))
    return None
