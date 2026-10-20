# KiCad reader evaluation — 2026-10-19

Historical initial evaluation. [Harness review fixes](REVIEW-FIX.md) were
subsequently accepted via direct ZIP review as reported by the user.
[Population errata/r2](population-errata-r2/ERRATA.md) now documents all twelve
source DNP attributes and corrects descriptive metadata in a new pending-review
revision. Original r1 and raw evidence remain unchanged. Statements below about
one representative source excerpt or pending harness review are historical.

Evaluation only for parts of tasks 1.5/5.2, at repository HEAD
`4e59ad93cc9f753e5c84ca8df7a49868dfde2470`. No product reader, custom
S-expression parser, fixture edit, gate re-review or support allowlist entry.
These findings have **not yet been reviewed/accepted**. Prior gate 7.1 and
inventory code review remain accepted with their previously recorded scope.

## Input and reproduction

Read-only snapshot: `C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1`.
Input `source/Edgeberry.kicad_pcb`, SHA-256:
`67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0`.
The file header declares format **20260206**, generator **pcbnew**,
generator_version **10.0**, not the exact producer patch 10.0.7.
Runtime version and file declaration must remain separate.

```powershell
Set-Location C:\dev\aoi-platform
.\.venv\Scripts\python.exe evaluation/kicad-reader/run.py 'C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1'
```

[run.py](run.py) records exact argv, return codes, output hashes, UTC time,
all fixture file hashes before/after, and individual oracle results in
[results.json](results.json). Its **exit 1 is expected for the unresolved
population discrepancy**, not a successful all-oracles verdict. Raw native
observations are in [pcbnew.stdout.txt](pcbnew.stdout.txt). Other `*.stdout.txt`
and `*.stderr.txt` retain command evidence. No fixture content is copied here.

## Comparison: documentation versus actual probe

| Candidate | Documentation / design assessment | Observed on this machine | Decision |
| --- | --- | --- | --- |
| kicad-cli 10.0.7 | Official export tool; derived export formats are not automatically lossless source records | `version`, `pcb --help`, `pcb export --help` exit 0; includes pos, stats, IPC-2581, ODB++, DXF, SVG, Gerber. No generic source-object JSON reader command in inspected help. No new exports executed | Keep for export provenance; CLI alone has not evidenced UUID/population/complete pad semantics |
| bundled Python pcbnew 10.0.7 | Native SWIG model exposes board/footprint/pad/outline data; deprecated and unstable across majors | Bundled Python successfully loads snapshot without opening editor; UUIDs, source positions, flags, pads/layers and analytic edge arcs extracted | Preferred **temporary evaluation backend**, not yet an accepted adapter |
| IPC / kicad-python | Official docs: KiCad 9/10 requires running PCB Editor GUI; headless CLI server added in 11. Designed as stable client/server API | No GUI session or IPC extraction probe run; no claim of field parity | Upgrade candidate; unsuitable for the present unattended 10.0.7 reader requirement without GUI lifecycle |
| kiutils | Python dataclass file reader, project advertises KiCad 6+; GPL-3.0. Inspected upstream `Board.from_sexpr` dispatch lacks a default unknown-token rejection, and `from_file` reads entire input | Source/document inspection only; not installed, no pinned release or fixture execution | Not selected. Exact 10.0 support, UUID/flags/unknown-token coverage and bounded parsing remain unverified |

Sources accessed 2026-10-19:
[SWIG lifecycle](https://dev-docs.kicad.org/en/apis-and-binding/pcbnew/index.html),
[IPC runtime and version limits](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/),
[kiutils project](https://github.com/mvnmgrx/kiutils),
[inspected board reader source](https://raw.githubusercontent.com/mvnmgrx/kiutils/master/src/kiutils/board.py),
[KiCad licenses](https://www.kicad.org/about/licenses/).
The kiutils source URL is a moving branch, **not a reproducible pinned dependency**.
KiCad is predominantly GPLv3-or-later with separately licensed dependencies;
deployment/redistribution must retain notices and assess obligations. Subprocess
separation is not a license exemption. No dependency was added to the product.

## Geometry and provenance observations

- Native outline API called with inference **disabled**, arc support requested,
  and NPTH-as-outline disabled. It reports valid, 1 outline, 0 holes,
  origin `(83.649, 51.772)` mm, size **135 x 90 mm**. This is centerline
  geometry, not the Gerber job's stroke-inflated 135.15 x 90.15 dimensions.
- Retained 12 Edge.Cuts line records and 3 arc records with UUID/start/end;
  arcs additionally retain midpoint/center/radius. A recorded arc has center
  `(86.149,54.272)`, radius 2.5, start `(83.649,54.272)`, end `(86.149,51.772)`.
  Counts and bounding dimensions do not prove topology or all curve geometry.
  No positive enclosed-cutout case is present; cutout support remains unverified.
- All 57 UUID/reference/value/footprint identities and all positions/angles/sides
  match population declarations. Angles compared modulo 360; raw API angles
  retained. The 28 assembly and 3 fiducial candidate UUID sets come from explicit
  fixture classifications, not inference from shapes or footprint names.
- R7/R8 remain 270R, top, angle 180 degrees, positions `(98.249,70.272)` and
  `(98.249,75.372)`. R7 pad 1 native world position `(99.1615,70.272)` matches
  the independent oracle for local x=-0.9125 rotated by 180 degrees.
- All pad UUIDs, number strings, local/world position, world angle, shape enum,
  size, drill, attribute enum, net and expanded layer membership are retained.
  This probe is **not complete pad geometry**: roundrect ratios, chamfers,
  custom primitives, per-layer padstacks and mask/paste overrides need separate
  extraction, rejection rules and independent geometry tests. Layer expansion
  does not preserve original wildcard syntax. Bottom transforms are not fully
  proven by a top-pad oracle.
- Four REF** preserved by full UUID: `00000000-0000-0000-0000-00005b7adb04`
  remains the bottom electrical via; `00000000-0000-0000-0000-00005c9e4f14`,
  `00000000-0000-0000-0000-00005ccbd5ac`,
  `00000000-0000-0000-0000-00005ccbd5d8` remain empty placeholders.
  No assembly target or registration approval is produced.

## Population conflict — do not silently normalize

Twelve G*** entries declare DNP=false in population.json but native API reports
DNP=true (attributes 92, including FP_DNP=64). Exclusion flags match. Source
inspection at PCB lines 3631–3633 confirms a multiline `attr` block with `dnp`
for UUID `18e8e642-d122-425a-b1c4-4622a1417921`; this is not evidence of API
inventing DNP. Full per-UUID expected/actual conflicts are in results.json:

```
110cdf80-ce50-49b4-8323-15cc6e2805de
18e8e642-d122-425a-b1c4-4622a1417921
683bda97-6bb0-4314-b236-b92ef02b473b
72e2cb3c-84a9-4e35-a2de-1bf710904a82
918b7da7-057f-4892-a244-8576d15a69fb
91cb5445-26f3-405b-8e77-03a53e85c2c2
973c81e6-7e5c-4c9c-8b29-3ba4ce3dc8a3
c26fea9b-ce24-49d8-9ed2-40dab0eda8f2
c30af8cd-6c66-4c4c-83ed-796f98a35f38
c896bb5f-b2ac-48fc-95b6-c8b25217b922
dcd0819f-f417-4d32-aecf-843f6f08bfa4
ff618834-9f37-479d-896c-eddeb1f1df65
```

No fixture or ledger correction is made. Gate acceptance is not rerun; this new
reader finding must be reviewed before population normalization is accepted.
Assembly/fiducial classification counts do not change. A future adapter must
retain declared and observed values and report SOURCE_CONFLICT, never overwrite.

## Failure, isolation and upgrade limits

An initial sandbox LoadBoard probe timed out at 30 seconds; retry outside sandbox
succeeded. CLI help inside sandbox had HKCU registry permission warnings.
The exact cause of the LoadBoard timeout is **not isolated**. Successful local
headless execution does not demonstrate service-account/sandbox compatibility.
Malformed synthetic input returns None from LoadBoard; the probe converts that
to exit 1. Missing input fails at the hash/open stage (FileNotFoundError), so
this does not test native missing-file behavior. No generic typed product errors
are implemented. Native load success does not establish unknown-construct
rejection; unsupported/future construct corpus and error locations remain open.

Harness subprocess timeout is 30s. Output is captured in memory: **no enforced
memory/output/CPU budget, process-tree kill or hostile-file sandbox** is supplied.
Future adapter needs Windows Job Object or equivalent containment, bounded IPC,
timeout/crash/error diagnostics and restricted temporary input permissions.
Pin exact KiCad build and bundled Python/native module identity; path `10.0`
alone is insufficient because patch upgrades can replace it. Executable hashes
and portable installer provenance are not yet pinned by this evaluation.
SWIG removal is currently planned for KiCad 11 per official docs; keep backend
behind a versioned observation protocol and re-evaluate IPC headless plus field
parity on an actual pinned 11 build before migrating. Do not silently upgrade.

## Smallest next slice (proposal, not implemented)

Task 1.5/5.2: a bounded **reader observation adapter** with proposed contract
`observe_kicad(admitted_artifact, pinned_backend, limits) -> Observation | Failure`.
Input is inventory-admitted PCB evidence; output retains source hash, runtime
identity, declared format and raw entity observations, never a BoardRevision or
inspection-ready geometry. No automatic source-to-canonical conversion.

Acceptance: exact backend identity gate; immutable schema and deterministic
diagnostics; independent rotated top/bottom and line/arc/cutout tests; explicit
unsupported constructs, newer formats, malformed data and duplicate UUID errors;
bounded process/output/time with crash/timeout cleanup tests; unchanged source
hashes; full UUID population reconciliation preserving the 12 conflicts above.
First resolve how unsupported constructs that native load normalizes/omits are
detected, and review the population discrepancy without modifying accepted r1.
If these cannot be evidenced, return failure/unverified observations, not usable
geometry. Tasks 1.5/5.2 remain PARTIAL/open; 5.3–5.5 are not implemented here.

## Repository checks

After documentation updates: `openspec validate board-geometry-foundation --strict`
passes; `git -c safe.directory=C:/dev/aoi-platform diff --check` exits 0 (only
LF/CRLF notices). Both probe scripts pass `python -m py_compile`. Full pytest
was not rerun because no shared source/test code changed. The native fixture
evaluation remains **9 passing aggregate checks, 1 failed population check**,
not an all-pass report. No commit/push or accepted fixture changes.
