"""Shared state schema between Trame UI and the kayakgen Hull aggregate.

The Trame app maintains a Vue-side state dict whose keys mirror the
:class:`Hull` field names. This module owns the conversion between that
flat state dict and a real :class:`Hull`, and the round-trip encoding to
and from a base64 URL fragment.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs

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


@dataclass(frozen=True)
class WebStateSchema:
    """Declared web-state keys and compatibility aliases."""

    snapshot_keys: tuple[str, ...]
    mesh_package_ref_aliases: tuple[str, ...]
    cfd_status_aliases: tuple[str, ...]
    cfd_payload_aliases: tuple[str, ...]
    cfd_status_line_aliases: tuple[str, ...]


MESH_PACKAGE_REF_ALIASES: tuple[str, ...] = ("mesh_package_ref", "cfd_mesh_package_ref")
CFD_STATUS_ALIASES: tuple[str, ...] = ("cfd_status", "status")
CFD_PAYLOAD_ALIASES: tuple[str, ...] = (
    "cfd_payload",
    "cfd_job_payload",
    "cfd_last_payload",
)
CFD_STATUS_LINE_ALIASES: tuple[str, ...] = ("cfd_status_lines",)

WEB_STATE_SCHEMA = WebStateSchema(
    snapshot_keys=(
        *HULL_STATE_FIELDS,
        "name",
        "target_speed_kt",
        "class_preset",
        *MESH_PACKAGE_REF_ALIASES,
        *CFD_STATUS_ALIASES,
        *CFD_PAYLOAD_ALIASES,
        *CFD_STATUS_LINE_ALIASES,
    ),
    mesh_package_ref_aliases=MESH_PACKAGE_REF_ALIASES,
    cfd_status_aliases=CFD_STATUS_ALIASES,
    cfd_payload_aliases=CFD_PAYLOAD_ALIASES,
    cfd_status_line_aliases=CFD_STATUS_LINE_ALIASES,
)

STATE_SNAPSHOT_KEYS: tuple[str, ...] = WEB_STATE_SCHEMA.snapshot_keys


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
