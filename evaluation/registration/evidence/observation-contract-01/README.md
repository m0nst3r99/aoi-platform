# Fiducial Observation Contract Slice A

Baseline master `e808fd3804fd9aa722f303708a5b9e4f39eb9add`, 2026-11-17.
Implementer verification only: READY FOR INDEPENDENT AUDIT.

## API and contract

`geometry.fiducial_observation.map_fiducial_observations(ObservationMappingInput)`
returns immutable `ObservationMapping` or existing `RegistrationFailure`.
The mapping retains its admitted input alongside the canonical RegistrationRequest.
No numerical fitting is performed. Structural assessment PASS means schema,
context, explicit correspondences and reference links passed. Numerical eligibility
remains NOT_PERFORMED: baseline, conditioning and residual gates belong to the
unchanged registration engine. Physical verification remains INDETERMINATE and
state UNVALIDATED, even with internally consistent calibration provenance.

Each observation carries observation/fiducial IDs; board/revision/hash, side/load,
station/machine/fixture context; camera, calibration ID/version; image ID; explicit
acquisition-time artifact reference; measurement-set ID; coordinate space; center
with full frame and units; detection status; optional confidence/sigma; artifact
provenance; and DECLARED_UNVERIFIED evidence state. Camera calibration association
is caller-declared and checked for consistency, not authenticated by this slice.
Time references are opaque evidence identifiers, not clocks or expiry checks.
Repeated image IDs must agree on acquisition-time and measurement-set references.

RAW_PIXEL, CALIBRATED_MM and INDEPENDENT_REFERENCE_MM are distinct space tags.
Only CALIBRATED_MM + DETECTED may map to fit observations. Independent reference
records are not silently reused as fit points; checkpoint integration remains a
separate future boundary. No conversion is invented. Source frame is canonical
PCB/mm/right/up with revision; target is canonical MACHINE/mm/right/up with machine
identity. Every observation center must match that complete target frame.

All supplied design declarations and observations must form a one-to-one ID match;
at least two and at most 64 are admitted. No implicit list matching, preference,
averaging, filtering, outlier removal or confidence weighting occurs. Input ordering
is canonicalized by IDs. Structural diagnostics follow schema traversal order;
semantic diagnostics follow canonical identity order. Duplicate/ambiguous IDs fail.

Confidence is finite in [0,1]. Optional localization sigma is finite, nonnegative
and bounded by 2**20 mm, retained only as a detector claim. Absent quality is kept
as None; the required downstream confidence field is 0 (unknown), not an invented
positive confidence. It is not used as a weight or accuracy certificate.
All coordinates have the existing finite +/-2**20 bound. Strings are at most
128 UTF-8 bytes (artifact locator up to 512), input text 65536 bytes, references
512, artifacts 128, provenance links per observation 8, retained output 262144 bytes.
Acquisition-time and calibration links are charged in addition to existing links.
Input admission and generated-request admission each enforce their own schema;
the latter is not an extra solve or an assertion of primitive-operation accounting.

Malformed inputs fail atomically with bounded diagnostics and no partial request.
Existing codes include SCHEMA_INVALID, INPUT_LIMIT_EXCEEDED, DUPLICATE_ID,
CONTEXT_MISMATCH, FIDUCIAL_INSUFFICIENT and MAPPING_UNVALIDATED. Pixel/reference
space or ambiguous/missing detections produce MAPPING_UNVALIDATED. Caller strings
claiming VERIFIED are not accepted as evidence states. Unverified calibration
provenance returns an explicitly UNVALIDATED envelope, never a physical guarantee.

## Verification

Executed (CPython 3.11.9, repository root):

```
.venv/Scripts/python.exe evaluation/registration/evidence/observation-contract-01/run.py run-01
```

Exact expanded pytest command, JUnit test identities, stdout/stderr, byte snapshots
and pre/post SHA-256 manifests are retained in run-01. Result: **188 PASS / 0 FAIL /
0 SKIP**, exit 0: 47 new contract tests plus all 141 existing registration and
positional tests. No broad historical suite or hardware execution. The new mapping
boundary and its generated RegistrationRequest justify this compatibility run.
Existing Decimal oracles ran unchanged as part of those tests; no new numerical
algorithm or arithmetic oracle is needed for this data-contract slice.

Tests cover 2/3/16/64 observations, exact literal translations and explicit IDs,
permutations, immutability, absence of fitting during mapping, duplicates, mixed
contexts/camera/calibration, pixel/reference discrimination, frame/units, detection
states, missing/ambiguous references, acquisition conflict, confidence/sigma
boundaries, absent quality, NaN/Infinity, malformed slots, text/count bounds,
untrusted verification claims and deterministic competing semantic failures.
Source and historical registration evidence hashes match before/after execution.

Limits and next boundary: vision adapter construction, calibrated pixel-to-metric
conversion, trusted calibration/reference authentication, temporal validity and
uncertainty qualification remain unimplemented. No hardware/OpenCV/SDK, resolver,
activation, physical validation or image processing is added. Original numerical
solver, positional assessment and tests are unchanged. All scenario statuses and
task checkboxes remain unchanged. No commit/push. Independent audit is next.
