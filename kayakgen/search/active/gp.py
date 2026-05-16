"""Vendored Gaussian-process surrogate for active-search v2 (RFC 0047).

Pure-Python (numpy-backed) Cholesky-factorised GP with Matern 5/2 and RBF
kernels, plus a vendored Nelder-Mead optimiser for marginal-likelihood
maximisation. No scipy / scikit-learn / GPyTorch / BoTorch dependency.

The GP is internal to algorithm-level candidate selection: surrogate-predicted
values must never appear in the candidate record's ``summary`` or in
``run.json``'s objective fields (RFC 0047 non-goal).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

import numpy as np


# ---------------------------------------------------------------------------
# Kernels
# ---------------------------------------------------------------------------


class Kernel(ABC):
    """Abstract kernel: takes positive hyperparameters ``theta``."""

    @property
    @abstractmethod
    def n_hyperparams(self) -> int:
        """Number of hyperparameters (length_scale, output_scale)."""

    @abstractmethod
    def initial_theta(self) -> np.ndarray:
        """Return the seed initialisation for marginal-likelihood fitting."""

    @abstractmethod
    def evaluate(
        self, x1: np.ndarray, x2: np.ndarray, theta: np.ndarray
    ) -> np.ndarray:
        """Return the kernel matrix ``K(x1, x2)`` under hyperparameters ``theta``."""


def _pairwise_sq_dists(x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
    """Return squared Euclidean distances between rows of ``x1`` and ``x2``."""
    diff = x1[:, None, :] - x2[None, :, :]
    return np.sum(diff * diff, axis=-1)


class MaternKernel52(Kernel):
    """Matern 5/2 isotropic kernel: hyperparams = (length_scale, output_scale)."""

    def __init__(self, length_scale_init: float = 1.0, output_scale_init: float = 1.0) -> None:
        if length_scale_init <= 0.0 or output_scale_init <= 0.0:
            raise ValueError("kernel hyperparameter inits must be positive")
        self._init = np.array(
            [float(length_scale_init), float(output_scale_init)], dtype=float
        )

    @property
    def n_hyperparams(self) -> int:
        return 2

    def initial_theta(self) -> np.ndarray:
        return self._init.copy()

    def evaluate(
        self, x1: np.ndarray, x2: np.ndarray, theta: np.ndarray
    ) -> np.ndarray:
        length_scale = max(float(theta[0]), 1e-9)
        output_scale = max(float(theta[1]), 1e-9)
        sq = _pairwise_sq_dists(x1, x2)
        # Clamp to nonnegative; numerical floor handles 0.
        sq = np.maximum(sq, 0.0)
        dist = np.sqrt(sq)
        scaled = math.sqrt(5.0) * dist / length_scale
        return (output_scale ** 2) * (
            1.0 + scaled + (5.0 / 3.0) * sq / (length_scale ** 2)
        ) * np.exp(-scaled)


class RbfKernel(Kernel):
    """RBF (squared-exponential) kernel: hyperparams = (length_scale, output_scale)."""

    def __init__(self, length_scale_init: float = 1.0, output_scale_init: float = 1.0) -> None:
        if length_scale_init <= 0.0 or output_scale_init <= 0.0:
            raise ValueError("kernel hyperparameter inits must be positive")
        self._init = np.array(
            [float(length_scale_init), float(output_scale_init)], dtype=float
        )

    @property
    def n_hyperparams(self) -> int:
        return 2

    def initial_theta(self) -> np.ndarray:
        return self._init.copy()

    def evaluate(
        self, x1: np.ndarray, x2: np.ndarray, theta: np.ndarray
    ) -> np.ndarray:
        length_scale = max(float(theta[0]), 1e-9)
        output_scale = max(float(theta[1]), 1e-9)
        sq = _pairwise_sq_dists(x1, x2)
        return (output_scale ** 2) * np.exp(-0.5 * sq / (length_scale ** 2))


def kernel_by_name(name: str) -> Kernel:
    """Map an RFC 0047 spec kernel name to a fresh kernel instance."""
    if name == "matern_5_2":
        return MaternKernel52()
    if name == "rbf":
        return RbfKernel()
    raise ValueError(f"unsupported GP kernel: {name!r}")


# ---------------------------------------------------------------------------
# Vendored Nelder-Mead
# ---------------------------------------------------------------------------


@dataclass
class _NMResult:
    x: np.ndarray
    fun: float
    nfev: int


def _nelder_mead(
    fn,
    x0: np.ndarray,
    *,
    max_evals: int = 200,
    step: float = 0.5,
    xatol: float = 1.0e-6,
    fatol: float = 1.0e-6,
) -> _NMResult:
    """Vendored Nelder-Mead minimiser.

    Pure-Python; deterministic given ``x0`` and the function. No reliance on
    scipy. Used for GP marginal-likelihood maximisation (we negate the LML).
    """

    x0 = np.asarray(x0, dtype=float)
    n = x0.size

    # Build initial simplex deterministically (no random vertex jitter).
    simplex = np.empty((n + 1, n), dtype=float)
    simplex[0] = x0
    for i in range(n):
        v = x0.copy()
        if v[i] != 0.0:
            v[i] = v[i] * (1.0 + step)
        else:
            v[i] = step
        simplex[i + 1] = v

    f_vals = np.array([fn(simplex[i]) for i in range(n + 1)], dtype=float)
    nfev = n + 1

    # Standard NM coefficients.
    alpha = 1.0
    gamma = 2.0
    rho = 0.5
    sigma = 0.5

    while nfev < max_evals:
        # Sort vertices ascending by function value (deterministic stable sort).
        order = np.argsort(f_vals, kind="stable")
        simplex = simplex[order]
        f_vals = f_vals[order]

        # Convergence test.
        max_x_span = float(np.max(np.abs(simplex[1:] - simplex[0])))
        max_f_span = float(np.max(np.abs(f_vals[1:] - f_vals[0])))
        if max_x_span < xatol and max_f_span < fatol:
            break

        # Centroid of all but the worst.
        centroid = simplex[:-1].mean(axis=0)
        worst = simplex[-1]
        f_worst = f_vals[-1]
        f_best = f_vals[0]
        f_second_worst = f_vals[-2]

        # Reflection.
        x_r = centroid + alpha * (centroid - worst)
        f_r = fn(x_r)
        nfev += 1

        if f_best <= f_r < f_second_worst:
            simplex[-1] = x_r
            f_vals[-1] = f_r
            continue

        if f_r < f_best:
            # Expansion.
            x_e = centroid + gamma * (x_r - centroid)
            f_e = fn(x_e)
            nfev += 1
            if f_e < f_r:
                simplex[-1] = x_e
                f_vals[-1] = f_e
            else:
                simplex[-1] = x_r
                f_vals[-1] = f_r
            continue

        # Contraction.
        x_c = centroid + rho * (worst - centroid)
        f_c = fn(x_c)
        nfev += 1
        if f_c < f_worst:
            simplex[-1] = x_c
            f_vals[-1] = f_c
            continue

        # Shrink.
        new_simplex = np.empty_like(simplex)
        new_simplex[0] = simplex[0]
        new_f = np.empty_like(f_vals)
        new_f[0] = f_vals[0]
        for i in range(1, n + 1):
            v = simplex[0] + sigma * (simplex[i] - simplex[0])
            new_simplex[i] = v
            new_f[i] = fn(v)
            nfev += 1
            if nfev >= max_evals:
                break
        simplex = new_simplex
        f_vals = new_f

    order = np.argsort(f_vals, kind="stable")
    return _NMResult(x=simplex[order[0]].copy(), fun=float(f_vals[order[0]]), nfev=nfev)


# ---------------------------------------------------------------------------
# Gaussian process
# ---------------------------------------------------------------------------


class GaussianProcess:
    """Cholesky-factorised GP with marginal-likelihood-fit hyperparameters.

    ``fit(X, y, *, rng, max_marginal_likelihood_evals=200)`` runs vendored
    Nelder-Mead on the (negative) log marginal likelihood and stores the
    resulting hyperparameters / factorisation. ``predict(X) -> (mean, var)``
    returns posterior mean and variance per row.
    """

    def __init__(self, kernel: Kernel, noise_floor: float = 1.0e-6) -> None:
        if noise_floor <= 0.0:
            raise ValueError("noise_floor must be positive")
        self.kernel = kernel
        self.noise_floor = float(noise_floor)
        self._X: np.ndarray | None = None
        self._y: np.ndarray | None = None
        self._y_mean: float = 0.0
        self._theta: np.ndarray | None = None
        self._L: np.ndarray | None = None
        self._alpha: np.ndarray | None = None

    # -- internals -------------------------------------------------------

    def _cholesky_with_jitter(self, K: np.ndarray) -> np.ndarray:
        n = K.shape[0]
        jitter = self.noise_floor
        # Up to 5 jitter doublings; deterministic, no rng.
        for _ in range(6):
            try:
                return np.linalg.cholesky(K + jitter * np.eye(n))
            except np.linalg.LinAlgError:
                jitter *= 10.0
        raise np.linalg.LinAlgError("GP Cholesky failed even after jitter inflation")

    def _negative_log_marginal_likelihood(
        self, theta: np.ndarray, X: np.ndarray, y_centered: np.ndarray
    ) -> float:
        # Constrain to positive hyperparameters via abs.
        theta_pos = np.abs(theta) + 1.0e-9
        K = self.kernel.evaluate(X, X, theta_pos)
        try:
            L = self._cholesky_with_jitter(K)
        except np.linalg.LinAlgError:
            return 1.0e12
        alpha = np.linalg.solve(L.T, np.linalg.solve(L, y_centered))
        # log |K| = 2 * sum(log(diag(L)))
        log_det = 2.0 * float(np.sum(np.log(np.diag(L))))
        n = X.shape[0]
        nll = 0.5 * float(y_centered @ alpha) + 0.5 * log_det + 0.5 * n * math.log(2.0 * math.pi)
        if not math.isfinite(nll):
            return 1.0e12
        return nll

    # -- public ----------------------------------------------------------

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        *,
        rng: np.random.Generator,
        max_marginal_likelihood_evals: int = 200,
    ) -> None:
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).ravel()
        if X.ndim != 2:
            raise ValueError("GP.fit expects X with shape (n_samples, n_features)")
        if X.shape[0] != y.shape[0]:
            raise ValueError("GP.fit: X and y row counts disagree")
        if X.shape[0] == 0:
            raise ValueError("GP.fit requires at least one observation")

        self._X = X.copy()
        self._y_mean = float(np.mean(y))
        y_centered = y - self._y_mean
        self._y = y_centered

        # Seed-derived deterministic initial hyperparameters: kernel's own
        # init scaled by a draw from the supplied RNG so reseeded runs are
        # byte-identical. The kernel init is the *anchor*; the rng nudges it
        # within +/- 50% so different seeds explore different starts but a
        # given seed is deterministic.
        anchor = self.kernel.initial_theta()
        nudges = rng.uniform(0.5, 1.5, size=anchor.size)
        theta0 = anchor * nudges

        def objective(theta: np.ndarray) -> float:
            return self._negative_log_marginal_likelihood(theta, self._X, self._y)

        result = _nelder_mead(
            objective,
            theta0,
            max_evals=max(int(max_marginal_likelihood_evals), 4),
        )
        theta_pos = np.abs(result.x) + 1.0e-9
        self._theta = theta_pos

        K = self.kernel.evaluate(self._X, self._X, theta_pos)
        self._L = self._cholesky_with_jitter(K)
        self._alpha = np.linalg.solve(self._L.T, np.linalg.solve(self._L, self._y))

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if self._X is None or self._theta is None or self._L is None or self._alpha is None:
            raise RuntimeError("GP.predict called before fit")
        X = np.asarray(X, dtype=float)
        if X.ndim != 2:
            raise ValueError("GP.predict expects X with shape (n_samples, n_features)")
        if X.shape[1] != self._X.shape[1]:
            raise ValueError(
                "GP.predict: feature count disagrees with fit() inputs "
                f"(got {X.shape[1]}, fit on {self._X.shape[1]})"
            )

        K_s = self.kernel.evaluate(self._X, X, self._theta)
        K_ss_diag = np.diag(self.kernel.evaluate(X, X, self._theta))
        mean = K_s.T @ self._alpha + self._y_mean
        v = np.linalg.solve(self._L, K_s)
        var = K_ss_diag - np.sum(v * v, axis=0)
        # Floor variance at zero for numerical safety.
        var = np.maximum(var, 0.0)
        return mean, var

    @property
    def fitted(self) -> bool:
        return self._theta is not None


__all__ = [
    "GaussianProcess",
    "Kernel",
    "MaternKernel52",
    "RbfKernel",
    "kernel_by_name",
]
