"""3D scene construction for the kayakgen web UI (VTK builders + scene mixin).

Extracted verbatim from ``kayakgen.ui.web.app`` (refactoring campaign
kayakgen-smoke-1, slice S2). ``KayakgenApp`` composes ``SceneMixin``.
"""

from __future__ import annotations

import numpy as np
import vtk

from kayakgen.model.hull import Hull
from kayakgen.ui import theme


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

class SceneMixin:
    """3D-scene methods of :class:`~kayakgen.ui.web.app.KayakgenApp`."""

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
