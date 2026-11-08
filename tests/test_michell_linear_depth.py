"""Independent polynomial controls for the depth quadrature correction."""

from __future__ import annotations

from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np
import pytest

from kayakgen.eval.michell_quadrature import integrate_linear_depth, wave_from_grid
from kayakgen.eval.resistance import KNOTS_TO_MS, wave_resistance_michell
from kayakgen.model.hull import Hull


@pytest.mark.parametrize("beta", [1e-6, 0.01, 1.0, 1000.0, 1e8])
def test_linear_depth_has_exact_laplace_transform_even_in_boundary_layer(beta: float) -> None:
    with localcontext() as ctx:
        ctx.prec = 60
        b = Decimal(str(beta))
        exponential = Decimal(0) if beta > 100 else (-b).exp()
        expected_constant = float((1 - exponential) / b)
        expected_linear = float((b - 1 + exponential) / (b * b))
    result = integrate_linear_depth(np.array([0.0, 1.0]), np.array([[1.0, 1.0], [1.0, 0.0]]), beta)
    np.testing.assert_allclose(result, [expected_constant, expected_linear], rtol=1e-12)


def _wigley_closed_transform_reference(fn: float) -> float:
    # Integrate a closed-form polynomial x/z transform independently of any grid
    # derivative or sampled-depth implementation. Tail bound is in the study.
    gravity = 9.80665
    rho = 1025.0
    length = 1.0
    beam = 0.1
    draft = 0.0625
    speed = fn * np.sqrt(gravity * length)
    k0 = gravity / speed**2
    theta = np.linspace(0.0, np.arccos(1 / 64), 200001)
    sec = 1 / np.cos(theta)
    alpha = k0 * sec
    beta = k0 * sec**2
    z = (
        1 / beta
        - 2 / (beta**3 * draft**2)
        + np.exp(-beta * draft) * (2 / (beta**2 * draft) + 2 / (beta**3 * draft**2))
    )
    a = length / 2
    x = 8 * beam / length**2 * (a * np.cos(alpha * a) / alpha - np.sin(alpha * a) / alpha**2)
    return float(
        16 * rho * gravity**2 / (np.pi * speed**2) * np.trapezoid((x * z) ** 2 * sec**3, theta)
    )


@pytest.mark.parametrize("fn", [0.25, 0.3, 0.4, 0.5])
def test_corrected_production_kernel_matches_independent_wigley_transform(fn: float) -> None:
    xs = np.linspace(-0.5, 0.5, 800)
    zs = np.linspace(0.0, 0.0625, 80)
    widths = 0.05 * (1 - (2 * xs[:, None]) ** 2) * (1 - (zs[None, :] / 0.0625) ** 2)
    actual = wave_from_grid(xs, zs, widths, fn * np.sqrt(9.80665), 640, 1025.0, 9.80665)
    assert actual == pytest.approx(_wigley_closed_transform_reference(fn), rel=1e-3)


def test_recorded_sharp_hull_no_longer_has_depth_endpoint_spike() -> None:
    path = Path(__file__).parent / "fixtures/numerical/fast-tourer-06.json"
    hull = Hull.model_validate_json(path.read_text())
    values = [
        wave_resistance_michell(hull, 4.5 * KNOTS_TO_MS, *resolution)
        for resolution in [(400, 25, 40), (800, 50, 80), (1600, 100, 160)]
    ]
    assert all(value > 0 for value in values)
    assert max(values) / min(values) < 1.05
