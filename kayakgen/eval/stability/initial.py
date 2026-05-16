"""Initial (design-waterline) stability evaluator.

Computes GM0 against the load case at the hull's design draft without
attempting a sinkage or trim solve.
"""

from __future__ import annotations

from kayakgen.eval.contract import LoadCase, StabilityResult
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.stability.load_case import _gm0_for_load_case
from kayakgen.model.hull import Hull


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
