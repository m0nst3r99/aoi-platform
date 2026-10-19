"""Portable byte-level oracles; no KiCad or local fixture dependency."""
from dataclasses import FrozenInstanceError, replace
from io import BytesIO

import pytest

from aoi_platform.inventory import (
    ArtifactDeclaration as Artifact, InventoryManifest as Manifest,
    InventoryLimits as Limits, InventorySuccess, InventoryFailure,
    inventory_artifacts,
)
from aoi_platform.geometry.errors import ErrorCode

ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
LIMITS = Limits("test-byte-policy-v1", 12, 20, 60, 2)


def artifact(name="pcb", **kwargs):
    return replace(Artifact(name, "kicad_pcb", name, ABC), **kwargs)


def manifest(*artifacts, **kwargs):
    return replace(Manifest("geometry", artifacts or (artifact(),), "fixture-r1", "fixed/source"), **kwargs)


def run(m=None, sources=None, limits=LIMITS):
    m = m or manifest()
    if sources is None:
        sources = {a.source_id: lambda: BytesIO(b"abc") for a in m.artifacts}
    return inventory_artifacts(m, sources, limits)


def failure(result, code):
    assert isinstance(result, InventoryFailure)
    assert not hasattr(result, "inventory")
    assert result.report.status == "rejected"
    assert code in [e.code for e in result.report.errors]
    return result


def test_success_preserves_declaration_separately_from_bytes_and_is_immutable():
    a = artifact(declared_size=3, declared_sha256=ABC.upper(),
                 metadata=(("units", "mm"), ("unknown", "")),
                 provenance=(("source", "reviewed snapshot"),))
    result = run(manifest(a))
    assert isinstance(result, InventorySuccess)
    record, = result.inventory.artifacts
    assert record.actual_size == record.bytes_read == 3
    assert record.computed_sha256 == ABC
    assert record.declaration.declared_sha256 == ABC.upper()
    assert dict(record.declaration.metadata) == {"units": "mm", "unknown": ""}
    assert record.eof is True
    assert result.inventory.manifest.fixture_revision == "fixture-r1"
    assert result.report.canonical_digest is None
    assert dict(result.report.checks)["scope"] == "artifact-bytes-only"
    with pytest.raises(FrozenInstanceError):
        record.actual_size = 4


def test_zero_bytes_is_valid_inventory_not_geometry_proof():
    result = run(manifest(artifact(declared_size=0, declared_sha256=EMPTY)), {"pcb": lambda: BytesIO()})
    assert isinstance(result, InventorySuccess)
    assert result.inventory.artifacts[0].actual_size == 0


@pytest.mark.parametrize("profile,spi,assembly", [
    ("geometry", (), ()), ("spi-2d", ("top",), ()),
    ("post-placement-2d", (), ("top", "bottom")),
    ("combined", ("top", "bottom"), ("top", "bottom")),
])
def test_profile_minimums_and_multiple_artifacts_same_role(profile, spi, assembly):
    arts = [artifact(), artifact("pcb2")]
    arts += [artifact(s, role="paste", sides=(s,)) for s in spi]
    arts += [artifact(r, role=r, sides=assembly) for r in ("bom", "placement")] if assembly else []
    m = manifest(*arts, profile=profile, spi_sides=spi, assembly_sides=assembly)
    assert isinstance(run(m), InventorySuccess)
    for role in {a.role for a in arts}:
        absent = replace(m, artifacts=tuple(a for a in arts if a.role != role))
        failure(run(absent), ErrorCode.REQUIRED_ARTIFACT_MISSING)


def test_reference_only_never_satisfies_required_side_and_is_still_checked():
    top = artifact("top", role="paste", sides=("top",))
    bottom = artifact("bottom", role="paste", sides=("bottom",), reference_only=True)
    m = manifest(artifact(), top, bottom, profile="spi-2d", spi_sides=("top",))
    assert isinstance(run(m), InventorySuccess)
    failure(run(replace(m, spi_sides=("bottom",))), ErrorCode.REQUIRED_ARTIFACT_MISSING)
    failure(run(replace(m, artifacts=(artifact(), top, replace(bottom, declared_sha256=EMPTY)))), ErrorCode.SOURCE_CONFLICT)


@pytest.mark.parametrize("change,code", [
    ({"profile": "guess"}, ErrorCode.FORMAT_UNSUPPORTED),
    ({"profile": []}, ErrorCode.FORMAT_UNSUPPORTED),
    ({"schema_version": "bad"}, ErrorCode.SCHEMA_INVALID),
    ({"fixture_revision": ""}, ErrorCode.SCHEMA_INVALID),
    ({"source_snapshot": None}, ErrorCode.SCHEMA_INVALID),
    ({"artifacts": []}, ErrorCode.SCHEMA_INVALID),
    ({"spi_sides": ("left",)}, ErrorCode.FORMAT_UNSUPPORTED),
    ({"assembly_sides": ("left",)}, ErrorCode.FORMAT_UNSUPPORTED),
    ({"spi_sides": ("top",)}, ErrorCode.SCHEMA_INVALID),
    ({"profile": "spi-2d"}, ErrorCode.SCHEMA_INVALID),
    ({"spi_sides": ("top", "top")}, ErrorCode.SCHEMA_INVALID),
])
def test_invalid_manifest_before_io(change, code):
    failure(run(replace(manifest(), **change), {}), code)


@pytest.mark.parametrize("change,code", [
    ({"role": "gerber-guessed"}, ErrorCode.FORMAT_UNSUPPORTED),
    ({"sides": ("left",)}, ErrorCode.FORMAT_UNSUPPORTED),
    ({"sides": ["top"]}, ErrorCode.SCHEMA_INVALID),
    ({"role": "paste", "sides": ("top", "bottom")}, ErrorCode.SCHEMA_INVALID),
    ({"role": "placement"}, ErrorCode.SCHEMA_INVALID),
    ({"role": "supporting"}, ErrorCode.SCHEMA_INVALID),
    ({"source_id": ""}, ErrorCode.SCHEMA_INVALID),
    ({"artifact_id": None}, ErrorCode.SCHEMA_INVALID),
    ({"declared_sha256": "g" * 64}, ErrorCode.SCHEMA_INVALID),
    ({"declared_sha256": None}, ErrorCode.SCHEMA_INVALID),
    ({"declared_sha256": "0" * 63}, ErrorCode.SCHEMA_INVALID),
    ({"declared_size": True}, ErrorCode.SCHEMA_INVALID),
    ({"declared_size": -1}, ErrorCode.SCHEMA_INVALID),
    ({"reference_only": 1}, ErrorCode.SCHEMA_INVALID),
    ({"metadata": {"units": "mm"}}, ErrorCode.SCHEMA_INVALID),
    ({"metadata": (("units", "mm"), ("units", "inch"))}, ErrorCode.SCHEMA_INVALID),
    ({"provenance": (("p", []),)}, ErrorCode.SCHEMA_INVALID),
])
def test_invalid_artifact_before_io(change, code):
    failure(run(manifest(artifact(**change)), {}), code)


def test_duplicate_identical_ids_preserve_both_diagnostics():
    r = failure(run(manifest(artifact(), artifact()), {}), ErrorCode.DUPLICATE_ID)
    assert len(r.report.errors) == 2
    assert r.report.errors[0] == r.report.errors[1]


def test_hash_and_size_mismatch_expected_actual_context_and_order():
    r = failure(run(manifest(artifact(declared_sha256=EMPTY, declared_size=1))), ErrorCode.SOURCE_CONFLICT)
    assert len(r.report.errors) == 2
    assert {e.expected for e in r.report.errors} == {EMPTY, "1"}
    assert {e.actual for e in r.report.errors} == {ABC, "3"}
    for e in r.report.errors:
        assert e.artifact_id == e.source_location.source == "pcb"
        c = dict(e.context)
        assert c["role"] == "kicad_pcb"
        assert c["fixture_revision"] == "fixture-r1"
        assert c["limits.max_total_bytes"] == "60"
    assert r.evidence[0].computed_sha256 == ABC


@pytest.mark.parametrize("key", ["max_artifacts", "max_artifact_bytes", "max_total_bytes", "chunk_bytes"])
@pytest.mark.parametrize("value", [0, -1, True, 1.5, None])
def test_invalid_limits(key, value):
    failure(run(limits=replace(LIMITS, **{key: value})), ErrorCode.POLICY_INVALID)


def test_invalid_chunk_ceiling_and_policy_and_boundary_inputs():
    failure(run(limits=replace(LIMITS, chunk_bytes=1024 * 1024 + 1)), ErrorCode.POLICY_INVALID)
    failure(run(limits=replace(LIMITS, policy_id="")), ErrorCode.POLICY_INVALID)
    failure(inventory_artifacts({}, {}, LIMITS), ErrorCode.SCHEMA_INVALID)
    failure(inventory_artifacts(manifest(), {}, None), ErrorCode.POLICY_INVALID)
    failure(inventory_artifacts(manifest(), [], LIMITS), ErrorCode.SCHEMA_INVALID)
    failure(inventory_artifacts(manifest(object()), {}, LIMITS), ErrorCode.SCHEMA_INVALID)


class Tracked(BytesIO):
    def __init__(self, data, short=False):
        super().__init__(data)
        self.requests = []
        self.closed_count = 0
        self.short = short

    def read(self, n):
        self.requests.append(n)
        return super().read(min(n, 1) if self.short else n)

    def close(self):
        self.closed_count += 1
        super().close()


def test_boundaries_streaming_short_reads_and_ownership():
    for chunk in (1, 3, 1024 * 1024):
        s = Tracked(b"abc", short=True)
        r = run(sources={"pcb": lambda: s}, limits=Limits("exact", 1, 3, 3, chunk))
        assert isinstance(r, InventorySuccess)
        assert s.closed_count == 1 and s.closed
        assert max(s.requests) <= min(chunk, 4)
    failure(run(manifest(artifact(), artifact("b")), limits=replace(LIMITS, max_artifacts=1)), ErrorCode.INPUT_LIMIT_EXCEEDED)


@pytest.mark.parametrize("key", ["max_artifact_bytes", "max_total_bytes"])
def test_byte_overrun_at_limit_plus_one_stops_all_reads(key):
    stream = Tracked(b"abc" + b"x" * 10000)
    opened = []
    def later():
        opened.append(True)
        return BytesIO(b"abc")
    r = failure(run(manifest(artifact("a", declared_size=1), artifact("z")),
                    {"a": lambda: stream, "z": later}, replace(LIMITS, **{key: 3})), ErrorCode.INPUT_LIMIT_EXCEEDED)
    assert not opened
    assert r.evidence[0].bytes_read == 4
    assert r.evidence[0].actual_size is None and r.evidence[0].computed_sha256 is None
    assert stream.closed_count == 1
    assert sum(stream.requests) == 4


def test_aggregate_boundary_counts_multiple_sources():
    m = manifest(artifact("a"), artifact("b"))
    assert isinstance(run(m, limits=replace(LIMITS, max_total_bytes=6)), InventorySuccess)
    r = failure(run(m, limits=replace(LIMITS, max_total_bytes=5)), ErrorCode.INPUT_LIMIT_EXCEEDED)
    assert sum(e.bytes_read for e in r.evidence) == 6


def test_source_missing_open_failure_read_failure_and_close_failure():
    failure(run(sources={}), ErrorCode.SOURCE_NOT_FOUND)
    def missing():
        raise FileNotFoundError("do not put OS path in report")
    failure(run(sources={"pcb": missing}), ErrorCode.SOURCE_NOT_FOUND)
    def denied():
        raise PermissionError("secret")
    failure(run(sources={"pcb": denied}), ErrorCode.SOURCE_IO_ERROR)

    class Broken(Tracked):
        def read(self, n):
            if self.tell():
                raise OSError("secret")
            return super().read(n)
    s = Broken(b"abc")
    r = failure(run(sources={"pcb": lambda: s}), ErrorCode.SOURCE_IO_ERROR)
    assert s.closed_count == 1 and r.evidence[0].bytes_read == 2
    assert r.evidence[0].computed_sha256 is None
    assert "secret" not in r.to_json()

    class BadClose(Tracked):
        def close(self):
            super().close()
            raise OSError("close")
    s = BadClose(b"abc")
    failure(run(sources={"pcb": lambda: s}), ErrorCode.SOURCE_IO_ERROR)
    assert s.closed_count == 1


@pytest.mark.parametrize("data", [None, "abc", b"way too many bytes"])
def test_bad_binary_protocol_never_succeeds(data):
    class Bad(Tracked):
        def read(self, n):
            return data
    s = Bad(b"")
    failure(run(sources={"pcb": lambda: s}), ErrorCode.SOURCE_IO_ERROR)
    assert s.closed_count == 1


def test_failed_read_bytes_still_consume_aggregate_budget_and_independent_sources_checked():
    class Partial(Tracked):
        def read(self, n):
            if self.tell():
                raise OSError()
            return super().read(n)
    s = Partial(b"abc")
    r = run(manifest(artifact("a"), artifact("b")), {"a": lambda: s, "b": lambda: BytesIO(b"abc")},
            replace(LIMITS, max_total_bytes=4))
    failure(r, ErrorCode.SOURCE_IO_ERROR)
    failure(r, ErrorCode.INPUT_LIMIT_EXCEEDED)
    assert sum(e.bytes_read for e in r.evidence) == 5


@pytest.mark.parametrize("bad", [False, True])
def test_manifest_mapping_and_metadata_order_do_not_change_serialization(bad):
    a = artifact("a", declared_size=1 if bad else 3, metadata=(("z", "2"), ("a", "1")))
    b = artifact("b", declared_sha256=EMPTY if bad else ABC)
    first = run(manifest(a, b), {"a": lambda: BytesIO(b"abc"), "b": lambda: BytesIO(b"abc")})
    second = run(manifest(b, replace(a, metadata=tuple(reversed(a.metadata)))),
                 {"b": lambda: BytesIO(b"abc"), "a": lambda: BytesIO(b"abc")})
    assert first.to_json() == second.to_json()


def test_duplicate_and_malformed_declarations_have_stable_reports():
    a, b = artifact("dup", declared_sha256="bad"), artifact("dup", source_id="other")
    assert run(manifest(a, b), {}).to_json() == run(manifest(b, a), {}).to_json()


def test_unused_factory_never_opened_and_source_identity_is_not_a_path():
    def unused():
        pytest.fail("Unregistered artifact must not cause source opening")
    result = run(manifest(artifact(source_id="https://opaque/id")),
                 {"https://opaque/id": lambda: BytesIO(b"abc"), "unused": unused})
    assert isinstance(result, InventorySuccess)


def test_failure_after_successful_read_is_not_partial_success():
    result = run(manifest(artifact("a"), artifact("missing")), {"a": lambda: BytesIO(b"abc")})
    failure(result, ErrorCode.SOURCE_NOT_FOUND)
    assert result.evidence[0].computed_sha256 == ABC


def test_close_failure_stops_independent_sources():
    class Broken(Tracked):
        def close(self):
            super().close()
            raise OSError()
    s = Broken(b"abc")
    def never():
        pytest.fail("Cannot continue after losing resource ownership")
    failure(run(manifest(artifact("a"), artifact("b")), {"a": lambda: s, "b": never}), ErrorCode.SOURCE_IO_ERROR)


def test_resource_failure_order_is_stable_and_duplicate_roles_are_not_ids():
    a, b = artifact("a"), artifact("b")
    limits = replace(LIMITS, max_total_bytes=3)
    assert run(manifest(a, b), limits=limits).to_json() == run(manifest(b, a), limits=limits).to_json()


def test_schema_rejection_opens_nothing_even_when_other_artifacts_valid():
    def never():
        pytest.fail("Schema gate must precede I/O")
    failure(run(manifest(artifact(), artifact("bad", declared_sha256="bad")),
                {"pcb": never, "bad": never}), ErrorCode.SCHEMA_INVALID)
