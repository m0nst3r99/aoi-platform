"""Pinned r2 source membership only; no KiCad geometry or completeness claim.

The private scanner accepts synthetic bytes for lexical tests. Only scan_pinned
admits real source. Token length includes quotes/escapes; parentheses count as
tokens. UTF-8 quoted escapes supported: quote, backslash, n, r, t. Other escapes,
comments, control characters and malformed list syntax fail explicitly.
Spans are zero-based half-open byte offsets; lines are one-based (LF counted).
"""
from dataclasses import dataclass, field
from hashlib import sha256
from uuid import UUID
import json

import c1_c2_artifact_binding as artifacts
from aoi_platform.geometry.errors import ErrorCode, diagnostic_json
from aoi_platform.geometry.reports import ContractError

MAX_DEPTH = 128
MAX_TOKEN = 65536
MAX_TOKENS = 500000
PCB_HASH = '67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0'
PCB_SIZE = 912379
PAIRS = tuple((c.PARENT, u) for _, c in artifacts.profile.GROUPS for u in sorted(c.PADS))

# Explicit declaration screen, NOT a complete KiCad construct grammar. Paths
# start at a pad directly under a board-level footprint. Presence alone blocks;
# no effective/default values are inferred. model/offset and zone_connect are
# deliberately excluded. Only the first occurrence span per path is retained;
# occurrence counts and all traversal remain bounded by the token budget.
MODIFIER_PATHS = (
    ('pad', 'drill'), ('pad', 'offset'), ('pad', 'drill', 'offset'),
    ('pad', 'padstack'), ('pad', 'padstack', 'layer'), ('pad', 'layer'),
    ('pad', 'primitives'), ('pad', 'options'),
)

# Selected-pad coverage only. Supported paths are leaves: no descendant is
# implicitly admitted. uuid/at/size/layers keep their existing semantic guards.
# net/pintype/zone_connect: optional, at most once, exactly one atom/string;
# values are retained without interpreting electrical or zone-fill semantics.
PAD_LEAVES = ('uuid', 'at', 'size', 'layers', 'net', 'pintype', 'zone_connect')
PRESENCE_ONLY = ('net', 'pintype', 'zone_connect')

# Exact relative paths outside direct pads; no prefix/wildcard admission.
# This table classifies declarations, not effective geometry or text/model semantics.
FOOTPRINT_PATHS = {
    **{(n,): 'existing-semantic-gate' for n in ('uuid','at','layer','attr')},
    **{(n,): 'metadata' for n in ('descr','path','sheetname','sheetfile',
                                'embedded_fonts','duplicate_pad_numbers_are_jumpers')},
    ('property',): 'metadata',
    **{('property',n): 'graphics/text' for n in ('at','layer','uuid','unlocked','hide','effects')},
    ('property','effects','font'): 'graphics/text',
    **{('property','effects','font',n): 'graphics/text' for n in ('size','thickness')},
    **{(kind,): 'graphics/text' for kind in ('fp_line','fp_circle')},
    **{('fp_line',n): 'graphics/text' for n in ('start','end','stroke','layer','uuid')},
    **{('fp_circle',n): 'graphics/text' for n in ('center','end','stroke','fill','layer','uuid')},
    **{(kind,'stroke',n): 'graphics/text'
       for kind in ('fp_line','fp_circle') for n in ('width','type')},
    ('model',): 'model-3d',
    **{('model',n): 'model-3d' for n in ('offset','scale','rotate')},
    **{('model',n,'xyz'): 'model-3d' for n in ('offset','scale','rotate')},
}


@dataclass(frozen=True)
class FootprintNodeDeclaration:
    path: tuple[str, ...]
    values: tuple[str, ...]
    span: tuple[int, int]
    lines: tuple[int, int]
    category: str
    semantics: str
    graphics_layer_values: tuple[str, ...] | None


@dataclass(frozen=True)
class PadNodeDeclaration:
    path: tuple[str, ...]
    values: tuple[str, ...]
    span: tuple[int, int]
    lines: tuple[int, int]
    has_children: bool
    coverage: str


@dataclass(frozen=True)
class ModifierDeclaration:
    path: tuple[str, ...]
    status: str
    first_span: tuple[int, int] | None
    first_lines: tuple[int, int] | None
    occurrences: int


@dataclass(frozen=True)
class FootprintField:
    name: str
    values: tuple[str, ...]
    literal: bytes
    span: tuple[int, int]
    lines: tuple[int, int]
    has_children: bool


@dataclass(frozen=True)
class SourceRecord:
    parent_uuid: str
    pad_uuid: str
    number: str
    pad_type: str
    shape: str
    layers: tuple[str, ...]
    span: tuple[int, int]
    lines: tuple[int, int]
    modifiers: tuple[ModifierDeclaration, ...]
    footprint_at: tuple = ()
    pad_at: tuple = ()
    pad_size: tuple = ()
    nodes: tuple[PadNodeDeclaration, ...] = ()
    footprint_fields: tuple[FootprintField, ...] = ()
    footprint_nodes: tuple[FootprintNodeDeclaration, ...] = ()


@dataclass(frozen=True)
class SourceFailure:
    diagnostic: ContractError
    modifier_records: tuple[SourceRecord, ...] = ()  # diagnostic evidence, never candidates


@dataclass(frozen=True)
class SourceSuccess:
    records: tuple[SourceRecord, ...]
    artifact_result: artifacts.ArtifactBindingSuccess
    status: str = field(default='four-pad-source-membership-and-explicit-fields-checked', init=False)
    completeness: str = field(default='not-verified', init=False)
    effective_copper_geometry: str = field(default='not-verified', init=False)


class ScanError(ValueError):
    def __init__(self, reason, offset, line, code=ErrorCode.SCHEMA_INVALID):
        super().__init__(reason)
        self.reason, self.offset, self.line, self.code = reason, offset, line, code


def _tokens(data):
    i = 0
    line = 1
    count = 0
    while i < len(data):
        b = data[i]
        if b in b' \t\r\n':
            line += b == 10
            i += 1
            continue
        start, first_line = i, line
        count += 1
        if count > MAX_TOKENS:
            raise ScanError('token-count limit', i, line, ErrorCode.INPUT_LIMIT_EXCEEDED)
        if b in b'()':
            i += 1
            yield chr(b), '', start, i, first_line, line
            continue
        quoted = b == 34
        value = bytearray()
        if quoted:
            i += 1
        while i < len(data):
            b = data[i]
            if not quoted and b in b'() \t\r\n':
                break
            if i - start >= MAX_TOKEN:
                raise ScanError('token-byte limit', start, first_line, ErrorCode.INPUT_LIMIT_EXCEEDED)
            if quoted and b == 34:
                i += 1
                break
            if b < 32 or b == 127 or (not quoted and b in b'";\\'):
                raise ScanError('unsupported character', i, line)
            if quoted and b == 92:
                i += 1
                if i >= len(data) or data[i] not in b'"\\nrt':
                    raise ScanError('unsupported escape', i, line)
                value.extend({34:b'"',92:b'\\',110:b'\n',114:b'\r',116:b'\t'}[data[i]])
            else:
                value.append(b)
            i += 1
        else:
            if quoted:
                raise ScanError('unterminated string', start, first_line)
        if i - start > MAX_TOKEN:
            raise ScanError('token-byte limit', start, first_line, ErrorCode.INPUT_LIMIT_EXCEEDED)
        if i < len(data) and data[i] not in b'() \t\r\n':
            raise ScanError('missing token separator', i, line)
        try:
            text = value.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            raise ScanError('invalid UTF-8', start, first_line) from None
        yield 'string' if quoted else 'atom', text, start, i, first_line, line


@dataclass
class _Node:
    start: int
    line: int
    head: str = ''
    atoms: list = field(default_factory=list)
    children_started: bool = False
    uuid: str | None = None
    layers: tuple | None = None
    selected: list = field(default_factory=list)
    modifiers: dict = field(default_factory=dict)
    numeric_fields: dict = field(default_factory=dict)
    quoted_atoms: bool = False
    pad_nodes: list = field(default_factory=list)
    deferred_structure_error: tuple | None = None
    footprint_fields: dict = field(default_factory=dict)
    footprint_nodes: list = field(default_factory=list)


def _scan(data, charge=None):
    """Bounded iterative lexical/structural scanner, not a general KiCad decoder.

    No AST: retain stack, footprint/pad UUID identities and selected pad records.
    One shared uniqueness set covers direct board footprints and their direct
    pads, including nonselected entities. Other UUID-bearing nodes are outside
    this uniqueness namespace, but still undergo syntax/UUID-field validation.
    Token count bounds work/storage, including nonselected UUIDs/field atoms.
    """
    def make(cls, *args):
        if charge is not None:
            charge(args)  # before retaining reconstructed metadata
        return cls(*args)
    stack, records, seen = [], [], set()
    root_closed = False
    wanted = {u for _, u in PAIRS}
    for kind, value, start, end, line, end_line in _tokens(data):
        if kind == '(':
            if root_closed or (stack and not stack[-1].head):
                raise ScanError('unexpected list', start, line)
            if len(stack) >= MAX_DEPTH:
                raise ScanError('depth limit', start, line, ErrorCode.INPUT_LIMIT_EXCEEDED)
            if stack:
                stack[-1].children_started = True
            stack.append(_Node(start, line))
        elif kind == ')':
            if not stack or not stack[-1].head:
                raise ScanError('unexpected close or empty list', start, line)
            node = stack.pop()
            parent = stack[-1] if stack else None
            if (len(stack) >= 2 and stack[0].head == 'kicad_pcb'
                    and stack[1].head == 'footprint'
                    and (len(stack) == 2 and node.head != 'pad'
                         or len(stack) > 2 and stack[2].head != 'pad')):
                relative = tuple(n.head for n in stack[2:]) + (node.head,)
                category = FOOTPRINT_PATHS.get(relative, 'unclassified')
                stack[1].footprint_nodes.append(make(FootprintNodeDeclaration, 
                    ('kicad_pcb','footprint') + relative, tuple(node.atoms),
                    (node.start,end), (node.line,end_line), category,
                    'existing-semantic-gate' if category == 'existing-semantic-gate'
                    else 'semantics-unchecked',
                    tuple(node.atoms) if category == 'graphics/text' and node.head == 'layer' else None))
            if (len(stack) == 2 and stack[0].head == 'kicad_pcb'
                    and parent.head == 'footprint' and node.head in ('layer', 'attr')):
                fields = parent.footprint_fields.setdefault(node.head, [])
                # Two retained occurrences suffice to reject duplicates. Raw
                # literals remain bounded by the input/token budgets.
                if len(fields) < 2:
                    fields.append(make(FootprintField, node.head, tuple(node.atoms),
                        data[node.start:end], (node.start,end), (node.line,end_line),
                        node.children_started))
            if parent is not None and (
                (len(stack) == 2 and stack[0].head == 'kicad_pcb'
                 and parent.head == 'footprint' and node.head == 'at') or
                (len(stack) == 3 and stack[0].head == 'kicad_pcb'
                 and stack[1].head == 'footprint' and parent.head == 'pad'
                 and node.head in ('at', 'size'))
            ):
                # Keep at most two occurrences: enough to reject duplicates.
                fields = parent.numeric_fields.setdefault(node.head, [])
                if len(fields) < 2:
                    fields.append((tuple(node.atoms), (node.start, end),
                                   (node.line, end_line), node.children_started or node.quoted_atoms))
            if (len(stack) >= 3 and stack[0].head == 'kicad_pcb'
                    and stack[1].head == 'footprint' and stack[2].head == 'pad'):
                path = tuple(n.head for n in stack[2:]) + (node.head,)
                coverage = ('semantics-unchecked' if path == ('pad', node.head)
                            and node.head in PRESENCE_ONLY else
                            'existing-semantic-gate' if path == ('pad', node.head)
                            and node.head in PAD_LEAVES else
                            'presence-blocked' if path in MODIFIER_PATHS else 'unclassified')
                # Token/depth limits bound retained nodes, values and path length.
                # UUID may occur last: collect until ownership is known, then
                # retain only selected records. Every descendant is represented.
                stack[2].pad_nodes.append(make(PadNodeDeclaration, path, tuple(node.atoms),
                    (node.start, end), (node.line, end_line), node.children_started, coverage))
                if path in MODIFIER_PATHS:
                    owner = stack[2]
                    previous = owner.modifiers.get(path)
                    owner.modifiers[path] = make(ModifierDeclaration, path, 'present',
                        previous.first_span if previous else (node.start, end),
                        previous.first_lines if previous else (node.line, end_line),
                        previous.occurrences + 1 if previous else 1)
            if node.head == 'uuid':
                direct_pad = (len(stack) == 3 and stack[0].head == 'kicad_pcb'
                              and stack[1].head == 'footprint' and parent.head == 'pad')
                if parent is None or len(node.atoms) != 1 or (node.children_started and not direct_pad) or parent.uuid is not None:
                    raise ScanError('invalid direct UUID field', start, line)
                if node.children_started:
                    parent.deferred_structure_error = ('invalid direct UUID field', start, line)
                try:
                    identity = UUID(node.atoms[0])
                except ValueError:
                    raise ScanError('invalid UUID', start, line) from None
                in_namespace = (
                    len(stack) == 2 and stack[0].head == 'kicad_pcb' and parent.head == 'footprint'
                ) or (
                    len(stack) == 3 and stack[0].head == 'kicad_pcb'
                    and stack[1].head == 'footprint' and parent.head == 'pad'
                )
                if in_namespace:
                    if identity in seen:
                        raise ScanError('duplicate UUID identity', start, line, ErrorCode.DUPLICATE_ID)
                    seen.add(identity)
                parent.uuid = node.atoms[0]
            if node.head == 'layers' and parent is not None and parent.head == 'pad':
                direct_pad = (len(stack) == 3 and stack[0].head == 'kicad_pcb'
                              and stack[1].head == 'footprint')
                if parent.layers is not None or not node.atoms or (node.children_started and not direct_pad):
                    raise ScanError('invalid direct layers field', start, line)
                if node.children_started:
                    parent.deferred_structure_error = ('invalid direct layers field', start, line)
                parent.layers = tuple(node.atoms)
            if node.head == 'pad' and node.uuid not in wanted and node.deferred_structure_error:
                raise ScanError(*node.deferred_structure_error)
            # For selected pads, descendants under uuid/layers are rejected by
            # exact-path coverage after EOF, with identity and offending span.
            # Nothing here admits nested UUID/layer semantics to the binding flow.
            if node.head == 'pad' and node.uuid in wanted:
                if parent is None or parent.head != 'footprint' or len(stack) != 2 or stack[0].head != 'kicad_pcb':
                    raise ScanError('selected pad is not direct footprint child', node.start, node.line)
                if len(node.atoms) != 3 or node.layers is None:
                    raise ScanError('missing explicit pad fields', node.start, node.line)
                parent.selected.append((node, end, end_line))
            if node.head == 'footprint' and node.selected:
                if node.uuid is None:
                    raise ScanError('missing direct footprint UUID', node.start, node.line)
                for pad, pad_end, pad_line in node.selected:
                    records.append(make(SourceRecord, node.uuid, pad.uuid, *pad.atoms, pad.layers,
                        (pad.start, pad_end), (pad.line, pad_line), tuple(
                            pad.modifiers.get(path, make(ModifierDeclaration, path, 'absent', None, None, 0))
                            for path in MODIFIER_PATHS),
                        tuple(node.numeric_fields.get('at', ())),
                        tuple(pad.numeric_fields.get('at', ())),
                        tuple(pad.numeric_fields.get('size', ())),
                        tuple(sorted(pad.pad_nodes, key=lambda item: item.span)),
                        tuple(f for name in ('layer','attr')
                              for f in node.footprint_fields.get(name, ())),
                        tuple(sorted(node.footprint_nodes, key=lambda item: item.span))))
            if parent is None:
                if node.head != 'kicad_pcb':
                    raise ScanError('root is not kicad_pcb', node.start, node.line)
                root_closed = True
        else:
            if not stack:
                raise ScanError('atom outside root', start, line)
            node = stack[-1]
            if not node.head:
                if kind != 'atom':
                    raise ScanError('quoted list head', start, line)
                node.head = value
            else:
                if node.children_started:
                    raise ScanError('atom after child list unsupported', start, line)
                node.atoms.append(value)
                node.quoted_atoms |= kind == 'string'
    if stack or not root_closed:
        raise ScanError('incomplete root at EOF', len(data), data.count(b'\n') + 1)
    if {(r.parent_uuid, r.pad_uuid) for r in records} != set(PAIRS) or len(records) != 4:
        raise ScanError('missing or conflicting selected membership', len(data), data.count(b'\n') + 1,
                        ErrorCode.SOURCE_CONFLICT)
    return tuple(sorted(records, key=lambda r: (r.parent_uuid, r.pad_uuid)))


def _failure(field, expected, actual, record=None, code=ErrorCode.SOURCE_CONFLICT,
             source_hash=PCB_HASH):
    context = [('artifact_id', 'pcb'), ('source_sha256', source_hash)]
    if record is not None:
        context += [('parent_uuid', record.parent_uuid), ('pad_uuid', record.pad_uuid),
                    ('byte_span', record.span), ('lines', record.lines)]
    def bounded(v):
        if isinstance(v, str) and len(v) > 256:
            return '<value exceeds diagnostic limit>'
        return repr(v)[:1024]
    return SourceFailure(ContractError(code, 'Pinned source membership check failed.', field,
        'Preserve source bytes; inspect declaration and source span.',
        expected=bounded(expected), actual=bounded(actual),
        context=tuple((k, diagnostic_json(v)) for k, v in context)))


def scan_pinned(data):
    if type(data) is not bytes:
        return _failure('pcb.bytes', 'bytes', type(data).__name__)
    if len(data) != PCB_SIZE:
        return _failure('pcb.size', PCB_SIZE, len(data))
    actual = sha256(data).hexdigest()
    if actual != PCB_HASH:
        return _failure('pcb.sha256', PCB_HASH, actual)
    return _scan_checked(data)


def _scan_checked(data, charge=None, verified_digest=None):
    """Private synthetic-test seam; does NOT admit arbitrary bytes to real flow.

    Real callers must use scan_pinned. Scan to EOF before reporting declarations.
    Synthetic diagnostics carry the actual synthetic digest, never the PCB pin.
    """
    digest = verified_digest if verified_digest is not None else sha256(data).hexdigest()
    try:
        records = _scan(data, charge)
    except ScanError as error:
        return _failure('pcb.syntax', 'bounded supported syntax and four records',
                        (error.reason, error.offset, error.line), code=error.code, source_hash=digest)
    for record in records:
        for modifier in record.modifiers:
            if modifier.status == 'present':
                failure = _failure('modifiers.' + '/'.join(modifier.path), 'absent',
                    ('present', modifier.first_span, modifier.first_lines, modifier.occurrences),
                    record, ErrorCode.GEOMETRY_UNSUPPORTED, digest)
                return SourceFailure(failure.diagnostic, records)
        counts = {}
        for node in record.nodes:
            counts[node.path] = counts.get(node.path, 0) + 1
            if node.coverage == 'unclassified':
                return _coverage_failure(record, node, digest, 'classified exact leaf path',
                                         node.path, ErrorCode.GEOMETRY_UNSUPPORTED)
            if node.coverage == 'semantics-unchecked' and (
                    len(node.values) != 1 or counts[node.path] > 1):
                return _coverage_failure(record, node, digest, 'one occurrence with one value',
                                         (counts[node.path], node.values), ErrorCode.SCHEMA_INVALID)
            # Unknown descendants are diagnosed at their own exact path/span.
            # Existing semantic guards remain responsible for uuid/at/size/layers.
    return records


def _coverage_failure(record, node, digest, expected, actual, code):
    from dataclasses import replace
    failure = _failure('pad.coverage', expected, actual, record, code, digest)
    return replace(failure, diagnostic=replace(failure.diagnostic,
        context=failure.diagnostic.context + tuple((key, diagnostic_json(value)) for key, value in (
            ('ancestry_path', ('kicad_pcb', 'footprint') + node.path),
            ('node_span', node.span), ('node_lines', node.lines)))))


def evaluate_source_boundaries(pcb, request, declarations, raw, policy):
    """Check source before the accepted artifact gates and their binding call.

    Product assurances stay unchanged. Explicit layers are compared to pinned
    observation; rectangle type comes from the typed request, not boundary shape.
    """
    records = scan_pinned(pcb)
    if isinstance(records, SourceFailure):
        return records
    footprint_error = check_footprint_fields(records, PCB_HASH)
    if footprint_error is not None:
        return footprint_error
    coverage_error = check_footprint_coverage(records, PCB_HASH)
    if coverage_error is not None:
        return coverage_error
    graphics_error = check_graphics_layers(records, PCB_HASH)
    if graphics_error is not None:
        return graphics_error
    checked = artifacts.preflight_boundary_evidence(request, declarations, policy)
    if isinstance(checked, artifacts.PreflightFailure):
        return checked
    try:
        artifacts._binding_inputs(request)
    except artifacts._Reject as error:
        return _failure(error.field, 'valid request', error.message if hasattr(error, 'message') else 'invalid')
    if len(declarations) != 4 or len(request.pads) != 4:
        return _failure('records.count', 4, (len(declarations), len(request.pads)))
    # Verify observation bytes BEFORE extracting explicit layer/shape declarations.
    digest, size = next((h, n) for k, h, n in artifacts.profile.PINS if k == 'observation')
    if type(raw) is not dict or type(raw.get('observation')) is not bytes:
        return _failure('observation.bytes', 'bytes', 'missing')
    data = raw['observation']
    if len(data) != size or sha256(data).hexdigest() != digest:
        return _failure('observation.pin', digest, 'size/hash mismatch')
    observation = json.loads(data)  # Exact accepted bytes, not arbitrary JSON.
    conflict = check_source_records(records, request, declarations, observation)
    if conflict is not None:
        return conflict
    artifact_raw = {k: raw[k] for k in ('observation', 'C1_boundary', 'C2_boundary') if k in raw}
    result = artifacts.evaluate_artifact_boundaries(request, declarations, artifact_raw, policy)
    if not isinstance(result, artifacts.ArtifactBindingSuccess):
        return result
    return SourceSuccess(records, result)


def _footprint_failure(record, name, fields, digest, expected, actual, code):
    from dataclasses import replace
    result = _failure('footprint.' + name, expected, actual, record, code, digest)
    return replace(result, diagnostic=replace(result.diagnostic,
        context=result.diagnostic.context + tuple((k, diagnostic_json(v)) for k,v in (
            ('ancestry_path', ('kicad_pcb','footprint',name)),
            ('field_spans', tuple(f.span for f in fields)),
            ('field_lines', tuple(f.lines for f in fields))))))


def check_footprint_fields(records, digest):
    """Two fields only, after scanning EOF; not whole-footprint coverage.

    Exactly one direct leaf layer F.Cu and attr smd. No other attr flags,
    descendants, defaults or inference from pads. Private synthetic callers
    supply the actual digest; this function does not perform hash admission.
    """
    for record in records:
        for name, expected in (('layer', ('F.Cu',)), ('attr', ('smd',))):
            fields = tuple(f for f in record.footprint_fields if f.name == name)
            if len(fields) != 1:
                return _footprint_failure(record,name,fields,digest,'exactly one direct field',
                                          len(fields),ErrorCode.SCHEMA_INVALID)
            if fields[0].has_children or fields[0].values != expected:
                return _footprint_failure(record,name,fields,digest,(expected,'leaf'),
                    (fields[0].values,fields[0].has_children),ErrorCode.GEOMETRY_UNSUPPORTED)
    return None


def check_footprint_coverage(records, digest):
    """Post-EOF selected-footprint declaration coverage, not source admission.

    Token count/depth bound node storage and path lengths. Every non-pad
    descendant is classified by exact path; known parents grant no exceptions.
    Metadata, graphics/text and model-3d values are not semantically evaluated.
    """
    from dataclasses import replace
    for record in records:
        for node in record.footprint_nodes:
            if node.category == 'unclassified':
                result = _failure('footprint.coverage', 'classified exact ancestry path',
                    node.path, record, ErrorCode.GEOMETRY_UNSUPPORTED, digest)
                return replace(result, diagnostic=replace(result.diagnostic,
                    context=result.diagnostic.context + tuple((k,diagnostic_json(v)) for k,v in (
                        ('ancestry_path',node.path),('node_span',node.span),('node_lines',node.lines)))))
    return None


def check_graphics_layers(records, digest):
    """C1+C2 evaluation policy only; no effective graphics/copper semantics.

    Scan span-ordered records linearly, separating repeated sibling instances.
    Only direct child fields count. Property display declaration means any
    at/layer/effects, regardless of name or hide. Keep at most two layer records
    for bounded diagnostics; count all. Input records come from the EOF scanner.
    """
    from dataclasses import replace
    for record in records:
        nodes = record.footprint_nodes
        i = 0
        while i < len(nodes):
            owner = nodes[i]
            i += 1
            if len(owner.path) != 3 or owner.path[-1] not in ('fp_line','fp_circle','property'):
                continue
            display = owner.path[-1] != 'property'
            layers, count = [], 0
            while i < len(nodes) and nodes[i].span[0] < owner.span[1]:
                child = nodes[i]
                i += 1
                if child.path[:-1] != owner.path:
                    continue
                if child.path[-1] in ('at','layer','effects'):
                    display = True
                if child.path[-1] == 'layer':
                    count += 1
                    if len(layers) < 2:
                        layers.append(child)
            if not display:
                continue
            allowed = ('F.SilkS','F.Fab') if owner.path[-1] == 'property' else ('F.SilkS','F.CrtYd')
            if count == 1 and len(layers[0].values) == 1 and layers[0].values[0] in allowed:
                continue
            code = ErrorCode.SCHEMA_INVALID if count != 1 else ErrorCode.GEOMETRY_UNSUPPORTED
            result = _failure('footprint.graphics.layer', ('one direct layer',allowed),
                (count,tuple(n.values for n in layers)), record, code, digest)
            return replace(result, diagnostic=replace(result.diagnostic,
                context=result.diagnostic.context + tuple((k,diagnostic_json(v)) for k,v in (
                    ('ancestry_path',owner.path+('layer',)),('owner_span',owner.span),
                    ('owner_lines',owner.lines),('layer_spans',tuple(n.span for n in layers))))))
    return None


def check_source_records(records, request, declarations, observation):
    """Shared checks only; inputs are bounded/admitted by the calling flow."""
    from aoi_platform.pad_candidates import PadRectangle
    for record in records:
        items = [e for e in declarations if e.source_pad_id == record.pad_uuid]
        pads = [p for p in request.pads if p.source_entity_id == record.pad_uuid]
        if len(items) != 1 or len(pads) != 1:
            return _failure('pad.record_count', (1, 1), (len(items), len(pads)), record)
        item, pad = items[0], pads[0]
        obs = next(p for f in observation['footprints'] if f['uuid'] == record.parent_uuid
                   for p in f['pads'] if p['uuid'] == record.pad_uuid)
        comparisons = (
            ('declaration.parent_uuid', record.parent_uuid, item.source_parent_id),
            ('request.parent_uuid', record.parent_uuid, pad.source_parent_entity_id),
            ('pad.number', record.number, pad.pad_number),
            ('pad.type', record.pad_type, pad.pad_type),
            ('pad.shape', record.shape, 'rect' if type(pad.rectangle) is PadRectangle else 'unsupported'),
            ('observation.number', record.number, obs['number']),
            ('observation.type', record.pad_type, 'smd' if obs['attribute'] == 1 else 'unsupported'),
            ('observation.shape', record.shape, 'rect' if obs['shape'] == 1 else 'unsupported'),
            ('observation.layers', tuple(sorted(record.layers)), tuple(sorted(obs['layers']))),
            ('declaration.copper_layer', True, item.copper_layer in record.layers),
            ('request.copper_layers', ('F.Cu',), pad.copper_layers),
        )
        for field_name, expected, actual in comparisons:
            if expected != actual:
                return _failure(field_name, expected, actual, record)
        from c1_c2_source_pose import check_pose
        footprint = next(f for f in observation['footprints'] if f['uuid'] == record.parent_uuid)
        source_layer = next(f for f in record.footprint_fields if f.name == 'layer')
        if footprint['layer'] != source_layer.values[0]:
            return _footprint_failure(record, 'layer', (source_layer,), PCB_HASH,
                source_layer.values[0], footprint['layer'], ErrorCode.SOURCE_CONFLICT)
        pose_error = check_pose(record, pad, footprint, obs)
        if pose_error is not None:
            return pose_error
    return None
