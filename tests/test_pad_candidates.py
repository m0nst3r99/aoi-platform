"""Synthetic product candidate contracts; independent corner oracles, no native API."""
from dataclasses import replace, FrozenInstanceError, fields
from io import BytesIO
from math import sqrt
import pytest

from aoi_platform.pad_candidates import (
    SyntheticPadPolicy, EvidenceReference, PadProvenance, PadParent, PadRectangle,
    SourcePad, PadCandidateRequest, PadBatchSuccess, PadBatchFailure,
    build_rectangular_pad_candidates as build,
)
from aoi_platform.inventory import ArtifactDeclaration, InventoryManifest, InventoryLimits, inventory_artifacts
from aoi_platform.geometry.models import Frame, FrameKind, Unit, AxisDirection as Axis, Point2
from aoi_platform.geometry.transforms import Transform2, TransformKind
from aoi_platform.geometry.errors import ErrorCode, diagnostic_json

POLICY = SyntheticPadPolicy('synthetic-rect-pad-candidate', '1', 4096, 4096, 1024,
    256, 1024, 16, 32768, 8388608, 128, 4096, 524288,
    1000000.0, 0.000001, 1000000.0, 360000.0, 1e-12, 0.0, 1e-6)
HASH = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'


def request():
    source = Frame('source', FrameKind.SOURCE, Unit.MM, 'datum', Axis.RIGHT, Axis.UP, 'scope')
    target = Frame('P', FrameKind.PCB, Unit.MM, 'datum', Axis.RIGHT, Axis.UP, 'scope')
    transform = Transform2('map', source, target,
        ((0., -1., 10.), (1., 0., 20.), (0., 0., 1.)), TransformKind.RIGID)
    inventory = inventory_artifacts(InventoryManifest('geometry',
        (ArtifactDeclaration('pcb', 'kicad_pcb', 'bytes', HASH),), 'synthetic-r1', 'snapshot'),
        {'bytes': lambda: BytesIO(b'abc')}, InventoryLimits('test', 1, 3, 3, 3))
    refs = (EvidenceReference('pcb', HASH, 'synthetic-declaration'),)
    prov = PadProvenance('pcb', 'bytes', HASH, 'parent-source', 'snapshot', 'synthetic-r1',
                         'synthetic', '1', refs)
    parent = PadParent('parent', 'parent-source', 'pcb', source, 'board-source', 'top', transform, refs, prov)
    pad = SourcePad('pad', 'parent', 'pad-source', 'parent-source', 'pcb', source, '1',
        'top', ('F.Cu',), 'smd', None, PadRectangle(Point2(2, 3, source), 4., 2., 0.),
        replace(prov, source_entity_id='pad-source'))
    return PadCandidateRequest('rect-pad-candidate-v1', POLICY, 'board', 'scope', target, inventory, (parent,), (pad,))


def with_pad(req, **kw):
    return replace(req, pads=(replace(req.pads[0], **kw),))


def failed(result, code):
    assert isinstance(result, PadBatchFailure)
    assert not hasattr(result, 'candidates')
    assert result.report.status.value == 'rejected'
    assert code in [e.code.value for e in result.report.errors]
    return result


@pytest.mark.parametrize('angle,wanted', [
    (0., [(8,20),(8,24),(6,24),(6,20)]),
    (90., [(9,23),(5,23),(5,21),(9,21)]),
    # c=s=sqrt(2)/2; independently rotate local corners then (-y+10,x+20).
    (45., [(7+3/sqrt(2),22-1/sqrt(2)),(7-1/sqrt(2),22+3/sqrt(2)),
           (7-3/sqrt(2),22+1/sqrt(2)),(7+1/sqrt(2),22-3/sqrt(2))]),
])
def test_independent_oracles(angle, wanted):
    req = request()
    req = with_pad(req, rectangle=replace(req.pads[0].rectangle, angle_deg=angle))
    before = repr(req)
    result = build(req)
    assert isinstance(result, PadBatchSuccess), result
    candidate, = result.candidates
    for point, xy in zip(candidate.vertices, wanted):
        assert (point.x, point.y) == pytest.approx(xy, abs=1e-6, rel=0)
        assert point.frame == req.target_frame
    assert len(candidate.vertices) == 4
    assert candidate.association_status == 'declaration-consistent'
    assert candidate.published is False and candidate.targeting_authorized is False
    assert result.report.canonical_digest is None
    assert repr(req) == before
    with pytest.raises(FrozenInstanceError):
        candidate.board_id = 'changed'
    with pytest.raises(FrozenInstanceError):
        candidate.source.provenance.source_id = 'changed'


def test_repeated_empty_numbers_and_lexical_order():
    r = request(); p = r.pads[0]
    pads = tuple(replace(p, pad_id=n, pad_number=number, source_entity_id=n,
                        provenance=replace(p.provenance, source_entity_id=n))
                 for n, number in [('z', '1'), (' a ', ''), ('B', '1')])
    result = build(replace(r, pads=pads))
    assert isinstance(result, PadBatchSuccess)
    assert [c.pad_id for c in result.candidates] == [' a ', 'B', 'z']
    assert [c.source.pad_number for c in result.candidates] == ['', '1', '1']
    assert result == build(replace(r, pads=tuple(reversed(pads))))


@pytest.mark.parametrize('kind', ['pad-id','parent-id','pad-source','parent-source'])
def test_ids_and_typed_source_alias(kind):
    r = request()
    if kind.startswith('pad'):
        p = r.pads[0]
        r = replace(r, pads=(p, replace(p, pad_id=p.pad_id if kind=='pad-id' else 'other')))
    else:
        p = r.parents[0]
        r = replace(r, parents=(p, replace(p, footprint_id=p.footprint_id if kind=='parent-id' else 'other')))
    failed(build(r), 'DUPLICATE_ID' if kind.endswith('-id') else 'SOURCE_CONFLICT')


def test_source_namespaces_are_separate():
    r = request(); p = r.pads[0]
    r = with_pad(r, source_entity_id='parent-source', provenance=replace(p.provenance, source_entity_id='parent-source'))
    assert isinstance(build(r), PadBatchSuccess)


@pytest.mark.parametrize('key,value', [('pad_id',''),('source_entity_id',''),('footprint_id','unknown'),
    ('pad_number',1),('source_parent_entity_id','wrong')])
def test_bad_pad_fields(key, value):
    failed(build(with_pad(request(), **{key:value})), 'SOURCE_CONFLICT' if key=='source_parent_entity_id' else 'SCHEMA_INVALID')


@pytest.mark.parametrize('field,value', [('source_id','wrong'),('computed_sha256','0'*64),
    ('artifact_id','wrong'),('source_entity_id','wrong'),('source_snapshot','wrong'),('fixture_revision','wrong')])
def test_provenance_binding(field, value):
    r = request(); p = r.pads[0]
    result = failed(build(with_pad(r, provenance=replace(p.provenance, **{field:value}))), 'SOURCE_CONFLICT')
    issue = result.report.errors[0]
    assert issue.entity_id == 'pad' and issue.artifact_id == 'pcb'
    assert issue.expected != issue.actual


@pytest.mark.parametrize('field,value', [('eof',False),('actual_size',4),('computed_sha256','0'*64),('bytes_read',True)])
def test_inventory_observations(field, value):
    r = request(); inv = r.inventory.inventory
    bad = replace(inv, artifacts=(replace(inv.artifacts[0], **{field:value}),))
    failed(build(replace(r, inventory=replace(r.inventory, inventory=bad))), 'SOURCE_CONFLICT')


@pytest.mark.parametrize('field,value', [('origin','other'),('frame_id','other'),('board_revision_id','other'),
    ('machine_id','machine'),('capture_id','capture'),('unit',Unit.INCH),('y_direction',Axis.DOWN)])
def test_full_frame_mismatch(field, value):
    r = request(); f = replace(r.pads[0].source_frame, **{field:value})
    result = build(with_pad(r, source_frame=f))
    assert isinstance(result, PadBatchFailure)
    assert any(e.code in (ErrorCode.CONTEXT_MISMATCH, ErrorCode.GEOMETRY_UNSUPPORTED) for e in result.report.errors)


@pytest.mark.parametrize('case', ['affine','reflection','unvalidated','missing','wrong-target'])
def test_transform_rejection(case):
    r = request(); parent = r.parents[0]; t = parent.source_to_p
    if case == 'affine': t = replace(t, kind=TransformKind.AFFINE, matrix=((2.,0.,0.),(0.,1.,0.),(0.,0.,1.)))
    if case == 'reflection': t = replace(t, kind=TransformKind.REFLECTION, matrix=((-1.,0.,0.),(0.,1.,0.),(0.,0.,1.)))
    if case == 'unvalidated': t = replace(t, to_frame=replace(t.to_frame, origin='other'))
    if case == 'missing': t = None
    if case == 'wrong-target': t = replace(t, to_frame=replace(t.to_frame, frame_id='other'))
    if case == 'unvalidated': r = replace(r, target_frame=t.to_frame)
    result = build(replace(r, parents=(replace(parent, source_to_p=t),)))
    failed(result, {'affine':'GEOMETRY_UNSUPPORTED','reflection':'GEOMETRY_UNSUPPORTED',
                   'unvalidated':'MAPPING_UNVALIDATED','missing':'TRANSFORM_MISSING','wrong-target':'CONTEXT_MISMATCH'}[case])


@pytest.mark.parametrize('kw', [dict(side='bottom'),dict(copper_layers=('F.Cu','B.Cu')),dict(copper_layers=('F.Cu','F.Cu')),
    dict(pad_type='tht'),dict(drill=1.),dict(rectangle=None)])
def test_unsupported(kw):
    failed(build(with_pad(request(), **kw)), 'GEOMETRY_UNSUPPORTED')


@pytest.mark.parametrize('field,value,code', [('width',0.,'SCHEMA_INVALID'),('height',float('nan'),'SCHEMA_INVALID'),
    ('angle_deg',float('inf'),'SCHEMA_INVALID'),('width',True,'SCHEMA_INVALID'),
    ('width',0.0000009,'INPUT_LIMIT_EXCEEDED'),('width',1000000.001,'INPUT_LIMIT_EXCEEDED'),
    ('angle_deg',360000.001,'INPUT_LIMIT_EXCEEDED')])
def test_numeric_rejections(field,value,code):
    r=request();failed(build(with_pad(r,rectangle=replace(r.pads[0].rectangle,**{field:value}))),code)


def test_stable_small_rectangle_at_large_coordinate():
    r=request(); f=r.pads[0].source_frame
    t=Transform2('identity',f,r.target_frame,((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID)
    r=replace(r,parents=(replace(r.parents[0],source_to_p=t),))
    r=with_pad(r,rectangle=PadRectangle(Point2(999999,999999,f),1e-6,1e-6,45.))
    result=build(r)
    assert isinstance(result,PadBatchSuccess),result


@pytest.mark.parametrize('field,value', [('max_pads',True),('max_pads',0),('max_pads',4097),
    ('rigid_guard_abs',1e-6),('policy_id','wrong'),('max_id_utf8_bytes',256.0)])
def test_invalid_policy_bounded_fallback(field,value):
    r=request();result=failed(build(replace(r,policy=replace(POLICY,**{field:value}))),'POLICY_INVALID')
    assert len(result.report.errors)==1
    assert len(result.report.to_json().encode())<4096


@pytest.mark.parametrize('name', ['parents','pads'])
def test_empty_batch(name):
    failed(build(replace(request(),**{name:()})),'SCHEMA_INVALID')


def test_mixed_batch_atomic_and_diagnostic_order():
    r=request();p=r.pads[0]
    bad=replace(p,pad_id='bad',source_entity_id='bad',side='bottom',provenance=replace(p.provenance,source_entity_id='bad'))
    a=failed(build(replace(r,pads=(p,bad))),'GEOMETRY_UNSUPPORTED')
    b=build(replace(r,pads=(bad,p)))
    assert a==b


@pytest.mark.parametrize('n,ok', [(256,True),(257,False)])
def test_identity_byte_boundary(n,ok):
    result=build(with_pad(request(),pad_id='x'*n))
    assert isinstance(result,PadBatchSuccess) if ok else isinstance(result,PadBatchFailure)


@pytest.mark.parametrize('n,ok', [(128,True),(129,False)])
def test_utf8_byte_not_character_boundary(n,ok):
    result=build(with_pad(request(),pad_id='é'*n))
    assert isinstance(result,PadBatchSuccess) if ok else isinstance(result,PadBatchFailure)


@pytest.mark.parametrize('n,ok', [(1024,True),(1025,False)])
def test_net_text_boundary(n,ok):
    result=build(with_pad(request(),net='n'*n))
    assert isinstance(result,PadBatchSuccess) if ok else isinstance(result,PadBatchFailure)


@pytest.mark.parametrize('count,ok', [(16,True),(17,False)])
def test_evidence_reference_boundary(count,ok):
    r=request();p=r.pads[0]
    result=build(with_pad(r,provenance=replace(p.provenance,evidence=p.provenance.evidence*count)))
    assert isinstance(result,PadBatchSuccess) if ok else isinstance(result,PadBatchFailure)


def test_diagnostic_exhaustion_reserved_blocker():
    r=request();p=r.pads[0]
    pads=tuple(replace(p,pad_id=f'{i:04}',source_entity_id=str(i),side='bottom',
        provenance=replace(p.provenance,source_entity_id=str(i))) for i in range(130))
    result=failed(build(replace(r,pads=pads)),'INPUT_LIMIT_EXCEEDED')
    assert result.truncation.occurred and result.truncation.reason=='issue_count'
    assert result.truncation.omitted_count is None
    assert len(result.report.issues)==128
    sizes=[len(diagnostic_json(e.to_dict()).encode()) for e in result.report.issues]
    assert max(sizes)<=4096 and sum(sizes)<=524288
    assert result==build(replace(r,pads=tuple(reversed(pads))))


def test_oversized_diagnostic_uses_reserved_issue_not_partial_text():
    r=request();p=r.pads[0]
    # JSON escaping expands control characters; input is still within byte limits.
    result=failed(build(with_pad(r,pad_id='\x01'*256,source_entity_id='\x02'*256,
        provenance=replace(p.provenance,source_entity_id='\x02'*256,source_snapshot='\x03'*1024))),
        'INPUT_LIMIT_EXCEEDED')
    assert result.truncation.reason=='issue_bytes'
    assert len(result.report.issues)==1


def test_no_encoding_giant_metadata_before_budget():
    r=request()
    result=failed(build(with_pad(r,net='x'*10000000)),'INPUT_LIMIT_EXCEEDED')
    assert result.truncation.reason=='input_budget'
    assert len(result.report.to_json())<4096


def test_mutable_and_malformed_inputs_fail():
    r=request()
    failed(build(replace(r,pads=list(r.pads))),'SCHEMA_INVALID')


@pytest.mark.parametrize('count', [4096,4097])
def test_pad_count_bound(count):
    r=request();p=r.pads[0]
    pads=tuple(replace(p,pad_id=str(i),source_entity_id=str(i),
        provenance=replace(p.provenance,source_entity_id=str(i))) for i in range(count))
    result=build(replace(r,pads=pads))
    if count==4096: assert isinstance(result,PadBatchSuccess),result
    else: failed(result,'INPUT_LIMIT_EXCEEDED')

@pytest.mark.parametrize('where', ['pad-frame','parent-frame','inventory-artifacts','manifest-artifacts',
                                  'provenance-hash','source-location'])
def test_malformed_typed_fields_return_failure(where):
    r = request()
    if where == 'pad-frame': r = with_pad(r, source_frame=None)
    if where == 'parent-frame': r = replace(r, parents=(replace(r.parents[0], source_frame=None),))
    if where == 'inventory-artifacts':
        r = replace(r, inventory=replace(r.inventory, inventory=replace(r.inventory.inventory, artifacts=None)))
    if where == 'manifest-artifacts':
        inv = r.inventory.inventory
        r = replace(r, inventory=replace(r.inventory, inventory=replace(inv, manifest=replace(inv.manifest, artifacts=None))))
    if where == 'provenance-hash': r = with_pad(r, provenance=replace(r.pads[0].provenance, computed_sha256=1))
    if where == 'source-location': r = with_pad(r, provenance=replace(r.pads[0].provenance, source_location=1))
    failed(build(r), 'SCHEMA_INVALID')


def test_whitespace_identity_preserved_even_on_failure():
    r = with_pad(request(), pad_id=' ', side='bottom')
    result = failed(build(r), 'GEOMETRY_UNSUPPORTED')
    assert dict(result.report.errors[0].context)['entity_id_json'] == '" "'
    assert isinstance(build(with_pad(request(), pad_id=' ')), PadBatchSuccess)


def test_known_diagnostic_context_and_source_location():
    from aoi_platform.geometry.reports import SourceLocation
    r = request(); p = r.pads[0]
    location = SourceLocation('synthetic.txt', 2, 3)
    result = failed(build(with_pad(r, provenance=replace(p.provenance, source_id='wrong', source_location=location))), 'SOURCE_CONFLICT')
    issue = result.report.errors[0]; context = dict(issue.context)
    assert issue.source_location == location
    assert issue.expected == 'bytes' and issue.actual == 'wrong'
    assert context['source_id'] == 'wrong'  # supplied conflicting claim retained
    assert context['source.board_revision_id'] == context['target.board_revision_id'] == 'scope'
    assert context['computed_sha256'] == HASH and context['transform_id'] == 'map'
    assert context['policy_id'] == POLICY.policy_id


@pytest.mark.parametrize('count', [4096, 4097])
def test_parent_count_boundary(count):
    r = request(); p = r.parents[0]
    parents = tuple(replace(p, footprint_id=str(i), source_entity_id=str(i),
        provenance=replace(p.provenance, source_entity_id=str(i))) for i in range(count))
    r = replace(r, parents=parents, pads=(replace(r.pads[0], footprint_id='0', source_parent_entity_id='0'),))
    result = build(r)
    if count == 4096: assert isinstance(result, PadBatchSuccess), result
    else: failed(result, 'INPUT_LIMIT_EXCEEDED')


@pytest.mark.parametrize('count', [1024, 1025])
def test_inventory_count_boundary(count):
    r = request(); inv = r.inventory.inventory
    declarations = (inv.manifest.artifacts[0],) + tuple(replace(inv.manifest.artifacts[0],
        artifact_id=f'extra{i}', reference_only=True) for i in range(count-1))
    observations = tuple(replace(inv.artifacts[0], declaration=d) for d in declarations)
    r = replace(r, inventory=replace(r.inventory, inventory=replace(inv,
        manifest=replace(inv.manifest, artifacts=declarations), artifacts=observations)))
    result = build(r)
    if count == 1024: assert isinstance(result, PadBatchSuccess), result
    else: failed(result, 'INPUT_LIMIT_EXCEEDED')


@pytest.mark.parametrize('extra', [0, 1])
def test_total_evidence_reference_boundary(extra):
    r = request(); p = r.pads[0]
    # 2047*16 + (14 or 15) + 2 parent refs = 32768 or 32769.
    pads = tuple(replace(p, pad_id=str(i), source_entity_id=str(i), provenance=replace(p.provenance,
        source_entity_id=str(i), evidence=p.provenance.evidence*(16 if i < 2047 else 14+extra))) for i in range(2048))
    result = build(replace(r, pads=pads))
    if extra == 0: assert isinstance(result, PadBatchSuccess), result
    else: failed(result, 'INPUT_LIMIT_EXCEEDED')


def test_total_metadata_utf8_exact_and_one_over():
    from dataclasses import is_dataclass
    from enum import Enum
    def text_size(value):
        if isinstance(value, Enum): return 0
        if type(value) is str: return len(value.encode('utf-8'))
        if type(value) is tuple: return sum(text_size(v) for v in value)
        if is_dataclass(value): return sum(text_size(getattr(value, f.name)) for f in fields(value))
        return 0
    r = request(); p = r.pads[0]
    pads = [replace(p, pad_id=str(i), source_entity_id=str(i), net='',
        provenance=replace(p.provenance, source_entity_id=str(i),
            evidence=(replace(p.provenance.evidence[0], locator='a'),))) for i in range(4096)]
    r = replace(r, pads=tuple(pads))
    remaining = 8388608 - text_size(r)
    for i, pad in enumerate(pads):
        a = min(1024, remaining); remaining -= a
        b = min(1023, remaining); remaining -= b
        pads[i] = replace(pad, net='n'*a, provenance=replace(pad.provenance,
            evidence=(replace(pad.provenance.evidence[0], locator='a'*(1+b)),)))
    assert remaining == 0
    exact = replace(r, pads=tuple(pads))
    assert text_size(exact) == 8388608
    assert isinstance(build(exact), PadBatchSuccess)
    # Last net is not filled; +1 stays inside its individual text bound.
    assert len(pads[-1].net) < 1024
    pads[-1] = replace(pads[-1], net=pads[-1].net+'n')
    failed(build(replace(r, pads=tuple(pads))), 'INPUT_LIMIT_EXCEEDED')


@pytest.mark.parametrize('extra', [0., 0.000001])
def test_output_coordinate_boundary(extra):
    r = request(); f = r.pads[0].source_frame
    t = Transform2('identity', f, r.target_frame, ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)), TransformKind.RIGID)
    r = replace(r, parents=(replace(r.parents[0], source_to_p=t),))
    r = with_pad(r, rectangle=PadRectangle(Point2(999999+extra,0,f),2.,2.,0.))
    if extra == 0: assert isinstance(build(r), PadBatchSuccess)
    else: failed(build(r), 'INPUT_LIMIT_EXCEEDED')


@pytest.mark.parametrize('dimension', [0.000001, 1000000.])
def test_dimension_inclusive_boundaries(dimension):
    r = request(); f = r.pads[0].source_frame
    r = with_pad(r, rectangle=PadRectangle(Point2(0,0,f), dimension, dimension, 0.))
    assert isinstance(build(r), PadBatchSuccess)


@pytest.mark.parametrize('angle', [-360000., 360000.])
def test_angle_inclusive_boundaries(angle):
    r = request()
    assert isinstance(build(with_pad(r, rectangle=replace(r.pads[0].rectangle, angle_deg=angle))), PadBatchSuccess)


def test_diagnostics_reserved_slot_boundary():
    r = request(); p = r.pads[0]
    pads = tuple(replace(p, pad_id=str(i), source_entity_id=str(i), side='bottom',
        provenance=replace(p.provenance, source_entity_id=str(i))) for i in range(127))
    result = failed(build(replace(r, pads=pads)), 'GEOMETRY_UNSUPPORTED')
    assert len(result.report.issues) == 127 and not result.truncation.occurred


def test_reference_only_primary_rejected():
    r = request(); inv = r.inventory.inventory
    d = replace(inv.manifest.artifacts[0], reference_only=True)
    inv = replace(inv, manifest=replace(inv.manifest, artifacts=(d,)),
                  artifacts=(replace(inv.artifacts[0], declaration=d),))
    failed(build(replace(r, inventory=replace(r.inventory, inventory=inv))), 'SOURCE_CONFLICT')


def test_duplicate_identity_reporting_is_permutation_stable():
    r = request(); p = r.pads[0]
    other = replace(p, source_entity_id='different', side='bottom',
                    provenance=replace(p.provenance, source_entity_id='different'))
    a = failed(build(replace(r, pads=(p, other))), 'DUPLICATE_ID')
    assert a == build(replace(r, pads=(other, p)))


def test_extreme_integer_rejected_before_duplicate_sort_serialization():
    r = request(); p = r.pads[0]
    bad = replace(p, rectangle=replace(p.rectangle, width=10**10000))
    failed(build(replace(r, pads=(p, bad))), 'SCHEMA_INVALID')


@pytest.mark.parametrize('extra', [0, 1])
def test_serialized_diagnostic_per_issue_boundary(extra):
    # Direct sink contract: independent JSON byte measurement includes escaping,
    # schema field names and all fixed messages; no production size helper used.
    import json
    from aoi_platform.pad_candidates import _Issues
    from aoi_platform.geometry.errors import GeometryError
    sink = _Issues(POLICY)
    error = GeometryError(ErrorCode.SCHEMA_INVALID, 'x', field_path='test')
    sink.add(error)
    base = len(json.dumps(sink.issues[0].to_dict(), sort_keys=True,
                          ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
    sink = _Issues(POLICY)
    def emit(): sink.add(GeometryError(ErrorCode.SCHEMA_INVALID, 'x'*(1+4096-base+extra), field_path='test'))
    if extra:
        from aoi_platform.pad_candidates import _Stop
        with pytest.raises(_Stop): emit()
        assert sink.truncation.reason == 'issue_bytes'
        assert sink.issues[0].code is ErrorCode.INPUT_LIMIT_EXCEEDED
    else:
        for _ in range(127): emit()
        assert sink.used == 520192
        assert not sink.truncation.occurred
        from aoi_platform.pad_candidates import _Stop
        with pytest.raises(_Stop): emit()
        assert len(sink.issues) == 128
        assert sum(len(json.dumps(i.to_dict(), sort_keys=True, ensure_ascii=False,
                       separators=(',', ':')).encode()) for i in sink.issues) <= 524288
