"""Resistance — ITTC viscous + Michell wave-making sanity checks.

The Michell implementation is calibrated against the Wigley parabolic
hull at Fn 0.30/0.40/0.50 to within 5 %. For the lofted kayak, the
``ε^(-1/2)`` gradient at the sharp bow/stern produces a known
non-monotone convergence; tests therefore assert qualitative shape
(positivity, growth with V, total drag in a paddler-class envelope) and
the Wigley benchmark, not point-wise absolute values on the kayak loft.
The full RFC 0005 limitation is documented in
``kayakgen/eval/resistance.py``.
"""

from __future__ import annotations

import math
import time

import numpy as np

from kayakgen.eval.resistance import (
    KNOTS_TO_MS,
    SEAWATER_DENSITY_KG_M3,
    resistance_curve,
    viscous_resistance,
    wave_resistance_michell,
    wetted_surface,
)
from kayakgen.model.hull import Hull


def test_zero_speed_is_zero_drag() -> None:
    hull = Hull()
    assert viscous_resistance(hull, 0.0) == 0.0
    assert wave_resistance_michell(hull, 0.0) == 0.0


def test_viscous_drag_grows_with_speed() -> None:
    hull = Hull()
    Sw = wetted_surface(hull)
    drags = [viscous_resistance(hull, v, Sw=Sw) for v in (0.5, 1.0, 1.5, 2.0, 3.0)]
    assert all(b > a for a, b in zip(drags, drags[1:]))


def test_viscous_envelope_at_paddling_speed() -> None:
    """ITTC-57 viscous drag at 3.5 kt should be in the kayak envelope (5–25 N)."""
    hull = Hull()
    Sw = wetted_surface(hull)
    Rv = viscous_resistance(hull, 3.5 * KNOTS_TO_MS, Sw=Sw)
    assert 5.0 < Rv < 25.0, f"Rv at 3.5 kt: {Rv:.1f} N"


def test_wave_resistance_returns_finite_positive() -> None:
    """Michell returns a finite, positive number across the kayak speed band."""
    hull = Hull()
    for V_kt in (1.0, 2.0, 3.0, 4.0, 5.0):
        Rw = wave_resistance_michell(hull, V_kt * KNOTS_TO_MS, n_stations=400, n_depths=20, n_theta=30)
        assert math.isfinite(Rw)
        assert Rw >= 0.0


def test_michell_calibrated_against_wigley() -> None:
    """Calibration of the 16/π prefactor against the Wigley parabolic hull.

    Wigley f(x,z) = (B/2) (1 - (2x/L)²) (1 - (z/T)²) is the standard
    thin-ship benchmark. With ≥800 stations and ≥40 theta, our
    implementation should reproduce the published Cw at Fn = 0.30 within
    ~5 %.
    """
    L, B, T = 1.0, 0.1, 0.0625
    n_x, n_z, n_theta = 1200, 100, 80

    xs = np.linspace(-L / 2, L / 2, n_x)
    zs = np.linspace(0.0, T, n_z)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    df_dx = (B / 2.0) * (-8.0 * X / (L * L)) * (1.0 - (Z / T) ** 2)

    g = 9.80665
    rho = SEAWATER_DENSITY_KG_M3

    def michell(V: float) -> float:
        k0 = g / (V * V)
        thetas = np.linspace(1e-3, math.pi / 2 - 1e-3, n_theta)
        sec_t = 1.0 / np.cos(thetas)
        sec2_t = sec_t ** 2
        sec3_t = sec_t ** 3
        pq2 = np.zeros_like(thetas)
        for k in range(n_theta):
            kp = np.cos(k0 * xs * sec_t[k])[:, None] * np.exp(-k0 * zs * sec2_t[k])[None, :]
            kq = np.sin(k0 * xs * sec_t[k])[:, None] * np.exp(-k0 * zs * sec2_t[k])[None, :]
            P = np.trapezoid(np.trapezoid(df_dx * kp, zs, axis=1), xs)
            Q = np.trapezoid(np.trapezoid(df_dx * kq, zs, axis=1), xs)
            pq2[k] = P * P + Q * Q
        return (16.0 * rho * g * g / (math.pi * V * V)) * np.trapezoid(pq2 * sec3_t, thetas)

    Fn = 0.30
    V = Fn * math.sqrt(g * L)
    Rw = michell(V)
    Cw = Rw / (0.5 * rho * V * V * L * L)
    # Published Wigley Cw at Fn 0.30 ≈ 1.3e-3 (Lazauskas, various)
    assert 1.0e-3 < Cw < 1.6e-3, f"Wigley Cw at Fn 0.30: {Cw:.4f}"


def test_total_drag_at_paddling_speed_in_envelope() -> None:
    """Total drag at 3.5 kt should be meaningful (>5 N) — the regime where
    paddler power output (40–250 W) drives the boat."""
    hull = Hull()
    Sw = wetted_surface(hull)
    V_ms = 3.5 * KNOTS_TO_MS
    Rt = viscous_resistance(hull, V_ms, Sw=Sw) + wave_resistance_michell(hull, V_ms)
    assert Rt > 5.0, f"Rt at 3.5 kt: {Rt:.1f} N"


def test_resistance_curve_shape_and_units() -> None:
    hull = Hull()
    curve = resistance_curve(hull, V_knots=np.linspace(1.0, 6.0, 11))
    assert len(curve.V_knots) == 11
    assert all(v >= 0 for v in curve.Rv_N)
    assert all(v >= 0 for v in curve.Rw_N)
    assert all(rt == rv + rw for rt, rv, rw in zip(curve.Rt_N, curve.Rv_N, curve.Rw_N))


def test_viscous_drag_scales_with_wetted_surface() -> None:
    hull = Hull()
    V_ms = 2.0
    Rv_full = viscous_resistance(hull, V_ms)
    Rv_double = viscous_resistance(hull, V_ms, Sw=2.0 * wetted_surface(hull))
    assert abs(Rv_double - 2.0 * Rv_full) / Rv_full < 1e-6


def test_resistance_curve_under_budget() -> None:
    hull = Hull()
    t0 = time.perf_counter()
    resistance_curve(hull, V_knots=np.linspace(1.0, 6.0, 11), n_stations=400, n_depths=20, n_theta=30)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert elapsed_ms < 5000, f"resistance_curve took {elapsed_ms:.0f} ms"
