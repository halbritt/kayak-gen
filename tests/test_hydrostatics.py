"""Hydrostatics from the integrated mesh — agree with the geometry the STL writer sees."""

from __future__ import annotations

import numpy as np

from kayakgen.eval.hydrostatics import SEAWATER_DENSITY_KG_M3, evaluate
from kayakgen.model.hull import Hull


def test_default_hydrostatics_match_golden_volume() -> None:
    h = evaluate(Hull())
    np.testing.assert_allclose(h.displaced_volume_m3, 0.11436507419829935, rtol=1e-9)
    np.testing.assert_allclose(
        h.displaced_mass_kg, 0.11436507419829935 * SEAWATER_DENSITY_KG_M3, rtol=1e-9
    )


def test_default_hydrostatics_match_golden_wetted() -> None:
    h = evaluate(Hull())
    np.testing.assert_allclose(h.wetted_surface_m2, 1.962403180945398, rtol=1e-9)


def test_lcb_at_default_is_midship() -> None:
    h = evaluate(Hull())
    assert abs(h.LCB_frac - 0.5) < 1e-6


def test_doubling_length_doubles_volume_for_geometric_scale() -> None:
    base = evaluate(Hull(length_m=4.5, beam_oa_m=0.55, draft_m=0.12))
    longer = evaluate(Hull(length_m=9.0, beam_oa_m=0.55, draft_m=0.12))
    np.testing.assert_allclose(longer.displaced_volume_m3, 2.0 * base.displaced_volume_m3, rtol=1e-3)


def test_cp_actual_in_reasonable_range() -> None:
    h = evaluate(Hull())
    assert 0.4 < h.Cp_actual < 0.7
    assert 0.6 < h.Cm_actual < 0.95


def test_cm_actual_uses_waterline_beam_when_present() -> None:
    hull = Hull(beam_oa_m=0.60, beam_wl_m=0.50)
    h = evaluate(hull)
    midship_area = hull.to_geometry().section_area(0.0)
    np.testing.assert_allclose(h.Cm_actual, midship_area / (0.50 * hull.draft_m))


def test_gm0_is_populated_and_grows_with_waterline_beam() -> None:
    narrow = evaluate(Hull(beam_oa_m=0.60, beam_wl_m=0.45))
    wide = evaluate(Hull(beam_oa_m=0.60, beam_wl_m=0.60))
    assert narrow.GM0_m is not None
    assert wide.GM0_m is not None
    assert wide.GM0_m > narrow.GM0_m
