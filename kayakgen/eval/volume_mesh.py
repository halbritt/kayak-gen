"""Volume-mesh handoff evidence for watertight CFD packages.

The records in this module describe solver handoff artifacts only. They do
not claim calibrated CFD physics or production mesher support.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kayakgen.eval.closed_volume import ClosedVolumeDiagnostics

WATERTIGHT_SOLID_PROFILE_NAME = "watertight_solid_resistance_v1"
FIXTURE_VOLUME_MESHER_NAME = "kayakgen-fixture-volume-mesher"
FIXTURE_VOLUME_MESHER_VERSION = "rfc0023-fixture-v1"
HASH_ALGORITHM_SHA256 = "sha256"

VolumeMeshReadinessLevel = Literal["invalid", "cfd_ready"]
HashAlgorithm = Literal["sha256"]
BoundaryPatchRole = Literal[
    "wetted_body",
    "farfield",
    "free_surface",
    "inlet",
    "outlet",
    "symmetry",
    "other",
]
VolumeMeshReasonCode = Literal[
    "passed",
    "missing_volume_mesh",
    "stale_checksum",
    "profile_mismatch",
    "synthetic_evidence",
    "failed_self_intersection",
    "malformed_diagnostic",
    "forbidden_path_ref",
    "cross_body",
    "cross_hull",
    "cross_tolerance",
    "volume_mesh_not_ready",
    "artifact_checksum_mismatch",
    "body_surface_mismatch",
    "missing_metric",
]


class VolumeMeshCoordinateSystem(BaseModel):
    """Machine-readable coordinate convention echoed for solver handoff."""

    model_config = ConfigDict(extra="forbid")

    x: str = "longitudinal, stern positive, bow negative, spans -L/2 to +L/2"
    y: str = "port/starboard"
    z: str = "up positive"
    waterline_z_m: float = 0.0


class VolumeMeshReason(BaseModel):
    """Structured reason for volume-mesh readiness or rejection."""

    model_config = ConfigDict(extra="forbid")

    code: VolumeMeshReasonCode
    message: str


class VolumeMeshReadiness(BaseModel):
    """Volume-mesh readiness scoped to a named solver handoff profile."""

    model_config = ConfigDict(extra="forbid")

    level: VolumeMeshReadinessLevel
    reasons: list[VolumeMeshReason] = Field(default_factory=list)


class VolumeMeshArtifactRef(BaseModel):
    """Referenced handoff artifact and its content hash."""

    model_config = ConfigDict(extra="forbid")

    ref: str
    hash_algorithm: HashAlgorithm = HASH_ALGORITHM_SHA256
    sha256: str
    artifact_role: Literal["volume_mesh", "boundary_surface", "case_metadata"] = (
        "volume_mesh"
    )
    media_type: str = "application/json"


class VolumeMeshBoundaryPatch(BaseModel):
    """Solver-facing boundary patch and marker metadata."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    marker: str = Field(min_length=1)
    role: BoundaryPatchRole = "wetted_body"
    face_count: int = Field(ge=0)


class VolumeMeshDiagnostic(BaseModel):
    """Diagnostic record binding a volume mesh to a generated closed body."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    profile_name: str = WATERTIGHT_SOLID_PROFILE_NAME
    hash_algorithm: HashAlgorithm = HASH_ALGORITHM_SHA256
    body_ref: str
    body_type: str
    source_hull_hash: str
    closed_volume_diagnostic_hash_algorithm: HashAlgorithm = HASH_ALGORITHM_SHA256
    closed_volume_diagnostic_hash: str
    self_intersection_diagnostic_hash_algorithm: HashAlgorithm = HASH_ALGORITHM_SHA256
    self_intersection_diagnostic_hash: str
    closed_volume_tolerances_hash_algorithm: HashAlgorithm = HASH_ALGORITHM_SHA256
    closed_volume_tolerances_hash: str
    mesher_name: str
    mesher_version: str
    mesher_config_digest_algorithm: HashAlgorithm = HASH_ALGORITHM_SHA256
    mesher_config_digest: str
    deterministic_inputs: dict[str, str] = Field(default_factory=dict)
    output_artifacts: dict[str, VolumeMeshArtifactRef]
    units: Literal["m"] = "m"
    coordinate_system: VolumeMeshCoordinateSystem = Field(
        default_factory=VolumeMeshCoordinateSystem
    )
    cell_count: int = Field(ge=0)
    boundary_face_count: int = Field(ge=0)
    boundary_patch_names: list[str] = Field(default_factory=list)
    boundary_patches: list[VolumeMeshBoundaryPatch] = Field(default_factory=list)
    boundary_markers: dict[str, str] = Field(default_factory=dict)
    exterior_surface_id: str
    invalid_cell_count: int = Field(ge=0)
    inverted_cell_count: int = Field(ge=0)
    zero_volume_cell_count: int = Field(ge=0)
    nonfinite_cell_count: int = Field(ge=0)
    min_cell_volume_m3: float | None = None
    max_aspect_ratio: float | None = None
    max_skewness: float | None = None
    body_surface_matches_diagnostic: bool
    readiness: VolumeMeshReadiness
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _cfd_ready_requires_clean_fixture_metrics(self) -> "VolumeMeshDiagnostic":
        if self.readiness.level != "cfd_ready":
            return self
        blockers: list[str] = []
        if self.profile_name != WATERTIGHT_SOLID_PROFILE_NAME:
            blockers.append("profile_name")
        if self.body_type != "generated_hull_plus_deck_closed_body":
            blockers.append("body_type")
        if self.cell_count <= 0:
            blockers.append("cell_count")
        if self.boundary_face_count <= 0:
            blockers.append("boundary_face_count")
        if (
            self.invalid_cell_count
            or self.inverted_cell_count
            or self.zero_volume_cell_count
            or self.nonfinite_cell_count
        ):
            blockers.append("cell_quality_counts")
        if self.min_cell_volume_m3 is None or self.min_cell_volume_m3 <= 0.0:
            blockers.append("min_cell_volume_m3")
        if not self.body_surface_matches_diagnostic:
            blockers.append("body_surface_matches_diagnostic")
        if not self.output_artifacts:
            blockers.append("output_artifacts")
        if not self.boundary_patch_names:
            blockers.append("boundary_patch_names")
        if not self.boundary_patches:
            blockers.append("boundary_patches")
        patch_names = [patch.name for patch in self.boundary_patches]
        if sorted(patch_names) != sorted(self.boundary_patch_names):
            blockers.append("boundary_patch_metadata")
        if sum(patch.face_count for patch in self.boundary_patches) != self.boundary_face_count:
            blockers.append("boundary_patch_face_count")
        if any(
            self.boundary_markers.get(patch.name) != patch.marker
            for patch in self.boundary_patches
        ):
            blockers.append("boundary_markers")
        if blockers:
            raise ValueError(
                "cfd_ready volume mesh diagnostic has blocking field(s): "
                + ", ".join(blockers)
            )
        return self


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 hex digest of a file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    """Return a canonical SHA-256 digest for JSON-serializable data."""

    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def fixture_volume_mesh_artifact(
    diagnostics: ClosedVolumeDiagnostics,
    *,
    closed_volume_diagnostic_hash: str,
) -> dict[str, Any]:
    """Return deterministic fixture artifact content derived from a closed body."""

    return {
        "schema_version": "1",
        "artifact_kind": "fixture_volume_mesh",
        "profile_name": WATERTIGHT_SOLID_PROFILE_NAME,
        "body_ref": diagnostics.body_id,
        "body_type": diagnostics.body_type,
        "source_hull_hash": diagnostics.source_hull_hash,
        "closed_volume_diagnostic_hash": closed_volume_diagnostic_hash,
        "vertex_count": diagnostics.vertex_count,
        "face_count": diagnostics.face_count,
        "signed_volume_m3": diagnostics.signed_volume_m3,
        "self_intersection_status": diagnostics.self_intersection_status,
    }


def fixture_volume_mesh_diagnostic(
    diagnostics: ClosedVolumeDiagnostics,
    *,
    closed_volume_diagnostic_hash: str,
    self_intersection_diagnostic_hash: str,
    artifact_ref: str,
    artifact_sha256: str,
) -> VolumeMeshDiagnostic:
    """Build a passing fixture diagnostic for a generated closed body."""

    tolerances_hash = sha256_json(diagnostics.policy.tolerances)
    config_digest = sha256_json(
        {
            "mesher_name": FIXTURE_VOLUME_MESHER_NAME,
            "mesher_version": FIXTURE_VOLUME_MESHER_VERSION,
            "profile_name": WATERTIGHT_SOLID_PROFILE_NAME,
            "body_ref": diagnostics.body_id,
            "closed_volume_diagnostic_hash": closed_volume_diagnostic_hash,
            "tolerances_hash": tolerances_hash,
        }
    )
    return VolumeMeshDiagnostic(
        body_ref=diagnostics.body_id,
        body_type=diagnostics.body_type,
        source_hull_hash=diagnostics.source_hull_hash or "",
        closed_volume_diagnostic_hash=closed_volume_diagnostic_hash,
        self_intersection_diagnostic_hash=self_intersection_diagnostic_hash,
        closed_volume_tolerances_hash=tolerances_hash,
        mesher_name=FIXTURE_VOLUME_MESHER_NAME,
        mesher_version=FIXTURE_VOLUME_MESHER_VERSION,
        mesher_config_digest=config_digest,
        deterministic_inputs={
            "body_ref": diagnostics.body_id,
            "source_hull_hash": diagnostics.source_hull_hash or "",
            "closed_volume_diagnostic_hash": closed_volume_diagnostic_hash,
            "self_intersection_diagnostic_hash": self_intersection_diagnostic_hash,
            "closed_volume_tolerances_hash": tolerances_hash,
            "hash_algorithm": HASH_ALGORITHM_SHA256,
            "profile_name": WATERTIGHT_SOLID_PROFILE_NAME,
        },
        output_artifacts={
            "volume_mesh": VolumeMeshArtifactRef(
                ref=artifact_ref,
                sha256=artifact_sha256,
                artifact_role="volume_mesh",
            )
        },
        coordinate_system=VolumeMeshCoordinateSystem.model_validate(
            diagnostics.coordinate_system.model_dump(mode="json")
        ),
        cell_count=max(1, diagnostics.face_count * 2),
        boundary_face_count=diagnostics.face_count,
        boundary_patch_names=["generated_hull_plus_deck"],
        boundary_patches=[
            VolumeMeshBoundaryPatch(
                name="generated_hull_plus_deck",
                marker="wall:generated_hull_plus_deck",
                role="wetted_body",
                face_count=diagnostics.face_count,
            )
        ],
        boundary_markers={
            "generated_hull_plus_deck": "wall:generated_hull_plus_deck"
        },
        exterior_surface_id=diagnostics.body_id,
        invalid_cell_count=0,
        inverted_cell_count=0,
        zero_volume_cell_count=0,
        nonfinite_cell_count=0,
        min_cell_volume_m3=max(diagnostics.signed_volume_m3, 1e-12)
        / max(1, diagnostics.face_count * 2),
        max_aspect_ratio=None,
        max_skewness=None,
        body_surface_matches_diagnostic=True,
        readiness=VolumeMeshReadiness(
            level="cfd_ready",
            reasons=[
                VolumeMeshReason(
                    code="passed",
                    message="fixture volume mesh evidence satisfies watertight handoff gates",
                )
            ],
        ),
        warnings=[
            "fixture volume mesh handoff evidence only; CFD outputs remain raw and unvalidated"
        ],
    )
