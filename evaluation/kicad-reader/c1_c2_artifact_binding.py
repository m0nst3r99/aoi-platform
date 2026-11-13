"""Pinned C1+C2 record-to-observation consistency, not PCB membership verification."""
from dataclasses import dataclass
from hashlib import sha256
import json
import c1_c2_replay_batch as profile
from aoi_platform.boundary_evidence import preflight_boundary_evidence, PreflightFailure, _binding_inputs, _Reject
from aoi_platform.boundary_binding import bind_pad_boundaries, BoundaryBindingSuccess
from aoi_platform.geometry.errors import ErrorCode, diagnostic_json
from aoi_platform.geometry.reports import ContractError


@dataclass(frozen=True, slots=True)
class ObservedBoundaryRecord:
    artifact_id: str
    artifact_sha256: str
    parent_uuid: str
    pad_uuid: str
    layer: str
    raw_vertices_iu: tuple
    normalized_vertices_mm: tuple
    closed: bool
    hole_count: int
    accessor: str
    native_protocol: str
    declared_build: str
    coordinate_space: str
    iu_per_mm: int
    clearance_iu: int
    max_error_iu: int
    error_location: str
    side_from_observation: str


@dataclass(frozen=True, slots=True)
class ArtifactBindingFailure:
    diagnostic: ContractError


@dataclass(frozen=True, slots=True)
class ArtifactBindingSuccess:
    records: tuple[ObservedBoundaryRecord, ...]
    binding: BoundaryBindingSuccess
    @property
    def status(self): return 'consistent-with-pinned-observation-artifacts'
    @property
    def source_membership_status(self): return 'not-verified'


class _Conflict(Exception):
    def __init__(self, field, expected, actual):
        self.field, self.expected, self.actual = field, expected, actual


def evaluate_artifact_boundaries(request, declarations, raw, policy):
    """raw is exactly observation/C1_boundary/C2_boundary immutable bytes.

    Hash/size pins precede JSON parsing. Joint preflight bounds caller records.
    Compare normalized values exactly, not with geometry tolerance. Caller
    canonical IDs, evidence labels, scope/P frame/transform and coverage are not
    decoded source facts; the product binder retains its unverified assurances.
    """
    checked=preflight_boundary_evidence(request,declarations,policy)
    if isinstance(checked,PreflightFailure):return checked
    artifact=None;digest=None;parent=None;pad=None
    def equal(field, expected, actual):
        if expected!=actual:raise _Conflict(field,expected,actual)
    try:
        _binding_inputs(request)
        equal('pad_count',4,len(request.pads))
        equal('declaration_count',4,len(declarations))
        pins={k:(h,n) for k,h,n in profile.PINS}
        inventory={a.declaration.artifact_id:(a.computed_sha256,a.actual_size) for a in request.inventory.inventory.artifacts}
        equal('inventory.pins',pins,inventory)
        keys={'observation','C1_boundary','C2_boundary'}
        equal('raw.type',True,type(raw) is dict)
        equal('raw.count',3,len(raw))
        equal('raw.keys',keys,set(raw))
        for artifact in sorted(keys):
            digest,size=pins[artifact]
            equal('raw.bytes',True,type(raw[artifact]) is bytes)
            equal('raw.size',size,len(raw[artifact]))
            equal('raw.sha256',digest,sha256(raw[artifact]).hexdigest())
    except (_Conflict,_Reject) as error:
        # Caller metadata was jointly bounded. Pins fix artifact and source IDs.
        # Keep comparisons compact; do not serialize whole inventories/payloads.
        field=error.field
        context=tuple((k,diagnostic_json(v)) for k,v in (
            ('artifact_id_json',artifact),('artifact_sha256',digest),('parent_uuid',parent),('pad_uuid',pad)) if v is not None)
        def bounded(value):
            text=repr(value)
            return text if len(text)<=512 else '<bounded diagnostic: value exceeds 512 characters>'
        return ArtifactBindingFailure(ContractError(ErrorCode.SOURCE_CONFLICT,
            'Declaration differs from pinned observation artifact.',field,'Correct the declaration; preserve artifact bytes.',
            expected=bounded(error.expected) if isinstance(error,_Conflict) else None,
            actual=bounded(error.actual) if isinstance(error,_Conflict) else None,context=context))
    records=_records_from_verified(request,declarations,raw)
    if isinstance(records,ArtifactBindingFailure):return records
    result=bind_pad_boundaries(request,declarations,policy)
    if not isinstance(result,BoundaryBindingSuccess):return result
    return ArtifactBindingSuccess(tuple(sorted(records,key=lambda r:(r.parent_uuid,r.pad_uuid))),result)


def _records_from_verified(request, declarations, raw, charge=None):
    """Private: preflight and exact byte pins must have passed. Never binds.

    Optional charge runs before retaining parsed metadata/reconstructed records.
    Budget exceptions propagate to the operation-owned ledger failure handler.
    """
    artifact=None;digest=None;parent=None;pad=None
    pins={k:(h,n) for k,h,n in profile.PINS}
    def equal(field, expected, actual):
        if expected!=actual:raise _Conflict(field,expected,actual)
    try:
        # From here all JSON is byte-identical to the bounded reviewed artifacts.
        decision=profile.evaluate_outline(raw['observation'])
        equal('observation.decision','not_rejected_by_outline_check',decision.status)
        observation=json.loads(raw['observation'])
        if charge is not None:charge(observation)
        equal('observation.build','10.0.7',observation['build'])
        equal('observation.input_sha256',pins['pcb'][0],observation['input_sha256'])
        expected_pairs={(c.PARENT,uid) for _,c in profile.GROUPS for uid in c.PADS}
        declared={}
        for item in declarations:
            parent,pad=item.source_parent_id,item.source_pad_id
            equal('declaration.duplicate',False,(parent,pad) in declared)
            declared[parent,pad]=item
        equal('declaration.pairs',expected_pairs,set(declared))
        records=[]
        for group,comparator in profile.GROUPS:
            artifact=group+'_boundary';digest=pins[artifact][0]
            payload=json.loads(raw[artifact])
            if charge is not None:charge(payload)
            equal('boundary.oracle',True,comparator.compare(payload)['passed'])
            equal('boundary.input_sha256',pins['pcb'][0],payload['input_sha256'])
            footprints=[f for f in observation['footprints'] if f['uuid']==comparator.PARENT]
            equal('observation.parent_count',1,len(footprints))
            footprint=footprints[0]
            equal('observation.side','F.Cu',footprint['layer'])
            observed={p['uuid']:p for p in footprint['pads']}
            equal('observation.pad_count',2,len(footprint['pads']))
            equal('observation.pad_ids',comparator.PADS,set(observed))
            seen=set()
            for row in payload['pads']:
                parent,pad=row['parent_uuid'],row['uuid'];key=parent,pad
                equal('boundary.duplicate',False,key in seen);seen.add(key)
                equal('boundary.parent',comparator.PARENT,parent)
                item=declared[key];obs=observed[pad];contour=row['contours'][0]
                raw_vertices=tuple(tuple(v) for v in contour['vertices_iu'])
                normalized=tuple((x/payload['iu_per_mm'],-y/payload['iu_per_mm']) for x,y in raw_vertices)
                equal('boundary.artifact_id',artifact,item.boundary.artifact_id)
                equal('boundary.hash',digest,item.boundary.computed_sha256)
                equal('source.artifact_id','pcb',item.source.artifact_id)
                equal('source.hash',pins['pcb'][0],item.source.computed_sha256)
                equal('observation.artifact_id','observation',item.observation.artifact_id)
                equal('observation.hash',pins['observation'][0],item.observation.computed_sha256)
                equal('boundary.layer',row['layer'],item.copper_layer)
                equal('boundary.build',payload['build'],item.producer_version)
                equal('boundary.closed',contour['closed'],item.contours[0].closed)
                equal('boundary.holes',contour['hole_count'],item.contours[0].hole_count)
                for i,(wanted,point) in enumerate(zip(normalized,item.contours[0].vertices)):
                    equal('contours[0].vertices['+str(i)+']',wanted,(point.x,point.y))
                equal('observation.pad_subset',(1,1,[0,0],{'F.Cu','F.Mask','F.Paste'}),
                    (obs['shape'],obs['attribute'],obs['drill_mm'],set(obs['layers'])))
                equal('observation.side','top',item.side)
                source=[p for p in request.pads if p.source_parent_entity_id==parent and p.source_entity_id==pad]
                equal('request.source_pad_count',1,len(source));source=source[0]
                equal('observation.number',obs['number'],source.pad_number)
                equal('observation.rectangle',(obs['position_mm'][0],-obs['position_mm'][1],*obs['size_mm'],obs['angle_deg']),
                    (source.rectangle.center.x,source.rectangle.center.y,source.rectangle.width,source.rectangle.height,source.rectangle.angle_deg))
                args=(artifact,digest,parent,pad,row['layer'],raw_vertices,normalized,
                    contour['closed'],contour['hole_count'],row['accessor'],payload['protocol'],payload['build'],
                    payload['coordinate_space'],payload['iu_per_mm'],payload['clearance_iu'],payload['max_error_iu'],payload['error_location'],'top')
                if charge is not None:charge(args)
                records.append(ObservedBoundaryRecord(*args))
            equal('boundary.pairs',{(comparator.PARENT,u) for u in comparator.PADS},seen)
        equal('record_count',4,len(records))
    except _Conflict as error:
        # Caller metadata was jointly bounded. Pins fix artifact and source IDs.
        # Keep comparisons compact; do not serialize whole inventories/payloads.
        field=error.field
        context=tuple((k,diagnostic_json(v)) for k,v in (
            ('artifact_id_json',artifact),('artifact_sha256',digest),('parent_uuid',parent),('pad_uuid',pad)) if v is not None)
        def bounded(value):
            text=repr(value)
            return text if len(text)<=512 else '<bounded diagnostic: value exceeds 512 characters>'
        return ArtifactBindingFailure(ContractError(ErrorCode.SOURCE_CONFLICT,
            'Declaration differs from pinned observation artifact.',field,'Correct the declaration; preserve artifact bytes.',
            expected=bounded(error.expected) if isinstance(error,_Conflict) else None,
            actual=bounded(error.actual) if isinstance(error,_Conflict) else None,context=context))
    return tuple(sorted(records,key=lambda r:(r.parent_uuid,r.pad_uuid)))
