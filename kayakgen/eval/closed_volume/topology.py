"""Topology and per-array diagnostics for closed-volume bodies.

This module owns the numeric routines that walk a triangle mesh once and
report counts the rest of the package consumes: vertex/face finiteness,
degenerate-face detection, raw and welded edge accounting, the assembled
``parts -> arrays`` flatten, and the signed-volume sum used by orientation
and readiness checks.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from pydantic import BaseModel, ConfigDict

from kayakgen.eval.closed_volume.schemas import (
    ClosedSurfacePart,
    ClosedVolumeTolerances,
    ClosedVolumeTriangleReference,
)


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
    valid_face_indices: np.ndarray


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
    valid_face_indices = np.flatnonzero(valid_faces_mask)

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
        valid_face_indices=valid_face_indices,
    )


def _assemble_parts(parts: tuple[ClosedSurfacePart, ...]) -> tuple[np.ndarray, np.ndarray]:
    vertices, faces, _ = _assemble_parts_with_refs(parts)
    return vertices, faces


def _assemble_parts_with_refs(
    parts: tuple[ClosedSurfacePart, ...],
) -> tuple[np.ndarray, np.ndarray, list[ClosedVolumeTriangleReference]]:
    vertices_by_part: list[np.ndarray] = []
    faces_by_part: list[np.ndarray] = []
    face_refs: list[ClosedVolumeTriangleReference] = []
    offset = 0
    for part in parts:
        vertices = np.asarray(part.vertices, dtype=float)
        faces = np.asarray(part.faces, dtype=np.int64)
        vertices_by_part.append(vertices)
        faces_by_part.append(faces + offset)
        for part_face_index in range(len(faces)):
            face_refs.append(
                ClosedVolumeTriangleReference(
                    body_face_index=len(face_refs),
                    part_name=part.name,
                    part_face_index=part_face_index,
                )
            )
        offset += len(vertices)
    if not vertices_by_part:
        return (
            np.empty((0, 3), dtype=float),
            np.empty((0, 3), dtype=np.int64),
            [],
        )
    return np.vstack(vertices_by_part), np.vstack(faces_by_part), face_refs


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
