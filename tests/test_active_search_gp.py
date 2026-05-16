"""RFC 0047 v2 vendored Gaussian-process surrogate tests."""

from __future__ import annotations

import numpy as np
import pytest

from kayakgen.search.active.gp import (
    GaussianProcess,
    MaternKernel52,
    RbfKernel,
    kernel_by_name,
)


def _synthetic_2d_dataset(seed: int = 0, n: int = 24):
    rng = np.random.default_rng(seed)
    X = rng.uniform(0.0, 1.0, size=(n, 2))
    y = np.sin(2.0 * np.pi * X[:, 0]) + 0.5 * X[:, 1]
    return X, y


def test_gaussian_process_fit_is_deterministic_with_seeded_rng() -> None:
    X, y = _synthetic_2d_dataset(seed=7)
    rng_a = np.random.default_rng(123)
    rng_b = np.random.default_rng(123)

    gp_a = GaussianProcess(MaternKernel52(), noise_floor=1.0e-6)
    gp_b = GaussianProcess(MaternKernel52(), noise_floor=1.0e-6)
    gp_a.fit(X, y, rng=rng_a, max_marginal_likelihood_evals=200)
    gp_b.fit(X, y, rng=rng_b, max_marginal_likelihood_evals=200)

    mean_a, var_a = gp_a.predict(X)
    mean_b, var_b = gp_b.predict(X)
    np.testing.assert_array_equal(mean_a, mean_b)
    np.testing.assert_array_equal(var_a, var_b)


def test_gaussian_process_predicts_mean_and_variance_with_correct_shape() -> None:
    X, y = _synthetic_2d_dataset(seed=1)
    gp = GaussianProcess(RbfKernel(), noise_floor=1.0e-6)
    gp.fit(X, y, rng=np.random.default_rng(0), max_marginal_likelihood_evals=100)
    test_X = np.array([[0.1, 0.2], [0.5, 0.5], [0.9, 0.1]])
    mean, var = gp.predict(test_X)
    assert mean.shape == (3,)
    assert var.shape == (3,)
    assert np.all(var >= 0.0)


def test_gp_predict_interpolates_training_points_closely() -> None:
    X, y = _synthetic_2d_dataset(seed=3, n=18)
    gp = GaussianProcess(MaternKernel52(), noise_floor=1.0e-6)
    gp.fit(X, y, rng=np.random.default_rng(2))
    mean, var = gp.predict(X)
    # On training data, mean should be close to y. (Not exact because of noise floor.)
    assert np.max(np.abs(mean - y)) < 0.5
    # Predicted variance at training points should be small.
    assert np.max(var) < 1.0


def test_gp_predict_raises_when_not_fitted() -> None:
    gp = GaussianProcess(MaternKernel52(), noise_floor=1.0e-6)
    with pytest.raises(RuntimeError):
        gp.predict(np.zeros((1, 2)))


def test_kernel_by_name_supports_known_kernels_and_rejects_unknown() -> None:
    assert isinstance(kernel_by_name("matern_5_2"), MaternKernel52)
    assert isinstance(kernel_by_name("rbf"), RbfKernel)
    with pytest.raises(ValueError):
        kernel_by_name("not_a_kernel")
