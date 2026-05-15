"""Active hull-design search (RFC 0044 v1).

Public surface:

  - :class:`kayakgen.search.active.spec.SearchSpec` and friends.
  - :func:`kayakgen.search.active.runner.run_search`.
  - :func:`kayakgen.search.active.nsga2.nsga2_iterations`.

The CLI exposes this through ``kayakgen search``. The default
``kayakgen sweep`` and ``kayakgen compare`` paths are untouched.
"""

from kayakgen.search.active.runner import (
    SearchRunRecord,
    SearchRunResult,
    run_search,
)
from kayakgen.search.active.spec import (
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
    "GenerationHistoryEntry",
    "ObjectiveSpec",
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
    "load_search_spec",
    "run_search",
]
