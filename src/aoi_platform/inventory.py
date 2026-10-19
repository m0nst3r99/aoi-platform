"""Bounded byte admission. No format parsing, filesystem access or publication.

Factories are trusted application code: return a fresh blocking binary stream;
this function owns and closes it. Manifest source IDs are opaque lookup keys.
"""

from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import re
from typing import BinaryIO, TypeAlias

from .geometry.errors import ErrorCode, GeometryError, diagnostic_json
from .geometry.reports import ContractError, SourceLocation, ValidationReport

Evidence: TypeAlias = tuple[tuple[str, str], ...]
ByteSources: TypeAlias = Mapping[str, Callable[[], BinaryIO]]
SCHEMA = "artifact-inventory-v1"
MAX_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class ArtifactDeclaration:
    artifact_id: str
    role: str
    source_id: str
    declared_sha256: str
    declared_size: int | None = None
    sides: tuple[str, ...] = ()
    reference_only: bool = False
    metadata: Evidence = ()
    provenance: Evidence = ()


@dataclass(frozen=True, slots=True)
class InventoryManifest:
    profile: str
    artifacts: tuple[ArtifactDeclaration, ...]
    fixture_revision: str
    source_snapshot: str
    spi_sides: tuple[str, ...] = ()
    assembly_sides: tuple[str, ...] = ()
    schema_version: str = SCHEMA


@dataclass(frozen=True, slots=True)
class InventoryLimits:
    policy_id: str
    max_artifacts: int
    max_artifact_bytes: int
    max_total_bytes: int
    chunk_bytes: int


@dataclass(frozen=True, slots=True)
class ArtifactObservation:
    declaration: ArtifactDeclaration
    bytes_read: int
    eof: bool
    actual_size: int | None
    computed_sha256: str | None


@dataclass(frozen=True, slots=True)
class ArtifactInventory:
    manifest: InventoryManifest
    artifacts: tuple[ArtifactObservation, ...]


@dataclass(frozen=True, slots=True)
class InventorySuccess:
    inventory: ArtifactInventory
    report: ValidationReport

    def to_json(self) -> str:
        return diagnostic_json({"kind": "success", "inventory": asdict(self.inventory),
                                "report": self.report.to_dict()})


@dataclass(frozen=True, slots=True)
class InventoryFailure:
    report: ValidationReport
    evidence: tuple[ArtifactObservation, ...] = ()

    def to_json(self) -> str:
        return diagnostic_json({"kind": "failure", "evidence": [asdict(e) for e in self.evidence],
                                "report": self.report.to_dict()})


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _pairs(value: object) -> bool:
    return (isinstance(value, tuple)
            and all(isinstance(p, tuple) and len(p) == 2 and _text(p[0])
                    and isinstance(p[1], str) for p in value)
            and len({p[0] for p in value}) == len(value))


def inventory_artifacts(manifest: InventoryManifest, byte_sources: ByteSources,
                        limits: InventoryLimits) -> InventorySuccess | InventoryFailure:
    """Validate declarations then hash streams; failure never carries inventory.

    Schema errors avoid all I/O. Byte limits allow one sentinel byte to detect
    overflow at an exact boundary. Report acceptance is scoped to bytes only.
    """
    issues: list[ContractError] = []
    observed: list[ArtifactObservation] = []
    context: dict[str, str] = {"scope": "artifact-bytes-only"}
    policy = "inventory-invalid-policy"
    if isinstance(manifest, InventoryManifest):
        for key in ("fixture_revision", "source_snapshot", "profile"):
            value = getattr(manifest, key)
            if _text(value):
                context[key] = value
    if isinstance(limits, InventoryLimits):
        if _text(limits.policy_id):
            policy = limits.policy_id
        for key in ("max_artifacts", "max_artifact_bytes", "max_total_bytes", "chunk_bytes"):
            value = getattr(limits, key)
            if type(value) in (int, float, str, bool) or value is None:
                context[f"limits.{key}"] = str(value)
    context["policy_id"] = policy

    def issue(code: ErrorCode, path: str, message: str, a=None, *, expected=None,
              actual=None, extra: Evidence = ()) -> None:
        known = dict(context)
        artifact_id = source = None
        if isinstance(a, ArtifactDeclaration):
            for name in ("artifact_id", "role", "source_id"):
                value = getattr(a, name)
                if _text(value):
                    known[name] = value
            artifact_id = known.get("artifact_id")
            source = known.get("source_id")
        known.update(extra)
        error = GeometryError(code, message, field_path=path,
                              context=tuple(sorted(known.items())),
                              expected=None if expected is None else str(expected),
                              actual=None if actual is None else str(actual))
        issues.append(ContractError.from_geometry_error(
            error, remediation="Correct the declaration, source or explicit limits and retry.",
            artifact_id=artifact_id,
            source_location=SourceLocation(source or "inventory-manifest")))

    def finish(canonical=None):
        report = ValidationReport("artifact-inventory", policy, tuple(issues),
                                  (("scope", "artifact-bytes-only"),),
                                  context=tuple(sorted(context.items())))
        if issues:
            return InventoryFailure(report, tuple(observed))
        return InventorySuccess(ArtifactInventory(canonical, tuple(observed)), report)

    if not isinstance(limits, InventoryLimits):
        issue(ErrorCode.POLICY_INVALID, "limits", "Supply InventoryLimits.")
        return finish()
    for key in ("max_artifacts", "max_artifact_bytes", "max_total_bytes", "chunk_bytes"):
        value = getattr(limits, key)
        if type(value) is not int or value < 1 or (key == "chunk_bytes" and value > MAX_CHUNK_BYTES):
            issue(ErrorCode.POLICY_INVALID, f"limits.{key}", "Invalid positive integer limit.",
                  expected=f"1..{MAX_CHUNK_BYTES}" if key == "chunk_bytes" else "positive integer",
                  actual=str(value) if type(value) in (int, float, str, bool, type(None)) else type(value).__name__)
    if not _text(limits.policy_id):
        issue(ErrorCode.POLICY_INVALID, "limits.policy_id", "Supply a policy identity.")
    if issues:
        return finish()
    if not isinstance(manifest, InventoryManifest):
        issue(ErrorCode.SCHEMA_INVALID, "manifest", "Supply InventoryManifest.")
        return finish()
    if not isinstance(manifest.artifacts, tuple):
        issue(ErrorCode.SCHEMA_INVALID, "manifest.artifacts", "Supply an immutable artifact tuple.")
        return finish()
    if len(manifest.artifacts) > limits.max_artifacts:
        issue(ErrorCode.INPUT_LIMIT_EXCEEDED, "manifest.artifacts", "Artifact count exceeds budget.",
              expected=limits.max_artifacts, actual=len(manifest.artifacts))
        return finish()
    if not isinstance(byte_sources, Mapping):
        issue(ErrorCode.SCHEMA_INVALID, "byte_sources", "Supply an explicit source factory mapping.")
    if manifest.schema_version != SCHEMA:
        issue(ErrorCode.SCHEMA_INVALID, "manifest.schema_version", "Unknown inventory schema.",
              expected=SCHEMA, actual=manifest.schema_version if isinstance(manifest.schema_version, str) else None)
    for key in ("fixture_revision", "source_snapshot"):
        if not _text(getattr(manifest, key)):
            issue(ErrorCode.SCHEMA_INVALID, f"manifest.{key}", "Supply declared provenance identity.")
    profiles = ("geometry", "spi-2d", "post-placement-2d", "combined")
    if manifest.profile not in profiles:
        issue(ErrorCode.FORMAT_UNSUPPORTED, "manifest.profile", "Unsupported profile.",
              actual=manifest.profile if isinstance(manifest.profile, str) else None)

    def sides(value, path, a=None):
        if not isinstance(value, tuple):
            issue(ErrorCode.SCHEMA_INVALID, path, "Supply an immutable side tuple.", a)
            return False
        valid = True
        for side in value:
            if side not in ("top", "bottom"):
                issue(ErrorCode.FORMAT_UNSUPPORTED, path, "Unsupported side.", a,
                      actual=side if isinstance(side, str) else None)
                valid = False
        if valid and len(set(value)) != len(value):
            issue(ErrorCode.SCHEMA_INVALID, path, "Duplicate side declaration.", a)
            valid = False
        return valid

    for key, active in (("spi_sides", manifest.profile in ("spi-2d", "combined")),
                        ("assembly_sides", manifest.profile in ("post-placement-2d", "combined"))):
        value = getattr(manifest, key)
        if sides(value, f"manifest.{key}") and manifest.profile in profiles:
            if bool(value) != active:
                issue(ErrorCode.SCHEMA_INVALID, f"manifest.{key}",
                      "Active inspection requires sides; inactive inspection requires none.")

    declarations = []
    for a in manifest.artifacts:
        if not isinstance(a, ArtifactDeclaration):
            issue(ErrorCode.SCHEMA_INVALID, "manifest.artifacts", "Supply ArtifactDeclaration records.")
            continue
        # ID-addressed fields are stable under input permutation (no row index).
        path = f"artifacts[{diagnostic_json(a.artifact_id)}]" if _text(a.artifact_id) else "artifacts"
        count = len(issues)
        for key in ("artifact_id", "source_id"):
            if not _text(getattr(a, key)):
                issue(ErrorCode.SCHEMA_INVALID, f"{path}.{key}", "Supply a nonempty identity.", a)
        if a.role not in ("kicad_pcb", "paste", "placement", "bom", "supporting"):
            issue(ErrorCode.FORMAT_UNSUPPORTED, f"{path}.role", "Unsupported role.", a,
                  actual=a.role if isinstance(a.role, str) else None)
        if type(a.reference_only) is not bool:
            issue(ErrorCode.SCHEMA_INVALID, f"{path}.reference_only", "Supply a boolean.", a)
        if a.role == "supporting" and a.reference_only is not True:
            issue(ErrorCode.SCHEMA_INVALID, f"{path}.reference_only", "Supporting artifacts must be reference-only.", a)
        if sides(a.sides, f"{path}.sides", a):
            if ((a.role == "paste" and len(a.sides) != 1)
                    or (a.role in ("placement", "bom") and not a.sides)
                    or (a.role == "kicad_pcb" and a.sides)):
                issue(ErrorCode.SCHEMA_INVALID, f"{path}.sides", "Side coverage conflicts with role schema.", a)
        if not isinstance(a.declared_sha256, str) or re.fullmatch(r"[a-fA-F0-9]{64}", a.declared_sha256) is None:
            issue(ErrorCode.SCHEMA_INVALID, f"{path}.declared_sha256", "Supply 64 hexadecimal SHA-256 digits.", a,
                  actual=a.declared_sha256 if isinstance(a.declared_sha256, str) else None)
        if a.declared_size is not None and (type(a.declared_size) is not int or a.declared_size < 0):
            issue(ErrorCode.SCHEMA_INVALID, f"{path}.declared_size", "Supply a nonnegative integer or None.", a)
        for key in ("metadata", "provenance"):
            if not _pairs(getattr(a, key)):
                issue(ErrorCode.SCHEMA_INVALID, f"{path}.{key}", "Supply immutable unique string key/value pairs.", a)
        if len(issues) == count:
            declarations.append(replace(a, sides=tuple(sorted(a.sides)),
                                        metadata=tuple(sorted(a.metadata)), provenance=tuple(sorted(a.provenance))))
    ids = Counter(a.artifact_id for a in manifest.artifacts
                  if isinstance(a, ArtifactDeclaration) and _text(a.artifact_id))
    for a in manifest.artifacts:
        if isinstance(a, ArtifactDeclaration) and _text(a.artifact_id) and ids[a.artifact_id] > 1:
            issue(ErrorCode.DUPLICATE_ID, "manifest.artifacts.artifact_id", "Artifact identity is duplicated.", a,
                  expected=1, actual=ids[a.artifact_id])
    if issues:
        return finish()
    declarations.sort(key=lambda a: a.artifact_id)
    canonical = replace(manifest, artifacts=tuple(declarations), spi_sides=tuple(sorted(manifest.spi_sides)),
                        assembly_sides=tuple(sorted(manifest.assembly_sides)))
    required = [("kicad_pcb", None)]
    required.extend(("paste", side) for side in canonical.spi_sides)
    required.extend((role, side) for side in canonical.assembly_sides for role in ("placement", "bom"))
    for role, side in required:
        if not any(a.role == role and not a.reference_only and (side is None or side in a.sides) for a in declarations):
            issue(ErrorCode.REQUIRED_ARTIFACT_MISSING, "manifest.artifacts", "Required participating role is absent.",
                  expected=role if side is None else f"{role}:{side}", extra=(("required_role", role),))
    # Coverage failures are declaration failures: no source needs to be opened.
    if issues:
        return finish()

    total = 0
    for a in declarations:
        path = f"artifacts[{diagnostic_json(a.artifact_id)}]"
        stream = None
        read = 0
        eof = False
        stop = False
        digest = sha256()
        stage = "open"
        try:
            try:
                factory = byte_sources[a.source_id]
            except KeyError:
                issue(ErrorCode.SOURCE_NOT_FOUND, f"{path}.source_id", "Byte source is not registered.", a,
                      expected=a.source_id)
                continue
            stream = factory()
            if not callable(getattr(stream, "read", None)) or not callable(getattr(stream, "close", None)):
                issue(ErrorCode.SOURCE_IO_ERROR, f"{path}.source_id", "Factory must return an owned binary stream.", a)
                stop = True
            else:
                stage = "read"
                while True:
                    n = min(limits.chunk_bytes, limits.max_artifact_bytes - read + 1,
                            limits.max_total_bytes - total + 1)
                    data = stream.read(n)
                    if not isinstance(data, bytes) or len(data) > n:
                        issue(ErrorCode.SOURCE_IO_ERROR, f"{path}.source_id", "Stream violated bounded binary read protocol.", a,
                              expected=f"bytes of length <= {n}", actual=type(data).__name__)
                        stop = True
                        break
                    if not data:
                        eof = True
                        break
                    read += len(data)
                    total += len(data)
                    for key, actual, limit in (("max_artifact_bytes", read, limits.max_artifact_bytes),
                                               ("max_total_bytes", total, limits.max_total_bytes)):
                        if actual > limit:
                            issue(ErrorCode.INPUT_LIMIT_EXCEEDED, f"limits.{key}", "Actual bytes exceed budget.", a,
                                  expected=limit, actual=actual)
                            stop = True
                    if stop:
                        break
                    digest.update(data)
        except Exception as exc:
            issue(ErrorCode.SOURCE_NOT_FOUND if isinstance(exc, FileNotFoundError) and stage == "open"
                  else ErrorCode.SOURCE_IO_ERROR, f"{path}.source_id", "Source operation failed.", a,
                  extra=(("io_stage", stage), ("exception_type", type(exc).__name__)))
        finally:
            if stream is not None:
                try:
                    stream.close()
                except Exception as exc:
                    issue(ErrorCode.SOURCE_IO_ERROR, f"{path}.source_id", "Source close failed.", a,
                          extra=(("io_stage", "close"), ("exception_type", type(exc).__name__)))
                    stop = True
        observed.append(ArtifactObservation(a, read, eof, read if eof else None, digest.hexdigest() if eof else None))
        if eof:
            if a.declared_size is not None and a.declared_size != read:
                issue(ErrorCode.SOURCE_CONFLICT, f"{path}.declared_size", "Declared size differs from bytes.", a,
                      expected=a.declared_size, actual=read)
            if a.declared_sha256.lower() != digest.hexdigest():
                issue(ErrorCode.SOURCE_CONFLICT, f"{path}.declared_sha256", "Declared hash differs from bytes.", a,
                      expected=a.declared_sha256, actual=digest.hexdigest())
        if stop:
            break
    return finish(canonical)
