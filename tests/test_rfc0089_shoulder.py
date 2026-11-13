"""RFC 0089 stage 5 — rounded shoulder, true-outline knuckles and the hollow measure."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from kayakgen.eval.form_metrics import (
    DEFAULT_KNUCKLE_PROBE_M,
    FormMetrics,
    _outline_hollow,
    _outline_knuckles,
    evaluate_form_metrics,
)
from kayakgen.model.hull import Hull
from kayakgen.search.objectives import OBJECTIVE_METADATA
from kayakgen.search.sweep import SweepSpec, run_sweep

FIXTURE = Path(__file__).parent / "fixtures" / "hulls" / "needle18-v2.json"
STATIONS = (-0.7, -0.4, -0.1, 0.0, 0.3, 0.6, 0.85)
# A low, flared deck edge under a square deck: a hard corner without rounding.
CORNERED = {"sheer_beam_ratio": 1.2, "sheer_height_frac": 0.3, "deck_crown_exponent": 10.0}


def _base() -> Hull:
    return Hull.model_validate_json(FIXTURE.read_text())


def _with_topsides(**topsides: object) -> Hull:
    payload = _base().model_dump()
    payload["distribution_v2"]["topsides"] = topsides
    return Hull.model_validate(payload)


def _turns_deg(points: np.ndarray) -> np.ndarray:
    steps = np.diff(points, axis=0)
    steps = steps[np.linalg.norm(steps, axis=1) > 1e-12]
    cross = steps[:-1, 0] * steps[1:, 1] - steps[:-1, 1] * steps[1:, 0]
    dot = (steps[:-1] * steps[1:]).sum(axis=1)
    return np.degrees(np.arctan2(cross, dot))


def test_unset_shoulder_is_not_serialized_and_bad_values_are_refused() -> None:
    plain = _with_topsides(sheer_beam_ratio=1.1)
    assert "shoulder_round_m" not in plain.model_dump()["distribution_v2"]["topsides"]
    rounded = _with_topsides(sheer_beam_ratio=1.1, shoulder_round_m=0.03)
    assert rounded.model_dump()["distribution_v2"]["topsides"]["shoulder_round_m"] == 0.03
    for bad in (0.0, -0.01, 0.5, float("nan")):
        with pytest.raises(ValidationError):
            _with_topsides(sheer_beam_ratio=1.1, shoulder_round_m=bad)


def test_rounding_removes_the_deck_edge_corner() -> None:
    cornered = evaluate_form_metrics(_with_topsides(**CORNERED))
    rounded = evaluate_form_metrics(_with_topsides(**CORNERED, shoulder_round_m=0.03))
    assert cornered.upper_knuckle_max_deg > 40.0
    assert rounded.upper_knuckle_max_deg < 20.0
    assert rounded.waterline_knuckle_max_deg < 2.0


def test_wall_sided_topside_no_longer_creases_the_waterline() -> None:
    upright = {"sheer_beam_ratio": 1.0, "sheer_height_frac": 0.6}
    creased = evaluate_form_metrics(_with_topsides(**upright))
    rounded = evaluate_form_metrics(_with_topsides(**upright, shoulder_round_m=0.03))
    assert creased.waterline_knuckle_max_deg > 20.0
    assert rounded.waterline_knuckle_max_deg < 2.0


def test_rounded_outline_has_no_corner_at_any_station() -> None:
    hull = _with_topsides(**CORNERED, shoulder_round_m=0.03)
    geom = hull.to_geometry()
    for xi in STATIONS:
        lower, upper = geom.half_section_outline(xi * hull.length_m / 2.0)
        # No single step of the fine outline turns more than a few degrees.
        assert np.abs(_turns_deg(np.vstack((lower[-2:], upper[1:])))).max() < 6.0


def test_rounded_ring_keeps_count_ends_and_lies_on_the_outline() -> None:
    plain = _with_topsides(**CORNERED).to_geometry()
    hull = _with_topsides(**CORNERED, shoulder_round_m=0.03)
    geom = hull.to_geometry()
    for xi in STATIONS:
        x = xi * hull.length_m / 2.0
        ring, reference = geom.section(x, "deck"), plain.section(x, "deck")
        assert ring.shape == reference.shape
        np.testing.assert_allclose(ring[0], reference[0], atol=1e-12)
        np.testing.assert_allclose(ring[-1], reference[-1], atol=1e-12)
        np.testing.assert_allclose(ring[:, 0], -ring[::-1, 0], atol=1e-12)
        np.testing.assert_allclose(ring[ring.shape[0] // 2], reference[ring.shape[0] // 2], atol=1e-12)
        upper = geom.half_section_outline(x)[1]
        for point in ring[ring.shape[0] // 2 :]:
            assert np.linalg.norm(upper - point, axis=1).min() < 2e-3


def test_rounded_side_meets_the_hull_on_its_own_line() -> None:
    hull = _with_topsides(sheer_beam_ratio=1.0, sheer_height_frac=0.6, shoulder_round_m=0.03)
    geom = hull.to_geometry()
    for xi in STATIONS:
        lower, upper = geom.half_section_outline(xi * hull.length_m / 2.0)
        np.testing.assert_allclose(lower[-1], upper[0], atol=1e-12)
        assert abs(_turns_deg(np.vstack((lower[-2:], upper[1:2])))[0]) < 2.0


def test_larger_round_gives_a_gentler_shoulder() -> None:
    tight = evaluate_form_metrics(
        _with_topsides(**CORNERED, shoulder_round_m=0.005), knuckle_span_xi=0.5
    )
    wide = evaluate_form_metrics(
        _with_topsides(**CORNERED, shoulder_round_m=0.04), knuckle_span_xi=0.5
    )
    assert wide.upper_knuckle_max_deg < tight.upper_knuckle_max_deg


def test_sheer_is_the_widest_point_of_a_rounded_side() -> None:
    hull = _with_topsides(sheer_beam_ratio=1.0, sheer_height_frac=0.6, shoulder_round_m=0.03)
    geom = hull.to_geometry()
    x = 0.1
    upper = geom.half_section_outline(x)[1]
    widest = int(np.argmax(upper[:, 0]))
    assert upper[widest, 0] > upper[0, 0]
    assert geom.sheer_z_at(x) == pytest.approx(upper[widest, 1])
    assert not geom.is_tumblehome_at(x)
    row = geom.sheer_line(3)[1]
    middle = geom.half_section_outline(0.0)[1]
    assert row[1] == pytest.approx(middle[:, 0].max())


def test_unrounded_hull_rings_are_unchanged_by_the_true_outline() -> None:
    hull = _with_topsides(**CORNERED)
    geom = hull.to_geometry()
    x = 0.4
    lower, upper = geom.half_section_outline(x)
    ring = geom.section(x, "deck")
    # The corner of the ring is a vertex of the true outline.
    sheer_z = geom.sheer_z_at(x)
    assert np.abs(upper[:, 1] - sheer_z).min() < 1e-12
    for point in ring[ring.shape[0] // 2 :]:
        assert np.linalg.norm(upper - point, axis=1).min() < 2e-3
    np.testing.assert_allclose(lower[-1], upper[0], atol=1e-12)


def test_hollow_reads_the_wrong_way_turn() -> None:
    lower = np.array([[0.0, -0.1], [0.2, 0.0]])
    convex = np.array([[0.2, 0.0], [0.25, 0.05], [0.25, 0.1], [0.0, 0.15]])
    assert _outline_hollow(lower, convex) == pytest.approx(0.0, abs=1e-9)
    # Out, straight back in over the waterline edge, then out again: 90 degrees to recover.
    waisted = np.array([[0.2, 0.0], [0.25, 0.05], [0.2, 0.1], [0.25, 0.15], [0.0, 0.2]])
    assert _outline_hollow(lower, waisted) == pytest.approx(90.0, abs=1e-6)
    assert _outline_hollow(lower[:1], convex) == 0.0


def test_narrow_sheer_over_a_rounded_side_reads_as_hollow() -> None:
    full = evaluate_form_metrics(
        _with_topsides(sheer_beam_ratio=1.25, sheer_height_frac=0.5, shoulder_round_m=0.03)
    )
    waisted = evaluate_form_metrics(
        _with_topsides(
            sheer_beam_ratio=0.8,
            sheer_height_frac=0.5,
            deck_crown_exponent=10.0,
            shoulder_round_m=0.03,
        )
    )
    assert full.upper_hollow_max_deg < 1.0
    assert waisted.upper_hollow_max_deg > 5.0
    assert abs(waisted.upper_hollow_x_m) <= 0.9 * _base().length_m / 2.0 + 1e-9


def test_knuckles_are_measured_on_the_true_outline() -> None:
    hull = _with_topsides(**CORNERED)
    metrics = evaluate_form_metrics(hull)
    geom = hull.to_geometry()
    lower, upper = geom.half_section_outline(metrics.upper_knuckle_x_m)
    _, direct, height = _outline_knuckles(lower, upper, DEFAULT_KNUCKLE_PROBE_M)
    assert direct == pytest.approx(metrics.upper_knuckle_max_deg)
    assert height == pytest.approx(metrics.upper_knuckle_height_m)


def test_blocks_written_before_the_hollow_still_load() -> None:
    block = evaluate_form_metrics(_base()).model_dump()
    old = {key: value for key, value in block.items() if "hollow" not in key}
    assert FormMetrics.model_validate(old).upper_hollow_max_deg is None


def test_sweep_reports_the_hollow_of_a_rounded_hull(tmp_path: Path) -> None:
    base = json.loads(FIXTURE.read_text())
    base["distribution_v2"]["topsides"] = {**CORNERED, "shoulder_round_m": 0.02}
    spec = SweepSpec(
        name="shoulder",
        base_hull=base,
        variables={"length_m": {"kind": "values", "values": [5.4864]}},
        evaluators={"hydrostatics": True, "form_metrics": True},
    )
    summary = run_sweep(spec, tmp_path / "shoulder").candidates[0].summary
    direct = evaluate_form_metrics(Hull.model_validate(base))
    assert summary["form.upper_hollow_max_deg"] == pytest.approx(direct.upper_hollow_max_deg)
    assert summary["form.upper_knuckle_max_deg"] == pytest.approx(direct.upper_knuckle_max_deg)
    metadata = OBJECTIVE_METADATA["form.upper_hollow_max_deg"]
    assert metadata.role == "explicit_exploratory"
    assert metadata.direction == "min"
