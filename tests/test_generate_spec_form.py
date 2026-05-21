"""Unit tests for the Generate-tab form builder (RFC 0057 stage 4 track 1)."""

from __future__ import annotations

import pytest

from kayakgen.search.active.spec import SearchSpec
from kayakgen.search.sweep import SweepSpec
from kayakgen.ui.web import generate_spec_form
from kayakgen.ui.web.generate_spec_form import (
    CFD_IN_LOOP_ACK_LABEL,
    DEFAULT_EVALUATORS,
    DEFAULT_OBJECTIVES,
    DEFAULT_VARIABLE_ROW,
    GenerateSpecFormError,
    admissible_objective_metrics,
    build_spec_from_form_state,
    objective_refusal_reason,
    refresh_cfd_in_loop_status,
)


# ---------------------------------------------------------------------------
# admissible_objective_metrics()
# ---------------------------------------------------------------------------


def test_admissible_objective_metrics_excludes_display_only() -> None:
    metrics = admissible_objective_metrics()
    # D-2: high-angle GZ keys are always refused as objectives.
    for forbidden in (
        "max_gz_m",
        "heel_at_max_gz_deg",
        "range_positive_stability_deg",
    ):
        assert forbidden not in metrics
    # RFC 0053 turning metrics are role="display_only" and excluded.
    for turning_metric in (
        "turning.edged_waterline_length_m",
        "turning.upright_waterline_length_m",
        "turning.lateral_plane_shift_m",
        "turning.rocker_weighted_maneuverability_signal",
    ):
        assert turning_metric not in metrics
    # D-3 conservative defaults are admissible.
    assert "GM0_m" in metrics
    assert "displaced_mass_kg" in metrics


def test_admissible_objective_metrics_excludes_claim_gated_refusals() -> None:
    metrics = admissible_objective_metrics()
    # RFC 0044: raw resistance and reserved design-fitness metrics require
    # stronger claim/accepted-use provenance and must not be in the picklist.
    assert "Rt_N_last" not in metrics
    assert "design_fitness" not in metrics

    resistance_refusal = objective_refusal_reason("Rt_N_last")
    assert resistance_refusal is not None
    assert resistance_refusal["code"] == "objective_claim_state_not_admissible"


def test_admissible_objective_metrics_returns_stable_registry_order() -> None:
    first = admissible_objective_metrics()
    second = admissible_objective_metrics()
    assert first == second
    # GM0_m is declared before displaced_mass_kg in OBJECTIVE_METADATA, so the
    # form's picklist must reflect that ordering.
    assert first.index("GM0_m") < first.index("displaced_mass_kg")


# ---------------------------------------------------------------------------
# build_spec_from_form_state — sweep round-trip
# ---------------------------------------------------------------------------


def _sweep_form_state() -> dict[str, object]:
    return {
        "generative_job_kind": "sweep",
        "generative_spec_name": "form-sweep",
        "generative_base_hull": {
            "length_m": 4.5,
            "beam_oa_m": 0.55,
            "beam_wl_m": 0.50,
            "draft_m": 0.12,
            "Cp": 0.55,
        },
        "generative_variables": [
            {
                "name": "beam_wl_m",
                "kind": "uniform",
                "min": 0.46,
                "max": 0.54,
                "count": 3,
                "values": "",
            },
            {
                "name": "Cp",
                "kind": "choice",
                "values": "0.52, 0.55, 0.58",
            },
        ],
        "generative_evaluators": dict(DEFAULT_EVALUATORS),
    }


def test_build_spec_from_form_state_sweep_round_trip() -> None:
    payload = build_spec_from_form_state(_sweep_form_state())
    # Wire-format sanity.
    assert payload["schema_version"] == "1"
    assert payload["name"] == "form-sweep"
    assert payload["variables"]["beam_wl_m"] == {
        "kind": "linspace",
        "min": 0.46,
        "max": 0.54,
        "count": 3,
    }
    assert payload["variables"]["Cp"] == {
        "kind": "values",
        "values": [0.52, 0.55, 0.58],
    }
    # The runner accepts the payload via Pydantic validation.
    spec = SweepSpec.model_validate(payload)
    assert spec.base_hull["length_m"] == 4.5
    assert spec.evaluators.hydrostatics is True


# ---------------------------------------------------------------------------
# build_spec_from_form_state — search round-trip
# ---------------------------------------------------------------------------


def _search_form_state() -> dict[str, object]:
    return {
        "generative_job_kind": "search",
        "generative_spec_name": "form-search",
        "generative_base_hull": {
            "length_m": 5.2,
            "beam_oa_m": 0.55,
            "beam_wl_m": 0.50,
            "draft_m": 0.12,
            "Cp": 0.55,
        },
        "generative_variables": [dict(DEFAULT_VARIABLE_ROW)],
        "generative_algorithm_kind": "nsga2",
        "generative_nsga2_population_size": 12,
        "generative_nsga2_generations": 4,
        "generative_seed": 1234,
        "generative_objectives": [dict(obj) for obj in DEFAULT_OBJECTIVES],
        "generative_evaluators": dict(DEFAULT_EVALUATORS),
        "generative_max_evaluations": 64,
        "generative_wall_clock_seconds": 600,
    }


def test_build_spec_from_form_state_search_round_trip() -> None:
    payload = build_spec_from_form_state(_search_form_state())
    assert payload["schema_version"] == "1"
    assert payload["name"] == "form-search"
    assert payload["search_space"]["beam_wl_m"] == {
        "kind": "uniform",
        "min": 0.46,
        "max": 0.54,
    }
    assert payload["algorithm"] == {
        "kind": "nsga2",
        "population_size": 12,
        "generations": 4,
        "seed": 1234,
    }
    assert payload["objectives"] == [
        {"metric": "GM0_m", "direction": "max"},
        {"metric": "displaced_mass_kg", "direction": "min"},
    ]
    assert payload["budget"] == {
        "max_evaluations": 64,
        "wall_clock_seconds": 600.0,
    }
    # The runner accepts the payload via Pydantic validation.
    spec = SearchSpec.model_validate(payload)
    assert spec.algorithm.kind == "nsga2"
    assert len(spec.objectives) == 2
    assert spec.base_hull["length_m"] == 5.2


def test_build_spec_from_selected_objective_metrics_round_trip() -> None:
    state = _search_form_state()
    state.pop("generative_objectives")
    state["generative_selected_objective_metrics"] = [
        "GM0_m",
        "mesh_problem_count",
    ]
    state["generative_objective_directions"] = {
        "GM0_m": "max",
        "mesh_problem_count": "min",
    }

    payload = build_spec_from_form_state(state)

    assert payload["objectives"] == [
        {"metric": "GM0_m", "direction": "max"},
        {"metric": "mesh_problem_count", "direction": "min"},
    ]
    SearchSpec.model_validate(payload)


def test_build_spec_from_form_state_search_ehvi_round_trip() -> None:
    state = _search_form_state()
    state["generative_algorithm_kind"] = "ehvi"
    state["generative_ehvi_initial_population_size"] = 8
    state["generative_ehvi_iteration_budget"] = 16
    payload = build_spec_from_form_state(state)
    assert payload["algorithm"] == {
        "kind": "ehvi",
        "initial_population_size": 8,
        "iteration_budget": 16,
        "seed": 1234,
    }
    spec = SearchSpec.model_validate(payload)
    assert spec.algorithm.kind == "ehvi"


# ---------------------------------------------------------------------------
# Display-only refusal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "display_only_metric",
    [
        "max_gz_m",
        "heel_at_max_gz_deg",
        "range_positive_stability_deg",
        "turning.edged_waterline_length_m",
    ],
)
def test_build_spec_from_form_state_refuses_display_only_objective(
    display_only_metric: str,
) -> None:
    state = _search_form_state()
    state["generative_objectives"] = [
        {"metric": display_only_metric, "direction": "max"}
    ]
    with pytest.raises(GenerateSpecFormError) as excinfo:
        build_spec_from_form_state(state)
    err = excinfo.value
    assert err.code == "objective_not_admissible"
    assert err.reason["metric"] == display_only_metric
    assert err.reason["refusal"]["code"] == "high_angle_gz_display_only"


@pytest.mark.parametrize("claim_gated_metric", ["Rt_N_last", "design_fitness"])
def test_build_spec_from_form_state_refuses_claim_gated_objective(
    claim_gated_metric: str,
) -> None:
    state = _search_form_state()
    state["generative_objectives"] = [
        {"metric": claim_gated_metric, "direction": "min"}
    ]
    with pytest.raises(GenerateSpecFormError) as excinfo:
        build_spec_from_form_state(state)
    err = excinfo.value
    assert err.code == "objective_not_admissible"
    assert err.reason["metric"] == claim_gated_metric
    assert err.reason["refusal"]["code"] == "objective_claim_state_not_admissible"


# ---------------------------------------------------------------------------
# CFD-in-loop acknowledgement gate (D-4)
# ---------------------------------------------------------------------------


def test_cfd_in_loop_block_absent_when_not_requested() -> None:
    state = _search_form_state()
    state["generative_evaluators"] = dict(DEFAULT_EVALUATORS)
    state["generative_cfd_in_loop_acknowledged"] = False
    payload = build_spec_from_form_state(state)
    assert "cfd_in_loop_acknowledged" not in payload["evaluators"]


def test_cfd_in_loop_block_requires_acknowledgement_when_requested() -> None:
    state = _search_form_state()
    evals = dict(DEFAULT_EVALUATORS)
    evals["cfd_in_loop"] = True
    state["generative_evaluators"] = evals
    state["generative_cfd_in_loop_acknowledged"] = False
    with pytest.raises(GenerateSpecFormError) as excinfo:
        build_spec_from_form_state(state)
    assert excinfo.value.code == "cfd_in_loop_ack_required"


def test_cfd_in_loop_first_class_does_not_require_acknowledgement() -> None:
    state = _search_form_state()
    evals = dict(DEFAULT_EVALUATORS)
    evals["cfd_in_loop"] = True
    state["generative_evaluators"] = evals
    state["generative_cfd_in_loop_status"] = "first_class"
    state["generative_cfd_in_loop_acknowledged"] = False

    payload = build_spec_from_form_state(state)

    assert "cfd_in_loop" not in payload["evaluators"]
    assert "cfd_in_loop_acknowledged" not in payload["evaluators"]
    SearchSpec.model_validate(payload)


def test_cfd_in_loop_block_emitted_when_acknowledged() -> None:
    state = _search_form_state()
    evals = dict(DEFAULT_EVALUATORS)
    evals["cfd_in_loop"] = True
    state["generative_evaluators"] = evals
    state["generative_cfd_in_loop_acknowledged"] = True
    # No refusal is raised once the acknowledgement is ticked. The wire
    # EvaluatorOptions is extra="forbid" so the form does NOT smuggle the
    # CFD-in-loop request into the payload — the runner's RFC 0046 opt-in is
    # the authoritative surface. The form's job is to gate submission.
    payload = build_spec_from_form_state(state)
    assert "cfd_in_loop" not in payload["evaluators"]
    assert "cfd_in_loop_acknowledged" not in payload["evaluators"]
    # The remainder of the form is preserved.
    assert payload["evaluators"]["hydrostatics"] is True
    # Round-trips against the search wire schema.
    SearchSpec.model_validate(payload)


def test_cfd_in_loop_ack_label_is_pre_vetted_copy() -> None:
    # Defense-in-depth: anyone editing the constant must rerun the
    # forbidden-claim scrub in tests/test_web_layout.py.
    assert (
        CFD_IN_LOOP_ACK_LABEL
        == "I accept evaluation may take orders of magnitude longer"
    )


# ---------------------------------------------------------------------------
# refresh_cfd_in_loop_status — RFC 0058 stage 2 / workflow 0056 D-14
# ---------------------------------------------------------------------------


class _StubState:
    """Minimal state shim that accepts arbitrary attribute writes."""


class _StubApp:
    def __init__(self) -> None:
        self.state = _StubState()


def test_refresh_cfd_in_loop_status_defaults_to_opt_in_only() -> None:
    app = _StubApp()
    status = refresh_cfd_in_loop_status(app)
    # Empty registry + no scope on the form's base_hull keeps the helper at
    # the default — the acknowledgement copy stays visible.
    assert status == "opt_in_only"
    assert app.state.generative_cfd_in_loop_status == "opt_in_only"


def test_refresh_cfd_in_loop_status_mirrors_first_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _StubApp()

    def _stub_status(**_: object) -> str:
        return "first_class"

    monkeypatch.setattr(
        generate_spec_form, "cfd_in_loop_evaluator_status", _stub_status
    )

    status = refresh_cfd_in_loop_status(app)
    # When the helper graduates the evaluator to first-class, the form
    # mirrors the literal onto state so the rendered acknowledgement
    # checkbox hides via Trame's reactive v_show.
    assert status == "first_class"
    assert app.state.generative_cfd_in_loop_status == "first_class"
