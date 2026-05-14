"""RFC 0040 solver-readiness report tests."""

from __future__ import annotations

from pathlib import Path

from kayakgen.eval.closed_volume import (
    diagnose_closed_volume_body,
    explicit_synthetic_body,
    explicit_synthetic_self_intersection_policy,
)
from kayakgen.eval.mesh_package import (
    closed_volume_solver_readiness_report,
    closed_volume_solver_readiness_report_from_package,
    watertight_solid_profile,
    write_mesh_package,
    write_watertight_volume_mesh_handoff_package,
)
from kayakgen.model.hull import Hull


WATERTIGHT_DISPATCH_PROFILE = {
    "name": "unavailable-watertight-solid",
    "required_mesh_profile": "watertight_solid_resistance_v1",
    "required_mesh_readiness": "cfd_ready",
}


def _tetrahedron() -> tuple[list[list[float]], list[list[int]]]:
    return (
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        [
            [0, 2, 1],
            [0, 1, 3],
            [1, 2, 3],
            [2, 0, 3],
        ],
    )


def _blocker_codes(report) -> set[str]:
    return {blocker.code for blocker in report.blockers}


def _warning_codes(report) -> set[str]:
    return {warning.code for warning in report.warnings}


def test_open_surface_package_report_blocks_watertight_solver_input(
    tmp_path: Path,
) -> None:
    manifest = write_mesh_package(Hull(name="rfc0040-open"), tmp_path, stations=8)

    report = closed_volume_solver_readiness_report(
        manifest,
        solver_profile=WATERTIGHT_DISPATCH_PROFILE,
    )

    assert report.gate_status == "blocked"
    assert report.input_semantics == "not_solver_input"
    assert report.solver_profile == "unavailable-watertight-solid"
    assert report.required_mesh_profile == "watertight_solid_resistance_v1"
    assert report.required_mesh_readiness == "cfd_ready"
    assert {
        "open_surface_not_closed_body",
        "generated_body_missing",
        "volume_mesh_missing",
        "solver_profile_not_satisfied",
    } <= _blocker_codes(report)
    assert report.boundary_patches == []
    assert manifest.readiness.level != "cfd_ready"


def test_generated_body_without_volume_mesh_report_blocks_handoff(
    tmp_path: Path,
) -> None:
    manifest = write_watertight_volume_mesh_handoff_package(
        Hull(name="rfc0040-generated-no-volume"),
        tmp_path,
        stations=8,
        closed_body_stations=8,
    )

    report = closed_volume_solver_readiness_report_from_package(
        tmp_path,
        solver_profile=WATERTIGHT_DISPATCH_PROFILE,
    )

    assert report.gate_status == "blocked"
    assert report.body_ref == manifest.body_ref
    assert report.body_profile == "generated_hull_plus_deck_closed_body_v1"
    assert report.generated_body_diagnostic_ref == "closed-volume-diagnostic.json"
    assert report.self_intersection_diagnostic_ref == "closed-volume-diagnostic.json"
    assert report.volume_mesh_diagnostic_ref is None
    assert report.evidence_hash_algorithm == "sha256"
    assert report.evidence_hash_algorithms == {
        "closed_volume_diagnostic": "sha256",
        "self_intersection_diagnostic": "sha256",
    }
    assert {"solver_profile_not_satisfied", "volume_mesh_missing"} <= _blocker_codes(
        report
    )
    assert "generated_body_not_solver_input" in _warning_codes(report)
    assert manifest.readiness.level != "cfd_ready"


def test_fixture_handoff_report_ready_for_profile_with_boundary_metadata(
    tmp_path: Path,
) -> None:
    manifest = write_watertight_volume_mesh_handoff_package(
        Hull(name="rfc0040-fixture-ready"),
        tmp_path,
        stations=8,
        closed_body_stations=8,
        include_fixture_volume_mesh=True,
    )

    report = closed_volume_solver_readiness_report_from_package(
        tmp_path,
        solver_profile=WATERTIGHT_DISPATCH_PROFILE,
    )

    assert manifest.readiness.level == "cfd_ready"
    assert report.gate_status == "ready_for_profile"
    assert report.input_semantics == "profile_input_candidate"
    assert report.blocker_reasons == []
    assert set(report.evidence_hash_algorithms) == set(manifest.evidence_hashes)
    assert set(report.evidence_hash_algorithms.values()) == {"sha256"}
    assert report.boundary_patches
    assert report.boundary_patches[0].name == "generated_hull_plus_deck"
    assert report.boundary_patches[0].marker == "wall:generated_hull_plus_deck"
    assert report.boundary_markers == {
        "generated_hull_plus_deck": "wall:generated_hull_plus_deck"
    }
    assert "fixture_handoff_not_production_meshing" in _warning_codes(report)
    assert "raw_solver_output_not_validated" in _warning_codes(report)


def test_synthetic_closed_body_report_cannot_satisfy_generated_kayak_handoff(
    tmp_path: Path,
) -> None:
    manifest = write_watertight_volume_mesh_handoff_package(
        Hull(name="rfc0040-synthetic-blocked"),
        tmp_path,
        stations=8,
        closed_body_stations=8,
    )
    vertices, faces = _tetrahedron()
    synthetic = diagnose_closed_volume_body(
        explicit_synthetic_body(
            vertices,
            faces,
            body_id="synthetic-readiness-blocker",
            policy=explicit_synthetic_self_intersection_policy(),
        )
    )

    report = closed_volume_solver_readiness_report(
        manifest,
        solver_profile=WATERTIGHT_DISPATCH_PROFILE,
        closed_volume_diagnostics=synthetic,
        self_intersection_diagnostics=synthetic,
    )

    assert report.gate_status == "blocked"
    assert report.input_semantics == "not_solver_input"
    assert "synthetic_body_not_generated_kayak" in _blocker_codes(report)
    assert "volume_mesh_missing" in _blocker_codes(report)
