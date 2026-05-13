"""Closed-volume contract models and diagnostics for explicit triangle meshes.

This module is intentionally limited to caller-supplied synthetic meshes. It
does not build closed bodies from generated ``Hull`` surfaces and it never
promotes a body to ``cfd_ready``.
"""

from __future__ import annotations

from collections import Counter
from typing import Literal, Self

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

ClosedVolumeReadinessLevel = Literal["invalid", "closed_volume"]
ClosedVolumeBodyType = Literal["explicit_synthetic_triangle_mesh"]
ClosedVolumeSelfIntersectionStatus = Literal[
    "not_checked", "passed", "failed", "inconclusive"
]
ClosedVolumeSelfIntersectionPolicy = Literal[
    "not_checked_rfc0016_compatibility",
    "required_rfc0021_conservative",
]
SelfIntersectionPairClassification = Literal["intersection", "near_contact"]

DEFAULT_VERTEX_WELD_TOLERANCE_M = 1e-6
DEFAULT_DEGENERATE_AREA_TOLERANCE_M2 = 1e-12
DEFAULT_SIGNED_VOLUME_TOLERANCE_M3 = 1e-12
DEFAULT_SELF_INTERSECTION_TOLERANCE_M = 1e-9
RFC0016_SYNTHETIC_PROFILE_NAME = "explicit_synthetic_closed_volume_v1"
RFC0021_SELF_INTERSECTION_PROFILE_NAME = (
    "explicit_synthetic_closed_volume_self_intersection_v1"
)
SELF_INTERSECTION_NOT_CHECKED_ALGORITHM = "not_checked_rfc0016_compatibility"
SELF_INTERSECTION_ALGORITHM = "assembled_welded_aabb_triangle_pairs_v1"
MAX_SELF_INTERSECTION_EXAMPLE_PAIRS = 8


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
    self_intersection_tolerance_m: float = Field(
        default=DEFAULT_SELF_INTERSECTION_TOLERANCE_M, ge=0
    )


class ClosedVolumePolicy(BaseModel):
    """Policy identity for the safe synthetic closed-volume slice."""

    model_config = ConfigDict(extra="forbid")

    profile_name: str = RFC0016_SYNTHETIC_PROFILE_NAME
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
    self_intersection_policy: ClosedVolumeSelfIntersectionPolicy = (
        "not_checked_rfc0016_compatibility"
    )
    tolerances: ClosedVolumeTolerances = Field(default_factory=ClosedVolumeTolerances)

    @model_validator(mode="after")
    def _align_rfc0021_profile_policy(self) -> Self:
        if self.profile_name == RFC0021_SELF_INTERSECTION_PROFILE_NAME:
            self.self_intersection_policy = "required_rfc0021_conservative"
        return self


def explicit_synthetic_self_intersection_policy() -> ClosedVolumePolicy:
    """Return the RFC 0021 explicit synthetic profile requiring the check."""

    return ClosedVolumePolicy(
        profile_name=RFC0021_SELF_INTERSECTION_PROFILE_NAME,
        self_intersection_policy="required_rfc0021_conservative",
    )


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


class ClosedVolumeTriangleReference(BaseModel):
    """Stable reference to an assembled-body triangle."""

    model_config = ConfigDict(extra="forbid")

    body_face_index: int = Field(ge=0)
    part_name: str
    part_face_index: int = Field(ge=0)


class ClosedVolumeSelfIntersectionPair(BaseModel):
    """Bounded example of a blocking non-adjacent triangle pair."""

    model_config = ConfigDict(extra="forbid")

    first: ClosedVolumeTriangleReference
    second: ClosedVolumeTriangleReference
    classification: SelfIntersectionPairClassification


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
    self_intersection_status: ClosedVolumeSelfIntersectionStatus
    self_intersection_algorithm: str
    self_intersection_tolerance_m: float = Field(ge=0)
    self_intersection_pair_count: int = Field(ge=0)
    self_intersection_example_pairs: list[ClosedVolumeSelfIntersectionPair] = Field(
        default_factory=list
    )
    warnings: list[str] = Field(default_factory=list)
    cfd_ready: Literal[False] = False

    @model_validator(mode="after")
    def _rfc0021_closed_volume_requires_passed_self_intersection(self) -> Self:
        if (
            self.readiness.level == "closed_volume"
            and _policy_requires_self_intersection(self.policy)
            and self.self_intersection_status != "passed"
        ):
            raise ValueError(
                "RFC 0021 closed-volume readiness requires passed "
                "self-intersection diagnostics"
            )
        return self


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
    vertices, faces, face_refs = _assemble_parts_with_refs(body.parts)
    body_report = _diagnose_arrays(vertices, faces, body.policy.tolerances)
    signed_volume = _signed_volume(vertices, body_report.valid_faces)
    self_intersections = _diagnose_self_intersections(
        vertices,
        body_report.valid_faces,
        [face_refs[int(index)] for index in body_report.valid_face_indices],
        body.policy,
    )

    reasons = _readiness_reasons(
        body_report,
        signed_volume,
        body.policy,
        self_intersections.status,
    )
    readiness = ClosedVolumeReadiness(
        level="invalid" if reasons else "closed_volume",
        reasons=reasons,
    )
    warnings = list(reasons)
    if self_intersections.status == "not_checked":
        warnings.append(
            "self-intersection diagnostic not checked under RFC 0016 compatibility profile"
        )
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
        self_intersection_status=self_intersections.status,
        self_intersection_algorithm=self_intersections.algorithm,
        self_intersection_tolerance_m=self_intersections.tolerance_m,
        self_intersection_pair_count=self_intersections.pair_count,
        self_intersection_example_pairs=self_intersections.example_pairs,
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
    valid_face_indices: np.ndarray


class _SelfIntersectionDiagnostics(BaseModel):
    status: ClosedVolumeSelfIntersectionStatus
    algorithm: str
    tolerance_m: float
    pair_count: int
    example_pairs: list[ClosedVolumeSelfIntersectionPair] = Field(default_factory=list)


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


def _diagnose_self_intersections(
    vertices: np.ndarray,
    faces: np.ndarray,
    face_refs: list[ClosedVolumeTriangleReference],
    policy: ClosedVolumePolicy,
) -> _SelfIntersectionDiagnostics:
    tolerance_m = policy.tolerances.self_intersection_tolerance_m
    if not _policy_requires_self_intersection(policy):
        return _SelfIntersectionDiagnostics(
            status="not_checked",
            algorithm=SELF_INTERSECTION_NOT_CHECKED_ALGORITHM,
            tolerance_m=tolerance_m,
            pair_count=0,
            example_pairs=[],
        )

    pairs = _find_self_intersection_pairs(vertices, faces, face_refs, policy)
    if not pairs:
        status: ClosedVolumeSelfIntersectionStatus = "passed"
    elif any(pair.classification == "intersection" for pair in pairs):
        status = "failed"
    else:
        status = "inconclusive"

    return _SelfIntersectionDiagnostics(
        status=status,
        algorithm=SELF_INTERSECTION_ALGORITHM,
        tolerance_m=tolerance_m,
        pair_count=len(pairs),
        example_pairs=pairs[:MAX_SELF_INTERSECTION_EXAMPLE_PAIRS],
    )


def _find_self_intersection_pairs(
    vertices: np.ndarray,
    faces: np.ndarray,
    face_refs: list[ClosedVolumeTriangleReference],
    policy: ClosedVolumePolicy,
) -> list[ClosedVolumeSelfIntersectionPair]:
    if len(faces) < 2:
        return []

    tolerances = policy.tolerances
    areas = _face_areas(vertices, faces)
    nondegenerate = areas > tolerances.degenerate_area_tolerance_m2
    if not nondegenerate.any():
        return []

    triangles = vertices[faces]
    expanded_mins = triangles.min(axis=1) - tolerances.self_intersection_tolerance_m
    expanded_maxs = triangles.max(axis=1) + tolerances.self_intersection_tolerance_m
    welded_faces, _ = _welded_faces(
        vertices,
        faces,
        tolerances.vertex_weld_tolerance_m,
    )
    vertex_fan_components = _vertex_fan_components(welded_faces)

    order = sorted(
        np.flatnonzero(nondegenerate).tolist(),
        key=lambda index: (
            float(expanded_mins[index, 0]),
            float(expanded_mins[index, 1]),
            float(expanded_mins[index, 2]),
            int(index),
        ),
    )
    pairs: list[ClosedVolumeSelfIntersectionPair] = []
    for offset, first_index in enumerate(order):
        first_max = expanded_maxs[first_index]
        for second_index in order[offset + 1 :]:
            if expanded_mins[second_index, 0] > first_max[0]:
                break
            if not _aabb_overlaps(
                expanded_mins[first_index],
                expanded_maxs[first_index],
                expanded_mins[second_index],
                expanded_maxs[second_index],
            ):
                continue
            if _faces_are_policy_neighbors(
                welded_faces,
                vertex_fan_components,
                first_index,
                second_index,
            ):
                continue

            first_triangle = triangles[first_index]
            second_triangle = triangles[second_index]
            classification = _blocking_triangle_pair_classification(
                first_triangle,
                second_triangle,
                tolerances.self_intersection_tolerance_m,
            )
            if classification is None:
                continue

            first_ref = face_refs[first_index]
            second_ref = face_refs[second_index]
            if second_ref.body_face_index < first_ref.body_face_index:
                first_ref, second_ref = second_ref, first_ref
            pairs.append(
                ClosedVolumeSelfIntersectionPair(
                    first=first_ref,
                    second=second_ref,
                    classification=classification,
                )
            )

    return sorted(
        pairs,
        key=lambda pair: (
            pair.first.body_face_index,
            pair.second.body_face_index,
            pair.classification,
        ),
    )


def _aabb_overlaps(
    first_min: np.ndarray,
    first_max: np.ndarray,
    second_min: np.ndarray,
    second_max: np.ndarray,
) -> bool:
    return bool(np.all(first_min <= second_max) and np.all(second_min <= first_max))


def _faces_are_policy_neighbors(
    welded_faces: np.ndarray,
    vertex_fan_components: dict[tuple[int, int], int],
    first_index: int,
    second_index: int,
) -> bool:
    first_vertices = {int(index) for index in welded_faces[first_index]}
    second_vertices = {int(index) for index in welded_faces[second_index]}
    shared_vertices = first_vertices & second_vertices
    if len(shared_vertices) >= 2:
        return True
    if len(shared_vertices) != 1:
        return False

    vertex = next(iter(shared_vertices))
    first_component = vertex_fan_components.get((vertex, first_index))
    second_component = vertex_fan_components.get((vertex, second_index))
    return first_component is not None and first_component == second_component


def _vertex_fan_components(welded_faces: np.ndarray) -> dict[tuple[int, int], int]:
    incident_faces: dict[int, list[int]] = {}
    for face_index, face in enumerate(welded_faces):
        for vertex in {int(index) for index in face}:
            incident_faces.setdefault(vertex, []).append(face_index)

    components: dict[tuple[int, int], int] = {}
    next_component = 0
    for vertex, face_indices in incident_faces.items():
        neighbors = {face_index: set[int]() for face_index in face_indices}
        for offset, first_index in enumerate(face_indices):
            first = {int(index) for index in welded_faces[first_index]}
            for second_index in face_indices[offset + 1 :]:
                second = {int(index) for index in welded_faces[second_index]}
                if len(first & second) >= 2:
                    neighbors[first_index].add(second_index)
                    neighbors[second_index].add(first_index)

        remaining = set(face_indices)
        while remaining:
            root = min(remaining)
            stack = [root]
            remaining.remove(root)
            while stack:
                face_index = stack.pop()
                components[(vertex, face_index)] = next_component
                for neighbor in sorted(neighbors[face_index]):
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        stack.append(neighbor)
            next_component += 1
    return components


def _blocking_triangle_pair_classification(
    first: np.ndarray,
    second: np.ndarray,
    tolerance_m: float,
) -> SelfIntersectionPairClassification | None:
    exact_eps = 1e-12
    if _triangles_intersect_or_touch(first, second, exact_eps):
        return "intersection"
    if tolerance_m > 0 and _triangle_distance(first, second) <= tolerance_m:
        return "near_contact"
    return None


def _triangles_intersect_or_touch(
    first: np.ndarray,
    second: np.ndarray,
    eps: float,
) -> bool:
    if _triangles_are_coplanar(first, second, eps):
        return _coplanar_triangles_intersect_or_touch(first, second, eps)

    for start, end in _triangle_edges(first):
        if _segment_intersects_triangle(start, end, second, eps):
            return True
    for start, end in _triangle_edges(second):
        if _segment_intersects_triangle(start, end, first, eps):
            return True
    return False


def _triangle_edges(triangle: np.ndarray) -> tuple[tuple[np.ndarray, np.ndarray], ...]:
    return (
        (triangle[0], triangle[1]),
        (triangle[1], triangle[2]),
        (triangle[2], triangle[0]),
    )


def _triangles_are_coplanar(first: np.ndarray, second: np.ndarray, eps: float) -> bool:
    normal, normal_length = _triangle_normal(first)
    other_normal, other_length = _triangle_normal(second)
    if normal_length <= eps or other_length <= eps:
        return False
    unit_normal = normal / normal_length
    other_unit_normal = other_normal / other_length
    if np.linalg.norm(np.cross(unit_normal, other_unit_normal)) > 1e-10:
        return False
    distances = np.abs((second - first[0]) @ unit_normal)
    return bool(distances.max() <= eps)


def _triangle_normal(triangle: np.ndarray) -> tuple[np.ndarray, float]:
    normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
    return normal, float(np.linalg.norm(normal))


def _segment_intersects_triangle(
    start: np.ndarray,
    end: np.ndarray,
    triangle: np.ndarray,
    eps: float,
) -> bool:
    normal, normal_length = _triangle_normal(triangle)
    if normal_length <= eps:
        return False
    unit_normal = normal / normal_length
    start_distance = float((start - triangle[0]) @ unit_normal)
    end_distance = float((end - triangle[0]) @ unit_normal)

    if abs(start_distance) <= eps and abs(end_distance) <= eps:
        return _coplanar_segment_intersects_triangle(start, end, triangle, unit_normal, eps)
    if start_distance > eps and end_distance > eps:
        return False
    if start_distance < -eps and end_distance < -eps:
        return False

    denominator = start_distance - end_distance
    if abs(denominator) <= eps:
        return False
    t = start_distance / denominator
    if t < -eps or t > 1.0 + eps:
        return False
    point = start + t * (end - start)
    return _point_in_triangle_3d(point, triangle, eps)


def _point_in_triangle_3d(point: np.ndarray, triangle: np.ndarray, eps: float) -> bool:
    a, b, c = triangle
    v0 = c - a
    v1 = b - a
    v2 = point - a
    dot00 = float(v0 @ v0)
    dot01 = float(v0 @ v1)
    dot02 = float(v0 @ v2)
    dot11 = float(v1 @ v1)
    dot12 = float(v1 @ v2)
    denominator = dot00 * dot11 - dot01 * dot01
    if abs(denominator) <= eps:
        return False
    inv_denominator = 1.0 / denominator
    u = (dot11 * dot02 - dot01 * dot12) * inv_denominator
    v = (dot00 * dot12 - dot01 * dot02) * inv_denominator
    return bool(u >= -eps and v >= -eps and u + v <= 1.0 + eps)


def _coplanar_segment_intersects_triangle(
    start: np.ndarray,
    end: np.ndarray,
    triangle: np.ndarray,
    normal: np.ndarray,
    eps: float,
) -> bool:
    projected = _project_points_to_2d(np.vstack((start, end, triangle)), normal)
    segment_start = projected[0]
    segment_end = projected[1]
    triangle_2d = projected[2:]
    return _segment_intersects_triangle_2d(segment_start, segment_end, triangle_2d, eps)


def _coplanar_triangles_intersect_or_touch(
    first: np.ndarray,
    second: np.ndarray,
    eps: float,
) -> bool:
    normal, normal_length = _triangle_normal(first)
    if normal_length <= eps:
        return False
    projected = _project_points_to_2d(np.vstack((first, second)), normal / normal_length)
    first_2d = projected[:3]
    second_2d = projected[3:]
    for start, end in _triangle_edges(first_2d):
        if _segment_intersects_triangle_2d(start, end, second_2d, eps):
            return True
    for start, end in _triangle_edges(second_2d):
        if _segment_intersects_triangle_2d(start, end, first_2d, eps):
            return True
    return bool(
        _point_in_triangle_2d(first_2d[0], second_2d, eps)
        or _point_in_triangle_2d(second_2d[0], first_2d, eps)
    )


def _project_points_to_2d(points: np.ndarray, normal: np.ndarray) -> np.ndarray:
    drop_axis = int(np.argmax(np.abs(normal)))
    keep_axes = [axis for axis in range(3) if axis != drop_axis]
    return points[:, keep_axes]


def _segment_intersects_triangle_2d(
    start: np.ndarray,
    end: np.ndarray,
    triangle: np.ndarray,
    eps: float,
) -> bool:
    if _point_in_triangle_2d(start, triangle, eps) or _point_in_triangle_2d(
        end,
        triangle,
        eps,
    ):
        return True
    for edge_start, edge_end in _triangle_edges(triangle):
        if _segments_intersect_2d(start, end, edge_start, edge_end, eps):
            return True
    return False


def _point_in_triangle_2d(point: np.ndarray, triangle: np.ndarray, eps: float) -> bool:
    orientations = [
        _orient_2d(triangle[0], triangle[1], point),
        _orient_2d(triangle[1], triangle[2], point),
        _orient_2d(triangle[2], triangle[0], point),
    ]
    has_negative = any(value < -eps for value in orientations)
    has_positive = any(value > eps for value in orientations)
    return not (has_negative and has_positive)


def _segments_intersect_2d(
    first_start: np.ndarray,
    first_end: np.ndarray,
    second_start: np.ndarray,
    second_end: np.ndarray,
    eps: float,
) -> bool:
    o1 = _orient_2d(first_start, first_end, second_start)
    o2 = _orient_2d(first_start, first_end, second_end)
    o3 = _orient_2d(second_start, second_end, first_start)
    o4 = _orient_2d(second_start, second_end, first_end)
    if ((o1 > eps and o2 < -eps) or (o1 < -eps and o2 > eps)) and (
        (o3 > eps and o4 < -eps) or (o3 < -eps and o4 > eps)
    ):
        return True
    return bool(
        (abs(o1) <= eps and _point_on_segment_2d(second_start, first_start, first_end, eps))
        or (abs(o2) <= eps and _point_on_segment_2d(second_end, first_start, first_end, eps))
        or (abs(o3) <= eps and _point_on_segment_2d(first_start, second_start, second_end, eps))
        or (abs(o4) <= eps and _point_on_segment_2d(first_end, second_start, second_end, eps))
    )


def _orient_2d(first: np.ndarray, second: np.ndarray, point: np.ndarray) -> float:
    return float(
        (second[0] - first[0]) * (point[1] - first[1])
        - (second[1] - first[1]) * (point[0] - first[0])
    )


def _point_on_segment_2d(
    point: np.ndarray,
    start: np.ndarray,
    end: np.ndarray,
    eps: float,
) -> bool:
    return bool(
        min(start[0], end[0]) - eps <= point[0] <= max(start[0], end[0]) + eps
        and min(start[1], end[1]) - eps <= point[1] <= max(start[1], end[1]) + eps
    )


def _triangle_distance(first: np.ndarray, second: np.ndarray) -> float:
    distances = [
        _point_triangle_distance(point, second)
        for point in first
    ] + [
        _point_triangle_distance(point, first)
        for point in second
    ]
    for first_start, first_end in _triangle_edges(first):
        for second_start, second_end in _triangle_edges(second):
            distances.append(
                _segment_segment_distance(
                    first_start,
                    first_end,
                    second_start,
                    second_end,
                )
            )
    return min(distances)


def _point_triangle_distance(point: np.ndarray, triangle: np.ndarray) -> float:
    a, b, c = triangle
    ab = b - a
    ac = c - a
    ap = point - a
    d1 = float(ab @ ap)
    d2 = float(ac @ ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return float(np.linalg.norm(ap))

    bp = point - b
    d3 = float(ab @ bp)
    d4 = float(ac @ bp)
    if d3 >= 0.0 and d4 <= d3:
        return float(np.linalg.norm(bp))

    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        projection = a + v * ab
        return float(np.linalg.norm(point - projection))

    cp = point - c
    d5 = float(ab @ cp)
    d6 = float(ac @ cp)
    if d6 >= 0.0 and d5 <= d6:
        return float(np.linalg.norm(cp))

    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        projection = a + w * ac
        return float(np.linalg.norm(point - projection))

    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        projection = b + w * (c - b)
        return float(np.linalg.norm(point - projection))

    normal = np.cross(ab, ac)
    normal_length = float(np.linalg.norm(normal))
    if normal_length == 0.0:
        return min(
            float(np.linalg.norm(point - a)),
            float(np.linalg.norm(point - b)),
            float(np.linalg.norm(point - c)),
        )
    return abs(float((point - a) @ normal)) / normal_length


def _segment_segment_distance(
    first_start: np.ndarray,
    first_end: np.ndarray,
    second_start: np.ndarray,
    second_end: np.ndarray,
) -> float:
    first_direction = first_end - first_start
    second_direction = second_end - second_start
    between_starts = first_start - second_start
    a = float(first_direction @ first_direction)
    b = float(first_direction @ second_direction)
    c = float(second_direction @ second_direction)
    d = float(first_direction @ between_starts)
    e = float(second_direction @ between_starts)
    denominator = a * c - b * b
    small = 1e-15

    if denominator < small:
        s_numerator = 0.0
        s_denominator = 1.0
        t_numerator = e
        t_denominator = c
    else:
        s_numerator = b * e - c * d
        t_numerator = a * e - b * d
        s_denominator = denominator
        t_denominator = denominator
        if s_numerator < 0.0:
            s_numerator = 0.0
            t_numerator = e
            t_denominator = c
        elif s_numerator > s_denominator:
            s_numerator = s_denominator
            t_numerator = e + b
            t_denominator = c

    if t_numerator < 0.0:
        t_numerator = 0.0
        if -d < 0.0:
            s_numerator = 0.0
        elif -d > a:
            s_numerator = s_denominator
        else:
            s_numerator = -d
            s_denominator = a
    elif t_numerator > t_denominator:
        t_numerator = t_denominator
        if -d + b < 0.0:
            s_numerator = 0.0
        elif -d + b > a:
            s_numerator = s_denominator
        else:
            s_numerator = -d + b
            s_denominator = a

    sc = 0.0 if abs(s_numerator) < small else s_numerator / s_denominator
    tc = 0.0 if abs(t_numerator) < small else t_numerator / t_denominator
    delta = between_starts + sc * first_direction - tc * second_direction
    return float(np.linalg.norm(delta))


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
    policy: ClosedVolumePolicy,
    self_intersection_status: ClosedVolumeSelfIntersectionStatus,
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
    if signed_volume <= policy.tolerances.signed_volume_tolerance_m3:
        reasons.append("body signed volume is not positive with outward normals")
    if _policy_requires_self_intersection(policy) and self_intersection_status != "passed":
        reasons.append(
            f"body self-intersection diagnostic status is {self_intersection_status}"
        )
    return reasons


def _policy_requires_self_intersection(policy: ClosedVolumePolicy) -> bool:
    if policy.profile_name == RFC0021_SELF_INTERSECTION_PROFILE_NAME:
        return True
    return policy.self_intersection_policy == "required_rfc0021_conservative"
