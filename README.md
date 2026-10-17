# AOI Platform V0.1 — Geometry Core

## Capacity and envelope records (current partial Sprint 1 slice)

`Outline`, `LineSegment` and `CircularArc` provide a single simple closed mm contour with analytic arc extrema. `Outline.polygon` closes the supplied vertex sequence explicitly; do not repeat the first vertex. Circular arcs have explicit start/end/center points and clockwise direction; full circles need at least two arcs. Holes, splines/ellipses, multiple contours, more than 512 edges, coordinates or radii above 1e6 mm, and unresolved/degenerate topology reject explicitly. No curve is replaced by endpoint chords.

`check_capacity(outline, BoardCapacity(id, version), rotation_deg=...)` requires a canonical PCB frame and an explicit rotation. Capacity is fixed at 280 x 550 mm. Exact quarter-turns use signed coordinate permutations. Other rotations use analytic projected extrema, including arc interiors. The recorded `capacity-binary64-v1` arithmetic guard is `min(1e-8, 16*ulp(max(550, abs(projected bounds))))` mm, not a physical fit tolerance. The mandatory 0.001 mm overrun remains a failure. Machine placement is not an input to this calculation. Topology predicates use a separate 1e-8 mm numerical guard, with numerically degenerate/unsupported geometry rejected.

`FixtureEnvelope` and `CameraTravelEnvelope` carry separate identities/versions, full machine frames, fixture/camera/configuration IDs, geometry/exclusions and explicit evidence. No physical rectangle or margin is defaulted. Synthetic evidence never promotes itself to qualified; a qualified declaration requires separate qualification references supplied by the caller (reference authenticity is not verified by this data model).

`validate_fit` separately evaluates capacity and the complete loaded board against axis-aligned rectangular usable regions/exclusions in M. Supply an explicit validated proper-rigid `load_transform`; capacity-test rotation is not placement. Outer boundary contact is allowed at zero margin; exclusion contact, overlap and either direction of containment fail. Positive margin uses minimum Euclidean clearance to both kinds of boundary. Analytic arc extrema, curve intersections/distances and filled-contour containment prevent endpoint-only or bounding-box exclusion checks. Violations use structured `BOARD_OUT_OF_ENVELOPE` diagnostics, ordered by usable region first and then exclusion ID.

Numerical policy `fixture-binary64-v1` uses a 1e-8 mm arithmetic guard on outer/margin comparisons and conservatively treats exclusion separation <=1e-8 mm as contact. This cannot hide the required 0.001 mm overrun/shortfall; it is not manufacturing tolerance. Nonrectangular envelope regions reject with `GEOMETRY_UNSUPPORTED`, including when other inputs are missing. Missing fixture geometry, margin or load remains unresolved with explicit reasons. Camera reachability always stays unresolved, including supplied travel rectangles. Reports retain policy, context and evidence IDs and cannot authorize motion or targeting; a synthetic fixture-fit pass does not qualify the envelope. Broader geometry, physical qualification and import integration remain open.

First implementation slice of OpenSpec `board-geometry-foundation`, using Python 3.11+ and the standard library at runtime. This is a package-oriented numerical core, not an inspection application. Foundation Prototype and Foundation Complete are not achieved.

## Run the tests

From `C:\dev\aoi-platform`, using the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
openspec validate board-geometry-foundation --strict
```

The test configuration uses `src/` directly; editable installation is not required to run tests. On a new development environment, the package declares its test extra as `.[test]` in `pyproject.toml`. No NumPy, OpenCV, parser, controller or camera library is imported by Geometry Core. The existing virtual environment's unrelated packages are unchanged.

## Public API and conventions

Import from `aoi_platform.geometry`:

- `Frame`, `Point2`, `Transform2`: frozen typed records with runtime validation.
- `Unit`, `FrameKind`, `AxisDirection`, `Parity`, `TransformKind`: explicit enum values; unrecognized strings are rejected rather than coerced.
- `normalize_angle(degrees)` returns [0,360); `signed_angular_difference(target, source)` returns target minus source in [-180,180).
- `GeometryError` exposes a stable `ErrorCode` and `field_path`.

`Point2` retains its full immutable Frame (and exposes `frame_id`). Frame IDs must be namespaced by the caller; origin and direction metadata must be declared. Canonical PCB frames require revision identity, mm, X right and Y up; machine frames require machine identity and mm. Image-frame metadata uses px, u right and v down, but no image dimensions, camera projection or calibration are implemented. Source frames can name a future panel/unit datum explicitly without inventing a panel subsystem or 3D coordinates.

Transforms map column vectors: `T_B_A` takes points in A to B. `outer.compose(inner, transform_id=...)` returns outer @ inner, applying inner first. Exact intermediate Frame equality includes metadata and context, not just the string ID. Conflicting known revision/machine/capture identities are rejected; this is not the later calibration/load lifecycle or six-machine acceptance implementation.

Constructors are `unit_conversion`, `rotation`, `translation`, and `reflection`; each requires explicit source/target frames and a transform ID. The unit-only constructor requires a declared common origin/axes. Rotation and translation require equal units; translations are in target-frame units. `reflection(axis="x", offset=c)` means x -> 2c-x (mirror about x=c); `axis="y"` means y -> 2c-y. A bottom-layer name never causes mirroring automatically.

`apply(Point2)` returns the target-frame point. `inverse(transform_id=...)` explicitly reverses endpoints. `map_orientation(angle, parity)` transforms the local +X vector and returns both target angle and combined parity; it ignores translation. An angle alone cannot represent reflection. Composition and inversion retain provenance entries/parent transform IDs.

`conventions_validated` is a derived, read-only result attribute, not a constructor argument. A raw matrix between different units, axis directions or declared origins has this flag false, even if the numbers appear correct or its provenance text claims conversion. `apply`, `map_orientation`, `inverse` and `compose` then reject with `MAPPING_UNVALIDATED`. This prevents an undeclared unit, axis or datum relationship from silently acting as normalization. Equal origin metadata declares a shared datum; origin descriptions are not parsed into physical positions.

Use `unit_conversion` for an explicit physical factor and `rotation`/`reflection` for an explicitly declared axis operation; their validated results may be composed and inverted. Translation alone is not axis-mapping evidence. These factories validate the declared numerical operation, not independent physical calibration or the truth of source metadata. Composition carries evidence only from two validated operands. Dataclass replacement reconstructs validation from scratch and cannot inherit a convention-change flag when replacing a matrix. No physical reflection is inferred from labels.

Rotation and reflection require a shared declared origin to become validated; the reflection offset specifies the mirror line, not a datum displacement. For distinct origins, compose the axis operation with an explicit `translation` between frames with matching units/axes. Its required `dx, dy` declare the source origin's coordinates in the target frame; explicitly supplying `(0, 0)` asserts coincidence rather than inferring it. Nonzero offsets and validated compositions/inverses preserve the declared datum relationship. Arbitrary provenance strings cannot supply this evidence.

Two validated `RIGID` operands compose to a rechecked `RIGID` result. Other combinations remain conservatively `AFFINE`, with parity computed from the matrix. A pair of reflections may numerically yield a proper rigid map, but this core does not promote it or a general affine input merely from determinant sign.

Direct construction accepts an explicit immutable 3x3 affine matrix with bottom row (0,0,1), subject to the convention-validation gate above. No unit factor is inserted automatically; a raw matrix across units remains unusable until represented through explicit validated operations. General affine algebra is available, but callers must not scale physical boards to force agreement between sources. `RIGID` enforces proper unit-scale isometry; `REFLECTION` enforces reversing parity and self-inverse geometry. Projective matrices and physical/pixel conversion are rejected pending camera calibration work.

## Numerical limits and remaining scope

This slice uses the numerical subset of proposed `synthetic-geometry-v1`: normalized linear-block spectral condition number <=1e8; test round-trip tolerance <=1e-6 mm. Isometry shape checks use absolute 1e-12 tolerance for binary64 roundoff. The condition calculation normalizes the 2x2 linear block by its maximum absolute coefficient, excluding translations. NaN/infinity, overflow, singular/ill-conditioned matrices, incompatible frames and invalid kinds fail explicitly. Calculations use binary64 without intermediate rounding; these test bounds are not a guarantee for arbitrary extreme coordinate magnitudes or measured hardware accuracy.

`Transform2.valid_domain` describes the finite affine plane, subject to representable output. The affine resolver has an explicit finite comparison rectangle; this is not a calibrated valid domain. Full configurable calibration policies, homographies, parser-driven multi-error import reports and targeting readiness remain unimplemented. Physical units are limited to declared mm/inch; unknown source units must be resolved before constructing frames.

The selected Sprint 1 affine resolver, capacity/envelope records, rectangle fixture checks and structured geometry diagnostics have executed evidence. Sprint exit and task checkbox changes still require review. KiCad/Gerber/placement/BOM imports, real fixtures, broader geometry, fiducial fitting, camera calibration, inspection REVIEW results and machine lifecycle validation remain open in their later sprint scopes. KiCad 10.0.7 remains an unverified target. See [implementation-status.md](openspec/changes/board-geometry-foundation/implementation-status.md) for per-task evidence and remaining obligations.

The current contextual affine resolver is exported as `TransformGraph`, `RectangleDomain`, `PathConsistencyPolicy`, and `ResolvedPath`. It follows only registered directed edges in a DAG, rejects cycles, enumerates all paths under resource limits, checks every rectangle corner using `synthetic-path-consistency-v1` (1e-6 mm default), and preserves the representative path plus all examined transform IDs. It does not synthesize inverse edges or handle pixel/projective/camera mappings.

## Structured geometry diagnostics (partial task 3.6)

`ContractError`, `SourceLocation`, and `ValidationReport` are immutable records exported from `aoi_platform.geometry`. Issues retain code, message, field path, remediation, artifact/entity IDs, optional one-based source row/column, expected/actual diagnostic text and explicit string key/value context. `GeometryError` remains a `ValueError` with the same code and field path, but its diagnostic payload is immutable. Resolver and `validate_fit` boundaries retain known request/frame/revision/machine/capture, transform/path, envelope/configuration and policy/domain evidence. Conflicts preserve separate expected/actual values; missing metadata is not inferred. `ContractError.from_geometry_error` automatically preserves this evidence and rejects conflicting caller additions. Source locations and artifact/entity provenance absent from the geometry request still need to be supplied by a future producer.

Resolver diagnostic policy `path-evidence-v1` bounds each path summary to 32 paths, 128 transform IDs total and 8192 UTF-8 bytes of encoded IDs, with explicit omitted counts. It preserves a deterministic prefix, not a complete path listing when truncated. An oversized registry is not scanned for diagnostics: its omitted edge count is recorded. These diagnostic limits do not relax search/comparison budgets and never turn failure into a usable result. Numeric helpers outside the resolver/fit boundaries retain only evidence actually available to them; no parser or calibration context is invented.

Reports retain all supplied issues, checks/results as diagnostic string pairs, policy/schema IDs, unresolved/conflicting fields and artifact digests. Blocking errors derive rejected status and forbid an accepted canonical digest. The implemented warning code is `OPTIONAL_DATA_ABSENT`; blocking geometry codes cannot be relabeled warnings. Accepted means no blocking issue was supplied to this report, not successful import/publication or validated geometry. Producers remain responsible for running required checks and emitting blocking errors for failed mandatory checks; diagnostic check strings are not executed as gate logic.

Implementation ordering convention (the spec requires stability but supplies no sort key): sort issues by canonical JSON of the complete issue, with lexicographically sorted keys, Unicode text and compact separators. Errors and warnings preserve that order separately. Evidence keys and field lists are sorted; duplicate issues are retained. `to_json()` is deterministic for the same report metadata and issue multiset, including ties. This is diagnostic serialization, not a board revision digest algorithm. Expected/actual values currently use text; complete import error vocabulary, typed policy results, parser collection and atomic publication remain open. No resolver policy is inferred from this ordering.
