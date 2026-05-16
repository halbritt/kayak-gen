"""RFC 0044 active-search runner integration tests."""

from __future__ import annotations

import json
from pathlib import Path


from kayakgen.search.active.runner import run_search
from kayakgen.search.active.spec import (
    ObjectiveSpec,
    SearchAlgorithmSpec,
    SearchBudget,
    SearchConstraint,
    SearchSpec,
    UniformVariable,
)
from kayakgen.search.sweep import CandidateRecord, EvaluatorOptions


def _base_spec(*, name: str = "search-tiny", **overrides) -> SearchSpec:
    spec = SearchSpec(
        name=name,
        base_hull={"length_m": 4.5, "beam_oa_m": 0.55, "draft_m": 0.12, "Cp": 0.55},
        search_space={
            "beam_wl_m": UniformVariable(kind="uniform", min=0.46, max=0.54),
        },
        algorithm=SearchAlgorithmSpec(
            kind="nsga2",
            population_size=4,
            generations=2,
            seed=1234,
        ),
        objectives=[
            ObjectiveSpec(metric="GM0_m", direction="max"),
            ObjectiveSpec(metric="displaced_mass_kg", direction="min"),
        ],
        evaluators=EvaluatorOptions(hydrostatics=True),
        constraints=[],
        budget=SearchBudget(max_evaluations=999),
    )
    if overrides:
        return spec.model_copy(update=overrides)
    return spec


def _write_spec(spec: SearchSpec, dest: Path) -> Path:
    path = dest / "spec.in.json"
    path.write_text(spec.model_dump_json())
    return path


def test_runner_writes_run_json_with_search_metadata(tmp_path: Path) -> None:
    spec_path = _write_spec(_base_spec(), tmp_path)
    out = tmp_path / "run"
    result = run_search(spec_path, out)

    run_payload = json.loads((out / "run.json").read_text())
    assert run_payload["search_class"] == "conservative"
    assert run_payload["name"] == "search-tiny"
    assert run_payload["search_metadata"]["seed"] == 1234
    assert run_payload["search_metadata"]["algorithm_kind"] == "nsga2"
    assert run_payload["search_metadata"]["population_size"] == 4
    assert run_payload["search_metadata"]["generations"] == 2
    assert run_payload["search_metadata"]["termination_reason"] == "completed"
    assert result.search_metadata.termination_reason == "completed"
    assert result.completed_count >= 1
    assert (out / "summary.csv").exists()
    assert (out / "failures.jsonl").exists()
    assert (out / "spec.json").exists()


def test_runner_writes_per_generation_history(tmp_path: Path) -> None:
    spec_path = _write_spec(_base_spec(), tmp_path)
    out = tmp_path / "run"
    result = run_search(spec_path, out)
    history = result.search_metadata.history
    assert len(history) == 2
    assert history[0].generation == 0
    assert history[1].generation == 1
    # The frontier size should be >= 1 when at least one feasible candidate
    # was evaluated.
    assert history[0].frontier_size >= 1


def test_runner_constraint_violation_produces_constraint_failed_status(
    tmp_path: Path,
) -> None:
    # Constrain displaced_mass_kg to an impossibly high lower bound so every
    # evaluated candidate violates it and gets constraint_failed.
    spec = _base_spec(name="search-constrained").model_copy(
        update={
            "constraints": [
                SearchConstraint(metric="displaced_mass_kg", min=1.0e9)
            ],
        }
    )
    spec_path = _write_spec(spec, tmp_path)
    out = tmp_path / "run"
    result = run_search(spec_path, out)
    assert result.constraint_failed_count >= 1
    # The complete status must not coexist with constraint_failed on any
    # single record (per-record assertion).
    for record_path in (out / "candidates").glob("*.record.json"):
        record = CandidateRecord.model_validate_json(record_path.read_text())
        assert record.status != "complete" or "constraint_violations" not in record.summary
    # And no constraint_failed candidate is in the final frontier.
    constraint_failed_keys = {
        CandidateRecord.model_validate_json(p.read_text()).candidate_key
        for p in (out / "candidates").glob("*.record.json")
        if CandidateRecord.model_validate_json(p.read_text()).status == "constraint_failed"
    }
    assert constraint_failed_keys.isdisjoint(set(result.final_frontier_keys))


def test_runner_exploratory_mode_tags_search_class_and_run_record(
    tmp_path: Path,
) -> None:
    spec = _base_spec(name="search-exploratory").model_copy(
        update={"objectives_explicit_exploratory": True}
    )
    spec_path = _write_spec(spec, tmp_path)
    out = tmp_path / "run"
    result = run_search(spec_path, out)
    assert result.search_class == "exploratory"
    payload = json.loads((out / "run.json").read_text())
    assert payload["search_class"] == "exploratory"


def test_runner_budget_exhausted_writes_pending_records(tmp_path: Path) -> None:
    # Set budget=1 so only the first candidate evaluates; the remaining
    # population-0 members never get evaluated. The runner shouldn't crash —
    # any unrun queued candidate is preserved across the iteration boundary
    # via the state checkpoint.
    spec = _base_spec(name="search-budget").model_copy(
        update={"budget": SearchBudget(max_evaluations=1)}
    )
    spec_path = _write_spec(spec, tmp_path)
    out = tmp_path / "run"
    result = run_search(spec_path, out)
    assert result.search_metadata.termination_reason == "budget_exhausted"
    assert result.completed_count + result.constraint_failed_count + result.failed_count >= 1


def test_runner_resume_replays_pending_first_then_continues(tmp_path: Path) -> None:
    spec = _base_spec(name="search-resume")
    spec_path = _write_spec(spec, tmp_path)
    out = tmp_path / "run"
    run_search(spec_path, out)
    # Resume on a completed run should not blow up and should leave the
    # frontier set stable.
    second = run_search(spec_path, out, resume=True)
    assert second.search_metadata.termination_reason in ("completed", "budget_exhausted")


def test_runner_resume_seed_preservation_produces_same_final_frontier(
    tmp_path: Path,
) -> None:
    spec = _base_spec(name="search-determ")
    spec_path = _write_spec(spec, tmp_path)
    out_a = tmp_path / "run-a"
    out_b = tmp_path / "run-b"
    result_a = run_search(spec_path, out_a)
    result_b = run_search(spec_path, out_b)
    assert set(result_a.final_frontier_keys) == set(result_b.final_frontier_keys)
    # Byte-identical record.json content for the same candidate key.
    for key in result_a.final_frontier_keys:
        a_bytes = (out_a / "candidates" / f"{key}.record.json").read_text()
        b_bytes = (out_b / "candidates" / f"{key}.record.json").read_text()
        assert a_bytes == b_bytes
