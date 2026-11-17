# Synthetic positional follow-up — 2026-11-17

Owner decision: 0.01 mm maximum positional error at inspected PCB locations;
universal 1e-12 coefficient accuracy is not required near degeneracy.
Implementation verification PASS; no independent acceptance or physical guarantee.

## Policy and interpretation

Additive API: `geometry.registration_position.assess_registration_positions`.
The caller supplies the existing registration request and fit policy, a tuple of
explicit `InspectionLocation` points, and `PositionalPolicy(0.01)`. Checkpoints are
explicit source/target coordinates in the request, with held-out evidence links.
Only a checkpoint at exactly the ROI point supplies coverage; there is no spatial
interpolation, extrapolation, area coverage or inferred reference observation.
At each covered point the returned binary64 coefficients are evaluated as
`r = hypot(c*x - s*y + tx - u, s*x + c*y + ty - v)` against the supplied reference.
Maximum point error, not average/RMS, is compared to 0.01 mm using unchanged
numerical guards. Guard overlap at the boundary is INDETERMINATE. Any definite
exceedance is FAIL; otherwise missing/ambiguous coverage is INDETERMINATE.
All matching supported checkpoints must pass. Empty ROI lists are INDETERMINATE.

Numerical PASS means agreement with supplied synthetic reference observations.
Structural evidence checks do not authenticate independence or physical truth.
Physical accuracy is always INDETERMINATE, validation NOT_PERFORMED, state DRAFT.
No activation or resolver registration is performed. Reference uncertainty,
calibration error, board deformation, temporal drift and unsampled ROI positions
cannot be bounded here. Even independently verified references establish residuals
only at their sampled coordinates and need their own uncertainty budget.

Rotation-coefficient error is deviation from the exact-input optimal fit. Fit
residual measures agreement at fitting fiducials; checkpoint residual measures
agreement at separate observations. Neither implies true ROI accuracy. The API
retains those quantities separately and does not change conditioning gates.

## Executed verification

From repository root with CPython 3.11.9:

```
.venv/Scripts/python.exe evaluation/registration/evidence/positional-followup-01/run.py run-01
.venv/Scripts/python.exe evaluation/registration/evidence/positional-followup-01/run.py run-02
.venv/Scripts/python.exe evaluation/registration/evidence/positional-followup-01/oracle_report.py
```

The runner records the exact pytest command, byte snapshots, pre/post SHA-256,
stdout/stderr, exit and JUnit test identities for each attempt. Run-01: 136 PASS.
Run-02: 141 PASS / 0 FAIL / 0 SKIP (39 new positional + 102 existing registration).
Run-02 adds N=2 controls and explicitly uses 180-digit context for reference
generation. Production positional source is unchanged between runs. Reverification
is justified by the new ROI/coverage contract and changed numerical test inputs;
no unrelated broad suite was executed. Source and historical hashes were unchanged
during both runs. Prior angular evidence and all earlier registration evidence
remain preserved. No production solver or guard was edited.

Independent test oracle uses exact `Decimal.from_float` inputs, direct centroids
and closed-form covariance, not production numeric helpers. Residuals evaluated
with returned coefficients converge between 100 and 180 digits within 1e-85 mm.
The standalone report records exact float-hex inputs/coefficients and numerical
results. Twenty N=2/3/16/64 cases at requested correlations 1e-8 through 1e-6:
17 numerical PASS, three unchanged NUMERICAL_AMBIGUITY rejections at the floor.
N=2 are correlation-one controls, not geometrically near-floor cases.
At corners (+/-150, +/-100) mm the maximum reference residual is
3.760489697545522e-7 mm; maximum coefficient error 1.668755457438552e-9;
maximum residual reporting error 1.268632295837062e-14 mm, within existing guards.
No false numerical PASS against 0.01 mm occurred in this corpus. References are
independently computed optimal synthetic positions, not real measurements.

Other focused tests cover exact translation, permutation invariance, corners far
from fit points, a 0.02 mm distant discrepancy despite zero fit residual,
0/0.009999/0.01/0.010001/0.1 mm boundaries, missing evidence, nearby-only coverage,
shared measurement sets, empty ROIs, malformed types/frames/nonfinite coordinates,
duplicate IDs, oversized metadata, missing slots, count caps and invalid policy.

Limits: finite synthetic corpus, existing guards remain tested hypotheses rather
than certified bounds. The original registration contract's validated-candidate
scenario is not closed by these draft-only checks. All 47 scenario statuses and
normative task checkboxes remain unchanged. No commit or push.
