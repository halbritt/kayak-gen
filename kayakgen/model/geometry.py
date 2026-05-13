"""HullGeometry interface and the lofted parametric implementation.

The lofted implementation here is a port of the original ``KayakGenerator``
(``generator.py``) onto the ``Hull`` aggregate. The math is unchanged — the
golden tests pin its behavior — but the parameters are owned by ``Hull``
and a small set of public accessors (``waterplane``, ``keel_line``,
``deck_centreline``, ``section_area``) replace the underscore-prefixed
calls the GUI used to reach for.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

import numpy as np
from stl import mesh as numpy_stl_mesh

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
        return self._get_slice_points(x, part)

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
