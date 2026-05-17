"""RFC 0052 local sensitivity service.

Computes a finite-difference Jacobian of summary metrics with respect to
Hull parameters. Sensitivity is intentionally a *service* over the existing
Hull aggregate and evaluator pipeline — not a method on Hull — so that the
finite-difference loop never leaks into the design aggregate, and so the
``services`` layer keeps owning the "exercise multiple evaluators against
one hull" orchestration.

The result is explicitly a *local* sensitivity tagged with the per-parameter
step that produced it. It is not a calibration or validity claim.
"""

from __future__ import annotations

import math
from typing import Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from kayakgen.eval.contract import LoadCase, StabilityResult
from kayakgen.eval.hydrostatics import Hydrostatics, evaluate as evaluate_hydrostatics
from kayakgen.eval.stability import evaluate_initial_stability
from kayakgen.model.hull import Hull

# Auto-step is ``AUTO_STEP_FRACTION * baseline_value`` per parameter, clamped
# to ``[AUTO_STEP_MIN, AUTO_STEP_MAX]``. The clamp keeps the step inside a
# regime where the lofted geometry is well-behaved (sub-millimeter dimensions
# round-trip cleanly through the float64 station mesh, and centimeter steps
# stay inside any single parameter's validity envelope).
AUTO_STEP_FRACTION: float = 1e-4
AUTO_STEP_MIN: float = 1e-9
AUTO_STEP_MAX: float = 1e-2


class SensitivityRequest(BaseModel):
    """Inputs for a local-sensitivity run.

    ``hull_path`` points to a serialized ``Hull`` JSON record; the service
    loads it through the standard ``load_hull`` adapter. ``params`` and
    ``metrics`` are lists of names; unknown names surface as structured
    non-finite entries in the result so the CLI can echo the rejection
    without aborting the whole sweep.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    hull_path: str
    params: list[str]
    metrics: list[str]
    step: float | None = None

    @field_validator("params", "metrics")
    @classmethod
    def _at_least_one(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("SensitivityRequest must list at least one entry")
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("SensitivityRequest entries must be non-blank strings")
        return value

    @field_validator("step")
    @classmethod
    def _step_must_be_positive_or_none(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if not math.isfinite(value) or value <= 0:
            raise ValueError("SensitivityRequest.step must be a positive finite number")
        return value


class SensitivityResult(BaseModel):
    """RFC 0052 read model: a local finite-difference Jacobian."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    hull_record_hash: str
    step_per_param: dict[str, float] = Field(default_factory=dict)
    metric_baseline: dict[str, float] = Field(default_factory=dict)
    metric_partials: dict[str, dict[str, float]] = Field(default_factory=dict)
    non_finite_partials: list[tuple[str, str, str]] = Field(default_factory=list)


# Each summary metric is read from a "snapshot" — a dict assembled from the
# evaluator outputs. The snapshot's keys define which metrics
# ``compute_sensitivity`` can answer for; metrics not in the snapshot are
# returned as ``non_finite_partials`` entries with reason
# ``unknown_metric``.
_MetricExtractor = Callable[[Hydrostatics, StabilityResult | None], float | None]


def _hydrostatic_metric(name: str) -> _MetricExtractor:
    def extract(hydro: Hydrostatics, _stability: StabilityResult | None) -> float | None:
        return getattr(hydro, name, None)

    return extract


def _stability_metric(name: str) -> _MetricExtractor:
    def extract(_hydro: Hydrostatics, stability: StabilityResult | None) -> float | None:
        if stability is None:
            return None
        return getattr(stability, name, None)

    return extract


# Metrics this service can answer for. Adding to this map is the integration
# point for new evaluator metrics: extend with a callable that pulls the
# value out of the per-hull evaluator pair.
_METRIC_EXTRACTORS: dict[str, _MetricExtractor] = {
    "GM0_m": _hydrostatic_metric("GM0_m"),
    "displaced_mass_kg": _hydrostatic_metric("displaced_mass_kg"),
    "displaced_volume_m3": _hydrostatic_metric("displaced_volume_m3"),
    "wetted_surface_m2": _hydrostatic_metric("wetted_surface_m2"),
    "waterplane_area_m2": _hydrostatic_metric("waterplane_area_m2"),
    "Cp_actual": _hydrostatic_metric("Cp_actual"),
    "Cm_actual": _hydrostatic_metric("Cm_actual"),
    "LCB_frac": _hydrostatic_metric("LCB_frac"),
    "displacement_error_kg": _stability_metric("displacement_error_kg"),
    "initial_GM0_m": _stability_metric("initial_GM0_m"),
}


# Metrics that come from the stability evaluator; the snapshot only runs the
# stability call when one of these is requested so the resistance-only case
# stays as cheap as a single hydrostatics evaluation.
_STABILITY_METRICS: frozenset[str] = frozenset({"displacement_error_kg", "initial_GM0_m"})


def _snapshot(
    hull: Hull,
    *,
    metrics: list[str],
) -> dict[str, float | None]:
    """Run the evaluators once and pull out the requested metric values."""

    hydro = evaluate_hydrostatics(hull)
    stability: StabilityResult | None = None
    if any(metric in _STABILITY_METRICS for metric in metrics):
        stability = evaluate_initial_stability(hull, LoadCase())

    out: dict[str, float | None] = {}
    for metric in metrics:
        extractor = _METRIC_EXTRACTORS.get(metric)
        if extractor is None:
            out[metric] = None
            continue
        value = extractor(hydro, stability)
        if value is None:
            out[metric] = None
            continue
        as_float = float(value)
        out[metric] = as_float if math.isfinite(as_float) else None
    return out


def _auto_step_for(parameter: str, baseline_value: float) -> float:
    """Return the per-parameter auto step (RFC 0052 default).

    ``1e-4 * baseline_value``, clamped to ``[1e-9, 1e-2]``. Falls back to the
    minimum clamp when the baseline is exactly zero so the central-difference
    perturbation still exists.
    """

    candidate = AUTO_STEP_FRACTION * abs(float(baseline_value))
    if candidate < AUTO_STEP_MIN:
        candidate = AUTO_STEP_MIN
    if candidate > AUTO_STEP_MAX:
        candidate = AUTO_STEP_MAX
    return candidate


def _perturb(hull: Hull, parameter: str, value: float) -> Hull:
    """Return a copy of ``hull`` with ``parameter`` overridden to ``value``."""

    return hull.model_copy(update={parameter: value})


def compute_sensitivity(
    hull: Hull,
    *,
    metrics: list[str],
    params: list[str],
    step: float | None = None,
) -> SensitivityResult:
    """Central-difference partials of ``metrics`` w.r.t. ``params``.

    For each (metric, param) pair the service evaluates the hull at
    ``param ± step`` and reports ``(plus - minus) / (2 * step)``. The
    per-parameter step is either ``step`` (when provided) or the auto-step
    described on :data:`AUTO_STEP_FRACTION` / :data:`AUTO_STEP_MIN` /
    :data:`AUTO_STEP_MAX`.

    Pairs that cannot be evaluated (unknown metric, unknown parameter,
    non-finite evaluator output, non-positive perturbed value rejected by
    the Hull validators) are reported in ``non_finite_partials`` as
    ``(metric, param, reason)`` tuples and omitted from ``metric_partials``.
    """

    if not metrics:
        raise ValueError("compute_sensitivity requires at least one metric")
    if not params:
        raise ValueError("compute_sensitivity requires at least one parameter")
    if step is not None and (not math.isfinite(step) or step <= 0):
        raise ValueError("compute_sensitivity step must be a positive finite number")

    hull_fields = type(hull).model_fields
    baseline_snapshot = _snapshot(hull, metrics=metrics)

    non_finite: list[tuple[str, str, str]] = []
    step_per_param: dict[str, float] = {}
    metric_baseline: dict[str, float] = {}
    metric_partials: dict[str, dict[str, float]] = {metric: {} for metric in metrics}

    for metric, value in baseline_snapshot.items():
        if value is None:
            for parameter in params:
                non_finite.append((metric, parameter, "metric_unavailable_at_baseline"))
            continue
        metric_baseline[metric] = float(value)

    # Resolve per-parameter steps once so the result records what was used,
    # even when a perturbed evaluation fails for a single metric.
    valid_params: list[str] = []
    for parameter in params:
        if parameter not in hull_fields:
            for metric in metrics:
                non_finite.append((metric, parameter, "unknown_parameter"))
            continue
        baseline_value = getattr(hull, parameter, None)
        if baseline_value is None or not isinstance(baseline_value, (int, float)):
            for metric in metrics:
                non_finite.append((metric, parameter, "non_numeric_parameter"))
            continue
        step_per_param[parameter] = (
            float(step) if step is not None else _auto_step_for(parameter, float(baseline_value))
        )
        valid_params.append(parameter)

    for parameter in valid_params:
        baseline_value = float(getattr(hull, parameter))
        step_value = step_per_param[parameter]
        try:
            plus_hull = _perturb(hull, parameter, baseline_value + step_value)
            minus_hull = _perturb(hull, parameter, baseline_value - step_value)
        except (ValueError, TypeError) as exc:
            for metric in metrics:
                non_finite.append((metric, parameter, f"perturbation_rejected:{exc}"))
            continue

        try:
            plus_snapshot = _snapshot(plus_hull, metrics=metrics)
            minus_snapshot = _snapshot(minus_hull, metrics=metrics)
        except (ValueError, ArithmeticError) as exc:
            for metric in metrics:
                non_finite.append((metric, parameter, f"evaluation_failed:{exc}"))
            continue

        for metric in metrics:
            if metric not in metric_baseline:
                # Already recorded the baseline failure for every parameter.
                continue
            plus_value = plus_snapshot.get(metric)
            minus_value = minus_snapshot.get(metric)
            if plus_value is None or minus_value is None:
                non_finite.append((metric, parameter, "perturbed_metric_unavailable"))
                continue
            partial = (plus_value - minus_value) / (2.0 * step_value)
            if not math.isfinite(partial):
                non_finite.append((metric, parameter, "non_finite_partial"))
                continue
            metric_partials[metric][parameter] = float(partial)

    # Drop metric rows whose baseline failed so the read model stays tight.
    metric_partials = {
        metric: partials
        for metric, partials in metric_partials.items()
        if metric in metric_baseline
    }

    return SensitivityResult(
        hull_record_hash=hull.hash(),
        step_per_param=step_per_param,
        metric_baseline=metric_baseline,
        metric_partials=metric_partials,
        non_finite_partials=non_finite,
    )


__all__ = [
    "AUTO_STEP_FRACTION",
    "AUTO_STEP_MAX",
    "AUTO_STEP_MIN",
    "SensitivityRequest",
    "SensitivityResult",
    "compute_sensitivity",
]
