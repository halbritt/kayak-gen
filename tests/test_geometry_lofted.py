"""LoftedHullGeometry public-accessor invariants."""

from __future__ import annotations

import numpy as np

from kayakgen.model.geometry import LoftedHullGeometry
from kayakgen.model.hull import Hull


def test_waterplane_zero_at_ends() -> None:
    geom = LoftedHullGeometry(Hull())
    wp = geom.waterplane(n=200)
    assert wp[0, 1] == 0.0
    assert wp[-1, 1] == 0.0


def test_keel_line_zero_at_ends() -> None:
    geom = LoftedHullGeometry(Hull())
    keel = geom.keel_line(n=200)
    assert keel[0, 1] == 0.0
    assert keel[-1, 1] == 0.0


def test_keel_deepest_at_midship() -> None:
    geom = LoftedHullGeometry(Hull())
    keel = geom.keel_line(n=201)
    z = keel[:, 1]
    assert z.argmin() == len(z) // 2  # symmetric, deepest at midship


def test_section_area_max_at_midship() -> None:
    geom = LoftedHullGeometry(Hull())
    xs = np.linspace(-2.0, 2.0, 41)
    areas = np.array([geom.section_area(x) for x in xs])
    assert areas.argmax() == len(areas) // 2  # x=0 is midship


def test_mesh_shape_matches_legacy() -> None:
    geom = LoftedHullGeometry(Hull())
    v_hull, f_hull = geom.mesh("hull")
    v_deck, f_deck = geom.mesh("deck")
    assert v_hull.shape == (150 * 79, 3)
    assert v_deck.shape == (150 * 79, 3)
    assert f_hull.shape == (149 * 78 * 2, 3)
    assert f_deck.shape == (149 * 78 * 2, 3)


def test_mesh_stations_override() -> None:
    geom = LoftedHullGeometry(Hull())
    v, f = geom.mesh("hull", stations=80)
    assert v.shape == (80 * 79, 3)
    assert f.shape == (79 * 78 * 2, 3)


def test_section_returns_2d_yz_pairs() -> None:
    geom = LoftedHullGeometry(Hull())
    pts = geom.section(0.0, "hull")
    assert pts.ndim == 2
    assert pts.shape[1] == 2
    assert pts.shape[0] == 79  # mirrored 40-pt quarter-slice


def test_half_breadth_grid_public_sampler_shape() -> None:
    geom = LoftedHullGeometry(Hull(beam_wl_m=0.50))
    xs, depths, grid = geom.half_breadth_grid(11, 7)
    assert xs.shape == (11,)
    assert depths.shape == (7,)
    assert grid.shape == (11, 7)
    assert grid[5, 0] > grid[5, -1]
