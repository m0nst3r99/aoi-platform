# Board geometry foundation design

## Authorized evaluation runner slice - 2026-10-19

This section supersedes runner/staging/transport proposals below; observation
semantics remain future work. Windows x64 + CPython x64, explicit ctypes Win32
prototypes/structures, trusted host/executable/helper. No KiCad run/version pin,
no inventory bridge or source factory/path resolution. Non-Windows and unsupported
required capabilities fail explicitly; no weaker fallback. Tested OS/Python are
recorded in execution evidence, not generalized to untested versions.

**Staging ownership:** input is caller-staged, read-only local disk handle with
artifact/source ID, exact size and SHA-256. Caller owns input/handle and must keep
it stable during execution. Runner owns only its duplicated handle and execution
resources; it never deletes caller input. Hash/size validation starts within the
runner entry deadline; acquisition/staging deadlines belong to a future bridge.
File-pointer sharing on duplicated handles is explicit: caller must not concurrently
seek/read the shared file object; helper access may advance the shared offset.
Validation uses read-only mapping without changing the caller offset. Input is
passed as an explicitly inherited handle (argv placeholder), stdin is NUL.

**Transport boundary:** runner controls executable/argv, cwd, explicit environment,
handles, Job, pipes, budgets, exit and cleanup only. No JSON parsing, framing,
backend version checks or handshake. Bounded malformed JSON is transport-success
when the process/cleanup contract succeeds. Protocol tests belong to a later layer.
Executable absolute path, shell=False semantics (direct CreateProcessW); no PATH
search. Only stdout/stderr writers, NUL stdin and duplicated staged handle inherit;
Job handle and parent's read ends do not. No breakaway flags.

**Success predicate:** root exit=0 AND no observed error/budget violation AND both
pipes reached EOF without read error AND Job accounting ActiveProcesses=0 AND root
termination confirmed AND I/O finished AND every owned handle/view reclaimed
within separate cleanup deadline. Query Job accounting, not Job signaled state or
notifications alone. Cleanup uncertainty yields failure with explicit cleanup_state,
not a claimed cleaned result. Failed assignment never resumes the suspended child.

**Implementation choice:** single-threaded PeekNamedPipe/ReadFile polling with one
reader per pipe and reads limited to bytes already available; rotate both streams.
No reader threads and no outstanding overlapped reads exist to cancel. On failure,
terminate Job, close I/O handles, query termination and release resources within
cleanup deadline. Pipe peek/read/close errors remain failures. No unbounded
communicate/capture_output. Execution deadline starts at function entry; cleanup
gets its own deadline. Win32 calls on trusted local resources are not a hard
real-time scheduling guarantee; native tests use an independent outer watchdog.

Process/job committed-memory and active-process limits are set and read back before
resume. KILL_ON_JOB_CLOSE applies. Raw status is retained; arbitrary crashes are
not labeled MEMORY_BUDGET. Peak accounting cannot detect every denied allocation.
Budget integers reject bool, zero and Win32 overflow. Raw output retention <= combined
budget, each stream <= its own budget, temporary read buffers <= chunk; conversions
may briefly double retained bytes. Failure prefixes share these bounds and are
explicitly unusable. Diagnostic text/count have fixed internal caps. No whole-stream
hash is claimed for prefixes. This is resource control, not a security sandbox.

Test policy (synthetic only): `windows-runner-test-v1`, input 1 MiB, stdout/stderr
64 KiB each, combined 96 KiB, chunk 4096 bytes, wall 5000 ms, cleanup 3000 ms,
process commit 128 MiB, job commit 384 MiB, active processes 8. Tests explicitly
replace individual limits for boundaries/enforcement; these are not production
defaults. No support/checkbox promotion from passing runner tests.

## Runner verification update - 2026-10-19

The evaluation runner is implemented; see [runner scope/results](../../../evaluation/windows_runner/README.md)
and [review-03 raw evidence](../../../evaluation/windows_runner/evidence/review-03/environment-command.json).
491 passed / 1 existing fixture-opt-in skip includes 57 portable + 41 Windows
runner cases. This replaces the old draft's runner NOT RUN status below only;
observation/protocol/geometry cases remain future work. No external runner review
acceptance yet. Task 1.5/5.2 remains PARTIAL. Universal parent-death cleanup is
incomplete: CreateProcess-suspended and Assign are not atomic; the native parent
crash test covers the already-assigned Job, not that earlier window. Other platform
builds and naturally incompatible enclosing Jobs are not native-tested. Read/peek/
close faults are tested; this implementation has no pending async read cancellation.

## Review draft: native observation boundary (2026-10-19, tasks 1.5/5.2 PARTIAL)

**Observation adapter proposal only. The separate runner slice above is authorized.** This
refines planning without changing normative PCB-001/GEO-001 requirements. The
existing inventory admits bytes, not geometry. Reader evaluation and accepted
population errata/r2 establish neither parser compatibility nor complete input
support. See [implementation status](implementation-status.md) and
[evaluation evidence](../../../evaluation/kicad-reader/README.md).

### Proposed API and immutable types

```python
observe_native(
    request: NativeObservationRequest,
    source: BinarySourceLease,
    backend: BackendIdentity,
    limits: ObservationLimits,
) -> NativeObservationSuccess | NativeObservationFailure
```

Names and protocol are proposed, not existing symbols. Frozen records use tuples
and primitive immutable values throughout; a frozen wrapper around mutable
dicts/lists is insufficient. Transport JSON is validated before constructing them.

| Record | Required fields and semantics |
| --- | --- |
| NativeObservationRequest | InventorySuccess admission plus selected artifact_id, source_id, computed SHA-256, actual size, fixture revision/snapshot, requested protocol `kicad-native-observation-v1`, mode `evaluation-only`. Require exactly one matching PCB artifact, EOF and full digest; reject InventoryFailure/reference-only admission. Revalidate consistency of supplied records, not object identity or a signature assumption. |
| BinarySourceLease | Explicit host-issued capability for the selected source_id; read-only source handle, ownership/lifetime and resource capability description. No URL, archive or arbitrary path resolution. Proposed Windows first implementation accepts a controlled local regular-file handle only, not a network path/device/reparse traversal. |
| BackendIdentity | Explicit absolute bundled Python executable, native extension/runtime dependency identity manifest and hashes, helper script hash, expected KiCad build `10.0.7`, architecture, Python ABI/version and protocol version. Record expected and observed identities independently. A directory named `10.0` or a child-reported version alone is not a pin. |
| ObservationLimits | Versioned policy ID; positive input bytes, stdout bytes, stderr bytes, combined output bytes, chunk bytes, wall-time ms, cleanup-time ms, process committed-memory bytes, aggregate job committed-memory bytes, max processes, JSON nesting/string/entity/diagnostic counts, and staging disk bytes. No silent unlimited defaults. Chunk <=1 MiB proposed; other values explicit until measured, no invented production-safe defaults. |
| NativeObservationSuccess | Frozen observations, provenance, required coverage/limitations tuple and ValidationReport scoped to `native-observation-evaluation-only`. Literal `geometry_usable=False`, `import_usable=False`, `targeting_authorized=False`; no BoardRevision/Transform object or implicit conversion into canonical models. Success means the observation protocol completed, not that the input format is supported for import. |
| NativeObservationFailure | ValidationReport plus bounded ExecutionEvidence (hashes, counters, exit/status, bounded log bytes or log digests, cleanup state). **No observations field and no success-shaped partial output.** Discard any candidate observations on failure. |

InventorySuccess contains no reusable source bytes. Before launch, stage a fresh
read of the supplied capability with streaming SHA-256 and compare both size and
hash against admitted evidence. Source ID, artifact ID and revision declarations
remain attached throughout. TOCTOU between inventory and stage is a conflict,
not permission to trust the previous digest. Do not pass the original fixture
path to native loader. Staging uses a unique host-owned directory, fixed generated
filename, restricted handle inheritance and no project/library sidecars.

Ownership: caller retains its source lease; runner owns duplicated handles,
temporary files and child resources and closes them on all paths. Stage bytes
through the containment worker, not an arbitrary blocking factory on the host
thread. Current inventory ByteSources factories are synchronous trusted callables
without deadlines; they are **not automatically compatible** with this lease.
If a deadline-capable source cannot be provided, fail `POLICY_INVALID` with
reason `SOURCE_CAPABILITY_UNSUPPORTED` before starting native work. Exact local
handle issuance/path/reparse/ACL checks require review and tests in a later bridge;
do not silently expand inventory's source API.

### Failures and diagnostic compatibility

Reuse GeometryError -> ContractError.from_geometry_error -> ValidationReport,
preserving code/field_path and all evidence already known. Proposed reason enum
is stored in context `adapter_reason`; it does not pretend new ErrorCode members
exist. Mappings below are proposals for review, not code changes.

| Failure | Existing ErrorCode / proposed reason |
| --- | --- |
| Invalid request, duplicate IDs or malformed protocol/schema | SCHEMA_INVALID or DUPLICATE_ID / REQUEST_INVALID, PROTOCOL_INVALID |
| Backend/protocol mismatch or native parse rejection | FORMAT_UNSUPPORTED / BACKEND_MISMATCH, PROTOCOL_VERSION_MISMATCH, NATIVE_LOAD_REJECTED |
| Hash/size mismatch, source metadata conflict | SOURCE_CONFLICT / STAGED_BYTES_MISMATCH, DECLARATION_CONFLICT |
| Missing/open/read/launch/crash/cleanup failure | SOURCE_NOT_FOUND or SOURCE_IO_ERROR / SOURCE_MISSING, READ_FAILED, LAUNCH_FAILED, PROCESS_CRASHED, CLEANUP_FAILED |
| Input/output/time/memory/process limit | INPUT_LIMIT_EXCEEDED / INPUT_BUDGET, OUTPUT_BUDGET, TIMEOUT, MEMORY_BUDGET, PROCESS_BUDGET |
| Requested containment unsupported/unverifiable | POLICY_INVALID / CONTAINMENT_UNAVAILABLE, LIMIT_UNSUPPORTED |

Preserve artifact/source IDs, declared revision, source digest, backend identities,
protocol, policy and limits; expected/actual must not overwrite each other.
Native entity UUID and source location are included only if known; no invented
line numbers from an API object. Diagnostics use existing canonical ordering and
serialization with meaningful duplicates retained. Bound diagnostics; exceeding
their count fails rather than returning an accepted truncated report. Runtime
timestamps/PIDs belong to execution evidence, not semantic equality assertions.
Report status ACCEPTED is restricted to its observation scope, never inspection
readiness. A malformed negative-probe response or crash is not native rejection.

### Subprocess lifecycle and Windows enforcement proposal

Use explicit argv and executable; never shell=True, shell interpolation, PATH
search or source-supplied options. Temporary backend: bundled pcbnew 10.0.7;
native load success does not admit every KiCad 10 file. Pin and verify installation
manifest plus helper hashes before execution; child handshake reports build/ABI/
protocol and rehashes staged input. This is drift detection under a trusted host,
not attestation against a malicious executable or a same-user attacker replacing
the install. Reject an untrusted/writable backend installation policy.

Proposed lifecycle: validate policy/capabilities -> create private stage/job ->
bounded stage/hash -> verify backend -> create worker suspended with hidden UI ->
assign job and verify limits -> resume -> bounded handshake/observations -> wait
for worker and descendants -> validate complete JSON -> cleanup -> return.
Never return success before cleanup; no resuming a worker that could not be
assigned to the required job. End-to-end monotonic deadline includes staging,
handshake and execution, with an explicit bounded cleanup deadline afterwards.

| Resource | Proposed enforcement | Evidence still required |
| --- | --- | --- |
| Input/staging disk | Fixed-size streaming read/write and measured counters; reject before writing bytes beyond budget; at most one documented sentinel byte to distinguish exact EOF. Stage hash and size must match admission. No other writable artifacts allowed by the worker protocol. | Exact boundary, +1 byte, dishonest size, mutation between reads, disk/full/read failures; source-handle and sidecar behavior. A cooperative worker protocol is not a disk quota against hostile code. |
| stdout/stderr | Drain both pipes concurrently in bounded chunks; per-stream and combined counters. Detect first overrun, terminate job, retain bounded prefix plus truncation/count evidence. No communicate(capture_output=True) unlimited buffering. | Flood either/both streams, deadlock, held pipes in descendants, invalid UTF-8, combined-limit boundary. |
| Wall time/tree | CreateProcess suspended, AssignProcessToJobObject before resume, no breakaway flags; KILL_ON_JOB_CLOSE; TerminateJobObject and wait for all job members plus pipe readers. Closing only the root process is insufficient. | Actual Windows child/grandchild, parent crash, hung native call, denied job assignment/nested-job conflict, cleanup timeout and all handles closed. |
| Memory | Set process and job committed-memory limits via JOBOBJECT_EXTENDED_LIMIT_INFORMATION; verify installed settings before resume. This bounds committed virtual memory, not RSS, kernel memory or the host Python process. | Real Windows allocation helper across descendants, memory-denial/crash behavior, accounting and diagnostic classification. Notifications alone are not proof every breach is reported. Unclassified failure stays failure, never guessed success. |
| Processes | Job active-process limit, descendants inherit job; no breakaway allowed. | Attempt fork/spawn above limit; prove no surviving normal CreateProcess descendants. Out-of-job/service-mediated creation is not a security containment claim. |
| Host decoding/diagnostics | Bounded byte buffers and bounded framing, duplicate JSON-key rejection, strict finite-number/type validation and explicit nesting/entity/string limits. Budget applies before constructing unbounded object graphs. | Deep/malformed JSON, duplicate keys, huge entity arrays, NaN/Infinity and report explosion. Host RSS is not bounded by child job; unsupported host-hard-memory policy fails explicitly. |
| Cleanup | Terminate and reap workers, close read/write/job/process handles, release staged-file handle and remove only owned temporary directory. Unexpected files or residual handles are failure evidence. | Windows sharing violations, cleanup denied, parent termination, no success until cleanup verified. Persist a bounded cleanup record; no deletion outside owned stage. |

These mechanisms are **not implemented or Windows-tested here**. If job assignment,
hard memory enforcement, supported pipe cancellation or required policy cannot be
established, return CONTAINMENT_UNAVAILABLE/LIMIT_UNSUPPORTED before native work;
do not fall back to timeout-only execution. A child allocation refusal may be
caught by a runtime, so protocol completeness still needs validation. No claim
that peak accounting detects every denied allocation. A timeout/Job Object is
resource control, **not a filesystem/network/security sandbox**. Requests requiring
hostile-file isolation, hard host-memory caps or disk quotas are unsupported by
this proposal and must fail rather than receive an overstated guarantee.

Official platform references (consulted 2026-10-19; documentation, not probe
evidence): [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[committed-memory fields](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information),
[process creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags).
No new native integration runs were performed for this contract.

### Observation protocol and evidence origins

One versioned UTF-8 JSON document on stdout after successful handshake, bounded by
the agreed framing protocol; stderr is diagnostic-only. Echo request ID, artifact
ID, stage hash, backend identity and protocol. Unknown version/fields, missing
required fields, duplicate UUIDs/keys, invalid types and nonfinite numbers reject.
The exact framing/handshake transport is a review decision below. Serialize records
deterministically by UUID, preserving repeated pad number strings as distinct pads.

Each observed field records origin (`native_api`, `derived`, `external_declaration`)
and accessor/calculation/declaration provenance; do not blend origins into one
unqualified value. Preserve native integer length coordinates and their scale when
available; p.ToMM conversions are derived with the conversion identified. Source
frame is artifact-hash-bound, not canonical P: source sheet coordinates, units,
axis/origin declarations and confidence are explicit. Raw angles include API
accessor and units without canonical modulo, sign or parity transformations.
Side derives from layer ID/name with that mapping recorded; retain original layer
membership and note that API expansion may lose original wildcard spelling.

- Footprints: UUID/reference/value/library ID, native position/angle/layer,
  raw attributes and API DNP/BOM/position exclusions; UUID links to source hash.
- Pads: UUID/parent UUID/number string, native and footprint-relative positions,
  native angles, shape/size/drill/layers and known padstack details. Missing
  semantics are explicit coverage gaps, not zero/default shapes or rectangles.
- Outline: separate board-level Edge.Cuts primitives from footprint-owned ones,
  retaining parent frame, line endpoints and arc start/mid/end data. Native
  outline validity, polygon/hole counts and bbox are derived native-algorithm
  observations; none replaces original curves/topology or independent validation.
- External population ledger/classifications are separately declared metadata;
  disagreement is retained as expected/actual evidence, not silently overwritten.
  Ledger agreement does **not** independently prove reader geometry/flags correct.
  No automatic assembly eligibility or fiducial approval. Fiducial candidates
  retain declaration UUID/source/provenance separately from observed geometry.
- Bottom local/world values are observations only; no inferred mirror, pose,
  source-to-canonical transform or targeting coordinates are returned.

### Construct coverage matrix (current evidence, not a support allowlist)

"Full" below means fields observed for the named fixture case, never whole-format
support. Any unverified completeness keeps observations evaluation-only. Unknown
features cannot be declared fail-closed unless detection is evidenced.

| Construct | Current category | Detection / evidence needed before promotion |
| --- | --- | --- |
| r2 footprint UUID/ref/value/position/angle/layer and DNP/exclusion fields | Fully observed for fixture fields; only DNP source correction independently reviewed in full | Native accessors and all-UUID source audit; add independent synthetic top/bottom numeric and flag oracles. Ledger count/match alone is insufficient. |
| Board-level Edge.Cuts lines/arcs | Observed primitive fields; partial geometry verification | Enumerate native drawing type/layer, preserve UUID/curves. 12 lines/3 arcs and 135x90 centerline evidenced. Add independent arc extrema/winding/topology; not merely bbox. |
| Enclosed cutouts/multiple loops | Identification API available; positive support unverified | Explicit nested contour fixtures, independent hole count/boundary/orientation oracle; no inferred outlines. r2 has zero holes, not proof of cutout support. |
| Footprint-local Edge.Cuts | Not detected by current board-drawing probe | Enumerate footprint graphical items and parent/local transforms; test top/bottom rotated local edges. Until then declare coverage unknown, not absent. |
| Bottom geometry | Raw pose/side observed; normalization unverified | Native local/world pad/primitive queries versus independent rotated/reflected oracles. Never apply implicit reflection in observation stage. |
| Simple/roundrect pads | Shape tags/basic dimensions identified; incomplete geometry | Preserve corner radius/ratios, orientation and per-layer properties with independent tests. Current dimensions alone are insufficient. |
| Custom pads/primitives, chamfers, padstacks, overrides | Intended rejection when recognized; complete detector not implemented | Enumerate every native shape/primitive/per-layer construct; explicit unsupported reason and UUID. Synthetic instances for each enum; detect dropped/normalized properties independently. Cannot claim general rejection today. |
| Splines/unknown visible native item types | Intended rejection of detected unsupported item | Exhaustive enumerator/type inventory and synthetic positive/negative fixtures; no default skip branch. |
| Tokens/data omitted or normalized by native loader (incl. unknown future tokens) | **Not reliably detected** | Native API has no proven source-preservation/loss ledger. Requires upstream parser diagnostics/source-aware coverage evidence or independently audited enumerator. No custom S-expression parser authorized. Hash/version/load success cannot close this gap. |
| Project/library/variant sidecar-dependent semantics | Not verified | Isolated stage without sidecars, explicit default-variant declaration and comparison fixtures; reject unsupported external dependency when detected, retain unknown coverage otherwise. |

Consequently the first observation proposal cannot satisfy PCB-001's import
fail-closed construct requirement. It produces **no usable geometry for import**.
If caller asks for import-ready/complete coverage, reject the mode before reading.
Do not lower the normative requirement or mark 5.2 complete to fit these limits.

### Acceptance plan: distinguish three evidence classes

| Class | Tests/evidence required | Current status |
| --- | --- | --- |
| Portable mocked | Identity/protocol mismatch, missing/malformed input, staged hash/size mismatch, schema/JSON/duplicates/nonfinite, bounded reads/output, timeout/crash classifications, deterministic diagnostics, no success-shaped failure, cleanup errors | Existing 23 harness regressions accepted; they do not test the proposed adapter/runner. New contract cases NOT RUN. |
| Native Windows process integration | Actual job assignment before resume; time/memory/process budgets; stdout/stderr concurrent overflow; child/grandchild termination, withheld EOF, crash, sharing violations and cleanup; capability-unavailable rejection | Historical NOT RUN statement superseded by runner verification above; untested cases remain gaps. Mock tests cannot substitute. |
| Native KiCad semantics | Read-only r2 with pinned build/hashes; independent small line/arc/cutout/top/bottom/local-Edge.Cuts/custom-pad and unsupported-token fixtures; source unchanged; exact population/provenance comparisons | Prior local r2 27/27 is narrow agent evidence; new synthetic oracles NOT RUN. No PASS for cutouts/bottom/custom/unknown-token coverage yet. |
| Review | Reviewer verified ZIP 23/23 regressions, 133/133 packaged hashes, 25/25 per snapshot, all 12 DNP source blocks; replay r1 26/27 fail and r2 27/27 pass from saved subprocess output | User reports metadata errata/r2 accepted; reviewer did not rerun KiCad native. Acceptance is not native rerun evidence or parser compatibility. |

### Historical proposal: bounded Windows process runner (superseded by implementation above)

Deliver a separately testable, **evaluation-internal** process runner, its frozen
execution request/result/failure schema and helper-process test fixtures. Proposed
entry: `run_bounded_worker(staged_input, executable_identity, argv, limits)` ->
`ExecutionSuccess | ExecutionFailure`. Success contains bounded raw bytes and
execution evidence only, no parsed KiCad observations or geometry. Staged input
uses the host-owned handle/digest contract; no new inventory source bridge in this
slice. Reject unsupported capabilities explicitly. This is part of 1.5/5.2, not
completion of either task or implementation of observe_native.

Acceptance: portable runner tests AND actual Windows job/pipe/deadline/memory/
descendant/cleanup tests above; exact-boundary/+1 tests, unchanged staged bytes,
executable/argument validation, invalid JSON accepted as raw transport bytes,
resource/launch/crash failure with preserved diagnostics,
no usable partial output; all prior tests retained. Record OS/build, commands,
hashes, results and limitations. If a mandatory capability is unavailable, the
slice remains incomplete and returns typed failure; never downgrade the policy.

Excluded: pcbnew observation semantics integration, new source parser, inventory
bridge/public API change, Gerber/BOM readers, canonicalization, publication,
camera/motion and automatic fixture mutation. Only the runner slice above is authorized.

Review decisions still needed: approve evaluation-only scope and failure mapping;
choose Win32 binding approach (ctypes vs pinned dependency) and minimum supported
Windows version/nested-job behavior; agree explicit test limit values and trusted
source/backend threat model; select bounded handshake framing (proposal: single
length-prefixed request/response with separate stderr and strict JSON payload);
approve native helper test matrix. These are proposed decisions, not normative
facts or pre-authorized defaults. Later observation semantics needs a separately
reviewed solution for loader omissions and source-local geometry completeness.

## 1. Context and decisions

This proposal defines the two capabilities GEO-001 and PCB-001 for an independent AOI platform. The separately authorized Geometry Core implementation is recorded in implementation-status.md; the remaining models/contracts and capability behavior remain open. A future implementation should run as ordinary Python modules on a PC/server, using OpenCV where appropriate, with no firmware, camera, or gantry requirement. One process may serve multiple machines; deployment topology is not prescribed.

The canonical board is planar in Phase 1. Keep its side, geometry, and provenance explicit so a later proposal can add surfaces, Z coordinates, height calibration, and post-reflow inspection profiles without reinterpreting existing 2D points. Do not add fictitious Z=0 measurements or use planar homography as a 3D model.

Decisions:

1. Physical canonical PCB coordinates use millimeters and a top-view right-handed XY frame; +Z points toward the top observer for orientation only.
2. Every source file owns a distinct frame. A shared filename, exporter, or similar extents never proves shared origin.
3. Import normalization, per-load registration, and camera calibration are separate immutable records.
4. Rigid transforms describe board placement. Explicit reflection describes side/export conventions; distortion and planar projection describe camera geometry. These operations are not interchangeable.
5. Required data is selected by a named import profile; unsupported or missing information cannot silently become an empty valid model.
6. Canonical data is independent of any inspection engine. Optional adapters preserve units, frames, and revision identity.

## 2. Coordinate frames and equations

Use column vectors. `T_B_A` maps coordinates from frame A into frame B. Composition is right to left: `T_C_A = T_C_B T_B_A`. Store both frame IDs; callers never infer matrix direction from context. For affine transforms, use homogeneous vector `[x,y,1]^T`; translation occupies the last column. A transform is invertible only when its linear block has nonzero determinant and passes the conditioning policy.

| Frame | Definition | Units and axes |
| --- | --- | --- |
| PCB `P` | Immutable board-revision datum, viewed from top. Default datum is the lower-left of the axis-aligned outline bounds **after** explicit KiCad-to-top-view axis normalization; manifest may select another documented datum. | mm; +X right, +Y up; top and bottom features use this same frame. |
| Source `S_i` | One KiCad, Gerber, or placement file's original numeric space, including exporter origin and side convention. | Declared mm/inch or format units; axes recorded individually. BOM has no geometric frame unless it actually supplies geometry. |
| Footprint `F_j` | Local origin and axes for one footprint instance, with source orientation preserved. | mm after conversion; normalized to P through a declared pose, including explicit bottom reflection when needed. |
| Machine `M_k` | Abstract work plane for machine k, fixed datum independent of board loading. | mm; +X/+Y defined in machine configuration; physical fixture and camera travel dimensions TBD in separate records. No steps or firmware axis signs. |
| Raw image `I_r` | Original capture pixel coordinates. | px; origin center of top-left pixel, u right, v down; valid centers `0..width-1`, `0..height-1`. |
| Undistorted image `I_u` | Output of an explicitly versioned lens model and rectification configuration. | px; same axis convention; dimensions and intrinsics may differ from raw. |
| Crop/engine `I_e` | Optional crop, resize, or rectified inspection raster. | px; separate frame with recorded mapping to its parent. |

Angles are degrees, normalized to `[0,360)` on stored component poses; signed differences use `[-180,180)`. Canonical positive rotation is counterclockwise viewed from the top. `R(theta) = [[cos(theta),-sin(theta)],[sin(theta),cos(theta)]]`; trig evaluation converts degrees to radians explicitly. Orientation of a reflected component is obtained from its transformed local +X direction, not by blindly negating an angle. Store parity separately because an angle cannot encode a reflection.

### Source normalization

`p_P = T_P_Si p_Si`, where `T_P_Si = Translate(tx,ty) R(theta) A s`. Here s is a declared unit conversion (inch to mm = 25.4, mm to mm = 1), A is a declared orthogonal axis permutation/reflection, and translation is in P millimeters. Any exporter transforms already applied to parsed geometry must be recorded; never apply them twice. Source profile includes origin meaning, units, axis mapping, rotation zero/direction, side semantics, and transform evidence. Resolve unknowns through manifest declarations or sufficient named correspondences, otherwise reject.

The top-view board datum is derived once from the authoritative KiCad outline and pinned in the revision record. Other sources align to that datum; they are not independently shifted to their own bounding-box minima. Scaling to make extents match is forbidden. If correspondence fitting estimates scale for diagnosis, compare with declared units and fail rather than publishing a scaled physical board.

Bottom-side records remain in P as viewed through the board from the top. Do not auto-mirror because a layer says bottom. A source explicitly declared as bottom-view about line x=c uses `x_top=2c-x_bottom, y_top=y_bottom`; the manifest must supply c in the appropriate source units/frame and any subsequent rotations/translations. A bottom-view presentation raster is a separate image transform. Maintain top/bottom layer tags independently of reflection parity. Polygon vertices and holes must be transformed consistently and winding normalized after reflection.

Example: source `(1,2)` inch, A=diag(1,-1), theta=90 degrees, t=(10,20) mm maps to `(60.8,45.4)` mm. This is a required nontrivial fixture, including its inverse. A 10 mm x 20 mm board mirrored about x=5 maps `(2,3)` to `(8,3)` and local +X to -X; applying the mirror twice restores both geometry and parity.

### Board loading and machine coordinates

Independent checkpoints for the preceding source-normalization example are mandatory. Compute each oracle directly, not using the composed transform under test:

| Stage | Independent arithmetic | Expected point |
| --- | --- | --- |
| Unit conversion | (1 x 25.4, 2 x 25.4) | (25.4, 50.8) mm |
| Reflection | (x, -y) | (25.4, -50.8) mm |
| 90-degree rotation | (-y, x) | (50.8, 25.4) mm |
| Translation | (x+10, y+20) | (60.8, 45.4) mm |

Inverse checkpoints are (50.8,25.4) after subtracting translation, (25.4,-50.8) after -90-degree rotation, (25.4,50.8) after reflection, and (1,2) inch after division by 25.4. Both independent forward checks and round trips must pass.

`p_M = T_M_P p_P`, with a proper rigid SE(2) transform (rotation plus translation, determinant +1, scale 1). An underside load is represented by a distinct declared load-side reflection frame followed by a proper rigid registration, never hidden in an SE(2) matrix. The frame path includes that reflection explicitly. Registration records bind to machine ID, board revision, load instance, side, and fixture configuration.

Keep three separate concepts:

| Concept | Meaning | Current status |
| --- | --- | --- |
| BoardCapacity | Maximum PCB dimensions 280 x 550 mm; compare complete outline extents after an explicitly declared capacity-test rotation, independent of translation in M. | Fixed board requirement, not a travel rectangle. |
| FixtureEnvelope | Usable mounting region in M, exclusions and required margins, bound to machine/fixture/configuration. Check the complete loaded outline, including arcs analytically or conservatively. | Physical geometry and margins TBD. |
| CameraTravelEnvelope | Permitted positions of a declared camera reference point in M, bound to machine/camera/mechanical configuration and exclusions. | Physical travel dimensions TBD until optics/mechanics selection. |

Exact 280 x 550 mm passes BoardCapacity; 550 x 280 mm may pass with an explicitly declared 90-degree capacity-test rotation. No implicit rotation is performed. Fixture fit and camera coverage do not follow from capacity acceptance. Synthetic tests may define a fixture rectangle `[0,280] x [0,550]` with zero margin, but it is not a physical default. A capacity-compliant board may fail fixture fit. Travel may extend beyond the board or be smaller depending on field of view, camera offsets and poses; no dimensions are inferred here.

Fit reports distinguish capacity, fixture fit and camera reachability, each pass/fail/unresolved. Missing physical envelopes do not block board import. Camera reachability remains unresolved in this foundation; a future optics/mechanics proposal must validate travel, field of view, working plane and coverage before physical targeting. Fixture/camera records are versioned and machine-scoped; a fit report never authorizes motion.

### Camera mapping

For a planar board at the calibrated plane, `lambda [u_u,v_u,1]^T = H_Iu_P [x_P,y_P,1]^T`. Normalize by the third coordinate; reject points near the horizon or outside the valid calibrated region. `p_Ir = D(p_Iu; lens_model, intrinsics, configuration)`; inverse uses the model's documented undistortion solver. D is nonlinear, not a homography. A no-distortion profile is an explicit identity model.

For a moving camera, H is specific to the capture pose. It may be composed as `H_Iu_P = H_Iu_M(capture_pose) T_M_P`. Captures must bind their effective H, registration, and calibration; a fixed transform from a different gantry position is invalid. Intrinsics alone cannot recover PCB coordinates. Camera resolution, model, intrinsics, lens distortion, crop, binning, focus/zoom configuration, and capture dimensions are inputs. Never silently scale calibration to a different resolution. A derived resize/crop calibration requires an explicit parent mapping and new identity.

Pixel centers use integer coordinates. Pixel area boundaries are half-integers; ROI bounds use half-open raster indices after an explicitly documented floor/ceil and clipping policy. Transform continuous polygon vertices before rasterization; do not round intermediate coordinates. An out-of-field ROI returns visibility status (inside/partial/outside); clipped results carry the original geometry and clipping report. General point conversion outside the declared valid domain fails rather than extrapolating silently.

## 3. Fiducials and calibration lifecycle

Design fiducials have stable IDs, side, center in P, shape, dimensions, and provenance. Observations carry fiducial ID, observation frame, measured point, confidence, and optional covariance. Correspondences use IDs rather than nearest-neighbor guesswork; duplicate IDs and side/revision mismatches fail.

- Rigid registration: two distinct, sufficiently separated, correctly identified fiducials constrain a proper SE(2) pose only when both point sets are in calibrated metric planes with known scale and handedness. Compare pair distances under policy; fit rotation and translation with scale fixed at one. Two points cannot establish a general camera homography or independently detect reflection/incorrect correspondence. Require independent side/correspondence/metric-mapping evidence or an additional held-out off-baseline fiducial under policy. Three or more are preferred for mismatch detection. Reject inadequate baseline, distance disagreement, excessive residuals or reflection indicated by independent evidence.
- Planar homography: four or more P-to-undistorted-pixel correspondences with full-rank geometry; a minimal four-point set must have no three collinear. Use an overdetermined fit when available. Reject poor spatial coverage, rank deficiency, excessive conditioning or reprojection error. Four points can interpolate incorrect measurements with near-zero residual; fitting residual alone is not validation. Require held-out checkpoints or a separately evidenced reference mapping under policy, including for overdetermined fits. Report inliers, rejected observations and independent validation evidence; do not silently discard data to pass a threshold.
- Intrinsic lens calibration: separately supplied or later estimated from a suitable multi-view calibration dataset; board fiducials at one plane do not determine a reliable general lens model. This change validates records and synthetic mappings, not a hardware calibration procedure.

Proposed `synthetic-geometry-v1` test policy: numerical affine/rigid round-trip <=1e-6 mm; distortion-free projective round-trip <=1e-6 mm and <=1e-6 px; nonlinear lens inverse <=1e-3 px under declared solver limits; fitted rigid fiducial RMS <=0.05 mm and maximum <=0.10 mm; projective reprojection RMS <=0.5 px and maximum <=1.0 px. Rigid baseline >=10 mm and pair-distance disagreement <=0.10 mm; homography fiducial convex-hull coverage >=10% of the intended board ROI. Condition number <=1e8 after coordinate normalization; projective denominator absolute value >1e-12 under the stored matrix normalization. Independent synthetic checkpoints use the corresponding rigid/projective RMS and maximum limits, in addition to known-transform numerical oracles. All calibration numbers in these documents refer to this synthetic policy unless another policy is explicitly selected. They are not production defaults, verified accuracy or a hardware error budget.

CalibrationPolicy is configurable, immutable data: policy ID/version, purpose synthetic/production, applicable model/algorithm, unit-bearing numerical/solver tolerances, minimum counts/baseline/coverage, pair-distance bound, conditioning/denominator limits, fit and independent-check residual limits, required independent evidence, valid domain, and evidence/approval references. Missing, nonfinite, negative or inconsistent limits fail POLICY_INVALID. Select a policy explicitly; no synthetic fallback for a production request. Changes create a new version and require revalidation before activation. Production policies and qualification evidence are TBD. Synthetic records remain visibly synthetic even when active for tests and cannot satisfy production context.

Unvalidated mappings return typed errors and no usable conversion or active mapping. At BuildInspectionInput, return blocked status with disposition REVIEW, reason codes and available machine/board/load/capture/policy context, without usable ROIs. REVIEW means uninspectable pending correction, not a defect judgment. Missing independent validation evidence yields MAPPING_UNVALIDATED. Never substitute identity, stale calibration or weaker policy; this condition cannot produce GOOD. Other geometry callers receive rejection rather than an inspection verdict.

Calibration and registration states: draft -> validated -> active -> invalidated; activation is explicit, immutable records are superseded rather than edited. Reject inactive, invalidated, expired (when expiry is configured), or incompatible records. A camera configuration or fixture change invalidates the relevant path. Board revision/load changes invalidate registration; machine/camera replacement invalidates that machine's calibration. Historical records remain readable for replay. No stale fallback to another machine, camera, side, revision, or load is permitted.

## 4. Typed data models

The following is a language-neutral schema proposal, not implementation code. All IDs are nonempty strings in their declared namespace; all numbers are finite binary64 values unless stated. Required means non-null. Versioned schema and validation policy IDs appear on every published aggregate. Unknown enum values fail schema validation. Optional fields distinguish unknown from empty/zero.

| Model | Required fields and constraints |
| --- | --- |
| Point2 / Polygon2 | x,y plus frame_id; polygon exterior and holes, closed topology, no self-intersection, positive area. Physical canonical values are mm. |
| Frame | frame_id, kind, unit enum mm/inch/px/source-unit, axis directions, origin description, board/machine/capture association as applicable. |
| Transform2 | transform_id, from_frame, to_frame, type rigid/affine/homography/reflection, normalized 3x3 matrix, unit declarations, parity, valid_domain, provenance, validation metrics; inverse is derived and checked. Distortion uses a separate model record. |
| BoardCapacity | capacity_id/version, width_mm=280, height_mm=550; explicit capacity-test orientation in request; no travel bounds. |
| FixtureEnvelope | envelope_id/version, machine_id, fixture_id/configuration, frame_id M, usable region/exclusions, margin_mm, evidence status synthetic/qualified; unresolved geometry is absent. |
| CameraTravelEnvelope | envelope_id/version, machine_id, camera_id, mechanical configuration, frame_id M, reference point definition, permitted region/exclusions, evidence status; physical dimensions TBD; does not itself prove optical coverage. |
| FitReport | Separate capacity/fixture/camera-reachability statuses pass/fail/unresolved; envelope IDs/versions, violations and unresolved reasons; no targeting authorization. |
| CalibrationPolicy | policy_id/version, purpose, model applicability, unit-bearing limits, required independent evidence, valid domain and evidence/approval references per section 3. |
| CameraCalibration | calibration_id, machine_id, camera_id, raw and undistorted sizes (positive integer width/height), intrinsics, lens_model_name/version and named parameters, configuration fingerprint, valid plane/domain, validation policy/results, state, created_at UTC, optional expires_at, parent calibration/mapping when derived. No fixed coefficient length for every lens model. |
| BoardRegistration | registration_id, board_revision_id, machine_id, load_id, load_side, fixture_id/configuration, frame path, fiducial observations, fit diagnostics, policy_id, state. |
| CaptureGeometry | capture_id, machine_id, camera_id, raw_image_size, configuration fingerprint, board_revision_id, load_id, side, calibration_id, registration_id, effective_homography_id, capture pose if relevant, timestamp UTC. |
| SourceArtifact | artifact_id, role, original filename, byte length, SHA-256, format/version, parser profile/version, source_frame_id if geometric, declared units/layer/side, source revision claim, provenance. |
| ImportManifest | schema_version, board_id, revision_label, profile, artifact list, role/side/layer assignments, source conventions/transforms and evidence, field mappings, authority decisions, fit policy, validation policy. |
| BoardRevision | board_id, immutable revision_id, human revision_label, content_digest, parent_revision_id optional, outline and cutouts in P, datum, side/layer map, artifact IDs, source transforms, component/pad/paste/fiducial collections, validation report, schema_version. Revision label alone is not identity. |
| FootprintInstance | footprint_id, reference, library_identifier optional, side, source local frame, transform to P, normalized orientation and parity, body/courtyard geometry optional, provenance. Footprint name does not imply known physical size. |
| Component | component_id, unique reference, footprint_id, position P, orientation_deg, side, value/part_number optional, assembly_state populated/DNP/unknown, placement provenance. DNP is distinct from missing placement. |
| Pad | pad_id, footprint_id, pad_number string (not globally unique), side/layers, copper geometry in P, drill optional, pad_type, net optional, source provenance. IDs stay unique when pad numbers repeat. |
| PasteFeature | paste_id, side, resolved filled geometry in P, source aperture/region provenance, optional linked pad IDs and match confidence. Many openings may map to one pad and some openings have no pad match. Paste geometry is not replaced with copper-pad geometry. |
| BomItem | bom_item_id, expanded unique references, quantity positive integer, value/part_number optional, raw fields, normalized population status, provenance. Group quantities must match expanded references under the manifest policy. |
| Fiducial | fiducial_id, side, position P, shape/size, source footprint/pad IDs optional, provenance, approved classification. Never identify every circular pad automatically as a fiducial. |
| ValidationReport | report_id, status accepted/rejected, errors, warnings, checks/results, policy_id, unresolved/conflicting fields, artifact digests, canonical digest if accepted. |
| ContractError | code enum, message, artifact/entity ID optional, field_path, expected/actual optional, source location optional, remediation, severity error/warning. Return all safely discoverable issues in stable order. |

Stable entity IDs are scoped to an immutable revision. Canonical serialization, deterministic ordering, source bytes, transform decisions, parser/schema versions, and policies contribute to the content digest; timestamps and filesystem paths do not. Same normalized inputs and manifest yield the same digest. Reusing a human label with different content creates a different revision with a conflict warning requiring acknowledgment; never overwrite a revision. Cross-revision equivalence of individual parts is not assumed.

## 5. Import pipeline and contracts

AOI Platform V0.1 initially targets KiCad 10.0.7. Target selection is not compatibility verification: REAL-PCB-01-r1 has KiCad 10.0.7 executable/export evidence and acquisition acceptance in supported-inputs.md; parser versions and compatibility results remain TBD. The real `REAL-PCB-01` bundle in supported-inputs.md is a Sprint 2 entry prerequisite; its export presence does not require Gerber or tabular import to be implemented before Sprints 3 and 4 respectively. Only evidence-backed combinations may enter a released support allowlist. Isolated evaluation may exercise a candidate input profile to establish that evidence, without publishing a supported-compatibility claim.

### Profiles and authority

Before implementing Gerber parsing from scratch, evaluate reuse of PyGerber or Gerbonara against the target construct/fixture matrix in supported-inputs.md. Record the exact evaluated version, license, API and geometry precision, polarity/region/macro/transform handling, source-location/provenance retention, bounded resource behavior, and positive/negative fixture results. Prefer an adapter to a suitable library. A from-scratch parser requires a documented evaluation explaining why reuse is insufficient and a separately reviewed scope; no such choice is made here. Library acceptance is not proof of semantic support: reject unsupported constructs explicitly with FORMAT_UNSUPPORTED and source location, never silently omit or approximate them. Candidate versions, evaluation results and selection are TBD.

Target input contract (verified support is recorded only in supported-inputs.md): KiCad `.kicad_pcb` s-expression boards through explicitly versioned parser profiles; Gerber RS-274X Paste with declared format/units and side/layer (X2 attributes, when present, must agree); CSV/TSV placement and BOM through named column/convention profiles or explicit manifest mappings. No exact parser-supported versions are evidenced yet; compatibility remains TBD in supported-inputs.md, separately from accepted fixture/export provenance. Release claims require exact KiCad/exporter and parser/library versions, settings, fixture hashes, independent oracles and test results. Unrecognized versions, aperture macros, transformations, or polarity operations must fail if they cannot be interpreted correctly; do not skip them. Legacy KiCad `.brd`, Gerber X3 placement, ODB++, IPC-2581, panel expansion, and automatic file-convention guessing are deferred.

KiCad supplies authoritative outline, footprints, copper-pad geometry and design fiducial candidates. Gerber supplies authoritative manufactured paste openings after polarity/region/aperture processing. Placement supplies assembly positions and orientations, cross-checked with KiCad. BOM supplies assembly metadata and population state. Authority is field-specific; an override must name the field, reason, source and reviewer decision in the manifest. No automatic last-file-wins merge.

Import profiles:

- `geometry`: KiCad plus manifest; produces validated board geometry, explicitly marked as not yet inspection-ready.
- `spi-2d`: geometry plus Gerber Paste for every selected inspection side; pad-to-paste links may remain unresolved with warnings, but paste geometry and its transform must be valid.
- `post-placement-2d`: geometry plus placement and BOM for every selected assembly side. Every populated inspectable reference must resolve to one footprint and placement. Explicit BOM/DNP exclusions are retained. Mechanical/non-assembly footprints require explicit classification. Unknown population or unresolved references block this profile.
- A combined request must pass both profiles. Missing optional data remains absent with a capability/coverage report; it never appears as evidence of no components or no paste.

### Artifact inventory slice (authorized 2026-10-19; tasks 3.4/5.1 PARTIAL)

`inventory_artifacts(manifest, byte_sources, limits)` is byte admission only, not ValidateImport or NormalizeBoard. The new immutable `InventoryManifest` schema `artifact-inventory-v1` contains profile (`geometry`, `spi-2d`, `post-placement-2d`, or `combined`, an explicit spelling of both inspection profiles), separate `spi_sides` and `assembly_sides` tuples of `top`/`bottom`, fixture revision, source snapshot identity, and artifact declarations. Unused requested-side tuples must be empty; active inspection profiles require a nonempty side tuple. Geometry always requires at least one participating `kicad_pcb`; SPI additionally requires participating `paste` for every SPI side; post-placement additionally requires `placement` and `bom` for every assembly side. Artifact side coverage is explicit (including both sides for one CSV); it is a declaration, not parsed evidence. Paste declarations name one side. No upper role cardinality is inferred: repeated roles are allowed with distinct artifact IDs. Cross-file consistency is later work. `supporting` roles are reference-only, for provenance/license/population artifacts; reference-only artifacts never satisfy mandatory roles but are still hashed and can fail inventory.

Each `ArtifactDeclaration` retains ID, role, opaque source ID, optional declared size, declared SHA-256, side coverage, reference-only flag, and immutable string key/value metadata and provenance. Metadata/conventions are opaque declarations, normalized only in ordering; empty string values are preserved, duplicate keys reject rather than overwrite. Manifest provenance applies to every record. Digest syntax is exactly 64 hexadecimal digits; preserve declared case and compare case-insensitively. The API accepts typed records (not a permissive JSON dictionary); malformed field values return rejected diagnostics at the boundary. It does not upgrade the acquisition manifest into an import schema automatically.

Return types are `InventorySuccess(inventory, report)` versus `InventoryFailure(report, evidence)`; failure has no inventory property. Evidence retains bytes read and EOF status, with complete size/digest only when EOF was observed. A completed read on a failed request is diagnostic evidence, never partial success. Success freezes declarations and verified byte observations separately; successful report scope explicitly says artifact bytes, not geometry/design-revision equivalence/parser compatibility/readiness. No canonical BoardRevision digest is created.

`byte_sources` is a trusted mapping from opaque IDs to zero-argument factories returning a fresh blocking binary stream implementing `read(n)` and `close()`. Inventory owns each returned stream and attempts close exactly once, including read errors and resource rejection; callers must not supply shared open streams. Unused mapping entries are neither opened nor enumerated. This API never opens paths, downloads URLs, extracts archives or evaluates fixture scripts. Factories are application code, not manifest data; they must honor bounded reads and perform their own I/O timeout control. No local-path adapter is introduced. Local verification uses explicit allowlisted paths under the supplied fixture root, not paths selected by manifest content.

`InventoryLimits` requires a policy ID, positive integer artifact count, per-artifact byte, total byte and chunk limits (bool rejected; chunk bounded to 1 MiB as an implementation memory ceiling). Count/schema gates run before opening sources. Traversal is sorted by artifact ID after duplicate checks; source mapping order is irrelevant. Each read requests at most chunk bytes and remaining byte budget plus one sentinel byte. That single-byte lookahead distinguishes exact-limit EOF from overflow; at most one byte beyond a budget is consumed before the whole request stops. All consumed bytes, including failed sources and reference-only sources, count toward the total. EOF alone establishes actual size and full SHA-256. Partial reads are supported; non-bytes, oversized returns or nonblocking None are source protocol errors. Invalid configuration yields POLICY_INVALID; count/byte exhaustion yields INPUT_LIMIT_EXCEEDED. Stop further reads after a limit/protocol/close failure; safely continue independent source-open/read and hash/size failures only while budgets permit. Schema failures return without I/O. No dependency is added for parsing.

Reuse ContractError/ValidationReport ordering and preserve duplicate meaningful issues. Extend ErrorCode additively with normative import codes FORMAT_UNSUPPORTED, REQUIRED_ARTIFACT_MISSING, DUPLICATE_ID, SOURCE_CONFLICT, INPUT_LIMIT_EXCEEDED and inventory I/O codes SOURCE_NOT_FOUND/SOURCE_IO_ERROR. Invalid schema/digest uses SCHEMA_INVALID; hash/size mismatches use SOURCE_CONFLICT. Diagnostics carry known ID/role/source, named field location, separate expected/actual, fixture/snapshot, and policy/limits. Exception type/stage is recorded without unstable or potentially sensitive OS error text. Tasks remain partial: entity models, import decoding, geometry semantics, reconciliation and publication are outside this slice.

### Operations

| Operation | Input | Output and failure semantics |
| --- | --- | --- |
| ValidateImport | Manifest + byte-addressable source artifacts + policy | ValidationReport and a non-published candidate if parseable; errors prevent promotion. No persistent mutation of an existing revision. |
| NormalizeBoard | Fully resolved manifest, parsed artifacts, accepted validation decisions | Immutable BoardRevision + accepted report; atomic publication only after all requested profile gates pass. Failure returns report and no published revision. |
| ResolveTransform | from/to frame IDs + explicit revision/load/capture context | One validated frame path with provenance, or TRANSFORM_MISSING/CONTEXT_MISMATCH/TRANSFORM_AMBIGUOUS. Multiple paths must agree within tolerance or fail. |
| ConvertPoints | finite points, from/to frame IDs, path ID/context | Same ordered number of points + path/calibration IDs; fail the batch with indexed errors if any point is outside domain or not convertible. No mixed silent successes. |
| FitRegistration | expected fiducials + observations + fit type + explicit context/policy | Draft registration/calibration candidate + residuals/inlier IDs/quality report; validation/activation remains explicit. No movement or acquisition. |
| ValidateFit | BoardRevision outline + BoardCapacity + capacity-test orientation + optional load transform/FixtureEnvelope/CameraTravelEnvelope | FitReport with separate statuses, violations and unresolved inputs. Camera reachability unresolved pending future optics/mechanics validation; no controller action. |
| BuildInspectionInput | accepted revision + capture geometry + ROI feature IDs + selected CalibrationPolicy | Tagged ready result with engine-neutral identities, image reference/size, ROI polygons, mappings, side, units and visibility; or blocked result with disposition REVIEW, reasons and context, no usable ROIs, when required profile/mapping/context cannot be validated. |

### Contextual affine resolver policy (Sprint 1 decision)

The resolver implementation for this slice accepts only a directed acyclic graph of registered affine `Transform2` edges. It traverses registered edges in their declared direction; it never synthesizes inverse edges. Callers may register the result of the existing explicit `inverse()` operation as a separate edge, subject to the same DAG and validation rules. A cycle is rejected with the typed `TRANSFORM_CYCLE_UNSUPPORTED` error. This is an implementation limit of the current resolver. The normative transform contract's invalid-path and ambiguity requirements remain in force; any future cycle-capable resolver remains open work and does not get silently waived.

Every candidate path is checked end-to-end. All frame metadata on every intermediate node participates in context validation; a missing value at an intermediate frame cannot bridge conflicting nonempty revision, machine, or capture identities elsewhere on the path. Pixel/image frames, projective maps, and camera mappings are outside this resolver.

Path consistency uses the separately versioned `synthetic-path-consistency-v1` policy (default tolerance `1e-6 mm`), not the round-trip or production-accuracy tolerances. The caller must provide a finite, nonempty rectangular domain in the source frame, with declared coordinates and units. Each candidate is evaluated at all four rectangle vertices. Euclidean output differences are converted to millimeters using the target frame's declared physical unit; the largest difference across vertices and path pairs must be at most the selected policy tolerance. Missing/invalid domain or policy fails explicitly. Every eligible path is enumerated within the configured path/edge limit; resource exhaustion fails explicitly and never returns a partial result. If paths disagree, resolution fails with ambiguity/inconsistency. If they agree, a deterministic representative is selected by lexicographic transform-ID sequence and the result records all examined path IDs, policy ID/version and domain.

This policy distinguishes the newly decided consistency procedure from the existing normative requirement that ambiguous paths fail. It does not define camera calibration, physical accuracy, or import-report aggregation.

Sprint 1 diagnostic implementation convention: immutable GeometryError payloads retain known request evidence at resolver and ValidateFit boundaries and preserve mismatches as separate expected/actual diagnostic text. Frame contexts use role-prefixed keys, so conflicting source/target/envelope values cannot overwrite each other. The ContractError adapter automatically retains this evidence; conflicting caller additions reject rather than overwrite. Path evidence policy `path-evidence-v1` records a deterministic prefix bounded to 32 paths, 128 IDs total and 8192 UTF-8 bytes of encoded IDs per summary, with explicit omitted path/transform counts. Search budgets remain independent and binding. Oversized graphs report omitted edge counts without diagnostic enumeration. These are representation/resource conventions, not relaxed normative geometry checks or inferred missing metadata.

Artifact ingestion is read-only, bounded by configured byte/entity limits, and never executes source content. Decode settings, CSV delimiter, decimal convention, encoding, and header mapping are declared. Decimal comma requires a compatible delimiter and explicit profile; units cannot be inferred from magnitude. NaN/Inf, zero-scale transforms, invalid layer assignments, malformed outlines, or empty required collections fail.

Validation steps: inventory and hashes -> parse and source semantics -> source-frame resolution -> normalization -> outline/topology -> entity joins -> profile coverage -> cross-source reconciliation -> BoardCapacity feasibility -> accepted report. Staged source data remains available for diagnostics on failure but is not an accepted revision. Physical envelopes are not required for import. A load needs a separate fixture check; targeting needs future travel/coverage validation.

Proposed synthetic-import-v1 reconciliation test tolerance (not verified production accuracy or an operational default) is <=0.05 mm positional and <=0.1 degree angular disagreement, measured after transforms and declared component symmetry (default 360-degree period, never guessed). A mismatch fails unless a reviewed authority decision resolves it. Check placement references, sides, footprint identity, duplicate references, BOM quantity/reference expansion, missing/excess references, and paste alignment evidence. Known DNP entries may have a footprint without a populated placement; mechanical features need explicit exemption. Fiducial correspondences or declared exporter datum evidence establish source registration; matching extents alone is insufficient. Source revision labels and file hashes cannot prove that separate exports came from the same board. Record explicit revision attestation and geometric checks; reject contradictions, and block promotion when consistency cannot be established.

## 6. Errors

BOARD_CAPACITY_EXCEEDED means the declared capacity-test orientation exceeds BoardCapacity. BOARD_OUT_OF_ENVELOPE means a loaded outline violates an explicitly supplied FixtureEnvelope. Unresolved physical dimensions are FitReport states, not invented pass results. POLICY_INVALID rejects invalid/mismatched policy data; MAPPING_UNVALIDATED rejects missing independent validation evidence. Inspection-boundary mapping failures carry the underlying error codes and disposition REVIEW.

Blocking codes: SCHEMA_INVALID, FORMAT_UNSUPPORTED, PARSE_FAILED, INPUT_LIMIT_EXCEEDED, UNITS_UNKNOWN, SOURCE_CONVENTION_UNKNOWN, TRANSFORM_MISSING, TRANSFORM_AMBIGUOUS, TRANSFORM_SINGULAR, TRANSFORM_ILL_CONDITIONED, OUTSIDE_VALID_DOMAIN, POINT_AT_INFINITY, CONTEXT_MISMATCH, CALIBRATION_INVALID, CALIBRATION_STALE, IMAGE_SIZE_MISMATCH, FIDUCIAL_INSUFFICIENT, FIDUCIAL_DEGENERATE, REGISTRATION_QUALITY_FAILED, OUTLINE_INVALID, BOARD_CAPACITY_EXCEEDED, BOARD_OUT_OF_ENVELOPE, POLICY_INVALID, MAPPING_UNVALIDATED, DUPLICATE_REFERENCE, DUPLICATE_ID, REFERENCE_UNRESOLVED, BOM_QUANTITY_MISMATCH, SIDE_LAYER_MISMATCH, SOURCE_CONFLICT, REVISION_MISMATCH, REQUIRED_ARTIFACT_MISSING, PROFILE_INCOMPLETE. Warnings include OPTIONAL_DATA_ABSENT, PASTE_PAD_UNMATCHED, REVISION_LABEL_REUSED, and ACKNOWLEDGED_SOURCE_OVERRIDE. Warnings cannot downgrade a mandatory gate. Reports identify source rows/entities where possible and describe a concrete correction.

## 7. Optional inspection component and six-machine isolation

The [Aman9y/open-aoi README](https://github.com/Aman9y/open-aoi/blob/main/README.md), reviewed 2026-10-16, describes an OpenCV inspection/alignment pipeline and region-oriented comparisons. This motivates an optional adapter, not an assertion of native KiCad/Gerber import or API compatibility. Before reuse, pin a commit and review its license, data types, pixel conventions, and alignment behavior.

The proposed adapter accepts BuildInspectionInput and returns feature-linked observations with explicit output frame, revision/capture IDs, quality status, and the engine's applied alignment/crop transform. Pixel displacements cannot be relabeled millimeters without the validated local mapping. Missing/unknown engine transforms produce an unusable result, never an assumed identity. Image-aligned coordinates may be reported in I_e; machine/PCB coordinates are derived only through known paths. No engine result can mutate source geometry or calibration. Adapter absence leaves all foundation imports and geometry tests operational. Detector evaluation and decision thresholds are deferred.

Machine-scoped keys include machine_id and camera_id; captures also bind revision, side, load, and calibration identities. A synthetic six-machine test uses overlapping capture names and different transforms to prove isolation in one process. Queueing, networking, and throughput are deferred; these identities do not imply a distributed architecture.

## 8. Verification and remaining decisions

All proposed tests use file fixtures, synthetic images/points, and fake metadata. They need no physical camera, motion hardware, firmware, external inspection engine, or network. Capability specs carry the normative scenarios and tasks trace them into later work. Round-trip tests are paired with independently calculated forward values so equally wrong forward and inverse mappings cannot pass unnoticed.

Reviewer decisions: preserve the canonical conventions; approve configurable synthetic policies and independent validation evidence; identify the real PCB and record KiCad 10.0.7 producer/build evidence, exporter settings and parser versions; evaluate the Gerber reuse candidate. Fixture geometry/margins and camera travel/coverage await optics/mechanics selection. Unverified support and all production qualification remain TBD. Actual optical accuracy and board warp limits require later hardware evidence. No production readiness is claimed.

## 9. Implementation acceptance levels

These are future implementation acceptance gates, not statements of current completion. Both levels preserve every GEO-001 and PCB-001 requirement and the future 3D boundary. Numeric limits remain selected versioned synthetic policies. Neither level proves physical accuracy, travel/coverage, production calibration or inspection performance. OpenSpec document validation checks change structure only; it is not implementation acceptance evidence.

### Foundation Prototype

Target: after Sprint 4, subject to all gates below. A restricted import demonstration is permitted while full capability conformance remains explicitly open.

1. Typed frame/point/transform/context models and source-to-PCB/machine conversion pass independent stage oracles, composition/inversion, angle/parity, unit and invalid-path tests under the selected synthetic policy. The canonical equations and (1,2) inch -> (60.8,45.4) mm result remain unchanged.
2. One real KiCad 10.0.7 board bundle meets the Sprint 2 prerequisite. Its actual `.kicad_pcb` imports with independently checked outline, footprints, pads and explicitly classified fiducials. Producer/build/settings, artifact hashes and parser version are recorded. Missing real fixture evidence blocks this gate.
3. A documented pinned PyGerber or Gerbonara reuse evaluation precedes the Paste adapter. The real F.Paste imports with explicitly evidenced source alignment, independent filled-geometry checks and preserved provenance. B.Paste is tested when bottom-side SPI is requested. Unsupported constructs fail explicitly, even when the library accepts them.
4. The real placement/BOM reconcile with that same revision using declared origin/units/angles/sides, references, quantities and population states. Synthetic negative companions exercise duplicate/unresolved references, conflicting sources and missing required artifacts. The requested SPI/post-placement profile gates pass only for the evidenced subset; untested support stays TBD.
5. Accepted revisions are immutable and reproducible, carry artifact/transform/parser/policy provenance, and survive failed-import rollback. Same-label/different-content and mixed-revision cases are tested. Frame and machine context cannot silently cross namespaces; synthetic mismatched-context tests pass for the implemented transformations. Full six-machine camera/calibration isolation remains OPEN until Sprint 5 evidence exists.
6. BoardCapacity, FixtureEnvelope and CameraTravelEnvelope stay separate, with unresolved physical checks reported as unresolved. Missing/unvalidated camera mappings cannot yield usable inspection coordinates or GOOD: unavailable geometry operations reject, and any exposed inspection boundary returns blocked REVIEW. Unsupported paths are disabled or explicitly rejected, never approximated by identity/stale calibration.
7. An acceptance report states the exact implemented subset, fixture/test evidence and all incomplete requirement/scenario names with original task IDs and planned follow-up. `sprint-plan.md` is the initial OPEN register. Passing this milestone does not close the change, mark unimplemented requirements satisfied, or turn partial tasks into completed tasks.

### Foundation Complete

Target: after Sprint 5 and any remaining closure work; elapsed sprints alone are insufficient.

1. All Foundation Prototype gates remain satisfied. Every normative requirement and scenario in both capability specs has traceable implementation and executed passing evidence, including supported positive cases and required rejection cases. No incomplete in-scope normative requirement may remain OPEN. Partial implementation or deferred in-scope tests blocks this level; do not relabel them optional or remove them for acceptance.
2. Camera projection, lens mapping, raster transforms, runtime dimensions and domains pass independent synthetic oracles. Two-fiducial metric rigid registration and four-or-more-point homography pass their distinct fit and independent-validation gates; missing evidence produces typed rejection and REVIEW.
3. Calibration-policy version/purpose enforcement, activation/invalidation, historical context and six-machine isolation pass the complete specified scenarios. Synthetic results cannot qualify production context; no real camera or firmware is needed for these software tests.
4. All import scenarios, real-fixture coverage and additional representative positive/negative fixtures pass. Exact tested versions/settings/library/adapter versions and results are recorded in supported-inputs.md; unsupported combinations have explicit rejection evidence. One real fixture is a baseline, not proof of every construct or dialect. Valid profiles for both sides must be exercised where the normative scenarios require them; the seed fixture need not itself have bottom-side SPI.
5. Every original implementation task has evidence or an explicitly justified optional-path decision consistent with the specs; no normative behavior may be waived. A decision not to integrate open-aoi is permitted, but its evaluation and fake-engine boundary tests remain required. Every scenario maps to evidence; reruns are offline and reproducible. Only Geometry Core evidence currently exists; it does not establish complete capability conformance.
6. Future 3D, physical travel/coverage, production accuracy, firmware and deployment remain explicitly outside this change. The specification requires these boundaries to remain unresolved, not a hardware qualification project to be completed. Foundation Complete is software-foundation conformance only.

### Selected Sprint 1 fixture subset (user decision, 2026-10-17)

These implementation decisions supplement, and do not narrow, the original normative requirements. The user explicitly selected axis-aligned rectangles in machine frame M for usable regions and exclusions, and single closed board contours of lines and circular arcs. Holes, splines and nonrectangular envelopes reject with `GEOMETRY_UNSUPPORTED`; broader normative geometry support remains open in the implementation ledger.

The selected contact policy permits contact with the usable boundary at zero margin. Exclusions are closed: intersection, either direction of containment, and boundary contact all fail. Positive margin requires minimum Euclidean clearance at least the declared margin from both the usable boundary and exclusions; exclusion contact is always forbidden. Fixture evaluation uses the entire outline after an explicit validated proper-rigid load into the exact envelope frame. It does not infer a load from matching IDs, reuse capacity rotation as placement, or treat a bounding box or endpoint sample as the filled board. Rectangle outer containment uses analytic full-contour extrema; exclusion checking combines analytic curve/rectangle distance with both containment directions.

Implementation numerical policy `fixture-binary64-v1` uses the bounded contour kernel (coordinates/radii <=1e6 mm, <=512 edges) and a 1e-8 mm arithmetic guard. Outer signed clearance and positive-margin distance comparisons allow at most that guard for roundoff; exclusion contact/overlap predicates conservatively reject separation <=1e-8 mm. This is not manufacturing tolerance or qualification evidence. A 0.001 mm outer overrun or margin shortfall must fail. Exact margin is accepted unless exclusion contact is involved. Near-contact configurations within the guard can conservatively fail and are not certified physically clear.

Missing usable geometry, margin or explicit load leaves fixture status unresolved with reasons. Supplied unsupported geometry rejects even when another input is missing. Capacity remains independent of placement; camera reachability always remains unresolved, including with a travel rectangle. Fit results retain policy, context, record identities/versions and evidence IDs and never authorize motion or targeting. Synthetic evidence is never promoted to qualified evidence. Import integration, broader outline/envelope geometry and lifecycle qualification remain open.

### Evidence and status rules

Record level, candidate revision, fixture/source hashes, selected policy IDs, exact versions/settings, test identifiers/results, and per-requirement status OPEN/PARTIAL/SATISFIED. PARTIAL is still open for conformance. Only recorded passing evidence can promote a scenario; one passing scenario cannot close a requirement with other open scenarios. Prototype acceptance may coexist with OPEN requirements. Complete acceptance may not. Current state: Geometry Core has executed synthetic tests; tasks 4.1–4.4 and acquisition gate 7.1 are completed. Neither acceptance level is achieved. Remaining implementation/fixture/calibration results stay open or TBD; see implementation-status.md. See sprint-plan.md for sprint entry/exit gates, original-task mapping and the initial open-requirement register.


## REVIEW DRAFT: immutable canonical Pad candidate (2026-10-23)

Status: proposal only for parts of tasks 3.4/5.5/5.13; no product implementation,
reader bridge, BoardRevision construction or publication. D1-D5 were selected by the user; the refinement below is controlling.
Numeric policy values and explicitly listed open decisions still require review. This section does not amend normative
requirements or imply compatibility from accepted evaluation observations.

### Normative requirements versus proposed subset

PCB-001 `Canonical outline, footprints, components, pads, and fiducials` requires
unique pad identity, repeated source number strings, copper geometry/transforms,
side/layers and provenance; its invalid-input scenario requires rejection before
publication. GEO-001 requires physical P in mm, X right/Y up, revision context,
explicit directed transformations and no guessed origin or bottom reflection.
Design section 4 scopes stable IDs to an immutable revision and defines Pad fields;
section 5 separates candidate validation from atomic publication.
These are existing requirements. Rectangle-only/SMD/top-only support, API names,
polygon representation, identity syntax and batch limits below are NEW proposals.
They cannot close the full tasks or the combined bottom/cutout scenario.

### Existing implementation constraints

- `Frame`/`Point2` in `src/aoi_platform/geometry/models.py`: full frame metadata,
  physical units, finite values; PCB frame requires board_revision_id and mm/right/up.
  `require_same_frame` compares the full record, not only its ID.
- `Transform2` in `geometry/transforms.py`: directed column-vector affine maps,
  explicit conversion/rotation/translation/reflection factories and composition;
  `conventions_validated`, singularity/conditioning and parity are existing guards.
  A transform's numerical validity is not independent evidence of a correct source datum.
- `TransformGraph` in `geometry/resolver.py`: explicit DAG/path/context/domain policy.
  First candidate slice proposes an already supplied transform, no new graph search.
- `ContractError`/`ValidationReport` in `geometry/reports.py` preserve diagnostics,
  expected/actual and stable ordering. Adapter preserves GeometryError evidence.
- `InventorySuccess` in `inventory.py` proves admitted artifact bytes only. It does
  not establish source geometry, same-design revision, parser support or readiness.
- No current product Pad model/reader-to-canonical bridge exists. Evaluation UUID
  rejection is not product entity validation.

### Proposed API and immutable records (not yet selected)

`build_rectangular_pad_candidates(request, limits) -> PadBatchSuccess | PadBatchFailure`

Frozen dataclasses with immutable nested tuples; no mutable dict/list references.
All identity/context fields supplied by caller; function generates no identity.

| Record | Proposed required fields and semantics |
| --- | --- |
| Request | schema_version, policy_id/version, board_id, candidate_scope_id, target Frame P, successful ArtifactInventory, tuple of parent records, tuple of source pads |
| Parent | footprint_id, source_entity_id, source artifact_id/hash, source Frame, side, validated source-to-P Transform2 and independent convention evidence IDs |
| SourcePad | pad_id, footprint_id, source_entity_id, pad_number exact string, side, explicit copper layers, pad_type, source Frame, rectangle, provenance; optional net; drill explicitly absent for this subset |
| Rectangle | center Point2, width/height strictly positive in source-frame units, pad-local orientation with declared zero/direction; suggested input basis +X right/+Y up and CCW degrees |
| Provenance | artifact_id, source_id, computed SHA-256 and source snapshot/fixture revision references matched to inventory; source pad/parent identifiers, producer/parser or synthetic authoring profile/version, declaration/evidence IDs and optional actual SourceLocation |
| Candidate | unchanged pad/footprint/number/source IDs, side/copper layers/type/net, four copper boundary vertices Point2 in P, original rectangle/frame, full applied transform and convention evidence, provenance, candidate scope/schema/policy; published=False, targeting_authorized=False |
| Success | tuple of all candidates plus ValidationReport with explicit scope canonical-pad-candidate-only; not import-ready/BoardRevision accepted |
| Failure | ValidationReport plus bounded diagnostic evidence; NO candidates property or partially usable geometry |

Parent IDs must resolve exactly once in request; source pad parent association and
artifact/context must match the parent record. Require unique pad IDs across batch
and unique parent IDs; repeated pad numbers remain permitted and unchanged. Source
entity IDs are scoped by artifact; never infer parent association from pad number.
Identity syntax/scope is D1/D2, not silently assumed to be KiCad UUID everywhere.
Missing source location remains absent; no fabricated lines or source metadata.
Source flags/assembly eligibility are not inferred from copper presence.

### Proposed rectangle transformation and independent oracle

Input rectangle is fully expressed in its declared source frame, including pad angle.
If this is footprint-local, the supplied transform must include footprint placement;
if board-source, it must not apply placement twice. Parent record declares which;
no inference from native API field names. Local corner order before transformation:
(-w/2,-h/2), (w/2,-h/2), (w/2,h/2), (-w/2,h/2), rotated about center then translated.
Output stores all four transformed corners with original index correspondence,
not an axis-aligned bbox. No repeated closing vertex. Reflection can reverse winding;
do not silently reorder, and do not treat winding as side. Filled polygon semantics
and reflection support require D3/D4. No rounded-corner/polygon approximation.

Independent proposed oracle: source mm/right/up, center (2,3), size (4,2), pad angle 0.
Source corners (0,2),(4,2),(4,4),(0,4). Explicit CCW90 then translation (10,20):
P corners (8,20),(8,24),(6,24),(6,20); center (7,22). Compute with integer formula
(x,y)->(10-y,20+x), without calling Transform2 to generate expected values.
If D3 includes reflection, explicit X reflection then same rotation/translation:
(8,20),(8,16),(6,16),(6,20), preserving corner association and reflected parity.
Test oracle tolerance proposed 1e-6 mm (1 nm), a synthetic assertion threshold,
not manufacturing tolerance or a policy to admit near-rectangular unsupported maps.
No intermediate rounding, no automatic bottom mirroring. Inch support, if chosen,
needs a separate independently calculated factor25.4 oracle and declared units.

### Validation, errors and all-or-nothing behavior

Validate request/schema/limits first; validate inventory membership, unique IDs,
parent association, geometry and contexts before constructing a success result.
Same frame ID with changed unit/origin/axes/context is a mismatch. Target must be
complete P; source and target revisions must match the selected candidate-scope
policy. Reject all known revision/machine/capture conflicts, never fill absent
metadata from another frame. Proposed first slice uses board-only context (no
machine/capture), top SMD copper F.Cu; other contexts/sides/layers reject explicitly.
No paste or mask geometry is generated from copper. D3 may broaden only by approval.

Explicit transform endpoints must match full source/target records. Missing mapping
is TRANSFORM_MISSING; unvalidated convention change is MAPPING_UNVALIDATED. Preserve
existing singular/ill-conditioned/context failures. Require supplied independent
convention evidence; evidence IDs are references, not signature/authenticity proofs.
No identity fallback, guessed unit factor/datum, or implicit resolver invocation.

Proposed supported maps after accounting for declared unit conversion: Euclidean
isometries (rotation/translation, and reflection only if D3 selected). Reject shear,
physical scaling, perspective/pixel/camera maps. Reuse the existing normalized
isometry guard if appropriate; its numerical policy must be documented, not silently
made looser. General affine support would require accepting parallelograms and a
separate geometry decision, not calling them rectangles.
Reject roundrect/custom/holes/drills/per-layer overrides and unsupported primitives
with GEOMETRY_UNSUPPORTED or FORMAT_UNSUPPORTED as appropriate, not truncation.
Malformed/nonfinite/nonpositive dimensions -> SCHEMA_INVALID; duplicates ->
DUPLICATE_ID; missing parent -> SCHEMA_INVALID with requested parent evidence;
artifact/hash conflict -> SOURCE_CONFLICT; context conflict -> CONTEXT_MISMATCH.
Invalid limits -> POLICY_INVALID; exhausted batch/diagnostic budget ->
INPUT_LIMIT_EXCEEDED, no success. No downgrade to warnings for required data.

Errors use ContractError and existing ValidationReport ordering; retain pad/parent,
artifact/hash, source/target frame snapshots, transform and policy when known.
Keep expected and actual distinct. Report all safely discoverable independent errors
within explicit limits; on exhaustion state incomplete diagnostics and blocking
budget error. No cross-batch persistence or mutation. No partial success inventory,
geometry/candidates on failure, or automatic deduplication. `accepted` report status,
if reused, applies only to this candidate operation and must carry that scope.

### Historical D1-D5 options (superseded by selection below)

| ID | Recommendation for smallest slice | Alternative / reason this needs a decision |
| --- | --- | --- |
| D1 candidate revision context | Caller reserves immutable candidate scope token, also used as Frame.board_revision_id; explicitly not a published revision or content digest | Separate candidate frame/context model avoids overloading existing revision field but expands core types. Existing spec does not settle prepublication identity allocation. Never generate/finalize revision ID here. |
| D2 identity and provenance binding | Opaque nonempty pad/parent IDs, exact string uniqueness scoped to candidate; separate source entity IDs; require successful inventory membership/hash | UUID-only canonical IDs or independently supplied provenance token are API choices not specified. Synthetic tests may use in-memory admitted authoring artifact; no native bridge required. |
| D3 supported subset | Start top-only SMD, F.Cu, mm/right/up source; rotation+translation only; reject all else explicitly | Add explicit reflection/inch/bottom support later with dedicated conventions/evidence. Normative full import still requires broader support. |
| D4 output geometry | Four indexed Point2 vertices, retain source corner order; filled convex quadrilateral, no bbox substitution | Or oriented rectangle type. Polygon ordering/serialization API is new; no canonical digest/publication is defined by this slice. |
| D5 resource/numeric policy | Explicit required limits for pads, parents, diagnostics, text/evidence lengths and finite coordinate/dimension bounds; positive integers, reject bool; named synthetic policy | Exact caps, isometry numeric guard and allowed empty batch still need selection. Recommend reject empty batch; test limits are not production defaults. |

The original options above are historical; use the selected contract refinement below. No product implementation has been authorized.

### Proposed acceptance after contract selection

Portable synthetic product tests: exact independent four-corner oracle, repeated
number strings with distinct IDs, duplicate/unknown-parent rejection, full-frame
mismatch (including reused ID), source/target context conflict, missing/unvalidated
mapping, unsupported transform/geometry, nonfinite/overflow, artifact/hash mismatch,
limits exact/exceeded and immutable/no-mutation inputs. Mixed valid+invalid batch
must yield failure with no candidate collection. Stable diagnostics and candidate
ordering under input permutations require a selected ordering policy (recommend
pad_id lexical ordering within scope); tests must not invent a revision digest.
Verify no published/targeting authority by result types, not a fake publication spy.
No native run needed. Candidate success is not PCB-001 import acceptance. Tasks
3.4/5.5/5.13 remain partial; Tasks 1.5/5.2 remain PARTIAL.


### Selected Pad candidate contract refinement (2026-10-23; review revision 2)

This subsection supersedes conflicting recommendations in the original draft.
D1-D4 and the structural parts of D5 are USER-SELECTED policy, not newly inferred
normative requirements. Numbers marked PROPOSED remain subject to review. Full
normative import/geometry scope remains open; no changes to Frame/Transform2 guards.

#### Selected identity, context and ordering

Caller supplies candidate_scope_id. Every source/target Frame used by a parent,
pad, point or transform must have board_revision_id exactly equal to that token.
It denotes unpublished revision context only: no content digest, accepted revision
or identity allocation is implied. target is FrameKind.PCB, mm/right/up. Proposed
source kinds SOURCE or FOOTPRINT; reject machine/capture context in this subset.
All complete endpoint records must match, including origin, axes and IDs.

Canonical pad_id and footprint_id are nonempty opaque strings, exact comparison
within candidate scope. Do not strip/normalize/case-fold or derive from pad_number.
Separate namespaces for pad and footprint IDs are proposed; do not impose a new
cross-type UUID namespace. Source entity IDs are paired with artifact_id; retain
original strings, no auto-generated mapping. All caller IDs are retained on output.
Candidate tuple order is pad_id lexical (Python Unicode code-point string order,
not locale collation). Diagnostics use existing ValidationReport ordering; neither
ordering implies a revision/content digest.

#### Field/type/requiredness and origin

Names describe proposed frozen dataclasses; R=required, O=optional. Tuples are deep
immutable and input objects are not mutated. Request does not read source bytes or
load native files. No arbitrary metadata dictionaries accepted.

| Record.field | Type; requirement | Source / validation |
| --- | --- | --- |
| Request.schema_version | str; R | Caller, exact proposed `rect-pad-candidate-v1` |
| Request.policy | SyntheticPadPolicy; R | Caller-selected exact ID/version and explicit limits; no defaults |
| Request.board_id | str; R | Caller board identity, not inferred from filename/hash |
| Request.candidate_scope_id | str; R | Caller reservation; equals every related frame revision context |
| Request.target_frame | Frame; R | Caller canonical P including explicit origin; no guessed datum |
| Request.inventory | InventorySuccess; R | Successful byte-admission result; embedded report accepted and evidence internally consistent; not authentication of object constructor |
| Request.parents | tuple[Parent,...]; R | Caller declarations; nonempty, unique footprint_id |
| Request.pads | tuple[SourcePad,...]; R | Caller declarations; nonempty, unique pad_id |
| Parent.footprint_id | str; R | Caller canonical ID within scope |
| Parent.source_entity_id | str; R | Caller source parent ID, artifact-scoped |
| Parent.artifact_id | str; R | Exact inventory artifact ID, exists once |
| Parent.source_frame | Frame; R | Explicit frame in which its pad rectangle coordinates are expressed; SOURCE or FOOTPRINT proposal |
| Parent.coordinate_basis | enum board-source / footprint-local; R | Caller; source frame kind must match chosen basis |
| Parent.side | literal top; R | Caller; mismatch with pad rejected |
| Parent.source_to_p | Transform2; R | Caller, complete endpoints match source_frame/target_frame; proper rigid only |
| Parent.convention_evidence | tuple[EvidenceReference,...]; R | Nonempty references for declared origin/axes/angle/placement; not inferred from `conventions_validated` alone |
| Parent.provenance | Provenance; R | Parent source identity/hash binding |
| SourcePad.pad_id | str; R | Caller, not pad number |
| SourcePad.footprint_id | str; R | Resolves exactly one parent |
| SourcePad.source_entity_id | str; R | Caller original pad ID |
| SourcePad.source_parent_entity_id | str; R | Caller declared association, matches resolved parent's source_entity_id |
| SourcePad.artifact_id | str; R | Same artifact as parent for this first subset |
| SourcePad.source_frame | Frame; R | Full equality with parent's coordinate frame |
| SourcePad.pad_number | str; R | Exact source string, repeated values allowed; whether empty string is allowed remains O2 below |
| SourcePad.side / copper_layers | literal top / tuple containing only `F.Cu`; R | Explicit declaration; duplicate layer entries rejected; no mask/paste derived |
| SourcePad.pad_type / drill | literal smd / literal None; R | Explicit absence of drill; holes/THT rejected |
| SourcePad.net | str or None; O | Source declaration if available; no invented empty/default net |
| SourcePad.rectangle | Rectangle; R | Filled rectangle, no cutouts/rounding/overrides |
| SourcePad.provenance | Provenance; R | Own source ID and parent assertion retained |
| Rectangle.center | Point2; R | Caller center in full source frame |
| Rectangle.width / height | finite positive float mm; R | Source dimensions; int inputs may convert to float, bool rejected |
| Rectangle.angle_deg | finite float; R | Explicit pad-local orientation, CCW from source +X, arbitrary finite angle within selected budget; do not require zero |
| Provenance.artifact_id / source_id | str; R | Both exactly match admitted ArtifactObservation.declaration |
| Provenance.computed_sha256 | 64 lower hex str; R | Exact computed hash of admitted complete/EOF artifact, not merely declared hash |
| Provenance.source_entity_id | str; R | Matches pad or parent field; parent assertion stored separately |
| Provenance.source_snapshot / fixture_revision | str; R | Exact inventory manifest references; claims, not proof of same design revision |
| Provenance.authoring_profile / version | str; R | Synthetic authoring or parser identity explicitly supplied; not invented by operation |
| Provenance.source_location | SourceLocation or None; O | Actual location if supplied; never fabricate line/column |
| Provenance.evidence | tuple[EvidenceReference,...]; R | Nonempty source-entity/association declaration evidence; bounded |
| EvidenceReference.artifact_id / computed_sha256 / locator | str; R | Reference to admitted evidence artifact + its computed hash + opaque source locator; no external fetch |
| Candidate | frozen record; R on success only | Copies pad ID/parent ID/number/side/layers/type/net, source rectangle/frame and provenance; carries board_id/scope/policy/schema, source_to_p, convention evidence and association verification status |
| Candidate.vertices | tuple[Point2,Point2,Point2,Point2]; R | Index 0..3 is source corner correspondence; all frame P; no closing vertex |
| Candidate.published / targeting_authorized | literal False; R | Fixed by result type, never caller-controlled |
| Candidate.association_status | literal declaration-consistent; R | Does not claim parsed-source verification |
| PadBatchSuccess.candidates / report | tuple[Candidate,...] / ValidationReport; R | Complete sorted batch; report scope `canonical-pad-candidate-only` |
| PadBatchFailure.report / truncation | ValidationReport / Truncation; R | No candidates/usable geometry field |
| Truncation.occurred / reason | bool / bounded enum or None; R | Whether processing/reporting was incomplete |
| Truncation.omitted_count | int or None; R | Exact only when known; None if scan stopped; do not invent a total |

Every required identity is nonempty without rewriting. Text validity is checked
before serialization. Inventory membership validates artifact ID, source ID, EOF,
actual size and declared/computed hash agreement, including reference-only evidence
artifacts; reference-only cannot supply the primary geometry artifact. Accepted
InventorySuccess is an in-process trusted result, not a security token/signature.

#### Parent association: what is and is not proved

The operation checks canonical parent lookup, same artifact/hash, source parent ID,
source frame/basis, side and candidate scope. It retains source locator and evidence
references. This proves consistency of supplied declarations with admitted bytes'
identities; it DOES NOT inspect those bytes to prove pad containment/membership.
A caller assertion or synthetic fixture oracle is not independent native-parser
verification. `declaration-consistent` must remain visible on success. A future
reader must supply its own source-aware association evidence and tests; this slice
cannot certify arbitrary source files. Requiring independently verified native
association here would require an out-of-scope reader; see O1 below.

#### Selected geometry and transform subset

Top SMD, only F.Cu; source mm/right/up; pad angle is explicit CCW about center.
For half extents (a,b), corners are (-a,-b),(a,-b),(a,b),(-a,b).
Apply R(pad_angle) then center translation in source, then source_to_p.
Proper rotation+translation only, no reflection/scale/shear. Preserve corner order;
output is the rectangle's four indexed P vertices, not its bbox or fitted rectangle.
Reject unsupported shapes and transform classes, do not project/approximate them.

PROPOSED enforcement: require TransformKind.RIGID and conventions_validated; reuse
existing Transform2 rigid validation: column squared norms within 1e-12 of 1,
column dot within 1e-12 of 0, rel_tol=0, Parity.PRESERVED. Existing finite/singular/
condition guards remain. Do not accept a raw AFFINE map merely because it happens
to approximate a rotation; caller must use validated rigid factories/composition.
Guard is numerical admission of floating-point rotation, not a physical stretch
allowance; slight residual within guard is retained, never silently orthogonalized.
`max_condition_number=1e8` is existing core guard, not sufficient proof of rigidity.
No changes to private Transform2 guard or new looser tolerance authorized.

#### Independent rotated-pad oracle (additional to previous oracle)

Explicit source center (2,3), width4, height2, pad angle +90 degrees.
R90(u,v)=(-v,u), producing source corners (3,1),(3,5),(1,5),(1,1).
Then source_to_p CCW90 + (10,20), formula (x,y)->(10-y,20+x):
P corners (9,23),(5,23),(5,21),(9,21), center (7,22).
Compare each indexed vertex, not only bbox or center. The earlier angle0 case
has (8,20),(8,24),(6,24),(6,20); this difference detects ignored pad rotation or
applying parent rotation twice. Expected numbers are fixed elementary arithmetic,
never generated via production geometry functions. Test oracle tolerance proposed
1e-6 mm; this is independent from the dimensionless 1e-12 transform guard.

#### PROPOSED numeric policy table, pending confirmation

Name/version proposed: `synthetic-rect-pad-candidate` / `1`. Explicit policy object
contains all values below. Version1 accepts the exact reviewed values rather than
silent defaults/loosening. Integers must be type int, not bool; all counts positive.
These limits bound this operation, not upstream inventory memory or a security sandbox.

| Field | Proposed value | Measurement / enforcement |
| --- | --- | --- |
| max_pads / max_parents | 4096 / 4096 | Reject before per-record processing; empty pads or parents rejected |
| max_inventory_artifacts | 1024 | Bound inventory lookup scan before indexing |
| max_id_utf8_bytes | 256 | Each opaque ID, number, origin label and policy/schema/profile/version string |
| max_text_utf8_bytes | 1024 | Each net, source locator/location text or descriptive string |
| max_evidence_refs_per_record | 16 | Each provenance or convention-evidence tuple |
| max_total_evidence_refs | 32768 | Whole request, including parent and pad references |
| max_total_input_utf8_bytes | 8388608 (8 MiB) | All traversed request and inventory metadata string occurrences, including repeats; reject before copying into outputs |
| max_diagnostics | 128 | All errors/warnings combined; includes reserved terminal budget issue |
| max_diagnostic_utf8_bytes | 4096 | Serialized JSON UTF-8 bytes per ContractError, including expected/actual/context |
| max_total_diagnostic_utf8_bytes | 524288 (512 KiB) | Sum serialized issue bytes; truncation metadata additionally bounded to 256 bytes |
| max_abs_coordinate_mm | 1000000 | Source centers/corners, transform translations and output corners; finite checks before/after arithmetic |
| min_dimension_mm / max_dimension_mm | 0.000001 / 1000000 | Positive width/height inclusive; minimum is proposed numerical subset, not manufacturing resolution |
| max_abs_angle_deg | 360000 | Source pad angle, retain raw angle; any trig argument reduction must be declared, not change recorded value |
| rigid_guard_abs / rel | 1e-12 / 0 | Existing dimensionless Transform2 norm/dot guard; positive parity mandatory |
| test_oracle_abs_mm | 1e-6 | Test assertion only; not a runtime acceptance slack for limits or unsupported geometry |

Check text length with bounded counting before allocating encoded oversized strings;
no giant serialization solely to discover it exceeds budget. Bounds apply to copied
provenance too; do not repeatedly attach the whole inventory to each candidate.
Exact boundary accepted where geometric validity permits; +1 byte/count or numeric
overrun rejects, with no tolerance added to resource/coordinate/dimension bounds.
Nonfinite/overflow rejects. Floating-point degeneracy (collapsed corners/zero area)
rejects even when dimension bounds pass; no polygon repair. Numerical tests must
cover bounds plus large-center/small-dimension combinations.

#### Diagnostic budget exhaustion without a usable batch

Reserve one issue slot AND 4096 serialized bytes from total budget for a compact
blocking INPUT_LIMIT_EXCEEDED issue. Reserve exists even if no truncation eventually
occurs. With the proposed policy, ordinary issues may use at most127 slots and
520192 bytes. A single oversize diagnostic is not emitted partially or silently
trimmed: stop recording it, use reserved budget issue and set truncation.occurred.
Do not promote any candidate. The terminal issue uses a fixed bounded message,
field_path/policy identifier and known counters; do not echo arbitrarily long IDs.
Truncation.reason is an enum (issue_count/issue_bytes/input_budget), omitted_count
is None unless exact. Failure retains no candidates; known full issues remain.

Traverse bounded validated identities in stable pad_id order, with deterministic
field order for malformed records (original index may be used when identity is
unavailable). Apply existing report sorting to retained issues plus the terminal
issue. Never deduplicate meaningful errors. Budget-exhaustion invariance across
malformed permutations is NOT promised when identity is absent; successful inputs
and identified-entity diagnostics remain deterministic. This explicit boundary
must be tested. An invalid policy cannot supply its own trustworthy budget: return
one fixed-size POLICY_INVALID issue within the same implementation hard cap,
without enumerating all malformed policy contents. No recursive reporting failure.

#### Remaining decisions / spec alignment

- O1: confirm declaration-consistent candidate association is acceptable for this
  first product candidate operation; actual source membership verification belongs
  to the future reader. No claim that inventory hash proves membership is permitted.
- O2: confirm pad_number permits empty string as an explicitly retained source value,
  or reject it for this subset. Recommendation: permit empty string, never invent a
  number; required means field present/type str. Canonical IDs remain nonempty.
- O3: approve exact numeric table, diagnostic reservation/fallback, minimum dimension,
  coordinate/angle caps, and rigid-kind restriction. These are proposals, not prior
  normative values. Recommend values above; no production accuracy claim.
- O4: confirm source entity uniqueness per artifact for pads and parents (separate
  typed namespaces) and reject two canonical records aliasing the same typed source
  entity; recommendation reject aliases to avoid duplicated copper. Normative spec
  requires unique canonical IDs but does not define source alias handling here.

No normative conflict identified if this remains an explicit bounded candidate
subset. General bottom/units/geometry import, independent source validation, full
revision lifecycle and atomic publication remain open. Candidate scope reuse must
not imply content equality; content digest and final identity allocation remain
future BoardRevision responsibilities. Implementation awaits contract selection
and explicit authorization; Tasks 1.5/5.2 stay PARTIAL.


### Pad candidate implementation authorization: selected O1-O4 (2026-10-23)

User selected O1 declaration-consistent association (no source-byte membership
verification); O2 empty pad_number preserved, all IDs still nonempty; O3 exact
revision-2 numeric table and rigid-kind restriction, diagnostic reservation/fallback,
reject empty batch; O4 reject aliases of typed source entity within artifact using
SOURCE_CONFLICT when canonical IDs differ, DUPLICATE_ID when canonical IDs repeat.
Pad/parent source namespaces are separate. These selections supersede O1-O4 pending
language above and authorize only the bounded candidate operation, not native reader,
BoardRevision construction/publication or targeting. Policy is synthetic v1, not
production accuracy. Candidate ordering is lexical pad_id; existing report ordering.

### Bounded Pad candidate implementation notes (2026-10-24)

O1-O4 above are selected; earlier pending/proposed wording is historical. API is
`build_rectangular_pad_candidates(PadCandidateRequest) -> PadBatchSuccess | PadBatchFailure`
in `src/aoi_platform/pad_candidates.py`. The exact explicit SyntheticPadPolicy v1
implements the selected table; no production defaults. Candidate source and parent
are retained frozen records, with four ordered Point2 vertices. Failure has no
candidate collection. No reader, revision construction, publication or targeting.

Preflight bounds the complete metadata tree before sorting/indexing/serialization,
counts string occurrences and evidence references, and excludes mutable/custom types.
Enums are fixed implementation vocabulary; variable strings are UTF-8 budgeted.
The structural work guard is 64*(max_pads+max_parents+max_inventory_artifacts+
max_total_evidence_refs) visited nodes and depth32; valid declared record nesting
fits below these bounds. This additionally bounds malformed nested tuple structures.
Binary integers exceeding1024 bits reject before serialization (not finite binary64
geometry). Snapshot/revision descriptions use the1024-byte text bound. Other IDs,
numbers, origins and policy/schema strings use256. These implementation safeguards
bound malformed work without increasing any selected geometry/resource allowance.
Duplicate-identity sort ties use bounded canonical record JSON after preflight;
normal candidates sort by exact pad_id. Diagnostic reservation still applies.
The total diagnostic byte cap is redundant at the selected127 ordinary slots times
4096 bytes, but independently checked; tests fill that exact520192-byte ordinary
budget and exercise the reserved blocker. Whitespace-only opaque IDs are preserved;
if the existing report's nonblank text guard prevents an entity field, its exact
value is retained under entity_id_json/artifact_id_json without relaxing report guards.

Corner construction uses explicit pad-angle rotation, source-center translation,
then the validated proper-rigid source_to_p mapping. Consecutive vector cross products
avoid cancellation from absolute-coordinate shoelace sums. No fitted/orthogonalized
replacement is made. Tests include independently derived45-degree corners in addition
to angle0/+90, and a1nm dimension rectangle near1e6mm. Numerical guard is not the
1e-6mm test oracle tolerance. Association remains declaration-consistent only.

New candidate evidence has a narrow -text Git attribute so future checkpoint staging
preserves its raw capture/hash bytes. Existing evidence attributes and bytes are unchanged.

## Source-checked records to candidate request - draft contract v1 (2026-11-06)

Review draft only; no implementation authorization or normative spec change.
Supports parts of Tasks 3.4/5.5/5.13; Tasks 1.5/5.2 and all incomplete aggregate
obligations remain PARTIAL. This is a candidate operation, not ValidateImport,
BoardRevision construction, publication or targeting authority.

### Scope and trust boundary

Profile: `c1-c2-source-checked-request-v1`. It remains fixture-specific:
REAL-PCB-01-r2 PCB, 912379 bytes, SHA-256
`67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0`.
Exactly the two parent/four pad UUID pairs and all eight artifact size/hash pins
in [the accepted replay profile](../../../../evaluation/kicad-reader/c1_c2_replay_batch.py)
remain required. These are fixed profile constants, not caller-overridable pins.
Observation is strict-v2 (196944 bytes, SHA-256
`cd3734ece758d2611b44dc89cec2c88e439ba2d5585024d484671645ed7725b9`);
C1/C2 boundary, report and transport pins remain separate. A future implementation
must freeze these constants in its reviewed profile, not trust mutable configuration.
Removing a pin is a new scope decision, not general importer support.

Operation: `prepare_source_checked_pad_request(admitted_bytes, inventory,
 declarations, caller_context, profile, limits) -> PreparedRequest | PreparationFailure`.
Names are fixed by this contract, not implemented APIs. Inputs/outputs and nested records are immutable.
`admitted_bytes` is an explicit bounded tuple of artifact-ID/bytes records; no path
resolution, source factory, native execution or implicit source acquisition occurs.
Validate inventory success and nested consistency, then independently hash/size-check
the exact bytes consumed against computed inventory observations AND fixed pins.
A caller-created InventorySuccess, record, status string, span or prior receipt is
not proof that bytes were read or that source verification occurred. Recompute checks
in this operation; reject a forged/conflicting declaration rather than repair it.

The adapter itself scans PCB bytes to EOF with existing ancestry/budget rules,
reconstructs source fields, validates pinned observation schema, reconstructs boundary
records from pinned bytes, and compares supplied declarations. It uses the existing
source-pose, coverage, layer and artifact comparison logic without relaxing guards.
Build strings/schema/hash equality do not authenticate a KiCad backend. Source-check
receipts are audit results of this operation, not signed attestations or transferable
capabilities; downstream callers cannot bypass rechecking by constructing one.

### Mapping and ownership of facts

| Field / immutable type | Adapter checks or derives from admitted bytes | Caller declaration retained separately |
|---|---|---|
| Canonical `board_id`, `candidate_scope_id`, parent/pad IDs: nonempty strings | Exact-string uniqueness, source aliases and association consistency; no identity generation/trim | All canonical IDs and unpublished scope; scope is not a content digest or accepted revision |
| Source parent/pad UUID and number: strings | Direct footprint/pad ancestry, direct UUID field, shared footprint/pad uniqueness; exact number retained, including repeated/empty numbers | Requested canonical-to-source association must match reconstructed pairs |
| Type/shape/side/layers | Source `smd rect`, footprint direct `F.Cu`/`attr smd`; exact explicit pad layers versus observation; candidate copper layer `('F.Cu',)` and top side | No caller shape/side flag overrides source; F.Mask/F.Paste are retained as source layers, not candidate copper |
| Pose/size: literals, Decimal values, spans | Direct footprint/at, pad/at, pad/size; cardinal rotation of local center once; pad angle is world rectangle orientation; compare observation center/angle/size and declarations | Caller does not supply authoritative geometry; supplied geometry is checked before constructing request |
| Rectangle / four indexed P vertices | Derive from source Decimal cardinal math, normalize Y once; correspondence `(3,2,1,0)`; source/observation coordinate tolerance 1 nm, exact angle rules unchanged | P datum must explicitly be normalized native-board, translation `(0,0)` for this profile; no bbox alignment |
| Frames and Transform2 | Full frame/context equality and existing validated-conventions/proper-rigid guards; normalized source is mm/right/up; reflection recorded separately, never slipped into rigid transform | Frame IDs, candidate scope, explicit source-to-P map and any machine/capture context; source does not prove these external contexts. Reject conflicting/unsupported declarations, never guess missing values |
| Provenance: artifact/source IDs, computed SHA-256, size, byte spans `[start,end)`, 1-based lines | Match inventory IDs/hash/size; derive spans/lines from exact source; bind observation/boundary/report/transport hashes and locators | Snapshot/revision labels and canonical locators are supplied metadata, not proof of common design revision |
| Coverage: immutable per-path records | Retain source path/value/span and checked/presence-only/unsupported result; enforce current exact pad/footprint paths, modifier rejection and graphics layer policy | Caller cannot upgrade unknown or semantics-unchecked to verified; supplied coverage claims remain distinct |

Only the four source memberships and the explicitly checked declarations are
established. Metadata/net/pintype/zone_connect, graphics/text semantics and model 3D
remain unchecked beyond existing structural/layer rules. Construct completeness,
effective copper and zone-fill effects remain unverified. All eight boundary
coverage categories and their existing assurance semantics remain unchanged.

### Ordering, bounded failure and candidate execution

1. Joint bounded validation of input types, successful inventory, immutable bytes,
   pins, exact artifact/entity set and caller context before dereferencing records.
2. Source scan/coverage/field checks; independently rebuild pose and artifact records.
   Compare every supplied record with reconstructed values; no fallback to caller data.
3. Only after all four pass, produce a complete PadCandidateRequest and separate
   SourceCheckEvidence. The orchestrator may pass that request to existing
   `bind_pad_boundaries` once (which calls the candidate API once). Preparation
   itself never calls the candidate API; do not call it again for pre-validation.
4. Any failed phase returns PreparationFailure with bounded ValidationReport and
   truncation data, no prepared request or candidates. Existing candidate/binding
   failure remains all-or-nothing; no partial success is published or retained as usable.

Use existing candidate/boundary limits and diagnostic reservation, scanner depth128,
raw token64KiB and total500000 tokens; exact fixed profile input sizes bound bytes.
Reject invalid limits before traversal; budget hashing, metadata collection and
comparisons, not only output. Keep deterministic source/pad/field diagnostic order.
Malformed input uses SCHEMA_INVALID, declaration/source disagreement SOURCE_CONFLICT,
unsupported path/type/map GEOMETRY_UNSUPPORTED, budget exhaustion INPUT_LIMIT_EXCEEDED;
retain existing typed inventory errors for byte admission. Diagnostics preserve
artifact/hash, parent/pad UUID, full field path, source span and expected/actual.
Opaque caller IDs use existing JSON-in-context handling; never trim identity.

PreparedRequest contains the request plus separate SourceCheckEvidence: profile and
verifier identity/version, artifact computed hashes/sizes, selected source pairs,
per-field checks/spans, normalization evidence and explicit unchecked categories.
Fixed receipt status: `selected-source-declarations-checked` (not `source-verified`).
The result does not upgrade candidate `association_status='declaration-consistent'`
or binding `source_membership_status='not-verified'`/coverage assurances. Evidence
about selected source checks lives alongside them; import-ready/published/targeting
remain false. These distinctions also apply when a serialized receipt is replayed.

### Acceptance examples and review boundary

Positive: real inventory of the same eight pinned C1+C2 artifacts; reconstruct all
four pairs and declarations, then bind once. Require four candidates and all16 P
corners against independent C1/C2 oracles, preserved spans/hashes, exactly one candidate
batch call, unchanged inputs, and unchanged candidate/binding assurances.

Negative: keep all admitted PCB/observation/boundary bytes unchanged; add0.001mm to
one supplied C2 center.x. Require SOURCE_CONFLICT with source-derived expected and
caller actual, parent/pad UUID, PCB hash and pose span; no prepared request, no
binding/candidate call and no candidates. This tests a declaration conflict after
real hash admission, not modified source bytes admitted via a test double.

The profile/API/receipt names and immutable types below are fixed for contract v1;
the contract remains for review, with no implementation authorization. Existing
numeric policies and accepted gates are reused, not new accuracy claims. No broader
source support, verifier authority, publication or task completion is established.


### Immutable profile v1: exact bytes and source entity set

Artifact IDs are also the source IDs in this profile. Each ID occurs exactly once;
no extra artifact is admitted. Only `pcb` has role `kicad_pcb`; the other seven
have role `supporting`, reference_only=true. Pins are literal immutable tuples.

| Artifact ID | Exact bytes | SHA-256 |
|---|---:|---|
| pcb | 912379 | 67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0 |
| observation | 196944 | cd3734ece758d2611b44dc89cec2c88e439ba2d5585024d484671645ed7725b9 |
| C1_boundary | 1689 | 9cd1d26d7756d81fc91d81712be01cba295a742ece11f9847c83866b897748b2 |
| C1_report | 813 | ae359be006e70c9b6d97b87d80b250d365b27b8196b3d230d1d21954f90852cc |
| C1_transport | 1354 | 003d26bee58ac17377275ca8e5c74d5dc4c9a57038b35f0e0a282f047537da07 |
| C2_boundary | 1689 | a8134211861f9f2709330e6d8e4c8185662e3d58f153895dbf5811270329b176 |
| C2_report | 813 | 098fc91d66b941f1c02fbeb4177816026837c40ed014a69bd9872ecbaa57d7ae |
| C2_transport | 1355 | 3a1381fa096b973de18f9fc9c96130775da0da8771d03803a516ee4f0c5b8d2e |

| Group | Direct footprint UUID | Direct pad UUID |
|---|---|---|
| C1 | 00000000-0000-0000-0000-00005bd482c8 | e2743daf-d278-4538-a77e-8f62f1b7978c |
| C1 | 00000000-0000-0000-0000-00005bd482c8 | 4e53dd71-4be4-4973-9c48-191e7b2e27bb |
| C2 | 00000000-0000-0000-0000-00005bd482e1 | 21e4d927-86ab-439d-8b84-9241bc089b89 |
| C2 | 00000000-0000-0000-0000-00005bd482e1 | fc38c22a-efcb-4dfc-b42c-80a66f75e1a4 |

### Fixed immutable API records

All new records are frozen, slotted dataclasses; nested collections are exact tuples,
bytes and existing immutable model records. No dict/list, mutable bytearray/view,
iterator or callback input is accepted. All listed fields are required. Optionality
inside reused model types remains as defined there; malformed nested records fail
before dereference. Type annotations do not themselves confer validation authority.

| Type | Fields/types and cardinality |
|---|---|
| AdmittedArtifactBytes | artifact_id: str; data: bytes |
| AdmittedBytes | tuple[AdmittedArtifactBytes, ...], exactly eight unique profile IDs; size checked before hash/parse |
| SourceDeclarations | parents: tuple[PadParent, ...] exactly two; pads: tuple[SourcePad, ...] exactly four; boundaries: tuple[BoundaryEvidence, ...] exactly four. These are untrusted supplied records, with no source-check status field |
| CallerContext | schema_version: str; board_id: str; candidate_scope_id: str; target_frame: Frame; candidate_policy: SyntheticPadPolicy; boundary_policy: BoundaryBindingPolicy. Parent source frames/transforms are supplied in SourceDeclarations; full context must agree |
| SourceCheckProfile | profile_id: literal c1-c2-source-checked-request-v1; version: literal 1; pins: tuple[ArtifactPin, ...]; pairs: tuple[SourcePair, ...], exact tables above, no override |
| ArtifactPin | artifact_id: str; size_bytes: int; sha256: str |
| SourcePair | parent_uuid: str; pad_uuid: str |
| PreparationLimits | candidate_policy: SyntheticPadPolicy; boundary_policy: BoundaryBindingPolicy; max_artifacts=8; max_total_bytes=1117036; scanner_max_depth=128; scanner_max_token_bytes=65536; scanner_max_tokens=500000. Exact values required; policies must equal CallerContext policies |
| SourceSpan | start_byte: int; end_byte: int (exclusive); first_line: int; last_line: int (1-based, inclusive), checked against source bytes |
| FieldCheck | artifact_id: str; source_pair: SourcePair; path: tuple[str, ...]; literals: tuple[str, ...]; spans: tuple[SourceSpan, ...]; result: literal checked or semantics-unchecked; expected_json: str; actual_json: str. JSON values are bounded diagnostic-style representations, not geometry authority |
| SourceCheckEvidence | profile: SourceCheckProfile; verifier_id: literal c1-c2-source-declaration-checker; verifier_version: literal 1; artifacts: tuple[ArtifactPin, ...] with recomputed values; pairs: tuple[SourcePair, ...]; checks: tuple[FieldCheck, ...]; normalization: tuple[EvidenceReference, ...]; unchecked_categories: tuple[str, ...]; status fixed selected-source-declarations-checked |
| PreparedRequest | request: PadCandidateRequest; boundary_declarations: tuple[BoundaryEvidence, ...] exactly four, reconstructed/compared; source_check: SourceCheckEvidence; report: ValidationReport (successful preparation). No candidates field |
| PreparationFailure | report: ValidationReport (blocking); truncation: PadTruncation. No request, boundary declarations, success receipt or candidates |

The preparation signature uses these exact types, plus inventory: InventorySuccess;
invalid runtime types (including failed/forged inventory internals) yield failure.
Prepared request embeds the validated inventory without duplicating it per pad.
Canonical pad order is lexical pad_id; boundary_declarations have the same associated
pad order. Receipts sort artifact IDs, source UUID pairs and field path/span, while
report diagnostics retain the accepted ordering contract.

The orchestrator passes `prepared.request`, `prepared.boundary_declarations` and
`caller_context.boundary_policy` to `bind_pad_boundaries` exactly once. Preparation
must not call `evaluate_source_boundaries`, `evaluate_artifact_boundaries`, replay
entrypoints or another flow which executes binding/candidates. Reuse their checks
by minimally extracting bounded, side-effect-free checking/reconstruction helpers;
keep existing flow behavior/tests intact. No broad refactor or hidden candidate
pre-validation. Source checks return facts/errors, not a binding success.

### Exact resource accounting

Total raw input is exactly 1117036 bytes across eight artifacts (per-artifact exact
lengths above); reject length/count excess before hashing or parsing. Acquisition is
outside this operation. Hash the supplied immutable bytes, not a reopened path.

Use the accepted `synthetic-rect-pad-candidate`/1 and
`synthetic-rect-boundary-binding`/1 exact policies in
[boundary contract: Exact synthetic policy and bounded work](boundary-evidence-binding-contract.md#exact-synthetic-policy-and-bounded-work-supplemental-values-for-review),
including its diagnostic fallback/reservation. Explicit limits: metadata traversal
root depth0/max32, 2686976 node occurrences, 8388608 UTF-8 input-text bytes, 256-byte
IDs/enums, 1024-byte descriptive values, 16 refs per collection and 32768 total refs.
Scanner has its separate 128-depth/65536-byte-token/500000-token limits. Numeric
source literals retain the accepted 64-character/plain Decimal/cardinal restrictions.
Exactly two parents/four pads/four boundaries further restrict the general policies.
Boundary correspondence remains max8 mappings/64 component comparisons per pad;
geometry matching occurs only in subsequent binding, not preparation.

Use one preparation work ledger across declarations, context, inventory metadata,
reconstructed records and receipt collection: do not reset per artifact/pad or
materialize an unbounded receipt before checking limits. Count occurrences and stop
before expanding nested collections; no whole-record JSON serialization for admission.
FieldCheck JSON text is bounded before serialization using the same text budgets.
Source bytes/token text scanning is charged to scanner limits; retained metadata is
also charged to the shared metadata ledger. Raw input bytes are not UTF-8 metadata.

One diagnostic budget: 128 issues, 4096 UTF-8 bytes each, 524288 total; reserve one
slot/4096 bytes for blocking INPUT_LIMIT_EXCEEDED (ordinary max127/520192 bytes).
On exhaustion return truncation with omitted_count=None unless actually known. Invalid
policy uses the accepted fixed fallback, never caller-supplied invalid limits. Reuse
policy numeric guards without tolerance relaxation. A successful preparation has no
blocking diagnostics; subsequent binding keeps its existing budget/assurances and
must not merge failures into a usable preparation or partial candidate batch.
