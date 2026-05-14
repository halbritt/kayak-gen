"""Mesh package manifest and artifact writer."""

from __future__ import annotations

import json
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
from kayakgen.eval.closed_volume import (
    diagnose_closed_volume_body,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.volume_mesh import (
    fixture_volume_mesh_artifact,
    fixture_volume_mesh_diagnostic,
    sha256_file,
)

PackagePart = Literal["hull", "deck"]
ReadinessAuthority = Literal[
    "surface_diagnostics",
    "verified_watertight_volume_mesh_evidence",
]


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
    body_ref: str | None = None
    closed_volume_diagnostic: str | None = None
    self_intersection_diagnostic: str | None = None
    volume_mesh_artifacts: dict[str, str] = Field(default_factory=dict)
    volume_mesh_diagnostic: str | None = None
    evidence_hashes: dict[str, str] = Field(default_factory=dict)
    readiness_authority: ReadinessAuthority = "surface_diagnostics"
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


def watertight_solid_profile() -> MeshSolverProfile:
    """Return the future watertight-solid solver profile boundary.

    Current generated packages do not satisfy this profile; it exists so
    dispatch code can depend on a stable profile name and readiness gate.
    """
    return MeshSolverProfile(
        profile_name="watertight_solid_resistance_v1",
        requires_watertight=True,
        accepted_parts=("hull", "deck"),
        normal_orientation="outward",
        waterline_boundary_policy="closed_volume_required",
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


def write_watertight_volume_mesh_handoff_package(
    hull: Hull,
    out_dir: str | Path,
    *,
    stations: int | None = None,
    closed_body_stations: int = 12,
    include_fixture_volume_mesh: bool = False,
) -> MeshPackageManifest:
    """Write a watertight-profile package with explicit RFC 0023 evidence.

    The default path writes generated closed-body diagnostics only and remains
    below ``cfd_ready``. Passing ``include_fixture_volume_mesh=True`` adds a
    deterministic fixture volume-mesh artifact derived from that generated body
    and promotes readiness from verified in-memory evidence.
    """

    out = Path(out_dir)
    manifest = write_mesh_package(
        hull,
        out,
        stations=stations,
        solver_profile=watertight_solid_profile(),
    )

    body = generated_hull_plus_deck_body(
        hull,
        stations=closed_body_stations,
    )
    closed_diagnostics = diagnose_closed_volume_body(body)
    closed_ref = "closed-volume-diagnostic.json"
    closed_path = out / closed_ref
    closed_path.write_text(closed_diagnostics.model_dump_json(indent=2) + "\n")
    closed_hash = sha256_file(closed_path)

    evidence_hashes = {
        "closed_volume_diagnostic": closed_hash,
        "self_intersection_diagnostic": closed_hash,
    }
    warnings = list(manifest.warnings)
    _append_once(
        warnings,
        "generated closed body diagnostic is present but volume mesh evidence is missing",
    )

    readiness = manifest.readiness
    volume_mesh_artifacts: dict[str, str] = {}
    volume_mesh_diagnostic_ref: str | None = None
    readiness_authority: ReadinessAuthority = "surface_diagnostics"

    if include_fixture_volume_mesh:
        artifact_ref = "volume-mesh.fixture.json"
        artifact_path = out / artifact_ref
        artifact = fixture_volume_mesh_artifact(
            closed_diagnostics,
            closed_volume_diagnostic_hash=closed_hash,
        )
        artifact_path.write_text(
            json.dumps(artifact, indent=2, sort_keys=True) + "\n"
        )
        artifact_hash = sha256_file(artifact_path)

        volume_diagnostic = fixture_volume_mesh_diagnostic(
            closed_diagnostics,
            closed_volume_diagnostic_hash=closed_hash,
            self_intersection_diagnostic_hash=closed_hash,
            artifact_ref=artifact_ref,
            artifact_sha256=artifact_hash,
        )
        volume_mesh_diagnostic_ref = "volume-mesh-diagnostic.json"
        volume_diagnostic_path = out / volume_mesh_diagnostic_ref
        volume_diagnostic_path.write_text(
            volume_diagnostic.model_dump_json(indent=2) + "\n"
        )
        volume_diagnostic_hash = sha256_file(volume_diagnostic_path)
        volume_mesh_artifacts = {"volume_mesh": artifact_ref}
        evidence_hashes.update(
            {
                "volume_mesh_diagnostic": volume_diagnostic_hash,
                "volume_mesh_artifacts.volume_mesh": artifact_hash,
            }
        )
        readiness = MeshReadiness(
            level="cfd_ready",
            reasons=[
                "watertight volume mesh fixture evidence verified for generated body",
                "CFD solver outputs remain raw and unvalidated",
            ],
        )
        readiness_authority = "verified_watertight_volume_mesh_evidence"
        warnings = list(readiness.reasons)

    manifest = manifest.model_copy(
        update={
            "readiness": readiness,
            "body_ref": closed_diagnostics.body_id,
            "closed_volume_diagnostic": closed_ref,
            "self_intersection_diagnostic": closed_ref,
            "volume_mesh_artifacts": volume_mesh_artifacts,
            "volume_mesh_diagnostic": volume_mesh_diagnostic_ref,
            "evidence_hashes": evidence_hashes,
            "readiness_authority": readiness_authority,
            "warnings": warnings,
        }
    )
    (out / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n")
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
    if any(diagnostics.readiness.level == "display" for diagnostics in diagnostics_by_part.values()):
        return MeshReadiness(level="display", reasons=reasons)

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
        for part, diagnostics in diagnostics_by_part.items():
            if diagnostics.raw_boundary_edges or diagnostics.welded_boundary_edges:
                _append_once(
                    reasons,
                    f"{part}: watertight profile requires zero boundary edges",
                )
        _append_once(
            reasons,
            "watertight solid profile requires a closed combined hull/deck volume",
        )
        _append_once(reasons, "current package writer emits separate open surfaces")
        return MeshReadiness(level="stl_surface", reasons=reasons)

    _append_once(reasons, "open wetted-surface profile; not watertight cfd_ready")
    return MeshReadiness(level="cfd_surface_candidate", reasons=reasons)


def _append_once(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
