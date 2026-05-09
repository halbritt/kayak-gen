import matplotlib
matplotlib.use("qtagg")
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
from matplotlib.gridspec import GridSpec
from PyQt6.QtCore import QTimer
from generator import KayakGenerator


class KayakGUI:
    SLIDERS = [
        ("length",          "Length (m)",       2.0,  6.0),
        ("beam",            "Beam (m)",          0.3,  0.9),
        ("draft",           "Draft (m)",         0.05, 0.25),
        ("deck_height",     "Deck Height (m)",   0.15, 0.40),
        ("Cp",              "Prismatic Coeff",   0.45, 0.70),
        ("deck_flatness",   "Deck Flatness",     2.0,  16.0),
        ("center_box_ratio","Parallel Mid-Body", 0.10, 0.60),
    ]

    DEFAULTS = dict(
        length=4.5, beam=0.55, draft=0.12, deck_height=0.23,
        Cp=0.55, deck_flatness=8.0, center_box_ratio=0.33,
    )

    def __init__(self):
        self.params = dict(self.DEFAULTS)

        self.fig = plt.figure(figsize=(16, 9))
        self.fig.suptitle("Kayak Generator", fontsize=14, fontweight="bold")

        gs = GridSpec(3, 1, figure=self.fig,
                      left=0.38, right=0.97, top=0.93, bottom=0.13,
                      hspace=0.45,
                      height_ratios=[2, 1, 1])
        self.ax_section = self.fig.add_subplot(gs[0])   # top: cross-section
        self.ax_profile = self.fig.add_subplot(gs[1])   # middle: sheer plan
        self.ax_plan    = self.fig.add_subplot(gs[2],   # bottom: plan view
                                               sharex=self.ax_profile)

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
        self.update_plots()
        self._refresh_metrics()
        plt.show()

    # ------------------------------------------------------------------
    def _build_sliders(self):
        n = len(self.SLIDERS)
        # Distribute sliders between y=0.18 and y=0.93
        top_start, bot_end = 0.93, 0.18
        step = (top_start - bot_end) / n

        self.sliders = {}
        for i, (key, label, vmin, vmax) in enumerate(self.SLIDERS):
            y = top_start - (i + 0.5) * step - 0.015
            ax = self.fig.add_axes([0.07, y, 0.26, 0.025])
            s = widgets.Slider(ax, label, vmin, vmax, valinit=self.params[key])
            s.label.set_fontsize(7)
            s.label.set_position((0.5, -1.8))
            s.label.set_horizontalalignment("center")
            s.on_changed(self._on_change)
            self.sliders[key] = s

    def _build_button(self):
        ax_btn = self.fig.add_axes([0.05, 0.205, 0.12, 0.045])
        self.btn = widgets.Button(ax_btn, "Generate STLs", color="steelblue", hovercolor="royalblue")
        self.btn.label.set_color("white")
        self.btn.on_clicked(self._on_generate)

        ax_rst = self.fig.add_axes([0.19, 0.205, 0.12, 0.045])
        self.btn_reset = widgets.Button(ax_rst, "Reset", color="0.75", hovercolor="0.85")
        self.btn_reset.on_clicked(self._on_reset)

        ax_3d = self.fig.add_axes([0.05, 0.255, 0.26, 0.045])
        self.btn_3d = widgets.Button(ax_3d, "3D View", color="0.25", hovercolor="0.35")
        self.btn_3d.label.set_color("white")
        self.btn_3d.on_clicked(self._on_open_3d)

        self.ax_status = self.fig.add_axes([0.05, 0.160, 0.26, 0.040])
        self.ax_status.axis("off")
        self.status = self.ax_status.text(0.5, 0.5, "", ha="center", va="center",
                                          transform=self.ax_status.transAxes, fontsize=8)

        self.ax_metrics = self.fig.add_axes([0.05, 0.020, 0.26, 0.100])
        self.ax_metrics.axis("off")
        self.metrics_text = self.ax_metrics.text(
            0.0, 1.0, "", ha="left", va="top",
            transform=self.ax_metrics.transAxes,
            fontsize=7.5, fontfamily="monospace",
        )

        half_L = self.params["length"] / 2
        self.ax_station = self.fig.add_axes([0.38, 0.04, 0.59, 0.025])
        self.station_slider = widgets.Slider(
            self.ax_station, "Station X (m)",
            -half_L, half_L, valinit=0.0,
        )
        self.station_slider.on_changed(self._on_station_change)

    # ------------------------------------------------------------------
    def _on_change(self, _val):
        for key, s in self.sliders.items():
            self.params[key] = s.val
        self.status.set_text("")
        self.update_plots()
        if self._pv_window is not None and self._pv_window.isVisible():
            self._3d_timer.start()
        self._refresh_metrics()
        half_L = self.params["length"] / 2
        self.station_slider.valmin = -half_L
        self.station_slider.valmax =  half_L
        self.station_slider.ax.set_xlim(-half_L, half_L)
        self.station_x = float(np.clip(self.station_x, -half_L, half_L))
        self.station_slider.set_val(self.station_x)

    def _on_station_change(self, val):
        self.station_x = float(val)
        self.update_plots()

    def _on_reset(self, _event):
        for key, s in self.sliders.items():
            s.set_val(self.DEFAULTS[key])

    def _on_generate(self, _event):
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            None, "Save kayak STLs", "kayak", "STL files (*.stl)"
        )
        if not path:
            return
        stem = path.removesuffix("_hull.stl").removesuffix(".stl")
        self.status.set_text("Generating…")
        self.fig.canvas.draw()
        kg = KayakGenerator(**self.params)
        kg.generate_stl("hull", f"{stem}_hull.stl")
        kg.generate_stl("deck", f"{stem}_deck.stl")
        import os
        self.status.set_text(f"Saved {os.path.basename(stem)}_hull/deck.stl")
        self.fig.canvas.draw()

    def _on_open_3d(self, _event):
        self.btn_3d.label.set_text("Opening…")
        self.fig.canvas.draw()
        from pyvista_view import PyVistaWindow
        if self._pv_window is None or not self._pv_window.isVisible():
            self._pv_window = PyVistaWindow(self.params)
            self._pv_window.show()
        self.btn_3d.label.set_text("3D View")
        self.fig.canvas.draw()

    def _flush_3d(self):
        if self._pv_window is not None and self._pv_window.isVisible():
            self._pv_window.update_mesh(self.params)

    def _compute_metrics(self) -> dict:
        p = self.params
        L, B, T = p["length"], p["beam"], p["draft"]
        Cp = p["Cp"]
        Cm = 0.85
        Cwp = 0.7 + 0.16 * Cp
        vol = Cp * Cm * L * B * T
        disp_kg = vol * 1025
        wpa = Cwp * L * B
        lob = L / B
        mid_area = Cm * B * T
        return dict(disp_kg=disp_kg, wpa=wpa, lob=lob, mid_area=mid_area)

    def _refresh_metrics(self):
        m = self._compute_metrics()
        txt = (
            f"Est. displ.  {m['disp_kg']:6.0f} kg\n"
            f"Waterplane   {m['wpa']:6.2f} m²\n"
            f"LOA/B ratio  {m['lob']:6.2f}\n"
            f"Mid section  {m['mid_area']:6.4f} m²"
        )
        self.metrics_text.set_text(txt)

    def _track_slider(self, key: str):
        self._last_slider_key = key

    def _on_key(self, event):
        if event.key not in ("left", "right", "up", "down"):
            return
        s = self.sliders[self._last_slider_key]
        delta = (s.valmax - s.valmin) * 0.01
        direction = 1 if event.key in ("right", "up") else -1
        s.set_val(float(np.clip(s.val + direction * delta, s.valmin, s.valmax)))

    # ------------------------------------------------------------------
    def _make_generator(self):
        return KayakGenerator(**self.params)

    def _station_data(self, kg, xs):
        """Return per-station arrays: half_beam, keel_z, deck_cl_z."""
        half_beam, keel_z, deck_cl_z = [], [], []
        for x in xs:
            frac = kg._get_area_fraction(x)
            decay = np.sqrt(frac)
            half_beam.append((kg.B / 2.0) * decay)
            keel_z.append(-kg.T * decay)
            ds = kg._get_deck_height_scaling(x)
            deck_cl_z.append((kg.H - kg.T) * ds)
        return (np.array(half_beam), np.array(keel_z), np.array(deck_cl_z))

    def update_plots(self):
        kg = self._make_generator()
        xs = np.linspace(-kg.L / 2, kg.L / 2, 200)
        half_beam, keel_z, deck_cl_z = self._station_data(kg, xs)

        # ---- Cross-section at selected station ----
        hull_pts = kg._get_slice_points(self.station_x, "hull")
        deck_pts = kg._get_slice_points(self.station_x, "deck")

        ax = self.ax_section
        ax.cla()
        ax.fill(hull_pts[:, 0], hull_pts[:, 1], alpha=0.15, color="steelblue")
        ax.fill(deck_pts[:, 0], deck_pts[:, 1], alpha=0.15, color="seagreen")
        ax.plot(hull_pts[:, 0], hull_pts[:, 1], color="steelblue", linewidth=2, label="Hull")
        ax.plot(deck_pts[:, 0], deck_pts[:, 1], color="seagreen",  linewidth=2, label="Deck")
        ax.axhline(0, color="k", linewidth=0.8, linestyle="--", alpha=0.5)
        ax.set_aspect("equal")
        half_L = kg.L / 2
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

        # ---- Sheer plan ----
        ax = self.ax_profile
        ax.cla()
        ax.fill_between(xs, keel_z, 0,         alpha=0.15, color="steelblue")
        ax.fill_between(xs, 0, deck_cl_z,       alpha=0.15, color="seagreen")
        ax.plot(xs, keel_z,    color="steelblue", linewidth=2, label="Keel line")
        ax.axhline(0, color="k", lw=0.8, ls="--", alpha=0.5, label="Waterline")
        ax.plot(xs, deck_cl_z, color="seagreen",  linewidth=2, label="Deck centreline")
        ax.set_title("Sheer Plan", fontsize=10)
        ax.set_ylabel("Z (m)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.25)
        self.ax_profile.axvline(self.station_x, color="crimson", lw=1.2, ls="--", alpha=0.85)

        # ---- Plan view ----
        ax = self.ax_plan
        ax.cla()
        ax.fill_between(xs, -half_beam, half_beam, alpha=0.20, color="steelblue")
        ax.plot(xs,  half_beam, color="steelblue", linewidth=2)
        ax.plot(xs, -half_beam, color="steelblue", linewidth=2)
        ax.axhline(0, color="k", linewidth=0.5, linestyle="--", alpha=0.4)
        ax.set_title("Plan View", fontsize=10)
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.grid(True, alpha=0.25)
        self.ax_plan.axvline(self.station_x, color="crimson", lw=1.2, ls="--", alpha=0.85)

        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    KayakGUI()
