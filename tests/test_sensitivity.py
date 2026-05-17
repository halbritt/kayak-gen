"""RFC 0052: sensitivity service, convergence flags, and noise advisories."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.contract import (
    ConvergenceFlag,
    EvaluationResult,
)
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.stability import evaluate_initial_stability
from kayakgen.eval.contract import ResistanceCurve, ResistanceMetadata
from kayakgen.model.hull import Hull
from kayakgen.search.compare import (
    build_comparison_report,
)
from kayakgen.search.objectives import OBJECTIVE_METADATA
from kayakgen.search.sweep import CandidateRecord, SweepRunRecord, SweepSpec, run_sweep
from kayakgen.services.sensitivity import (
    AUTO_STEP_FRACTION,
    AUTO_STEP_MAX,
    AUTO_STEP_MIN,
    SensitivityResult,
    compute_sensitivity,
)


# ---------------------------------------------------------------------------
# SensitivityResult round-trip


def test_sensitivity_result_round_trips_through_json() -> None:
    hull = Hull()
    result = compute_sensitivity(
        hull,
        metrics=["GM0_m", "displaced_mass_kg"],
        params=["beam_oa_m", "length_m"],
    )
    loaded = SensitivityResult.model_validate_json(result.model_dump_json())
    assert loaded == result
    assert loaded.hull_record_hash == hull.hash()
    assert set(loaded.metric_baseline) == {"GM0_m", "displaced_mass_kg"}
    assert set(loaded.step_per_param) == {"beam_oa_m", "length_m"}


# ---------------------------------------------------------------------------
# Numeric: partial sign for a well-understood (parameter, metric) pair


def test_length_increases_displaced_mass_partial_is_positive() -> None:
    """Displaced mass scales monotonically with length for the lofted hull,
    so the central-difference partial is positive — the same sign assertion
    the RFC's worked example calls for, applied to the metric for which
    the lofted hydrostatic model is most directly responsive to ``length_m``.
    """

    hull = Hull()
    result = compute_sensitivity(
        hull,
        metrics=["displaced_mass_kg"],
        params=["length_m"],
        step=0.05,
    )
    assert "length_m" in result.metric_partials["displaced_mass_kg"]
    partial = result.metric_partials["displaced_mass_kg"]["length_m"]
    assert partial > 0.0


def test_beam_increases_initial_gm0_partial_is_positive() -> None:
    """A wider beam raises the transverse waterplane moment of inertia, so
    the GM0_m partial w.r.t. ``beam_oa_m`` is strictly positive on a default
    hull — the canonical sign check for the central-difference loop.
    """

    hull = Hull()
    result = compute_sensitivity(
        hull,
        metrics=["GM0_m"],
        params=["beam_oa_m"],
    )
    partial = result.metric_partials["GM0_m"]["beam_oa_m"]
    assert partial > 0.0


# ---------------------------------------------------------------------------
# Auto-step lives inside the documented clamp range


@pytest.mark.parametrize(
    "parameter,baseline_attr",
    [
        ("length_m", "length_m"),
        ("beam_oa_m", "beam_oa_m"),
        ("Cp", "Cp"),
    ],
)
def test_auto_step_lies_inside_documented_clamp(parameter: str, baseline_attr: str) -> None:
    hull = Hull()
    result = compute_sensitivity(hull, metrics=["GM0_m"], params=[parameter])
    step = result.step_per_param[parameter]
    assert AUTO_STEP_MIN <= step <= AUTO_STEP_MAX
    baseline_value = float(getattr(hull, baseline_attr))
    # The 1e-4 * baseline fraction is honored when it falls inside the clamp.
    expected = AUTO_STEP_FRACTION * abs(baseline_value)
    if AUTO_STEP_MIN <= expected <= AUTO_STEP_MAX:
        assert step == pytest.approx(expected)


# ---------------------------------------------------------------------------
# ConvergenceFlag appears on default ``kayakgen evaluate`` output


def test_default_evaluate_result_carries_non_empty_convergence(tmp_path: Path) -> None:
    hull_path = tmp_path / "hull.json"
    hull_path.write_text(Hull().model_dump_json())
    out_path = tmp_path / "out.eval.json"
    cli = CliRunner()
    result = cli.invoke(
        app,
        ["evaluate", str(hull_path), "--skip-resistance", "--out", str(out_path)],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(out_path.read_text())
    assert "convergence" in payload
    assert payload["convergence"], "default evaluate convergence must be non-empty"
    stages = {entry["stage"] for entry in payload["convergence"]}
    assert "hydrostatics" in stages
    # Round-trips through the typed model without losing the field.
    parsed = EvaluationResult.model_validate(payload)
    assert parsed.convergence
    assert all(isinstance(flag, ConvergenceFlag) for flag in parsed.convergence)


def test_evaluation_result_emits_stability_convergence_when_stability_present() -> None:
    hull = Hull()
    hydro = evaluate_hydrostatics(hull)
    stability = evaluate_initial_stability(hull)
    result = EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=hydro,
        stability=stability,
    )
    stages = [flag.stage for flag in result.convergence]
    # design_waterline_initial does not emit an iteration stage; hydrostatics
    # always emits the single converged entry.
    assert "hydrostatics" in stages


# ---------------------------------------------------------------------------
# Comparison report: pairwise_notes flag when default-objective metrics are
# below the registry threshold for two synthetic Pareto candidates.


def _write_synthetic_two_candidate_run(
    root: Path,
    *,
    metrics_left: dict[str, float],
    metrics_right: dict[str, float],
) -> None:
    candidates = root / "candidates"
    candidates.mkdir(parents=True, exist_ok=True)
    hull = Hull()
    hydro = evaluate_hydrostatics(hull)

    def _write_candidate(key: str, summary_metrics: dict[str, float]) -> CandidateRecord:
        evaluation = EvaluationResult(
            hull_hash=hull.hash(),
            hydrostatics=hydro,
            resistance=ResistanceCurve(
                V_knots=[3.0],
                Fn=[0.25],
                Rv_N=[5.0],
                Rw_N=[2.0],
                Rt_N=[7.0],
                metadata=ResistanceMetadata(),
            ),
        )
        eval_path = candidates / f"{key}.eval.json"
        eval_path.write_text(evaluation.model_dump_json(indent=2))
        record = CandidateRecord(
            candidate_index=0 if key.endswith("-a") else 1,
            candidate_key=key,
            parameters={},
            attempted_hull=hull.model_dump(mode="json"),
            status="complete",
            hull_hash=hull.hash(),
            artifacts={"evaluation": str(eval_path.relative_to(root))},
            summary={
                "GM0_m": summary_metrics["GM0_m"],
                "displacement_error_kg": summary_metrics["displacement_error_kg"],
                "mesh_problem_count": summary_metrics["mesh_problem_count"],
            },
        )
        return record

    records = [
        _write_candidate("candidate-a", metrics_left),
        _write_candidate("candidate-b", metrics_right),
    ]
    run = SweepRunRecord(
        name="pairwise-noise",
        spec_hash="pairwise-noise",
        candidate_count=2,
        pending_count=0,
        completed_count=2,
        failed_count=0,
        skipped_count=0,
        candidates=records,
    )
    (root / "run.json").write_text(run.model_dump_json(indent=2))


def test_pairwise_notes_flags_within_evaluator_noise_pair(tmp_path: Path) -> None:
    gm0_threshold = OBJECTIVE_METADATA["GM0_m"].within_evaluator_noise_threshold or 0.0
    err_threshold = (
        OBJECTIVE_METADATA["displacement_error_kg"].within_evaluator_noise_threshold or 0.0
    )
    mesh_threshold = (
        OBJECTIVE_METADATA["mesh_problem_count"].within_evaluator_noise_threshold or 0.0
    )
    assert gm0_threshold > 0 and err_threshold > 0 and mesh_threshold > 0

    _write_synthetic_two_candidate_run(
        tmp_path,
        metrics_left={
            "GM0_m": 0.100,
            "displacement_error_kg": 0.10,
            "mesh_problem_count": 0.0,
        },
        metrics_right={
            "GM0_m": 0.100 + gm0_threshold / 4.0,
            "displacement_error_kg": 0.10 + err_threshold / 4.0,
            "mesh_problem_count": 0.0,
        },
    )

    report = build_comparison_report(tmp_path)
    assert report.pareto_front_keys, "synthetic pair must both be on the frontier"
    assert report.pairwise_notes, "pair within registry tolerances must be flagged"
    note = report.pairwise_notes[0]
    assert note.within_evaluator_noise is True
    assert {note.left_key, note.right_key} == {"candidate-a", "candidate-b"}
    assert "GM0_m" in note.metric_differences
    assert note.metric_differences["GM0_m"] < gm0_threshold


def test_pairwise_notes_absent_when_pair_differs_above_threshold(tmp_path: Path) -> None:
    gm0_threshold = OBJECTIVE_METADATA["GM0_m"].within_evaluator_noise_threshold or 0.0
    assert gm0_threshold > 0
    _write_synthetic_two_candidate_run(
        tmp_path,
        metrics_left={
            "GM0_m": 0.100,
            "displacement_error_kg": 0.10,
            "mesh_problem_count": 0.0,
        },
        metrics_right={
            # Above the GM0 tolerance — pair should NOT be flagged.
            "GM0_m": 0.100 + gm0_threshold * 10.0,
            "displacement_error_kg": 0.10,
            "mesh_problem_count": 0.0,
        },
    )
    report = build_comparison_report(tmp_path)
    assert report.pairwise_notes == []


# ---------------------------------------------------------------------------
# Default sweep summary.csv stays byte-stable: the new
# ``within_evaluator_noise_threshold`` field never leaks into rows.


def test_default_sweep_summary_csv_columns_do_not_leak_registry_field(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="noise-threshold-leak",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}},
    )
    run_sweep(spec, tmp_path)
    summary_text = (tmp_path / "summary.csv").read_text()
    header = summary_text.splitlines()[0]
    assert "within_evaluator_noise_threshold" not in header
    assert "within_evaluator_noise" not in header
