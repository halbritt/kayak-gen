"""RFC 0089 stage 6 — round sections that turn up to the waterline."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from kayakgen.eval.form_metrics import evaluate_form_metrics
from kayakgen.model.hull import Hull

FIXTURE = Path(__file__).parent / "fixtures" / "hulls" / "needle18-v2.json"
STATIONS = (-0.7, -0.4, 0.0, 0.3, 0.6)


def _hull(**distribution: object) -> Hull:
    payload = Hull.model_validate_json(FIXTURE.read_text()).model_dump()
    payload["distribution_v2"].update(distribution)
    return Hull.model_validate(payload)


def test_unset_side_exponent_is_omitted_and_changes_nothing() -> None:
    base = Hull.model_validate_json(FIXTURE.read_text())
    assert "section_side_exponent" not in base.model_dump()["distribution_v2"]
    assert base.distribution_v2.sample_section_side_exponent(0.0) is None
    set_hull = _hull(section_side_exponent=2.0)
    assert set_hull.model_dump()["distribution_v2"]["section_side_exponent"] == 2.0


@pytest.mark.parametrize("bad", [0.5, 7.0, float("nan")])
def test_out_of_range_side_exponent_is_refused(bad: float) -> None:
    with pytest.raises(ValidationError):
        _hull(section_side_exponent=bad)


def test_side_exponent_is_refused_for_other_families() -> None:
    with pytest.raises(ValidationError, match="only to the 'round'"):
        _hull(cross_section_family="shallow_v", section_side_exponent=2.0)


def test_side_meets_the_waterline_upright() -> None:
    flared = _hull().to_geometry()
    upright = _hull(section_side_exponent=2.0).to_geometry()
    for xi in STATIONS:
        x = xi * flared.L / 2.0
        assert flared._hull_waterline_tangent(x)[0] > 0.3
        assert upright._hull_waterline_tangent(x)[0] < 0.05


def test_ring_keeps_count_breadth_and_keel_depth() -> None:
    plain = _hull().to_geometry()
    turned = _hull(section_side_exponent=2.5).to_geometry()
    for xi in STATIONS:
        x = xi * plain.L / 2.0
        before, after = plain.section(x, "hull"), turned.section(x, "hull")
        assert before.shape == after.shape
        np.testing.assert_allclose(after[0], before[0], atol=1e-12)
        np.testing.assert_allclose(after[-1], before[-1], atol=1e-12)
        middle = before.shape[0] // 2
        np.testing.assert_allclose(after[middle], before[middle], atol=1e-12)
        assert np.all(np.diff(after[after.shape[0] // 2 :, 0]) >= 0.0)
        # The explicit rocker lifts the keel a little above the floor beside it.
        assert np.all(np.diff(after[after.shape[0] // 2 :, 1]) >= -5e-4)
        assert turned.section_area(x) > plain.section_area(x)


def test_equal_exponents_of_two_give_an_ellipse() -> None:
    hull = _hull(section_exponent=2.0, section_side_exponent=2.0, deadrise_deg=0.0)
    geom = hull.to_geometry()
    x = 0.0
    half_b, draft = geom._half_breadth_at(x), geom._draft_at(x)
    arc = geom._hull_quarter_section(x, 400)
    # The explicit rocker lifts the keel; compare the shape without it.
    lift = geom._rocker_at(x)
    assert lift == pytest.approx(0.0, abs=1e-12)
    radius = (arc[:, 0] / half_b) ** 2 + (arc[:, 1] / draft) ** 2
    np.testing.assert_allclose(radius, 1.0, atol=1e-9)


def test_larger_side_exponent_is_fuller() -> None:
    areas = [
        _hull(section_side_exponent=m).to_geometry().section_area(0.0) for m in (1.0, 1.5, 2.5, 4.0)
    ]
    assert areas == sorted(areas)
    assert areas[0] == pytest.approx(_hull().to_geometry().section_area(0.0), rel=2e-2)


def test_upright_side_under_a_wall_sided_topside_has_no_waterline_crease() -> None:
    topsides = {"sheer_beam_ratio": 1.0, "sheer_height_frac": 0.6}
    creased = evaluate_form_metrics(_hull(topsides=topsides))
    fair = evaluate_form_metrics(_hull(topsides=topsides, section_side_exponent=2.0))
    assert creased.waterline_knuckle_max_deg > 20.0
    assert fair.waterline_knuckle_max_deg < 3.0
    assert fair.upper_hollow_max_deg < 3.0
