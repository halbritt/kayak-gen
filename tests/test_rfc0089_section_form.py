"""RFC 0089 — section fullness, form metrics and multi-load righting arms."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.closed_volume import (
    diagnose_closed_volume_body,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.contract import EvaluationResult, LoadCase
from kayakgen.eval.form_metrics import evaluate_form_metrics
from kayakgen.eval.high_angle_gz import build_high_angle_gz_block, build_load_case_gz_table
from kayakgen.eval.hydrostatics import evaluate
from kayakgen.model.hull import Hull
from kayakgen.search.sweep import EvaluatorOptions, SweepSpec, run_sweep

FIXTURE = Path(__file__).parent / "fixtures" / "hulls" / "needle18-v2.json"


def _base() -> Hull:
    return Hull.model_validate_json(FIXTURE.read_text())


def _with(hull: Hull, **v2: object) -> Hull:
    payload = hull.model_dump()
    payload["distribution_v2"].update(v2)
    return Hull.model_validate(payload)


def _section_area(hull: Hull, x: float) -> float:
    ring = hull.to_geometry().section(x, "hull")
    y, z = ring[:, 0], ring[:, 1]
    return abs(0.5 * float(np.sum(y * np.roll(z, -1) - np.roll(y, -1) * z)))


# ----- section exponent -----


def test_unset_exponent_keeps_bytes_identity_and_geometry() -> None:
    base = _base()
    assert "section_exponent" not in base.model_dump()["distribution_v2"]
    assert "section_exponent" not in json.loads(base.model_dump_json())["distribution_v2"]
    assert Hull.model_validate_json(base.model_dump_json()).hash() == base.hash()
    explicit = _with(base, section_exponent=2.0)
    assert explicit.hash() != base.hash()
    for x in (-2.0, -0.7, 0.0, 1.3):
        np.testing.assert_array_equal(
            explicit.to_geometry().section(x, "hull"), base.to_geometry().section(x, "hull")
        )


@pytest.mark.parametrize("exponent", [1.5, 3.0, 5.0, 8.0])
def test_section_follows_the_stated_power_law(exponent: float) -> None:
    hull = _with(_base(), section_exponent=exponent, deadrise_deg=0.0, rocker={"kind": "uniform", "value": 0.0})
    ring = hull.to_geometry().section(0.0, "hull")
    half_b = float(np.abs(ring[:, 0]).max())
    draft = float(-ring[:, 1].min())
    expected = -draft * (1.0 - (np.abs(ring[:, 0]) / half_b) ** exponent)
    np.testing.assert_allclose(ring[:, 1], expected, atol=1e-12)
    # Area coefficient of the power-law section is m / (m + 1); the
    # polygon through 30-odd points sits within 1% of it.
    coefficient = _section_area(hull, 0.0) / (2.0 * half_b * draft)
    assert coefficient == pytest.approx(exponent / (exponent + 1.0), rel=0.01)


def test_fuller_section_displaces_more_and_keeps_waterline() -> None:
    base = _base()
    full = _with(base, section_exponent=4.0)
    assert evaluate(full).displaced_mass_kg > 1.15 * evaluate(base).displaced_mass_kg
    for x in (-1.5, 0.0, 1.5):
        b0 = np.abs(base.to_geometry().section(x, "hull")[:, 0]).max()
        b1 = np.abs(full.to_geometry().section(x, "hull")[:, 0]).max()
        assert b1 == pytest.approx(b0, abs=1e-12)


def test_hydrostatics_agree_with_section_integration() -> None:
    hull = _with(_base(), section_exponent=3.5)
    xs = np.linspace(-hull.length_m / 2.0, hull.length_m / 2.0, 801)
    volume = float(np.trapezoid([_section_area(hull, float(x)) for x in xs], xs))
    assert evaluate(hull).displaced_mass_kg == pytest.approx(volume * 1025.0, rel=2e-3)


def test_exponent_accepts_a_longitudinal_distribution() -> None:
    hull = _with(
        _base(),
        section_exponent={"kind": "key_points", "knots": [(-1.0, 2.0), (0.0, 4.0), (1.0, 2.5)]},
    )
    spec = hull.distribution_v2
    assert spec is not None
    assert spec.sample_section_exponent(0.0) == pytest.approx(4.0)
    assert spec.sample_section_exponent(-1.0) == pytest.approx(2.0)
    mid = _section_area(hull, 0.0) / _section_area(_base(), 0.0)
    assert mid == pytest.approx((4.0 / 5.0) / (2.0 / 3.0), rel=0.01)


def test_generated_body_stays_closed_with_exponent_and_topsides() -> None:
    hull = _with(
        _base(),
        section_exponent=4.0,
        topsides={"sheer_beam_ratio": 1.15, "sheer_height_frac": 0.6},
    )
    diagnostics = diagnose_closed_volume_body(generated_hull_plus_deck_body(hull))
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0
    assert diagnostics.degenerate_faces == 0
    assert diagnostics.signed_volume_m3 > 0
    block = build_high_angle_gz_block(hull, LoadCase(), heel_grid_deg=[0.0, 10.0, 20.0])
    assert block["available"] is True


@pytest.mark.parametrize("value", [1.49, 8.01, float("nan"), float("inf")])
def test_out_of_range_exponent_is_refused(value: float) -> None:
    with pytest.raises(ValidationError):
        _with(_base(), section_exponent=value)


def test_exponent_is_refused_for_other_families() -> None:
    with pytest.raises(ValidationError, match="round"):
        _with(_base(), cross_section_family="shallow_arch", section_exponent=3.0)


# ----- form metrics -----


def test_class_ratio_matches_direct_section_measurement() -> None:
    hull = _base()
    metrics = evaluate_form_metrics(hull)
    geom = hull.to_geometry()
    xs = np.linspace(-hull.length_m / 2.0, hull.length_m / 2.0, 2001)
    rings = [geom.section(float(x), "hull") for x in xs]
    plane = min(float(r[:, 1].min()) for r in rings) + 0.1016
    beams = []
    wet = []
    for x, ring in zip(xs, rings):
        y, z = np.abs(ring[:, 0]), ring[:, 1]
        if z.min() >= plane or plane > 0.0:
            beams.append(0.0)
            continue
        order = np.argsort(z)
        beams.append(2.0 * float(np.interp(plane, z[order], y[order])))
        wet.append(float(x))
    assert metrics.class_waterline_beam_m == pytest.approx(max(beams), rel=2e-3)
    assert metrics.class_waterline_length_m == pytest.approx(max(wet) - min(wet), abs=0.02)
    assert metrics.class_length_beam_ratio == pytest.approx(
        metrics.class_waterline_length_m / metrics.class_waterline_beam_m
    )


def test_class_ratio_reads_topsides_above_the_design_waterline() -> None:
    plain = _base()
    flared = _with(plain, topsides={"sheer_beam_ratio": 1.3, "sheer_height_frac": 0.6})
    draft = float(-plain.to_geometry().section(0.0, "hull")[:, 1].min())
    high = draft + 0.03
    a = evaluate_form_metrics(plain, class_ratio_draft_m=high)
    b = evaluate_form_metrics(flared, class_ratio_draft_m=high)
    assert b.class_waterline_beam_m > a.class_waterline_beam_m
    assert b.max_overall_beam_m == pytest.approx(1.3 * a.max_overall_beam_m, rel=1e-3)


def test_catch_zone_is_forward_and_bounded() -> None:
    hull = _base()
    metrics = evaluate_form_metrics(hull, reference_station_x_m=0.0)
    assert metrics.reference_station_origin == "supplied"
    assert metrics.catch_zone_max_beam_m < metrics.beam_at_reference_m <= metrics.max_overall_beam_m
    far_forward = evaluate_form_metrics(
        hull, reference_station_x_m=0.0, catch_zone_forward_m=(2.0, 2.5)
    )
    assert far_forward.catch_zone_max_beam_m < metrics.catch_zone_max_beam_m
    clipped = evaluate_form_metrics(
        hull, reference_station_x_m=0.0, catch_zone_forward_m=(2.0, 9.0)
    )
    assert "catch zone clipped at the bow" in clipped.notes
    default = evaluate_form_metrics(hull)
    assert default.reference_station_origin == "section_area_centroid"
    assert abs(default.reference_station_x_m) < 0.2 * hull.length_m


def test_draft_beyond_the_body_reports_no_ratio() -> None:
    metrics = evaluate_form_metrics(_base(), class_ratio_draft_m=5.0)
    assert metrics.class_length_beam_ratio is None
    assert "no waterline at the stated class draft" in metrics.notes


@pytest.mark.parametrize(
    "kwargs",
    [
        {"class_ratio_draft_m": 0.0},
        {"class_ratio_draft_m": float("nan")},
        {"catch_zone_forward_m": (1.0, 1.0)},
        {"reference_station_x_m": 99.0},
    ],
)
def test_form_metrics_refuse_bad_inputs(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        evaluate_form_metrics(_base(), **kwargs)  # type: ignore[arg-type]


def test_evaluation_result_omits_unset_form_metrics() -> None:
    hull = _base()
    result = EvaluationResult(hull_hash=hull.hash(), hydrostatics=evaluate(hull))
    assert "form_metrics" not in json.loads(result.model_dump_json())
    with_block = result.model_copy(update={"form_metrics": evaluate_form_metrics(hull)})
    restored = EvaluationResult.model_validate_json(with_block.model_dump_json())
    assert restored.form_metrics == with_block.form_metrics


def test_cli_form_metrics_flag(tmp_path: Path) -> None:
    hull_path = tmp_path / "hull.json"
    hull_path.write_text(FIXTURE.read_text())
    runner = CliRunner()
    plain = tmp_path / "plain.json"
    assert runner.invoke(
        app, ["evaluate", str(hull_path), "--skip-resistance", "--out", str(plain)]
    ).exit_code == 0
    assert "form_metrics" not in json.loads(plain.read_text())
    out = tmp_path / "form.json"
    result = runner.invoke(
        app,
        ["evaluate", str(hull_path), "--skip-resistance", "--form-metrics",
         "--class-ratio-draft-m", "0.09", "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    block = json.loads(out.read_text())["form_metrics"]
    assert block["class_ratio_draft_m"] == pytest.approx(0.09)
    assert block["class_length_beam_ratio"] > 0
    bad = runner.invoke(
        app,
        ["evaluate", str(hull_path), "--skip-resistance", "--form-metrics",
         "--class-ratio-draft-m", "-1", "--out", str(tmp_path / "bad.json")],
    )
    assert bad.exit_code == 1


# ----- multi-load righting arms -----

LIGHT = {"name": "day", "paddler_mass_kg": 82.0, "hull_mass_kg": 18.0}
HEAVY = {"name": "trip", "paddler_mass_kg": 82.0, "hull_mass_kg": 18.0, "cargo_mass_kg": 30.0}


def test_load_case_table_matches_single_load_blocks() -> None:
    hull = _with(_base(), topsides={"sheer_beam_ratio": 1.15, "sheer_height_frac": 0.6})
    grid = [0.0, 10.0, 20.0]
    cases = [LoadCase.model_validate(LIGHT), LoadCase.model_validate(HEAVY)]
    table = build_load_case_gz_table(hull, cases, heel_grid_deg=grid)
    assert [entry["name"] for entry in table["load_cases"]] == ["day", "trip"]
    assert table["load_cases"][1]["total_mass_kg"] == pytest.approx(130.0)
    for entry, case in zip(table["load_cases"], cases):
        assert entry["high_angle_gz"] == build_high_angle_gz_block(hull, case, heel_grid_deg=grid)
    day, trip = (
        [point["gz_m"] for point in entry["high_angle_gz"]["heel_points"]]
        for entry in table["load_cases"]
    )
    assert day != trip


def test_load_case_table_refuses_ambiguous_names() -> None:
    hull = _base()
    with pytest.raises(ValueError, match="unique"):
        build_load_case_gz_table(
            hull, [LoadCase(name="a"), LoadCase(name="a")], heel_grid_deg=[0.0, 10.0]
        )
    with pytest.raises(ValueError, match="non-blank"):
        build_load_case_gz_table(hull, [LoadCase(name=" ")], heel_grid_deg=[0.0, 10.0])
    with pytest.raises(ValueError, match="at least one"):
        build_load_case_gz_table(hull, [], heel_grid_deg=[0.0, 10.0])


# ----- sweep -----


def _sweep_spec(**evaluators: object) -> SweepSpec:
    # The deterministic sweep merges flat top-level fields; the base
    # hull carries the section exponent and the sweep varies length.
    base = json.loads(FIXTURE.read_text())
    base["distribution_v2"]["section_exponent"] = 4.0
    return SweepSpec(
        name="rfc0089",
        base_hull=base,
        variables={"length_m": {"kind": "values", "values": [5.0, 5.4864]}},
        evaluators={"hydrostatics": True, **evaluators},
    )


def test_default_evaluator_options_keep_their_serialized_form() -> None:
    dumped = EvaluatorOptions().model_dump(mode="json")
    for name in (
        "form_metrics",
        "form_metrics_class_ratio_draft_m",
        "form_metrics_catch_zone_forward_m",
        "high_angle_gz_load_cases",
    ):
        assert name not in dumped
    restored = EvaluatorOptions.model_validate(
        EvaluatorOptions(form_metrics=True, high_angle_gz_load_cases=[LIGHT]).model_dump(mode="json")
    )
    assert restored.form_metrics is True
    assert restored.high_angle_gz_load_cases == [LIGHT]


def test_evaluator_options_refuse_bad_rfc0089_values() -> None:
    with pytest.raises(ValidationError):
        EvaluatorOptions(high_angle_gz_load_cases=[LIGHT, LIGHT])
    with pytest.raises(ValidationError):
        EvaluatorOptions(high_angle_gz_load_cases=[{"name": "x", "unknown": 1}])
    with pytest.raises(ValidationError):
        EvaluatorOptions(form_metrics_catch_zone_forward_m=(1.2, 0.6))
    with pytest.raises(ValidationError):
        EvaluatorOptions(form_metrics_class_ratio_draft_m=0.0)


def test_sweep_reports_form_metrics_and_load_cases(tmp_path: Path) -> None:
    spec = _sweep_spec(
        form_metrics=True,
        high_angle_gz_heel_grid_deg=[0.0, 10.0, 20.0],
        high_angle_gz_load_cases=[LIGHT, HEAVY],
    )
    run = run_sweep(spec, tmp_path)
    assert run.completed_count == 2
    by_length = {record.parameters["length_m"]: record for record in run.candidates}
    short, long = by_length[5.0], by_length[5.4864]
    assert long.summary["displaced_mass_kg"] > short.summary["displaced_mass_kg"]
    assert long.summary["form.class_length_beam_ratio"] > short.summary["form.class_length_beam_ratio"]
    assert long.summary["form.class_waterline_beam_m"] == pytest.approx(
        short.summary["form.class_waterline_beam_m"], rel=1e-6
    )
    for record in run.candidates:
        table = json.loads((tmp_path / record.artifacts["load_case_gz"]).read_text())
        assert [entry["name"] for entry in table["load_cases"]] == ["day", "trip"]
        for entry in table["load_cases"]:
            for point in entry["high_angle_gz"]["heel_points"]:
                key = f"load_case_gz.{entry['name']}.gz_m_at_{point['heel_deg']:g}deg"
                assert record.summary[key] == point["gz_m"]
        evaluation = EvaluationResult.model_validate_json(
            (tmp_path / record.artifacts["evaluation"]).read_text()
        )
        assert evaluation.form_metrics is not None
        assert evaluation.form_metrics.class_length_beam_ratio == pytest.approx(
            record.summary["form.class_length_beam_ratio"]
        )
    with (tmp_path / "summary.csv").open() as handle:
        header = next(csv.reader(handle))
    assert "form.class_length_beam_ratio" in header
    assert "form.catch_zone_max_beam_m" in header


def test_sweep_without_rfc0089_options_is_unchanged(tmp_path: Path) -> None:
    run = run_sweep(_sweep_spec(), tmp_path)
    for record in run.candidates:
        assert "load_case_gz" not in record.artifacts
        assert not any(key.startswith(("form.", "load_case_gz.")) for key in record.summary)
        assert "form_metrics" not in record.evaluator_settings
        assert "form_metrics" not in json.loads(
            (tmp_path / record.artifacts["evaluation"]).read_text()
        )
    with (tmp_path / "summary.csv").open() as handle:
        header = next(csv.reader(handle))
    assert not any(column.startswith("form.") for column in header)
