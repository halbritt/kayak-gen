"""RFC 0028 generated closed-body plumb-stem endpoint semantics."""

from __future__ import annotations

import numpy as np

from kayakgen.eval.closed_volume import diagnose_closed_volume_body
from kayakgen.eval.generated_closed_body import generated_hull_plus_deck_closed_body
from kayakgen.eval.mesh_diagnostics import diagnose_mesh
from kayakgen.model.hull import Hull


def _arrays(body) -> tuple[np.ndarray, np.ndarray]:
    part = body.parts[0]
    return np.asarray(part.vertices, dtype=float), np.asarray(part.faces, dtype=np.int64)


def _face_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    triangles = vertices[faces]
    return np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])


def test_exact_plumb_endpoints_have_nonzero_terminal_sections() -> None:
    hull = Hull(bow_rake=0.0, stern_rake=0.0)
    vertices, _faces = _arrays(generated_hull_plus_deck_closed_body(hull, stations=6))

    bow = vertices[np.isclose(vertices[:, 0], -hull.length_m / 2)]
    stern = vertices[np.isclose(vertices[:, 0], hull.length_m / 2)]

    assert np.ptp(bow[:, 1]) > 0.5
    assert np.ptp(bow[:, 2]) > 0.2
    assert np.ptp(stern[:, 1]) > 0.5
    assert np.ptp(stern[:, 2]) > 0.2


def test_generated_plumb_body_diagnostics_prove_closed_positive_volume() -> None:
    body = generated_hull_plus_deck_closed_body(
        Hull(bow_rake=0.0, stern_rake=0.0),
        stations=4,
    )

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.readiness.level == "closed_volume"
    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0
    assert diagnostics.degenerate_faces == 0
    assert diagnostics.signed_volume_m3 > 0.0
    assert diagnostics.self_intersection_status == "passed"
    assert diagnostics.cfd_ready is False


def test_plumb_cap_normals_are_mirrored_under_x_convention() -> None:
    hull = Hull(bow_rake=0.0, stern_rake=0.0)
    vertices, faces = _arrays(generated_hull_plus_deck_closed_body(hull, stations=4))
    normals = _face_normals(vertices, faces)
    face_x = vertices[faces][:, :, 0]

    bow_cap = np.isclose(face_x, -hull.length_m / 2).all(axis=1)
    stern_cap = np.isclose(face_x, hull.length_m / 2).all(axis=1)

    assert bow_cap.sum() > 0
    assert stern_cap.sum() > 0
    assert normals[bow_cap, 0].max() < 0.0
    assert normals[stern_cap, 0].min() > 0.0


def test_default_raked_generated_body_uses_apex_closure_without_degenerate_faces() -> None:
    diagnostics = diagnose_closed_volume_body(
        generated_hull_plus_deck_closed_body(Hull(), stations=4)
    )

    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.degenerate_faces == 0
    assert diagnostics.signed_volume_m3 > 0.0
    assert diagnostics.self_intersection_status == "passed"


def test_generated_body_closes_when_waterline_beam_differs_from_overall_beam() -> None:
    diagnostics = diagnose_closed_volume_body(
        generated_hull_plus_deck_closed_body(
            Hull(bow_rake=0.0, stern_rake=0.0, beam_oa_m=0.60, beam_wl_m=0.50),
            stations=4,
        )
    )

    assert diagnostics.readiness.level == "closed_volume"
    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0
    assert diagnostics.degenerate_faces == 0
    assert diagnostics.self_intersection_status == "passed"


def test_open_plumb_stl_surface_remains_inspection_mesh_not_closed_body() -> None:
    diagnostics = diagnose_mesh(Hull(bow_rake=0.0), stations=24)

    assert diagnostics.readiness.level == "stl_surface"
    assert diagnostics.raw_boundary_edges > 0
    assert diagnostics.welded_boundary_edges > 0
    assert "mesh has boundary edges and is not a closed volume" in diagnostics.warnings
