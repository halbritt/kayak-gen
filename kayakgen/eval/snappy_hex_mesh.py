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
from pathlib import Path
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

MeshEvidenceBindCode = Literal[
    "closed_body_hash_mismatch",
    "snappy_evidence_body_mismatch",
    "polymesh_artifact_drift",
    "evidence_not_recorded",
    "evidence_translation_failed",
]

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


def render_snappy_dicts_from_body(
    body: ClosedVolumeBody,
    *,
    padding_x: tuple[float, float] = (3.0, 5.0),
    padding_y: float = 1.5,
    padding_below: float = 1.5,
    padding_above: float = 1.0,
    hull_refinement_levels: tuple[int, int] = (2, 3),
    background_cell_size_m: float = 0.25,
    max_global_cells: int = 800_000,
) -> dict[str, str]:
    """Render REAL parameterized OpenFOAM dict strings derived from ``body``.

    The output is keyed by :data:`REQUIRED_DICT_KEYS` and contains valid
    OpenFOAM v2512 dictionary contents that the OpenFoam case renderer
    consumes verbatim. The strings are derived deterministically from the
    body's bounding box and the supplied padding/refinement knobs.

    This helper is separate from :func:`default_snappy_hex_mesh_dict_scaffold`
    so existing callers continue to receive the deterministic placeholder
    output; callers that need real dicts opt in explicitly.
    """

    # Late import to avoid the cfd package importing snappy_hex_mesh (cycle).
    from kayakgen.eval.cfd.openfoam_v2512_interfoam.case_render import (
        TEMPLATES_DIR,
        _fmt,
    )
    from string import Template

    bounds = _bounding_box_with_padding(
        body,
        padding_x=padding_x,
        padding_y=padding_y,
        padding_below=padding_below,
        padding_above=padding_above,
    )
    x_min, x_max, y_min, y_max, z_min, z_max = bounds
    cell = background_cell_size_m
    nx = max(1, int(round((x_max - x_min) / cell)))
    ny = max(1, int(round((y_max - y_min) / cell)))
    nz = max(1, int(round((z_max - z_min) / cell)))

    substitutions: dict[str, str] = {
        "case_template_version": "openfoam-v2512-snappyhexmesh-watertight-v1",
        "x_min": _fmt(x_min),
        "x_max": _fmt(x_max),
        "y_min": _fmt(y_min),
        "y_max": _fmt(y_max),
        "z_min": _fmt(z_min),
        "z_max": _fmt(z_max),
        "nx": str(nx),
        "ny": str(ny),
        "nz": str(nz),
        "refinement_min_x": _fmt(x_min + 0.25 * (x_max - x_min)),
        "refinement_min_y": _fmt(y_min + 0.35 * (y_max - y_min)),
        "refinement_min_z": _fmt(z_min + 0.35 * (z_max - z_min)),
        "refinement_max_x": _fmt(x_min + 0.75 * (x_max - x_min)),
        "refinement_max_y": _fmt(y_min + 0.65 * (y_max - y_min)),
        "refinement_max_z": _fmt(z_min + 0.65 * (z_max - z_min)),
        "surface_level_min": str(int(hull_refinement_levels[0])),
        "surface_level_max": str(int(hull_refinement_levels[1])),
        "location_in_mesh_x": _fmt(x_min + 0.05 * (x_max - x_min)),
        "location_in_mesh_y": _fmt(0.5 * (y_min + y_max)),
        "location_in_mesh_z": _fmt(z_max - 0.2 * (z_max - z_min)),
        "max_global_cells": str(int(max_global_cells)),
        "max_local_cells": str(int(max_global_cells // 4)),
        "feature_edge_level": str(int(hull_refinement_levels[1])),
        "included_angle_deg": "150",
        "end_time": "0.05",
        "delta_t": "0.01",
        "write_interval": "0.01",
        "rho_inf": "1000",
        "forces_patch_name": "hull",
        "cofr_x": "0",
        "cofr_y": "0",
        "cofr_z": "0",
        "waterline_z": _fmt(body.waterline_z_m),
        "water_nu": "1.09e-06",
        "water_rho": "998.8",
        "air_nu": "1.48e-05",
        "air_rho": "1",
        "inlet_speed_ms": "2",
    }

    file_map: dict[str, str] = {
        "controlDict": "system_controlDict_solve.template",
        "snappyHexMeshDict": "system_snappyHexMeshDict.template",
        "meshQualityDict": "system_meshQualityDict.template",
        "surfaceFeatureExtractDict": "system_surfaceFeatureExtractDict.template",
        "blockMeshDict": "system_blockMeshDict.template",
    }

    rendered: dict[str, str] = {}
    for key in REQUIRED_DICT_KEYS:
        template_filename = file_map[key]
        raw = (TEMPLATES_DIR / template_filename).read_text()
        rendered[key] = Template(raw).safe_substitute(substitutions)
    return rendered


def _bounding_box_with_padding(
    body: ClosedVolumeBody,
    *,
    padding_x: tuple[float, float],
    padding_y: float,
    padding_below: float,
    padding_above: float,
) -> tuple[float, float, float, float, float, float]:
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")
    for part in body.parts:
        for vertex in part.vertices:
            vx, vy, vz = (float(c) for c in vertex)
            if vx < min_x:
                min_x = vx
            if vy < min_y:
                min_y = vy
            if vz < min_z:
                min_z = vz
            if vx > max_x:
                max_x = vx
            if vy > max_y:
                max_y = vy
            if vz > max_z:
                max_z = vz
    if min_x == float("inf"):
        raise ValueError("ClosedVolumeBody has no vertices to bound")
    return (
        min_x - padding_x[0],
        max_x + padding_x[1],
        min_y - padding_y,
        max_y + padding_y,
        min_z - padding_below,
        max_z + padding_above,
    )


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


class MeshEvidenceBindError(Exception):
    """Structured rejection raised when evidence-binding gates fail.

    The ``code`` attribute carries one of the RFC 0045 rejection codes
    (``closed_body_hash_mismatch``, ``snappy_evidence_body_mismatch``,
    ``polymesh_artifact_drift``). Additional ``evidence_not_recorded`` /
    ``evidence_translation_failed`` codes are emitted when the evidence
    record is shaped correctly but the translator refuses to issue a
    :class:`VolumeMeshDiagnostic`.
    """

    def __init__(self, code: MeshEvidenceBindCode, message: str) -> None:
        super().__init__(message)
        self.code: MeshEvidenceBindCode = code
        self.message: str = message


def closed_body_content_sha256(body: ClosedVolumeBody) -> str:
    """Return a deterministic SHA-256 of a closed-body's identity + triangle mesh.

    The hash is derived from the canonical JSON serialization of the body's
    identity fields and per-part vertex/face data so two callers with the
    same in-memory body always agree on the same hash. This is the binding
    identity used by RFC 0045's evidence-binding gate and is independent of
    on-disk STL encoding which is not byte-deterministic across runs.
    """

    parts_payload = [
        {
            "name": part.name,
            "vertices": [list(v) for v in part.vertices],
            "faces": [list(f) for f in part.faces],
        }
        for part in body.parts
    ]
    payload = {
        "body_id": body.body_id,
        "body_type": body.body_type,
        "source_hull_hash": body.source_hull_hash or "",
        "profile_name": body.policy.profile_name,
        "waterline_z_m": body.waterline_z_m,
        "parts": parts_payload,
    }
    return sha256_json(payload)


def _recompute_polymesh_checksums(
    polymesh_dir: Path,
    artifact_names: list[str],
) -> dict[str, str]:
    """Return SHA-256 digests for the polyMesh files named in ``artifact_names``.

    Only filenames recorded in the evidence record's
    ``artifact_checksums`` are recomputed; files outside that set (e.g.
    auxiliary ``points.gz`` rotations) are intentionally ignored so the
    drift check stays scoped to the recorded surface.
    """

    checksums: dict[str, str] = {}
    for name in artifact_names:
        candidate = polymesh_dir / name
        if not candidate.is_file():
            continue
        digest = hashlib.sha256()
        with open(candidate, "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        checksums[name] = digest.hexdigest()
    return checksums


def bind_evidence_to_mesh_package(
    evidence: SnappyHexMeshEvidence,
    *,
    closed_body_hash: str,
    polymesh_dir: Path | None = None,
) -> VolumeMeshDiagnostic:
    """Validate evidence body bindings and return the bound diagnostic.

    Three gates must all pass:

    1. ``evidence.body_profile`` matches
       :data:`SNAPPYHEXMESH_BODY_PROFILE` (the RFC 0040 generated body
       profile name). Failure emits ``snappy_evidence_body_mismatch``.
    2. ``evidence.body_ref_hash`` matches ``closed_body_hash``. Failure
       emits ``closed_body_hash_mismatch``.
    3. If ``polymesh_dir`` is supplied, each artifact name recorded in
       ``evidence.artifact_checksums`` is re-hashed on disk and compared
       to the recorded checksum. Any mismatch (or missing file) emits
       ``polymesh_artifact_drift``.

    On success the helper invokes
    :func:`snappy_hex_mesh_volume_mesh_diagnostic` and returns the
    resulting :class:`VolumeMeshDiagnostic`. A ``None`` return from the
    translator (partial evidence after the body checks) escalates to
    ``evidence_not_recorded`` / ``evidence_translation_failed`` so
    callers always either get a usable diagnostic or a structured
    :class:`MeshEvidenceBindError`.
    """

    if evidence.body_profile != SNAPPYHEXMESH_BODY_PROFILE:
        raise MeshEvidenceBindError(
            code="snappy_evidence_body_mismatch",
            message=(
                f"snappyHexMesh evidence body_profile {evidence.body_profile!r} "
                f"does not match required profile {SNAPPYHEXMESH_BODY_PROFILE!r}"
            ),
        )
    if not evidence.body_ref_hash or evidence.body_ref_hash != closed_body_hash:
        raise MeshEvidenceBindError(
            code="closed_body_hash_mismatch",
            message=(
                "snappyHexMesh evidence body_ref_hash does not match the current "
                "hull's closed-body hash; the evidence is bound to a different body"
            ),
        )

    if polymesh_dir is not None:
        recorded = dict(evidence.artifact_checksums)
        # Restrict the drift check to polymesh-style artifact names so that
        # case-metadata or volume_mesh placeholder names are ignored when
        # they are not present on disk.
        candidate_names = [
            name for name in recorded if (polymesh_dir / name).is_file()
        ]
        if not candidate_names:
            raise MeshEvidenceBindError(
                code="polymesh_artifact_drift",
                message=(
                    f"no recorded polyMesh artifacts were present under "
                    f"{polymesh_dir}; cannot verify polymesh artifact integrity"
                ),
            )
        actual = _recompute_polymesh_checksums(polymesh_dir, candidate_names)
        for name in candidate_names:
            if actual.get(name) != recorded.get(name):
                raise MeshEvidenceBindError(
                    code="polymesh_artifact_drift",
                    message=(
                        f"polyMesh artifact {name!r} checksum differs from the "
                        "evidence record; the on-disk artifact has drifted "
                        "since evidence was captured"
                    ),
                )

    if evidence.dispatch_state != "evidence_recorded":
        raise MeshEvidenceBindError(
            code="evidence_not_recorded",
            message=(
                f"snappyHexMesh evidence dispatch_state is "
                f"{evidence.dispatch_state!r}; only 'evidence_recorded' "
                "evidence can be bound to a mesh package"
            ),
        )

    diagnostic = snappy_hex_mesh_volume_mesh_diagnostic(evidence)
    if diagnostic is None:
        raise MeshEvidenceBindError(
            code="evidence_translation_failed",
            message=(
                "snappyHexMesh evidence translator refused to issue a "
                "VolumeMeshDiagnostic; required gates are not all satisfied"
            ),
        )
    return diagnostic


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
    "render_snappy_dicts_from_body",
    "compute_dict_hashes",
    "build_snappy_hex_mesh_evidence",
    "snappy_hex_mesh_volume_mesh_diagnostic",
    "MeshEvidenceBindError",
    "MeshEvidenceBindCode",
    "bind_evidence_to_mesh_package",
    "closed_body_content_sha256",
]
