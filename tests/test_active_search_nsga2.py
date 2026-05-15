"""Vendored NSGA-II determinism and operator invariants (RFC 0044)."""

from __future__ import annotations

import math

from kayakgen.search.active.nsga2 import (
    Generation,
    Individual,
    initialize_population,
    non_dominated_sort,
    nsga2_iterations,
)
from kayakgen.search.active.spec import (
    ChoiceVariable,
    SearchAlgorithmSpec,
    UniformVariable,
)


def _quadratic_evaluator(individual: Individual) -> Individual:
    x = float(individual.genome["x"])
    y = float(individual.genome["y"])
    # Two-objective ZDT-style: minimise both.
    return individual.model_copy(
        update={"objectives": (x * x, (1.0 - x) ** 2 + y * y), "feasible": True}
    )


def _spec() -> SearchAlgorithmSpec:
    return SearchAlgorithmSpec(
        kind="nsga2",
        population_size=8,
        generations=4,
        seed=42,
    )


def _search_space() -> dict:
    return {
        "x": UniformVariable(kind="uniform", min=0.0, max=1.0),
        "y": UniformVariable(kind="uniform", min=-1.0, max=1.0),
    }


def _serialize(generation: Generation) -> list[tuple]:
    out: list[tuple] = []
    for ind in generation.population:
        out.append(
            (
                tuple(sorted(ind.genome.items())),
                tuple(ind.objectives),
                ind.rank,
                ind.feasible,
            )
        )
    return out


def test_nsga2_seeded_run_is_deterministic() -> None:
    spec = _spec()
    search_space = _search_space()
    a = [_serialize(g) for g in nsga2_iterations(spec, search_space, _quadratic_evaluator)]
    b = [_serialize(g) for g in nsga2_iterations(spec, search_space, _quadratic_evaluator)]
    assert a == b
    assert len(a) == spec.generations


def test_nsga2_population_respects_bounds() -> None:
    spec = _spec()
    search_space = _search_space()
    for generation in nsga2_iterations(spec, search_space, _quadratic_evaluator):
        for individual in generation.population:
            x = individual.genome["x"]
            y = individual.genome["y"]
            assert 0.0 <= x <= 1.0
            assert -1.0 <= y <= 1.0


def test_nsga2_choice_variable_population_stays_in_values() -> None:
    import random

    rng = random.Random(7)
    space = {
        "letter": ChoiceVariable(kind="choice", values=["a", "b", "c"]),
        "x": UniformVariable(kind="uniform", min=0.0, max=2.0),
    }
    population = initialize_population(rng, space, 16)
    for individual in population:
        assert individual.genome["letter"] in {"a", "b", "c"}
        assert 0.0 <= individual.genome["x"] <= 2.0


def test_nsga2_non_dominated_sort_finds_known_front() -> None:
    # Two clearly-Pareto-front candidates (A and B) and one dominated (C).
    inds = [
        Individual(genome={"i": 0}, objectives=(1.0, 4.0), feasible=True),
        Individual(genome={"i": 1}, objectives=(2.0, 3.0), feasible=True),
        Individual(genome={"i": 2}, objectives=(3.0, 5.0), feasible=True),  # dominated by A
    ]
    fronts = non_dominated_sort(inds)
    assert fronts[0] == [0, 1]
    assert fronts[1] == [2]


def test_nsga2_infeasible_individuals_sort_to_back() -> None:
    inds = [
        Individual(genome={"i": 0}, objectives=(math.inf, math.inf), feasible=False),
        Individual(genome={"i": 1}, objectives=(2.0, 3.0), feasible=True),
    ]
    fronts = non_dominated_sort(inds)
    assert fronts[0] == [1]
    assert fronts[1] == [0]


def test_nsga2_runs_specified_generations() -> None:
    spec = _spec()
    search_space = _search_space()
    generations = list(nsga2_iterations(spec, search_space, _quadratic_evaluator))
    assert [g.index for g in generations] == list(range(spec.generations))
    for g in generations:
        assert len(g.population) == spec.population_size
