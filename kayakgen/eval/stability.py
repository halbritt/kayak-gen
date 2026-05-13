"""Initial stability and load-case helpers.

Full high-angle GZ requires a human decision about heeled volume semantics.
This module exposes design-waterline initial stability and a conservative
sinkage-equilibrium mode with explicit load-case provenance. Generalized trim
and high-angle GZ remain reserved until their input contracts land.
"""

from __future__ import annotations

from kayakgen.eval.contract import LoadCase, StabilityResult
from kayakgen.eval.hydrostatics import Hydrostatics, evaluate as evaluate_hydrostatics
from kayakgen.model.hull import Hull

COMPAT_KG_ABOVE_KEEL_M = 0.25
DEFAULT_EQUILIBRIUM_TOLERANCE_KG = 1.0
DEFAULT_EQUILIBRIUM_MAX_ITERATIONS = 60
EQUILIBRIUM_DRAFT_TOLERANCE_M = 1e-9


class GZNotImplementedError(NotImplementedError):
    """Raised when high-angle stability is requested before its RFC lands."""


def _gm0_for_load_case(hydro_gm0_m: float | None, kg_above_keel_m: float) -> float | None:
    if hydro_gm0_m is None:
        return None
    return hydro_gm0_m + COMPAT_KG_ABOVE_KEEL_M - kg_above_keel_m


def _mass_for_load_case(hull: Hull, load_case: LoadCase) -> tuple[Hydrostatics, float]:
    hydro = evaluate_hydrostatics(hull)
    return hydro, hydro.displaced_volume_m3 * load_case.seawater_density_kg_m3


def evaluate_initial_stability(
    hull: Hull,
    load_case: LoadCase | None = None,
) -> StabilityResult:
    """Evaluate design-waterline initial GM for ``hull`` and ``load_case``."""
    load_case = load_case or LoadCase()
    hydro = evaluate_hydrostatics(hull)
    kg_above_keel_m = load_case.kg_above_keel_for_draft(hull.draft_m)
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
    return StabilityResult(
        load_case=load_case,
        initial_GM0_m=gm0,
        load_mass_kg=load_case.total_mass_kg,
        displaced_mass_kg=hydro.displaced_mass_kg,
        displacement_error_kg=displacement_error,
        warnings=warnings,
        gz_curve=None,
    )


def evaluate_equilibrium_stability(
    hull: Hull,
    load_case: LoadCase | None = None,
    *,
    tolerance_kg: float = DEFAULT_EQUILIBRIUM_TOLERANCE_KG,
    max_iterations: int = DEFAULT_EQUILIBRIUM_MAX_ITERATIONS,
) -> StabilityResult:
    """Evaluate initial stability at a solved sinkage-equilibrium draft.

    The current load-case contract has no longitudinal CG or load-position
    inputs, so generalized trim equilibrium is not yet computable. For the
    symmetric centered-load case available today, this reports zero trim with an
    explicit warning and solves only the vertical displacement balance.
    """
    if tolerance_kg <= 0:
        raise ValueError("tolerance_kg must be positive")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")

    load_case = load_case or LoadCase()
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
        equilibrium_draft_m=draft,
        sinkage_m=None if draft is None else draft - hull.draft_m,
        trim_angle_deg=0.0 if bracketed else None,
        equilibrium_tolerance_kg=tolerance_kg,
        equilibrium_iterations=iterations,
        equilibrium_max_iterations=max_iterations,
        warnings=warnings,
        gz_curve=None,
    )


def evaluate_gz_curve(*_args: object, **_kwargs: object) -> None:
    raise GZNotImplementedError(
        "high-angle GZ is reserved until heeled-volume semantics are decided"
    )
