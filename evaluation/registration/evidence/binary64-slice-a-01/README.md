# Binary64 pure rigid registration Slice A

Date: 2026-11-17. Implementer evidence, not an independent audit verdict.
Baseline: `master` at `14e23b7f1c9de82518fc2f11fe66d3205ca1bcf2`.
No commit or push. No historical test count is substituted for these runs.

## Scope and public boundary

New entry point: `fit_rigid_registration(request, policy)` in
[registration.py](../../../../src/aoi_platform/geometry/registration.py).
It returns an immutable `RegistrationDraft` or `RegistrationFailure`.
The algorithm is `proper-rigid-binary64-v1`: proper 2D rigid, fixed scale one,
uniform weights, all identified fit points retained. No automatic outlier removal.

Request types include `RevisionKey`, `RegistrationContext`, `FiducialDeclaration`,
`MetricObservation`, `ArtifactReference`, `CalibrationReference`, and
`IndependentValidationEvidence`. Required context includes revision/content hash,
side, load, station, machine and fixture/configuration; P and M are explicit mm,
X-right/Y-up frames. Measurements must already be in M. This bounded entry point
does not change the general Geometry Core frame/transform constructors.

Policy identity/version, synthetic purpose, baseline/pair-distance/fit/checkpoint
thresholds and evidence requirements are explicitly supplied. No production
defaults. Policy changes require a new caller-managed version; the pure solver
does not own a policy registry or enforce historical version uniqueness.

Successful drafts retain a detached canonical immutable request/policy snapshot,
represented coefficients, residuals/guards, checkpoint assessments and bounded
resource counts. They have no apply/conversion/activation/resolver interface.
`validation_state` remains `NOT_PERFORMED`. Independent evidence remains
`DECLARED_UNVERIFIED`, including when declared disjoint measurement-set checks
pass. SHA-256 syntax checks do not read artifacts or authenticate issuers.
Calibration validity, physical observation independence, current load and actual
side/parity cannot be verified by this solver.

Failure returns one bounded typed diagnostic without coefficients or partial
draft. Frozen caller records are structurally readmitted, including malformed
objects constructed by bypassing constructors. Semantic checks use canonical ID
ordering; structural errors use fixed schema/slot order. Output is counted using
a bounded canonical JSON traversal before publication; no serialized partial
result is returned. Numeric checkpoint disagreement is reported without refitting.

## Numerical implementation and remaining limitations

[Private solver](../../../../src/aoi_platform/geometry/_registration_numeric.py)
uses anchor differences, `math.fsum`, separate positive centering scales,
compensated covariance, `hypot` rotation normalization, and compensated translation.
Residuals are evaluated from the represented returned coefficients, not an ideal
unserialized rotation. RMS and maximum use all fit points. Finite checks are
fail-closed. No exact-dyadic integer arithmetic or primitive-work ledger remains.

The dimensionless correlation floor is `1e-8`; its decision margin is
`256*n*2**-52`. Physical comparisons use `128*2**-52*L + 8*ulp(value)`;
pair-distance disagreement uses the sum of distance margins. Equality or overlap
with a threshold is indeterminate, never silently relaxed. Fit ambiguity fails
atomically; checkpoint ambiguity remains an assessment on an unvalidated draft.

These margins are tested hypotheses, not rigorous interval bounds, uncertainty
estimates or production accuracy certification. The literal/oracle corpus does
not establish every possible binary64 input or platform. No bit-identical libm
guarantee is claimed. Pair-only data cannot establish reflection correctness.
Independently declared checkpoints are not independently verified measurements.

## Resource limits demonstrated

- 64 fit pairs, 32 checkpoints; the combined 96-record case passes.
- Coordinate components at `2**20` mm pass admission; the next float fails.
- ID text: 128 UTF-8 bytes; locator/free metadata: 512 bytes.
- Total input text: 65,536 bytes, counting repeated occurrences.
- Artifact/calibration/evidence collections: 128/16/16.
- Per provenance tuple: 8 references; total reference occurrences: 512.
- Output cap: 262,144 UTF-8 bytes; legitimate control-character escaping can
  exceed it even when input text is bounded, producing atomic failure.
- A failure has one diagnostic and no unbounded caller-value formatting.

Tests independently construct exact-total text and reference counts. A reduced
output cap tests exact-size/one-less behavior; a separate case reaches the real
output cap through JSON escaping without changing the production limit. No
primitive counts, performance guarantee, or platform capacity claim is made.

## Runs and preserved failures

Each run directory contains exact source/test snapshots, SHA-256 manifests,
command, wall duration, exit code and full test identities/output.

| Run | Result | Reason and source provenance |
| --- | --- | --- |
| [01](run-01/pytest.txt) | 81 PASS, 1 FAIL; 0.39 s pytest; exit 1 | Test imported nonexistent `TransformResolver`; actual class is `TransformGraph`. No oracle contradiction. |
| [02](run-02/pytest.txt) | 2 FAIL, 50 deselected; 0.22 s; exit 1 | New adversarial reproductions: legacy frame reconstruction exception and missing slot escaped atomic failure. |
| [03](run-03/pytest.txt) | 95 PASS; 0.39 s; exit 0 | Admission converts missing slots to typed failure; detached frame snapshots are context-validated before use. |
| [04](run-04/pytest.txt) | 102 PASS; 0.54 s; exit 0 | Added real output-cap, evidence/reference caps, combined maximum counts and snapshot-detachment coverage. |
| [05](run-05/pytest.txt) | **102 PASS / 0 FAIL / 0 SKIP; 0.61 s; exit 0** | Final source/test snapshot; additionally cross-checks fitted-coefficient oracle convergence at 100/160 digits. |

Final command (from repository root):

```text
C:/dev/aoi-platform/.venv/Scripts/python.exe -m pytest tests/test_registration.py tests/test_registration_limits.py -vv -p no:cacheprovider --junitxml=evaluation/registration/evidence/binary64-slice-a-01/run-05/junit.xml
```

See [invocation](run-05/invocation.json), [JUnit identities](run-05/junit.xml)
and [accepted source/test hashes](run-05/hashes.json). Earlier snapshots are not
retroactively described as testing later source. Python: CPython 3.11.9, MSC
64-bit AMD64, Windows 10.0.26300 (as reported by the runtime).

No H249/H55, full historical suite, native KiCad or Windows runner was executed.
No existing functional interface was changed; the only legacy source edit adds
three ErrorCode members. Existing model/transform/resolver/outline implementations
are untouched. No legacy regression PASS claim is made for this session.

## Independent oracle methodology and observations

[Tests](../../../../tests/test_registration.py) use direct Decimal centroids and
closed-form proper-rigid covariance independently of production anchor/scaling
helpers. Inputs use exact `Decimal.from_float`. Fitted coefficients and residual
evaluations are cross-checked at 100 and 160 digits, requiring agreement tighter
than `1e-85`. Residual quality is independently evaluated from the represented
returned binary64 coefficients. Expected values do not come from production
solver counters or guard helpers.

Literal cases include translation/cardinal and 3/5-4/5 rotations, noisy fixed-scale
1025/1024 data, large offsets with 2**-10 baseline, correlation degeneracy,
reflection/wrong correspondence/outliers, equality and adjacent thresholds.
Independent Decimal checks reject any acceptance outside caller thresholds or
metric error beyond the reported margin. There was no such contradiction.

The [report generator](oracle_report.py) and [14-case numeric report](run-05/oracle-report.json)
are reconstructable using the final snapshots. Exact command and environment are
in [oracle invocation](run-05/oracle-invocation.json); exit 0. The largest recorded
RMS error was approximately `5.01824e-12` mm, against a `3.72606e-9` mm margin
(ratio about 0.001347). This observation applies only to that corpus.

## Preservation and coverage

[Historical manifest](historical-before.json) and
[preservation result](historical-preservation.json): 1,200 tracked historical
evaluation/fixture/spec/task files checked, zero changed. Unrelated untracked
paths were inventoried separately; no cleanup, staging, rename or overwrite was
performed on them. Their bytes were not independently hashed by this session.

G12-G14: bounded rigid-fitting contribution only; no projective implementation.
G15-G17: draft/declared-evidence separation and synthetic policy controls only.
G18-G20: pure typed failures/context checks, not inspection or runtime lifecycle.
P09: caller declarations retained; fiducial classification/approval not implemented.
All 47 scenario statuses and normative task checkboxes remain unchanged.

Implementer verdict: **READY FOR INDEPENDENT AUDIT**, not accepted/validated for
production. Next action: independent audit of admission, conditioning/guard
hypotheses, evidence semantics, output bounds and the final source/test snapshot.

Delivery validation: the first `delivery-validation.json` is preserved as an
incomplete validator attempt. Its row regex also counted six supplemental mapping
references, and root-level HANDOFF link checks encountered an empty-parent-path
PowerShell error. Supplemental references are now explicitly formatted as code;
the corrected validator resolves absolute parent paths. Use
[delivery-validation-02.json](delivery-validation-02.json) for final checks.
