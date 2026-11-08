"""Operating request equality and numerical budgets survive public consumers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kayakgen.eval.contract import EvaluationContext, EvaluationResult, LoadCase
from kayakgen.model.hull import Hull
from kayakgen.search.compare import build_comparison_report
from kayakgen.search.pareto import Objective
from kayakgen.search.sweep import CandidateRecord, SweepRunRecord, SweepSpec, run_sweep


def owner_hull(number: int = 8) -> Hull:
    return Hull.model_validate_json(
        (Path(__file__).parent / f"fixtures/numerical/fast-tourer-{number:02d}.json").read_text()
    )


def test_component_projection_preserves_physical_values_and_inherited_kg() -> None:
    base = EvaluationContext.for_hull(
        owner_hull(),
        load_case=LoadCase(
            components=[
                dict(name="person", mass_kg=80.0, x_m=-0.1, kg_above_keel_m=0.4),
                dict(name="gear", mass_kg=20.0, x_m=0.2, kg_above_keel_m=0.1),
            ]
        ),
        equilibrium=True,
    )
    data = base.model_dump(mode="json")
    data["load_case"].update(paddler_mass_kg=1.0, hull_mass_kg=2.0, cargo_mass_kg=3.0)
    data["load_case"]["components"].reverse()
    for component in data["load_case"]["components"]:
        component["name"] = "different label"
    equivalent = EvaluationContext.model_validate(data)
    assert base.operating_comparison_inputs() == equivalent.operating_comparison_inputs()
    data["load_case"]["kg_above_keel_m"] = 0.8
    assert (
        base.operating_comparison_inputs()
        == EvaluationContext.model_validate(data).operating_comparison_inputs()
    )
    data["load_case"]["components"][0]["x_m"] += 0.1
    assert (
        base.operating_comparison_inputs()
        != EvaluationContext.model_validate(data).operating_comparison_inputs()
    )
    inherited = EvaluationContext.for_hull(
        owner_hull(),
        load_case=LoadCase(components=[dict(name="inherited KG", mass_kg=100.0)]),
        equilibrium=True,
    )
    changed = inherited.model_dump(mode="json")
    changed["load_case"]["kg_above_keel_m"] = 0.4
    assert (
        inherited.operating_comparison_inputs()
        != EvaluationContext.model_validate(changed).operating_comparison_inputs()
    )


def test_projection_ignores_resistance_budget_and_owns_returned_nested_data() -> None:
    base = EvaluationContext.for_hull(
        owner_hull(), load_case=LoadCase(cargo_mass_kg=10.0), equilibrium=False
    )
    data = base.model_dump(mode="json")
    data.update(
        n_stations=1600,
        n_depths=100,
        n_theta=640,
        numerical_relative_tolerance=0.001,
        hydrostatic_stations=3,
    )
    same = EvaluationContext.model_validate(data)
    expected = base.operating_comparison_inputs()
    assert expected == same.operating_comparison_inputs()
    returned = base.operating_comparison_inputs()
    returned.clear()
    assert base.operating_comparison_inputs() == expected
    nested = base.operating_comparison_inputs()
    nested["load"]["kg"]["kg_above_keel_m"] = 999.0
    assert base.operating_comparison_inputs() == expected
    assert json.loads(json.dumps(expected)) == expected


def _consumer_report(root: Path, evaluations: list[EvaluationResult]):
    root.mkdir()
    records = []
    for i, result in enumerate(evaluations):
        rel = f"{i}.json"
        (root / rel).write_text(result.model_dump_json())
        records.append(
            CandidateRecord(
                candidate_index=i,
                candidate_key=str(i),
                parameters={},
                attempted_hull={},
                status="complete",
                hull_hash=result.hull_hash,
                artifacts={"evaluation": rel},
                summary={"Rt_N_last": result.resistance.Rt_N[-1]},
            )
        )
    run = SweepRunRecord(
        name="operating-consumer-fixture",
        spec_hash="fixture",
        candidate_count=len(records),
        pending_count=0,
        completed_count=len(records),
        failed_count=0,
        skipped_count=0,
        candidates=records,
    )
    (root / "run.json").write_text(run.model_dump_json())
    return build_comparison_report(
        root, objectives=[Objective(metric="Rt_N_last", direction="min")], explicit_exploratory=True
    )


def test_sweep_cli_budget_and_density_reach_actual_assessment_and_comparison(tmp_path) -> None:
    from kayakgen.cli.main import app

    hull = owner_hull()
    spec = SweepSpec.model_validate(
        dict(
            name="budget-forwarding",
            base_hull=hull.model_dump(mode="json"),
            variables={"Cp": {"kind": "values", "values": [hull.Cp]}},
            evaluators=dict(
                resistance=True,
                water_density_kg_m3=997.0,
                stability_load_case=dict(
                    paddler_mass_kg=180 * 0.45359237,
                    cargo_mass_kg=35 * 0.45359237,
                    hull_mass_kg=40 * 0.45359237,
                    seawater_density_kg_m3=1025.0,
                ),
                speeds_knots=[5.0],
                n_stations=400,
                n_depths=25,
                n_theta=40,
                numerical_relative_tolerance=0.01,
            ),
        )
    )
    run_dir = tmp_path / "sweep"
    run = run_sweep(spec, run_dir)
    record = run.candidates[0]
    fresh = EvaluationResult.model_validate_json(
        (run_dir / record.artifacts["evaluation"]).read_text()
    )
    assert fresh.context.numerical_relative_tolerance == 0.01
    assert fresh.resistance.metadata.numerical_quality.status == "converged"
    assert "seawater_density_kg_m3" in fresh.context.load_supplied_fields
    assert (
        record.summary["resistance_operating_context"]
        == fresh.context.operating_comparison_inputs()
    )
    actual_hull = Hull.model_validate_json((run_dir / record.artifacts["hull"]).read_text())
    sea_data = fresh.context.model_dump(mode="json")
    sea_data["load_case"]["seawater_density_kg_m3"] = 1025.0
    sea_context = EvaluationContext.model_validate(sea_data)
    h = tmp_path / "hull.json"
    h.write_text(actual_hull.model_dump_json())
    c = tmp_path / "context.json"
    c.write_text(sea_context.model_dump_json())
    out = tmp_path / "cli.json"
    invocation = CliRunner().invoke(
        app, ["evaluate", str(h), "--context", str(c), "--out", str(out)]
    )
    assert invocation.exit_code == 0, invocation.output
    sea = EvaluationResult.model_validate_json(out.read_text())
    assert sea.resistance.metadata.numerical_quality.status == "converged"
    assert fresh.resistance.Rt_N[0] / sea.resistance.Rt_N[0] == pytest.approx(997 / 1025, rel=1e-12)
    report = _consumer_report(tmp_path / "comparison", [fresh, sea])
    assert any("incompatible_operating_inputs" in warning for warning in report.warnings)
    assert len(report.pareto_front_keys) == 2
    for summary in report.candidate_summaries:
        assert summary.provenance["Rt_N_last"]["operating_context"]


def test_numerical_budget_and_adequacy_do_not_imply_operating_incompatibility(tmp_path):
    from numerical_test_cases import assessed_curve
    from kayakgen.eval.hydrostatics import evaluate

    hull = owner_hull()
    context = EvaluationContext.for_hull(
        hull,
        speeds_knots=(5.0,),
        n_stations=400,
        n_depths=25,
        n_theta=40,
        numerical_relative_tolerance=0.01,
    )
    # Consumer fixture reuses a real assessed curve; hydro values are irrelevant
    # to this projection and no matched-load or numerical re-evaluation is claimed.
    result = EvaluationResult(
        hull_hash=hull.record_hash(),
        context=context,
        resistance=assessed_curve(),
        hydrostatics=evaluate(hull),
    )
    raw = result.model_dump(mode="json")
    raw["context"]["numerical_relative_tolerance"] = None
    raw["context_hash"] = None
    raw["resistance"]["metadata"]["numerical_quality"] = {}
    unassessed = EvaluationResult.model_validate(raw)
    assert context.operating_comparison_inputs() == unassessed.context.operating_comparison_inputs()
    report = _consumer_report(tmp_path / "budget-consumer", [result, unassessed])
    assert not any("incompatible_operating_inputs" in warning for warning in report.warnings)
    assert report.pareto_front_keys == ["0"]
    changed = result.model_dump(mode="json")
    changed["context"]["numerical_relative_tolerance"] = 0.02
    changed["context_hash"] = None
    with pytest.raises(ValueError, match="numerical budget"):
        EvaluationResult.model_validate(changed)


def test_solved_pose_excludes_realized_values_but_retains_solver_accuracy_inputs():
    base = EvaluationContext.for_hull(
        owner_hull(),
        equilibrium=True,
        hydrostatic_stations=150,
        equilibrium_tolerance_kg=0.01,
        moment_tolerance_kg_m=0.02,
    )
    data = base.model_dump(mode="json")
    data.update(sinkage_m=0.03, trim_angle_deg=-0.7)
    assert (
        base.operating_comparison_inputs()
        == EvaluationContext.model_validate(data).operating_comparison_inputs()
    )
    for key, value in [
        ("hydrostatic_stations", 3),
        ("equilibrium_tolerance_kg", 1.0),
        ("moment_tolerance_kg_m", 0.5),
        ("equilibrium_max_iterations", 30),
        ("max_trim_angle_deg", 4.0),
    ]:
        changed = base.model_dump(mode="json")
        changed[key] = value
        assert (
            base.operating_comparison_inputs()
            != EvaluationContext.model_validate(changed).operating_comparison_inputs()
        )


def test_active_frontier_retains_different_and_missing_operating_conditions():
    from numerical_test_cases import assessed_curve
    from kayakgen.search.active.runner import _final_frontier_keys
    from kayakgen.search.active.spec import ObjectiveSpec

    records = []
    for i, number in enumerate((6, 8)):
        hull = owner_hull(number)
        context = EvaluationContext.for_hull(
            hull, speeds_knots=(5.0,), load_case=LoadCase(paddler_mass_kg=82.0)
        )
        curve = assessed_curve(number)
        records.append(
            CandidateRecord(
                candidate_index=i,
                candidate_key=str(number),
                parameters={},
                attempted_hull=hull.model_dump(mode="json"),
                status="complete",
                summary={
                    "Rt_N_last": curve.Rt_N[-1],
                    "resistance_numerical_quality": curve.metadata.numerical_quality.model_dump(
                        mode="json"
                    ),
                    "resistance_operating_context": context.operating_comparison_inputs(),
                },
            )
        )
    objectives = [ObjectiveSpec(metric="Rt_N_last", direction="min")]
    assert _final_frontier_keys(records, objectives, exploratory=True) == ["6"]
    other = EvaluationContext.for_hull(
        owner_hull(8),
        speeds_knots=(5.0,),
        load_case=LoadCase(paddler_mass_kg=82.0, cargo_mass_kg=10.0),
    )
    records[1].summary["resistance_operating_context"] = other.operating_comparison_inputs()
    assert _final_frontier_keys(records, objectives, exploratory=True) == ["6", "8"]
    records[1].summary.pop("resistance_operating_context")
    assert _final_frontier_keys(records, objectives, exploratory=True) == ["6", "8"]


def test_unsupported_policy_public_report_explains_diagnostic_only_admission(tmp_path, monkeypatch):
    from numerical_test_cases import assessed_curve
    from kayakgen.eval.hydrostatics import evaluate
    import kayakgen.eval.resistance as resistance

    hull = owner_hull()
    context = EvaluationContext.for_hull(
        hull,
        speeds_knots=(5.0,),
        n_stations=400,
        n_depths=25,
        n_theta=40,
        numerical_relative_tolerance=0.01,
    )
    record = EvaluationResult(
        hull_hash=hull.record_hash(),
        context=context,
        resistance=assessed_curve(),
        hydrostatics=evaluate(hull),
    ).model_dump(mode="json")
    record["resistance"]["metadata"]["numerical_quality"]["policy_version"] = (
        "unsupported_history_v99"
    )
    historical = EvaluationResult.model_validate(record)

    def forbidden(*args, **kwargs):
        raise AssertionError("comparison recomputed numerical evaluator")

    monkeypatch.setattr(resistance, "resistance_curve", forbidden)
    report = _consumer_report(tmp_path / "historical", [historical])
    assert report.pareto_front_keys == []
    summary = report.candidate_summaries[0]
    assert summary.metrics["Rt_N_last"] > 0
    assert summary.provenance["Rt_N_last"]["numerical_quality"]["status"] == "converged"
    assert any("not adequate for ranking" in warning for warning in summary.warnings)
