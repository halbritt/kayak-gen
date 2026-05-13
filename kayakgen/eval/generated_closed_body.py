"""Compatibility entry point for generated hull-plus-deck closed bodies."""

from __future__ import annotations

from kayakgen.eval.closed_volume import (
    ClosedVolumeBody,
    generated_hull_plus_deck_closed_body as _canonical_generated_closed_body,
)
from kayakgen.model.hull import Hull

DEFAULT_GENERATED_CLOSED_BODY_STATIONS = 32


def generated_hull_plus_deck_closed_body(
    hull: Hull,
    *,
    stations: int | None = None,
    body_id: str | None = None,
) -> ClosedVolumeBody:
    """Build the canonical generated closed body through the legacy import path."""

    return _canonical_generated_closed_body(
        hull,
        body_id=body_id,
        stations=(
            DEFAULT_GENERATED_CLOSED_BODY_STATIONS
            if stations is None
            else stations
        ),
    )
