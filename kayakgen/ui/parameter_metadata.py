"""Presentation-layer label / unit / description registry for hull parameters.

RFC 0060: the web Generate panel form needs friendly field labels and
hover-for-description tooltips for the raw hull-JSON parameters
(`length_m`, `beam_oa_m`, `Cp`, ...). The registry is a single source of
truth that the presentation layer consults; the form's submitted JSON
payload continues to use the original parameter names (the registry
keys), so this module is purely additive on the wire.

Closes audit finding `AUD-O-003` from
`docs/audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HullParameterMetadata(BaseModel):
    """Presentation-layer label / unit / description for one hull
    parameter exposed by the web Generate panel form.

    Fields are presentation-only; the form's submitted JSON payload uses
    the original parameter name (the registry key), not any of these
    fields.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    parameter: str = Field(min_length=1)
    label: str = Field(min_length=1)
    unit: str | None = None
    description: str = Field(min_length=1)


HULL_PARAMETER_METADATA: dict[str, HullParameterMetadata] = {
    "length_m": HullParameterMetadata(
        parameter="length_m",
        label="Length",
        unit="m",
        description="Overall length, bow tip to stern tip.",
    ),
    "beam_oa_m": HullParameterMetadata(
        parameter="beam_oa_m",
        label="Beam OA",
        unit="m",
        description="Overall beam at the widest cross-section.",
    ),
    "beam_wl_m": HullParameterMetadata(
        parameter="beam_wl_m",
        label="Beam WL",
        unit="m",
        description="Beam at the design waterline.",
    ),
    "draft_m": HullParameterMetadata(
        parameter="draft_m",
        label="Draft",
        unit="m",
        description="Vertical distance from waterline to deepest point.",
    ),
    "deck_height_m": HullParameterMetadata(
        parameter="deck_height_m",
        label="Deck height",
        unit="m",
        description="Vertical distance from waterline to deck sheer.",
    ),
    "Cp": HullParameterMetadata(
        parameter="Cp",
        label="Prismatic coefficient (Cp)",
        unit=None,
        description=(
            "Volume coefficient: displaced volume divided by midship "
            "area times waterline length. Higher = fuller ends."
        ),
    ),
    "Cm": HullParameterMetadata(
        parameter="Cm",
        label="Midship coefficient (Cm)",
        unit=None,
        description=(
            "Midship-section coefficient: midship area divided by "
            "(beam_wl × draft). Higher = fuller midsection."
        ),
    ),
    "deck_flatness": HullParameterMetadata(
        parameter="deck_flatness",
        label="Deck flatness",
        unit=None,
        description=(
            "Dimensionless deck-crown flatness control; higher = flatter "
            "deck (less crown)."
        ),
    ),
    "center_box_ratio": HullParameterMetadata(
        parameter="center_box_ratio",
        label="Parallel mid-body ratio",
        unit=None,
        description=(
            "Fraction of length occupied by the parallel mid-body "
            "section (0 = pure fish-form, 1 = fully prismatic)."
        ),
    ),
    "bow_rake": HullParameterMetadata(
        parameter="bow_rake",
        label="Bow rake",
        unit=None,
        description=(
            "Bow-end fullness: 0 = plumb stem, 1 = legacy raked taper. "
            "Dimensionless; reverse rake and values outside [0, 1] are "
            "invalid."
        ),
    ),
    "stern_rake": HullParameterMetadata(
        parameter="stern_rake",
        label="Stern rake",
        unit=None,
        description=(
            "Stern-end fullness: 0 = plumb transom, 1 = legacy raked "
            "taper. Same shape as bow_rake."
        ),
    ),
}


def label_with_unit(parameter: str) -> str:
    """Return ``label (unit)`` for use as a Vuetify field label.

    Returns the raw parameter name if the registry has no entry for it.
    Callers should not rely on this fallback in production; the
    regression test in ``tests/test_hull_parameter_metadata.py`` pins the
    contract.
    """

    metadata = HULL_PARAMETER_METADATA.get(parameter)
    if metadata is None:
        return parameter
    if metadata.unit is None:
        return metadata.label
    return f"{metadata.label} ({metadata.unit})"


def description(parameter: str) -> str | None:
    """Return the tooltip text for ``parameter``, or ``None`` if not in the registry."""

    metadata = HULL_PARAMETER_METADATA.get(parameter)
    return metadata.description if metadata is not None else None


__all__ = [
    "HULL_PARAMETER_METADATA",
    "HullParameterMetadata",
    "description",
    "label_with_unit",
]
