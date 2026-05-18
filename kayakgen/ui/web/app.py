"""Trame app factory for the kayakgen web frontend.

Importing this module requires the ``kayakgen[web]`` extras
(``trame``, ``trame-vuetify``, ``trame-vtk``, ``vtk``).
"""

from __future__ import annotations

import html
import json
from typing import Any

import numpy as np
import vtk
from trame.app import get_server
from trame.ui.vuetify3 import SinglePageWithDrawerLayout
from trame.widgets import html as html_widgets
from trame.widgets import vtk as vtkw
from trame.widgets import vuetify3 as v3

from kayakgen.model.hull import Hull
from kayakgen.ui import theme
from kayakgen.ui.web.controllers import (
    CFD_LOCAL_FILESYSTEM_NOTICE,
    CFD_RAW_RESULTS_WARNING,
    CfdWebError,
    CfdWebStore,
    HullStore,
    InProcessGenerativeJobManager,
    class_preset_options,
    class_preset_read_model,
    candidate_state_from_report_json,
    clamp_beam_wl_state,
    comparison_view_model_from_json,
    cancel_generative_job_payload,
    cfd_error_lines_from_payload,
    cfd_job_logs_payload,
    cfd_job_raw_result_payload,
    cfd_job_status_payload,
    cfd_logs_lines_from_payload,
    cfd_profile_names,
    cfd_raw_result_lines_from_payload,
    cfd_status_lines_from_payload,
    create_cfd_job_payload,
    evaluation_payload,
    evaluation_summary,
    generative_job_frontier_payload,
    generative_job_list_payload,
    generative_job_log_payload,
    hydro_lines_from_state,
    hull_from_web_state,
    mesh_diagnostics_lines_from_state,
    mesh_package_view_model,
    metrics_from_state,
    register_rest_routes,
    resistance_table_view_model,
    resume_generative_job_payload,
    run_cfd_job_payload,
    start_generative_job_payload,
    validation_error_payload,
    validity_badge_from_state,
)
from kayakgen.ui.web.read_models import (
    web_high_angle_gz_section_html,
    web_high_angle_gz_view_model_from_json,
)
from kayakgen.ui.web.state import (
    HULL_STATE_FIELDS,
    MESH_PACKAGE_REF_ALIASES,
    STATE_SNAPSHOT_KEYS,
    decode_hull_query,
    encode_hull_query,
    hull_from_query_string,
    state_dict_from_hull,
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

PARAMETER_RAIL_CSS = (
    ".kg-param-slider .v-slider__label { "
    "font: var(--type-label); "
    "color: var(--text-secondary); "
    "white-space: nowrap; "
    "overflow: hidden; "
    "text-overflow: ellipsis; "
    "}"
)

RAW_COMPARATIVE_CAPTION = "Raw comparative filter; not final prediction."
RESISTANCE_DETAIL_COPY = (
    "Uncalibrated; no accepted final-prediction validity envelope. "
    "Compare nearby candidates, do not report as drag."
)
HIGH_ANGLE_GZ_HEADING = "High-angle GZ unavailable"
HIGH_ANGLE_GZ_COPY = (
    "High-angle GZ visualisation is deferred; see RFC 0020 / RFC 0024."
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

PERSISTENT_COPY: dict[str, str] = {
    "raw_comparative_filter": RAW_COMPARATIVE_CAPTION,
    "resistance_detail": RESISTANCE_DETAIL_COPY,
    "high_angle_gz_heading": HIGH_ANGLE_GZ_HEADING,
    "mesh_package_readiness_heading": MESH_PACKAGE_READINESS_HEADING,
    "mesh_package_readiness": MESH_PACKAGE_READINESS_COPY,
    "cfd_local_banner": CFD_LOCAL_FILESYSTEM_NOTICE,
    "cfd_artifact_strapline": CFD_ARTIFACT_STRAPLINE,
    "share_toast": SHARE_TOAST_COPY,
}

_SLIDER_BY_KEY = {key: (label, vmin, vmax, step) for key, label, vmin, vmax, step in SLIDER_DEFS}


def _param_row_raw_attrs(key: str, label: str) -> list[str]:
    escaped_key = html.escape(key, quote=True)
    escaped_label = html.escape(label, quote=True)
    return [
        f'data-param-key="{escaped_key}"',
        f'data-testid="param-{escaped_key}"',
        'role="group"',
        f'aria-label="{escaped_label}"',
    ]


def _build_polydata(vertices: np.ndarray, faces: np.ndarray) -> vtk.vtkPolyData:
    pts = vtk.vtkPoints()
    for v in vertices:
        pts.InsertNextPoint(*v)

    cells = vtk.vtkCellArray()
    for f in faces:
        cells.InsertNextCell(3)
        for idx in f:
            cells.InsertCellPoint(int(idx))

    poly = vtk.vtkPolyData()
    poly.SetPoints(pts)
    poly.SetPolys(cells)

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(poly)
    normals.SplittingOff()
    normals.Update()
    return normals.GetOutput()


def _make_actor(
    poly: vtk.vtkPolyData,
    rgb: tuple[float, float, float],
    opacity: float,
) -> vtk.vtkActor:
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*rgb)
    actor.GetProperty().SetOpacity(opacity)
    actor.GetProperty().SetInterpolationToPhong()
    return actor


def _default_generative_jobs_root_for_app() -> str:
    """Default jobs root for the Trame app's in-process job manager.

    Honors ``KAYAKGEN_GENERATIVE_JOBS_ROOT`` for tests/operators; otherwise
    falls back to ``~/.local/share/kayakgen/generative_jobs/``.
    """

    import os
    from pathlib import Path as _Path

    override = os.environ.get("KAYAKGEN_GENERATIVE_JOBS_ROOT")
    if override:
        return str(_Path(override).expanduser())
    return str(_Path.home() / ".local" / "share" / "kayakgen" / "generative_jobs")


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


class KayakgenApp:
    """Trame app driving the kayakgen web UI."""

    def __init__(
        self,
        server: Any | None = None,
        initial_hull: Hull | None = None,
        initial_query: str | None = None,
    ) -> None:
        self.server = server if server is not None else get_server(client_type="vue3")
        self.state = self.server.state
        self.ctrl = self.server.controller

        if initial_hull is None and initial_query:
            initial_hull = hull_from_query_string(initial_query)
        hull = initial_hull or Hull()
        self.state.update(state_dict_from_hull(hull))
        self.state.target_speed_kt = 3.5
        self.state.share_url = ""
        self.state.share_status = ""
        self.state.share_toast = False
        self.state.metrics_lines = []
        self.state.analysis_tab = "analysis"
        self.state.analysis_lines = []
        self.state.class_preset = "custom"
        self.state.class_preset_options = list(CLASS_PRESET_OPTIONS)
        self.state.validity_badge = "Custom (L/B_wl=0.0)"
        self.state.validity_badge_aria_label = "Design validity badge: unavailable"
        self._init_slider_bounds()
        self._applying_class_preset = False
        self._active_preset_seed_name = ""
        self._active_preset_seed_snapshot: dict[str, Any] = {}
        self.state.export_menu_rows = [dict(row) for row in EXPORT_MENU_ROWS]
        self.state.export_status = ""
        self.state.mesh_profile_label = MESH_PROFILE_LABEL
        self.state.mesh_profile_id = MESH_PROFILE_ID
        self.state.mesh_profile_options = []
        self.state.mesh_readiness_level = MESH_READINESS_LEVEL
        self.state.mesh_package_readiness_copy = MESH_PACKAGE_READINESS_COPY
        self.state.mesh_hull_diagnostics_lines = []
        self.state.mesh_deck_diagnostics_lines = []
        self.state.mesh_package_warning_lines = []
        self.state.mesh_package_status = "No mesh package selected."
        self.state.resistance_table_rows = []
        self.state.resistance_table_html = ""
        self.state.resistance_table_caption = RESISTANCE_DETAIL_COPY
        self.state.resistance_claim_state = "uncalibrated_comparative"
        self.state.advisory_count = 0
        self.state.advisory_lines = ["No design advisories for current hull."]
        self.state.comparison_json = ""
        self.state.comparison_status = "Paste a comparison report JSON to inspect candidates."
        self.state.comparison_lines = []
        self.state.comparison_candidate_options = []
        self.state.selected_candidate_index = 0
        # RFC 0043 stage 3 web read model: high-angle GZ section state. The
        # section is rendered as precomputed HTML (see ``read_models.py``) so
        # the layout never templates artifact field names directly.
        self.state.high_angle_gz_section_visible = False
        self.state.high_angle_gz_section_html = ""
        self.state.cfd_profile_options = cfd_profile_names()
        self.state.cfd_solver_profile = (
            self.state.cfd_profile_options[0]
            if self.state.cfd_profile_options
            else "unavailable-open-wetted-surface"
        )
        self.state.cfd_mesh_package_ref = ""
        self.state.cfd_speed_mps = 2.5
        self.state.cfd_job_id = ""
        self.state.cfd_warning = CFD_RAW_RESULTS_WARNING
        self.state.cfd_local_banner = CFD_LOCAL_FILESYSTEM_NOTICE
        self.state.cfd_artifact_strapline = CFD_ARTIFACT_STRAPLINE
        self.state.cfd_jobs_root = ""
        self.state.cfd_status_lines = cfd_status_lines_from_payload(None)
        self.state.cfd_logs_lines = []
        self.state.cfd_raw_result_lines = []
        self.state.status_package = MESH_PROFILE_LABEL
        self.state.status_readiness = MESH_READINESS_LEVEL
        self.state.status_resistance = "uncalibrated_comparative"
        self.state.status_cfd = "unavailable"
        self.state.status_segments = []
        self.state.status_package_aria_label = ""
        self.state.status_readiness_aria_label = ""
        self.state.status_resistance_aria_label = ""
        self.state.status_cfd_aria_label = ""

        self._renderer = vtk.vtkRenderer()
        self._renderer.SetBackground(*theme.vtk_background_rgb(dark=False))
        self._render_window = vtk.vtkRenderWindow()
        self._render_window.AddRenderer(self._renderer)
        self._render_window.SetOffScreenRendering(1)
        self._interactor = vtk.vtkRenderWindowInteractor()
        self._interactor.SetRenderWindow(self._render_window)

        self._hull_actor: vtk.vtkActor | None = None
        self._deck_actor: vtk.vtkActor | None = None
        self._hull_store = HullStore()
        self._cfd_store = CfdWebStore()
        self.state.cfd_jobs_root = str(self._cfd_store.jobs_root)
        self._generative_manager = InProcessGenerativeJobManager(
            jobs_root=_default_generative_jobs_root_for_app(),
        )
        self.state.generative_jobs_root = str(self._generative_manager.jobs_root)
        self.state.generative_spec_json = ""
        self.state.generative_job_id = ""
        self.state.generative_status = (
            "Paste a sweep or search spec JSON and submit to start a new job."
        )
        self.state.generative_jobs_lines = []
        self.state.generative_log_lines = []
        self.state.generative_frontier_lines = []
        self._rebuild_scene(hull)

        self.ctrl.export_stl = lambda part: self._export_stl(part)
        self.ctrl.export_hydro_json = lambda: self._export_hydro_json()
        self.ctrl.share_url = lambda: self._share_url()
        self.ctrl.reset = lambda: self._reset()
        self.ctrl.refresh_analysis = lambda: self._refresh_analysis()
        self.ctrl.load_comparison = lambda: self._load_comparison()
        self.ctrl.load_candidate = lambda: self._load_selected_candidate()
        self.ctrl.prepare_cfd_job = lambda: self._prepare_cfd_job()
        self.ctrl.refresh_cfd_job = lambda: self._refresh_cfd_job()
        self.ctrl.run_cfd_job = lambda: self._run_cfd_job()
        self.ctrl.load_cfd_logs = lambda: self._load_cfd_logs()
        self.ctrl.load_cfd_raw_result = lambda: self._load_cfd_raw_result()
        self.ctrl.submit_generative_search = lambda: self._submit_generative_job("search")
        self.ctrl.submit_generative_sweep = lambda: self._submit_generative_job("sweep")
        self.ctrl.refresh_generative_jobs = lambda: self._refresh_generative_jobs()
        self.ctrl.cancel_generative_job = lambda: self._cancel_generative_job()
        self.ctrl.resume_generative_job = lambda: self._resume_generative_job()
        self.ctrl.load_generative_log = lambda: self._load_generative_log()
        self.ctrl.load_generative_frontier = lambda: self._load_generative_frontier()
        self.ctrl.focus_review_tab = lambda tab: self._focus_review_tab(tab)
        self.ctrl.on_server_bind.add(self._on_server_bind)

        self._wire_state_listeners()
        self._build_layout()
        self._refresh_metrics()
        self._refresh_analysis()
        self._refresh_status_segments()
        self._refresh_mesh()

    # ----- parameter rail state -----

    def _init_slider_bounds(self) -> None:
        for key, _label, vmin, vmax, _step in SLIDER_DEFS:
            setattr(self.state, f"{key}_min", vmin)
            setattr(self.state, f"{key}_max", vmax)

    def _apply_slider_bounds(self, preset: str) -> None:
        model = class_preset_read_model(preset)
        bounds = model["bounds"]
        for key, _label, vmin, vmax, _step in SLIDER_DEFS:
            bound = bounds.get(key)
            setattr(self.state, f"{key}_min", bound["min"] if bound else vmin)
            setattr(self.state, f"{key}_max", bound["max"] if bound else vmax)

    def _apply_class_preset(self, preset: str) -> None:
        model = class_preset_read_model(str(preset or "custom"))
        if model["preset"] == "custom":
            self.state.class_preset = "custom"
            self._active_preset_seed_name = ""
            self._active_preset_seed_snapshot = {}
            self._apply_slider_bounds("custom")
            self._refresh_current_hull_surface()
            return

        self._applying_class_preset = True
        try:
            self._apply_slider_bounds(model["preset"])
            values = clamp_beam_wl_state({**self._state_snapshot(), **model["values"]})
            self.state.update(
                {
                    key: values[key]
                    for key in model["values"]
                    if key in values
                }
            )
            self._active_preset_seed_name = str(model["preset"])
            self._active_preset_seed_snapshot = {
                key: getattr(self.state, key)
                for key in HULL_STATE_FIELDS
            }
        finally:
            self._applying_class_preset = False
        self._refresh_current_hull_surface()

    def _state_matches_preset_seed(self, preset: str) -> bool:
        model = class_preset_read_model(preset)
        if model["preset"] == "custom" or preset != self._active_preset_seed_name:
            return False
        snapshot = self._state_snapshot()
        if any(
            abs(float(snapshot.get(key, 0.0)) - float(value)) > 1e-9
            for key, value in self._active_preset_seed_snapshot.items()
        ):
            return False
        return all(
            abs(float(snapshot.get(key, 0.0)) - float(value)) <= 1e-9
            for key, value in model["values"].items()
        )

    # ----- 3D scene -----

    def _rebuild_scene(self, hull: Hull) -> None:
        if self._hull_actor is not None:
            self._renderer.RemoveActor(self._hull_actor)
        if self._deck_actor is not None:
            self._renderer.RemoveActor(self._deck_actor)

        geom = hull.to_geometry()
        v_hull, f_hull = geom.mesh("hull", stations=80)
        v_deck, f_deck = geom.mesh("deck", stations=80)

        self._hull_actor = _make_actor(
            _build_polydata(v_hull, f_hull),
            theme.rgb_float("data-hull"),
            1.0,
        )
        self._deck_actor = _make_actor(
            _build_polydata(v_deck, f_deck),
            theme.rgb_float("data-deck"),
            0.85,
        )
        self._renderer.AddActor(self._hull_actor)
        self._renderer.AddActor(self._deck_actor)
        self._renderer.ResetCamera()
        self._render_window.Render()

    # ----- handlers -----

    def _current_hull(self) -> Hull:
        return hull_from_web_state(self._state_snapshot())

    def _state_snapshot(self) -> dict[str, Any]:
        return {
            key: getattr(self.state, key)
            for key in STATE_SNAPSHOT_KEYS
            if hasattr(self.state, key)
        }

    def _refresh_current_hull_surface(self) -> None:
        try:
            hull = self._current_hull()
        except Exception:
            self._refresh_metrics()
            self._refresh_analysis()
            self._refresh_mesh()
            return
        self._rebuild_scene(hull)
        self._refresh_metrics()
        self._refresh_analysis()
        self._refresh_mesh()
        if hasattr(self, "view") and self.view is not None:
            self.view.update()

    def _refresh_metrics(self) -> None:
        try:
            m = metrics_from_state(self._state_snapshot())
        except Exception as exc:  # validation errors from Pydantic
            payload = validation_error_payload(exc)
            details = payload.get("details", [])
            messages = [f"{d['field']}: {d['message']}" for d in details]
            self.state.metrics_lines = ["Invalid hull state", *messages]
            self.state.advisory_count = 0
            self.state.advisory_lines = ["Advisories unavailable for invalid hull state."]
            self._refresh_status_segments()
            return
        self.state.metrics_lines = [
            f"Displacement {m['displaced_mass_kg']:7.1f} kg",
            f"Wetted surf  {m['wetted_surface_m2']:7.3f} m²",
            f"Waterplane   {m['waterplane_area_m2']:7.3f} m²",
            f"Cp / Cm      {m['Cp_actual']:.3f} / {m['Cm_actual']:.3f}",
            f"L/B_wl       {m['l_over_bwl']:7.2f}",
            f"At {self.state.target_speed_kt:.1f} kt (Fn {m['Fn']:.2f})",
            f"  Claim     {m['resistance_claim_state']}",
            "  Warning   raw comparative filter; not final prediction",
            f"  Viscous   {m['Rv_N']:6.1f} N",
            f"  Wave      {m['Rw_N']:6.1f} N",
            f"  Total     {m['Rt_N']:6.1f} N",
        ]
        if m["advisory_warnings"]:
            self.state.metrics_lines.extend(
                ["Advisory", *[f"  {w}" for w in m["advisory_warnings"]]]
            )
            self.state.advisory_lines = list(m["advisory_warnings"])
        else:
            self.state.advisory_lines = ["No design advisories for current hull."]
        self.state.advisory_count = len(m["advisory_warnings"])
        self.state.status_resistance = m["resistance_claim_state"]
        self._refresh_validity_badge()
        self._refresh_status_segments()

    def _refresh_analysis(self) -> None:
        state = self._state_snapshot()
        try:
            self.state.analysis_lines = hydro_lines_from_state(state)
        except Exception as exc:
            payload = validation_error_payload(exc)
            details = payload.get("details", [])
            messages = [f"{d['field']}: {d['message']}" for d in details]
            self.state.analysis_lines = ["Analysis unavailable", *messages]
        try:
            model = resistance_table_view_model(state)
        except Exception as exc:
            payload = validation_error_payload(exc)
            details = payload.get("details", [])
            messages = [f"{d['field']}: {d['message']}" for d in details]
            self.state.resistance_table_rows = []
            self.state.resistance_table_html = _pre_html(["Resistance unavailable", *messages])
            return
        self.state.resistance_table_rows = model["rows"]
        self.state.resistance_table_caption = model["caption"]
        self.state.resistance_claim_state = model["metadata"]["claim_state"]
        self.state.resistance_table_html = _resistance_table_html(model["rows"])

    def _refresh_mesh(self) -> None:
        state = self._state_snapshot()
        try:
            self.state.mesh_hull_diagnostics_lines = mesh_diagnostics_lines_from_state(
                state,
                part="hull",
            )
            self.state.mesh_deck_diagnostics_lines = mesh_diagnostics_lines_from_state(
                state,
                part="deck",
            )
        except Exception as exc:
            payload = validation_error_payload(exc)
            details = payload.get("details", [])
            messages = [f"{d['field']}: {d['message']}" for d in details]
            self.state.mesh_hull_diagnostics_lines = ["Hull diagnostics unavailable", *messages]
            self.state.mesh_deck_diagnostics_lines = ["Deck diagnostics unavailable", *messages]

        package_ref = str(
            next((state.get(key) for key in MESH_PACKAGE_REF_ALIASES if state.get(key)), "")
        )
        model = mesh_package_view_model(package_ref) if package_ref else None
        if model is None:
            model = mesh_package_view_model("")
            self.state.mesh_package_status = "No mesh package selected."
            self.state.mesh_package_warning_lines = [
                "No mesh package selected.",
                MESH_PACKAGE_READINESS_COPY,
            ]
            self.state.mesh_package_readiness_copy = (
                "No mesh package selected. Live diagnostics use the current hull and deck. "
                f"{MESH_PACKAGE_READINESS_COPY}"
            )
        else:
            self.state.mesh_package_status = str(model.get("status", "unknown"))
            self.state.mesh_package_warning_lines = list(model.get("warnings", []))
            reasons = model.get("readiness", {}).get("reasons", [])
            self.state.mesh_package_readiness_copy = (
                "; ".join(reasons) if reasons else "Mesh package readiness has no warnings."
            )
        self.state.mesh_profile_options = model["profile_options"]
        self.state.mesh_profile_label = model["profile"]["label"]
        self.state.mesh_profile_id = model["profile"]["profile_id"]
        readiness = model["readiness"]
        self.state.mesh_readiness_level = (
            readiness.get("display") or readiness.get("level") or "unavailable"
        )

    def _refresh_validity_badge(self) -> None:
        try:
            badge = validity_badge_from_state(self._state_snapshot())
        except Exception:
            badge = "Custom (L/B_wl=0.0)"
        self.state.validity_badge = badge
        self.state.validity_badge_aria_label = f"Design validity badge: {badge}"

    def _refresh_status_segments(self) -> None:
        try:
            summary = evaluation_summary(self._state_snapshot())
            self.state.status_package = summary["package"]["label"]
            self.state.status_readiness = (
                summary["readiness"].get("display")
                or summary["readiness"].get("level")
                or "unavailable"
            )
            self.state.status_resistance = summary["resistance_claim"]["claim_state"]
            self.state.status_cfd = summary["cfd_status"]
        except Exception:
            self.state.status_package = MESH_PROFILE_LABEL
            self.state.status_readiness = "unavailable"
        self.state.status_segments = [
            f"package: {self.state.status_package}",
            f"readiness: {self.state.status_readiness}",
            f"resistance: {self.state.status_resistance}",
            f"cfd: {self.state.status_cfd}",
        ]
        for segment in STATUS_SEGMENTS:
            label = segment["key"]
            value = getattr(self.state, segment["state_key"])
            setattr(
                self.state,
                f"{segment['state_key']}_aria_label",
                f"{label}: {value}; opens {segment['target_tab']} tab",
            )

    def _set_cfd_status_segment(self, payload: dict[str, Any] | None = None) -> None:
        status = "unavailable"
        if payload:
            run = payload.get("run", {})
            status = str(run.get("status") or status)
        self.state.status_cfd = status
        self._refresh_status_segments()

    def _focus_review_tab(self, tab: str) -> None:
        if tab in {entry["value"] for entry in REVIEW_TABS}:
            self.state.analysis_tab = tab

    def _on_hull_param_change(self, **_kwargs: Any) -> None:
        if self._applying_class_preset:
            return
        if self.state.class_preset != "custom":
            if self._state_matches_preset_seed(str(self.state.class_preset)):
                self._apply_slider_bounds(str(self.state.class_preset))
                self._refresh_current_hull_surface()
                return
            self.state.class_preset = "custom"
            self._active_preset_seed_name = ""
            self._active_preset_seed_snapshot = {}
            self._apply_slider_bounds("custom")
            self._refresh_current_hull_surface()
            return
        normalized = clamp_beam_wl_state(self._state_snapshot())
        if normalized.get("beam_wl_m") != self.state.beam_wl_m:
            self.state.beam_wl_m = normalized["beam_wl_m"]
            return
        self._refresh_current_hull_surface()

    def _on_view_param_change(self, **_kwargs: Any) -> None:
        self._refresh_metrics()
        self._refresh_analysis()

    def _on_class_preset_change(self, **_kwargs: Any) -> None:
        self._apply_class_preset(str(self.state.class_preset or "custom"))

    def _wire_state_listeners(self) -> None:
        self.state.change(*HULL_STATE_FIELDS)(self._on_hull_param_change)
        self.state.change("target_speed_kt")(self._on_view_param_change)
        self.state.change("class_preset")(self._on_class_preset_change)

    def _on_server_bind(self, ws_server: Any) -> None:
        register_rest_routes(
            ws_server.app,
            self._hull_store,
            cfd_store=self._cfd_store,
            generative_manager=self._generative_manager,
        )
        self._install_browser_request_middleware(ws_server.app)

    def _install_browser_request_middleware(self, aiohttp_app: Any) -> None:
        if aiohttp_app.get("kayakgen_browser_request_middleware_installed"):
            return

        from aiohttp import web

        @web.middleware
        async def browser_request_middleware(request: Any, handler: Any) -> Any:
            if request.method == "GET" and request.path in {"/", "/index.html"}:
                query_hull = request.query.get("hull")
                if query_hull:
                    self.load_from_query(query_hull)
            if request.method == "POST" and request.path == "/paraview/":
                websocket_scheme = "wss" if request.scheme == "https" else "ws"
                return web.json_response(
                    {
                        "sessionURL": f"{websocket_scheme}://{request.host}/ws",
                        "secret": "wslink-secret",
                    }
                )
            if request.method == "GET" and request.path == "/favicon.ico":
                return web.Response(status=204)
            return await handler(request)

        aiohttp_app.middlewares.append(browser_request_middleware)
        aiohttp_app["kayakgen_browser_request_middleware_installed"] = True

    def _share_url(self) -> None:
        self.state.share_url = f"?hull={encode_hull_query(self._current_hull())}"
        self.state.share_status = SHARE_TOAST_COPY
        self.state.share_toast = True

    def _export_stl(self, part: str) -> None:
        from kayakgen.ui.web.controllers import stl_bytes_for_part

        data = stl_bytes_for_part(self._state_snapshot(), part)
        if hasattr(self.ctrl, "trigger"):
            self.ctrl.trigger("download_stl", part, data)

    def _export_hydro_json(self) -> None:
        data = json.dumps(
            evaluation_payload(self._state_snapshot()),
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        self.state.export_status = "Hydro JSON prepared from current local evaluation data."
        if hasattr(self.ctrl, "trigger"):
            self.ctrl.trigger("download_json", "kayak_hydro.json", data)

    def _reset(self) -> None:
        self.state.update(state_dict_from_hull(Hull()))
        self.state.target_speed_kt = 3.5
        self.state.class_preset = "custom"
        self._apply_slider_bounds("custom")
        self.state.analysis_tab = "analysis"
        self._refresh_current_hull_surface()

    def _load_comparison(self) -> None:
        payload = str(self.state.comparison_json or "")
        model = comparison_view_model_from_json(payload)
        self.state.comparison_status = model["status"]
        self.state.comparison_lines = model["lines"]
        self.state.comparison_candidate_options = model["candidate_options"]
        if model["candidate_options"]:
            self.state.selected_candidate_index = model["candidate_options"][0]
        self._refresh_high_angle_section(payload)

    def _refresh_high_angle_section(self, payload: str) -> None:
        view = web_high_angle_gz_view_model_from_json(payload)
        self.state.high_angle_gz_section_visible = bool(view["visible"])
        self.state.high_angle_gz_section_html = web_high_angle_gz_section_html(view)

    def _load_selected_candidate(self) -> None:
        try:
            updated = candidate_state_from_report_json(
                str(self.state.comparison_json or ""),
                self.state.selected_candidate_index,
                self._state_snapshot(),
            )
        except Exception as exc:
            self.state.comparison_status = f"Candidate reload failed: {exc}"
            return
        self.state.update({key: updated[key] for key in HULL_STATE_FIELDS if key in updated})
        self.state.class_preset = "custom"
        self._apply_slider_bounds("custom")
        self._refresh_current_hull_surface()
        self.state.comparison_status = (
            f"Applied sweep parameters for candidate {self.state.selected_candidate_index}"
        )

    def _cfd_request_payload(self) -> dict[str, Any]:
        return {
            "mesh_package_ref": str(self.state.cfd_mesh_package_ref or ""),
            "solver_profile": str(self.state.cfd_solver_profile or ""),
            "speed_mps": self.state.cfd_speed_mps,
            "hull_ref": self._current_hull().hash(),
        }

    def _set_cfd_error(self, exc: CfdWebError, title: str) -> None:
        self.state.cfd_status_lines = cfd_error_lines_from_payload(exc.payload, title=title)
        self.state.status_cfd = "failed"
        self._refresh_status_segments()

    def _prepare_cfd_job(self) -> None:
        try:
            payload = create_cfd_job_payload(self._cfd_request_payload(), self._cfd_store)
        except CfdWebError as exc:
            self._set_cfd_error(exc, "CFD job preparation rejected")
            return
        self.state.cfd_job_id = payload["job_id"]
        self.state.cfd_status_lines = cfd_status_lines_from_payload(payload)
        self.state.cfd_logs_lines = []
        self.state.cfd_raw_result_lines = []
        self._set_cfd_status_segment(payload)

    def _refresh_cfd_job(self) -> None:
        try:
            payload = cfd_job_status_payload(str(self.state.cfd_job_id or ""), self._cfd_store)
        except CfdWebError as exc:
            self._set_cfd_error(exc, "CFD status unavailable")
            return
        self.state.cfd_status_lines = cfd_status_lines_from_payload(payload)
        self._set_cfd_status_segment(payload)

    def _run_cfd_job(self) -> None:
        try:
            payload = run_cfd_job_payload(str(self.state.cfd_job_id or ""), self._cfd_store)
        except CfdWebError as exc:
            self._set_cfd_error(exc, "CFD run failed")
            return
        self.state.cfd_status_lines = cfd_status_lines_from_payload(payload)
        self._set_cfd_status_segment(payload)

    def _load_cfd_logs(self) -> None:
        try:
            payload = cfd_job_logs_payload(str(self.state.cfd_job_id or ""), self._cfd_store)
        except CfdWebError as exc:
            self.state.cfd_logs_lines = cfd_error_lines_from_payload(
                exc.payload,
                title="CFD logs unavailable",
            )
            return
        self.state.cfd_logs_lines = cfd_logs_lines_from_payload(payload)

    def _load_cfd_raw_result(self) -> None:
        try:
            payload = cfd_job_raw_result_payload(str(self.state.cfd_job_id or ""), self._cfd_store)
        except CfdWebError as exc:
            self.state.cfd_raw_result_lines = cfd_error_lines_from_payload(
                exc.payload,
                title="CFD raw artifact unavailable",
            )
            return
        self.state.cfd_raw_result_lines = cfd_raw_result_lines_from_payload(payload)

    # ----- generative-jobs panel -----

    def _submit_generative_job(self, kind: str) -> None:
        text = str(self.state.generative_spec_json or "").strip()
        if not text:
            self.state.generative_status = (
                "Paste a sweep or search spec JSON before submitting."
            )
            return
        try:
            spec_payload = json.loads(text)
        except ValueError as exc:
            self.state.generative_status = f"Spec is not valid JSON: {exc}"
            return
        try:
            payload = start_generative_job_payload(
                {"spec": spec_payload},
                self._generative_manager,
                job_kind=kind,  # type: ignore[arg-type]
            )
        except Exception as exc:  # noqa: BLE001 - surface a clean message
            self.state.generative_status = f"Submit failed: {exc}"
            return
        job_id = payload["job_id"]
        self.state.generative_job_id = job_id
        self.state.generative_status = (
            f"Submitted {kind} job {job_id}; state={payload['state']}."
        )
        self._refresh_generative_jobs()

    def _refresh_generative_jobs(self) -> None:
        listing = generative_job_list_payload(self._generative_manager)
        rows: list[str] = []
        for job in listing.get("jobs", []):
            rows.append(
                f"{job['job_id']}\t{job['job_kind']}\t{job['state']}\t"
                f"{job['realized_evaluations']}/{job['completed_count']}c/"
                f"{job['failed_count']}f"
            )
        if not rows:
            rows = ["(no generative jobs yet)"]
        self.state.generative_jobs_lines = rows

    def _cancel_generative_job(self) -> None:
        job_id = str(self.state.generative_job_id or "").strip()
        if not job_id:
            self.state.generative_status = "Enter a job id to cancel."
            return
        try:
            payload = cancel_generative_job_payload(
                self._generative_manager, job_id
            )
        except Exception as exc:  # noqa: BLE001
            self.state.generative_status = f"Cancel failed: {exc}"
            return
        self.state.generative_status = (
            f"Cancel requested for {payload['job_id']}; state={payload['state']}."
        )
        self._refresh_generative_jobs()

    def _resume_generative_job(self) -> None:
        job_id = str(self.state.generative_job_id or "").strip()
        if not job_id:
            self.state.generative_status = "Enter a job id to resume."
            return
        try:
            payload = resume_generative_job_payload(
                self._generative_manager, job_id
            )
        except Exception as exc:  # noqa: BLE001
            self.state.generative_status = f"Resume failed: {exc}"
            return
        self.state.generative_status = (
            f"Resumed {payload['job_id']}; state={payload['state']}."
        )
        self._refresh_generative_jobs()

    def _load_generative_log(self) -> None:
        job_id = str(self.state.generative_job_id or "").strip()
        if not job_id:
            self.state.generative_log_lines = ["(enter a job id)"]
            return
        try:
            payload = generative_job_log_payload(
                self._generative_manager, job_id, since_byte=0
            )
        except Exception as exc:  # noqa: BLE001
            self.state.generative_log_lines = [f"log unavailable: {exc}"]
            return
        log_text = payload.get("log", "")
        if not log_text.strip():
            self.state.generative_log_lines = ["(no log lines yet)"]
            return
        self.state.generative_log_lines = log_text.splitlines()[-200:]

    def _load_generative_frontier(self) -> None:
        job_id = str(self.state.generative_job_id or "").strip()
        if not job_id:
            self.state.generative_frontier_lines = ["(enter a job id)"]
            return
        try:
            payload = generative_job_frontier_payload(
                self._generative_manager, job_id
            )
        except Exception as exc:  # noqa: BLE001
            self.state.generative_frontier_lines = [f"frontier unavailable: {exc}"]
            return
        if not payload.get("frontier_available"):
            note = payload.get("note") or "frontier not available yet"
            self.state.generative_frontier_lines = [note]
            return
        rows: list[str] = []
        for row in payload.get("frontier", []):
            params = ", ".join(
                f"{k}={v}" for k, v in sorted((row.get("parameters") or {}).items())
            )
            rows.append(
                f"{row.get('candidate_key')}\t{row.get('status')}\t{params}"
            )
        self.state.generative_frontier_lines = rows or ["(empty frontier)"]

    def load_from_query(self, query: str) -> None:
        try:
            hull = decode_hull_query(query)
        except Exception:
            return
        self.state.update(state_dict_from_hull(hull))
        self.state.class_preset = "custom"
        self._apply_slider_bounds("custom")
        self._refresh_current_hull_surface()

    # ----- layout -----

    def _region_attrs(self, region: str) -> dict[str, str]:
        return {
            "id": LAYOUT_TEST_IDS[region],
            "data-testid": LAYOUT_TEST_IDS[region],
            "aria-label": f"{region} region",
            "classes": REGION_CLASSES[region],
        }

    def _build_layout(self) -> None:
        with SinglePageWithDrawerLayout(self.server) as layout:
            html_widgets.Style(ROOT_THEME_CSS)
            html_widgets.Style(PARAMETER_RAIL_CSS)
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
                        "position: absolute; left: -10000px; top: auto; "
                        "width: 1px; height: 1px; overflow: hidden;"
                    ),
                    **{
                        "data-testid": "share-url-state",
                        "aria-hidden": "true",
                        "tabindex": "-1",
                    },
                )

            with layout.drawer as drawer:
                drawer.width = 360
                with v3.VContainer(**self._region_attrs("params")):
                    v3.VCardTitle("Parameters", classes="kg-region-title")
                    with v3.VRadioGroup(
                        v_model=("class_preset",),
                        inline=True,
                        density="compact",
                        hide_details=True,
                        classes="kg-class-preset-radio",
                    ):
                        for preset in CLASS_PRESET_OPTIONS:
                            v3.VRadio(label=preset["label"], value=preset["value"])
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
                    v3.VChip(
                        "{{ validity_badge }}",
                        classes="kg-validity-badge",
                        size="small",
                        **{
                            "data-testid": "validity-badge",
                            "role": "status",
                            "aria-live": "polite",
                            "aria-label": ("validity_badge_aria_label",),
                        },
                    )

            with layout.content:
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
                                        "height: 520px; min-height: 480px; "
                                        "width: 100%;"
                                    ),
                                ):
                                    self.view = vtkw.VtkRemoteView(
                                        self._render_window,
                                        ref="view",
                                        classes="kg-vtk-viewport",
                                        style=(
                                            "height: 100%; min-height: 480px; "
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
                    v3.VBtn(
                        "Refresh Analysis",
                        click=self.ctrl.refresh_analysis,
                        density="compact",
                        classes="kg-review-action",
                    )
                    v3.VCardText(
                        "<pre>{{ analysis_lines.join('\\n') }}</pre>",
                        classes="font-mono text-caption mt-2",
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
                v3.VCardTitle(HIGH_ANGLE_GZ_HEADING, classes="kg-unavailable-heading")
                v3.VCardText(HIGH_ANGLE_GZ_COPY)
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
                    "<pre>{{ mesh_hull_diagnostics_lines.join('\\n') }}</pre>",
                    classes="font-mono text-caption",
                    html=True,
                )
            with v3.VCard(classes="kg-review-card kg-mesh-card mt-2"):
                v3.VCardTitle("Deck diagnostics")
                v3.VCardText(
                    "<pre>{{ mesh_deck_diagnostics_lines.join('\\n') }}</pre>",
                    classes="font-mono text-caption",
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
                v3.VChip(
                    "{{ mesh_readiness_level }}",
                    size="small",
                    classes="kg-readiness-chip",
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
                    "Submit a sweep or search spec JSON. Jobs run server-local "
                    "in the same process; no hosted worker is running.",
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
                    v3.VTextarea(
                        v_model=("generative_spec_json",),
                        label="Spec JSON (sweep or search)",
                        rows=8,
                        auto_grow=True,
                        density="compact",
                        **{"data-testid": "generative-spec-textarea"},
                    )
                    v3.VBtn(
                        "Submit Search",
                        click=self.ctrl.submit_generative_search,
                        density="compact",
                        classes="mr-2",
                        **{"data-testid": "submit-generative-search"},
                    )
                    v3.VBtn(
                        "Submit Sweep",
                        click=self.ctrl.submit_generative_sweep,
                        density="compact",
                        classes="mr-2",
                        **{"data-testid": "submit-generative-sweep"},
                    )
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
                        "<pre>{{ generative_jobs_lines.join('\\n') }}</pre>",
                        classes="font-mono text-caption mt-2",
                        html=True,
                    )
                    v3.VCardText(
                        "<pre>{{ generative_log_lines.join('\\n') }}</pre>",
                        classes="font-mono text-caption",
                        html=True,
                    )
                    v3.VCardText(
                        "<pre>{{ generative_frontier_lines.join('\\n') }}</pre>",
                        classes="font-mono text-caption",
                        html=True,
                    )

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


def create_app(
    initial_hull: Hull | None = None,
    server: Any | None = None,
    initial_query: str | None = None,
) -> KayakgenApp:
    """Factory: build and return a configured :class:`KayakgenApp`."""
    return KayakgenApp(server=server, initial_hull=initial_hull, initial_query=initial_query)
