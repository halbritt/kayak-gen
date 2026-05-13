"""Shared state schema between Trame UI and the kayakgen Hull aggregate.

The Trame app maintains a Vue-side state dict whose keys mirror the
:class:`Hull` field names. This module owns the conversion between that
flat state dict and a real :class:`Hull`, and the round-trip encoding to
and from a base64 URL fragment.
"""

from __future__ import annotations

import base64
from urllib.parse import parse_qs
from typing import Any

from kayakgen.model.hull import Hull


# Fields the UI exposes as sliders / inputs. Order matters for layout.
HULL_STATE_FIELDS: tuple[str, ...] = (
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


def state_dict_from_hull(hull: Hull) -> dict[str, Any]:
    """Project a :class:`Hull` onto the flat state dict the Vue app reads."""
    out: dict[str, Any] = {field: getattr(hull, field) for field in HULL_STATE_FIELDS}
    out["name"] = hull.name
    return out


def hull_from_state_dict(state: dict[str, Any]) -> Hull:
    """Build a :class:`Hull` from the Vue-side state dict.

    Unknown keys are dropped (Pydantic would otherwise reject them with
    ``extra="forbid"``).
    """
    payload = {k: v for k, v in state.items() if k in HULL_STATE_FIELDS or k == "name"}
    return Hull(**payload)


def encode_hull_query(hull: Hull) -> str:
    """URL-safe base64 of the Hull JSON. Decodes via :func:`decode_hull_query`."""
    return base64.urlsafe_b64encode(hull.model_dump_json().encode("utf-8")).decode("ascii")


def decode_hull_query(query: str) -> Hull:
    """Inverse of :func:`encode_hull_query`."""
    blob = base64.urlsafe_b64decode(query.encode("ascii")).decode("utf-8")
    return Hull.model_validate_json(blob)


def hull_from_query_string(query: str) -> Hull | None:
    """Decode a `?hull=...` query string into a Hull, if present."""
    raw = query[1:] if query.startswith("?") else query
    values = parse_qs(raw).get("hull")
    if not values:
        return None
    return decode_hull_query(values[0])
