"""Vendored NSGA-II implementation (RFC 0044 v1).

Pure-Python multi-objective evolutionary algorithm with seeded determinism.
Uses ``random.Random(seed)`` exclusively; never consumes the global RNG.

Operators:
  - SBX (simulated binary crossover) for ``uniform`` variables, ``eta_c`` default 15.
  - Polynomial mutation for ``uniform`` variables, ``eta_m`` default 20,
    mutation probability ``1/n_vars`` per gene.
  - Uniform random resampling for ``choice`` variables; no crossover.
  - Binary tournament selection (size 2) using non-dominated rank then
    crowding distance.

The runner consumes :func:`nsga2_iterations`, which yields one
:class:`Generation` per algorithm step so the runner can checkpoint between
generations.
"""

from __future__ import annotations

import math
import random
from typing import Any, Callable, Iterator

from pydantic import BaseModel, ConfigDict, Field

from kayakgen.search.active.spec import (
    ChoiceVariable,
    SearchAlgorithmSpec,
    SearchVariable,
    UniformVariable,
)


# ---------------------------------------------------------------------------
# Population data structures
# ---------------------------------------------------------------------------


class Individual(BaseModel):
    """One candidate genome and its scored objectives.

    ``objectives`` are filled in by the evaluator callback; the algorithm
    treats them as floats in minimize-direction. A ``rank`` and
    ``crowding_distance`` are populated by the non-dominated sort.

    ``feasible`` reports whether the evaluator considered the candidate
    feasible; infeasible individuals are pushed to the back of every front
    (handled by the runner's wrapping of the objective vector).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    genome: dict[str, Any]
    objectives: tuple[float, ...] = ()
    rank: int = -1
    crowding_distance: float = 0.0
    feasible: bool = True


class Generation(BaseModel):
    """A single completed generation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    index: int
    population: list[Individual] = Field(default_factory=list)
    fronts: list[list[int]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Operator primitives
# ---------------------------------------------------------------------------


def _sample_variable(rng: random.Random, variable: SearchVariable) -> Any:
    if isinstance(variable, UniformVariable):
        return rng.uniform(variable.min, variable.max)
    if isinstance(variable, ChoiceVariable):
        return rng.choice(variable.values)
    raise TypeError(f"unsupported search variable kind: {type(variable).__name__}")


def initialize_population(
    rng: random.Random,
    search_space: dict[str, SearchVariable],
    population_size: int,
) -> list[Individual]:
    """Sample ``population_size`` individuals uniformly from the search_space."""
    population: list[Individual] = []
    names = list(search_space)
    for _ in range(population_size):
        genome = {name: _sample_variable(rng, search_space[name]) for name in names}
        population.append(Individual(genome=genome))
    return population


def _sbx_crossover_continuous(
    rng: random.Random,
    p1: float,
    p2: float,
    lower: float,
    upper: float,
    eta_c: float,
) -> tuple[float, float]:
    """Simulated binary crossover for one continuous gene."""
    if math.isclose(p1, p2):
        return p1, p2
    if lower >= upper:
        return p1, p2

    # Order parents so p1_l <= p2_h.
    if p1 < p2:
        p_lo, p_hi = p1, p2
    else:
        p_lo, p_hi = p2, p1

    u = rng.random()
    # Standard SBX (Deb & Agrawal 1995) with bounded handling.
    beta = 1.0 + (2.0 * (p_lo - lower) / max(p_hi - p_lo, 1e-14))
    alpha = 2.0 - beta ** (-(eta_c + 1.0))
    if u <= 1.0 / alpha:
        beta_q = (u * alpha) ** (1.0 / (eta_c + 1.0))
    else:
        beta_q = (1.0 / (2.0 - u * alpha)) ** (1.0 / (eta_c + 1.0))
    c1 = 0.5 * ((p_lo + p_hi) - beta_q * (p_hi - p_lo))

    beta = 1.0 + (2.0 * (upper - p_hi) / max(p_hi - p_lo, 1e-14))
    alpha = 2.0 - beta ** (-(eta_c + 1.0))
    if u <= 1.0 / alpha:
        beta_q = (u * alpha) ** (1.0 / (eta_c + 1.0))
    else:
        beta_q = (1.0 / (2.0 - u * alpha)) ** (1.0 / (eta_c + 1.0))
    c2 = 0.5 * ((p_lo + p_hi) + beta_q * (p_hi - p_lo))

    c1 = min(max(c1, lower), upper)
    c2 = min(max(c2, lower), upper)
    if rng.random() < 0.5:
        return c1, c2
    return c2, c1


def _polynomial_mutation_continuous(
    rng: random.Random,
    value: float,
    lower: float,
    upper: float,
    eta_m: float,
) -> float:
    """Polynomial mutation for one continuous gene."""
    if lower >= upper:
        return value
    u = rng.random()
    delta1 = (value - lower) / (upper - lower)
    delta2 = (upper - value) / (upper - lower)
    mut_pow = 1.0 / (eta_m + 1.0)
    if u < 0.5:
        xy = 1.0 - delta1
        val = 2.0 * u + (1.0 - 2.0 * u) * (xy ** (eta_m + 1.0))
        deltaq = val ** mut_pow - 1.0
    else:
        xy = 1.0 - delta2
        val = 2.0 * (1.0 - u) + 2.0 * (u - 0.5) * (xy ** (eta_m + 1.0))
        deltaq = 1.0 - val ** mut_pow
    new_value = value + deltaq * (upper - lower)
    return min(max(new_value, lower), upper)


def crossover(
    rng: random.Random,
    parent_a: Individual,
    parent_b: Individual,
    search_space: dict[str, SearchVariable],
    eta_c: float,
) -> tuple[Individual, Individual]:
    """Per-gene SBX for uniform variables; uniform mix for choice variables."""
    child_a_genome: dict[str, Any] = {}
    child_b_genome: dict[str, Any] = {}
    for name, variable in search_space.items():
        a_val = parent_a.genome[name]
        b_val = parent_b.genome[name]
        if isinstance(variable, UniformVariable):
            ca, cb = _sbx_crossover_continuous(
                rng,
                float(a_val),
                float(b_val),
                variable.min,
                variable.max,
                eta_c,
            )
            child_a_genome[name] = ca
            child_b_genome[name] = cb
        elif isinstance(variable, ChoiceVariable):
            if rng.random() < 0.5:
                child_a_genome[name] = a_val
                child_b_genome[name] = b_val
            else:
                child_a_genome[name] = b_val
                child_b_genome[name] = a_val
        else:  # pragma: no cover - guarded by spec validators
            raise TypeError(f"unsupported variable: {variable!r}")
    return Individual(genome=child_a_genome), Individual(genome=child_b_genome)


def mutate(
    rng: random.Random,
    individual: Individual,
    search_space: dict[str, SearchVariable],
    eta_m: float,
    mutation_probability: float,
) -> Individual:
    """Polynomial mutation for uniform genes; resample for choice genes."""
    new_genome: dict[str, Any] = {}
    for name, variable in search_space.items():
        if rng.random() < mutation_probability:
            if isinstance(variable, UniformVariable):
                new_genome[name] = _polynomial_mutation_continuous(
                    rng,
                    float(individual.genome[name]),
                    variable.min,
                    variable.max,
                    eta_m,
                )
            elif isinstance(variable, ChoiceVariable):
                new_genome[name] = rng.choice(variable.values)
            else:  # pragma: no cover
                new_genome[name] = individual.genome[name]
        else:
            new_genome[name] = individual.genome[name]
    return Individual(genome=new_genome)


# ---------------------------------------------------------------------------
# Non-dominated sort + crowding distance
# ---------------------------------------------------------------------------


def _dominates(a: Individual, b: Individual) -> bool:
    """Return whether ``a`` Pareto-dominates ``b`` (all objectives are minimized)."""
    if not a.objectives or not b.objectives:
        return False
    # Infeasible individuals never dominate feasible ones.
    if a.feasible != b.feasible:
        return a.feasible and not b.feasible
    better_in_any = False
    for av, bv in zip(a.objectives, b.objectives):
        if av > bv:
            return False
        if av < bv:
            better_in_any = True
    return better_in_any


def non_dominated_sort(population: list[Individual]) -> list[list[int]]:
    """Return ranked fronts as lists of indices into ``population``."""
    n = len(population)
    dominated_by: list[list[int]] = [[] for _ in range(n)]
    domination_count = [0 for _ in range(n)]
    fronts: list[list[int]] = [[]]

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if _dominates(population[i], population[j]):
                dominated_by[i].append(j)
            elif _dominates(population[j], population[i]):
                domination_count[i] += 1
        if domination_count[i] == 0:
            population[i] = population[i].model_copy(update={"rank": 0})
            fronts[0].append(i)

    front_index = 0
    while fronts[front_index]:
        next_front: list[int] = []
        for i in fronts[front_index]:
            for j in dominated_by[i]:
                domination_count[j] -= 1
                if domination_count[j] == 0:
                    population[j] = population[j].model_copy(
                        update={"rank": front_index + 1}
                    )
                    next_front.append(j)
        front_index += 1
        fronts.append(next_front)

    # Drop the trailing empty list.
    return [f for f in fronts if f]


def crowding_distance_assignment(
    population: list[Individual], front: list[int]
) -> None:
    """Assign crowding distances to individuals in ``front`` (in place)."""
    if not front:
        return
    n_objectives = len(population[front[0]].objectives)
    distances = {idx: 0.0 for idx in front}
    front_len = len(front)
    if front_len <= 2:
        for idx in front:
            population[idx] = population[idx].model_copy(
                update={"crowding_distance": math.inf}
            )
        return

    for m in range(n_objectives):
        ordered = sorted(front, key=lambda idx: population[idx].objectives[m])
        distances[ordered[0]] = math.inf
        distances[ordered[-1]] = math.inf
        f_min = population[ordered[0]].objectives[m]
        f_max = population[ordered[-1]].objectives[m]
        denom = f_max - f_min
        if denom <= 0.0:
            continue
        for k in range(1, front_len - 1):
            next_v = population[ordered[k + 1]].objectives[m]
            prev_v = population[ordered[k - 1]].objectives[m]
            distances[ordered[k]] += (next_v - prev_v) / denom

    for idx in front:
        population[idx] = population[idx].model_copy(
            update={"crowding_distance": distances[idx]}
        )


# ---------------------------------------------------------------------------
# Selection + iteration
# ---------------------------------------------------------------------------


def _tournament(rng: random.Random, population: list[Individual]) -> Individual:
    """Binary tournament; lower rank wins, then larger crowding distance."""
    i = rng.randrange(len(population))
    j = rng.randrange(len(population))
    a = population[i]
    b = population[j]
    if a.rank < b.rank:
        return a
    if a.rank > b.rank:
        return b
    if a.crowding_distance > b.crowding_distance:
        return a
    if a.crowding_distance < b.crowding_distance:
        return b
    # Tie-break by chosen index order (lower-i wins) for determinism.
    return a if i <= j else b


def _make_offspring(
    rng: random.Random,
    population: list[Individual],
    search_space: dict[str, SearchVariable],
    population_size: int,
    eta_c: float,
    eta_m: float,
) -> list[Individual]:
    n_vars = max(len(search_space), 1)
    mutation_probability = 1.0 / n_vars
    offspring: list[Individual] = []
    while len(offspring) < population_size:
        parent_a = _tournament(rng, population)
        parent_b = _tournament(rng, population)
        child_a, child_b = crossover(rng, parent_a, parent_b, search_space, eta_c)
        child_a = mutate(rng, child_a, search_space, eta_m, mutation_probability)
        child_b = mutate(rng, child_b, search_space, eta_m, mutation_probability)
        offspring.append(child_a)
        if len(offspring) < population_size:
            offspring.append(child_b)
    return offspring


def select_next_population(
    combined: list[Individual], population_size: int
) -> tuple[list[Individual], list[list[int]]]:
    """Pick the next-generation survivors by rank then crowding distance.

    Returns ``(selected, fronts)`` where ``fronts`` is the non-dominated
    decomposition of ``combined``.
    """
    fronts = non_dominated_sort(combined)
    for front in fronts:
        crowding_distance_assignment(combined, front)

    selected: list[Individual] = []
    for front in fronts:
        if len(selected) + len(front) <= population_size:
            selected.extend(combined[idx] for idx in front)
        else:
            remaining = population_size - len(selected)
            ordered = sorted(
                front,
                key=lambda idx: (-combined[idx].crowding_distance, idx),
            )
            selected.extend(combined[idx] for idx in ordered[:remaining])
            break
    return selected, fronts


# ---------------------------------------------------------------------------
# Public iterator
# ---------------------------------------------------------------------------


EvaluatorCallable = Callable[[Individual], Individual]


def nsga2_iterations(
    spec: SearchAlgorithmSpec,
    search_space: dict[str, SearchVariable],
    evaluator: EvaluatorCallable,
    rng_seed: int | None = None,
) -> Iterator[Generation]:
    """Yield :class:`Generation` per algorithm step.

    The evaluator must return an :class:`Individual` with its ``objectives``
    populated. The caller is responsible for shaping its return into a
    minimize-direction tuple; infeasible individuals should set
    ``feasible=False`` and may use ``math.inf`` for missing objective slots.

    The runner can ``next(...)`` this iterator generation-by-generation and
    persist state between calls. Exhausts after ``spec.generations`` yields.
    """
    seed = spec.seed if rng_seed is None else rng_seed
    rng = random.Random(seed)

    population = initialize_population(rng, search_space, spec.population_size)
    population = [evaluator(ind) for ind in population]
    population, fronts = select_next_population(population, spec.population_size)
    yield Generation(index=0, population=list(population), fronts=fronts)

    for gen_index in range(1, spec.generations):
        offspring = _make_offspring(
            rng,
            population,
            search_space,
            spec.population_size,
            spec.crossover_eta,
            spec.mutation_eta,
        )
        offspring = [evaluator(ind) for ind in offspring]
        combined = list(population) + offspring
        population, fronts = select_next_population(combined, spec.population_size)
        yield Generation(index=gen_index, population=list(population), fronts=fronts)
