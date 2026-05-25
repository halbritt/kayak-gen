"""Presentation-layer label / unit / description registry for hydrostatics rows.

RFC 0062: the Hydro tab and ``hydro_rows_from_state`` need a single source
of truth for human-readable labels, units, and descriptions of the rows
surfaced by ``analysis_view_model::hydro_rows``. The registry is a
sibling to :mod:`kayakgen.ui.parameter_metadata` (RFC 0060) and the
desktop slider registry consumed by RFC 0061; this is the third
application of the D043 "presentation-layer registry per surface family"
pattern.

The registry is presentation-only. The numeric values surfaced in the
hydro tuple ``(label, value, unit)`` come from the evaluator; only the
``label`` and ``unit`` slots are sourced here. The wire payload shape
emitted by ``hydro_rows_from_state`` is byte-stable across the refactor
(pinned by ``tests/test_hydrostatics_row_metadata.py``).

Closes audit finding ``AUD-O-005`` from
``docs/audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HydrostaticsRowMetadata(BaseModel):
    """Presentation-layer label / unit / description for one hydrostatics
    row surfaced by the Hydro tab.

    Fields are presentation-only; the underlying numeric values come
    from the evaluator. ``unit`` is ``None`` for dimensionless rows
    (Cp actual, Cm actual, L/B wl).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    parameter: str = Field(min_length=1)
    label: str = Field(min_length=1)
    unit: str | None = None
    description: str = Field(min_length=1)


HYDROSTATICS_ROW_METADATA: dict[str, HydrostaticsRowMetadata] = {
    "displacement": HydrostaticsRowMetadata(
        parameter="displacement",
        label="Displacement",
        unit="kg",
        description=(
            "Displaced mass at the design waterline. Equals the "
            "kayak's weight including paddler and load when the hull "
            "sits at the modelled waterline."
        ),
    ),
    "wetted_surface": HydrostaticsRowMetadata(
        parameter="wetted_surface",
        label="Wetted surface",
        unit="m^2",
        description=(
            "Hull surface area below the waterline. Drives viscous "
            "resistance: lower is faster at low speeds."
        ),
    ),
    "waterplane_area": HydrostaticsRowMetadata(
        parameter="waterplane_area",
        label="Waterplane area",
        unit="m^2",
        description=(
            "Cross-section area at the waterline. Influences pitch "
            "and heave responses."
        ),
    ),
    "gm0": HydrostaticsRowMetadata(
        parameter="gm0",
        label="GM0",
        unit="m",
        description=(
            "Initial metacentric height. Larger values mean stiffer "
            "initial stability; very small or negative values mean "
            "the hull is unstable at zero heel."
        ),
    ),
    "cp_actual": HydrostaticsRowMetadata(
        parameter="cp_actual",
        label="Cp actual",
        unit=None,
        description=(
            "Prismatic coefficient computed from the current hull "
            "geometry. Compare against the rail-input Cp to see how "
            "closely the generated hull tracks the requested shape."
        ),
    ),
    "cm_actual": HydrostaticsRowMetadata(
        parameter="cm_actual",
        label="Cm actual",
        unit=None,
        description=(
            "Midship coefficient computed from the current hull "
            "geometry. Compare against the rail-input Cm."
        ),
    ),
    "l_over_bwl": HydrostaticsRowMetadata(
        parameter="l_over_bwl",
        label="L/B wl",
        unit=None,
        description=(
            "Length-to-beam ratio at the waterline. Used by the "
            "class-envelope validity badge."
        ),
    ),
}


__all__ = [
    "HYDROSTATICS_ROW_METADATA",
    "HydrostaticsRowMetadata",
]
