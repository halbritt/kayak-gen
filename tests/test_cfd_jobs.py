"""Local CFD dispatch job tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kayakgen.eval.cfd.jobs import (
    CfdDispatchError,
    CfdJobSpec,
    CfdRunRecord,
    load_cfd_run_record,
    load_run_record,
    mock_failing_local_command_profile,
    prepare_cfd_job,
    prepare_local_job,
    read_local_status,
    run_cfd_job,
    run_local_job,
    solver_profile_names,
    unavailable_open_surface_profile,
    unavailable_watertight_solid_profile,
)
from kayakgen.eval.mesh_diagnostics import MeshReadiness
from kayakgen.eval.mesh_package import watertight_solid_profile, write_mesh_package
from kayakgen.model.hull import Hull


def test_job_spec_and_run_record_round_trip() -> None:
    job = CfdJobSpec(
        job_id="cfd-test",
        hull_ref="../mesh/hull.json",
        mesh_package_ref="../mesh",
        solver_profile="unavailable-open-wetted-surface",
        speed_mps=2.2,
        seawater_density_kg_m3=1025.0,
        kinematic_viscosity_m2_s=1.19e-6,
        created_at="2026-05-13T00:00:00Z",
        input_manifest="../mesh/manifest.json",
        mesh_readiness="cfd_surface_candidate",
        mesh_warnings=["raw dispatch only"],
    )
    run = CfdRunRecord(
        job_id=job.job_id,
        status="queued",
        solver_profile=job.solver_profile,
        input_manifest=job.input_manifest,
        mesh_warnings=job.mesh_warnings,
    )

    assert CfdJobSpec.model_validate_json(job.model_dump_json()) == job
    assert CfdRunRecord.model_validate_json(run.model_dump_json()) == run
    assert run.result_semantics == "raw_unvalidated"


def test_prepare_local_job_writes_deterministic_job_directory(tmp_path: Path) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_mesh_package(Hull(), mesh_dir, stations=8)
    profile = unavailable_open_surface_profile()

    first = prepare_local_job(
        mesh_dir,
        jobs_dir,
        profile,
        speed_mps=2.4,
        created_at="2026-05-13T00:00:00Z",
    )
    second = prepare_local_job(
        mesh_dir,
        jobs_dir,
        profile,
        speed_mps=2.4,
        created_at="2026-05-13T00:00:00Z",
    )

    assert second.job_dir == first.job_dir
    assert first.job_spec.job_id.startswith("cfd-")
    assert first.job_spec.mesh_package_ref == "../../mesh"
    assert first.job_spec.input_manifest == "../../mesh/manifest.json"
    assert first.job_spec.mesh_readiness == "cfd_surface_candidate"
    assert first.run_record.status == "queued"
    assert {"job.json", "profile.json", "run.json"} <= {
        path.name for path in first.job_dir.iterdir()
    }
    assert read_local_status(first.job_dir).status == "queued"


def test_public_prepare_api_returns_job_paths(tmp_path: Path) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_mesh_package(Hull(), mesh_dir, stations=8)

    paths = prepare_cfd_job(
        mesh_dir,
        jobs_dir,
        solver_profile_name="unavailable_open_wetted_surface_v1",
        speed_mps=2.4,
    )

    assert "unavailable-open-wetted-surface" in solver_profile_names()
    assert paths.job_dir.name.startswith("cfd-")
    assert paths.job_path == paths.job_dir / "job.json"
    assert paths.run_path == paths.job_dir / "run.json"
    assert paths.run.status == "queued"
    assert load_cfd_run_record(paths.job_dir).status == "queued"


def test_prepare_rejects_watertight_profile_below_cfd_ready(tmp_path: Path) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_mesh_package(
        Hull(),
        mesh_dir,
        stations=8,
        solver_profile=watertight_solid_profile(),
    )

    with pytest.raises(CfdDispatchError, match="readiness below solver requirement"):
        prepare_local_job(
            mesh_dir,
            jobs_dir,
            unavailable_watertight_solid_profile(),
            speed_mps=2.4,
        )


def test_prepare_rejects_forged_watertight_cfd_ready_manifest_over_open_artifacts(
    tmp_path: Path,
) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    manifest = write_mesh_package(
        Hull(),
        mesh_dir,
        stations=8,
        solver_profile=watertight_solid_profile(),
    )
    forged = manifest.model_copy(
        update={
            "readiness": MeshReadiness(
                level="cfd_ready",
                reasons=["forged readiness claim"],
            ),
            "warnings": ["forged readiness claim"],
        }
    )
    (mesh_dir / "manifest.json").write_text(forged.model_dump_json(indent=2))

    with pytest.raises(
        CfdDispatchError,
        match="watertight dispatch requires profile-scoped closed-volume diagnostic evidence",
    ):
        prepare_local_job(
            mesh_dir,
            jobs_dir,
            unavailable_watertight_solid_profile(),
            speed_mps=2.4,
        )


def test_prepare_rejects_forged_watertight_quality_report_evidence(
    tmp_path: Path,
) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    manifest = write_mesh_package(
        Hull(),
        mesh_dir,
        stations=8,
        solver_profile=watertight_solid_profile(),
    )
    forged = manifest.model_copy(
        update={
            "readiness": MeshReadiness(
                level="cfd_ready",
                reasons=["forged readiness claim"],
            ),
            "warnings": ["forged readiness claim"],
        }
    )
    (mesh_dir / "manifest.json").write_text(forged.model_dump_json(indent=2))
    forged_evidence = {
        "profile_name": "watertight_solid_resistance_v1",
        "readiness": {"level": "cfd_ready", "reasons": []},
        "raw_boundary_edges": 0,
        "welded_boundary_edges": 0,
        "raw_nonmanifold_edges": 0,
        "welded_nonmanifold_edges": 0,
        "closed_volume": True,
        "signed_volume_m3": 1.0,
    }
    for ref in manifest.quality_reports.values():
        (mesh_dir / ref).write_text(json.dumps(forged_evidence))

    with pytest.raises(
        CfdDispatchError,
        match="watertight dispatch requires profile-scoped closed-volume diagnostic evidence",
    ):
        prepare_local_job(
            mesh_dir,
            jobs_dir,
            unavailable_watertight_solid_profile(),
            speed_mps=2.4,
        )


def test_prepare_rejects_solver_profile_mismatch(tmp_path: Path) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_mesh_package(Hull(), mesh_dir, stations=8)

    with pytest.raises(CfdDispatchError, match="solver profile mismatch"):
        prepare_local_job(
            mesh_dir,
            jobs_dir,
            unavailable_watertight_solid_profile(),
            speed_mps=2.4,
        )


def test_prepare_rejects_non_positive_job_inputs(tmp_path: Path) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_mesh_package(Hull(), mesh_dir, stations=8)

    with pytest.raises(CfdDispatchError, match="speed_mps"):
        prepare_local_job(
            mesh_dir,
            jobs_dir,
            unavailable_open_surface_profile(),
            speed_mps=0.0,
        )


def test_unavailable_adapter_writes_unavailable_run_record(tmp_path: Path) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_mesh_package(Hull(), mesh_dir, stations=8)
    job = prepare_local_job(
        mesh_dir,
        jobs_dir,
        unavailable_open_surface_profile(),
        speed_mps=2.4,
    )

    record = run_cfd_job(job.job_dir)

    assert record.status == "unavailable"
    assert record.error_kind == "solver_unavailable"
    assert "raw and unvalidated" in (record.error_message or "")
    assert record.result_semantics == "raw_unvalidated"
    assert load_run_record(job.job_dir / "run.json") == record


def test_mock_local_command_adapter_writes_failed_record_and_logs(tmp_path: Path) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_mesh_package(Hull(), mesh_dir, stations=8)
    job = prepare_local_job(
        mesh_dir,
        jobs_dir,
        mock_failing_local_command_profile(),
        speed_mps=2.4,
    )

    record = run_local_job(job.job_dir)

    assert record.status == "failed"
    assert record.error_kind == "command_failed"
    assert "mock CFD command failed intentionally" in (record.error_message or "")
    assert record.raw_records == {"returncode": 7}
    assert record.logs == {"stdout": "logs/stdout.log", "stderr": "logs/stderr.log"}
    assert (job.job_dir / "logs" / "stdout.log").read_text() == "mock CFD command starting\n"
    assert (
        job.job_dir / "logs" / "stderr.log"
    ).read_text() == "mock CFD command failed intentionally\n"
