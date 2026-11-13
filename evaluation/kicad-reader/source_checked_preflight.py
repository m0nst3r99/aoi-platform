"""Pinned preparation structural preflight; no hashing, source scan or execution."""
from dataclasses import dataclass, fields
from typing import Literal, Union, get_args, get_origin, get_type_hints
from types import UnionType
from math import isfinite
from hashlib import sha256
from aoi_platform import pad_candidates as c
from aoi_platform import boundary_evidence as b
from aoi_platform.geometry.reports import ValidationReport, ContractError
from aoi_platform.geometry.errors import ErrorCode

@dataclass(frozen=True, slots=True)
class ArtifactPin:
    artifact_id: str
    size_bytes: int
    sha256: str

@dataclass(frozen=True, slots=True)
class SourcePair:
    parent_uuid: str
    pad_uuid: str

@dataclass(frozen=True, slots=True)
class AdmittedArtifactBytes:
    artifact_id: str
    data: bytes

AdmittedBytes = tuple[AdmittedArtifactBytes, ...]

@dataclass(frozen=True, slots=True)
class SourceDeclarations:
    parents: tuple[c.PadParent, ...]
    pads: tuple[c.SourcePad, ...]
    boundaries: tuple[b.BoundaryEvidence, ...]

@dataclass(frozen=True, slots=True)
class CallerContext:
    schema_version: str
    board_id: str
    candidate_scope_id: str
    target_frame: c.Frame
    candidate_policy: c.SyntheticPadPolicy
    boundary_policy: b.BoundaryBindingPolicy

@dataclass(frozen=True, slots=True)
class SourceCheckProfile:
    profile_id: str
    version: str
    pins: tuple[ArtifactPin, ...]
    pairs: tuple[SourcePair, ...]

@dataclass(frozen=True, slots=True)
class PreparationLimits:
    candidate_policy: c.SyntheticPadPolicy
    boundary_policy: b.BoundaryBindingPolicy
    max_artifacts: int
    max_total_bytes: int
    scanner_max_depth: int
    scanner_max_token_bytes: int
    scanner_max_tokens: int

@dataclass(frozen=True, slots=True)
class SourceSpan:
    start_byte: int
    end_byte: int
    first_line: int
    last_line: int

@dataclass(frozen=True, slots=True)
class FieldCheck:
    artifact_id: str
    source_pair: SourcePair
    path: tuple[str, ...]
    literals: tuple[str, ...]
    spans: tuple[SourceSpan, ...]
    result: Literal['checked', 'semantics-unchecked']
    expected_json: str
    actual_json: str

@dataclass(frozen=True, slots=True)
class SourceCheckEvidence:
    profile: SourceCheckProfile
    verifier_id: Literal['c1-c2-source-declaration-checker']
    verifier_version: Literal['1']
    artifacts: tuple[ArtifactPin, ...]
    pairs: tuple[SourcePair, ...]
    checks: tuple[FieldCheck, ...]
    normalization: tuple[c.EvidenceReference, ...]
    unchecked_categories: tuple[str, ...]
    @property
    def status(self): return 'selected-source-declarations-checked'

@dataclass(frozen=True, slots=True)
class PreparedRequest:
    request: c.PadCandidateRequest
    boundary_declarations: tuple[b.BoundaryEvidence, ...]
    source_check: SourceCheckEvidence
    report: ValidationReport

@dataclass(frozen=True, slots=True)
class PreparationFailure:
    report: ValidationReport
    truncation: c.PadTruncation

@dataclass(frozen=True, slots=True)
class PreparationPreflightSuccess:
    nodes: int
    text_bytes: int
    evidence_refs: int
    raw_bytes: int
    @property
    def status(self): return 'preflight-only-bytes-not-hash-verified'

PINS = (
    ArtifactPin('pcb', 912379, '67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0'),
    ArtifactPin('observation', 196944, 'cd3734ece758d2611b44dc89cec2c88e439ba2d5585024d484671645ed7725b9'),
    ArtifactPin('C1_boundary', 1689, '9cd1d26d7756d81fc91d81712be01cba295a742ece11f9847c83866b897748b2'),
    ArtifactPin('C1_report', 813, 'ae359be006e70c9b6d97b87d80b250d365b27b8196b3d230d1d21954f90852cc'),
    ArtifactPin('C1_transport', 1354, '003d26bee58ac17377275ca8e5c74d5dc4c9a57038b35f0e0a282f047537da07'),
    ArtifactPin('C2_boundary', 1689, 'a8134211861f9f2709330e6d8e4c8185662e3d58f153895dbf5811270329b176'),
    ArtifactPin('C2_report', 813, '098fc91d66b941f1c02fbeb4177816026837c40ed014a69bd9872ecbaa57d7ae'),
    ArtifactPin('C2_transport', 1355, '3a1381fa096b973de18f9fc9c96130775da0da8771d03803a516ee4f0c5b8d2e'),
)
PAIRS = (
    SourcePair('00000000-0000-0000-0000-00005bd482c8','e2743daf-d278-4538-a77e-8f62f1b7978c'),
    SourcePair('00000000-0000-0000-0000-00005bd482c8','4e53dd71-4be4-4973-9c48-191e7b2e27bb'),
    SourcePair('00000000-0000-0000-0000-00005bd482e1','21e4d927-86ab-439d-8b84-9241bc089b89'),
    SourcePair('00000000-0000-0000-0000-00005bd482e1','fc38c22a-efcb-4dfc-b42c-80a66f75e1a4'),
)
PROFILE = SourceCheckProfile('c1-c2-source-checked-request-v1','1',PINS,PAIRS)
C_POLICY = c.SyntheticPadPolicy(*c._POLICY)
B_POLICY = b.BoundaryBindingPolicy(*b._POLICY)
LIMITS = PreparationLimits(C_POLICY,B_POLICY,8,1117036,128,65536,500000)
_NEW = {ArtifactPin,SourcePair,AdmittedArtifactBytes,SourceDeclarations,CallerContext,
        SourceCheckProfile,PreparationLimits}
_ALLOWED = b._ALLOWED | _NEW | {c.SyntheticPadPolicy,b.BoundaryBindingPolicy}
_HINTS = {cls:get_type_hints(cls) for cls in _ALLOWED}


def _matches(value, annotation):
    origin=get_origin(annotation); args=get_args(annotation)
    if origin in (Union,UnionType): return any(_matches(value,a) for a in args)
    if origin is Literal: return any(type(value) is type(a) and value==a for a in args)
    if origin is tuple: return type(value) is tuple
    # Existing geometry models intentionally accept integer real coordinates.
    if annotation is float: return type(value) in (int,float)
    return type(value) is annotation


class Ledger(b._Budget):
    def __init__(self):
        super().__init__(B_POLICY)
        self.raw_bytes=0
        self.hashed_bytes=0

    def walk(self, roots):
        stack=[(v,t,name,0) for v,t,name in reversed(roots)]
        while stack:
            v,t,name,depth=stack.pop()
            self.take('nodes',1,self.p.max_nodes)
            b._check(depth<=self.p.max_depth,'budget.depth',ErrorCode.INPUT_LIMIT_EXCEEDED)
            b._check(_matches(v,t),name)
            origin=get_origin(t)
            if origin in (Union,UnionType):
                t=next(a for a in get_args(t) if _matches(v,a)); origin=get_origin(t)
            if type(v) is str: self.text(v,name)
            elif type(v) is bytes:
                b._check(len(v)<=912379,'budget.artifact_bytes',ErrorCode.INPUT_LIMIT_EXCEEDED)
                self.take('raw_bytes',len(v),1117036)
            elif type(v) is tuple:
                cap={'parents':2,'pads':4,'boundaries':4,'pins':8,'pairs':4,'admitted_bytes':8,
                     'artifacts':8,'coverage':8,'contours':1,'vertices':4}.get(name,16 if name in b._REFS else self.p.max_total_evidence_refs)
                b._check(len(v)<=cap,'budget.'+name,ErrorCode.INPUT_LIMIT_EXCEEDED)
                args=get_args(t)
                if not args: types=(object,)*len(v)
                elif len(args)==2 and args[1] is Ellipsis: types=(args[0],)*len(v)
                else:
                    b._check(len(v)==len(args),name); types=args
                b._check(self.nodes+len(stack)+len(v)<=self.p.max_nodes,'budget.nodes',ErrorCode.INPUT_LIMIT_EXCEEDED)
                stack.extend((x,a,name,depth+1) for x,a in reversed(tuple(zip(v,types))))
            elif type(v) in _ALLOWED:
                if type(v) in (b.ArtifactRef,c.EvidenceReference): self.take('refs',1,self.p.max_total_evidence_refs)
                fs=fields(v)
                b._check(self.nodes+len(stack)+len(fs)<=self.p.max_nodes,'budget.nodes',ErrorCode.INPUT_LIMIT_EXCEEDED)
                for f in reversed(fs):
                    b._check(hasattr(v,f.name),name+'.'+f.name)
                    stack.append((getattr(v,f.name),_HINTS[type(v)][f.name],f.name,depth+1))
            elif type(v) is float: b._check(isfinite(v),name)
            elif type(v) is int: b._check(v.bit_length()<=1024,name)
            # Enums, bool and None already matched their exact annotated type.


def _exact_policy(value, expected, field):
    b._check(type(value) is type(expected),field,ErrorCode.POLICY_INVALID)
    for f in fields(expected):
        b._check(hasattr(value,f.name),field,ErrorCode.POLICY_INVALID)
        x=getattr(value,f.name); y=getattr(expected,f.name)
        if type(y) in (c.SyntheticPadPolicy,b.BoundaryBindingPolicy):
            _exact_policy(x,y,field+'.'+f.name)
        else: b._check(type(x) is type(y) and x==y,field+'.'+f.name,ErrorCode.POLICY_INVALID)


def _unique(values, field):
    b._check(len(values)==len(set(values)),field,ErrorCode.DUPLICATE_ID)


def _preflight(admitted_bytes, inventory, declarations, caller_context,
               profile, limits, ledger):
    """Structural/pin declarations only; success is NOT admission or source verification."""
    try:
        _exact_policy(limits,LIMITS,'limits')
        b._check(type(caller_context) is CallerContext,'caller_context')
        b._check(hasattr(caller_context,'candidate_policy') and hasattr(caller_context,'boundary_policy'),'caller_context')
        _exact_policy(caller_context.candidate_policy,C_POLICY,'candidate_policy')
        _exact_policy(caller_context.boundary_policy,B_POLICY,'boundary_policy')
        ledger.walk(((admitted_bytes,AdmittedBytes,'admitted_bytes'),
                     (inventory,c.InventorySuccess,'inventory'),
                     (declarations,SourceDeclarations,'declarations'),
                     (caller_context,CallerContext,'caller_context'),
                     (profile,SourceCheckProfile,'profile'),(limits,PreparationLimits,'limits')))
        b._check(profile.profile_id==PROFILE.profile_id and profile.version=='1','profile',ErrorCode.POLICY_INVALID)
        for rows,name in ((profile.pins,'pins'),(admitted_bytes,'admitted_bytes')):
            _unique(tuple(x.artifact_id for x in rows),name)
            b._check({x.artifact_id for x in rows}=={x.artifact_id for x in PINS},name,ErrorCode.SOURCE_CONFLICT)
        b._check(set(profile.pins)==set(PINS),'profile.pins',ErrorCode.SOURCE_CONFLICT)
        _unique(profile.pairs,'pairs')
        b._check(set(profile.pairs)==set(PAIRS),'profile.pairs',ErrorCode.SOURCE_CONFLICT)
        by_pin={p.artifact_id:p for p in PINS}
        for item in admitted_bytes:
            b._check(len(item.data)==by_pin[item.artifact_id].size_bytes,'bytes.size',ErrorCode.SOURCE_CONFLICT)
        b._check(len(declarations.parents)==2 and len(declarations.pads)==4 and len(declarations.boundaries)==4,'declarations.count')
        _unique(tuple(p.footprint_id for p in declarations.parents),'parent.id')
        _unique(tuple(p.pad_id for p in declarations.pads),'pad.id')
        pairs=tuple(SourcePair(p.source_parent_entity_id,p.source_entity_id) for p in declarations.pads)
        _unique(pairs,'pad.source_pair')
        b._check(set(pairs)==set(PAIRS),'pad.source_pairs',ErrorCode.SOURCE_CONFLICT)
        _unique(tuple(p.source_entity_id for p in declarations.parents),'parent.source_id')
        b._check({p.source_entity_id for p in declarations.parents}=={p.parent_uuid for p in PAIRS},'parent.source_ids',ErrorCode.SOURCE_CONFLICT)
        ep=tuple(SourcePair(e.source_parent_id,e.source_pad_id) for e in declarations.boundaries)
        _unique(ep,'boundary.source_pairs')
        b._check(set(ep)==set(PAIRS),'boundary.source_pairs',ErrorCode.SOURCE_CONFLICT)
        ctx=caller_context
        request=c.PadCandidateRequest(ctx.schema_version,ctx.candidate_policy,ctx.board_id,
            ctx.candidate_scope_id,ctx.target_frame,inventory,declarations.parents,declarations.pads)
        # Shape/consistency checker only: no preflight reset, binding or candidate call.
        b._binding_inputs(request)
        b._check(len(inventory.inventory.artifacts)==8,'inventory.count')
        for obs in inventory.inventory.artifacts:
            decl=obs.declaration
            b._check(decl.artifact_id in by_pin,'inventory.id',ErrorCode.SOURCE_CONFLICT)
            pin=by_pin[decl.artifact_id]
            b._check((decl.source_id,decl.declared_sha256,decl.declared_size,obs.computed_sha256,obs.actual_size)==
                     (pin.artifact_id,pin.sha256,pin.size_bytes,pin.sha256,pin.size_bytes),'inventory.pin',ErrorCode.SOURCE_CONFLICT)
            b._check(decl.role==('kicad_pcb' if pin.artifact_id=='pcb' else 'supporting') and
                     decl.reference_only is (pin.artifact_id!='pcb'),'inventory.role',ErrorCode.SOURCE_CONFLICT)
        return PreparationPreflightSuccess(ledger.nodes,ledger.text_bytes,ledger.refs,ledger.raw_bytes)
    except b._Reject as error:
        sink=c._Issues(C_POLICY)  # fixed fallback, never use rejected policy values
        exhausted=error.code is ErrorCode.INPUT_LIMIT_EXCEEDED
        if exhausted:
            try: sink.exhaust(error.field)
            except c._Stop: pass
        else:
            sink.issues.append(ContractError(error.code,'Preparation preflight rejected.',
                error.field,'Correct bounded inputs; no source checks have run.'))
        return PreparationFailure(ValidationReport('source-preflight',PROFILE.profile_id,
            tuple(sink.issues),()),sink.truncation)


def preflight_source_checked_request(admitted_bytes, inventory, declarations, caller_context,
                                     profile, limits):
    return _preflight(admitted_bytes, inventory, declarations, caller_context,
                      profile, limits, Ledger())


@dataclass(frozen=True, slots=True)
class ByteVerificationSuccess:
    nodes: int
    text_bytes: int
    evidence_refs: int
    raw_bytes: int
    hashed_bytes: int
    @property
    def status(self): return 'bytes-match-pins-and-inventory-only'


def _verify_bytes(admitted_bytes, inventory, declarations, caller_context,
                  profile, limits, ledger):
    """Same immutable buffers, same ledger; no source parsing or preparation receipt."""
    checked=_preflight(admitted_bytes,inventory,declarations,caller_context,profile,limits,ledger)
    if isinstance(checked,PreparationFailure): return checked
    observed={o.declaration.artifact_id:o for o in inventory.inventory.artifacts}
    pins={p.artifact_id:p for p in profile.pins}
    try:
        for item in sorted(admitted_bytes,key=lambda x:x.artifact_id):
            pin=pins[item.artifact_id]; obs=observed[item.artifact_id]
            ledger.take('hashed_bytes',len(item.data),limits.max_total_bytes)
            actual=sha256(item.data).hexdigest()
            # Hash output is retained/compared only after charging bounded metadata.
            ledger.text(actual,'computed_sha256')
            if (actual!=pin.sha256 or actual!=obs.computed_sha256 or
                len(item.data)!=pin.size_bytes or len(item.data)!=obs.actual_size):
                issue=ContractError(ErrorCode.SOURCE_CONFLICT,'Artifact bytes disagree.',
                    'bytes.sha256','Supply the pinned admitted bytes.',artifact_id=item.artifact_id,
                    expected=pin.sha256,actual=actual,context=(
                        ('inventory_sha256',obs.computed_sha256),
                        ('profile_size',str(pin.size_bytes)),('inventory_size',str(obs.actual_size)),
                        ('actual_size',str(len(item.data)))))
                return PreparationFailure(ValidationReport('source-bytes',PROFILE.profile_id,(issue,),()),
                    c.PadTruncation(False,None,None))
        return ByteVerificationSuccess(ledger.nodes,ledger.text_bytes,ledger.refs,
                                       ledger.raw_bytes,ledger.hashed_bytes)
    except b._Reject as error:
        sink=c._Issues(C_POLICY)
        try: sink.exhaust(error.field)
        except c._Stop: pass
        return PreparationFailure(ValidationReport('source-bytes',PROFILE.profile_id,
            tuple(sink.issues),()),sink.truncation)


def verify_source_checked_bytes(admitted_bytes, inventory, declarations, caller_context,
                                profile, limits):
    return _verify_bytes(admitted_bytes,inventory,declarations,caller_context,profile,limits,Ledger())
