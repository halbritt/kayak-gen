"""Mesh package manifest and artifact writer."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from kayakgen.eval.mesh_diagnostics import (
    MeshDiagnostics,
    MeshReadiness,
    MeshSolverProfile,
    diagnose_mesh,
)
from kayakgen.io.json import save_hull
from kayakgen.io.stl import write_stl
from kayakgen.model.geometry import PartType
from kayakgen.model.hull import Hull

PackagePart = Literal["hull", "deck"]


class MeshPackageCoordinateSystem(BaseModel):
    """Machine-readable coordinate convention for mesh packages."""

    model_config = ConfigDict(extra="forbid")

    x: str = "longitudinal, stern positive, bow negative, spans -L/2 to +L/2"
    y: str = "port/starboard"
    z: str = "up positive"
    waterline_z_m: float = 0.0


class MeshPackageManifest(BaseModel):
    """Manifest for a deterministic mesh package."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    hull_hash: str
    units: Literal["m"] = "m"
    coordinate_system: MeshPackageCoordinateSystem = Field(
        default_factory=MeshPackageCoordinateSystem
    )
    solver_profile: MeshSolverProfile
    readiness: MeshReadiness
    parts: list[PackagePart]
    hull_json: str
    quality_reports: dict[PackagePart, str]
    surfaces: dict[PackagePart, str]
    warnings: list[str] = Field(default_factory=list)


def open_wetted_surface_profile() -> MeshSolverProfile:
    """Return the first explicitly accepted open-surface solver profile."""
    return MeshSolverProfile(
        profile_name="open_wetted_surface_resistance_v1",
        requires_watertight=False,
        accepted_parts=("hull", "deck"),
        normal_orientation="consistent",
        waterline_boundary_policy="open_waterline_allowed",
        max_nonmanifold_edges=0,
    )


def write_mesh_package(
    hull: Hull,
    out_dir: str | Path,
    *,
    parts: tuple[PackagePart, ...] = ("hull", "deck"),
    stations: int | None = None,
    solver_profile: MeshSolverProfile | None = None,
) -> MeshPackageManifest:
    """Write a deterministic mesh package and return its manifest."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    profile = solver_profile or open_wetted_surface_profile()

    hull_path = out / "hull.json"
    save_hull(hull, hull_path)

    quality_reports: dict[PackagePart, str] = {}
    surfaces: dict[PackagePart, str] = {}
    diagnostics_by_part: dict[PackagePart, MeshDiagnostics] = {}
    for part in parts:
        diagnostics = diagnose_mesh(hull, part=part, stations=stations)
        diagnostics_by_part[part] = diagnostics
        quality_path = out / f"quality.{part}.json"
        surface_path = out / f"{part}.stl"
        quality_path.write_text(diagnostics.model_dump_json(indent=2))
        write_stl(hull, part, surface_path)
        quality_reports[part] = quality_path.name
        surfaces[part] = surface_path.name

    readiness = _package_readiness(diagnostics_by_part, profile)
    manifest = MeshPackageManifest(
        hull_hash=hull.hash(),
        solver_profile=profile,
        readiness=readiness,
        parts=list(parts),
        hull_json=hull_path.name,
        quality_reports=quality_reports,
        surfaces=surfaces,
        warnings=readiness.reasons,
    )
    (out / "manifest.json").write_text(manifest.model_dump_json(indent=2))
    return manifest


def _package_readiness(
    diagnostics_by_part: dict[PackagePart, MeshDiagnostics],
    profile: MeshSolverProfile,
) -> MeshReadiness:
    reasons: list[str] = []
    for part, diagnostics in diagnostics_by_part.items():
        for warning in diagnostics.warnings:
            _append_once(reasons, f"{part}: {warning}")

    if any(diagnostics.readiness.level == "invalid" for diagnostics in diagnostics_by_part.values()):
        return MeshReadiness(level="invalid", reasons=reasons)

    disallowed_parts = sorted(set(diagnostics_by_part) - set(profile.accepted_parts))
    if disallowed_parts:
        for part in disallowed_parts:
            _append_once(reasons, f"{part}: part not accepted by solver profile")
        return MeshReadiness(level="stl_surface", reasons=reasons)

    has_nonmanifold = any(
        diagnostics.raw_nonmanifold_edges > profile.max_nonmanifold_edges
        or diagnostics.welded_nonmanifold_edges > profile.max_nonmanifold_edges
        for diagnostics in diagnostics_by_part.values()
    )
    if has_nonmanifold:
        _append_once(reasons, "nonmanifold edges exceed solver profile")
        return MeshReadiness(level="stl_surface", reasons=reasons)

    if profile.requires_watertight:
        _append_once(reasons, "watertight solid profile is not implemented")
        return MeshReadiness(level="stl_surface", reasons=reasons)

    _append_once(reasons, "open wetted-surface profile; not watertight cfd_ready")
    return MeshReadiness(level="cfd_surface_candidate", reasons=reasons)


def _append_once(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
