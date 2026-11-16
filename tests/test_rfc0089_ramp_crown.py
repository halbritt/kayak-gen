"""RFC 0089 stage 7 — longitudinal ramp distribution for searchable deck crown."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from kayakgen.eval.closed_volume import (
    diagnose_closed_volume_body,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.form_metrics import evaluate_form_metrics
from kayakgen.model import Hull, RampDistribution
from kayakgen.search.active.runner import run_search
from kayakgen.search.active.spec import (
    ObjectiveSpec,
    SearchAlgorithmSpec,
    SearchBudget,
    SearchConstraint,
    SearchSpec,
    UniformVariable,
)
from kayakgen.search.sweep import EvaluatorOptions

FIXTURE = Path(__file__).parent / "fixtures" / "hulls" / "needle18-v2.json"
PLAN = {
    "max_half_breadth_m": 0.27,
    "max_position_xi": 0.25,
    "forward_exponent": 1.8,
    "aft_exponent": 2.0,
}
DAY = {"name": "day", "paddler_mass_kg": 82.0, "hull_mass_kg": 18.0}


def test_ramp_distribution_holds_ends_and_blends_monotonically_with_zero_end_slope() -> None:
    ramp = RampDistribution(forward=2.4, aft=8.8, forward_xi=-0.3, aft_xi=0.2)
    assert ramp.sample(-1.0)[0] == pytest.approx(2.4)
    assert ramp.sample(-0.3)[0] == pytest.approx(2.4)
    assert ramp.sample(-0.05)[0] == pytest.approx(0.5 * (2.4 + 8.8))
    assert ramp.sample(0.2)[0] == pytest.approx(8.8)
    assert ramp.sample(1.0)[0] == pytest.approx(8.8)

    xi = np.linspace(-0.3, 0.2, 501)
    values = ramp.sample(xi)
    assert values.min() >= 2.4 - 1e-12
    assert values.max() <= 8.8 + 1e-12
    assert np.all(np.diff(values) > 0.0)

    eps = 1e-5
    slope_fwd = (ramp.sample(-0.3 + eps)[0] - ramp.sample(-0.3 - eps)[0]) / (2.0 * eps)
    slope_aft = (ramp.sample(0.2 + eps)[0] - ramp.sample(0.2 - eps)[0]) / (2.0 * eps)
    assert abs(slope_fwd) < 1e-3
    assert abs(slope_aft) < 1e-3


@pytest.mark.parametrize(
    "kwargs",
    [
        {"forward": 2.5, "aft": 8.0, "forward_xi": 0.2, "aft_xi": 0.2},
        {"forward": 2.5, "aft": 8.0, "forward_xi": 0.3, "aft_xi": -0.1},
        {"forward": 2.5, "aft": 8.0, "forward_xi": -1.1, "aft_xi": 0.2},
        {"forward": 2.5, "aft": 8.0, "forward_xi": -0.2, "aft_xi": 1.1},
        {"forward": float("nan"), "aft": 8.0},
        {"forward": 2.5, "aft": float("inf")},
        {"forward": 2.5, "aft": 8.0, "extra_field": 1.0},
    ],
)
def test_invalid_ramp_distribution_is_refused(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValidationError):
        RampDistribution(**kwargs)


def test_ramp_deck_crown_arches_foredeck_and_squares_aft_deck_in_closed_body() -> None:
    payload = Hull.model_validate_json(FIXTURE.read_text()).model_dump()
    payload["distribution_v2"]["section_side_exponent"] = {
        "kind": "ramp",
        "forward": 2.4,
        "aft": 1.0,
        "forward_xi": -0.3,
        "aft_xi": 0.15,
    }
    payload["distribution_v2"]["topsides"] = {
        "sheer_height_frac": {"kind": "ramp", "forward": 0.45, "aft": 0.65, "forward_xi": -0.3, "aft_xi": 0.15},
        "sheer_plan": dict(PLAN),
        "deck_crown_exponent": {
            "kind": "ramp",
            "forward": 2.2,
            "aft": 9.0,
            "forward_xi": -0.3,
            "aft_xi": 0.15,
        },
        "shoulder_round_m": 0.04,
    }
    hull = Hull.model_validate(payload)
    restored = Hull.model_validate_json(hull.model_dump_json())
    assert restored.hash() == hull.hash()

    scalar_payload = json.loads(hull.model_dump_json())
    scalar_payload["distribution_v2"]["topsides"]["deck_crown_exponent"] = 9.0
    scalar_hull = Hull.model_validate(scalar_payload)
    assert hull.hash() != scalar_hull.hash()

    geom = hull.to_geometry()
    scalar_geom = scalar_hull.to_geometry()
    # Foredeck (-1.1 m, xi ~ -0.40 <= -0.30) is arched relative to scalar 9.0;
    # aft deck (+1.1 m, xi ~ +0.40 >= +0.15) matches scalar 9.0.
    fwd_ramp = geom.section(-1.1, "deck")
    fwd_flat = scalar_geom.section(-1.1, "deck")
    assert fwd_ramp[:, 1].max() == pytest.approx(fwd_flat[:, 1].max(), abs=1e-9)
    mid_panel = (np.abs(fwd_ramp[:, 0]) > 0.04) & (np.abs(fwd_ramp[:, 0]) < 0.14)
    assert (fwd_flat[mid_panel, 1] - fwd_ramp[mid_panel, 1]).max() > 0.01
    np.testing.assert_allclose(geom.section(1.1, "deck"), scalar_geom.section(1.1, "deck"), atol=1e-12)

    body = generated_hull_plus_deck_body(hull, stations=41, section_points=16)
    assert diagnose_closed_volume_body(body).readiness.level == "closed_volume"
    metrics = evaluate_form_metrics(hull)
    assert metrics.waterline_knuckle_max_deg < 3.0


@pytest.mark.parametrize("bad_crown", [{"kind": "ramp", "forward": 1.8, "aft": 8.0}, {"kind": "ramp", "forward": 2.5, "aft": 12.5}])
def test_out_of_range_ramp_deck_crown_is_refused(bad_crown: dict[str, object]) -> None:
    payload = Hull.model_validate_json(FIXTURE.read_text()).model_dump()
    payload["distribution_v2"]["topsides"] = {
        "sheer_height_frac": 0.5,
        "deck_crown_exponent": bad_crown,
    }
    with pytest.raises(ValidationError, match="deck_crown_exponent"):
        Hull.model_validate(payload)


def test_active_search_varies_forward_and_aft_deck_crown_ramp_independently(tmp_path: Path) -> None:
    base = json.loads(FIXTURE.read_text())
    base["distribution_v2"]["topsides"] = {
        "sheer_height_frac": 0.55,
        "sheer_plan": dict(PLAN),
        "deck_crown_exponent": {
            "kind": "ramp",
            "forward": 2.5,
            "aft": 8.0,
            "forward_xi": -0.3,
            "aft_xi": 0.15,
        },
        "shoulder_round_m": 0.03,
    }
    fwd_key = "distribution_v2.topsides.deck_crown_exponent.forward"
    aft_key = "distribution_v2.topsides.deck_crown_exponent.aft"
    spec = SearchSpec(
        name="ramp-crown-search",
        base_hull=base,
        search_space={
            fwd_key: UniformVariable(min=2.0, max=3.2),
            aft_key: UniformVariable(min=6.0, max=11.0),
        },
        algorithm=SearchAlgorithmSpec(population_size=4, generations=1, seed=11),
        objectives=[
            ObjectiveSpec(metric="form.catch_zone_max_upper_beam_m", direction="min"),
            ObjectiveSpec(metric="form.foot_clear_height_m", direction="max"),
        ],
        evaluators=EvaluatorOptions(
            hydrostatics=True,
            form_metrics=True,
            high_angle_gz_heel_grid_deg=[0.0, 20.0],
            high_angle_gz_load_cases=[DAY],
        ),
        constraints=[SearchConstraint(metric="load_case_gz.day.gz_m_at_20deg", min=0.005)],
        budget=SearchBudget(max_evaluations=4),
        objectives_explicit_exploratory=True,
    )
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(spec.model_dump_json())
    run_search(spec_path, tmp_path / "run")
    run_payload = json.loads((tmp_path / "run" / "run.json").read_text())
    complete = [c for c in run_payload["candidates"] if c["status"] == "complete"]
    assert len(complete) == 4
    assert len({c["parameters"][fwd_key] for c in complete}) > 1
    assert len({c["parameters"][aft_key] for c in complete}) > 1
    for candidate in complete:
        crown = candidate["attempted_hull"]["distribution_v2"]["topsides"]["deck_crown_exponent"]
        assert crown["kind"] == "ramp"
        assert 2.0 <= crown["forward"] <= 3.2
        assert 6.0 <= crown["aft"] <= 11.0

