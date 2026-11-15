"""Pinned receipt assembly; no acquisition, binding, candidate execution or publication.

PCB spans denote exact scanner tokens/expressions. JSON comparisons use the whole
hashed document as an explicitly enclosing span and the root JSON pointer ("").
Comparison paths name checker operations, not fabricated JSON token locations.
Caller identity/context/provenance remain declarations, never authenticated facts.
"""
from dataclasses import replace
from decimal import Decimal
import json
import re

import source_checked_preflight as pre
import source_checked_declarations as source
import source_checked_boundaries as boundaries
from aoi_platform.geometry.errors import GeometryError
from aoi_platform.geometry.models import require_same_frame


UNCHECKED = ('construct-completeness', 'effective-copper-geometry', 'zone-fill-effects',
             'metadata-net-pintype-zone_connect-semantics', 'graphics-text-model3d-semantics',
             'caller-context-authenticity', 'backend-authenticity', 'general-format-support')


def _require(ok, field, code=pre.ErrorCode.SOURCE_CONFLICT):
    if not ok:
        raise GeometryError(code, 'Preparation invariant failed.', field_path=field)


def _json_size(value):
    """Exact ASCII JSON size before serialization; values have already been bounded."""
    if isinstance(value, str):
        return 2 + sum(2 if c in '\\"\b\f\n\r\t' else
                       6 if ord(c)<32 or 127<=ord(c)<=65535 else
                       12 if ord(c)>65535 else 1 for c in value)
    if value is None: return 4
    if type(value) is bool: return 4 if value else 5
    if type(value) in (int,float): return len(str(value))
    if type(value) is tuple: return 2+max(0,len(value)-1)+sum(_json_size(v) for v in value)
    if type(value) is dict:
        return 2+max(0,len(value)-1)+sum(_json_size(k)+1+_json_size(v) for k,v in value.items())
    raise GeometryError(pre.ErrorCode.SCHEMA_INVALID,'Unsupported check value.',field_path='receipt.json')


def _json_value(value):
    if isinstance(value,Decimal): return str(value)
    if type(value) in (tuple,list): return tuple(_json_value(x) for x in value)
    if type(value) in (set,frozenset): return tuple(sorted(_json_value(x) for x in value))
    if type(value) is dict: return {k:_json_value(v) for k,v in sorted(value.items())}
    return value


class _Receipt:
    """Private operation-owned collector. Never accepted as a public input."""
    def __init__(self, ledger):
        self.ledger=ledger
        self.raw={}
        self.checks=[]

    def admitted(self, raw):
        self.raw=raw  # same immutable buffers, only after actual hash admission

    def context(self, request, declarations):
        _context(request,declarations)

    def _json(self, value):
        value=_json_value(value)  # fixed-size checker facts, not caller object graphs
        source._charge(self.ledger,value)
        size=_json_size(value)
        pre.b._check(size<=self.ledger.p.max_text_utf8_bytes,'receipt.json',pre.ErrorCode.INPUT_LIMIT_EXCEEDED)
        self.ledger.take('text_bytes',size,self.ledger.p.max_total_input_utf8_bytes)
        return json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False)

    def span(self, artifact, span, lines):
        raw=self.raw[artifact]
        start,end=span
        _require(type(start) is int and type(end) is int and 0<=start<end<=len(raw),
                 'receipt.span.bounds',pre.ErrorCode.SCHEMA_INVALID)
        actual=(raw.count(b'\n',0,start)+1,raw.count(b'\n',0,end-1)+1)
        _require(tuple(lines)==actual,'receipt.span.lines',pre.ErrorCode.SCHEMA_INVALID)
        args=(start,end,*actual)
        source._charge(self.ledger,args)
        return pre.SourceSpan(*args)

    def add(self,artifact,pair,path,literals,spans,expected,actual,result='checked'):
        _require(bool(spans),'receipt.span.missing',pre.ErrorCode.SCHEMA_INVALID)
        values=(artifact,pair,tuple(path),tuple(literals),tuple(spans),result,
                self._json(expected),self._json(actual))
        source._charge(self.ledger,values)  # before FieldCheck/list retention
        self.checks.append(pre.FieldCheck(*values))

    def source_check(self, record, name, expected, actual):
        numeric=(record.footprint_at,record.pad_at,record.pad_size)
        if name.startswith(('request.center','request.width','request.height','request.angle',
                            'observation.footprint','observation.local','observation.center',
                            'observation.width','observation.height','observation.angle')):
            selected=[(v[0],v[1],v[2]) for fields in numeric for v in fields]
        elif name.endswith('parent_uuid'):
            selected=[(n.values,n.span,n.lines) for n in record.footprint_nodes
                      if n.path==('kicad_pcb','footprint','uuid')]
        elif name.startswith('footprint.'):
            selected=[(f.values,f.span,f.lines) for f in record.footprint_fields if f.name==name.split('.')[-1]]
        elif 'layer' in name:
            selected=[(n.values,n.span,n.lines) for n in record.nodes if n.path==('pad','layers')]
        else:
            index=0 if 'number' in name else 1 if 'type' in name else 2
            selected=[(((record.number,record.pad_type,record.shape)[index],),(a,b),lines)
                      for (a,b),lines in record.header_fields[index:index+1]]
        spans=tuple(self.span('pcb',s,ln) for _,s,ln in selected)
        for values,(start,end),_ in selected:
            literal=self.raw['pcb'][start:end].decode('utf-8')
            # Selected direct leaf fields have no descendants or escaped strings.
            # Compare retained values to the exact span, never just its valid range.
            tokens=re.findall(r'"[^"\\]*"|[^\s()]+',literal)
            tokens=tuple(x[1:-1] if x.startswith('"') else x for x in tokens)
            observed=tokens[1:] if literal.startswith('(') else tokens
            _require(observed==tuple(values),'receipt.span.literal',pre.ErrorCode.SCHEMA_INVALID)
        literals=tuple(self.raw['pcb'][s.start_byte:s.end_byte].decode('utf-8') for s in spans)
        self.add('pcb',pre.SourcePair(record.parent_uuid,record.pad_uuid),
                 ('source-comparison',name),literals,spans,expected,actual)

    def source_coverage(self, records):
        # Called only after all source structural/coverage/field gates have passed.
        for r in records:
            pair=pre.SourcePair(r.parent_uuid,r.pad_uuid)
            for n in r.nodes+r.footprint_nodes:
                coverage=getattr(n,'coverage',getattr(n,'semantics','semantics-unchecked'))
                result='checked' if coverage=='existing-semantic-gate' else 'semantics-unchecked'
                literal=(self.raw['pcb'][n.span[0]:n.span[1]].decode('utf-8'),) if n.values else ()
                self.add('pcb',pair,('source-coverage',)+n.path,literal,
                         (self.span('pcb',n.span,n.lines),),coverage,coverage,result)
            # Absence has no token span: record enclosing selected pad scope explicitly.
            for m in r.modifiers:
                self.add('pcb',pair,('enclosing-pad-absence',)+m.path,(),
                         (self.span('pcb',r.span,r.lines),),'absent',m.status)

    def parsed_json(self, artifact, payload):
        # Parsing/schema gates own payloads. No duplicate parse or retained JSON graph.
        _require(artifact in self.raw and type(payload) is dict,'receipt.json.artifact')

    def json_check(self, artifact, parent, pad, field, expected, actual):
        if field.startswith('observation.') or field.startswith('request.'):
            artifact='observation'
        group=artifact[:2] if artifact.startswith(('C1_','C2_')) else None
        pairs=[p for i,p in enumerate(pre.PAIRS)
               if (parent is None or p.parent_uuid==parent) and (pad is None or p.pad_uuid==pad)
               and (group is None or (i<2)==(group=='C1'))]
        raw=self.raw[artifact]
        span=self.span(artifact,(0,len(raw)),(1,raw.count(b'\n',0,len(raw)-1)+1))
        for pair in pairs:
            self.add(artifact,pair,('json-enclosing-pointer:', 'comparison',field),(),
                     (span,),expected,actual)

    def json_conflict(self, artifact, parent, pad, field, expected, actual):
        """Bounded failure provenance; the JSON document span is enclosing only."""
        if field.startswith(('observation.', 'request.')):
            artifact='observation'
        raw=self.raw[artifact]
        span=self.span(artifact,(0,len(raw)),(1,raw.count(b'\n',0,len(raw)-1)+1))
        digest=next(a.sha256 for a in self.ledger.artifacts if a.artifact_id==artifact)
        context=tuple((k,v) for k,v in (
            ('artifact_sha256',digest),('parent_uuid',parent),('pad_uuid',pad),
            ('span_kind','json-document-enclosing'),('json_pointer','""'),
            ('comparison_locator',field),
            ('enclosing_span',self._json((span.start_byte,span.end_byte))),
            ('line_range',self._json((span.first_line,span.last_line)))) if v is not None)
        args=(pre.ErrorCode.SOURCE_CONFLICT,'Declaration differs from pinned observation artifact.',
              field,'Correct the declaration; preserve artifact bytes.')
        expected_json=self._json(expected);actual_json=self._json(actual)
        source._charge(self.ledger,(args,artifact,pad,expected_json,actual_json,context))
        return pre.ContractError(*args,artifact_id=artifact,entity_id=pad,
            expected=expected_json,actual=actual_json,context=context)


def _context(request, declarations):
    """Pure contextual validation; never call any binding/candidate entrypoint."""
    c=pre.c
    c._require(request.schema_version=='rect-pad-candidate-v1','schema_version')
    c._id(request.board_id,'board_id');c._id(request.candidate_scope_id,'candidate_scope_id')
    c._frame(request.target_frame,request)
    inventory=c._inventory(request.inventory)
    parents={p.footprint_id:p for p in request.parents}
    pads={p.pad_id:p for p in request.pads}
    seen=set()
    for p in sorted(request.parents,key=lambda p:p.footprint_id):
        c._id(p.footprint_id,'parent.id')
        c._parent_geometry(p,request)
        _require(p.coordinate_basis=='board-source','parent.coordinate_basis',pre.ErrorCode.GEOMETRY_UNSUPPORTED)
        _require(p.source_to_p.matrix==((1,0,0),(0,1,0),(0,0,1)),
                 'parent.normalized-datum',pre.ErrorCode.GEOMETRY_UNSUPPORTED)
    evidence_ids=set()
    for e in sorted(declarations,key=lambda e:(e.canonical_pad_id,e.evidence_id)):
        for name in ('evidence_id','canonical_parent_id','canonical_pad_id','source_parent_id','source_pad_id'):
            c._id(getattr(e,name),name)
        _require(e.evidence_id not in evidence_ids,'evidence_id',pre.ErrorCode.DUPLICATE_ID)
        evidence_ids.add(e.evidence_id)
        _require(e.canonical_pad_id in pads and e.canonical_pad_id not in seen,'boundary.pad')
        seen.add(e.canonical_pad_id)
        p=pads[e.canonical_pad_id]
        c._id(p.pad_id,'pad.id')
        _require(p.footprint_id in parents,'pad.parent')
        parent=parents[p.footprint_id]
        _require(e.canonical_parent_id==p.footprint_id,'boundary.parent')
        _require(e.source_parent_id==p.source_parent_entity_id==parent.source_entity_id==e.membership.source_parent_id,'source.parent')
        _require(e.source_pad_id==p.source_entity_id==e.membership.source_pad_id,'source.pad')
        _require(e.coordinate_basis=='board-source-normalized','boundary.coordinate_basis')
        _require(e.side==p.side==parent.side=='top' and e.copper_layer=='F.Cu','side',pre.ErrorCode.GEOMETRY_UNSUPPORTED)
        _require(e.producer_identity=='pcbnew' and e.producer_version=='10.0.7'
                 and e.protocol_version=='C1-C2-pinned-boundary','boundary.producer')
        for record in (parent,p):
            _require(record.artifact_id=='pcb','record.artifact')
            c._provenance(record.provenance,'pcb',record.source_entity_id,inventory,request.inventory.inventory.manifest)
        c._evidence(parent.convention_evidence,inventory)
        c._frame(p.source_frame,request,True);c._frame(e.boundary_frame,request,True)
        require_same_frame(p.source_frame,parent.source_frame,'pad.source_frame')
        require_same_frame(p.rectangle.center.frame,p.source_frame,'pad.center.frame')
        require_same_frame(e.boundary_to_p.from_frame,e.boundary_frame,'boundary.source_frame')
        require_same_frame(e.boundary_to_p.to_frame,request.target_frame,'boundary.target_frame')
        e.boundary_to_p._require_validated_conventions();e.boundary_to_p._validate_isometry()
        _require(e.boundary_to_p.kind==parent.source_to_p.kind and e.boundary_to_p.matrix==parent.source_to_p.matrix,
                 'boundary.normalized-datum',pre.ErrorCode.GEOMETRY_UNSUPPORTED)
        _require(len(e.contours)==1 and len(e.contours[0].vertices)==4 and e.contours[0].closed
                 and e.contours[0].hole_count==0,'boundary.topology',pre.ErrorCode.GEOMETRY_UNSUPPORTED)
        for v in e.contours[0].vertices: require_same_frame(v.frame,e.boundary_frame,'boundary.vertex.frame')
        _require(len(e.coverage)==8 and {x.category for x in e.coverage}==set(pre.b.CATEGORIES),'coverage.categories')
        refs=(e.source,e.observation,e.boundary)+e.auxiliary_evidence+e.membership.audit_refs
        _require((e.membership.verifier_identity is None and e.membership.verifier_version is None)
                 or (bool(e.membership.verifier_identity) and bool(e.membership.verifier_version)),
                 'membership.verifier',pre.ErrorCode.SCHEMA_INVALID)
        for x in e.coverage:
            _require(x.status in ('unknown','observed-supported') and
                     x.basis in ('caller-declaration','API-observation','source-audit'),'coverage',pre.ErrorCode.GEOMETRY_UNSUPPORTED)
            refs+=x.evidence
        for ref in refs:
            c._id(ref.artifact_id,'reference.artifact_id');c._id(ref.locator,'reference.locator')
            _require(ref.artifact_id in inventory and
                     ref.computed_sha256==inventory[ref.artifact_id].computed_sha256,'reference.hash')
    _require(seen==set(pads),'boundary.pairs')


def prepare_source_checked_pad_request(admitted_bytes, inventory, declarations, caller_context, profile, limits):
    """Recheck bytes, construct complete immutable audit records, or fail atomically.

    Exact public v1 inputs/outputs are preserved. Receipt status is audit scope,
    not source authentication, import readiness or a transferable capability.
    """
    ledger=pre.Ledger()
    receipt=_Receipt(ledger)
    try:
        result=boundaries._check_boundary_records(admitted_bytes,inventory,declarations,caller_context,
            profile,limits,ledger,recorder=receipt)
        if isinstance(result,pre.PreparationFailure):return result
        ctx=caller_context
        request_args=(ctx.schema_version,ctx.candidate_policy,ctx.board_id,
            ctx.candidate_scope_id,ctx.target_frame,inventory,
            tuple(sorted(declarations.parents,key=lambda p:p.footprint_id)),
            tuple(sorted(declarations.pads,key=lambda p:p.pad_id)))
        source._charge(ledger,request_args)
        request=pre.c.PadCandidateRequest(*request_args)
        # All supplied geometric declarations were compared, not silently repaired.
        by_pair={(r.parent_uuid,r.pad_uuid):r for r in result.records}
        rebuilt=[]
        for e in sorted(declarations.boundaries,key=lambda e:e.canonical_pad_id):
            r=by_pair[e.source_parent_id,e.source_pad_id]
            source._charge(ledger,r.normalized_vertices_mm)
            points=tuple(pre.c.Point2(x,y,e.boundary_frame) for x,y in r.normalized_vertices_mm)
            source._charge(ledger,(points,r.closed,r.hole_count))
            contour=pre.b.BoundaryContour(points,r.closed,r.hole_count)
            source._charge(ledger,(e,contour))
            rebuilt.append(replace(e,contours=(contour,)))
        normalization=[]
        for r in result.source_result.records:
            for field,values in (('footprint.at',r.footprint_at),('pad.at',r.pad_at),('pad.size',r.pad_size)):
                for _,span,lines,_ in values:
                    receipt.span('pcb',span,lines)
                    locator=f'byte:{span[0]}:{span[1]};{field};mm;Y-once;cardinal-world-angle;order=3,2,1,0'
                    args=('pcb',pre.PINS[0].sha256,locator)
                    source._charge(ledger,args)
                    ledger.take('refs',1,ledger.p.max_total_evidence_refs)
                    normalization.append(pre.c.EvidenceReference(*args))
        checks=tuple(sorted(receipt.checks,key=lambda x:(x.artifact_id,x.source_pair.parent_uuid,
            x.source_pair.pad_uuid,x.path,tuple((s.start_byte,s.end_byte) for s in x.spans))))
        args=(pre.PROFILE,'c1-c2-source-declaration-checker','1',
              tuple(sorted(ledger.artifacts,key=lambda a:a.artifact_id)),
              tuple(sorted(pre.PAIRS,key=lambda p:(p.parent_uuid,p.pad_uuid))),checks,tuple(normalization),UNCHECKED)
        source._charge(ledger,args)
        evidence=pre.SourceCheckEvidence(*args)
        report_args=('source-preparation',pre.PROFILE.profile_id,(),())
        source._charge(ledger,report_args)
        report=pre.ValidationReport(*report_args)
        output=(request,tuple(rebuilt),evidence,report)
        source._charge(ledger,output)
        return pre.PreparedRequest(*output)
    except pre.b._Reject as error:
        if error.code is not pre.ErrorCode.INPUT_LIMIT_EXCEEDED:
            return source._failure(pre.ContractError(error.code,'Preparation rejected.',error.field,'Correct bounded inputs.'))
        sink=pre.c._Issues(pre.C_POLICY)
        try:sink.exhaust(error.field)
        except pre.c._Stop:pass
        return pre.PreparationFailure(pre.ValidationReport('source-preparation',pre.PROFILE.profile_id,
            tuple(sink.issues),()),sink.truncation)
    except GeometryError as error:
        return source._failure(pre.ContractError.from_geometry_error(error,remediation='Correct preparation declarations/provenance.'))
