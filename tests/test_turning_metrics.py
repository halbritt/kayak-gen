"""Tests for the RFC 0053 turning and edged-waterline metrics."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.contract import EvaluationResult
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.turning import TurningMetrics, evaluate_turning_metrics
from kayakgen.model.hull import Hull
from kayakgen.search.objectives import (
    OBJECTIVE_METADATA,
    OBJECTIVE_REJECTION_DISPLAY_ONLY,
    is_objective_metric_admissible,
)
from kayakgen.search.sweep import SweepSpec, run_sweep

TURNING_METRIC_KEYS = (
    "turning.edged_waterline_length_m",
    "turning.upright_waterline_length_m",
    "turning.lateral_plane_shift_m",
    "turning.rocker_weighted_maneuverability_signal",
)


def test_symmetric_hull_at_zero_heel_matches_upright_waterline_length() -> None:
    hull = Hull()
    metrics = evaluate_turning_metrics(hull, heel_deg=0.0)
    assert metrics.heel_deg == 0.0
    assert metrics.method == "geometric_proxy_v1"
    assert metrics.upright_waterline_length_m > 0.0
    assert metrics.edged_waterline_length_m == pytest.approx(
        metrics.upright_waterline_length_m, abs=1e-9
    )


def test_edged_waterline_length_non_increasing_with_heel() -> None:
    hull = Hull()
    lengths = []
    for heel in (0.0, 5.0, 10.0, 15.0, 20.0):
        metrics = evaluate_turning_metrics(hull, heel_deg=heel)
        lengths.append(metrics.edged_waterline_length_m)
    # Edged waterline length must not *increase* as heel increases.
    for prev, nxt in zip(lengths, lengths[1:]):
        assert nxt <= prev + 1e-9, (
            f"edged waterline length increased with heel: {lengths!r}"
        )


def test_zero_heel_lateral_plane_shift_is_zero_by_symmetry() -> None:
    hull = Hull()
    metrics = evaluate_turning_metrics(hull, heel_deg=0.0)
    assert metrics.lateral_plane_shift_m == pytest.approx(0.0, abs=1e-9)


def test_turning_metrics_schema_round_trip() -> None:
    metrics = evaluate_turning_metrics(Hull(), heel_deg=8.0)
    payload = metrics.model_dump_json()
    rebuilt = TurningMetrics.model_validate_json(payload)
    assert rebuilt == metrics
    assert rebuilt.schema_version == "1"
    assert rebuilt.method == "geometric_proxy_v1"


def test_evaluation_result_round_trips_with_turning_metrics() -> None:
    hull = Hull()
    hydro = evaluate_hydrostatics(hull)
    metrics = evaluate_turning_metrics(hull, heel_deg=8.0)
    result = EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=hydro,
        turning_metrics=metrics,
    )
    rebuilt = EvaluationResult.model_validate_json(result.model_dump_json())
    assert rebuilt.turning_metrics is not None
    assert rebuilt.turning_metrics.edged_waterline_length_m == pytest.approx(
        metrics.edged_waterline_length_m
    )


def test_cli_evaluate_turning_writes_block(tmp_path: Path) -> None:
    hull_path = tmp_path / "hull.json"
    hull_path.write_text(Hull().model_dump_json())
    out = tmp_path / "with_turning.eval.json"
    result = CliRunner().invoke(
        app,
        [
            "evaluate",
            str(hull_path),
            "--skip-resistance",
            "--turning",
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(out.read_text())
    assert payload.get("turning_metrics") is not None
    block = payload["turning_metrics"]
    assert block["method"] == "geometric_proxy_v1"
    assert block["heel_deg"] == pytest.approx(8.0)
    for key in (
        "edged_waterline_length_m",
        "upright_waterline_length_m",
        "lateral_plane_shift_m",
        "rocker_weighted_maneuverability_signal",
    ):
        assert key in block


def test_cli_evaluate_default_omits_turning_block(tmp_path: Path) -> None:
    hull_path = tmp_path / "hull.json"
    hull_path.write_text(Hull().model_dump_json())
    out = tmp_path / "default.eval.json"
    result = CliRunner().invoke(
        app,
        ["evaluate", str(hull_path), "--skip-resistance", "--out", str(out)],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(out.read_text())
    assert payload.get("turning_metrics") is None


def test_cli_evaluate_turning_heel_override(tmp_path: Path) -> None:
    hull_path = tmp_path / "hull.json"
    hull_path.write_text(Hull().model_dump_json())
    out = tmp_path / "heel.eval.json"
    result = CliRunner().invoke(
        app,
        [
            "evaluate",
            str(hull_path),
            "--skip-resistance",
            "--turning",
            "--turning-heel-deg",
            "15",
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(out.read_text())
    assert payload["turning_metrics"]["heel_deg"] == pytest.approx(15.0)


def test_sweep_with_turning_metrics_writes_numeric_columns(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="turning",
        base_hull={"beam_oa_m": 0.60},
        variables={
            "beam_wl_m": {"kind": "values", "values": [0.50, 0.55]},
        },
        evaluators={
            "hydrostatics": True,
            "resistance": False,
            "stl": False,
            "turning_metrics": True,
            "turning_metrics_heel_deg": 10.0,
        },
    )
    run = run_sweep(spec, tmp_path)
    assert run.completed_count == 2
    header = (tmp_path / "summary.csv").read_text().splitlines()[0]
    for key in TURNING_METRIC_KEYS:
        assert key in header
    for record in run.candidates:
        for key in TURNING_METRIC_KEYS:
            assert key in record.summary
        # Surface only the numeric outputs -- no embedded record.
        assert "turning_metrics" not in record.summary


def test_sweep_default_excludes_turning_columns(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="no-turning",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50]}},
    )
    run = run_sweep(spec, tmp_path)
    header = (tmp_path / "summary.csv").read_text().splitlines()[0]
    for key in TURNING_METRIC_KEYS:
        assert key not in header
    for record in run.candidates:
        for key in TURNING_METRIC_KEYS:
            assert key not in record.summary


@pytest.mark.parametrize("metric", TURNING_METRIC_KEYS)
def test_turning_metrics_refused_as_pareto_or_search_objectives(metric: str) -> None:
    assert metric in OBJECTIVE_METADATA
    assert OBJECTIVE_METADATA[metric].role == "display_only"
    admissible, reason = is_objective_metric_admissible(
        metric, explicit_exploratory=False
    )
    assert admissible is False
    assert reason is not None
    assert reason["code"] == OBJECTIVE_REJECTION_DISPLAY_ONLY
    # Even the exploratory opt-in cannot promote a display-only metric.
    admissible_exploratory, reason_exploratory = is_objective_metric_admissible(
        metric, explicit_exploratory=True
    )
    assert admissible_exploratory is False
    assert reason_exploratory is not None
    assert reason_exploratory["code"] == OBJECTIVE_REJECTION_DISPLAY_ONLY
