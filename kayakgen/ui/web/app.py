"""Trame app factory for the kayakgen web frontend.

Importing this module requires the ``kayakgen[web]`` extras
(``trame``, ``trame-vuetify``, ``trame-vtk``, ``vtk``).
"""

from __future__ import annotations

from typing import Any

import vtk
from trame.app import get_server

from kayakgen.model.hull import Hull
from kayakgen.ui import theme
from kayakgen.ui.web.controllers import (
    CFD_LOCAL_FILESYSTEM_NOTICE,
    CFD_RAW_RESULTS_WARNING,
    CfdWebStore,
    HullStore,
    class_preset_read_model,
    clamp_beam_wl_state,
    cfd_profile_names,
    cfd_status_lines_from_payload,
)
from kayakgen.services.generative_jobs import SubprocessGenerativeJobManager
from kayakgen.ui.web.generate_spec_form import (
    initialize_form_state,
)
from kayakgen.ui.web.generate_state_listener import install_generate_state_listener
from kayakgen.ui.web.presentation import (
    SLIDER_DEFS,  # noqa: F401
    PARAMETER_GROUPS,  # noqa: F401
    CLASS_PRESETS,  # noqa: F401
    CLASS_PRESET_OPTIONS,  # noqa: F401
    EXPORT_MENU_ROWS,  # noqa: F401
    REVIEW_TABS,  # noqa: F401
    STATUS_SEGMENTS,  # noqa: F401
    LAYOUT_TEST_IDS,  # noqa: F401
    REGION_CLASSES,  # noqa: F401
    RESPONSIVE_CLASS_HOOKS,  # noqa: F401
    ROOT_THEME_CSS,  # noqa: F401
    WORKSPACE_SHELL_CSS,  # noqa: F401
    PARAMETER_RAIL_CSS,  # noqa: F401
    RAW_COMPARATIVE_CAPTION,  # noqa: F401
    RESISTANCE_DETAIL_COPY,  # noqa: F401
    HIGH_ANGLE_GZ_HEADING,  # noqa: F401
    HIGH_ANGLE_GZ_COPY,  # noqa: F401
    MESH_PACKAGE_READINESS_HEADING,  # noqa: F401
    MESH_PROFILE_LABEL,  # noqa: F401
    MESH_PROFILE_ID,  # noqa: F401
    MESH_READINESS_LEVEL,  # noqa: F401
    MESH_PACKAGE_READINESS_COPY,  # noqa: F401
    WATERTIGHT_DISABLED_COPY,  # noqa: F401
    CFD_ARTIFACT_STRAPLINE,  # noqa: F401
    SHARE_TOAST_COPY,  # noqa: F401
    GENERATIVE_JOBS_EMPTY_COPY,  # noqa: F401
    GENERATIVE_JOBS_RUNNING_COPY,  # noqa: F401
    GENERATIVE_JOBS_FAILED_COPY,  # noqa: F401
    GENERATIVE_JOBS_CANCELLED_COPY,  # noqa: F401
    GENERATIVE_JOBS_RESUMABLE_COPY,  # noqa: F401
    FRONTIER_LOADING_COPY,  # noqa: F401
    FRONTIER_RENDERED_COPY,  # noqa: F401
    INVALID_HULL_STATE_COPY,  # noqa: F401
    PERSISTENT_COPY,  # noqa: F401
    _SLIDER_BY_KEY,  # noqa: F401
    VALIDITY_BADGE_TITLE_SUB_TOURING,  # noqa: F401
    VALIDITY_BADGE_TITLE_BEYOND_ELITE,  # noqa: F401
    validity_badge_title_for,  # noqa: F401
    COMPARISON_TOGGLE_LIVE_FRONTIER_HELP,  # noqa: F401
    COMPARISON_TOGGLE_IMPORTED_REPORT_HELP,  # noqa: F401
    MESH_NO_PACKAGE_CHIP_TITLE,  # noqa: F401
    MESH_LIVE_READINESS_CHIP_TITLE,  # noqa: F401
    _param_row_raw_attrs,  # noqa: F401
    _pre_html,  # noqa: F401
    _resistance_table_html,  # noqa: F401
    _generative_job_state_flags,  # noqa: F401
)
from kayakgen.ui.web.generate_panel import (
    GeneratePanelMixin,
    _default_generative_jobs_root_for_app,
)
from kayakgen.ui.web.handlers import HandlersMixin
from kayakgen.ui.web.layout import LayoutMixin
from kayakgen.ui.web.scene import (
    SceneMixin,
    _build_polydata,  # noqa: F401
    _make_actor,  # noqa: F401
)
from kayakgen.ui.web.state import (
    HULL_STATE_FIELDS,
    STATE_SNAPSHOT_KEYS,  # noqa: F401
    hull_from_query_string,
    state_dict_from_hull,
)


class KayakgenApp(HandlersMixin, GeneratePanelMixin, LayoutMixin, SceneMixin):
    """Trame app driving the kayakgen web UI."""

    def __init__(
        self,
        server: Any | None = None,
        initial_hull: Hull | None = None,
        initial_query: str | None = None,
        generative_manager: Any | None = None,
    ) -> None:
        self.server = server if server is not None else get_server(client_type="vue3")
        self.state = self.server.state
        self.ctrl = self.server.controller
        self.state.workspace_style_html = (
            f"<style>{ROOT_THEME_CSS}</style><style>{PARAMETER_RAIL_CSS}</style>"
        )

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
        self.state.validity_badge_title = validity_badge_title_for(
            "Custom (L/B_wl=0.0)"
        )
        self.state.invalid_hull_state_visible = False
        self.state.invalid_hull_state_lines = []
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
        self.state.mesh_hull_diagnostic_rows = []
        self.state.mesh_deck_diagnostic_rows = []
        self.state.mesh_package_warning_lines = []
        self.state.mesh_package_status = "No mesh package selected."
        self.state.resistance_table_rows = []
        self.state.resistance_table_html = ""
        self.state.resistance_table_caption = RESISTANCE_DETAIL_COPY
        self.state.resistance_claim_state = "uncalibrated_comparative"
        self.state.advisory_count = 0
        self.state.advisory_lines = ["No design advisories for current hull."]
        self.state.hydro_table_rows = []
        self.state.comparison_source = "live_frontier"
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
        if generative_manager is None:
            self._generative_manager = SubprocessGenerativeJobManager(
                jobs_root=_default_generative_jobs_root_for_app(),
            )
        else:
            self._generative_manager = generative_manager
        self.state.generative_jobs_root = str(self._generative_manager.jobs_root)
        self.state.generative_spec_json = ""
        self.state.generative_job_id = ""
        self.state.generative_status = (
            "Paste a sweep or search spec JSON and submit to start a new job."
        )
        self.state.generative_jobs_lines = []
        self.state.generative_jobs_table_rows = []
        self.state.generative_jobs_empty = True
        self.state.generative_jobs_running = False
        self.state.generative_jobs_failed = False
        self.state.generative_jobs_cancelled = False
        self.state.generative_jobs_resumable = False
        self.state.generative_jobs_failed_kind = ""
        self.state.generative_log_lines = []
        self.state.generative_frontier_lines = []
        self.state.generative_frontier_loading = False
        self.state.generative_frontier_rendered = False
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
        self.ctrl.apply_form_to_json = lambda: self._apply_generative_form_to_json()
        self.ctrl.refresh_generative_jobs = lambda: self._refresh_generative_jobs()
        self.ctrl.cancel_generative_job = lambda: self._cancel_generative_job()
        self.ctrl.resume_generative_job = lambda: self._resume_generative_job()
        self.ctrl.load_generative_log = lambda: self._load_generative_log()
        self.ctrl.load_generative_frontier = lambda: self._load_generative_frontier()
        self.ctrl.refresh_generative_frontier_view = (
            lambda: self._refresh_generative_frontier_view()
        )
        self.ctrl.fork_generative_job = (
            lambda job_id, new_seed=None: self._fork_generative_job(job_id, new_seed)
        )
        self.ctrl.load_generative_candidate = (
            lambda candidate_payload: self._load_generative_candidate(candidate_payload)
        )
        self.ctrl.undo_generative_handoff = lambda: self._undo_generative_handoff()
        self.ctrl.focus_review_tab = lambda tab: self._focus_review_tab(tab)
        self.ctrl.on_server_bind.add(self._on_server_bind)
        install_generate_state_listener(self)

        self._wire_state_listeners()
        initialize_form_state(self)
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


def create_app(
    initial_hull: Hull | None = None,
    server: Any | None = None,
    initial_query: str | None = None,
    generative_manager: Any | None = None,
) -> KayakgenApp:
    """Factory: build and return a configured :class:`KayakgenApp`.

    ``generative_manager`` (RFC 0057) may be supplied to override the
    default subprocess generative-job manager; tests may pass an in-process
    manager for synchronous joins.
    """
    return KayakgenApp(
        server=server,
        initial_hull=initial_hull,
        initial_query=initial_query,
        generative_manager=generative_manager,
    )
