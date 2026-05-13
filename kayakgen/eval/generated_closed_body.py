"""Generated hull-plus-deck closed-body construction.

This builder is separate from the open hull/deck STL inspection path. It
constructs a single explicit triangle body from parametric station rings so the
closed-volume diagnostics, rather than rake settings, decide closure readiness.
"""

from __future__ import annotations

import numpy as np

from kayakgen.eval.closed_volume import (
    ClosedSurfacePart,
    ClosedVolumeBody,
    explicit_synthetic_self_intersection_policy,
)
from kayakgen.model.geometry import LoftedHullGeometry
from kayakgen.model.hull import Hull

GENERATED_CLOSED_BODY_PART_NAME = "generated-hull-plus-deck-closed-body"
DEFAULT_GENERATED_CLOSED_BODY_STATIONS = 32


def generated_hull_plus_deck_closed_body(
    hull: Hull,
    *,
    stations: int | None = None,
    body_id: str | None = None,
) -> ClosedVolumeBody:
    """Build a generated closed body from ``hull`` without using display STLs.

    Exact plumb endpoint sections are owned here: when a side-specific rake is
    exactly ``0.0``, the endpoint station uses the limiting full-size section
    instead of the open-inspection mesh's collapsed tip.
    """

    geom = hull.to_geometry()
    if not isinstance(geom, LoftedHullGeometry):
        raise ValueError("generated closed-body construction requires lofted geometry")

    n = stations if stations is not None else DEFAULT_GENERATED_CLOSED_BODY_STATIONS
    if n < 2:
        raise ValueError("stations must be at least 2")

    if n < 3 and (hull.bow_rake > 0.0 or hull.stern_rake > 0.0):
        raise ValueError("raked endpoint closure requires at least 3 stations")

    xs = np.linspace(-geom.L / 2, geom.L / 2, n)
    bow_plumb = hull.bow_rake == 0.0
    stern_plumb = hull.stern_rake == 0.0
    ring_start = 0 if bow_plumb else 1
    ring_stop = n if stern_plumb else n - 1
    ring_xs = xs[ring_start:ring_stop]
    rings = [_section_ring(geom, float(x)) for x in ring_xs]
    ring_size = len(rings[0])
    if any(len(ring) != ring_size for ring in rings):
        raise ValueError("all closed-body station rings must have the same vertex count")

    vertices = np.vstack(
        [
            np.column_stack((np.full(ring_size, x), ring[:, 0], ring[:, 1]))
            for x, ring in zip(ring_xs, rings, strict=True)
        ]
    )
    faces = _loft_faces(len(rings), ring_size)
    vertices, faces = _add_endpoint_closures(
        vertices,
        faces,
        ring_size,
        bow_x=float(xs[0]),
        stern_x=float(xs[-1]),
        bow_plumb=bow_plumb,
        stern_plumb=stern_plumb,
    )

    face_array = np.asarray(faces, dtype=np.int64)
    if _signed_volume(vertices, face_array) < 0.0:
        face_array = face_array[:, [0, 2, 1]]

    part = ClosedSurfacePart(
        name=GENERATED_CLOSED_BODY_PART_NAME,
        vertices=tuple(tuple(float(value) for value in row) for row in vertices),
        faces=tuple(tuple(int(index) for index in row) for row in face_array),
    )
    return ClosedVolumeBody(
        body_id=body_id or f"generated-hull-plus-deck-{hull.hash()[:12]}",
        policy=explicit_synthetic_self_intersection_policy(),
        parts=(part,),
    )


def _section_ring(geom: LoftedHullGeometry, x: float) -> np.ndarray:
    hull = geom._get_slice_points(x, "hull", closed_body_endpoint=True)
    deck = geom._get_slice_points(x, "deck", closed_body_endpoint=True)
    # Hull order is port waterline -> keel -> starboard waterline. Deck order
    # is port sheer -> deck centerline -> starboard sheer, so reverse it to
    # close around the outside and drop duplicate sheer endpoints.
    deck_return = deck[::-1]
    deck_start = 1 if np.allclose(deck_return[0], hull[-1], atol=1e-12) else 0
    deck_stop = -1 if np.allclose(deck_return[-1], hull[0], atol=1e-12) else None
    ring = np.vstack((hull, deck_return[deck_start:deck_stop]))
    if _signed_area_yz(ring) < 0.0:
        return ring[::-1]
    return ring


def _loft_faces(num_rings: int, ring_size: int) -> list[list[int]]:
    faces: list[list[int]] = []
    for ring_index in range(num_rings - 1):
        base = ring_index * ring_size
        next_base = (ring_index + 1) * ring_size
        for point_index in range(ring_size):
            point_next = (point_index + 1) % ring_size
            a = base + point_index
            b = base + point_next
            c = next_base + point_index
            d = next_base + point_next
            faces.extend([[a, b, c], [b, d, c]])
    return faces


def _add_endpoint_closures(
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
    stern_base = len(vertices) - ring_size
    closure_vertices = [vertices]

    if bow_plumb:
        bow_center_index = len(vertices)
        closure_vertices.append(_cap_center(vertices[bow_base : bow_base + ring_size]))
        for point_index in range(ring_size):
            point_next = (point_index + 1) % ring_size
            faces.append(
                [bow_center_index, bow_base + point_next, bow_base + point_index]
            )
    else:
        bow_apex_index = len(vertices)
        closure_vertices.append(np.array([[bow_x, 0.0, 0.0]], dtype=float))
        for point_index in range(ring_size):
            point_next = (point_index + 1) % ring_size
            faces.append([bow_apex_index, bow_base + point_next, bow_base + point_index])

    vertices_with_bow = np.vstack(closure_vertices)
    stern_base = len(vertices) - ring_size
    closure_vertices = [vertices_with_bow]
    stern_index_offset = len(vertices_with_bow)

    if stern_plumb:
        stern_center_index = stern_index_offset
        closure_vertices.append(
            _cap_center(vertices[stern_base : stern_base + ring_size])
        )
        for point_index in range(ring_size):
            point_next = (point_index + 1) % ring_size
            faces.append(
                [stern_center_index, stern_base + point_index, stern_base + point_next]
            )
    else:
        stern_apex_index = stern_index_offset
        closure_vertices.append(np.array([[stern_x, 0.0, 0.0]], dtype=float))
        for point_index in range(ring_size):
            point_next = (point_index + 1) % ring_size
            faces.append(
                [stern_apex_index, stern_base + point_index, stern_base + point_next]
            )
    return np.vstack(closure_vertices), faces


def _signed_area_yz(points: np.ndarray) -> float:
    y = points[:, 0]
    z = points[:, 1]
    return float(
        0.5 * np.sum(y * np.roll(z, -1) - np.roll(y, -1) * z)
    )


def _cap_center(ring_vertices: np.ndarray) -> np.ndarray:
    return np.array(
        [
            float(ring_vertices[0, 0]),
            float(ring_vertices[:, 1].mean()),
            float(ring_vertices[:, 2].mean()),
        ]
    )


def _signed_volume(vertices: np.ndarray, faces: np.ndarray) -> float:
    if len(faces) == 0:
        return 0.0
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)
