"""Shared design advisory bands for kayak hulls.

These checks are intentionally non-blocking. They surface the class
envelope from the design constraints doc without making exploratory
designs invalid.
"""

from __future__ import annotations

from dataclasses import dataclass

from kayakgen.model.hull import Hull


@dataclass(frozen=True)
class DesignAdvisory:
    """Derived advisory metrics and warning strings for a hull."""

    l_over_bwl: float
    cp: float
    displaced_mass_kg: float | None
    warnings: tuple[str, ...]


def design_advisory(
    hull: Hull,
    *,
    cp: float | None = None,
    displaced_mass_kg: float | None = None,
) -> DesignAdvisory:
    """Return non-blocking advisory metrics for hull-design feedback.

    Bands are drawn from ``docs/design/kayak_hull_design_constraints.md``:
    useful sea-kayak/surfski ``L/B_wl`` values start around 8 and run
    through the elite surfski region. RFC 0006's advisory banner uses
    ``Cp`` 0.50-0.65 and displacement volume 0.075-0.180 m3; the mass
    thresholds below use seawater density, matching the hydrostatics
    evaluator.
    """

    beam_wl = hull.beam_wl_m or hull.beam_oa_m
    l_over_bwl = hull.length_m / beam_wl
    cp_value = hull.Cp if cp is None else cp

    warnings: list[str] = []
    if l_over_bwl < 8.0:
        warnings.append("L/B_wl below touring guidance")
    elif l_over_bwl > 15.5:
        warnings.append("L/B_wl beyond elite surfski guidance")

    if cp_value < 0.50:
        warnings.append("Cp below recommended kayak range")
    elif cp_value > 0.65:
        warnings.append("Cp above recommended kayak range")

    if displaced_mass_kg is not None:
        if displaced_mass_kg < 0.075 * 1025.0:
            warnings.append("displacement below typical single-paddler load")
        elif displaced_mass_kg > 0.180 * 1025.0:
            warnings.append("displacement above typical single-paddler load")

    return DesignAdvisory(
        l_over_bwl=l_over_bwl,
        cp=cp_value,
        displaced_mass_kg=displaced_mass_kg,
        warnings=tuple(warnings),
    )
