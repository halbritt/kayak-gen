"""Measured, versioned refinement evidence for exploratory resistance screening."""

from __future__ import annotations

import hashlib
import json
import math
from time import perf_counter
from typing import TYPE_CHECKING, Any

import numpy as np

from kayakgen.eval.contract import ResistanceCurve
from kayakgen.eval.michell_quadrature import wave_from_grid
from kayakgen.model.hull import Hull

if TYPE_CHECKING:
    from kayakgen.model.operating_state import OperatingPose

from kayakgen.eval.michell_screening import (
    POLICY_VERSION,
    REFERENCE_FN_RANGE,
    REFERENCE_RESOLUTION_FLOOR,
    REFERENCE_RELATIVE_ALLOWANCE,
    achieved_uncertainty,
    refinement_levels,
)


def _resolution(n: int, m: int, t: int) -> dict[str, int]:
    return {"n_stations": n, "n_depths": m, "n_theta": t}


def _fingerprint(curve: ResistanceCurve, grid: tuple[np.ndarray, ...]) -> str:
    digest = hashlib.sha256(
        json.dumps(
            {
                "method": curve.metadata.numerical_method_version,
                "speeds_knots": curve.V_knots,
                "constants": curve.metadata.constants,
                "viscous_N": curve.Rv_N,
                "resolution": curve.metadata.quadrature,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    )
    for array in grid:
        digest.update(np.asarray(array, dtype="<f8").tobytes())
    return digest.hexdigest()


def assess_resistance(
    hull: Hull,
    curve: ResistanceCurve,
    tolerance: float,
    *,
    pose: OperatingPose | None = None,
) -> dict[str, Any]:
    """Assess the reported grid; refinement never replaces its requested values."""
    from kayakgen.eval.resistance import (
        KNOTS_TO_MS,
        WETTED_SURFACE_STATIONS,
        NUMERICAL_METHOD_VERSION,
        _half_breadth_grid,
        viscous_resistance,
        wetted_surface,
    )

    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("numerical_relative_tolerance must be finite and positive")
    n, m, t = (curve.metadata.quadrature[key] for key in ("n_stations", "n_depths", "n_theta"))
    assessment: dict[str, Any] = {
        "status": "unknown",
        "policy_version": POLICY_VERSION,
        "resolutions": [_resolution(n, m, t)],
        "relative_changes": [],
        "relative_tolerance": tolerance,
        "evidence": "",
        "speeds_knots": list(curve.V_knots),
        "absolute_uncertainty_N": [],
        "observations": [],
        "surface_observations": [],
        "viscous_uncertainty_N": [],
        "input_fingerprint": None,
        "comparison_inputs": None,
        "reference_fn_range": REFERENCE_FN_RANGE,
        "reference_resolution_floor": dict(REFERENCE_RESOLUTION_FLOOR),
        "reference_relative_allowance": REFERENCE_RELATIVE_ALLOWANCE,
    }
    if curve.metadata.numerical_method_version != NUMERICAL_METHOD_VERSION:
        assessment["evidence"] = "numerical_method_version_mismatch"
        return assessment
    rho = curve.metadata.constants["seawater_density_kg_m3"]
    gravity = curve.metadata.constants["gravity_m_s2"]
    nu = curve.metadata.constants["seawater_kinematic_viscosity_m2_s"]
    if any(not math.isfinite(value) or value <= 0 for value in (rho, gravity, nu)):
        assessment["evidence"] = "invalid_assessed_fluid_inputs"
        return assessment
    actual_fn = np.asarray(curve.V_knots) * KNOTS_TO_MS / math.sqrt(gravity * hull.length_m)
    assessment["comparison_inputs"] = {
        "speeds_knots": list(curve.V_knots),
        "hull_length_m": hull.length_m,
        "density_kg_m3": rho,
        "kinematic_viscosity_m2_s": nu,
        "gravity_m_s2": gravity,
        "numerical_method_version": curve.metadata.numerical_method_version,
        "model_family": curve.metadata.model_family,
        "calibration_model_version": curve.metadata.model_version,
    }
    if len(curve.Fn) != len(actual_fn) or not np.allclose(curve.Fn, actual_fn, rtol=1e-12, atol=0):
        assessment["evidence"] = "reported_fn_does_not_match_assessed_inputs"
        return assessment
    if not all(REFERENCE_FN_RANGE[0] <= fn <= REFERENCE_FN_RANGE[1] for fn in actual_fn):
        assessment["evidence"] = "outside_numerical_reference_fn_scope; raw speed points retained"
        return assessment
    if any(
        curve.metadata.quadrature[key] < minimum
        for key, minimum in REFERENCE_RESOLUTION_FLOOR.items()
    ):
        assessment["evidence"] = (
            "outside_numerical_reference_resolution_scope; raw requested grid retained"
        )
        return assessment
    surface_values = []
    surface_observations = []
    assessment["surface_observations"] = surface_observations
    surface_stations = WETTED_SURFACE_STATIONS
    for stations in (surface_stations, 2 * surface_stations, 4 * surface_stations):
        started = perf_counter()
        area = wetted_surface(hull, stations=stations, pose=pose)
        rv = np.array(
            [
                viscous_resistance(hull, v * KNOTS_TO_MS, Sw=area, rho=rho, nu=nu)
                for v in curve.V_knots
            ]
        )
        if not math.isfinite(area) or not np.all(np.isfinite(rv)):
            assessment["evidence"] = (
                "non_finite_surface_refinement; numerical assessment unavailable"
            )
            return assessment
        surface_observations.append(
            {
                "stations": stations,
                "wetted_surface_m2": area,
                "viscous_resistance_N": rv.tolist(),
                "seconds": perf_counter() - started,
            }
        )
        surface_values.append(rv)
    assessment["surface_observations"] = surface_observations
    if not np.array_equal(surface_values[0], np.asarray(curve.Rv_N)):
        assessment["evidence"] = "reported_viscous_values_do_not_match_assessed_inputs"
        return assessment
    viscous_uncertainty = abs(surface_values[0] - surface_values[2]) + abs(
        surface_values[1] - surface_values[2]
    )
    assessment["viscous_uncertainty_N"] = viscous_uncertainty.tolist()
    cache: dict[tuple[int, int], tuple[np.ndarray, ...]] = {}
    levels = refinement_levels(n, m, t)
    observations = []
    values = []
    for nx, nz, nt in levels:
        started = perf_counter()
        if (nx, nz) not in cache:
            cache[(nx, nz)] = (
                _half_breadth_grid(hull, nx, nz, pose=pose)
                if pose is not None
                else _half_breadth_grid(hull, nx, nz)
            )
        grid = cache[(nx, nz)]
        rw = np.array(
            [wave_from_grid(*grid, v * KNOTS_TO_MS, nt, rho, gravity) for v in curve.V_knots]
        )
        rt = np.asarray(curve.Rv_N) + rw
        observations.append(
            {
                "resolution": _resolution(nx, nz, nt),
                "total_resistance_N": [float(x) if math.isfinite(x) else None for x in rt],
                "seconds": perf_counter() - started,
            }
        )
        values.append(rt)
        if not np.all(np.isfinite(rt)):
            assessment.update(
                observations=observations,
                resolutions=[o["resolution"] for o in observations],
                evidence="non_finite_refinement; numerical assessment unavailable",
            )
            return assessment
    assessment["input_fingerprint"] = _fingerprint(curve, cache[(n, m)])
    assessment["observations"] = observations
    assessment["resolutions"] = [o["resolution"] for o in observations]
    if not np.array_equal(values[0], np.asarray(curve.Rt_N)):
        assessment["evidence"] = "reported_values_do_not_match_assessed_inputs"
        return assessment
    allowances = [
        achieved_uncertainty(
            [float(row[index]) for row in values],
            [float(row[index]) for row in surface_values],
        )
        for index in range(len(curve.V_knots))
    ]
    uncertainty = np.asarray([row[0] for row in allowances])
    relative = np.divide(
        uncertainty, abs(values[0]), out=np.full_like(uncertainty, np.inf), where=values[0] != 0
    )
    if not np.all(np.isfinite(relative)):
        assessment["evidence"] = "zero_resistance_cannot_support_relative_screening_budget"
        return assessment
    assessment["absolute_uncertainty_N"] = uncertainty.tolist()
    assessment["relative_changes"] = relative.tolist()
    assessment["status"] = "converged" if np.max(relative) <= tolerance else "not_converged"
    assessment["evidence"] = (
        "RFC0077: requested-to-finest change + independent x/z/theta residuals "
        "+ wetted-surface viscous refinement + closed-transform reference allowance; empirical screening uncertainty, "
        "not physical validation or a universal mathematical error bound"
    )
    return assessment
