"""Active-search spec Pydantic schemas (RFC 0044 v1, RFC 0047 v2)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from kayakgen.search.sweep import EvaluatorOptions


class UniformVariable(BaseModel):
    """Continuous uniform search variable."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["uniform"] = "uniform"
    min: float
    max: float

    @model_validator(mode="after")
    def _validate_bounds(self) -> "UniformVariable":
        if not self.min < self.max:
            raise ValueError(
                f"uniform variable requires min < max (got min={self.min}, max={self.max})"
            )
        return self


class ChoiceVariable(BaseModel):
    """Discrete categorical search variable."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["choice"] = "choice"
    values: list[Any] = Field(..., min_length=1)

    @field_validator("values")
    @classmethod
    def _values_not_empty(cls, value: list[Any]) -> list[Any]:
        if not value:
            raise ValueError("choice variable requires non-empty values")
        return value


SearchVariable = UniformVariable | ChoiceVariable


class SearchAlgorithmSpec(BaseModel):
    """Algorithm-config block (v1 NSGA-II).

    v1 admits ``kind = "nsga2"`` (RFC 0044). The crossover/mutation knobs
    default to the standard NSGA-II SBX/polynomial choices. EHVI v2
    (RFC 0047) lives in a sibling :class:`EhviAlgorithmConfig` and is
    selected via :data:`SearchSpec.algorithm` accepting either record type.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["nsga2"] = "nsga2"
    population_size: int = Field(..., ge=2)
    generations: int = Field(..., ge=1)
    seed: int
    crossover_eta: float = Field(default=15.0, gt=0)
    mutation_eta: float = Field(default=20.0, gt=0)


GpKernelName = Literal["matern_5_2", "rbf"]


class EhviAlgorithmConfig(BaseModel):
    """v2 EHVI-over-multi-output-GP algorithm config (RFC 0047)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["ehvi"] = "ehvi"
    initial_population_size: int = Field(..., ge=2)
    iteration_budget: int = Field(..., ge=0)
    seed: int
    gp_kernel: GpKernelName = "matern_5_2"
    gp_noise_floor: float = Field(default=1.0e-6, gt=0.0)
    reference_point: Literal["auto"] | list[float] = "auto"
    candidate_pool_size: int = Field(default=256, ge=1)


SearchAlgorithm = Annotated[
    SearchAlgorithmSpec | EhviAlgorithmConfig,
    Field(discriminator="kind"),
]


class ObjectiveSpec(BaseModel):
    """One objective metric + direction."""

    model_config = ConfigDict(extra="forbid")

    metric: str
    direction: Literal["min", "max"]

    @field_validator("metric")
    @classmethod
    def _metric_not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("objective metric must not be blank")
        return text


class SearchConstraint(BaseModel):
    """A hard-rejection constraint on a metric.

    ``min`` and ``max`` are both optional but at least one must be set.
    """

    model_config = ConfigDict(extra="forbid")

    metric: str
    min: float | None = None
    max: float | None = None
    reason: str | None = None

    @field_validator("metric")
    @classmethod
    def _metric_not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("constraint metric must not be blank")
        return text

    @model_validator(mode="after")
    def _at_least_one_bound(self) -> "SearchConstraint":
        if self.min is None and self.max is None:
            raise ValueError("constraint requires at least one of min or max")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("constraint min must be <= max")
        return self


class SearchBudget(BaseModel):
    """Evaluation budget. At least one of ``max_evaluations`` / wall_clock must be set."""

    model_config = ConfigDict(extra="forbid")

    max_evaluations: int | None = Field(default=None, ge=1)
    wall_clock_seconds: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _at_least_one_budget(self) -> "SearchBudget":
        if self.max_evaluations is None and self.wall_clock_seconds is None:
            raise ValueError(
                "budget requires at least one of max_evaluations or wall_clock_seconds"
            )
        return self


class SearchLimits(BaseModel):
    """Runtime limits for the active-search runner."""

    model_config = ConfigDict(extra="forbid")

    max_pending: int = Field(default=0, ge=0)


class SearchSpec(BaseModel):
    """JSON-compatible active-search input (RFC 0044 v1)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    name: str = "search"
    base_hull: dict[str, Any] = Field(default_factory=dict)
    search_space: dict[str, SearchVariable]
    algorithm: SearchAlgorithm
    objectives: list[ObjectiveSpec] | None = None
    evaluators: EvaluatorOptions = Field(default_factory=EvaluatorOptions)
    constraints: list[SearchConstraint] = Field(default_factory=list)
    budget: SearchBudget
    limits: SearchLimits = Field(default_factory=SearchLimits)
    objectives_explicit_exploratory: bool = False

    @field_validator("search_space")
    @classmethod
    def _search_space_not_empty(
        cls, value: dict[str, SearchVariable]
    ) -> dict[str, SearchVariable]:
        if not value:
            raise ValueError("search_space must define at least one variable")
        return value


TerminationReason = Literal[
    "budget_exhausted",
    "wall_clock_exhausted",
    "operator_stop",
    "completed",
]

SearchClass = Literal["conservative", "exploratory"]


class GenerationHistoryEntry(BaseModel):
    """Per-generation summary appended to ``search_metadata.history``."""

    model_config = ConfigDict(extra="forbid")

    generation: int
    evaluated_count: int
    constraint_failed_count: int
    failed_count: int
    frontier_size: int
    objective_summary: dict[str, dict[str, float]] = Field(default_factory=dict)


class EhviHistoryEntry(BaseModel):
    """Per-iteration summary appended to ``search_metadata.history`` for EHVI runs.

    Extends the NSGA-II per-generation shape additively: every key the v1
    history carries is still present; ``ehvi_score`` is the EHVI of the
    candidate selected for evaluation in this iteration (zero for the LHS-
    initialisation phase) and ``frontier_size`` is the running Pareto-front
    size after the iteration evaluated.
    """

    model_config = ConfigDict(extra="forbid")

    iteration: int
    evaluated_count: int
    constraint_failed_count: int
    failed_count: int
    frontier_size: int
    ehvi_score: float = 0.0
    objective_summary: dict[str, dict[str, float]] = Field(default_factory=dict)


class SearchMetadata(BaseModel):
    """Header block recorded in ``run.json`` for active-search runs."""

    model_config = ConfigDict(extra="forbid")

    algorithm_kind: Literal["nsga2", "ehvi"] = "nsga2"
    seed: int
    population_size: int | None = None
    generations: int | None = None
    initial_population_size: int | None = None
    iteration_budget: int | None = None
    gp_kernel: Literal["matern_5_2", "rbf"] | None = None
    objectives: list[ObjectiveSpec]
    constraints: list[SearchConstraint] = Field(default_factory=list)
    realized_max_evaluations: int | None = None
    realized_wall_clock_seconds: float | None = None
    realized_evaluations: int = 0
    termination_reason: TerminationReason
    history: list[GenerationHistoryEntry] = Field(default_factory=list)
    ehvi_history: list[EhviHistoryEntry] = Field(default_factory=list)


def load_search_spec(path: str | Path) -> SearchSpec:
    """Parse a search spec JSON file."""
    return SearchSpec.model_validate_json(Path(path).read_text())
