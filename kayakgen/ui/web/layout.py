"""Workspace layout construction for the kayakgen web UI.

Extracted verbatim from ``kayakgen.ui.web.app`` (refactoring campaign
kayakgen-smoke-1, slice S4). ``KayakgenApp`` composes ``LayoutMixin``.
"""

from __future__ import annotations

import html
from typing import Any

from trame.ui.vuetify3 import SinglePageWithDrawerLayout
from trame.widgets import html as html_widgets
from trame.widgets import vtk as vtkw
from trame.widgets import vuetify3 as v3

from kayakgen.ui import theme
from kayakgen.ui.web.generate_fork_button import render_fork_button
from kayakgen.ui.web.generate_frontier_view import render_frontier_view_section
from kayakgen.ui.web.generate_spec_form import render_spec_form_section
from kayakgen.ui.web.presentation import (
    COMPARISON_TOGGLE_IMPORTED_REPORT_HELP,
    COMPARISON_TOGGLE_LIVE_FRONTIER_HELP,
    EXPORT_MENU_ROWS,
    GENERATIVE_JOBS_CANCELLED_COPY,
    GENERATIVE_JOBS_EMPTY_COPY,
    GENERATIVE_JOBS_FAILED_COPY,
    GENERATIVE_JOBS_RESUMABLE_COPY,
    GENERATIVE_JOBS_RUNNING_COPY,
    HIGH_ANGLE_GZ_COPY,
    HIGH_ANGLE_GZ_HEADING,
    LAYOUT_TEST_IDS,
    MESH_LIVE_READINESS_CHIP_TITLE,
    MESH_NO_PACKAGE_CHIP_TITLE,
    MESH_PACKAGE_READINESS_HEADING,
    PARAMETER_GROUPS,
    RAW_COMPARATIVE_CAPTION,
    REGION_CLASSES,
    REVIEW_TABS,
    STATUS_SEGMENTS,
    WATERTIGHT_DISABLED_COPY,
    _SLIDER_BY_KEY,
    _param_row_raw_attrs,
)


class LayoutMixin:
    """Layout-construction methods of :class:`~kayakgen.ui.web.app.KayakgenApp`."""

    def _region_attrs(self, region: str) -> dict[str, str]:
        return {
            "id": LAYOUT_TEST_IDS[region],
            "data-testid": LAYOUT_TEST_IDS[region],
            "aria-label": f"{region} region",
            "classes": REGION_CLASSES[region],
        }

    def _build_layout(self) -> None:
        with SinglePageWithDrawerLayout(self.server) as layout:
            layout.title.set_text("kayakgen")

            with layout.toolbar:
                v3.VToolbarTitle("kayakgen ▸ {{ name }}", classes="kg-toolbar-breadcrumb")
                v3.VSpacer()
                v3.VSelect(
                    v_model=("class_preset",),
                    items=("class_preset_options",),
                    item_title="label",
                    item_value="value",
                    label="Class",
                    density="compact",
                    hide_details=True,
                    classes="kg-class-preset-select",
                )
                v3.VBtn("Reset", click=self.ctrl.reset, classes="kg-toolbar-action")
                v3.VBtn("Share", click=self.ctrl.share_url, classes="kg-toolbar-action")
                self._render_export_menu()
                v3.VSnackbar(
                    "{{ share_status }}",
                    v_model=("share_toast",),
                    timeout=3000,
                    location="top right",
                    classes="kg-share-toast",
                )
                v3.VTextField(
                    v_model=("share_url",),
                    label="Share state",
                    readonly=True,
                    hide_details=True,
                    classes="kg-share-state-probe",
                    style=(
                        "position: absolute; "
                        f"left: {theme.SPACING['screen-reader-offset']}; top: auto; "
                        f"width: {theme.DENSITY['screen-reader-size']}; "
                        f"height: {theme.DENSITY['screen-reader-size']}; overflow: hidden;"
                    ),
                    **{
                        "data-testid": "share-url-state",
                        "aria-hidden": "true",
                        "aria-live": "polite",
                        "tabindex": "-1",
                    },
                )

            with layout.drawer as drawer:
                drawer.width = 360
                with v3.VContainer(**self._region_attrs("params")):
                    v3.VCardTitle("Parameters", classes="kg-region-title")
                    # ParameterRailHeader: read-only class chip + validity badge.
                    # The VRadioGroup for class presets is removed (§0.3 / §4.2).
                    # Class selection is still available via the toolbar VSelect.
                    v3.VChip(
                        "{{ class_preset_options.find(o => o.value === class_preset)?.label || class_preset }}",
                        classes="kg-class-preset-chip mb-1",
                        size="small",
                        **{"data-testid": "class-preset-chip"},
                    )
                    # AUD-O-001: the chip's CSS-only colour shift is the only
                    # visual cue of badge meaning. Bind ``title`` to the
                    # plain-text tooltip (computed in _refresh_validity_badge)
                    # so sighted users without screen readers can discover the
                    # meaning of every envelope state on hover.
                    v3.VChip(
                        "{{ validity_badge }}",
                        classes=(
                            "kg-validity-badge",
                            "validity_badge.startsWith('In ') ? "
                            "'bg-state-success-soft' : 'bg-state-warn-soft'",
                        ),
                        size="small",
                        **{
                            "data-testid": "validity-badge",
                            "role": "status",
                            "aria-live": "polite",
                            "aria-label": ("validity_badge_aria_label",),
                            "title": ("validity_badge_title",),
                        },
                    )
                    v3.VCardText(
                        "<pre>{{ invalid_hull_state_lines.join('\\n') }}</pre>",
                        v_show=("invalid_hull_state_visible",),
                        classes="kg-state-panel kg-state-panel--failed",
                        html=True,
                        **{"data-testid": "invalid-hull-state"},
                    )
                    for group_label, keys in PARAMETER_GROUPS:
                        v3.VDivider(classes="mt-3")
                        v3.VCardSubtitle(group_label, classes="kg-rail-group-label")
                        for key in keys:
                            label, vmin, vmax, step = _SLIDER_BY_KEY[key]
                            with html_widgets.Div(
                                raw_attrs=_param_row_raw_attrs(key, label),
                                classes=f"kg-param-slider kg-param-{key} mt-3",
                            ):
                                v3.VSlider(
                                    v_model=(key,),
                                    label=label,
                                    min=(f"{key}_min", vmin),
                                    max=(f"{key}_max", vmax),
                                    step=step,
                                    thumb_label=True,
                                    density="compact",
                                    classes="kg-param-slider-control",
                                )
                    v3.VDivider(classes="mt-3")

            with layout.content:
                html_widgets.Div(v_html=("workspace_style_html",))
                with v3.VContainer(
                    fluid=True,
                    classes="fill-height pa-0 kg-workspace-shell kg-workspace-grid",
                    **{"data-testid": "workspace-shell"},
                ):
                    with v3.VRow(classes="ma-0 fill-height kg-workspace-main"):
                        with v3.VCol(cols=12, md=7, classes="pa-2"):
                            with v3.VContainer(fluid=True, **self._region_attrs("geometry")):
                                v3.VCardTitle("Geometry", classes="kg-region-title")
                                with v3.VSheet(
                                    classes="kg-vtk-frame",
                                    style=(
                                        f"height: {theme.DENSITY['viewport-height']}; "
                                        f"min-height: {theme.DENSITY['viewport-min-height']}; "
                                        "width: 100%;"
                                    ),
                                ):
                                    self.view = vtkw.VtkRemoteView(
                                        self._render_window,
                                        ref="view",
                                        classes="kg-vtk-viewport",
                                        style=(
                                            "height: 100%; "
                                            f"min-height: {theme.DENSITY['viewport-min-height']}; "
                                            "width: 100%; display: block;"
                                        ),
                                        **{"data-testid": "geometry-vtk-view"},
                                    )
                                with v3.VCard(classes="kg-metrics-strip kg-metrics-strip-scroll"):
                                    v3.VCardTitle("Metrics")
                                    v3.VCardText(
                                        "<pre>{{ metrics_lines.join('\\n') }}</pre>",
                                        classes="font-mono text-caption",
                                        html=True,
                                    )
                        with v3.VCol(cols=12, md=5, classes="pa-2"):
                            with v3.VContainer(fluid=True, **self._region_attrs("review")):
                                with v3.VTabs(
                                    v_model=("analysis_tab",),
                                    classes="kg-review-tabs",
                                    **{"data-testid": "review-tabs"},
                                ):
                                    for tab in REVIEW_TABS:
                                        v3.VTab(
                                            tab["label"],
                                            value=tab["value"],
                                            **{"data-testid": tab["test_id"]},
                                        )
                                with v3.VWindow(v_model=("analysis_tab",)):
                                    self._render_hydro_tab()
                                    self._render_mesh_tab()
                                    self._render_comparison_tab()
                                    self._render_cfd_tab()
                                    self._render_generate_tab()
                                    self._render_advisories_tab()
                    self._render_status_bar()

    def _render_export_menu(self) -> None:
        with v3.VMenu(location="bottom", close_on_content_click=True):
            with v3.Template(v_slot_activator=("{ props }",)):
                v3.VBtn(
                    "Export",
                    v_bind=("props",),
                    classes="kg-toolbar-action kg-export-menu-under-1200",
                    **{"aria-label": "Export menu"},
                )
            with v3.VList(classes="kg-export-menu-list", density="compact"):
                for row in EXPORT_MENU_ROWS:
                    attrs: dict[str, Any] = {
                        "title": row["label"],
                        "subtitle": row["subtitle"],
                        "disabled": row["disabled"],
                        "classes": row["row_class"],
                    }
                    if row["disabled"]:
                        attrs["aria-disabled"] = "true"
                    else:
                        attrs["click"] = self._export_menu_action(str(row["action_key"]))
                    v3.VListItem(**attrs)

    def _export_menu_action(self, action_key: str) -> Any:
        if action_key == "export_hull_stl":
            return lambda: self.ctrl.export_stl("hull")
        if action_key == "export_deck_stl":
            return lambda: self.ctrl.export_stl("deck")
        if action_key == "export_hydro_json":
            return self.ctrl.export_hydro_json
        raise ValueError(f"unknown export menu action: {action_key}")

    def _render_hydro_tab(self) -> None:
        with v3.VWindowItem(value="analysis"):
            with v3.VCard(classes="kg-review-card kg-hydro-card"):
                v3.VCardTitle("Hydrostatics")
                with v3.VCardText():
                    # Key/value table replacing the former <pre> block.
                    v3.VCardText(
                        (
                            "<table class='kg-hydro-table' data-testid='hydro-kv-table'>"
                            "<tbody>"
                            "<tr v-for='row in hydro_table_rows' :key='row.label'"
                            " :title='row.description'"
                            " :data-testid=\"'hydro-row-' + row.label\">"
                            "<th data-testid='hydro-row-label'>{{ row.label }}</th>"
                            "<td>{{ row.value }}</td>"
                            "</tr>"
                            "</tbody>"
                            "</table>"
                        ),
                        classes="kg-hydro-kv-wrap",
                        html=True,
                    )
                    v3.VChip(
                        "Computed from integrated geometry (60 stations)",
                        size="small",
                        classes="kg-claim-chip",
                    )
            with v3.VCard(classes="kg-review-card kg-stability-card mt-2"):
                v3.VCardTitle("Stability")
                v3.VCardText("Primary stability (analytic from waterplane)")
                # High-angle GZ: reduced to tonal warning alert (§0.4 / §4.4).
                v3.VAlert(
                    HIGH_ANGLE_GZ_COPY,
                    title=HIGH_ANGLE_GZ_HEADING,
                    type="warning",
                    prominent=False,
                    variant="tonal",
                    classes="kg-high-angle-gz-alert mt-2",
                    **{"data-testid": "high-angle-gz-alert"},
                )
            with v3.VCard(classes="kg-review-card kg-resistance-card mt-2"):
                v3.VCardTitle("Resistance - raw comparative filter")
                v3.VCardText(RAW_COMPARATIVE_CAPTION)
                v3.VCardText("{{ resistance_table_caption }}")
                v3.VCardText(
                    "{{ resistance_table_html }}",
                    classes="font-mono text-caption kg-resistance-table-wrap",
                    html=True,
                )
                v3.VChip(
                    "uncalibrated_comparative",
                    size="small",
                    classes="kg-claim-chip kg-claim-uncalibrated",
                )

    def _render_mesh_tab(self) -> None:
        with v3.VWindowItem(value="mesh"):
            with v3.VCard(classes="kg-review-card kg-mesh-card"):
                v3.VCardTitle("Hull diagnostics")
                v3.VCardText(
                    (
                        "<table class='kg-mesh-diag-table'"
                        " data-testid='mesh-hull-diag-table'>"
                        "<tbody>"
                        "<tr v-for='row in mesh_hull_diagnostic_rows' :key='row.label'>"
                        "<th>{{ row.label }}</th>"
                        "<td>{{ row.value }}</td>"
                        "</tr>"
                        "</tbody>"
                        "</table>"
                    ),
                    classes="kg-mesh-diag-kv-wrap",
                    html=True,
                )
            with v3.VCard(classes="kg-review-card kg-mesh-card mt-2"):
                v3.VCardTitle("Deck diagnostics")
                v3.VCardText(
                    (
                        "<table class='kg-mesh-diag-table'"
                        " data-testid='mesh-deck-diag-table'>"
                        "<tbody>"
                        "<tr v-for='row in mesh_deck_diagnostic_rows' :key='row.label'>"
                        "<th>{{ row.label }}</th>"
                        "<td>{{ row.value }}</td>"
                        "</tr>"
                        "</tbody>"
                        "</table>"
                    ),
                    classes="kg-mesh-diag-kv-wrap",
                    html=True,
                )
            with v3.VCard(classes="kg-review-card kg-mesh-readiness-card mt-2"):
                v3.VCardTitle(MESH_PACKAGE_READINESS_HEADING)
                v3.VSelect(
                    v_model=("mesh_profile_label",),
                    items=("mesh_profile_options",),
                    item_title="label",
                    item_value="label",
                    label="Profile",
                    density="compact",
                    classes="kg-mesh-profile-select",
                )
                v3.VCardText("Manifest profile: {{ mesh_profile_id }}")
                # When no package is selected, show two chips: neutral
                # "No package built" + live status_readiness (§0.6 / §4.5).
                # Otherwise show the package readiness level.
                # AUD-O-003: each chip carries a ``title`` tooltip explaining
                # its meaning so the relationship between "no package built"
                # and the live readiness level is discoverable on hover.
                v3.VCardText(
                    (
                        "<template v-if=\"mesh_package_status === 'No mesh package selected.'\">"
                        "<v-chip size='small' class='kg-readiness-chip kg-no-package-chip'"
                        " data-testid='mesh-no-package-chip'"
                        f" title='{html.escape(MESH_NO_PACKAGE_CHIP_TITLE, quote=True)}'"
                        ">No package built</v-chip>"
                        "<v-chip size='small' class='kg-readiness-chip kg-live-readiness-chip'"
                        " data-testid='mesh-live-readiness-chip'"
                        f" title='{html.escape(MESH_LIVE_READINESS_CHIP_TITLE, quote=True)}'"
                        ">{{ status_readiness }}</v-chip>"
                        "</template>"
                        "<template v-else>"
                        "<v-chip size='small' class='kg-readiness-chip'"
                        " data-testid='mesh-readiness-level-chip'>{{ mesh_readiness_level }}</v-chip>"
                        "</template>"
                    ),
                    html=True,
                    classes="kg-readiness-chip-wrap",
                )
                v3.VCardText("{{ mesh_package_readiness_copy }}")
                v3.VCardText(WATERTIGHT_DISABLED_COPY)
                v3.VCardText(
                    "<pre>{{ mesh_package_warning_lines.join('\\n') }}</pre>",
                    classes="font-mono text-caption",
                    html=True,
                )

    def _render_comparison_tab(self) -> None:
        with v3.VWindowItem(value="comparison"):
            with v3.VCard(classes="kg-review-card kg-comparison-card"):
                v3.VCardTitle("Comparison")
                with v3.VCardText():
                    # ComparisonSourceToggle (§4.6): live frontier vs imported report.
                    # AUD-O-002: add per-button ``title`` tooltips and a visible
                    # subtitle so an operator can discover what each toggle
                    # value means without clicking it.
                    with v3.VBtnToggle(
                        v_model=("comparison_source",),
                        density="compact",
                        classes="kg-comparison-source-toggle mb-2",
                        **{"data-testid": "comparison-source-toggle"},
                    ):
                        v3.VBtn(
                            "Live frontier",
                            value="live_frontier",
                            density="compact",
                            **{
                                "data-testid": "comparison-toggle-live-frontier",
                                "title": COMPARISON_TOGGLE_LIVE_FRONTIER_HELP,
                            },
                        )
                        v3.VBtn(
                            "Imported report",
                            value="imported_report",
                            density="compact",
                            **{
                                "data-testid": "comparison-toggle-imported-report",
                                "title": COMPARISON_TOGGLE_IMPORTED_REPORT_HELP,
                            },
                        )
                    v3.VCardText(
                        (
                            f"<div class='kg-comparison-source-help-line'>"
                            f"{html.escape(COMPARISON_TOGGLE_LIVE_FRONTIER_HELP)}"
                            f"</div>"
                            f"<div class='kg-comparison-source-help-line'>"
                            f"{html.escape(COMPARISON_TOGGLE_IMPORTED_REPORT_HELP)}"
                            f"</div>"
                        ),
                        html=True,
                        classes="kg-comparison-source-help text-caption text-medium-emphasis mb-2 pa-0",
                        **{
                            "data-testid": "comparison-source-help",
                        },
                    )
                    v3.VCardText(
                        "Live frontier has no report loaded.",
                        v_show=("comparison_source === 'live_frontier'",),
                        classes="kg-state-panel",
                        **{"data-testid": "comparison-no-report-state"},
                    )
                    # Live frontier block.
                    with html_widgets.Div(
                        v_show=("comparison_source === 'live_frontier'",),
                        classes="kg-comparison-live-frontier",
                        **{"data-testid": "comparison-live-frontier-block"},
                    ):
                        render_frontier_view_section(self)

                    # Imported report block.
                    with html_widgets.Div(
                        v_show=("comparison_source === 'imported_report'",),
                        classes="kg-comparison-imported-report",
                        **{"data-testid": "comparison-imported-report-block"},
                    ):
                        v3.VCardText(
                            "Imported report block is present.",
                            classes="kg-state-panel kg-state-panel--rendered",
                            **{"data-testid": "comparison-report-present-state"},
                        )
                        v3.VTextarea(
                            v_model=("comparison_json",),
                            label="Comparison report JSON",
                            rows=5,
                            auto_grow=True,
                            density="compact",
                        )
                        v3.VBtn(
                            "Load Report",
                            click=self.ctrl.load_comparison,
                            density="compact",
                            classes="mr-2",
                        )
                        v3.VSelect(
                            v_model=("selected_candidate_index",),
                            items=("comparison_candidate_options",),
                            label="Candidate index",
                            density="compact",
                            classes="mt-2",
                        )
                        v3.VBtn(
                            "Apply Candidate Parameters",
                            click=self.ctrl.load_candidate,
                            density="compact",
                        )
                        v3.VCardText("Pinned candidates: none", classes="kg-pinned-empty")
                        v3.VCardText(
                            "<pre>{{ comparison_status }}</pre>",
                            classes="font-mono text-caption mt-2",
                            html=True,
                        )
                        v3.VCardText(
                            "<pre>{{ comparison_lines.join('\\n') }}</pre>",
                            classes="font-mono text-caption",
                            html=True,
                        )
                        # RFC 0043 stage 3 display-only high-angle GZ section.
                        # The HTML is precomputed by ``read_models.py`` so app.py
                        # never embeds artifact field name string literals.
                        v3.VCardText(
                            "{{ high_angle_gz_section_html }}",
                            v_show=("high_angle_gz_section_visible",),
                            classes="kg-high-angle-gz-wrap",
                            html=True,
                            **{"data-testid": "high-angle-gz-wrap"},
                        )

    def _render_cfd_tab(self) -> None:
        with v3.VWindowItem(value="cfd"):
            with v3.VCard(classes="kg-review-card kg-cfd-card"):
                v3.VCardTitle("CFD")
                v3.VCardText("{{ cfd_local_banner }}", classes="kg-cfd-banner")
                v3.VCardText("{{ cfd_artifact_strapline }}", classes="kg-cfd-banner")
                with v3.VCardText():
                    v3.VCardText(
                        "No CFD job prepared.",
                        v_show=("!cfd_job_id",),
                        classes="kg-state-panel",
                        **{"data-testid": "cfd-no-job-state"},
                    )
                    v3.VCardText(
                        "<pre>{{ cfd_status_lines.join('\\n') }}</pre>",
                        v_show=("!!cfd_job_id",),
                        classes="kg-state-panel kg-cfd-status-state",
                        html=True,
                        **{"data-testid": "cfd-status-state"},
                    )
                    v3.VSelect(
                        v_model=("cfd_solver_profile",),
                        items=("cfd_profile_options",),
                        label="Local solver/test profile",
                        density="compact",
                    )
                    v3.VTextField(
                        v_model=("cfd_mesh_package_ref",),
                        label="Server-local mesh package path",
                        density="compact",
                    )
                    v3.VTextField(
                        v_model=("cfd_speed_mps",),
                        label="Speed (m/s)",
                        type="number",
                        density="compact",
                    )
                    v3.VTextField(
                        v_model=("cfd_job_id",),
                        label="Job ID",
                        density="compact",
                    )
                    v3.VTextField(
                        v_model=("cfd_jobs_root",),
                        label="Local CFD jobs root",
                        readonly=True,
                        density="compact",
                    )
                    v3.VBtn(
                        "Prepare",
                        click=self.ctrl.prepare_cfd_job,
                        density="compact",
                        classes="mr-2",
                    )
                    v3.VBtn(
                        "Run",
                        click=self.ctrl.run_cfd_job,
                        density="compact",
                        classes="mr-2",
                    )
                    v3.VBtn(
                        "Refresh",
                        click=self.ctrl.refresh_cfd_job,
                        density="compact",
                        classes="mr-2",
                    )
                    v3.VBtn(
                        "Logs",
                        click=self.ctrl.load_cfd_logs,
                        density="compact",
                        classes="mr-2",
                    )
                    v3.VBtn(
                        "Raw Result",
                        click=self.ctrl.load_cfd_raw_result,
                        density="compact",
                    )
                    v3.VCardText(
                        "<pre>{{ cfd_status_lines.join('\\n') }}</pre>",
                        classes="font-mono text-caption mt-2",
                        html=True,
                    )
                    v3.VCardText(
                        "<pre>{{ cfd_logs_lines.join('\\n') }}</pre>",
                        classes="font-mono text-caption",
                        html=True,
                    )
                    v3.VCardText(
                        "<pre>{{ cfd_raw_result_lines.join('\\n') }}</pre>",
                        classes="font-mono text-caption",
                        html=True,
                    )

    def _render_generate_tab(self) -> None:
        with v3.VWindowItem(value="generate"):
            with v3.VCard(classes="kg-review-card kg-generate-card"):
                v3.VCardTitle("Generate")
                v3.VCardText(
                    (
                        "Build a sweep or search spec and submit it to the "
                        "server-local job manager."
                    ),
                    classes="kg-generate-banner",
                )
                v3.VCardText("{{ generative_status }}", classes="kg-generate-status")
                with v3.VCardText():
                    v3.VTextField(
                        v_model=("generative_jobs_root",),
                        label="Generative jobs root",
                        readonly=True,
                        density="compact",
                    )
                    with html_widgets.Div(classes="kg-generate-build"):
                        render_spec_form_section(self)
                    # Single kind-aware submit button (§4.7); label and action vary by kind.
                    # The button is always present; we use v_show to swap between two
                    # styled buttons that each have data-testid="generative-submit".
                    # AUD-O-004: each button is bound to ``generative_submit_disabled``
                    # and points at a visible blocking-reason span via
                    # ``aria-describedby``. The span text is the operator-facing
                    # reason computed by ``refresh_submit_blocking_reason``.
                    v3.VBtn(
                        "Submit Search",
                        click=self.ctrl.submit_generative_search,
                        density="compact",
                        classes="mr-2 kg-generate-submit",
                        v_show=("generative_job_kind !== 'sweep'",),
                        disabled=("generative_submit_disabled",),
                        **{
                            "data-testid": "generative-submit",
                            "aria-describedby": "submit-blocking-reason-search",
                        },
                    )
                    v3.VBtn(
                        "Submit Sweep",
                        click=self.ctrl.submit_generative_sweep,
                        density="compact",
                        classes="mr-2 kg-generate-submit",
                        v_show=("generative_job_kind === 'sweep'",),
                        disabled=("generative_submit_disabled",),
                        **{
                            "data-testid": "generative-submit",
                            "aria-describedby": "submit-blocking-reason-sweep",
                        },
                    )
                    v3.VCardText(
                        (
                            "<span id='submit-blocking-reason-search'"
                            " data-testid='submit-blocking-reason-search'"
                            " class='kg-generate-submit-blocking-reason"
                            " text-caption text-warning'"
                            " v-show=\"generative_submit_disabled"
                            " && generative_job_kind !== 'sweep'\">"
                            "{{ generative_submit_blocking_reason }}"
                            "</span>"
                            "<span id='submit-blocking-reason-sweep'"
                            " data-testid='submit-blocking-reason-sweep'"
                            " class='kg-generate-submit-blocking-reason"
                            " text-caption text-warning'"
                            " v-show=\"generative_submit_disabled"
                            " && generative_job_kind === 'sweep'\">"
                            "{{ generative_submit_blocking_reason }}"
                            "</span>"
                        ),
                        html=True,
                        classes="kg-generate-submit-blocking-reason-wrap pa-0",
                    )
                    with html_widgets.Div(classes="kg-generate-watch"):
                        v3.VBtn(
                            "Refresh Jobs",
                            click=self.ctrl.refresh_generative_jobs,
                            density="compact",
                            classes="mr-2",
                        )
                        v3.VTextField(
                            v_model=("generative_job_id",),
                            label="Selected job id",
                            density="compact",
                        )
                        v3.VBtn(
                            "Cancel",
                            click=self.ctrl.cancel_generative_job,
                            density="compact",
                            classes="mr-2",
                        )
                        v3.VBtn(
                            "Resume",
                            click=self.ctrl.resume_generative_job,
                            density="compact",
                            classes="mr-2",
                        )
                        v3.VBtn(
                            "Load Log",
                            click=self.ctrl.load_generative_log,
                            density="compact",
                            classes="mr-2",
                        )
                        v3.VBtn(
                            "Load Frontier",
                            click=self.ctrl.load_generative_frontier,
                            density="compact",
                        )
                        v3.VCardText(
                            GENERATIVE_JOBS_EMPTY_COPY,
                            v_show=("generative_jobs_empty",),
                            classes="kg-state-panel",
                            **{"data-testid": "generative-jobs-empty-state"},
                        )
                        v3.VCardText(
                            GENERATIVE_JOBS_RUNNING_COPY,
                            v_show=("generative_jobs_running",),
                            classes="kg-state-panel kg-state-panel--running",
                            **{"data-testid": "generative-jobs-running-state"},
                        )
                        v3.VCardText(
                            (
                                GENERATIVE_JOBS_FAILED_COPY
                                + " {{ generative_jobs_failed_kind }}"
                            ),
                            v_show=("generative_jobs_failed",),
                            classes="kg-state-panel kg-state-panel--failed",
                            **{"data-testid": "generative-jobs-failed-state"},
                        )
                        v3.VCardText(
                            GENERATIVE_JOBS_CANCELLED_COPY,
                            v_show=("generative_jobs_cancelled",),
                            classes="kg-state-panel kg-state-panel--cancelled",
                            **{"data-testid": "generative-jobs-cancelled-state"},
                        )
                        v3.VCardText(
                            GENERATIVE_JOBS_RESUMABLE_COPY,
                            v_show=("generative_jobs_resumable",),
                            classes="kg-state-panel kg-state-panel--resumable",
                            **{"data-testid": "generative-jobs-resumable-state"},
                        )
                        # Jobs index as VDataTable (§4.7 / §18).
                        v3.VDataTable(
                            headers=(
                                "[{title: 'Job ID', key: 'job_id', sortable: true},"
                                " {title: 'Kind', key: 'job_kind', sortable: true},"
                                " {title: 'State', key: 'state', sortable: true},"
                                " {title: 'Error kind', key: 'error_kind', sortable: true}]"
                            ),
                            items=("generative_jobs_table_rows",),
                            item_value="job_id",
                            density="compact",
                            classes="kg-jobs-table",
                            **{"data-testid": "generative-jobs-table"},
                        )
                        self._render_generate_job_fork_buttons()
                        v3.VCardText(
                            "<pre>{{ generative_log_lines.join('\\n') }}</pre>",
                            classes="font-mono text-caption",
                            html=True,
                        )
                    # Frontier view section moved to Comparison tab (§8.1 / §0.9).

    def _render_generate_job_fork_buttons(self) -> None:
        """Render fork buttons for any succeeded rows known at layout build time."""

        try:
            summaries = self._generative_manager.list()
        except Exception:  # noqa: BLE001 - render should not depend on the store
            summaries = []
        for summary in summaries:
            if hasattr(summary, "model_dump"):
                payload = summary.model_dump(mode="json")
            elif isinstance(summary, dict):
                payload = dict(summary)
            else:
                payload = {
                    "job_id": getattr(summary, "job_id", ""),
                    "state": getattr(summary, "state", ""),
                }
            if payload.get("state") != "succeeded":
                continue
            render_fork_button(self, job_summary=payload)

    def _render_advisories_tab(self) -> None:
        with v3.VWindowItem(value="advisories"):
            with v3.VCard(classes="kg-review-card kg-advisories-card"):
                v3.VCardTitle("Advisories")
                v3.VChip("{{ advisory_count }} advisories", size="small")
                v3.VCardText(
                    "<pre>{{ advisory_lines.join('\\n') }}</pre>",
                    classes="font-mono text-caption",
                    html=True,
                )

    def _render_status_bar(self) -> None:
        with v3.VSheet(
            classes="kg-status-bar kg-status-wrap-under-960",
            **{
                "data-testid": "workspace-status-bar",
                "aria-live": "polite",
            },
        ):
            for segment in STATUS_SEGMENTS:
                state_key = segment["state_key"]
                label = segment["key"]
                target_tab = segment["target_tab"]
                v3.VBtn(
                    f"{label}: {{{{ {state_key} }}}}",
                    click=lambda tab=target_tab: self._focus_review_tab(tab),
                    density="compact",
                    variant="text",
                    classes=f"kg-status-segment kg-status-{label}",
                    **{
                        "data-testid": f"status-{label}",
                        "aria-label": (f"{state_key}_aria_label",),
                    },
                )
