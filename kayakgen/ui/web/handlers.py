"""Handler methods for the kayakgen web UI (state refresh, exports, CFD).

Extracted verbatim from ``kayakgen.ui.web.app`` (refactoring campaign
kayakgen-smoke-1, slice S5). ``KayakgenApp`` composes ``HandlersMixin``.
"""

from __future__ import annotations

import json
from typing import Any

from kayakgen.model.hull import Hull
from kayakgen.ui.web.controllers import (
    CfdWebError,
    candidate_state_from_report_json,
    cfd_error_lines_from_payload,
    cfd_job_logs_payload,
    cfd_job_raw_result_payload,
    cfd_job_status_payload,
    cfd_logs_lines_from_payload,
    cfd_raw_result_lines_from_payload,
    cfd_status_lines_from_payload,
    clamp_beam_wl_state,
    comparison_view_model_from_json,
    create_cfd_job_payload,
    evaluation_payload,
    evaluation_summary,
    hull_from_web_state,
    hydro_lines_from_state,
    hydro_rows_from_state,
    mesh_diagnostics_lines_from_state,
    mesh_diagnostics_rows_from_state,
    mesh_package_view_model,
    metrics_from_state,
    register_rest_routes,
    resistance_table_view_model,
    run_cfd_job_payload,
    validation_error_payload,
    validity_badge_from_state,
)
from kayakgen.ui.web.presentation import (
    INVALID_HULL_STATE_COPY,
    MESH_PACKAGE_READINESS_COPY,
    MESH_PROFILE_LABEL,
    REVIEW_TABS,
    SHARE_TOAST_COPY,
    STATUS_SEGMENTS,
    _pre_html,
    _resistance_table_html,
    validity_badge_title_for,
)
from kayakgen.ui.web.read_models import (
    web_high_angle_gz_section_html,
    web_high_angle_gz_view_model_from_json,
)
from kayakgen.ui.web.state import (
    HULL_STATE_FIELDS,
    MESH_PACKAGE_REF_ALIASES,
    STATE_SNAPSHOT_KEYS,
    encode_hull_query,
    state_dict_from_hull,
)


class HandlersMixin:
    """Handler methods of :class:`~kayakgen.ui.web.app.KayakgenApp`."""

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
            self.state.invalid_hull_state_visible = True
            self.state.invalid_hull_state_lines = [INVALID_HULL_STATE_COPY, *messages]
            self.state.advisory_count = 0
            self.state.advisory_lines = ["Advisories unavailable for invalid hull state."]
            self._refresh_status_segments()
            return
        self.state.invalid_hull_state_visible = False
        self.state.invalid_hull_state_lines = []
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
            self.state.hydro_table_rows = hydro_rows_from_state(state)
        except Exception as exc:
            payload = validation_error_payload(exc)
            details = payload.get("details", [])
            messages = [f"{d['field']}: {d['message']}" for d in details]
            self.state.analysis_lines = ["Analysis unavailable", *messages]
            self.state.hydro_table_rows = [{"label": "Error", "value": m} for m in messages]
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
            self.state.mesh_hull_diagnostic_rows = mesh_diagnostics_rows_from_state(
                state,
                part="hull",
            )
            self.state.mesh_deck_diagnostic_rows = mesh_diagnostics_rows_from_state(
                state,
                part="deck",
            )
        except Exception as exc:
            payload = validation_error_payload(exc)
            details = payload.get("details", [])
            messages = [f"{d['field']}: {d['message']}" for d in details]
            self.state.mesh_hull_diagnostics_lines = ["Hull diagnostics unavailable", *messages]
            self.state.mesh_deck_diagnostics_lines = ["Deck diagnostics unavailable", *messages]
            self.state.mesh_hull_diagnostic_rows = [
                {"label": "Error", "value": m} for m in messages
            ]
            self.state.mesh_deck_diagnostic_rows = [
                {"label": "Error", "value": m} for m in messages
            ]

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
        self.state.validity_badge_title = validity_badge_title_for(badge)

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
