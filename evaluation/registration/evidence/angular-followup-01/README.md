# Independent angular follow-up — BLOCKED

2026-11-17, master 14e23b7f1c9de82518fc2f11fe66d3205ca1bcf2.
Controlled reviewer execution, not saved implementer PASS reuse. No production
source/guard changes, regression-test additions, commit or push.

Command (repository cwd), exit 0:
`C:/dev/aoi-platform/.venv/Scripts/python.exe evaluation/registration/evidence/angular-followup-01/audit.py`
Environment: PYTHONDONTWRITEBYTECODE=1; configured CPython 3.11.9 venv.
Exit 0 means the experiment completed, not numerical acceptance.

[Script](audit.py) uses existing request/policy schema fixtures only. Its separate
oracle uses direct Decimal centroids/covariance and exact Decimal.from_float inputs,
with 100/180-digit agreement better than 1e-85. It neither calls production numeric
helpers nor reuses the existing oracle. All 20 input arrays and returned coefficients
are preserved as float.hex strings in [results](results.json); reconstruct using
float.fromhex. The schema fixture and production files are snapshotted; pre/post
SHA-256 values in results match. Re-running in this directory would encounter the
exclusive results-file guard; copy the script to a fresh evidence directory first.

Construction: radius 0.01 regular N-gon p; q=(p.x,-p.y)+t*R(0.6,0.8)*p.
N=3/16/64 produce near-zero proper-rigid correlation through cancellation of the
reflected component. N=2 noncoincident pairs necessarily have correlation 1 and
are controls, not evidence of near-floor coverage. Target t values: 1e-8, 2e-8,
5e-8, 1e-7, 1e-6. Physical policy: baseline .001 mm; pair/RMS/max limits .05 mm;
remaining policy fields come from the snapshotted fixture. Inputs enter the public
fit_rigid_registration API without bypassing admission or altering guards.

Results: 20 cases, 17 drafts, three conditioning NUMERICAL_AMBIGUITY failures at
1e-8 (N=3/16/64). All 20 permuted public requests return identical results.
Twelve drafts exceed the existing test coefficient criterion 1e-12; this criterion
is not a certified public error bound. Worst: N=3, t=2e-8, coefficient error
1.668755457438551857041862959e-9, rho=1.999999983088519896e-8. The independently
optimal (c,s) begins (0.6000000140410920543,0.7999999894691807667).
Exact returned-coefficient RMS is 0.01414213548230959545 mm; its reported error
is 1.4454141720045947e-18 mm versus guard 2.8435587218211822e-14 mm.

N=64 coefficient errors at 2e-8/5e-8/1e-7/1e-6 respectively:
5.63139816265929e-10, 1.23614667024284e-10, 4.33482950803509e-11,
2.87052420632667e-12. This confirms angular sensitivity, not a physical false PASS.

Every draft's residuals are independently evaluated from its represented returned
coefficients, separately from the optimal coefficients. Zero false PASS at the
original physical thresholds or 85 RMS threshold probes (exact returned RMS rounded
to binary64 plus -4/-1/0/1/4 reported guards). Equality-near probes are ambiguous;
one-guard boundary results depend on rounding. No certification of every threshold,
checkpoint, platform, offset or admitted input is implied. The thresholds here are
synthetic, not production accuracy qualifications.

Mechanism: cancellation in centered/scaled covariance products precedes fsum;
normalizing the small covariance vector amplifies its directional error. fsum does
not recover errors already incurred by centering, scaling and products. Stop for
owner review of coefficient accuracy requirements/conditioning policy. No automatic
guard increase or tolerance relaxation is authorized. No additional experiments or
regression tests after confirming this counterexample.
