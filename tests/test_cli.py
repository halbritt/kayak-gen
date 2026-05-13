"""CLI surface checks."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.contract import LoadCase, LongitudinalLoadComponent
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.model.hull import Hull

FIXTURE_PROFILE_NAME = "fixture-local-command"
FIXTURE_WARNING_FRAGMENT = "not calibrated, validated, or final design fitness"


def test_sweep_runs_json_spec(tmp_path) -> None:
    sweep = tmp_path / "sweep.json"
    sweep.write_text(
        """
{
  "schema_version": "1",
  "name": "cli-smoke",
  "base_hull": {"beam_oa_m": 0.60},
  "variables": {
    "beam_wl_m": {"kind": "values", "values": [0.50]}
  },
  "evaluators": {"hydrostatics": true, "resistance": false, "mesh_diagnostics": false, "stl": false}
}
""".strip()
    )
    result = CliRunner().invoke(app, ["sweep", str(sweep), "--out", str(tmp_path / "out")])
    assert result.exit_code == 0
    assert "1 complete" in result.stdout
    assert (tmp_path / "out" / "run.json").exists()


def test_compare_writes_report_for_sweep_run(tmp_path) -> None:
    sweep = tmp_path / "sweep.json"
    run_dir = tmp_path / "run"
    report = tmp_path / "comparison.json"
    sweep.write_text(
        """
{
  "schema_version": "1",
  "name": "cli-compare",
  "base_hull": {"beam_oa_m": 0.60},
  "variables": {
    "beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}
  },
  "evaluators": {"hydrostatics": true, "resistance": false, "mesh_diagnostics": false, "stl": false}
}
""".strip()
    )
    runner = CliRunner()
    sweep_result = runner.invoke(app, ["sweep", str(sweep), "--out", str(run_dir)])
    assert sweep_result.exit_code == 0

    compare_result = runner.invoke(app, ["compare", str(run_dir), "--out", str(report)])

    assert compare_result.exit_code == 0
    assert "pareto candidates" in compare_result.stdout
    assert "\"report_kind\": \"pareto_frontier\"" in report.read_text()


def test_compare_fails_for_directory_without_run_record(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        ["compare", str(tmp_path), "--out", str(tmp_path / "comparison.json")],
    )

    assert result.exit_code == 1
    assert "missing sweep run record" in result.stderr


def test_mesh_check_writes_diagnostics(tmp_path) -> None:
    hull = tmp_path / "hull.json"
    hull.write_text(Hull().model_dump_json())
    out = tmp_path / "mesh.json"
    result = CliRunner().invoke(app, ["mesh-check", str(hull), "--out", str(out)])
    assert result.exit_code == 0
    assert "stl_surface" in out.read_text()


def test_generate_accepts_non_default_bow_rake_and_beam_wl(tmp_path) -> None:
    hull = tmp_path / "non_default.json"
    hull_model = Hull(beam_oa_m=0.58, beam_wl_m=0.50, bow_rake=0.0)
    hull.write_text(hull_model.model_dump_json())
    out = tmp_path / "non_default"

    result = CliRunner().invoke(app, ["generate", str(hull), "--stl-out", str(out)])

    assert result.exit_code == 0
    assert (tmp_path / "non_default_hull.stl").stat().st_size > 0
    assert (tmp_path / "non_default_deck.stl").stat().st_size > 0


def test_evaluate_accepts_non_default_bow_rake_and_beam_wl(tmp_path) -> None:
    hull_model = Hull(beam_oa_m=0.58, beam_wl_m=0.50, bow_rake=0.0)
    hull = tmp_path / "non_default.json"
    out = tmp_path / "non_default.eval.json"
    hull.write_text(hull_model.model_dump_json())

    result = CliRunner().invoke(
        app,
        ["evaluate", str(hull), "--skip-resistance", "--out", str(out)],
    )

    assert result.exit_code == 0
    assert "uncalibrated/comparative" not in result.stdout
    data = json.loads(out.read_text())
    expected = evaluate_hydrostatics(hull_model)
    assert data["resistance"] is None
    assert data["hydrostatics"]["displaced_volume_m3"] == pytest.approx(
        expected.displaced_volume_m3
    )
    assert data["hydrostatics"]["waterplane_area_m2"] == pytest.approx(
        expected.waterplane_area_m2
    )


def test_evaluate_with_resistance_prints_claim_warning(tmp_path) -> None:
    hull = tmp_path / "hull.json"
    out = tmp_path / "hull.eval.json"
    hull.write_text(Hull().model_dump_json())

    result = CliRunner().invoke(app, ["evaluate", str(hull), "--out", str(out)])

    assert result.exit_code == 0
    assert "Resistance is uncalibrated/comparative only; see metadata." in result.stdout
    data = json.loads(out.read_text())
    assert data["resistance"]["metadata"]["claim_state"] == "uncalibrated_comparative"
    assert "not_final_performance_prediction" in data["resistance"]["metadata"]["warnings"]


def test_mesh_package_writes_manifest_and_artifacts(tmp_path) -> None:
    hull = tmp_path / "hull.json"
    hull.write_text(Hull().model_dump_json())
    out = tmp_path / "mesh-package"

    result = CliRunner().invoke(app, ["mesh-package", str(hull), "--out", str(out)])

    assert result.exit_code == 0
    assert "cfd_surface_candidate" in result.stdout
    assert (out / "manifest.json").exists()
    assert (out / "quality.hull.json").exists()
    assert (out / "quality.deck.json").exists()
    assert (out / "hull.stl").exists()
    assert (out / "deck.stl").exists()


def test_mesh_package_can_select_watertight_profile_without_cfd_ready(tmp_path) -> None:
    hull = tmp_path / "hull.json"
    hull.write_text(Hull().model_dump_json())
    out = tmp_path / "mesh-package"

    result = CliRunner().invoke(
        app,
        [
            "mesh-package",
            str(hull),
            "--out",
            str(out),
            "--solver-profile",
            "watertight-solid",
        ],
    )

    assert result.exit_code == 0
    assert "stl_surface" in result.stdout
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["solver_profile"]["profile_name"] == "watertight_solid_resistance_v1"
    assert manifest["readiness"]["level"] == "stl_surface"
    assert any("separate open surfaces" in warning for warning in manifest["warnings"])


def test_cfd_prepare_status_and_unavailable_run(tmp_path) -> None:
    hull = tmp_path / "hull.json"
    hull.write_text(Hull().model_dump_json())
    mesh_package = tmp_path / "mesh-package"
    jobs = tmp_path / "jobs"
    runner = CliRunner()
    mesh_result = runner.invoke(app, ["mesh-package", str(hull), "--out", str(mesh_package)])
    assert mesh_result.exit_code == 0

    prepare_result = runner.invoke(
        app,
        [
            "cfd",
            "prepare",
            "--mesh-package",
            str(mesh_package),
            "--out",
            str(jobs),
            "--speed-mps",
            "2.5",
        ],
    )
    assert prepare_result.exit_code == 0
    assert "status: queued" in prepare_result.stdout
    assert "raw and unvalidated" in prepare_result.stdout
    job_dir = next(path for path in jobs.iterdir() if path.is_dir())

    status_result = runner.invoke(app, ["cfd", "status", str(job_dir)])
    assert status_result.exit_code == 0
    assert "status: queued" in status_result.stdout
    assert "unavailable-open-wetted-surface" in status_result.stdout

    run_result = runner.invoke(app, ["cfd", "run", str(job_dir)])
    assert run_result.exit_code == 0
    assert "status: unavailable" in run_result.stdout
    assert "error_kind: solver_unavailable" in run_result.stdout
    run_record = json.loads((job_dir / "run.json").read_text())
    assert run_record["status"] == "unavailable"


def test_cfd_profiles_lists_fixture_local_command() -> None:
    result = CliRunner().invoke(app, ["cfd", "profiles"])

    assert result.exit_code == 0
    assert FIXTURE_PROFILE_NAME in result.stdout.splitlines()


def test_cfd_fixture_run_and_status_keep_raw_warning_visible(tmp_path) -> None:
    hull = tmp_path / "hull.json"
    hull.write_text(Hull().model_dump_json())
    mesh_package = tmp_path / "mesh-package"
    jobs = tmp_path / "jobs"
    runner = CliRunner()
    mesh_result = runner.invoke(app, ["mesh-package", str(hull), "--out", str(mesh_package)])
    assert mesh_result.exit_code == 0

    prepare_result = runner.invoke(
        app,
        [
            "cfd",
            "prepare",
            "--mesh-package",
            str(mesh_package),
            "--solver-profile",
            FIXTURE_PROFILE_NAME,
            "--out",
            str(jobs),
            "--speed-mps",
            "2.5",
        ],
    )
    assert prepare_result.exit_code == 0
    assert "raw and unvalidated" in prepare_result.stdout
    job_dir = next(path for path in jobs.iterdir() if path.is_dir())

    run_result = runner.invoke(app, ["cfd", "run", str(job_dir)])
    assert run_result.exit_code == 0
    assert "status: succeeded" in run_result.stdout
    assert "raw and unvalidated" in run_result.stdout
    assert FIXTURE_WARNING_FRAGMENT in run_result.stdout

    status_result = runner.invoke(app, ["cfd", "status", str(job_dir)])
    assert status_result.exit_code == 0
    assert "status: succeeded" in status_result.stdout
    assert f"solver_profile: {FIXTURE_PROFILE_NAME}" in status_result.stdout
    assert "raw and unvalidated" in status_result.stdout
    assert FIXTURE_WARNING_FRAGMENT in status_result.stdout

    run_record = json.loads((job_dir / "run.json").read_text())
    assert run_record["status"] == "succeeded"
    assert run_record["result_semantics"] == "raw_unvalidated"
    assert FIXTURE_WARNING_FRAGMENT in " ".join(run_record["raw_records"]["warnings"])


def test_cfd_prepare_rejects_watertight_solver_for_current_package(tmp_path) -> None:
    hull = tmp_path / "hull.json"
    hull.write_text(Hull().model_dump_json())
    mesh_package = tmp_path / "mesh-package"
    jobs = tmp_path / "jobs"
    runner = CliRunner()
    mesh_result = runner.invoke(
        app,
        [
            "mesh-package",
            str(hull),
            "--out",
            str(mesh_package),
            "--solver-profile",
            "watertight-solid",
        ],
    )
    assert mesh_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "cfd",
            "prepare",
            "--mesh-package",
            str(mesh_package),
            "--solver-profile",
            "unavailable-watertight-solid",
            "--out",
            str(jobs),
            "--speed-mps",
            "2.5",
        ],
    )

    assert result.exit_code == 1
    assert "readiness stl_surface is below required cfd_ready" in result.stderr


def test_stability_writes_initial_result(tmp_path) -> None:
    hull = tmp_path / "hull.json"
    hull.write_text(Hull().model_dump_json())
    out = tmp_path / "stability.json"
    result = CliRunner().invoke(app, ["stability", str(hull), "--out", str(out)])
    assert result.exit_code == 0
    assert "design_waterline_initial" in out.read_text()


def test_stability_equilibrium_flag_writes_equilibrium_result(tmp_path) -> None:
    hull_model = Hull(draft_m=0.12)
    target_draft_m = 0.135
    hydro = evaluate_hydrostatics(hull_model.model_copy(update={"draft_m": target_draft_m}))
    load_model = LoadCase(
        paddler_mass_kg=hydro.displaced_volume_m3 * 1025.0 - 18.0,
        hull_mass_kg=18.0,
        cargo_mass_kg=0.0,
    )
    hull = tmp_path / "hull.json"
    load = tmp_path / "load.json"
    out = tmp_path / "stability.json"
    hull.write_text(hull_model.model_dump_json())
    load.write_text(load_model.model_dump_json())

    result = CliRunner().invoke(
        app,
        [
            "stability",
            str(hull),
            "--load-case",
            str(load),
            "--equilibrium",
            "--tolerance-kg",
            "0.05",
            "--max-iterations",
            "80",
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert data["method"] == "equilibrium_sinkage"
    assert data["status"] == "converged"
    assert data["equilibrium_draft_m"] == pytest.approx(target_draft_m, abs=5e-4)
    assert abs(data["displacement_error_kg"]) <= 0.05
    assert data["draft_at_midship_m"] == pytest.approx(data["equilibrium_draft_m"])
    assert data["load_lcg_m"] == pytest.approx(0.0)
    assert data["moment_error_kg_m"] == pytest.approx(0.0)


def test_stability_equilibrium_writes_component_trim_fields(tmp_path) -> None:
    hull_model = Hull()
    load_model = LoadCase(
        components=[
            LongitudinalLoadComponent(
                name="test-load",
                mass_kg=90.0,
                x_m=-0.30,
                kg_above_keel_m=0.25,
            )
        ]
    )
    hull = tmp_path / "hull.json"
    load = tmp_path / "load.json"
    out = tmp_path / "stability.json"
    hull.write_text(hull_model.model_dump_json())
    load.write_text(load_model.model_dump_json())

    result = CliRunner().invoke(
        app,
        [
            "stability",
            str(hull),
            "--load-case",
            str(load),
            "--equilibrium",
            "--tolerance-kg",
            "0.2",
            "--moment-tolerance-kg-m",
            "0.2",
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert data["method"] == "equilibrium_trim"
    assert data["status"] == "converged"
    assert data["trim_angle_deg"] < 0.0
    assert data["load_lcg_m"] == pytest.approx(-0.30)
    assert data["buoyancy_lcb_m"] == pytest.approx(data["load_lcg_m"], abs=3e-3)
    assert abs(data["displacement_error_kg"]) <= 0.2
    assert abs(data["moment_error_kg_m"]) <= data["moment_tolerance_kg_m"]
