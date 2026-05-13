"""Shared design advisory bands for kayak hulls.

These checks are intentionally non-blocking. They surface the class
envelope from the design constraints doc without making exploratory
designs invalid.
"""

from __future__ import annotations

from dataclasses import dataclass

from kayakgen.model.hull import Hull
from kayakgen.model.validity import (
    DesignValidityReport,
    design_warning_messages,
    evaluate_design_validity,
)


@dataclass(frozen=True)
class Advisory:
    """Structured warning guidance for UI field highlighting."""

    code: str
    message: str
    field_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "field_refs", tuple(self.field_refs))


@dataclass(frozen=True)
class DesignAdvisory:
    """Derived advisory metrics and warning strings for a hull."""

    l_over_bwl: float
    cp: float
    displaced_mass_kg: float | None
    warnings: tuple[str, ...]
    advisories: tuple[Advisory, ...]
    design_validity: DesignValidityReport


def design_advisory(
    hull: Hull,
    *,
    cp: float | None = None,
    displaced_mass_kg: float | None = None,
    selected_class: str | None = None,
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
    report = evaluate_design_validity(
        hull,
        cp=cp_value,
        displaced_mass_kg=displaced_mass_kg,
        selected_class=selected_class,
    )

    return DesignAdvisory(
        l_over_bwl=l_over_bwl,
        cp=cp_value,
        displaced_mass_kg=displaced_mass_kg,
        warnings=design_warning_messages(report),
        advisories=_advisories_from_design_validity(report),
        design_validity=report,
    )


def _advisories_from_design_validity(
    report: DesignValidityReport,
) -> tuple[Advisory, ...]:
    return tuple(
        Advisory(
            code=finding.code,
            message=finding.message,
            field_refs=finding.parameters,
        )
        for finding in report.findings
        if finding.level == "advisory" and finding.severity == "warning"
    )
