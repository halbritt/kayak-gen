"""GUI parameter conversion shared by desktop and PyVista views.

RFC 0061 retired the short-key GUI form and replaced it with canonical
Hull JSON field names. The legacy ``hull_from_gui_params`` shim still
returns a valid ``Hull`` (filtered against ``Hull.model_fields``), but
it now emits a ``DeprecationWarning`` naming RFC 0061.
"""

from __future__ import annotations

import warnings

import pytest

from kayakgen.ui.gui_params import hull_from_gui_params


def test_gui_params_preserve_new_hull_fields() -> None:
    """The shim accepts canonical Hull JSON keys post-RFC 0061.

    The old short-key form (``length``, ``beam``, ...) is no longer
    translated; the shim filters against ``Hull.model_fields`` so the
    canonical names are the only ones that round-trip.
    """

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        hull = hull_from_gui_params(
            {
                "length_m": 5.0,
                "beam_oa_m": 0.58,
                "beam_wl_m": 0.53,
                "draft_m": 0.12,
                "deck_height_m": 0.23,
                "Cp": 0.54,
                "Cm": 0.81,
                "deck_flatness": 8.0,
                "center_box_ratio": 0.33,
                "bow_rake": 0.0,
                "stern_rake": 1.0,
            }
        )
    assert hull.beam_wl_m == 0.53
    assert hull.Cm == 0.81
    assert hull.bow_rake == 0.0
    assert hull.stern_rake == 1.0


def test_hull_from_gui_params_emits_rfc_0061_deprecation_warning() -> None:
    """RFC 0061 §4: the shim must announce its deprecation."""

    with pytest.warns(DeprecationWarning, match="RFC 0061"):
        hull_from_gui_params(
            {
                "length_m": 4.5,
                "beam_oa_m": 0.55,
                "beam_wl_m": 0.55,
                "draft_m": 0.12,
                "deck_height_m": 0.23,
                "Cp": 0.55,
                "Cm": 0.85,
                "deck_flatness": 8.0,
                "center_box_ratio": 0.33,
                "bow_rake": 1.0,
                "stern_rake": 1.0,
            }
        )
