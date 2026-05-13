"""Focused mesh diagnostics tests."""

from __future__ import annotations

import numpy as np
import pytest

from kayakgen.eval.mesh_diagnostics import diagnose_mesh
from kayakgen.model.hull import Hull


class _FakeGeometry:
    def __init__(self, vertices: np.ndarray, faces: np.ndarray) -> None:
        self.vertices = vertices
        self.faces = faces

    def mesh(self, part: str, stations: int | None = None) -> tuple[np.ndarray, np.ndarray]:
        return self.vertices, self.faces


class _FakeHull:
    def __init__(self, vertices: np.ndarray, faces: np.ndarray) -> None:
        self._geometry = _FakeGeometry(vertices, faces)

    def to_geometry(self) -> _FakeGeometry:
        return self._geometry


def test_diagnose_default_hull_reports_stl_surface_profile() -> None:
    diagnostics = diagnose_mesh(Hull(), stations=20)

    assert diagnostics.profile.part == "hull"
    assert diagnostics.profile.stations == 20
    assert diagnostics.profile.vertex_count == 20 * 79
    assert diagnostics.profile.face_count == 19 * 78 * 2
    assert diagnostics.profile.surface_area_m2 > 0.0
    assert diagnostics.profile.bbox is not None
    assert diagnostics.profile.bbox.min_xyz[0] == pytest.approx(-2.25)
    assert diagnostics.profile.bbox.max_xyz[0] == pytest.approx(2.25)

    assert diagnostics.raw_boundary_edges > 0
    assert diagnostics.welded_boundary_edges > 0
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0
    assert diagnostics.degenerate_faces == 0
    assert diagnostics.nonfinite_vertices == 0
    assert diagnostics.nonfinite_faces == 0
    assert diagnostics.readiness.level == "stl_surface"
    assert diagnostics.solver_profile is None
    assert "mesh has boundary edges and is not a closed volume" in diagnostics.warnings


def test_diagnose_deck_uses_requested_part() -> None:
    diagnostics = diagnose_mesh(Hull(), part="deck", stations=10)

    assert diagnostics.profile.part == "deck"
    assert diagnostics.profile.vertex_count == 10 * 79
    assert diagnostics.profile.face_count == 9 * 78 * 2
    assert diagnostics.profile.bbox is not None
    assert diagnostics.profile.bbox.max_xyz[2] > 0.0
    assert diagnostics.readiness.level == "stl_surface"


def test_tolerance_welded_edges_are_counted_separately_from_raw_edges() -> None:
    vertices = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
        ]
    )
    faces = np.array([[0, 1, 2], [3, 4, 5]])

    diagnostics = diagnose_mesh(_FakeHull(vertices, faces))

    assert diagnostics.raw_boundary_edges == 6
    assert diagnostics.welded_boundary_edges == 4
    assert diagnostics.profile.welded_vertex_count == 4
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0


def test_degenerate_and_nonfinite_counts_make_mesh_invalid() -> None:
    vertices = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [np.nan, 1.0, 0.0],
        ]
    )
    faces = np.array([[0, 1, 2], [0, 1, 3]])

    diagnostics = diagnose_mesh(_FakeHull(vertices, faces))

    assert diagnostics.degenerate_faces == 2
    assert diagnostics.nonfinite_vertices == 1
    assert diagnostics.nonfinite_faces == 0
    assert diagnostics.readiness.level == "invalid"


def test_nonfinite_face_indices_are_reported_without_crashing() -> None:
    vertices = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]
    )
    faces = np.array([[0.0, 1.0, 2.0], [0.0, np.nan, 2.0]])

    diagnostics = diagnose_mesh(_FakeHull(vertices, faces))

    assert diagnostics.nonfinite_vertices == 0
    assert diagnostics.nonfinite_faces == 1
    assert diagnostics.readiness.level == "invalid"


def test_weld_tolerance_must_be_positive() -> None:
    with pytest.raises(ValueError, match="weld_tolerance_m must be positive"):
        diagnose_mesh(Hull(), weld_tolerance_m=0.0)
