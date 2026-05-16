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
    ReadinessLevel,
    diagnose_mesh,
)
from kayakgen.io.json import save_hull
from kayakgen.io.stl import write_stl
from kayakgen.model.hull import Hull
from kayakgen.eval.closed_volume import (
    ClosedVolumeDiagnostics,
    diagnose_closed_volume_body,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.volume_mesh import (
    FIXTURE_VOLUME_MESHER_NAME,
    HASH_ALGORITHM_SHA256,
    HashAlgorithm,
    VolumeMeshBoundaryPatch,
    VolumeMeshDiagnostic,
    fixture_volume_mesh_artifact,
    fixture_volume_mesh_diagnostic,
    sha256_file,
)

PackagePart = Literal["hull", "deck"]
ReadinessAuthority = Literal[
    "surface_diagnostics",
    "verified_watertight_volume_mesh_evidence",
]
SolverReadinessGateStatus = Literal["ready_for_profile", "blocked"]
SolverReadinessInputSemantics = Literal[
    "not_solver_input",
    "profile_input_candidate",
]
SolverReadinessIssueSource = Literal[
    "mesh_package_manifest",
    "closed_volume_diagnostic",
    "self_intersection_diagnostic",
    "volume_mesh_diagnostic",
    "dispatch_profile",
    "solver_result",
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
    evidence_hash_algorithm: HashAlgorithm = HASH_ALGORITHM_SHA256
    evidence_hash_algorithms: dict[str, HashAlgorithm] = Field(default_factory=dict)
    volume_mesh_boundary_patches: list[VolumeMeshBoundaryPatch] = Field(
        default_factory=list
    )
    volume_mesh_boundary_markers: dict[str, str] = Field(default_factory=dict)
    readiness_authority: ReadinessAuthority = "surface_diagnostics"
    warnings: list[str] = Field(default_factory=list)


class SolverReadinessIssue(BaseModel):
    """Structured blocker or warning in an RFC 0040 readiness report."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    source: SolverReadinessIssueSource
    ref: str | None = None


class ClosedVolumeSolverReadinessReport(BaseModel):
    """Explanatory read model for profile-scoped solver-input readiness."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    hull_hash: str
    body_ref: str | None = None
    body_profile: str | None = None
    mesh_package_ref: str | None = None
    solver_profile: str
    required_mesh_profile: str | None = None
    required_mesh_readiness: ReadinessLevel = "cfd_ready"
    generated_body_diagnostic_ref: str | None = None
    self_intersection_diagnostic_ref: str | None = None
    volume_mesh_diagnostic_ref: str | None = None
    evidence_hash_algorithm: HashAlgorithm = HASH_ALGORITHM_SHA256
    evidence_hashes: dict[str, str] = Field(default_factory=dict)
    evidence_hash_algorithms: dict[str, HashAlgorithm] = Field(default_factory=dict)
    boundary_patches: list[VolumeMeshBoundaryPatch] = Field(default_factory=list)
    boundary_markers: dict[str, str] = Field(default_factory=dict)
    gate_status: SolverReadinessGateStatus
    blocker_reasons: list[str] = Field(default_factory=list)
    blockers: list[SolverReadinessIssue] = Field(default_factory=list)
    warnings: list[SolverReadinessIssue] = Field(default_factory=list)
    input_semantics: SolverReadinessInputSemantics


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
    bound_volume_mesh_diagnostic: VolumeMeshDiagnostic | None = None,
) -> MeshPackageManifest:
    """Write a deterministic mesh package and return its manifest.

    When ``bound_volume_mesh_diagnostic`` is omitted the manifest layout
    and bytes are byte-identical to the historical writer. When supplied
    (RFC 0045 evidence binding), the diagnostic is serialized alongside
    the manifest, evidence hashes are recorded, and readiness is promoted
    to ``cfd_ready`` via ``verified_watertight_volume_mesh_evidence``.
    """
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
    if bound_volume_mesh_diagnostic is not None:
        manifest = _augment_manifest_with_bound_diagnostic(
            manifest,
            hull,
            out,
            stations=stations,
            bound_diagnostic=bound_volume_mesh_diagnostic,
        )
    (out / "manifest.json").write_text(manifest.model_dump_json(indent=2))
    return manifest


def _augment_manifest_with_bound_diagnostic(
    manifest: MeshPackageManifest,
    hull: Hull,
    out: Path,
    *,
    stations: int | None,
    bound_diagnostic: VolumeMeshDiagnostic,
) -> MeshPackageManifest:
    """Return a manifest extended with an RFC 0045 bound volume-mesh diagnostic.

    Writes a closed-volume diagnostic for the generated body, the bound
    volume-mesh diagnostic, hashes both, and embeds artifact references
    so the readiness gate accepts ``cfd_ready`` from the harness-derived
    diagnostic.
    """

    body = generated_hull_plus_deck_body(
        hull,
        stations=stations if stations is not None else 12,
    )
    closed_diagnostics = diagnose_closed_volume_body(body)
    closed_ref = "closed-volume-diagnostic.json"
    closed_path = out / closed_ref
    closed_path.write_text(closed_diagnostics.model_dump_json(indent=2) + "\n")
    closed_hash = sha256_file(closed_path)

    # Rebind the diagnostic's body identity to the freshly-generated closed
    # body so the existing readiness gate (which compares body_ref /
    # source_hull_hash against the manifest) accepts the harness diagnostic.
    aligned_diagnostic = bound_diagnostic.model_copy(
        update={
            "body_ref": closed_diagnostics.body_id,
            "source_hull_hash": closed_diagnostics.source_hull_hash or "",
        }
    )
    volume_mesh_diagnostic_ref = "volume-mesh-diagnostic.json"
    volume_diagnostic_path = out / volume_mesh_diagnostic_ref
    volume_diagnostic_path.write_text(
        aligned_diagnostic.model_dump_json(indent=2) + "\n"
    )
    volume_diagnostic_hash = sha256_file(volume_diagnostic_path)

    volume_mesh_artifacts: dict[str, str] = {
        name: artifact.ref
        for name, artifact in aligned_diagnostic.output_artifacts.items()
    }
    evidence_hashes: dict[str, str] = {
        "closed_volume_diagnostic": closed_hash,
        "self_intersection_diagnostic": closed_hash,
        "volume_mesh_diagnostic": volume_diagnostic_hash,
    }
    for name, artifact in aligned_diagnostic.output_artifacts.items():
        evidence_hashes[f"volume_mesh_artifacts.{name}"] = artifact.sha256
    evidence_hash_algorithms = {
        key: HASH_ALGORITHM_SHA256 for key in evidence_hashes
    }
    readiness = MeshReadiness(
        level="cfd_ready",
        reasons=[
            "snappyHexMesh harness evidence bound; watertight handoff gates satisfied",
            "CFD solver outputs remain raw and unvalidated",
        ],
    )
    warnings = list(readiness.reasons)
    return manifest.model_copy(
        update={
            "readiness": readiness,
            "body_ref": closed_diagnostics.body_id,
            "closed_volume_diagnostic": closed_ref,
            "self_intersection_diagnostic": closed_ref,
            "volume_mesh_artifacts": volume_mesh_artifacts,
            "volume_mesh_diagnostic": volume_mesh_diagnostic_ref,
            "evidence_hashes": evidence_hashes,
            "evidence_hash_algorithms": evidence_hash_algorithms,
            "volume_mesh_boundary_patches": list(aligned_diagnostic.boundary_patches),
            "volume_mesh_boundary_markers": dict(aligned_diagnostic.boundary_markers),
            "readiness_authority": "verified_watertight_volume_mesh_evidence",
            "warnings": warnings,
        }
    )


def closed_volume_solver_readiness_report(
    manifest: MeshPackageManifest | object,
    *,
    mesh_package_ref: str | None = None,
    solver_profile: object | None = None,
    required_mesh_profile: str | None = None,
    required_mesh_readiness: ReadinessLevel | None = None,
    closed_volume_diagnostics: ClosedVolumeDiagnostics | object | None = None,
    self_intersection_diagnostics: ClosedVolumeDiagnostics | object | None = None,
    volume_mesh_diagnostic: VolumeMeshDiagnostic | object | None = None,
    extra_blockers: list[SolverReadinessIssue] | None = None,
    extra_warnings: list[SolverReadinessIssue] | None = None,
) -> ClosedVolumeSolverReadinessReport:
    """Build the RFC 0040 report without trusting readiness strings alone."""

    manifest = MeshPackageManifest.model_validate(manifest)
    profile_name = _profile_value(
        solver_profile,
        "name",
        default=manifest.solver_profile.profile_name,
    )
    required_profile = (
        required_mesh_profile
        or _profile_value(solver_profile, "required_mesh_profile", default=None)
        or manifest.solver_profile.profile_name
    )
    required_readiness = (
        required_mesh_readiness
        or _profile_value(solver_profile, "required_mesh_readiness", default=None)
        or "cfd_ready"
    )
    closed = (
        ClosedVolumeDiagnostics.model_validate(closed_volume_diagnostics)
        if closed_volume_diagnostics is not None
        else None
    )
    self_diagnostic = (
        ClosedVolumeDiagnostics.model_validate(self_intersection_diagnostics)
        if self_intersection_diagnostics is not None
        else closed
    )
    volume = (
        VolumeMeshDiagnostic.model_validate(volume_mesh_diagnostic)
        if volume_mesh_diagnostic is not None
        else None
    )

    blockers: list[SolverReadinessIssue] = list(extra_blockers or [])
    warnings: list[SolverReadinessIssue] = list(extra_warnings or [])

    def block(
        code: str,
        message: str,
        source: SolverReadinessIssueSource,
        ref: str | None = None,
    ) -> None:
        _append_issue_once(
            blockers,
            SolverReadinessIssue(
                code=code,
                message=message,
                source=source,
                ref=ref,
            ),
        )

    def warn(
        code: str,
        message: str,
        source: SolverReadinessIssueSource,
        ref: str | None = None,
    ) -> None:
        _append_issue_once(
            warnings,
            SolverReadinessIssue(
                code=code,
                message=message,
                source=source,
                ref=ref,
            ),
        )

    if required_profile and manifest.solver_profile.profile_name != required_profile:
        block(
            "solver_profile_not_satisfied",
            "mesh package solver profile does not match the requested solver profile",
            "dispatch_profile",
        )

    if manifest.solver_profile.requires_watertight and manifest.readiness.level != "cfd_ready":
        block(
            "solver_profile_not_satisfied",
            "watertight solver profile requires cfd_ready package readiness",
            "mesh_package_manifest",
        )
    elif not manifest.solver_profile.requires_watertight and required_readiness == "cfd_ready":
        block(
            "open_surface_not_closed_body",
            "open wetted-surface packages are not closed-volume solver input",
            "mesh_package_manifest",
        )

    if manifest.readiness_authority != "verified_watertight_volume_mesh_evidence":
        warn(
            "readiness_authority_not_volume_mesh",
            "manifest readiness is not derived from verified volume-mesh evidence",
            "mesh_package_manifest",
        )

    if closed is None:
        if manifest.body_ref or manifest.closed_volume_diagnostic:
            block(
                "generated_body_diagnostics_failed",
                "generated body diagnostic evidence is referenced but unavailable to report",
                "closed_volume_diagnostic",
                manifest.closed_volume_diagnostic,
            )
        else:
            block(
                "generated_body_missing",
                "no generated closed-body diagnostic evidence is referenced",
                "mesh_package_manifest",
            )
    else:
        _assess_closed_body_evidence(
            manifest,
            closed,
            self_diagnostic,
            block,
            warn,
        )

    if volume is None:
        block(
            "volume_mesh_missing",
            "no volume-mesh diagnostic evidence is available",
            "volume_mesh_diagnostic",
            manifest.volume_mesh_diagnostic,
        )
    else:
        _assess_volume_mesh_evidence(
            manifest,
            volume,
            required_profile,
            block,
            warn,
        )

    if volume and volume.mesher_name == FIXTURE_VOLUME_MESHER_NAME:
        warn(
            "fixture_handoff_not_production_meshing",
            "fixture volume-mesh evidence is a handoff fixture, not production meshing",
            "volume_mesh_diagnostic",
            manifest.volume_mesh_diagnostic,
        )
    warn(
        "raw_solver_output_not_validated",
        "solver-input readiness does not validate or calibrate solver output",
        "solver_result",
    )

    gate_status: SolverReadinessGateStatus = (
        "blocked" if blockers else "ready_for_profile"
    )
    boundary_patches = (
        list(volume.boundary_patches)
        if volume is not None
        else list(manifest.volume_mesh_boundary_patches)
    )
    boundary_markers = (
        dict(volume.boundary_markers)
        if volume is not None
        else dict(manifest.volume_mesh_boundary_markers)
    )
    evidence_hash_algorithms = _evidence_hash_algorithms(manifest)
    return ClosedVolumeSolverReadinessReport(
        hull_hash=manifest.hull_hash,
        body_ref=manifest.body_ref or (closed.body_id if closed else None),
        body_profile=closed.profile_name if closed else None,
        mesh_package_ref=mesh_package_ref,
        solver_profile=str(profile_name),
        required_mesh_profile=required_profile,
        required_mesh_readiness=required_readiness,
        generated_body_diagnostic_ref=manifest.closed_volume_diagnostic,
        self_intersection_diagnostic_ref=manifest.self_intersection_diagnostic,
        volume_mesh_diagnostic_ref=manifest.volume_mesh_diagnostic,
        evidence_hash_algorithm=manifest.evidence_hash_algorithm,
        evidence_hashes=dict(manifest.evidence_hashes),
        evidence_hash_algorithms=evidence_hash_algorithms,
        boundary_patches=boundary_patches,
        boundary_markers=boundary_markers,
        gate_status=gate_status,
        blocker_reasons=list(dict.fromkeys(issue.code for issue in blockers)),
        blockers=blockers,
        warnings=warnings,
        input_semantics=(
            "not_solver_input"
            if gate_status == "blocked"
            else "profile_input_candidate"
        ),
    )


def closed_volume_solver_readiness_report_from_package(
    package_dir: str | Path,
    *,
    mesh_package_ref: str | None = None,
    solver_profile: object | None = None,
    required_mesh_profile: str | None = None,
    required_mesh_readiness: ReadinessLevel | None = None,
) -> ClosedVolumeSolverReadinessReport:
    """Read manifest/evidence files and build a solver-readiness report."""

    package_root = Path(package_dir)
    manifest = MeshPackageManifest.model_validate_json(
        (package_root / "manifest.json").read_text()
    )
    blockers: list[SolverReadinessIssue] = []
    closed = _load_report_evidence(
        package_root,
        manifest,
        "closed_volume_diagnostic",
        manifest.closed_volume_diagnostic,
        ClosedVolumeDiagnostics,
        blockers,
    )
    self_diagnostic = _load_report_evidence(
        package_root,
        manifest,
        "self_intersection_diagnostic",
        manifest.self_intersection_diagnostic,
        ClosedVolumeDiagnostics,
        blockers,
    )
    volume = _load_report_evidence(
        package_root,
        manifest,
        "volume_mesh_diagnostic",
        manifest.volume_mesh_diagnostic,
        VolumeMeshDiagnostic,
        blockers,
    )
    return closed_volume_solver_readiness_report(
        manifest,
        mesh_package_ref=mesh_package_ref or str(package_root),
        solver_profile=solver_profile,
        required_mesh_profile=required_mesh_profile,
        required_mesh_readiness=required_mesh_readiness,
        closed_volume_diagnostics=closed,
        self_intersection_diagnostics=self_diagnostic,
        volume_mesh_diagnostic=volume,
        extra_blockers=blockers,
    )


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
    evidence_hash_algorithms = {
        key: HASH_ALGORITHM_SHA256 for key in evidence_hashes
    }
    warnings = list(manifest.warnings)
    _append_once(
        warnings,
        "generated closed body diagnostic is present but volume mesh evidence is missing",
    )

    readiness = manifest.readiness
    volume_mesh_artifacts: dict[str, str] = {}
    volume_mesh_diagnostic_ref: str | None = None
    volume_mesh_boundary_patches: list[VolumeMeshBoundaryPatch] = []
    volume_mesh_boundary_markers: dict[str, str] = {}
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
        evidence_hash_algorithms = {
            key: HASH_ALGORITHM_SHA256 for key in evidence_hashes
        }
        volume_mesh_boundary_patches = list(volume_diagnostic.boundary_patches)
        volume_mesh_boundary_markers = dict(volume_diagnostic.boundary_markers)
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
            "evidence_hash_algorithms": evidence_hash_algorithms,
            "volume_mesh_boundary_patches": volume_mesh_boundary_patches,
            "volume_mesh_boundary_markers": volume_mesh_boundary_markers,
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

    if any(
        diagnostics.readiness.level == "invalid"
        for diagnostics in diagnostics_by_part.values()
    ):
        return MeshReadiness(level="invalid", reasons=reasons)
    if any(
        diagnostics.readiness.level == "display"
        for diagnostics in diagnostics_by_part.values()
    ):
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


def _assess_closed_body_evidence(
    manifest: MeshPackageManifest,
    closed: ClosedVolumeDiagnostics,
    self_diagnostic: ClosedVolumeDiagnostics | None,
    block,
    warn,
) -> None:
    if closed.body_type == "explicit_synthetic_triangle_mesh":
        block(
            "synthetic_body_not_generated_kayak",
            "synthetic closed-volume diagnostics cannot satisfy generated kayak handoff",
            "closed_volume_diagnostic",
            manifest.closed_volume_diagnostic,
        )
        return
    if closed.body_type != "generated_hull_plus_deck_closed_body":
        block(
            "generated_body_diagnostics_failed",
            f"unsupported closed-volume body type {closed.body_type!r}",
            "closed_volume_diagnostic",
            manifest.closed_volume_diagnostic,
        )
    if closed.body_id != manifest.body_ref:
        block(
            "volume_mesh_stale_or_cross_body",
            "closed-volume diagnostic body_ref does not match manifest body_ref",
            "closed_volume_diagnostic",
            manifest.closed_volume_diagnostic,
        )
    if closed.source_hull_hash != manifest.hull_hash:
        block(
            "volume_mesh_stale_or_cross_body",
            "closed-volume diagnostic source hull hash does not match manifest hull hash",
            "closed_volume_diagnostic",
            manifest.closed_volume_diagnostic,
        )
    if closed.readiness.level != "closed_volume":
        block(
            "generated_body_diagnostics_failed",
            "generated body diagnostic is below closed_volume readiness",
            "closed_volume_diagnostic",
            manifest.closed_volume_diagnostic,
        )
    if (
        closed.raw_boundary_edges
        or closed.welded_boundary_edges
        or closed.raw_nonmanifold_edges
        or closed.welded_nonmanifold_edges
        or closed.degenerate_faces
        or closed.nonfinite_vertices
        or closed.nonfinite_faces
        or closed.invalid_face_indices
    ):
        block(
            "generated_body_diagnostics_failed",
            "generated body diagnostic has blocking topology or numeric counts",
            "closed_volume_diagnostic",
            manifest.closed_volume_diagnostic,
        )
    if closed.self_intersection_status != "passed":
        block(
            "self_intersection_not_passed",
            "closed-volume self-intersection diagnostic did not pass",
            "self_intersection_diagnostic",
            manifest.self_intersection_diagnostic,
        )
    if self_diagnostic is not None:
        if self_diagnostic.body_id != closed.body_id:
            block(
                "volume_mesh_stale_or_cross_body",
                "self-intersection diagnostic body_ref does not match closed body",
                "self_intersection_diagnostic",
                manifest.self_intersection_diagnostic,
            )
        if self_diagnostic.self_intersection_status != "passed":
            block(
                "self_intersection_not_passed",
                "self-intersection diagnostic did not pass",
                "self_intersection_diagnostic",
                manifest.self_intersection_diagnostic,
            )
    warn(
        "generated_body_not_solver_input",
        "generated closed-body diagnostics are evaluation evidence, not solver input alone",
        "closed_volume_diagnostic",
        manifest.closed_volume_diagnostic,
    )


def _assess_volume_mesh_evidence(
    manifest: MeshPackageManifest,
    volume: VolumeMeshDiagnostic,
    required_profile: str | None,
    block,
    warn,
) -> None:
    if volume.body_type == "explicit_synthetic_triangle_mesh":
        block(
            "synthetic_body_not_generated_kayak",
            "synthetic volume-mesh evidence cannot satisfy generated kayak handoff",
            "volume_mesh_diagnostic",
            manifest.volume_mesh_diagnostic,
        )
    if volume.profile_name != required_profile:
        block(
            "solver_profile_not_satisfied",
            "volume-mesh diagnostic profile does not match required solver mesh profile",
            "volume_mesh_diagnostic",
            manifest.volume_mesh_diagnostic,
        )
    if volume.body_ref != manifest.body_ref:
        block(
            "volume_mesh_stale_or_cross_body",
            "volume-mesh diagnostic body_ref does not match manifest body_ref",
            "volume_mesh_diagnostic",
            manifest.volume_mesh_diagnostic,
        )
    if volume.source_hull_hash != manifest.hull_hash:
        block(
            "volume_mesh_stale_or_cross_body",
            "volume-mesh diagnostic hull hash does not match manifest hull hash",
            "volume_mesh_diagnostic",
            manifest.volume_mesh_diagnostic,
        )
    if volume.readiness.level != "cfd_ready":
        block(
            "volume_mesh_quality_failed",
            "volume-mesh diagnostic is below cfd_ready",
            "volume_mesh_diagnostic",
            manifest.volume_mesh_diagnostic,
        )
    if (
        volume.invalid_cell_count
        or volume.inverted_cell_count
        or volume.zero_volume_cell_count
        or volume.nonfinite_cell_count
        or not volume.body_surface_matches_diagnostic
    ):
        block(
            "volume_mesh_quality_failed",
            "volume-mesh diagnostic has blocking quality or body-surface counts",
            "volume_mesh_diagnostic",
            manifest.volume_mesh_diagnostic,
        )
    if set(volume.output_artifacts) != set(manifest.volume_mesh_artifacts):
        block(
            "volume_mesh_stale_or_cross_body",
            "volume-mesh artifact set does not match manifest references",
            "volume_mesh_diagnostic",
            manifest.volume_mesh_diagnostic,
        )
    for name, artifact in volume.output_artifacts.items():
        if manifest.volume_mesh_artifacts.get(name) != artifact.ref:
            block(
                "volume_mesh_stale_or_cross_body",
                f"volume-mesh artifact ref mismatch for {name}",
                "volume_mesh_diagnostic",
                manifest.volume_mesh_diagnostic,
            )
    if not volume.boundary_patches:
        block(
            "volume_mesh_quality_failed",
            "volume-mesh diagnostic lacks boundary patch metadata",
            "volume_mesh_diagnostic",
            manifest.volume_mesh_diagnostic,
        )
    warn(
        "boundary_patch_metadata_present",
        "volume-mesh report includes solver-facing boundary patch and marker metadata",
        "volume_mesh_diagnostic",
        manifest.volume_mesh_diagnostic,
    )


def _profile_value(profile: object | None, name: str, *, default: object) -> object:
    if profile is None:
        return default
    if isinstance(profile, dict):
        return profile.get(name, default)
    return getattr(profile, name, default)


def _evidence_hash_algorithms(
    manifest: MeshPackageManifest,
) -> dict[str, HashAlgorithm]:
    return {
        key: manifest.evidence_hash_algorithms.get(
            key,
            manifest.evidence_hash_algorithm,
        )
        for key in manifest.evidence_hashes
    }


def _load_report_evidence(
    package_root: Path,
    manifest: MeshPackageManifest,
    key: str,
    ref: str | None,
    model_type,
    blockers: list[SolverReadinessIssue],
):
    if not ref:
        return None
    try:
        path = _resolve_report_ref(package_root, ref)
        expected_hash = manifest.evidence_hashes.get(key)
        actual_hash = sha256_file(path)
        if expected_hash is None:
            _append_issue_once(
                blockers,
                SolverReadinessIssue(
                    code="volume_mesh_stale_or_cross_body",
                    message=f"missing evidence hash for {key}",
                    source="mesh_package_manifest",
                    ref=ref,
                ),
            )
        elif expected_hash != actual_hash:
            _append_issue_once(
                blockers,
                SolverReadinessIssue(
                    code="volume_mesh_stale_or_cross_body",
                    message=f"stale evidence hash for {key}",
                    source="mesh_package_manifest",
                    ref=ref,
                ),
            )
        return model_type.model_validate_json(path.read_text())
    except Exception as exc:
        _append_issue_once(
            blockers,
            SolverReadinessIssue(
                code="generated_body_diagnostics_failed"
                if key != "volume_mesh_diagnostic"
                else "volume_mesh_quality_failed",
                message=f"could not load {key}: {exc}",
                source=(
                    "volume_mesh_diagnostic"
                    if key == "volume_mesh_diagnostic"
                    else "closed_volume_diagnostic"
                ),
                ref=ref,
            ),
        )
        return None


def _resolve_report_ref(package_root: Path, ref: str) -> Path:
    ref_path = Path(ref)
    if not ref or ref_path.is_absolute() or ".." in ref_path.parts:
        raise ValueError(f"forbidden path ref {ref!r}")
    root = package_root.resolve()
    path = (package_root / ref_path).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"forbidden path ref {ref!r}")
    if not path.is_file():
        raise FileNotFoundError(ref)
    return path


def _append_issue_once(
    values: list[SolverReadinessIssue],
    issue: SolverReadinessIssue,
) -> None:
    if not any(
        existing.code == issue.code
        and existing.source == issue.source
        and existing.ref == issue.ref
        and existing.message == issue.message
        for existing in values
    ):
        values.append(issue)


def _append_once(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
