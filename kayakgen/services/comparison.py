"""Comparison report loading and candidate-apply orchestration.

These helpers turn a ``ComparisonReport`` JSON string into the display
view-model consumed by the Trame comparison panel, and apply one
candidate's sweep parameters back into the flat web-state dict.
"""

from __future__ import annotations

from typing import Any

from kayakgen.search.compare import ComparisonReport
from kayakgen.services.design import clamp_beam_wl_state

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


def comparison_view_model_from_json(payload: str) -> dict[str, Any]:
    """Parse a ``ComparisonReport`` JSON string into display rows."""
    if not payload.strip():
        return {
            "status": "Paste a comparison report JSON to inspect candidates.",
            "lines": [],
            "candidate_options": [],
        }
    try:
        report = ComparisonReport.model_validate_json(payload)
    except Exception as exc:
        return {
            "status": f"Invalid comparison report: {exc}",
            "lines": [],
            "candidate_options": [],
        }

    pareto = set(report.pareto_front_keys)
    lines = [
        f"Report: {report.run_name}",
        f"Kind: {report.report_kind}",
        f"Spec hash: {report.spec_hash[:12]}",
        "",
        "Objectives",
    ]
    if report.objectives:
        lines.extend(
            f"  {objective.metric} ({objective.direction})"
            for objective in report.objectives
        )
    else:
        lines.append("  none")
    if report.warnings:
        lines.extend(["", "Report warnings", *[f"  {warning}" for warning in report.warnings]])

    lines.extend(["", "Candidates", "  idx  status    pareto  key       warnings"])
    for summary in report.candidate_summaries:
        marker = "yes" if summary.candidate_key in pareto else "no"
        warning_text = "; ".join(summary.warnings) if summary.warnings else "-"
        if summary.error:
            warning_text = f"{warning_text}; error: {summary.error}"
        lines.append(
            f"  {summary.candidate_index:>3}  {summary.status:<8}  "
            f"{marker:<6}  {summary.candidate_key[:8]}  {warning_text}"
        )
    return {
        "status": (
            f"{len(report.candidate_summaries)} candidates, "
            f"{len(report.pareto_front_keys)} pareto"
        ),
        "lines": lines,
        "candidate_options": [
            summary.candidate_index for summary in report.candidate_summaries
        ],
    }


def candidate_state_from_report_json(
    payload: str,
    candidate_index: int | str,
    current_state: dict[str, Any],
) -> dict[str, Any]:
    """Apply one report candidate's sweep parameters to current web state."""
    report = ComparisonReport.model_validate_json(payload)
    index = int(candidate_index)
    for summary in report.candidate_summaries:
        if summary.candidate_index != index:
            continue
        updated = dict(current_state)
        for key, value in summary.parameters.items():
            if key in _HULL_STATE_FIELDS:
                updated[key] = value
        return clamp_beam_wl_state(updated)
    raise ValueError(f"unknown candidate index: {candidate_index}")
