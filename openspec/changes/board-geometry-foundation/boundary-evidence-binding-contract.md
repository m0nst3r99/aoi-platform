# Boundary evidence binding - revision 2 for review

Status: B1-B4 selected by user, 2026-10-29; exact supplemental limits below
are proposed for review. No product implementation authorized by this document.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. Existing accepted code,
oracles, evidence and normative requirements are unchanged.

## Existing requirements versus proposed slice

[Import requirements](specs/pcb-data-import/spec.md) require explicit source
frames/transforms, preserved pad geometry/provenance and rejection of unsupported
constructs (requirements at lines 15, 32, 45 and 131). They do not prescribe this
API or establish that current native observations detect every unsupported feature.
The proposed operation is bounded candidate validation, NOT ValidateImport,
BoardRevision construction, publication or a KiCad support allowlist entry.

Proposed signature: `bind_pad_boundaries(request: PadCandidateRequest,
 evidence: tuple[BoundaryEvidence, ...], policy: BoundaryBindingPolicy)
 -> BoundaryBindingSuccess | BoundaryBindingFailure`.
All records and nested collections are immutable. The request carries the existing
successful inventory, canonical/source IDs, scope and explicit source-to-P maps.

## Proposed fields (all required unless marked optional)

| Record / field | Type | Source and validation |
|---|---|---|
| ArtifactRef.artifact_id / computed_sha256 | nonempty str / SHA-256 hex str | Exact identity and computed digest of an artifact in request InventorySuccess; never merely declared hash |
| ArtifactRef.locator | bounded nonempty str | Explicit record/field locator inside admitted evidence; locator alone does not verify bytes-to-record correspondence |
| BoundaryEvidence.evidence_id | nonempty str | Caller supplied, unique exact string in batch; no generation or repair |
| source / observation / boundary | ArtifactRef each | PCB/source, observation and boundary artifact identities; may share an artifact only when explicit distinct locators describe their roles |
| auxiliary_evidence | tuple[ArtifactRef, ...] | Empty allowed; report/transport/audit references when available; labels distinguish observation execution from boundary execution |
| canonical_parent_id / canonical_pad_id | nonempty str | Exact matches to request records; not inferred from reference or pad number |
| source_parent_id / source_pad_id | nonempty str | Exact matches to request source identities, scoped by source artifact and typed namespace; no silent UUID normalization |
| boundary_frame | Frame | Full declared frame/context, not frame_id alone; same unpublished candidate scope |
| boundary_to_p | Transform2 | Explicit validated proper-rigid transform, matching full boundary/target frames; no guessed origin |
| coordinate_basis | literal `board-source-normalized` | Already mm/right/up; no native Y-down input at this layer or second parent placement |
| contours | tuple[BoundaryContour, ...] | Exactly one for accepted subset; preserve supplied order |
| BoundaryContour.vertices | tuple[Point2, ...] | Exactly four distinct finite vertices, no repeated closing point; all full frames match boundary_frame |
| BoundaryContour.closed / hole_count | bool / int | Must be true / zero; reject bool as integer |
| copper_layer / side | literal F.Cu / literal top | Must agree with pad declaration; no layer inferred from rectangular shape |
| producer_identity / producer_version / protocol_version | bounded nonempty str each | Declared metadata; not authenticated by hash/schema checks |
| coverage | tuple[ConstructCoverage, ...] | Required named categories below; unknown is explicit, missing category is failure |
| membership | MembershipEvidence | Declared association and optional supplied audit metadata only; never independently verified by this operation |

`ConstructCoverage` contains `category`, `status` (observed-supported,
observed-unsupported, unknown), `basis` (caller-declaration, API-observation,
source-audit), bounded `detail` and tuple of ArtifactRef. Required categories:
shape, side, layer-effective-geometry, offset, per-layer-overrides,
custom-primitives, drill, source-construct-completeness. These statuses describe
evidence claims; they are not a trusted caller-controlled bypass switch.

`MembershipEvidence` contains declared source parent/pad IDs and optional supplied
source-audit references. Optional verifier identity/version must be supplied together
or both absent; these are unverified metadata, not execution of a verifier.
Binding checks exact consistency against SourcePad/PadParent only. No decoder,
source-byte membership check or source-aware coverage verifier is included.
Artifact-to-record locators and fields remain supplied declarations even when
artifact identity and computed hash match InventorySuccess.

## Binding and geometry behavior

1. Bound metadata/count/depth before indexing, sorting or serialization. Require
   successful inventory and exact references; reject missing/duplicate bindings,
   extra bindings outside the request, conflicting source identities or hashes.
2. Check declared associations, full frames/context and coverage. First subset is
   top SMD rectangle/F.Cu only, no drill, offset, overrides or custom primitives.
   Unknown coverage is retained and does not block declaration-consistent binding.
   Any observed-unsupported status blocks with GEOMETRY_UNSUPPORTED. Claims of
   observed-supported remain unverified declarations, regardless of basis label.
   Explicit geometry outside the subset also blocks; unknown cannot override an
   actual unsupported shape/layer/map. Existing candidate API remains unchanged.
3. Reuse `build_rectangular_pad_candidates` once for the whole batch, without
   weakening its guards. Transform boundary vertices into P using explicit maps;
   compare all four candidate vertices with cyclic/reversed correspondence only.
   Reject self-crossing/nonrectangular contours or failed edge correspondence;
   never sort an unordered point set, fit a bbox or silently approximate geometry.
4. Only after every record succeeds return candidates plus immutable binding
   records, correspondence and ValidationReport. Keep candidate association_status
   declaration-consistent and published/targeting_authorized false. Boundary
   agreement is not a source-membership or import-readiness upgrade.

Native IU/Y-down conversion and its reflection evidence belong upstream. The
accepted C1/C2 evaluation performs that normalization explicitly; moving it into
product or admitting arbitrary native observations is not part of this draft.

Hash matching proves artifact byte identity, schema proves structural conformity,
and rectangular polygon agreement proves only that geometric comparison. None
proves that the source lacked constructs which a loader omitted or normalized.
Current C1/C2 evidence is fixture-specific. An arbitrary caller coverage declaration
cannot establish general reader support or fail-closed construct detection.

## Failure and bounded reporting

Failure contains ValidationReport and truncation metadata, never candidates or
usable geometry (including when one group passed). Reuse existing ContractError /
ValidationReport stable ordering, expected/actual preservation and candidate
reservation/fallback semantics; do not silently drop blocking failures.
Include known artifact IDs/hashes, canonical/source parent/pad identities, field,
frame/context and policy identity. Do not invent missing source locations or IDs.

Error mapping: malformed/missing coverage categories or field types use
SCHEMA_INVALID; duplicate identities use DUPLICATE_ID; conflicting bindings or
geometric disagreement use SOURCE_CONFLICT; full-frame/context mismatch uses
CONTEXT_MISMATCH; resource exhaustion uses INPUT_LIMIT_EXCEEDED. Explicit unsupported
constructs, observed-unsupported coverage, unsupported layer/shape/map or topology
outside one closed four-vertex contour without holes use GEOMETRY_UNSUPPORTED.
A four-vertex contour that fails rectangle/edge correspondence is SOURCE_CONFLICT.
No new error enum is proposed. Batch failure never publishes, repairs identity,
filters unsupported pads or returns partial success.

## Selected decisions and explicit output assurance

B1: declaration-consistent geometry binding; unknown retained, unsupported blocked.
B2: artifact-to-record is supplied declaration; no decoder/source-aware verifier.
B3: explicit synthetic policy v1, max-component distance in P, 1e-6 mm.
B4: reuse candidate budgets/reservation; bounded traversal and eight categories.
These choices replace the earlier alternative proposals, not normative import rules.

`BoundaryBindingSuccess` contains immutable candidates, per-binding results,
ValidationReport and policy identity. Required literal statuses (not caller switches):

| Field | Exact success value |
|---|---|
| status | `declaration-consistent-geometry-binding` |
| association_status | `declaration-consistent` |
| artifact_record_status | `supplied-declaration-unverified` |
| source_membership_status | `not-verified` |
| source_construct_coverage_status | `not-verified` |
| import_ready / published / targeting_authorized | false / false / false |

Each result preserves all eight supplied coverage records and their evidence/basis,
plus an explicit tuple of unknown categories (possibly empty). Even an empty tuple
or eight observed-supported declarations does NOT change any assurance status.
Per-binding geometric result records correspondence and max-component error in P;
it says `within-synthetic-policy`, never source-verified. Candidate association
properties remain unchanged. Success order is canonical pad_id lexical; category
output follows the fixed category order listed above; raw vertex order is retained.
Failure has status `rejected`, report/truncation and no candidates/binding-success
collection; it cannot be mistaken for partial success.

## Exact synthetic policy and bounded work (supplemental values for review)

Proposed policy_id `synthetic-rect-boundary-binding`, version `1`. Every policy field
is required, with these exact values; no default argument, inferred tolerance or
production accuracy claim. Reject bool for integer/numeric limits, nonfinite,
nonpositive limits, wrong version or values outside this policy. Zero values below
are geometry/guard constants, not positive resource limits. Candidate policy stays
`synthetic-rect-pad-candidate` / `1` unchanged.

| Limit / constant | Exact value / interpretation |
|---|---|
| max pads / parents / inventory artifacts | 4096 / 4096 / 1024 (existing candidate caps) |
| max bindings | 4096, exactly one per requested pad; empty batch rejected |
| contours / vertices / holes | exactly 1 / 4 / 0 per binding; closed=true |
| coverage categories | exactly the eight named above, each once; missing/duplicate/unknown category rejected |
| correspondence trials | exactly 8 maximum per pad: four cyclic starts times two directions |
| component comparisons | at most 64 per pad, 262144 per batch (8 x 4 x 2 x 4096) |
| comparison_abs_mm | 0.000001, max absolute X/Y difference after mapping both geometries to P |
| ID and enum UTF-8 bytes | 256 each; opaque IDs exact, nonempty, no trim/normalization |
| detail / locator / other descriptive text UTF-8 bytes | 1024 each |
| total input text UTF-8 bytes | 8388608 across request AND boundary evidence, counted by occurrence |
| evidence refs per collection / total occurrences | 16 / 32768 across request AND boundary evidence |
| auxiliary refs per binding | 16 (subject to shared total) |
| coverage refs per category / membership audit refs | 16 / 16 (subject to shared total) |
| primary refs | exactly source + observation + boundary; each counts toward total occurrences |
| traversal depth | 32, root depth 0 |
| total traversal node occurrences | 2686976 = 64 x (4096 + 4096 + 1024 + 32768), shared across request and evidence |
| diagnostics count / single UTF-8 bytes / total UTF-8 bytes | 128 / 4096 / 524288 |
| max absolute coordinate / dimension mm | 1000000 / 1000000 |
| minimum rectangle dimension mm / max absolute pad angle degrees | 0.000001 / 360000 |
| rigid guard abs / rel | 1e-12 / 0, reuse existing Transform2 kind/parity/conventions guards |

All boundary vertices, transformed P coordinates and candidate inputs must remain
finite and within coordinate caps; dimensions/angles use existing candidate guards.
Do not loosen guards or silently orthogonalize. Binding comparison tolerance is a
new explicit synthetic runtime criterion; candidate test_oracle_abs_mm remains a
test assertion parameter, not transform admission slack.

At most eight correspondence candidates are examined; accept exactly one matching
mapping. None or multiple within tolerance yield SOURCE_CONFLICT, not first-match
selection. This avoids silently choosing ambiguous corner identity on tiny pads.

Preflight jointly counts request/evidence node, text and reference occurrences before
sorting, indexing, transforming or calling candidate API. Repeated object references
are counted each time. Only exact immutable records/tuples/scalars are admitted;
no arbitrary iterators/callbacks. Check tuple lengths before expanding a traversal
stack; check string character count then bounded UTF-8 scalar widths without encoding
an unbounded string. No full-inventory serialization to discover an excess.
Each primary/auxiliary/coverage/membership ArtifactRef occurrence counts, including
repeated refs. Output evidence uses validated refs; candidate request is not expanded
by duplicating the inventory per binding. Total work counters are not reset per pad.

Use one aggregate diagnostic budget across binding and candidate phases, not 128
each. Reserve one issue slot and 4096 bytes for terminal INPUT_LIMIT_EXCEEDED:
ordinary issues at most 127 and 520192 bytes; each at most 4096 bytes. On exhaustion,
stop unsafe work, retain bounded issues plus blocking terminal issue/truncation,
never candidates. omitted_count is None unless known exactly. Invalid policy uses
the existing bounded candidate fallback strategy, not values from the invalid policy.
Merging candidate diagnostics must honor the same aggregate reservation; do not
serialize/collect unbounded issues before deciding to truncate. Existing deterministic
ValidationReport ordering and expected/actual preservation remain in force.

## Review boundary and acceptance still pending

B1-B4 are settled. The supplemental policy name, exact boundary-specific limits,
output literal names and unique-correspondence rule above are concrete proposals
for this contract review, not prior normative requirements or implementation approval.
No source verifier/decoder is required for the selected declaration-only slice;
those remain necessary work before claiming verified source-safe import.

Portable acceptance: independent synthetic IDs/oracles plus C1+C2 16-corner replay;
unknown retained without assurance upgrade; observed-unsupported rejected; wrong
binding/context/topology, ambiguous correspondence, exact/exceeded combined budgets,
diagnostic exhaustion and mixed-batch no-candidates failure. Keep actual hash binding
checks distinct from supplied record consistency and test doubles. No native run,
product implementation or new import-compatibility claim follows from this document.
