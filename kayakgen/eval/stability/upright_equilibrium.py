"""Upright sinkage solver and the public equilibrium-stability entry point.

Compact legacy load cases (no longitudinal components) take the centered
sinkage-only path implemented here. Load cases with explicit longitudinal
components delegate to :mod:`kayakgen.eval.stability.trim_equilibrium`.
"""

from __future__ import annotations

from kayakgen.eval.contract import LoadCase, StabilityResult
from kayakgen.eval.stability.load_case import (
    _gm0_for_load_case,
    _mass_for_load_case,
)
from kayakgen.eval.stability.trim_equilibrium import (
    DEFAULT_MAX_TRIM_ANGLE_DEG,
    _evaluate_trim_equilibrium,
)
from kayakgen.model.hull import Hull

DEFAULT_EQUILIBRIUM_TOLERANCE_KG = 1.0
DEFAULT_EQUILIBRIUM_MAX_ITERATIONS = 60
EQUILIBRIUM_DRAFT_TOLERANCE_M = 1e-9


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
