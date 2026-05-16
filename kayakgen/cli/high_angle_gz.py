"""Backwards-compatibility shim for the high-angle GZ read-model builder.

The real implementation moved to ``kayakgen.eval.high_angle_gz`` as part of
Phase 2 of ``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md``. Importers can
continue to use ``kayakgen.cli.high_angle_gz``; new callers should target
``kayakgen.eval.high_angle_gz`` directly.

This module exposes the original public names verbatim and re-exports
``generated_hull_plus_deck_body`` so the existing
``kayakgen.cli.high_angle_gz.generated_hull_plus_deck_body`` monkeypatch
point in tests keeps working.
"""

from __future__ import annotations

from kayakgen.eval.closed_volume import generated_hull_plus_deck_body
from kayakgen.eval.high_angle_gz import (
    HIGH_ANGLE_GZ_BODY_PROFILE,
    HIGH_ANGLE_GZ_RESULT_SEMANTICS,
    HIGH_ANGLE_GZ_SURFACE_WARNINGS,
    build_high_angle_gz_block,
    parse_heel_grid_deg,
)

__all__ = [
    "HIGH_ANGLE_GZ_BODY_PROFILE",
    "HIGH_ANGLE_GZ_RESULT_SEMANTICS",
    "HIGH_ANGLE_GZ_SURFACE_WARNINGS",
    "build_high_angle_gz_block",
    "generated_hull_plus_deck_body",
    "parse_heel_grid_deg",
]
