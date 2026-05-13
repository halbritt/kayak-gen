"""CLI surface checks."""

from __future__ import annotations

from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.model.hull import Hull


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


def test_stability_writes_initial_result(tmp_path) -> None:
    hull = tmp_path / "hull.json"
    hull.write_text(Hull().model_dump_json())
    out = tmp_path / "stability.json"
    result = CliRunner().invoke(app, ["stability", str(hull), "--out", str(out)])
    assert result.exit_code == 0
    assert "design_waterline_initial" in out.read_text()
