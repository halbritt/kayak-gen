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
depth ``z`` below the waterline. The physical model and 16/π prefactor
remain unchanged. RFC 0077 integrates each sampled linear depth segment
against its exponential kernel exactly, avoiding the unresolved near-surface
boundary layer of the former depth trapezoid. Uniform longitudinal gradients
and angular trapezoids remain resolution-sensitive, especially near sharp tips.

Diagnostic curves default to unknown numerical quality. Explicitly requesting
a numerical screening budget evaluates independent x/z/theta refinements and
records achieved uncertainty against independent closed-transform controls.
Assessment never replaces the requested-grid values or promotes physical claims.

ITTC-57 friction line (well-converged for any hull):

.. math::
    C_f = \\frac{0.075}{(\\log_{10} \\mathrm{Re} - 2)^2},\\quad
    R_v = \\tfrac{1}{2} \\rho V^2 S_w C_f
"""

from __future__ import annotations

import math
from time import perf_counter

import numpy as np

from kayakgen.eval.claims import (
    ACCEPTED_USE_COMPARATIVE_FILTER,
    UNCALIBRATED_COMPARATIVE,
    uncalibrated_resistance_warnings,
)
from kayakgen.eval.contract import NumericalQuality, ResistanceCurve, ResistanceMetadata
from kayakgen.model.hull import Hull
from kayakgen.model.operating_state import OperatingPose
from kayakgen.eval.michell_quadrature import wave_from_grid

GRAVITY_M_S2 = 9.80665
SEAWATER_DENSITY_KG_M3 = 1025.0
SEAWATER_KINEMATIC_VISCOSITY_M2_S = 1.19e-6  # 15 °C
KNOTS_TO_MS = 0.514444
NUMERICAL_METHOD_VERSION = "michell_linear_depth_v2"
WETTED_SURFACE_STATIONS = 60


def _half_breadth_grid(hull: Hull, n_stations: int, n_depths: int, pose: OperatingPose | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample ``f(x, z)`` on a regular ``n_stations × n_depths`` grid.

    Returns ``(xs, zs, f)`` where ``xs`` runs from ``-L/2`` to ``+L/2``,
    ``zs`` runs from 0 (waterline) to ``draft`` (positive downward), and
    ``f[i, j]`` is the half-breadth at ``(xs[i], zs[j])``.
    """
    if pose is not None:
        from kayakgen.eval.immersed_geometry import immersed_geometry

        return immersed_geometry(hull, pose).half_breadth_grid(n_stations, n_depths)
    return hull.to_geometry().half_breadth_grid(n_stations, n_depths)


def wetted_surface(hull: Hull, stations: int = WETTED_SURFACE_STATIONS, *, pose: OperatingPose | None = None) -> float:
    """Wetted surface area from triangle areas of the hull mesh."""
    if pose is not None:
        from kayakgen.eval.immersed_geometry import immersed_geometry

        geom = immersed_geometry(hull, pose, stations)
    else:
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
    *,
    pose: OperatingPose | None = None,
) -> float:
    """ITTC-57 viscous resistance in Newtons."""
    if V_ms <= 0:
        return 0.0
    if Sw is None:
        Sw = wetted_surface(hull, pose=pose)
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
    *,
    pose: OperatingPose | None = None,
) -> float:
    """Wave-making resistance via the polar Michell integral, Newtons."""
    if V_ms <= 0:
        return 0.0
    if n_stations < 3 or n_depths < 2 or n_theta < 2:
        raise ValueError("Michell quadrature requires >=3 stations, >=2 depths and >=2 angles")
    xs, zs, half_breadths = _half_breadth_grid(hull, n_stations, n_depths, pose=pose)
    return wave_from_grid(xs, zs, half_breadths, V_ms, n_theta, rho, g)



def _validate_fluid_properties(rho: float, nu: float) -> None:
    if not math.isfinite(rho) or rho <= 0 or not math.isfinite(nu) or nu <= 0:
        raise ValueError("water density and viscosity must be finite and positive")


def resistance_curve(
    hull: Hull,
    V_knots: np.ndarray | None = None,
    n_stations: int = 600,
    n_depths: int = 25,
    n_theta: int = 40,
    *,
    pose: OperatingPose | None = None,
    rho: float = SEAWATER_DENSITY_KG_M3,
    nu: float = SEAWATER_KINEMATIC_VISCOSITY_M2_S,
    numerical_relative_tolerance: float | None = None,
) -> ResistanceCurve:
    """Sweep viscous + wave resistance across a speed range."""
    _validate_fluid_properties(rho, nu)
    if V_knots is None:
        V_knots = np.linspace(1.0, 6.0, 21)

    Sw = wetted_surface(hull, pose=pose)
    V_ms = V_knots * KNOTS_TO_MS
    Fn = V_ms / np.sqrt(GRAVITY_M_S2 * hull.length_m)
    Rv = np.array([viscous_resistance(hull, v, Sw=Sw, rho=rho, nu=nu) for v in V_ms])
    Rw = np.array(
        [
            wave_resistance_michell(hull, v, n_stations, n_depths, n_theta, rho=rho, pose=pose)
            for v in V_ms
        ]
    )
    Rt = Rv + Rw

    metadata = ResistanceMetadata(
        claim_state=UNCALIBRATED_COMPARATIVE,
        accepted_uses=[ACCEPTED_USE_COMPARATIVE_FILTER],
        calibration_fixture_ids=[],
        validation_fixture_ids=[],
        model_version=None,
        fit_status=None,
        fit_metrics={},
        validity_envelope=None,
        model_family="raw_ittc_michell",
        numerical_method_version=NUMERICAL_METHOD_VERSION,
        calibration_status="uncalibrated",
        accepted_use=[ACCEPTED_USE_COMPARATIVE_FILTER],
        verification_fixtures=["wigley_parabolic_hull"],
        constants={
            "gravity_m_s2": GRAVITY_M_S2,
            "seawater_density_kg_m3": rho,
            "seawater_kinematic_viscosity_m2_s": nu,
        },
        quadrature={
            "n_stations": n_stations,
            "n_depths": n_depths,
            "n_theta": n_theta,
        },
        warnings=uncalibrated_resistance_warnings(),
    )

    curve = ResistanceCurve(
        V_knots=V_knots.tolist(),
        Fn=Fn.tolist(),
        Rv_N=Rv.tolist(),
        Rw_N=Rw.tolist(),
        Rt_N=Rt.tolist(),
        metadata=metadata,
    )
    if numerical_relative_tolerance is not None:
        from kayakgen.eval.numerical_resistance import assess_resistance

        curve.metadata.numerical_quality = NumericalQuality.model_validate(
            assess_resistance(hull, curve, numerical_relative_tolerance, pose=pose)
        )
        # Bind newly assessed evidence through the same parser used for saved
        # curves; requested values and metadata must still match its observations.
        return ResistanceCurve.model_validate(curve.model_dump())
    return curve


def evaluate_resistance(
    hull: Hull,
    V_ms: float,
    Sw: float | None = None,
    n_stations: int = 400,
    n_depths: int = 20,
    n_theta: int = 30,
    *,
    pose: OperatingPose | None = None,
    rho: float = SEAWATER_DENSITY_KG_M3,
    nu: float = SEAWATER_KINEMATIC_VISCOSITY_M2_S,
) -> dict[str, float]:
    """Compute viscous + wave resistance at a single speed."""
    _validate_fluid_properties(rho, nu)
    t0 = perf_counter()
    Rv = viscous_resistance(hull, V_ms, Sw=Sw, pose=pose, rho=rho, nu=nu)
    t1 = perf_counter()
    Rw = wave_resistance_michell(hull, V_ms, n_stations, n_depths, n_theta, pose=pose, rho=rho)
    t2 = perf_counter()
    return {
        "Rv_N": Rv,
        "Rw_N": Rw,
        "Rt_N": Rv + Rw,
        "Fn": V_ms / math.sqrt(GRAVITY_M_S2 * hull.length_m),
        "viscous_ms": (t1 - t0) * 1000.0,
        "wave_ms": (t2 - t1) * 1000.0,
    }
