"""Immutable v1 Michell screening definition and retained-observation arithmetic.

These definitions describe saved policy v1 records. A future method or policy
must add a new version rather than reinterpret historical evidence.
"""

from __future__ import annotations

from collections.abc import Sequence

POLICY_VERSION = "michell_linear_depth_screening_v1"
METHOD_VERSION = "michell_linear_depth_v2"
REFERENCE_FN_RANGE = (0.25, 0.5)
REFERENCE_RESOLUTION_FLOOR = {"n_stations": 400, "n_depths": 25, "n_theta": 40}
REFERENCE_RELATIVE_ALLOWANCE = 7.088306821851369e-5
SURFACE_STATIONS = (60, 120, 240)
KNOTS_TO_MS = 0.514444


def refinement_levels(n: int, m: int, t: int) -> list[tuple[int, int, int]]:
    middle_angle, fine_angle = max(2 * t, 160), max(4 * t, 640)
    return [
        (n, m, t),
        (n, 4 * m, fine_angle),
        (2 * n, 4 * m, fine_angle),
        (4 * n, 4 * m, fine_angle),
        (4 * n, m, fine_angle),
        (4 * n, 2 * m, fine_angle),
        (4 * n, 4 * m, t),
        (4 * n, 4 * m, middle_angle),
    ]


def achieved_uncertainty(
    wave_grid_totals: Sequence[float], viscous: Sequence[float]
) -> tuple[float, float]:
    """Return the total and viscous allowances from exactly eight + three observations."""
    if len(wave_grid_totals) != 8 or len(viscous) != 3:
        raise ValueError("v1 screening requires eight wave grids and three surface observations")
    finest = wave_grid_totals[3]
    viscous_error = abs(viscous[0] - viscous[2]) + abs(viscous[1] - viscous[2])
    residual = sum(abs(finest - wave_grid_totals[index]) for index in (2, 5, 7))
    return (
        abs(wave_grid_totals[0] - finest)
        + residual
        + abs(finest) * REFERENCE_RELATIVE_ALLOWANCE
        + viscous_error,
        viscous_error,
    )
