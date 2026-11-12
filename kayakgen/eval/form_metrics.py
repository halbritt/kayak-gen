"""Form metrics read off the generated sections (RFC 0089).

Two geometric measures a designer otherwise takes by hand:

* the race-class length-to-beam ratio, waterline length over waterline
  beam with the hull floating at a stated draft below its lowest keel
  point (the Sound Rowers kayak classes assume 4 in);
* the same waterline beam as a fraction of overall length, which the
  USCA kayak classes limit (Sea Kayak: at least 8.5% at 4 in);
* paddle clearance, the overall beam of hull and deck in a zone forward
  of a reference station, where the blade enters the water.

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


def _crossing_x(x_in: float, v_in: float, x_out: float, v_out: float) -> float:
    """Station where a positive value ``v_in`` reaches zero toward ``x_out``."""

    if v_in <= 0.0 or v_out >= v_in:
        return x_in
    return x_in + (x_out - x_in) * v_in / (v_in - v_out)


def evaluate_form_metrics(
    hull: Hull,
    *,
    class_ratio_draft_m: float = DEFAULT_CLASS_RATIO_DRAFT_M,
    catch_zone_forward_m: tuple[float, float] = DEFAULT_CATCH_ZONE_FORWARD_M,
    reference_station_x_m: float | None = None,
    catch_upper_height_m: float = DEFAULT_CATCH_UPPER_HEIGHT_M,
) -> FormMetrics:
    """Compute :class:`FormMetrics` for ``hull``."""

    if not np.isfinite(class_ratio_draft_m) or class_ratio_draft_m <= 0.0:
        raise ValueError("class_ratio_draft_m must be positive and finite")
    near, far = (float(catch_zone_forward_m[0]), float(catch_zone_forward_m[1]))
    if not (np.isfinite(near) and np.isfinite(far)) or far <= near:
        raise ValueError("catch_zone_forward_m must be an increasing (near, far) pair")
    if not np.isfinite(catch_upper_height_m) or catch_upper_height_m < 0.0:
        raise ValueError("catch_upper_height_m must be nonnegative and finite")
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
        notes=notes,
    )
