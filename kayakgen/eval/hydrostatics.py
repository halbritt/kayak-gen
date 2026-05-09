"""Hydrostatics from the integrated geometry.

This is the single source of truth RFC 0007 §4 promotes from a formula
envelope to integrated values. Every consumer (desktop GUI metrics, web
frontend, CLI evaluate, future optimisers) calls into ``evaluate``.
"""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from kayakgen.model.hull import Hull

SEAWATER_DENSITY_KG_M3 = 1025.0


class Hydrostatics(BaseModel):
    """Integrated hydrostatic projections of a hull."""

    model_config = ConfigDict(extra="forbid")

    displaced_volume_m3: float = Field(ge=0)
    displaced_mass_kg: float = Field(ge=0)
    wetted_surface_m2: float = Field(ge=0)
    waterplane_area_m2: float = Field(ge=0)
    LCB_frac: float
    Cp_actual: float
    Cm_actual: float
    GM0_m: float | None = None
    gz_curve: list[tuple[float, float]] | None = None


def _signed_volume(vertices: np.ndarray, faces: np.ndarray) -> float:
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    return float(abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0))


def _surface_area(vertices: np.ndarray, faces: np.ndarray) -> float:
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    return float(0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum())


def _waterplane_area(vertices: np.ndarray) -> float:
    """Area of the design-waterline polygon at z=0.

    Each station contributes a port/starboard pair of points at z=0
    (the topmost ring of hull vertices). Pair them across stations and
    integrate via the trapezoidal rule along x.
    """
    z_top = vertices[:, 2].max()
    on_top = np.isclose(vertices[:, 2], z_top, atol=1e-9)
    pts = vertices[on_top]
    pts = pts[np.argsort(pts[:, 0])]

    xs_unique, idx = np.unique(pts[:, 0], return_inverse=True)
    half_breadths = np.zeros_like(xs_unique)
    for i, _x in enumerate(xs_unique):
        ys = pts[idx == i, 1]
        half_breadths[i] = abs(ys).max()
    return float(np.trapezoid(2.0 * half_breadths, xs_unique))


def evaluate(hull: Hull, stations: int | None = None) -> Hydrostatics:
    """Compute hydrostatics from the integrated mesh of ``hull``."""
    geom = hull.to_geometry()
    vertices, faces = geom.mesh("hull", stations=stations)

    volume = _signed_volume(vertices, faces)
    mass = volume * SEAWATER_DENSITY_KG_M3
    wetted = _surface_area(vertices, faces)
    waterplane = _waterplane_area(vertices)

    # LCB: x-coordinate of centroid of unit-volume tetrahedra, normalized.
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    cross = np.cross(b, c)
    tet_v = np.einsum("ij,ij->i", a, cross) / 6.0
    centroids_x = (a[:, 0] + b[:, 0] + c[:, 0]) / 4.0
    if abs(tet_v.sum()) > 0:
        lcb_m = float((tet_v * centroids_x).sum() / tet_v.sum())
    else:
        lcb_m = 0.0
    lcb_frac = (lcb_m + hull.length_m / 2.0) / hull.length_m

    midship_area = geom.section_area(0.0)
    cp_actual = volume / (midship_area * hull.length_m) if midship_area > 0 else 0.0
    cm_actual = midship_area / (hull.beam_oa_m * hull.draft_m) if hull.beam_oa_m * hull.draft_m > 0 else 0.0

    return Hydrostatics(
        displaced_volume_m3=volume,
        displaced_mass_kg=mass,
        wetted_surface_m2=wetted,
        waterplane_area_m2=waterplane,
        LCB_frac=lcb_frac,
        Cp_actual=cp_actual,
        Cm_actual=cm_actual,
    )
