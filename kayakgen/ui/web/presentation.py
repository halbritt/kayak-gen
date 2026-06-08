"""Presentation constants, CSS, copy, and pure helpers for the kayakgen web UI.

Extracted verbatim from ``kayakgen.ui.web.app`` (refactoring campaign
kayakgen-smoke-1, slice S1). ``app.py`` re-exports every name defined here,
so ``kayakgen.ui.web.app.<name>`` import paths keep working.
"""

from __future__ import annotations

import html
from typing import Any

from kayakgen.ui import theme
from kayakgen.ui.web.controllers import (
    CFD_LOCAL_FILESYSTEM_NOTICE,
    class_preset_options,
)


# (state_key, label, min, max, step). target_speed_kt is a viewing param,
# not a Hull field; controllers ignore unrecognized state keys.
SLIDER_DEFS: list[tuple[str, str, float, float, float]] = [
    ("length_m", "Length (m)", 2.0, 6.5, 0.05),
    ("beam_oa_m", "Beam OA (m)", 0.30, 0.90, 0.005),
    ("beam_wl_m", "Beam WL (m)", 0.30, 0.90, 0.005),
    ("draft_m", "Draft (m)", 0.05, 0.25, 0.005),
    ("deck_height_m", "Deck Height (m)", 0.15, 0.40, 0.005),
    ("Cp", "Prismatic Cp", 0.45, 0.70, 0.005),
    ("Cm", "Midship Cm", 0.65, 0.95, 0.005),
    ("deck_flatness", "Deck Flatness", 2.0, 16.0, 0.5),
    ("center_box_ratio", "Parallel Mid-Body", 0.10, 0.60, 0.01),
    ("bow_rake", "Bow Rake (1=raked)", 0.0, 1.0, 0.05),
    ("stern_rake", "Stern Rake (1=raked)", 0.0, 1.0, 0.05),
    ("target_speed_kt", "Target Speed (kt)", 1.0, 6.0, 0.1),
]

PARAMETER_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Principal dimensions",
        ("length_m", "beam_oa_m", "beam_wl_m", "draft_m", "deck_height_m"),
    ),
    (
        "Shape coefficients",
        ("Cp", "Cm", "deck_flatness", "center_box_ratio"),
    ),
    ("Ends and view", ("bow_rake", "stern_rake", "target_speed_kt")),
)

CLASS_PRESETS: tuple[str, ...] = (
    "touring",
    "performance",
    "surfski_int",
    "surfski_elite",
    "custom",
)
CLASS_PRESET_OPTIONS: tuple[dict[str, str], ...] = tuple(class_preset_options())

EXPORT_MENU_ROWS: tuple[dict[str, Any], ...] = (
    {
        "key": "hull_stl",
        "label": "Hull STL",
        "status": "enabled",
        "available": True,
        "disabled": False,
        "row_class": "kg-export-row kg-export-hull-stl",
        "action_key": "export_hull_stl",
        "subtitle": "Current open hull inspection surface",
    },
    {
        "key": "deck_stl",
        "label": "Deck STL",
        "status": "enabled",
        "available": True,
        "disabled": False,
        "row_class": "kg-export-row kg-export-deck-stl",
        "action_key": "export_deck_stl",
        "subtitle": "Current open deck inspection surface",
    },
    {
        "key": "hydro_json",
        "label": "Hydro JSON",
        "status": "enabled",
        "available": True,
        "disabled": False,
        "row_class": "kg-export-row kg-export-hydro-json",
        "action_key": "export_hydro_json",
        "subtitle": "Current local evaluation data",
    },
    {
        "key": "stability_json",
        "label": "Stability JSON",
        "status": "unavailable",
        "available": False,
        "disabled": True,
        "row_class": "kg-export-row kg-export-stability-json",
        "action_key": "",
        "subtitle": "Use kayakgen stability for current initial-stability JSON.",
    },
    {
        "key": "mesh_package",
        "label": "Mesh package (CLI only)",
        "status": "unavailable",
        "available": False,
        "disabled": True,
        "row_class": "kg-export-row kg-export-mesh-package",
        "action_key": "",
        "subtitle": (
            "Mesh package authoring is not enabled in the browser; "
            "use kayakgen mesh-package."
        ),
    },
)

REVIEW_TABS: tuple[dict[str, str], ...] = (
    {"label": "Hydro", "value": "analysis", "test_id": "tab-hydro"},
    {"label": "Mesh", "value": "mesh", "test_id": "tab-mesh"},
    {"label": "Comparison", "value": "comparison", "test_id": "tab-comparison"},
    {"label": "CFD", "value": "cfd", "test_id": "tab-cfd"},
    {"label": "Generate", "value": "generate", "test_id": "tab-generate"},
    {"label": "Advisories", "value": "advisories", "test_id": "tab-advisories"},
)

STATUS_SEGMENTS: tuple[dict[str, str], ...] = (
    {
        "key": "package",
        "state_key": "status_package",
        "target_tab": "mesh",
        "aria_label": "package profile status",
    },
    {
        "key": "readiness",
        "state_key": "status_readiness",
        "target_tab": "mesh",
        "aria_label": "mesh readiness level",
    },
    {
        "key": "resistance",
        "state_key": "status_resistance",
        "target_tab": "analysis",
        "aria_label": "resistance claim state",
    },
    {
        "key": "cfd",
        "state_key": "status_cfd",
        "target_tab": "cfd",
        "aria_label": "local CFD job status",
    },
)

LAYOUT_TEST_IDS: dict[str, str] = {
    "params": "region-params",
    "geometry": "region-geometry",
    "review": "region-review",
}

REGION_CLASSES: dict[str, str] = {
    "params": "kg-region kg-region-params kg-parameter-rail kg-collapse-under-960",
    "geometry": (
        "kg-region kg-region-geometry kg-geometry-pane "
        "kg-geometry-accordion-under-960"
    ),
    "review": "kg-region kg-region-review kg-review-pane kg-review-body-under-960",
}

RESPONSIVE_CLASS_HOOKS: tuple[str, ...] = (
    "kg-workspace-shell",
    "kg-workspace-grid",
    "kg-collapse-under-960",
    "kg-geometry-accordion-under-960",
    "kg-review-body-under-960",
    "kg-export-menu-under-1200",
    "kg-metrics-strip-scroll",
    "kg-status-wrap-under-960",
)

ROOT_THEME_CSS = theme.css_root_block()

WORKSPACE_SHELL_CSS = """
.kg-workspace-shell {
  background: var(--surface-bg);
  color: var(--text-primary);
  font: var(--type-body);
}
.kg-workspace-main {
  gap: var(--space-0);
}
.kg-region {
  background: var(--surface-panel);
  border: var(--border-width-thin) var(--border-style-solid) var(--surface-border);
  border-radius: var(--radius-md);
  box-shadow: var(--elevation-panel);
  padding: var(--space-4);
}
.kg-region-params {
  background: var(--surface-rail);
}
.kg-region-review {
  background: var(--surface-review);
}
.kg-region-title,
.kg-review-card .v-card-title,
.kg-generate-card .v-card-title {
  color: var(--text-primary);
  font: var(--type-heading);
  padding: var(--space-0) var(--space-0) var(--space-3);
}
.kg-toolbar-breadcrumb {
  color: var(--text-primary);
  font: var(--type-display);
}
.kg-toolbar-action,
.kg-class-preset-select,
.kg-export-menu-list .v-list-item-title,
.kg-review-tabs .v-tab,
.kg-status-segment {
  font: var(--type-label);
}
.kg-class-preset-chip,
.kg-validity-badge,
.kg-claim-chip,
.kg-readiness-chip,
.kg-chip {
  border-radius: var(--radius-sm);
  font: var(--type-caption);
}
.kg-rail-group-label,
.kg-generate-section-label,
.kg-frontier-heading {
  color: var(--text-secondary);
  font: var(--type-label);
  padding: var(--space-3) var(--space-0) var(--space-2);
}
.kg-param-slider {
  padding-block: var(--space-1);
}
.kg-param-slider .v-slider__label {
  color: var(--text-secondary);
  font: var(--type-label);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.kg-param-slider-control .v-slider-track__fill,
.kg-param-slider-control .v-slider-thumb__surface {
  background: var(--state-focus-rail);
}
.kg-vtk-frame {
  background: var(--surface-viewport-bg);
  border: var(--border-width-thin) var(--border-style-solid) var(--surface-border);
  border-radius: var(--radius-md);
  box-shadow: var(--elevation-panel);
  overflow: hidden;
}
.kg-vtk-viewport {
  background: var(--surface-viewport-bg);
}
.kg-metrics-strip {
  background: var(--surface-muted);
  border: var(--border-width-thin) var(--border-style-solid) var(--surface-border);
  border-radius: var(--radius-md);
  box-shadow: var(--elevation-none);
  margin-block-start: var(--space-3);
}
.kg-metrics-strip .v-card-title {
  font: var(--type-label);
  padding: var(--space-3) var(--space-3) var(--space-1);
}
.kg-metrics-strip pre,
.kg-review-card pre,
.kg-resistance-table,
.kg-hydro-table,
.kg-mesh-diag-table {
  font: var(--type-metric);
}
.kg-review-tabs {
  border-block-end: var(--border-width-thin) var(--border-style-solid) var(--surface-border);
  margin-block-end: var(--space-3);
}
.kg-review-card,
.kg-frontier-section {
  background: var(--surface-panel);
  border: var(--border-width-thin) var(--border-style-solid) var(--surface-border);
  border-radius: var(--radius-md);
  box-shadow: var(--elevation-panel);
  margin-block-end: var(--space-3);
}
.kg-review-card .v-card-text,
.kg-frontier-section .v-card-text {
  color: var(--text-secondary);
  font: var(--type-body);
  padding: var(--space-2) var(--space-3);
}
.kg-hydro-table,
.kg-mesh-diag-table,
.kg-resistance-table {
  border-collapse: collapse;
  width: var(--frontier-max-width);
  max-width: var(--frontier-max-width);
}
.kg-hydro-table th,
.kg-mesh-diag-table th,
.kg-resistance-table th {
  color: var(--text-secondary);
  font: var(--type-label);
  padding: var(--table-row-padding-y) var(--table-row-padding-x);
  text-align: left;
}
.kg-hydro-table td,
.kg-mesh-diag-table td,
.kg-resistance-table td {
  color: var(--text-primary);
  font: var(--type-metric);
  padding: var(--table-row-padding-y) var(--table-row-padding-x);
}
.kg-resistance-row-target {
  background: var(--state-focus-row);
}
.kg-cfd-banner,
.kg-generate-banner,
.kg-generate-status,
.kg-frontier-empty,
.kg-pinned-empty,
.kg-generate-section-help {
  color: var(--text-secondary);
  font: var(--type-caption);
}
.kg-generate-card .v-field,
.kg-cfd-card .v-field,
.kg-comparison-card .v-field,
.kg-mesh-readiness-card .v-field {
  border-radius: var(--radius-sm);
}
.kg-workspace-shell .v-btn,
.kg-workspace-shell .v-tab,
.kg-workspace-shell .v-field,
.kg-workspace-shell .v-slider,
.kg-workspace-shell .v-selection-control,
.kg-workspace-shell select,
.kg-workspace-shell input,
.kg-workspace-shell textarea,
.kg-workspace-shell button {
  border-radius: var(--radius-sm);
}
.kg-workspace-shell .v-btn:hover,
.kg-workspace-shell .v-tab:hover,
.kg-workspace-shell select:hover,
.kg-workspace-shell input:hover,
.kg-workspace-shell textarea:hover,
.kg-variable-remove-btn:hover {
  background: var(--state-hover-surface);
  color: var(--state-hover-text);
}
.kg-workspace-shell .v-btn:active,
.kg-workspace-shell .v-tab:active,
.kg-workspace-shell button:active {
  background: var(--state-active-surface);
  color: var(--state-active-text);
}
.kg-workspace-shell .v-btn:focus-visible,
.kg-workspace-shell .v-tab:focus-visible,
.kg-workspace-shell .v-field:focus-within,
.kg-workspace-shell .v-slider:focus-within,
.kg-workspace-shell .v-selection-control:focus-within,
.kg-workspace-shell select:focus-visible,
.kg-workspace-shell input:focus-visible,
.kg-workspace-shell textarea:focus-visible,
.kg-workspace-shell button:focus-visible,
.kg-toolbar-action:focus-visible,
.kg-export-menu-under-1200:focus-visible,
.kg-class-preset-select:focus-within {
  outline: var(--state-focus-ring-width) var(--border-style-solid) var(--state-focus-ring);
  outline-offset: var(--space-1);
}
.kg-workspace-shell .v-btn--disabled,
.kg-workspace-shell .v-tab--disabled,
.kg-workspace-shell .v-field--disabled,
.kg-workspace-shell [aria-disabled="true"],
.kg-workspace-shell select:disabled,
.kg-workspace-shell input:disabled,
.kg-workspace-shell textarea:disabled,
.kg-workspace-shell button:disabled {
  background: var(--state-disabled-surface);
  color: var(--state-disabled-text);
  cursor: not-allowed;
}
.kg-workspace-shell .v-btn--active,
.kg-workspace-shell .v-tab--selected,
.kg-workspace-shell .v-btn-toggle .v-btn--active {
  background: var(--state-active-surface);
  color: var(--state-active-text);
}
.kg-generate-variables-table-wrap,
.kg-generate-objectives-list-wrap,
.kg-resistance-table-wrap,
.kg-readiness-chip-wrap {
  padding-block: var(--space-2);
}
.kg-generate-build,
.kg-generate-watch,
.kg-generate-pick {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.kg-generate-variable-table {
  border: var(--border-width-thin) var(--border-style-solid) var(--surface-border);
  border-radius: var(--radius-sm);
  border-collapse: separate;
  border-spacing: var(--space-0);
  overflow: hidden;
  width: var(--frontier-max-width);
  max-width: var(--frontier-max-width);
}
.kg-generate-variable-table th,
.kg-generate-variable-table td {
  font: var(--type-caption);
  padding: var(--table-row-padding-y) var(--table-row-padding-x);
}
.kg-generate-variable-table select,
.kg-generate-variable-table input {
  background: var(--surface-panel);
  border: var(--border-width-thin) var(--border-style-solid) var(--surface-border);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font: var(--type-body);
  min-height: var(--control-height-compact);
}
.kg-variable-remove-btn {
  background: var(--state-hover-surface);
  border: var(--border-width-thin) var(--border-style-solid) var(--surface-border);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font: var(--type-label);
  min-height: var(--control-height-compact);
}
.kg-status-bar {
  align-items: center;
  background: var(--surface-panel);
  border-block-start: var(--border-width-thin) var(--border-style-solid) var(--surface-border);
  display: flex;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
}
.kg-status-segment {
  color: var(--text-secondary);
  min-height: var(--control-height-compact);
}
.kg-state-panel {
  background: var(--surface-muted);
  border: var(--border-width-thin) var(--border-style-solid) var(--surface-border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font: var(--type-caption);
  margin-block: var(--space-2);
  padding: var(--space-2) var(--space-3);
}
.kg-state-panel--running {
  background: var(--state-info-bg);
  color: var(--state-info);
}
.kg-state-panel--failed,
.kg-state-panel--cancelled {
  background: var(--state-error-bg);
  color: var(--state-error-text);
}
.kg-state-panel--resumable {
  background: var(--state-advisory-bg);
  color: var(--state-advisory-text);
}
.kg-state-panel--rendered {
  background: var(--state-focus-row);
  color: var(--text-primary);
}
@media (max-width: %s) {
  .kg-collapse-under-960,
  .kg-geometry-accordion-under-960,
  .kg-review-body-under-960 {
    border-radius: var(--radius-sm);
    margin-block-end: var(--space-3);
  }
  .kg-status-wrap-under-960 {
    align-items: stretch;
    flex-wrap: wrap;
  }
}
""" % theme.DENSITY["collapse-breakpoint"]

PARAMETER_RAIL_CSS = WORKSPACE_SHELL_CSS

RAW_COMPARATIVE_CAPTION = "Raw comparative filter; not final prediction."
RESISTANCE_DETAIL_COPY = (
    "Uncalibrated; no accepted final-prediction validity envelope. "
    "Compare nearby candidates, do not report as drag."
)
HIGH_ANGLE_GZ_HEADING = "High-angle GZ unavailable"
HIGH_ANGLE_GZ_COPY = (
    "High-angle GZ (stability at large heel angles) is not rendered in the "
    "workspace. Use `kayakgen stability --high-angle-gz` or load a design "
    "report on the Comparison tab to inspect this data."
)
MESH_PACKAGE_READINESS_HEADING = "Mesh package readiness"
MESH_PROFILE_LABEL = "open-wetted-surface"
MESH_PROFILE_ID = "open_wetted_surface_resistance_v1"
MESH_READINESS_LEVEL = "cfd_surface_candidate"
MESH_PACKAGE_READINESS_COPY = "Open wetted-surface profile; not watertight cfd_ready."
WATERTIGHT_DISABLED_COPY = (
    "Current generated packages do not satisfy watertight-solid readiness."
)
CFD_ARTIFACT_STRAPLINE = "Raw solver artifact only; not calibrated or validated."
SHARE_TOAST_COPY = "Shareable URL copied"
GENERATIVE_JOBS_EMPTY_COPY = "(no generative jobs yet)"
GENERATIVE_JOBS_RUNNING_COPY = "Generative job is running."
GENERATIVE_JOBS_FAILED_COPY = "Generative job failed."
GENERATIVE_JOBS_CANCELLED_COPY = "Generative job cancelled."
GENERATIVE_JOBS_RESUMABLE_COPY = "Generative job can be resumed."
FRONTIER_LOADING_COPY = "Loading Pareto frontier."
FRONTIER_RENDERED_COPY = "Pareto frontier rendered."
INVALID_HULL_STATE_COPY = "Invalid hull state"

PERSISTENT_COPY: dict[str, str] = {
    "raw_comparative_filter": RAW_COMPARATIVE_CAPTION,
    "resistance_detail": RESISTANCE_DETAIL_COPY,
    "high_angle_gz_heading": HIGH_ANGLE_GZ_HEADING,
    "mesh_package_readiness_heading": MESH_PACKAGE_READINESS_HEADING,
    "mesh_package_readiness": MESH_PACKAGE_READINESS_COPY,
    "cfd_local_banner": CFD_LOCAL_FILESYSTEM_NOTICE,
    "cfd_artifact_strapline": CFD_ARTIFACT_STRAPLINE,
    "share_toast": SHARE_TOAST_COPY,
    "generative_jobs_empty": GENERATIVE_JOBS_EMPTY_COPY,
    "generative_jobs_running": GENERATIVE_JOBS_RUNNING_COPY,
    "generative_jobs_failed": GENERATIVE_JOBS_FAILED_COPY,
    "generative_jobs_cancelled": GENERATIVE_JOBS_CANCELLED_COPY,
    "generative_jobs_resumable": GENERATIVE_JOBS_RESUMABLE_COPY,
    "frontier_loading": FRONTIER_LOADING_COPY,
    "frontier_rendered": FRONTIER_RENDERED_COPY,
    "invalid_hull_state": INVALID_HULL_STATE_COPY,
}

_SLIDER_BY_KEY = {key: (label, vmin, vmax, step) for key, label, vmin, vmax, step in SLIDER_DEFS}


#: AUD-O-001 — plain-text tooltip copy for each validity-badge state. The
#: badge string is produced by ``validity_badge_from_state`` and takes one of
#: four shapes:
#:
#:   * ``"In <class> envelope"`` — hull fits a standard class envelope.
#:   * ``"Custom — sub-touring"`` — hull below the touring class envelope.
#:   * ``"Custom — beyond elite"`` — hull beyond the elite-surfski class
#:     envelope.
#:   * ``"Custom (L/B_wl=X.X)"`` — hull L/B ratio not matched by any class.
#:
#: The tooltip is computed at the same time as the aria-label so the chip's
#: ``title=`` attribute always reflects the live badge.
VALIDITY_BADGE_TITLE_SUB_TOURING = (
    "Hull is below the touring class envelope. The class selector falls back "
    "to custom; advisory only."
)
VALIDITY_BADGE_TITLE_BEYOND_ELITE = (
    "Hull exceeds the elite-surfski class envelope. The class selector falls "
    "back to custom; advisory only."
)


def validity_badge_title_for(badge: str) -> str:
    """Return the operator-facing tooltip for a validity-badge state string.

    AUD-O-001: the badge chip's CSS-only colour change is the only visual
    hint of its meaning; the tooltip provides plain-text discoverability
    for sighted users without screen readers.
    """

    if not isinstance(badge, str) or not badge:
        return ""
    if badge.startswith("In ") and badge.endswith(" envelope"):
        class_label = badge[len("In ") : -len(" envelope")].strip()
        if class_label:
            return (
                f"Hull dimensions fit the {class_label} class envelope. "
                "Advisory — does not certify seaworthiness or solver readiness."
            )
        return (
            "Hull dimensions fit a standard class envelope. Advisory — does "
            "not certify seaworthiness or solver readiness."
        )
    if badge == "Custom — sub-touring":
        return VALIDITY_BADGE_TITLE_SUB_TOURING
    if badge == "Custom — beyond elite":
        return VALIDITY_BADGE_TITLE_BEYOND_ELITE
    if badge.startswith("Custom (L/B_wl="):
        ratio_part = badge[len("Custom (L/B_wl=") :].rstrip(")")
        if ratio_part:
            return (
                f"Hull length-to-beam ratio is {ratio_part}; not matched by "
                "any standard class envelope. Custom design."
            )
        return (
            "Hull length-to-beam ratio is not matched by any standard class "
            "envelope. Custom design."
        )
    return "Design validity badge (advisory only)."


#: AUD-O-002 — comparison-source toggle subtitles. The toggle exposes two
#: button values (``live_frontier`` / ``imported_report``); the subtitle
#: tells the operator what each one means without clicking the toggle.
COMPARISON_TOGGLE_LIVE_FRONTIER_HELP = (
    "Live frontier: candidates from this session's jobs index."
)
COMPARISON_TOGGLE_IMPORTED_REPORT_HELP = (
    "Imported report: a saved ComparisonReport JSON loaded into the workspace "
    "for comparison."
)

#: AUD-O-003 — mesh chip-pair tooltips clarifying what each chip means.
MESH_NO_PACKAGE_CHIP_TITLE = (
    "No CFD mesh package has been generated for this hull yet."
)
MESH_LIVE_READINESS_CHIP_TITLE = (
    "Live hull/deck readiness reported by the mesh diagnostic, independent "
    "of whether a mesh package exists."
)


def _param_row_raw_attrs(key: str, label: str) -> list[str]:
    escaped_key = html.escape(key, quote=True)
    escaped_label = html.escape(label, quote=True)
    return [
        f'data-param-key="{escaped_key}"',
        f'data-testid="param-{escaped_key}"',
        'role="group"',
        f'aria-label="{escaped_label}"',
    ]


def _pre_html(lines: list[str]) -> str:
    body = "\n".join(html.escape(str(line)) for line in lines)
    return f"<pre>{body}</pre>"


def _resistance_table_html(rows: list[dict[str, Any]]) -> str:
    header = (
        "<table class=\"kg-resistance-table\" data-testid=\"resistance-table\">"
        "<thead><tr>"
        "<th>target</th><th>kt</th><th>Fn</th><th>Rv N</th><th>Rw N</th><th>Rt N</th>"
        "</tr></thead><tbody>"
    )
    body: list[str] = []
    for row in rows:
        target_marker = "target" if row["is_target"] else ""
        row_class = "kg-resistance-row-target state-focus-row" if row["is_target"] else ""
        body.append(
            f"<tr class=\"{row_class}\">"
            f"<td>{target_marker}</td>"
            f"<td>{row['speed_kt']:.1f}</td>"
            f"<td>{row['Fn']:.2f}</td>"
            f"<td>{row['Rv_N']:.1f}</td>"
            f"<td>{row['Rw_N']:.1f}</td>"
            f"<td><strong>{row['Rt_N']:.1f}</strong></td>"
            "</tr>"
        )
    return header + "".join(body) + "</tbody></table>"


def _generative_job_state_flags(rows: list[dict[str, Any]]) -> dict[str, bool]:
    states = {str(row.get("state") or "") for row in rows}
    return {
        "empty": not rows,
        "running": bool(states & {"queued", "running"}),
        "failed": "failed" in states,
        "cancelled": "cancelled" in states,
        "resumable": "resumable" in states,
    }
