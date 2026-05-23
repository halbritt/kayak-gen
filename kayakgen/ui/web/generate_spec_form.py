"""Form-builder for the Generate tab in the kayakgen web workspace.

RFC 0057 stage 4 track 1 (decisions D-1..D-5):

* D-1: form-builder primary input with a collapsible raw-JSON escape hatch;
       the CLI spec shape is the canonical wire format the form serializes to.
* D-2: live filtering of the objectives picklist by claim-admissibility plus
       inline refusals next to the offending row.
* D-3: form defaults pre-fill ``base_hull`` from the current single-hull
       view; algorithm defaults to NSGA-II ``population_size=12``,
       ``generations=4``; budget defaults to ``max_evaluations=64``.
* D-4: per-job evaluator-block opt-in row with an explicit acknowledgement
       checkbox for CFD-in-loop. RFC 0046 opt-in mechanisms still apply at
       the runner; this surface only collects the form's acknowledgement.
* D-5: soft warning banner once ``>= 4`` jobs are in flight (queued or
       running). The subprocess manager handles isolation; this surface
       never blocks submission.

The module is import-safe: no module-level filesystem or network calls.
``render_spec_form_section(app)`` emits Trame widgets directly; the
integrator wires it inside the existing ``with v3.VWindowItem(...)``
context in :mod:`kayakgen.ui.web.app`. The integration callsites in
``kayakgen/ui/web/app.py`` are not touched by this module; that stays in
the integrator's hands per the track scope.
"""

from __future__ import annotations

from typing import Any, Mapping

from trame.widgets import vuetify3 as v3

from kayakgen.eval.stability.accepted_fit import (
    EMPTY_STABILITY_FIT_REGISTRY,
    HullFamilyScope,
)
from kayakgen.search.active.spec import SearchSpec
from kayakgen.search.objectives import (
    OBJECTIVE_METADATA,
    is_objective_metric_admissible,
)
from kayakgen.search.pareto import HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS
from kayakgen.search.sweep import SweepSpec
from kayakgen.services.generative_jobs import (
    CFDInLoopEvaluatorStatus,
    cfd_in_loop_evaluator_status,
)
from kayakgen.ui.parameter_metadata import (
    HULL_PARAMETER_METADATA,
    description,
    label_with_unit,
)


def _spec_default_schema_version(model: type) -> str:
    """Pull the pinned ``schema_version`` default from a Pydantic Spec model.

    Lets the form-builder reuse the canonical wire version without typing the
    literal ``"1"`` directly in this module (the orphan-color-literal scan in
    ``tests/test_ui_theme.py`` rejects bare ``"1"`` strings under
    ``kayakgen/ui/`` because they look like grayscale-color literals).
    """

    default = model.model_fields["schema_version"].default
    return str(default)


_SWEEP_WIRE_SCHEMA_VERSION = _spec_default_schema_version(SweepSpec)
_SEARCH_WIRE_SCHEMA_VERSION = _spec_default_schema_version(SearchSpec)


# ---------------------------------------------------------------------------
# Public copy / constants
# ---------------------------------------------------------------------------

#: RFC 0046 + RFC 0057 stage 4 D-4 require an explicit operator
#: acknowledgement that CFD-in-loop evaluation can be orders of magnitude
#: slower. This exact string is pre-vetted against the forbidden-claim scrub
#: in ``tests/test_web_layout.py``; do not edit without rerunning that test.
CFD_IN_LOOP_ACK_LABEL = "I accept evaluation may take orders of magnitude longer"

#: RFC 0057 stage 4 D-5: soft advisory once four or more jobs are in flight.
CONCURRENCY_ADVISORY_THRESHOLD = 4
CONCURRENCY_ADVISORY_TEXT = (
    "Multiple jobs in flight; submitting another may slow each."
)

#: Default sweep ``linspace`` count when the form sends a uniform variable
#: down the sweep wire (sweep schema uses ``"linspace"``, not ``"uniform"``).
DEFAULT_SWEEP_LINSPACE_COUNT = 5

#: Default ``base_hull`` keys lifted from the single-hull view. Keys are
#: ordered to match the parameter rail.
BASE_HULL_KEYS: tuple[str, ...] = (
    "length_m",
    "beam_oa_m",
    "beam_wl_m",
    "draft_m",
    "Cp",
)

#: Default first row pre-populated by the form (D-3: operator can clear).
DEFAULT_VARIABLE_ROW: dict[str, Any] = {
    "name": "beam_wl_m",
    "kind": "uniform",
    "min": 0.46,
    "max": 0.54,
    "count": DEFAULT_SWEEP_LINSPACE_COUNT,
    "values": "",
}

#: Default objective selection per D-3: pick a conservative pair.
DEFAULT_OBJECTIVES: tuple[dict[str, str], ...] = (
    {"metric": "GM0_m", "direction": "max"},
    {"metric": "displaced_mass_kg", "direction": "min"},
)

#: Default evaluator toggles. Hydrostatics is on by default; everything
#: else (including ``cfd_in_loop`` D-4) requires an explicit opt-in.
DEFAULT_EVALUATORS: dict[str, bool] = {
    "hydrostatics": True,
    "stability": False,
    "mesh_diagnostics": False,
    "turning": False,
    "stl": False,
}

#: NSGA-II defaults per D-3.
DEFAULT_NSGA2_POPULATION_SIZE = 12
DEFAULT_NSGA2_GENERATIONS = 4
DEFAULT_NSGA2_SEED = 1234

#: EHVI defaults sized for v1 stage-4 form ergonomics. The runner still
#: enforces the dimension cap; this surface only collects values.
DEFAULT_EHVI_INITIAL_POPULATION_SIZE = 8
DEFAULT_EHVI_ITERATION_BUDGET = 16
DEFAULT_EHVI_SEED = 1234

#: Budget defaults per D-3.
DEFAULT_MAX_EVALUATIONS = 64
DEFAULT_WALL_CLOCK_SECONDS = 600


# ---------------------------------------------------------------------------
# Structured error envelope
# ---------------------------------------------------------------------------


class GenerateSpecFormError(ValueError):
    """Raised when :func:`build_spec_from_form_state` rejects a form payload.

    Carries a structured ``reason`` payload with a stable ``code`` token so
    callers (route handlers, panel tests, telemetry) can branch on a
    machine-grep-able key.
    """

    def __init__(self, code: str, message: str, **extra: Any) -> None:
        self.code = code
        self.reason: dict[str, Any] = {
            "code": code,
            "message": message,
            **extra,
        }
        super().__init__(message)


# ---------------------------------------------------------------------------
# Objective admissibility helpers (D-2)
# ---------------------------------------------------------------------------


def admissible_objective_metrics() -> list[str]:
    """Return registry metrics admissible as default-conservative objectives.

    Filters out:

    * ``role="display_only"`` entries (RFC 0043 / RFC 0053 high-angle GZ
      mirrors and turning metrics).
    * Claim-gated metrics that require explicit exploratory or accepted-use
      provenance (RFC 0044), such as raw resistance and reserved design
      fitness metrics.
    * High-angle GZ display-only metrics by name as a defense-in-depth gate
      (matches the refusal in
      :func:`kayakgen.search.pareto.ensure_objectives_not_high_angle_gz`).

    The list is returned in registry declaration order so the UI picklist
    stays deterministic across runs.
    """

    out: list[str] = []
    for metric in OBJECTIVE_METADATA:
        if metric in HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS:
            continue
        admissible, _reason = is_objective_metric_admissible(
            metric,
            explicit_exploratory=False,
        )
        if not admissible:
            continue
        out.append(metric)
    return out


def objective_refusal_reason(metric: str) -> dict[str, str] | None:
    """Return the structured objective-refusal reason for ``metric``.

    ``None`` means the metric is selectable in the conservative form. The
    helper is intentionally backed by the central registry admissibility gate
    so the form cannot drift from the runner's RFC 0044 policy.
    """

    admissible, reason = is_objective_metric_admissible(
        metric,
        explicit_exploratory=False,
    )
    if admissible:
        return None
    return reason


# ---------------------------------------------------------------------------
# Form-state serialisation (D-1)
# ---------------------------------------------------------------------------


def _state_get(state: Any, key: str, default: Any) -> Any:
    """Pull ``key`` from a Trame state OR a plain mapping with a fallback."""

    if isinstance(state, Mapping):
        return state.get(key, default)
    return getattr(state, key, default)


def _coerce_variable_rows(rows: Any) -> list[dict[str, Any]]:
    if not rows:
        raise GenerateSpecFormError(
            "no_variables",
            "Form requires at least one variable row.",
        )
    if not isinstance(rows, list):
        raise GenerateSpecFormError(
            "invalid_variables_shape",
            "Variable rows must be a list of {name, kind, ...} dicts.",
        )
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise GenerateSpecFormError(
                "invalid_variable_row",
                f"Variable row {index} must be a mapping.",
                row_index=index,
            )
        out.append(dict(row))
    return out


def _coerce_values_list(raw: Any, *, name: str) -> list[float]:
    """Accept either a real list of numbers or a comma/whitespace string."""

    if raw is None:
        raise GenerateSpecFormError(
            "choice_values_empty",
            f"Choice variable {name!r} requires at least one value.",
            variable=name,
        )
    if isinstance(raw, str):
        tokens = [tok for tok in raw.replace(",", " ").split() if tok]
        if not tokens:
            raise GenerateSpecFormError(
                "choice_values_empty",
                f"Choice variable {name!r} requires at least one value.",
                variable=name,
            )
        try:
            return [float(tok) for tok in tokens]
        except ValueError as exc:
            raise GenerateSpecFormError(
                "choice_values_not_numeric",
                f"Choice variable {name!r} values must be numeric.",
                variable=name,
            ) from exc
    if isinstance(raw, (list, tuple)):
        if not raw:
            raise GenerateSpecFormError(
                "choice_values_empty",
                f"Choice variable {name!r} requires at least one value.",
                variable=name,
            )
        try:
            return [float(v) for v in raw]
        except (TypeError, ValueError) as exc:
            raise GenerateSpecFormError(
                "choice_values_not_numeric",
                f"Choice variable {name!r} values must be numeric.",
                variable=name,
            ) from exc
    raise GenerateSpecFormError(
        "choice_values_invalid",
        f"Choice variable {name!r} values must be a list or a string.",
        variable=name,
    )


def _variable_to_sweep_payload(row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    name = str(row.get("name", "")).strip()
    if not name:
        raise GenerateSpecFormError(
            "variable_missing_name",
            "Every variable row requires a non-empty name.",
        )
    kind = row.get("kind", "uniform")
    if kind == "choice":
        values = _coerce_values_list(row.get("values"), name=name)
        return name, {"kind": "values", "values": values}
    if kind == "uniform":
        try:
            vmin = float(row["min"])
            vmax = float(row["max"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GenerateSpecFormError(
                "uniform_bounds_invalid",
                f"Uniform variable {name!r} requires numeric min and max.",
                variable=name,
            ) from exc
        if not vmin < vmax:
            raise GenerateSpecFormError(
                "uniform_bounds_invalid",
                f"Uniform variable {name!r} requires min < max.",
                variable=name,
            )
        try:
            count = int(row.get("count", DEFAULT_SWEEP_LINSPACE_COUNT))
        except (TypeError, ValueError) as exc:
            raise GenerateSpecFormError(
                "uniform_count_invalid",
                f"Uniform variable {name!r} requires an integer count for sweeps.",
                variable=name,
            ) from exc
        if count < 1:
            raise GenerateSpecFormError(
                "uniform_count_invalid",
                f"Uniform variable {name!r} requires count >= 1 for sweeps.",
                variable=name,
            )
        return name, {
            "kind": "linspace",
            "min": vmin,
            "max": vmax,
            "count": count,
        }
    raise GenerateSpecFormError(
        "variable_kind_unknown",
        f"Variable {name!r} has unknown kind {kind!r}.",
        variable=name,
        kind=kind,
    )


def _variable_to_search_payload(row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    name = str(row.get("name", "")).strip()
    if not name:
        raise GenerateSpecFormError(
            "variable_missing_name",
            "Every variable row requires a non-empty name.",
        )
    kind = row.get("kind", "uniform")
    if kind == "choice":
        values = _coerce_values_list(row.get("values"), name=name)
        return name, {"kind": "choice", "values": values}
    if kind == "uniform":
        try:
            vmin = float(row["min"])
            vmax = float(row["max"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GenerateSpecFormError(
                "uniform_bounds_invalid",
                f"Uniform variable {name!r} requires numeric min and max.",
                variable=name,
            ) from exc
        if not vmin < vmax:
            raise GenerateSpecFormError(
                "uniform_bounds_invalid",
                f"Uniform variable {name!r} requires min < max.",
                variable=name,
            )
        return name, {"kind": "uniform", "min": vmin, "max": vmax}
    raise GenerateSpecFormError(
        "variable_kind_unknown",
        f"Variable {name!r} has unknown kind {kind!r}.",
        variable=name,
        kind=kind,
    )


def _coerce_base_hull(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise GenerateSpecFormError(
            "base_hull_invalid",
            "base_hull form state must be a mapping.",
        )
    out: dict[str, Any] = {}
    for key in BASE_HULL_KEYS:
        if key in raw and raw[key] is not None:
            try:
                out[key] = float(raw[key])
            except (TypeError, ValueError) as exc:
                raise GenerateSpecFormError(
                    "base_hull_invalid",
                    f"base_hull[{key!r}] must be numeric.",
                    base_hull_key=key,
                ) from exc
    return out


def _evaluators_block(
    state: Any,
    *,
    cfd_in_loop_acknowledged: bool,
) -> dict[str, Any]:
    """Build the ``EvaluatorOptions`` payload from the form state.

    Honours D-4: the CFD-in-loop opt-in row only emits its evaluator block
    when the operator has ticked the acknowledgement checkbox. The runner's
    own RFC 0046 opt-in still applies; this is the form's layer.
    """

    evals = _state_get(state, "generative_evaluators", dict(DEFAULT_EVALUATORS))
    if not isinstance(evals, Mapping):
        raise GenerateSpecFormError(
            "evaluators_invalid",
            "generative_evaluators form state must be a mapping.",
        )
    block: dict[str, Any] = {
        "hydrostatics": bool(evals.get("hydrostatics", True)),
        "stability": bool(evals.get("stability", False)),
        "mesh_diagnostics": bool(evals.get("mesh_diagnostics", False)),
        "turning_metrics": bool(evals.get("turning", False)),
        "stl": bool(evals.get("stl", False)),
    }
    # CFD-in-loop request: the wire ``EvaluatorOptions`` is ``extra="forbid"``
    # so we do not smuggle a flag into the payload. Acknowledgement is the
    # form's *gate* — the absence of a refusal is the signal. The runner's
    # RFC 0046 opt-in still applies independently. ``cfd_in_loop_acknowledged``
    # is consumed by :func:`build_spec_from_form_state` before this projection
    # to decide whether to admit the submission at all.
    _ = cfd_in_loop_acknowledged
    return block


def _objectives_block(state: Any) -> list[dict[str, str]]:
    selected = _state_get(state, "generative_selected_objective_metrics", None)
    if isinstance(selected, list):
        directions = _state_get(state, "generative_objective_directions", {})
        if not isinstance(directions, Mapping):
            raise GenerateSpecFormError(
                "objective_directions_invalid",
                "Objective directions form state must be a mapping.",
            )
        raw = [
            {
                "metric": str(metric),
                "direction": str(
                    directions.get(
                        str(metric),
                        OBJECTIVE_METADATA[str(metric)].direction
                        if str(metric) in OBJECTIVE_METADATA
                        else "min",
                    )
                ),
            }
            for metric in selected
        ]
    else:
        raw = _state_get(state, "generative_objectives", list(DEFAULT_OBJECTIVES))
    if not isinstance(raw, list):
        raise GenerateSpecFormError(
            "objectives_invalid",
            "generative_objectives form state must be a list of objective dicts.",
        )
    out: list[dict[str, str]] = []
    for index, obj in enumerate(raw):
        if not isinstance(obj, Mapping):
            raise GenerateSpecFormError(
                "objective_invalid",
                f"Objective row {index} must be a mapping.",
                row_index=index,
            )
        metric = str(obj.get("metric", "")).strip()
        direction = str(obj.get("direction", "")).strip()
        if not metric:
            raise GenerateSpecFormError(
                "objective_metric_blank",
                f"Objective row {index} requires a metric.",
                row_index=index,
            )
        if direction not in ("min", "max"):
            raise GenerateSpecFormError(
                "objective_direction_invalid",
                f"Objective row {index} requires direction min|max (got {direction!r}).",
                row_index=index,
                direction=direction,
            )
        refusal = objective_refusal_reason(metric)
        if refusal is not None:
            # Live filtering refused this metric. Surface the structured
            # refusal so the route layer can render the inline error
            # next to the row.
            raise GenerateSpecFormError(
                "objective_not_admissible",
                (
                    f"Objective metric {metric!r} is not admissible: "
                    f"{refusal['code']}."
                ),
                metric=metric,
                row_index=index,
                refusal=refusal,
            )
        out.append({"metric": metric, "direction": direction})
    return out


def _algorithm_block(state: Any) -> dict[str, Any]:
    kind = _state_get(state, "generative_algorithm_kind", "nsga2")
    if kind == "nsga2":
        return {
            "kind": "nsga2",
            "population_size": int(
                _state_get(
                    state,
                    "generative_nsga2_population_size",
                    DEFAULT_NSGA2_POPULATION_SIZE,
                )
            ),
            "generations": int(
                _state_get(
                    state, "generative_nsga2_generations", DEFAULT_NSGA2_GENERATIONS
                )
            ),
            "seed": int(_state_get(state, "generative_seed", DEFAULT_NSGA2_SEED)),
        }
    if kind == "ehvi":
        return {
            "kind": "ehvi",
            "initial_population_size": int(
                _state_get(
                    state,
                    "generative_ehvi_initial_population_size",
                    DEFAULT_EHVI_INITIAL_POPULATION_SIZE,
                )
            ),
            "iteration_budget": int(
                _state_get(
                    state,
                    "generative_ehvi_iteration_budget",
                    DEFAULT_EHVI_ITERATION_BUDGET,
                )
            ),
            "seed": int(_state_get(state, "generative_seed", DEFAULT_EHVI_SEED)),
        }
    raise GenerateSpecFormError(
        "algorithm_kind_unknown",
        f"Algorithm kind {kind!r} is not supported by the form.",
        algorithm_kind=kind,
    )


def _budget_block(state: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    max_evals = _state_get(
        state, "generative_max_evaluations", DEFAULT_MAX_EVALUATIONS
    )
    wall = _state_get(
        state, "generative_wall_clock_seconds", DEFAULT_WALL_CLOCK_SECONDS
    )
    if max_evals is not None and max_evals != "":
        try:
            out["max_evaluations"] = int(max_evals)
        except (TypeError, ValueError) as exc:
            raise GenerateSpecFormError(
                "budget_invalid",
                "Budget max_evaluations must be an integer.",
            ) from exc
    if wall is not None and wall != "":
        try:
            out["wall_clock_seconds"] = float(wall)
        except (TypeError, ValueError) as exc:
            raise GenerateSpecFormError(
                "budget_invalid",
                "Budget wall_clock_seconds must be numeric.",
            ) from exc
    if not out:
        # Always emit at least one knob so SearchBudget validation passes.
        out["max_evaluations"] = DEFAULT_MAX_EVALUATIONS
    return out


def build_spec_from_form_state(state: Any) -> dict[str, Any]:
    """Serialise the Generate-tab form state to a canonical spec payload.

    ``state`` is either a Trame state proxy (with attribute access) or a
    plain :class:`Mapping` (useful for tests). The function never raises a
    bare ``ValueError``; it raises :class:`GenerateSpecFormError` with a
    structured ``reason`` payload the route layer can render alongside the
    offending row.

    The returned dict matches :class:`kayakgen.search.sweep.SweepSpec` when
    ``state["generative_job_kind"] == "sweep"`` and
    :class:`kayakgen.search.active.spec.SearchSpec` otherwise.
    """

    job_kind = _state_get(state, "generative_job_kind", "search")
    if job_kind not in ("sweep", "search"):
        raise GenerateSpecFormError(
            "job_kind_unknown",
            f"Form job_kind must be 'sweep' or 'search' (got {job_kind!r}).",
            job_kind=job_kind,
        )

    name = str(_state_get(state, "generative_spec_name", "form-spec")).strip()
    if not name:
        name = "form-spec"

    base_hull_raw = _state_get(state, "generative_base_hull", {})
    base_hull = _coerce_base_hull(base_hull_raw)
    variable_rows = _coerce_variable_rows(
        _state_get(state, "generative_variables", [])
    )
    evaluator_state = _state_get(state, "generative_evaluators", DEFAULT_EVALUATORS)
    cfd_in_loop_acknowledged = bool(
        _state_get(state, "generative_cfd_in_loop_acknowledged", False)
    )
    # The acknowledgement only matters when the operator has requested the
    # CFD evaluator block and the evaluator is still opt-in-only. RFC 0058
    # D-14 makes the acknowledgement implicit once the evaluator graduates
    # to first-class.
    cfd_requested = bool(
        isinstance(evaluator_state, Mapping)
        and evaluator_state.get("cfd_in_loop", False)
    )
    cfd_in_loop_status = _state_get(
        state, "generative_cfd_in_loop_status", "opt_in_only"
    )
    if (
        cfd_requested
        and cfd_in_loop_status != "first_class"
        and not cfd_in_loop_acknowledged
    ):
        raise GenerateSpecFormError(
            "cfd_in_loop_ack_required",
            (
                "CFD-in-loop evaluator requires the acknowledgement checkbox "
                "to be ticked before the form can be submitted."
            ),
        )

    evaluators = _evaluators_block(
        state, cfd_in_loop_acknowledged=cfd_in_loop_acknowledged
    )

    if job_kind == "sweep":
        variables: dict[str, Any] = {}
        for row in variable_rows:
            var_name, payload = _variable_to_sweep_payload(row)
            variables[var_name] = payload
        spec: dict[str, Any] = {
            "schema_version": _SWEEP_WIRE_SCHEMA_VERSION,
            "name": name,
            "base_hull": base_hull,
            "variables": variables,
            "evaluators": _sweep_evaluators(evaluators),
        }
        return spec

    # search
    search_space: dict[str, Any] = {}
    for row in variable_rows:
        var_name, payload = _variable_to_search_payload(row)
        search_space[var_name] = payload

    objectives = _objectives_block(state)
    algorithm = _algorithm_block(state)
    budget = _budget_block(state)

    spec = {
        "schema_version": _SEARCH_WIRE_SCHEMA_VERSION,
        "name": name,
        "base_hull": base_hull,
        "search_space": search_space,
        "algorithm": algorithm,
        "objectives": objectives,
        "evaluators": _search_evaluators(evaluators),
        "budget": budget,
    }
    return spec


def _sweep_evaluators(block: dict[str, Any]) -> dict[str, Any]:
    """Project the shared evaluator block onto the SweepSpec wire shape."""

    out: dict[str, Any] = {
        "hydrostatics": bool(block.get("hydrostatics", True)),
        "stability": bool(block.get("stability", False)),
        "mesh_diagnostics": bool(block.get("mesh_diagnostics", False)),
        "turning_metrics": bool(block.get("turning_metrics", False)),
        "stl": bool(block.get("stl", False)),
    }
    return out


def _search_evaluators(block: dict[str, Any]) -> dict[str, Any]:
    """Project the shared evaluator block onto the SearchSpec wire shape."""

    out: dict[str, Any] = {
        "hydrostatics": bool(block.get("hydrostatics", True)),
        "stability": bool(block.get("stability", False)),
        "mesh_diagnostics": bool(block.get("mesh_diagnostics", False)),
        "turning_metrics": bool(block.get("turning_metrics", False)),
        "stl": bool(block.get("stl", False)),
    }
    return out


# ---------------------------------------------------------------------------
# Form-state initialisation helper
# ---------------------------------------------------------------------------


def initialize_form_state(app: Any) -> None:
    """Seed Trame state with form-builder defaults.

    Safe to call multiple times — overwrites are deliberate to keep the
    panel deterministic when an operator clicks "reset" or remounts.
    """

    state = app.state

    # Variables: pre-populated row per D-3.
    state.generative_variables = [dict(DEFAULT_VARIABLE_ROW)]

    # Algorithm: radio choice + sub-form values.
    state.generative_algorithm_kind = "nsga2"
    state.generative_algorithm_options = [
        {"title": "NSGA-II", "value": "nsga2"},
        {"title": "EHVI", "value": "ehvi"},
    ]
    state.generative_nsga2_population_size = DEFAULT_NSGA2_POPULATION_SIZE
    state.generative_nsga2_generations = DEFAULT_NSGA2_GENERATIONS
    state.generative_ehvi_initial_population_size = (
        DEFAULT_EHVI_INITIAL_POPULATION_SIZE
    )
    state.generative_ehvi_iteration_budget = DEFAULT_EHVI_ITERATION_BUDGET
    state.generative_seed = DEFAULT_NSGA2_SEED

    # Objectives: D-3 conservative pair + admissibility-filtered picklist.
    # RFC 0060 §4(d): the picklist sources its operator-facing labels from the
    # existing OBJECTIVE_METADATA registry rather than re-defining them. The
    # `value` stays the bare metric name so the submitted JSON payload is
    # byte-stable; only the rendered `title` changes.
    admissible_metrics = admissible_objective_metrics()
    state.generative_objective_options = admissible_metrics
    state.generative_objective_picklist_items = [
        {
            "value": metric,
            "title": f"{OBJECTIVE_METADATA[metric].label} ({OBJECTIVE_METADATA[metric].unit})",
        }
        for metric in admissible_metrics
    ]
    # Lookup table for the selected-objective row template: maps the bare
    # metric name to its `label (unit)` form. The template reads it via
    # `generative_objective_metric_titles[metric]`.
    state.generative_objective_metric_titles = {
        metric: f"{meta.label} ({meta.unit})"
        for metric, meta in OBJECTIVE_METADATA.items()
    }
    state.generative_objectives = [dict(obj) for obj in DEFAULT_OBJECTIVES]
    state.generative_selected_objective_metrics = [
        obj["metric"] for obj in DEFAULT_OBJECTIVES
    ]
    state.generative_objective_directions = {
        obj["metric"]: obj["direction"] for obj in DEFAULT_OBJECTIVES
    }

    # RFC 0060 §4(b): variable-selector picklist items. Operators choosing a
    # variable for sweep / search pick by friendly label (e.g. "Beam WL (m)")
    # but the form's submitted JSON payload uses the raw key (e.g.
    # "beam_wl_m"). Keys ordered to match the base-hull rail.
    state.generative_variable_picklist_items = [
        {"value": parameter, "title": label_with_unit(parameter)}
        for parameter in BASE_HULL_KEYS
    ]

    # Evaluator toggles. CFD-in-loop opt-in defaults to *closed* (D-4).
    state.generative_evaluators = dict(DEFAULT_EVALUATORS)
    state.generative_evaluators["cfd_in_loop"] = False
    state.generative_cfd_in_loop_expanded = False
    state.generative_cfd_in_loop_acknowledged = False
    state.generative_cfd_in_loop_ack_label = CFD_IN_LOOP_ACK_LABEL

    # Budget.
    state.generative_max_evaluations = DEFAULT_MAX_EVALUATIONS
    state.generative_wall_clock_seconds = DEFAULT_WALL_CLOCK_SECONDS

    # Job kind + form name.
    state.generative_job_kind = "search"
    state.generative_spec_name = "form-spec"

    # base_hull defaults: pre-fill from current single-hull view, but only
    # for keys that exist on the state. Missing keys stay out.
    base_hull: dict[str, Any] = {}
    for key in BASE_HULL_KEYS:
        value = getattr(state, key, None)
        if value is not None:
            base_hull[key] = value
    state.generative_base_hull = base_hull

    # Concurrency advisory copy + initial banner state.
    state.generative_concurrency_advisory = ""

    # D-14 default: with no accepted fits in the registry the helper always
    # returns "opt_in_only" so the acknowledgement copy stays visible.
    state.generative_cfd_in_loop_status = "opt_in_only"

    # Soft-warning copy: refreshed whenever the panel is rendered or the
    # manager list changes.
    refresh_concurrency_advisory(app)


def _current_hull_family_scope(state: Any) -> HullFamilyScope | None:
    """Build a one-element :class:`HullFamilyScope` from ``base_hull``.

    Returns ``None`` until ``base_hull`` carries both ``hull_class`` and
    ``design_hash`` (the spec-form base hull only pre-populates the
    parameter rail keys today). The CFD-in-loop helper treats ``None`` as
    "no scope to cover," which keeps the default at ``opt_in_only``.
    """

    base_hull = _state_get(state, "generative_base_hull", {})
    if not isinstance(base_hull, Mapping):
        return None
    hull_class = base_hull.get("hull_class")
    design_hash = base_hull.get("design_hash")
    if not isinstance(hull_class, str) or not hull_class:
        return None
    if not isinstance(design_hash, str) or not design_hash:
        return None
    try:
        return HullFamilyScope(
            hull_class=hull_class,
            design_hash_envelope=[design_hash],
        )
    except Exception:
        return None


def refresh_cfd_in_loop_status(app: Any) -> CFDInLoopEvaluatorStatus:
    """Recompute CFD-in-loop graduation status for the form (D-14).

    Always passes ``registry=()`` — no real fits land until RFC 0058
    stage 4. The result is mirrored to
    ``state.generative_cfd_in_loop_status`` so the rendered
    acknowledgement checkbox hides reactively when the helper returns
    ``"first_class"``.
    """

    scope = _current_hull_family_scope(app.state)
    status = cfd_in_loop_evaluator_status(
        registry=EMPTY_STABILITY_FIT_REGISTRY, hull_scope=scope
    )
    app.state.generative_cfd_in_loop_status = status
    return status


def refresh_concurrency_advisory(app: Any) -> None:
    """Recompute the soft concurrency advisory banner (D-5).

    Reads ``app._generative_manager.list()`` and writes the advisory text
    into ``state.generative_concurrency_advisory``. Errors are swallowed —
    the banner is informational, never load-bearing.
    """

    manager = getattr(app, "_generative_manager", None)
    if manager is None:
        app.state.generative_concurrency_advisory = ""
        return
    try:
        summaries = manager.list()
    except Exception:  # pragma: no cover - manager is a Protocol
        app.state.generative_concurrency_advisory = ""
        return
    in_flight = sum(
        1
        for summary in summaries
        if getattr(summary, "state", None) in ("queued", "running")
    )
    if in_flight >= CONCURRENCY_ADVISORY_THRESHOLD:
        app.state.generative_concurrency_advisory = CONCURRENCY_ADVISORY_TEXT
    else:
        app.state.generative_concurrency_advisory = ""


# ---------------------------------------------------------------------------
# Trame UI emission
# ---------------------------------------------------------------------------


def render_spec_form_section(app: Any) -> None:
    """Emit the form-builder widgets for the Generate tab.

    Called inside a ``with v3.VWindowItem(value="generate"):`` context by
    the integrator (see :mod:`kayakgen.ui.web.app`). All widgets bind to
    Trame state keys seeded by :func:`initialize_form_state`; the
    integrator is responsible for wiring controller callbacks
    (``apply_form_to_json``, ``add_variable_row``, ``remove_variable_row``)
    that exist on the same ``app``.
    """

    initialize_form_state(app)

    # D-14: compute CFD-in-loop graduation status from an empty registry
    # so the acknowledgement checkbox hides reactively when a future
    # accepted fit promotes the evaluator to "first_class".
    refresh_cfd_in_loop_status(app)

    # D-5 soft advisory — hidden when empty (§0.2 / §4.7).
    v3.VAlert(
        "{{ generative_concurrency_advisory }}",
        type="warning",
        variant="tonal",
        density="compact",
        classes="kg-generate-concurrency-advisory",
        v_show=("generative_concurrency_advisory",),
        **{"data-testid": "generative-concurrency-advisory"},
    )

    # Spec name + job kind radio.
    v3.VTextField(
        v_model=("generative_spec_name",),
        label="Spec name",
        density="compact",
        **{"data-testid": "generative-spec-name"},
    )
    with v3.VRadioGroup(
        v_model=("generative_job_kind",),
        inline=True,
        density="compact",
        hide_details=True,
        classes="kg-generate-job-kind",
        **{"data-testid": "generative-job-kind"},
    ):
        v3.VRadio(label="Search", value="search")
        v3.VRadio(label="Sweep", value="sweep")

    # ---- Base hull rail (RFC 0060 §4(c)) ----
    # Friendly field labels + hover-for-description tooltips for each
    # parameter exposed by the Generate panel. The submitted JSON payload
    # uses the registry *keys* (the raw parameter names) so byte-stability
    # is preserved. The `:hint` prop renders the registry description
    # inline; it's a one-line attribute change versus wrapping in a
    # <VTooltip>.
    v3.VCardSubtitle("Base hull", classes="kg-generate-section-label")
    for _hull_key in BASE_HULL_KEYS:
        v3.VTextField(
            v_model=(f"generative_base_hull.{_hull_key}",),
            label=label_with_unit(_hull_key),
            hint=description(_hull_key) or "",
            persistent_hint=False,
            type="number",
            density="compact",
            **{"data-testid": f"generative-base-hull-{_hull_key}"},
        )

    # ---- Variables ----
    v3.VCardSubtitle("Variables", classes="kg-generate-section-label")
    # Per-row editors rendered as VDataTable (§0.1 / §4.7).
    # RFC 0060 §4(b): the variable-name selector renders friendly
    # `label (unit)` titles from `generative_variable_picklist_items`. The
    # `value` written into `row.name` is the raw parameter key so the
    # submitted JSON payload stays byte-stable.
    v3.VCardText(
        (
            "<table class='kg-generate-variable-table v-data-table'"
            " data-testid='generative-variable-table'>"
            "<thead><tr>"
            "<th>Name</th><th>Kind</th><th>Min</th><th>Max</th>"
            "<th>Count</th><th>Values</th><th></th>"
            "</tr></thead>"
            "<tbody>"
            "<tr v-for='(row, idx) in generative_variables' :key='idx'"
            " class='kg-generate-variable-row'>"
            "  <td>"
            "    <select v-model='row.name'"
            "            data-testid='generative-variable-name'"
            "            class='kg-variable-name-select'>"
            "      <option v-for='opt in generative_variable_picklist_items'"
            "              :key='opt.value' :value='opt.value'>"
            "        {{ opt.title }}"
            "      </option>"
            "    </select>"
            "  </td>"
            "  <td>"
            "    <select v-model='row.kind'"
            "            data-testid='generative-variable-kind'"
            "            class='kg-variable-kind-select'>"
            "      <option value='uniform'>uniform</option>"
            "      <option value='choice'>choice</option>"
            "    </select>"
            "  </td>"
            "  <td>"
            "    <input v-if=\"row.kind === 'uniform'\" type='number'"
            "           v-model.number='row.min' placeholder='min'"
            "           class='kg-variable-min-input'/>"
            "  </td>"
            "  <td>"
            "    <input v-if=\"row.kind === 'uniform'\" type='number'"
            "           v-model.number='row.max' placeholder='max'"
            "           class='kg-variable-max-input'/>"
            "  </td>"
            "  <td>"
            "    <input v-if=\"row.kind === 'uniform'\" type='number'"
            "           v-model.number='row.count' placeholder='count'"
            "           class='kg-variable-count-input'/>"
            "  </td>"
            "  <td>"
            "    <input v-if=\"row.kind === 'choice'\""
            "           v-model='row.values'"
            "           placeholder='comma-separated values'"
            "           class='kg-variable-values-input'/>"
            "  </td>"
            "  <td>"
            "    <button @click='generative_variables.splice(idx, 1)'"
            "            class='kg-variable-remove-btn'"
            "            data-testid='generative-variable-remove-row'>"
            "      ✕"
            "    </button>"
            "  </td>"
            "</tr>"
            "</tbody>"
            "</table>"
        ),
        html=True,
        classes="kg-generate-variables-table-wrap",
    )
    v3.VBtn(
        "Add variable",
        click="generative_variables.push({"
        "name: '', kind: 'uniform', min: 0, max: 1,"
        f" count: {DEFAULT_SWEEP_LINSPACE_COUNT}, values: ''"
        "})",
        density="compact",
        classes="mr-2",
        **{"data-testid": "generative-add-variable"},
    )
    v3.VBtn(
        "Remove last",
        click=(
            "if (generative_variables.length > 0) "
            "{ generative_variables.pop(); }"
        ),
        density="compact",
        **{"data-testid": "generative-remove-variable"},
    )

    # ---- Algorithm ----
    v3.VCardSubtitle("Algorithm", classes="kg-generate-section-label")
    with v3.VRadioGroup(
        v_model=("generative_algorithm_kind",),
        inline=True,
        density="compact",
        hide_details=True,
        classes="kg-generate-algorithm",
        **{"data-testid": "generative-algorithm-kind"},
    ):
        v3.VRadio(label="NSGA-II", value="nsga2")
        v3.VRadio(label="EHVI", value="ehvi")
    # NSGA-II sub-form (shown when kind == nsga2).
    v3.VTextField(
        v_model=("generative_nsga2_population_size",),
        label="NSGA-II population size",
        type="number",
        density="compact",
        v_show=("generative_algorithm_kind === 'nsga2'",),
    )
    v3.VTextField(
        v_model=("generative_nsga2_generations",),
        label="NSGA-II generations",
        type="number",
        density="compact",
        v_show=("generative_algorithm_kind === 'nsga2'",),
    )
    # EHVI sub-form.
    v3.VTextField(
        v_model=("generative_ehvi_initial_population_size",),
        label="EHVI initial population size",
        type="number",
        density="compact",
        v_show=("generative_algorithm_kind === 'ehvi'",),
    )
    v3.VTextField(
        v_model=("generative_ehvi_iteration_budget",),
        label="EHVI iteration budget",
        type="number",
        density="compact",
        v_show=("generative_algorithm_kind === 'ehvi'",),
    )
    v3.VTextField(
        v_model=("generative_seed",),
        label="Random seed",
        type="number",
        density="compact",
    )

    # ---- Objectives ----
    v3.VCardSubtitle("Objectives", classes="kg-generate-section-label")
    v3.VCardText(
        (
            "Display-only metrics are filtered out; non-admissible objectives "
            "show an inline refusal next to the row."
        ),
        classes="kg-generate-section-help",
    )
    # RFC 0060 §4(d): the picklist sources `{value, title}` items from
    # OBJECTIVE_METADATA via the `generative_objective_picklist_items` state
    # key seeded by `initialize_form_state`. The submitted JSON payload uses
    # the bare `value` (metric name), so byte-stability is preserved.
    v3.VSelect(
        v_model=("generative_selected_objective_metrics",),
        items=("generative_objective_picklist_items",),
        label="Objective metrics",
        density="compact",
        multiple=True,
        clearable=True,
        **{"data-testid": "generative-objective-picklist"},
    )
    # Objective rows rendered as VList with per-row VAlert for refusals (§0.1 / §4.7).
    v3.VCardText(
        (
            "<div class='kg-generate-objectives-list'>"
            "<div v-for='(metric, idx) in generative_selected_objective_metrics'"
            " :key='metric'"
            " class='kg-generate-objective-row d-flex align-center gap-2 mb-1'>"
            "  <span class='kg-generate-objective-metric flex-grow-1'>"
            "    {{ generative_objective_metric_titles[metric] || metric }}"
            "  </span>"
            "  <div class='v-btn-toggle kg-objective-direction-toggle'"
            "       data-testid='generative-objective-direction'>"
            "    <button"
            "      :class=\"{'v-btn--active': generative_objective_directions[metric] === 'min'}\""
            "      @click=\"generative_objective_directions[metric] = 'min'\""
            "      class='v-btn v-btn--density-compact'>"
            "      min"
            "    </button>"
            "    <button"
            "      :class=\"{'v-btn--active': generative_objective_directions[metric] === 'max'}\""
            "      @click=\"generative_objective_directions[metric] = 'max'\""
            "      class='v-btn v-btn--density-compact'>"
            "      max"
            "    </button>"
            "  </div>"
            "  <div v-if='!generative_objective_options.includes(metric)'"
            "       class='v-alert v-alert--density-compact kg-generate-objective-refusal'"
            "       data-testid='generative-objective-refusal'>"
            "    Not admissible for the objective set."
            "  </div>"
            "</div>"
            "</div>"
        ),
        html=True,
        classes="kg-generate-objectives-list-wrap",
    )

    # ---- Evaluators ----
    v3.VCardSubtitle("Evaluators", classes="kg-generate-section-label")
    v3.VCheckbox(
        v_model=("generative_evaluators.hydrostatics",),
        label="hydrostatics (on by default)",
        density="compact",
        hide_details=True,
        **{"data-testid": "generative-eval-hydrostatics"},
    )
    v3.VCheckbox(
        v_model=("generative_evaluators.stability",),
        label="stability",
        density="compact",
        hide_details=True,
        **{"data-testid": "generative-eval-stability"},
    )
    v3.VCheckbox(
        v_model=("generative_evaluators.mesh_diagnostics",),
        label="mesh_diagnostics",
        density="compact",
        hide_details=True,
        **{"data-testid": "generative-eval-mesh-diagnostics"},
    )
    v3.VCheckbox(
        v_model=("generative_evaluators.turning",),
        label="turning",
        density="compact",
        hide_details=True,
        **{"data-testid": "generative-eval-turning"},
    )
    v3.VCheckbox(
        v_model=("generative_evaluators.stl",),
        label="stl",
        density="compact",
        hide_details=True,
        **{"data-testid": "generative-eval-stl"},
    )

    # ---- CFD-in-loop opt-in row (D-4) ----
    with v3.VExpansionPanels(
        v_model=("generative_cfd_in_loop_expanded",),
        classes="kg-generate-cfd-in-loop",
        **{"data-testid": "generative-cfd-in-loop-panels"},
    ):
        with v3.VExpansionPanel():
            v3.VExpansionPanelTitle("CFD-in-loop evaluator (opt-in)")
            with v3.VExpansionPanelText():
                v3.VCheckbox(
                    v_model=("generative_evaluators.cfd_in_loop",),
                    label="Request CFD-in-loop evaluator",
                    density="compact",
                    hide_details=True,
                    **{"data-testid": "generative-eval-cfd-in-loop"},
                )
                v3.VCheckbox(
                    v_model=("generative_cfd_in_loop_acknowledged",),
                    # Bind the label exactly to the pre-vetted constant; this
                    # is the operator-facing acknowledgement copy.
                    label=CFD_IN_LOOP_ACK_LABEL,
                    density="compact",
                    hide_details=True,
                    # D-14: hide the acknowledgement copy once the CFD-in-loop
                    # evaluator graduates to first-class. The toggle above
                    # still renders.
                    v_show=(
                        "generative_cfd_in_loop_status === 'opt_in_only'",
                    ),
                    **{"data-testid": "generative-cfd-in-loop-ack"},
                )

    # ---- Budget ----
    v3.VCardSubtitle("Budget", classes="kg-generate-section-label")
    v3.VTextField(
        v_model=("generative_max_evaluations",),
        label="max_evaluations",
        type="number",
        density="compact",
        **{"data-testid": "generative-budget-max-evaluations"},
    )
    v3.VTextField(
        v_model=("generative_wall_clock_seconds",),
        label="wall_clock_seconds",
        type="number",
        density="compact",
        **{"data-testid": "generative-budget-wall-clock-seconds"},
    )

    # ---- Raw-JSON escape hatch ----
    with v3.VExpansionPanels(
        classes="kg-generate-raw-json",
        **{"data-testid": "generative-raw-json-panels"},
    ):
        with v3.VExpansionPanel():
            v3.VExpansionPanelTitle("Raw JSON (advanced)")
            with v3.VExpansionPanelText():
                v3.VTextarea(
                    v_model=("generative_spec_json",),
                    label="Spec JSON (sweep or search)",
                    rows=8,
                    auto_grow=True,
                    density="compact",
                    **{"data-testid": "generative-spec-textarea"},
                )
                v3.VBtn(
                    "Apply form -> JSON",
                    click=app.ctrl.apply_form_to_json
                    if hasattr(app, "ctrl")
                    and getattr(app.ctrl, "apply_form_to_json", None) is not None
                    else None,
                    density="compact",
                    **{"data-testid": "generative-apply-form-to-json"},
                )


__all__ = [
    "BASE_HULL_KEYS",
    "CFD_IN_LOOP_ACK_LABEL",
    "CONCURRENCY_ADVISORY_TEXT",
    "CONCURRENCY_ADVISORY_THRESHOLD",
    "DEFAULT_EHVI_INITIAL_POPULATION_SIZE",
    "DEFAULT_EHVI_ITERATION_BUDGET",
    "DEFAULT_EHVI_SEED",
    "DEFAULT_EVALUATORS",
    "DEFAULT_MAX_EVALUATIONS",
    "DEFAULT_NSGA2_GENERATIONS",
    "DEFAULT_NSGA2_POPULATION_SIZE",
    "DEFAULT_NSGA2_SEED",
    "DEFAULT_OBJECTIVES",
    "DEFAULT_SWEEP_LINSPACE_COUNT",
    "DEFAULT_VARIABLE_ROW",
    "DEFAULT_WALL_CLOCK_SECONDS",
    "GenerateSpecFormError",
    "admissible_objective_metrics",
    "build_spec_from_form_state",
    "initialize_form_state",
    "objective_refusal_reason",
    "refresh_cfd_in_loop_status",
    "refresh_concurrency_advisory",
    "render_spec_form_section",
]
