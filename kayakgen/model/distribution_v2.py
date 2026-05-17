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
from pydantic import BaseModel, ConfigDict, Field, model_validator


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
