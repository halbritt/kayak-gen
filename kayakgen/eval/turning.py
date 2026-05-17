"""Turning and edged-waterline metrics (RFC 0053).

Computes a geometric-proxy ``TurningMetrics`` block from a :class:`Hull` by
intersecting heeled stations against the still waterline (z=0). The metric
block is purely additive on :class:`EvaluationResult` and opt-in via the
``--turning`` flag on ``kayakgen evaluate`` or
``evaluators.turning_metrics`` on a :class:`SweepSpec`.

The integrators here intentionally do NOT call any other evaluator
(hydrostatics, stability, resistance, CFD): turning is its own domain
service over the :class:`Hull` aggregate. The numbers it emits carry raw
metric units (m, m^2) and a ``method="geometric_proxy_v1"`` literal so
downstream readers can tell them apart from any future dynamic / measured
turning evaluator.
"""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from kayakgen.model.hull import Hull


class TurningMetrics(BaseModel):
    """Geometric turning-proxy metrics derived from heeled cross-sections.

    All numeric fields carry raw metric units (no normalisation):

    * ``edged_waterline_length_m`` / ``upright_waterline_length_m``: X-span
      of stations whose section dips below z=0 at the requested heel and at
      heel=0 respectively.
    * ``lateral_plane_shift_m``: signed X-shift of the submerged-area
      centroid between heeled and upright stations (positive = shifts
      toward +x).
    * ``rocker_weighted_maneuverability_signal``: ``sum_stations(|rocker(x)| *
      depth(x)) / waterline_length`` (m). The combined rocker-weighted
      signal is NOT split bow/stern in v1.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    heel_deg: float = Field(ge=0.0, le=60.0)
    edged_waterline_length_m: float = Field(ge=0.0)
    upright_waterline_length_m: float = Field(ge=0.0)
    lateral_plane_shift_m: float
    rocker_weighted_maneuverability_signal: float = Field(ge=0.0)
    method: Literal["geometric_proxy_v1"] = "geometric_proxy_v1"
    notes: list[str] = Field(default_factory=list)


def _station_submerged_area_and_centroid(
    section_yz: np.ndarray, heel_rad: float
) -> tuple[float, float, float]:
    """Return ``(submerged_area, y_centroid, min_z_after_rotation)``.

    ``section_yz`` is the (y, z) cross-section ring at one station. The
    ring is rotated about the X axis by ``heel_rad`` (positive heel rolls
    the +y side of the hull downward into the water) and then clipped at
    z=0. Returns the area below the waterline and the y-centroid of that
    clipped polygon.
    """
    if section_yz.shape[0] < 3:
        return 0.0, 0.0, 0.0

    cos_h = math.cos(heel_rad)
    sin_h = math.sin(heel_rad)
    ys = section_yz[:, 0]
    zs = section_yz[:, 1]
    # Rotate about X. Positive heel pushes +y down (z decreases on the
    # +y side, z increases on the -y side), which matches the physical
    # convention of edging toward starboard.
    ys_rot = ys * cos_h + zs * sin_h
    zs_rot = -ys * sin_h + zs * cos_h
    min_z = float(zs_rot.min())

    # Sutherland-Hodgman style clip against z<=0 half-plane on the rotated
    # ring, treating it as a closed polygon in (y_rot, z_rot).
    clipped = _clip_below_waterline(np.column_stack((ys_rot, zs_rot)))
    if clipped.shape[0] < 3:
        return 0.0, 0.0, min_z

    yy = clipped[:, 0]
    zz = clipped[:, 1]
    cross = yy * np.roll(zz, -1) - np.roll(yy, -1) * zz
    area_signed = 0.5 * float(cross.sum())
    area = abs(area_signed)
    if area <= 0.0:
        return 0.0, 0.0, min_z

    # Polygon centroid (y component is enough for lateral-plane shift).
    cy = float(
        ((yy + np.roll(yy, -1)) * cross).sum() / (6.0 * area_signed)
    )
    return area, cy, min_z


def _clip_below_waterline(ring: np.ndarray) -> np.ndarray:
    """Clip a closed polygon to ``z <= 0`` using Sutherland-Hodgman.

    ``ring`` is an ``(N, 2)`` array of ``(y, z)`` vertices in order.
    Returns the clipped polygon's vertices (possibly empty).
    """
    if ring.shape[0] < 3:
        return np.empty((0, 2), dtype=float)
    output: list[tuple[float, float]] = []
    n = ring.shape[0]
    for i in range(n):
        cur = ring[i]
        prev = ring[i - 1]
        cur_inside = cur[1] <= 0.0
        prev_inside = prev[1] <= 0.0
        if cur_inside:
            if not prev_inside:
                output.append(_intersect_waterline(prev, cur))
            output.append((float(cur[0]), float(cur[1])))
        elif prev_inside:
            output.append(_intersect_waterline(prev, cur))
    return np.array(output, dtype=float) if output else np.empty((0, 2), dtype=float)


def _intersect_waterline(p1: np.ndarray, p2: np.ndarray) -> tuple[float, float]:
    """Linear-interpolate the point where segment ``p1->p2`` crosses z=0."""
    dz = p2[1] - p1[1]
    if dz == 0.0:
        return float(p1[0]), 0.0
    t = -p1[1] / dz
    y = p1[0] + t * (p2[0] - p1[0])
    return float(y), 0.0


def _station_rocker_depth_terms(
    xs: np.ndarray, zs: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(|rocker_at_x|, submerged_depth_at_x)`` for the keel line.

    Rocker at station x is interpreted as the rise of the keel above the
    deepest point: ``z_keel(x) - min(z_keel)`` (always >= 0 for a hull
    whose keel is at or below the waterline). The submerged depth is the
    absolute distance below z=0 of the keel at that station.
    """
    deepest = float(zs.min())
    rocker = zs - deepest
    depth = np.maximum(-zs, 0.0)
    return np.abs(rocker), depth


def evaluate_turning_metrics(
    hull: Hull, *, heel_deg: float = 8.0
) -> TurningMetrics:
    """Compute :class:`TurningMetrics` for ``hull`` at ``heel_deg``.

    The integrators walk each station of the lofted hull (open hull
    surface), rotate its (y, z) cross-section about X by ``heel_deg``,
    and intersect with the still waterline at z=0. The edged waterline
    length is the X-span of stations whose rotated section dips below
    the waterline; the lateral-plane shift is the X-centroid of the
    submerged-area column at heel minus at upright.
    """
    if not 0.0 <= heel_deg <= 60.0:
        raise ValueError("heel_deg must be in [0, 60]")

    geom = hull.to_geometry()
    n_stations = max(64, int(getattr(geom, "num_stations", 150)))
    xs = np.linspace(-hull.length_m / 2.0, hull.length_m / 2.0, n_stations)
    heel_rad = math.radians(heel_deg)

    edged_submerged_x: list[float] = []
    upright_submerged_x: list[float] = []
    edged_area_at_x: list[float] = []
    upright_area_at_x: list[float] = []

    for x in xs:
        section = geom.section(float(x), "hull")
        if section.shape[0] < 3:
            continue
        area_h, _cy_h, min_z_h = _station_submerged_area_and_centroid(
            section, heel_rad
        )
        area_u, _cy_u, min_z_u = _station_submerged_area_and_centroid(
            section, 0.0
        )
        # A station "dips below z=0" iff some point of the rotated ring is
        # at or below the still waterline. Use ``<= 0`` so the lofted hull's
        # tip stations (whose rotated max-z sits exactly on the waterline)
        # still count as submerged at heel=0; otherwise the upright edged
        # waterline length would mistakenly exclude the tips.
        if min_z_h <= 0.0:
            edged_submerged_x.append(float(x))
            edged_area_at_x.append(area_h)
        if min_z_u <= 0.0:
            upright_submerged_x.append(float(x))
            upright_area_at_x.append(area_u)

    edged_len = (
        float(max(edged_submerged_x) - min(edged_submerged_x))
        if len(edged_submerged_x) >= 2
        else 0.0
    )
    upright_len = (
        float(max(upright_submerged_x) - min(upright_submerged_x))
        if len(upright_submerged_x) >= 2
        else 0.0
    )

    # Lateral plane shift = X-centroid of submerged area at heel minus at
    # upright. Submerged area at a station times x gives a first moment;
    # divide by the area sum to get the X-centroid. Sum form (no integration
    # weights) keeps stations on equal footing.
    def _x_centroid(x_vals: list[float], area_vals: list[float]) -> float:
        total = sum(area_vals)
        if total <= 0.0:
            return 0.0
        return float(
            sum(xv * av for xv, av in zip(x_vals, area_vals)) / total
        )

    edged_xc = _x_centroid(edged_submerged_x, edged_area_at_x)
    upright_xc = _x_centroid(upright_submerged_x, upright_area_at_x)
    lateral_shift = edged_xc - upright_xc

    # Rocker-weighted maneuverability: sum_stations(|rocker(x)| * depth(x))
    # divided by waterline length (m, m, /m -> m). The upright waterline
    # length is used as the normalising length so the signal is independent
    # of heel angle for a given hull at its design draft.
    keel = geom.keel_line(n=n_stations)
    keel_xs = keel[:, 0]
    keel_zs = keel[:, 1]
    rocker_abs, depth = _station_rocker_depth_terms(keel_xs, keel_zs)
    rocker_sum = float(np.sum(rocker_abs * depth))
    waterline_for_norm = upright_len if upright_len > 0.0 else hull.length_m
    rocker_signal = rocker_sum / waterline_for_norm if waterline_for_norm > 0 else 0.0

    notes: list[str] = []
    if heel_deg == 0.0:
        notes.append("heel_deg=0; edged metrics equal upright metrics by construction")
    if not edged_submerged_x:
        notes.append("no station of the heeled hull dips below z=0")

    return TurningMetrics(
        heel_deg=float(heel_deg),
        edged_waterline_length_m=edged_len,
        upright_waterline_length_m=upright_len,
        lateral_plane_shift_m=float(lateral_shift),
        rocker_weighted_maneuverability_signal=float(rocker_signal),
        notes=notes,
    )
