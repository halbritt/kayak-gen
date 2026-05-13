"""GUI parameter conversion shared by desktop and PyVista views."""

from __future__ import annotations

from kayakgen.ui.gui_params import hull_from_gui_params


def test_gui_params_preserve_new_hull_fields() -> None:
    hull = hull_from_gui_params(
        {
            "length": 5.0,
            "beam": 0.58,
            "beam_wl": 0.53,
            "draft": 0.12,
            "deck_height": 0.23,
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
