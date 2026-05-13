"""Trame app factory for the kayakgen web frontend.

Importing this module requires the ``kayakgen[web]`` extras
(``trame``, ``trame-vuetify``, ``trame-vtk``, ``vtk``).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import vtk
from trame.app import get_server
from trame.ui.vuetify3 import SinglePageWithDrawerLayout
from trame.widgets import vtk as vtkw
from trame.widgets import vuetify3 as v3

from kayakgen.model.hull import Hull
from kayakgen.ui.web.controllers import (
    HullStore,
    analysis_lines_from_state,
    candidate_state_from_report_json,
    clamp_beam_wl_state,
    comparison_view_model_from_json,
    hull_from_web_state,
    metrics_from_state,
    register_rest_routes,
    validation_error_payload,
)
from kayakgen.ui.web.state import (
    HULL_STATE_FIELDS,
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
    ("target_speed_kt", "Target Speed (kt)", 1.0, 6.0, 0.1),
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


def _make_actor(poly: vtk.vtkPolyData, rgb: tuple[float, float, float], opacity: float) -> vtk.vtkActor:
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*rgb)
    actor.GetProperty().SetOpacity(opacity)
    actor.GetProperty().SetInterpolationToPhong()
    return actor


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
        self.state.metrics_lines = []
        self.state.analysis_tab = "analysis"
        self.state.analysis_lines = []
        self.state.comparison_json = ""
        self.state.comparison_status = "Paste a comparison report JSON to inspect candidates."
        self.state.comparison_lines = []
        self.state.comparison_candidate_options = []
        self.state.selected_candidate_index = 0

        self._renderer = vtk.vtkRenderer()
        self._renderer.SetBackground(0.10, 0.10, 0.18)
        self._render_window = vtk.vtkRenderWindow()
        self._render_window.AddRenderer(self._renderer)
        self._render_window.SetOffScreenRendering(1)
        self._interactor = vtk.vtkRenderWindowInteractor()
        self._interactor.SetRenderWindow(self._render_window)

        self._hull_actor: vtk.vtkActor | None = None
        self._deck_actor: vtk.vtkActor | None = None
        self._hull_store = HullStore()
        self._rebuild_scene(hull)

        self.ctrl.export_stl = lambda part: self._export_stl(part)
        self.ctrl.share_url = lambda: self._share_url()
        self.ctrl.reset = lambda: self._reset()
        self.ctrl.refresh_analysis = lambda: self._refresh_analysis()
        self.ctrl.load_comparison = lambda: self._load_comparison()
        self.ctrl.load_candidate = lambda: self._load_selected_candidate()
        self.ctrl.on_server_bind.add(
            lambda ws_server: register_rest_routes(ws_server.app, self._hull_store)
        )

        self._wire_state_listeners()
        self._build_layout()
        self._refresh_metrics()
        self._refresh_analysis()

    # ----- 3D scene -----

    def _rebuild_scene(self, hull: Hull) -> None:
        if self._hull_actor is not None:
            self._renderer.RemoveActor(self._hull_actor)
        if self._deck_actor is not None:
            self._renderer.RemoveActor(self._deck_actor)

        geom = hull.to_geometry()
        v_hull, f_hull = geom.mesh("hull", stations=80)
        v_deck, f_deck = geom.mesh("deck", stations=80)

        self._hull_actor = _make_actor(_build_polydata(v_hull, f_hull), (0.227, 0.494, 0.749), 1.0)
        self._deck_actor = _make_actor(_build_polydata(v_deck, f_deck), (0.298, 0.686, 0.431), 0.85)
        self._renderer.AddActor(self._hull_actor)
        self._renderer.AddActor(self._deck_actor)
        self._renderer.ResetCamera()
        self._render_window.Render()

    # ----- handlers -----

    def _current_hull(self) -> Hull:
        return hull_from_web_state(dict(self.state.to_dict()))

    def _refresh_metrics(self) -> None:
        try:
            m = metrics_from_state(dict(self.state.to_dict()))
        except Exception as exc:  # validation errors from Pydantic
            payload = validation_error_payload(exc)
            details = payload.get("details", [])
            messages = [f"{d['field']}: {d['message']}" for d in details]
            self.state.metrics_lines = ["Invalid hull state", *messages]
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

    def _refresh_analysis(self) -> None:
        try:
            self.state.analysis_lines = analysis_lines_from_state(dict(self.state.to_dict()))
        except Exception as exc:
            payload = validation_error_payload(exc)
            details = payload.get("details", [])
            messages = [f"{d['field']}: {d['message']}" for d in details]
            self.state.analysis_lines = ["Analysis unavailable", *messages]

    def _on_param_change(self, **_kwargs: Any) -> None:
        normalized = clamp_beam_wl_state(dict(self.state.to_dict()))
        if normalized.get("beam_wl_m") != self.state.beam_wl_m:
            self.state.beam_wl_m = normalized["beam_wl_m"]
            return
        try:
            hull = self._current_hull()
        except Exception:
            self._refresh_metrics()
            self._refresh_analysis()
            return
        self._rebuild_scene(hull)
        self._refresh_metrics()
        self._refresh_analysis()
        if hasattr(self, "view") and self.view is not None:
            self.view.update()

    def _wire_state_listeners(self) -> None:
        watched = list(HULL_STATE_FIELDS) + ["target_speed_kt"]
        self.state.change(*watched)(self._on_param_change)

    def _share_url(self) -> None:
        self.state.share_url = f"?hull={encode_hull_query(self._current_hull())}"

    def _export_stl(self, part: str) -> None:
        from kayakgen.ui.web.controllers import stl_bytes_for_part

        data = stl_bytes_for_part(dict(self.state.to_dict()), part)
        if hasattr(self.ctrl, "trigger"):
            self.ctrl.trigger("download_stl", part, data)

    def _reset(self) -> None:
        self.state.update(state_dict_from_hull(Hull()))
        self.state.target_speed_kt = 3.5
        self._refresh_analysis()

    def _load_comparison(self) -> None:
        model = comparison_view_model_from_json(str(self.state.comparison_json or ""))
        self.state.comparison_status = model["status"]
        self.state.comparison_lines = model["lines"]
        self.state.comparison_candidate_options = model["candidate_options"]
        if model["candidate_options"]:
            self.state.selected_candidate_index = model["candidate_options"][0]

    def _load_selected_candidate(self) -> None:
        try:
            updated = candidate_state_from_report_json(
                str(self.state.comparison_json or ""),
                self.state.selected_candidate_index,
                dict(self.state.to_dict()),
            )
        except Exception as exc:
            self.state.comparison_status = f"Candidate reload failed: {exc}"
            return
        self.state.update({key: updated[key] for key in HULL_STATE_FIELDS if key in updated})
        hull = hull_from_web_state(updated)
        self._rebuild_scene(hull)
        self._refresh_metrics()
        self._refresh_analysis()
        if hasattr(self, "view") and self.view is not None:
            self.view.update()
        self.state.comparison_status = (
            f"Applied sweep parameters for candidate {self.state.selected_candidate_index}"
        )

    def load_from_query(self, query: str) -> None:
        try:
            hull = decode_hull_query(query)
        except Exception:
            return
        self.state.update(state_dict_from_hull(hull))
        self._rebuild_scene(hull)
        self._refresh_metrics()
        self._refresh_analysis()

    # ----- layout -----

    def _build_layout(self) -> None:
        with SinglePageWithDrawerLayout(self.server) as layout:
            layout.title.set_text("kayakgen")

            with layout.toolbar:
                v3.VSpacer()
                v3.VBtn("Reset", click=self.ctrl.reset)
                v3.VBtn("Share", click=self.ctrl.share_url)
                v3.VBtn("Export Hull STL", click=lambda: self.ctrl.export_stl("hull"))
                v3.VBtn("Export Deck STL", click=lambda: self.ctrl.export_stl("deck"))

            with layout.drawer as drawer:
                drawer.width = 360
                with v3.VContainer():
                    for key, label, vmin, vmax, step in SLIDER_DEFS:
                        v3.VSlider(
                            v_model=(key,),
                            label=label,
                            min=vmin,
                            max=vmax,
                            step=step,
                            thumb_label="always",
                            density="compact",
                            classes="mt-2",
                        )
                    v3.VDivider()
                    v3.VTextField(
                        v_model=("share_url",),
                        label="Shareable URL",
                        readonly=True,
                        density="compact",
                        classes="mt-2",
                    )
                    with v3.VCard(classes="mt-3"):
                        v3.VCardTitle("Metrics")
                        v3.VCardText(
                            "<pre>{{ metrics_lines.join('\\n') }}</pre>",
                            classes="font-mono text-caption",
                            html=True,
                        )

            with layout.content:
                with v3.VContainer(fluid=True, classes="fill-height pa-0"):
                    self.view = vtkw.VtkRemoteView(self._render_window, ref="view")
                    with v3.VCard(classes="ma-2"):
                        with v3.VTabs(v_model=("analysis_tab",)):
                            v3.VTab("Analysis", value="analysis")
                            v3.VTab("Comparison", value="comparison")
                        with v3.VWindow(v_model=("analysis_tab",)):
                            with v3.VWindowItem(value="analysis"):
                                with v3.VCardText():
                                    v3.VBtn(
                                        "Refresh Analysis",
                                        click=self.ctrl.refresh_analysis,
                                        density="compact",
                                    )
                                    v3.VCardText(
                                        "<pre>{{ analysis_lines.join('\\n') }}</pre>",
                                        classes="font-mono text-caption mt-2",
                                        html=True,
                                    )
                            with v3.VWindowItem(value="comparison"):
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


def create_app(
    initial_hull: Hull | None = None,
    server: Any | None = None,
    initial_query: str | None = None,
) -> KayakgenApp:
    """Factory: build and return a configured :class:`KayakgenApp`."""
    return KayakgenApp(server=server, initial_hull=initial_hull, initial_query=initial_query)
