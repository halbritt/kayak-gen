"""Regression: pin the RFC 0061 desktop-slider registry contract.

The desktop GUI's ``KayakGUI.SLIDERS`` / ``DEFAULTS`` / ``GLOBAL_RANGES``
now derive from:

* :data:`kayakgen.ui.desktop_slider_ranges.SLIDER_RANGES` /
  ``SLIDER_DEFAULTS`` / ``SLIDER_STEPS`` — the desktop-tuned slider
  ranges, step overrides, and default values.
* :data:`kayakgen.ui.parameter_metadata.HULL_PARAMETER_METADATA` and
  :data:`kayakgen.ui.parameter_metadata.VIEW_PARAMETER_METADATA` — the
  presentation-layer label / description registry.

This test pins the five assertions from RFC 0061 §5:

1. every ``SLIDER_RANGES`` key resolves to one of the two registries;
2. ``HULL_PARAMETER_METADATA.keys()`` and
   ``VIEW_PARAMETER_METADATA.keys()`` are disjoint;
3. every Hull-side ``SLIDER_RANGES`` key resolves to a real ``Hull``
   field;
4. ``KayakGUI.SLIDERS[i][1] == label_with_unit(SLIDERS[i][0])`` for
   every row;
5. ``KayakGUI.DEFAULTS`` filtered through the canonical Hull keys
   produces a valid ``Hull``.

Closes D043's named "desktop SLIDERS migration to the same registry"
follow-up.
"""

from __future__ import annotations

import pytest

from kayakgen.model.hull import Hull
from kayakgen.ui.desktop_slider_ranges import SLIDER_RANGES
from kayakgen.ui.parameter_metadata import (
    HULL_PARAMETER_METADATA,
    VIEW_PARAMETER_METADATA,
    label_with_unit,
)


@pytest.fixture(scope="module")
def kayak_gui_class():
    """Import ``KayakGUI`` lazily so the test still runs without ``kayakgen[desktop]``.

    The desktop GUI module imports matplotlib + PyQt6 at import time; if
    either is missing, skip rather than fail.
    """

    pytest.importorskip("matplotlib", reason="kayakgen[desktop] is not installed")
    pytest.importorskip("PyQt6", reason="kayakgen[desktop] is not installed")
    from kayakgen.ui.desktop import KayakGUI

    return KayakGUI


@pytest.mark.parametrize("key", sorted(SLIDER_RANGES.keys()))
def test_slider_range_key_resolves_to_some_registry(key: str) -> None:
    """RFC 0061 §5: every ``SLIDER_RANGES`` key must be owned by one of
    the two registries (Hull-side or view-only)."""

    assert key in HULL_PARAMETER_METADATA or key in VIEW_PARAMETER_METADATA, (
        f"SLIDER_RANGES key {key!r} is missing from both "
        "HULL_PARAMETER_METADATA and VIEW_PARAMETER_METADATA"
    )


def test_hull_and_view_registries_have_disjoint_keys() -> None:
    """The two registries describe disjoint parameter sets.

    A key appearing in both would mean a parameter is both a Hull field
    and a view-only parameter, which violates the RFC 0061 boundary
    (and would make the ``label_with_unit`` fall-back order ambiguous).
    """

    overlap = set(HULL_PARAMETER_METADATA) & set(VIEW_PARAMETER_METADATA)
    assert overlap == set(), (
        f"HULL_PARAMETER_METADATA and VIEW_PARAMETER_METADATA share keys: "
        f"{sorted(overlap)!r}"
    )


@pytest.mark.parametrize(
    "key",
    sorted(set(SLIDER_RANGES) - set(VIEW_PARAMETER_METADATA)),
)
def test_hull_side_slider_key_resolves_to_hull_field(key: str) -> None:
    """Every Hull-side ``SLIDER_RANGES`` key must name a real ``Hull`` field.

    The view-only keys (``target_speed_kt``) are excluded; they are
    intentionally not ``Hull`` fields.
    """

    hull_fields = set(Hull.model_fields.keys())
    assert key in hull_fields, (
        f"SLIDER_RANGES Hull-side key {key!r} does not resolve to a Hull "
        f"field; available fields: {sorted(hull_fields)}"
    )


def test_kayak_gui_slider_labels_match_label_with_unit(kayak_gui_class) -> None:
    """``KayakGUI.SLIDERS[i][1] == label_with_unit(SLIDERS[i][0])`` per row.

    Catches drift between the SLIDERS table (which feeds the matplotlib
    Slider label) and the registry (which is the canonical source).
    """

    for key, label, _vmin, _vmax in kayak_gui_class.SLIDERS:
        assert label == label_with_unit(key), (
            f"KayakGUI.SLIDERS row for {key!r} carries label {label!r} but "
            f"label_with_unit({key!r}) returns {label_with_unit(key)!r}"
        )


def test_kayak_gui_defaults_round_trip_through_hull(kayak_gui_class) -> None:
    """``KayakGUI.DEFAULTS`` filtered through the Hull-side keys must
    construct a valid ``Hull`` — i.e. the defaults respect Hull's
    validators (ranges, types, frozen-shape)."""

    non_hull = set(kayak_gui_class._NON_HULL_GUI_KEYS)
    hull = Hull(
        **{
            key: value
            for key, value in kayak_gui_class.DEFAULTS.items()
            if key not in non_hull
        }
    )
    # If construction succeeded, the round-trip is asserted by Hull's
    # own validators. We additionally pin a couple of values so a
    # silent default-set drift trips this test.
    assert hull.length_m == kayak_gui_class.DEFAULTS["length_m"]
    assert hull.beam_oa_m == kayak_gui_class.DEFAULTS["beam_oa_m"]
