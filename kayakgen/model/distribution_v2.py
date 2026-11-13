"""Geometry V2 — explicit longitudinal distribution model (RFC 0048).

This module defines the value-object schema that ``Hull.distribution_v2``
points at when ``Hull.geometry_kind == "distribution_v2"``. It declares:

* the :class:`LongitudinalDistribution` discriminated union
  (``UniformDistribution`` / ``PolynomialDistribution`` /
  ``KeyPointsDistribution``), each parametrized in the normalized
  longitudinal coordinate ``xi`` ∈ ``[-1, 1]`` (bow at ``-1``, stern at
  ``+1``);
* the :class:`CrossSectionFamily` literal naming the six section
  families the V2 loft admits;
* :class:`DistributionV2Spec`, the top-level value object owned by
  ``Hull``.

The module is **model-layer**: it imports nothing from
``kayakgen.eval``/``search``/``ui``/``cli``. Sampling-by-station happens
on the :class:`LongitudinalDistribution` records themselves; the
cross-section sampling routines live alongside the
:class:`DistributionV2Geometry` strategy in
:mod:`kayakgen.model.geometry`.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator


CrossSectionFamily = Literal[
    "round",
    "shallow_arch",
    "shallow_v",
    "deep_v",
    "hard_chine",
    "multi_chine",
]


class UniformDistribution(BaseModel):
    """Constant-valued longitudinal distribution.

    ``sample(xi)`` returns ``value`` for any ``xi`` ∈ ``[-1, 1]``.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    kind: Literal["uniform"] = "uniform"
    value: float

    def sample(self, xi: float | np.ndarray) -> np.ndarray:
        xi_arr = np.atleast_1d(np.asarray(xi, dtype=float))
        return np.full_like(xi_arr, float(self.value), dtype=float)


class PolynomialDistribution(BaseModel):
    """Polynomial-in-``xi`` distribution.

    ``coefficients = [a0, a1, a2, ...]`` evaluates as
    ``a0 + a1 * xi + a2 * xi^2 + ...`` for ``xi ∈ [-1, 1]``.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    kind: Literal["polynomial"] = "polynomial"
    coefficients: list[float] = Field(min_length=1)

    def sample(self, xi: float | np.ndarray) -> np.ndarray:
        xi_arr = np.atleast_1d(np.asarray(xi, dtype=float))
        out = np.zeros_like(xi_arr, dtype=float)
        for power, coef in enumerate(self.coefficients):
            out = out + float(coef) * (xi_arr**power)
        return out


class KeyPointsDistribution(BaseModel):
    """Cubic-spline interpolated key-point distribution.

    ``knots`` are ``(xi, value)`` pairs; ``xi`` must be strictly
    increasing in ``[-1, 1]``. Sampling outside the knot range clamps to
    the endpoint values (no extrapolation).
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    kind: Literal["key_points"] = "key_points"
    knots: list[tuple[float, float]] = Field(min_length=2)

    @model_validator(mode="after")
    def _validate_monotonic_knots(self) -> "KeyPointsDistribution":
        xs = [pt[0] for pt in self.knots]
        for prev, curr in zip(xs[:-1], xs[1:]):
            if curr <= prev:
                raise ValueError("KeyPointsDistribution knots must be strictly increasing in xi")
        if xs[0] < -1.0 - 1e-12 or xs[-1] > 1.0 + 1e-12:
            raise ValueError("KeyPointsDistribution knots must lie in xi ∈ [-1, 1]")
        return self

    def sample(self, xi: float | np.ndarray) -> np.ndarray:
        xi_arr = np.atleast_1d(np.asarray(xi, dtype=float))
        xs = np.array([pt[0] for pt in self.knots], dtype=float)
        ys = np.array([pt[1] for pt in self.knots], dtype=float)
        clamped = np.clip(xi_arr, xs[0], xs[-1])
        if len(xs) == 2:
            # Linear fall-back when only two knots are provided; cubic
            # spline needs at least three for a meaningful second
            # derivative.
            return np.interp(clamped, xs, ys)
        result = _cubic_spline_interp(xs, ys, clamped)
        return result


def _cubic_spline_interp(xs: np.ndarray, ys: np.ndarray, query: np.ndarray) -> np.ndarray:
    """Natural cubic spline interpolation without SciPy.

    Solves the tridiagonal system for second derivatives at interior
    knots with the natural boundary condition (zero second derivative
    at both ends) and evaluates the resulting piecewise cubic.
    """

    n = len(xs)
    h = np.diff(xs)
    alpha = np.zeros(n, dtype=float)
    for i in range(1, n - 1):
        alpha[i] = (3.0 / h[i]) * (ys[i + 1] - ys[i]) - (3.0 / h[i - 1]) * (ys[i] - ys[i - 1])

    li = np.zeros(n, dtype=float)
    mu = np.zeros(n, dtype=float)
    zi = np.zeros(n, dtype=float)
    li[0] = 1.0
    for i in range(1, n - 1):
        li[i] = 2.0 * (xs[i + 1] - xs[i - 1]) - h[i - 1] * mu[i - 1]
        mu[i] = h[i] / li[i]
        zi[i] = (alpha[i] - h[i - 1] * zi[i - 1]) / li[i]
    li[n - 1] = 1.0

    b = np.zeros(n, dtype=float)
    c = np.zeros(n, dtype=float)
    d = np.zeros(n, dtype=float)
    for j in range(n - 2, -1, -1):
        c[j] = zi[j] - mu[j] * c[j + 1]
        b[j] = (ys[j + 1] - ys[j]) / h[j] - h[j] * (c[j + 1] + 2.0 * c[j]) / 3.0
        d[j] = (c[j + 1] - c[j]) / (3.0 * h[j])

    # Locate each query in the knot intervals.
    idx = np.searchsorted(xs, query, side="right") - 1
    idx = np.clip(idx, 0, n - 2)
    dx = query - xs[idx]
    return ys[idx] + b[idx] * dx + c[idx] * (dx**2) + d[idx] * (dx**3)


LongitudinalDistribution = Annotated[
    Union[UniformDistribution, PolynomialDistribution, KeyPointsDistribution],
    Field(discriminator="kind"),
]


def sample_distribution(
    distribution: LongitudinalDistribution,
    xi: float | np.ndarray,
) -> np.ndarray:
    """Convenience sampler dispatching by record kind.

    Pydantic round-trips the discriminated union back into one of the
    concrete records, so callers can always call ``.sample(xi)`` on a
    materialized ``LongitudinalDistribution``. This wrapper exists for
    sites that have a typing-narrow union and prefer a free function.
    """

    return distribution.sample(xi)


SHEER_BEAM_RATIO_MIN = 0.6
SHEER_BEAM_RATIO_MAX = 1.5
SHEER_PLAN_EXPONENT_MIN = 1.2
SHEER_PLAN_EXPONENT_MAX = 4.0
_SHEER_PLAN_VALIDATION_XI = np.linspace(-0.9, 0.9, 181)
DECK_CROWN_EXPONENT_MIN = 2.0
DECK_CROWN_EXPONENT_MAX = 12.0
SECTION_EXPONENT_MIN = 1.5
SECTION_EXPONENT_MAX = 8.0
SECTION_EXPONENT_DEFAULT = 2.0
SECTION_SIDE_EXPONENT_MIN = 1.0
SECTION_SIDE_EXPONENT_MAX = 6.0
SHEER_HEIGHT_FRAC_MIN = 0.05
SHEER_HEIGHT_FRAC_MAX = 0.95
SHOULDER_ROUND_MAX_M = 0.2
_TOPSIDES_VALIDATION_XI = np.linspace(-1.0, 1.0, 201)


def _sample_scalar_or_longitudinal(
    value: "float | LongitudinalDistribution", xi: float | np.ndarray
) -> np.ndarray:
    xi_arr = np.atleast_1d(np.asarray(xi, dtype=float))
    if isinstance(value, (int, float)):
        return np.full(xi_arr.shape, float(value))
    return np.asarray(value.sample(xi_arr), dtype=float)


class SheerPlan(BaseModel):
    """The sheer drawn as its own fair outline in plan view (RFC 0089).

    Half-breadth is ``max_half_breadth_m * (1 - u ** n)``, where ``u``
    runs from 0 at ``max_position_xi`` to 1 at the bow (with
    ``forward_exponent``) or the stern (with ``aft_exponent``). Each
    side is monotone and curves one way only, so the outline has no
    hollow, pinch or flat. A lower exponent gives a finer, straighter
    end. All four fields are scalars so a search can vary them.
    """

    model_config = ConfigDict(extra="forbid")

    max_half_breadth_m: float = Field(gt=0.0, le=0.6, allow_inf_nan=False)
    max_position_xi: float = Field(ge=-0.5, le=0.8, allow_inf_nan=False)
    forward_exponent: float = Field(
        ge=SHEER_PLAN_EXPONENT_MIN, le=SHEER_PLAN_EXPONENT_MAX, allow_inf_nan=False
    )
    aft_exponent: float = Field(
        ge=SHEER_PLAN_EXPONENT_MIN, le=SHEER_PLAN_EXPONENT_MAX, allow_inf_nan=False
    )

    def half_breadth(self, xi: float | np.ndarray) -> np.ndarray:
        xi_arr = np.clip(np.atleast_1d(np.asarray(xi, dtype=float)), -1.0, 1.0)
        forward = xi_arr < self.max_position_xi
        u = np.where(
            forward,
            (self.max_position_xi - xi_arr) / (1.0 + self.max_position_xi),
            (xi_arr - self.max_position_xi) / (1.0 - self.max_position_xi),
        )
        exponent = np.where(forward, self.forward_exponent, self.aft_exponent)
        return self.max_half_breadth_m * (1.0 - np.clip(u, 0.0, 1.0) ** exponent)


class TopsidesSpec(BaseModel):
    """Above-waterline hull sides between the design waterline and the sheer.

    Without this record the V2 deck meets the hull on the design
    waterline, so the body has no reserve of breadth above the water.
    With it, each station carries a topside strip from the waterline
    edge up to the sheer, and the deck spans sheer to sheer.

    ``sheer_beam_ratio`` is the sheer half-breadth divided by the local
    waterline half-breadth (1 = wall-sided, above 1 = flared, below 1 =
    tumblehome, RFC 0089). A ratio keeps the flare proportional to the
    local breadth so it vanishes at pointed ends. ``sheer_height_frac``
    is the sheer height above the design waterline divided by the local
    deck freeboard. Both accept a scalar or a
    :class:`LongitudinalDistribution`.

    ``sheer_plan`` (RFC 0089) replaces the ratio with a fair outline of
    the sheer in plan view; ``sheer_beam_ratio`` must then be left at
    1. ``deck_crown_exponent`` (RFC 0089) sets how square the deck is
    between sheer and crown; unset keeps the built-in arch.

    ``shoulder_round_m`` (RFC 0089 stage 5) rounds the deck edge. The
    side then leaves the waterline on the hull's own line and takes
    half the sheer height to turn, so it may stand wider than the sheer
    on the way up, and a blend replaces the outline for this distance
    either side of the sheer. The upper outline is then one curve with
    no corner, and the sheer is where that curve is widest. The
    distance shortens by itself where the section is small.

    The three RFC 0089 fields are omitted from serialized output while
    unset.
    """

    model_config = ConfigDict(extra="forbid")

    sheer_beam_ratio: Union[float, LongitudinalDistribution] = 1.0
    sheer_height_frac: Union[float, LongitudinalDistribution] = 0.6
    sheer_plan: SheerPlan | None = None
    deck_crown_exponent: Union[float, LongitudinalDistribution, None] = None
    shoulder_round_m: float | None = Field(
        default=None, gt=0.0, le=SHOULDER_ROUND_MAX_M, allow_inf_nan=False
    )

    @model_validator(mode="after")
    def _check_ranges(self) -> "TopsidesSpec":
        if self.sheer_plan is not None and self.sheer_beam_ratio != 1.0:
            raise ValueError(
                "give sheer_plan or sheer_beam_ratio, not both: with a sheer_plan "
                "leave sheer_beam_ratio at 1"
            )
        ratio = _sample_scalar_or_longitudinal(self.sheer_beam_ratio, _TOPSIDES_VALIDATION_XI)
        frac = _sample_scalar_or_longitudinal(self.sheer_height_frac, _TOPSIDES_VALIDATION_XI)
        if not (np.isfinite(ratio).all() and np.isfinite(frac).all()):
            raise ValueError("topsides values must be finite")
        if ratio.min() < SHEER_BEAM_RATIO_MIN or ratio.max() > SHEER_BEAM_RATIO_MAX:
            raise ValueError(
                "sheer_beam_ratio must stay within "
                f"[{SHEER_BEAM_RATIO_MIN}, {SHEER_BEAM_RATIO_MAX}] along the hull"
            )
        if frac.min() < SHEER_HEIGHT_FRAC_MIN or frac.max() > SHEER_HEIGHT_FRAC_MAX:
            raise ValueError(
                "sheer_height_frac must stay within "
                f"[{SHEER_HEIGHT_FRAC_MIN}, {SHEER_HEIGHT_FRAC_MAX}] along the hull"
            )
        if self.deck_crown_exponent is not None:
            crown = _sample_scalar_or_longitudinal(self.deck_crown_exponent, _TOPSIDES_VALIDATION_XI)
            if not np.isfinite(crown).all():
                raise ValueError("deck_crown_exponent must be finite")
            if crown.min() < DECK_CROWN_EXPONENT_MIN or crown.max() > DECK_CROWN_EXPONENT_MAX:
                raise ValueError(
                    "deck_crown_exponent must stay within "
                    f"[{DECK_CROWN_EXPONENT_MIN}, {DECK_CROWN_EXPONENT_MAX}] along the hull"
                )
        return self

    def sample_sheer_beam_ratio(self, xi: float) -> float:
        value = float(_sample_scalar_or_longitudinal(self.sheer_beam_ratio, xi)[0])
        return float(min(max(value, SHEER_BEAM_RATIO_MIN), SHEER_BEAM_RATIO_MAX))

    def sheer_half_breadth(self, xi: float, waterline_half_breadth: float) -> float:
        """Sheer half-breadth at ``xi`` for the local waterline half-breadth.

        With a ``sheer_plan`` the outline is held within the ratio range
        of the local waterline, which only acts close to the pointed
        ends; the spec refuses a plan that would need it elsewhere.
        """

        if self.sheer_plan is None:
            return float(waterline_half_breadth * self.sample_sheer_beam_ratio(xi))
        value = float(self.sheer_plan.half_breadth(xi)[0])
        low = SHEER_BEAM_RATIO_MIN * waterline_half_breadth
        high = SHEER_BEAM_RATIO_MAX * waterline_half_breadth
        return float(min(max(value, low), high))

    def sample_sheer_height_frac(self, xi: float) -> float:
        value = float(_sample_scalar_or_longitudinal(self.sheer_height_frac, xi)[0])
        return float(min(max(value, SHEER_HEIGHT_FRAC_MIN), SHEER_HEIGHT_FRAC_MAX))

    def sample_deck_crown_exponent(self, xi: float) -> float | None:
        if self.deck_crown_exponent is None:
            return None
        value = float(_sample_scalar_or_longitudinal(self.deck_crown_exponent, xi)[0])
        return float(min(max(value, DECK_CROWN_EXPONENT_MIN), DECK_CROWN_EXPONENT_MAX))

    @model_serializer(mode="wrap")
    def _omit_unset_rfc0089_fields(self, handler):  # type: ignore[no-untyped-def]
        data = handler(self)
        if isinstance(data, dict):
            if self.sheer_plan is None:
                data.pop("sheer_plan", None)
            if self.deck_crown_exponent is None:
                data.pop("deck_crown_exponent", None)
            if self.shoulder_round_m is None:
                data.pop("shoulder_round_m", None)
        return data


class DistributionV2Spec(BaseModel):
    """Explicit-distribution geometry payload (RFC 0048).

    The eight longitudinal distributions describe the canonical body in
    the normalized ``xi`` coordinate; ``xi = -1`` is the bow, ``xi = +1``
    is the stern. The cross-section family literal selects which of the
    six pure-Python sampling routines the V2 loft consults to turn the
    distribution values into a per-station ring.

    Deadrise and chine radius accept either a scalar (constant value) or
    a :class:`LongitudinalDistribution` (per-station value). The rocker
    distribution is consumed by the V2 loft to bias the keel line; the
    legacy scalar ``rocker_bow_m`` / ``rocker_stern_m`` knobs are
    preserved for backwards-compatible reporting and ride on the spec
    as derived end values.

    ``multi_chine_count`` parametrizes the ``multi_chine`` family's
    chine count (range 2-4). It is ignored by the other five families.

    ``topsides`` (RFC 0088) is optional. When unset the deck meets the
    hull on the design waterline, exactly as before the field existed.

    ``section_exponent`` (RFC 0089) is optional and applies to the
    ``round`` family only. When unset the section is the parabola it
    always was.

    ``section_side_exponent`` (RFC 0089 stage 6) is optional and applies
    to the ``round`` family only. At 2 and above the side turns up and
    meets the waterline vertically, as on a U-shaped section; between 1
    and 2 a quadratic blend eases the flare down to vertical without a
    waterline crease; when unset the side meets the waterline at the
    angle the parabola or power curve gives it.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"

    waterline_half_breadth: LongitudinalDistribution
    draft_profile: LongitudinalDistribution
    section_area_curve: LongitudinalDistribution
    deck_freeboard: LongitudinalDistribution
    rocker: LongitudinalDistribution

    rocker_bow_m: float = Field(default=0.0, ge=0)
    rocker_stern_m: float = Field(default=0.0, ge=0)
    lcb_target_frac: float = Field(default=0.5, ge=0, le=1)
    max_beam_position_frac: float = Field(default=0.5, ge=0, le=1)

    cross_section_family: CrossSectionFamily = "round"
    deadrise_deg: Union[float, LongitudinalDistribution] = 0.0
    chine_radius_m: Union[float, LongitudinalDistribution] = 0.02
    bow_flare_deg: float = 0.0

    multi_chine_count: int = Field(default=2, ge=2, le=4)

    # RFC 0088. Omitted from serialized output while unset so every
    # record and design identity written before the field existed stays
    # byte-stable.
    topsides: TopsidesSpec | None = None

    # RFC 0089. Fullness of the ``round`` section below the waterline:
    # half-breadth ``y`` at depth ``z`` follows
    # ``z = -draft * (1 - (y / half_breadth) ** section_exponent)``.
    # 2 is the parabola every earlier record was built with; larger
    # values give a flatter floor and a firmer bilge. Omitted from
    # serialized output while unset, like ``topsides``.
    section_exponent: Union[float, LongitudinalDistribution, None] = None

    # RFC 0089 stage 6. How the ``round`` section reaches the waterline:
    # at 2 and above ``z = -draft * (1 - (y / half_breadth) **
    # section_exponent) ** (1 / section_side_exponent)``, which meets the
    # waterline vertically with finite curvature (equal to
    # ``section_exponent``: a superellipse; 2 and 2: an ellipse). Between
    # 1 and 2, ``(2 - m) * (-z / draft) + (m - 1) * (-z / draft) ** 2 =
    # 1 - (y / half_breadth) ** section_exponent`` eases the waterline
    # flare from the stage 1 curve at 1 down to vertical at 2. Omitted
    # while unset.
    section_side_exponent: Union[float, LongitudinalDistribution, None] = None

    @model_validator(mode="after")
    def _check_sheer_plan_against_waterline(self) -> "DistributionV2Spec":
        plan = self.topsides.sheer_plan if self.topsides is not None else None
        if plan is None:
            return self
        waterline = np.maximum(
            np.asarray(self.waterline_half_breadth.sample(_SHEER_PLAN_VALIDATION_XI), dtype=float),
            0.0,
        )
        sheer = plan.half_breadth(_SHEER_PLAN_VALIDATION_XI)
        low = sheer < SHEER_BEAM_RATIO_MIN * waterline - 1e-12
        high = sheer > SHEER_BEAM_RATIO_MAX * waterline + 1e-12
        if low.any() or high.any():
            where = float(_SHEER_PLAN_VALIDATION_XI[np.flatnonzero(low | high)[0]])
            raise ValueError(
                "sheer_plan must stay within "
                f"[{SHEER_BEAM_RATIO_MIN}, {SHEER_BEAM_RATIO_MAX}] times the waterline "
                f"half-breadth for |xi| <= 0.9 (first violated at xi = {where:.2f})"
            )
        return self

    @model_validator(mode="after")
    def _check_section_exponent(self) -> "DistributionV2Spec":
        if self.section_exponent is None:
            return self
        if self.cross_section_family != "round":
            raise ValueError(
                "section_exponent applies only to the 'round' cross_section_family"
            )
        values = _sample_scalar_or_longitudinal(self.section_exponent, _TOPSIDES_VALIDATION_XI)
        if not np.isfinite(values).all():
            raise ValueError("section_exponent must be finite")
        if values.min() < SECTION_EXPONENT_MIN or values.max() > SECTION_EXPONENT_MAX:
            raise ValueError(
                "section_exponent must stay within "
                f"[{SECTION_EXPONENT_MIN}, {SECTION_EXPONENT_MAX}] along the hull"
            )
        return self

    @model_validator(mode="after")
    def _check_section_side_exponent(self) -> "DistributionV2Spec":
        if self.section_side_exponent is None:
            return self
        if self.cross_section_family != "round":
            raise ValueError(
                "section_side_exponent applies only to the 'round' cross_section_family"
            )
        values = _sample_scalar_or_longitudinal(
            self.section_side_exponent, _TOPSIDES_VALIDATION_XI
        )
        if not np.isfinite(values).all():
            raise ValueError("section_side_exponent must be finite")
        if values.min() < SECTION_SIDE_EXPONENT_MIN or values.max() > SECTION_SIDE_EXPONENT_MAX:
            raise ValueError(
                "section_side_exponent must stay within "
                f"[{SECTION_SIDE_EXPONENT_MIN}, {SECTION_SIDE_EXPONENT_MAX}] along the hull"
            )
        return self

    def sample_section_side_exponent(self, xi: float) -> float | None:
        if self.section_side_exponent is None:
            return None
        value = float(_sample_scalar_or_longitudinal(self.section_side_exponent, xi)[0])
        return float(min(max(value, SECTION_SIDE_EXPONENT_MIN), SECTION_SIDE_EXPONENT_MAX))

    def sample_section_exponent(self, xi: float) -> float:
        if self.section_exponent is None:
            return SECTION_EXPONENT_DEFAULT
        value = float(_sample_scalar_or_longitudinal(self.section_exponent, xi)[0])
        return float(min(max(value, SECTION_EXPONENT_MIN), SECTION_EXPONENT_MAX))

    @model_serializer(mode="wrap")
    def _omit_unset_optional_records(self, handler):  # type: ignore[no-untyped-def]
        data = handler(self)
        if isinstance(data, dict):
            if self.topsides is None:
                data.pop("topsides", None)
            if self.section_exponent is None:
                data.pop("section_exponent", None)
            if self.section_side_exponent is None:
                data.pop("section_side_exponent", None)
        return data
