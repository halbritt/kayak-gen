"""Regression: pin the RFC 0060 hull-parameter metadata registry contract.

The registry lives at ``kayakgen.ui.parameter_metadata`` and feeds the
web Generate-panel form's friendly labels and tooltips. The contract:

* every key in ``BASE_HULL_KEYS`` has a registry entry — the rail can't
  render a bare key as a label;
* every entry's ``label``, ``description``, and (if non-``None``)
  ``unit`` are non-blank trimmed strings — Pydantic min-length is
  defense in depth, but this test pins the trimmed-stringness;
* every registry key resolves to a ``Hull`` field name — catches stale
  registry rows after a ``Hull`` schema refactor;
* the helper API renders the expected presentational strings.

Closes RFC 0060 §5 + extends the audit-finding ``AUD-O-003`` follow-up.
"""

from __future__ import annotations

import pytest

from kayakgen.model.hull import Hull
from kayakgen.ui.parameter_metadata import (
    HULL_PARAMETER_METADATA,
    HullParameterMetadata,
    description,
    label_with_unit,
)
from kayakgen.ui.web.generate_spec_form import BASE_HULL_KEYS


@pytest.mark.parametrize("key", BASE_HULL_KEYS)
def test_base_hull_key_has_registry_entry(key: str) -> None:
    """Every ``BASE_HULL_KEYS`` entry must have a registry row.

    Without this, the rail would have to fall back to the raw JSON
    parameter name as a label — the exact bug RFC 0060 fixes.
    """

    assert key in HULL_PARAMETER_METADATA, (
        f"BASE_HULL_KEYS key {key!r} is missing from HULL_PARAMETER_METADATA"
    )


@pytest.mark.parametrize("key", sorted(HULL_PARAMETER_METADATA.keys()))
def test_registry_entry_fields_are_trimmed_non_blank(key: str) -> None:
    metadata = HULL_PARAMETER_METADATA[key]
    assert isinstance(metadata, HullParameterMetadata)
    # `parameter` should equal the dict key; defensive pin.
    assert metadata.parameter == key, (
        f"HULL_PARAMETER_METADATA[{key!r}].parameter is {metadata.parameter!r}; "
        "the registry key and the value-object parameter must match"
    )
    label = metadata.label
    assert label.strip() == label and label.strip() != "", (
        f"HULL_PARAMETER_METADATA[{key!r}].label must be a non-blank trimmed string"
    )
    desc = metadata.description
    assert desc.strip() == desc and desc.strip() != "", (
        f"HULL_PARAMETER_METADATA[{key!r}].description must be a non-blank trimmed string"
    )
    if metadata.unit is not None:
        unit = metadata.unit
        assert unit.strip() == unit and unit.strip() != "", (
            f"HULL_PARAMETER_METADATA[{key!r}].unit must be a non-blank trimmed string "
            "when not None"
        )


@pytest.mark.parametrize("key", sorted(HULL_PARAMETER_METADATA.keys()))
def test_registry_key_resolves_to_hull_field(key: str) -> None:
    """Each registry key must name a real ``Hull`` field.

    Catches stale registry rows after a ``Hull`` schema refactor — the
    registry is purely presentational, but a description that points at
    a nonexistent field is dead documentation that misleads operators.
    """

    hull_fields = set(Hull.model_fields.keys())
    assert key in hull_fields, (
        f"HULL_PARAMETER_METADATA key {key!r} does not resolve to a Hull field; "
        f"available fields: {sorted(hull_fields)}"
    )


def test_label_with_unit_dimensional_parameter() -> None:
    assert label_with_unit("length_m") == "Length (m)"


def test_label_with_unit_dimensionless_parameter() -> None:
    # `Cp` has unit=None; the helper returns the bare label, no parens.
    assert label_with_unit("Cp") == "Prismatic coefficient (Cp)"


def test_label_with_unit_unknown_parameter_falls_back_to_raw_key() -> None:
    assert label_with_unit("unknown_param") == "unknown_param"


def test_description_returns_registry_text_for_known_key() -> None:
    assert description("length_m") == (
        "Overall length, bow tip to stern tip."
    )


def test_description_returns_none_for_unknown_key() -> None:
    assert description("not_a_real_param") is None


def test_registry_has_eleven_entries() -> None:
    """RFC 0060 §2 lists 11 keys; pin the count so adds/removes are deliberate."""

    assert len(HULL_PARAMETER_METADATA) == 11, (
        "HULL_PARAMETER_METADATA drifted from the RFC 0060 §2 baseline of 11 "
        f"entries (now {len(HULL_PARAMETER_METADATA)}); update RFC 0060 first"
    )
