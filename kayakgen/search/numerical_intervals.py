"""Achieved numerical intervals for reported resistance comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from kayakgen.eval.contract import NumericalQuality, ResistanceComparisonInputs
from kayakgen.eval.michell_screening import POLICY_VERSION


INCOMPATIBLE_OPERATING_INPUTS = "incompatible_operating_inputs"


def operating_inputs_compatible(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Compare supplied operating context and any recorded physical curve conditions."""
    if (("operating_context" in left, left.get("operating_context"))
            != ("operating_context" in right, right.get("operating_context"))):
        return False
    if "operating_context" in left:
        # The complete operating projection already establishes the conditions.
        # Missing numerical assessment is an admission issue, not a load change.
        return True
    keys = []
    for details in (left, right):
        quality = details.get("numerical_quality")
        raw = (quality.comparison_inputs if isinstance(quality, NumericalQuality)
               else quality.get("comparison_inputs") if isinstance(quality, dict) else None)
        if raw is None:
            keys.append(None)
        else:
            try:
                keys.append(ResistanceComparisonInputs.model_validate(raw).comparison_key())
            except ValidationError:
                return False
    return keys[0] == keys[1]


@dataclass(frozen=True)
class ComparableInterval:
    bounds: tuple[float, float]
    comparison_key: tuple[Any, ...]


def objective_interval(
    metric: str,
    value: float,
    provenance: dict[str, Any],
) -> ComparableInterval | None:
    """Return a usable interval; missing achieved bounds are never zero error.

    Non-resistance objectives retain their existing exact comparison semantics.
    Only the registered last-speed resistance projection currently has an
    unambiguous mapping from objective value to the per-speed assessment.
    """
    from kayakgen.search.objectives import OBJECTIVE_METADATA

    metadata = OBJECTIVE_METADATA.get(metric)
    if metadata is None or metadata.source_evaluator != "resistance":
        return ComparableInterval((value, value), ("exact", metric))
    if metric != "Rt_N_last":
        return None
    details = provenance.get(metric)
    if not isinstance(details, dict):
        return None
    try:
        quality = NumericalQuality.model_validate(details.get("numerical_quality"))
    except ValidationError:
        return None
    if (
        quality.policy_version != POLICY_VERSION
        or quality.status != "converged"
        or not quality.absolute_uncertainty_N
        or quality.comparison_inputs is None
    ):
        return None
    if quality.observations and quality.observations[0].total_resistance_N[-1] != value:
        return None
    error = quality.absolute_uncertainty_N[-1]
    return ComparableInterval(
        (value - error, value + error),
        (
            *quality.comparison_inputs.comparison_key(),
            "operating_context" in details,
            details.get("operating_context"),
        ),
    )
