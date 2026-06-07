"""CLI surface checks."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.contract import LoadCase, LongitudinalLoadComponent
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.model.hull import Hull
from kayakgen.model.validity import CODE_L_BWL_LOW
from kayakgen.search.pareto import SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN
from kayakgen.search.sweep import SweepSpec, run_sweep
from kayakgen.services.artifact_store import FilesystemArtifactStore

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


def test_sweep_resume_reports_pending_count(tmp_path) -> None:
    sweep = tmp_path / "sweep.json"
    out = tmp_path / "out"
    sweep.write_text(
        """
{
  "schema_version": "1",
  "name": "cli-pending",
  "base_hull": {"beam_oa_m": 0.60},
  "variables": {
    "beam_wl_m": {"kind": "values", "values": [0.50]}
  },
  "evaluators": {"hydrostatics": true, "resistance": false, "mesh_diagnostics": false, "stl": false}
}
""".strip()
    )
    runner = CliRunner()
    first = runner.invoke(app, ["sweep", str(sweep), "--out", str(out)])
    assert first.exit_code == 0
    run_dir = out / "candidates"
    record_path = next(run_dir.glob("*.record.json"))
    record = json.loads(record_path.read_text())
    record["status"] = "pending"
    record_path.write_text(json.dumps(record, indent=2))

    result = runner.invoke(app, ["sweep", str(sweep), "--out", str(out), "--resume"])

    assert result.exit_code == 0
    assert "1 pending" in result.stdout


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


def _stage_gated_compare_run(run_dir) -> None:
    """Stage a sweep run whose candidates carry the gated Rt_N_last metric.

    Mirrors the function-level fixture in tests/test_compare.py
    (test_raw_resistance_objective_without_opt_in_is_refused): the
    raw_unvalidated resistance metric is planted in candidate summaries so
    an explicit ``-o Rt_N_last:min`` objective trips the RFC 0044 gate.
    """
    spec = SweepSpec(
        name="cli-compare-gated",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}},
    )
    run = run_sweep(spec, run_dir)
    for index, record in enumerate(run.candidates):
        record.summary["Rt_N_last"] = float(10 + index)
        record.summary["resistance_use"] = "comparative_filter"
    FilesystemArtifactStore(
        run_dir,
        run_id=f"sweep-{run.spec_hash[:16]}-{run_dir.name}",
    ).put_json("sweep_run_record", run, canonical_path=run_dir / "run.json")


def test_compare_gated_objective_without_opt_in_refuses_at_cli(tmp_path) -> None:
    """Audit G3 / D048: the CLI wiring of the RFC 0044 refusal.

    All prior refusal coverage was function-level (build_comparison_report);
    the CLI's broad ``try/except -> exit 1`` wrapper meant a wiring
    regression (flag dropped, token swallowed) would never be caught. This
    pins: gated objective without --explicit-exploratory -> exit code 1
    with the RFC 0044 token surfaced in the CLI error output."""

    run_dir = tmp_path / "run"
    _stage_gated_compare_run(run_dir)
    report = tmp_path / "comparison.json"

    result = CliRunner().invoke(
        app,
        ["compare", str(run_dir), "--out", str(report), "-o", "Rt_N_last:min"],
    )

    assert result.exit_code == 1, result.output
    assert SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN in result.stderr
    # refusal happens before the report is written
    assert not report.exists()


def test_compare_gated_objective_with_opt_in_writes_exploratory_report(
    tmp_path,
) -> None:
    """Audit G3 / D048: the opt-in half of the CLI pair — same gated
    objective WITH --explicit-exploratory -> exit 0 and the written report
    is labeled exploratory_frontier."""

    run_dir = tmp_path / "run"
    _stage_gated_compare_run(run_dir)
    report = tmp_path / "comparison.json"

    result = CliRunner().invoke(
        app,
        [
            "compare",
            str(run_dir),
            "--out",
            str(report),
            "-o",
            "Rt_N_last:min",
            "--explicit-exploratory",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(report.read_text())
    assert payload["report_kind"] == "exploratory_frontier"


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


def test_generate_accepts_independent_stern_rake_json(tmp_path) -> None:
    hull = tmp_path / "mixed_rake.json"
    hull.write_text(
        json.dumps(
            {
                "beam_oa_m": 0.58,
                "beam_wl_m": 0.50,
                "bow_rake": 0.0,
                "stern_rake": 1.0,
            }
        )
    )
    out = tmp_path / "mixed_rake"

    result = CliRunner().invoke(app, ["generate", str(hull), "--stl-out", str(out)])

    assert result.exit_code == 0
    assert (tmp_path / "mixed_rake_hull.stl").stat().st_size > 0
    assert (tmp_path / "mixed_rake_deck.stl").stat().st_size > 0


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
    assert data["design_validity"]["schema_version"] == "1"
    assert isinstance(data["design_validity"]["findings"], list)


def test_evaluate_json_includes_design_validity_for_valid_hulls(tmp_path) -> None:
    hull_model = Hull(length_m=4.0, beam_oa_m=0.70, beam_wl_m=0.65)
    hull = tmp_path / "advisory.json"
    out = tmp_path / "advisory.eval.json"
    hull.write_text(hull_model.model_dump_json())

    result = CliRunner().invoke(
        app,
        ["evaluate", str(hull), "--skip-resistance", "--out", str(out)],
    )

    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert data["design_validity"]["warning_count"] == 1
    assert data["design_validity"]["findings"][0]["code"] == CODE_L_BWL_LOW
    assert data["design_validity"]["findings"][0]["surface"] == ["cli"]


def test_evaluate_still_rejects_invalid_beam_wl(tmp_path) -> None:
    hull = tmp_path / "invalid.json"
    out = tmp_path / "invalid.eval.json"
    hull.write_text(json.dumps({"beam_oa_m": 0.55, "beam_wl_m": 0.60}))

    result = CliRunner().invoke(
        app,
        ["evaluate", str(hull), "--skip-resistance", "--out", str(out)],
    )

    assert result.exit_code != 0
    assert not out.exists()


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
    assert "readiness: cfd_surface_candidate" in result.stdout
    assert "readiness_blocker: not_watertight_profile" in result.stdout
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
    assert "readiness_blocker: missing_volume_mesh" in result.stdout
    assert "readiness_blocker: readiness_below_cfd_ready" in result.stdout
    assert "readiness_reason:" in result.stdout
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["solver_profile"]["profile_name"] == "watertight_solid_resistance_v1"
    assert manifest["readiness"]["level"] == "stl_surface"
    assert any("separate open surfaces" in warning for warning in manifest["warnings"])


def test_mesh_package_mixed_rake_stays_below_cfd_ready(tmp_path) -> None:
    hull = tmp_path / "mixed_rake.json"
    hull.write_text(Hull(bow_rake=0.0, stern_rake=1.0).model_dump_json())
    out = tmp_path / "mesh-package"

    result = CliRunner().invoke(app, ["mesh-package", str(hull), "--out", str(out)])

    assert result.exit_code == 0
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["hull_json"] == "hull.json"
    assert manifest["readiness"]["level"] == "cfd_surface_candidate"
    assert manifest["readiness"]["level"] != "cfd_ready"


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
    assert "blocker_class: missing_volume_mesh" in result.stderr
    assert "readiness stl_surface is below required cfd_ready" in result.stderr


def test_stability_writes_initial_result(tmp_path) -> None:
    hull = tmp_path / "hull.json"
    hull.write_text(Hull().model_dump_json())
    out = tmp_path / "stability.json"
    result = CliRunner().invoke(app, ["stability", str(hull), "--out", str(out)])
    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert data["method"] == "design_waterline_initial"
    assert data["gz_curve"] is None
    assert "high_angle_gz_not_implemented" in data["warnings"]
    forbidden = {
        "max_gz_m",
        "heel_at_max_gz_deg",
        "righting_moment_nm",
        "range_positive_stability_deg",
        "area_under_positive_gz_m_deg",
    }
    assert forbidden.isdisjoint(data)


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
