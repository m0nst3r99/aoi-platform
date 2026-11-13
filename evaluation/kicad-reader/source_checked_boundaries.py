"""Pinned C1+C2 boundary checks; intermediate only, no receipt or execution."""
from dataclasses import dataclass
import json
import source_checked_preflight as pre
import source_checked_declarations as source
import c1_c2_artifact_binding as artifacts


@dataclass(frozen=True, slots=True)
class BoundaryArtifactLink:
    boundary_id: str
    boundary_sha256: str
    report_id: str
    report_sha256: str
    transport_id: str
    transport_sha256: str
    source_sha256: str


@dataclass(frozen=True, slots=True)
class BoundaryRecordCheckSuccess:
    source_result: source.SourceDeclarationCheckSuccess
    records: tuple[artifacts.ObservedBoundaryRecord, ...]
    links: tuple[BoundaryArtifactLink, ...]
    nodes: int
    text_bytes: int
    evidence_refs: int
    hashed_bytes: int

    @property
    def status(self): return 'selected-boundary-records-intermediate-only'
    @property
    def completeness(self): return 'not-verified'
    @property
    def effective_copper_geometry(self): return 'not-verified'


def _links_from_verified(raw, ledger):
    """Pinned report/transport checks, not runtime attestation or arbitrary JSON."""
    pins={p.artifact_id:p.sha256 for p in pre.PINS}
    links=[]
    artifact=None
    def equal(field, expected, actual):
        if expected!=actual or type(expected) is not type(actual):
            raise artifacts._Conflict(field,expected,actual)
    try:
        for group in ('C1','C2'):
            artifact=group+'_transport'
            transport=json.loads(raw[artifact])
            source._charge(ledger,transport)
            equal('transport.success',True,transport['success'])
            ev=transport['result']['evidence']
            for key,value in (('root_exit',0),('active_processes',0),
                              ('cleanup_state','cleaned'),('stdout_eof',True),
                              ('stderr_eof',True),('limits_verified',True)):
                equal('transport.'+key,value,ev[key])
            equal('transport.observed_stdout',len(raw[group+'_boundary']),ev['observed_stdout'])
            for key in ('caller_handle_usable','stage_unchanged','helper_temp_empty'):
                equal('transport.'+key,True,transport[key])
            artifact=group+'_report'
            report=json.loads(raw[artifact])
            source._charge(ledger,report)
            for key in ('transport','cleanup','staging_removed','inputs_unchanged','fixture_unchanged','passed'):
                equal('report.'+key,True,report[key])
            equal('report.worker_exit',0,report['worker_exit'])
            equal('report.stdout_sha256',pins[group+'_boundary'],report['output_hashes']['stdout.bin'])
            equal('report.comparison.passed',True,report['comparison']['passed'])
            args=(group+'_boundary',pins[group+'_boundary'],group+'_report',pins[group+'_report'],
                  group+'_transport',pins[group+'_transport'],pins['pcb'])
            source._charge(ledger,args)
            links.append(BoundaryArtifactLink(*args))
        return tuple(links)
    except artifacts._Conflict as error:
        return source._failure(pre.ContractError(pre.ErrorCode.SOURCE_CONFLICT,
            'Pinned boundary report/transport disagree.',error.field,'Preserve and inspect artifact evidence.',
            artifact_id=artifact,expected=repr(error.expected),actual=repr(error.actual),
            context=(('artifact_sha256',pins[artifact]),)))


def check_boundary_records(admitted_bytes, inventory, declarations, caller_context, profile, limits):
    ledger=pre.Ledger()
    checked=source._check_source(admitted_bytes,inventory,declarations,caller_context,profile,limits,ledger)
    if isinstance(checked,pre.PreparationFailure):return checked
    raw={item.artifact_id:item.data for item in admitted_bytes}
    try:
        links=_links_from_verified(raw,ledger)
        if isinstance(links,pre.PreparationFailure):return links
        ctx=caller_context
        request=pre.c.PadCandidateRequest(ctx.schema_version,ctx.candidate_policy,ctx.board_id,
            ctx.candidate_scope_id,ctx.target_frame,inventory,declarations.parents,declarations.pads)
        records=artifacts._records_from_verified(request,declarations.boundaries,raw,
            charge=lambda value:source._charge(ledger,value))
        if isinstance(records,artifacts.ArtifactBindingFailure):return source._failure(records.diagnostic)
        return BoundaryRecordCheckSuccess(checked,records,links,ledger.nodes,ledger.text_bytes,
                                         ledger.refs,ledger.hashed_bytes)
    except pre.b._Reject as error:
        sink=pre.c._Issues(pre.C_POLICY)
        try:sink.exhaust(error.field)
        except pre.c._Stop:pass
        return pre.PreparationFailure(pre.ValidationReport('source-boundaries',pre.PROFILE.profile_id,
            tuple(sink.issues),()),sink.truncation)
