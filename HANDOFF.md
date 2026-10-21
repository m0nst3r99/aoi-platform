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
