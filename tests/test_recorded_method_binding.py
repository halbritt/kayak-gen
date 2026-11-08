"""Saved method identities must agree without demanding a runtime evaluator.

Retained numbers are consumer fixtures. Historical labels exercise serialization
compatibility, not numerical equivalence of different resistance methods.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from evaluator_guard import forbid_evaluator_calls
from pydantic import ValidationError

from kayakgen.eval.contract import EvaluationContext, EvaluationResult
from kayakgen.model.hull import Hull


# Evaluators a saved-result parser must never run. Shared with the guard's own
# order regressions in test_evaluator_guard.py.
PARSER_FORBIDDEN_EVALUATORS = {
    "kayakgen.eval.hydrostatics": ["evaluate"],
    "kayakgen.eval.resistance": [
        "resistance_curve",
        "evaluate_resistance",
        "wave_resistance_michell",
        "wetted_surface",
    ],
    "kayakgen.eval.numerical_resistance": ["assess_resistance"],
    "kayakgen.eval.michell_quadrature": ["wave_from_grid"],
    "kayakgen.eval.immersed_geometry": ["evaluate_immersed", "immersed_geometry"],
    "kayakgen.eval.stability.operating_equilibrium": ["evaluate_fixed_body_equilibrium"],
    "kayakgen.services.evaluation": [
        "evaluate_with_context",
        "evaluate_hydrostatics",
        "resistance_curve",
        "evaluate_resistance",
        "evaluate_equilibrium_stability",
    ],
}
# Modules that import the forbidden functions by name. The guard preloads them
# (with the target modules) before installing stubs so none keeps a stub alias.
PARSER_GUARD_CONSUMERS = (
    "kayakgen.eval",
    "kayakgen.eval.stability.initial",
    "kayakgen.eval.stability.load_case",
    "kayakgen.eval.stability.trim_equilibrium",
    "kayakgen.services.sensitivity",
    "kayakgen.services.design_report",
)


@pytest.fixture(autouse=True)
def forbid_evaluator_rerun():
    with forbid_evaluator_calls(
        PARSER_FORBIDDEN_EVALUATORS, consumers=PARSER_GUARD_CONSUMERS
    ) as guard:
        yield
    # Strict: stub calls are recorded even when pydantic wraps the AssertionError.
    assert guard.calls == []


def payload(context_method: str | None, curve_method: str | None, *, assessed: bool = False):
    root = Path(__file__).resolve().parents[1] / "docs/research/rfc0077"
    hull = Hull.model_validate_json(
        (root / "context-integration/study/candidates/candidate-08/hull.json").read_text()
    )
    curve = json.loads((root / "closure/08_5.json").read_text())
    if not assessed:
        curve["metadata"]["numerical_quality"] = {}
    curve["metadata"]["numerical_method_version"] = curve_method
    versions = [("hydrostatics", "mesh_integral_v1")]
    if context_method is not None:
        versions.append(("resistance", context_method))
    context = EvaluationContext.for_hull(
        hull,
        evaluator_versions=versions,
        speeds_knots=tuple(curve["V_knots"]),
        **curve["metadata"]["quadrature"],
        numerical_relative_tolerance=0.01 if assessed else None,
    )
    return dict(
        hull_hash=hull.record_hash(),
        context=context.model_dump(mode="json"),
        hydrostatics=json.loads(
            (root / "context-integration/study/candidates/candidate-08/hydro.json").read_text()
        ),
        resistance=curve,
    )


@pytest.mark.parametrize("context_method", ["michell_trapezoid_v1", ""])
def test_conflicting_recorded_methods_are_refused_before_any_evaluation(context_method):
    data = payload(context_method, "michell_linear_depth_v2", assessed=True)
    with pytest.raises(
        ValidationError, match="resistance method does not match evaluation context"
    ):
        EvaluationResult.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "context_method,curve_method,assessed",
    [
        ("michell_linear_depth_v2", "michell_linear_depth_v2", True),
        ("michell_trapezoid_v1", "michell_trapezoid_v1", False),
        ("archived_method_unavailable_v0", "archived_method_unavailable_v0", False),
        ("michell_trapezoid_v1", None, False),
        (None, "michell_linear_depth_v2", True),
        (None, None, False),
    ],
)
def test_matching_historical_and_missing_method_metadata_remain_readable(
    context_method, curve_method, assessed
):
    result = EvaluationResult.model_validate_json(
        json.dumps(payload(context_method, curve_method, assessed=assessed))
    )
    assert dict(result.context.evaluator_versions).get("resistance") == context_method
    assert result.resistance.metadata.numerical_method_version == curve_method
    assert result.resistance.metadata.numerical_quality.status == (
        "converged" if assessed else "unknown"
    )
