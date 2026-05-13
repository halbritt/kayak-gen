"""Shared conversion from desktop GUI parameter names to ``Hull`` fields."""

from __future__ import annotations

from typing import Any

from kayakgen.model.hull import Hull

GUI_TO_HULL = {
    "length": "length_m",
    "beam": "beam_oa_m",
    "beam_wl": "beam_wl_m",
    "draft": "draft_m",
    "deck_height": "deck_height_m",
    "Cp": "Cp",
    "deck_flatness": "deck_flatness",
    "center_box_ratio": "center_box_ratio",
    "bow_rake": "bow_rake",
}


def hull_from_gui_params(params: dict[str, Any]) -> Hull:
    """Build a :class:`Hull` from the desktop/PyVista GUI parameter dict."""
    payload = {
        hull_key: params[gui_key]
        for gui_key, hull_key in GUI_TO_HULL.items()
        if gui_key in params
    }
    return Hull(**payload)
