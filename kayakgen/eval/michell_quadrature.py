"""Exact Laplace integration of the sampled linear depth interpolant."""

from __future__ import annotations

import numpy as np


def integrate_linear_depth(zs: np.ndarray, values: np.ndarray, beta: float) -> np.ndarray:
    """Integrate each sampled row against exp(-beta*z), including thin layers."""
    widths = np.diff(zs)
    q = beta * widths
    constant = -np.expm1(-q) / beta
    linear = np.empty_like(q)
    small = q < 1e-3
    # The closed form cancels near zero; integrate the exponential's series.
    t = q[small]
    linear[small] = widths[small] * (0.5 - t / 3 + t**2 / 8 - t**3 / 30 + t**4 / 144)
    linear[~small] = (1 - (1 + q[~small]) * np.exp(-q[~small])) / (beta * beta * widths[~small])
    decay = np.exp(-beta * zs[:-1])
    left = (constant - linear) * decay
    right = linear * decay
    return np.einsum("ij,j->i", values[:, :-1], left) + np.einsum("ij,j->i", values[:, 1:], right)


def wave_from_grid(
    xs: np.ndarray,
    zs: np.ndarray,
    half_breadths: np.ndarray,
    speed_mps: float,
    n_theta: int,
    rho: float,
    gravity: float,
) -> float:
    """Michell quadrature with the existing x/theta rules and exact linear z."""
    k0 = gravity / speed_mps**2
    gradient = np.gradient(half_breadths, xs, axis=0)
    thetas = np.linspace(0.0, np.pi / 2 - 1e-3, n_theta)
    integrand = np.empty_like(thetas)
    for i, theta in enumerate(thetas):
        sec = 1.0 / np.cos(theta)
        depth = integrate_linear_depth(zs, gradient, k0 * sec**2)
        phase = k0 * xs * sec
        p = np.trapezoid(depth * np.cos(phase), xs)
        q = np.trapezoid(depth * np.sin(phase), xs)
        integrand[i] = (p * p + q * q) * sec**3
    return float(16 * rho * gravity**2 / (np.pi * speed_mps**2) * np.trapezoid(integrand, thetas))
