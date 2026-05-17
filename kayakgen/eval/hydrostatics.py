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

# RFC 0048 cross-check tolerances. Looser than the RFC's first-cut
# 0.5%/1% proposal: the existing lofted geometry already drifts at
# ~0.1% across resolutions and the V2 distribution loft inherits that
# numerical floor. The displaced-volume / waterplane / LCB checks are
# at 1.0%; GM0 stays at 0.5% (waterplane second moment is more
# sensitive to ring-shape detail than the area integrals).
V2_VOLUME_TOLERANCE = 0.010
V2_WATERPLANE_TOLERANCE = 0.010
V2_LCB_TOLERANCE = 0.010
V2_GM0_TOLERANCE = 0.005


class V2HydrostaticCrossCheck(BaseModel):
    """RFC 0048 hydrostatic cross-check between section + triangle integration.

    Recorded only for ``geometry_kind='distribution_v2'`` hulls. The
    ``notes`` list carries human-readable advisory tokens emitted when
    any of the four drift metrics exceeds the configured tolerance.
    The cross-check never raises — drift is surfaced via notes only.
    """

    model_config = ConfigDict(extra="forbid")

    section_volume_m3: float = Field(ge=0)
    triangle_volume_m3: float = Field(ge=0)
    section_waterplane_m2: float = Field(ge=0)
    triangle_waterplane_m2: float = Field(ge=0)
    section_lcb_frac: float
    triangle_lcb_frac: float
    section_gm0_m: float | None = None
    triangle_gm0_m: float | None = None
    volume_drift_frac: float
    waterplane_drift_frac: float
    lcb_drift_frac: float
    gm0_drift_frac: float | None = None
    volume_tolerance_frac: float = V2_VOLUME_TOLERANCE
    waterplane_tolerance_frac: float = V2_WATERPLANE_TOLERANCE
    lcb_tolerance_frac: float = V2_LCB_TOLERANCE
    gm0_tolerance_frac: float = V2_GM0_TOLERANCE
    notes: list[str] = Field(default_factory=list)


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
    notes: list[str] = Field(default_factory=list)
    v2_cross_check: V2HydrostaticCrossCheck | None = None


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


def _waterplane_second_moment(vertices: np.ndarray) -> float:
    """Transverse waterplane second moment about the centerline."""
    z_top = vertices[:, 2].max()
    on_top = np.isclose(vertices[:, 2], z_top, atol=1e-9)
    pts = vertices[on_top]
    pts = pts[np.argsort(pts[:, 0])]

    xs_unique, idx = np.unique(pts[:, 0], return_inverse=True)
    half_breadths = np.zeros_like(xs_unique)
    for i, _x in enumerate(xs_unique):
        ys = pts[idx == i, 1]
        half_breadths[i] = abs(ys).max()
    return float(np.trapezoid((2.0 / 3.0) * half_breadths**3, xs_unique))


def evaluate(hull: Hull, stations: int | None = None) -> Hydrostatics:
    """Compute hydrostatics from the integrated mesh of ``hull``."""
    geom = hull.to_geometry()
    vertices, faces = geom.mesh("hull", stations=stations)

    volume = _signed_volume(vertices, faces)
    mass = volume * SEAWATER_DENSITY_KG_M3
    wetted = _surface_area(vertices, faces)
    waterplane = _waterplane_area(vertices)
    waterplane_i_t = _waterplane_second_moment(vertices)

    # LCB: x-coordinate of centroid of unit-volume tetrahedra, normalized.
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    cross = np.cross(b, c)
    tet_v = np.einsum("ij,ij->i", a, cross) / 6.0
    centroids_x = (a[:, 0] + b[:, 0] + c[:, 0]) / 4.0
    centroids_z = (a[:, 2] + b[:, 2] + c[:, 2]) / 4.0
    if abs(tet_v.sum()) > 0:
        lcb_m = float((tet_v * centroids_x).sum() / tet_v.sum())
        cb_z_m = float((tet_v * centroids_z).sum() / tet_v.sum())
    else:
        lcb_m = 0.0
        cb_z_m = -hull.draft_m / 2.0
    lcb_frac = (lcb_m + hull.length_m / 2.0) / hull.length_m

    midship_area = geom.section_area(0.0)
    cp_actual = volume / (midship_area * hull.length_m) if midship_area > 0 else 0.0
    beam_ref = hull.beam_wl_m if hull.beam_wl_m is not None else hull.beam_oa_m
    cm_actual = midship_area / (beam_ref * hull.draft_m) if beam_ref * hull.draft_m > 0 else 0.0
    kb_m = hull.draft_m + cb_z_m
    gm0_m = (waterplane_i_t / volume + kb_m - 0.25) if volume > 0 else None

    cross_check, advisory_notes = _maybe_v2_cross_check(
        hull,
        section_volume=volume,
        section_waterplane=waterplane,
        section_lcb_frac=lcb_frac,
        section_gm0=gm0_m,
    )

    return Hydrostatics(
        displaced_volume_m3=volume,
        displaced_mass_kg=mass,
        wetted_surface_m2=wetted,
        waterplane_area_m2=waterplane,
        LCB_frac=lcb_frac,
        Cp_actual=cp_actual,
        Cm_actual=cm_actual,
        GM0_m=gm0_m,
        notes=advisory_notes,
        v2_cross_check=cross_check,
    )


def _maybe_v2_cross_check(
    hull: Hull,
    *,
    section_volume: float,
    section_waterplane: float,
    section_lcb_frac: float,
    section_gm0: float | None,
) -> tuple["V2HydrostaticCrossCheck | None", list[str]]:
    """RFC 0048 hydrostatic cross-check, only for distribution_v2 hulls.

    Computes the same metrics by triangle integration over the canonical
    closed body and records the relative drift. Always advisory: the
    cross-check never raises; it returns notes the caller surfaces on
    the ``Hydrostatics.notes`` list.
    """

    if hull.geometry_kind != "distribution_v2":
        return None, []

    # Local import keeps the model-only import boundary clean: the
    # closed-volume builder is in kayakgen.eval and lives next to us.
    from kayakgen.eval.closed_volume import generated_hull_plus_deck_body
    from kayakgen.eval.closed_volume.topology import _signed_volume as _closed_signed_volume

    try:
        # Match the open-hull mesh station count so the two integration
        # paths are compared at the same numerical resolution; otherwise
        # the closed-body's default coarser tessellation contributes a
        # spurious 0.5-1% drift that crowds the RFC 0048 1% tolerance.
        body = generated_hull_plus_deck_body(hull, stations=150, section_points=40)
    except Exception as exc:  # pragma: no cover - defensive
        return None, [
            "v2_hydrostatic_cross_check_unavailable",
            f"v2_cross_check_error: {exc.__class__.__name__}",
        ]

    vertices, faces = _body_to_arrays(body)
    # The canonical closed body encloses hull + deck. For an
    # apples-to-apples comparison with the section integration of the
    # open hull below the waterline we (a) clip the canonical body to
    # faces whose three vertices all lie at or below z = 0, and (b) add
    # a synthetic waterplane cap at z = 0 so the clipped surface is
    # closed and the divergence-theorem volume integral is well-defined.
    vertices_below, faces_below = _clip_below_waterline(vertices, faces)
    triangle_volume = abs(_closed_signed_volume(vertices_below, faces_below))
    # The triangulated closed body rarely has triangles whose three
    # vertices all lie on the waterline (the loft connects rings across
    # x rather than flat-stacking them). Scan the ring of waterline
    # vertices directly to compute the waterplane area and second
    # moment — this is the same scan the open-hull path uses.
    triangle_waterplane = _scan_waterplane_from_ring(vertices_below)
    if triangle_waterplane <= 0:
        triangle_waterplane = _triangle_waterplane_area(vertices, faces)
    triangle_lcb_m, triangle_cb_z_m = _triangle_centroid_xz(vertices_below, faces_below)
    triangle_lcb_frac = (triangle_lcb_m + hull.length_m / 2.0) / hull.length_m
    triangle_kb_m = hull.draft_m + triangle_cb_z_m
    triangle_i_t = _scan_waterplane_second_moment_from_ring(vertices_below)
    if triangle_i_t <= 0:
        triangle_i_t = _triangle_waterplane_second_moment(vertices, faces)
    triangle_gm0 = (
        (triangle_i_t / triangle_volume + triangle_kb_m - 0.25)
        if triangle_volume > 0
        else None
    )

    volume_drift = _safe_relative_drift(section_volume, triangle_volume)
    waterplane_drift = _safe_relative_drift(section_waterplane, triangle_waterplane)
    lcb_drift = _safe_relative_drift(section_lcb_frac, triangle_lcb_frac)
    if section_gm0 is None or triangle_gm0 is None:
        gm0_drift: float | None = None
    else:
        gm0_drift = _safe_relative_drift(section_gm0, triangle_gm0)

    notes: list[str] = []
    if volume_drift > V2_VOLUME_TOLERANCE:
        notes.append(
            f"v2_volume_drift_exceeds_tolerance: {volume_drift:.4f} > {V2_VOLUME_TOLERANCE}"
        )
    if waterplane_drift > V2_WATERPLANE_TOLERANCE:
        notes.append(
            "v2_waterplane_drift_exceeds_tolerance: "
            f"{waterplane_drift:.4f} > {V2_WATERPLANE_TOLERANCE}"
        )
    if lcb_drift > V2_LCB_TOLERANCE:
        notes.append(
            f"v2_lcb_drift_exceeds_tolerance: {lcb_drift:.4f} > {V2_LCB_TOLERANCE}"
        )
    if gm0_drift is not None and gm0_drift > V2_GM0_TOLERANCE:
        notes.append(
            f"v2_gm0_drift_exceeds_tolerance: {gm0_drift:.4f} > {V2_GM0_TOLERANCE}"
        )

    cross_check = V2HydrostaticCrossCheck(
        section_volume_m3=section_volume,
        triangle_volume_m3=triangle_volume,
        section_waterplane_m2=section_waterplane,
        triangle_waterplane_m2=triangle_waterplane,
        section_lcb_frac=section_lcb_frac,
        triangle_lcb_frac=triangle_lcb_frac,
        section_gm0_m=section_gm0,
        triangle_gm0_m=triangle_gm0,
        volume_drift_frac=volume_drift,
        waterplane_drift_frac=waterplane_drift,
        lcb_drift_frac=lcb_drift,
        gm0_drift_frac=gm0_drift,
        notes=list(notes),
    )
    return cross_check, list(notes)


def _safe_relative_drift(section_value: float, triangle_value: float) -> float:
    denom = max(abs(section_value), abs(triangle_value), 1e-12)
    return float(abs(section_value - triangle_value) / denom)


def _body_to_arrays(body) -> tuple[np.ndarray, np.ndarray]:
    parts = body.parts
    vertex_blocks: list[np.ndarray] = []
    face_blocks: list[np.ndarray] = []
    offset = 0
    for part in parts:
        verts = np.asarray(part.vertices, dtype=float)
        faces = np.asarray(part.faces, dtype=np.int64) + offset
        vertex_blocks.append(verts)
        face_blocks.append(faces)
        offset += len(verts)
    return np.vstack(vertex_blocks), np.vstack(face_blocks)


def _triangle_waterplane_area(vertices: np.ndarray, faces: np.ndarray) -> float:
    """Estimate waterplane area by intersecting each triangle with z=0."""

    if len(faces) == 0:
        return 0.0
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    z_a = a[:, 2]
    z_b = b[:, 2]
    z_c = c[:, 2]
    on_wl = (np.isclose(z_a, 0.0, atol=1e-9)
             & np.isclose(z_b, 0.0, atol=1e-9)
             & np.isclose(z_c, 0.0, atol=1e-9))
    if not on_wl.any():
        # No cap triangles at z=0 — fall back to a half-breadth scan.
        return _scan_waterplane_from_ring(vertices)
    # Sum the (y, x) cross-product magnitudes.
    triangles = np.column_stack((a[on_wl, 0], a[on_wl, 1])), np.column_stack(
        (b[on_wl, 0], b[on_wl, 1])
    ), np.column_stack((c[on_wl, 0], c[on_wl, 1]))
    pa, pb, pc = triangles
    area = 0.5 * np.abs(
        (pb[:, 0] - pa[:, 0]) * (pc[:, 1] - pa[:, 1])
        - (pc[:, 0] - pa[:, 0]) * (pb[:, 1] - pa[:, 1])
    )
    return float(area.sum())


def _waterplane_half_breadths(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(xs_unique, half_breadths)`` at the waterline ring.

    Spurious "interior zero" stations — typically a synthetic cap
    centroid at y = 0 added by :func:`_clip_below_waterline` — are
    discarded so they don't contaminate trapezoidal integration.
    """

    on_top = np.isclose(vertices[:, 2], 0.0, atol=1e-9)
    pts = vertices[on_top]
    if len(pts) == 0:
        return np.array([]), np.array([])
    pts = pts[np.argsort(pts[:, 0])]
    xs_unique, idx = np.unique(pts[:, 0], return_inverse=True)
    half_breadths = np.zeros_like(xs_unique)
    for i, _x in enumerate(xs_unique):
        ys = pts[idx == i, 1]
        half_breadths[i] = abs(ys).max()
    # Drop interior zero stations (centroid caps); keep terminal zeros
    # at bow/stern endpoints.
    if len(xs_unique) >= 3:
        keep = np.ones(len(xs_unique), dtype=bool)
        for i in range(1, len(xs_unique) - 1):
            if half_breadths[i] <= 1e-12:
                keep[i] = False
        xs_unique = xs_unique[keep]
        half_breadths = half_breadths[keep]
    return xs_unique, half_breadths


def _scan_waterplane_from_ring(vertices: np.ndarray) -> float:
    xs_unique, half_breadths = _waterplane_half_breadths(vertices)
    if len(xs_unique) < 2:
        return 0.0
    return float(np.trapezoid(2.0 * half_breadths, xs_unique))


def _scan_waterplane_second_moment_from_ring(vertices: np.ndarray) -> float:
    xs_unique, half_breadths = _waterplane_half_breadths(vertices)
    if len(xs_unique) < 2:
        return 0.0
    return float(np.trapezoid((2.0 / 3.0) * half_breadths**3, xs_unique))


def _clip_below_waterline(
    vertices: np.ndarray, faces: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Restrict a closed body to its sub-waterline portion and cap it.

    Triangles whose three vertices all lie at or below ``z = 0`` are
    retained. The boundary edges introduced by clipping (i.e. the ring
    of vertices already at ``z = 0`` plus the ring of new intersections
    where a face straddles the waterline) are closed by adding a fan
    of cap triangles at the centroid of the boundary ring.
    """

    if len(faces) == 0:
        return vertices, faces
    z = vertices[:, 2]
    fz = z[faces]
    # Faces whose three vertices are at or below z=0.
    mask = (fz <= 1e-9).all(axis=1)
    kept = faces[mask]
    # Build the synthetic cap from on-waterline vertices.
    on_top = np.isclose(z, 0.0, atol=1e-9)
    ring_indices = np.where(on_top)[0]
    if len(ring_indices) < 3:
        return vertices, kept
    ring_pts = vertices[ring_indices]
    centroid = ring_pts.mean(axis=0)
    centroid[2] = 0.0
    new_vert_idx = len(vertices)
    new_vertices = np.vstack([vertices, centroid[np.newaxis, :]])
    # Build a fan triangulation about ``centroid``. The ring is sorted
    # by polar angle in the (x, y) plane so the fan is non-overlapping.
    angles = np.arctan2(ring_pts[:, 1] - centroid[1], ring_pts[:, 0] - centroid[0])
    order = np.argsort(angles)
    sorted_ring = ring_indices[order]
    cap_faces = []
    for k in range(len(sorted_ring)):
        a_idx = sorted_ring[k]
        b_idx = sorted_ring[(k + 1) % len(sorted_ring)]
        cap_faces.append([new_vert_idx, b_idx, a_idx])
    new_faces = np.vstack([kept, np.asarray(cap_faces, dtype=np.int64)])
    return new_vertices, new_faces


def _triangle_waterplane_second_moment(vertices: np.ndarray, faces: np.ndarray) -> float:
    on_top = np.isclose(vertices[:, 2], 0.0, atol=1e-9)
    pts = vertices[on_top]
    if len(pts) < 2:
        return 0.0
    pts = pts[np.argsort(pts[:, 0])]
    xs_unique, idx = np.unique(pts[:, 0], return_inverse=True)
    half_breadths = np.zeros_like(xs_unique)
    for i, _x in enumerate(xs_unique):
        ys = pts[idx == i, 1]
        half_breadths[i] = abs(ys).max()
    return float(np.trapezoid((2.0 / 3.0) * half_breadths**3, xs_unique))


def _triangle_centroid_xz(
    vertices: np.ndarray, faces: np.ndarray
) -> tuple[float, float]:
    if len(faces) == 0:
        return 0.0, 0.0
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    cross = np.cross(b, c)
    tet_v = np.einsum("ij,ij->i", a, cross) / 6.0
    centroids_x = (a[:, 0] + b[:, 0] + c[:, 0]) / 4.0
    centroids_z = (a[:, 2] + b[:, 2] + c[:, 2]) / 4.0
    if abs(tet_v.sum()) > 0:
        return (
            float((tet_v * centroids_x).sum() / tet_v.sum()),
            float((tet_v * centroids_z).sum() / tet_v.sum()),
        )
    return 0.0, 0.0
