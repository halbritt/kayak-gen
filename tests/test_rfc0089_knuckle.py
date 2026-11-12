"""RFC 0089 stage 4 — section knuckles in the form metrics."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from kayakgen.eval.form_metrics import (
    DEFAULT_KNUCKLE_PROBE_M,
    FormMetrics,
    _section_knuckles,
    evaluate_form_metrics,
)
from kayakgen.model.hull import Hull
from kayakgen.search.objectives import OBJECTIVE_METADATA
from kayakgen.search.sweep import SweepSpec, run_sweep

FIXTURE = Path(__file__).parent / "fixtures" / "hulls" / "needle18-v2.json"
KNUCKLE_KEYS = ("form.upper_knuckle_max_deg", "form.waterline_knuckle_max_deg")


def _base() -> Hull:
    return Hull.model_validate_json(FIXTURE.read_text())


def _with_topsides(**topsides: object) -> Hull:
    payload = _base().model_dump()
    payload["distribution_v2"]["topsides"] = topsides
    return Hull.model_validate(payload)


def test_sharp_corners_read_their_full_angle() -> None:
    hull = np.array([[-0.2, 0.0], [0.0, -0.1], [0.2, 0.0]])
    deck = np.array([[-0.2, 0.0], [-0.2, 0.1], [0.0, 0.1], [0.2, 0.1], [0.2, 0.0]])
    joint, upper, height = _section_knuckles(hull, deck, 0.002)
    assert joint == pytest.approx(90.0 - np.degrees(np.arctan2(0.1, 0.2)), abs=1e-6)
    assert upper == pytest.approx(90.0, abs=1e-6)
    assert height == pytest.approx(0.1, abs=1e-9)
    # The reading of a true corner does not depend on the probe length.
    assert _section_knuckles(hull, deck, 0.01)[1] == pytest.approx(90.0, abs=1e-6)


def test_smooth_curve_reads_probe_over_radius() -> None:
    radius, probe = 0.1, 0.002
    lower = np.linspace(-np.pi / 2.0, 0.0, 400)
    upper = np.linspace(0.0, np.pi / 2.0, 400)
    half_hull = np.column_stack((radius * np.cos(lower), radius * np.sin(lower)))
    half_deck = np.column_stack((radius * np.cos(upper), radius * np.sin(upper)))
    hull = np.vstack((half_hull[::-1] * [-1.0, 1.0], half_hull[1:]))
    deck = np.vstack((half_deck * [-1.0, 1.0], half_deck[::-1][1:]))
    joint, upper_deg, _ = _section_knuckles(hull, deck, probe)
    expected = np.degrees(probe / radius)
    assert joint == pytest.approx(expected, rel=0.05)
    assert upper_deg == pytest.approx(expected, rel=0.05)


def test_degenerate_rings_read_zero() -> None:
    empty = np.zeros((0, 2))
    assert _section_knuckles(empty, empty, 0.002) == (0.0, 0.0, 0.0)
    point = np.zeros((5, 2))
    assert _section_knuckles(point, point, 0.002) == (0.0, 0.0, 0.0)


def test_knuckle_fields_are_reported_and_located() -> None:
    metrics = evaluate_form_metrics(_base())
    assert metrics.knuckle_probe_m == pytest.approx(DEFAULT_KNUCKLE_PROBE_M)
    assert 0.0 <= metrics.upper_knuckle_max_deg <= 180.0
    assert 0.0 <= metrics.waterline_knuckle_max_deg <= 180.0
    half = _base().length_m / 2.0
    assert abs(metrics.upper_knuckle_x_m) <= 0.9 * half + 1e-9
    assert abs(metrics.waterline_knuckle_x_m) <= 0.9 * half + 1e-9
    assert metrics.upper_knuckle_height_m >= 0.0


def test_matches_direct_section_measurement() -> None:
    hull = _with_topsides(sheer_beam_ratio=1.2, sheer_height_frac=0.3)
    metrics = evaluate_form_metrics(hull)
    geom = hull.to_geometry()
    x = metrics.upper_knuckle_x_m
    joint, upper, height = _section_knuckles(
        np.asarray(geom.section(x, "hull"), dtype=float),
        np.asarray(geom.section(x, "deck"), dtype=float),
        DEFAULT_KNUCKLE_PROBE_M,
    )
    assert upper == pytest.approx(metrics.upper_knuckle_max_deg)
    assert height == pytest.approx(metrics.upper_knuckle_height_m)
    assert joint <= metrics.waterline_knuckle_max_deg + 1e-9


def test_low_flared_deck_edge_is_a_sharper_knuckle() -> None:
    upright = evaluate_form_metrics(_with_topsides(sheer_beam_ratio=1.0, sheer_height_frac=0.7))
    flared = evaluate_form_metrics(_with_topsides(sheer_beam_ratio=1.2, sheer_height_frac=0.3))
    assert flared.upper_knuckle_max_deg > upright.upper_knuckle_max_deg + 5.0
    assert flared.upper_knuckle_height_m < upright.upper_knuckle_height_m
    # A flared topside leaves the waterline along the hull, so that joint is fair.
    assert flared.waterline_knuckle_max_deg < upright.waterline_knuckle_max_deg


def test_span_limits_the_stations_read() -> None:
    hull = _with_topsides(sheer_beam_ratio=1.2, sheer_height_frac=0.3)
    wide = evaluate_form_metrics(hull, knuckle_span_xi=0.9)
    narrow = evaluate_form_metrics(hull, knuckle_span_xi=0.2)
    assert narrow.upper_knuckle_max_deg <= wide.upper_knuckle_max_deg + 1e-9
    assert abs(narrow.upper_knuckle_x_m) <= 0.2 * hull.length_m / 2.0 + 1e-9


@pytest.mark.parametrize(
    "kwargs",
    [
        {"knuckle_probe_m": 0.0},
        {"knuckle_probe_m": float("nan")},
        {"knuckle_span_xi": 0.0},
        {"knuckle_span_xi": 1.5},
    ],
)
def test_bad_knuckle_inputs_are_refused(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        evaluate_form_metrics(_base(), **kwargs)


def test_blocks_written_before_knuckles_still_load() -> None:
    block = evaluate_form_metrics(_base()).model_dump(mode="json")
    old = {key: value for key, value in block.items() if "knuckle" not in key}
    restored = FormMetrics.model_validate(old)
    assert restored.upper_knuckle_max_deg is None
    assert restored.waterline_knuckle_max_deg is None
    assert restored.foot_clear_height_m == block["foot_clear_height_m"]


def test_sweep_reports_knuckles(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="knuckle",
        base_hull=json.loads(FIXTURE.read_text()),
        variables={"length_m": {"kind": "values", "values": [5.4864]}},
        evaluators={"hydrostatics": True, "form_metrics": True},
    )
    summary = run_sweep(spec, tmp_path / "knuckle").candidates[0].summary
    direct = evaluate_form_metrics(_base())
    assert summary["form.upper_knuckle_max_deg"] == pytest.approx(direct.upper_knuckle_max_deg)
    assert summary["form.waterline_knuckle_max_deg"] == pytest.approx(
        direct.waterline_knuckle_max_deg
    )


def test_knuckle_metrics_are_exploratory_objectives() -> None:
    for key in KNUCKLE_KEYS:
        metadata = OBJECTIVE_METADATA[key]
        assert metadata.role == "explicit_exploratory"
        assert metadata.direction == "min"
