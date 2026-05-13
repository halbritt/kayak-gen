"""Initial stability and load-case helpers.

Full high-angle GZ requires a human decision about heeled volume semantics.
This module only exposes design-waterline initial stability with explicit
load-case provenance.
"""

from __future__ import annotations

from kayakgen.eval.contract import LoadCase, StabilityResult
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.model.hull import Hull

COMPAT_KG_ABOVE_KEEL_M = 0.25


class GZNotImplementedError(NotImplementedError):
    """Raised when high-angle stability is requested before its RFC lands."""


def evaluate_initial_stability(
    hull: Hull,
    load_case: LoadCase | None = None,
) -> StabilityResult:
    """Evaluate design-waterline initial GM for ``hull`` and ``load_case``."""
    load_case = load_case or LoadCase()
    hydro = evaluate_hydrostatics(hull)
    gm0 = None
    kg_above_keel_m = load_case.kg_above_keel_for_draft(hull.draft_m)
    if hydro.GM0_m is not None:
        gm0 = hydro.GM0_m + COMPAT_KG_ABOVE_KEEL_M - kg_above_keel_m
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


def evaluate_gz_curve(*_args: object, **_kwargs: object) -> None:
    raise GZNotImplementedError(
        "high-angle GZ is reserved until heeled-volume semantics are decided"
    )
