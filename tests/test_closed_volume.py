"""Closed-volume contract tests for explicit synthetic meshes."""

from __future__ import annotations

import pytest

from kayakgen.eval.closed_volume import (
    ClosedVolumeDiagnostics,
    diagnose_closed_volume_body,
    explicit_synthetic_body,
)


def _tetrahedron() -> tuple[list[list[float]], list[list[int]]]:
    vertices = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    faces = [
        [0, 2, 1],
        [0, 1, 3],
        [1, 2, 3],
        [2, 0, 3],
    ]
    return vertices, faces


def test_valid_closed_tetrahedron_has_serializable_contract_without_cfd_ready() -> None:
    vertices, faces = _tetrahedron()
    body = explicit_synthetic_body(vertices, faces, body_id="valid-tetrahedron")

    diagnostics = diagnose_closed_volume_body(body)
    loaded = ClosedVolumeDiagnostics.model_validate_json(diagnostics.model_dump_json())

    assert loaded.body_id == "valid-tetrahedron"
    assert loaded.body_type == "explicit_synthetic_triangle_mesh"
    assert loaded.profile_name == "explicit_synthetic_closed_volume_v1"
    assert loaded.policy.body_type == "explicit_synthetic_triangle_mesh"
    assert loaded.policy.waterline_semantics == "metadata_only"
    assert loaded.policy.cap_policy == "not_applicable_explicit_mesh"
    assert loaded.policy.deck_join_policy == "not_applicable_explicit_mesh"
    assert loaded.policy.cfd_readiness_policy == "never_claim_cfd_ready"
    assert loaded.policy.tolerances.vertex_weld_tolerance_m > 0.0

    assert loaded.readiness.level == "closed_volume"
    assert loaded.cfd_ready is False
    assert loaded.raw_boundary_edges == 0
    assert loaded.welded_boundary_edges == 0
    assert loaded.raw_nonmanifold_edges == 0
    assert loaded.welded_nonmanifold_edges == 0
    assert loaded.signed_volume_m3 == pytest.approx(1.0 / 6.0)
    assert "not cfd_ready" in " ".join(loaded.warnings)


def test_open_body_reports_body_level_boundary_edges() -> None:
    vertices, faces = _tetrahedron()
    body = explicit_synthetic_body(vertices, faces[:-1], body_id="open-tetrahedron")

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.readiness.level == "invalid"
    assert diagnostics.raw_boundary_edges == 3
    assert diagnostics.welded_boundary_edges == 3
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0
    assert "body has boundary edges and is not closed" in diagnostics.warnings
    assert diagnostics.part_diagnostics[0].raw_boundary_edges == 3


def test_nonmanifold_body_reports_body_level_nonmanifold_edges() -> None:
    vertices, faces = _tetrahedron()
    body = explicit_synthetic_body(
        vertices,
        faces + [[0, 1, 3]],
        body_id="nonmanifold-tetrahedron",
    )

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.readiness.level == "invalid"
    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.raw_nonmanifold_edges == 3
    assert diagnostics.welded_nonmanifold_edges == 3
    assert "body has non-manifold edges" in diagnostics.warnings
    assert diagnostics.part_diagnostics[0].raw_nonmanifold_edges == 3


def test_reversed_orientation_is_not_accepted_as_closed_volume() -> None:
    vertices, faces = _tetrahedron()
    reversed_faces = [list(reversed(face)) for face in faces]
    body = explicit_synthetic_body(vertices, reversed_faces, body_id="inside-out")

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.readiness.level == "invalid"
    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.signed_volume_m3 == pytest.approx(-1.0 / 6.0)
    assert "body signed volume is not positive with outward normals" in diagnostics.warnings


def test_out_of_range_face_indices_are_reported_without_crashing() -> None:
    vertices, faces = _tetrahedron()
    body = explicit_synthetic_body(
        vertices,
        faces + [[0, 1, 9]],
        body_id="invalid-index",
    )

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.readiness.level == "invalid"
    assert diagnostics.invalid_face_indices == 1
    assert "body contains out-of-range face indices" in diagnostics.warnings
