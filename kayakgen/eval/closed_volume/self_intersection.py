"""RFC 0021 self-intersection diagnostics for closed-volume bodies.

This module implements the conservative non-adjacent triangle-pair scan and
all geometry kernels (triangle/segment intersection, coplanar handling,
point-in-triangle, point/segment distance) the scan depends on. The
:func:`_diagnose_self_intersections` entry point returns a status record
that ``diagnose_closed_volume_body`` folds into the body-level report.
"""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, Field

from kayakgen.eval.closed_volume.schemas import (
    MAX_SELF_INTERSECTION_EXAMPLE_PAIRS,
    SELF_INTERSECTION_ALGORITHM,
    SELF_INTERSECTION_NOT_CHECKED_ALGORITHM,
    ClosedVolumePolicy,
    ClosedVolumeSelfIntersectionPair,
    ClosedVolumeSelfIntersectionStatus,
    ClosedVolumeTriangleReference,
    SelfIntersectionPairClassification,
    _policy_requires_self_intersection,
)
from kayakgen.eval.closed_volume.topology import _face_areas, _welded_faces


class _SelfIntersectionDiagnostics(BaseModel):
    status: ClosedVolumeSelfIntersectionStatus
    algorithm: str
    tolerance_m: float
    pair_count: int
    example_pairs: list[ClosedVolumeSelfIntersectionPair] = Field(default_factory=list)


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
