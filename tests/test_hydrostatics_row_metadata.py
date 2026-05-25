"""Regression net for the RFC 0062 ``HydrostaticsRowMetadata`` registry.

The registry lives at :mod:`kayakgen.ui.hydrostatics_metadata` and feeds
the ``analysis_view_model::hydro_rows`` label + unit slots. The contract:

* every key referenced by ``analysis_view_model::hydro_rows`` exists in
  the registry — the Hydro tab can't render a bare key as a label;
* every entry's ``label`` and ``description`` are non-blank trimmed
  strings; Pydantic's ``min_length=1`` is defense in depth, but this
  test pins the trimmed-stringness for human-readable copy;
* the label list emitted by ``analysis_view_model`` matches the registry
  labels (so the wiring actually goes through the registry);
* ``hydro_rows_from_state`` output is byte-stable across the refactor
  (the regression assertion pins the post-``b82b544`` baseline; future
  intentional copy changes update both the registry and this list in
  the same commit).

Closes RFC 0062 §Acceptance + the audit finding ``AUD-O-005`` follow-up.
"""

from __future__ import annotations

import pytest

from kayakgen.ui.hydrostatics_metadata import (
    HYDROSTATICS_ROW_METADATA,
    HydrostaticsRowMetadata,
)

EXPECTED_KEYS: tuple[str, ...] = (
    "displacement",
    "wetted_surface",
    "waterplane_area",
    "gm0",
    "cp_actual",
    "cm_actual",
    "l_over_bwl",
)

EXPECTED_LABELS: tuple[str, ...] = (
    "Displacement",
    "Wetted surface",
    "Waterplane area",
    "GM0",
    "Cp actual",
    "Cm actual",
    "L/B wl",
)


def test_registry_covers_expected_keys() -> None:
    """Every key consumed by ``analysis_view_model`` must have a row."""
    assert set(HYDROSTATICS_ROW_METADATA.keys()) == set(EXPECTED_KEYS)


def test_registry_has_seven_entries() -> None:
    """RFC 0062 §Proposal lists 7 rows; pin the count so adds/removes are deliberate."""

    assert len(HYDROSTATICS_ROW_METADATA) == 7, (
        "HYDROSTATICS_ROW_METADATA drifted from the RFC 0062 baseline of 7 "
        f"entries (now {len(HYDROSTATICS_ROW_METADATA)}); update RFC 0062 first"
    )


@pytest.mark.parametrize("key", EXPECTED_KEYS)
def test_registry_entries_are_well_formed(key: str) -> None:
    meta = HYDROSTATICS_ROW_METADATA[key]
    assert isinstance(meta, HydrostaticsRowMetadata)
    # `parameter` field must equal the registry key; defensive pin.
    assert meta.parameter == key, (
        f"HYDROSTATICS_ROW_METADATA[{key!r}].parameter is {meta.parameter!r}; "
        "the registry key and the value-object parameter must match"
    )
    label = meta.label
    assert label.strip() == label and label.strip() != "", (
        f"HYDROSTATICS_ROW_METADATA[{key!r}].label must be a non-blank trimmed string"
    )
    desc = meta.description
    assert desc.strip() == desc and desc.strip() != "", (
        f"HYDROSTATICS_ROW_METADATA[{key!r}].description must be a non-blank trimmed string"
    )
    if meta.unit is not None:
        unit = meta.unit
        assert unit.strip() == unit and unit.strip() != "", (
            f"HYDROSTATICS_ROW_METADATA[{key!r}].unit must be a non-blank trimmed string "
            "when not None"
        )


def test_analysis_view_model_labels_match_registry() -> None:
    """``analysis_view_model::hydro_rows`` labels must come from the registry.

    Without this, the wiring could silently regress to a hardcoded
    label and only manual UI inspection would catch the drift.
    """

    from kayakgen.model.hull import Hull
    from kayakgen.services.evaluation import analysis_view_model
    from kayakgen.ui.web.state import state_dict_from_hull

    state = state_dict_from_hull(Hull())
    rows = analysis_view_model(state)["hydro_rows"]
    expected_labels = [HYDROSTATICS_ROW_METADATA[k].label for k in EXPECTED_KEYS]
    actual_labels = [row[0] for row in rows]
    assert actual_labels == expected_labels


def test_hydro_rows_from_state_byte_stable() -> None:
    """``hydro_rows_from_state`` label output must remain byte-stable.

    The expected list is the post-``b82b544`` / pre-RFC 0062 baseline.
    Any future intentional label change requires updating
    :data:`EXPECTED_LABELS` in the same commit as the registry edit
    (intentional change), otherwise this test fails.
    """

    from kayakgen.model.hull import Hull
    from kayakgen.services.evaluation import hydro_rows_from_state
    from kayakgen.ui.web.state import state_dict_from_hull

    state = state_dict_from_hull(Hull())
    rows = hydro_rows_from_state(state)
    labels = [row["label"] for row in rows if row["label"] != "Warning"]
    assert labels == list(EXPECTED_LABELS)


def test_hydro_rows_from_state_preserves_unit_in_value() -> None:
    """``hydro_rows_from_state`` must keep its ``"<value> <unit>"`` value formatting.

    The wire payload is ``[{"label", "value"}]`` with ``value`` carrying
    the formatted number and (when present) the unit suffix; pin this
    so the registry-sourced unit is still concatenated by
    ``hydro_rows_from_state``.
    """

    from kayakgen.model.hull import Hull
    from kayakgen.services.evaluation import hydro_rows_from_state
    from kayakgen.ui.web.state import state_dict_from_hull

    state = state_dict_from_hull(Hull())
    rows = hydro_rows_from_state(state)
    by_label = {row["label"]: row["value"] for row in rows}
    # Dimensional rows carry the unit suffix; dimensionless rows do not.
    assert by_label["Displacement"].endswith(" kg")
    assert by_label["Wetted surface"].endswith(" m^2")
    assert by_label["Waterplane area"].endswith(" m^2")
    assert by_label["GM0"].endswith(" m")
    # Dimensionless rows: no trailing space, no unit suffix.
    for label in ("Cp actual", "Cm actual", "L/B wl"):
        value = by_label[label]
        assert " " not in value, (
            f"hydro_rows_from_state value for {label!r} ({value!r}) must not "
            "carry a unit suffix; the registry stores unit=None for this row"
        )
