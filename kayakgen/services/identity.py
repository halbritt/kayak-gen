"""Identity hashing functions for kayakgen artifacts (RFC 0049).

This module owns the four explicit hash concepts defined by RFC 0049:

- :func:`record_hash` — SHA-256 over a canonical-form JSON payload. The
  invariant is "differs iff the canonical bytes differ"; canonicalisation
  is sorted keys + no insignificant whitespace.
- :func:`design_hash_for_hull` — SHA-256 over *only* the physical inputs
  that affect a hull's geometry/evaluation. Renaming a hull, changing
  ``class_preset`` (if it ever lands), or reordering JSON keys does not
  change this hash. Changing ``Cp`` (or any other physical input) does.
- :func:`run_hash` — SHA-256 over a canonical ``{spec, version}`` blob.

All hashes are 64-character lowercase hex (SHA-256). The functions are
pure: they own no state and depend on no global configuration.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kayakgen.model.hull import Hull


_DESIGN_FIELDS: tuple[str, ...] = (
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
    "rocker_bow_m",
    "rocker_stern_m",
    "LCB_frac",
)


def _canonical_json(value: Any) -> str:
    """Return canonical JSON: sorted keys, no insignificant whitespace."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def record_hash(payload: dict[str, Any]) -> str:
    """SHA-256 of canonical-form JSON of ``payload``.

    JSON key order has no effect on the hash. Two payloads whose canonical
    JSON encodings are byte-equal hash identically; anything else differs.
    """

    encoded = _canonical_json(payload).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def design_hash_for_hull(hull: "Hull") -> str:
    """SHA-256 over a hull's physical design inputs only.

    Covers ``length_m``, ``beam_oa_m``, ``beam_wl_m``, ``draft_m``,
    ``deck_height_m``, ``Cp``, ``Cm``, ``deck_flatness``,
    ``center_box_ratio``, ``bow_rake``, ``stern_rake``, ``rocker_bow_m``,
    ``rocker_stern_m``, ``LCB_frac``, plus ``geometry_kind`` (defaulted to
    ``"lofted"`` when the hull predates RFC 0048). Invariant under
    renaming the hull or reordering JSON keys.
    """

    payload: dict[str, Any] = {}
    for field in _DESIGN_FIELDS:
        payload[field] = getattr(hull, field)
    payload["geometry_kind"] = getattr(hull, "geometry_kind", None) or "lofted"
    return record_hash(payload)


def run_hash(spec_payload: dict[str, Any], kayakgen_version: str) -> str:
    """SHA-256 over a canonical ``{spec, version}`` blob.

    The two fields jointly identify a run's deterministic inputs: the
    sweep/search/CFD spec payload and the kayakgen package version pin.
    """

    payload = {"spec": spec_payload, "version": kayakgen_version}
    return record_hash(payload)


__all__ = [
    "design_hash_for_hull",
    "record_hash",
    "run_hash",
]
