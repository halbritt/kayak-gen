"""Mesh package and watertight handoff validation for CFD dispatch.

Helpers that gate a ``SolverProfile`` + ``MeshPackageManifest`` pair before
preparing a CFD job. Split out from the historical
``kayakgen.eval.cfd.jobs`` per Phase 3A of
``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from kayakgen.eval.cfd.records import CfdDispatchError, SolverProfile
from kayakgen.eval.mesh_diagnostics import ReadinessLevel
from kayakgen.eval.mesh_package import MeshPackageManifest
from kayakgen.eval.volume_mesh import (
    VolumeMeshDiagnostic,
    sha256_file,
    sha256_json,
)

READINESS_ORDER: dict[ReadinessLevel, int] = {
    "invalid": 0,
    "display": 1,
    "stl_surface": 2,
    "cfd_surface_candidate": 3,
    "cfd_ready": 4,
}


class _WatertightDispatchEvidence(BaseModel):
    """Internal result for profile-scoped closed-volume dispatch evidence."""

    accepted: bool
    code: str = "accepted"
    reason: str | None = None


def _load_mesh_manifest(mesh_dir: Path) -> MeshPackageManifest:
    manifest_path = mesh_dir / "manifest.json"
    try:
        return MeshPackageManifest.model_validate_json(manifest_path.read_text())
    except FileNotFoundError as exc:
        raise CfdDispatchError(
            f"mesh package manifest not found: {manifest_path}",
            code="missing_artifact",
        ) from exc
    except ValidationError as exc:
        raise CfdDispatchError(
            f"malformed mesh package manifest: {manifest_path}",
            code="malformed_manifest",
        ) from exc


def _validate_mesh_package(
    mesh_dir: Path,
    manifest: MeshPackageManifest,
    solver_profile: SolverProfile,
) -> None:
    if solver_profile.required_mesh_profile:
        actual_profile = manifest.solver_profile.profile_name
        if actual_profile != solver_profile.required_mesh_profile:
            raise CfdDispatchError(
                "mesh package solver profile mismatch: "
                f"expected {solver_profile.required_mesh_profile!r}, got {actual_profile!r}",
                code="mesh_profile_mismatch",
            )

    refs = [
        manifest.hull_json,
        *manifest.quality_reports.values(),
        *manifest.surfaces.values(),
    ]
    for ref in refs:
        _resolve_package_ref(mesh_dir, ref)

    actual = READINESS_ORDER[manifest.readiness.level]
    required = READINESS_ORDER[solver_profile.required_mesh_readiness]
    if _solver_profile_requires_watertight_evidence(solver_profile, manifest):
        evidence = _watertight_dispatch_evidence(mesh_dir, manifest, solver_profile)
        if not evidence.accepted:
            detail = f": {evidence.reason}" if evidence.reason else ""
            readiness_detail = ""
            if actual < required:
                readiness_detail = (
                    "; mesh package readiness below solver requirement: "
                    f"readiness {manifest.readiness.level} is below required "
                    f"{solver_profile.required_mesh_readiness}"
                )
            raise CfdDispatchError(
                "watertight dispatch requires profile-scoped closed-volume "
                f"diagnostic evidence{detail}{readiness_detail}",
                code=evidence.code,
            )

    if actual < required:
        raise CfdDispatchError(
            "mesh package readiness below solver requirement: "
            f"readiness {manifest.readiness.level} is below required "
            f"{solver_profile.required_mesh_readiness}",
            code="readiness_below_requirement",
        )


def _solver_profile_requires_watertight_evidence(
    solver_profile: SolverProfile,
    manifest: MeshPackageManifest,
) -> bool:
    if solver_profile.required_mesh_readiness == "cfd_ready":
        return True
    if solver_profile.required_mesh_profile == "watertight_solid_resistance_v1":
        return True
    return bool(manifest.solver_profile.requires_watertight)


def _watertight_dispatch_evidence(
    mesh_dir: Path,
    manifest: MeshPackageManifest,
    solver_profile: SolverProfile,
) -> _WatertightDispatchEvidence:
    try:
        return _validate_watertight_dispatch_evidence(
            mesh_dir,
            manifest,
            solver_profile,
        )
    except CfdDispatchError as exc:
        return _WatertightDispatchEvidence(
            accepted=False,
            code=exc.code,
            reason=f"{exc.code}: {exc}",
        )


def _validate_watertight_dispatch_evidence(
    mesh_dir: Path,
    manifest: MeshPackageManifest,
    solver_profile: SolverProfile,
) -> _WatertightDispatchEvidence:
    if solver_profile.required_mesh_readiness != "cfd_ready":
        raise CfdDispatchError(
            "watertight handoff evidence only satisfies cfd_ready dispatch",
            code="readiness_below_requirement",
        )
    if solver_profile.required_mesh_profile != "watertight_solid_resistance_v1":
        raise CfdDispatchError(
            "watertight evidence profile mismatch: expected "
            "'watertight_solid_resistance_v1'",
            code="evidence_profile_mismatch",
        )
    if manifest.readiness_authority != "verified_watertight_volume_mesh_evidence":
        raise CfdDispatchError(
            "manifest readiness_authority is not verified watertight volume mesh evidence",
            code="missing_volume_mesh",
        )
    if not manifest.body_ref:
        raise CfdDispatchError(
            "manifest body_ref is missing for watertight handoff",
            code="missing_volume_mesh",
        )
    if not manifest.closed_volume_diagnostic:
        raise CfdDispatchError(
            "closed volume diagnostic is not referenced",
            code="missing_volume_mesh",
        )
    if not manifest.self_intersection_diagnostic:
        raise CfdDispatchError(
            "self-intersection diagnostic is not referenced",
            code="missing_volume_mesh",
        )
    if not manifest.volume_mesh_diagnostic:
        raise CfdDispatchError(
            "volume mesh diagnostic is not referenced",
            code="missing_volume_mesh",
        )
    if not manifest.volume_mesh_artifacts:
        raise CfdDispatchError(
            "volume mesh artifact is not referenced",
            code="missing_volume_mesh",
        )

    closed_path, closed_hash = _verified_evidence_path(
        mesh_dir,
        manifest,
        "closed_volume_diagnostic",
        manifest.closed_volume_diagnostic,
    )
    self_path, self_hash = _verified_evidence_path(
        mesh_dir,
        manifest,
        "self_intersection_diagnostic",
        manifest.self_intersection_diagnostic,
    )
    volume_path, volume_hash = _verified_evidence_path(
        mesh_dir,
        manifest,
        "volume_mesh_diagnostic",
        manifest.volume_mesh_diagnostic,
    )
    artifact_hashes: dict[str, str] = {}
    for name, ref in sorted(manifest.volume_mesh_artifacts.items()):
        _path, artifact_hash = _verified_evidence_path(
            mesh_dir,
            manifest,
            f"volume_mesh_artifacts.{name}",
            ref,
        )
        artifact_hashes[name] = artifact_hash

    closed = _load_closed_volume_diagnostic(
        closed_path,
        code="malformed_diagnostic",
    )
    self_diagnostic = (
        closed
        if self_path == closed_path
        else _load_closed_volume_diagnostic(
            self_path,
            code="malformed_diagnostic",
        )
    )
    _validate_closed_volume_handoff(
        manifest,
        closed,
        self_diagnostic,
    )

    volume = _load_volume_mesh_diagnostic(volume_path)
    _validate_volume_mesh_handoff(
        manifest,
        solver_profile,
        volume,
        closed_hash=closed_hash,
        self_hash=self_hash,
        volume_hash=volume_hash,
        closed_tolerances_hash=sha256_json(closed.policy.tolerances),
        artifact_hashes=artifact_hashes,
    )
    return _WatertightDispatchEvidence(accepted=True)


def _resolve_package_ref(mesh_dir: Path, ref: str) -> Path:
    ref_path = Path(ref)
    if not ref or ref_path.is_absolute() or ".." in ref_path.parts:
        raise CfdDispatchError(
            f"forbidden path ref {ref!r}",
            code="forbidden_path_ref",
        )
    root = mesh_dir.resolve()
    path = (mesh_dir / ref_path).resolve()
    if not path.is_relative_to(root):
        raise CfdDispatchError(
            f"forbidden path ref {ref!r}",
            code="forbidden_path_ref",
        )
    if not path.is_file():
        raise CfdDispatchError(
            f"mesh package is missing referenced artifact: {ref}",
            code="missing_artifact",
        )
    return path


def _verified_evidence_path(
    mesh_dir: Path,
    manifest: MeshPackageManifest,
    key: str,
    ref: str,
) -> tuple[Path, str]:
    path = _resolve_package_ref(mesh_dir, ref)
    actual = sha256_file(path)
    expected = _expected_evidence_hash(manifest, key, ref)
    if expected is None:
        raise CfdDispatchError(
            f"missing evidence hash for {key} ({ref})",
            code="stale_checksum",
        )
    if actual != expected:
        raise CfdDispatchError(
            f"stale checksum for {key} ({ref})",
            code="stale_checksum",
        )
    return path, actual


def _expected_evidence_hash(
    manifest: MeshPackageManifest,
    key: str,
    ref: str,
) -> str | None:
    aliases = (
        key,
        ref,
        f"volume_mesh_artifact:{key.rsplit('.', maxsplit=1)[-1]}",
    )
    for alias in aliases:
        expected = manifest.evidence_hashes.get(alias)
        if expected:
            return expected
    return None


def _load_closed_volume_diagnostic(path: Path, *, code: str):
    from kayakgen.eval.closed_volume import ClosedVolumeDiagnostics

    try:
        return ClosedVolumeDiagnostics.model_validate_json(path.read_text())
    except (ValidationError, ValueError) as exc:
        raise CfdDispatchError(
            f"malformed closed-volume diagnostic {path.name}: {exc}",
            code=code,
        ) from exc


def _load_volume_mesh_diagnostic(path: Path) -> VolumeMeshDiagnostic:
    try:
        return VolumeMeshDiagnostic.model_validate_json(path.read_text())
    except (ValidationError, ValueError) as exc:
        raise CfdDispatchError(
            f"malformed volume mesh diagnostic {path.name}: {exc}",
            code="malformed_diagnostic",
        ) from exc


def _validate_closed_volume_handoff(
    manifest: MeshPackageManifest,
    closed: Any,
    self_diagnostic: Any,
) -> None:
    if closed.body_type == "explicit_synthetic_triangle_mesh":
        raise CfdDispatchError(
            "synthetic closed-volume evidence cannot satisfy generated kayak handoff",
            code="synthetic_evidence",
        )
    if closed.body_type != "generated_hull_plus_deck_closed_body":
        raise CfdDispatchError(
            f"unsupported closed-volume body_type {closed.body_type!r}",
            code="malformed_diagnostic",
        )
    if closed.profile_name != "generated_hull_plus_deck_closed_body_v1":
        raise CfdDispatchError(
            "closed-volume diagnostic profile mismatch",
            code="evidence_profile_mismatch",
        )
    if closed.body_id != manifest.body_ref:
        raise CfdDispatchError(
            "closed-volume diagnostic body_ref mismatch",
            code="cross_body",
        )
    if closed.source_hull_hash != manifest.hull_hash:
        raise CfdDispatchError(
            "closed-volume diagnostic source hull hash mismatch",
            code="cross_hull",
        )
    if self_diagnostic.body_id != closed.body_id:
        raise CfdDispatchError(
            "self-intersection diagnostic body_ref mismatch",
            code="cross_body",
        )
    if self_diagnostic.source_hull_hash != closed.source_hull_hash:
        raise CfdDispatchError(
            "self-intersection diagnostic source hull hash mismatch",
            code="cross_hull",
        )
    if sha256_json(self_diagnostic.policy.tolerances) != sha256_json(
        closed.policy.tolerances
    ):
        raise CfdDispatchError(
            "self-intersection diagnostic tolerance set mismatch",
            code="cross_tolerance",
        )
    if closed.self_intersection_status != "passed":
        raise CfdDispatchError(
            "self-intersection diagnostic did not pass",
            code="failed_self_intersection",
        )
    if self_diagnostic.self_intersection_status != "passed":
        raise CfdDispatchError(
            "self-intersection diagnostic did not pass",
            code="failed_self_intersection",
        )
    if closed.readiness.level != "closed_volume":
        raise CfdDispatchError(
            "closed-volume diagnostic is below closed_volume readiness",
            code="volume_mesh_not_ready",
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
        raise CfdDispatchError(
            "closed-volume diagnostic has blocking topology or numeric counts",
            code="volume_mesh_not_ready",
        )


def _validate_volume_mesh_handoff(
    manifest: MeshPackageManifest,
    solver_profile: SolverProfile,
    volume: VolumeMeshDiagnostic,
    *,
    closed_hash: str,
    self_hash: str,
    volume_hash: str,
    closed_tolerances_hash: str,
    artifact_hashes: dict[str, str],
) -> None:
    if volume.profile_name != solver_profile.required_mesh_profile:
        raise CfdDispatchError(
            "volume mesh diagnostic profile mismatch",
            code="evidence_profile_mismatch",
        )
    if volume.readiness.level != "cfd_ready":
        raise CfdDispatchError(
            "volume mesh diagnostic is below cfd_ready",
            code="volume_mesh_not_ready",
        )
    if volume.body_ref != manifest.body_ref:
        raise CfdDispatchError(
            "volume mesh diagnostic body_ref mismatch",
            code="cross_body",
        )
    if volume.source_hull_hash != manifest.hull_hash:
        raise CfdDispatchError(
            "volume mesh diagnostic source hull hash mismatch",
            code="cross_hull",
        )
    if volume.closed_volume_diagnostic_hash != closed_hash:
        raise CfdDispatchError(
            "volume mesh diagnostic closed-volume hash mismatch",
            code="stale_checksum",
        )
    if volume.self_intersection_diagnostic_hash != self_hash:
        raise CfdDispatchError(
            "volume mesh diagnostic self-intersection hash mismatch",
            code="stale_checksum",
        )
    if volume.closed_volume_tolerances_hash != closed_tolerances_hash:
        raise CfdDispatchError(
            "volume mesh diagnostic tolerance set mismatch",
            code="cross_tolerance",
        )
    if (
        _expected_evidence_hash(
            manifest,
            "volume_mesh_diagnostic",
            manifest.volume_mesh_diagnostic or "",
        )
        != volume_hash
    ):
        raise CfdDispatchError(
            "manifest volume mesh diagnostic hash mismatch",
            code="stale_checksum",
        )
    if not volume.body_surface_matches_diagnostic:
        raise CfdDispatchError(
            "volume mesh body surface does not match diagnostic",
            code="body_surface_mismatch",
        )
    if set(volume.output_artifacts) != set(manifest.volume_mesh_artifacts):
        raise CfdDispatchError(
            "volume mesh artifact set mismatch",
            code="artifact_checksum_mismatch",
        )
    for name, artifact in volume.output_artifacts.items():
        if artifact.ref != manifest.volume_mesh_artifacts[name]:
            raise CfdDispatchError(
                f"volume mesh artifact ref mismatch for {name}",
                code="artifact_checksum_mismatch",
            )
        if artifact.sha256 != artifact_hashes[name]:
            raise CfdDispatchError(
                f"volume mesh artifact checksum mismatch for {name}",
                code="artifact_checksum_mismatch",
            )


def _validate_positive_job_inputs(
    *,
    speed_mps: float,
    seawater_density_kg_m3: float,
    kinematic_viscosity_m2_s: float,
) -> None:
    invalid = []
    if speed_mps <= 0:
        invalid.append("speed_mps")
    if seawater_density_kg_m3 <= 0:
        invalid.append("seawater_density_kg_m3")
    if kinematic_viscosity_m2_s <= 0:
        invalid.append("kinematic_viscosity_m2_s")
    if invalid:
        raise CfdDispatchError("CFD job inputs must be positive: " + ", ".join(invalid))


__all__ = [
    "READINESS_ORDER",
]
