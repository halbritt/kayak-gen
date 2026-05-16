"""RFC 0047 v2 EHVI calculator tests."""

from __future__ import annotations

import math

import numpy as np
import pytest

from kayakgen.search.active.ehvi import EhviDimensionError, compute_ehvi


def test_compute_ehvi_strictly_nonnegative() -> None:
    rng = np.random.default_rng(7)
    pareto = np.array([[1.0, 5.0], [2.0, 3.0], [4.0, 2.0]])
    ref = np.array([6.0, 6.0])
    for _ in range(50):
        mu = rng.uniform(-1.0, 6.0, size=2)
        sigma = rng.uniform(0.1, 1.0, size=2)
        ehvi = compute_ehvi(mu, sigma, pareto, ref)
        assert ehvi >= 0.0


def test_compute_ehvi_zero_when_candidate_strictly_dominated() -> None:
    # 2D: a Pareto point at (1, 1); a candidate at (5, 5) with tiny variance
    # should produce essentially zero EHVI (it's strictly worse than the
    # existing front).
    pareto = np.array([[1.0, 1.0]])
    ref = np.array([10.0, 10.0])
    mu = np.array([5.0, 5.0])
    sigma = np.array([0.01, 0.01])
    ehvi = compute_ehvi(mu, sigma, pareto, ref)
    assert ehvi >= 0.0
    assert ehvi < 1.0e-3


def test_compute_ehvi_increases_with_promising_candidate() -> None:
    pareto = np.array([[1.0, 5.0], [3.0, 3.0], [5.0, 1.0]])
    ref = np.array([6.0, 6.0])
    sigma = np.array([0.5, 0.5])
    # A candidate with mean near the "knee" should beat one far outside the
    # box.
    knee_score = compute_ehvi(np.array([2.0, 2.0]), sigma, pareto, ref)
    far_score = compute_ehvi(np.array([5.9, 5.9]), sigma, pareto, ref)
    assert knee_score > far_score


def test_compute_ehvi_1d_reduces_to_expected_improvement() -> None:
    # 1D EHVI is Expected Improvement against the incumbent best (minimisation).
    pareto = np.array([[2.0]])
    ref = np.array([10.0])
    mu = np.array([1.0])
    sigma = np.array([1.0])
    ehvi = compute_ehvi(mu, sigma, pareto, ref)
    # Closed-form EI: best=2, m=1, s=1, z=1; (best-m)*Phi(z) + s*phi(z)
    z = 1.0
    expected = (2.0 - 1.0) * 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))) + 1.0 * (
        math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    )
    assert abs(ehvi - expected) < 1.0e-9


def test_compute_ehvi_rejects_4plus_objectives() -> None:
    pareto = np.array([[1.0, 1.0, 1.0, 1.0]])
    ref = np.array([2.0, 2.0, 2.0, 2.0])
    mu = np.array([0.5, 0.5, 0.5, 0.5])
    sigma = np.array([0.1, 0.1, 0.1, 0.1])
    with pytest.raises(EhviDimensionError):
        compute_ehvi(mu, sigma, pareto, ref)


def test_compute_ehvi_3d_runs_and_is_nonnegative() -> None:
    pareto = np.array([[1.0, 3.0, 5.0], [2.0, 2.0, 4.0], [3.0, 1.0, 3.0]])
    ref = np.array([6.0, 6.0, 6.0])
    mu = np.array([1.5, 1.5, 3.0])
    sigma = np.array([0.5, 0.5, 0.5])
    ehvi = compute_ehvi(mu, sigma, pareto, ref)
    assert ehvi >= 0.0


def test_compute_ehvi_empty_pareto_front_returns_positive_for_uncertain_candidate() -> None:
    # With no existing front, every region under the reference point is
    # "improvement"; a finite-variance candidate should produce positive EHVI.
    ref = np.array([5.0, 5.0])
    ehvi = compute_ehvi(
        np.array([1.0, 1.0]),
        np.array([0.5, 0.5]),
        np.empty((0, 2)),
        ref,
    )
    assert ehvi > 0.0
