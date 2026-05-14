"""Closed-volume contract tests for explicit synthetic meshes."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kayakgen.eval.closed_volume import (
    ClosedSurfacePart,
    ClosedVolumeBody,
    ClosedVolumeDiagnostics,
    ClosedVolumeReadiness,
    ClosedVolumeTolerances,
    diagnose_closed_volume_body,
    explicit_synthetic_body,
    explicit_synthetic_self_intersection_policy,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.volume_mesh import (
    VolumeMeshDiagnostic,
    fixture_volume_mesh_diagnostic,
    sha256_file,
    sha256_json,
)
from kayakgen.model.hull import Hull


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


def _offset_vertices(
    vertices: list[list[float]],
    offset: tuple[float, float, float],
) -> list[list[float]]:
    return [
        [vertex[0] + offset[0], vertex[1] + offset[1], vertex[2] + offset[2]]
        for vertex in vertices
    ]


def _two_tetrahedra_same_part(
    offset: tuple[float, float, float],
    *,
    reverse_second: bool = False,
) -> tuple[list[list[float]], list[list[int]]]:
    vertices, faces = _tetrahedron()
    second_faces = [[index + len(vertices) for index in face] for face in faces]
    if reverse_second:
        second_faces = [list(reversed(face)) for face in second_faces]
    return vertices + _offset_vertices(vertices, offset), faces + second_faces


def _part(
    name: str,
    vertices: list[list[float]],
    faces: list[list[int]],
) -> ClosedSurfacePart:
    return ClosedSurfacePart(
        name=name,
        vertices=tuple(tuple(value for value in vertex) for vertex in vertices),
        faces=tuple(tuple(index for index in face) for face in faces),
    )


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
    assert loaded.policy.self_intersection_policy == "not_checked_rfc0016_compatibility"
    assert loaded.policy.tolerances.vertex_weld_tolerance_m > 0.0

    assert loaded.readiness.level == "closed_volume"
    assert loaded.cfd_ready is False
    assert loaded.raw_boundary_edges == 0
    assert loaded.welded_boundary_edges == 0
    assert loaded.raw_nonmanifold_edges == 0
    assert loaded.welded_nonmanifold_edges == 0
    assert loaded.signed_volume_m3 == pytest.approx(1.0 / 6.0)
    assert loaded.self_intersection_status == "not_checked"
    assert loaded.self_intersection_algorithm == "not_checked_rfc0016_compatibility"
    assert loaded.self_intersection_tolerance_m > 0.0
    assert loaded.self_intersection_pair_count == 0
    assert loaded.self_intersection_example_pairs == []
    assert "not checked" in " ".join(loaded.warnings)
    assert "not cfd_ready" in " ".join(loaded.warnings)


def test_rfc0021_valid_closed_tetrahedron_requires_passed_self_intersection() -> None:
    vertices, faces = _tetrahedron()
    body = explicit_synthetic_body(
        vertices,
        faces,
        body_id="valid-tetrahedron-rfc0021",
        policy=explicit_synthetic_self_intersection_policy(),
    )

    diagnostics = diagnose_closed_volume_body(body)
    loaded = ClosedVolumeDiagnostics.model_validate_json(diagnostics.model_dump_json())

    assert loaded.profile_name == "explicit_synthetic_closed_volume_self_intersection_v1"
    assert loaded.policy.self_intersection_policy == "required_rfc0021_conservative"
    assert loaded.readiness.level == "closed_volume"
    assert loaded.self_intersection_status == "passed"
    assert loaded.self_intersection_algorithm == "assembled_welded_aabb_triangle_pairs_v1"
    assert loaded.self_intersection_pair_count == 0
    assert loaded.self_intersection_example_pairs == []
    assert loaded.cfd_ready is False


def test_rfc0021_closed_edge_manifold_self_intersection_blocks_readiness() -> None:
    vertices, faces = _two_tetrahedra_same_part((0.25, 0.25, 0.25))
    body = explicit_synthetic_body(
        vertices,
        faces,
        body_id="overlapping-components",
        policy=explicit_synthetic_self_intersection_policy(),
    )

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0
    assert diagnostics.signed_volume_m3 == pytest.approx(1.0 / 3.0)
    assert diagnostics.readiness.level == "invalid"
    assert diagnostics.self_intersection_status == "failed"
    assert diagnostics.self_intersection_pair_count == 3
    assert 0 < len(diagnostics.self_intersection_example_pairs) <= 8
    assert {
        pair.classification for pair in diagnostics.self_intersection_example_pairs
    } == {"intersection"}
    assert "self-intersection diagnostic status is failed" in " ".join(
        diagnostics.warnings
    )


def test_rfc0021_cross_part_intersection_is_body_level_failure() -> None:
    vertices, faces = _tetrahedron()
    body = ClosedVolumeBody(
        body_id="cross-part-overlap",
        policy=explicit_synthetic_self_intersection_policy(),
        parts=(
            _part("hull-fixture", vertices, faces),
            _part("deck-fixture", _offset_vertices(vertices, (0.25, 0.25, 0.25)), faces),
        ),
    )

    diagnostics = diagnose_closed_volume_body(body)

    assert all(report.raw_boundary_edges == 0 for report in diagnostics.part_diagnostics)
    assert all(report.raw_nonmanifold_edges == 0 for report in diagnostics.part_diagnostics)
    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.readiness.level == "invalid"
    assert diagnostics.self_intersection_status == "failed"
    assert diagnostics.self_intersection_pair_count == 3
    assert any(
        {pair.first.part_name, pair.second.part_name}
        == {"hull-fixture", "deck-fixture"}
        for pair in diagnostics.self_intersection_example_pairs
    )


def test_rfc0021_vertex_only_pinch_is_not_skipped_as_adjacency() -> None:
    vertices, faces = _two_tetrahedra_same_part(
        (0.0, 0.0, 0.0),
        reverse_second=True,
    )
    vertices[5] = [-1.0, 0.0, 0.0]
    vertices[6] = [0.0, -1.0, 0.0]
    vertices[7] = [0.0, 0.0, -1.0]
    body = explicit_synthetic_body(
        vertices,
        faces,
        body_id="vertex-pinch",
        policy=explicit_synthetic_self_intersection_policy(),
    )

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0
    assert diagnostics.signed_volume_m3 == pytest.approx(1.0 / 3.0)
    assert diagnostics.readiness.level == "invalid"
    assert diagnostics.self_intersection_status == "failed"
    assert diagnostics.self_intersection_pair_count > 0


def test_rfc0021_near_contact_is_inconclusive_and_examples_are_capped() -> None:
    gap_m = 5e-7
    vertices, faces = _two_tetrahedra_same_part((1.0 + gap_m, 0.0, 0.0))
    policy = explicit_synthetic_self_intersection_policy().model_copy(
        update={
            "tolerances": ClosedVolumeTolerances(
                vertex_weld_tolerance_m=1e-12,
                self_intersection_tolerance_m=1e-6,
            )
        }
    )
    body = explicit_synthetic_body(
        vertices,
        faces,
        body_id="near-contact",
        policy=policy,
    )

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.readiness.level == "invalid"
    assert diagnostics.self_intersection_status == "inconclusive"
    assert diagnostics.self_intersection_pair_count > 8
    assert len(diagnostics.self_intersection_example_pairs) == 8
    assert {
        pair.classification for pair in diagnostics.self_intersection_example_pairs
    } == {"near_contact"}
    assert "self-intersection diagnostic status is inconclusive" in " ".join(
        diagnostics.warnings
    )


def test_rfc0021_profile_rejects_serialized_closed_volume_without_passed_check() -> None:
    vertices, faces = _tetrahedron()
    diagnostics = diagnose_closed_volume_body(
        explicit_synthetic_body(
            vertices,
            faces,
            body_id="valid-tetrahedron-rfc0021",
            policy=explicit_synthetic_self_intersection_policy(),
        )
    )
    forged = diagnostics.model_copy(
        update={
            "readiness": ClosedVolumeReadiness(level="closed_volume", reasons=[]),
            "self_intersection_status": "inconclusive",
        }
    ).model_dump()

    with pytest.raises(ValidationError, match="requires passed self-intersection"):
        ClosedVolumeDiagnostics.model_validate(forged)


def test_rfc0023_fixture_volume_mesh_diagnostic_round_trips(tmp_path) -> None:
    artifact = tmp_path / "fixture-volume.mesh"
    artifact.write_bytes(b"fixture volume mesh\n")
    hull = Hull(name="rfc0023-volume-mesh")
    closed_diagnostics = diagnose_closed_volume_body(
        generated_hull_plus_deck_body(hull, stations=4)
    )
    closed_hash = sha256_json(closed_diagnostics)

    diagnostic = fixture_volume_mesh_diagnostic(
        closed_diagnostics,
        closed_volume_diagnostic_hash=closed_hash,
        self_intersection_diagnostic_hash=closed_hash,
        artifact_ref="fixture-volume.mesh",
        artifact_sha256=sha256_file(artifact),
    )
    loaded = VolumeMeshDiagnostic.model_validate_json(diagnostic.model_dump_json())

    assert loaded.body_ref == closed_diagnostics.body_id
    assert loaded.source_hull_hash == hull.hash()
    assert loaded.closed_volume_diagnostic_hash == closed_hash
    assert loaded.self_intersection_diagnostic_hash == closed_hash
    assert loaded.deterministic_inputs["closed_volume_diagnostic_hash"] == closed_hash
    assert loaded.output_artifacts["volume_mesh"].sha256 == sha256_file(artifact)
    assert loaded.cell_count > 0
    assert loaded.boundary_face_count == closed_diagnostics.face_count
    assert loaded.body_surface_matches_diagnostic is True
    assert loaded.readiness.level == "cfd_ready"
    assert loaded.readiness.reasons[0].code == "passed"


def test_rfc0023_volume_mesh_records_structured_blockers() -> None:
    hull = Hull(name="rfc0023-volume-mesh-blocked")
    closed_diagnostics = diagnose_closed_volume_body(
        generated_hull_plus_deck_body(hull, stations=4)
    )
    passing = fixture_volume_mesh_diagnostic(
        closed_diagnostics,
        closed_volume_diagnostic_hash=sha256_json(closed_diagnostics),
        self_intersection_diagnostic_hash=sha256_json(closed_diagnostics),
        artifact_ref="fixture-volume.mesh",
        artifact_sha256="0" * 64,
    )

    payload = passing.model_dump(mode="json")
    payload.update(
        {
            "output_artifacts": {},
            "cell_count": 0,
            "inverted_cell_count": 2,
            "body_surface_matches_diagnostic": False,
            "readiness": {"level": "invalid", "reasons": [
                {
                    "code": "missing_volume_mesh",
                    "message": "volume mesh artifact is missing",
                },
                {
                    "code": "volume_mesh_not_ready",
                    "message": "volume mesh contains blocking cell counts",
                },
                {
                    "code": "body_surface_mismatch",
                    "message": "body surface does not match generated diagnostic",
                },
            ]},
        }
    )
    blocked = VolumeMeshDiagnostic.model_validate(payload)

    assert blocked.readiness.level == "invalid"
    assert {reason.code for reason in blocked.readiness.reasons} >= {
        "missing_volume_mesh",
        "volume_mesh_not_ready",
        "body_surface_mismatch",
    }


def test_rfc0021_broad_phase_handles_many_non_overlapping_components() -> None:
    vertices, faces = _tetrahedron()
    all_vertices: list[list[float]] = []
    all_faces: list[list[int]] = []
    for component_index in range(80):
        offset = len(all_vertices)
        all_vertices.extend(
            _offset_vertices(vertices, (float(component_index * 3), 0.0, 0.0))
        )
        all_faces.extend([[index + offset for index in face] for face in faces])
    body = explicit_synthetic_body(
        all_vertices,
        all_faces,
        body_id="many-separated-components",
        policy=explicit_synthetic_self_intersection_policy(),
    )

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.face_count == 320
    assert diagnostics.readiness.level == "closed_volume"
    assert diagnostics.self_intersection_status == "passed"
    assert diagnostics.self_intersection_pair_count == 0


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


def test_nonfinite_vertices_are_reported_without_crashing() -> None:
    vertices, faces = _tetrahedron()
    body = explicit_synthetic_body(
        vertices + [[float("nan"), 0.0, 0.0]],
        faces + [[0, 1, 4]],
        body_id="nonfinite-vertex",
        policy=explicit_synthetic_self_intersection_policy(),
    )

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.readiness.level == "invalid"
    assert diagnostics.nonfinite_vertices == 1
    assert diagnostics.part_diagnostics[0].nonfinite_vertices == 1
    assert "body contains non-finite vertices" in diagnostics.warnings


def test_degenerate_faces_are_reported_without_masking_closed_edges() -> None:
    vertices, faces = _tetrahedron()
    body = explicit_synthetic_body(
        vertices,
        faces + [[0, 0, 1]],
        body_id="degenerate-face",
        policy=explicit_synthetic_self_intersection_policy(),
    )

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.readiness.level == "invalid"
    assert diagnostics.degenerate_faces == 1
    assert diagnostics.part_diagnostics[0].degenerate_faces == 1
    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0
    assert "body contains degenerate faces" in diagnostics.warnings


def test_custom_tolerances_round_trip_through_diagnostics_json() -> None:
    vertices, faces = _tetrahedron()
    tolerances = ClosedVolumeTolerances(
        vertex_weld_tolerance_m=2e-6,
        degenerate_area_tolerance_m2=3e-12,
        signed_volume_tolerance_m3=4e-13,
        self_intersection_tolerance_m=5e-9,
    )
    policy = explicit_synthetic_self_intersection_policy().model_copy(
        update={"tolerances": tolerances}
    )
    body = explicit_synthetic_body(
        vertices,
        faces,
        body_id="custom-tolerances",
        policy=policy,
    )

    diagnostics = diagnose_closed_volume_body(body)
    loaded = ClosedVolumeDiagnostics.model_validate_json(diagnostics.model_dump_json())

    assert loaded.readiness.level == "closed_volume"
    assert loaded.policy.tolerances == tolerances
    assert loaded.self_intersection_tolerance_m == pytest.approx(
        tolerances.self_intersection_tolerance_m
    )
