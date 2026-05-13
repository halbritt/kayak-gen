"""Closed-volume contract models and diagnostics for explicit triangle meshes.

This module is intentionally limited to caller-supplied synthetic meshes. It
does not build closed bodies from generated ``Hull`` surfaces and it never
promotes a body to ``cfd_ready``.
"""

from __future__ import annotations

from collections import Counter
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

ClosedVolumeReadinessLevel = Literal["invalid", "closed_volume"]
ClosedVolumeBodyType = Literal["explicit_synthetic_triangle_mesh"]

DEFAULT_VERTEX_WELD_TOLERANCE_M = 1e-6
DEFAULT_DEGENERATE_AREA_TOLERANCE_M2 = 1e-12
DEFAULT_SIGNED_VOLUME_TOLERANCE_M3 = 1e-12


class ClosedVolumeTolerances(BaseModel):
    """Numeric tolerances used by closed-volume diagnostics."""

    model_config = ConfigDict(extra="forbid")

    vertex_weld_tolerance_m: float = Field(default=DEFAULT_VERTEX_WELD_TOLERANCE_M, gt=0)
    degenerate_area_tolerance_m2: float = Field(
        default=DEFAULT_DEGENERATE_AREA_TOLERANCE_M2, ge=0
    )
    signed_volume_tolerance_m3: float = Field(
        default=DEFAULT_SIGNED_VOLUME_TOLERANCE_M3, ge=0
    )


class ClosedVolumePolicy(BaseModel):
    """Policy identity for the safe synthetic closed-volume slice."""

    model_config = ConfigDict(extra="forbid")

    profile_name: str = "explicit_synthetic_closed_volume_v1"
    body_type: ClosedVolumeBodyType = "explicit_synthetic_triangle_mesh"
    waterline_semantics: Literal["metadata_only"] = "metadata_only"
    cap_policy: Literal["not_applicable_explicit_mesh"] = "not_applicable_explicit_mesh"
    deck_join_policy: Literal["not_applicable_explicit_mesh"] = (
        "not_applicable_explicit_mesh"
    )
    normal_orientation: Literal["outward_positive_signed_volume"] = (
        "outward_positive_signed_volume"
    )
    cfd_readiness_policy: Literal["never_claim_cfd_ready"] = "never_claim_cfd_ready"
    tolerances: ClosedVolumeTolerances = Field(default_factory=ClosedVolumeTolerances)


class ClosedSurfacePart(BaseModel):
    """Serializable triangle-mesh part in a closed-volume body."""

    model_config = ConfigDict(extra="forbid")

    name: str
    vertices: tuple[tuple[float, float, float], ...]
    faces: tuple[tuple[int, int, int], ...]


class ClosedVolumeBody(BaseModel):
    """Serializable explicit synthetic closed-volume body."""

    model_config = ConfigDict(extra="forbid")

    body_id: str
    body_type: ClosedVolumeBodyType = "explicit_synthetic_triangle_mesh"
    policy: ClosedVolumePolicy = Field(default_factory=ClosedVolumePolicy)
    parts: tuple[ClosedSurfacePart, ...]


class ClosedVolumeReadiness(BaseModel):
    """Closed-volume diagnostic result without CFD readiness claims."""

    model_config = ConfigDict(extra="forbid")

    level: ClosedVolumeReadinessLevel
    reasons: list[str] = Field(default_factory=list)


class ClosedSurfacePartDiagnostics(BaseModel):
    """Per-part topology and numeric diagnostics."""

    model_config = ConfigDict(extra="forbid")

    name: str
    vertex_count: int = Field(ge=0)
    face_count: int = Field(ge=0)
    raw_boundary_edges: int = Field(ge=0)
    raw_nonmanifold_edges: int = Field(ge=0)
    welded_boundary_edges: int = Field(ge=0)
    welded_nonmanifold_edges: int = Field(ge=0)
    degenerate_faces: int = Field(ge=0)
    nonfinite_vertices: int = Field(ge=0)
    nonfinite_faces: int = Field(ge=0)
    invalid_face_indices: int = Field(ge=0)


class ClosedVolumeDiagnostics(BaseModel):
    """Authoritative body-level diagnostics for a closed-volume body."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    body_id: str
    body_type: ClosedVolumeBodyType
    profile_name: str
    policy: ClosedVolumePolicy
    readiness: ClosedVolumeReadiness
    part_diagnostics: list[ClosedSurfacePartDiagnostics]
    vertex_count: int = Field(ge=0)
    face_count: int = Field(ge=0)
    raw_boundary_edges: int = Field(ge=0)
    raw_nonmanifold_edges: int = Field(ge=0)
    welded_boundary_edges: int = Field(ge=0)
    welded_nonmanifold_edges: int = Field(ge=0)
    degenerate_faces: int = Field(ge=0)
    nonfinite_vertices: int = Field(ge=0)
    nonfinite_faces: int = Field(ge=0)
    invalid_face_indices: int = Field(ge=0)
    signed_volume_m3: float
    warnings: list[str] = Field(default_factory=list)
    cfd_ready: Literal[False] = False


def explicit_synthetic_body(
    vertices: object,
    faces: object,
    *,
    body_id: str = "explicit-synthetic-body",
    part_name: str = "body",
    policy: ClosedVolumePolicy | None = None,
) -> ClosedVolumeBody:
    """Return a serializable body from caller-supplied triangle arrays."""

    vertex_rows = _vertices_tuple(vertices)
    face_rows = _faces_tuple(faces)
    return ClosedVolumeBody(
        body_id=body_id,
        policy=policy or ClosedVolumePolicy(),
        parts=(ClosedSurfacePart(name=part_name, vertices=vertex_rows, faces=face_rows),),
    )


def diagnose_closed_volume_body(body: ClosedVolumeBody) -> ClosedVolumeDiagnostics:
    """Diagnose an explicit synthetic body at part and assembled-body levels."""

    if body.body_type != "explicit_synthetic_triangle_mesh":
        raise ValueError("closed-volume diagnostics only accept explicit synthetic meshes")
    if body.policy.body_type != body.body_type:
        raise ValueError("policy body_type must match body body_type")

    part_reports = [_diagnose_part(part, body.policy.tolerances) for part in body.parts]
    vertices, faces = _assemble_parts(body.parts)
    body_report = _diagnose_arrays(vertices, faces, body.policy.tolerances)
    signed_volume = _signed_volume(vertices, body_report.valid_faces)

    reasons = _readiness_reasons(body_report, signed_volume, body.policy.tolerances)
    readiness = ClosedVolumeReadiness(
        level="invalid" if reasons else "closed_volume",
        reasons=reasons,
    )
    warnings = list(reasons)
    if readiness.level == "closed_volume":
        warnings.append("closed-volume synthetic diagnostic only; not cfd_ready")

    return ClosedVolumeDiagnostics(
        body_id=body.body_id,
        body_type=body.body_type,
        profile_name=body.policy.profile_name,
        policy=body.policy,
        readiness=readiness,
        part_diagnostics=[
            ClosedSurfacePartDiagnostics(
                name=part.name,
                vertex_count=report.vertex_count,
                face_count=report.face_count,
                raw_boundary_edges=report.raw_boundary_edges,
                raw_nonmanifold_edges=report.raw_nonmanifold_edges,
                welded_boundary_edges=report.welded_boundary_edges,
                welded_nonmanifold_edges=report.welded_nonmanifold_edges,
                degenerate_faces=report.degenerate_faces,
                nonfinite_vertices=report.nonfinite_vertices,
                nonfinite_faces=report.nonfinite_faces,
                invalid_face_indices=report.invalid_face_indices,
            )
            for part, report in zip(body.parts, part_reports, strict=True)
        ],
        vertex_count=body_report.vertex_count,
        face_count=body_report.face_count,
        raw_boundary_edges=body_report.raw_boundary_edges,
        raw_nonmanifold_edges=body_report.raw_nonmanifold_edges,
        welded_boundary_edges=body_report.welded_boundary_edges,
        welded_nonmanifold_edges=body_report.welded_nonmanifold_edges,
        degenerate_faces=body_report.degenerate_faces,
        nonfinite_vertices=body_report.nonfinite_vertices,
        nonfinite_faces=body_report.nonfinite_faces,
        invalid_face_indices=body_report.invalid_face_indices,
        signed_volume_m3=signed_volume,
        warnings=warnings,
    )


def dispatch_evidence_satisfies_profile(
    evidence: object,
    required_mesh_profile: str | None,
    required_mesh_readiness: str,
) -> bool:
    """Return whether this safe-slice evidence can satisfy CFD dispatch.

    Workflow 0027 deliberately never promotes synthetic closed-volume
    diagnostics to ``cfd_ready``. The validator still parses the evidence so
    dispatch code can distinguish contract-aware rejection from blind manifest
    trust.
    """

    diagnostics = ClosedVolumeDiagnostics.model_validate(evidence)
    if required_mesh_profile and diagnostics.profile_name != required_mesh_profile:
        return False
    if required_mesh_readiness == "cfd_ready":
        return False
    return False


class _ArrayDiagnostics(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    vertex_count: int
    face_count: int
    raw_boundary_edges: int
    raw_nonmanifold_edges: int
    welded_boundary_edges: int
    welded_nonmanifold_edges: int
    degenerate_faces: int
    nonfinite_vertices: int
    nonfinite_faces: int
    invalid_face_indices: int
    valid_faces: np.ndarray


def _diagnose_part(
    part: ClosedSurfacePart,
    tolerances: ClosedVolumeTolerances,
) -> _ArrayDiagnostics:
    return _diagnose_arrays(
        np.asarray(part.vertices, dtype=float),
        np.asarray(part.faces, dtype=np.int64),
        tolerances,
    )


def _diagnose_arrays(
    vertices: np.ndarray,
    faces: np.ndarray,
    tolerances: ClosedVolumeTolerances,
) -> _ArrayDiagnostics:
    vertices = np.asarray(vertices, dtype=float)
    faces = np.asarray(faces)
    vertex_finite = (
        np.isfinite(vertices).all(axis=1)
        if vertices.ndim == 2 and vertices.shape[1] == 3
        else np.array([], dtype=bool)
    )
    face_finite = (
        np.isfinite(faces).all(axis=1)
        if faces.ndim == 2 and faces.shape[1] == 3
        else np.array([], dtype=bool)
    )
    face_indices = (
        np.zeros((len(faces), 3), dtype=np.int64)
        if faces.ndim == 2
        else np.empty((0, 3), dtype=np.int64)
    )
    if face_finite.any():
        face_indices[face_finite] = faces[face_finite].astype(np.int64)

    valid_faces_mask = face_finite.copy()
    index_range_mask = (face_indices >= 0).all(axis=1)
    index_range_mask &= (face_indices < len(vertices)).all(axis=1)
    valid_faces_mask &= index_range_mask
    if vertex_finite.size and index_range_mask.any():
        finite_vertex_mask = np.zeros_like(valid_faces_mask)
        finite_vertex_mask[index_range_mask] = vertex_finite[
            face_indices[index_range_mask]
        ].all(axis=1)
        valid_faces_mask &= finite_vertex_mask
    valid_faces = face_indices[valid_faces_mask]

    areas = _face_areas(vertices, valid_faces)
    degenerate_faces = int((areas <= tolerances.degenerate_area_tolerance_m2).sum())
    nonfinite_vertices = int(vertex_finite.size - vertex_finite.sum())
    nonfinite_faces = int(face_finite.size - face_finite.sum())
    invalid_face_indices = int(face_finite.sum() - valid_faces_mask.sum())

    raw_boundary_edges, raw_nonmanifold_edges = _edge_counts(valid_faces)
    welded_faces, _ = _welded_faces(
        vertices,
        valid_faces,
        tolerances.vertex_weld_tolerance_m,
    )
    welded_boundary_edges, welded_nonmanifold_edges = _edge_counts(welded_faces)

    return _ArrayDiagnostics(
        vertex_count=int(len(vertices)),
        face_count=int(len(valid_faces)),
        raw_boundary_edges=raw_boundary_edges,
        raw_nonmanifold_edges=raw_nonmanifold_edges,
        welded_boundary_edges=welded_boundary_edges,
        welded_nonmanifold_edges=welded_nonmanifold_edges,
        degenerate_faces=degenerate_faces,
        nonfinite_vertices=nonfinite_vertices,
        nonfinite_faces=nonfinite_faces,
        invalid_face_indices=invalid_face_indices,
        valid_faces=valid_faces,
    )


def _assemble_parts(parts: tuple[ClosedSurfacePart, ...]) -> tuple[np.ndarray, np.ndarray]:
    vertices_by_part: list[np.ndarray] = []
    faces_by_part: list[np.ndarray] = []
    offset = 0
    for part in parts:
        vertices = np.asarray(part.vertices, dtype=float)
        faces = np.asarray(part.faces, dtype=np.int64)
        vertices_by_part.append(vertices)
        faces_by_part.append(faces + offset)
        offset += len(vertices)
    if not vertices_by_part:
        return np.empty((0, 3), dtype=float), np.empty((0, 3), dtype=np.int64)
    return np.vstack(vertices_by_part), np.vstack(faces_by_part)


def _vertices_tuple(vertices: object) -> tuple[tuple[float, float, float], ...]:
    array = np.asarray(vertices, dtype=float)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("vertices must be an Nx3 array")
    return tuple(tuple(float(value) for value in row) for row in array)


def _faces_tuple(faces: object) -> tuple[tuple[int, int, int], ...]:
    array = np.asarray(faces)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("faces must be an Nx3 array")
    if not np.isfinite(array).all():
        raise ValueError("faces must contain finite vertex indices")
    return tuple(tuple(int(value) for value in row) for row in array)


def _face_areas(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    if len(faces) == 0:
        return np.array([], dtype=float)
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    return 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)


def _edge_counts(faces: np.ndarray) -> tuple[int, int]:
    edges: Counter[tuple[int, int]] = Counter()
    for face in faces:
        if len(set(face.tolist())) < 3:
            continue
        for start, end in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edges[tuple(sorted((int(start), int(end))))] += 1
    boundary = sum(1 for count in edges.values() if count == 1)
    nonmanifold = sum(1 for count in edges.values() if count > 2)
    return boundary, nonmanifold


def _welded_faces(
    vertices: np.ndarray,
    faces: np.ndarray,
    tolerance_m: float,
) -> tuple[np.ndarray, int]:
    if len(vertices) == 0 or len(faces) == 0:
        return faces.copy(), 0

    finite = np.isfinite(vertices).all(axis=1)
    inverse = np.empty(len(vertices), dtype=np.int64)
    next_index = 0
    if finite.any():
        quantized = np.rint(vertices[finite] / tolerance_m).astype(np.int64)
        _, finite_inverse = np.unique(quantized, axis=0, return_inverse=True)
        inverse[finite] = finite_inverse
        next_index = int(finite_inverse.max() + 1)
    nonfinite_indices = np.flatnonzero(~finite)
    if len(nonfinite_indices):
        inverse[nonfinite_indices] = np.arange(
            next_index,
            next_index + len(nonfinite_indices),
            dtype=np.int64,
        )
    return inverse[faces], int(inverse.max() + 1)


def _signed_volume(vertices: np.ndarray, faces: np.ndarray) -> float:
    if len(faces) == 0:
        return 0.0
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def _readiness_reasons(
    report: _ArrayDiagnostics,
    signed_volume: float,
    tolerances: ClosedVolumeTolerances,
) -> list[str]:
    reasons: list[str] = []
    if report.nonfinite_vertices:
        reasons.append("body contains non-finite vertices")
    if report.nonfinite_faces:
        reasons.append("body contains non-finite face indices")
    if report.invalid_face_indices:
        reasons.append("body contains out-of-range face indices")
    if report.degenerate_faces:
        reasons.append("body contains degenerate faces")
    if report.raw_boundary_edges or report.welded_boundary_edges:
        reasons.append("body has boundary edges and is not closed")
    if report.raw_nonmanifold_edges or report.welded_nonmanifold_edges:
        reasons.append("body has non-manifold edges")
    if signed_volume <= tolerances.signed_volume_tolerance_m3:
        reasons.append("body signed volume is not positive with outward normals")
    return reasons
