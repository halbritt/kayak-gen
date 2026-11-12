"""RFC 0089 stage 3 — foot room in the form metrics."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.form_metrics import FormMetrics, evaluate_form_metrics
from kayakgen.model.hull import Hull
from kayakgen.search.objectives import OBJECTIVE_METADATA
from kayakgen.search.sweep import EvaluatorOptions, SweepSpec, run_sweep

FIXTURE = Path(__file__).parent / "fixtures" / "hulls" / "needle18-v2.json"
FOOT_KEYS = ("form.foot_clear_height_m", "form.foot_clear_width_m", "form.foot_station_beam_m")


def _base() -> Hull:
    return Hull.model_validate_json(FIXTURE.read_text())


def _with_topsides(**topsides: object) -> Hull:
    payload = _base().model_dump()
    payload["distribution_v2"]["topsides"] = topsides
    return Hull.model_validate(payload)


def _z_at(ring: np.ndarray, y: float) -> float:
    order = np.argsort(ring[:, 0])
    return float(np.interp(y, ring[order, 0], ring[order, 1]))


def test_foot_box_matches_direct_section_measurement() -> None:
    hull = _base()
    width = 0.24
    metrics = evaluate_form_metrics(
        hull, reference_station_x_m=0.0, foot_station_forward_m=0.8, foot_box_width_m=width
    )
    geom = hull.to_geometry()
    lower = np.asarray(geom.section(-0.8, "hull"), dtype=float)
    upper = np.asarray(geom.section(-0.8, "deck"), dtype=float)
    expected = _z_at(upper, width / 2.0) - _z_at(lower, width / 2.0)
    assert metrics.foot_clear_height_m == pytest.approx(expected, abs=1e-9)
    assert metrics.foot_station_depth_m == pytest.approx(
        float(upper[:, 1].max() - lower[:, 1].min()), abs=1e-9
    )
    assert metrics.foot_station_beam_m == pytest.approx(2.0 * float(np.abs(lower[:, 0]).max()))
    assert 0.0 < metrics.foot_clear_height_m < metrics.foot_station_depth_m


def test_clear_width_and_clear_height_are_inverse() -> None:
    hull = _base()
    first = evaluate_form_metrics(hull, foot_box_height_m=0.15)
    assert 0.0 < first.foot_clear_width_m < first.foot_station_beam_m
    second = evaluate_form_metrics(hull, foot_box_width_m=first.foot_clear_width_m)
    assert second.foot_clear_height_m == pytest.approx(0.15, abs=1e-6)


def test_wider_box_and_forward_station_have_less_room() -> None:
    hull = _base()
    narrow = evaluate_form_metrics(hull, foot_box_width_m=0.20)
    wide = evaluate_form_metrics(hull, foot_box_width_m=0.34)
    assert wide.foot_clear_height_m < narrow.foot_clear_height_m
    near = evaluate_form_metrics(hull, foot_station_forward_m=0.8, foot_box_height_m=0.15)
    far = evaluate_form_metrics(hull, foot_station_forward_m=1.6, foot_box_height_m=0.15)
    assert far.foot_clear_width_m < near.foot_clear_width_m
    assert far.foot_station_beam_m < near.foot_station_beam_m


def test_box_too_tall_reports_zero_width() -> None:
    metrics = evaluate_form_metrics(_base(), foot_box_height_m=2.0)
    assert metrics.foot_clear_width_m == 0.0
    assert metrics.foot_station_depth_m > 0.0


def test_deck_shape_changes_foot_room() -> None:
    tall = evaluate_form_metrics(
        _with_topsides(sheer_beam_ratio=1.0, sheer_height_frac=0.7, deck_crown_exponent=8.0)
    )
    low = evaluate_form_metrics(
        _with_topsides(sheer_beam_ratio=1.0, sheer_height_frac=0.2, deck_crown_exponent=2.0)
    )
    assert tall.foot_clear_height_m > low.foot_clear_height_m
    pinched = evaluate_form_metrics(
        _with_topsides(sheer_beam_ratio=0.7, sheer_height_frac=0.7), foot_box_height_m=0.15
    )
    upright = evaluate_form_metrics(
        _with_topsides(sheer_beam_ratio=1.0, sheer_height_frac=0.7), foot_box_height_m=0.15
    )
    assert pinched.foot_clear_width_m < upright.foot_clear_width_m


def test_foot_station_forward_of_the_bow_is_noted() -> None:
    metrics = evaluate_form_metrics(_base(), foot_station_forward_m=50.0)
    assert "foot station is forward of the bow" in metrics.notes
    assert metrics.foot_clear_height_m == 0.0
    assert metrics.foot_clear_width_m == 0.0
    assert metrics.foot_station_beam_m == 0.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"foot_station_forward_m": -0.1},
        {"foot_station_forward_m": float("nan")},
        {"foot_box_width_m": 0.0},
        {"foot_box_height_m": float("inf")},
    ],
)
def test_bad_foot_inputs_are_refused(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        evaluate_form_metrics(_base(), **kwargs)


def test_blocks_written_before_foot_room_still_load() -> None:
    block = evaluate_form_metrics(_base()).model_dump(mode="json")
    old = {key: value for key, value in block.items() if not key.startswith("foot_")}
    restored = FormMetrics.model_validate(old)
    assert restored.foot_clear_height_m is None
    assert restored.class_length_beam_ratio == block["class_length_beam_ratio"]


def test_foot_options_are_omitted_at_default_and_validated() -> None:
    dumped = EvaluatorOptions(form_metrics=True).model_dump(mode="json")
    assert not any(name.startswith("form_metrics_foot") for name in dumped)
    custom = EvaluatorOptions(form_metrics=True, form_metrics_foot_box_width_m=0.28)
    restored = EvaluatorOptions.model_validate(custom.model_dump(mode="json"))
    assert restored.form_metrics_foot_box_width_m == pytest.approx(0.28)
    with pytest.raises(ValidationError):
        EvaluatorOptions(form_metrics_foot_box_height_m=0.0)
    with pytest.raises(ValidationError):
        EvaluatorOptions(form_metrics_foot_station_forward_m=-1.0)


def test_sweep_reports_foot_room(tmp_path: Path) -> None:
    def run(name: str, **evaluators: object):  # type: ignore[no-untyped-def]
        spec = SweepSpec(
            name=name,
            base_hull=json.loads(FIXTURE.read_text()),
            variables={"length_m": {"kind": "values", "values": [5.4864]}},
            evaluators={"hydrostatics": True, "form_metrics": True, **evaluators},
        )
        return run_sweep(spec, tmp_path / name).candidates[0].summary

    default = run("default")
    assert all(default[key] is not None for key in FOOT_KEYS)
    direct = evaluate_form_metrics(_base())
    assert default["form.foot_clear_height_m"] == pytest.approx(direct.foot_clear_height_m)
    narrow = run("narrow", form_metrics_foot_box_width_m=0.2)
    assert narrow["form.foot_clear_height_m"] > default["form.foot_clear_height_m"]


def test_foot_metrics_are_exploratory_objectives() -> None:
    for key in FOOT_KEYS:
        metadata = OBJECTIVE_METADATA[key]
        assert metadata.role == "explicit_exploratory"
        assert metadata.direction == "max"


def test_cli_foot_flags(tmp_path: Path) -> None:
    hull_path = tmp_path / "hull.json"
    hull_path.write_text(FIXTURE.read_text())
    out = tmp_path / "form.json"
    result = CliRunner().invoke(
        app,
        ["evaluate", str(hull_path), "--skip-resistance", "--form-metrics",
         "--foot-station-forward-m", "0.9", "--foot-box-width-m", "0.25",
         "--foot-box-height-m", "0.2", "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    block = json.loads(out.read_text())["form_metrics"]
    assert block["foot_station_forward_m"] == pytest.approx(0.9)
    assert block["foot_box_width_m"] == pytest.approx(0.25)
    assert block["foot_clear_height_m"] > 0
    bad = CliRunner().invoke(
        app,
        ["evaluate", str(hull_path), "--skip-resistance", "--form-metrics",
         "--foot-box-width-m", "0", "--out", str(tmp_path / "bad.json")],
    )
    assert bad.exit_code == 1
