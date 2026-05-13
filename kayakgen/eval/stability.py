"""Initial stability and load-case helpers.

Full high-angle GZ requires a human decision about heeled volume semantics.
This module exposes design-waterline initial stability, the legacy centered
sinkage-equilibrium mode, and a bounded fixed-body upright trim slice for
explicit longitudinal load components. High-angle GZ remains reserved until
its closed-volume contract lands.
"""

from __future__ import annotations

import math

import numpy as np

from kayakgen.eval.contract import LoadCase, StabilityResult
from kayakgen.eval.hydrostatics import Hydrostatics, evaluate as evaluate_hydrostatics
from kayakgen.model.hull import Hull

COMPAT_KG_ABOVE_KEEL_M = 0.25
DEFAULT_EQUILIBRIUM_TOLERANCE_KG = 1.0
DEFAULT_EQUILIBRIUM_MAX_ITERATIONS = 60
EQUILIBRIUM_DRAFT_TOLERANCE_M = 1e-9
DEFAULT_MAX_TRIM_ANGLE_DEG = 8.0
TRIM_STATIONS = 61
TRIM_DRAFT_TOLERANCE_M = 1e-5


class GZNotImplementedError(NotImplementedError):
    """Raised when high-angle stability is requested before its RFC lands."""


def _gm0_for_load_case(hydro_gm0_m: float | None, kg_above_keel_m: float) -> float | None:
    if hydro_gm0_m is None:
        return None
    return hydro_gm0_m + COMPAT_KG_ABOVE_KEEL_M - kg_above_keel_m


def _mass_for_load_case(hull: Hull, load_case: LoadCase) -> tuple[Hydrostatics, float]:
    hydro = evaluate_hydrostatics(hull)
    return hydro, hydro.displaced_volume_m3 * load_case.seawater_density_kg_m3


def _polygon_area(points: np.ndarray) -> float:
    if len(points) < 3:
        return 0.0
    ys = points[:, 0]
    zs = points[:, 1]
    return float(0.5 * abs(np.sum(ys * np.roll(zs, -1) - np.roll(ys, -1) * zs)))


def _clipped_section_area(section: np.ndarray, waterline_z: float) -> float:
    """Area of ``section`` below a local waterline in body coordinates."""
    if len(section) < 3:
        return 0.0
    if waterline_z >= float(section[:, 1].max()):
        return _polygon_area(section)
    if waterline_z <= float(section[:, 1].min()):
        return 0.0

    clipped: list[np.ndarray] = []
    for i, current in enumerate(section):
        previous = section[i - 1]
        current_inside = current[1] <= waterline_z
        previous_inside = previous[1] <= waterline_z

        if current_inside != previous_inside:
            dz = current[1] - previous[1]
            if abs(dz) > 1e-12:
                ratio = (waterline_z - previous[1]) / dz
                clipped.append(previous + ratio * (current - previous))
        if current_inside:
            clipped.append(current)

    if not clipped:
        return 0.0
    return _polygon_area(np.array(clipped))


def _trim_hydrostatic_state(
    hull: Hull,
    *,
    draft_at_midship_m: float,
    trim_angle_deg: float,
    density_kg_m3: float,
    stations: int = TRIM_STATIONS,
    section_samples: list[tuple[float, np.ndarray]] | None = None,
) -> tuple[float, float]:
    """Return ``(displaced_mass_kg, signed_lcb_m)`` for fixed-body trim.

    ``trim_angle_deg > 0`` is stern-down/bow-up. Since model ``+x`` points
    sternward, the trimmed waterline rises with positive ``x`` for positive
    trim.
    """
    if section_samples is None:
        geom = hull.to_geometry()
        xs = np.linspace(-hull.length_m / 2.0, hull.length_m / 2.0, stations)
        section_samples = [(float(x), geom.section(float(x), "hull")) for x in xs]
    else:
        xs = np.array([sample[0] for sample in section_samples], dtype=float)
    tan_trim = math.tan(math.radians(trim_angle_deg))
    area_by_station = np.zeros_like(xs)
    for i, (x, section) in enumerate(section_samples):
        waterline_z = draft_at_midship_m - hull.draft_m + x * tan_trim
        area_by_station[i] = _clipped_section_area(section, waterline_z)

    volume = float(np.trapezoid(area_by_station, xs))
    if volume <= 0:
        return 0.0, 0.0
    lcb_m = float(np.trapezoid(area_by_station * xs, xs) / volume)
    return volume * density_kg_m3, lcb_m


def _solve_midship_draft_for_trim(
    hull: Hull,
    load_case: LoadCase,
    *,
    trim_angle_deg: float,
    tolerance_kg: float,
    max_iterations: int,
    section_samples: list[tuple[float, np.ndarray]] | None = None,
) -> tuple[float | None, float, float, int, bool]:
    target_mass = load_case.total_mass_kg
    low = max(hull.draft_m * 0.01, 1e-4)
    high = hull.draft_m
    low_mass, low_lcb = _trim_hydrostatic_state(
        hull,
        draft_at_midship_m=low,
        trim_angle_deg=trim_angle_deg,
        density_kg_m3=load_case.seawater_density_kg_m3,
        section_samples=section_samples,
    )
    high_mass, high_lcb = _trim_hydrostatic_state(
        hull,
        draft_at_midship_m=high,
        trim_angle_deg=trim_angle_deg,
        density_kg_m3=load_case.seawater_density_kg_m3,
        section_samples=section_samples,
    )
    if not (low_mass <= target_mass <= high_mass):
        return None, high_mass, high_lcb, 0, False

    best_draft = high
    best_mass = high_mass
    best_lcb = high_lcb
    iterations = 0
    converged = False
    for iterations in range(1, max_iterations + 1):
        draft = (low + high) / 2.0
        mass, lcb = _trim_hydrostatic_state(
            hull,
            draft_at_midship_m=draft,
            trim_angle_deg=trim_angle_deg,
            density_kg_m3=load_case.seawater_density_kg_m3,
            section_samples=section_samples,
        )
        best_draft = draft
        best_mass = mass
        best_lcb = lcb
        error = mass - target_mass
        if abs(error) <= tolerance_kg and (high - low) <= TRIM_DRAFT_TOLERANCE_M:
            converged = True
            break
        if error < 0:
            low = draft
        else:
            high = draft
    return best_draft, best_mass, best_lcb, iterations, converged


def _evaluate_trim_equilibrium(
    hull: Hull,
    load_case: LoadCase,
    *,
    tolerance_kg: float,
    moment_tolerance_kg_m: float,
    max_iterations: int,
    max_trim_angle_deg: float,
) -> StabilityResult:
    target_mass = load_case.total_mass_kg
    load_lcg_m = load_case.load_lcg_m_for_draft(hull.draft_m)
    warnings = [
        "equilibrium_trim_attempted",
        "fixed_body_station_area_trim_model",
        "trim_sign_positive_stern_down",
        "high_angle_gz_not_implemented",
    ]

    _, full_mass = _mass_for_load_case(hull, load_case)
    if target_mass > full_mass:
        warnings.extend(["equilibrium_not_converged", "equilibrium_mass_out_of_bracket"])
        return StabilityResult(
            load_case=load_case,
            method="equilibrium_trim",
            status="not_converged",
            initial_GM0_m=None,
            load_mass_kg=target_mass,
            displaced_mass_kg=full_mass,
            displacement_error_kg=full_mass - target_mass,
            load_lcg_m=load_lcg_m,
            equilibrium_tolerance_kg=tolerance_kg,
            moment_tolerance_kg_m=moment_tolerance_kg_m,
            equilibrium_iterations=0,
            equilibrium_max_iterations=max_iterations,
            warnings=warnings,
            gz_curve=None,
        )

    geom = hull.to_geometry()
    xs = np.linspace(-hull.length_m / 2.0, hull.length_m / 2.0, TRIM_STATIONS)
    samples = [(float(x), geom.section(float(x), "hull")) for x in xs]

    def state_for_trim(trim: float) -> tuple[float | None, float, float, int, bool, float]:
        draft, mass, lcb, inner_iterations, mass_converged = _solve_midship_draft_for_trim(
            hull,
            load_case,
            trim_angle_deg=trim,
            tolerance_kg=tolerance_kg,
            max_iterations=max(30, max_iterations),
            section_samples=samples,
        )
        moment_error = mass * lcb - target_mass * load_lcg_m
        return draft, mass, lcb, inner_iterations, mass_converged, moment_error

    sampled: list[tuple[float, tuple[float | None, float, float, int, bool, float]]] = []
    for trim in np.linspace(-max_trim_angle_deg, max_trim_angle_deg, 33):
        state = state_for_trim(float(trim))
        if state[0] is not None:
            sampled.append((float(trim), state))

    bracket: tuple[
        tuple[float, tuple[float | None, float, float, int, bool, float]],
        tuple[float, tuple[float | None, float, float, int, bool, float]],
    ] | None = None
    for left, right in zip(sampled, sampled[1:], strict=False):
        left_error = left[1][5]
        right_error = right[1][5]
        if left_error == 0 or left_error * right_error <= 0:
            bracket = (left, right)
            break

    if bracket is None:
        warnings.extend(["equilibrium_not_converged", "equilibrium_moment_out_of_bracket"])
        if sampled:
            edge_trim, edge = min(sampled, key=lambda item: abs(item[1][5]))
        else:
            edge_trim, edge = 0.0, state_for_trim(0.0)
        return StabilityResult(
            load_case=load_case,
            method="equilibrium_trim",
            status="not_converged",
            initial_GM0_m=None,
            load_mass_kg=target_mass,
            displaced_mass_kg=edge[1],
            displacement_error_kg=edge[1] - target_mass,
            draft_at_midship_m=edge[0],
            equilibrium_draft_m=edge[0],
            sinkage_m=None if edge[0] is None else edge[0] - hull.draft_m,
            trim_angle_deg=edge_trim,
            load_lcg_m=load_lcg_m,
            buoyancy_lcb_m=edge[2],
            moment_error_kg_m=edge[5],
            equilibrium_tolerance_kg=tolerance_kg,
            moment_tolerance_kg_m=moment_tolerance_kg_m,
            equilibrium_iterations=0,
            equilibrium_max_iterations=max_iterations,
            warnings=warnings,
            gz_curve=None,
        )

    low_trim, low_state = bracket[0]
    high_trim, high_state = bracket[1]
    best_trim = high_trim
    best_state = high_state
    converged = False
    iterations = 0
    for iterations in range(1, max_iterations + 1):
        trim = (low_trim + high_trim) / 2.0
        state = state_for_trim(trim)
        best_trim = trim
        best_state = state
        draft, mass, lcb, _inner, mass_converged, moment_error = state
        if (
            draft is not None
            and mass_converged
            and abs(mass - target_mass) <= tolerance_kg
            and abs(moment_error) <= moment_tolerance_kg_m
        ):
            converged = True
            break
        if moment_error < 0:
            low_trim = trim
        else:
            high_trim = trim

    draft, mass, lcb, _inner, _mass_converged, moment_error = best_state
    if converged:
        warnings.append("equilibrium_trim_solved")
    else:
        warnings.extend(["equilibrium_not_converged", "max_iterations_exceeded"])

    kg_above_keel_m = load_case.load_kg_above_keel_m_for_draft(draft or hull.draft_m)
    hydro = evaluate_hydrostatics(hull.model_copy(update={"draft_m": draft or hull.draft_m}))
    if load_case.kg_reference_value_m is not None and load_case.kg_reference != "keel":
        warnings.append("kg_reference_normalized_to_keel")
    return StabilityResult(
        load_case=load_case,
        method="equilibrium_trim",
        status="converged" if converged else "not_converged",
        initial_GM0_m=_gm0_for_load_case(hydro.GM0_m, kg_above_keel_m),
        load_mass_kg=target_mass,
        displaced_mass_kg=mass,
        displacement_error_kg=mass - target_mass,
        draft_at_midship_m=draft,
        equilibrium_draft_m=draft,
        sinkage_m=None if draft is None else draft - hull.draft_m,
        trim_angle_deg=best_trim,
        load_lcg_m=load_lcg_m,
        buoyancy_lcb_m=lcb,
        moment_error_kg_m=moment_error,
        equilibrium_tolerance_kg=tolerance_kg,
        moment_tolerance_kg_m=moment_tolerance_kg_m,
        equilibrium_iterations=iterations,
        equilibrium_max_iterations=max_iterations,
        warnings=warnings,
        gz_curve=None,
    )


def evaluate_initial_stability(
    hull: Hull,
    load_case: LoadCase | None = None,
) -> StabilityResult:
    """Evaluate design-waterline initial GM for ``hull`` and ``load_case``."""
    load_case = load_case or LoadCase()
    if load_case.total_mass_kg <= 0:
        raise ValueError("load case total mass must be positive")
    hydro = evaluate_hydrostatics(hull)
    kg_above_keel_m = (
        load_case.load_kg_above_keel_m_for_draft(hull.draft_m)
        if load_case.uses_longitudinal_components
        else load_case.kg_above_keel_for_draft(hull.draft_m)
    )
    load_lcg_m = (
        load_case.load_lcg_m_for_draft(hull.draft_m)
        if load_case.uses_longitudinal_components
        else 0.0
    )
    gm0 = _gm0_for_load_case(hydro.GM0_m, kg_above_keel_m)
    displacement_error = hydro.displaced_mass_kg - load_case.total_mass_kg
    warnings = [
        "design_waterline_initial_stability_only",
        "equilibrium_sinkage_trim_not_solved",
        "high_angle_gz_not_implemented",
    ]
    if abs(displacement_error) > 5.0:
        warnings.append("load_displacement_mismatch")
    if load_case.kg_reference_value_m is not None and load_case.kg_reference != "keel":
        warnings.append("kg_reference_normalized_to_keel")
    if load_case.uses_longitudinal_components:
        warnings.append("longitudinal_components_normalized")
    return StabilityResult(
        load_case=load_case,
        initial_GM0_m=gm0,
        load_mass_kg=load_case.total_mass_kg,
        displaced_mass_kg=hydro.displaced_mass_kg,
        displacement_error_kg=displacement_error,
        load_lcg_m=load_lcg_m,
        warnings=warnings,
        gz_curve=None,
    )


def evaluate_equilibrium_stability(
    hull: Hull,
    load_case: LoadCase | None = None,
    *,
    tolerance_kg: float = DEFAULT_EQUILIBRIUM_TOLERANCE_KG,
    moment_tolerance_kg_m: float | None = None,
    max_iterations: int = DEFAULT_EQUILIBRIUM_MAX_ITERATIONS,
    max_trim_angle_deg: float = DEFAULT_MAX_TRIM_ANGLE_DEG,
) -> StabilityResult:
    """Evaluate load-case equilibrium.

    Compact legacy load cases keep the centered sinkage-only path and report
    zero trim with an explicit warning. Load cases with explicit longitudinal
    components use the bounded fixed-body upright trim solver.
    """
    if tolerance_kg <= 0:
        raise ValueError("tolerance_kg must be positive")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")
    if max_trim_angle_deg <= 0:
        raise ValueError("max_trim_angle_deg must be positive")

    load_case = load_case or LoadCase()
    if load_case.total_mass_kg <= 0:
        raise ValueError("load case total mass must be positive")
    effective_moment_tolerance = (
        moment_tolerance_kg_m
        if moment_tolerance_kg_m is not None
        else max(0.1, tolerance_kg * hull.length_m * 0.05)
    )
    if effective_moment_tolerance <= 0:
        raise ValueError("moment_tolerance_kg_m must be positive")
    if load_case.uses_longitudinal_components:
        return _evaluate_trim_equilibrium(
            hull,
            load_case,
            tolerance_kg=tolerance_kg,
            moment_tolerance_kg_m=effective_moment_tolerance,
            max_iterations=max_iterations,
            max_trim_angle_deg=max_trim_angle_deg,
        )

    target_mass = load_case.total_mass_kg
    lower_draft = max(min(hull.draft_m, hull.deck_height_m) * 0.01, 1e-4)
    upper_draft = max(hull.draft_m, hull.deck_height_m)

    lower_hydro, lower_mass = _mass_for_load_case(
        hull.model_copy(update={"draft_m": lower_draft}),
        load_case,
    )
    upper_hydro, upper_mass = _mass_for_load_case(
        hull.model_copy(update={"draft_m": upper_draft}),
        load_case,
    )

    hydro = upper_hydro
    displaced_mass = upper_mass
    draft: float | None = upper_draft
    kg_draft = upper_draft
    iterations = 0
    converged = False
    bracketed = lower_mass <= target_mass <= upper_mass
    warnings = [
        "equilibrium_sinkage_attempted",
        "trim_assumed_zero_centered_load",
        "generalized_trim_not_implemented",
        "high_angle_gz_not_implemented",
    ]

    if not bracketed:
        if target_mass < lower_mass:
            hydro = lower_hydro
            displaced_mass = lower_mass
            kg_draft = lower_draft
        draft = None
        warnings.extend(["equilibrium_not_converged", "equilibrium_mass_out_of_bracket"])
    else:
        low = lower_draft
        high = upper_draft
        for iterations in range(1, max_iterations + 1):
            draft = (low + high) / 2.0
            kg_draft = draft
            hydro, displaced_mass = _mass_for_load_case(
                hull.model_copy(update={"draft_m": draft}),
                load_case,
            )
            error = displaced_mass - target_mass
            if abs(error) <= tolerance_kg and (high - low) <= EQUILIBRIUM_DRAFT_TOLERANCE_M:
                converged = True
                break
            if error < 0:
                low = draft
            else:
                high = draft
        if not converged:
            warnings.extend(["equilibrium_not_converged", "max_iterations_exceeded"])
        else:
            warnings.append("equilibrium_sinkage_solved")

    kg_above_keel_m = load_case.kg_above_keel_for_draft(kg_draft)
    if load_case.kg_reference_value_m is not None and load_case.kg_reference != "keel":
        warnings.append("kg_reference_normalized_to_keel")
    displacement_error = displaced_mass - target_mass
    return StabilityResult(
        load_case=load_case,
        method="equilibrium_sinkage",
        status="converged" if converged else "not_converged",
        initial_GM0_m=_gm0_for_load_case(hydro.GM0_m, kg_above_keel_m),
        load_mass_kg=target_mass,
        displaced_mass_kg=displaced_mass,
        displacement_error_kg=displacement_error,
        draft_at_midship_m=draft,
        equilibrium_draft_m=draft,
        sinkage_m=None if draft is None else draft - hull.draft_m,
        trim_angle_deg=0.0 if bracketed else None,
        load_lcg_m=0.0 if bracketed else None,
        buoyancy_lcb_m=0.0 if bracketed else None,
        moment_error_kg_m=0.0 if bracketed else None,
        equilibrium_tolerance_kg=tolerance_kg,
        moment_tolerance_kg_m=effective_moment_tolerance,
        equilibrium_iterations=iterations,
        equilibrium_max_iterations=max_iterations,
        warnings=warnings,
        gz_curve=None,
    )


def evaluate_gz_curve(*_args: object, **_kwargs: object) -> None:
    raise GZNotImplementedError(
        "high-angle GZ is reserved until closed_volume_body_not_defined is resolved"
    )
