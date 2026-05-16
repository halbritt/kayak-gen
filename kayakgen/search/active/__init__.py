"""Active hull-design search (RFC 0044 v1 NSGA-II, RFC 0047 v2 EHVI).

Public surface:

  - :class:`kayakgen.search.active.spec.SearchSpec` and friends.
  - :func:`kayakgen.search.active.runner.run_search`.
  - :func:`kayakgen.search.active.nsga2.nsga2_iterations`.
  - :class:`kayakgen.search.active.gp.GaussianProcess` (v2).
  - :func:`kayakgen.search.active.ehvi.compute_ehvi` (v2).

The CLI exposes this through ``kayakgen search``. The default
``kayakgen sweep`` and ``kayakgen compare`` paths are untouched.
"""

from kayakgen.search.active.ehvi import EhviDimensionError, compute_ehvi
from kayakgen.search.active.gp import (
    GaussianProcess,
    Kernel,
    MaternKernel52,
    RbfKernel,
    kernel_by_name,
)
from kayakgen.search.active.runner import (
    SearchRunRecord,
    SearchRunResult,
    run_search,
)
from kayakgen.search.active.spec import (
    EhviAlgorithmConfig,
    EhviHistoryEntry,
    GenerationHistoryEntry,
    ObjectiveSpec,
    SearchAlgorithmSpec,
    SearchBudget,
    SearchConstraint,
    SearchLimits,
    SearchMetadata,
    SearchSpec,
    SearchVariable,
    ChoiceVariable,
    UniformVariable,
    load_search_spec,
)

__all__ = [
    "ChoiceVariable",
    "EhviAlgorithmConfig",
    "EhviDimensionError",
    "EhviHistoryEntry",
    "GaussianProcess",
    "GenerationHistoryEntry",
    "Kernel",
    "MaternKernel52",
    "ObjectiveSpec",
    "RbfKernel",
    "SearchAlgorithmSpec",
    "SearchBudget",
    "SearchConstraint",
    "SearchLimits",
    "SearchMetadata",
    "SearchRunRecord",
    "SearchRunResult",
    "SearchSpec",
    "SearchVariable",
    "UniformVariable",
    "compute_ehvi",
    "kernel_by_name",
    "load_search_spec",
    "run_search",
]
