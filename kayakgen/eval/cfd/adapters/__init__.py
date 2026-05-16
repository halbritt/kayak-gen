"""Local CFD solver adapters used by the dispatch surface."""

from __future__ import annotations

from kayakgen.eval.cfd.adapters.fixture import FixtureLocalCommandAdapter
from kayakgen.eval.cfd.adapters.mock import MockFailingLocalCommandAdapter
from kayakgen.eval.cfd.adapters.openfoam_v2512 import (
    OpenFoamLocalAdapter,
    resolve_real_solver_execution_opt_in,
)
from kayakgen.eval.cfd.adapters.unavailable import UnavailableSolverAdapter

__all__ = [
    "FixtureLocalCommandAdapter",
    "MockFailingLocalCommandAdapter",
    "OpenFoamLocalAdapter",
    "UnavailableSolverAdapter",
    "resolve_real_solver_execution_opt_in",
]
