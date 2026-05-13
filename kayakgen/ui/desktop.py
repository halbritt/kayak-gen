"""Matplotlib + PyQt6 desktop GUI for kayakgen.

Refactor of the legacy ``gui.py`` onto the new package boundary
(RFC 0007 step 7). Two changes from the legacy version:

- The cross-section, sheer plan, and plan view now consume the public
  geometry accessors on :class:`HullGeometry` (``section``,
  ``waterplane``, ``keel_line``, ``deck_centreline``) instead of
  reaching into ``_get_area_fraction`` / ``_get_deck_height_scaling`` /
  ``_get_slice_points``.
- The metrics panel is sourced from
  :func:`kayakgen.eval.hydrostatics.evaluate` — a single integrated
  truth value — rather than the prior formula envelope.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("qtagg")

import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
import numpy as np
from matplotlib.gridspec import GridSpec
from PyQt6.QtCore import QTimer

from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.resistance import KNOTS_TO_MS, evaluate_resistance
from kayakgen.model.advisory import design_advisory
from kayakgen.model.classes import KayakClass, list_classes
from kayakgen.model.hull import Hull
from kayakgen.ui import theme
from kayakgen.ui.gui_params import GUI_TO_HULL as _GUI_TO_HULL
from kayakgen.ui.gui_params import hull_from_gui_params as _hull_from_gui_params

matplotlib.rcParams.update(theme.matplotlib_rc_params())


PLOT_COLORS = {
    "hull": theme.PLOT_PALETTE["hull"],
    "deck": theme.PLOT_PALETTE["deck"],
    "focus": theme.PLOT_PALETTE["station"],
    "waterline": theme.COLORS_LIGHT["surface-viewport-grid"],
    "primary_button": theme.COLORS_LIGHT["brand-primary"],
    "primary_button_hover": theme.COLORS_LIGHT["brand-primary-hover"],
    "neutral_button": theme.COLORS_LIGHT["button-neutral"],
    "neutral_button_hover": theme.COLORS_LIGHT["button-neutral-hover"],
    "dark_button": theme.COLORS_LIGHT["button-strong"],
    "dark_button_hover": theme.COLORS_LIGHT["button-strong-hover"],
    "button_text": theme.COLORS_LIGHT["text-inverse"],
}

STATUS_SEGMENTS = (
    "package: open-wetted-surface",
    "readiness: cfd_surface_candidate",
    "resistance: uncalibrated_comparative",
    "cfd: not_prepared",
)


class KayakGUI:
    SLIDERS = [
        ("length", "Length (m)", 2.0, 6.5),
        ("beam", "Beam OA (m)", 0.30, 0.90),
        ("beam_wl", "Beam WL (m)", 0.30, 0.90),
        ("draft", "Draft (m)", 0.05, 0.25),
        ("deck_height", "Deck Height (m)", 0.15, 0.40),
        ("Cp", "Prismatic Coeff", 0.45, 0.70),
        ("Cm", "Midship Cm", 0.65, 0.95),
        ("deck_flatness", "Deck Flatness", 2.0, 16.0),
        ("center_box_ratio", "Parallel Mid-Body", 0.10, 0.60),
        ("bow_rake", "Bow Rake (1=raked)", 0.0, 1.0),
        ("stern_rake", "Stern Rake (1=raked)", 0.0, 1.0),
        ("target_speed_kt", "Target Speed (kt)", 1.0, 6.0),
    ]

    DEFAULTS = dict(
        length=4.5,
        beam=0.55,
        beam_wl=0.55,
        draft=0.12,
        deck_height=0.23,
        Cp=0.55,
        Cm=0.85,
        deck_flatness=8.0,
        center_box_ratio=0.33,
        bow_rake=1.0,
        stern_rake=1.0,
        target_speed_kt=3.5,
    )

    GLOBAL_RANGES = {key: (vmin, vmax) for key, _label, vmin, vmax in SLIDERS}
    SLIDER_STEPS = {"Cm": 0.005}

    # target_speed_kt is a viewing parameter, not a Hull field.
    _NON_HULL_GUI_KEYS = ("target_speed_kt",)

    def __init__(self, hull: Hull | None = None) -> None:
        self.params = dict(self.DEFAULTS)
        if hull is not None:
            self.params.update(
                {
                    gui_key: getattr(hull, hull_key)
                    for gui_key, hull_key in _GUI_TO_HULL.items()
                }
            )

        self.fig = plt.figure(figsize=(16, 9))
        self.fig.suptitle("Kayak Generator", fontsize=14, fontweight="bold")

        gs = GridSpec(
            3,
            1,
            figure=self.fig,
            left=0.38,
            right=0.97,
            top=0.93,
            bottom=0.13,
            hspace=0.45,
            height_ratios=[2, 1, 1],
        )
        self.ax_section = self.fig.add_subplot(gs[0])
        self.ax_profile = self.fig.add_subplot(gs[1])
        self.ax_plan = self.fig.add_subplot(gs[2], sharex=self.ax_profile)

        self._active_class_name = "custom"
        self._applying_class = False
        self._build_sliders()
        self._last_slider_key = list(self.sliders.keys())[0]
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)
        for key, s in self.sliders.items():
            s.on_changed(lambda _v, k=key: self._track_slider(k))

        self._pv_window = None
        self.station_x = 0.0
        self._3d_timer = QTimer()
        self._3d_timer.setSingleShot(True)
        self._3d_timer.setInterval(80)
        self._3d_timer.timeout.connect(self._flush_3d)

        self._build_button()
        self._build_class_selector()
        self.update_plots()
        self._refresh_metrics()
        plt.show()

    def _build_class_selector(self) -> None:
        """Radio buttons for class presets (RFC 0006 §4)."""
        labels = [kc.label for kc in list_classes()] + ["Custom"]
        self._class_names = [kc.name for kc in list_classes()] + ["custom"]
        ax = self.fig.add_axes([0.05, 0.330, 0.26, 0.110])
        ax.set_title("Class preset", fontsize=8, loc="left")
        self.class_radio = widgets.RadioButtons(ax, labels, active=len(labels) - 1)
        for txt in self.class_radio.labels:
            txt.set_fontsize(7)
        self.class_radio.on_clicked(self._on_class_select)

    def _on_class_select(self, label: str) -> None:
        idx = next(
            (i for i, kc in enumerate(list_classes()) if kc.label == label),
            None,
        )
        if idx is None:
            self._active_class_name = "custom"
            self._apply_slider_ranges(None)
            self._refresh_metrics()
            return
        kc = list_classes()[idx]
        self._active_class_name = kc.name
        seeds = {
            "length": kc.length_m.default,
            "beam": kc.beam_oa_m.default,
            "beam_wl": kc.beam_wl_m.default,
            "draft": kc.draft_m.default,
            "Cp": kc.Cp.default,
        }
        self._applying_class = True
        self._apply_slider_ranges(kc)
        # Setting slider values in turn fires _on_change, which rebuilds
        # plots and 3D once per call. Cheap because we set five values.
        for key, val in seeds.items():
            slider = self.sliders.get(key)
            if slider is not None:
                slider.set_val(val)
        self._applying_class = False
        self._refresh_metrics()

    def _apply_slider_ranges(self, kc: KayakClass | None) -> None:
        ranges = dict(self.GLOBAL_RANGES)
        if kc is not None:
            ranges.update(
                {
                    "length": (kc.length_m.min, kc.length_m.max),
                    "beam": (kc.beam_oa_m.min, kc.beam_oa_m.max),
                    "beam_wl": (kc.beam_wl_m.min, kc.beam_wl_m.max),
                    "draft": (kc.draft_m.min, kc.draft_m.max),
                    "Cp": (kc.Cp.min, kc.Cp.max),
                }
            )
        for key, (vmin, vmax) in ranges.items():
            slider = self.sliders.get(key)
            if slider is None:
                continue
            slider.valmin = vmin
            slider.valmax = vmax
            slider.ax.set_xlim(vmin, vmax)

    def _build_sliders(self) -> None:
        n = len(self.SLIDERS)
        top_start, bot_end = 0.93, 0.46
        step = (top_start - bot_end) / n

        self.sliders: dict[str, widgets.Slider] = {}
        for i, (key, label, vmin, vmax) in enumerate(self.SLIDERS):
            y = top_start - (i + 0.5) * step - 0.015
            ax = self.fig.add_axes([0.07, y, 0.26, 0.018])
            kwargs = {}
            if key in self.SLIDER_STEPS:
                kwargs["valstep"] = self.SLIDER_STEPS[key]
            s = widgets.Slider(
                ax, label, vmin, vmax, valinit=self.params[key], **kwargs
            )
            s.label.set_fontsize(6.5)
            s.label.set_position((0.5, -1.8))
            s.label.set_horizontalalignment("center")
            s.on_changed(self._on_change)
            self.sliders[key] = s

    def _build_button(self) -> None:
        ax_btn = self.fig.add_axes([0.05, 0.205, 0.12, 0.045])
        self.btn = widgets.Button(
            ax_btn,
            "Export STLs",
            color=PLOT_COLORS["primary_button"],
            hovercolor=PLOT_COLORS["primary_button_hover"],
        )
        self.btn.label.set_color(PLOT_COLORS["button_text"])
        self.btn.on_clicked(self._on_generate)

        ax_rst = self.fig.add_axes([0.19, 0.205, 0.12, 0.045])
        self.btn_reset = widgets.Button(
            ax_rst,
            "Reset",
            color=PLOT_COLORS["neutral_button"],
            hovercolor=PLOT_COLORS["neutral_button_hover"],
        )
        self.btn_reset.on_clicked(self._on_reset)

        ax_3d = self.fig.add_axes([0.05, 0.255, 0.26, 0.045])
        self.btn_3d = widgets.Button(
            ax_3d,
            "3D View",
            color=PLOT_COLORS["dark_button"],
            hovercolor=PLOT_COLORS["dark_button_hover"],
        )
        self.btn_3d.label.set_color(PLOT_COLORS["button_text"])
        self.btn_3d.on_clicked(self._on_open_3d)

        self.ax_status = self.fig.add_axes([0.05, 0.130, 0.26, 0.070])
        self.ax_status.axis("off")
        self.status = self.ax_status.text(
            0.0,
            1.0,
            self._status_segments_block(),
            ha="left",
            va="top",
            transform=self.ax_status.transAxes,
            fontsize=6.2,
            fontfamily="monospace",
        )

        self.ax_metrics = self.fig.add_axes([0.05, 0.020, 0.26, 0.100])
        self.ax_metrics.axis("off")
        self.metrics_text = self.ax_metrics.text(
            0.0,
            1.0,
            "",
            ha="left",
            va="top",
            transform=self.ax_metrics.transAxes,
            fontsize=7.5,
            fontfamily="monospace",
        )

        half_L = self.params["length"] / 2
        self.ax_station = self.fig.add_axes([0.38, 0.04, 0.59, 0.025])
        self.station_slider = widgets.Slider(
            self.ax_station, "Station X (m)", -half_L, half_L, valinit=0.0
        )
        self.station_slider.on_changed(self._on_station_change)

    def _on_change(self, _val) -> None:
        if not self._applying_class and self._active_class_name != "custom":
            self._active_class_name = "custom"
            self._apply_slider_ranges(None)
        for key, s in self.sliders.items():
            self.params[key] = s.val
        # beam_wl must not exceed beam_oa: clamp live, never the other way.
        if self.params["beam_wl"] > self.params["beam"]:
            self.params["beam_wl"] = self.params["beam"]
            self.sliders["beam_wl"].set_val(self.params["beam"])
            return  # the set_val above re-enters _on_change
        self.status.set_text(self._status_segments_block())
        self.update_plots()
        if self._pv_window is not None and self._pv_window.isVisible():
            self._3d_timer.start()
        self._refresh_metrics()
        half_L = self.params["length"] / 2
        self.station_slider.valmin = -half_L
        self.station_slider.valmax = half_L
        self.station_slider.ax.set_xlim(-half_L, half_L)
        self.station_x = float(np.clip(self.station_x, -half_L, half_L))
        self.station_slider.set_val(self.station_x)

    def _on_station_change(self, val) -> None:
        self.station_x = float(val)
        self.update_plots()

    def _on_reset(self, _event) -> None:
        for key, s in self.sliders.items():
            s.set_val(self.DEFAULTS[key])

    def _status_segments_text(self) -> str:
        return " · ".join(STATUS_SEGMENTS)

    def _status_segments_block(self) -> str:
        return "\n".join(STATUS_SEGMENTS)

    def _on_generate(self, _event) -> None:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            None, "Save kayak STLs", "kayak", "STL files (*.stl)"
        )
        if not path:
            return
        stem = path.removesuffix("_hull.stl").removesuffix(".stl")
        self.status.set_text("Exporting STLs…")
        self.fig.canvas.draw()
        geom = _hull_from_gui_params(self.params).to_geometry()
        geom.generate_stl("hull", f"{stem}_hull.stl")
        geom.generate_stl("deck", f"{stem}_deck.stl")
        self.status.set_text(self._status_segments_block())
        self.fig.canvas.draw()

    def _on_open_3d(self, _event) -> None:
        self.btn_3d.label.set_text("Opening…")
        self.fig.canvas.draw()
        from kayakgen.ui.pv_window import PyVistaWindow

        if self._pv_window is None or not self._pv_window.isVisible():
            self._pv_window = PyVistaWindow(self.params)
            self._pv_window.show()
        self.btn_3d.label.set_text("3D View")
        self.fig.canvas.draw()

    def _flush_3d(self) -> None:
        if self._pv_window is not None and self._pv_window.isVisible():
            self._pv_window.update_mesh(self.params)

    def _classify(self, hull: Hull) -> str:
        """Return a short label describing where this hull sits in the class envelope (RFC 0006)."""
        l_over_bwl = hull.length_m / (hull.beam_wl_m or hull.beam_oa_m)
        for kc in list_classes():
            if (
                kc.length_m.min <= hull.length_m <= kc.length_m.max
                and kc.beam_oa_m.min <= hull.beam_oa_m <= kc.beam_oa_m.max
                and kc.beam_wl_m.min <= (hull.beam_wl_m or hull.beam_oa_m) <= kc.beam_wl_m.max
            ):
                return kc.label
        if l_over_bwl < 8:
            return f"Custom — sub-touring (L/B_wl={l_over_bwl:.1f})"
        if l_over_bwl > 15:
            return f"Custom — beyond elite (L/B_wl={l_over_bwl:.1f})"
        return f"Custom (L/B_wl={l_over_bwl:.1f})"

    def _refresh_metrics(self) -> None:
        # Single source of truth: integrated hydrostatics on the same mesh
        # the STL exporter and CFD will see. Stations reduced from the
        # default 150 to 60 here so the per-slider call stays under ~30 ms.
        hull = _hull_from_gui_params(self.params)
        h = evaluate_hydrostatics(hull, stations=60)
        advisory = design_advisory(
            hull,
            cp=h.Cp_actual,
            displaced_mass_kg=h.displaced_mass_kg,
            selected_class=(
                self._active_class_name
                if self._active_class_name != "custom"
                else None
            ),
        )
        klass = self._classify(hull)
        if self._active_class_name != "custom":
            klass = f"{klass} preset"
        V_ms = self.params["target_speed_kt"] * KNOTS_TO_MS
        # Coarser station/depth/theta grids on the live path so the call
        # stays under ~30 ms per slider tick. RFC 0005 budgets <100 ms for
        # the full curve; this is a single-speed evaluation.
        r = evaluate_resistance(
            hull,
            V_ms,
            Sw=h.wetted_surface_m2,
            n_stations=40,
            n_depths=12,
            n_theta=20,
        )
        txt = (
            f"Class        {klass}\n"
            f"Displacement {h.displaced_mass_kg:6.1f} kg\n"
            f"Wetted surf  {h.wetted_surface_m2:6.3f} m²\n"
            f"Waterplane   {h.waterplane_area_m2:6.3f} m²\n"
            f"Cp / Cm      {h.Cp_actual:.3f} / {h.Cm_actual:.3f}\n"
            f"L/B_wl       {advisory.l_over_bwl:6.2f}\n"
            f"At {self.params['target_speed_kt']:.1f} kt (Fn {r['Fn']:.2f}):\n"
            f"  Viscous   {r['Rv_N']:6.1f} N\n"
            f"  Wave      {r['Rw_N']:6.1f} N\n"
            f"  Total     {r['Rt_N']:6.1f} N"
        )
        if advisory.warnings:
            txt += "\nAdvisory    " + "\n            ".join(advisory.warnings)
        self.metrics_text.set_text(txt)

    def _track_slider(self, key: str) -> None:
        self._last_slider_key = key

    def _on_key(self, event) -> None:
        if event.key not in ("left", "right", "up", "down"):
            return
        s = self.sliders[self._last_slider_key]
        delta = (s.valmax - s.valmin) * 0.01
        direction = 1 if event.key in ("right", "up") else -1
        s.set_val(float(np.clip(s.val + direction * delta, s.valmin, s.valmax)))

    def _geometry(self):
        return _hull_from_gui_params(self.params).to_geometry()

    def update_plots(self) -> None:
        geom = self._geometry()
        wp = geom.waterplane(n=200)
        keel = geom.keel_line(n=200)
        deck_cl = geom.deck_centreline(n=200)
        xs = wp[:, 0]
        half_beam = wp[:, 1]
        keel_z = keel[:, 1]
        deck_cl_z = deck_cl[:, 1]

        hull_pts = geom.section(self.station_x, "hull")
        deck_pts = geom.section(self.station_x, "deck")

        ax = self.ax_section
        ax.cla()
        ax.fill(hull_pts[:, 0], hull_pts[:, 1], alpha=0.15, color=PLOT_COLORS["hull"])
        ax.fill(deck_pts[:, 0], deck_pts[:, 1], alpha=0.15, color=PLOT_COLORS["deck"])
        ax.plot(
            hull_pts[:, 0],
            hull_pts[:, 1],
            color=PLOT_COLORS["hull"],
            linewidth=2,
            label="Hull",
        )
        ax.plot(
            deck_pts[:, 0],
            deck_pts[:, 1],
            color=PLOT_COLORS["deck"],
            linewidth=2,
            label="Deck",
        )
        ax.axhline(
            0,
            color=PLOT_COLORS["waterline"],
            linewidth=0.8,
            linestyle="--",
            alpha=0.5,
        )
        ax.set_aspect("equal")
        half_L = geom.L / 2
        pct = (self.station_x / half_L * 100) if half_L > 0 else 0
        side = "fwd" if self.station_x < -0.01 else ("aft" if self.station_x > 0.01 else "mid")
        ax.set_title(
            f"Cross-Section  x = {self.station_x:+.2f} m  ({abs(pct):.0f}% {side})",
            fontsize=9,
        )
        ax.set_xlabel("Y (m)")
        ax.set_ylabel("Z (m)")
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.25)

        ax = self.ax_profile
        ax.cla()
        ax.fill_between(xs, keel_z, 0, alpha=0.15, color=PLOT_COLORS["hull"])
        ax.fill_between(xs, 0, deck_cl_z, alpha=0.15, color=PLOT_COLORS["deck"])
        ax.plot(xs, keel_z, color=PLOT_COLORS["hull"], linewidth=2, label="Keel line")
        ax.axhline(0, color=PLOT_COLORS["waterline"], lw=0.8, ls="--", alpha=0.5, label="Waterline")
        ax.plot(xs, deck_cl_z, color=PLOT_COLORS["deck"], linewidth=2, label="Deck centreline")
        ax.set_title("Sheer Plan", fontsize=10)
        ax.set_ylabel("Z (m)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.25)
        ax.axvline(self.station_x, color=PLOT_COLORS["focus"], lw=1.2, ls="--", alpha=0.85)

        ax = self.ax_plan
        ax.cla()
        ax.fill_between(xs, -half_beam, half_beam, alpha=0.20, color=PLOT_COLORS["hull"])
        ax.plot(xs, half_beam, color=PLOT_COLORS["hull"], linewidth=2)
        ax.plot(xs, -half_beam, color=PLOT_COLORS["hull"], linewidth=2)
        ax.axhline(0, color=PLOT_COLORS["waterline"], linewidth=0.5, linestyle="--", alpha=0.4)
        ax.set_title("Plan View", fontsize=10)
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.grid(True, alpha=0.25)
        ax.axvline(self.station_x, color=PLOT_COLORS["focus"], lw=1.2, ls="--", alpha=0.85)

        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    KayakGUI()
