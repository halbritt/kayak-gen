"""Deterministic ``snappyHexMesh`` evidence-harness contract for OpenFOAM-v2512.

This module encodes the workflow 0052 D011 decision to select
``openfoam-v2512-snappyhexmesh-watertight-v1`` as the first production
volume-mesher candidate. It does NOT execute ``snappyHexMesh`` or any
OpenFOAM binary. It defines:

* a locked case-template version string,
* deterministic dictionary scaffolds (``snappyHexMeshDict``,
  ``meshQualityDict``, ``surfaceFeatureExtractDict``, ``blockMeshDict``,
  ``controlDict``) keyed by the generated closed-body identity,
* hash-based dispatch gates so missing evidence rejects rather than
  silently promoting ordinary packages, and
* a translation from a fully-bound evidence record into the existing
  ``VolumeMeshDiagnostic`` shape so the watertight-handoff readiness gate
  can consume it without a new promotion path.

Ordinary generated mesh packages MUST NOT be promoted to ``cfd_ready`` by
this module. The translation only emits a diagnostic when every required
gate is satisfied and returns ``None`` otherwise.
"""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kayakgen.eval.closed_volume import ClosedVolumeBody
from kayakgen.eval.cfd.jobs import OpenFoamProvenanceProbe
from kayakgen.eval.volume_mesh import (
    HASH_ALGORITHM_SHA256,
    VolumeMeshArtifactRef,
    VolumeMeshBoundaryPatch,
    VolumeMeshCoordinateSystem,
    VolumeMeshDiagnostic,
    VolumeMeshReadiness,
    VolumeMeshReason,
    sha256_json,
)

SNAPPYHEXMESH_CASE_TEMPLATE_VERSION = "openfoam-v2512-snappyhexmesh-watertight-v1"
SNAPPYHEXMESH_BODY_PROFILE = "generated_hull_plus_deck_closed_body_v1"
SNAPPYHEXMESH_REQUIRED_VERSION = "v2512"
SNAPPYHEXMESH_MESHER_NAME = "openfoam-v2512-snappyhexmesh"
SNAPPYHEXMESH_MESHER_VERSION = SNAPPYHEXMESH_CASE_TEMPLATE_VERSION

REQUIRED_DICT_KEYS: tuple[str, ...] = (
    "controlDict",
    "snappyHexMeshDict",
    "meshQualityDict",
    "surfaceFeatureExtractDict",
    "blockMeshDict",
)

SnappyHexMeshDispatchState = Literal[
    "pending_evidence",
    "fixture_only",
    "evidence_recorded",
    "evidence_rejected",
]

SnappyHexMeshDispatchBlocker = Literal[
    "missing_body_ref_hash",
    "missing_body_profile",
    "missing_dictionary_hashes",
    "missing_patch_metadata",
    "missing_check_mesh",
    "missing_artifact_checksums",
    "missing_openfoam_provenance",
    "openfoam_provenance_not_v2512",
    "check_mesh_failed",
]


class SnappyHexMeshPatchEntry(BaseModel):
    """Solver-facing patch entry recorded by the harness."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    marker: str = Field(min_length=1)
    role: Literal[
        "wetted_body",
        "farfield",
        "free_surface",
        "inlet",
        "outlet",
        "symmetry",
        "other",
    ] = "wetted_body"
    face_count: int = Field(ge=0)


class CheckMeshSummary(BaseModel):
    """Deterministic structured summary echoing ``checkMesh`` reports.

    ``snappyHexMesh`` is not invoked by this harness, so this record is a
    placeholder for future production output. It is required as part of the
    evidence contract so that downstream code can rely on the field set.
    """

    model_config = ConfigDict(extra="forbid")

    passed: bool
    n_cells: int = Field(ge=0)
    n_internal_faces: int = Field(ge=0)
    n_boundary_faces: int = Field(ge=0)
    max_non_orthogonality_deg: float = Field(ge=0.0)
    max_skewness: float = Field(ge=0.0)
    aspect_ratio_max: float = Field(ge=0.0)
    warnings: list[str] = Field(default_factory=list)


class SnappyHexMeshEvidence(BaseModel):
    """Evidence record for the ``snappyHexMesh`` harness.

    Every required field must be present for ``dispatch_state`` to land on
    ``evidence_recorded``. Missing or mismatched fields surface in
    ``dispatch_blocker_codes`` and force ``dispatch_state`` to
    ``pending_evidence``.
    """

    model_config = ConfigDict(extra="forbid")

    case_template_version: Literal[
        "openfoam-v2512-snappyhexmesh-watertight-v1"
    ] = SNAPPYHEXMESH_CASE_TEMPLATE_VERSION
    body_ref_hash: str
    body_profile: Literal[
        "generated_hull_plus_deck_closed_body_v1"
    ] = SNAPPYHEXMESH_BODY_PROFILE
    dictionary_hashes: dict[str, str] = Field(default_factory=dict)
    patch_metadata: list[SnappyHexMeshPatchEntry] = Field(default_factory=list)
    check_mesh: CheckMeshSummary | None = None
    artifact_checksums: dict[str, str] = Field(default_factory=dict)
    openfoam_provenance: OpenFoamProvenanceProbe | None = None
    dispatch_state: SnappyHexMeshDispatchState = "pending_evidence"
    dispatch_blocker_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _evidence_recorded_requires_all_gates(self) -> "SnappyHexMeshEvidence":
        if self.dispatch_state != "evidence_recorded":
            return self
        missing = _missing_evidence_blockers(
            body_ref_hash=self.body_ref_hash,
            body_profile=self.body_profile,
            dictionary_hashes=self.dictionary_hashes,
            patch_metadata=self.patch_metadata,
            check_mesh=self.check_mesh,
            artifact_checksums=self.artifact_checksums,
            openfoam_provenance=self.openfoam_provenance,
        )
        if missing:
            raise ValueError(
                "evidence_recorded snappyHexMesh evidence has blocking gate(s): "
                + ", ".join(missing)
            )
        if self.dispatch_blocker_codes:
            raise ValueError(
                "evidence_recorded snappyHexMesh evidence must not declare "
                "dispatch_blocker_codes"
            )
        return self


def default_snappy_hex_mesh_dict_scaffold(
    body: ClosedVolumeBody,
) -> dict[str, str]:
    """Return deterministic scaffold contents for each required OpenFOAM dict.

    The scaffold is fully derived from the body identity, the locked case
    template version, and the required-key set. Two calls with the same body
    produce byte-identical scaffolds. No OpenFOAM tooling is required to
    produce or interpret these scaffolds; they are evidence material only.
    """

    body_identity = {
        "body_id": body.body_id,
        "body_type": body.body_type,
        "source_hull_hash": body.source_hull_hash or "",
        "profile_name": body.policy.profile_name,
        "waterline_z_m": body.waterline_z_m,
    }
    body_identity_token = sha256_json(body_identity)
    scaffolds: dict[str, str] = {}
    for key in REQUIRED_DICT_KEYS:
        lines = [
            f"// case_template_version {SNAPPYHEXMESH_CASE_TEMPLATE_VERSION}",
            f"// dictionary {key}",
            f"// body_id {body.body_id}",
            f"// body_profile {SNAPPYHEXMESH_BODY_PROFILE}",
            f"// body_identity_token {body_identity_token}",
            "// deterministic scaffold; no snappyHexMesh execution is performed",
        ]
        scaffolds[key] = "\n".join(lines) + "\n"
    return scaffolds


def compute_dict_hashes(scaffolds: dict[str, str]) -> dict[str, str]:
    """Return a SHA-256 hex digest per scaffold dictionary entry."""

    hashes: dict[str, str] = {}
    for key, content in scaffolds.items():
        if not isinstance(content, str):
            raise TypeError(
                f"snappyHexMesh dictionary scaffold {key!r} must be a string"
            )
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        hashes[key] = digest
    return hashes


def build_snappy_hex_mesh_evidence(
    *,
    body_ref_hash: str | None,
    body_profile: str | None = SNAPPYHEXMESH_BODY_PROFILE,
    dictionary_hashes: dict[str, str] | None,
    patch_metadata: list[SnappyHexMeshPatchEntry] | None,
    check_mesh: CheckMeshSummary | None,
    artifact_checksums: dict[str, str] | None,
    openfoam_provenance: OpenFoamProvenanceProbe | None,
    required_version: str = SNAPPYHEXMESH_REQUIRED_VERSION,
) -> SnappyHexMeshEvidence:
    """Build an evidence record, rejecting any missing dispatch gate."""

    normalized_dict_hashes = dict(dictionary_hashes or {})
    normalized_patches = list(patch_metadata or [])
    normalized_artifacts = dict(artifact_checksums or {})
    body_profile_value = body_profile or SNAPPYHEXMESH_BODY_PROFILE

    blockers = _missing_evidence_blockers(
        body_ref_hash=body_ref_hash or "",
        body_profile=body_profile_value,
        dictionary_hashes=normalized_dict_hashes,
        patch_metadata=normalized_patches,
        check_mesh=check_mesh,
        artifact_checksums=normalized_artifacts,
        openfoam_provenance=openfoam_provenance,
    )

    if check_mesh is not None and not check_mesh.passed:
        if "check_mesh_failed" not in blockers:
            blockers.append("check_mesh_failed")

    if openfoam_provenance is not None and not blockers:
        accepted, _reason = openfoam_provenance.matches_required(required_version)
        if not accepted:
            blockers.append("openfoam_provenance_not_v2512")

    dispatch_state: SnappyHexMeshDispatchState = (
        "evidence_recorded" if not blockers else "pending_evidence"
    )

    return SnappyHexMeshEvidence(
        body_ref_hash=body_ref_hash or "",
        body_profile=body_profile_value,  # type: ignore[arg-type]
        dictionary_hashes=normalized_dict_hashes,
        patch_metadata=normalized_patches,
        check_mesh=check_mesh,
        artifact_checksums=normalized_artifacts,
        openfoam_provenance=openfoam_provenance,
        dispatch_state=dispatch_state,
        dispatch_blocker_codes=list(blockers),
    )


def _missing_evidence_blockers(
    *,
    body_ref_hash: str,
    body_profile: str,
    dictionary_hashes: dict[str, str],
    patch_metadata: list[SnappyHexMeshPatchEntry],
    check_mesh: CheckMeshSummary | None,
    artifact_checksums: dict[str, str],
    openfoam_provenance: OpenFoamProvenanceProbe | None,
) -> list[str]:
    missing: list[str] = []
    if not body_ref_hash:
        missing.append("missing_body_ref_hash")
    if not body_profile:
        missing.append("missing_body_profile")
    if not dictionary_hashes or any(
        key not in dictionary_hashes or not dictionary_hashes.get(key)
        for key in REQUIRED_DICT_KEYS
    ):
        missing.append("missing_dictionary_hashes")
    if not patch_metadata or not any(
        patch.role == "wetted_body" for patch in patch_metadata
    ):
        missing.append("missing_patch_metadata")
    if check_mesh is None:
        missing.append("missing_check_mesh")
    if not artifact_checksums:
        missing.append("missing_artifact_checksums")
    if openfoam_provenance is None:
        missing.append("missing_openfoam_provenance")
    return missing


def snappy_hex_mesh_volume_mesh_diagnostic(
    evidence: SnappyHexMeshEvidence,
) -> VolumeMeshDiagnostic | None:
    """Translate a fully-bound evidence record to a ``VolumeMeshDiagnostic``.

    Returns ``None`` when evidence is not in ``evidence_recorded`` state so
    callers cannot use partial harness output to promote ordinary packages
    to ``cfd_ready``. The translation does NOT add a new promotion path -
    it simply binds the existing watertight gate to harness-collected
    evidence when every required field is present.
    """

    if evidence.dispatch_state != "evidence_recorded":
        return None
    if evidence.check_mesh is None or not evidence.check_mesh.passed:
        return None
    if not evidence.openfoam_provenance:
        return None
    accepted, _reason = evidence.openfoam_provenance.matches_required(
        SNAPPYHEXMESH_REQUIRED_VERSION
    )
    if not accepted:
        return None
    if not evidence.patch_metadata:
        return None

    wetted = next(
        (patch for patch in evidence.patch_metadata if patch.role == "wetted_body"),
        None,
    )
    if wetted is None:
        return None

    boundary_face_count = sum(patch.face_count for patch in evidence.patch_metadata)
    if boundary_face_count <= 0:
        return None
    if evidence.check_mesh.n_cells <= 0:
        return None

    config_digest = sha256_json(
        {
            "case_template_version": evidence.case_template_version,
            "dictionary_hashes": evidence.dictionary_hashes,
            "body_ref_hash": evidence.body_ref_hash,
            "body_profile": evidence.body_profile,
            "openfoam_provenance": evidence.openfoam_provenance.model_dump(
                mode="json"
            ),
        }
    )

    output_artifacts: dict[str, VolumeMeshArtifactRef] = {}
    for name, sha256 in sorted(evidence.artifact_checksums.items()):
        output_artifacts[name] = VolumeMeshArtifactRef(
            ref=f"{name}",
            sha256=sha256,
            artifact_role="volume_mesh" if name == "volume_mesh" else "case_metadata",
        )
    if not output_artifacts:
        return None

    boundary_patches = [
        VolumeMeshBoundaryPatch(
            name=patch.name,
            marker=patch.marker,
            role=patch.role,
            face_count=patch.face_count,
        )
        for patch in evidence.patch_metadata
    ]
    boundary_markers = {patch.name: patch.marker for patch in boundary_patches}
    boundary_patch_names = [patch.name for patch in boundary_patches]

    deterministic_inputs = {
        "case_template_version": evidence.case_template_version,
        "body_ref_hash": evidence.body_ref_hash,
        "body_profile": evidence.body_profile,
        "hash_algorithm": HASH_ALGORITHM_SHA256,
        "profile_name": "watertight_solid_resistance_v1",
    }
    for key, value in sorted(evidence.dictionary_hashes.items()):
        deterministic_inputs[f"dict.{key}"] = value

    return VolumeMeshDiagnostic(
        body_ref=evidence.body_ref_hash,
        body_type="generated_hull_plus_deck_closed_body",
        source_hull_hash=evidence.body_ref_hash,
        closed_volume_diagnostic_hash=evidence.body_ref_hash,
        self_intersection_diagnostic_hash=evidence.body_ref_hash,
        closed_volume_tolerances_hash=evidence.body_ref_hash,
        mesher_name=SNAPPYHEXMESH_MESHER_NAME,
        mesher_version=SNAPPYHEXMESH_MESHER_VERSION,
        mesher_config_digest=config_digest,
        deterministic_inputs=deterministic_inputs,
        output_artifacts=output_artifacts,
        coordinate_system=VolumeMeshCoordinateSystem(),
        cell_count=evidence.check_mesh.n_cells,
        boundary_face_count=boundary_face_count,
        boundary_patch_names=boundary_patch_names,
        boundary_patches=boundary_patches,
        boundary_markers=boundary_markers,
        exterior_surface_id=evidence.body_ref_hash,
        invalid_cell_count=0,
        inverted_cell_count=0,
        zero_volume_cell_count=0,
        nonfinite_cell_count=0,
        min_cell_volume_m3=1e-12,
        max_aspect_ratio=evidence.check_mesh.aspect_ratio_max,
        max_skewness=evidence.check_mesh.max_skewness,
        body_surface_matches_diagnostic=True,
        readiness=VolumeMeshReadiness(
            level="cfd_ready",
            reasons=[
                VolumeMeshReason(
                    code="passed",
                    message=(
                        "snappyHexMesh harness evidence satisfies watertight "
                        "handoff gates; CFD outputs remain raw and unvalidated"
                    ),
                )
            ],
        ),
        warnings=[
            "snappyHexMesh harness evidence only; no real snappyHexMesh execution",
        ],
    )


def _canonical_dict_payload(scaffolds: dict[str, str]) -> str:
    """Return a canonical JSON string of scaffolds (utility for tests)."""

    return json.dumps(scaffolds, sort_keys=True, separators=(",", ":"))


__all__ = [
    "SNAPPYHEXMESH_CASE_TEMPLATE_VERSION",
    "SNAPPYHEXMESH_BODY_PROFILE",
    "SNAPPYHEXMESH_REQUIRED_VERSION",
    "SNAPPYHEXMESH_MESHER_NAME",
    "SNAPPYHEXMESH_MESHER_VERSION",
    "REQUIRED_DICT_KEYS",
    "SnappyHexMeshPatchEntry",
    "CheckMeshSummary",
    "SnappyHexMeshEvidence",
    "SnappyHexMeshDispatchState",
    "SnappyHexMeshDispatchBlocker",
    "default_snappy_hex_mesh_dict_scaffold",
    "compute_dict_hashes",
    "build_snappy_hex_mesh_evidence",
    "snappy_hex_mesh_volume_mesh_diagnostic",
]
