"""Desktop matplotlib slider ranges and step overrides.

Kept separate from ``HullParameterMetadata`` per D043 open question 1:
ranges are UI-tuned and differ from ``Hull`` validator ranges. The
registry is presentation-only; the slider ranges are presentation +
input-shape.

RFC 0061 extracts these from the legacy
``kayakgen.ui.desktop.KayakGUI.SLIDERS`` / ``DEFAULTS`` literals.
Keys are canonical Hull JSON field names (plus the view-only
``target_speed_kt`` from ``VIEW_PARAMETER_METADATA``); the numeric
values are byte-equal to today's desktop literals so behavior is
preserved.
"""

from __future__ import annotations

SLIDER_RANGES: dict[str, tuple[float, float]] = {
    "length_m": (2.0, 6.5),
    "beam_oa_m": (0.30, 0.90),
    "beam_wl_m": (0.30, 0.90),
    "draft_m": (0.05, 0.25),
    "deck_height_m": (0.15, 0.40),
    "Cp": (0.45, 0.70),
    "Cm": (0.65, 0.95),
    "deck_flatness": (2.0, 16.0),
    "center_box_ratio": (0.10, 0.60),
    "bow_rake": (0.0, 1.0),
    "stern_rake": (0.0, 1.0),
    "target_speed_kt": (1.0, 6.0),
}

SLIDER_STEPS: dict[str, float] = {"Cm": 0.005}

SLIDER_DEFAULTS: dict[str, float] = {
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
    "target_speed_kt": 3.5,
}


__all__ = [
    "SLIDER_DEFAULTS",
    "SLIDER_RANGES",
    "SLIDER_STEPS",
]
