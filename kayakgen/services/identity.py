"""Identity hashing functions for kayakgen artifacts (RFC 0049).

This module owns the four explicit hash concepts defined by RFC 0049:

- :func:`record_hash` — SHA-256 over a canonical-form JSON payload. The
  invariant is "differs iff the canonical bytes differ"; canonicalisation
  is sorted keys + no insignificant whitespace.
- :func:`design_hash_for_hull` — SHA-256 over *only* the physical inputs
  that affect a hull's geometry/evaluation. Renaming a hull, changing
  ``class_preset`` (if it ever lands), or reordering JSON keys does not
  change this hash. The geometry strategy determines its physical inputs.
- :func:`run_hash` — SHA-256 over a canonical ``{spec, version}`` blob.

Record, run and legacy lofted hashes are 64-character lowercase SHA-256 hex.
V2 physical identities include a scheme prefix, ``distribution_v2_v2:``, so
legacy scalar-only identities cannot be mistaken for complete v2 identities.
The functions own no state and depend on no global configuration.
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


def legacy_design_hash_for_hull(hull: "Hull") -> str:
    """Return the pre-RFC-0068 scalar-only design hash for historical lookup.

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


def design_hash_for_hull(hull: "Hull") -> str:
    """Identify physical design inputs in the geometry's declared scheme.

    Lofted identities remain byte-stable. V2 uses length and the complete
    nested distribution spec; its legacy scalar reporting fields do not
    drive that geometry. The scheme is part of the digest and its prefix.
    """
    if hull.geometry_kind == "lofted":
        return legacy_design_hash_for_hull(hull)
    scheme = "distribution_v2_v2"
    payload = {
        "scheme": scheme,
        "length_m": hull.length_m,
        "distribution_v2": hull.distribution_v2.model_dump(mode="json"),
    }
    return scheme + ":" + record_hash(payload)


def run_hash(spec_payload: dict[str, Any], kayakgen_version: str) -> str:
    """SHA-256 over a canonical ``{spec, version}`` blob.

    The two fields jointly identify a run's deterministic inputs: the
    sweep/search/CFD spec payload and the kayakgen package version pin.
    """

    payload = {"spec": spec_payload, "version": kayakgen_version}
    return record_hash(payload)


__all__ = [
    "design_hash_for_hull",
    "legacy_design_hash_for_hull",
    "record_hash",
    "run_hash",
]
