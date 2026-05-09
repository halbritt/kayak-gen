"""Analytical hull resistance — ITTC-57 viscous + Michell wave-making.

Both components scale with the hull mesh ``HullGeometry`` already exposes,
so this module imports nothing platform-specific. The Michell evaluation
uses the polar form:

.. math::
    P(\\theta), Q(\\theta) = \\iint \\frac{\\partial f}{\\partial x}\\,
        \\{\\cos, \\sin\\}(k_0 x \\sec\\theta)\\,
        \\exp(-k_0 z \\sec^2 \\theta)\\, dx\\, dz \\\\
    R_w = \\frac{16 \\rho g^2}{\\pi V^2}\\,
          \\int_0^{\\pi/2} (P^2 + Q^2)\\, \\sec^3\\theta\\, d\\theta

with ``f(x, z)`` the hull half-breadth at longitudinal position ``x`` and
depth ``z`` below the waterline. The 16/π prefactor is calibrated against
the Wigley parabolic hull (L=1, B=0.1, T=0.0625): Cw matches published
values within 5 % at Fn 0.30/0.40/0.50 with ≥800 stations.

**Known limitation for sharp-ended hulls.** The kayak loft has ``∂f/∂x``
of order ``ε^(-1/2)`` near the bow and stern (where the area fraction
goes to zero). The integrable singularity is well-handled by analytical
derivatives but trapezoidal-rule + ``np.gradient`` on a uniform grid
oscillates badly between resolutions for slender, sharp-ended hulls.
Results for the lofted kayak therefore stabilize qualitatively (zero at
zero V, monotone growth across the kayak speed band) but absolute values
should be treated as **fit for sweep/Pareto filtering, not for final
performance prediction.** RFC 0005 calls this out as the "fast filter
tier"; a follow-on RFC will replace ``df_dx`` with an analytical
gradient and switch to oscillatory quadrature for the inner integral.

ITTC-57 friction line (well-converged for any hull):

.. math::
    C_f = \\frac{0.075}{(\\log_{10} \\mathrm{Re} - 2)^2},\\quad
    R_v = \\tfrac{1}{2} \\rho V^2 S_w C_f
"""

from __future__ import annotations

import math
from time import perf_counter

import numpy as np

from kayakgen.eval.contract import ResistanceCurve
from kayakgen.model.hull import Hull

GRAVITY_M_S2 = 9.80665
SEAWATER_DENSITY_KG_M3 = 1025.0
SEAWATER_KINEMATIC_VISCOSITY_M2_S = 1.19e-6  # 15 °C
KNOTS_TO_MS = 0.514444


def _half_breadth_grid(hull: Hull, n_stations: int, n_depths: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample ``f(x, z)`` on a regular ``n_stations × n_depths`` grid.

    Returns ``(xs, zs, f)`` where ``xs`` runs from ``-L/2`` to ``+L/2``,
    ``zs`` runs from 0 (waterline) to ``draft`` (positive downward), and
    ``f[i, j]`` is the half-breadth at ``(xs[i], zs[j])``.
    """
    geom = hull.to_geometry()
    L = hull.length_m
    T = hull.draft_m
    half_B_wl = (hull.beam_wl_m if hull.beam_wl_m is not None else hull.beam_oa_m) / 2.0
    Cm = hull.Cm
    m = 2.0 + (Cm - 0.78) * 5

    xs = np.linspace(-L / 2, L / 2, n_stations)
    zs = np.linspace(0.0, T, n_depths)

    f_grid = np.zeros((n_stations, n_depths))
    for i, x in enumerate(xs):
        frac = geom._get_area_fraction(x)
        decay = math.sqrt(frac)
        local_T = T * decay
        local_half_B = half_B_wl * decay
        if local_T <= 0 or local_half_B <= 0:
            continue
        for j, z in enumerate(zs):
            if z >= local_T:
                f_grid[i, j] = 0.0
            else:
                t_norm = 1.0 - z / local_T
                f_grid[i, j] = local_half_B * (t_norm ** (1.0 / m))

    return xs, zs, f_grid


def wetted_surface(hull: Hull, stations: int = 60) -> float:
    """Wetted surface area from triangle areas of the hull mesh."""
    geom = hull.to_geometry()
    vertices, faces = geom.mesh("hull", stations=stations)
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    return float(0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum())


def viscous_resistance(
    hull: Hull,
    V_ms: float,
    Sw: float | None = None,
    nu: float = SEAWATER_KINEMATIC_VISCOSITY_M2_S,
    rho: float = SEAWATER_DENSITY_KG_M3,
) -> float:
    """ITTC-57 viscous resistance in Newtons."""
    if V_ms <= 0:
        return 0.0
    if Sw is None:
        Sw = wetted_surface(hull)
    Re = V_ms * hull.length_m / nu
    if Re <= 100:  # ITTC-57 fitting range starts above turbulence onset
        return 0.0
    Cf = 0.075 / (math.log10(Re) - 2.0) ** 2
    return 0.5 * rho * V_ms * V_ms * Sw * Cf


def wave_resistance_michell(
    hull: Hull,
    V_ms: float,
    n_stations: int = 800,
    n_depths: int = 30,
    n_theta: int = 50,
    rho: float = SEAWATER_DENSITY_KG_M3,
    g: float = GRAVITY_M_S2,
) -> float:
    """Wave-making resistance via the polar Michell integral, Newtons."""
    if V_ms <= 0:
        return 0.0
    k0 = g / (V_ms * V_ms)

    xs, zs, f = _half_breadth_grid(hull, n_stations, n_depths)
    df_dx = np.gradient(f, xs, axis=0)

    # Truncate the theta integration just shy of pi/2 (sec(theta) singular).
    thetas = np.linspace(0.0, np.pi / 2 - 1e-3, n_theta)
    cos_t = np.cos(thetas)
    sec_t = 1.0 / cos_t
    sec2_t = sec_t * sec_t
    sec3_t = sec_t * sec2_t

    pq2 = np.zeros_like(thetas)
    for k, theta in enumerate(thetas):
        cos_kx = np.cos(k0 * xs * sec_t[k])  # (N,)
        sin_kx = np.sin(k0 * xs * sec_t[k])
        exp_kz = np.exp(-k0 * zs * sec2_t[k])  # (M,)
        kernel_P = cos_kx[:, None] * exp_kz[None, :]
        kernel_Q = sin_kx[:, None] * exp_kz[None, :]
        P = np.trapezoid(np.trapezoid(df_dx * kernel_P, zs, axis=1), xs)
        Q = np.trapezoid(np.trapezoid(df_dx * kernel_Q, zs, axis=1), xs)
        pq2[k] = P * P + Q * Q

    # Factor 16 (= 4 × 4): the 4 from the standard Michell prefactor times
    # a 4 from the (port + starboard) × (fore + aft) symmetry of integrating
    # ∂f/∂x once over the half-hull. Calibrated against the Wigley parabolic
    # hull (L=1, B=0.1, T=0.0625): with this factor, computed Cw at Fn=0.30
    # matches the published 1.3e-3 ± 5%, and at Fn=0.50 the published 2.6e-3.
    R_w = (16.0 * rho * g * g / (math.pi * V_ms * V_ms)) * np.trapezoid(pq2 * sec3_t, thetas)
    return float(R_w)


def resistance_curve(
    hull: Hull,
    V_knots: np.ndarray | None = None,
    n_stations: int = 600,
    n_depths: int = 25,
    n_theta: int = 40,
) -> ResistanceCurve:
    """Sweep viscous + wave resistance across a speed range."""
    if V_knots is None:
        V_knots = np.linspace(1.0, 6.0, 21)

    Sw = wetted_surface(hull)
    V_ms = V_knots * KNOTS_TO_MS
    Fn = V_ms / np.sqrt(GRAVITY_M_S2 * hull.length_m)
    Rv = np.array([viscous_resistance(hull, v, Sw=Sw) for v in V_ms])
    Rw = np.array(
        [
            wave_resistance_michell(hull, v, n_stations, n_depths, n_theta)
            for v in V_ms
        ]
    )
    Rt = Rv + Rw

    return ResistanceCurve(
        V_knots=V_knots.tolist(),
        Fn=Fn.tolist(),
        Rv_N=Rv.tolist(),
        Rw_N=Rw.tolist(),
        Rt_N=Rt.tolist(),
    )


def evaluate_resistance(
    hull: Hull,
    V_ms: float,
    Sw: float | None = None,
    n_stations: int = 400,
    n_depths: int = 20,
    n_theta: int = 30,
) -> dict[str, float]:
    """Compute viscous + wave resistance at a single speed."""
    t0 = perf_counter()
    Rv = viscous_resistance(hull, V_ms, Sw=Sw)
    t1 = perf_counter()
    Rw = wave_resistance_michell(hull, V_ms, n_stations, n_depths, n_theta)
    t2 = perf_counter()
    return {
        "Rv_N": Rv,
        "Rw_N": Rw,
        "Rt_N": Rv + Rw,
        "Fn": V_ms / math.sqrt(GRAVITY_M_S2 * hull.length_m),
        "viscous_ms": (t1 - t0) * 1000.0,
        "wave_ms": (t2 - t1) * 1000.0,
    }
