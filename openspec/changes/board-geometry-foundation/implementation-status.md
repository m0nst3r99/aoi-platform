# Geometry Core implementation evidence

Date: 2026-10-17 (Asia/Bangkok). Workspace: `C:\dev\aoi-platform`, verified by creating, reading and removing a dedicated write probe there before implementation. The user authorized only the first Geometry Core subset, not the full Sprint 1 plan or all 63 tasks. Neither Foundation Prototype nor Foundation Complete is achieved.

## Delivered files and behavior

- `pyproject.toml`: Python >=3.11 package metadata, standard-library runtime, pytest test extra and src-layout test configuration.
- `README.md`: API conventions, test commands, numerical limits and explicit remaining scope.
- `src/aoi_platform/__init__.py`, `src/aoi_platform/py.typed`: package and typing marker.
- `src/aoi_platform/geometry/{__init__,errors,models,angles,transforms}.py`: public exports, typed errors, immutable Point2/Frame, angles and immutable affine Transform2.
- `tests/conftest.py`, `tests/test_models.py`, `tests/test_angles.py`, `tests/test_transforms.py`: synthetic fixtures, independent expected values and negative cases.
- This evidence document plus proposal/design/sprint-plan/tasks status updates. Normative capability requirements and transform equations are unchanged.

The core checks complete intermediate Frame records, rejects conflicting known revision/machine/capture metadata, and never infers a source origin from metadata names. Source frames may represent future panel/unit datums without a new subsystem. This does not implement a frame registry, path search, load/calibration lifecycle, board revision storage or cross-machine processing service.

Affine transforms retain IDs, endpoints, units via frames, immutable matrix, kind, derived parity, condition metric and provenance. Composition/inversion record their parent IDs. Physical-to-pixel mapping and projective matrices reject explicitly. Direct affine algebra is available for declared matrices; there is no board-import fitting or automatic scale-to-extents behavior. Bounded valid regions and full Transform2/calibration contracts remain partial.

## Executed tests

Runtime observed: Python 3.11.9; pytest 9.1.1 in the existing project `.venv`. No runtime/test packages were installed or upgraded.

Command, executed from the workspace:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Initial implementation result: **78 passed in 0.13s**, exit code 0. No failed or skipped tests. Earlier incremental runs passed 40 model/angle tests, then 77 tests before adding the condition-threshold boundary case. These are software synthetic tests only. The review-correction results and available line-coverage check are recorded below; no static-type-checker result or branch coverage is claimed. Editable installation/wheel distribution was not tested.

| Behavior / specification scenario | Independent evidence | Task status |
| --- | --- | --- |
| Point/frame validation | `test_models.py`: finite numbers, immutable records, explicit enum/datum/context checks, PCB/machine/image conventions | 3.1 PARTIAL; full models/contracts open |
| Unit conversion and intermediate oracles | `test_required_chain_and_independent_inverse_checkpoints`: literals (25.4,50.8), (25.4,-50.8), (50.8,25.4), (60.8,45.4), inverse checkpoints; independent mm-to-inch test | 4.1 DONE |
| Bottom reflection and direction/parity | `test_bottom_reflection_preserves_angle_and_parity_semantics`: x=5 maps (2,3) to (8,3), 0 degrees to 180/reflected, 30 to 150, inverse restores angle/parity; bottom-name identity test | 4.2 DONE |
| Rotation, translation, angle wrapping | `test_angles.py`, required chain, direction-vector checks; 359.95 -> 0.02 gives +0.07; antipodal tie -180 | 4.3 DONE |
| Composition/inversion order | `test_noncommuting_transforms_apply_inner_first`: rotate-then-translate gives (8,1), reverse order (-2,11); shear oracle gives (20,2), inverse (5,6) | 4.4 DONE |
| Affine round trips and known forward values | `test_seeded_forward_oracles_and_round_trips`: seed 1007, five explicit corner/origin/negative points plus 200 samples; independent scalar forward formulas, recovered physical error <=1e-6 mm | 4.4 DONE |
| Singular/ill-conditioned/nonfinite/type failures | Parameterized invalid matrices, explicit enum/kind checks, normalized condition threshold, extreme representable scales and overflow rejection | 4.5 PARTIAL; no path resolver |
| Frame incompatibility | Exact intermediate record checks, same-ID/different-metadata collisions, conflicting revision/machine/capture endpoints, explicit units/datum rejection | 3.1/4.5 PARTIAL; not full machine/calibration isolation |

Numeric policy: proposed `synthetic-geometry-v1` affine subset. Round-trip bound <=1e-6 mm; normalized 2x2 spectral condition <=1e8. Unit-scale isometry checks use absolute 1e-12 binary64 shape tolerance. These bounds are not verified hardware accuracy or a general guarantee for arbitrarily large coordinates. The full configurable policy and production-purpose qualification remain unimplemented.

## OpenSpec validation

Command: `openspec validate board-geometry-foundation --strict` from `C:\dev\aoi-platform`. Actual result: "Change 'board-geometry-foundation' is valid", exit code 0. OpenSpec validation does not replace implementation tests or complete any remaining task.

## Remaining work — intentionally open for review

Only original tasks **4.1, 4.2, 4.3, 4.4** are checked; **59 remain unchecked**. Task 3.1 remains open for the complete typed-model contract, despite the tested point/frame/affine subset. Task 3.6 remains open: individual GeometryError is not the multi-error report/ordering contract. Task 4.5 remains open: explicit pairwise frame checks are not graph resolution, missing-path detection or ambiguous-path validation.

Further Sprint 1 work includes capacity/fixture/travel records and checks (3.2, 4.15–4.17), full error reports, and contextual path resolution. No normative requirement is removed or weakened by limiting this implementation slice. Later import, real PCB fixture, Gerber evaluation, BOM/placement, fiducial registration, camera/lens calibration, REVIEW inspection boundary, six-machine lifecycle validation and optional engine work remain open. Source provenance/immutable board revision persistence is specified but not implemented by immutable numerical records alone. Future 3D and physical travel/coverage remain outside this slice.

KiCad 10.0.7 is still an unverified target; no parser compatibility, real fixture test or production accuracy is claimed. No project files were created under Codex outputs. `C:\dev\aoi-reference` was not modified. No push or deployment was performed. Existing untracked `.agents/` and `.claude/` content was left untouched.

## Geometry Core review corrections — 2026-10-17

Scoped fixes only; no additional task is completed. Original method/constructor signatures are unchanged. `Transform2.conventions_validated` is a derived, read-only attribute. A raw map across different units or axis directions remains unvalidated and cannot be applied, inverted, composed or used for orientation mapping: those operations return `MAPPING_UNVALIDATED`. Provenance text is not authorization. Explicit unit/rotation/reflection factories and compositions/inverses of validated operands retain the needed evidence. Translation alone does not declare an axis mapping. Dataclass replacement recomputes validation, preventing a changed matrix from inheriting that evidence. This flag concerns declared numerical conventions, not hardware/source calibration or production accuracy.

Composition now preserves RIGID only when both operands are validated RIGID maps, and rechecks the product's isometry. Reflection/general-affine operands conservatively produce AFFINE, with independently computed parity; a positive determinant alone never promotes a map to RIGID. All prior source-frame, matrix and context checks remain active.

Changed in this correction: `src/aoi_platform/geometry/transforms.py`, `src/aoi_platform/geometry/errors.py`, new `tests/test_transform_validation_regressions.py`, `README.md`, and this status document. Existing tests and normative requirements are unchanged; existing unrelated workspace files were left untouched.

Regression evidence:

- Before the fix, six regression cases failed as expected: both directions of raw inch/mm identity, three incompatible axis conventions with raw identity, and loss of RIGID classification on composition.
- After the fix, `.venv/Scripts/python.exe -m pytest -q` reported **104 passed in 0.14s**, exit code 0: all 78 existing cases plus 26 new regression cases, no final failures/skips.
- Additional adversarial cases cover forged provenance, replacing a validated matrix, blocking all computational entry points, cancellation through composition, preserving explicit unit/shear/inverse workflows, and conservative reflection/general-affine kind handling.
- `coverage` and `pytest-cov` are not installed in the existing environment. Python's available standard-library `trace` line-coverage check ran the same suite: **104 passed in 0.86s**, exit code 0. It reported **100% executable-line coverage** for the four measured modules: angles (8 lines), errors (33), models (101), transforms (245). This is the standard-library trace metric, not branch coverage or a pytest-cov result. Annotated reports are local under ignored `.pytest_cache/geometry-coverage/`.

Reproduce the available coverage check from the workspace without installing packages:

```powershell
@'
from pathlib import Path
import sys
import trace
import pytest
source = Path('src/aoi_platform').resolve()
tracer = trace.Trace(count=True, trace=False, ignoredirs=[sys.base_prefix, sys.prefix, str(Path('tests').resolve())])
exit_code = tracer.runfunc(pytest.main, ['-q'])
counts = {key: count for key, count in tracer.results().counts.items() if Path(key[0]).resolve().is_relative_to(source)}
trace.CoverageResults(counts=counts).write_results(show_missing=True, summary=True, coverdir='.pytest_cache/geometry-coverage')
raise SystemExit(exit_code)
'@ | ./.venv/Scripts/python.exe -
```

Strict OpenSpec validation is run after these corrections; its result is reported in delivery. The same 59 tasks remain open, including full contextual path resolution, envelope checks, calibration and imports. No new inspection validation workflow, source parser, hardware qualification or other OpenSpec task was implemented. No commit or push was performed.
