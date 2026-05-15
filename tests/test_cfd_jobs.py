"""Local CFD dispatch job tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from kayakgen.eval.cfd.jobs import (
    CfdDispatchError,
    CfdJobSpec,
    CfdOpenFoamForceDatResult,
    CfdOpenFoamForceDatSample,
    CfdOpenFoamRawResult,
    CfdRunRecord,
    OPENFOAM_CASE_ROOT,
    OPENFOAM_CASE_TEMPLATE_VERSION,
    OPENFOAM_FORCE_DAT_OUTPUT,
    OPENFOAM_PROFILE_NAME,
    OPENFOAM_RAW_RESULT,
    SolverRawResult,
    load_cfd_run_record,
    load_run_record,
    mock_failing_local_command_profile,
    openfoam_v2512_interfoam_local_profile,
    parse_openfoam_force_dat,
    prepare_cfd_job,
    prepare_local_job,
    read_local_status,
    run_cfd_job,
    run_local_job,
    solver_profile_by_name,
    solver_profile_names,
    unavailable_open_surface_profile,
    unavailable_watertight_solid_profile,
)
from kayakgen.eval.closed_volume import (
    ClosedVolumeReadiness,
    diagnose_closed_volume_body,
    explicit_synthetic_body,
    explicit_synthetic_self_intersection_policy,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.contract import CfdResult
from kayakgen.eval.mesh_diagnostics import MeshReadiness
from kayakgen.eval.mesh_package import (
    watertight_solid_profile,
    write_mesh_package,
    write_watertight_volume_mesh_handoff_package,
)
from kayakgen.eval.volume_mesh import VolumeMeshDiagnostic, sha256_file
from kayakgen.model.hull import Hull

FIXTURE_PROFILE_NAME = "fixture-local-command"
FIXTURE_RAW_RESULT = "raw-result.json"
FIXTURE_WARNING_FRAGMENT = "not calibrated, validated, or final design fitness"
OPENFOAM_FORCE_FIXTURE = Path(__file__).parent / "fixtures" / "openfoam" / "force.dat"
OPENFOAM_WARNING_FRAGMENT = "not calibrated, validated, or final design fitness"


def _prepare_fixture_job(tmp_path: Path, *, speed_mps: float = 2.4):
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_mesh_package(Hull(), mesh_dir, stations=8)
    return prepare_cfd_job(
        mesh_dir,
        jobs_dir,
        solver_profile_name=FIXTURE_PROFILE_NAME,
        speed_mps=speed_mps,
    )


def _prepare_openfoam_job(tmp_path: Path, *, speed_mps: float = 2.4):
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_watertight_volume_mesh_handoff_package(
        Hull(name="openfoam-skeleton"),
        mesh_dir,
        stations=8,
        closed_body_stations=8,
        include_fixture_volume_mesh=True,
    )
    return prepare_cfd_job(
        mesh_dir,
        jobs_dir,
        solver_profile_name=OPENFOAM_PROFILE_NAME,
        speed_mps=speed_mps,
    )


def _set_fixture_command(job_dir: Path, command_template: list[str]) -> None:
    profile_path = job_dir / "profile.json"
    profile = json.loads(profile_path.read_text())
    assert profile["name"] == FIXTURE_PROFILE_NAME
    assert profile["adapter_name"] == "fixture_local_command"
    profile["command_template"] = command_template
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")


def _set_openfoam_profile_fields(job_dir: Path, **updates: object) -> None:
    profile_path = job_dir / "profile.json"
    profile = json.loads(profile_path.read_text())
    assert profile["name"] == OPENFOAM_PROFILE_NAME
    assert profile["adapter_name"] == "openfoam_local"
    profile.update(updates)
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")


def _case_file_texts(job_dir: Path) -> dict[str, str]:
    case_dir = job_dir / "case"
    assert case_dir.is_dir()
    return {
        path.relative_to(job_dir).as_posix(): path.read_text()
        for path in sorted(case_dir.rglob("*"))
        if path.is_file()
    }


def _fixture_warning_text(raw_records: dict[str, object]) -> str:
    warnings = raw_records.get("warnings")
    assert isinstance(warnings, list)
    return " ".join(str(warning) for warning in warnings)


def _write_manifest(mesh_dir: Path, manifest) -> None:
    (mesh_dir / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n")


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
    assert job.claim_state == "raw_unvalidated"
    assert run.claim_state == "raw_unvalidated"
    assert job.accepted_uses == []
    assert run.accepted_uses == []
    assert json.loads(job.model_dump_json())["claim_state"] == "raw_unvalidated"
    assert json.loads(run.model_dump_json())["claim_state"] == "raw_unvalidated"
    assert run.result_semantics == "raw_unvalidated"


def test_cfd_records_reject_validated_or_calibrated_promotion() -> None:
    with pytest.raises(ValidationError, match="raw_unvalidated"):
        CfdRunRecord(
            job_id="cfd-test",
            status="succeeded",
            solver_profile="unavailable-open-wetted-surface",
            input_manifest="../mesh/manifest.json",
            claim_state="calibrated_model",
        )

    with pytest.raises(ValidationError, match="accepted uses"):
        SolverRawResult(status="succeeded", accepted_uses=["final_prediction"])


def test_reserved_cfd_drag_result_serializes_raw_claim_state() -> None:
    result = CfdResult(solver="reserved", drag_N=12.0)

    assert result.claim_state == "raw_unvalidated"
    assert result.accepted_uses == []
    assert json.loads(result.model_dump_json())["claim_state"] == "raw_unvalidated"
    with pytest.raises(ValidationError, match="raw_unvalidated"):
        CfdResult(solver="reserved", drag_N=12.0, claim_state="calibrated_model")


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


def test_fixture_local_command_profile_contract_is_listed() -> None:
    profile = solver_profile_by_name(FIXTURE_PROFILE_NAME)

    assert FIXTURE_PROFILE_NAME in solver_profile_names()
    assert profile.name == FIXTURE_PROFILE_NAME
    assert profile.required_mesh_readiness == "cfd_surface_candidate"
    assert profile.required_mesh_profile == "open_wetted_surface_resistance_v1"
    assert profile.adapter_name == "fixture_local_command"
    assert profile.result_semantics == "raw_unvalidated"
    assert profile.claim_state == "raw_unvalidated"
    assert profile.accepted_uses == []


def test_openfoam_v2512_interfoam_profile_contract_is_listed() -> None:
    profile = solver_profile_by_name(OPENFOAM_PROFILE_NAME)

    assert OPENFOAM_PROFILE_NAME in solver_profile_names()
    assert solver_profile_by_name("openfoam_v2512_interfoam_local_v1") == profile
    assert openfoam_v2512_interfoam_local_profile() == profile
    assert profile.name == OPENFOAM_PROFILE_NAME
    assert profile.required_mesh_readiness == "cfd_ready"
    assert profile.required_mesh_profile == "watertight_solid_resistance_v1"
    assert profile.adapter_name == "openfoam_local"
    assert profile.solver_name == "OpenFOAM.com OpenFOAM-v2512 interFoam"
    assert profile.solver_version_command == ["foamVersion"]
    assert profile.required_solver_version == "v2512"
    assert profile.case_template_version == OPENFOAM_CASE_TEMPLATE_VERSION
    assert profile.expected_raw_outputs == [OPENFOAM_FORCE_DAT_OUTPUT]
    assert profile.timeout_seconds is not None
    assert profile.log_limit_bytes is not None
    assert profile.result_semantics == "raw_unvalidated"
    assert profile.claim_state == "raw_unvalidated"
    assert profile.accepted_uses == []


def test_fixture_prepare_writes_deterministic_case_files(tmp_path: Path) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_mesh_package(Hull(), mesh_dir, stations=8)
    profile = solver_profile_by_name(FIXTURE_PROFILE_NAME)

    first = prepare_local_job(
        mesh_dir,
        jobs_dir,
        profile,
        speed_mps=2.4,
        created_at="2026-05-13T00:00:00Z",
    )
    first_case_files = _case_file_texts(first.job_dir)
    second = prepare_local_job(
        mesh_dir,
        jobs_dir,
        profile,
        speed_mps=2.4,
        created_at="2026-05-13T00:00:00Z",
    )

    assert second.job_dir == first.job_dir
    assert {"case/fixture-case.json", "case/command.json"} <= set(first_case_files)
    assert _case_file_texts(second.job_dir) == first_case_files

    fixture_input = json.loads(first_case_files["case/fixture-case.json"])
    assert fixture_input["job_id"] == first.job_spec.job_id
    assert fixture_input["solver_profile"] == FIXTURE_PROFILE_NAME
    assert fixture_input["speed_mps"] == pytest.approx(2.4)
    assert fixture_input["seawater_density_kg_m3"] == pytest.approx(1025.0)
    assert fixture_input["kinematic_viscosity_m2_s"] == pytest.approx(1.19e-6)
    assert fixture_input["result_semantics"] == "raw_unvalidated"
    assert fixture_input["mesh"]["hull_hash"] == first.mesh_manifest.hull_hash
    assert fixture_input["mesh"]["readiness"] == "cfd_surface_candidate"
    assert fixture_input["mesh"]["solver_profile"] == "open_wetted_surface_resistance_v1"

    command_spec = json.loads(first_case_files["case/command.json"])
    assert command_spec["command"] == first.solver_profile.command_template
    assert command_spec["case_input"] == "case/fixture-case.json"
    assert command_spec["raw_output"] == FIXTURE_RAW_RESULT
    assert command_spec["result_semantics"] == "raw_unvalidated"


def test_openfoam_prepare_writes_deterministic_case_files(tmp_path: Path) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    manifest = write_watertight_volume_mesh_handoff_package(
        Hull(name="openfoam-deterministic-case"),
        mesh_dir,
        stations=8,
        closed_body_stations=8,
        include_fixture_volume_mesh=True,
    )
    profile = solver_profile_by_name(OPENFOAM_PROFILE_NAME)

    first = prepare_local_job(
        mesh_dir,
        jobs_dir,
        profile,
        speed_mps=2.4,
        created_at="2026-05-13T00:00:00Z",
    )
    first_case_files = _case_file_texts(first.job_dir)
    second = prepare_local_job(
        mesh_dir,
        jobs_dir,
        profile,
        speed_mps=2.4,
        created_at="2026-05-13T00:00:00Z",
    )

    assert second.job_dir == first.job_dir
    assert {
        "case/openfoam/kayakgen-case.json",
        "case/openfoam/kayakgen-command.json",
        "case/openfoam/system/controlDict",
        "case/openfoam/constant/transportProperties",
        "case/openfoam/0/U",
    } <= set(first_case_files)
    assert _case_file_texts(second.job_dir) == first_case_files

    case_input = json.loads(first_case_files["case/openfoam/kayakgen-case.json"])
    assert case_input["job_id"] == first.job_spec.job_id
    assert case_input["solver_profile"] == OPENFOAM_PROFILE_NAME
    assert case_input["case_template_version"] == OPENFOAM_CASE_TEMPLATE_VERSION
    assert case_input["speed_mps"] == pytest.approx(2.4)
    assert case_input["expected_raw_outputs"] == [OPENFOAM_FORCE_DAT_OUTPUT]
    assert case_input["mesh"]["hull_hash"] == manifest.hull_hash
    assert case_input["mesh"]["readiness"] == "cfd_ready"
    assert case_input["mesh"]["solver_profile"] == "watertight_solid_resistance_v1"
    assert case_input["mesh"]["volume_mesh_artifacts"]
    assert case_input["result_semantics"] == "raw_unvalidated"

    command_spec = json.loads(first_case_files["case/openfoam/kayakgen-command.json"])
    assert command_spec["command"] == first.solver_profile.command_template
    assert command_spec["version_command"] == ["foamVersion"]
    assert command_spec["expected_raw_outputs"] == [OPENFOAM_FORCE_DAT_OUTPUT]
    assert command_spec["result_semantics"] == "raw_unvalidated"
    assert "application interFoam;" in first_case_files["case/openfoam/system/controlDict"]


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


def test_prepare_rejects_passed_rfc0021_closed_volume_as_cfd_ready_evidence(
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
    diagnostic = diagnose_closed_volume_body(
        explicit_synthetic_body(
            vertices,
            faces,
            body_id="rfc0021-passed-synthetic",
            policy=explicit_synthetic_self_intersection_policy(),
        )
    )
    assert diagnostic.readiness.level == "closed_volume"
    assert diagnostic.self_intersection_status == "passed"
    assert diagnostic.cfd_ready is False
    for ref in manifest.quality_reports.values():
        (mesh_dir / ref).write_text(diagnostic.model_dump_json(indent=2))

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


def test_prepare_rejects_generated_closed_body_as_cfd_ready_evidence(
    tmp_path: Path,
) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    hull = Hull(name="generated-dispatch-boundary")
    manifest = write_mesh_package(
        hull,
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

    diagnostic = diagnose_closed_volume_body(
        generated_hull_plus_deck_body(hull, stations=10)
    )
    assert diagnostic.profile_name == "generated_hull_plus_deck_closed_body_v1"
    assert diagnostic.readiness.level == "closed_volume"
    assert diagnostic.self_intersection_status == "passed"
    assert diagnostic.cfd_ready is False
    for ref in manifest.quality_reports.values():
        (mesh_dir / ref).write_text(diagnostic.model_dump_json(indent=2))

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


def test_prepare_accepts_matching_watertight_volume_mesh_handoff(
    tmp_path: Path,
) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    manifest = write_watertight_volume_mesh_handoff_package(
        Hull(name="rfc0023-positive-handoff"),
        mesh_dir,
        stations=8,
        closed_body_stations=8,
        include_fixture_volume_mesh=True,
    )

    job = prepare_local_job(
        mesh_dir,
        jobs_dir,
        unavailable_watertight_solid_profile(),
        speed_mps=2.4,
    )

    assert manifest.readiness.level == "cfd_ready"
    assert job.mesh_manifest.readiness.level == "cfd_ready"
    assert job.job_spec.mesh_readiness == "cfd_ready"
    assert job.job_spec.mesh_evidence_hashes == manifest.evidence_hashes
    assert job.run_record.status == "queued"


def test_prepare_rejects_watertight_handoff_with_stale_artifact_hash(
    tmp_path: Path,
) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_watertight_volume_mesh_handoff_package(
        Hull(name="rfc0023-stale-artifact"),
        mesh_dir,
        stations=8,
        closed_body_stations=8,
        include_fixture_volume_mesh=True,
    )
    (mesh_dir / "volume-mesh.fixture.json").write_text('{"tampered": true}\n')

    with pytest.raises(CfdDispatchError) as excinfo:
        prepare_local_job(
            mesh_dir,
            jobs_dir,
            unavailable_watertight_solid_profile(),
            speed_mps=2.4,
        )

    assert excinfo.value.code == "stale_checksum"
    assert "stale checksum" in str(excinfo.value)


def test_prepare_rejects_watertight_handoff_with_forbidden_path_ref(
    tmp_path: Path,
) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    manifest = write_watertight_volume_mesh_handoff_package(
        Hull(name="rfc0023-forbidden-ref"),
        mesh_dir,
        stations=8,
        closed_body_stations=8,
        include_fixture_volume_mesh=True,
    )
    forged = manifest.model_copy(update={"volume_mesh_diagnostic": "../outside.json"})
    _write_manifest(mesh_dir, forged)

    with pytest.raises(CfdDispatchError) as excinfo:
        prepare_local_job(
            mesh_dir,
            jobs_dir,
            unavailable_watertight_solid_profile(),
            speed_mps=2.4,
        )

    assert excinfo.value.code == "forbidden_path_ref"
    assert "forbidden path ref" in str(excinfo.value)


def test_prepare_rejects_synthetic_closed_volume_even_with_volume_mesh_refs(
    tmp_path: Path,
) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    manifest = write_watertight_volume_mesh_handoff_package(
        Hull(name="rfc0023-synthetic-rejection"),
        mesh_dir,
        stations=8,
        closed_body_stations=8,
        include_fixture_volume_mesh=True,
    )
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
    synthetic = diagnose_closed_volume_body(
        explicit_synthetic_body(
            vertices,
            faces,
            body_id="synthetic-not-generated",
            policy=explicit_synthetic_self_intersection_policy(),
        )
    )
    closed_path = mesh_dir / "closed-volume-diagnostic.json"
    closed_path.write_text(synthetic.model_dump_json(indent=2) + "\n")
    forged = manifest.model_copy(
        update={
            "evidence_hashes": {
                **manifest.evidence_hashes,
                "closed_volume_diagnostic": sha256_file(closed_path),
                "self_intersection_diagnostic": sha256_file(closed_path),
            }
        }
    )
    _write_manifest(mesh_dir, forged)

    with pytest.raises(CfdDispatchError) as excinfo:
        prepare_local_job(
            mesh_dir,
            jobs_dir,
            unavailable_watertight_solid_profile(),
            speed_mps=2.4,
        )

    assert excinfo.value.code == "synthetic_evidence"
    assert "synthetic closed-volume evidence" in str(excinfo.value)


def test_prepare_rejects_failed_self_intersection_evidence(
    tmp_path: Path,
) -> None:
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    manifest = write_watertight_volume_mesh_handoff_package(
        Hull(name="rfc0023-self-intersection"),
        mesh_dir,
        stations=8,
        closed_body_stations=8,
        include_fixture_volume_mesh=True,
    )
    closed_path = mesh_dir / "closed-volume-diagnostic.json"
    closed = diagnose_closed_volume_body(
        generated_hull_plus_deck_body(Hull(name="rfc0023-self-intersection"), stations=8)
    )
    failed = closed.model_copy(
        update={
            "readiness": ClosedVolumeReadiness(
                level="invalid",
                reasons=["self-intersection diagnostic status is failed"],
            ),
            "self_intersection_status": "failed",
            "self_intersection_pair_count": 1,
        }
    )
    closed_path.write_text(failed.model_dump_json(indent=2) + "\n")
    forged = manifest.model_copy(
        update={
            "evidence_hashes": {
                **manifest.evidence_hashes,
                "closed_volume_diagnostic": sha256_file(closed_path),
                "self_intersection_diagnostic": sha256_file(closed_path),
            }
        }
    )
    _write_manifest(mesh_dir, forged)

    with pytest.raises(CfdDispatchError) as excinfo:
        prepare_local_job(
            mesh_dir,
            jobs_dir,
            unavailable_watertight_solid_profile(),
            speed_mps=2.4,
        )

    assert excinfo.value.code == "failed_self_intersection"


def test_watertight_job_identity_changes_with_accepted_evidence_hash(
    tmp_path: Path,
) -> None:
    hull = Hull(name="rfc0023-job-identity")
    jobs_dir = tmp_path / "jobs"
    first_mesh = tmp_path / "mesh-a"
    second_mesh = tmp_path / "mesh-b"
    first_manifest = write_watertight_volume_mesh_handoff_package(
        hull,
        first_mesh,
        stations=8,
        closed_body_stations=8,
        include_fixture_volume_mesh=True,
    )
    second_manifest = write_watertight_volume_mesh_handoff_package(
        hull,
        second_mesh,
        stations=8,
        closed_body_stations=8,
        include_fixture_volume_mesh=True,
    )
    artifact_path = second_mesh / "volume-mesh.fixture.json"
    artifact = json.loads(artifact_path.read_text())
    artifact["fixture_variant"] = "changed-evidence"
    artifact_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    artifact_hash = sha256_file(artifact_path)

    volume_path = second_mesh / "volume-mesh-diagnostic.json"
    volume_data = json.loads(volume_path.read_text())
    volume_data["output_artifacts"]["volume_mesh"]["sha256"] = artifact_hash
    volume_path.write_text(json.dumps(volume_data, indent=2, sort_keys=True) + "\n")
    volume = VolumeMeshDiagnostic.model_validate_json(volume_path.read_text())
    volume_hash = sha256_file(volume_path)
    second_manifest = second_manifest.model_copy(
        update={
            "evidence_hashes": {
                **second_manifest.evidence_hashes,
                "volume_mesh_diagnostic": volume_hash,
                "volume_mesh_artifacts.volume_mesh": artifact_hash,
            }
        }
    )
    _write_manifest(second_mesh, second_manifest)

    first = prepare_local_job(
        first_mesh,
        jobs_dir,
        unavailable_watertight_solid_profile(),
        speed_mps=2.4,
    )
    second = prepare_local_job(
        second_mesh,
        jobs_dir,
        unavailable_watertight_solid_profile(),
        speed_mps=2.4,
    )

    assert volume.output_artifacts["volume_mesh"].sha256 == artifact_hash
    assert first_manifest.evidence_hashes != second_manifest.evidence_hashes
    assert first.job_dir != second.job_dir


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


def test_fixture_adapter_succeeds_with_schema_valid_raw_unvalidated_output(
    tmp_path: Path,
) -> None:
    job = _prepare_fixture_job(tmp_path, speed_mps=2.4)

    record = run_cfd_job(job.job_dir)

    assert record.status == "succeeded"
    assert record.error_kind is None
    assert record.error_message is None
    assert record.output_manifest == FIXTURE_RAW_RESULT
    assert record.result_semantics == "raw_unvalidated"
    assert record.claim_state == "raw_unvalidated"
    assert (job.job_dir / FIXTURE_RAW_RESULT).is_file()

    raw = record.raw_records
    assert raw["job_id"] == job.job.job_id
    assert raw["speed_mps"] == pytest.approx(2.4)
    assert raw["drag_force_n"] > 0.0
    assert isinstance(raw["residual_summary"], dict)
    assert raw["fixture_version"]
    assert raw["returncode"] == 0
    assert raw["claim_state"] == "raw_unvalidated"
    assert raw["accepted_uses"] == []
    assert FIXTURE_WARNING_FRAGMENT in _fixture_warning_text(raw)
    assert load_run_record(job.job_dir / "run.json") == record


def test_fixture_missing_command_persists_unavailable_or_failed_record(
    tmp_path: Path,
) -> None:
    job = _prepare_fixture_job(tmp_path)
    missing_command = job.job_dir / "bin" / "missing-fixture-command"
    _set_fixture_command(job.job_dir, [str(missing_command)])

    record = run_cfd_job(job.job_dir)

    assert record.status in {"unavailable", "failed"}
    assert record.error_kind
    assert record.error_message
    assert str(missing_command) in record.error_message
    assert record.result_semantics == "raw_unvalidated"
    assert load_run_record(job.job_dir / "run.json") == record


def test_fixture_nonzero_command_persists_failed_record_and_logs(
    tmp_path: Path,
) -> None:
    job = _prepare_fixture_job(tmp_path)
    _set_fixture_command(
        job.job_dir,
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.stdout.write('fixture command starting\\n'); "
                "sys.stderr.write('fixture command failed intentionally\\n'); "
                "sys.exit(7)"
            ),
        ],
    )

    record = run_cfd_job(job.job_dir)

    assert record.status == "failed"
    assert record.error_kind == "command_failed"
    assert "exited with code 7" in (record.error_message or "")
    assert "fixture command failed intentionally" in (record.error_message or "")
    assert record.raw_records["returncode"] == 7
    assert record.logs == {"stdout": "logs/stdout.log", "stderr": "logs/stderr.log"}
    assert (job.job_dir / "logs" / "stdout.log").read_text() == "fixture command starting\n"
    assert (
        job.job_dir / "logs" / "stderr.log"
    ).read_text() == "fixture command failed intentionally\n"
    assert load_run_record(job.job_dir / "run.json") == record


def test_fixture_clean_command_with_missing_raw_output_persists_failed_record(
    tmp_path: Path,
) -> None:
    job = _prepare_fixture_job(tmp_path)
    _set_fixture_command(
        job.job_dir,
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.write('no raw output written\\n'); sys.exit(0)",
        ],
    )

    record = run_cfd_job(job.job_dir)

    assert record.status == "failed"
    assert record.error_kind == "missing_output"
    assert FIXTURE_RAW_RESULT in (record.error_message or "")
    assert record.output_manifest is None
    assert not (job.job_dir / FIXTURE_RAW_RESULT).exists()
    assert load_run_record(job.job_dir / "run.json") == record


def test_fixture_malformed_raw_output_persists_failed_record(tmp_path: Path) -> None:
    job = _prepare_fixture_job(tmp_path)
    _set_fixture_command(
        job.job_dir,
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "Path('raw-result.json').write_text('{not fixture json'); "
                "print('wrote malformed raw output')"
            ),
        ],
    )

    record = run_cfd_job(job.job_dir)

    assert record.status == "failed"
    assert record.error_kind == "malformed_output"
    assert "malformed" in (record.error_message or "")
    assert record.output_manifest is None
    assert load_run_record(job.job_dir / "run.json") == record


def test_openfoam_missing_version_command_persists_unavailable_record(
    tmp_path: Path,
) -> None:
    job = _prepare_openfoam_job(tmp_path)
    missing_command = job.job_dir / "bin" / "missing-foamVersion"
    _set_openfoam_profile_fields(
        job.job_dir,
        solver_version_command=[str(missing_command)],
    )

    record = run_cfd_job(job.job_dir)

    assert record.status == "unavailable"
    assert record.error_kind == "solver_unavailable"
    assert "version command unavailable" in (record.error_message or "")
    assert str(missing_command) in record.error_message
    assert record.logs == {
        "version_stdout": "logs/version_stdout.log",
        "version_stderr": "logs/version_stderr.log",
    }
    assert record.result_semantics == "raw_unvalidated"
    assert load_run_record(job.job_dir / "run.json") == record


def test_openfoam_version_mismatch_persists_unavailable_record(tmp_path: Path) -> None:
    job = _prepare_openfoam_job(tmp_path)
    _set_openfoam_profile_fields(
        job.job_dir,
        solver_version_command=[
            sys.executable,
            "-c",
            "print('OpenFOAM-v2306')",
        ],
    )

    record = run_cfd_job(job.job_dir)

    assert record.status == "unavailable"
    assert record.error_kind == "version_mismatch"
    assert "required 'v2512'" in (record.error_message or "")
    assert record.raw_records["solver_version"] == "OpenFOAM-v2306"
    assert record.result_semantics == "raw_unvalidated"
    assert load_run_record(job.job_dir / "run.json") == record


def test_openfoam_nonzero_solver_command_persists_failed_record_and_capped_logs(
    tmp_path: Path,
) -> None:
    job = _prepare_openfoam_job(tmp_path)
    _set_openfoam_profile_fields(
        job.job_dir,
        solver_version_command=[
            sys.executable,
            "-c",
            "print('OpenFOAM-v2512')",
        ],
        command_template=[
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.stdout.write('x' * 120); "
                "sys.stderr.write('interFoam failed intentionally\\n'); "
                "sys.exit(6)"
            ),
        ],
        log_limit_bytes=40,
    )

    record = run_cfd_job(job.job_dir)

    assert record.status == "failed"
    assert record.error_kind == "command_failed"
    assert "exited with code 6" in (record.error_message or "")
    assert record.raw_records["returncode"] == 6
    assert record.raw_records["solver_version"] == "OpenFOAM-v2512"
    assert record.logs == {
        "version_stdout": "logs/version_stdout.log",
        "version_stderr": "logs/version_stderr.log",
        "stdout": "logs/stdout.log",
        "stderr": "logs/stderr.log",
    }
    assert "[truncated" in (job.job_dir / "logs" / "stdout.log").read_text()
    assert (
        job.job_dir / "logs" / "stderr.log"
    ).read_text() == "interFoam failed intentionally\n"
    assert load_run_record(job.job_dir / "run.json") == record


def test_openfoam_solver_timeout_persists_failed_record(tmp_path: Path) -> None:
    job = _prepare_openfoam_job(tmp_path)
    _set_openfoam_profile_fields(
        job.job_dir,
        solver_version_command=[
            sys.executable,
            "-c",
            "print('OpenFOAM-v2512')",
        ],
        command_template=[
            sys.executable,
            "-c",
            "import time; time.sleep(1)",
        ],
        timeout_seconds=0.05,
    )

    record = run_cfd_job(job.job_dir)

    assert record.status == "failed"
    assert record.error_kind == "timeout"
    assert "timed out" in (record.error_message or "")
    assert record.raw_records["solver_version"] == "OpenFOAM-v2512"
    assert record.result_semantics == "raw_unvalidated"
    assert load_run_record(job.job_dir / "run.json") == record


def test_openfoam_clean_command_with_missing_force_dat_persists_failed_record(
    tmp_path: Path,
) -> None:
    job = _prepare_openfoam_job(tmp_path)
    _set_openfoam_profile_fields(
        job.job_dir,
        solver_version_command=[
            sys.executable,
            "-c",
            "print('OpenFOAM-v2512')",
        ],
        command_template=[
            sys.executable,
            "-c",
            "print('fake interFoam completed without force output')",
        ],
    )

    record = run_cfd_job(job.job_dir)

    assert record.status == "failed"
    assert record.error_kind == "missing_output"
    assert OPENFOAM_FORCE_DAT_OUTPUT in (record.error_message or "")
    assert record.output_manifest is None
    assert record.raw_records["returncode"] == 0
    assert load_run_record(job.job_dir / "run.json") == record


def test_openfoam_malformed_force_dat_persists_failed_record(tmp_path: Path) -> None:
    job = _prepare_openfoam_job(tmp_path)
    _set_openfoam_profile_fields(
        job.job_dir,
        solver_version_command=[
            sys.executable,
            "-c",
            "print('OpenFOAM-v2512')",
        ],
        command_template=[
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "p=Path('case/openfoam/postProcessing/forces/0/force.dat'); "
                "p.parent.mkdir(parents=True, exist_ok=True); "
                "p.write_text('not enough numeric fields\\n')"
            ),
        ],
    )

    record = run_cfd_job(job.job_dir)

    assert record.status == "failed"
    assert record.error_kind == "malformed_output"
    assert "malformed" in (record.error_message or "")
    assert record.output_manifest is None
    assert load_run_record(job.job_dir / "run.json") == record


def test_openfoam_parser_readable_force_dat_does_not_enable_succeeded_path(
    tmp_path: Path,
) -> None:
    job = _prepare_openfoam_job(tmp_path)
    _set_openfoam_profile_fields(
        job.job_dir,
        solver_version_command=[
            sys.executable,
            "-c",
            "print('OpenFOAM-v2512')",
        ],
        command_template=[
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "p=Path('case/openfoam/postProcessing/forces/0/force.dat'); "
                "p.parent.mkdir(parents=True, exist_ok=True); "
                "p.write_text("
                "'# Force\\n"
                "# Time\\ttotal_x total_y total_z\\t"
                "pressure_x pressure_y pressure_z\\t"
                "viscous_x viscous_y viscous_z\\n"
                "0.0 3.5 0.0 0.0 1.0 0.0 0.0 2.5 0.0 0.0\\n'"
                "); "
                "print('fake interFoam completed')"
            ),
        ],
    )

    record = run_cfd_job(job.job_dir)

    assert record.status == "failed"
    assert record.error_kind == "solver_success_blocked"
    assert record.output_manifest == OPENFOAM_RAW_RESULT
    assert record.raw_records["drag_force_n"] == pytest.approx(3.5)
    assert record.raw_records["claim_state"] == "raw_unvalidated"
    assert record.raw_records["accepted_uses"] == []
    assert OPENFOAM_WARNING_FRAGMENT in _fixture_warning_text(record.raw_records)
    assert load_run_record(job.job_dir / "run.json") == record


def test_openfoam_rerun_ignores_stale_force_dat_and_raw_result(
    tmp_path: Path,
) -> None:
    job = _prepare_openfoam_job(tmp_path)
    _set_openfoam_profile_fields(
        job.job_dir,
        solver_version_command=[
            sys.executable,
            "-c",
            "print('OpenFOAM-v2512')",
        ],
        command_template=[
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "p=Path('case/openfoam/postProcessing/forces/0/force.dat'); "
                "p.parent.mkdir(parents=True, exist_ok=True); "
                "p.write_text("
                "'# Force\\n"
                "# Time\\ttotal_x total_y total_z\\t"
                "pressure_x pressure_y pressure_z\\t"
                "viscous_x viscous_y viscous_z\\n"
                "0.0 3.5 0.0 0.0 1.0 0.0 0.0 2.5 0.0 0.0\\n'"
                "); "
                "print('first fake interFoam completed')"
            ),
        ],
    )

    first = run_cfd_job(job.job_dir)

    assert first.status == "failed"
    assert first.error_kind == "solver_success_blocked"
    assert first.output_manifest == OPENFOAM_RAW_RESULT
    assert first.raw_records["drag_force_n"] == pytest.approx(3.5)
    assert (job.job_dir / OPENFOAM_RAW_RESULT).is_file()

    _set_openfoam_profile_fields(
        job.job_dir,
        command_template=[
            sys.executable,
            "-c",
            "print('second fake interFoam completed without force output')",
        ],
    )

    second = run_cfd_job(job.job_dir)

    assert second.status == "failed"
    assert second.error_kind == "missing_output"
    assert second.output_manifest is None
    assert "drag_force_n" not in second.raw_records
    assert not (job.job_dir / OPENFOAM_RAW_RESULT).exists()
    force_path = job.job_dir / OPENFOAM_CASE_ROOT / OPENFOAM_FORCE_DAT_OUTPUT
    assert not force_path.exists()
    assert load_run_record(job.job_dir / "run.json") == second


def test_openfoam_force_dat_parser_reads_checked_in_fixture() -> None:
    parsed = parse_openfoam_force_dat(
        OPENFOAM_FORCE_FIXTURE,
        source_ref="fixtures/openfoam/force.dat",
    )

    assert parsed.source_ref == "fixtures/openfoam/force.dat"
    assert parsed.sample_count == 3
    assert parsed.last_sample.time_s == pytest.approx(1.0)
    assert parsed.last_sample.pressure_force_n == pytest.approx((3.0, 0.0, 0.0))
    assert parsed.last_sample.viscous_force_n == pytest.approx((1.25, 0.0, 0.0))
    assert parsed.last_sample.porous_force_n == pytest.approx((0.0, 0.0, 0.0))
    assert parsed.last_sample.total_force_n == pytest.approx((4.25, 0.0, 0.0))
    assert parsed.last_sample.drag_force_n == pytest.approx(4.25)
    assert parsed.claim_state == "raw_unvalidated"
    assert parsed.accepted_uses == []


def test_openfoam_force_dat_parser_rejects_malformed_fixture(tmp_path: Path) -> None:
    malformed = tmp_path / "force.dat"
    malformed.write_text("# no samples\n")

    with pytest.raises(CfdDispatchError) as excinfo:
        parse_openfoam_force_dat(malformed)

    assert excinfo.value.code == "malformed_output"


def test_openfoam_raw_models_reject_validated_or_calibrated_promotion() -> None:
    sample = CfdOpenFoamForceDatSample(
        time_s=1.0,
        pressure_force_n=(1.0, 0.0, 0.0),
        viscous_force_n=(2.0, 0.0, 0.0),
        porous_force_n=(0.0, 0.0, 0.0),
        total_force_n=(3.0, 0.0, 0.0),
        drag_force_n=3.0,
    )

    with pytest.raises(ValidationError, match="accepted uses"):
        CfdOpenFoamForceDatResult(
            source_ref="force.dat",
            sample_count=1,
            last_sample=sample,
            accepted_uses=["final_prediction"],
        )

    with pytest.raises(ValidationError, match="raw_unvalidated"):
        CfdOpenFoamRawResult(
            job_id="cfd-openfoam",
            solver_name="OpenFOAM.com OpenFOAM-v2512 interFoam",
            solver_version="OpenFOAM-v2512",
            speed_mps=2.4,
            seawater_density_kg_m3=1025.0,
            kinematic_viscosity_m2_s=1.19e-6,
            mesh_profile="watertight_solid_resistance_v1",
            mesh_readiness="cfd_ready",
            drag_force_n=3.0,
            raw_output_refs=["postProcessing/forces/0/force.dat"],
            command=["interFoam", "-case", "case/openfoam"],
            version_command=["foamVersion"],
            returncode=0,
            claim_state="calibrated_model",
        )
