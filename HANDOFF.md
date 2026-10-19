# Handoff — 2026-10-19 (Asia/Bangkok)

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
