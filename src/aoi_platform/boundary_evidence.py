"""Bounded declaration preflight only; no geometry matching or candidate execution."""
from dataclasses import dataclass, fields
from enum import Enum
from math import isfinite
from . import pad_candidates as candidate
from .geometry.models import Frame, Point2
from .geometry.transforms import Transform2
from .geometry.errors import ErrorCode, GeometryError
from .geometry.reports import ContractError, ValidationReport

CATEGORIES = ('shape','side','layer-effective-geometry','offset','per-layer-overrides','custom-primitives','drill','source-construct-completeness')

@dataclass(frozen=True, slots=True)
class BoundaryBindingPolicy:
    policy_id: str
    version: str
    max_pads: int
    max_parents: int
    max_inventory_artifacts: int
    max_bindings: int
    contours: int
    vertices: int
    holes: int
    coverage_categories: int
    correspondence_trials: int
    component_comparisons_per_pad: int
    component_comparisons_total: int
    comparison_abs_mm: float
    max_id_utf8_bytes: int
    max_text_utf8_bytes: int
    max_total_input_utf8_bytes: int
    max_evidence_refs_per_record: int
    max_total_evidence_refs: int
    max_depth: int
    max_nodes: int
    max_diagnostics: int
    max_diagnostic_utf8_bytes: int
    max_total_diagnostic_utf8_bytes: int
    max_abs_coordinate_mm: float
    max_dimension_mm: float
    min_dimension_mm: float
    max_abs_angle_deg: float
    rigid_guard_abs: float
    rigid_guard_rel: float

_POLICY = ('synthetic-rect-boundary-binding','1',4096,4096,1024,4096,1,4,0,8,8,64,262144,1e-6,256,1024,8388608,16,32768,32,2686976,128,4096,524288,1e6,1e6,1e-6,360000.,1e-12,0.)

@dataclass(frozen=True, slots=True)
class ArtifactRef:
    artifact_id: str
    computed_sha256: str
    locator: str

@dataclass(frozen=True, slots=True)
class ConstructCoverage:
    category: str
    status: str
    basis: str
    detail: str
    evidence: tuple[ArtifactRef, ...]

@dataclass(frozen=True, slots=True)
class MembershipEvidence:
    source_parent_id: str
    source_pad_id: str
    audit_refs: tuple[ArtifactRef, ...]
    verifier_identity: str | None
    verifier_version: str | None

@dataclass(frozen=True, slots=True)
class BoundaryContour:
    vertices: tuple[Point2, ...]
    closed: bool
    hole_count: int

@dataclass(frozen=True, slots=True)
class BoundaryEvidence:
    evidence_id: str
    source: ArtifactRef
    observation: ArtifactRef
    boundary: ArtifactRef
    auxiliary_evidence: tuple[ArtifactRef, ...]
    canonical_parent_id: str
    canonical_pad_id: str
    source_parent_id: str
    source_pad_id: str
    boundary_frame: Frame
    boundary_to_p: Transform2
    coordinate_basis: str
    contours: tuple[BoundaryContour, ...]
    copper_layer: str
    side: str
    producer_identity: str
    producer_version: str
    protocol_version: str
    coverage: tuple[ConstructCoverage, ...]
    membership: MembershipEvidence

@dataclass(frozen=True, slots=True)
class Assurance:
    @property
    def association_status(self): return 'declaration-consistent'
    @property
    def artifact_record_status(self): return 'supplied-declaration-unverified'
    @property
    def source_membership_status(self): return 'not-verified'
    @property
    def source_construct_coverage_status(self): return 'not-verified'
    @property
    def import_ready(self): return False
    @property
    def published(self): return False
    @property
    def targeting_authorized(self): return False

@dataclass(frozen=True, slots=True)
class PreflightSuccess(Assurance):
    nodes: int
    text_bytes: int
    evidence_refs: int
    @property
    def status(self): return 'preflight-only-not-bound'

@dataclass(frozen=True, slots=True)
class PreflightFailure:
    report: ValidationReport
    truncation: candidate.PadTruncation
    @property
    def status(self): return 'rejected'

class _Reject(Exception):
    def __init__(self, code, field): self.code, self.field = code, field

def _check(ok, field, code=ErrorCode.SCHEMA_INVALID):
    if not ok: raise _Reject(code,field)

def _policy(policy):
    _check(type(policy) is BoundaryBindingPolicy,'policy',ErrorCode.POLICY_INVALID)
    for f,expected in zip(fields(BoundaryBindingPolicy),_POLICY):
        actual=getattr(policy,f.name)
        _check(type(actual) is type(expected) and actual==expected,'policy.'+f.name,ErrorCode.POLICY_INVALID)

_ALLOWED = candidate._ALLOWED | {ArtifactRef,ConstructCoverage,MembershipEvidence,BoundaryContour,BoundaryEvidence}
_TEXT = {'detail','locator','net','source','message','remediation','expected','actual','source_snapshot','fixture_revision'}
_REFS = {'evidence','convention_evidence','auxiliary_evidence','audit_refs'}

class _Budget:
    def __init__(self,p): self.p=p; self.nodes=0; self.text_bytes=0; self.refs=0
    def take(self,kind,n,limit):
        value=getattr(self,kind)+n
        _check(value<=limit,'budget.'+kind,ErrorCode.INPUT_LIMIT_EXCEEDED)
        setattr(self,kind,value)
    def text(self,value,name):
        cap=self.p.max_text_utf8_bytes if name in _TEXT else self.p.max_id_utf8_bytes
        _check(len(value)<=cap,'budget.text',ErrorCode.INPUT_LIMIT_EXCEEDED)
        size=0
        for char in value:
            n=ord(char);_check(not 0xD800<=n<=0xDFFF,name)
            size+=1 if n<128 else 2 if n<2048 else 3 if n<65536 else 4
            _check(size<=cap,'budget.text',ErrorCode.INPUT_LIMIT_EXCEEDED)
        self.take('text_bytes',size,self.p.max_total_input_utf8_bytes)

def _walk(request,evidence,p):
    budget=_Budget(p)
    stack=[(evidence,'bindings',0),(request,'request',0)]
    while stack:
        v,name,depth=stack.pop()
        budget.take('nodes',1,p.max_nodes)
        _check(depth<=p.max_depth,'budget.depth',ErrorCode.INPUT_LIMIT_EXCEEDED)
        if type(v) is str: budget.text(v,name)
        elif type(v) is tuple:
            cap={'pads':p.max_pads,'parents':p.max_parents,'artifacts':p.max_inventory_artifacts,'bindings':p.max_bindings,'coverage':8,'contours':1,'vertices':4}.get(name,16 if name in _REFS else p.max_total_evidence_refs)
            _check(len(v)<=cap,'budget.'+name,ErrorCode.INPUT_LIMIT_EXCEEDED)
            _check(budget.nodes+len(stack)+len(v)<=p.max_nodes,'budget.nodes',ErrorCode.INPUT_LIMIT_EXCEEDED)
            stack.extend((x,name,depth+1) for x in reversed(v))
        elif type(v) in _ALLOWED:
            if type(v) in (ArtifactRef,candidate.EvidenceReference):budget.take('refs',1,p.max_total_evidence_refs)
            fs=fields(v)
            _check(budget.nodes+len(stack)+len(fs)<=p.max_nodes,'budget.nodes',ErrorCode.INPUT_LIMIT_EXCEEDED)
            stack.extend((getattr(v,f.name),f.name,depth+1) for f in reversed(fs))
        elif type(v) is int: _check(v.bit_length()<=1024,name)
        elif type(v) is float: _check(isfinite(v),name)
        elif v is None or type(v) is bool: pass
        elif type(v) in (candidate.FrameKind,candidate.Unit,candidate.AxisDirection,candidate.Parity,candidate.TransformKind,candidate.Code,candidate.ReportStatus,candidate.Severity): pass
        else: raise _Reject(ErrorCode.SCHEMA_INVALID,name)
    return budget

def preflight_boundary_evidence(request,evidence,policy):
    """Structural and resource admission only; no artifact/geometry binding claim."""
    try:
        _policy(policy)
        _check(type(request) is candidate.PadCandidateRequest,'request')
        _check(type(evidence) is tuple,'bindings')
        budget=_walk(request,evidence,policy)
        _check(type(request.policy) is candidate.SyntheticPadPolicy,'request.policy',ErrorCode.POLICY_INVALID)
        for f,expected in zip(fields(candidate.SyntheticPadPolicy),candidate._POLICY):
            value=getattr(request.policy,f.name)
            _check(type(value) is type(expected) and value==expected,'request.policy.'+f.name,ErrorCode.POLICY_INVALID)
        _check(type(request.inventory) is candidate.InventorySuccess,'inventory')
        _check(type(request.pads) is tuple and type(request.parents) is tuple and len(request.pads)>0,'request.pads')
        _check(len(evidence)==len(request.pads),'bindings')
        for e in evidence:
            _check(type(e) is BoundaryEvidence,'bindings.item')
            for name in ('evidence_id','canonical_parent_id','canonical_pad_id','source_parent_id','source_pad_id','producer_identity','producer_version','protocol_version'):
                _check(type(getattr(e,name)) is str and bool(getattr(e,name)),name)
            _check(type(e.boundary_frame) is Frame and type(e.boundary_to_p) is Transform2,'frame')
            _check(e.coordinate_basis=='board-source-normalized','coordinate_basis')
            _check(e.copper_layer=='F.Cu' and e.side=='top','layer',ErrorCode.GEOMETRY_UNSUPPORTED)
            _check(type(e.membership) is MembershipEvidence,'membership')
            m=e.membership
            _check(type(m.source_parent_id) is str and bool(m.source_parent_id) and type(m.source_pad_id) is str and bool(m.source_pad_id),'membership.identity')
            _check((m.verifier_identity is None and m.verifier_version is None) or (type(m.verifier_identity) is str and bool(m.verifier_identity) and type(m.verifier_version) is str and bool(m.verifier_version)),'membership.verifier')
            _check(type(e.contours) is tuple and len(e.contours)==1,'contours',ErrorCode.GEOMETRY_UNSUPPORTED)
            c=e.contours[0];_check(type(c) is BoundaryContour,'contour')
            _check(c.closed is True and type(c.hole_count) is int and c.hole_count==0,'topology',ErrorCode.GEOMETRY_UNSUPPORTED)
            _check(type(c.vertices) is tuple and len(c.vertices)==4 and all(type(v) is Point2 for v in c.vertices),'vertices')
            _check(type(e.coverage) is tuple and len(e.coverage)==8,'coverage')
            _check(all(type(x) is ConstructCoverage for x in e.coverage),'coverage.item')
            _check({x.category for x in e.coverage}==set(CATEGORIES),'coverage.categories')
            refs=[e.source,e.observation,e.boundary]
            for collection in (e.auxiliary_evidence,m.audit_refs):
                _check(type(collection) is tuple,'references');refs.extend(collection)
            for x in e.coverage:
                _check(x.status in ('unknown','observed-supported','observed-unsupported') and x.basis in ('caller-declaration','API-observation','source-audit') and type(x.detail) is str,'coverage')
                _check(x.status!='observed-unsupported','coverage',ErrorCode.GEOMETRY_UNSUPPORTED)
                _check(type(x.evidence) is tuple,'coverage.evidence');refs.extend(x.evidence)
            for ref in refs:
                _check(type(ref) is ArtifactRef,'reference')
                _check(type(ref.artifact_id) is str and bool(ref.artifact_id) and candidate._digest(ref.computed_sha256) and type(ref.locator) is str and bool(ref.locator),'reference')
        return PreflightSuccess(budget.nodes,budget.text_bytes,budget.refs)
    except _Reject as error:
        exhausted=error.code==ErrorCode.INPUT_LIMIT_EXCEEDED
        issue=ContractError(error.code,'Boundary preflight rejected.',error.field,'Correct bounded declarations and retry.')
        report=ValidationReport('boundary-preflight',_POLICY[0],(issue,),(),context=(('scope','preflight-only'),))
        return PreflightFailure(report,candidate.PadTruncation(exhausted,'input_budget' if exhausted else None,None))


@dataclass(frozen=True, slots=True)
class DeclarationBindingSuccess(Assurance):
    bindings: tuple[BoundaryEvidence, ...]
    report: ValidationReport
    @property
    def status(self): return 'declaration-binding-only-no-geometry-check'


def _binding_inputs(request):
    """Validate shapes before dereference; joint preflight already bounded traversal."""
    from .inventory import ArtifactInventory, ArtifactObservation, ArtifactDeclaration, InventoryManifest
    inv=request.inventory
    _check(type(inv) is candidate.InventorySuccess,'inventory')
    _check(type(inv.report) is ValidationReport,'inventory.report')
    _check(inv.report.status is candidate.ReportStatus.ACCEPTED and not inv.report.errors
           and not inv.report.unresolved_fields and not inv.report.conflicting_fields,'inventory.report',ErrorCode.SOURCE_CONFLICT)
    data=inv.inventory
    _check(type(data) is ArtifactInventory,'inventory.inventory')
    manifest=data.manifest
    _check(type(manifest) is InventoryManifest,'inventory.manifest')
    _check(type(manifest.artifacts) is tuple and type(data.artifacts) is tuple,'inventory.artifacts')
    _check(manifest.schema_version=='artifact-inventory-v1','inventory.schema')
    _check(type(manifest.fixture_revision) is str and bool(manifest.fixture_revision)
           and type(manifest.source_snapshot) is str and bool(manifest.source_snapshot),'inventory.provenance')
    declarations={}
    for decl in manifest.artifacts:
        _check(type(decl) is ArtifactDeclaration,'inventory.declaration')
        for key in ('artifact_id','role','source_id'):
            _check(type(getattr(decl,key)) is str and bool(getattr(decl,key)),'inventory.declaration.'+key)
        _check(candidate._digest(decl.declared_sha256),'inventory.declared_sha256')
        _check(decl.declared_size is None or (type(decl.declared_size) is int and decl.declared_size>=0),'inventory.declared_size')
        _check(decl.artifact_id not in declarations,'inventory.artifact_id',ErrorCode.DUPLICATE_ID)
        declarations[decl.artifact_id]=decl
    seen=set()
    for obs in data.artifacts:
        _check(type(obs) is ArtifactObservation,'inventory.observation')
        _check(type(obs.declaration) is ArtifactDeclaration,'inventory.observation.declaration')
        key=obs.declaration.artifact_id
        _check(type(key) is str,'inventory.observation.artifact_id')
        _check(key not in seen,'inventory.observation.artifact_id',ErrorCode.DUPLICATE_ID);seen.add(key)
        _check(key in declarations and obs.declaration==declarations[key],'inventory.manifest_observation',ErrorCode.SOURCE_CONFLICT)
        _check(obs.eof is True,'inventory.eof',ErrorCode.SOURCE_CONFLICT)
        _check(type(obs.bytes_read) is int and type(obs.actual_size) is int and obs.bytes_read>=0
               and obs.bytes_read==obs.actual_size,'inventory.size',ErrorCode.SOURCE_CONFLICT)
        _check(obs.declaration.declared_size is None or obs.actual_size==obs.declaration.declared_size,'inventory.declared_size',ErrorCode.SOURCE_CONFLICT)
        _check(candidate._digest(obs.computed_sha256) and obs.computed_sha256==obs.declaration.declared_sha256,'inventory.digest',ErrorCode.SOURCE_CONFLICT)
    _check(seen==set(declarations) and bool(seen),'inventory.artifacts',ErrorCode.SOURCE_CONFLICT)
    _check(type(request.target_frame) is Frame,'target_frame')
    for record in request.parents+request.pads:
        _check(type(record) in (candidate.PadParent,candidate.SourcePad),'record')
        _check(type(record.source_frame) is Frame,'record.source_frame')
        _check(type(record.provenance) is candidate.PadProvenance,'record.provenance')
        prov=record.provenance
        for key in ('artifact_id','source_id','computed_sha256','source_entity_id','source_snapshot','fixture_revision'):
            _check(type(getattr(prov,key)) is str and bool(getattr(prov,key)),'provenance.'+key)
        _check(type(prov.evidence) is tuple and all(type(ref) is candidate.EvidenceReference for ref in prov.evidence),'provenance.evidence')
        _check(prov.source_snapshot==manifest.source_snapshot and prov.fixture_revision==manifest.fixture_revision,'provenance.snapshot',ErrorCode.SOURCE_CONFLICT)
        if type(record) is candidate.PadParent:
            _check(type(record.source_to_p) is Transform2,'parent.source_to_p')
            _check(type(record.source_to_p.from_frame) is Frame and type(record.source_to_p.to_frame) is Frame,'parent.transform.frames')
        else:
            _check(type(record.rectangle) is candidate.PadRectangle,'pad.rectangle')
            _check(type(record.rectangle.center) is Point2 and type(record.rectangle.center.frame) is Frame,'pad.center')


def bind_boundary_declarations(request, evidence, policy):
    """Identity/hash/frame consistency only. Never decode artifacts or build candidates."""
    checked = preflight_boundary_evidence(request, evidence, policy)
    if isinstance(checked, PreflightFailure):
        return checked
    from .geometry.models import require_same_frame
    entity = None
    artifact = None
    def require(ok, field, code=ErrorCode.SOURCE_CONFLICT):
        _check(ok,field,code)
    try:
        _binding_inputs(request)
        inventory = {}
        for item in request.inventory.inventory.artifacts:
            key=item.declaration.artifact_id
            require(key not in inventory,'inventory.artifact_id',ErrorCode.DUPLICATE_ID)
            inventory[key]=item
        parents={}; pads={}
        for value in request.parents:
            require(type(value) is candidate.PadParent,'parents',ErrorCode.SCHEMA_INVALID)
            require(type(value.footprint_id) is str and bool(value.footprint_id),'parent.id',ErrorCode.SCHEMA_INVALID)
            require(value.footprint_id not in parents,'parent.id',ErrorCode.DUPLICATE_ID)
            parents[value.footprint_id]=value
        for value in request.pads:
            require(type(value) is candidate.SourcePad,'pads',ErrorCode.SCHEMA_INVALID)
            require(type(value.pad_id) is str and bool(value.pad_id),'pad.id',ErrorCode.SCHEMA_INVALID)
            require(value.pad_id not in pads,'pad.id',ErrorCode.DUPLICATE_ID)
            pads[value.pad_id]=value
        bound={}; ids=set()
        for e in sorted(evidence,key=lambda x:(x.canonical_pad_id,x.evidence_id)):
            entity=e.canonical_pad_id;artifact=e.source.artifact_id
            require(e.evidence_id not in ids,'evidence_id',ErrorCode.DUPLICATE_ID);ids.add(e.evidence_id)
            require(entity not in bound,'canonical_pad_id',ErrorCode.DUPLICATE_ID)
            require(entity in pads,'canonical_pad_id')
            pad=pads[entity]
            require(e.canonical_parent_id==pad.footprint_id and pad.footprint_id in parents,'canonical_parent_id')
            parent=parents[pad.footprint_id]
            require(e.source_parent_id==pad.source_parent_entity_id==parent.source_entity_id==e.membership.source_parent_id,'source_parent_id')
            require(e.source_pad_id==pad.source_entity_id==e.membership.source_pad_id,'source_pad_id')
            require(artifact==pad.artifact_id==parent.artifact_id,'source.artifact_id')
            refs=(e.source,e.observation,e.boundary)+e.auxiliary_evidence+e.membership.audit_refs
            refs+=tuple(ref for c in e.coverage for ref in c.evidence)
            for ref in refs:
                require(ref.artifact_id in inventory,'reference.artifact_id')
                require(ref.computed_sha256==inventory[ref.artifact_id].computed_sha256,'reference.computed_sha256')
            for record,source_id in ((parent,parent.source_entity_id),(pad,pad.source_entity_id)):
                prov=record.provenance
                require(prov.artifact_id==artifact and prov.computed_sha256==e.source.computed_sha256 and prov.source_entity_id==source_id,'provenance')
                require(prov.source_id==inventory[artifact].declaration.source_id,'provenance.source_id')
                for ref in prov.evidence:
                    require(ref.artifact_id in inventory and ref.computed_sha256==inventory[ref.artifact_id].computed_sha256,'provenance.evidence')
            require_same_frame(pad.source_frame,parent.source_frame,'pad.source_frame')
            require_same_frame(pad.rectangle.center.frame,pad.source_frame,'pad.center.frame')
            require_same_frame(parent.source_to_p.from_frame,parent.source_frame,'parent.transform.source')
            require_same_frame(parent.source_to_p.to_frame,request.target_frame,'parent.transform.target')
            require_same_frame(e.boundary_to_p.from_frame,e.boundary_frame,'boundary.transform.source')
            require_same_frame(e.boundary_to_p.to_frame,request.target_frame,'boundary.transform.target')
            for point in e.contours[0].vertices:require_same_frame(point.frame,e.boundary_frame,'boundary.vertex.frame')
            frames=(pad.source_frame,parent.source_frame,request.target_frame,e.boundary_frame)
            require(all(frame.board_revision_id==request.candidate_scope_id for frame in frames),'frame.board_revision_id',ErrorCode.CONTEXT_MISMATCH)
            for key in ('machine_id','capture_id'):
                require(len({getattr(frame,key) for frame in frames if getattr(frame,key) is not None})<=1,'frame.'+key,ErrorCode.CONTEXT_MISMATCH)
            bound[entity]=e
        require(set(bound)==set(pads),'bindings')
        report=ValidationReport('boundary-declaration-binding',policy.policy_id,(),(),context=(('scope','declarations-only-no-geometry'),))
        return DeclarationBindingSuccess(tuple(bound[k] for k in sorted(bound)),report)
    except (_Reject,GeometryError) as error:
        # Match candidate diagnostics: opaque whitespace IDs remain exact JSON
        # evidence; report text fields themselves require nonblank strings.
        context=tuple((key,candidate.diagnostic_json(value))
            for key,value in (('entity_id_json',entity),('artifact_id_json',artifact))
            if value is not None and not value.strip())
        diagnostic_entity=entity if entity and entity.strip() else None
        diagnostic_artifact=artifact if artifact and artifact.strip() else None
        if isinstance(error,GeometryError):
            issue=ContractError.from_geometry_error(error,remediation='Correct declared binding.',entity_id=diagnostic_entity,artifact_id=diagnostic_artifact,context=context)
        else:
            issue=ContractError(error.code,'Boundary declaration conflict.',error.field,'Correct declared binding.',entity_id=diagnostic_entity,artifact_id=diagnostic_artifact,context=context)
        # Existing diagnostic reservation handles oversized full-frame evidence.
        sink=candidate._Issues(candidate.SyntheticPadPolicy(*candidate._POLICY))
        try:
            size=len(candidate.diagnostic_json(issue.to_dict()).encode('utf-8'))
            if size>policy.max_diagnostic_utf8_bytes:sink.exhaust('issue_bytes')
            sink.issues.append(issue)
        except candidate._Stop:pass
        report=ValidationReport('boundary-declaration-binding',policy.policy_id,tuple(sink.issues),(),context=(('scope','declarations-only-no-geometry'),))
        return PreflightFailure(report,sink.truncation)
