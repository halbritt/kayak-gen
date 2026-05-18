"""Progress-sink integration tests for run_search/run_sweep (RFC 0057 stage 1)."""

from __future__ import annotations

from pathlib import Path

from kayakgen.search.active.runner import run_search
from kayakgen.search.active.spec import (
    EhviAlgorithmConfig,
    ObjectiveSpec,
    SearchAlgorithmSpec,
    SearchBudget,
    SearchSpec,
    UniformVariable,
)
from kayakgen.search.sweep import EvaluatorOptions, ParameterSweep, SweepSpec, run_sweep


class _RecordingSink:
    """Minimal :class:`GenerativeJobProgressSink` for tests."""

    def __init__(self, *, cancel_after: int | None = None) -> None:
        self.candidate_events: list[dict[str, object]] = []
        self.checkpoint_events: list[dict[str, object]] = []
        self._cancel_after = cancel_after
        self._cancelled = False

    def candidate_completed(
        self,
        *,
        candidate_key: str,
        status: str,
        generation: int | None,
        iteration: int | None,
        realized_evaluations: int,
    ) -> None:
        self.candidate_events.append(
            {
                "candidate_key": candidate_key,
                "status": status,
                "generation": generation,
                "iteration": iteration,
                "realized_evaluations": realized_evaluations,
            }
        )
        if (
            self._cancel_after is not None
            and realized_evaluations >= self._cancel_after
        ):
            self._cancelled = True

    def checkpoint(
        self,
        *,
        generation: int | None,
        iteration: int | None,
        realized_evaluations: int,
    ) -> None:
        self.checkpoint_events.append(
            {
                "generation": generation,
                "iteration": iteration,
                "realized_evaluations": realized_evaluations,
            }
        )

    def should_cancel(self) -> bool:
        return self._cancelled


def _nsga2_spec() -> SearchSpec:
    return SearchSpec(
        name="search-progress-sink",
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


def _ehvi_spec() -> SearchSpec:
    return SearchSpec(
        name="search-progress-sink-ehvi",
        base_hull={"length_m": 4.5, "beam_oa_m": 0.55, "draft_m": 0.12, "Cp": 0.55},
        search_space={
            "beam_wl_m": UniformVariable(kind="uniform", min=0.46, max=0.54),
        },
        algorithm=EhviAlgorithmConfig(
            kind="ehvi",
            initial_population_size=3,
            iteration_budget=2,
            seed=4321,
            candidate_pool_size=8,
        ),
        objectives=[
            ObjectiveSpec(metric="GM0_m", direction="max"),
            ObjectiveSpec(metric="displaced_mass_kg", direction="min"),
        ],
        evaluators=EvaluatorOptions(hydrostatics=True),
        constraints=[],
        budget=SearchBudget(max_evaluations=999),
    )


def _write_spec(spec: SearchSpec, dest: Path) -> Path:
    path = dest / "spec.in.json"
    path.write_text(spec.model_dump_json())
    return path


def test_run_search_nsga2_emits_progress_events(tmp_path: Path) -> None:
    spec = _nsga2_spec()
    spec_path = _write_spec(spec, tmp_path)
    sink = _RecordingSink()

    result = run_search(spec_path, tmp_path / "run", progress_sink=sink)

    assert sink.candidate_events, "candidate_completed must fire at least once"
    assert sink.checkpoint_events, "checkpoint must fire at least once"
    statuses = {ev["status"] for ev in sink.candidate_events}
    assert statuses.issubset({"complete", "failed", "constraint_failed"})
    last = sink.candidate_events[-1]
    assert isinstance(last["realized_evaluations"], int)
    assert last["realized_evaluations"] >= 1
    assert result.completed_count >= 0


def test_run_search_nsga2_default_byte_stable_against_sink(tmp_path: Path) -> None:
    spec = _nsga2_spec()
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    spec_path_a = _write_spec(spec, dir_a)
    spec_path_b = _write_spec(spec, dir_b)

    out_a = tmp_path / "run-a"
    out_b = tmp_path / "run-b"
    run_search(spec_path_a, out_a)
    run_search(spec_path_b, out_b, progress_sink=_RecordingSink())

    candidates_a = sorted((out_a / "candidates").glob("*.record.json"))
    candidates_b = sorted((out_b / "candidates").glob("*.record.json"))
    assert [p.name for p in candidates_a] == [p.name for p in candidates_b]
    for ca, cb in zip(candidates_a, candidates_b):
        assert ca.read_text() == cb.read_text(), (
            f"progress_sink changed canonical output for {ca.name}"
        )


def test_run_search_nsga2_cancels_via_sink(tmp_path: Path) -> None:
    spec = _nsga2_spec().model_copy(
        update={
            "algorithm": SearchAlgorithmSpec(
                kind="nsga2",
                population_size=4,
                generations=10,
                seed=1234,
            ),
        }
    )
    spec_path = _write_spec(spec, tmp_path)
    sink = _RecordingSink(cancel_after=2)

    result = run_search(spec_path, tmp_path / "run", progress_sink=sink)

    assert result.search_metadata.termination_reason in (
        "operator_stop",
        "completed",
    )
    if result.search_metadata.termination_reason == "operator_stop":
        assert result.search_metadata.realized_evaluations < 4 * 10


def test_run_search_ehvi_emits_progress_events(tmp_path: Path) -> None:
    spec = _ehvi_spec()
    spec_path = _write_spec(spec, tmp_path)
    sink = _RecordingSink()

    run_search(spec_path, tmp_path / "run", progress_sink=sink)

    assert sink.candidate_events
    assert sink.checkpoint_events
    iterations = [ev["iteration"] for ev in sink.candidate_events]
    assert all(isinstance(i, int) for i in iterations)
    assert all(ev["generation"] is None for ev in sink.candidate_events)


def test_run_sweep_emits_progress_events(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="sweep-progress-sink",
        base_hull={"length_m": 4.5, "beam_oa_m": 0.55, "draft_m": 0.12, "Cp": 0.55},
        variables={
            "beam_wl_m": ParameterSweep(kind="values", values=[0.48, 0.50, 0.52]),
        },
        evaluators=EvaluatorOptions(hydrostatics=True),
    )
    sink = _RecordingSink()

    run_sweep(spec, tmp_path / "run", progress_sink=sink)

    assert len(sink.candidate_events) == 3
    keys = [ev["candidate_key"] for ev in sink.candidate_events]
    assert len(set(keys)) == 3


def test_run_sweep_cancels_via_sink(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="sweep-cancel",
        base_hull={"length_m": 4.5, "beam_oa_m": 0.55, "draft_m": 0.12, "Cp": 0.55},
        variables={
            "beam_wl_m": ParameterSweep(
                kind="values",
                values=[0.46, 0.48, 0.50, 0.52, 0.54],
            ),
        },
        evaluators=EvaluatorOptions(hydrostatics=True),
    )
    sink = _RecordingSink(cancel_after=2)

    run_sweep(spec, tmp_path / "run", progress_sink=sink)

    assert len(sink.candidate_events) <= 3
    assert len(sink.candidate_events) >= 2
