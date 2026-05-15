"""High-angle GZ CLI surfacing helpers (RFC 0043, stage 1).

This module assembles the opt-in ``high_angle_gz`` JSON block surfaced by
``kayakgen stability --high-angle-gz``. The block is a display-only read model
backed by ``evaluate_gz_curve``; the underlying evaluator return type is
unchanged so default ``kayakgen stability`` output is byte-equal to prior
behavior when the flag is absent.

All output stays ``unvalidated_hydrostatic_comparison`` and carries the RFC
0024 warnings ``deck_immersion_assumption``, ``flooding_not_modeled``,
``not_safety_or_seaworthiness_claim``, ``active_paddler_not_modeled``, and
``sealed_body_assumption``. These are emitted by the CLI surface; the
evaluator-level warning set is preserved and merged in as well so callers see
both the surfacing-stable contract and the evaluator-emitted detail.
"""

from __future__ import annotations

from collections.abc import Sequence
import math
from typing import Any

from kayakgen.eval.closed_volume import (
    ClosedVolumeBody,
    diagnose_closed_volume_body,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.contract import LoadCase
from kayakgen.eval.stability import (
    DEFAULT_GZ_HEEL_GRID_DEG,
    GeneratedBodyGZCurve,
    evaluate_gz_curve,
)
from kayakgen.model.hull import Hull

HIGH_ANGLE_GZ_BODY_PROFILE = "generated_hull_plus_deck_closed_body_v1"
HIGH_ANGLE_GZ_RESULT_SEMANTICS = "unvalidated_hydrostatic_comparison"
HIGH_ANGLE_GZ_SURFACE_WARNINGS: tuple[str, ...] = (
    "deck_immersion_assumption",
    "flooding_not_modeled",
    "not_safety_or_seaworthiness_claim",
    "active_paddler_not_modeled",
    "sealed_body_assumption",
)


def parse_heel_grid_deg(value: str | None) -> list[float]:
    """Parse a comma-separated heel grid override, enforcing strict increase."""

    if value is None:
        return [float(angle) for angle in DEFAULT_GZ_HEEL_GRID_DEG]
    raw = [piece.strip() for piece in value.split(",") if piece.strip()]
    if not raw:
        raise ValueError("--heel-grid-deg must contain at least one angle")
    try:
        grid = [float(piece) for piece in raw]
    except ValueError as exc:
        raise ValueError(f"--heel-grid-deg values must be finite floats: {exc}") from exc
    for angle in grid:
        if not math.isfinite(angle):
            raise ValueError("--heel-grid-deg values must be finite")
        if angle < 0.0 or angle > 90.0:
            raise ValueError("--heel-grid-deg values must be between 0 and 90 degrees")
    for left, right in zip(grid, grid[1:], strict=False):
        if right <= left:
            raise ValueError("--heel-grid-deg must be strictly increasing")
    return grid


def _dedupe(values: Sequence[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value not in out:
            out.append(value)
    return out


def _per_heel_records(curve: GeneratedBodyGZCurve) -> list[dict[str, Any]]:
    by_heel = {entry: idx for idx, entry in enumerate(curve.heel_deg)}
    records: list[dict[str, Any]] = []
    for metadata in curve.heel_point_metadata:
        record: dict[str, Any] = {
            "heel_deg": metadata.heel_deg,
            "status": metadata.status,
            "sinkage_m": metadata.sinkage_m,
            "iterations": metadata.displacement_iterations,
            "max_iterations": metadata.displacement_max_iterations,
            "residual_displacement_kg": metadata.displacement_residual_kg,
            "residual_longitudinal_moment_kg_m": metadata.longitudinal_moment_residual_kg_m,
            "clipping_status": metadata.clipping_status,
            "warnings": list(metadata.warnings),
            "gz_m": None,
        }
        index = by_heel.get(metadata.heel_deg)
        if index is not None and metadata.status == "computed":
            record["gz_m"] = curve.gz_m[index]
        records.append(record)
    return records


def _summary_block(curve: GeneratedBodyGZCurve, heel_grid_deg: Sequence[float]) -> dict[str, Any] | None:
    if curve.status != "computed":
        return None
    if len(curve.heel_deg) != len(heel_grid_deg):
        return None
    return {
        "max_gz": curve.max_gz_m,
        "heel_at_max_gz": curve.heel_at_max_gz_deg,
        "range_positive_stability_deg": curve.range_positive_stability_deg,
    }


def _unavailable_block(
    *,
    heel_grid_deg: Sequence[float],
    reason_code: str,
    reason_detail: str,
    evaluator_warnings: Sequence[str] = (),
    assumptions: Sequence[str] = (),
) -> dict[str, Any]:
    warnings = _dedupe([*evaluator_warnings, *HIGH_ANGLE_GZ_SURFACE_WARNINGS])
    return {
        "available": False,
        "result_semantics": HIGH_ANGLE_GZ_RESULT_SEMANTICS,
        "body_profile": HIGH_ANGLE_GZ_BODY_PROFILE,
        "heel_grid_deg": list(heel_grid_deg),
        "unavailable_reason": {
            "code": reason_code,
            "detail": reason_detail,
        },
        "heel_points": [],
        "summary": None,
        "assumptions": list(assumptions),
        "warnings": warnings,
    }


def build_high_angle_gz_block(
    hull: Hull,
    load_case: LoadCase,
    *,
    heel_grid_deg: Sequence[float],
    body_builder=None,
) -> dict[str, Any]:
    """Assemble the opt-in CLI ``high_angle_gz`` block for ``hull``.

    ``body_builder`` is an injection seam (resolved at call time) so tests can
    simulate the "generated body unavailable" path without crafting degenerate
    hulls. When ``None``, the module-level ``generated_hull_plus_deck_body`` is
    used and may be monkeypatched at module scope.
    """

    builder = body_builder if body_builder is not None else generated_hull_plus_deck_body
    try:
        body = builder(hull)
    except Exception as exc:  # pragma: no cover - defensive
        return _unavailable_block(
            heel_grid_deg=heel_grid_deg,
            reason_code="generated_closed_body_not_available",
            reason_detail=f"body_builder_raised: {exc}",
        )

    if body is None:
        return _unavailable_block(
            heel_grid_deg=heel_grid_deg,
            reason_code="generated_closed_body_not_available",
            reason_detail="body_builder_returned_none",
        )

    if not isinstance(body, ClosedVolumeBody):
        return _unavailable_block(
            heel_grid_deg=heel_grid_deg,
            reason_code="generated_closed_body_not_available",
            reason_detail="body_builder_returned_non_closed_volume_body",
        )

    try:
        diagnostics = diagnose_closed_volume_body(body)
    except Exception as exc:  # pragma: no cover - defensive
        return _unavailable_block(
            heel_grid_deg=heel_grid_deg,
            reason_code="generated_closed_body_not_available",
            reason_detail=f"closed_volume_diagnostic_raised: {exc}",
        )

    curve = evaluate_gz_curve(
        hull,
        load_case,
        heel_grid_deg=list(heel_grid_deg),
        body_ref=body,
        body_diagnostics=diagnostics,
    )

    if not isinstance(curve, GeneratedBodyGZCurve) or curve.status != "computed":
        evaluator_warnings = list(getattr(curve, "warnings", ()) or ())
        reason_code = "generated_closed_body_not_available"
        if curve.body_type == "explicit_synthetic_triangle_mesh":
            reason_code = "synthetic_body_not_allowed_for_real_gz"
        elif "heel_point_non_converged" in evaluator_warnings:
            reason_code = "heel_point_non_converged"
        return _unavailable_block(
            heel_grid_deg=heel_grid_deg,
            reason_code=reason_code,
            reason_detail="evaluate_gz_curve returned status != computed",
            evaluator_warnings=evaluator_warnings,
            assumptions=list(curve.assumptions),
        )

    surface_warnings = _dedupe([*curve.warnings, *HIGH_ANGLE_GZ_SURFACE_WARNINGS])
    return {
        "available": True,
        "result_semantics": HIGH_ANGLE_GZ_RESULT_SEMANTICS,
        "body_profile": HIGH_ANGLE_GZ_BODY_PROFILE,
        "method": curve.method,
        "body_ref": curve.body_ref,
        "body_type": curve.body_type,
        "body_diagnostic_ref": curve.body_diagnostic_ref,
        "heel_grid_deg": list(curve.heel_grid_deg),
        "heel_points": _per_heel_records(curve),
        "summary": _summary_block(curve, heel_grid_deg),
        "assumptions": list(curve.assumptions),
        "warnings": surface_warnings,
    }
