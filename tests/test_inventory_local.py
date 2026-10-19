"""Opt-in accepted-bundle byte test; never a parser or acquisition gate test.

Set AOI_REAL_PCB_01_ROOT to an existing REAL-PCB-01-r1 directory. Nothing is
copied into the repository. Normal test runs skip without this environment key.
"""
import json
import os
from pathlib import Path

import pytest

from aoi_platform.inventory import (
    ArtifactDeclaration, InventoryManifest, InventoryLimits,
    InventorySuccess, inventory_artifacts,
)


@pytest.mark.skipif(not os.environ.get("AOI_REAL_PCB_01_ROOT"), reason="Local accepted fixture is opt-in")
def test_real_pcb_01_r1_bytes():
    root = Path(os.environ["AOI_REAL_PCB_01_ROOT"]).resolve(strict=True)
    def bounded_path(relative):
        path = (root / relative).resolve(strict=True)
        assert path.is_relative_to(root) and path.is_file()
        return path
    # Fixed evidence files; no fixture scripts, geometry or external tools run.
    ledger = json.loads(bounded_path("manifest.json").read_text(encoding="utf-8"))
    population = json.loads(bounded_path("population.json").read_text(encoding="utf-8"))
    assert ledger["fixture_revision"] == "REAL-PCB-01-r1"
    assert len(population) == 57
    assert sum(p["retain_fiducial_data"] for p in population) == 3
    assert sum(p["assembly_target_eligible"] for p in population) == 28
    roles = {
        "source/Edgeberry.kicad_pcb": ("kicad_pcb", (), False),
        "exports/gerber/Edgeberry-F_Paste.gbr": ("paste", ("top",), False),
        "exports/placement/Edgeberry-all-pos.csv": ("placement", ("top", "bottom"), False),
        "exports/bom/Edgeberry-bom.csv": ("bom", ("top", "bottom"), False),
        "before/exports/gerber/Edgeberry-B_Paste.gbr": ("paste", ("bottom",), True),
    }
    declarations, factories, expected = [], {}, {}
    for line in bounded_path("SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        assert relative not in expected
        path = bounded_path(relative)
        role, sides, reference = roles.get(relative, ("supporting", (), True))
        declarations.append(ArtifactDeclaration(
            relative, role, relative, digest, declared_size=None, sides=sides,
            reference_only=reference,
            metadata=(("conventions_declared", json.dumps(ledger["conventions"], sort_keys=True)),),
            provenance=(("fixture_revision", ledger["fixture_revision"]),
                        ("relative_source", relative))))
        # Explicit root-checked allowlist, no adapter accepting arbitrary paths.
        factories[relative] = lambda path=path: path.open("rb")
        expected[relative] = digest
    m = InventoryManifest("combined", tuple(declarations), "REAL-PCB-01-r1", str(root / "source"),
                          spi_sides=("top",), assembly_sides=("top", "bottom"))
    limits = InventoryLimits("local-byte-verification-v1", 32, 4 * 1024 * 1024,
                             16 * 1024 * 1024, 4096)
    result = inventory_artifacts(m, factories, limits)
    assert isinstance(result, InventorySuccess), result.report.to_json()
    assert len(result.inventory.artifacts) == 25
    assert {a.declaration.artifact_id: a.computed_sha256 for a in result.inventory.artifacts} == expected
    bottom = next(a for a in result.inventory.artifacts if a.declaration.role == "paste" and a.declaration.sides == ("bottom",))
    assert bottom.declaration.reference_only
    assert result.report.canonical_digest is None
    print("REAL-PCB-01-r1: 25 streamed artifacts; bytes =", sum(a.actual_size for a in result.inventory.artifacts))
