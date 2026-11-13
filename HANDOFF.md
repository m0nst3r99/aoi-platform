# Current State / Next Action

Snapshot: 2026-11-13, authorized integration on master; merge parents are
`350c1e3c7de7037f8c187b4b1011cb383433c5de` (master) and
`3262563f4638d6da63799b69de0dad6f50b4acfe` (checkpoint).
Verified merge snapshot: `5d5658bc1ac29a4100b0ada8dc0c33db70c52256`, with exactly
those two parents. This follow-up documentation commit records verification;
obtain the current HEAD from Git rather than treating the snapshot as latest HEAD.

| Item | Current state |
|---|---|
| Git workflow | Master is the primary development branch. Checkpoint remains preserved history/evidence. This explicitly authorized full merge supersedes the former proposal to port only pad candidates. Future branch changes, merges, commits and pushes require explicit authorization |
| Implementation | Geometry core and bounded inventory; evaluation KiCad protocol v2/outline/replay controls; canonical rectangular pad candidates; boundary evidence/correspondence/binding; pinned C1+C2 source preflight, byte hashing, declarations and boundary records |
| Actual phase | Sprint 2 bounded evaluation/integration, not a completed product KiCad importer. SourceCheckEvidence and PreparedRequest record types exist, but complete receipt/request construction API remains NOT IMPLEMENTED |
| Acceptance | Historical selected-subset acceptance only. Candidate 100 focused PASS and reviewer-reported 470 PASS/1 skip; boundary 233 PASS is saved implementer output, reviewer static review did not rerun it. Integration does not create new geometry/parser acceptance |
| Open obligations | 1.5/5.2, 3.4/5.5/5.13 and other aggregate obligations stay PARTIAL/open; no checkbox or normative requirement changes. No Foundation, publication or targeting readiness |
| Risks | Pinned C1+C2 coverage is not general parsing; effective copper, graphics/model and zone-fill semantics remain unverified. Runner pre-assignment host-death gap and recorded historical provenance limitations remain |
| Preservation | Checkpoint technical history below is retained byte-for-byte as the baseline; master governance is retained in AGENTS. Local-only inventory: 1,755 untracked and 5,343 ignored files, including 66 ignored ZIPs. All 7,098 matched SHA-256/size after merge |
| Audit location | Local temporary directory `C:/Users/nhanp/AppData/Local/Temp/vscode-agent-codex-sandbox-oaYh4G/aoi-merge-preflight-c8665007b9a54b2180a4fc2fd8dc1524`; contains local-only manifest, parent tracked-tree inventories and preservation checks. Not uploaded or committed |
| Post-merge result | 7,098/7,098 local-only files still match size/SHA-256; zero accidentally tracked. All checkpoint blobs except the two intentionally reconciled documents match the merge tree; AGENTS is the preserved master-only file with seven governance lines added. No master file lost. No push; final tracked changes consist only of this documentation follow-up |
| Current checks | Git preflight and path-collision checks PASS; checkpoint non-document blob preservation PASS; no lost master files/unmerged entries/conflict markers; strict OpenSpec validation PASS. Default staged whitespace check exits 2 on preserved historical content (17,815 non-document findings, identical to checkpoint baseline); no new non-document findings. New documentation-prefix and AGENTS checks PASS. No pytest/native/expensive runner rerun |
| Next single action (proposal) | Define and review the bounded receipt/PreparedRequest construction slice atop the existing source-checked boundary result, under 1.5/5.2 and 3.4/5.5/5.13; no implementation is authorized by this merge task |
| Acceptance / stop conditions | Require complete field/span/normalization provenance, one operation ledger, immutable request/receipt, explicit unchecked categories and atomic failure; preparation must never call binding/candidates. Stop if intermediate results cannot supply required provenance within existing budgets or require widening pinned scope; do not fabricate receipt evidence |

## Session startup

Read [AGENTS.md](AGENTS.md), verify actual Git root/branch/HEAD/status and diff
summaries, then read this section. Consult only relevant
[implementation status](openspec/changes/board-geometry-foundation/implementation-status.md),
[OpenSpec tasks](openspec/changes/board-geometry-foundation/tasks.md), design and
source/tests. Work only within the current explicit authorization. A next action
is a proposal. Preserve local-only and historical artifacts; no automatic cleanup.

## Historical technical record - checkpoint baseline

The complete checkpoint document follows unchanged. Earlier Current/Next, pending
review, branch and authorization statements describe their historical scope and
are superseded by this entry where they conflict. Master bootstrap snapshots are
recoverable from commits 59429eb and 350c1e3; their stable governance is retained
above and in AGENTS rather than duplicating their long snapshots here.

# Handoff — 2026-10-19 (Asia/Bangkok)

## Supervised KiCad-through-runner attempt - 2026-10-20

User reports runner v1 reviewer checked 640/640 hashes and reran 57 portable tests;
read 41 native case evidence but did not rerun native. Runner is NOT accepted as
complete containment. Pre-assignment host-death gap remains unchanged.

New evaluation-only [integration](evaluation/windows_runner/kicad_local.py) and
[staged helper](evaluation/windows_runner/kicad_staged_helper.py) reuse the runner,
probe and schema without modifying them. Explicit source is REAL-PCB-01-r2 at the
previously recorded local snapshot; no original fixture path is passed to loader.
Staged size 912379 bytes, SHA-256
`67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0`.

[New evidence](evaluation/windows_runner/evidence/kicad-local-01/report.json):
- Hash mismatch PASS: STAGED_INPUT_MISMATCH, root_pid null, not resumed.
- Control transport FAIL: TIMEOUT at 30061 ms (30 s execution / 5 s cleanup,
  independent 45 s watchdog). stderr only loading digest; no loaded marker/JSON.
- Protocol/comparison BLOCKED, not PASS. Diagnostic prefixes were never parsed.
  No KiCad build observation completed; executable/helper hashes are recorded but
  are not full dependency pinning. Cause of LoadBoard stall is undetermined.
- Runner cleanup confirmed, Job active count zero. Helper temporary file remained
  when killed; owner TemporaryDirectory cleanup removed entire staging directory,
  confirmed separately in post-run-cleanup.json. Caller handle usable and staged
  bytes unchanged before owner cleanup. All 25 r2 snapshot file hashes unchanged.
- Related tests: 80 passed (57 portable runner + 23 existing harness), no full suite.

Reproduce with a NEW output directory:
`.venv/Scripts/python.exe evaluation/windows_runner/kicad_local.py evaluation/windows_runner/evidence/NEW_ID`
Policy is fixed in integration before execution: input 16 MiB, stdout 2 MiB,
stderr 256 KiB, combined 2.25 MiB, chunk 64 KiB, process commit 1 GiB,
Job commit 1.5 GiB, 4 processes. No limits were relaxed and no retry attempted.
Next step: review the captured LoadBoard timeout and authorize narrow diagnosis;
do not claim successful KiCad-through-runner observations or parser compatibility.
Tasks 1.5/5.2 PARTIAL; no runner/shared/product/fixture/spec/checkbox/allowlist edits.
This new attempt is unreviewed. Prior accepted metadata remains unchanged.


## Current bounded Windows runner evidence - 2026-10-19

Final checks: strict OpenSpec validation PASS; git diff --check PASS (only pre-existing LF/CRLF notices). New untracked runner code/docs whitespace check PASS. Raw commands/results are in runner evidence review-03/final-validation.json.

HEAD: `4e59ad93cc9f753e5c84ca8df7a49868dfde2470`. No commit/push/reset.
Existing uncommitted documentation/evaluation work is preserved. New evaluation-only
runner is in [evaluation/windows_runner](evaluation/windows_runner/README.md).
The authorized ownership/transport/success contract was revised in design before
implementation. No product code, fixture, normative spec, checkbox or allowlist
changed by this runner slice; prior task/supported-inputs edits remain untouched.

Latest actual run: **491 passed, 1 skipped in 17.99s**, evidence
[evaluation/windows_runner/evidence/review-03](evaluation/windows_runner/evidence/review-03/environment-command.json).
This includes 57 portable runner tests and 41 Windows cases, 23 existing harness
regressions and 370 product tests. Skip is the existing local-fixture opt-in.
Actual OS: Windows 10.0 build 26300 AMD64; CPython 3.11.9 MSC v.1938 AMD64.
Each native case has an independent watchdog. Fault-injected cases are distinguished
from real enforcement in the runner README. No KiCad/accepted fixture was run.
Earlier runner evidence is retained; review-03 supersedes review-01/02.

**New runner code/results await review; not accepted by the prior reviews.**
Errata/r2 metadata and harness acceptance below remain valid in their stated scope.
Tasks 1.5/5.2 stay PARTIAL. Synthetic memory/count/output/tree tests do not establish
parser compatibility or observation geometry. Slice remains incomplete for universal
runner-parent crash protection: native crash test covers an assigned Job, while
CreateProcess-suspended to Assign has an unprotected host-death window. Also not
native-proven: naturally incompatible enclosing Jobs and other OS/runtime versions.
Single-reader polling has no outstanding async I/O/thread to cancel; no claim of a
CancelIo failure test. Permanent cleanup errors return unconfirmed, not success.

Next: review transport code/evidence and resolve the non-atomic pre-assignment
host-death gap before treating the entire runner contract as complete. Do not start
KiCad adapter/bridge/protocol semantics from this evidence. Reproduction commands
are in the runner README; fresh collector IDs preserve earlier runs. Review ZIP
contains runner code/tests, raw results, contract, this handoff and SHA-256 manifest,
without the large accepted fixtures.

## Historical acceptance and adapter contract draft — 2026-10-19

User reports **errata and REAL-PCB-01-r2 accepted for population metadata
correction via direct ZIP review**. Reviewer reran 23/23 regressions, checked
133/133 package hashes and 25/25 checksums in each snapshot, compared all twelve
DNP UUIDs directly with PCB source, confirmed only twelve dnp=false->true edits
and 23 other files byte-identical. Saved-subprocess replay: r1 FAIL 26/27; r2 PASS
27/27. Reviewer **did not rerun KiCad native**. No signature/attestation or parser
compatibility acceptance is implied. This supersedes pending-review statements
below for errata/r2 metadata only.

r1 remains unchanged. [Errata](evaluation/kicad-reader/population-errata-r2/ERRATA.md)
links r1 source/population/audit hashes to derived r2 at
`C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r2`.
Frozen manifests/ZIPs retain their preparation-time pending status; acceptance is
recorded here, without rewriting snapshots or historical evidence.

[Design contract draft](openspec/changes/board-geometry-foundation/design.md#review-draft-native-observation-boundary-2026-10-19-tasks-1552-partial)
is **awaiting review**, not implemented. It proposes immutable observation input/
output, inventory/hash/backend binding, typed failure without usable observations,
Windows resource-control requirements, a construct coverage matrix and distinct
mock/native/review acceptance evidence. All observations stay evaluation-only;
native loader omissions are not reliably detectable today.

Exactly one next slice proposed: bounded Windows process runner with synthetic
helper integration tests, separate from KiCad observation semantics. Decisions
on Win32 binding, limits/threat model and framing remain for review. No product
adapter/parser, fixture edits, checkbox/allowlist changes, commit or push. Tasks
1.5/5.2 remain PARTIAL. This turn only updates documentation; no pytest or native
probe rerun. `openspec validate board-geometry-foundation --strict` passed;
`git diff --check` passed (LF/CRLF notices only). Existing uncommitted task
evidence edits were preserved; this turn did not change tasks or checkboxes.

## Historical population errata / r2 preparation — 2026-10-19

Harness v2 fixes **accepted by direct ZIP review**, as reported by the user:
reviewer reran 23/23 regressions, verified 44/44 manifest hashes and 14 unchanged
old logs. Reviewer did not have the full source PCB or rerun KiCad. This is
user-relayed review acceptance, not an agent-created signature/attestation.

[Errata](evaluation/kicad-reader/population-errata-r2/ERRATA.md) and derived
REAL-PCB-01-r2 are **pending review**. New snapshot:
`C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r2`.
Parent r1 is unchanged. Exactly 12 population dnp fields changed false to true;
all UUID/classification/eligibility/exclusion/fiducial fields remain unchanged.
This corrects fixture descriptions, not PCB data or an assembly decision.
Manifest and checksum inventory were regenerated with parent hashes, exact edits
and pending-review status; no r1 acceptance was inherited.

New native runs: [r1](evaluation/kicad-reader/runs/errata-r1-01/results.json)
FAIL 26/27, population_fields and 12 expected conflicts;
[r2](evaluation/kicad-reader/runs/errata-r2-01/results.json) PASS 27/27, zero
conflicts. Unmodified reviewed harness; no check waived. Regression rerun:
23 passed. Parent hashes and unchanged derived artifact bytes verified.
Metadata consistency is not parser compatibility. Product adapter, unsupported
construct coverage and resource containment remain open; 1.5/5.2 PARTIAL,
no checkbox/allowlist changes. No product publication, commit or push.

Next: review errata/r2 and bundled source directly. Do not rerun derivation into
the existing directory; [derive_r2.py](evaluation/kicad-reader/derive_r2.py) refuses
existing targets. Older awaiting-review statements for harness fixes below are
historical; they do not apply to the accepted v2 fixes. Errata/r2 acceptance
remains separate and has not been granted.

## Historical harness review fixes — 2026-10-19

Evaluation-only authorization; no product adapter, fixture/population edits,
checkbox/allowlist changes, commit or push. HEAD remains
`4e59ad93cc9f753e5c84ca8df7a49868dfde2470`; pre-existing documentation changes remain.

Three review failure groups reproduced before edits: positive probe failure can
pass; negative outcomes are not validated; bbox/dictionary checks mask invalid
outline/duplicate UUIDs. Bad JSON also prevented report persistence.
[Before-regression evidence](evaluation/kicad-reader/regression-before.txt):
11 failed, 1 passed. [Expanded regressions](evaluation/kicad-reader/test_harness.py)
now report **23 passed**. New harness declares 27 required checks, defaults each
to fail/not-completed, persists diagnostics, validates the observation schema and
requires exact negative rejection code plus exit 2. Valid/count/holes/bbox are
separate; UUID uniqueness/set and R7/R8 presence precede dependent comparisons.

[New run](evaluation/kicad-reader/runs/review-fix-01/results.json): **26/27 pass**,
exit 1/outcome failed for the existing 12 DNP conflicts. Both negative probes
reject correctly. All fixture hashes unchanged. [Source audit](evaluation/kicad-reader/runs/review-fix-01/dnp-source-audit.json)
confirms multiline source dnp for **all 12 UUIDs**, with raw attributes, line
numbers and source/population/report hashes. No correction to accepted r1.

Old root evidence and review ZIP remain unchanged; old scripts copied to
`run-before-review.py` / `probe-before-review.py`. New runs require a fresh
`--output` directory; reuse fails without overwriting. Old reproduction commands
below without this flag are historical. See [review notes](evaluation/kicad-reader/REVIEW-FIX.md).
These fixes/results are **awaiting review**, not an attestation or new compatibility
acceptance. Next step is review of the new ZIP and disposition of DNP conflict;
product adapter and containment/unsupported-construct work remain unimplemented.

```powershell
.\.venv\Scripts\python.exe -m pytest evaluation/kicad-reader/test_harness.py -q
.\.venv\Scripts\python.exe evaluation/kicad-reader/run.py 'C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1' --output evaluation/kicad-reader/runs/choose-a-new-run-id
```

## Historical initial reader evaluation — superseded by harness fixes above

HEAD: `4e59ad93cc9f753e5c84ca8df7a49868dfde2470`. Tracked tree was clean at
evaluation start. The old uncommitted inventory/document list below is historical:
those changes are now in HEAD. Existing agent directories and seven review ZIPs
remain untouched/untracked. This turn adds [evaluation/kicad-reader/](evaluation/kicad-reader/)
and updates this handoff plus OpenSpec task/status evidence; no shared code/test edits.

The user authorized reader evaluation under 1.5/5.2, superseding the inventory-only
authorization and “not evaluated yet” statements below. No product parser is implemented.
[Report](evaluation/kicad-reader/README.md) and [results](evaluation/kicad-reader/results.json)
are new agent findings **not yet reviewed**, separate from accepted gate 7.1,
inventory review and Sprint 1 subset review. No signatures/attestations created.

- CLI and bundled pcbnew report 10.0.7. Native loading succeeds outside sandbox;
  sandbox attempt times out after 30s, cause not isolated.
- Outline centerline 135 x 90 mm, 12 lines/3 arcs, 57 footprints; 28 assembly refs
  and 3 fiducial candidates by ledger UUID. All positions/angles/sides agree;
  R7/R8 270R and independent R7 pad world oracle agree.
- **New conflict:** 12 G*** entries have native DNP=true versus population.json
  false. A source multiline attr block confirms dnp for a representative UUID.
  Full UUID/expected/actual pairs are retained. Do not silently normalize or edit r1.
- Harness exit 1: nine of ten aggregate checks pass; population equality fails.
  Malformed native load returns None; missing file fails before load at hashing.
  All snapshot file hashes agree before/after. This is not renewed acquisition review.
- Next: review finding and conflict handling, prove unsupported-construct detection
  and resource isolation, then authorize the proposed bounded observation adapter.
  Temporary recommendation: pinned pcbnew subprocess; IPC 10 requires GUI, SWIG
  removal planned for 11. No compatibility claim or task closure.

Reproduce (local KiCad required; not part of portable tests):

```powershell
.\.venv\Scripts\python.exe evaluation/kicad-reader/run.py 'C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1'
openspec validate board-geometry-foundation --strict
git -c safe.directory=C:/dev/aoi-platform diff --check
```

Full pytest not rerun: no shared code changes. Validation results are recorded in
the evaluation report. All following current-state/next-step statements are
**historical as of the preceding handoff**, superseded by this section where different.

## Điểm tiếp tục

- Repository: `C:\dev\aoi-platform`.
- HEAD đã kiểm tra khi lập handoff: `c459fc969eddc6cf55a0fb1d83346df26ecb7b60`.
- Công việc hiện tại: inventory byte-admission slice **đã qua code review trực tiếp từ ZIP**, theo kết quả người dùng chuyển tiếp ngày 2026-10-19. Reviewer báo 370 passed, 1 skipped và thêm 1.200 ca độc lập pass; reviewer **chưa chạy lại bundle REAL-PCB-01-r1**. Bước tiếp theo là đề xuất/evaluate reader KiCad, chưa triển khai parser. Trạng thái chờ review trong bản handoff trước là lịch sử, đã được thay thế.
- Yêu cầu mới nhất chỉ là ghi handoff; không triển khai thêm. Không reset, commit/push, archive change, sửa cấu hình agent hoặc fixture accepted. Giữ mọi thay đổi hiện có.

## Working tree chưa commit

Các file tracked đang modified:

- [README.md](README.md): hướng dẫn inventory.
- [design.md](openspec/changes/board-geometry-foundation/design.md): cập nhật gate trước đó và schema/API/stream policy inventory.
- [implementation-status.md](openspec/changes/board-geometry-foundation/implementation-status.md): gate acceptance và evidence inventory.
- [proposal.md](openspec/changes/board-geometry-foundation/proposal.md): đồng bộ acquisition gate trước đó.
- [sprint-plan.md](openspec/changes/board-geometry-foundation/sprint-plan.md): gate, đề xuất ban đầu và cập nhật authorization inventory.
- [supported-inputs.md](openspec/changes/board-geometry-foundation/supported-inputs.md): fixture accepted, hashes, conventions và giới hạn review.
- [tasks.md](openspec/changes/board-geometry-foundation/tasks.md): riêng 7.1 đã checked; evidence 3.4/5.1 PARTIAL, vẫn unchecked.
- [errors.py](src/aoi_platform/geometry/errors.py): thêm mã lỗi import/I/O; không thay hành vi geometry.

File mới untracked thuộc công việc:

- [inventory.py](src/aoi_platform/inventory.py).
- [test_inventory.py](tests/test_inventory.py).
- [test_inventory_local.py](tests/test_inventory_local.py).
- [HANDOFF.md](HANDOFF.md), được tạo trong lượt này.

Untracked đã có trước lượt handoff, không sửa/xóa/đưa vào commit tự động: [.agents/](.agents/), [.claude/](.claude/), [aoi-sprint1-diagnostics-review.zip](aoi-sprint1-diagnostics-review.zip), [aoi-sprint1-envelope-review.zip](aoi-sprint1-envelope-review.zip), [aoi-sprint1-resolver-review-v2.zip](aoi-sprint1-resolver-review-v2.zip), [aoi-sprint1-resolver-review.zip](aoi-sprint1-resolver-review.zip), [aoi-sprint1-review-v2.zip](aoi-sprint1-review-v2.zip), [aoi-sprint1-review.zip](aoi-sprint1-review.zip).

`git diff --stat` không tính các file untracked. Diff tài liệu gồm cả thay đổi gate từ lượt trước; không coi toàn bộ diff là thay đổi mới của inventory.

## Review và quyết định đã chốt

### Đã accepted / user quyết định rõ

- Gate **7.1 accepted cho REAL-PCB-01-r1**. Không lặp lại acquisition/review gate. Agent tại máy đã kiểm tra bytes, commands và hashes; review bên ngoài dựa trên báo cáo người dùng chuyển tiếp, **không trực tiếp xác minh bytes bundle**. Người dùng xác nhận review và cho phép đóng riêng 7.1. Không có chữ ký/attestation do agent tạo thay người khác.
- R7/R8 lấy PCB **270R** làm authority cho dữ liệu fixture, không xác nhận thiết kế điện. Chỉ hai Value trong schematic working đổi 22R → 270R. Bản trước sửa, hashes trước/sau và exports cũ giữ nguyên. Không bulk update PCB.
- Requested SPI **top**; B.Paste cũ chỉ reference-only. Placement cả hai mặt, mm, absolute origin, không negate bottom X. Export CLI KiCad **10.0.7**; metadata/header không sửa để giả tạo provenance.
- Bốn REF** giữ nguyên theo UUID: `00000000-0000-0000-0000-00005b7adb04` là non-assembly-electrical-via; `00000000-0000-0000-0000-00005c9e4f14`, `00000000-0000-0000-0000-00005ccbd5ac`, `00000000-0000-0000-0000-00005ccbd5d8` là unresolved-empty-placeholder. Không assembly targets cho chúng; giữ fiducials riêng, giữ population flags và Paste geometry.
- Người dùng cho phép **chỉ** inventory 3.4/5.1: streaming, explicit budgets, immutable results, diagnostics; không reader/parser KiCad/Gerber, geometry import, reconciliation, publication, camera/hardware hoặc đánh giá pcbnew/IPC.
- Các quyết định Sprint 1 đã chốt trước: resolver directed DAG, không inverse tự sinh, consistency `synthetic-path-consistency-v1` trên bốn góc miền hữu hạn; fixture subset rectangle/line/arc và quy tắc contact/margin. Không thay các bảo vệ đó.

### Review acceptance và giới hạn xác nhận

- Inventory byte-admission slice đã qua review trực tiếp từ ZIP. Kết quả reviewer (370 passed, 1 skipped; 1.200 ca độc lập pass) được ghi **theo thông tin người dùng chuyển tiếp**, không phải agent tự chạy hoặc xác minh lại 1.200 ca. ZIP: [aoi-sprint2-inventory-review.zip](aoi-sprint2-inventory-review.zip); lượt cập nhật này không mở hay sửa ZIP.
- Review exit Sprint 1 cho subset affine/DAG và line/arc/rectangle đã chốt, cùng review quyết định 1.1/1.2, **đã accepted trong chat** theo cập nhật của người dùng. Đây là review acceptance; người dùng xác nhận thông tin review và yêu cầu ghi hồ sơ, không tạo thêm chữ ký/attestation hoặc suy thành xác nhận mọi yêu cầu normative.
- Checkbox được giữ nguyên trong lượt chỉ đồng bộ trạng thái review này: 4.1–4.4 và 7.1 checked (5/63); 1.1/1.2 có ghi review accepted riêng, không còn là review blocker. 3.4/5.1 và các task tổng còn nghĩa vụ giữ PARTIAL/open.
- Local bundle test 1 passed là evidence agent chạy trước đó. Reviewer chưa rerun bundle; code-review acceptance không thay thế mức bằng chứng local này.
- Parser compatibility, Foundation Prototype/Complete và hardware readiness chưa đạt.

## Fixture cố định và provenance

Root accepted: `C:\dev\aoi-reference\Edgeberry-Baseboard-working\fixture-revisions\REAL-PCB-01-r1`.

- [Snapshot source](../aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/source/).
- [Exports mới](../aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/exports/).
- [Manifest](../aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/manifest.json), [population](../aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/population.json), [SHA256SUMS](../aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1/SHA256SUMS.txt).

Upstream commit do user khai báo: `f88d9adabefffb9dd2a6909d15d14b1965cca943`; không chứng minh byte equivalence với upstream. Fixture revision riêng, không thay schematic revision 1.5/Gerber rev?. Manifest đóng băng còn câu review-pending từ giai đoạn chuẩn bị; gate acceptance mới được ghi ở repository, không sửa fixture để đổi câu lịch sử đó.

Đã ghi nhận: 57 footprint, 28 assembly refs, 32 placement rows, 18 BOM groups (từ 19 do R1/R7/R8 gộp 270R Qty3), 3 fiducial candidates, 56 F.Paste flashes. Export có cảnh báo font Lato bị thay thế; lần BOM đầu lỗi std::bad_any_cast, lần điều chỉnh thành công; exact argv và cả kết quả lỗi/thành công được giữ. Không khẳng định root cause đã được cô lập.

## API / implementation hiện có

`aoi_platform.inventory.inventory_artifacts(manifest, byte_sources, limits)`:

- Frozen `ArtifactDeclaration`, `InventoryManifest`, `InventoryLimits`, `ArtifactObservation`, `ArtifactInventory`; kết quả `InventorySuccess` hoặc `InventoryFailure`. Failure không có trường inventory; evidence không phải usable partial inventory.
- Giữ riêng declared SHA/size/metadata/provenance và computed SHA/actual size. Hash đầy đủ chỉ xuất hiện khi EOF; report chỉ có scope artifact-bytes-only, không canonical BoardRevision digest.
- Profile geometry cần PCB; SPI thêm Paste từng spi_side; post-placement thêm BOM/placement từng assembly_side; combined là cả hai. Side top/bottom khai báo riêng cho SPI và assembly. Role không unique; artifact ID unique. Reference-only vẫn hash nhưng không thỏa role bắt buộc. `supporting` phải reference-only.
- ByteSources là mapping opaque ID → factory trả fresh blocking BinaryIO, không resolver filesystem/URL. Inventory đọc chunk và đóng stream. Limits count/per-artifact/total/chunk đều explicit; chunk tối đa 1 MiB; một byte sentinel có thể vượt budget để phân biệt exact EOF. Resource/protocol/close failure dừng đọc tiếp; lỗi độc lập chỉ thu khi an toàn.
- Reuse ContractError/ValidationReport, stable issue sorting, không deduplicate meaningful errors. Thêm ErrorCode: FORMAT_UNSUPPORTED, REQUIRED_ARTIFACT_MISSING, DUPLICATE_ID, SOURCE_CONFLICT, INPUT_LIMIT_EXCEEDED, SOURCE_NOT_FOUND, SOURCE_IO_ERROR.
- Factory là trusted application code; chưa có timeout cho I/O bị treo hay sandbox/process memory enforcement. Không có local path adapter trong product. Test local dùng explicit root-checked allowlist và chỉ đọc fixture.

## Tests/checks đã chạy — không rerun trong lượt handoff

| Kiểm chứng | Kết quả đã quan sát |
| --- | --- |
| Portable inventory | 75 cases pass (có parametrization, không phải 75 hàm) |
| Toàn bộ pytest sau sửa code cuối | **370 passed, 1 skipped in 0.66s**, exit 0; 295 test cũ giữ nguyên |
| Local fixture opt-in | **1 passed in 0.20s**, exit 0; API stream 25 artifact, tổng **2,454,516 bytes**, hashes khớp |
| Strict OpenSpec sau cập nhật ledger | Valid, exit 0 |
| git diff --check sau cập nhật ledger | Exit 0; chỉ notices LF/CRLF, không whitespace error |
| File code/test mới untracked | Đã kiểm tra trailing whitespace riêng |
| Lượt chuẩn bị code review | collect-only xác nhận 75 cases; không chạy lại tests lúc trích code |
| Review trực tiếp từ ZIP, user chuyển tiếp | 370 passed, 1 skipped; thêm 1.200 ca độc lập pass; agent không rerun/xác minh bộ 1.200 ca |
| Bundle trong external review | Chưa được reviewer chạy lại; giữ evidence local của agent riêng |

Skip mặc định duy nhất là test fixture local do chưa đặt biến môi trường; test đó đã chạy riêng và pass. Editor runTests không discover pytest nên dùng Python của `.venv`. Test pass không thay thế review hoặc đáp ứng toàn bộ normative scenarios.

## Lệnh tái hiện (PowerShell)

```powershell
Set-Location C:\dev\aoi-platform
git -c safe.directory=C:/dev/aoi-platform rev-parse HEAD
git -c safe.directory=C:/dev/aoi-platform status --short
git -c safe.directory=C:/dev/aoi-platform diff --stat
git -c safe.directory=C:/dev/aoi-platform diff --check

# Suite portable: bỏ biến local chỉ trong process shell hiện tại.
Remove-Item Env:AOI_REAL_PCB_01_ROOT -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest tests/test_inventory.py --collect-only -q

# Kiểm chứng bytes trên fixture đã accepted; không acquisition/export lại.
$env:AOI_REAL_PCB_01_ROOT = 'C:\dev\aoi-reference\Edgeberry-Baseboard-working\fixture-revisions\REAL-PCB-01-r1'
.\.venv\Scripts\python.exe -m pytest tests/test_inventory_local.py -q -s
Remove-Item Env:AOI_REAL_PCB_01_ROOT

openspec validate board-geometry-foundation --strict
```

`safe.directory` chỉ truyền riêng từng lệnh vì máy từng báo dubious ownership; không sửa global Git config. Không chạy script chuẩn bị/export trong fixture khi chỉ cần kiểm chứng bytes. Không tự copy bundle vào repo; nếu sau này cần package fixture phải review cách đóng gói/license.

## Gap và bước tiếp theo

1. Đề xuất/evaluate hướng tái sử dụng reader KiCad theo task 1.5/5.2 trước khi chọn API/thư viện: exact version, license, provenance/UUID, geometry fidelity, unsupported constructs và resource behavior. **Chưa triển khai parser.** Lượt hiện tại chỉ sửa tài liệu, chưa thực hiện evaluation mới.
2. Không mở lại code review inventory hoặc gate 7.1 chỉ vì các câu review-pending lịch sử. Nếu có finding mới, tái hiện và xử lý trong authorization tương ứng; review pass không đóng các nghĩa vụ ngoài byte-admission.
3. 3.4 PARTIAL: artifact/provenance byte admission đã có; entity records/identity ở tầng parse còn mở. 5.1 PARTIAL: inventory/profile declaration/limits đã có; full ImportManifest semantics và parsed-candidate integration còn mở.
4. Reader/API evaluation, format/construct verification, geometry imports, BOM/placement reconciliation và publication đều ngoài authorization hiện tại. Đề xuất pcbnew/IPC trước đó chỉ là planning, không triển khai/evaluate thêm từ handoff này.
5. Nếu được cho phép sửa, chạy regression liên quan, full pytest, local opt-in khi ảnh hưởng byte inventory, strict OpenSpec và diff check; ghi kết quả thật và giữ task mở nếu còn nghĩa vụ.

Lưu ý lịch sử: phần gate closure trong implementation-status.md còn câu “inventory/API proposal chưa implemented” đúng ở thời điểm closure 2026-10-18; đã bị phần inventory 2026-10-19 phía trên thay thế cho trạng thái hiện tại. Phần đề xuất Sprint 2 cũ trong sprint-plan.md cũng được giữ có nhãn lịch sử. Không dùng các câu cũ để làm lại từ đầu hoặc coi inventory chưa tồn tại.


## Supervised environment A/B diagnosis - 2026-10-20

User reports local-attempt ZIP review verified 19/19 hashes; timeout cause was
unknown. New evidence is [kicad-ab-01](evaluation/windows_runner/evidence/kicad-ab-01/report.json).
Exactly two NEW sequential native runs (not simultaneous and not replayed A):
A minimal environment; B current host-session environment, with TEMP/TMP kept in
the same private owned staging cwd. Executable/helper/source bytes, argv/cwd and
Job/budgets match; verification recorded. No sandbox/permission/budget changes.
Only integration/helper changed; runner/probe stayed byte-identical.

Both transport FAIL TIMEOUT at 30016 ms. Last milestone for each is
`before-LoadBoard`; imports completed (A about 47 ms, B about 31 ms). No
`after-LoadBoard`, no stdout. Protocol/comparison NOT RUN; diagnostic prefixes
were not parsed as observations. Environment differences: 97 names, no values or
secrets stored. This does not identify the cause or rule out environment effects.
No third run or expanded matrix. No full suite/80 regression rerun; syntax and
same-input/config/hash checks passed, git diff --check passed.

Both Jobs active_processes=0 and runner cleanup_state=cleaned. Killed helpers
left temporary copies; owner removed them between runs and removed the entire
staging directory afterward. Caller handles remained usable; staged bytes and
all r2 hashes unchanged. Host-crash gap remains unchanged. Tasks 1.5/5.2 PARTIAL.

Next smallest step, not executed: review these milestone traces and consider one
supervised thread/wait-stack capture during LoadBoard, with separate authorization
for any needed diagnostic tooling. Do not expand environment trials or timeout.
Reproduction command (would launch two more runs; not executed again):
`.venv/Scripts/python.exe evaluation/windows_runner/kicad_local.py --ab evaluation/windows_runner/evidence/NEW_ID`
New A/B evidence awaits review; no parser compatibility or containment acceptance.


## Native stack tooling preflight - 2026-10-20

User reports A/B review verified 16/16 hashes; cause remains unknown. This turn
checked PATH, listed program/tool/extension locations and WinDbg package inventory:
no CDB/NTSD/WinDbg/LLDB/GDB collector found in accessible locations (not an exhaustive
machine inventory). WPR profile listing worked; resmon/taskmgr exist, but this
session has no native GUI control for wait-chain collection. No trace started.
BLOCKED_TOOLING: zero native runs, no snapshot, no new staging/Job or fixture access.
No thread wait location or cause inferred. No installation/elevation or code edits.
Evidence: [tool preflight](evaluation/windows_runner/evidence/native-stack-toolcheck-01/report.json).
Next smallest step: supply an existing CDB x64 path or separately arrange Microsoft
Debugging Tools for Windows; only then retry the authorized single snapshot run.
No full suite/regression run; diff check passed. Task 1.5/5.2 remains PARTIAL.

Visible-font attempt 2026-10-20: Start-Process failed before obtaining a PID due to duplicate environment keys PATH/Path; no loaded/JSON, no timeout or process cleanup to perform, no retry/environment changes; evidence: evaluation/kicad-reader/runs/visible-font-a2233478e4074f06bf4f2916578680f9/result.json; font-dialog hypothesis remains unconfirmed.


## Native logging redirect control - 2026-10-20

User reports observing and dismissing two missing-font dialogs (Lato Black/Heavy,
DejaVu Sans Bold fallback), after which a probe continued. This is user-observed
evidence, distinct from earlier timed-out agent runs. Verified bundled wx 4.3.1 /
wxWidgets 3.3.3 exposes LogStderr and Log.SetActiveTarget; synthetic warning reached
stderr. Only evaluation helper changed: retain LogStderr target after pcbnew import;
no log suppression, font installation, PCB save or runner changes.

Exactly one runner control, unchanged 30s/budgets and 45s watchdog: transport PASS,
comparison PASS (18/18 checks), observed KiCad 10.0.7, elapsed 515 ms.
Both original font warnings and additional native image-handler warnings retained
in stderr, followed by after-LoadBoard and loaded. This supports the dialog-blocking
hypothesis; it is not parser compatibility or complete containment acceptance.
Job active count zero, cleanup cleaned, helper-temp empty, owner staging removed,
caller handle usable and fixture hashes unchanged. No full suite or unrelated
regressions run. Targeted logging warning check and native comparison are evidence.
[New evidence](evaluation/windows_runner/evidence/kicad-stderr-log-01/report.json).
Next: review this helper logging change and successful control; keep tasks 1.5/5.2
PARTIAL and host-crash gap open. No checkbox/allowlist/commit/push changes.

Logging redirect accepted per user-relayed ZIP review (2026-10-20): 12/12 hashes, JSON equal to r2 baseline, transport evidence 515 ms and comparison 18/18 PASS; reviewer did not rerun native. Font-dialog blocker closed for the tested path only; parser compatibility and host-crash gap remain open.

Synthetic rectangular cutout control (2026-10-20), awaiting review: exactly one native run through unchanged runner/helper/budgets, transport PASS in 265 ms; schema/build/hash and explicit geometry oracle PASS (8/8 checks). Outer [0,20]x[0,10] mm; inner [8,12]x[4,6] mm. All eight line UUID/endpoints preserved; native valid, one outer outline, one hole, bbox 20x10 mm. Job active=0, cleaned; helper-temp/staging removed; synthetic PCB hash unchanged. r1/r2 not accessed by this control. Evidence/script/oracle: evaluation/windows_runner/evidence/cutout-01 and evaluation/windows_runner/cutout_control.py. No old regressions/full suite run; diff check PASS. Only this fixture cutout recognition established, not general topology or usable import geometry; tasks 1.5/5.2 PARTIAL. Next: review this narrow oracle/evidence before extending geometry coverage.

Cutout control accepted per user-relayed ZIP review: 12/12 hashes, eight primitives/endpoints, outer20x10/cutout4x2, evidence8/8 PASS; reviewer did not rerun native. Not generalized topology/import support.

Bottom rotation synthetic control (2026-10-20), awaiting review: exactly one native runner control, transport PASS in 1530 ms, 44/44 checks PASS, build 10.0.7. Top origin(10,10), bottom(30,20), each footprint90deg, pads stored local(1,2)/(-3,1), raw angles30/60deg. Independent pre-run oracle from KiCad tag10.0.7 parser/BOARD_ITEM/RotatePoint/PAD source: world=(X+v,Y-u), no extra mirror for already-stored bottom coordinates; top world(12,9)/(11,13), bottom(32,19)/(31,23). UUID/parent association, raw angles, local/world positions, size and layer sets matched. Coordinate tolerance1nm; no angle modulo normalization. Source/reference/formula/oracle hashes frozen before launch and unchanged. Raw actual retained. Cleanup cleaned, Job active0, helper-temp/staging removed, synthetic PCB unchanged. No runner/probe/product/r1/r2 changes or old regression/full-suite runs. Diff check PASS. Script: evaluation/windows_runner/bottom_control.py; evidence: evaluation/windows_runner/evidence/bottom-01. Only this fixture convention established; no canonical/targeting geometry or general bottom support. Task1.5/5.2 PARTIAL, host-crash gap open. Next: review this narrow geometry evidence.

Bottom rotation review accepted per user-relayed ZIP review: 13/13 hashes and independent fixture/oracle matched. Reviewer did not rerun native KiCad or verify all source links; no canonical bottom transform established. This supersedes the preceding awaiting-review wording only within that scope.

Footprint-local Edge.Cuts evaluation (2026-10-20), pending review: probe protocol v2 adds separate footprint_edges and explicit incomplete geometry coverage. Bundled API metadata inspected before implementation. Independent source-authored oracle frozen before exactly one native control: two asymmetric segments on top/bottom footprints at 90 degrees; board-level rectangle remains four separate edges. Transport PASS, 641 ms; 10/10 detection/schema/hash/cleanup checks PASS. Native aggregate outline valid=false/count=0 retained, not used to derive detection expectations. API endpoints retained as native-api-unclassified, distinct from file-local declarations. Job active0, cleaned, helper-temp empty, caller handle usable, owner staging removed; fixture/oracle unchanged. Focused portable regressions: 53 PASS (23 historical replay with explicit legacy opt-in, 30 new schema cases); new tests initially reproduced 28 failures/2 passes before fix. No full suite or historical native reruns. Files: [protocol](evaluation/kicad-reader/PROTOCOL-v2.md), [control](evaluation/windows_runner/footprint_edges_control.py), [evidence](evaluation/windows_runner/evidence/footprint-edges-01/report.json). Tasks1.5/5.2 remain PARTIAL; no canonical geometry, general topology, parser compatibility or host-crash containment claim. Next: review detection/protocol delta and this narrow native evidence.


Footprint-local Edge.Cuts detection accepted per user-relayed ZIP review: 20/20 manifest hashes matched; two segments with correct parent/type/layer and four separate board edges verified. Reviewer did not rerun native KiCad or the 53 tests, and did not independently verify baseline/index or native-run count. Acceptance is limited to detection in this fixture, not canonical geometry or topology; Tasks 1.5/5.2 remain PARTIAL. This supersedes the preceding pending-review wording only within that scope. Future control runs now include kicad_local.py in dependencies_sha256; historical reports/hashes/evidence remain unchanged. No native rerun for this provenance addition.


Portable test implementer rerun (2026-10-21): 53 passed in 1.31s, exit code 0, for test_harness.py and test_footprint_edges.py only. This is an implementer rerun, not an independent reviewer rerun. Explicit argv used -o cache_dir inside the new evidence directory, with no -p option. [Evidence: argv/cwd/exit code/stdout/stderr](evaluation/windows_runner/evidence/footprint-edges-portable-rerun-03/); rerun-01/02 remain unchanged. No native KiCad or full suite run. Tasks 1.5/5.2 remain PARTIAL.


Portable probe enumeration (2026-10-21): implementer run, 58 passed in 1.22s, exit 0 (5 new runpy/fake-pcbnew cases plus 53 existing portable tests). [Test](evaluation/kicad-reader/test_probe_enumeration.py); [argv/cwd/exit/stdout/stderr](evaluation/windows_runner/evidence/footprint-enumeration-portable-01/). Covers empty/incomplete collection, two parent/item identities and separate board edges, raw asymmetric API endpoints without transforms, other-layer skip, and explicit non-PCB_SHAPE/missing-parent/wrong-parent failures without observation JSON. Fake supplies constant accessors only; no KiCad parsing/geometry simulation. Probe logic unchanged. This verifies Python enumeration/rejection control flow, not native API behavior, topology, canonical geometry or parser compatibility; no native/full-suite run. Tasks 1.5/5.2 remain PARTIAL. No historical evidence, runner/helper, product or checkbox changes.


Portable non-segment footprint Edge.Cuts case (2026-10-21): added exactly one enumeration test for fake PCB_SHAPE enum 2 (SHAPE_T_ARC), retaining UUID/parent/layer, native-shape-2 tag and asymmetric API endpoints; actual probe payload passes existing schema and coverage remains incomplete. Enumeration file only: 6 passed in 0.13s, exit 0, implementer mocked run. [argv/cwd/exit/stdout/stderr](evaluation/windows_runner/evidence/footprint-enumeration-portable-02/). No arc geometry inferred from endpoints; no native evidence or general arc support claim. Probe/schema unchanged; Tasks 1.5/5.2 remain PARTIAL. No native/full suite, ZIP, commit or push.


D-outline native control (2026-10-21): exactly one new run, overall FAIL (26/27 checks). [Control](evaluation/windows_runner/d_outline_control.py); [report](evaluation/windows_runner/evidence/d-outline-01/report.json); [individual comparisons](evaluation/windows_runner/evidence/d-outline-01/comparisons.json). Analytic oracle and hashes written before launch: arc start(10,0), mid(15,5), end(10,10), center(10,5), radius5; closing diameter; tolerance1nm. Both UUID/types and all primitive fields PASS; native valid=true/count1/holes[0]/origin(10,0) PASS. Native bbox size(5.00252,10) versus expected(5,10): X error0.00252mm exceeds 0.000001mm. Cause not established; tessellation is a hypothesis, not a verified diagnosis. No tolerance/oracle changes or rerun. Transport PASS, 561ms, root exit0, schema/build10.0.7/source hash PASS. Job active0/cleaned, helper-temp empty, caller handle usable, stage/source/oracle unchanged and owner staging removed. Raw stdout/stderr and actual/expected retained. No winding/general-topology/canonical claim. Tasks1.5/5.2 remain PARTIAL. No existing probe/schema/runner/helper/evidence changes; no full suite, ZIP, commit/push. Stop at bbox discrepancy for review.


D bbox diagnostic (2026-10-21), implementer evidence awaiting review: metadata introspection (no LoadBoard) confirmed m_MaxError/Outline/PointCount/CPoint accessors. Exactly one diagnostic native run via unchanged runner/helper/budgets/logging, 13/13 checks PASS. Byte-identical d-outline-01 source copy hash 6b719b92832c6c10d03618c7fc5c6369e926497389d81b33d40513f5c79bb9e7; separate polygon prediction/hash frozen before launch. Actual max error5000IU, bbox width5.002520mm and extreme(15.00252,5)mm match prediction within1nm. All outer contour vertices retained in raw JSON. This supports the source-derived approximation explanation; does NOT change d-outline-01 FAIL or its analytic oracle/tolerance and does not establish topology/canonical geometry. Cleanup cleaned/Job active0, helper-temp empty, caller handle usable, owner staging removed; source/prediction unchanged. Prior control/evidence and probe/schema/runner/helper hashes preserved. [Evidence](evaluation/windows_runner/evidence/d-bbox-diagnostic-01/); scripts d_bbox_diagnostic_control.py and d_bbox_diagnostic_probe.py in evaluation/windows_runner. Tasks1.5/5.2 PARTIAL. No full suite, ZIP, commit/push.


D bbox diagnostic accepted by user (2026-10-21), limited to the D fixture and based on implementer-provided code/results: runtime m_MaxError=5000IU, bbox width5.002520mm and extreme(15.00252,5)mm match the polygon prediction. No direct evidence-bundle review or independent native rerun has occurred. This supersedes the preceding awaiting-review wording only within this acceptance scope. d-outline-01 remains FAIL against its original analytic oracle; historical results/tolerance unchanged. Topology/canonical geometry remain unverified; Tasks1.5/5.2 remain PARTIAL.


Roundrect diagnostic (2026-10-21), implementer evidence awaiting review: bundled metadata introspection confirmed ratio/radius F_Cu accessors and ROUNDRECT enum4; saved KiCad tag10.0.7 pad/padstack source verifies KiROUND(min(size.x,size.y)*ratio). Independent oracle frozen before exactly one native run: top unrotated footprint, one pad4x2mm, ratio0.25, radius0.5mm; size/radius tolerance1nm, ratio tolerance1e-12. 21/21 checks PASS including UUID/parent, shape, size, ratio/radius, layer set, build/source hash and cleanup. Job active0/cleaned, helper-temp empty, caller handle usable, owner stage removed; fixture/oracle/references unchanged. [Evidence/source citations/raw output/comparisons](evaluation/windows_runner/evidence/roundrect-01/); separate roundrect_diagnostic_control.py and roundrect_diagnostic_probe.py under evaluation/windows_runner. Only fixture parameters verified; boundary, rotation/bottom, per-layer overrides and canonical geometry remain unverified. Existing probe/schema/protocol/runner/helper unchanged. Tasks1.5/5.2 PARTIAL. No real board, full suite, historical rerun, ZIP, commit/push.


Roundrect fixture-parameter acceptance (2026-10-21), per user-relayed review: ZIP CRC passed; 26/26 manifest hashes and 9/9 Python dependency hashes matched. Oracle/source snapshot, raw output and 21/21 checks agree on pad4x2mm, ratio0.25, radius0.5mm. Reviewer checked schema against saved JSON; did not rerun native or independently verify online source/executable. Acceptance is limited to roundrect parameters of this fixture, not boundary, rotation/bottom, per-layer overrides or canonical geometry. Supersedes prior awaiting-review wording only within this scope. Tasks1.5/5.2 remain PARTIAL.


Bow-tie negative native control (2026-10-21), implementer evidence awaiting review: exactly one run, 32/32 checks PASS, outcome expected_invalid_outline_observed. Four source-authored segments/UUIDs and analytic crossing(5,5), t=u=0.5, frozen with hashes before launch; endpoint tolerance1nm. Transport/schema/build10.0.7/input hash PASS, root exit0; exactly four segment UUIDs/endpoints and empty footprint_edges verified. Native outline.valid=false as expected; no count/holes/bbox expectations for invalid outline. Control PASS means invalid detection observed, not crash/transport failure. Job active0/cleaned, caller handle usable, helper-temp empty, owner staging removed; fixture/oracle unchanged. [Control](evaluation/windows_runner/bow_tie_control.py); [raw output/comparisons/hashes/transport/report](evaluation/windows_runner/evidence/bow-tie-01/). Only native invalid-outline detection for this fixture; product OUTLINE_INVALID/publication gate unproven. Tasks1.5/5.2 PARTIAL. Existing probe/schema/runner/helper/evidence unchanged; no real board, full suite, ZIP, commit/push.


Bow-tie fixture detection accepted per user-relayed review (2026-10-21): ZIP CRC clean; 20/20 manifest hashes, 8/8 Python dependency hashes and 2/2 pre-run hashes matched. Independent crossing(5,5) oracle, raw primitives, 32 checks and 23 comparisons consistent; schema on saved JSON PASS. Native evidence records outline.valid=false, exit0, transport561ms and successful cleanup. Reviewer did not rerun native or verify executable/runtime. Acceptance only covers native invalid-outline detection of this fixture, not product OUTLINE_INVALID/publication gate. Supersedes preceding awaiting-review wording only within this scope. Tasks1.5/5.2 remain PARTIAL.


Evaluation outline decision (2026-10-21): new outline_decision.py validates JSON bytes with existing strict-v2 schema, no legacy opt-in. Invalid native outline yields immutable rejected/OUTLINE_INVALID diagnostic at outline.valid retaining schema-validated input_sha256/build, no inferred entity UUID. Expected decoding/schema errors yield rejected/SCHEMA_INVALID without unvalidated provenance. valid=true yields only not_rejected_by_outline_check. No revision/usable geometry output or publication call. [Portable evidence](evaluation/windows_runner/evidence/outline-decision-portable-01/): only test_outline_decision.py run, 17 passed in0.06s, exit0; includes original bow-tie stdout bytes replay. Schema acceptance is not provenance authentication or complete geometry validation; product OUTLINE_INVALID/atomic publication remain unproven. Tasks1.5/5.2 PARTIAL. Existing probe/schema/protocol/runner/helper/evidence unchanged. No native/full suite/ZIP/commit/push.


Outline-decision evaluation accepted per user-relayed review (2026-10-21): ZIP CRC clean, 9/9 manifest hashes matched; replay bytes and schema byte-identical to reviewed bow-tie ZIP. Reviewer exercised OUTLINE_INVALID, valid=true intermediate status and 14 invalid inputs in memory with expected results. Implementer log records17 pytest PASS; reviewer did not rerun the complete pytest/import-path execution. Acceptance is evaluation decision only, not provenance authentication, product rejection or atomic publication. Supersedes prior unreviewed status only within this scope. Tasks1.5/5.2 remain PARTIAL.


Outline decision entrypoint integration (2026-10-21), implementer evidence awaiting review: run.py persists JSON outline_decision and typed diagnostics on successful strict-v2 probe execution. Rejected decisions force failed outcome/nonzero exit via diagnostics; existing required oracle checks remain unchanged. valid=true is only not_rejected_by_outline_check. Transport failure/timeout leaves outline_decision=null, never evaluates partial stdout. Explicit unversioned historical replay records not_applicable_historical_replay and unknown coverage; v2 markers prevent legacy fallback. Existing schema function moved verbatim into observation_schema.py; run.py re-exports schema, decision loads shared definitions without reexecuting entrypoint. [Evidence](evaluation/windows_runner/evidence/outline-decision-integration-01/): exactly test_harness.py and test_outline_decision.py, 53 passed in2.35s, exit0 (23 existing harness, 13 integration, 17 decision cases). Evaluation-only; schema does not authenticate provenance, intermediate status is not import-ready, product rejection/atomic publication remain unproven. Tasks1.5/5.2 PARTIAL. No native/full suite, probe/protocol/runner/helper/historical evidence changes, ZIP, commit/push.


## Safe continuation checkpoint (2026-10-21; no Git commit)

HEAD verified: 6e52b4c0cd2843e321512fa9ce6636e7b0ebf6a9. Index empty.
Tracked unstaged changes: HANDOFF.md, evaluation/kicad-reader/probe.py, run.py,
test_harness.py. New evaluation modules/tests/controls/evidence remain untracked;
untracked .agents/ and .claude/ are pre-existing integration files, leave untouched.
No AGENTS.md found at C:/, C:/dev/, repo root or repository search excluding
.git/.venv. OpenSpec status board-geometry-foundation reports planning artifacts
complete; this is NOT implementation completion. Tasks1.5/5.2 explicitly PARTIAL
and unchecked. No task/status/allowlist edits authorized.

Current task finished: package outline-decision entrypoint integration for review.
[Review ZIP](aoi-outline-integration-review-044be98424c0.zip): 13/13 manifest hashes,
CRC and inventory verified; packaged current evaluation files match disk at this
checkpoint. Contains pre-integration run.py byte-for-byte under review-reference,
from reviewed aoi-outline-decision-review-4ecfbfb9badb.zip. Shared schema function
AST and newline-normalized text match old schema; run.py still exposes schema.
New schema module is a dependency, not a new protocol. Report has typed rejection
for strict-v2, intermediate true status, null decision on transport failure and
explicit not-applicable historical replay. Existing oracle checks remain required.
Integration is awaiting user/reviewer feedback; do NOT record acceptance yet.
Standalone outline decision, bow-tie detection, roundrect parameters and earlier
narrow fixture acceptances are recorded above with their distinct review limits.

[Latest test evidence](evaluation/windows_runner/evidence/outline-decision-integration-01/):
53 passed in2.35s, exit0, implementer run of test_harness.py and
test_outline_decision.py only. argv/cwd/exit/raw stdout/stderr saved. No tests/native
rerun during packaging/checkpoint. LF normalization followed that test execution;
current manifest is not a historical test-time dependency attestation.
Other evidence: outline-decision-portable-01 (17 PASS), bow-tie-01 (32 checks),
roundrect-01 (21 checks), d-bbox-diagnostic-01 (13 checks), d-outline-01 remains FAIL
on analytic bbox; none of these historical results may be overwritten.
Reproduction when separately authorized: .venv/Scripts/python.exe -B -m pytest
evaluation/kicad-reader/test_harness.py evaluation/kicad-reader/test_outline_decision.py
-q -o cache_dir=<NEW-EVIDENCE-DIRECTORY>/pytest-cache

Open provenance gap: bottom_control.py, bow_tie_control.py, cutout_control.py,
d_bbox_diagnostic_control.py, d_outline_control.py, footprint_edges_control.py,
kicad_local.py and roundrect_diagnostic_control.py hash run.py but lack new
observation_schema.py/outline_decision.py inventory. Schema-only consumers require
the former; strict entrypoint decision paths additionally require the latter.
kicad_local.py has an older inventory omitting run.py itself. Report gaps only;
do not retrofit historical hashes. Older standalone scripts/bundles copied alone
may need coherent dependency snapshots. Planning/status descriptions containing
old review-pending/DNP notes are historical and not comprehensively synchronized.

Restrictions: evaluation-only, no product adapter/publication/usable canonical
geometry claim; schema does not authenticate provenance. Host-crash before Job
assignment containment gap remains. Preserve fixtures, oracle bytes, all old
logs/ZIPs, source/probe/runner/helper unless specifically authorized. No reset,
cleanup, staging, commit/push, archive or checkbox changes. Preserve Task1.5/5.2
PARTIAL. Current request permits HANDOFF edits only.

Next single action: await review feedback on the integration ZIP; read that feedback
before selecting any implementation or dependency-inventory correction. Do not
start another geometry/native slice automatically.

## Integration acceptance and dependency inventory (2026-10-21)

Supersedes the checkpoint's pending-review/next-action statements: user reports
outline-decision integration ZIP review PASS within evaluation-only scope,
independent rerun 53 passed and no manifest hash mismatch. This is not product
acceptance, complete geometry or atomic publication; Tasks 1.5/5.2 stay PARTIAL.

Updated eight Windows control/integration inventories to include observation_schema.py
where run.py.schema is consumed (including both kicad_local inventories; the older
A/B inventory now includes run.py). Those paths do not invoke outline_decision.py.
The evaluation run.py report now hashes itself and shared schema; it additionally
hashes outline_decision.py only on the strict decision path, not transport failure
or historical replay. No runner/helper mechanics or observation semantics changed.

[New portable evidence](evaluation/windows_runner/evidence/dependency-inventory-01/):
56 passed in 2.34s, exit 0 (test_harness.py + test_outline_decision.py; includes
three dependency-path/hash regressions). Implementer rerun, not independent review.
invocation/result/raw stdout/stderr, pre-run code/input hashes, syntax checks and
inventory audit retained; all recorded code/input hashes unchanged after tests.
No native/full-suite rerun; old evidence and recorded hashes were not rewritten.
Historical dependency gaps remain historical limitations, not retroactively fixed.

Next action: review this inventory-only change and new portable evidence before
selecting further work. No commit/push, checkbox/allowlist or fixture changes.

## Dependency inventory review acceptance (2026-10-21)

User reports review PASS for aoi-dependency-inventory-review-b25561382762.zip,
within evaluation-only scope: independent rerun 56 passed; 42/42 manifest hashes,
15/15 pre-run hashes and eight packaged diffs verified. Current inventory accepted
with the documented baseline limitations. No historical baseline reconstruction or
evidence modification is required. This supersedes the preceding pending-review
next action. No claim of product acceptance, complete geometry or atomic publication.
Tasks 1.5/5.2 remain PARTIAL; no checkbox/allowlist change.

Proposed next slice (not implemented or authorized by this note): one synthetic
native control for repeated pad number strings, tracing tasks 5.5 and pcb-data-import
spec's Bottom footprint and repeated pad numbers scenario. Use two distinct pad UUIDs
both numbered "1" in one unrotated top footprint at explicit asymmetric positions;
verify both observations survive with exact string numbers, parent association and
independent coordinates. Existing probe already emits pad UUID/number/position.
Pre-run oracle/hashes, one bounded native run, unchanged fixture and cleanup evidence;
no canonicalization/publication, no claim to close the full combined scenario.
Next action: user review of this single proposal before implementation.


## Repeated pad numbers native control (2026-10-21; pending review)

One new native control through the existing runner/helper, unchanged budgets and
stderr logging: [repeated-pads-01](evaluation/windows_runner/evidence/repeated-pads-01/).
36/36 checks PASS; transport 1812 ms, root exit 0, build 10.0.7, strict schema PASS.
Two separate UUIDs under one top unrotated footprint retain string number "1";
local (1,2)/(4,3), world (11,12)/(14,13) mm match the pre-launch independent
translation oracle within 1 nm. Parent association is nested observation membership,
not a separate native parent accessor. Size and layer membership also match.
Fixture/oracle and dependency hashes unchanged; Job active_processes=0, cleaned,
caller handle usable, helper-temp empty and owner staging removed. Native duplicate
image-handler warnings remain in stderr; not suppressed. No test suite rerun.

Only new repeated_pads_control.py and new evidence added, plus this handoff note.
No probe/schema/runner/helper changes. Native acceptance remains pending ZIP review;
this does not establish canonical pad records, combined bottom/cutout behavior,
product acceptance or atomic publication. Tasks 1.5/5.2 remain PARTIAL.

Next action: review repeated-pad ZIP. User authorizes commit/push of accepted related
changes only after review PASS. Current branch is master; use a separate working
branch for that checkpoint, do not merge/push development into main/master. Remote
origin is https://github.com/m0nst3r99/aoi-platform.git. No commit/push yet; inspect
scope/index and exclude caches, environments and temporary files before staging.

## Repeated pads review acceptance and checkpoint authorization (2026-10-21)

User reports ZIP aoi-repeated-pads-review-ea63f736c34e.zip PASS for evaluation-only
repeated pads: reviewer verified 27/27 manifest hashes, fixture/oracle, nine Python
dependency hashes and independently checked raw observation; no native rerun.
This supersedes the pending-review next action above. Tasks 1.5/5.2 remain PARTIAL;
no product acceptance, complete geometry or atomic publication claim.

Checkpoint scope: current code/evidence in the three reviewed outline integration,
dependency inventory and repeated-pad packages, plus this HANDOFF. 49/49 current
packaged evaluation files match the latest reviewed bytes. Required untracked
D-bbox/roundrect probe dependencies match their accepted historical report hashes;
the D-outline fixture matches its control-pinned hash. These are included unchanged
so staged controls have their local dependencies. Other historical evidence/tests,
agent integration files and review ZIPs remain outside this checkpoint.

User authorized one checkpoint commit and push on new branch
checkpoint/outline-inventory-repeated-pads; no main/master commit/push or merge.
Verify staged byte hashes and diff before committing. No native/test rerun in this
checkpoint operation. Preserve all historical evidence and documented limitations.

Checkpoint pre-commit verification: 48 changed paths staged, evaluation blobs
byte-identical to working files and latest applicable reviewed package hashes.
No ZIP/cache/environment/agent files staged; maximum staged file 58,935 bytes
before this note. Recognizable private-key/token pattern scan found no matches
(not an exhaustive secret audit). Default cached diff --check exits 2: 1,867
whitespace findings. CR-aware check leaves one new blank line at EOF in
observation_schema.py:79. These are reviewed preserved bytes, intentionally not
rewritten; do not report whitespace validation PASS. No algorithm/test/oracle
changes made during commit preparation. Remaining historical files stay uncommitted.

## Current Git workflow (2026-10-21)

Checkpoint was committed and pushed with explicit authorization as
f77efa171cfb58e843e93ebbe6d16a0f30ab9358 on
checkpoint/outline-inventory-repeated-pads; that remains the current working branch.
The earlier pre-commit/pending-push instructions above are historical.
Local master and origin/master refs both resolve to
6e52b4c0cd2843e321512fa9ce6636e7b0ebf6a9 at this check (no remote fetch performed).
User designates master as canonical integration branch. Previous main has unrelated
history and must not be used as a development base. User reports master protection
is being configured; agent has not verified or modified GitHub rulesets.

Continue on the current checkpoint branch unless explicitly instructed otherwise.
Existing OpenSpec scope permits implementation/tests/evidence, not automatic
commit/push. Every future commit/push requires explicit authorization. Never merge
into master, delete branches, force push, reset history or change protection settings
without explicit approval. Preserve untracked tests/oracles/evidence; no git clean
or indiscriminate git add -A. At task end report changed files, actual test results,
Git status and proposed commit/push; wait for approval before publishing.
Tasks 1.5/5.2 remain PARTIAL. No new implementation slice selected by this update.


## Strict-v2 duplicate pad UUID evaluation (2026-10-22; pending review)

Shared observation_schema.py now rejects duplicate pad UUID identity across all
footprints in strict-v2 only. UUID objects are compared without changing source
strings, merging or dropping pads. Distinct UUIDs with repeated number string "1"
remain valid. Legacy replay returns before this new check; its behavior is unchanged.
Decision reports SCHEMA_INVALID; entrypoint fails with nonzero exit. No product
DUPLICATE_ID/publication/canonical geometry claim; Tasks 1.5/5.2 remain PARTIAL.

Portable evidence: evaluation/windows_runner/evidence/duplicate-pad-uuid-portable-01/.
Exactly test_harness.py and test_outline_decision.py executed: 64 passed in 2.44s,
exit 0. Raw repeated-pads stdout bytes match the accepted review ZIP. Negatives
are in-memory copies: same footprint, distinct valid parent UUIDs across footprints,
and equivalent UUID spelling. Before introducing collisions, schema-valid controls
are asserted. Schema does not mutate the payload. Replayed synthetic board passes
the outline decision only; unrelated real-board harness oracles still fail as expected.
Eight code/input hashes match before/after; argv/cwd/raw stdout/stderr recorded.
Implementer portable run only, no native/full-suite run or independent review yet.

Changes: shared schema, two portable test files, this status note and HANDOFF.
Probe, run.py decision routing, runner/helper, legacy protocol, historical evidence,
checkboxes and allowlist unchanged. Prior HANDOFF workflow edits retained.
Next: review the duplicate-pad UUID ZIP. No commit/push authorization for this slice.


## Duplicate pad UUID review acceptance (2026-10-23)

User reports duplicate-pad-uuid review ZIP PASS within evaluation-only scope:
independent rerun 64 passed; 28/28 manifest hashes and eight pre/post-run hashes
match; raw repeated-pads replay matches the previously accepted bytes. This
supersedes the pending-review and no-independent-review statements above for this
slice only. No native rerun is claimed. Historical evidence remains unchanged.
Tasks 1.5/5.2 remain PARTIAL; no product rejection/publication or canonical geometry
acceptance. No commit/push authorization has been given for this slice.

Next proposal for review, not implemented: strict-v2 duplicate board-level edge UUID
rejection. Current schema validates each UUID but constructs a set from board edges
without checking duplicates within that collection. Trace: task 3.4 and PCB-001
invalid-outline/nonfinite/duplicate-entity scenario. Portable replay with a single
in-memory UUID collision should reject SCHEMA_INVALID through decision and entrypoint;
valid distinct-edge replay and historical legacy behavior must remain unchanged.
No new native fixture/run, geometry normalization or publication implementation.


## Strict-v2 duplicate board-edge UUID evaluation (2026-10-23; pending review)

Observation schema now rejects duplicate UUID identity within board-level edges,
including identical and equivalent UUID strings. This is separate from accepted
pad UUID checks; no new cross-entity collision rule. Payloads are not changed,
merged or dropped. Legacy returns before the strict-v2 checks and is unchanged.
SCHEMA_INVALID propagates through decision and failed/nonzero entrypoint.

Evidence: evaluation/windows_runner/evidence/duplicate-board-edge-uuid-portable-01/.
Exactly test_harness.py and test_outline_decision.py: 71 passed in 3.06s, exit 0.
Seven new cases cover identity spellings, nonmutation and legacy behavior. Existing
accepted raw repeated-pads positive replay remains schema-valid/intermediate (not
import-ready). Negative copies change only one edge UUID after asserting a valid
control. Eight pre/post code/input hashes match; argv/cwd and raw outputs retained.
No native/full-suite run or historical evidence changes. Implementer evidence only;
new slice awaits review. Tasks 1.5/5.2 remain PARTIAL; no product/publication claim.

Only shared schema and its two portable test files changed, plus HANDOFF/status.
Git f77efa1 predates accepted pad-UUID work: Git diffs are cumulative. Review package
also includes exact pad-UUID ZIP baseline and separate diffs isolating new code/tests;
document diffs additionally include the intervening acceptance notes.
No commit/push. Next action: review board-edge UUID ZIP before any publishing.


## Duplicate board-edge UUID review acceptance (2026-10-23)

User reports duplicate-board-edge-uuid ZIP PASS within evaluation-only scope:
independent rerun 71 passed; 38/38 manifest hashes, eight pre/post-run hashes and
ten baseline/diffs match. Pad-UUID baseline matches the previously accepted version.
This supersedes pending-review statements for this slice only. No native rerun or
product/canonical/publication acceptance is inferred. Tasks 1.5/5.2 remain PARTIAL.
Historical evidence unchanged; no commit/push authorization.

Next proposal, not implemented: compare footprint UUID uniqueness by UUID identity
in strict-v2. Current schema compares footprint UUID strings, unlike accepted pad
and board-edge identity checks; equivalent spellings can evade that collection's
duplicate check. Trace task 3.4 and PCB-001 duplicate-entity scenario. Portable
controls should start with two valid distinct footprints and disjoint pad UUIDs,
then change only the second footprint UUID to an identical/equivalent first UUID.
Require SCHEMA_INVALID through decision and failed/nonzero entrypoint, nonmutation,
and unchanged legacy behavior. Scope excludes cross-entity collision and parent
reference matching policy. No native run or geometry normalization is proposed.


## Strict-v2 footprint UUID identity (2026-10-23; pending review)

Footprint uniqueness now compares UUID identity instead of strings. Parent list and
reference matching, cross-entity collision checks, pad/board-edge checks, probe and
runner are unchanged. No payload rewriting. Legacy behavior unchanged.
Evidence: evaluation/windows_runner/evidence/duplicate-footprint-uuid-portable-01/.
Only test_harness.py and test_outline_decision.py ran: 78 passed in 2.67s, exit 0.
Seven new cases use two valid distinct footprints with disjoint pad UUIDs and no
footprint_edges. Identical/equivalent footprint collisions reject SCHEMA_INVALID;
positive remains intermediate, entrypoint retains unrelated real-board oracles.
Nonmutation and legacy checked. Eight pre/post code/input hashes match. No native.
Tasks 1.5/5.2 remain PARTIAL; historical evidence retained. No commit/push.

Next proposal (not implemented): review a product-facing immutable canonical Pad
candidate contract for tasks 3.4/5.5 with explicit source artifact/hash/entity and
validated source-to-P transform, starting with synthetic rectangular copper pads.
Design.md Pad contract (line 410) requires geometry in P, identity/number/layers and
provenance; task 5.13 forbids guessed transforms. Define all required fields and
failure behavior before code, preserve repeated numbers, reject invalid/missing
provenance/context/unsupported geometry, and keep candidate non-published. No native
reader bridge, BoardRevision publication or targeting authority in that first slice.
This replaces a proposed continuing chain of evaluation-only UUID hardening.

Review packaging: exact Git f77efa1 baseline yields cumulative pad/edge/footprint
diff; accepted board-edge ZIP provides separate baseline/diff for this slice.
Documentation diff includes intervening acceptance notes. Await review authorization.


## Footprint UUID acceptance and Pad candidate contract (2026-10-23)

User reports footprint UUID ZIP review PASS within evaluation-only scope:
independent rerun 78 passed; 38/38 manifest hashes, eight pre/post-run hashes and
ten baseline/diffs match. Supersedes pending-review statements for this slice only;
no native rerun/product acceptance inferred. Historical evidence unchanged.
Tasks 1.5/5.2 remain PARTIAL; no commit/push authorization.

New review draft in design.md: immutable canonical Pad candidate, tasks 3.4/5.5/5.13.
Normative requirements separated from D1-D5 proposals: candidate revision scope,
identity/provenance binding, supported geometry/maps, output representation and
limits/numeric policy. Product implementation blocked on selection; no reader bridge,
BoardRevision creation, publication, targeting or native run. Next action: review
contract and select decisions, then authorize a bounded implementation separately.


## Pad candidate contract revision 2 (2026-10-23; documentation only)

D1-D4 and structural D5 selections recorded in design.md. Candidate scope is caller
supplied unpublished revision context, all source/target frames match it; no core
guards relaxed. Opaque canonical IDs retain exact strings; top SMD/F.Cu/mm proper
rigid subset supports explicit nonzero pad angle and indexed vertices.
Complete field/source/context table, parent declaration-versus-verification boundary,
proposed numeric budgets/diagnostic reservation and independent +90-degree pad oracle
added. O1-O4 remain for review: declaration-consistent association, empty pad number,
exact limits/numeric guard and source-entity alias policy. No product code/tests/native,
commit/push or historical evidence edits. Tasks 1.5/5.2 PARTIAL. Next: select remaining
contract decisions before implementation authorization.

## Canonical Pad candidate implementation (2026-10-24; review pending)

O1-O4 selected by user; this supersedes the earlier pending-contract entry.
`src/aoi_platform/pad_candidates.py` adds immutable bounded synthetic top-SMD/F.Cu
rectangle candidates from explicit mm/right/up proper-rigid maps. Input inventory
identity/hash and complete frame/scope are checked; repeated/empty pad numbers stay
unchanged. Source aliases reject; batch failure has no candidates. Association is
only declaration-consistent, not verified membership from source bytes. No reader,
BoardRevision, publication, targeting authority or native execution was added.

`tests/test_pad_candidates.py`: independent angle0/+90/45 corner oracles, context,
provenance, alias/identity, immutable/all-or-nothing behavior, malformed inputs,
exact/exceeded metadata/count/numeric limits and diagnostic reservation coverage.
Evidence: `evaluation/pad-candidate/evidence/canonical-pad-candidate-02/`.
Focused100 PASS (exit0); default full pytest470 PASS/1 skipped (exit0). The skip is
opt-in local REAL-PCB-01 inventory, not a passing real-fixture test. This default
suite uses testpaths=tests; historical evaluation/native suites were not rerun.
28 code/test/config hashes match before/after and current bytes; raw stdout/stderr
and argv/cwd/exit are preserved. Strict OpenSpec validation passed. Earlier run01
is retained as development evidence, not the final reviewed-code result. No rerun
was needed for packaging because the28 inputs still match. These are implementer
results; new candidate implementation awaits independent review.

Only a narrow `/evaluation/pad-candidate/** -text` attribute was added to preserve
new evidence bytes. No historical evidence or existing core guards were changed.
Tasks3.4/5.5/5.13 remain PARTIAL (this bounded candidate subset only); Tasks1.5/5.2
remain PARTIAL. General pad geometry, native association, full import/reconciliation,
canonical revision lifecycle and atomic publication remain open. InventorySuccess
is a trusted in-process result, not authentication or proof of design consistency.

Branch checkpoint/outline-inventory-repeated-pads; HEAD f77efa171cfb58e843e93ebbe6d16a0f30ab9358.
Index stays empty; pre-existing evaluation/document/untracked work is retained.
No native, commit or push. Next single action: review the canonical Pad candidate
ZIP and its isolated pre-implementation baseline/diffs before any further work.

## Canonical Pad candidate review accepted (2026-10-24)

User reports review PASS for the selected bounded candidate subset. Reviewer rerun:
470 passed, 1 skipped; 74/74 manifest hashes, 28/28 pre/post hashes and all six
baseline/diffs matched. Review package: aoi-canonical-pad-candidate-review-a3365c21c98c.zip.
This supersedes the review-pending status and review-next-action above; those entries
remain historical. These are reviewer results relayed by the user, not a new agent
rerun or an attestation.

Acceptance is limited to the selected synthetic top-SMD/F.Cu rectangle candidate
operation with explicit proper-rigid transforms and declaration-consistent association.
It does not verify native source membership, general geometry/parser compatibility,
BoardRevision publication, atomic publication, targeting or production accuracy.
The skipped local fixture test remains unverified by this rerun. Tasks 1.5/5.2 and
aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.

This update changes documentation only: no code/evidence edits, tests/native runs,
commit or push. Await explicit authorization for any next implementation or publishing.

## Repeated-pads replay bridge review accepted (2026-10-24; fixture-only)

User reports review PASS for aoi-repeated-pads-bridge-review-e3e1903f89b6.zip.
Reviewer rerun: 21 passed; 28/28 manifest hashes and 20/20 pre/post hashes matched.
These are reviewer results relayed by the user, not a new agent rerun or attestation.
The bridge's review-pending status is superseded by this fixture-only acceptance.
Evidence remains evaluation/kicad-reader/evidence/repeated-pads-bridge-01/.

Acceptance covers only the accepted repeated-pads replay: explicit normalization
N(x,y)=(x,-y), separate reflection evidence, caller-declared translation (0,20),
and inventory-bound PCB/raw observation hashes. Build/schema checks are value
checks, not backend authentication. Association remains declaration-consistent;
no general reader/geometry compatibility, native membership verification,
BoardRevision/publication, atomic publication, targeting or production accuracy
is established. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL.

Documentation-only acceptance update; no code/evidence changes, tests/native runs,
checkbox changes, commit or push. Await explicit authorization for further work.

## Portable Pad candidate control review accepted (2026-10-25)

User reports review PASS for aoi-pad-candidate-control-review-39b45b1cd14a.zip.
Reviewer rerun: 25 passed; 30/30 manifest hashes and 23/23 pre/post hashes matched.
These reviewer results were relayed by the user; no new agent rerun or attestation.
Evidence: evaluation/windows_runner/evidence/pad-candidate-control-portable-01/.

Acceptance covers portable orchestration with fake execution: forwarding the exact
execution stdout, no historical fallback, and blocking before bridge on transport
failure/timeout, unconfirmed cleanup or hash mismatch. It does not establish a
native runner/helper/probe-to-candidate end-to-end path or backend authenticity.
The repeated-pads fixture-only scope, declaration-consistent association and runner
host-crash gap remain. No general geometry/import compatibility, BoardRevision,
publication/atomic publication, targeting or production accuracy claim is made.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.

Documentation-only acceptance update; no code/evidence changes, tests/native runs,
commit or push. Further implementation or native execution requires authorization.

## Native callback review accepted (2026-10-25; portable only)

User reports PASS for aoi-pad-native-callback-review-74fa0a1b712d.zip: reviewer rerun
14 passed; 20/20 manifest hashes and 10/10 pre/post hashes matched. Tests used fake
Popen; native end-to-end execution, backend authenticity and complete containment
are not established. The existing host-crash gap remains open. Tasks 1.5/5.2 and
aggregate 3.4/5.5/5.13 remain PARTIAL. No geometry/publication scope expanded.

User explicitly authorized the related accepted checkpoint commit/push on the
current checkpoint branch, not master. Includes accepted UUID validation dependencies,
canonical Pad candidates, replay bridge, portable control/callback and reviewed evidence.
Unrelated historical evidence and agent integration files remain outside this checkpoint.
Two exact source/test -text rules preserve reviewed candidate bytes at staging.
No tests/native were rerun for this documentation/checkpoint operation.

## Native Pad candidate integration review accepted (2026-10-25; fixture-only)

User reports review PASS for aoi-pad-native-integration-review-f452dff5ba6c.zip.
Reviewer compared hashes, raw output, candidate oracle and cleanup evidence;
reviewer did not rerun native execution. This is user-relayed review acceptance,
not an independent native rerun or attestation.

Evidence: evaluation/windows_runner/evidence/pad-candidate-native-integration-01/.
Exactly one implementer native run connected NativeExecution -> control -> bridge
-> Pad candidates on the accepted repeated-pads fixture: 11/11 checks PASS,
root exit 0, transport 1750 ms, two candidates matching the oracle, input/output
hash binding, Job active_processes=0, cleanup cleaned and owned staging removed.
The earlier portable-only entries remain historical; this acceptance adds native
end-to-end evidence only for this pinned fixture and tested runtime.

Acceptance does not establish general geometry/parser compatibility, backend
authentication, independently verified source membership, BoardRevision publication,
atomic publication, targeting or production accuracy. Association remains
declaration-consistent. The suspended-CreateProcess-before-Job-assignment
host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL;
no checkbox changes. No code/evidence edits, tests/native reruns, commit or push
were performed for this acceptance update. Await authorization for further work.

## C1 portable rectangle review accepted (2026-10-26)

User reports review PASS for aoi-c1-rectangle-review-21f9943fc1a4.zip:
reviewer rerun 3 passed; 24/24 manifest hashes, 17/17 pre/post hashes and all
eight oracle corners matched. These are reviewer results relayed by the user,
not a new implementer rerun or attestation. Evidence remains
evaluation/kicad-reader/evidence/c1-rectangle-portable-03/.

Acceptance covers portable C1 rectangle candidate math from saved observation,
explicit same-datum P with translation (0,0), and reflection correspondence
(3,2,1,0). InventorySuccess is a trusted test double: PCB bytes_read and
actual_size are deliberately fake values of 1, not the source PCB size.
This does not verify real PCB byte admission, source membership/provenance,
native boundary vertices, strict-v2 import or real import. No publication or
targeting authority is established. The two earlier setup-failure runs remain
historical and unchanged. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL;
no checkbox changes. This acceptance update changes documentation only: no
code/evidence edits, tests/native runs, commit or push. Await further authorization.

## C1 real inventory integration review accepted (2026-10-26)

User reports review PASS for aoi-c1-real-inventory-review-d39b9d398bff.zip.
Reviewer obtained the PCB source with the recorded hash and reran 1 test PASS:
real inventory_artifacts byte admission, closed streams and all eight oracle
corners matched. All 26 manifest hashes and 19 inputs matched, including the
PCB supplied outside the ZIP. These are reviewer results relayed by the user,
not a new implementer rerun or attestation. Evidence remains
evaluation/kicad-reader/evidence/c1-real-inventory-portable-01/.

This separate integration uses actual PCB bytes (912379 bytes) and saved
observation bytes (196715 bytes), not the earlier inventory test double or fake
PCB size 1. The earlier portable acceptance and its limitations remain historical
and unchanged. Acceptance covers byte admission and the selected C1 candidate
math with explicit same-datum P, translation (0,0), and correspondence (3,2,1,0).
It does not establish source membership, backend authenticity, native boundary
vertices, strict-v2 observation/import, general real import, BoardRevision or
atomic publication, targeting, or production accuracy. Association remains
declaration-consistent; no native execution was part of this integration test.
The existing runner host-crash gap remains open. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL; no checkbox changes. This acceptance update changes
documentation only: no code/evidence edits, tests/native runs, commit or push.
Await explicit authorization for further work.


### 2026-10-26 - C1 comparator runtime-validation fix review accepted

User relayed review PASS for aoi-c1-boundary-fix-review-2e78c6182476.zip:
reviewer reran 23 portable tests successfully, including three Python -O
subprocess regressions (wrong build, open contour, and hole rejection).
All 18 manifest hashes and six pre/post-run hashes matched. Acceptance covers
explicit comparator runtime validation in place of assertions and its portable
regressions. These are reviewer results reported by the user, not a new
implementer rerun or an attestation. Evidence remains
`evaluation/kicad-reader/evidence/c1-boundary-portable-02/`.

The separate C1 boundary probe has NOT been run native. Portable comparator
acceptance does not establish native copper-boundary verification, backend
identity, general geometry/import support, publication or targeting authority.
Oracle, tolerance, probe and historical evidence remain unchanged. The runner
host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain
PARTIAL; no checkbox changes. This update changes documentation only: no
code/evidence edits, tests/native runs, commit or push. Await explicit
authorization for further work.


### 2026-10-26 - C1 native boundary review accepted (two C1/F.Cu pads only)

User relayed review PASS for aoi-c1-boundary-native-review-e2fa6c097b7f.zip.
Reviewer replayed saved raw output: all eight oracle corners matched exactly
(0 IU deviation); all 24 manifest hashes and 12 inputs matched. Reviewer did
NOT rerun native KiCad. These are reviewer results reported by the user, not
an additional implementer run or an attestation. Evidence remains
`evaluation/windows_runner/evidence/c1-boundary-native-01/`.

Acceptance covers only the two C1/F.Cu pad boundaries from the single recorded
native control, including raw polygon correspondence to the independent oracle.
The saved control reports successful transport, confirmed cleanup with Job
active processes 0, staging removal and unchanged fixture/input hashes.
The earlier statement that the probe had not run native is historical and is
superseded by this recorded control; no historical evidence is changed.

This does not establish other pads/layers, general geometry/import support,
backend authenticity or full dependency pinning, canonical publication,
targeting authority or production accuracy. The runner host-crash gap remains
open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
This acceptance update changes documentation only: no code/evidence edits,
tests/native runs, commit or push. Await explicit authorization for further work.


### 2026-10-27 - Pinned C1 replay flow review accepted

User relayed review PASS for aoi-c1-replay-flow-review-03f2cb9ff26b.zip.
Reviewer reran the portable tests with the real matching PCB: 25 passed.
All 31 manifest hashes and 24 inputs matched, including the PCB outside the
ZIP. These are reviewer results reported by the user, not a new implementer
rerun or an attestation. Evidence remains
`evaluation/kicad-reader/evidence/c1-replay-flow-portable-01/`.

Acceptance covers the evaluation-only pinned replay for exactly two C1/F.Cu
pads: real byte admission of PCB, legacy observation, boundary output and
report/transport; post-admission gates; candidate/oracle/boundary comparison.
The five hash/size pins remain fixed. Legacy is not upgraded to strict-v2.
Private post-admission gate tests deliberately use mutated in-memory payloads
with an unmodified positive inventory; these are test doubles, not evidence
that changed payloads pass the public hash gates. Candidate API failure also
uses a test double. Real hash-gate tests remain distinct.

No native execution was part of this replay test run. Hash binding establishes
consistency with pinned evidence, not backend authenticity or full dependency
pinning. Acceptance does not establish arbitrary-board import, other pads or
layers, general geometry, BoardRevision/publication or targeting authority.
Candidates remain unpublished with declaration-consistent association. The
runner host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13
remain PARTIAL; no checkbox changes. This update changes documentation only:
no code/evidence edits, tests/native runs, commit or push. Await explicit
authorization for further work.


### 2026-10-27 - C1 strict control identity-fix review accepted (fake execution)

User relayed review PASS for aoi-c1-strict-identity-review-be1c9bce130e.zip.
Reviewer reran 50 portable tests successfully; all 41 manifest hashes and 29
inputs matched. Each of the three current-execution identity mismatches
(artifact_id, source_id, policy_id) was blocked before observation gates.
These are reviewer results reported by the user, not a new implementer rerun
or an attestation. Final evidence remains
`evaluation/kicad-reader/evidence/c1-strict-control-portable-03/`.
Portable-02 remains historical evidence from before the patch was applied;
its 47-test result is not evidence for the identity fix.

Acceptance is evaluation-only and limited to fake execution: exact stdout
forwarding, strict-v2 validation without legacy opt-in, distinct current
observation versus historical boundary transports, and identity rejection
without candidates. No native end-to-end execution of this strict control has
been demonstrated. PCB and historical boundary pins, legacy replay, oracle
and normalization remain unchanged. No general import, complete geometry,
backend authenticity, BoardRevision/publication or targeting authority claim.
The runner host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13
remain PARTIAL; no checkbox changes. This acceptance update changes only
documentation: no code/evidence edits, tests/native runs, commit or push.
Await explicit authorization for further work.


### 2026-10-27 - C1 strict-v2 native control review accepted (C1/F.Cu only)

User relayed review PASS for aoi-c1-strict-native-review-a1d6b8e47ce8.zip.
Reviewer replayed offline through schema, inventory and boundary checks:
two candidates and all eight oracle corners matched. All 47 manifest hashes
and 33 inputs matched. Reviewer did NOT rerun native KiCad. These are reviewer
results reported by the user, not a new implementer rerun or an attestation.
Evidence remains `evaluation/windows_runner/evidence/c1-strict-native-01/`.

Acceptance covers only the recorded single native strict-v2 control for the
two pinned C1/F.Cu pads, with current observation transport kept separate from
historical boundary transport. No legacy fallback was used. The earlier
fake-execution-only limitation remains historical for those portable tests;
this recorded native control now provides limited end-to-end evidence for C1.
Historical code/evidence, PCB/boundary pins, oracle and tolerance are unchanged.

This does not establish arbitrary-board import, other pads/layers, complete
geometry, backend authenticity or full dependency pinning, BoardRevision or
atomic publication, targeting authority or production accuracy. Candidates
remain unpublished with declaration-consistent association. The runner
host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain
PARTIAL; no checkbox changes. This acceptance update changes documentation
only: no code/evidence edits, tests/native runs, commit or push. Await explicit
authorization for further work.

### 2026-10-27 - C2 real-inventory portable review accepted

User relayed review PASS for aoi-c2-real-inventory-review-75a44ae909cf.zip.
Reviewer reran with the real PCB: 1 passed; all eight oracle corners,
35 manifest hashes and 19 inputs matched. The strict-v2 observation matched
the previously accepted C1 native artifact at
`evaluation/windows_runner/evidence/c1-strict-native-01/stdout.bin`.
These are reviewer results reported by the user, not a new implementer run
or an attestation. Portable evidence remains
`evaluation/kicad-reader/evidence/c2-real-inventory-portable-02/`;
the initial encoding/collection failure in portable-01 remains historical.

Acceptance covers only the two C2 pads in the real-inventory portable test,
using the source-derived C2 oracle and saved strict-v2 observation. No legacy
payload upgrade or inventory test double is used. C2 native copper boundary
has NOT been verified; C1 native boundary acceptance does not extend to C2.
This does not establish general import, complete geometry, publication or
targeting authority. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL;
no checkbox changes. Historical evidence and existing limitations remain
unchanged. This update changes documentation only: no code/evidence edits,
tests/native runs, commit or push.

### 2026-10-27 - C2 boundary portable review accepted

User relayed review PASS for aoi-c2-boundary-review-0be117dff9b0.zip.
Reviewer reran 23 tests: all passed; 15 manifest hashes, six pre/post inputs
and all eight oracle IU corners matched. These are reviewer results reported
by the user, not a new implementer run or an attestation. Evidence remains
`evaluation/kicad-reader/evidence/c2-boundary-portable-01/`.

Acceptance covers the C2/F.Cu portable comparator subset, including
cyclic/reversed correspondence, invalid geometry/topology rejection and
Python -O rejection checks. The C2 probe has NOT run native; no C2 native
copper boundary verification is claimed. Existing C1 flows and historical
evidence remain unchanged. This does not establish general geometry/import,
publication or targeting authority. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13
remain PARTIAL; no checkbox changes. Documentation-only acceptance update:
no code/evidence edits, tests/native runs, commit or push.

### 2026-10-28 - C2 native boundary review accepted (C2/F.Cu only)

User relayed review PASS for aoi-c2-boundary-native-review-f1db1fab8c25.zip.
Reviewer replayed raw output and confirmed all eight oracle corners matched
exactly (0 IU difference); 24 manifest hashes and 12 inputs matched. Reviewer
did NOT rerun native KiCad. These are reviewer results reported by the user,
not a new implementer run or an attestation. Evidence remains
`evaluation/windows_runner/evidence/c2-boundary-native-01/`.

Acceptance is limited to the two pinned C2/F.Cu pad boundaries in the recorded
single native control. The earlier portable-review statement that the C2 probe
had not run native is historical and superseded only within this limited scope.
No general geometry/import, other pads/layers, canonical geometry, publication
or targeting authority is established. The runner host-crash gap remains open.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
C1 flows and historical evidence remain unchanged. Documentation-only update:
no code/evidence edits, tests/native runs, commit or push.

### 2026-10-28 - Pinned C2 replay review accepted

User relayed review PASS for aoi-c2-replay-flow-review-0004a68d1635.zip.
Reviewer reran with the real PCB: 26 passed; 34 manifest hashes and 26 inputs
matched. Observation and boundary matched the previously accepted artifacts.
These are reviewer results reported by the user, not a new implementer run or
an attestation. Evidence remains
`evaluation/kicad-reader/evidence/c2-replay-flow-portable-01/`.

Acceptance covers only the pinned two-pad C2/F.Cu evaluation replay with real
inventory, saved strict-v2 observation, historical C2 boundary/report/transport,
source-derived oracle and candidate comparison. Private-gate test doubles remain
distinct from actual byte-admission/hash-gate tests; they do not demonstrate
altered artifacts passing real admission. This is not a new native execution,
arbitrary-board import, publication or targeting authority. The runner
host-crash gap remains open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain
PARTIAL; no checkbox changes. C1 flows and historical evidence remain unchanged.
Documentation-only acceptance update: no code/evidence edits, tests/native
runs, commit or push.

### 2026-10-28 - Pinned C1+C2 replay batch review accepted

User relayed review PASS for aoi-c1-c2-batch-review-1c1ce42e15bb.zip.
Reviewer reran with the real PCB: 29 passed; 40 manifest hashes and 32 inputs
matched. Four pads, all 16 oracle corners and all-or-nothing behavior passed.
These are reviewer results reported by the user, not a new implementer run or
an attestation. Evidence remains
`evaluation/kicad-reader/evidence/c1-c2-replay-batch-portable-01/`.

Acceptance covers only the pinned C1+C2/F.Cu evaluation replay: eight artifacts,
two boundary gates and one candidate API call for four pads, using a common
normalized native-board datum, P translation (0,0) and one unpublished scope.
Private-gate test doubles remain distinct from real hash-admission tests.
This does not establish new native execution, arbitrary-board import, general
geometry, publication or targeting authority. The runner host-crash gap remains
open. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.

Deferred documentation fix for the next authorized code turn:
`evaluation/kicad-reader/c1_c2_replay_batch.py` still opens with the stale
"Pinned C2 replay only" docstring. Its actual profile and behavior cover C1+C2.
Do not change these reviewed bytes in this acceptance-only update. Existing
flows and historical evidence remain unchanged. Only HANDOFF and implementation
status updated; no code/evidence edits, tests/native runs, commit or push.

### 2026-10-29 - Boundary preflight review accepted (preflight only)

User relayed review PASS for aoi-boundary-preflight-review-03b1c504fae4.zip.
Reviewer reran 60 tests: all passed; 37 manifest hashes and 18 inputs matched.
These are reviewer results reported by the user, not a new implementer run or
an attestation. Evidence remains
`evaluation/kicad-reader/evidence/boundary-preflight-portable-03/`;
historical runs 01/02 remain unchanged.

Acceptance covers immutable records, exact policy validation and joint bounded
preflight only. The result is preflight-only-not-bound, with no candidates;
geometry matching, artifact-to-record binding and candidate API execution are
not implemented by this slice. Source membership/construct coverage remain
unverified; no import readiness, publication or targeting authority is granted.
Budget primitive tests exercise counters/traversal boundaries; they are NOT
full-batch admission evidence for a complete valid maximum-size request.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Existing limitations, code and historical evidence remain unchanged. Only
HANDOFF and implementation status updated; no code/evidence edits, tests/native
runs, commit or push.

### 2026-10-29 - Boundary declaration binding review accepted

User relayed review PASS for aoi-boundary-whitespace-id-review-62d4c7ec6788.zip:
reviewer reran 114 tests, all passed; 37 manifest hashes and 19 inputs matched.
Review covers declaration binding, successful/consistent inventory validation,
nested-record validation and exact opaque-ID diagnostics, including whitespace.
These are reviewer results reported by the user, not a new implementer run or
an attestation. Evidence: evaluation/kicad-reader/evidence/boundary-binding-opaque-02/.
The six failures in opaque-01 were test setup errors; all historical logs remain
unchanged, including the earlier inventory/nested-record reproduction evidence.

This acceptance extends the earlier preflight-only milestone with identity,
artifact/hash and full-frame/context declaration binding. Status remains
`declaration-binding-only-no-geometry-check`; no candidates are returned.
Artifact-to-record association remains `supplied-declaration-unverified`;
source membership and construct coverage are not verified. Geometry matching
and candidate API execution remain unimplemented by this slice. No import
readiness, publication, targeting authority or complete geometry is established.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Only HANDOFF and implementation status updated. No code/evidence changes,
tests/native runs, commit or push.

### 2026-11-02 - Boundary correspondence review accepted (correspondence only)

User relayed review PASS for aoi-boundary-correspondence-review-65f5e272779d.zip:
reviewer reran 28 tests, all passed; 37 manifest hashes and 18 inputs matched.
These are reviewer results reported by the user, not a new implementer run or
an attestation. Evidence remains
`evaluation/kicad-reader/evidence/boundary-correspondence-portable-03/`.
Historical runs 01/02 and their test-data floating-point failures remain intact.

Acceptance is correspondence-only: bounded finite four-vertex contours in P,
topology/adjacency checks, raw order preserved and exactly one of eight
cyclic/reversed mappings within synthetic tolerance. No-match and ambiguous
mapping remain distinct. This is not rectangle admission or binding/candidate
execution; it grants no source verification, import readiness or targeting.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Only HANDOFF and implementation status updated; no code/evidence changes,
tests/native runs, commit or push.

### 2026-11-02 - Boundary orchestration implemented, awaiting review

Added boundary_binding.py and test_boundary_orchestration.py. Declaration binding
must pass before one candidate API call for the complete batch. Explicit proper-
rigid boundary transforms are checked and applied into P, then correspondence is
checked per pad. Any failed phase returns no candidates; no partial batch success.
Rectangle admission comes from the existing candidate API, not convex contours.
Coverage records/unknown categories and unverified assurance are preserved.

Implementer run: boundary-orchestration-portable-01, 151 passed (exit 0): nine new
orchestration cases plus binding/preflight/correspondence regressions. Raw logs,
argv/cwd and unchanged pre/post code/input hashes are in
`evaluation/kicad-reader/evidence/boundary-orchestration-portable-01/`.
Independent review is pending. No native/full suite run, ZIP, commit or push.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. No source-membership
verification, publication, targeting authority or general import claim.

### 2026-11-04 - Boundary orchestration static review accepted

User relayed static review PASS for aoi-boundary-orchestration-review-11041a814eb4.zip:
31 manifest hashes, 23 inputs and 21 baseline files matched. The 151 PASS result
is from the saved implementer log, not a reviewer rerun. Reviewer did not rerun
the tests. This records the user's report of review, not an attestation or a new
verification run. Evidence remains
`evaluation/kicad-reader/evidence/boundary-orchestration-portable-01/`.
The earlier orchestration "awaiting review" / "review is pending" statements
are historical and superseded by this scoped static-review acceptance.

Acceptance covers declaration binding followed by one candidate batch call,
explicit boundary transformation to P and per-pad correspondence, with no
candidates returned on failure. Assurance remains declaration-consistent;
coverage, source membership and artifact-to-record association are unverified.
No import readiness, publication, targeting authority or general import support
is established. Rectangle admission relies on the existing candidate API, not
convex-contour detection. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL;
no checkbox changes. Historical evidence remains unchanged.

Only HANDOFF and implementation status updated; diff --check run. No code/evidence
changes, tests/native runs, commit or push.

### 2026-11-04 - C1+C2 boundary integration static review accepted

User relayed static review PASS for aoi-c1-c2-binding-integration-review-3ea971408b22.zip:
43 manifest hashes and 36 inputs matched, including REAL-PCB-01-r2 PCB outside
that ZIP. The 2 PASS result is from the saved implementer log; reviewer has not
rerun the tests. This records review reported by the user, not an attestation
or a new verification run. Evidence remains
`evaluation/kicad-reader/evidence/c1-c2-binding-integration-01/`.

Acceptance is limited to the pinned C1+C2 portable integration: real artifact
inventory, four pads / 16 oracle corners, and all-or-nothing rejection when a C2
boundary declaration is changed in memory after hash admission. That negative
case does not change admitted artifact bytes or verify artifact-to-record
membership. Results remain declaration-consistent; source membership and
coverage remain unverified. No general import readiness, publication, targeting
authority or new native boundary verification is established.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Only HANDOFF and implementation status updated; diff --check run. Historical
code/evidence remain unchanged. No tests/native runs, commit or push.

### 2026-11-04 - C1+C2 artifact consistency static review accepted

User relayed static review PASS for aoi-c1-c2-artifact-binding-review-8bb969704d13.zip:
45 manifest hashes and 38 inputs matched, including the PCB outside the ZIP.
The 11 PASS result is from the saved implementer log; reviewer has not rerun
the tests. This records review reported by the user, not an attestation or a
new verification run. Evidence remains
`evaluation/kicad-reader/evidence/c1-c2-artifact-binding-portable-01/`.

Acceptance is limited to consistency with pinned C1+C2 observation/boundary
artifacts. The changed C2 vertex declaration is rejected before binding, with
no candidates and diagnostic artifact/hash, parent/pad UUID and expected/actual.
The negative case changes only a declaration in memory after hash admission;
original artifact bytes remain unchanged. Source membership and completeness
remain unverified. This does not establish general import readiness, publication,
targeting authority or new native execution evidence.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Only HANDOFF and implementation status updated; diff --check run. Historical
code/evidence remain unchanged. No tests/native runs, commit or push.


### 2026-11-05 - C1+C2 source membership scanner: blocked, not accepted

Added evaluation-only c1_c2_source_membership.py and its portable test file.
The iterative scanner checks the fixed r2 size/hash before parsing, enforces
128 nesting levels / 65536 token bytes / 500000 tokens, and scans through EOF.
It retains selected pad spans/lines and checks direct ownership and explicit fields.
No existing helper, product code, fixture or historical evidence was changed.

Implementer run: 29 passed, 5 failed (exit 1), with 40 pre/post input hashes
unchanged. Evidence: evaluation/kicad-reader/evidence/c1-c2-source-membership-portable-01/.
The five real-input cases are blocked before binding: the scanner's global UUID
uniqueness check encounters UUID 0ae7c3ce-ceb0-44ab-be65-2ff0efa576c2 twice in the
pinned PCB, at line 15576 (dimension) and line 15600 (its nested gr_text).
See source-duplicate-audit.json; source SHA-256 remains
67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0.
These are outside the four target pads. No expectation, source bytes or hash was
changed to obtain a pass. Full requested positive membership/binding evidence is
NOT established, and the changed-parent negative does not yet reach its intended
gate on the real PCB. Next single action: decide the UUID uniqueness namespace
(footprint/pad nodes versus all UUID-bearing nodes), then adjust only if authorized.
Completeness/effective copper geometry remain unverified; Tasks 1.5/5.2 and
aggregate geometry/import tasks remain PARTIAL. This is unreviewed work in progress.
No native/full suite, ZIP, commit or push. git diff --check passed.


### 2026-11-05 - C1+C2 source UUID namespace scoped; portable verification

User explicitly selected one shared UUID-identity uniqueness namespace: UUID
fields directly owned by every footprint directly under kicad_pcb and every pad
directly under those footprints. Nonselected footprints/pads are included. Other
UUID-bearing nodes (including dimension and its gr_text) are outside uniqueness;
syntax, direct UUID field validation, ancestry, EOF traversal and depth/token
limits remain enforced. This supersedes the pending scope decision above without
changing historical evidence or the pinned PCB.

Updated evaluation/kicad-reader/c1_c2_source_membership.py and its test file.
Regression covers cross-footprint pad collisions, footprint/pad collisions,
footprint/footprint collisions, equivalent UUID spelling, nonselected duplicates
at EOF, and dimension/gr_text shared UUID outside the namespace.
Implementer result: 37 passed in 1.82s, exit 0 (28 scanner/integration cases and
9 existing artifact-binding cases). Evidence:
`evaluation/kicad-reader/evidence/c1-c2-source-membership-portable-02/`.
All 40 pre/post input hashes match; portable-01 (29 PASS / 5 FAIL) remains
byte-identical. Real r2 positive reaches binding once, four candidates and all
16 oracle corners; changed-parent declaration returns SOURCE_CONFLICT before
the artifact/binding path, preserving expected/actual parent, pad UUID, source
hash and source span, without candidates. PCB pin remains unchanged.

This is implementer evidence, not independent review acceptance. Source membership
and explicit fields are checked only for the four pinned C1+C2 pads. Construct
completeness and effective copper geometry remain unverified; product assurances
are not upgraded. Tasks 1.5/5.2 and aggregate tasks remain PARTIAL. Next action:
review this scoped scanner change and new evidence. No native/full suite, ZIP,
commit or push. git diff --check passed.


### 2026-11-05 - C1+C2 source membership scanner static review accepted

User relayed static review PASS for aoi-c1-c2-source-membership-review-6c0de141bbe3.zip:
54 manifest hashes and 40 inputs matched, including the PCB outside the ZIP.
The 37 PASS result is from the saved implementer log; reviewer has not rerun
these tests. This records the review reported by the user, not an attestation
or a new verification run. It supersedes the review-pending wording above.
Evidence: evaluation/kicad-reader/evidence/c1-c2-source-membership-portable-02/.
The 29 PASS / 5 FAIL run and source-duplicate-audit.json in portable-01 remain
unchanged historical evidence of the earlier global-UUID scope.

Accepted uniqueness uses one shared namespace for direct UUID fields of every
footprint directly under kicad_pcb and every pad directly under those footprints,
including nonselected footprint/pad records. Dimension/gr_text and other nodes
are outside that uniqueness namespace; ancestry, syntax, EOF and scanner budgets
remain checked. The changed-parent declaration is rejected as SOURCE_CONFLICT
before binding, without candidates, retaining expected/actual parent, pad UUID,
source hash and span.

Acceptance covers source membership and explicit fields of only the four pinned
C1+C2 pads. Construct completeness and effective copper geometry remain unverified;
no general importer, import readiness, publication or targeting authority is
established. Product assurances remain unchanged. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL; no checkbox changes.
Only HANDOFF and implementation status updated; git diff --check passed.
No code/evidence changes, tests/native runs, commit or push.


### 2026-11-05 - C1+C2 explicit modifier declaration screen (unreviewed)

Extended evaluation/kicad-reader/c1_c2_source_membership.py and its portable tests.
The fixed inspected paths, relative to a pad directly below a board-level
footprint, are: pad/drill, pad/offset, pad/drill/offset, pad/padstack,
pad/padstack/layer, pad/layer, pad/primitives and pad/options. These are a finite
presence screen, not a complete KiCad grammar or an assertion of effective values.
model/offset and zone_connect are excluded. Product code and prior flows unchanged.

Every selected pad records present/absent for each path, first half-open byte span,
one-based source lines when present, and occurrence count. Storage retains only
the first occurrence per path; traversal still observes all tokens through EOF
under the existing depth/token budgets. Any listed presence is rejected as
GEOMETRY_UNSUPPORTED before binding; failure contains diagnostic source records,
never candidates. The real entrypoint still checks exact PCB size/hash first.
Synthetic scanner diagnostics use the synthetic bytes' actual hash, not the pin.

Implementer evidence: evaluation/kicad-reader/evidence/c1-c2-modifiers-portable-01/.
49 passed in 1.96s, exit 0; all 40 pre/post hashes unchanged. Both the source
membership tests and existing artifact-binding tests ran. Real pinned r2 has all
eight paths absent in all four pads, reaches binding once and retains the four
candidates / 16-corner oracle check. Private synthetic drill-with-offset returns
GEOMETRY_UNSUPPORTED; a failure-only test double verifies early propagation before
binding. This does not admit synthetic bytes past the real pin (separate rejection
test). model/offset and zone_connect exclusion and EOF syntax rejection are tested.

Result concerns only presence of the listed explicit declarations. Completeness,
effective copper geometry and zone-fill effects remain unverified; product
assurances are unchanged. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL.
Historical evidence remains intact. Next action: review this modifier slice.
No native/full suite, ZIP, commit or push. git diff --check passed.


### 2026-11-05 - C1+C2 modifier declaration screen static review accepted

User relayed static review PASS for aoi-c1-c2-modifiers-review-306bbf8ac908.zip:
52 manifest hashes, 40 inputs (including the PCB outside the ZIP), two baseline
files and two diffs matched. The 49 PASS result is from the saved implementer
log; reviewer has not rerun the tests. This records user-relayed review, not an
attestation or a new verification run. Earlier unreviewed/review-pending wording
for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/c1-c2-modifiers-portable-01/.

Acceptance covers only presence of eight ancestry-specific paths in the four
pinned C1+C2 pads: pad/drill, pad/offset, pad/drill/offset, pad/padstack,
pad/padstack/layer, pad/layer, pad/primitives and pad/options. model/offset and
zone_connect remain separate from this screen.
The real pinned PCB case records all eight paths absent and passes binding with
four candidates / 16 oracle corners. Private-scanner synthetic drill/offset
bytes produce GEOMETRY_UNSUPPORTED. A failure-only test double checks propagation
before binding; it does not demonstrate admission of modified bytes through the
real hash gate or native execution. These evidence types remain distinct.

Construct completeness, effective copper geometry and zone-fill effects remain
unverified; no general import readiness, publication or targeting authority is
established. Product assurances are unchanged. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL; historical evidence and checkboxes remain unchanged.
Only HANDOFF and implementation status updated; git diff --check passed.
No code/evidence changes, tests/native runs, commit or push.


### 2026-11-05 - C1+C2 source pose/size gate (unreviewed)

Extended c1_c2_source_membership.py to retain direct footprint/at, pad/at and
pad/size literals, half-open byte spans and source lines (at most two occurrences
to detect duplicates). Added evaluation/kicad-reader/c1_c2_source_pose.py and
its portable tests. The gate runs before artifact/binding execution. Missing,
duplicate, nested/quoted numeric fields, malformed/nonfinite values, nonpositive
sizes and noncardinal angles reject explicitly. Evaluation numeric subset uses
plain decimal literals of at most 64 characters (no exponent), existing magnitude
bounds 1e6 and angle bound +/-360000 degrees. No source defaults are inferred.

Decimal cardinal arithmetic computes C=F+K(theta)*local once; pad alpha is world
orientation, not theta+alpha. Source corners use C+K(alpha)*q, then N(x,y)=(x,-y)
once. Existing normalized native-board datum / P translation (0,0) and source to
candidate correspondence (3,2,1,0) are retained. Expected geometry comes only from
source declarations; observation and candidate API do not generate the oracle.
Coordinates/size compare at 1 nm; raw angles compare exactly. This is synthetic
fixture evaluation, not a general import or production accuracy claim.

Evidence: evaluation/kicad-reader/evidence/c1-c2-source-pose-portable-01/.
Implementer result: 68 passed in 2.37s, exit 0; all 42 pre/post input hashes match.
Ran new pose tests plus membership/modifier and artifact-binding regression files.
Four source-derived centers/raw angles/sizes agree with strict-v2 observation;
16 Decimal corners agree with independent C1/C2 oracles within 1 nm. A memory-only
C2 request center.x increase of 0.001 mm returns SOURCE_CONFLICT before binding,
without candidates, preserving UUID/hash, pad and pose-field spans, expected/actual.
PCB and other artifact bytes remain unchanged. No native execution or full suite.

Scope is declared pose/size of the four pinned pads. Completeness, effective copper
geometry and zone-fill effects remain unverified; no publication or targeting
claim. Tasks 1.5/5.2 and aggregate tasks remain PARTIAL. Historical evidence intact.
Next action: review the pose gate and portable evidence. No ZIP, commit or push.
git diff --check passed.


### 2026-11-05 - C1+C2 source pose/size static review accepted

User relayed static review PASS for aoi-c1-c2-source-pose-review-11e7ef6d53b1.zip:
52 manifest hashes, 42 inputs (including the PCB outside the ZIP), the scanner
baseline and its diff matched. The 68 PASS result is from the saved implementer
log; reviewer has not rerun the tests. This records user-relayed review, not an
attestation or a new verification run. Earlier unreviewed/review-pending wording
for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/c1-c2-source-pose-portable-01/.

Acceptance is limited to declared pose/size of the four pinned C1+C2 pads, using
the bounded Decimal cardinal subset. Coordinate/size tolerance is 1 nm; raw angles
compare exactly. Footprint rotation places the local center once, pad angle is
world orientation, and Y normalization occurs once with correspondence (3,2,1,0).
The memory-only C2 center.x deviation is rejected before binding without candidates.

Construct completeness, effective copper geometry and zone-fill effects remain
unverified; no general import readiness, publication or targeting authority is
established. Product assurances are unchanged. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL; historical evidence and checkboxes remain unchanged.
Only HANDOFF and implementation status updated; git diff --check passed.
No code/evidence changes, tests/native runs, commit or push.

### 2026-11-05 - Selected C1+C2 pad ancestry coverage (review pending)

Evaluation-only change in c1_c2_source_membership.py and new
test_c1_c2_pad_coverage.py. Every child/descendant
of the four pinned pads is retained as an immutable path/value/span/line record.
The existing depth 128, token 64 KiB and 500,000-token limits bound traversal and
storage; the real source still requires exact PCB size/hash before scanning.
No footprint coverage or product importer changes.

Supported paths below are relative to kicad_pcb/footprint/pad and are LEAVES;
no known parent implicitly permits any descendant:
- uuid: one direct UUID value, existing UUID validation/uniqueness/membership.
- at: one direct field, three unquoted numeric literals; existing bounded Decimal
  cardinal gate, no nested values; required by the pose gate.
- size: one direct field, two positive unquoted numeric literals; existing pose gate.
- layers: one nonempty direct list of layer values, existing observation comparison.
- net, pintype, zone_connect: optional, at most one occurrence each, exactly one
  atom/string value, no descendants. Values/spans retained as semantics-unchecked;
  electrical and zone-fill behavior are NOT evaluated.
The eight existing modifier paths remain presence-blocked. All other paths fail
GEOMETRY_UNSUPPORTED before binding, retaining source hash, parent/pad UUID,
full ancestry path and offending node span/lines. Selected uuid/layers descendant
errors are deferred until EOF coverage can report the exact unsupported path;
nonselected structural rejection remains. No nested semantics are admitted.
Model 3D/offset outside the selected pads is not confused with pad modifiers.

Evidence: evaluation/kicad-reader/evidence/c1-c2-pad-coverage-portable-02/.
Implementer: 86 passed in 2.62s, exit 0; 43 pre/post input hashes unchanged.
Ran only coverage, source-pose, source-membership and artifact-binding test files.
The first run (portable-01: 84 passed) is preserved; portable-02 adds explicit
unknown-descendant regressions beneath uuid/layers and the diagnostic ordering fix.
Real PCB positive yields four candidates/16 oracle corners. Synthetic unknown-node
cases exercise the private scanner; real pin admission rejects synthetic bytes.
A failure-only test double proves early propagation before preflight/binding;
it is not evidence that altered PCB bytes pass hash admission.

This is implementer evidence, not review acceptance. Scope is declarations inside
four selected pads only. Footprint coverage, construct completeness, effective
copper and zone-fill semantics remain unverified. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL. No native/full suite, ZIP, commit or push.
Next action: review this coverage slice and its saved portable evidence.

### 2026-11-05 - C1+C2 pad coverage static review accepted

User relayed static review PASS for aoi-c1-c2-pad-coverage-review-5b271f9fd9d3.zip:
60 manifest hashes, 43 inputs (including the PCB outside the ZIP), the byte-exact
scanner baseline and its diff matched. The 86 PASS result is from the saved
implementer log; reviewer has not rerun the tests. This records user-relayed
review, not an attestation or a new verification run. Review-pending wording in
the preceding slice entry is historical and superseded by this acceptance.

Both evidence runs remain unchanged: c1-c2-pad-coverage-portable-01 records 84 PASS;
c1-c2-pad-coverage-portable-02 records 86 PASS. The two added cases cover unknown
descendants beneath uuid and layers, with the selected-pad diagnostic ordering
fix so coverage reports the unsupported ancestry path after EOF. Historical
recorded hashes and evidence have not been rewritten.

Acceptance covers descendants inside the four pinned C1+C2 pads only. net,
pintype and zone_connect retain values/spans with semantics-unchecked status.
Real PCB admission/binding, private synthetic scanner tests and failure-only
early-blocking test doubles remain distinct; doubles do not establish hash
admission for modified bytes. Footprint coverage, construct completeness,
effective copper geometry and zone-fill semantics remain unverified. No general
import readiness, publication or targeting authority is established.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; checkboxes unchanged.
Only HANDOFF and implementation status updated; no code/evidence changes,
tests/native runs, commit or push. Next implementation requires separate scope.

### 2026-11-06 - C1+C2 footprint layer/attr gate (review pending)

Evaluation scanner now retains direct footprint/layer and footprint/attr values,
raw literal bytes, byte spans and line spans for the two selected parents. Exactly
one leaf layer F.Cu and one leaf attr smd are required; missing/duplicate fields
fail SCHEMA_INVALID, unsupported values/extra attr flags/descendants fail
GEOMETRY_UNSUPPORTED before preflight/binding. At most two occurrences per field
are retained to detect duplicates, under existing scanner budgets. The source
layer is compared with the pinned observation footprint layer (SOURCE_CONFLICT
on disagreement). No inference from pad layers or native attribute integer.
Other footprint nodes are outside this gate; no whole-footprint coverage claim.

Changed c1_c2_source_membership.py; added test_c1_c2_footprint_fields.py.
Evidence: evaluation/kicad-reader/evidence/c1-c2-footprint-fields-portable-01/.
Implementer portable run: 98 passed in 3.30s, exit 0; 44 pre/post hashes unchanged.
Only footprint-fields, pad-coverage, source-pose, source-membership and
artifact-binding test files ran. Real r2 positive retains four candidates and
16 oracle corners. Synthetic B.Cu/extra attr, missing/duplicate/empty fields and
nested descendants reject. Scanner-record test doubles prove the downstream
field gate blocks before binding, not real hash admission; actual scan_pinned
rejects synthetic bytes. Nested model fields/unselected footprints are excluded.

Scope remains two declared fields of C1+C2 only. Broader footprint coverage,
construct completeness, effective copper and zone-fill semantics remain open.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. Existing evidence unchanged.
No native/full suite, ZIP, commit or push. Next action: review this slice/evidence.

### 2026-11-06 - C1+C2 footprint layer/attr static review accepted

User relayed static review PASS for aoi-c1-c2-footprint-fields-review-97e1d5568e82.zip:
54 manifest hashes, 44 inputs including the PCB outside the ZIP, the byte-exact
scanner baseline and its diff matched. The 98 PASS result comes from the saved
implementer log; reviewer has not rerun the tests. This records user-relayed
review, not an attestation or a new verification run. Earlier review-pending
wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/c1-c2-footprint-fields-portable-01/.

Acceptance covers only direct footprint/layer and footprint/attr of the two
pinned C1+C2 footprints. Real PCB admission with four candidates/16 oracle corners,
private synthetic scanner cases, and scanner-record test doubles remain distinct.
Test doubles demonstrate downstream early blocking, not real hash admission for
altered bytes. Broader footprint coverage, construct completeness, effective
copper geometry and zone-fill semantics remain unverified. No general import
readiness, publication or targeting authority is established.
Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; checkboxes unchanged.
Historical evidence is preserved. Only HANDOFF and implementation status updated;
no code/evidence changes, tests/native runs, commit or push.

### 2026-11-06 - C1+C2 non-pad footprint descendant coverage (review pending)

Updated evaluation scanner c1_c2_source_membership.py and added
test_c1_c2_footprint_coverage.py. Exact full ancestry paths from the two pinned
footprint source blocks are enumerated in FOOTPRINT_PATHS; known parents never
admit unknown children by prefix. Immutable records retain values, byte/line
spans, category and semantics status. Graphics/text layer values are separate
from footprint/pad layers. Direct pad subtrees retain their existing separate
gate. uuid/at/layer/attr gates are preserved; metadata, graphics/text and model-3d
remain semantics-unchecked. No model transform is applied to pads.

Post-EOF coverage rejects unclassified paths with GEOMETRY_UNSUPPORTED before
preflight/binding, including source hash, parent/pad UUID, full path and node span.
Existing depth/token-size/token-count budgets bound traversal and retained records.
Only selected footprint records survive scanning; unselected footprints are not
claimed covered. This is declaration-path coverage, not a KiCad semantic decoder.

Evidence: evaluation/kicad-reader/evidence/c1-c2-footprint-coverage-portable-01/.
Implementer run: 103 passed in 3.85s, exit 0; 45 pre/post input hashes unchanged.
Ran footprint-coverage, footprint-fields, pad-coverage, source-pose,
source-membership and artifact-binding portable test files only. Real PCB checks
all observed paths, graphics/text layer counts, four candidates and 16 corners.
Synthetic unknown nodes under property/effects/font, fp_line/stroke and
model/offset/xyz reject. Scanner-record doubles prove downstream blocking only;
real hash admission still rejects synthetic bytes. EOF rejection is retained.

Review pending. Construct completeness, effective copper geometry, graphics/text
and model semantics, electrical and zone-fill behavior remain unverified. No
import-ready/publication/targeting authority. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL. Historical evidence unchanged. No native/full suite,
ZIP, commit or push. Next action: review this slice and its portable evidence.

### 2026-11-06 - C1+C2 non-pad footprint coverage static review accepted

User relayed static review PASS for aoi-c1-c2-footprint-coverage-review-ca0d30c984e0.zip:
55 manifest hashes, 45 inputs including the PCB outside the ZIP, the byte-exact
scanner baseline and its diff matched. The 103 PASS result comes from the saved
implementer log; reviewer has not rerun the tests. This records user-relayed
review, not an attestation or a new verification run. Earlier review-pending
wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/c1-c2-footprint-coverage-portable-01/.

Acceptance covers declaration-path coverage of descendants outside pad subtrees
of exactly the two pinned C1+C2 footprints. Metadata, graphics/text and model 3D
remain semantics-unchecked; graphics/text layers are recorded separately. Real
PCB admission, private synthetic scanner cases and scanner-record early-blocking
test doubles remain distinct; doubles do not establish hash admission for altered
bytes. Construct completeness, effective copper geometry and zone-fill semantics
remain unverified. No general import readiness, publication or targeting authority
is established. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; checkboxes
and historical evidence unchanged. Only HANDOFF and implementation status updated;
no code/evidence changes, tests/native runs, commit or push.

### 2026-11-06 - C1+C2 graphics/text layer policy (review pending)

Updated evaluation scanner c1_c2_source_membership.py; added
test_c1_c2_graphics_layers.py. After existing field/coverage gates and before
preflight/binding, each fp_line/fp_circle requires exactly one direct layer in
F.SilkS/F.CrtYd. A property with any direct at/layer/effects requires exactly one
layer in F.SilkS/F.Fab; metadata-only properties may omit it. No inference from
hide or property name. Span-ordered traversal separates sibling instances in
linear work with at most two retained diagnostic layer records. Missing/duplicate
layers yield SCHEMA_INVALID; out-of-subset/malformed layer values yield
GEOMETRY_UNSUPPORTED, with parent UUID/hash/path and owner/layer spans.

Evidence: evaluation/kicad-reader/evidence/c1-c2-graphics-layers-portable-01/.
Implementer result: 124 passed in 4.35s, exit 0; 46 pre/post hashes unchanged.
Ran graphics-layers plus existing footprint-coverage/fields, pad-coverage,
source-pose/membership and artifact-binding portable tests only. Real r2 retains
four candidates/16 oracle corners. Synthetic F.Cu/Edge.Cuts, missing/duplicate
layers, display triggers and sibling isolation are checked. Metadata-only
properties pass without guessing from names/hide. Private scanner-record doubles
prove early blocking, not hash admission; real pin still rejects synthetic bytes.

This is the user-selected evaluation subset policy, not normative general KiCad
support. Graphics geometry/text rendering, effective copper, model, electrical
and zone-fill semantics remain unverified; recorded graphics/text semantics stay
unchecked beyond this layer declaration gate. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL. Review pending; historical evidence unchanged.
No native/full suite, ZIP, commit or push. Next action: review code/evidence.

### 2026-11-06 - C1+C2 graphics/text layer static review accepted

User relayed static review PASS for aoi-c1-c2-graphics-layers-review-b29a4d121826.zip:
56 manifest hashes, 46 inputs including the PCB outside the ZIP, the byte-exact
scanner baseline and its diff matched. The 124 PASS result is from the saved
implementer log; reviewer has not rerun the tests. This records user-relayed
review, not an attestation or a new verification run. Earlier review-pending
wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/c1-c2-graphics-layers-portable-01/.

Acceptance retains the agreed evaluation-only C1+C2 layer policy: each
fp_line/fp_circle has exactly one direct F.SilkS/F.CrtYd layer; a property with
any direct at/layer/effects requires exactly one F.SilkS/F.Fab layer. Metadata-only
properties may omit layer; neither hide nor property name determines display.
Real pinned PCB admission (four candidates/16 corners), synthetic scanner cases
and early-blocking test doubles remain distinct. Test doubles do not establish
hash admission for altered bytes. Graphics geometry/text rendering semantics,
effective copper, construct completeness and zone-fill semantics remain
unverified; this is not general import readiness, publication or targeting
authority. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; checkboxes and
historical evidence unchanged. Only HANDOFF and implementation status updated;
no code/evidence changes, tests/native runs, commit or push.

### 2026-11-06 - Source-checked request records/profile/preflight (review pending)

Implemented evaluation/kicad-reader/source_checked_preflight.py and its new
portable test_source_checked_preflight.py. Frozen/slotted records include the
contract input/output types; this slice only produces PreparationPreflightSuccess
or PreparationFailure. It never constructs PreparedRequest/SourceCheckEvidence,
scans PCB, performs geometry matching or calls binding/candidate execution.

Preflight checks exact record/nested types, the eight artifact IDs and declared
size/hash pins, four source pairs, exact policies/limits and internally consistent
successful inventory. One iterative ledger counts shared metadata nodes, UTF-8
bytes, reference occurrences and raw byte lengths. Fixed diagnostic fallback and
terminal budget reservation are reused. Existing geometry numeric fields retain
their integer-or-float behavior; integer policy limits reject bool. Success is
explicitly preflight-only-bytes-not-hash-verified: raw-byte digest recomputation
and source checks remain for the next phase, not implied by InventorySuccess.
Synthetic positive structural inputs intentionally have zero-filled bytes and
pinned metadata; they do not claim byte admission. A separate test uses real
inventory of the pinned PCB/artifacts. Exact/exceeded aggregate counter tests
exercise the ledger primitive, not full-profile admission at every aggregate cap.

Evidence: evaluation/kicad-reader/evidence/source-checked-preflight-portable-02/.
Implementer: 66 passed in 0.35s, exit 0; 74 pre/post input hashes unchanged and
rechecked against current files before this entry. Includes the external real PCB.
Only the new test file ran. Historical portable-01 retains 59 PASS/2 FAIL: the
PowerShell transfer converted the intended Unicode test literal to '?'; replacing
that setup literal with chr(0xE9) preserves the intended UTF-8 boundary assertion.
Five further focused tests were added for no hash-verification claim, shared refs,
depth, missing slots and rejected inventory. No old evidence was overwritten.

No production importer, source verification, receipt, candidates, publication or
new assurance is delivered by preflight. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13
remain PARTIAL. No native/full suite, ZIP, commit or push. Review pending; next
single action is review this preflight slice before enabling source preparation.

### 2026-11-06 - Source-checked preflight static review accepted

User relayed static review PASS for aoi-source-checked-preflight-review-6614d97ac74d.zip:
90 manifest hashes and 74 inputs matched SHA-256 and size, including the PCB outside
the ZIP. The 66 PASS result is from the saved implementer log; reviewer has not
rerun the tests. This records user-relayed review, not a new verification run or
attestation. Earlier review-pending wording for this slice is historical and
superseded by this acceptance. Evidence remains
 evaluation/kicad-reader/evidence/source-checked-preflight-portable-02/.

Acceptance is preflight-only: structural records, profile/pin declarations and
bounded metadata admission. No raw-byte hash verification, source scan, receipt
construction or binding/candidate execution is established. Synthetic zero-filled
inputs with pinned metadata are structural test doubles, not byte admission.
The separate real-inventory test uses the pinned PCB/artifacts. Ledger primitive
exact/exceeded tests do not establish full-profile admission at every budget cap.
Historical portable-01 (59 PASS/2 setup failures caused by Unicode literal transfer)
and its logs/hashes remain unchanged; the chr(0xE9) setup correction is documented.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. No source-verification,
import-ready, publication or targeting assurance is added. Only HANDOFF and
implementation status updated; no code/evidence changes, tests/native runs,
commit or push. Further preparation phases require a separately authorized slice.

### 2026-11-06 - Source-checked byte hash phase (review pending)

Added verify_source_checked_bytes in evaluation/kicad-reader/source_checked_preflight.py
and test_source_checked_bytes.py. The existing public structural preflight delegates
to a private checker accepting the operation-owned ledger. Byte verification creates
one ledger, runs that preflight, then hashes the exact eight immutable buffers in
artifact-ID order and compares digest/size against profile pins AND inventory.
Hash work is charged to a separate hashed_bytes counter on the same ledger (cap
1117036), and computed digest text consumes the existing shared metadata budget.
No source scan, receipt, prepared request, binding or candidate execution occurs.
Success status is bytes-match-pins-and-inventory-only; failures return no candidates.

Evidence: evaluation/kicad-reader/evidence/source-checked-bytes-portable-01/.
Implementer result: 81 passed in 0.61s, exit 0 (15 new byte tests plus 66 preflight
regressions); 75 pre/post input SHA-256/size records unchanged. Includes the real
external PCB and eight-artifact inventory case. Same-size one-byte mutations in
each artifact fail SOURCE_CONFLICT with actual/expected hash and artifact identity.
Spies prove rejected preflight blocks hashing and actual input buffer identity is
preserved. Synthetic zero-filled inputs still pass structural preflight and fail
hash verification. A private ledger test double demonstrates metadata-budget
exhaustion carries across phases; it is not real full-profile cap admission.

Review pending. Hash agreement does not prove source membership, source semantics,
backend authenticity, geometry completeness or import readiness. Tasks 1.5/5.2
and aggregate 3.4/5.5/5.13 remain PARTIAL. Historical evidence unchanged. No native,
full suite, ZIP, commit or push. Next action: review this byte-verification slice.

### 2026-11-07 - Source-checked byte hash phase static review accepted

User relayed static review PASS for aoi-source-checked-bytes-review-e30b2de76ca7.zip:
87 manifest hashes, 75 inputs matched by SHA-256 and size, and the byte-exact
preflight baseline and diff matched. The 81 PASS result comes from the saved
implementer log; reviewer has not rerun the tests. This records user-relayed
review, not an attestation or a new verification run. Earlier review-pending
wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/source-checked-bytes-portable-01/.

Acceptance is byte-verification-only: the exact eight immutable buffers match
profile pins and inventory computed hashes/sizes. One operation-owned ledger spans
structural preflight and hashing, retaining metadata and hash-work accounting.
Real pinned eight-artifact inventory tests, synthetic zero-filled buffers and the
private ledger-exhaustion test double remain distinct. Zero-filled buffers pass
structural preflight but fail hashing; the ledger double is not full-profile cap
admission evidence. Source scan, receipt construction and candidate execution are
later phases, not established here. Hash agreement does not establish source
membership, geometry completeness, backend authenticity or import readiness.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. Historical evidence and
checkboxes unchanged. Only HANDOFF and implementation status updated; no code or
evidence changes, tests/native runs, commit or push.

### 2026-11-07 - Source declarations phase (review pending)

Added evaluation/kicad-reader/source_checked_declarations.py and its portable tests.
Minimal shared helpers: source_checked_preflight._verify_bytes accepts the existing
operation-owned ledger; its public byte API still creates its own operation ledger.
c1_c2_source_membership.check_source_records holds the former source/observation/
request checks, reused by the unchanged evaluation binding flow. Optional private
scanner charge hook checks reconstructed record arguments before record construction
and retention; old callers keep the prior behavior. Transient scanner stack/tokens
retain their separate accepted depth/token bounds.

New check_source_declarations first completes all eight byte hash checks, then scans
the same PCB buffer to EOF, runs pad/modifier and footprint field/coverage/graphics
layer gates, compares strict-v2 observation and supplied declarations, and computes
four source Decimal poses. Shared ledger charges reconstructed metadata, including
repeated footprint occurrences, observation metadata and retained pose results.
SourceDeclarationCheckSuccess contains source records/poses and counters only: no
PreparedRequest, SourceCheckEvidence receipt, binding or candidates. Completeness,
effective copper, graphics/model and zone-fill semantics remain unverified.

Evidence: evaluation/kicad-reader/evidence/source-checked-declarations-portable-01/.
Implementer: 216 passed in 6.42s, exit 0; 77 pre/post SHA-256/size inputs unchanged.
11 new tests plus 81 preflight/hash and 124 affected C1+C2 regression tests. Real
pinned PCB positive checks four pads/16 oracle corners; supplied C2 center.x +0.001mm
fails SOURCE_CONFLICT with pose spans before later result collection/binding flow.
All eight artifact mutation cases prevent scanner entry. A private budget test
double fills the ledger after hashing and proves failure before reconstructed
footprint-record storage; it is not full-profile cap admission evidence.

Review pending; Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. Historical
evidence preserved. No native/full suite, ZIP, commit or push. Next action: review
the source-check intermediate slice before receipt/request preparation.

### 2026-11-07 - Source declarations phase static review accepted

User relayed static review PASS for aoi-source-checked-declarations-review-7fa6215e3cc9.zip:
93 manifest hashes, 77 inputs matched by SHA-256 and size (including the external
PCB), and both byte-exact baselines and their diffs matched. The 216 PASS result
comes from the saved implementer log; reviewer has not rerun the tests. This
records user-relayed review, not an attestation or a new verification run. Earlier
review-pending wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/source-checked-declarations-portable-01/.

Acceptance covers the source-check intermediate for the pinned C1+C2 four pads
and two footprints, with one shared ledger across preflight, byte verification
and reconstructed metadata accounting. Receipt/PreparedRequest construction and
binding/candidate execution remain later phases; no new publication or targeting
authority is established. Completeness and effective copper geometry remain
unverified, with graphics/model and zone-fill semantics still outside the checks.

Keep evidence categories distinct: the real pinned PCB case checks four pads and
16 oracle corners; the declaration-conflict case changes C2 center.x in memory
while preserving artifact bytes; hash-gate mutation cases block scanner entry;
the private budget test double demonstrates rejection before reconstructed record
storage, not real full-profile admission at the aggregate budget cap.

Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL. Historical evidence and
checkboxes unchanged. Only HANDOFF and implementation status updated; no code or
evidence changes, tests/native runs, commit or push.


### 2026-11-07 - Boundary-record checks phase (review pending)

Added evaluation/kicad-reader/source_checked_boundaries.py and portable tests.
check_boundary_records uses one operation ledger across preflight, eight-buffer
hash verification, source declarations and boundary checks. Minimal extractions:
source_checked_declarations._check_source accepts that ledger; the public source
API still owns a fresh ledger. c1_c2_artifact_binding._records_from_verified is a
private reconstruction/comparison helper reused by the existing artifact flow;
its precondition is successful preflight and exact byte verification. Existing
artifact flow retains its hash admission and binding behavior.

The new phase checks pinned C1/C2 report stdout hashes and transport/cleanup
conditions, reconstructs exactly four boundary records by parent/pad UUID, retains
raw IU/order, normalizes Y once, and compares supplied boundary declarations
exactly. Parsed pinned metadata and reconstructed record/link arguments are charged
before retention/construction. JSON parsing remains bounded by exact artifact sizes;
this is not an arbitrary JSON decoder or runtime attestation. Budget rejection uses
the existing blocking diagnostic reservation and returns no partial records.
BoundaryRecordCheckSuccess contains source intermediate results, observed records,
artifact links and counters only: no receipt, PreparedRequest, binding or candidates.

Evidence: evaluation/kicad-reader/evidence/source-checked-boundaries-portable-01/.
Implementer run: 233 passed in 9.38s, exit 0; 79 pre/post inputs unchanged by SHA-256
and size. Includes 17 new tests plus the 216 affected preflight/hash/source/artifact
regressions. Real eight-artifact positive checks four raw records/16 literal oracle
corners and one ledger. A C2 vertex declaration mutation leaves artifacts unchanged
and yields SOURCE_CONFLICT with artifact/hash, parent/pad UUID and expected/actual.
Source conflict and hash failures block boundary checks; spies prohibit binding and
candidate calls in the new phase. Private report/transport mutation doubles exercise
link rejection without claiming byte admission; ledger exhaustion doubles prove
failure before record retention, not full-profile admission at the aggregate cap.

Review pending. Pinned C1+C2 only; completeness, effective copper, graphics/model
and zone-fill semantics remain unverified. Receipt/PreparedRequest and execution
remain later phases. Tasks 1.5/5.2 and aggregate 3.4/5.5/5.13 remain PARTIAL; no
checkbox changes. Historical evidence preserved. No native/full suite, ZIP,
commit or push. Next action: review this intermediate boundary-record slice.


### 2026-11-13 - Boundary-record phase static review accepted

User relayed static review PASS for aoi-source-checked-boundaries-review-17e598edb8fe.zip:
95 manifest hashes, 79 inputs matched by SHA-256 and size (including the external
PCB), and both byte-exact baselines and their diffs matched. The 233 PASS result
is from the saved implementer log; reviewer has not rerun the tests. This records
user-relayed review, not an attestation or a new verification run. Earlier
review-pending wording for this slice is historical and superseded by this acceptance.
Evidence remains evaluation/kicad-reader/evidence/source-checked-boundaries-portable-01/.

Acceptance is limited to pinned C1+C2 boundary-record checks with one shared ledger
across preflight, byte hashing, source declarations and boundary checks. Raw IU/order,
single Y normalization and report/transport links remain explicit. Success is an
intermediate result only; receipt/PreparedRequest construction and binding/candidate
execution remain later phases. No import readiness or publication authority is implied.

Keep real eight-artifact evidence separate from the in-memory C2 vertex declaration
conflict, source/hash gating, spies prohibiting binding/candidate calls, and private
report/transport or budget test doubles. Completeness, effective copper geometry,
graphics/model and zone-fill semantics remain unverified. Tasks 1.5/5.2 and aggregate
3.4/5.5/5.13 remain PARTIAL; checkboxes and historical evidence are unchanged.
Only HANDOFF and implementation status updated; no code/evidence changes,
tests/native runs, commit or push.
