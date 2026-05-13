"""Mesh package manifest and artifact writer."""

from __future__ import annotations

from pathlib import Path

from kayakgen.eval.mesh_package import (
    MeshPackageManifest,
    open_wetted_surface_profile,
    write_mesh_package,
)
from kayakgen.model.hull import Hull


def test_open_wetted_surface_profile_is_not_watertight() -> None:
    profile = open_wetted_surface_profile()

    assert profile.profile_name == "open_wetted_surface_resistance_v1"
    assert profile.requires_watertight is False
    assert profile.waterline_boundary_policy == "open_waterline_allowed"


def test_write_mesh_package_creates_manifest_and_artifacts(tmp_path: Path) -> None:
    manifest = write_mesh_package(Hull(), tmp_path, stations=12)

    expected = {
        "manifest.json",
        "hull.json",
        "quality.hull.json",
        "quality.deck.json",
        "hull.stl",
        "deck.stl",
    }
    assert expected <= {path.name for path in tmp_path.iterdir()}
    assert manifest.hull_hash == Hull().hash()
    assert manifest.units == "m"
    assert manifest.coordinate_system.x.startswith("longitudinal, stern positive")
    assert manifest.coordinate_system.waterline_z_m == 0.0
    assert manifest.parts == ["hull", "deck"]
    assert manifest.hull_json == "hull.json"
    assert manifest.quality_reports == {
        "hull": "quality.hull.json",
        "deck": "quality.deck.json",
    }
    assert manifest.surfaces == {
        "hull": "hull.stl",
        "deck": "deck.stl",
    }
    assert manifest.readiness.level == "cfd_surface_candidate"
    assert "cfd_ready" in " ".join(manifest.warnings)


def test_mesh_package_manifest_round_trips_from_json(tmp_path: Path) -> None:
    manifest = write_mesh_package(Hull(), tmp_path, stations=8)
    loaded = MeshPackageManifest.model_validate_json((tmp_path / "manifest.json").read_text())

    assert loaded == manifest
    assert loaded.solver_profile.requires_watertight is False
    assert loaded.readiness.level != "cfd_ready"


def test_mesh_package_uses_relative_manifest_paths(tmp_path: Path) -> None:
    manifest = write_mesh_package(Hull(), tmp_path, stations=8)
    paths = [manifest.hull_json, *manifest.quality_reports.values(), *manifest.surfaces.values()]

    assert all("/" not in path for path in paths)
    assert all(not Path(path).is_absolute() for path in paths)
