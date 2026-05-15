"""RFC 0044 ``kayakgen search`` CLI surface."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from kayakgen.cli.main import app


def _spec_text() -> str:
    return json.dumps(
        {
            "schema_version": "1",
            "name": "cli-search-tiny",
            "base_hull": {
                "length_m": 4.5,
                "beam_oa_m": 0.55,
                "draft_m": 0.12,
                "Cp": 0.55,
            },
            "search_space": {
                "beam_wl_m": {"kind": "uniform", "min": 0.46, "max": 0.54}
            },
            "algorithm": {
                "kind": "nsga2",
                "population_size": 4,
                "generations": 2,
                "seed": 7,
            },
            "objectives": [
                {"metric": "GM0_m", "direction": "max"},
                {"metric": "displaced_mass_kg", "direction": "min"},
            ],
            "evaluators": {"hydrostatics": True},
            "constraints": [],
            "budget": {"max_evaluations": 16},
        }
    )


def test_cli_search_invokes_runner_and_prints_banner(tmp_path: Path) -> None:
    spec_path = tmp_path / "search.json"
    spec_path.write_text(_spec_text())
    out = tmp_path / "run"

    result = CliRunner().invoke(
        app, ["search", str(spec_path), "--out", str(out)]
    )
    assert result.exit_code == 0, result.stdout
    assert "search: cli-search-tiny" in result.stdout
    assert "seed=7" in result.stdout
    assert "objectives:" in result.stdout
    assert "GM0_m:max" in result.stdout
    assert "displaced_mass_kg:min" in result.stdout
    assert "budget_max_evaluations: 16" in result.stdout
    assert (out / "run.json").exists()


def test_cli_search_skip_resume_flag_default(tmp_path: Path) -> None:
    spec_path = tmp_path / "search.json"
    spec_path.write_text(_spec_text())
    out = tmp_path / "run"
    # The default invocation never passes --resume; the runner is exercised
    # in non-resume mode and must succeed without a state.json checkpoint.
    result = CliRunner().invoke(
        app, ["search", str(spec_path), "--out", str(out)]
    )
    assert result.exit_code == 0
    payload = json.loads((out / "run.json").read_text())
    assert payload["name"] == "cli-search-tiny"
    assert payload["search_class"] == "conservative"


def test_cli_search_exploratory_banner(tmp_path: Path) -> None:
    payload = json.loads(_spec_text())
    payload["objectives_explicit_exploratory"] = True
    spec_path = tmp_path / "search.json"
    spec_path.write_text(json.dumps(payload))
    out = tmp_path / "run"

    result = CliRunner().invoke(
        app, ["search", str(spec_path), "--out", str(out)]
    )
    assert result.exit_code == 0
    assert "exploratory" in result.stdout
    run_json = json.loads((out / "run.json").read_text())
    assert run_json["search_class"] == "exploratory"


def test_default_sweep_and_compare_behavior_unchanged_when_search_module_imported(
    tmp_path: Path,
) -> None:
    # Importing the active-search module must not perturb the sweep CLI's
    # default output. We exercise the public CLI here as a smoke check.
    import kayakgen.search.active  # noqa: F401  (load it before sweep)

    sweep_path = tmp_path / "sweep.json"
    sweep_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "name": "cli-sweep-after-search-import",
                "base_hull": {"beam_oa_m": 0.60},
                "variables": {
                    "beam_wl_m": {"kind": "values", "values": [0.50]}
                },
                "evaluators": {
                    "hydrostatics": True,
                    "resistance": False,
                    "mesh_diagnostics": False,
                    "stl": False,
                },
            }
        )
    )
    out = tmp_path / "out"
    result = CliRunner().invoke(
        app, ["sweep", str(sweep_path), "--out", str(out)]
    )
    assert result.exit_code == 0
    assert "1 complete" in result.stdout
    assert (out / "run.json").exists()
