"""Interactive PyVista 3D preview window."""

from __future__ import annotations

import numpy as np
import pyvista as pv
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from kayakgen.model.hull import Hull
from kayakgen.ui import theme
from kayakgen.ui.parameter_metadata import VIEW_PARAMETER_METADATA

# RFC 0061: view-only keys live in VIEW_PARAMETER_METADATA so the
# desktop GUI and the PyVista preview cannot drift on which keys are
# not Hull fields.
_NON_HULL_GUI_KEYS: tuple[str, ...] = tuple(VIEW_PARAMETER_METADATA.keys())


def _hull_from_params(params: dict) -> Hull:
    """Build a :class:`Hull` from the desktop ``params`` dict.

    Filters out view-only keys (``target_speed_kt``) sourced from
    ``VIEW_PARAMETER_METADATA``. Replaces the legacy
    ``kayakgen.ui.gui_params.hull_from_gui_params`` indirection per RFC
    0061; ``params`` is already keyed by canonical Hull JSON field
    names.
    """

    return Hull(
        **{key: value for key, value in params.items() if key not in _NON_HULL_GUI_KEYS}
    )


PV_COLORS = {
    "viewport_bg": theme.vtk_background_rgb(dark=False),
    "hull": theme.PLOT_PALETTE["hull"],
    "deck": theme.PLOT_PALETTE["deck"],
    "waterline": theme.PLOT_PALETTE["waterline"],
}


def _build_pv_mesh(vertices: np.ndarray, faces: np.ndarray) -> pv.PolyData:
    pv_faces = np.hstack([np.full((len(faces), 1), 3), faces]).ravel()
    mesh = pv.PolyData(vertices, pv_faces)
    mesh.compute_normals(inplace=True)
    return mesh


class PyVistaWindow(QMainWindow):
    PRESETS = [
        ("Top", [(0, 0, 20), (0, 0, 0), (0, 1, 0)]),
        ("Side", [(20, 0, 2), (0, 0, 0), (0, 0, 1)]),
        ("Front", [(0, 20, 2), (0, 0, 0), (0, 0, 1)]),
        ("Iso", [(10, 10, 6), (0, 0, 0), (0, 0, 1)]),
    ]

    def __init__(self, params: dict) -> None:
        super().__init__()
        self._update_title(params)
        self.resize(900, 650)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        layout.addLayout(toolbar)
        for label, cam in self.PRESETS:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, c=cam: self._set_camera(c))
            toolbar.addWidget(btn)
        toolbar.addStretch()

        self._plotter = QtInteractor(central)
        layout.addWidget(self._plotter.interactor)

        self._plotter.set_background(PV_COLORS["viewport_bg"])
        self._hull_actor = None
        self._deck_actor = None
        self._build_scene(params)
        self._plotter.add_axes()
        self._plotter.reset_camera()

    def _update_title(self, params: dict) -> None:
        self.setWindowTitle(
            f"Kayak 3D — {params['length_m']:.1f}m × {params['beam_oa_m']:.2f}m beam"
        )

    def _build_scene(self, params: dict) -> None:
        geom = _hull_from_params(params).to_geometry()
        hull_pv = _build_pv_mesh(*geom.mesh("hull", stations=80))
        deck_pv = _build_pv_mesh(*geom.mesh("deck", stations=80))

        self._hull_actor = self._plotter.add_mesh(
            hull_pv,
            color=PV_COLORS["hull"],
            smooth_shading=True,
            split_sharp_edges=True,
            show_edges=False,
            name="hull",
        )
        self._deck_actor = self._plotter.add_mesh(
            deck_pv,
            color=PV_COLORS["deck"],
            smooth_shading=True,
            split_sharp_edges=True,
            opacity=0.85,
            show_edges=False,
            name="deck",
        )
        wl = pv.Plane(
            center=(0, 0, 0),
            direction=(0, 0, 1),
            i_size=geom.L * 1.2,
            j_size=geom.B * 2.0,
        )
        self._plotter.add_mesh(
            wl,
            color=PV_COLORS["waterline"],
            opacity=0.2,
            show_edges=False,
            name="waterline",
        )

    def update_mesh(self, params: dict) -> None:
        geom = _hull_from_params(params).to_geometry()
        for part, attr in [("hull", "_hull_actor"), ("deck", "_deck_actor")]:
            verts, faces = geom.mesh(part, stations=80)
            pv_mesh = _build_pv_mesh(verts, faces)
            actor = getattr(self, attr)
            actor.mapper.dataset.points = pv_mesh.points
            actor.mapper.dataset.faces = pv_mesh.faces
            actor.mapper.dataset.compute_normals(inplace=True)
        self._plotter.render()
        self._update_title(params)

    def _set_camera(self, cam) -> None:
        self._plotter.camera_position = cam
        self._plotter.render()
