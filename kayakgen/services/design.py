"""Hull-state design service: presets, slider bounds, validity badge.

Pure orchestration helpers consumed by the web controllers. These do not
depend on any HTTP / Trame state object — callers project the relevant
state into a plain ``dict`` and pass it in.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from kayakgen.model.classes import CLASSES, KayakClass, list_classes
from kayakgen.model.hull import Hull

# Mirrors :data:`kayakgen.ui.web.state.HULL_STATE_FIELDS`. Duplicated to keep
# the services layer free of any ``kayakgen.ui.*`` imports per the
# architectural boundary contract.
_HULL_STATE_FIELDS: tuple[str, ...] = (
    "length_m",
    "beam_oa_m",
    "beam_wl_m",
    "draft_m",
    "deck_height_m",
    "Cp",
    "Cm",
    "deck_flatness",
    "center_box_ratio",
    "bow_rake",
    "stern_rake",
)
FULL_HULL_STATE_KEY = "loaded_hull_payload"

CLASS_PRESET_HULL_FIELDS: tuple[str, ...] = (
    "length_m",
    "beam_oa_m",
    "beam_wl_m",
    "draft_m",
    "Cp",
)


def _hull_from_state_dict(state: dict[str, Any]) -> Hull:
    """Build a :class:`Hull` from a flat state dict. Drops unknown keys."""
    loaded_hull = loaded_hull_from_web_state(state)
    if loaded_hull is not None and state_matches_loaded_hull(state, loaded_hull):
        return loaded_hull
    payload = {k: v for k, v in state.items() if k in _HULL_STATE_FIELDS or k == "name"}
    return Hull(**payload)


def loaded_hull_from_web_state(state: dict[str, Any]) -> Hull | None:
    """Return the opaque loaded Hull payload carried by web state, if valid."""
    raw = state.get(FULL_HULL_STATE_KEY)
    if raw is None:
        return None
    try:
        if isinstance(raw, str):
            return Hull.model_validate_json(raw)
        return Hull.model_validate(raw)
    except (TypeError, ValueError, ValidationError):
        return None


def state_matches_loaded_hull(state: dict[str, Any], hull: Hull) -> bool:
    """Return True when visible hull fields still match the opaque payload."""
    for field in (*_HULL_STATE_FIELDS, "name"):
        if field not in state:
            continue
        if not _state_value_equals_model_value(state[field], getattr(hull, field)):
            return False
    return True


def _state_value_equals_model_value(state_value: Any, model_value: Any) -> bool:
    if state_value is None or model_value is None:
        return state_value is model_value
    if isinstance(state_value, (int, float)) or isinstance(model_value, (int, float)):
        try:
            return abs(float(state_value) - float(model_value)) <= 1e-9
        except (TypeError, ValueError):
            return False
    return state_value == model_value


def clamp_beam_wl_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with web ``beam_wl_m`` constrained to ``beam_oa_m``."""
    normalized = dict(state)
    beam_oa = normalized.get("beam_oa_m")
    beam_wl = normalized.get("beam_wl_m")
    if beam_oa is None or beam_wl is None:
        return normalized
    try:
        beam_oa_f = float(beam_oa)
        beam_wl_f = float(beam_wl)
    except (TypeError, ValueError):
        return normalized
    if beam_wl_f > beam_oa_f:
        normalized["beam_wl_m"] = beam_oa_f
    return normalized


def hull_from_web_state(state: dict[str, Any]) -> Hull:
    """Build a Hull from web state after applying UI-level normalization."""
    return _hull_from_state_dict(clamp_beam_wl_state(state))


def class_preset_options() -> list[dict[str, str]]:
    """Return stable class preset ids with human labels for web controls."""
    return [
        *[
            {
                "value": kayak_class.name,
                "label": kayak_class.label,
            }
            for kayak_class in list_classes()
        ],
        {"value": "custom", "label": "Custom"},
    ]


def class_preset_read_model(preset: str) -> dict[str, Any]:
    """Class preset values and bounds for the web parameter rail."""
    if preset == "custom" or preset not in CLASSES:
        return {
            "preset": "custom",
            "label": "Custom",
            "values": {},
            "bounds": {},
        }
    kayak_class = CLASSES[preset]
    hull = kayak_class.default_hull()
    return {
        "preset": kayak_class.name,
        "label": kayak_class.label,
        "values": {
            field: getattr(hull, field)
            for field in CLASS_PRESET_HULL_FIELDS
        },
        "bounds": _class_bounds(kayak_class),
    }


def validity_badge_from_state(state: dict[str, Any]) -> str:
    """Return the exact RFC 0033/0034 web validity badge string."""
    hull = hull_from_web_state(state)
    matching_class = _matching_kayak_class(hull)
    if matching_class is not None:
        return f"In {matching_class.label} envelope"

    beam_wl = hull.beam_wl_m or hull.beam_oa_m
    l_over_bwl = hull.length_m / beam_wl
    if l_over_bwl < 8.0:
        return "Custom — sub-touring"
    if l_over_bwl > 15.5:
        return "Custom — beyond elite"
    return f"Custom (L/B_wl={l_over_bwl:.1f})"


def validation_error_payload(exc: Exception) -> dict[str, Any]:
    """Controlled JSON payload for invalid web state."""
    details: list[dict[str, str]] = []
    if isinstance(exc, ValidationError):
        for err in exc.errors():
            loc = ".".join(str(part) for part in err.get("loc", ())) or "state"
            details.append(
                {
                    "field": loc,
                    "message": str(err.get("msg", "invalid value")),
                    "type": str(err.get("type", "value_error")),
                }
            )
    else:
        details.append(
            {
                "field": "state",
                "message": "invalid hull state",
                "type": type(exc).__name__,
            }
        )
    return {"error": "invalid_hull_state", "details": details}


def _class_bounds(kayak_class: KayakClass) -> dict[str, dict[str, float]]:
    return {
        field: {
            "min": getattr(kayak_class, field).min,
            "max": getattr(kayak_class, field).max,
            "default": getattr(kayak_class, field).default,
        }
        for field in CLASS_PRESET_HULL_FIELDS
    }


def _matching_kayak_class(hull: Hull) -> KayakClass | None:
    for kayak_class in list_classes():
        if _hull_in_kayak_class(hull, kayak_class):
            return kayak_class
    return None


def _hull_in_kayak_class(hull: Hull, kayak_class: KayakClass) -> bool:
    values = {
        "length_m": hull.length_m,
        "beam_oa_m": hull.beam_oa_m,
        "beam_wl_m": hull.beam_wl_m or hull.beam_oa_m,
        "draft_m": hull.draft_m,
        "Cp": hull.Cp,
    }
    bounds = _class_bounds(kayak_class)
    return all(
        bounds[field]["min"] <= value <= bounds[field]["max"]
        for field, value in values.items()
    )
