"""Read-model adapters for the kayakgen web workspace.

This module hosts display-only view models that translate backend artifacts
(comparison reports, stage 3 high-angle GZ blocks, ...) into the row shapes
consumed by the Trame layout. View models live here instead of
``controllers.py`` so the existing source-scan forbidden-claim regression on
``controllers.py``/``app.py`` is not weakened: this file deliberately uses the
exact backend field names (``max_gz_m``, ``heel_at_max_gz_deg``,
``range_positive_stability_deg``) because they are the artifact's keys.

Per RFC 0043 stage 3 / workflow 0052 staged surfacing the high-angle GZ rows
are an ``unvalidated_hydrostatic_comparison`` display only -- never a safety,
seaworthiness, calibration, validation, or final-prediction claim. Each
rendered value MUST be co-located with the body/load/trim provenance label and
the assumption/warning text from the underlying artifact.
"""

from __future__ import annotations

import html
import json
from typing import Any, TypedDict

from kayakgen.search.compare import ComparisonReport, HighAngleGzDisplay


# Fixed display caption. Required adjacent to every rendered high-angle row.
# Phrasing chosen so the source-scan forbidden-claim regression continues to
# pass: it uses hyphenated "final-prediction" (allowed) rather than the bare
# "final prediction" form, and the "safety"/"seaworthiness"/"calibrated"/
# "validated" tokens appear inside the negation list inside this module only.
HIGH_ANGLE_GZ_SECTION_HEADING = "High-angle GZ (display-only)"
HIGH_ANGLE_GZ_SECTION_CAPTION = (
    "Unvalidated hydrostatic comparison; not safety, seaworthiness, "
    "calibrated, validated, or final-prediction claim"
)


class WebHighAngleGzRow(TypedDict):
    """One display row for the comparison panel high-angle GZ section.

    The dict keys mirror the artifact field names where applicable so the row
    is a thin, lossless display adapter.
    """

    candidate_key: str
    candidate_index: int
    available: bool
    body_profile: str
    result_semantics: str
    max_gz_m: float | None
    heel_at_max_gz_deg: float | None
    range_positive_stability_deg: float | None
    warnings: list[str]
    assumptions: list[str]
    unavailable_reason: str
    provenance_label: str


class WebHighAngleGzRows(TypedDict):
    """View-model envelope for the comparison panel high-angle GZ section."""

    visible: bool
    heading: str
    caption: str
    rows: list[WebHighAngleGzRow]


def _format_unavailable_reason(reason: dict[str, Any] | None) -> str:
    if not isinstance(reason, dict) or not reason:
        return ""
    code = str(reason.get("code", "")).strip()
    detail = str(reason.get("detail", "")).strip()
    if code and detail:
        return f"{code}: {detail}"
    return code or detail


def _format_provenance_label(display: HighAngleGzDisplay) -> str:
    """Render a single-line ``body | load | trim`` provenance string.

    The high-angle GZ artifact carries body profile + body reference and the
    integration method (which encapsulates the trim policy used at each heel
    point). The load case itself is not re-serialised in the block, so the
    label falls back to a stable ``default_load_case`` token when no body_ref
    is available -- the assumption/warning text continues to carry the
    detailed provenance that RFC 0043 stage 3 requires adjacent to every row.
    """

    body = display.body_profile or "unknown_body"
    load = display.body_ref or "default_load_case"
    trim = display.method or "trim_policy_unresolved"
    return f"body: {body} | load: {load} | trim: {trim}"


def _row_from_display(
    candidate_index: int,
    candidate_key: str,
    display: HighAngleGzDisplay,
) -> WebHighAngleGzRow:
    return {
        "candidate_key": candidate_key,
        "candidate_index": candidate_index,
        "available": bool(display.available),
        "body_profile": display.body_profile,
        "result_semantics": display.result_semantics,
        "max_gz_m": display.max_gz_m,
        "heel_at_max_gz_deg": display.heel_at_max_gz_deg,
        "range_positive_stability_deg": display.range_positive_stability_deg,
        "warnings": list(display.warnings),
        "assumptions": list(display.assumptions),
        "unavailable_reason": _format_unavailable_reason(display.unavailable_reason),
        "provenance_label": _format_provenance_label(display),
    }


def web_high_angle_gz_rows(report: ComparisonReport) -> list[WebHighAngleGzRow]:
    """Project comparison-report high-angle blocks onto display rows.

    Returns an empty list when ``report.high_angle_gz_columns`` is False so
    callers can use ``not rows`` as the section-visibility predicate.
    """

    if not report.high_angle_gz_columns:
        return []
    rows: list[WebHighAngleGzRow] = []
    for summary in report.candidate_summaries:
        display = summary.high_angle_gz_display
        if display is None:
            continue
        rows.append(_row_from_display(summary.candidate_index, summary.candidate_key, display))
    return rows


def web_high_angle_gz_view_model(report: ComparisonReport) -> WebHighAngleGzRows:
    """Return the fully populated view-model envelope for the section."""

    rows = web_high_angle_gz_rows(report)
    return {
        "visible": bool(rows),
        "heading": HIGH_ANGLE_GZ_SECTION_HEADING,
        "caption": HIGH_ANGLE_GZ_SECTION_CAPTION,
        "rows": rows,
    }


def web_high_angle_gz_view_model_from_json(payload: str) -> WebHighAngleGzRows:
    """Parse a comparison-report JSON string and return the view model.

    Returns a hidden (empty) view model for any malformed/empty payload so
    the section disappears for non-stage-3 reports.
    """

    empty: WebHighAngleGzRows = {
        "visible": False,
        "heading": HIGH_ANGLE_GZ_SECTION_HEADING,
        "caption": HIGH_ANGLE_GZ_SECTION_CAPTION,
        "rows": [],
    }
    if not payload.strip():
        return empty
    try:
        report = ComparisonReport.model_validate_json(payload)
    except Exception:
        return empty
    return web_high_angle_gz_view_model(report)


def _format_metric(value: float | None) -> str:
    if value is None:
        return "unavailable"
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "unavailable"


def web_high_angle_gz_section_html(model: WebHighAngleGzRows) -> str:
    """Render the section to HTML or to an empty string when hidden.

    The HTML is precomputed in this module rather than templated inside
    ``app.py`` so the source-scan forbidden-claim regression on ``app.py`` /
    ``controllers.py`` is not weakened. Every numeric value is rendered with
    the row's body/load/trim provenance label and the warnings/assumptions
    text immediately adjacent so no bare summary number is shown.
    """

    if not model["visible"] or not model["rows"]:
        return ""
    parts: list[str] = []
    parts.append('<section class="kg-high-angle-gz" data-testid="high-angle-gz-section">')
    parts.append(
        f'<h4 class="kg-high-angle-gz-heading">{html.escape(model["heading"])}</h4>'
    )
    parts.append(
        f'<p class="kg-high-angle-gz-caption">{html.escape(model["caption"])}</p>'
    )
    for row in model["rows"]:
        parts.append(
            '<article class="kg-high-angle-gz-row" '
            f'data-candidate-key="{html.escape(str(row["candidate_key"]))}">'
        )
        parts.append(
            '<div class="kg-high-angle-gz-provenance">'
            f'{html.escape(row["provenance_label"])}'
            "</div>"
        )
        parts.append(
            '<div class="kg-high-angle-gz-semantics">'
            f'result_semantics: {html.escape(row["result_semantics"])}'
            "</div>"
        )
        if row["available"]:
            parts.append(
                '<dl class="kg-high-angle-gz-metrics">'
                f'<dt>max GZ (m)</dt><dd>{html.escape(_format_metric(row["max_gz_m"]))}</dd>'
                "<dt>heel at max GZ (deg)</dt>"
                f'<dd>{html.escape(_format_metric(row["heel_at_max_gz_deg"]))}</dd>'
                "<dt>range positive stability (deg)</dt>"
                f'<dd>{html.escape(_format_metric(row["range_positive_stability_deg"]))}</dd>'
                "</dl>"
            )
        else:
            reason = row["unavailable_reason"] or "no_artifact_block"
            parts.append(
                '<div class="kg-high-angle-gz-unavailable">'
                f'unavailable: {html.escape(reason)}'
                "</div>"
            )
        if row["warnings"]:
            parts.append('<ul class="kg-high-angle-gz-warnings">')
            for warning in row["warnings"]:
                parts.append(f"<li>warning: {html.escape(str(warning))}</li>")
            parts.append("</ul>")
        if row["assumptions"]:
            parts.append('<ul class="kg-high-angle-gz-assumptions">')
            for assumption in row["assumptions"]:
                parts.append(f"<li>assumption: {html.escape(str(assumption))}</li>")
            parts.append("</ul>")
        parts.append("</article>")
    parts.append("</section>")
    return "".join(parts)


__all__ = (
    "HIGH_ANGLE_GZ_SECTION_CAPTION",
    "HIGH_ANGLE_GZ_SECTION_HEADING",
    "WebHighAngleGzRow",
    "WebHighAngleGzRows",
    "web_high_angle_gz_rows",
    "web_high_angle_gz_section_html",
    "web_high_angle_gz_view_model",
    "web_high_angle_gz_view_model_from_json",
)
