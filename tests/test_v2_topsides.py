"""RFC 0088 — distribution_v2 topsides (above-waterline hull sides)."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from kayakgen.eval.closed_volume import (
    diagnose_closed_volume_body,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.contract import LoadCase
from kayakgen.eval.hydrostatics import evaluate
from kayakgen.eval.stability import evaluate_gz_curve
from kayakgen.model.distribution_v2 import KeyPointsDistribution, TopsidesSpec
from kayakgen.model.hull import Hull
from kayakgen.services.build_export import write_offsets_csv

FIXTURE = Path(__file__).parent / "fixtures" / "hulls" / "needle18-v2.json"
RATIO = 1.15
FRAC = 0.6


def _base() -> Hull:
    return Hull.model_validate_json(FIXTURE.read_text())


def _with_topsides(hull: Hull, **topsides: object) -> Hull:
    payload = hull.model_dump()
    payload["distribution_v2"]["topsides"] = topsides or {
        "sheer_beam_ratio": RATIO,
        "sheer_height_frac": FRAC,
    }
    return Hull.model_validate(payload)


def _starboard(section: np.ndarray) -> np.ndarray:
    return section[len(section) // 2 :]


def test_unset_topsides_is_absent_from_serialized_records() -> None:
    hull = _base()
    assert hull.distribution_v2 is not None and hull.distribution_v2.topsides is None
    assert "topsides" not in hull.model_dump_json()
    assert "topsides" not in hull.distribution_v2.model_dump(mode="json")
    # The fixture file predates the field; identity must not move.
    assert hull.model_dump_json() == Hull.model_validate_json(hull.model_dump_json()).model_dump_json()


def test_topsides_round_trip_and_change_design_identity() -> None:
    base = _base()
    flared = _with_topsides(base)
    loaded = Hull.model_validate_json(flared.model_dump_json())
    assert loaded == flared
    assert loaded.distribution_v2.topsides == TopsidesSpec(
        sheer_beam_ratio=RATIO, sheer_height_frac=FRAC
    )
    assert flared.design_hash() != base.design_hash()
    assert flared.record_hash() != base.record_hash()
    wall_sided = _with_topsides(base, sheer_beam_ratio=1.0, sheer_height_frac=FRAC)
    assert wall_sided.design_hash() not in {base.design_hash(), flared.design_hash()}


def test_upper_ring_carries_sheer_and_keeps_ring_contract() -> None:
    base = _base()
    flared = _with_topsides(base)
    g0, g1 = base.to_geometry(), flared.to_geometry()
    for x in (-2.0, -0.7, 0.0, 1.1, 2.3):
        before, after = g0.section(x, "deck"), g1.section(x, "deck")
        assert after.shape == before.shape
        np.testing.assert_allclose(after[0], before[0])
        np.testing.assert_allclose(after[-1], before[-1])
        np.testing.assert_allclose(after[len(after) // 2], before[len(before) // 2])
        np.testing.assert_array_equal(g1.section(x, "hull"), g0.section(x, "hull"))

        half_b = g0._half_breadth_at(x)
        freeboard = g0._deck_height_at(x)
        quarter = _starboard(after)
        widest = int(np.argmax(quarter[:, 0]))
        assert quarter[widest, 0] == pytest.approx(RATIO * half_b)
        assert quarter[widest, 1] == pytest.approx(FRAC * freeboard)
        # Deck rises monotonically inboard of the sheer; the topside
        # strip descends monotonically to the waterline edge.
        assert np.all(np.diff(quarter[: widest + 1, 0]) > 0)
        assert np.all(np.diff(quarter[: widest + 1, 1]) <= 1e-12)
        assert np.all(np.diff(quarter[widest:, 0]) < 0)
        assert np.all(np.diff(quarter[widest:, 1]) < 0)
        assert quarter[:, 1].max() == pytest.approx(freeboard)


def test_sheer_line_reports_waterline_edge_without_topsides() -> None:
    base = _base()
    flared = _with_topsides(base)
    plain = base.to_geometry().sheer_line(21)
    sheer = flared.to_geometry().sheer_line(21)
    assert np.all(plain[:, 2] == 0.0)
    np.testing.assert_allclose(sheer[:, 1], RATIO * plain[:, 1])
    assert sheer[0, 1] == 0.0 and sheer[-1, 1] == 0.0  # flare vanishes at pointed ends
    assert np.all(sheer[:, 2] > 0.0)


def test_upright_hydrostatics_do_not_depend_on_topsides() -> None:
    base = evaluate(_base())
    flared = evaluate(_with_topsides(_base()))
    assert flared.displaced_volume_m3 == base.displaced_volume_m3
    assert flared.wetted_surface_m2 == base.wetted_surface_m2
    assert flared.waterplane_area_m2 == base.waterplane_area_m2
    assert flared.GM0_m == base.GM0_m


@pytest.mark.parametrize(
    "family", ["round", "shallow_arch", "shallow_v", "deep_v", "hard_chine", "multi_chine"]
)
def test_closed_body_with_topsides_passes_diagnostics(family: str) -> None:
    payload = _base().model_dump()
    payload["distribution_v2"]["cross_section_family"] = family
    payload["distribution_v2"]["topsides"] = {
        "sheer_beam_ratio": KeyPointsDistribution(
            knots=[(-1.0, 1.05), (0.0, 1.2), (1.0, 1.1)]
        ).model_dump(),
        "sheer_height_frac": 0.5,
    }
    body = generated_hull_plus_deck_body(
        Hull.model_validate(payload), stations=31, section_points=12
    )
    readiness = diagnose_closed_volume_body(body).readiness
    assert readiness.level == "closed_volume", readiness


def test_flared_topsides_raise_righting_arm_at_heel() -> None:
    load = LoadCase(
        paddler_mass_kg=81.6466266,
        cargo_mass_kg=15.87573295,
        hull_mass_kg=18.1436948,
        kg_above_keel_m=0.25,
    )

    def gz(hull: Hull) -> list[float]:
        body = generated_hull_plus_deck_body(hull, stations=41, section_points=16)
        curve = evaluate_gz_curve(
            hull,
            load,
            heel_grid_deg=[0.0, 5.0, 20.0, 30.0],
            body_ref=body,
            body_diagnostics=diagnose_closed_volume_body(body),
        )
        assert curve.status == "computed", curve.warnings
        return [float(v) for v in curve.gz_m]

    plain = gz(_base())
    wall = gz(_with_topsides(_base(), sheer_beam_ratio=1.0, sheer_height_frac=FRAC))
    flared = gz(_with_topsides(_base(), sheer_beam_ratio=1.2, sheer_height_frac=FRAC))
    assert plain[0] == pytest.approx(0.0, abs=1e-6)
    assert flared[0] == pytest.approx(0.0, abs=1e-6)
    for index in (2, 3):
        assert plain[index] < wall[index] < flared[index]
    assert flared[3] - plain[3] > 0.01  # more than 10 mm of righting arm at 30 degrees


@pytest.mark.parametrize(
    "topsides",
    [
        {"sheer_beam_ratio": 0.55},
        {"sheer_beam_ratio": 1.6},
        {"sheer_beam_ratio": float("nan")},
        {"sheer_height_frac": 0.0},
        {"sheer_height_frac": 1.0},
        {"sheer_beam_ratio": {"kind": "keypoints", "knots": [(-1.0, 1.1), (0.0, 0.9), (1.0, 1.1)]}},
        {"sheer_height_frac": {"kind": "polynomial", "coefficients": [0.5, 0.0, 0.6]}},
        {"flare_deg": 10.0},
    ],
)
def test_topsides_refuse_out_of_range_values(topsides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _with_topsides(_base(), **topsides)


def test_offsets_export_reports_sheer_above_waterline(tmp_path: Path) -> None:
    def sheer_column(hull: Hull, name: str) -> list[float]:
        out = write_offsets_csv(hull, tmp_path / name, n_stations=5)
        rows = [line for line in out.read_text().splitlines() if not line.startswith("#")]
        return [float(row["sheer_Z"]) for row in csv.DictReader(rows)]

    base = _base()
    assert sheer_column(base, "plain.csv")[2] == pytest.approx(0.0, abs=1e-9)
    flared = _with_topsides(base)
    expected = FRAC * flared.to_geometry()._deck_height_at(0.0)
    assert sheer_column(flared, "flared.csv")[2] == pytest.approx(expected, abs=1e-6)


@pytest.mark.parametrize(
    "family", ["round", "shallow_arch", "shallow_v", "deep_v", "hard_chine", "multi_chine"]
)
def test_topside_strip_leaves_waterline_along_hull_tangent(family: str) -> None:
    """No knuckle on the waterline: the strip continues the hull arc's direction."""

    payload = _base().model_dump()
    payload["distribution_v2"]["cross_section_family"] = family
    payload["distribution_v2"]["topsides"] = {"sheer_beam_ratio": 1.2, "sheer_height_frac": FRAC}
    geometry = Hull.model_validate(payload).to_geometry()
    geometry.num_points = 400

    def direction(start: np.ndarray, end: np.ndarray) -> float:
        return float(np.degrees(np.arctan2(end[1] - start[1], end[0] - start[0])))

    for x in (-2.2, -1.0, 0.3, 1.4, 2.4):
        hull_arc = geometry._hull_quarter_section(x)
        upper = geometry._deck_quarter_section(x)
        tangent_y, tangent_z = geometry._hull_waterline_tangent(x)
        expected = float(np.degrees(np.arctan2(tangent_z, tangent_y)))
        np.testing.assert_allclose(upper[-1], hull_arc[-1], atol=1e-12)
        assert direction(upper[-1], upper[-2]) == pytest.approx(expected, abs=2.0)
        widest = int(np.argmax(upper[:, 0]))
        strip = upper[widest:]
        assert np.all(np.diff(strip[:, 1]) < 0)
        assert np.all(np.diff(strip[:, 0]) <= 1e-12)


def test_waterline_tangent_is_independent_of_section_resolution() -> None:
    hull = _with_topsides(_base())
    coarse, fine = hull.to_geometry(), hull.to_geometry()
    coarse.num_points, fine.num_points = 12, 200
    assert coarse._hull_waterline_tangent(0.4) == fine._hull_waterline_tangent(0.4)


@pytest.mark.parametrize("chine_count", [2, 3, 4])
@pytest.mark.parametrize("points", [12, 40, 200])
def test_multi_chine_arc_has_no_notch_at_its_ends(chine_count: int, points: int) -> None:
    """Breadth and height increase monotonically from keel to waterline edge."""

    payload = _base().model_dump()
    payload["distribution_v2"]["cross_section_family"] = "multi_chine"
    payload["distribution_v2"]["multi_chine_count"] = chine_count
    geometry = Hull.model_validate(payload).to_geometry()
    for x in (-2.2, -1.0, 0.0, 1.4, 2.4):
        arc = geometry._hull_quarter_section(x, points)
        assert len(arc) == points
        assert np.all(np.diff(arc[:, 0]) >= -1e-12)
        assert np.all(np.diff(arc[:, 1]) >= -1e-12)
