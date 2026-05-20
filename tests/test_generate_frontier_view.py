"""Unit tests for the Pareto frontier view module (RFC 0057 stage 4 track 2)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from kayakgen.ui.web.generate_frontier_view import (
    FORBIDDEN_METRIC_TOKENS,
    apply_candidate_to_hull,
    build_frontier_view_model,
    refresh_frontier_view,
    undo_candidate_handoff,
)


# ---------------------------------------------------------------------------
# Forbidden-token scrub set — kept in lock-step with tests/test_web_layout.py.
# ---------------------------------------------------------------------------

FORBIDDEN_TOKENS: tuple[str, ...] = (
    "_".join(("max", "gz", "m")),
    "_".join(("heel", "at", "max", "gz", "deg")),
    "_".join(("range", "positive", "stability", "deg")),
    "_".join(("area", "under", "positive", "gz", "m", "deg")),
    "_".join(("righting", "moment", "nm")),
    "_".join(("gz", "m")),
    "fixture" + "_" + "only",
    "Open" + "FOAM",
    "SU2",
    "worker queue",
    "calibrated drag",
    "design fitness",
    "cfd_ready",
    "final prediction",
    "hos" + "ted",
    "cloud",
)


def _sample_payload(
    *,
    with_third_objective: bool = False,
    include_forbidden_keys: bool = False,
) -> dict[str, Any]:
    summary_a: dict[str, Any] = {
        "GM0_m": 0.32,
        "displaced_mass_kg": 18.5,
        "convergence_flag": "converged",
        "claim_state": "raw_unvalidated",
    }
    summary_b: dict[str, Any] = {
        "GM0_m": 0.41,
        "displaced_mass_kg": 19.7,
        "convergence_flag": "converged",
        "claim_state": "raw_unvalidated",
    }
    if with_third_objective:
        summary_a["wetted_surface_m2"] = 1.21
        summary_b["wetted_surface_m2"] = 1.34
    if include_forbidden_keys:
        # The view-model must drop these silently.
        summary_a[FORBIDDEN_METRIC_TOKENS[0]] = 0.40
        summary_b[FORBIDDEN_METRIC_TOKENS[1]] = 47.0
        summary_a[FORBIDDEN_METRIC_TOKENS[2]] = 75.0

    return {
        "result_semantics": "raw_unvalidated",
        "job_id": "job-test",
        "frontier_available": True,
        "frontier": [
            # Provided out-of-order to verify deterministic sorting.
            {
                "candidate_key": "cand-b",
                "status": "complete",
                "parameters": {"beam_wl_m": 0.52, "draft_m": 0.13},
                "summary": summary_b,
            },
            {
                "candidate_key": "cand-a",
                "status": "complete",
                "parameters": {"beam_wl_m": 0.48, "draft_m": 0.11},
                "summary": summary_a,
            },
        ],
    }


# ---------------------------------------------------------------------------
# build_frontier_view_model
# ---------------------------------------------------------------------------


def test_build_view_model_orders_rows_deterministically_by_candidate_key() -> None:
    payload = _sample_payload()

    view = build_frontier_view_model(
        payload, x_metric="GM0_m", y_metric="displaced_mass_kg"
    )

    assert view["available"] is True
    assert [row["candidate_key"] for row in view["rows"]] == ["cand-a", "cand-b"]
    # Re-running with identical input is byte-stable (deterministic ordering).
    again = build_frontier_view_model(
        payload, x_metric="GM0_m", y_metric="displaced_mass_kg"
    )
    assert [row["candidate_key"] for row in again["rows"]] == ["cand-a", "cand-b"]


def test_build_view_model_two_objectives_populates_scatter_points_no_z() -> None:
    payload = _sample_payload()

    view = build_frontier_view_model(
        payload, x_metric="GM0_m", y_metric="displaced_mass_kg"
    )

    assert view["z_metric"] is None
    assert view["axis_labels"]["z"] is None
    assert len(view["scatter_points"]) == 2
    for point in view["scatter_points"]:
        assert point["z"] is None
        assert isinstance(point["x"], float)
        assert isinstance(point["y"], float)
        assert point["marker"] == "o"  # converged -> circle marker
        # Color is sourced from theme palette tokens — never a banned literal.
        assert point["color"].startswith("#")
        assert point["color_class"].startswith("kg-frontier-point--")
        assert point["color_token"] in {"state-raw", "state-info", "state-advisory",
                                        "state-success", "state-error", "text-muted"}


def test_build_view_model_three_objectives_populates_third_column() -> None:
    payload = _sample_payload(with_third_objective=True)

    view = build_frontier_view_model(
        payload,
        x_metric="GM0_m",
        y_metric="displaced_mass_kg",
        z_metric="wetted_surface_m2",
    )

    assert view["z_metric"] == "wetted_surface_m2"
    assert view["axis_labels"]["z"] == "wetted_surface_m2"
    for row in view["rows"]:
        assert isinstance(row["z"], float)
    for point in view["scatter_points"]:
        assert isinstance(point["z"], float)
        assert isinstance(point["z_color_ratio"], float)
    assert view["color_axis"]["metric"] == "wetted_surface_m2"
    assert view["color_axis"]["min"] == pytest.approx(1.21)
    assert view["color_axis"]["max"] == pytest.approx(1.34)


def test_build_view_model_drops_forbidden_high_angle_gz_keys() -> None:
    payload = _sample_payload(include_forbidden_keys=True)

    view = build_frontier_view_model(
        payload, x_metric="GM0_m", y_metric="displaced_mass_kg"
    )

    # No row should leak any high-angle GZ display-only metric key.
    for row in view["rows"]:
        for key in row["parameters"]:
            assert all(token not in key for token in FORBIDDEN_METRIC_TOKENS), key


def test_build_view_model_refuses_forbidden_axis_metric() -> None:
    payload = _sample_payload(include_forbidden_keys=True)

    view = build_frontier_view_model(
        payload, x_metric=FORBIDDEN_METRIC_TOKENS[0], y_metric="GM0_m"
    )

    assert view["available"] is False
    assert view["rows"] == []
    assert view["scatter_points"] == []
    assert view["note"]
    # The axis label must not echo the banned metric key back to the caller.
    assert FORBIDDEN_METRIC_TOKENS[0] not in view["axis_labels"]["x"]


# ---------------------------------------------------------------------------
# Forbidden-claim scan: every string output of build_frontier_view_model
# is scrubbed of banned tokens.
# ---------------------------------------------------------------------------


def _walk_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            out.append(str(k))
            out.extend(_walk_strings(v))
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            out.extend(_walk_strings(item))
    return out


def test_build_view_model_outputs_are_scrubbed_of_forbidden_tokens() -> None:
    payload = _sample_payload(with_third_objective=True, include_forbidden_keys=True)
    view = build_frontier_view_model(
        payload,
        x_metric="GM0_m",
        y_metric="displaced_mass_kg",
        z_metric="wetted_surface_m2",
    )

    strings = _walk_strings(view)
    lowered = [s.lower() for s in strings]

    for token in FORBIDDEN_TOKENS:
        token_lower = token.lower()
        for value in lowered:
            assert token_lower not in value, (
                f"forbidden token {token!r} leaked through view-model value {value!r}"
            )


# ---------------------------------------------------------------------------
# apply_candidate_to_hull
# ---------------------------------------------------------------------------


class _FakeState:
    """Minimal stand-in for the Trame state object used by the view module."""

    def __init__(self, **fields: Any) -> None:
        for key, value in fields.items():
            setattr(self, key, value)

    def update(self, mapping: dict[str, Any]) -> None:
        for key, value in mapping.items():
            setattr(self, key, value)


def test_apply_candidate_to_hull_mutates_state_and_captures_prior() -> None:
    state = _FakeState(
        length_m=5.0,
        beam_oa_m=0.55,
        beam_wl_m=0.50,
        draft_m=0.12,
        deck_height_m=0.30,
        Cp=0.55,
        Cm=0.85,
        deck_flatness=0.4,
        center_box_ratio=0.3,
        bow_rake=1.0,
        stern_rake=1.0,
        generative_handoff_prior=None,
        generative_handoff_toast="",
    )
    refresh_calls: list[int] = []
    app = SimpleNamespace(state=state, _refresh_current_hull_surface=lambda: refresh_calls.append(1))

    prior = apply_candidate_to_hull(
        app,
        {"parameters": {"beam_wl_m": 0.48, "draft_m": 0.11}},
    )

    # The prior snapshot is captured before mutation.
    assert prior["beam_wl_m"] == pytest.approx(0.50)
    assert prior["draft_m"] == pytest.approx(0.12)
    # The state is mutated to the candidate's values.
    assert state.beam_wl_m == pytest.approx(0.48)
    assert state.draft_m == pytest.approx(0.11)
    # The prior snapshot lives on app.state for the undo controller.
    assert state.generative_handoff_prior["beam_wl_m"] == pytest.approx(0.50)
    assert state.generative_handoff_toast == "Loaded candidate; undo available."
    # Hull surface was refreshed after the mutation.
    assert refresh_calls == [1]


def test_undo_candidate_handoff_restores_prior_state() -> None:
    state = _FakeState(
        length_m=5.0,
        beam_oa_m=0.55,
        beam_wl_m=0.48,
        draft_m=0.11,
        deck_height_m=0.30,
        Cp=0.55,
        Cm=0.85,
        deck_flatness=0.4,
        center_box_ratio=0.3,
        bow_rake=1.0,
        stern_rake=1.0,
        generative_handoff_prior={"beam_wl_m": 0.50, "draft_m": 0.12},
        generative_handoff_toast="loaded cand-a",
    )
    app = SimpleNamespace(state=state, _refresh_current_hull_surface=lambda: None)

    restored = undo_candidate_handoff(app)

    assert restored is True
    assert state.beam_wl_m == pytest.approx(0.50)
    assert state.draft_m == pytest.approx(0.12)
    assert state.generative_handoff_prior == {}
    assert state.generative_handoff_toast == ""


# ---------------------------------------------------------------------------
# refresh_frontier_view integration with a fake manager.
# ---------------------------------------------------------------------------


def test_refresh_frontier_view_updates_state_keys_from_payload(tmp_path) -> None:
    import json
    from kayakgen.services.generative_jobs import InProcessGenerativeJobManager

    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")
    # Hand-craft a job + run.json so we exercise refresh_frontier_view without
    # actually executing a search.
    job_id = "viewtest1234"
    job_dir = manager.jobs_root / job_id
    output_dir = job_dir / "output"
    output_dir.mkdir(parents=True)
    spec_path = job_dir / "spec.json"
    spec_path.write_text("{}")
    (job_dir / "log.txt").write_text("")
    (job_dir / "job.json").write_text(
        json.dumps(
            {
                "schema_version": "1",
                "job_id": job_id,
                "job_kind": "search",
                "spec_ref": "spec.json",
                "spec_hash": "0" * 64,
                "output_dir": str(output_dir),
                "state": "succeeded",
                "progress": {
                    "schema_version": "1",
                    "realized_evaluations": 2,
                    "budget_max_evaluations": None,
                    "generation": None,
                    "iteration": None,
                    "pending_count": 0,
                    "completed_count": 2,
                    "failed_count": 0,
                    "constraint_failed_count": 0,
                    "wall_clock_seconds": 0.0,
                    "last_candidate_key": None,
                    "last_update_at": 0.0,
                },
                "started_at": None,
                "completed_at": None,
                "cancellation_requested_at": None,
                "error": None,
                "log_tail_ref": "log.txt",
                "resumable_from_checkpoint": False,
            },
            sort_keys=True,
        )
    )
    (output_dir / "run.json").write_text(
        json.dumps(
            {
                "final_frontier_keys": ["cand-a", "cand-b"],
                "candidates": [
                    {
                        "candidate_key": "cand-a",
                        "status": "complete",
                        "parameters": {"beam_wl_m": 0.48},
                        "hull_hash": "deadbeef",
                        "summary": {"GM0_m": 0.32, "displaced_mass_kg": 18.5},
                    },
                    {
                        "candidate_key": "cand-b",
                        "status": "complete",
                        "parameters": {"beam_wl_m": 0.52},
                        "hull_hash": "feedface",
                        "summary": {"GM0_m": 0.41, "displaced_mass_kg": 19.7},
                    },
                ],
            }
        )
    )

    state = _FakeState(
        generative_frontier_x_metric="",
        generative_frontier_y_metric="",
        generative_frontier_z_metric="",
        generative_frontier_view_available=False,
    )
    app = SimpleNamespace(state=state, _generative_manager=manager)

    view = refresh_frontier_view(app, job_id)

    assert view["available"] is True
    assert state.generative_frontier_view_available is True
    assert state.generative_frontier_x_metric == "GM0_m"
    assert state.generative_frontier_y_metric == "displaced_mass_kg"
    assert state.generative_frontier_metric_options == ["GM0_m", "displaced_mass_kg"]
    assert [row["candidate_key"] for row in state.generative_frontier_table_rows] == ["cand-a", "cand-b"]
    # SVG fallback is precomputed so the layout test surface can assert on it.
    assert "<svg" in state.generative_frontier_scatter_svg
    assert "cand-a" in state.generative_frontier_scatter_svg
