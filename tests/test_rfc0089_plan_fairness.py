"""RFC 0089 stage 8 — plan-outline hollow and overall-beam search admission."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kayakgen.eval.form_metrics import FormMetrics, evaluate_form_metrics
from kayakgen.model import Hull
from kayakgen.search.active.runner import run_search
from kayakgen.search.active.spec import (
    ObjectiveSpec,
    SearchAlgorithmSpec,
    SearchBudget,
    SearchConstraint,
    SearchSpec,
    UniformVariable,
)
from kayakgen.search.objectives import OBJECTIVE_METADATA
from kayakgen.search.sweep import EvaluatorOptions, SweepSpec, run_sweep

FIXTURE = Path(__file__).parent / "fixtures" / "hulls" / "needle18-v2.json"


def _stepped_hull() -> Hull:
    payload = Hull.model_validate_json(FIXTURE.read_text()).model_dump()
    payload["distribution_v2"]["section_side_exponent"] = {
        "kind": "ramp",
        "forward": 2.5,
        "aft": 1.0,
        "forward_xi": -0.30,
        "aft_xi": 0.15,
    }
    payload["distribution_v2"]["topsides"] = {
        "sheer_height_frac": 0.75,
        "sheer_plan": {
            "max_half_breadth_m": 0.27,
            "max_position_xi": 0.25,
            "forward_exponent": 1.35,
            "aft_exponent": 1.60,
        },
        "deck_crown_exponent": {"kind": "ramp", "forward": 2.5, "aft": 8.0, "forward_xi": -0.30, "aft_xi": 0.15},
        "shoulder_round_m": 0.06,
    }
    return Hull.model_validate(payload)


def test_convex_plan_outline_reads_zero_hollow_and_stepped_transition_is_flagged() -> None:
    fair = evaluate_form_metrics(Hull.model_validate_json(FIXTURE.read_text()))
    assert fair.plan_hollow_max_deg == pytest.approx(0.0, abs=1e-6)
    assert fair.plan_hollow_x_m == pytest.approx(0.0, abs=1e-9)

    stepped = evaluate_form_metrics(_stepped_hull())
    assert stepped.plan_hollow_max_deg > 3.0
    assert -1.0 < stepped.plan_hollow_x_m < 0.2


def test_blocks_written_before_plan_hollow_still_load() -> None:
    dumped = evaluate_form_metrics(Hull.model_validate_json(FIXTURE.read_text())).model_dump()
    legacy = {k: v for k, v in dumped.items() if not k.startswith("plan_hollow")}
    restored = FormMetrics.model_validate(legacy)
    assert restored.plan_hollow_max_deg is None
    assert restored.plan_hollow_x_m is None


def test_sweep_and_registry_expose_plan_hollow_and_max_overall_beam(tmp_path: Path) -> None:
    hull = _stepped_hull()
    spec = SweepSpec(
        name="plan-fairness",
        base_hull=json.loads(hull.model_dump_json()),
        variables={"length_m": {"kind": "values", "values": [hull.length_m]}},
        evaluators={"hydrostatics": True, "form_metrics": True},
    )
    summary = run_sweep(spec, tmp_path / "run").candidates[0].summary
    direct = evaluate_form_metrics(hull)
    assert summary["form.plan_hollow_max_deg"] == pytest.approx(direct.plan_hollow_max_deg)
    assert summary["form.max_overall_beam_m"] == pytest.approx(direct.max_overall_beam_m)
    for key in ("form.plan_hollow_max_deg", "form.max_overall_beam_m"):
        meta = OBJECTIVE_METADATA[key]
        assert meta.role == "explicit_exploratory"
        assert meta.direction == "min"


def test_active_search_constrains_plan_hollow_and_max_overall_beam(tmp_path: Path) -> None:
    base = json.loads(_stepped_hull().model_dump_json())
    spec = SearchSpec(
        name="smooth-plan-search",
        base_hull=base,
        search_space={
            "distribution_v2.section_side_exponent.forward_xi": UniformVariable(min=-0.95, max=-0.25),
            "distribution_v2.section_side_exponent.aft_xi": UniformVariable(min=0.15, max=0.60),
            "distribution_v2.topsides.sheer_plan.forward_exponent": UniformVariable(min=1.35, max=1.90),
        },
        algorithm=SearchAlgorithmSpec(population_size=6, generations=1, seed=19),
        objectives=[
            ObjectiveSpec(metric="form.catch_zone_max_upper_beam_m", direction="min"),
            ObjectiveSpec(metric="form.plan_hollow_max_deg", direction="min"),
        ],
        evaluators=EvaluatorOptions(hydrostatics=True, form_metrics=True),
        constraints=[
            SearchConstraint(metric="form.plan_hollow_max_deg", max=2.5),
            SearchConstraint(metric="form.max_overall_beam_m", max=0.58),
        ],
        budget=SearchBudget(max_evaluations=6),
        objectives_explicit_exploratory=True,
    )
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(spec.model_dump_json())
    run_search(spec_path, tmp_path / "run")
    run_payload = json.loads((tmp_path / "run" / "run.json").read_text())
    for candidate in run_payload["candidates"]:
        if candidate["status"] == "complete":
            assert candidate["summary"]["form.plan_hollow_max_deg"] <= 2.5
            assert candidate["summary"]["form.max_overall_beam_m"] <= 0.58
        elif candidate["status"] == "constraint_failed":
            assert (
                candidate["summary"]["form.plan_hollow_max_deg"] > 2.5
                or candidate["summary"]["form.max_overall_beam_m"] > 0.58
            )

