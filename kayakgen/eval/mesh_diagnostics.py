"""Mesh diagnostics for generated hull and deck surfaces."""

from __future__ import annotations

from collections import Counter
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from kayakgen.model.geometry import PartType
from kayakgen.model.hull import Hull

ReadinessLevel = Literal["invalid", "display", "stl_surface", "cfd_surface_candidate", "cfd_ready"]

DEFAULT_WELD_TOLERANCE_M = 1e-6
DEGENERATE_AREA_TOLERANCE_M2 = 1e-12


class MeshBoundingBox(BaseModel):
    """Axis-aligned mesh bounds in model coordinates."""

    model_config = ConfigDict(extra="forbid")

    min_xyz: tuple[float, float, float]
    max_xyz: tuple[float, float, float]


class MeshReadiness(BaseModel):
    """Conservative downstream-readiness classification for a mesh."""

    model_config = ConfigDict(extra="forbid")

    level: ReadinessLevel
    reasons: list[str] = Field(default_factory=list)


class MeshSolverProfile(BaseModel):
    """Solver-readiness profile. Required before emitting ``cfd_ready``."""

    model_config = ConfigDict(extra="forbid")

    profile_name: str
    requires_watertight: bool = True
    accepted_parts: tuple[PartType, ...] = ("hull", "deck")
    normal_orientation: str = "consistent"
    waterline_boundary_policy: str = "undecided"
    duplicate_vertex_tolerance_m: float = Field(default=DEFAULT_WELD_TOLERANCE_M, gt=0)
    degenerate_area_tolerance_m2: float = Field(default=DEGENERATE_AREA_TOLERANCE_M2, ge=0)
    max_nonmanifold_edges: int = Field(default=0, ge=0)


class MeshProfile(BaseModel):
    """Basic mesh profile independent of topology checks."""

    model_config = ConfigDict(extra="forbid")

    part: PartType
    stations: int | None = None
    vertex_count: int = Field(ge=0)
    face_count: int = Field(ge=0)
    welded_vertex_count: int = Field(ge=0)
    weld_tolerance_m: float = Field(gt=0)
    bbox: MeshBoundingBox | None = None
    surface_area_m2: float = Field(ge=0)


class MeshDiagnostics(BaseModel):
    """Topology and numeric diagnostics for a generated surface mesh."""

    model_config = ConfigDict(extra="forbid")

    profile: MeshProfile
    readiness: MeshReadiness
    raw_boundary_edges: int = Field(ge=0)
    raw_nonmanifold_edges: int = Field(ge=0)
    welded_boundary_edges: int = Field(ge=0)
    welded_nonmanifold_edges: int = Field(ge=0)
    degenerate_faces: int = Field(ge=0)
    nonfinite_vertices: int = Field(ge=0)
    nonfinite_faces: int = Field(ge=0)
    solver_profile: MeshSolverProfile | None = None
    warnings: list[str] = Field(default_factory=list)


def diagnose_mesh(
    hull: Hull,
    part: PartType = "hull",
    stations: int | None = None,
    *,
    weld_tolerance_m: float = DEFAULT_WELD_TOLERANCE_M,
) -> MeshDiagnostics:
    """Return diagnostics for ``hull`` using its declared ``HullGeometry.mesh``."""

    if weld_tolerance_m <= 0:
        raise ValueError("weld_tolerance_m must be positive")

    vertices, faces = hull.to_geometry().mesh(part, stations=stations)
    vertices = np.asarray(vertices, dtype=float)
    faces = np.asarray(faces)

    vertex_finite_mask = np.isfinite(vertices).all(axis=1) if vertices.ndim == 2 else np.array([])
    face_finite_mask = (
        np.isfinite(faces).all(axis=1)
        if faces.ndim == 2 and faces.shape[1] == 3
        else np.array([])
    )
    nonfinite_vertices = int(vertex_finite_mask.size - vertex_finite_mask.sum())
    nonfinite_faces = int(face_finite_mask.size - face_finite_mask.sum())

    face_indices = _finite_face_indices(faces, face_finite_mask)
    areas = _face_areas(vertices, face_indices, vertex_finite_mask, face_finite_mask)
    degenerate_faces = int((areas <= DEGENERATE_AREA_TOLERANCE_M2).sum())
    surface_area = float(areas[np.isfinite(areas)].sum())

    welded_faces, welded_vertex_count = _welded_faces(vertices, face_indices, weld_tolerance_m)
    raw_boundary_edges, raw_nonmanifold_edges = _edge_counts(face_indices)
    welded_boundary_edges, welded_nonmanifold_edges = _edge_counts(welded_faces)

    bbox = _bbox(vertices, vertex_finite_mask)
    profile = MeshProfile(
        part=part,
        stations=stations,
        vertex_count=int(len(vertices)),
        face_count=int(len(face_indices)),
        welded_vertex_count=welded_vertex_count,
        weld_tolerance_m=weld_tolerance_m,
        bbox=bbox,
        surface_area_m2=surface_area,
    )

    readiness = _readiness(
        raw_boundary_edges=raw_boundary_edges,
        raw_nonmanifold_edges=raw_nonmanifold_edges,
        welded_boundary_edges=welded_boundary_edges,
        welded_nonmanifold_edges=welded_nonmanifold_edges,
        degenerate_faces=degenerate_faces,
        nonfinite_vertices=nonfinite_vertices,
        nonfinite_faces=nonfinite_faces,
    )

    return MeshDiagnostics(
        profile=profile,
        readiness=readiness,
        raw_boundary_edges=raw_boundary_edges,
        raw_nonmanifold_edges=raw_nonmanifold_edges,
        welded_boundary_edges=welded_boundary_edges,
        welded_nonmanifold_edges=welded_nonmanifold_edges,
        degenerate_faces=degenerate_faces,
        nonfinite_vertices=nonfinite_vertices,
        nonfinite_faces=nonfinite_faces,
        solver_profile=None,
        warnings=list(readiness.reasons),
    )


def _finite_face_indices(faces: np.ndarray, face_finite_mask: np.ndarray) -> np.ndarray:
    if faces.ndim != 2 or faces.shape[1] != 3:
        return np.empty((0, 3), dtype=np.int64)
    face_indices = np.zeros(faces.shape, dtype=np.int64)
    if face_finite_mask.any():
        face_indices[face_finite_mask] = faces[face_finite_mask].astype(np.int64)
    return face_indices


def _face_areas(
    vertices: np.ndarray,
    faces: np.ndarray,
    vertex_finite_mask: np.ndarray,
    face_finite_mask: np.ndarray,
) -> np.ndarray:
    areas = np.zeros(len(faces), dtype=float)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or faces.ndim != 2 or faces.shape[1] != 3:
        return areas

    valid = face_finite_mask.copy()
    valid &= (faces >= 0).all(axis=1)
    valid &= (faces < len(vertices)).all(axis=1)
    if vertex_finite_mask.size:
        valid &= vertex_finite_mask[faces].all(axis=1)
    if not valid.any():
        return areas

    valid_faces = faces[valid]
    a = vertices[valid_faces[:, 0]]
    b = vertices[valid_faces[:, 1]]
    c = vertices[valid_faces[:, 2]]
    areas[valid] = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    return areas


def _edge_counts(faces: np.ndarray) -> tuple[int, int]:
    edges: Counter[tuple[int, int]] = Counter()
    for face in faces:
        if len(set(face.tolist())) < 3:
            continue
        for start, end in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge = tuple(sorted((int(start), int(end))))
            edges[edge] += 1
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
            next_index, next_index + len(nonfinite_indices), dtype=np.int64
        )

    return inverse[faces], int(inverse.max() + 1)


def _bbox(vertices: np.ndarray, vertex_finite_mask: np.ndarray) -> MeshBoundingBox | None:
    if vertices.ndim != 2 or vertices.shape[1] != 3 or not vertex_finite_mask.any():
        return None
    finite_vertices = vertices[vertex_finite_mask]
    return MeshBoundingBox(
        min_xyz=tuple(float(value) for value in finite_vertices.min(axis=0)),
        max_xyz=tuple(float(value) for value in finite_vertices.max(axis=0)),
    )


def _readiness(
    *,
    raw_boundary_edges: int,
    raw_nonmanifold_edges: int,
    welded_boundary_edges: int,
    welded_nonmanifold_edges: int,
    degenerate_faces: int,
    nonfinite_vertices: int,
    nonfinite_faces: int,
) -> MeshReadiness:
    reasons: list[str] = []
    if nonfinite_vertices:
        reasons.append("mesh contains non-finite vertices")
    if nonfinite_faces:
        reasons.append("mesh contains non-finite face indices")
    if degenerate_faces:
        reasons.append("mesh contains degenerate faces")
    if raw_boundary_edges or welded_boundary_edges:
        reasons.append("mesh has boundary edges and is not a closed volume")
    if raw_nonmanifold_edges or welded_nonmanifold_edges:
        reasons.append("mesh has non-manifold edges")

    if nonfinite_vertices or nonfinite_faces:
        return MeshReadiness(level="invalid", reasons=reasons)

    if not reasons:
        reasons.append("current generator contract is an STL surface, not a CFD-ready volume")
    return MeshReadiness(level="stl_surface", reasons=reasons)
