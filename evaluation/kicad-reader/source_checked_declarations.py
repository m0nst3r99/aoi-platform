"""Source-check intermediate for fixed C1+C2; no receipt or candidate execution."""
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
import json
import source_checked_preflight as pre
import c1_c2_source_membership as source
from c1_c2_source_pose import source_pose, SourcePose
from observation_schema import schema


@dataclass(frozen=True, slots=True)
class SourceDeclarationCheckSuccess:
    records: tuple[source.SourceRecord, ...]
    poses: tuple[SourcePose, ...]
    nodes: int
    text_bytes: int
    evidence_refs: int
    hashed_bytes: int
    @property
    def status(self): return 'selected-source-declarations-intermediate-only'
    @property
    def completeness(self): return 'not-verified'
    @property
    def effective_copper_geometry(self): return 'not-verified'


def _charge(ledger, value):
    """Internal reconstructed metadata only; charge before storing in result/record.

    Scanner transient stack/tokens retain their separate bounds. Repeated retained
    values count by occurrence, including repeated footprint data in pad records.
    """
    stack=[(value,0)]
    while stack:
        value,depth=stack.pop()
        ledger.take('nodes',1,ledger.p.max_nodes)
        pre.b._check(depth<=ledger.p.max_depth,'budget.source_depth',pre.ErrorCode.INPUT_LIMIT_EXCEEDED)
        if type(value) is str: ledger.text(value,'detail')
        elif type(value) is bytes: ledger.take('text_bytes',len(value),ledger.p.max_total_input_utf8_bytes)
        elif type(value) is Decimal: ledger.text(str(value),'detail')
        elif type(value) in (tuple,list):
            pre.b._check(ledger.nodes+len(stack)+len(value)<=ledger.p.max_nodes,'budget.nodes',pre.ErrorCode.INPUT_LIMIT_EXCEEDED)
            stack.extend((v,depth+1) for v in reversed(value))
        elif type(value) is dict:
            pre.b._check(ledger.nodes+len(stack)+2*len(value)<=ledger.p.max_nodes,'budget.nodes',pre.ErrorCode.INPUT_LIMIT_EXCEEDED)
            for k,v in value.items():stack.extend(((k,depth+1),(v,depth+1)))
        elif is_dataclass(value):
            fs=fields(value)
            pre.b._check(ledger.nodes+len(stack)+len(fs)<=ledger.p.max_nodes,'budget.nodes',pre.ErrorCode.INPUT_LIMIT_EXCEEDED)
            stack.extend((getattr(value,f.name),depth+1) for f in fs)
        else: pre.b._check(value is None or type(value) in (bool,int,float),'source.metadata')


def _failure(issue):
    # Use the accepted diagnostic sink/reservation for source diagnostics too.
    sink=pre.c._Issues(pre.C_POLICY)
    try:
        size=len(pre.c.diagnostic_json(issue.to_dict()).encode('utf-8'))
        if size>pre.C_POLICY.max_diagnostic_utf8_bytes:sink.exhaust('issue_bytes')
        else:sink.issues.append(issue)
    except pre.c._Stop:pass
    return pre.PreparationFailure(pre.ValidationReport('source-declarations',pre.PROFILE.profile_id,
        tuple(sink.issues),()),sink.truncation)


def _check_source(admitted_bytes, inventory, declarations, caller_context, profile, limits, ledger):
    verified=pre._verify_bytes(admitted_bytes,inventory,declarations,caller_context,profile,limits,ledger)
    if isinstance(verified,pre.PreparationFailure):return verified
    raw={item.artifact_id:item.data for item in admitted_bytes}  # eight references; no copies
    try:
        records=source._scan_checked(raw['pcb'],charge=lambda v:_charge(ledger,v),
                                     verified_digest=source.PCB_HASH)
        if isinstance(records,source.SourceFailure):return _failure(records.diagnostic)
        for gate in (source.check_footprint_fields,source.check_footprint_coverage,source.check_graphics_layers):
            rejected=gate(records,source.PCB_HASH)
            if rejected is not None:return _failure(rejected.diagnostic)
        # Exact pinned JSON has bounded length and known depth, not arbitrary input.
        observation=json.loads(raw['observation'])
        _charge(ledger,observation)
        schema(observation)  # strict-v2; no legacy opt-in
        ctx=caller_context
        request=pre.c.PadCandidateRequest(ctx.schema_version,ctx.candidate_policy,ctx.board_id,
            ctx.candidate_scope_id,ctx.target_frame,inventory,declarations.parents,declarations.pads)
        rejected=source.check_source_records(records,request,declarations.boundaries,observation)
        if rejected is not None:return _failure(rejected.diagnostic)
        poses=[]
        for record in records:
            pose=source_pose(record)  # bounded cardinal arithmetic; checked above
            _charge(ledger,pose)
            poses.append(pose)
        return SourceDeclarationCheckSuccess(records,tuple(poses),ledger.nodes,ledger.text_bytes,
                                              ledger.refs,ledger.hashed_bytes)
    except pre.b._Reject as error:
        sink=pre.c._Issues(pre.C_POLICY)
        try:sink.exhaust(error.field)
        except pre.c._Stop:pass
        return pre.PreparationFailure(pre.ValidationReport('source-declarations',pre.PROFILE.profile_id,
            tuple(sink.issues),()),sink.truncation)


def check_source_declarations(admitted_bytes, inventory, declarations, caller_context, profile, limits):
    return _check_source(admitted_bytes,inventory,declarations,caller_context,profile,limits,pre.Ledger())
