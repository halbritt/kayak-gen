"""Expected Hypervolume Improvement calculator (RFC 0047).

Pure-Python EHVI for 1, 2, and 3 minimisation objectives. 4+ objectives are
refused at v1: an exact pure-Python sub-region decomposition for n>=4 is
impractical, and approximate Monte-Carlo EHVI is out of scope for v1.

All math is in *minimisation* space: callers translate ``max`` objectives into
their negated form before calling :func:`compute_ehvi`. The reference point and
Pareto front are likewise expressed in minimisation space; the reference point
dominates the worst acceptable design (each coordinate must be at least as
large as every Pareto-front coordinate).

References:
  - Couckuyt, Deschrijver, Dhaene 2014, "Fast calculation of multiobjective
    probability of improvement and expected improvement criteria for Pareto
    optimization".
  - Yang, Emmerich, Deutz, Back 2017, "Multi-Objective Bayesian Global
    Optimization using Expected Hypervolume Improvement Gradient".
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np


class EhviDimensionError(ValueError):
    """Raised when EHVI is requested for an unsupported objective count."""


# ---------------------------------------------------------------------------
# Standard-normal helpers (pure-Python; avoids scipy.stats)
# ---------------------------------------------------------------------------


_SQRT_2 = math.sqrt(2.0)
_SQRT_2PI = math.sqrt(2.0 * math.pi)


def _phi(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / _SQRT_2PI


def _Phi(x: float) -> float:
    """Standard normal CDF via math.erf."""
    return 0.5 * (1.0 + math.erf(x / _SQRT_2))


# ---------------------------------------------------------------------------
# Pareto-set utilities
# ---------------------------------------------------------------------------


def _nondominated(points: np.ndarray) -> np.ndarray:
    """Return the strict Pareto-minimal subset of ``points`` (rows)."""
    if points.size == 0:
        return points
    keep = []
    n = points.shape[0]
    for i in range(n):
        dominated = False
        pi = points[i]
        for j in range(n):
            if i == j:
                continue
            pj = points[j]
            # j dominates i iff pj <= pi in all dims and pj < pi in any.
            if np.all(pj <= pi) and np.any(pj < pi):
                dominated = True
                break
        if not dominated:
            keep.append(i)
    return points[np.array(keep, dtype=int)]


# ---------------------------------------------------------------------------
# EHVI: single objective (Expected Improvement)
# ---------------------------------------------------------------------------


def _ehvi_1d(
    mu: np.ndarray, sigma: np.ndarray, pareto_front: np.ndarray, reference_point: np.ndarray
) -> float:
    """1D EHVI degenerates to Expected Improvement against the incumbent best."""
    # In minimisation, the incumbent best is the minimum across all observed
    # Pareto-front points (which is just the single best point in 1D).
    if pareto_front.size == 0:
        best = float(reference_point[0])
    else:
        best = float(np.min(pareto_front[:, 0]))
    m = float(mu[0])
    s = float(sigma[0])
    if s <= 0.0:
        return max(best - m, 0.0)
    z = (best - m) / s
    ei = (best - m) * _Phi(z) + s * _phi(z)
    return max(ei, 0.0)


# ---------------------------------------------------------------------------
# EHVI: two objectives via Emmerich's closed-form sum
# ---------------------------------------------------------------------------


def _ehvi_2d(
    mu: np.ndarray, sigma: np.ndarray, pareto_front: np.ndarray, reference_point: np.ndarray
) -> float:
    """2D EHVI via axis-aligned grid decomposition (same approach as 3D).

    Partition the box [-inf, ref] into axis-aligned cells using the
    Pareto-front coordinates. For each cell that is *not* dominated by any
    Pareto point (so landing there is an "improvement"), accumulate the
    product of:
      - probability that the candidate lands in the cell (independent normal),
      - and the improvement volume of the cell (cell area capped at ref).
    """
    return _ehvi_nd_grid(mu, sigma, pareto_front, reference_point, n_obj=2)


# ---------------------------------------------------------------------------
# EHVI: three objectives via sub-region decomposition
# ---------------------------------------------------------------------------


def _box_dominated_by_front(
    lower: np.ndarray, upper: np.ndarray, front: np.ndarray
) -> bool:
    """Return whether the *entire* axis-aligned box [lower, upper) is dominated.

    A box is dominated iff some Pareto point ``p`` satisfies ``p <= lower``
    coordinate-wise (then every point in the box is dominated by ``p``).
    """
    if front.shape[0] == 0:
        return False
    for p in front:
        if np.all(p <= lower):
            return True
    return False


def _ehvi_3d(
    mu: np.ndarray, sigma: np.ndarray, pareto_front: np.ndarray, reference_point: np.ndarray
) -> float:
    """3D EHVI via axis-aligned grid decomposition (Couckuyt 2014 style)."""
    return _ehvi_nd_grid(mu, sigma, pareto_front, reference_point, n_obj=3)


def _ehvi_nd_grid(
    mu: np.ndarray,
    sigma: np.ndarray,
    pareto_front: np.ndarray,
    reference_point: np.ndarray,
    *,
    n_obj: int,
) -> float:
    """Pure-Python EHVI for n_obj in {2, 3} via axis-aligned cell decomposition.

    Builds a grid over (per-axis sorted unique coordinates union reference)
    coordinates, walks each cell, skips those entirely dominated by the
    Pareto front, and accumulates:
      - probability that the candidate lands inside the cell (independent
        normal CDF differences), times
      - the *improvement* volume contributed by that cell: the hypervolume
        between (ref - upper) and (ref - lower) bounded at the reference.

    The reference point dominates the box; cells outside [-inf, ref] are not
    enumerated. Each cell's "improvement" is the difference between dominating
    its lower-corner and dominating its upper-corner (both clipped at ref).
    """
    ref = np.asarray(reference_point, dtype=float)
    front = pareto_front.copy()

    NEG_INF = -1.0e30
    coords_per_axis: list[list[float]] = []
    for axis in range(n_obj):
        cs = sorted({NEG_INF, float(ref[axis])} | {float(p[axis]) for p in front})
        coords_per_axis.append(cs)

    mu_arr = np.asarray(mu, dtype=float)
    sigma_arr = np.maximum(np.asarray(sigma, dtype=float), 1.0e-12)

    ehvi = 0.0
    # Iterate cells as the cartesian product of consecutive coordinate pairs.
    def _enumerate_cells(axis: int, lower: list[float], upper: list[float]):
        nonlocal ehvi
        if axis == n_obj:
            l_arr = np.asarray(lower, dtype=float)
            u_arr = np.asarray(upper, dtype=float)
            if _box_dominated_by_front(l_arr, u_arr, front):
                return
            # Cell must sit within [-inf, ref]; coords were built only up to ref.
            prob = 1.0
            for a in range(n_obj):
                prob *= (
                    _Phi((u_arr[a] - mu_arr[a]) / sigma_arr[a])
                    - _Phi((l_arr[a] - mu_arr[a]) / sigma_arr[a])
                )
            if prob <= 0.0:
                return
            vol_l = 1.0
            vol_u = 1.0
            for a in range(n_obj):
                vol_l *= max(ref[a] - l_arr[a], 0.0)
                vol_u *= max(ref[a] - u_arr[a], 0.0)
            vol = max(vol_l - vol_u, 0.0)
            ehvi += prob * vol
            return
        coords = coords_per_axis[axis]
        for i in range(len(coords) - 1):
            lower.append(coords[i])
            upper.append(coords[i + 1])
            _enumerate_cells(axis + 1, lower, upper)
            lower.pop()
            upper.pop()

    _enumerate_cells(0, [], [])
    return max(ehvi, 0.0)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def compute_ehvi(
    mu: Sequence[float] | np.ndarray,
    sigma: Sequence[float] | np.ndarray,
    pareto_front: Sequence[Sequence[float]] | np.ndarray,
    reference_point: Sequence[float] | np.ndarray,
) -> float:
    """Compute Expected Hypervolume Improvement (minimisation space).

    Args:
        mu: posterior-mean vector per objective.
        sigma: posterior-stddev vector per objective.
        pareto_front: current Pareto front (rows = points, cols = objectives).
        reference_point: hypervolume reference dominated by every Pareto point.

    Returns:
        Nonnegative scalar EHVI. Zero for candidates strictly dominated by an
        existing front point with zero variance.

    Raises:
        EhviDimensionError if the number of objectives is not in {1, 2, 3}.
    """

    mu = np.asarray(mu, dtype=float).ravel()
    sigma = np.asarray(sigma, dtype=float).ravel()
    if mu.shape != sigma.shape:
        raise ValueError("compute_ehvi: mu and sigma must have the same shape")
    n_obj = mu.shape[0]
    if n_obj < 1 or n_obj > 3:
        raise EhviDimensionError(
            f"compute_ehvi supports 1-3 objectives; got {n_obj}"
        )

    ref = np.asarray(reference_point, dtype=float).ravel()
    if ref.shape[0] != n_obj:
        raise ValueError("compute_ehvi: reference_point dimensionality mismatch")

    pf = np.asarray(pareto_front, dtype=float)
    if pf.size == 0:
        pf = np.empty((0, n_obj), dtype=float)
    elif pf.ndim == 1:
        pf = pf.reshape(1, n_obj)
    if pf.shape[1] != n_obj:
        raise ValueError("compute_ehvi: pareto_front dimensionality mismatch")
    if pf.shape[0] > 0:
        pf = _nondominated(pf)

    if n_obj == 1:
        return _ehvi_1d(mu, sigma, pf, ref)
    if n_obj == 2:
        return _ehvi_2d(mu, sigma, pf, ref)
    return _ehvi_3d(mu, sigma, pf, ref)


__all__ = ["EhviDimensionError", "compute_ehvi"]
