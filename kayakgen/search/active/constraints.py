"""Hard-rejection constraint evaluation for active search (RFC 0044)."""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, ConfigDict

from kayakgen.search.active.spec import SearchConstraint


class ConstraintViolation(BaseModel):
    """One violated constraint on an evaluated candidate."""

    model_config = ConfigDict(extra="forbid")

    metric: str
    bound: str  # "min" or "max"
    threshold: float
    actual: float | None
    reason: str | None = None


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def evaluate_constraints(
    summary: dict[str, Any],
    constraints: list[SearchConstraint],
) -> list[ConstraintViolation]:
    """Return violations of ``constraints`` against the candidate ``summary`` dict.

    Missing metrics produce a violation with ``actual=None`` so the candidate
    is still flagged ``constraint_failed`` and not silently allowed onto the
    frontier.
    """

    violations: list[ConstraintViolation] = []
    for constraint in constraints:
        actual = _coerce_float(summary.get(constraint.metric))
        if constraint.min is not None:
            if actual is None or actual < constraint.min:
                violations.append(
                    ConstraintViolation(
                        metric=constraint.metric,
                        bound="min",
                        threshold=constraint.min,
                        actual=actual,
                        reason=constraint.reason,
                    )
                )
        if constraint.max is not None:
            if actual is None or actual > constraint.max:
                violations.append(
                    ConstraintViolation(
                        metric=constraint.metric,
                        bound="max",
                        threshold=constraint.max,
                        actual=actual,
                        reason=constraint.reason,
                    )
                )
    return violations
