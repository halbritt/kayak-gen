"""RFC 0044 SearchSpec schema round-trips and validation."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from kayakgen.search.active.spec import (
    ChoiceVariable,
    ObjectiveSpec,
    SearchAlgorithmSpec,
    SearchBudget,
    SearchConstraint,
    SearchLimits,
    SearchSpec,
    UniformVariable,
)


def _full_spec_payload() -> dict:
    return {
        "schema_version": "1",
        "name": "touring-sea-kayak-pareto",
        "base_hull": {"length_m": 5.2, "beam_oa_m": 0.55, "draft_m": 0.12},
        "search_space": {
            "length_m": {"kind": "uniform", "min": 4.4, "max": 5.6},
            "beam_wl_m": {"kind": "uniform", "min": 0.46, "max": 0.55},
            "Cp": {"kind": "uniform", "min": 0.50, "max": 0.62},
        },
        "algorithm": {
            "kind": "nsga2",
            "population_size": 24,
            "generations": 8,
            "seed": 1234,
        },
        "objectives": [
            {"metric": "GM0_m", "direction": "max"},
            {"metric": "displacement_error_kg", "direction": "min"},
        ],
        "evaluators": {"hydrostatics": True},
        "constraints": [
            {"metric": "displaced_mass_kg", "min": 85.0},
            {"metric": "wetted_surface_m2", "max": 1.5, "reason": "drag-class"},
        ],
        "budget": {"max_evaluations": 192, "wall_clock_seconds": 600.0},
        "limits": {"max_pending": 8},
        "objectives_explicit_exploratory": False,
    }


def test_search_spec_round_trips_json() -> None:
    payload = _full_spec_payload()
    spec = SearchSpec.model_validate(payload)
    again = SearchSpec.model_validate_json(spec.model_dump_json())
    assert again.model_dump() == spec.model_dump()
    parsed = json.loads(spec.model_dump_json())
    assert parsed["search_space"]["length_m"]["kind"] == "uniform"
    assert parsed["algorithm"]["seed"] == 1234


def test_search_spec_rejects_missing_budget() -> None:
    with pytest.raises(ValidationError):
        SearchBudget()  # neither set


def test_search_spec_uniform_variable_min_lt_max() -> None:
    with pytest.raises(ValidationError):
        UniformVariable.model_validate({"kind": "uniform", "min": 0.6, "max": 0.6})
    with pytest.raises(ValidationError):
        UniformVariable.model_validate({"kind": "uniform", "min": 0.7, "max": 0.5})


def test_choice_variable_requires_non_empty_values() -> None:
    with pytest.raises(ValidationError):
        ChoiceVariable.model_validate({"kind": "choice", "values": []})


def test_search_algorithm_requires_population_size_at_least_two() -> None:
    with pytest.raises(ValidationError):
        SearchAlgorithmSpec(population_size=1, generations=4, seed=1)


def test_search_constraint_requires_at_least_one_bound() -> None:
    with pytest.raises(ValidationError):
        SearchConstraint(metric="GM0_m")


def test_search_spec_defaults_omit_objectives() -> None:
    payload = _full_spec_payload()
    payload.pop("objectives")
    spec = SearchSpec.model_validate(payload)
    assert spec.objectives is None


def test_search_spec_search_space_must_not_be_empty() -> None:
    payload = _full_spec_payload()
    payload["search_space"] = {}
    with pytest.raises(ValidationError):
        SearchSpec.model_validate(payload)


def test_search_limits_defaults() -> None:
    limits = SearchLimits()
    assert limits.max_pending == 0


def test_objective_spec_metric_must_not_be_blank() -> None:
    with pytest.raises(ValidationError):
        ObjectiveSpec(metric="   ", direction="min")
