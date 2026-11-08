"""Cached real owner-study assessments for public numerical admission tests."""

from functools import lru_cache
from pathlib import Path

import numpy as np

from kayakgen.eval.resistance import resistance_curve
from kayakgen.model.hull import Hull


@lru_cache(maxsize=None)
def assessed_curve(number: int = 8, speed: float = 5.0, rho: float = 1025.0):
    hull = Hull.model_validate_json(
        (Path(__file__).parent / f"fixtures/numerical/fast-tourer-{number:02d}.json").read_text()
    )
    curve = resistance_curve(
        hull,
        np.array([speed]),
        n_stations=400,
        n_depths=25,
        n_theta=40,
        rho=rho,
        numerical_relative_tolerance=0.01,
    )
    assert curve.metadata.numerical_quality.status == "converged"
    return curve
