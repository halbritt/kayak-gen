"""Form metrics read off the generated sections (RFC 0089).

Two geometric measures a designer otherwise takes by hand:

* the race-class length-to-beam ratio, waterline length over waterline
  beam with the hull floating at a stated draft below its lowest keel
  point (the Sound Rowers kayak classes assume 4 in);
* the same waterline beam as a fraction of overall length, which the
  USCA kayak classes limit (Sea Kayak: at least 8.5% at 4 in);
* paddle clearance, the overall beam of hull and deck in a zone forward
  of a reference station, where the blade enters the water;
* foot room, the largest centred box that fits between hull and deck at
  the foot station, measured on the outer surface;
* knuckles, the corner in the sections where hull meets topside at the
  design waterline and the sharpest corner above it, which a fair
  topside and deck edge keep small.

Like turning metrics (RFC 0053) this evaluator reads only the
:class:`Hull` geometry and calls no other evaluator. The bow is at
``-x``; "forward" is toward ``-x``.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from kayakgen.model.hull import Hull

DEFAULT_CLASS_RATIO_DRAFT_M = 0.1016
DEFAULT_CATCH_ZONE_FORWARD_M: tuple[float, float] = (0.6, 1.2)
DEFAULT_CATCH_UPPER_HEIGHT_M = 0.10
DEFAULT_FOOT_STATION_FORWARD_M = 1.0
DEFAULT_FOOT_BOX_WIDTH_M = 0.30
DEFAULT_FOOT_BOX_HEIGHT_M = 0.30
DEFAULT_KNUCKLE_PROBE_M = 0.002
DEFAULT_KNUCKLE_SPAN_XI = 0.9
_FOOT_BOX_SAMPLES = 41
_STATIONS = 401


class FormMetrics(BaseModel):
    """Class ratio and paddle-clearance beams for one hull.

    ``class_beam_length_fraction`` is the class waterline beam divided
    by the overall length. ``class_length_beam_ratio`` is ``None`` when the stated draft leaves
    no waterline (deeper than the body or zero breadth). The reference
    station is the centroid of the design-waterline section areas unless
    the caller supplies one; it stands in for the seat.
    ``catch_zone_max_upper_beam_m`` counts only the body at or above
    ``catch_upper_height_m`` over the design waterline, which is what a
    paddle shaft has to clear; unlike ``catch_zone_max_beam_m`` it falls
    when the sheer is narrower than the waterline.

    Foot room is read at the station ``foot_station_forward_m`` forward
    of the reference station. ``foot_clear_height_m`` is the height of
    the tallest centred box ``foot_box_width_m`` wide that fits between
    hull and deck there; ``foot_clear_width_m`` is the width of the
    widest centred box ``foot_box_height_m`` tall. Both are taken on the
    outer surface: shell thickness, a seat, pedals and a cockpit are not
    modelled. The foot fields are ``None`` in blocks written before they
    existed.

    Knuckles are corners in the section outline. The turn at a point is
    the angle between the chord from ``knuckle_probe_m`` before it and
    the chord to ``knuckle_probe_m`` after it, along the outline, so a
    sharp corner reads its full angle and a curve of radius ``r`` reads
    about ``knuckle_probe_m / r`` radians. ``waterline_knuckle_max_deg``
    is the largest turn at the joint of the hull ring and the deck ring,
    which is the design waterline when the hull has topsides and the
    gunwale when it has none. ``upper_knuckle_max_deg`` is the largest
    turn above that joint: the topside and the deck edge, leaving out
    the deck centreline. Both are taken at stations within
    ``knuckle_span_xi`` of the half length either side of the middle,
    and each has the station where it occurs. The outline is the
    generated polyline, so a turn is never read finer than its point
    spacing. The knuckle fields are ``None`` in blocks written before
    they existed.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    class_ratio_draft_m: float = Field(gt=0.0)
    class_waterline_length_m: float = Field(ge=0.0)
    class_waterline_beam_m: float = Field(ge=0.0)
    class_length_beam_ratio: float | None = None
    overall_length_m: float = Field(gt=0.0)
    class_beam_length_fraction: float = Field(ge=0.0)
    reference_station_x_m: float
    reference_station_origin: Literal["section_area_centroid", "supplied"]
    catch_zone_forward_m: tuple[float, float]
    catch_zone_max_beam_m: float = Field(ge=0.0)
    catch_upper_height_m: float = Field(ge=0.0)
    catch_zone_max_upper_beam_m: float = Field(ge=0.0)
    beam_at_reference_m: float = Field(ge=0.0)
    max_overall_beam_m: float = Field(ge=0.0)
    foot_station_forward_m: float | None = Field(default=None, ge=0.0)
    foot_box_width_m: float | None = Field(default=None, gt=0.0)
    foot_box_height_m: float | None = Field(default=None, gt=0.0)
    foot_clear_height_m: float | None = Field(default=None, ge=0.0)
    foot_clear_width_m: float | None = Field(default=None, ge=0.0)
    foot_station_beam_m: float | None = Field(default=None, ge=0.0)
    foot_station_depth_m: float | None = Field(default=None, ge=0.0)
    knuckle_probe_m: float | None = Field(default=None, gt=0.0)
    knuckle_span_xi: float | None = Field(default=None, gt=0.0, le=1.0)
    waterline_knuckle_max_deg: float | None = Field(default=None, ge=0.0, le=180.0)
    waterline_knuckle_x_m: float | None = None
    upper_knuckle_max_deg: float | None = Field(default=None, ge=0.0, le=180.0)
    upper_knuckle_x_m: float | None = None
    upper_knuckle_height_m: float | None = None
    method: Literal["section_envelope_v1"] = "section_envelope_v1"
    notes: list[str] = Field(default_factory=list)


def _half_breadth_at_height(rings: list[np.ndarray], z: float) -> float:
    """Largest ``|y|`` at which any ring polyline crosses height ``z``."""

    best = 0.0
    for ring in rings:
        if ring.shape[0] < 2:
            continue
        y0, z0 = ring[:-1, 0], ring[:-1, 1]
        y1, z1 = ring[1:, 0], ring[1:, 1]
        crossing = ((z0 - z) * (z1 - z) <= 0.0) & (z0 != z1)
        if crossing.any():
            t = (z - z0[crossing]) / (z1[crossing] - z0[crossing])
            best = max(best, float(np.abs(y0[crossing] + t * (y1[crossing] - y0[crossing])).max()))
        level = (z0 == z) & (z1 == z)
        if level.any():
            best = max(best, float(np.abs(np.concatenate((y0[level], y1[level]))).max()))
    return best


def _breadth_at_or_above(ring: np.ndarray, z: float) -> float:
    """Largest ``|y|`` of the ring polyline at heights of ``z`` or more."""

    if ring.shape[0] == 0:
        return 0.0
    above = ring[:, 1] >= z
    best = float(np.abs(ring[above, 0]).max()) if above.any() else 0.0
    return max(best, _half_breadth_at_height([ring], z))


def _vertical_chord(rings: list[np.ndarray], y: float) -> tuple[float, float] | None:
    """Lowest and highest ``z`` at which the ring polylines cross offset ``y``."""

    lows: list[float] = []
    highs: list[float] = []
    for ring in rings:
        if ring.shape[0] < 2:
            continue
        y0, z0 = ring[:-1, 0], ring[:-1, 1]
        y1, z1 = ring[1:, 0], ring[1:, 1]
        crossing = ((y0 - y) * (y1 - y) <= 0.0) & (y0 != y1)
        if crossing.any():
            t = (y - y0[crossing]) / (y1[crossing] - y0[crossing])
            z = z0[crossing] + t * (z1[crossing] - z0[crossing])
            lows.append(float(z.min()))
            highs.append(float(z.max()))
        upright = (y0 == y) & (y1 == y)
        if upright.any():
            z = np.concatenate((z0[upright], z1[upright]))
            lows.append(float(z.min()))
            highs.append(float(z.max()))
    if not lows:
        return None
    return min(lows), max(highs)


def _box_clear_height(rings: list[np.ndarray], width: float) -> float:
    """Height of the tallest centred box ``width`` wide inside the section."""

    floor = -np.inf
    roof = np.inf
    for y in np.linspace(-width / 2.0, width / 2.0, _FOOT_BOX_SAMPLES):
        chord = _vertical_chord(rings, float(y))
        if chord is None:
            return 0.0
        floor = max(floor, chord[0])
        roof = min(roof, chord[1])
    return max(float(roof - floor), 0.0)


def _box_clear_width(rings: list[np.ndarray], height: float, max_width: float) -> float:
    """Width of the widest centred box ``height`` tall inside the section."""

    if max_width <= 0.0 or _box_clear_height(rings, 0.0) < height:
        return 0.0
    if _box_clear_height(rings, max_width) >= height:
        return float(max_width)
    low, high = 0.0, float(max_width)
    for _ in range(40):
        mid = 0.5 * (low + high)
        if _box_clear_height(rings, mid) >= height:
            low = mid
        else:
            high = mid
    return low


def _crossing_x(x_in: float, v_in: float, x_out: float, v_out: float) -> float:
    """Station where a positive value ``v_in`` reaches zero toward ``x_out``."""

    if v_in <= 0.0 or v_out >= v_in:
        return x_in
    return x_in + (x_out - x_in) * v_in / (v_in - v_out)


def _section_knuckles(
    hull_ring: np.ndarray, deck_ring: np.ndarray, probe: float
) -> tuple[float, float, float]:
    """Turn of one half section at the hull-to-deck joint and the sharpest turn above it.

    Returns ``(joint_deg, upper_deg, upper_height_m)``. The half outline
    runs from the keel up the hull ring to the joint and on along the
    deck ring to the centreline. The turn at a point is the angle between
    the chord from ``probe`` before it and the chord to ``probe`` after
    it, along the outline. "Above" starts ``probe`` past the joint and
    stops ``probe`` short of the centreline, which leaves out the
    centreline ridge.
    """

    if hull_ring.shape[0] < 3 or deck_ring.shape[0] < 3:
        return 0.0, 0.0, 0.0
    lower = hull_ring[hull_ring.shape[0] // 2 :]
    upper = deck_ring[deck_ring.shape[0] // 2 :][::-1]

    def clean(points: np.ndarray) -> np.ndarray:
        steps = np.linalg.norm(np.diff(points, axis=0), axis=1)
        return points[np.concatenate(([True], steps > 1e-12))]

    lower, upper = clean(lower), clean(upper)
    if lower.shape[0] < 2 or upper.shape[0] < 2:
        return 0.0, 0.0, 0.0
    outline = np.vstack((lower, upper[1:]))
    arc = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(outline, axis=0), axis=1))))
    joint = float(arc[lower.shape[0] - 1])
    end = float(arc[-1])

    def point(s: np.ndarray) -> np.ndarray:
        return np.column_stack((np.interp(s, arc, outline[:, 0]), np.interp(s, arc, outline[:, 1])))

    def turn_at(s: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        here = point(s)
        before = here - point(s - probe)
        after = point(s + probe) - here
        cross = before[:, 0] * after[:, 1] - before[:, 1] * after[:, 0]
        dot = (before * after).sum(axis=1)
        return np.degrees(np.abs(np.arctan2(cross, dot))), here[:, 1]

    joint_deg = 0.0
    if joint >= probe and end - joint >= probe:
        joint_deg = float(turn_at(np.array([joint]))[0][0])
    start, stop = joint + probe, end - probe
    if stop <= start:
        return joint_deg, 0.0, 0.0
    count = max(int(np.ceil((stop - start) / (probe / 4.0))), 1) + 1
    at = np.unique(np.concatenate((np.linspace(start, stop, count), arc[(arc >= start) & (arc <= stop)])))
    turn, height = turn_at(at)
    worst = int(np.argmax(turn))
    return joint_deg, float(turn[worst]), float(height[worst])


def evaluate_form_metrics(
    hull: Hull,
    *,
    class_ratio_draft_m: float = DEFAULT_CLASS_RATIO_DRAFT_M,
    catch_zone_forward_m: tuple[float, float] = DEFAULT_CATCH_ZONE_FORWARD_M,
    reference_station_x_m: float | None = None,
    catch_upper_height_m: float = DEFAULT_CATCH_UPPER_HEIGHT_M,
    foot_station_forward_m: float = DEFAULT_FOOT_STATION_FORWARD_M,
    foot_box_width_m: float = DEFAULT_FOOT_BOX_WIDTH_M,
    foot_box_height_m: float = DEFAULT_FOOT_BOX_HEIGHT_M,
    knuckle_probe_m: float = DEFAULT_KNUCKLE_PROBE_M,
    knuckle_span_xi: float = DEFAULT_KNUCKLE_SPAN_XI,
) -> FormMetrics:
    """Compute :class:`FormMetrics` for ``hull``."""

    if not np.isfinite(class_ratio_draft_m) or class_ratio_draft_m <= 0.0:
        raise ValueError("class_ratio_draft_m must be positive and finite")
    near, far = (float(catch_zone_forward_m[0]), float(catch_zone_forward_m[1]))
    if not (np.isfinite(near) and np.isfinite(far)) or far <= near:
        raise ValueError("catch_zone_forward_m must be an increasing (near, far) pair")
    if not np.isfinite(catch_upper_height_m) or catch_upper_height_m < 0.0:
        raise ValueError("catch_upper_height_m must be nonnegative and finite")
    if not np.isfinite(foot_station_forward_m) or foot_station_forward_m < 0.0:
        raise ValueError("foot_station_forward_m must be nonnegative and finite")
    for name, value in (("foot_box_width_m", foot_box_width_m), ("foot_box_height_m", foot_box_height_m)):
        if not np.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be positive and finite")
    if not np.isfinite(knuckle_probe_m) or knuckle_probe_m <= 0.0:
        raise ValueError("knuckle_probe_m must be positive and finite")
    if not np.isfinite(knuckle_span_xi) or not 0.0 < knuckle_span_xi <= 1.0:
        raise ValueError("knuckle_span_xi must be in (0, 1]")
    half_length = hull.length_m / 2.0
    if reference_station_x_m is not None and not -half_length <= reference_station_x_m <= half_length:
        raise ValueError("reference_station_x_m must lie within the hull length")

    geom = hull.to_geometry()
    xs = np.linspace(-half_length, half_length, _STATIONS)
    hull_rings = [np.asarray(geom.section(float(x), "hull"), dtype=float) for x in xs]
    deck_rings = [np.asarray(geom.section(float(x), "deck"), dtype=float) for x in xs]

    keel_z = np.array([ring[:, 1].min() if ring.shape[0] else 0.0 for ring in hull_rings])
    plane_z = float(keel_z.min()) + class_ratio_draft_m
    class_half = np.array(
        [_half_breadth_at_height([h, d], plane_z) for h, d in zip(hull_rings, deck_rings)]
    )
    overall = 2.0 * np.array(
        [
            max(
                float(np.abs(h[:, 0]).max()) if h.shape[0] else 0.0,
                float(np.abs(d[:, 0]).max()) if d.shape[0] else 0.0,
            )
            for h, d in zip(hull_rings, deck_rings)
        ]
    )

    upper = 2.0 * np.array([_breadth_at_or_above(d, catch_upper_height_m) for d in deck_rings])

    notes: list[str] = []
    wet = np.flatnonzero(class_half > 0.0)
    if wet.size:
        first, last = int(wet[0]), int(wet[-1])
        x_bow = xs[first]
        if first > 0:
            x_bow = _crossing_x(xs[first], class_half[first], xs[first - 1], class_half[first - 1])
        x_stern = xs[last]
        if last < len(xs) - 1:
            x_stern = _crossing_x(xs[last], class_half[last], xs[last + 1], class_half[last + 1])
        class_length = float(x_stern - x_bow)
        class_beam = 2.0 * float(class_half.max())
    else:
        class_length = 0.0
        class_beam = 0.0
    ratio = class_length / class_beam if class_length > 0.0 and class_beam > 0.0 else None
    if ratio is None:
        notes.append("no waterline at the stated class draft")

    if reference_station_x_m is None:
        areas = np.array([max(float(geom.section_area(float(x))), 0.0) for x in xs])
        total = float(np.trapezoid(areas, xs))
        reference = float(np.trapezoid(areas * xs, xs) / total) if total > 0.0 else 0.0
        origin: Literal["section_area_centroid", "supplied"] = "section_area_centroid"
    else:
        reference = float(reference_station_x_m)
        origin = "supplied"

    zone_bow = max(reference - far, -half_length)
    zone_stern = max(reference - near, -half_length)
    if reference - far < -half_length:
        notes.append("catch zone clipped at the bow")
    zone_xs = np.unique(np.concatenate((xs[(xs >= zone_bow) & (xs <= zone_stern)], [zone_bow, zone_stern])))
    catch_max = float(np.interp(zone_xs, xs, overall).max())

    foot_x = reference - float(foot_station_forward_m)
    if foot_x < -half_length:
        notes.append("foot station is forward of the bow")
        foot_rings: list[np.ndarray] = []
    else:
        foot_rings = [
            np.asarray(geom.section(foot_x, "hull"), dtype=float),
            np.asarray(geom.section(foot_x, "deck"), dtype=float),
        ]
    foot_beam = 2.0 * max(
        (float(np.abs(ring[:, 0]).max()) for ring in foot_rings if ring.shape[0]), default=0.0
    )

    joint_deg, joint_x = 0.0, 0.0
    knuckle_deg, knuckle_x, knuckle_z = 0.0, 0.0, 0.0
    for x, h, d in zip(xs, hull_rings, deck_rings):
        if abs(float(x)) > knuckle_span_xi * half_length:
            continue
        at_joint, above, height = _section_knuckles(h, d, float(knuckle_probe_m))
        if at_joint > joint_deg:
            joint_deg, joint_x = at_joint, float(x)
        if above > knuckle_deg:
            knuckle_deg, knuckle_x, knuckle_z = above, float(x), height

    return FormMetrics(
        class_ratio_draft_m=float(class_ratio_draft_m),
        class_waterline_length_m=class_length,
        class_waterline_beam_m=class_beam,
        class_length_beam_ratio=ratio,
        overall_length_m=float(hull.length_m),
        class_beam_length_fraction=class_beam / float(hull.length_m),
        reference_station_x_m=reference,
        reference_station_origin=origin,
        catch_zone_forward_m=(near, far),
        catch_zone_max_beam_m=catch_max,
        catch_upper_height_m=float(catch_upper_height_m),
        catch_zone_max_upper_beam_m=float(np.interp(zone_xs, xs, upper).max()),
        beam_at_reference_m=float(np.interp(reference, xs, overall)),
        max_overall_beam_m=float(overall.max()),
        foot_station_forward_m=float(foot_station_forward_m),
        foot_box_width_m=float(foot_box_width_m),
        foot_box_height_m=float(foot_box_height_m),
        foot_clear_height_m=_box_clear_height(foot_rings, float(foot_box_width_m)),
        foot_clear_width_m=_box_clear_width(foot_rings, float(foot_box_height_m), foot_beam),
        foot_station_beam_m=foot_beam,
        foot_station_depth_m=_box_clear_height(foot_rings, 0.0),
        knuckle_probe_m=float(knuckle_probe_m),
        knuckle_span_xi=float(knuckle_span_xi),
        waterline_knuckle_max_deg=joint_deg,
        waterline_knuckle_x_m=joint_x,
        upper_knuckle_max_deg=knuckle_deg,
        upper_knuckle_x_m=knuckle_x,
        upper_knuckle_height_m=knuckle_z,
        notes=notes,
    )
