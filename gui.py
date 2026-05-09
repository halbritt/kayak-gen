import matplotlib
matplotlib.use("qtagg")
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
from matplotlib.gridspec import GridSpec
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

        gs = GridSpec(2, 2, figure=self.fig,
                      left=0.32, right=0.97, top=0.93, bottom=0.08,
                      hspace=0.45, wspace=0.35)
        self.ax_section = self.fig.add_subplot(gs[0, 0])
        self.ax_profile = self.fig.add_subplot(gs[0, 1])
        self.ax_plan    = self.fig.add_subplot(gs[1, :])

        self._build_sliders()
        self._build_button()
        self.update_plots()
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
            ax = self.fig.add_axes([0.04, y, 0.24, 0.025])
            s = widgets.Slider(ax, label, vmin, vmax, valinit=self.params[key])
            s.on_changed(self._on_change)
            self.sliders[key] = s

    def _build_button(self):
        ax_btn = self.fig.add_axes([0.04, 0.07, 0.11, 0.045])
        self.btn = widgets.Button(ax_btn, "Generate STLs", color="steelblue", hovercolor="royalblue")
        self.btn.label.set_color("white")
        self.btn.on_clicked(self._on_generate)

        ax_rst = self.fig.add_axes([0.17, 0.07, 0.11, 0.045])
        self.btn_reset = widgets.Button(ax_rst, "Reset", color="0.75", hovercolor="0.85")
        self.btn_reset.on_clicked(self._on_reset)

        ax_3d = self.fig.add_axes([0.04, 0.13, 0.24, 0.045])
        self.btn_3d = widgets.Button(ax_3d, "3D View", color="0.25", hovercolor="0.35")
        self.btn_3d.label.set_color("white")
        self.btn_3d.on_clicked(self._on_open_3d)
        self._pv_window = None

        self.ax_status = self.fig.add_axes([0.04, 0.01, 0.24, 0.04])
        self.ax_status.axis("off")
        self.status = self.ax_status.text(0.5, 0.5, "", ha="center", va="center",
                                          transform=self.ax_status.transAxes, fontsize=8)

    # ------------------------------------------------------------------
    def _on_change(self, _val):
        for key, s in self.sliders.items():
            self.params[key] = s.val
        self.status.set_text("")
        self.update_plots()

    def _on_reset(self, _event):
        for key, s in self.sliders.items():
            s.set_val(self.DEFAULTS[key])

    def _on_generate(self, _event):
        self.status.set_text("Generating…")
        self.fig.canvas.draw()
        kg = KayakGenerator(**self.params)
        kg.generate_stl("hull", "kayak_hull.stl")
        kg.generate_stl("deck", "kayak_deck.stl")
        self.status.set_text("Saved kayak_hull.stl + kayak_deck.stl")
        self.fig.canvas.draw()

    def _on_open_3d(self, _event):
        from pyvista_view import PyVistaWindow
        if self._pv_window is None or not self._pv_window.isVisible():
            self._pv_window = PyVistaWindow(self.params)
            self._pv_window.show()

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

        # ---- Cross-section at midship ----
        hull_pts = kg._get_slice_points(0, "hull")
        deck_pts = kg._get_slice_points(0, "deck")

        ax = self.ax_section
        ax.cla()
        ax.fill(hull_pts[:, 0], hull_pts[:, 1], alpha=0.15, color="steelblue")
        ax.fill(deck_pts[:, 0], deck_pts[:, 1], alpha=0.15, color="seagreen")
        ax.plot(hull_pts[:, 0], hull_pts[:, 1], color="steelblue", linewidth=2, label="Hull")
        ax.plot(deck_pts[:, 0], deck_pts[:, 1], color="seagreen",  linewidth=2, label="Deck")
        ax.axhline(0, color="k", linewidth=0.8, linestyle="--", alpha=0.5)
        ax.set_aspect("equal")
        ax.set_title("Midship Cross-Section", fontsize=10)
        ax.set_xlabel("Y (m)")
        ax.set_ylabel("Z (m)")
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.25)

        # ---- Side profile ----
        ax = self.ax_profile
        ax.cla()
        ax.fill_between(xs, keel_z, 0,         alpha=0.15, color="steelblue")
        ax.fill_between(xs, 0, deck_cl_z,       alpha=0.15, color="seagreen")
        ax.plot(xs, keel_z,    color="steelblue", linewidth=2, label="Keel")
        ax.plot(xs, np.zeros_like(xs), color="k", linewidth=0.8, linestyle="--", alpha=0.5)
        ax.plot(xs, deck_cl_z, color="seagreen",  linewidth=2, label="Deck CL")
        ax.set_title("Side Profile", fontsize=10)
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Z (m)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.25)

        # ---- Plan view ----
        ax = self.ax_plan
        ax.cla()
        ax.fill_between(xs, -half_beam, half_beam, alpha=0.20, color="steelblue")
        ax.plot(xs,  half_beam, color="steelblue", linewidth=2)
        ax.plot(xs, -half_beam, color="steelblue", linewidth=2)
        ax.axhline(0, color="k", linewidth=0.5, linestyle="--", alpha=0.4)
        ax.set_aspect("equal")
        ax.set_title("Plan View", fontsize=10)
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.grid(True, alpha=0.25)

        self.fig.canvas.draw_idle()

        if self._pv_window is not None and self._pv_window.isVisible():
            self._pv_window.update_mesh(self.params)


if __name__ == "__main__":
    KayakGUI()
