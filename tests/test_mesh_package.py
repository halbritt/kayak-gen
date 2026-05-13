"""Mesh package manifest and artifact writer."""

from __future__ import annotations

from pathlib import Path

from kayakgen.eval.mesh_package import (
    MeshPackageManifest,
    open_wetted_surface_profile,
    watertight_solid_profile,
    write_mesh_package,
)
from kayakgen.model.hull import Hull


def test_open_wetted_surface_profile_is_not_watertight() -> None:
    profile = open_wetted_surface_profile()

    assert profile.profile_name == "open_wetted_surface_resistance_v1"
    assert profile.requires_watertight is False
    assert profile.waterline_boundary_policy == "open_waterline_allowed"


def test_watertight_solid_profile_is_blocked_for_current_open_surfaces() -> None:
    profile = watertight_solid_profile()

    assert profile.profile_name == "watertight_solid_resistance_v1"
    assert profile.requires_watertight is True
    assert profile.waterline_boundary_policy == "closed_volume_required"
    assert profile.normal_orientation == "outward"


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
    assert "bow negative" in manifest.coordinate_system.x
    assert "-L/2 to +L/2" in manifest.coordinate_system.x
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


def test_watertight_profile_package_stays_below_cfd_ready(tmp_path: Path) -> None:
    manifest = write_mesh_package(
        Hull(),
        tmp_path,
        stations=12,
        solver_profile=watertight_solid_profile(),
    )

    assert manifest.solver_profile.profile_name == "watertight_solid_resistance_v1"
    assert manifest.solver_profile.requires_watertight is True
    assert manifest.readiness.level == "stl_surface"
    warning_text = " ".join(manifest.warnings)
    assert "requires zero boundary edges" in warning_text
    assert "closed combined hull/deck volume" in warning_text
    assert "separate open surfaces" in warning_text


def test_mixed_rake_open_package_does_not_claim_cfd_ready(tmp_path: Path) -> None:
    manifest = write_mesh_package(
        Hull(bow_rake=0.0, stern_rake=1.0),
        tmp_path,
        stations=12,
    )

    assert manifest.readiness.level == "cfd_surface_candidate"
    assert "cfd_ready" in " ".join(manifest.warnings)


def test_mixed_rake_watertight_profile_keeps_open_surface_boundary(tmp_path: Path) -> None:
    manifest = write_mesh_package(
        Hull(bow_rake=0.0, stern_rake=1.0),
        tmp_path,
        stations=12,
        solver_profile=watertight_solid_profile(),
    )

    assert manifest.readiness.level == "stl_surface"
    warning_text = " ".join(manifest.warnings)
    assert "requires zero boundary edges" in warning_text
    assert "current package writer emits separate open surfaces" in warning_text


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
