"""HullGeometry interface and the lofted parametric implementation.

The lofted implementation here is a port of the original ``KayakGenerator``
(``generator.py``) onto the ``Hull`` aggregate. The math is unchanged — the
golden tests pin its behavior — but the parameters are owned by ``Hull``
and a small set of public accessors (``waterplane``, ``keel_line``,
``deck_centreline``, ``section_area``) replace the underscore-prefixed
calls the GUI used to reach for.

The :class:`DistributionV2Geometry` class implements the RFC 0048
distribution-model successor: it consumes an explicit
``DistributionV2Spec`` (half-breadth, draft, deck-freeboard, rocker,
section-area distributions plus a cross-section family literal) and
produces both the canonical closed-body section ring and the derived
open inspection sections via the same public API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

import numpy as np
from stl import mesh as numpy_stl_mesh

from kayakgen.model.distribution_v2 import (
    CrossSectionFamily,
    DistributionV2Spec,
    LongitudinalDistribution,
)
from kayakgen.model.hull import Hull

PartType = Literal["hull", "deck"]


class HullGeometry(ABC):
    """Read-only geometry derived from a :class:`Hull`."""

    hull: Hull

    @abstractmethod
    def section(self, x: float, part: PartType) -> np.ndarray:
        """Return the (y, z) cross-section points of the given part at station ``x``."""

    @abstractmethod
    def mesh(self, part: PartType, stations: int | None = None) -> tuple[np.ndarray, np.ndarray]:
        """Return ``(vertices, faces)`` arrays for the given part."""

    @abstractmethod
    def waterplane(self, n: int = 200) -> np.ndarray:
        """Return ``(x, half_beam)`` samples of the design waterline."""

    @abstractmethod
    def keel_line(self, n: int = 200) -> np.ndarray:
        """Return ``(x, z)`` samples of the keel along the centerline."""

    @abstractmethod
    def deck_centreline(self, n: int = 200) -> np.ndarray:
        """Return ``(x, z)`` samples of the deck along the centerline."""

    @abstractmethod
    def section_area(self, x: float) -> float:
        """Return the cross-sectional submerged area at station ``x``."""

    @abstractmethod
    def half_breadth_grid(
        self, n_stations: int, n_depths: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return ``(xs, depths, half_breadths)`` for resistance integration."""


class LoftedHullGeometry(HullGeometry):
    """Lofted, parametric hull geometry — the original kayak-gen math."""

    NUM_STATIONS = 150
    NUM_POINTS = 40

    def __init__(self, hull: Hull) -> None:
        self.hull = hull
        self.num_stations = self.NUM_STATIONS
        self.num_points = self.NUM_POINTS

    # Convenience aliases used by the legacy GUI; kept private to the
    # implementation so callers can't reach across the abstraction.
    @property
    def L(self) -> float:
        return self.hull.length_m

    @property
    def B(self) -> float:
        return self.hull.beam_oa_m

    @property
    def B_wl(self) -> float:
        """Beam at the design waterline; falls back to overall beam if unset."""
        return self.hull.beam_wl_m if self.hull.beam_wl_m is not None else self.hull.beam_oa_m

    def _half_beam_for_part(self, part: PartType) -> float:
        """Half-beam to use at midship for ``part``.

        The hull (wetted surface) tapers from the keel up to the waterline
        at ``beam_wl``; the deck (topside surface) carries the overall beam
        ``beam_oa``. When ``beam_wl_m`` is None on the Hull, both fall back
        to the overall beam, preserving legacy behaviour.
        """
        return (self.B_wl if part == "hull" else self.B) / 2.0

    @property
    def T(self) -> float:
        return self.hull.draft_m

    @property
    def H(self) -> float:
        return self.hull.deck_height_m

    @property
    def Cp(self) -> float:
        return self.hull.Cp

    @property
    def Cm(self) -> float:
        return self.hull.Cm

    @property
    def deck_power(self) -> float:
        return self.hull.deck_flatness

    @property
    def center_ratio(self) -> float:
        return self.hull.center_box_ratio

    # ----- shape helpers (ported verbatim from KayakGenerator) -----

    def _get_area_fraction(self, x: float) -> float:
        x_norm = (2 * x) / self.L
        if abs(x_norm) >= 0.9999:
            return 0.0
        exponent = self.Cp / (1.0 - self.Cp)
        return 1 - abs(x_norm) ** exponent

    PLUMB_TRANSITION_FRAC = 0.05  # RFC 0004 §"Modified decay function"

    def _plumb_transition_decay(self, x: float) -> float:
        """Full-size until the final plumb transition near either end."""
        x_norm = abs((2 * x) / self.L)
        if x_norm <= 1.0 - self.PLUMB_TRANSITION_FRAC:
            return 1.0
        phase = (1.0 - x_norm) / self.PLUMB_TRANSITION_FRAC
        return float(max(0.0, min(1.0, phase)))

    def _rake_for_x(self, x: float) -> float:
        """Return the side-specific stem rake under the RFC 0028 X convention."""
        return self.hull.bow_rake if x <= 0.0 else self.hull.stern_rake

    def _is_exact_plumb_endpoint(self, x: float) -> bool:
        if np.isclose(x, -self.L / 2, rtol=0.0, atol=1e-12):
            return self.hull.bow_rake == 0.0
        if np.isclose(x, self.L / 2, rtol=0.0, atol=1e-12):
            return self.hull.stern_rake == 0.0
        return False

    def _end_decay(self, x: float) -> float:
        """Blended decay between fully raked (sqrt area) and fully plumb.

        ``hull.bow_rake`` and ``hull.stern_rake`` interpolate independently:
        1.0 reproduces the original raked loft (``sqrt(area_fraction)``),
        0.0 produces a near-vertical stem with the keel held at full draft
        until the last ``PLUMB_TRANSITION_FRAC`` of that half-length.
        Intermediate values blend linearly.
        """
        frac = self._get_area_fraction(x)
        if frac <= 0.0:
            return 0.0
        raked = np.sqrt(frac)
        plumb = self._plumb_transition_decay(x)
        rake = self._rake_for_x(x)
        return float(rake * raked + (1.0 - rake) * plumb)

    def _get_deck_height_scaling(self, x: float) -> float:
        x_norm = abs((2 * x) / self.L)
        if x_norm <= self.center_ratio:
            raked = 1.0
        else:
            decay_phase = (x_norm - self.center_ratio) / (1.0 - self.center_ratio)
            raked = 1 - decay_phase**2
        plumb = self._plumb_transition_decay(x)
        rake = self._rake_for_x(x)
        return float(rake * raked + (1.0 - rake) * plumb)

    def _get_slice_points(
        self,
        x: float,
        part_type: PartType,
        *,
        closed_body_endpoint: bool = False,
    ) -> np.ndarray:
        # _end_decay blends raked (sqrt-of-area-fraction, the legacy form)
        # with plumb (full-draft until the last PLUMB_TRANSITION_FRAC of the
        # half-length). With bow_rake/stern_rake=1.0 (default) it reproduces
        # the original loft bit-for-bit; the golden tests pin this.
        force_plumb_endpoint = closed_body_endpoint and self._is_exact_plumb_endpoint(x)
        hull_decay = 1.0 if force_plumb_endpoint else self._end_decay(x)

        local_B = self._half_beam_for_part(part_type) * hull_decay
        local_T = self.T * hull_decay
        deck_scale = 1.0 if force_plumb_endpoint else self._get_deck_height_scaling(x)
        local_Deck = (self.H - self.T) * deck_scale

        if local_B < 0.0001:
            local_B = 0.0001

        starboard_pts: list[list[float]] = []

        if part_type == "hull":
            angles = np.linspace(-np.pi / 2, 0, self.num_points)
            m = 2.0 + (self.Cm - 0.78) * 5
            for theta in angles:
                t_norm = (theta + np.pi / 2) / (np.pi / 2)
                y = local_B * (t_norm ** (1 / m))
                z = -local_T + (local_T * t_norm)
                starboard_pts.append([y, z])
        elif part_type == "deck":
            ys = np.linspace(0, local_B, self.num_points)
            for y in ys:
                y_norm = y / local_B
                z = local_Deck * (1 - y_norm**self.deck_power)
                starboard_pts.append([y, z])
        else:
            raise ValueError(f"unknown part_type: {part_type!r}")

        points: list[list[float]] = []
        for i in range(len(starboard_pts) - 1, -1, -1):
            p = starboard_pts[i]
            points.append([-p[0], p[1]])
        for i in range(1, len(starboard_pts)):
            p = starboard_pts[i]
            points.append([p[0], p[1]])

        return np.array(points)

    # ----- HullGeometry interface -----

    def section(self, x: float, part: PartType) -> np.ndarray:
        """Cross-section ring at ``x`` using the open-loft end-decay.

        This is the loft used by the open hull/deck STL surfaces. The result
        is *not* watertight at the ends — exact plumb-stem endpoint closure
        is handled separately by :meth:`section_for_closed_body`.
        """

        return self._get_slice_points(x, part)

    def section_for_closed_body(self, x: float, part: PartType) -> np.ndarray:
        """Cross-section ring at ``x`` honoring exact plumb-stem closure.

        Public entry point introduced by Phase 2 step 4 of
        ``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md``: replaces the
        previous ``_get_slice_points(..., closed_body_endpoint=True)``
        reach-in used by ``kayakgen.eval.closed_volume`` to assemble the
        generated closed-body. At endpoints where ``bow_rake==0`` or
        ``stern_rake==0`` the section snaps to the exact plumb-stem ring
        instead of decaying to zero; elsewhere the behaviour is identical
        to :meth:`section`.
        """

        return self._get_slice_points(x, part, closed_body_endpoint=True)

    def mesh(
        self, part: PartType, stations: int | None = None
    ) -> tuple[np.ndarray, np.ndarray]:
        n = stations if stations is not None else self.num_stations
        x_positions = np.linspace(-self.L / 2, self.L / 2, n)

        all_slices: list[np.ndarray] = []
        for x in x_positions:
            slice_pts = self._get_slice_points(x, part)
            full_pts = np.column_stack(
                (np.full(len(slice_pts), x), slice_pts[:, 0], slice_pts[:, 1])
            )
            all_slices.append(full_pts)

        vertices = np.vstack(all_slices)
        pts_per_slice = len(all_slices[0])
        num_slices = len(all_slices)

        faces: list[list[int]] = []
        for i in range(num_slices - 1):
            s = i * pts_per_slice
            t = (i + 1) * pts_per_slice
            for j in range(pts_per_slice - 1):
                c1, c2, n1, n2 = s + j, s + j + 1, t + j, t + j + 1
                if part == "hull":
                    faces.extend([[c1, n1, c2], [c2, n1, n2]])
                else:
                    faces.extend([[c1, n2, c2], [c2, n2, n1]])

        return vertices, np.array(faces)

    def waterplane(self, n: int = 200) -> np.ndarray:
        xs = np.linspace(-self.L / 2, self.L / 2, n)
        half = np.array([(self.B_wl / 2.0) * self._end_decay(x) for x in xs])
        return np.column_stack((xs, half))

    def keel_line(self, n: int = 200) -> np.ndarray:
        xs = np.linspace(-self.L / 2, self.L / 2, n)
        zs = np.array([-self.T * self._end_decay(x) for x in xs])
        return np.column_stack((xs, zs))

    def deck_centreline(self, n: int = 200) -> np.ndarray:
        xs = np.linspace(-self.L / 2, self.L / 2, n)
        zs = np.array([(self.H - self.T) * self._get_deck_height_scaling(x) for x in xs])
        return np.column_stack((xs, zs))

    def section_area(self, x: float) -> float:
        pts = self._get_slice_points(x, "hull")
        if len(pts) < 3:
            return 0.0
        ys = pts[:, 0]
        zs = pts[:, 1]
        return float(0.5 * abs(np.sum(ys * np.roll(zs, -1) - np.roll(ys, -1) * zs)))

    def half_breadth_grid(
        self, n_stations: int, n_depths: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Sample submerged half-breadth on a regular ``x``/depth grid."""
        xs = np.linspace(-self.L / 2, self.L / 2, n_stations)
        depths = np.linspace(0.0, self.T, n_depths)
        m = 2.0 + (self.Cm - 0.78) * 5
        f_grid = np.zeros((n_stations, n_depths))

        for i, x in enumerate(xs):
            decay = self._end_decay(x)
            local_T = self.T * decay
            local_half_B = (self.B_wl / 2.0) * decay
            if local_T <= 0 or local_half_B <= 0:
                continue
            for j, depth in enumerate(depths):
                if depth >= local_T:
                    continue
                t_norm = 1.0 - depth / local_T
                f_grid[i, j] = local_half_B * (t_norm ** (1.0 / m))

        return xs, depths, f_grid

    # ----- legacy API kept for the GUI shim and tests -----

    def get_mesh_arrays(
        self, part_type: PartType, stations: int | None = None
    ) -> tuple[np.ndarray, np.ndarray]:
        return self.mesh(part_type, stations)

    def generate_stl(self, part_type: PartType, filename: str) -> None:
        vertices, faces = self.mesh(part_type)
        data = np.zeros(len(faces), dtype=numpy_stl_mesh.Mesh.dtype)
        mesh_obj = numpy_stl_mesh.Mesh(data)
        for i, f in enumerate(faces):
            for j in range(3):
                mesh_obj.vectors[i][j] = vertices[f[j], :]
        mesh_obj.save(filename)
        print(f"Saved {filename}")


# ---------------------------------------------------------------------------
# RFC 0048 — Geometry V2 distribution-model strategy
# ---------------------------------------------------------------------------


def _sample_scalar_or_distribution(
    value: float | LongitudinalDistribution,
    xi: float,
) -> float:
    """Sample a scalar-or-:class:`LongitudinalDistribution` at one ``xi``."""

    if isinstance(value, (int, float)):
        return float(value)
    return float(value.sample(xi)[0])


def _section_round(
    half_breadth: float,
    draft: float,
    n: int,
    *,
    deadrise_rad: float,
) -> np.ndarray:
    """Round (sinh-shaped) family: today's default loft sampled by angle.

    Parametrization mirrors the lofted family's m=2 fall-back (rounded
    bottom) and lets ``deadrise_rad`` tilt the keel tangent upward,
    matching the "deeper-V" notion at small deadrise.
    """

    angles = np.linspace(-np.pi / 2.0, 0.0, n)
    t_norm = (angles + np.pi / 2.0) / (np.pi / 2.0)
    m = 2.0
    y = half_breadth * (t_norm ** (1.0 / m))
    # base z runs from -draft to 0 as t_norm sweeps 0->1
    z_base = -draft + draft * t_norm
    # deadrise raises the keel above -draft by tan(angle)*y_local
    z = z_base + np.tan(deadrise_rad) * y * (1.0 - t_norm)
    z = np.minimum(z, 0.0)
    z[-1] = 0.0
    y[-1] = half_breadth
    return np.column_stack((y, z))


def _section_shallow_arch(
    half_breadth: float,
    draft: float,
    n: int,
    *,
    deadrise_rad: float,
) -> np.ndarray:
    """Shallow-arch family: a flat-floored arc clipped from a wide circle.

    Models classic touring-kayak shallow-arch sections by sampling the
    upper quadrant of an ellipse with vertical-to-horizontal ratio
    ``draft / half_breadth`` and a small deadrise lift.

    The parametrization walks ``t`` from 0 (keel) to 1 (waterline)
    with ``y = half_breadth * sqrt(1 - (1-t)^2)`` (ellipse quadrant)
    and ``z = -draft * (1 - t)^1.5`` (slightly flat-bottomed lift).
    """

    t = np.linspace(0.0, 1.0, n)
    y = half_breadth * np.sqrt(np.clip(1.0 - (1.0 - t) ** 2.0, 0.0, None))
    z = -draft * (1.0 - t) ** 1.5
    z = z + np.tan(deadrise_rad) * y * (1.0 - t)
    # Clamp to the waterline; deadrise lift can push interior points
    # above z=0 otherwise.
    z = np.minimum(z, 0.0)
    z[-1] = 0.0
    y[-1] = half_breadth
    return np.column_stack((y, z))


def _section_shallow_v(
    half_breadth: float,
    draft: float,
    n: int,
    *,
    deadrise_rad: float,
    chine_radius: float,
) -> np.ndarray:
    """Shallow-V family: low deadrise filleted into a near-flat run.

    The section is two segments: a straight V from the keel up to a
    chine-radius transition, then a near-flat run out to the
    waterline. ``deadrise_rad`` (typically <= 15°) controls the slope.
    """

    base_deadrise = max(deadrise_rad, np.radians(5.0))
    return _section_v_with_fillet(
        half_breadth,
        draft,
        n,
        deadrise_rad=base_deadrise,
        chine_radius=chine_radius,
        slope_cap=np.tan(np.radians(20.0)),
    )


def _section_deep_v(
    half_breadth: float,
    draft: float,
    n: int,
    *,
    deadrise_rad: float,
    chine_radius: float,
) -> np.ndarray:
    """Deep-V family: high deadrise into a soft chine."""

    base_deadrise = max(deadrise_rad, np.radians(15.0))
    return _section_v_with_fillet(
        half_breadth,
        draft,
        n,
        deadrise_rad=base_deadrise,
        chine_radius=chine_radius,
        slope_cap=np.tan(np.radians(60.0)),
    )


def _section_v_with_fillet(
    half_breadth: float,
    draft: float,
    n: int,
    *,
    deadrise_rad: float,
    chine_radius: float,
    slope_cap: float,
) -> np.ndarray:
    """Shared V+fillet sampler used by shallow-V and deep-V families."""

    # If the V slope at the keel times the half-beam already meets the
    # full draft, the section is pure V; otherwise blend with a fillet.
    slope = min(np.tan(deadrise_rad), slope_cap)
    n_v = max(n // 2, 4)
    n_top = n - n_v
    # Bottom segment: straight V from keel to the chine point.
    chine_y = half_breadth * 0.6
    chine_z = -draft + slope * chine_y
    y_v = np.linspace(0.0, chine_y, n_v)
    z_v = -draft + slope * y_v
    # Optional radius transition is folded into the chine point itself
    # by softening the topside section with a quadratic.
    softness = max(chine_radius, 1e-4)
    y_top = np.linspace(chine_y, half_breadth, n_top + 1)[1:]
    rel = (y_top - chine_y) / max(half_breadth - chine_y, 1e-9)
    z_top = chine_z + (0.0 - chine_z) * (rel ** (1.0 + softness * 4.0))
    y = np.concatenate([y_v, y_top])
    z = np.concatenate([z_v, z_top])
    # Ensure last point is exactly at waterline.
    z[-1] = 0.0
    y[-1] = half_breadth
    return np.column_stack((y, z))


def _section_hard_chine(
    half_breadth: float,
    draft: float,
    n: int,
    *,
    deadrise_rad: float,
    chine_radius: float,
) -> np.ndarray:
    """Hard-chine family: single sharp bilge at ~60% of the half-beam.

    The section is two straight segments joined at the chine. ``chine_radius``
    rounds the corner by sampling additional points along an arc.
    """

    chine_y = half_breadth * 0.6
    slope = np.tan(max(deadrise_rad, np.radians(8.0)))
    chine_z = -draft + slope * chine_y
    radius = min(chine_radius, half_breadth * 0.4, draft * 0.4)
    n_v = max(n // 2 - 2, 3)
    n_arc = 5 if radius > 1e-4 else 0
    n_top = n - n_v - n_arc
    y_v = np.linspace(0.0, chine_y - radius, n_v)
    z_v = -draft + slope * y_v
    if n_arc > 0:
        thetas = np.linspace(np.pi, np.pi / 2.0, n_arc)
        cy = chine_y - radius
        cz = chine_z + radius * (1.0 - 0.0)  # center above the V slope by radius
        y_arc = cy - radius * np.cos(thetas)
        z_arc = cz + radius * np.sin(thetas) - radius
    else:
        y_arc = np.array([])
        z_arc = np.array([])
    # Topside: straight slab to the gunwale at z=0.
    y_top_start = chine_y if n_arc == 0 else float(y_arc[-1])
    z_top_start = chine_z if n_arc == 0 else float(z_arc[-1])
    y_top = np.linspace(y_top_start, half_breadth, n_top + 1)[1:]
    rel = (y_top - y_top_start) / max(half_breadth - y_top_start, 1e-9)
    z_top = z_top_start + (0.0 - z_top_start) * rel
    y = np.concatenate([y_v, y_arc, y_top])
    z = np.concatenate([z_v, z_arc, z_top])
    z[-1] = 0.0
    y[-1] = half_breadth
    return np.column_stack((y, z))


def _section_multi_chine(
    half_breadth: float,
    draft: float,
    n: int,
    *,
    deadrise_rad: float,
    chine_radius: float,
    chine_count: int,
) -> np.ndarray:
    """Multi-chine family: 2-4 polygonal facets between keel and gunwale.

    Builds an angle-stepped polygonal profile in the (y, z) plane,
    softened at each vertex by ``chine_radius``. ``chine_count`` is
    clamped to ``[2, 4]`` (the multi-chine literal value).
    """

    chine_count = max(2, min(int(chine_count), 4))
    base_deadrise = max(deadrise_rad, np.radians(5.0))
    # Define chine vertices at evenly-spaced fractions of the (y, z)
    # diagonal between the keel point (0, -draft) and gunwale
    # (half_breadth, 0). The first segment honors the deadrise slope.
    fractions = np.linspace(0.0, 1.0, chine_count + 2)  # includes keel + gunwale
    vertices_y: list[float] = []
    vertices_z: list[float] = []
    # Keel
    vertices_y.append(0.0)
    vertices_z.append(-draft)
    slope = np.tan(base_deadrise)
    for f in fractions[1:-1]:
        y_v = half_breadth * f
        z_v = -draft + slope * y_v * (1.0 - 0.5 * f) + (0.0 - (-draft)) * (f ** 2.2) * 0.7
        # Clamp z below or at waterline.
        z_v = min(z_v, -0.01 * draft)
        vertices_y.append(y_v)
        vertices_z.append(z_v)
    # Gunwale
    vertices_y.append(half_breadth)
    vertices_z.append(0.0)

    # Allocate sample budget per segment.
    n_segments = len(vertices_y) - 1
    per_seg = max(n // n_segments, 3)
    ys: list[float] = []
    zs: list[float] = []
    for i in range(n_segments):
        seg_n = per_seg + (1 if i == n_segments - 1 else 0)
        y_seg = np.linspace(vertices_y[i], vertices_y[i + 1], seg_n + 1)
        z_seg = np.linspace(vertices_z[i], vertices_z[i + 1], seg_n + 1)
        if i == 0:
            ys.extend(y_seg)
            zs.extend(z_seg)
        else:
            ys.extend(y_seg[1:])
            zs.extend(z_seg[1:])

    ys_arr = np.array(ys, dtype=float)
    zs_arr = np.array(zs, dtype=float)
    if len(ys_arr) != n:
        # Resample to exactly n points along the running arc length so
        # ring counts stay stable across stations.
        dy = np.diff(ys_arr)
        dz = np.diff(zs_arr)
        d = np.concatenate([[0.0], np.cumsum(np.hypot(dy, dz))])
        if d[-1] <= 0:
            d = np.linspace(0.0, 1.0, len(ys_arr))
        target = np.linspace(0.0, d[-1], n)
        ys_arr = np.interp(target, d, ys_arr)
        zs_arr = np.interp(target, d, zs_arr)
    # Smoothing of chine vertices is implicit in the resampling; the
    # ``chine_radius_m`` parameter modulates a final small averaging
    # pass for visual smoothness on the section ring.
    if chine_radius > 0.0 and len(ys_arr) >= 5:
        window = max(3, int(round(chine_radius * 1000.0)))
        window = min(window, 5)
        kernel = np.ones(window) / window
        ys_smooth = np.convolve(ys_arr, kernel, mode="same")
        zs_smooth = np.convolve(zs_arr, kernel, mode="same")
        # Preserve endpoints exactly.
        ys_smooth[0] = ys_arr[0]
        ys_smooth[-1] = ys_arr[-1]
        zs_smooth[0] = zs_arr[0]
        zs_smooth[-1] = zs_arr[-1]
        ys_arr, zs_arr = ys_smooth, zs_smooth
    return np.column_stack((ys_arr, zs_arr))


_CROSS_SECTION_FAMILIES = {
    "round": _section_round,
    "shallow_arch": _section_shallow_arch,
    "shallow_v": _section_shallow_v,
    "deep_v": _section_deep_v,
    "hard_chine": _section_hard_chine,
    "multi_chine": _section_multi_chine,
}


class DistributionV2Geometry(HullGeometry):
    """Distribution-model strategy implementing RFC 0048.

    The canonical body is the source of truth. Every public accessor
    consumes the same per-station ring derived from the spec's
    longitudinal distributions and the chosen cross-section family.

    * :meth:`section_for_closed_body` returns the canonical ring (port
      ↔ starboard ↔ deck, walking counterclockwise in the (y, z) plane)
      that the RFC 0022 generated-closed-body builder consumes.
    * :meth:`section` returns the *derived* open inspection section for
      ``part``: the lower hull arc for ``hull`` and the upper deck arc
      for ``deck``. Both are sliced out of the canonical ring.

    The two halves agree by construction: the open inspection STL is
    derived from the canonical body, so the closed-body diagnostics
    chain (RFC 0021 + RFC 0023 + RFC 0040 + RFC 0045) needs no separate
    code path.
    """

    NUM_STATIONS = 150
    NUM_POINTS = 40

    def __init__(self, hull: Hull) -> None:
        if hull.distribution_v2 is None:
            raise ValueError("DistributionV2Geometry requires hull.distribution_v2 to be set")
        self.hull = hull
        self.spec: DistributionV2Spec = hull.distribution_v2
        self.num_stations = self.NUM_STATIONS
        self.num_points = self.NUM_POINTS

    # ----- coordinate helpers -----

    @property
    def L(self) -> float:
        return float(self.hull.length_m)

    def _xi_for_x(self, x: float) -> float:
        """Convert physical station ``x`` (m) to normalized ``xi`` ∈ [-1, 1]."""

        return float((2.0 * x) / self.L)

    def _half_breadth_at(self, x: float) -> float:
        xi = self._xi_for_x(x)
        return max(0.0, float(self.spec.waterline_half_breadth.sample(xi)[0]))

    def _draft_at(self, x: float) -> float:
        xi = self._xi_for_x(x)
        return max(0.0, float(self.spec.draft_profile.sample(xi)[0]))

    def _deck_height_at(self, x: float) -> float:
        xi = self._xi_for_x(x)
        return max(0.0, float(self.spec.deck_freeboard.sample(xi)[0]))

    def _rocker_at(self, x: float) -> float:
        xi = self._xi_for_x(x)
        return float(self.spec.rocker.sample(xi)[0])

    def _deadrise_rad_at(self, x: float) -> float:
        xi = self._xi_for_x(x)
        deg = _sample_scalar_or_distribution(self.spec.deadrise_deg, xi)
        return float(np.radians(deg))

    def _chine_radius_at(self, x: float) -> float:
        xi = self._xi_for_x(x)
        value = _sample_scalar_or_distribution(self.spec.chine_radius_m, xi)
        return float(max(value, 0.0))

    # ----- canonical body construction -----

    def _hull_quarter_section(self, x: float) -> np.ndarray:
        """Sample the starboard-quarter hull arc at ``x`` (Nx2 y/z)."""

        family: CrossSectionFamily = self.spec.cross_section_family
        half_b = self._half_breadth_at(x)
        draft = self._draft_at(x)
        deadrise_rad = self._deadrise_rad_at(x)
        chine_radius = self._chine_radius_at(x)
        # Shift the entire arc by the rocker contribution so the keel
        # tracks the explicit rocker distribution.
        rocker = self._rocker_at(x)

        # Endpoints can have zero half_breadth or zero draft. Pin a
        # near-zero arc so the section ring count is stable across
        # stations (the closed-body builder and the meshing helpers
        # require an Nx2 array of the same width at every station).
        half_b_safe = max(half_b, 1e-4)
        draft_safe = max(draft, 1e-4)

        sampler = _CROSS_SECTION_FAMILIES[family]
        if family in ("round", "shallow_arch"):
            arc = sampler(half_b_safe, draft_safe, self.num_points, deadrise_rad=deadrise_rad)
        elif family in ("shallow_v", "deep_v", "hard_chine"):
            arc = sampler(
                half_b_safe,
                draft_safe,
                self.num_points,
                deadrise_rad=deadrise_rad,
                chine_radius=chine_radius,
            )
        else:
            arc = sampler(
                half_b_safe,
                draft_safe,
                self.num_points,
                deadrise_rad=deadrise_rad,
                chine_radius=chine_radius,
                chine_count=self.spec.multi_chine_count,
            )
        if rocker != 0.0:
            # The explicit rocker shifts only the keel: linearly
            # attenuate the lift from full at y = 0 to zero at the
            # gunwale so the waterline ring count and gunwale z stay
            # invariant across stations.
            arc = arc.copy()
            ys = arc[:, 0]
            y_max = float(max(ys.max(), 1e-9))
            attenuation = 1.0 - ys / y_max
            lift = rocker * attenuation
            arc[:, 1] = np.minimum(arc[:, 1] + lift, 0.0)
        return arc

    def _deck_quarter_section(self, x: float) -> np.ndarray:
        """Sample the starboard-quarter deck arc at ``x`` (Nx2 y/z)."""

        half_b = self._half_breadth_at(x)
        freeboard = self._deck_height_at(x)
        half_b_safe = max(half_b, 1e-4)
        freeboard_safe = max(freeboard, 1e-4)
        ys = np.linspace(0.0, half_b_safe, self.num_points)
        rel = ys / half_b_safe
        # Use bow_flare to bias deck arch on the forward half.
        flare = float(np.radians(self.spec.bow_flare_deg)) if x < 0.0 else 0.0
        z = freeboard_safe * (1.0 - rel ** (4.0 + 6.0 * flare))
        return np.column_stack((ys, z))

    def _mirror_for_part(self, quarter: np.ndarray, part: PartType) -> np.ndarray:
        """Mirror a quarter section (port → starboard, like LoftedHullGeometry)."""

        points: list[list[float]] = []
        for i in range(len(quarter) - 1, -1, -1):
            p = quarter[i]
            points.append([-float(p[0]), float(p[1])])
        for i in range(1, len(quarter)):
            p = quarter[i]
            points.append([float(p[0]), float(p[1])])
        return np.asarray(points, dtype=float)

    # ----- HullGeometry interface -----

    def section(self, x: float, part: PartType) -> np.ndarray:
        """Open inspection section derived from the canonical body ring.

        For ``hull`` this is the lower arc (z <= 0); for ``deck`` this
        is the upper arc (z >= 0). Both are mirrored port → starboard,
        matching :class:`LoftedHullGeometry.section` shape conventions.
        """

        if part == "hull":
            arc = self._hull_quarter_section(x)
        elif part == "deck":
            arc = self._deck_quarter_section(x)
        else:
            raise ValueError(f"unknown part_type: {part!r}")
        return self._mirror_for_part(arc, part)

    def section_for_closed_body(self, x: float, part: PartType) -> np.ndarray:
        """Canonical closed-body section ring for ``part`` at ``x``.

        The closed-body builder takes hull and deck sections and joins
        them into a single counterclockwise ring; for the V2 geometry
        the two halves are derived from the same per-station spec values
        so they meet at the gunwale by construction.
        """

        return self.section(x, part)

    def mesh(
        self, part: PartType, stations: int | None = None
    ) -> tuple[np.ndarray, np.ndarray]:
        n = stations if stations is not None else self.num_stations
        x_positions = np.linspace(-self.L / 2.0, self.L / 2.0, n)

        all_slices: list[np.ndarray] = []
        for x in x_positions:
            slice_pts = self.section(float(x), part)
            full_pts = np.column_stack(
                (np.full(len(slice_pts), x), slice_pts[:, 0], slice_pts[:, 1])
            )
            all_slices.append(full_pts)

        vertices = np.vstack(all_slices)
        pts_per_slice = len(all_slices[0])
        num_slices = len(all_slices)

        faces: list[list[int]] = []
        for i in range(num_slices - 1):
            s = i * pts_per_slice
            t = (i + 1) * pts_per_slice
            for j in range(pts_per_slice - 1):
                c1, c2, n1, n2 = s + j, s + j + 1, t + j, t + j + 1
                if part == "hull":
                    faces.extend([[c1, n1, c2], [c2, n1, n2]])
                else:
                    faces.extend([[c1, n2, c2], [c2, n2, n1]])

        return vertices, np.array(faces)

    def waterplane(self, n: int = 200) -> np.ndarray:
        xs = np.linspace(-self.L / 2.0, self.L / 2.0, n)
        half = np.array([self._half_breadth_at(float(x)) for x in xs])
        return np.column_stack((xs, half))

    def keel_line(self, n: int = 200) -> np.ndarray:
        xs = np.linspace(-self.L / 2.0, self.L / 2.0, n)
        zs = np.array(
            [-self._draft_at(float(x)) + self._rocker_at(float(x)) for x in xs]
        )
        zs = np.minimum(zs, 0.0)
        return np.column_stack((xs, zs))

    def deck_centreline(self, n: int = 200) -> np.ndarray:
        xs = np.linspace(-self.L / 2.0, self.L / 2.0, n)
        zs = np.array([self._deck_height_at(float(x)) for x in xs])
        return np.column_stack((xs, zs))

    def section_area(self, x: float) -> float:
        pts = self.section(x, "hull")
        if len(pts) < 3:
            return 0.0
        ys = pts[:, 0]
        zs = pts[:, 1]
        return float(0.5 * abs(np.sum(ys * np.roll(zs, -1) - np.roll(ys, -1) * zs)))

    def half_breadth_grid(
        self, n_stations: int, n_depths: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        xs = np.linspace(-self.L / 2.0, self.L / 2.0, n_stations)
        max_draft = float(max(self._draft_at(float(x)) for x in xs))
        depths = np.linspace(0.0, max(max_draft, 1e-9), n_depths)
        f_grid = np.zeros((n_stations, n_depths))
        for i, x in enumerate(xs):
            section = self.section(float(x), "hull")
            half_b = self._half_breadth_at(float(x))
            local_draft = self._draft_at(float(x))
            if half_b <= 0 or local_draft <= 0:
                continue
            # Sample the starboard arc only.
            arc = section[section[:, 0] >= 0]
            arc = arc[np.argsort(arc[:, 1])]  # by z, deep first
            for j, depth in enumerate(depths):
                if depth >= local_draft:
                    continue
                z_query = -depth
                # interpolate y at z_query along arc.
                zs_arc = arc[:, 1]
                ys_arc = arc[:, 0]
                if z_query <= zs_arc[0]:
                    f_grid[i, j] = float(ys_arc[0])
                elif z_query >= zs_arc[-1]:
                    f_grid[i, j] = float(ys_arc[-1])
                else:
                    f_grid[i, j] = float(np.interp(z_query, zs_arc, ys_arc))
        return xs, depths, f_grid
