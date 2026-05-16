"""Generated and explicit body builders for closed-volume diagnostics.

This module owns the constructors that produce :class:`ClosedVolumeBody`
instances: the explicit-mesh wrapper used by the synthetic test fixtures
and the RFC 0022 generated hull-plus-deck builder that lofts cross-section
rings from a parametric ``Hull`` and closes the bow and stern. The
endpoint-closure and ring-walking helpers live here alongside the array
shape utilities that turn raw input into the schema's tuple types.
"""

from __future__ import annotations

import numpy as np

from kayakgen.eval.closed_volume.schemas import (
    DEFAULT_GENERATED_CLOSED_BODY_SECTION_POINTS,
    DEFAULT_GENERATED_CLOSED_BODY_STATIONS,
    GENERATED_CLOSED_BODY_PART_NAME,
    GENERATED_CLOSED_BODY_TYPE,
    ClosedSurfacePart,
    ClosedVolumeBody,
    ClosedVolumePolicy,
    ClosedVolumeTolerances,
    ClosedVolumeWaterlineMetadata,
    generated_hull_plus_deck_policy,
)
from kayakgen.eval.closed_volume.topology import _signed_volume


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


def generated_hull_plus_deck_body(
    hull: object,
    *,
    body_id: str | None = None,
    stations: int = DEFAULT_GENERATED_CLOSED_BODY_STATIONS,
    section_points: int = DEFAULT_GENERATED_CLOSED_BODY_SECTION_POINTS,
    policy: ClosedVolumePolicy | None = None,
) -> ClosedVolumeBody:
    """Build the RFC 0022 closed evaluation body from parametric ``Hull`` data."""

    from kayakgen.model.hull import Hull

    source_hull = Hull.model_validate(hull)
    profile_policy = policy or generated_hull_plus_deck_policy()
    if profile_policy.body_type != GENERATED_CLOSED_BODY_TYPE:
        raise ValueError("generated body policy must use the generated body type")

    vertices, faces = _generated_hull_plus_deck_mesh(
        source_hull,
        stations=stations,
        section_points=section_points,
        tolerances=profile_policy.tolerances,
    )
    source_hash = source_hull.hash()
    return ClosedVolumeBody(
        body_id=body_id or f"generated-closed-body-{source_hash[:12]}",
        body_type=GENERATED_CLOSED_BODY_TYPE,
        source_hull_hash=source_hash,
        waterline_metadata=ClosedVolumeWaterlineMetadata(
            waterline_z_m=0.0,
            beam_wl_m=(
                source_hull.beam_wl_m
                if source_hull.beam_wl_m is not None
                else source_hull.beam_oa_m
            ),
        ),
        policy=profile_policy,
        parts=(
            ClosedSurfacePart(
                name=GENERATED_CLOSED_BODY_PART_NAME,
                vertices=_vertices_tuple(vertices),
                faces=_faces_tuple(faces),
            ),
        ),
    )


def generated_hull_plus_deck_closed_body(
    hull: object,
    *,
    body_id: str | None = None,
    stations: int = DEFAULT_GENERATED_CLOSED_BODY_STATIONS,
    section_points: int = DEFAULT_GENERATED_CLOSED_BODY_SECTION_POINTS,
    policy: ClosedVolumePolicy | None = None,
) -> ClosedVolumeBody:
    """Compatibility alias for the RFC 0022 builder name."""

    return generated_hull_plus_deck_body(
        hull,
        body_id=body_id,
        stations=stations,
        section_points=section_points,
        policy=policy,
    )


def _generated_hull_plus_deck_mesh(
    hull: object,
    *,
    stations: int,
    section_points: int,
    tolerances: ClosedVolumeTolerances,
) -> tuple[np.ndarray, np.ndarray]:
    if stations < 2:
        raise ValueError("generated closed body requires at least two stations")
    if section_points < 4:
        raise ValueError("generated closed body requires at least four section points")

    geometry = hull.to_geometry()
    if hasattr(geometry, "num_points"):
        geometry.num_points = section_points
    length_m = float(hull.length_m)
    x_positions = np.linspace(-length_m / 2.0, length_m / 2.0, stations)
    bow_plumb = hull.bow_rake == 0.0
    stern_plumb = hull.stern_rake == 0.0
    if stations < 3 and (not bow_plumb or not stern_plumb):
        raise ValueError("raked endpoint closure requires at least three stations")

    ring_start = 0 if bow_plumb else 1
    ring_stop = stations if stern_plumb else stations - 1
    ring_xs = x_positions[ring_start:ring_stop]
    rings = [
        _generated_cross_section_ring(geometry, float(x), tolerances)
        for x in ring_xs
    ]
    ring_size = len(rings[0])
    if any(len(ring) != ring_size for ring in rings):
        raise ValueError("generated closed body rings must have a stable point count")

    vertices: list[list[float]] = []
    for x, ring in zip(ring_xs, rings, strict=True):
        vertices.extend([[float(x), float(y), float(z)] for y, z in ring])

    faces: list[list[int]] = []
    for station_index in range(len(rings) - 1):
        current = station_index * ring_size
        next_station = (station_index + 1) * ring_size
        for ring_index in range(ring_size):
            next_ring_index = (ring_index + 1) % ring_size
            c1 = current + ring_index
            c2 = current + next_ring_index
            n1 = next_station + ring_index
            n2 = next_station + next_ring_index
            faces.extend([[c1, c2, n1], [c2, n2, n1]])

    vertex_array, faces = _add_generated_endpoint_closures(
        np.asarray(vertices, dtype=float),
        faces,
        ring_size,
        bow_x=float(x_positions[0]),
        stern_x=float(x_positions[-1]),
        bow_plumb=bow_plumb,
        stern_plumb=stern_plumb,
    )
    face_array = np.asarray(faces, dtype=np.int64)
    if _signed_volume(vertex_array, face_array) < 0.0:
        face_array = face_array[:, [0, 2, 1]]
    return vertex_array, face_array


def _generated_cross_section_ring(
    geometry: object,
    x: float,
    tolerances: ClosedVolumeTolerances,
) -> np.ndarray:
    hull_section = _generated_section_points(geometry, x, "hull")
    deck_section = _generated_section_points(geometry, x, "deck")
    if hull_section.ndim != 2 or hull_section.shape[1] != 2:
        raise ValueError("generated hull section must be an Nx2 array")
    if deck_section.ndim != 2 or deck_section.shape[1] != 2:
        raise ValueError("generated deck section must be an Nx2 array")

    tolerance = max(
        tolerances.vertex_weld_tolerance_m,
        tolerances.join_match_tolerance_m,
    )
    points: list[np.ndarray] = []
    for point in hull_section:
        _append_ring_point(points, point, tolerance)

    # Deck sections are stored port->centerline->starboard. The closed body
    # ring walks counterclockwise in the y/z plane: hull port->starboard,
    # optional starboard topside strip, deck starboard->port, optional port
    # topside strip back to the first hull point.
    _append_ring_point(points, deck_section[-1], tolerance)
    for point in deck_section[-2::-1]:
        _append_ring_point(points, point, tolerance)

    if len(points) < 4:
        raise ValueError("generated closed body ring has too few distinct points")
    if np.linalg.norm(points[-1] - points[0]) <= tolerance:
        points.pop()

    ring = np.asarray(points, dtype=float)
    if _ring_area_yz(ring) < 0.0:
        ring = ring[::-1].copy()
    if abs(_ring_area_yz(ring)) <= tolerances.degenerate_area_tolerance_m2:
        raise ValueError("generated closed body ring area is degenerate")
    return ring


def _generated_section_points(
    geometry: object,
    x: float,
    part: str,
) -> np.ndarray:
    """Return the closed-body section ring at ``x``.

    Per Phase 2 step 4 of ``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md``
    the closed-body builder consumes the public
    :meth:`HullGeometry.section_for_closed_body` entry point. Geometries
    that pre-date the method fall back to their open :meth:`section`
    surface; the result will not honor exact plumb-stem endpoint
    closure but the generated-body diagnostic chain catches that
    downstream.
    """

    closed_section = getattr(geometry, "section_for_closed_body", None)
    if callable(closed_section):
        return np.asarray(closed_section(x, part), dtype=float)
    return np.asarray(geometry.section(x, part), dtype=float)


def _add_generated_endpoint_closures(
    vertices: np.ndarray,
    faces: list[list[int]],
    ring_size: int,
    *,
    bow_x: float,
    stern_x: float,
    bow_plumb: bool,
    stern_plumb: bool,
) -> tuple[np.ndarray, list[list[int]]]:
    bow_base = 0
    closure_vertices = [vertices]

    if bow_plumb:
        bow_center = len(vertices)
        closure_vertices.append(_ring_cap_center(bow_x, vertices[bow_base:ring_size, 1:]))
        for ring_index in range(ring_size):
            next_ring_index = (ring_index + 1) % ring_size
            faces.append([bow_center, bow_base + next_ring_index, bow_base + ring_index])
    else:
        bow_apex = len(vertices)
        closure_vertices.append(np.array([[bow_x, 0.0, 0.0]], dtype=float))
        for ring_index in range(ring_size):
            next_ring_index = (ring_index + 1) % ring_size
            faces.append([bow_apex, bow_base + next_ring_index, bow_base + ring_index])

    vertices_with_bow = np.vstack(closure_vertices)
    stern_base = len(vertices) - ring_size
    stern_index_offset = len(vertices_with_bow)
    closure_vertices = [vertices_with_bow]

    if stern_plumb:
        stern_center = stern_index_offset
        closure_vertices.append(
            _ring_cap_center(stern_x, vertices[stern_base : stern_base + ring_size, 1:])
        )
        for ring_index in range(ring_size):
            next_ring_index = (ring_index + 1) % ring_size
            faces.append([stern_center, stern_base + ring_index, stern_base + next_ring_index])
    else:
        stern_apex = stern_index_offset
        closure_vertices.append(np.array([[stern_x, 0.0, 0.0]], dtype=float))
        for ring_index in range(ring_size):
            next_ring_index = (ring_index + 1) % ring_size
            faces.append([stern_apex, stern_base + ring_index, stern_base + next_ring_index])

    return np.vstack(closure_vertices), faces


def _append_ring_point(
    points: list[np.ndarray],
    point: np.ndarray,
    tolerance: float,
) -> None:
    point = np.asarray(point, dtype=float)
    if points and np.linalg.norm(point - points[-1]) <= tolerance:
        return
    points.append(point)


def _ring_area_yz(ring: np.ndarray) -> float:
    y = ring[:, 0]
    z = ring[:, 1]
    return float(0.5 * np.sum(y * np.roll(z, -1) - np.roll(y, -1) * z))


def _ring_cap_center(x: float, ring: np.ndarray) -> list[float]:
    center = ring.mean(axis=0)
    return [float(x), float(center[0]), float(center[1])]


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
