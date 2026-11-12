"""RFC 0089 stage 2 — tumblehome, sheer plan, deck crown, search admission."""

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
from kayakgen.eval.contract import LoadCase
from kayakgen.eval.form_metrics import evaluate_form_metrics
from kayakgen.eval.high_angle_gz import build_high_angle_gz_block
from kayakgen.eval.hydrostatics import evaluate
from kayakgen.model.distribution_v2 import SheerPlan
from kayakgen.model.hull import Hull
from kayakgen.search.active.runner import run_search
from kayakgen.search.active.spec import (
    ObjectiveSpec,
    SearchAlgorithmSpec,
    SearchBudget,
    SearchConstraint,
    SearchSpec,
    UniformVariable,
)
from kayakgen.search.objectives import (
    OBJECTIVE_METADATA,
    OBJECTIVE_REJECTION_CLAIM_GATED,
    OBJECTIVE_REJECTION_DISPLAY_ONLY,
    is_objective_metric_admissible,
)
from kayakgen.search.pareto import (
    HighAngleGzObjectiveRefusedError,
    Objective,
    ensure_objectives_not_high_angle_gz,
)
from kayakgen.search.sweep import EvaluatorOptions
from kayakgen.services.build_export import write_offsets_csv

FIXTURE = Path(__file__).parent / "fixtures" / "hulls" / "needle18-v2.json"
FRAC = 0.6
PLAN = {
    "max_half_breadth_m": 0.27,
    "max_position_xi": 0.25,
    "forward_exponent": 1.8,
    "aft_exponent": 2.0,
}


def _base() -> Hull:
    return Hull.model_validate_json(FIXTURE.read_text())


def _with_topsides(hull: Hull, **topsides: object) -> Hull:
    payload = hull.model_dump()
    payload["distribution_v2"]["topsides"] = {"sheer_height_frac": FRAC, **topsides}
    return Hull.model_validate(payload)


def _upper_quarter(hull: Hull, x: float) -> np.ndarray:
    return hull.to_geometry()._deck_quarter_section(x)


# ----- byte stability -----


def test_unset_stage2_fields_are_not_serialized() -> None:
    hull = _with_topsides(_base(), sheer_beam_ratio=1.15)
    dumped = json.loads(hull.model_dump_json())["distribution_v2"]["topsides"]
    assert set(dumped) == {"sheer_beam_ratio", "sheer_height_frac"}
    assert Hull.model_validate_json(hull.model_dump_json()).hash() == hull.hash()
    plan = dict(PLAN)
    with_plan = _with_topsides(_base(), sheer_plan=plan)
    assert with_plan.hash() != hull.hash()
    restored = Hull.model_validate_json(with_plan.model_dump_json())
    assert restored.distribution_v2.topsides.sheer_plan == SheerPlan(**plan)


# ----- tumblehome -----


@pytest.mark.parametrize("ratio", [0.95, 0.8, 0.6])
def test_tumblehome_narrows_the_sheer_without_widening_the_section(ratio: float) -> None:
    hull = _with_topsides(_base(), sheer_beam_ratio=ratio)
    geometry = hull.to_geometry()
    plain = _base().to_geometry()
    for x in (-2.0, -0.8, 0.0, 1.1, 2.2):
        half_b = float(np.abs(plain.section(x, "hull")[:, 0]).max())
        freeboard = float(plain.section(x, "deck")[:, 1].max())
        quarter = _upper_quarter(hull, x)
        assert quarter.shape == plain._deck_quarter_section(x).shape
        np.testing.assert_allclose(quarter[0], [0.0, freeboard], atol=1e-12)
        np.testing.assert_allclose(quarter[-1], [half_b, 0.0], atol=1e-12)
        sheer = quarter[np.argmin(np.abs(quarter[:, 1] - FRAC * freeboard))]
        assert sheer[0] == pytest.approx(ratio * half_b, rel=1e-9)
        # The turn at the waterline may bulge by about 1% of the
        # half-breadth, no more.
        assert quarter[:, 0].max() <= 1.011 * half_b
        assert np.all(np.diff(quarter[:, 1]) <= 1e-12)
    sheer_line = geometry.sheer_line(21)
    np.testing.assert_allclose(sheer_line[:, 1], ratio * plain.sheer_line(21)[:, 1])


@pytest.mark.parametrize(
    "family", ["round", "shallow_arch", "shallow_v", "deep_v", "hard_chine", "multi_chine"]
)
def test_closed_body_with_sheer_plan_and_crown(family: str) -> None:
    payload = _base().model_dump()
    payload["distribution_v2"]["cross_section_family"] = family
    payload["distribution_v2"]["topsides"] = {
        "sheer_height_frac": 0.5,
        "sheer_plan": PLAN,
        "deck_crown_exponent": 8.0,
    }
    body = generated_hull_plus_deck_body(
        Hull.model_validate(payload), stations=31, section_points=12
    )
    readiness = diagnose_closed_volume_body(body).readiness
    assert readiness.level == "closed_volume", readiness


def test_upright_hydrostatics_do_not_depend_on_tumblehome() -> None:
    base = evaluate(_base())
    narrow = evaluate(
        _with_topsides(_base(), sheer_beam_ratio=0.8, deck_crown_exponent=9.0)
    )
    assert narrow.displaced_volume_m3 == base.displaced_volume_m3
    assert narrow.wetted_surface_m2 == base.wetted_surface_m2
    assert narrow.GM0_m == base.GM0_m


def test_righting_arm_orders_tumblehome_wall_sided_flared() -> None:
    load = LoadCase(paddler_mass_kg=82.0, hull_mass_kg=18.0)

    def gz(hull: Hull) -> list[float]:
        block = build_high_angle_gz_block(hull, load, heel_grid_deg=[0.0, 20.0, 30.0])
        assert block["available"] is True
        return [point["gz_m"] for point in block["heel_points"]]

    narrow = gz(_with_topsides(_base(), sheer_beam_ratio=0.8))
    wall = gz(_with_topsides(_base(), sheer_beam_ratio=1.0))
    flared = gz(_with_topsides(_base(), sheer_beam_ratio=1.2))
    for index in (1, 2):
        assert narrow[index] < wall[index] < flared[index]


def test_offsets_report_the_sheer_height_under_tumblehome(tmp_path: Path) -> None:
    hull = _with_topsides(_base(), sheer_beam_ratio=0.8)
    path = tmp_path / "offsets.csv"
    write_offsets_csv(hull, path)
    rows = [
        line.split(",")
        for line in path.read_text().splitlines()
        if line and not line.startswith("#") and not line.startswith("X")
    ]
    geometry = hull.to_geometry()
    middle = rows[len(rows) // 2]
    x = float(middle[0])
    assert float(middle[3]) == pytest.approx(geometry.sheer_z_at(x), abs=1e-8)
    assert float(middle[3]) > 0.0
    assert _base().to_geometry().sheer_z_at(0.0) is None


@pytest.mark.parametrize(
    "topsides",
    [
        {"sheer_beam_ratio": 0.55},
        {"sheer_beam_ratio": 1.1, "sheer_plan": PLAN},
        {"sheer_plan": {**PLAN, "max_half_breadth_m": 0.45}},
        {"sheer_plan": {**PLAN, "max_half_breadth_m": 0.12}},
        {"sheer_plan": {**PLAN, "forward_exponent": 1.1}},
        {"sheer_plan": {**PLAN, "aft_exponent": 4.5}},
        {"sheer_plan": {**PLAN, "max_position_xi": 0.9}},
        {"sheer_plan": {**PLAN, "extra": 1}},
        {"deck_crown_exponent": 1.9},
        {"deck_crown_exponent": 12.5},
        {"deck_crown_exponent": float("nan")},
    ],
)
def test_out_of_range_stage2_topsides_are_refused(topsides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _with_topsides(_base(), **topsides)


# ----- sheer plan -----


def test_sheer_plan_is_a_fair_outline() -> None:
    plan = SheerPlan(**PLAN)
    xi = np.linspace(-1.0, 1.0, 801)
    half = plan.half_breadth(xi)
    peak = int(np.argmax(half))
    assert xi[peak] == pytest.approx(0.25, abs=2.0 / 800)
    assert half[peak] == pytest.approx(0.27, rel=1e-5)
    assert half[0] == pytest.approx(0.0, abs=1e-12) and half[-1] == pytest.approx(0.0, abs=1e-12)
    # Monotone each side of the widest point and curving one way only:
    # no pinch, hollow or flat anywhere in the outline.
    assert np.all(np.diff(half[: peak + 1]) > 0)
    assert np.all(np.diff(half[peak:]) < 0)
    assert np.all(np.diff(half[: peak + 1], 2) < 1e-12)
    assert np.all(np.diff(half[peak:], 2) < 1e-12)
    finer = SheerPlan(**{**PLAN, "forward_exponent": 1.3}).half_breadth(xi)
    assert np.all(finer[1:peak] < half[1:peak])
    np.testing.assert_allclose(finer[peak:], half[peak:])


def test_geometry_follows_the_sheer_plan() -> None:
    hull = _with_topsides(_base(), sheer_plan=PLAN)
    plain = _base().to_geometry()
    geometry = hull.to_geometry()
    plan = SheerPlan(**PLAN)
    tumblehome = flared = 0
    for x in (-2.0, -1.2, -0.5, 0.0, 0.7, 1.5, 2.2):
        xi = 2.0 * x / hull.length_m
        half_b = float(np.abs(plain.section(x, "hull")[:, 0]).max())
        freeboard = float(plain.section(x, "deck")[:, 1].max())
        expected = float(plan.half_breadth(xi)[0])
        assert 0.6 * half_b <= expected <= 1.5 * half_b
        quarter = geometry._deck_quarter_section(x)
        sheer = quarter[np.argmin(np.abs(quarter[:, 1] - FRAC * freeboard))]
        assert sheer[0] == pytest.approx(expected, rel=1e-9)
        assert geometry.is_tumblehome_at(x) == (expected < half_b)
        tumblehome += expected < half_b
        flared += expected > half_b
    # One fair outline gives tumblehome forward and flare aft.
    assert tumblehome and flared
    line = geometry.sheer_line(41)
    np.testing.assert_allclose(
        line[1:-1, 1], plan.half_breadth(2.0 * line[1:-1, 0] / hull.length_m), rtol=1e-9
    )
    assert line[0, 1] == 0.0 and line[-1, 1] == 0.0


def test_sheer_plan_moves_shaft_clearance_and_keeps_upright_hydrostatics() -> None:
    wide = _with_topsides(_base(), sheer_plan=PLAN)
    fine = _with_topsides(_base(), sheer_plan={**PLAN, "forward_exponent": 1.4})
    kwargs = {"reference_station_x_m": 0.0, "catch_upper_height_m": 0.05}
    a = evaluate_form_metrics(wide, **kwargs)
    b = evaluate_form_metrics(fine, **kwargs)
    assert b.catch_zone_max_upper_beam_m < a.catch_zone_max_upper_beam_m
    assert evaluate(fine).GM0_m == evaluate(_base()).GM0_m
    assert evaluate(fine).displaced_volume_m3 == evaluate(_base()).displaced_volume_m3


# ----- deck crown -----


def test_deck_crown_exponent_squares_the_deck() -> None:
    aft = 1.0  # aft of midships the built-in arch exponent is exactly 4
    built_in = _with_topsides(_base(), sheer_beam_ratio=1.1)
    same = _with_topsides(_base(), sheer_beam_ratio=1.1, deck_crown_exponent=4.0)
    square = _with_topsides(_base(), sheer_beam_ratio=1.1, deck_crown_exponent=10.0)
    np.testing.assert_allclose(_upper_quarter(same, aft), _upper_quarter(built_in, aft), atol=1e-15)
    a, b = _upper_quarter(built_in, aft), _upper_quarter(square, aft)
    np.testing.assert_array_equal(a[:, 0], b[:, 0])
    assert np.all(b[:, 1] >= a[:, 1] - 1e-15)
    assert (b[:, 1] - a[:, 1]).max() > 0.01
    volume = lambda hull: diagnose_closed_volume_body(  # noqa: E731
        generated_hull_plus_deck_body(hull)
    ).signed_volume_m3
    assert volume(square) > volume(built_in)


def test_deck_crown_exponent_accepts_a_distribution() -> None:
    hull = _with_topsides(
        _base(),
        deck_crown_exponent={"kind": "key_points", "knots": [(-1.0, 4.0), (0.0, 8.0), (1.0, 6.0)]},
    )
    spec = hull.distribution_v2.topsides
    assert spec.sample_deck_crown_exponent(0.0) == pytest.approx(8.0)
    assert spec.sample_deck_crown_exponent(1.0) == pytest.approx(6.0)
    assert _base().distribution_v2.topsides is None


# ----- form metrics -----


def test_class_beam_length_fraction_is_beam_over_overall_length() -> None:
    hull = _base()
    metrics = evaluate_form_metrics(hull)
    assert metrics.overall_length_m == pytest.approx(hull.length_m)
    assert metrics.class_beam_length_fraction == pytest.approx(
        metrics.class_waterline_beam_m / hull.length_m
    )
    # USCA Sea Kayak: at least 8.5% of length at the 4 in waterline.
    assert 0.07 < metrics.class_beam_length_fraction < 0.10
    with pytest.raises(ValueError):
        evaluate_form_metrics(hull, catch_upper_height_m=-0.01)


def test_upper_beam_without_topsides_reads_the_deck_above_the_height() -> None:
    hull = _base()
    low = evaluate_form_metrics(hull, catch_upper_height_m=0.0)
    high = evaluate_form_metrics(hull, catch_upper_height_m=0.10)
    assert low.catch_zone_max_upper_beam_m == pytest.approx(low.catch_zone_max_beam_m, rel=1e-6)
    assert high.catch_zone_max_upper_beam_m < low.catch_zone_max_upper_beam_m


# ----- search admission -----

FORM_METRICS = (
    "form.class_length_beam_ratio",
    "form.class_waterline_beam_m",
    "form.class_beam_length_fraction",
    "form.catch_zone_max_beam_m",
    "form.catch_zone_max_upper_beam_m",
    "form.beam_at_reference_m",
)


@pytest.mark.parametrize("metric", FORM_METRICS)
def test_form_metrics_are_objectives_only_under_exploratory_opt_in(metric: str) -> None:
    assert OBJECTIVE_METADATA[metric].role == "explicit_exploratory"
    assert OBJECTIVE_METADATA[metric].default_objective_eligible is False
    admissible, reason = is_objective_metric_admissible(metric, explicit_exploratory=False)
    assert admissible is False and reason["code"] == OBJECTIVE_REJECTION_CLAIM_GATED
    assert is_objective_metric_admissible(metric, explicit_exploratory=True) == (True, None)


@pytest.mark.parametrize("exploratory", [False, True])
def test_load_case_gz_is_never_an_objective(exploratory: bool) -> None:
    metric = "load_case_gz.day.gz_m_at_20deg"
    admissible, reason = is_objective_metric_admissible(metric, explicit_exploratory=exploratory)
    assert admissible is False and reason["code"] == OBJECTIVE_REJECTION_DISPLAY_ONLY
    with pytest.raises(HighAngleGzObjectiveRefusedError):
        ensure_objectives_not_high_angle_gz([Objective(metric=metric, direction="max")])


DAY = {"name": "day", "paddler_mass_kg": 82.0, "hull_mass_kg": 18.0}


def _search_spec(*, gz_floor_m: float, objective: str = "form.catch_zone_max_upper_beam_m") -> SearchSpec:
    base = json.loads(FIXTURE.read_text())
    base["distribution_v2"]["topsides"] = {
        "sheer_height_frac": FRAC,
        "sheer_plan": dict(PLAN),
        "deck_crown_exponent": 4.0,
    }
    return SearchSpec(
        name="deck",
        base_hull=base,
        search_space={
            "distribution_v2.topsides.sheer_plan.forward_exponent": UniformVariable(
                min=1.4, max=2.4
            ),
            "distribution_v2.topsides.deck_crown_exponent": UniformVariable(min=3.0, max=10.0),
        },
        algorithm=SearchAlgorithmSpec(population_size=4, generations=1, seed=7),
        objectives=[
            ObjectiveSpec(metric=objective, direction="min"),
            ObjectiveSpec(metric="GM0_m", direction="max"),
        ],
        evaluators=EvaluatorOptions(
            hydrostatics=True,
            form_metrics=True,
            high_angle_gz_heel_grid_deg=[0.0, 10.0, 20.0],
            high_angle_gz_load_cases=[DAY],
        ),
        constraints=[SearchConstraint(metric="load_case_gz.day.gz_m_at_20deg", min=gz_floor_m)],
        budget=SearchBudget(max_evaluations=4),
        objectives_explicit_exploratory=True,
    )


def _run(spec: SearchSpec, tmp_path: Path) -> dict:
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(spec.model_dump_json())
    run_search(spec_path, tmp_path / "run")
    return json.loads((tmp_path / "run" / "run.json").read_text())


def test_search_varies_deck_controls_under_a_righting_arm_floor(tmp_path: Path) -> None:
    payload = _run(_search_spec(gz_floor_m=-1.0), tmp_path)
    complete = [c for c in payload["candidates"] if c["status"] == "complete"]
    assert len(complete) == 4
    key = "distribution_v2.topsides.sheer_plan.forward_exponent"
    assert len({c["parameters"][key] for c in complete}) > 1
    for candidate in complete:
        summary = candidate["summary"]
        assert summary["form.catch_zone_max_upper_beam_m"] > 0
        assert "load_case_gz.day.gz_m_at_20deg" in summary
    ordered = sorted(complete, key=lambda c: c["parameters"][key])
    assert (
        ordered[0]["summary"]["form.catch_zone_max_upper_beam_m"]
        < ordered[-1]["summary"]["form.catch_zone_max_upper_beam_m"]
    )
    assert payload["final_frontier_keys"]


def test_search_rejects_candidates_below_the_righting_arm_floor(tmp_path: Path) -> None:
    payload = _run(_search_spec(gz_floor_m=1.0), tmp_path)
    statuses = {c["status"] for c in payload["candidates"]}
    assert statuses == {"constraint_failed"}
    assert payload["final_frontier_keys"] == []


def test_search_refuses_a_load_case_gz_objective(tmp_path: Path) -> None:
    spec = _search_spec(gz_floor_m=-1.0, objective="load_case_gz.day.gz_m_at_20deg")
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(spec.model_dump_json())
    with pytest.raises(ValueError, match="display-only"):
        run_search(spec_path, tmp_path / "run")
