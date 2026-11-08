"""Deterministic sweep specs and run records."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:  # pragma: no cover - import only for type hints
    from kayakgen.services.artifact_store import FilesystemArtifactStore
    from kayakgen.services.generative_jobs import GenerativeJobProgressSink

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from kayakgen.eval.contract import EvaluationResult
from kayakgen.eval.high_angle_gz import build_high_angle_gz_block
from kayakgen.eval.contract import LoadCase
from kayakgen.eval.stability import DEFAULT_GZ_HEEL_GRID_DEG
from kayakgen.eval.turning import evaluate_turning_metrics
from kayakgen.eval.sweep_artifacts import (
    HighAngleGzArtifact,
    StlArtifactSet,
    write_candidate_high_angle_gz,
    write_candidate_stl,
)
from kayakgen.io.json import write_text_atomic, save_evaluation, save_hull
from kayakgen.model.hull import Hull
from kayakgen.model.validity import DesignValidityReport, evaluate_design_validity
from kayakgen.search.candidate_reuse import (
    CandidateReuseUnavailable as SweepReuseUnavailable,
    load_reusable_candidate,
)
from kayakgen.search.objectives import OBJECTIVE_METADATA
from kayakgen.search.pareto import HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS

ParameterKind = Literal["values", "linspace"]
CandidateStatus = Literal["pending", "complete", "failed", "skipped", "constraint_failed"]
SweepExecutionState = Literal["running", "complete", "cancelled", "incomplete"]


class ParameterSweep(BaseModel):
    """One deterministic parameter expansion."""

    model_config = ConfigDict(extra="forbid")

    kind: ParameterKind
    values: list[float] | None = None
    min: float | None = None
    max: float | None = None
    count: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _validate_kind(self) -> "ParameterSweep":
        if self.kind == "values":
            if not self.values:
                raise ValueError("values sweep requires non-empty values")
            return self
        if self.min is None or self.max is None or self.count is None:
            raise ValueError("linspace sweep requires min, max, and count")
        return self

    def expand(self) -> list[float]:
        if self.kind == "values":
            return list(self.values or [])
        assert self.min is not None and self.max is not None and self.count is not None
        return [float(v) for v in np.linspace(self.min, self.max, self.count)]


class EvaluatorOptions(BaseModel):
    """Evaluators to run for each valid candidate."""

    model_config = ConfigDict(extra="forbid")

    hydrostatics: bool = True
    resistance: bool = False
    numerical_relative_tolerance: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    stability: bool = False
    stability_equilibrium: bool = False
    stability_load_case: dict[str, Any] = Field(default_factory=dict)
    stability_tolerance_kg: float = Field(default=1.0, gt=0)
    stability_moment_tolerance_kg_m: float | None = Field(default=None, gt=0)
    water_density_kg_m3: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    kinematic_viscosity_m2_s: float = Field(default=1.19e-6, gt=0, allow_inf_nan=False)
    hydrostatic_stations: int = Field(default=150, ge=3)
    n_stations: int = Field(default=600, ge=3)
    n_depths: int = Field(default=25, ge=3)
    n_theta: int = Field(default=40, ge=3)
    speeds_knots: tuple[float, ...] = tuple(1 + .25*i for i in range(21))
    mesh_diagnostics: bool = False
    stl: bool = False
    high_angle_gz: bool = False
    high_angle_gz_heel_grid_deg: list[float] | None = None
    turning_metrics: bool = False
    turning_metrics_heel_deg: float = 8.0


class SweepLimits(BaseModel):
    """Runtime limits for a sweep."""

    model_config = ConfigDict(extra="forbid")

    max_candidates: int = Field(default=1000, ge=1)


class SweepSpec(BaseModel):
    """JSON-compatible deterministic sweep input."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    name: str = "sweep"
    base_hull: dict[str, Any] = Field(default_factory=dict)
    variables: dict[str, ParameterSweep]
    evaluators: EvaluatorOptions = Field(default_factory=EvaluatorOptions)
    limits: SweepLimits = Field(default_factory=SweepLimits)

    def spec_hash(self) -> str:
        return hashlib.sha256(_canonical_json(self.model_dump(mode="json")).encode("utf-8")).hexdigest()


class CandidateRecord(BaseModel):
    """Persistent record for one candidate expansion."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    candidate_index: int
    candidate_key: str
    parameters: dict[str, Any]
    attempted_hull: dict[str, Any]
    status: CandidateStatus
    hull_hash: str | None = None
    artifacts: dict[str, str] = Field(default_factory=dict)
    evaluator_settings: dict[str, Any] = Field(default_factory=dict)
    evaluator_versions: dict[str, str] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    design_validity: DesignValidityReport = Field(default_factory=DesignValidityReport)
    design_warning_count: int = 0
    design_unsupported_count: int = 0
    stl_artifacts: StlArtifactSet | None = None
    high_angle_gz_artifact: HighAngleGzArtifact | None = None
    error: str | None = None

    @model_validator(mode="after")
    def _sync_design_validity_counts(self) -> "CandidateRecord":
        self.design_warning_count = self.design_validity.warning_count
        self.design_unsupported_count = self.design_validity.unsupported_count
        return self


class SweepRunRecord(BaseModel):
    """Top-level run record."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    name: str
    spec_hash: str
    candidate_count: int
    pending_count: int
    completed_count: int
    failed_count: int
    skipped_count: int
    candidates: list[CandidateRecord]
    execution_state: SweepExecutionState | None = None
    requested_candidate_count: int | None = Field(default=None, ge=0)
    processed_candidate_count: int | None = Field(default=None, ge=0)
    reused_count: int | None = Field(default=None, ge=0)
    reused_candidate_keys: list[str] = Field(default_factory=list)
    execution_errors: list[str] = Field(default_factory=list)
    previous_run_artifact_hash: str | None = None

    @model_validator(mode="after")
    def _execution_scope_matches_outcomes(self) -> "SweepRunRecord":
        if self.execution_state is None:
            return self
        processed = len(self.candidates)
        if (self.requested_candidate_count is None or self.processed_candidate_count != processed
                or self.candidate_count != processed or self.requested_candidate_count < processed):
            raise ValueError("execution scope must name the requested and processed candidate sets")
        if self.reused_count != len(self.reused_candidate_keys) or self.skipped_count != self.reused_count:
            raise ValueError("reuse count must match its execution keys")
        complete = {r.candidate_key for r in self.candidates if r.status == "complete"}
        if not set(self.reused_candidate_keys).issubset(complete):
            raise ValueError("only completed outcomes can be reused")
        if (self.completed_count != sum(r.status == "complete" for r in self.candidates)
                or self.pending_count != sum(r.status == "pending" for r in self.candidates)
                or self.failed_count != sum(r.status == "failed" for r in self.candidates)):
            raise ValueError("outcome counts must match candidate scientific states")
        if self.execution_state == "complete" and (
            processed != self.requested_candidate_count or self.pending_count != 0
            or any(r.status == "skipped" for r in self.candidates) or self.execution_errors
        ):
            raise ValueError("complete execution must resolve the entire requested scope")
        return self


def load_sweep_spec(path: str | Path) -> SweepSpec:
    return SweepSpec.model_validate_json(Path(path).read_text())


def expand_candidates(spec: SweepSpec) -> list[tuple[int, str, dict[str, Any], dict[str, Any]]]:
    """Return ``(index, key, params, attempted_hull)`` rows in stable order."""
    names = list(spec.variables)
    value_lists = [spec.variables[name].expand() for name in names]
    combos = list(product(*value_lists))
    if len(combos) > spec.limits.max_candidates:
        raise ValueError(
            f"sweep expands to {len(combos)} candidates, over max {spec.limits.max_candidates}"
        )

    spec_hash = spec.spec_hash()
    rows: list[tuple[int, str, dict[str, Any], dict[str, Any]]] = []
    for index, combo in enumerate(combos):
        params = {name: value for name, value in zip(names, combo)}
        attempted = dict(spec.base_hull) | params
        key_payload = {"spec_hash": spec_hash, "parameters": params}
        candidate_key = hashlib.sha256(_canonical_json(key_payload).encode("utf-8")).hexdigest()
        rows.append((index, candidate_key, params, attempted))
    return rows


def run_sweep(
    spec: SweepSpec,
    out_dir: str | Path,
    resume: bool = False,
    *,
    progress_sink: "GenerativeJobProgressSink | None" = None,
) -> SweepRunRecord:
    """Run a deterministic sweep and write candidate/run artifacts.

    Routes every persisted artifact through
    :class:`kayakgen.services.artifact_store.FilesystemArtifactStore`
    (RFC 0049) so the run directory gains a ``_store/`` content-addressed
    mirror and the SQLite index records the run + candidates + metrics +
    artifacts. Canonical artifact paths retain their existing layout.

    ``progress_sink`` is an optional :class:`GenerativeJobProgressSink`
    (RFC 0057). When provided, the runner calls
    ``progress_sink.candidate_completed(...)`` after every candidate
    write and checks ``progress_sink.should_cancel()`` between
    emissions; a ``True`` cancel breaks the iteration loop after the
    in-flight candidate finishes. Default ``progress_sink=None``
    leaves progress publication disabled.
    """
    from kayakgen import __version__ as kayakgen_version
    from kayakgen.services.artifact_store import (
        FilesystemArtifactStore,
        index_candidates,
    )
    from kayakgen.services.identity import run_hash as compute_run_hash

    expanded = expand_candidates(spec)
    out = Path(out_dir)
    candidates_dir = out / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)

    spec_hash_value = spec.spec_hash()
    run_hash_value = compute_run_hash(
        spec.model_dump(mode="json"), kayakgen_version
    )
    store = FilesystemArtifactStore.open_run(
        out, kind="sweep", spec_hash=spec_hash_value, run_hash_value=run_hash_value,
    )
    run_id = store.run_id
    prior_run = store.manifest.artifacts.get("run.json")
    if resume and (out / "run.json").exists() and prior_run is None:
        raise SweepReuseUnavailable("legacy run provenance is unknown; preserve it and use a new output directory")
    store.put_json("sweep_run_record", spec, canonical_path=out / "spec.json")
    run = SweepRunRecord(
        name=spec.name, spec_hash=spec_hash_value, candidate_count=0,
        pending_count=0, completed_count=0, failed_count=0, skipped_count=0,
        candidates=[], execution_state="running", requested_candidate_count=len(expanded),
        processed_candidate_count=0, reused_count=0,
        previous_run_artifact_hash=prior_run.artifact_hash if prior_run is not None else None,
    )
    store.put_json("sweep_run_record", run, canonical_path=out / "run.json")
    cancelled = False
    try:
        for index, candidate_key, params, attempted in expanded:
            if cancelled:
                break
            record = load_reusable_candidate(store, candidate_key) if resume else None
            if record is not None and record.status in ("complete", "pending"):
                if record.parameters != params or record.attempted_hull != attempted:
                    raise SweepReuseUnavailable(f"cached candidate differs from requested inputs: {candidate_key}")
                if record.status == "complete":
                    run.reused_candidate_keys.append(candidate_key)
            else:
                request = CandidateRecord(
                    candidate_index=index, candidate_key=candidate_key, parameters=params,
                    attempted_hull=attempted, status="pending",
                )
                record = _run_candidate(spec, request, store)
            run.candidates.append(record)
            if progress_sink is not None:
                progress_sink.candidate_completed(
                    candidate_key=record.candidate_key, status=record.status,
                    generation=None, iteration=index, realized_evaluations=len(run.candidates),
                )
                cancelled = progress_sink.should_cancel()
        state = ("cancelled" if cancelled else "incomplete"
                 if any(record.status == "pending" for record in run.candidates) else "complete")
        run = _execution_snapshot(run, state)
        _write_summary(out / "summary.csv", run.candidates)
        store.put_file("sweep_summary_csv", out / "summary.csv")
        _write_failures(out / "failures.jsonl", [r for r in run.candidates if r.status == "failed"])
        store.put_file("sweep_failures_jsonl", out / "failures.jsonl")
        index_candidates(
            run_id=run_id, candidate_rows=[_index_row_for_candidate(rec) for rec in run.candidates],
            index=store.index,
        )
        # Completion is published after every required bundle output.
        store.put_json("sweep_run_record", run, canonical_path=out / "run.json")
    except Exception as exc:
        incomplete = _execution_snapshot(run, "incomplete", errors=[str(exc)])
        store.put_json("sweep_run_record", incomplete, canonical_path=out / "run.json")
        raise
    return run


def _execution_snapshot(
    run: SweepRunRecord, state: SweepExecutionState, *, errors: list[str] | None = None,
) -> SweepRunRecord:
    return SweepRunRecord.model_validate({**run.model_dump(mode="json"),
        "execution_state": state, "execution_errors": errors or [],
        "candidate_count": len(run.candidates), "processed_candidate_count": len(run.candidates),
        "pending_count": sum(r.status == "pending" for r in run.candidates),
        "completed_count": sum(r.status == "complete" for r in run.candidates),
        "failed_count": sum(r.status == "failed" for r in run.candidates),
        "skipped_count": len(run.reused_candidate_keys), "reused_count": len(run.reused_candidate_keys),
    })


def _run_candidate(
    spec: SweepSpec, request: CandidateRecord, store: "FilesystemArtifactStore",
) -> CandidateRecord:
    try:
        record = _evaluate_candidate(
            hull=Hull(**request.attempted_hull), spec=spec, index=request.candidate_index,
            candidate_key=request.candidate_key, params=request.parameters,
            attempted=request.attempted_hull, out=store.run_dir, store=store,
        )
    except (ValidationError, ValueError) as exc:
        record = request.model_copy(update={
            "status": "failed", "evaluator_settings": spec.evaluators.model_dump(mode="json"),
            "evaluator_versions": {"sweep_schema": "1"}, "error": str(exc),
        })
    store.put_json(
        "candidate_record", record, candidate_key=record.candidate_key,
        canonical_path=store.run_dir / "candidates" / f"{record.candidate_key}.record.json",
    )
    return record



def _index_row_for_candidate(record: CandidateRecord) -> dict[str, Any]:
    """Build a SQLite-index row payload from a CandidateRecord."""

    metrics: dict[str, float] = {}
    for key, value in record.summary.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            metrics[key] = float(value)
    return {
        "candidate_key": record.candidate_key,
        "status": record.status,
        "hull_design_hash": _try_design_hash(record),
        "hull_record_hash": record.hull_hash,
        "metrics": metrics,
    }


def _try_design_hash(record: CandidateRecord) -> str | None:
    try:
        hull = Hull.model_validate(record.attempted_hull)
    except (ValidationError, ValueError):
        return None
    return hull.design_hash()


def _evaluate_candidate(
    hull: Hull,
    spec: SweepSpec,
    index: int,
    candidate_key: str,
    params: dict[str, Any],
    attempted: dict[str, Any],
    out: Path,
    store: Any | None = None,
) -> CandidateRecord:
    candidates_dir = out / "candidates"
    hull_path = candidates_dir / f"{candidate_key}.hull.json"
    eval_path = candidates_dir / f"{candidate_key}.eval.json"

    from kayakgen.eval.contract import EvaluationContext
    from kayakgen.services.evaluation import evaluate_with_context
    supplied_load = dict(spec.evaluators.stability_load_case)
    if spec.evaluators.water_density_kg_m3 is not None:
        supplied_load["seawater_density_kg_m3"] = spec.evaluators.water_density_kg_m3
    load_case = LoadCase.model_validate(supplied_load)
    context = EvaluationContext.for_hull(
        hull, load_case=load_case,
        input_origin="supplied" if supplied_load else "legacy_default",
        equilibrium=spec.evaluators.stability and spec.evaluators.stability_equilibrium,
        equilibrium_tolerance_kg=spec.evaluators.stability_tolerance_kg,
        moment_tolerance_kg_m=spec.evaluators.stability_moment_tolerance_kg_m,
        n_stations=spec.evaluators.n_stations, n_depths=spec.evaluators.n_depths,
        n_theta=spec.evaluators.n_theta, speeds_knots=spec.evaluators.speeds_knots,
        numerical_relative_tolerance=spec.evaluators.numerical_relative_tolerance,
        hydrostatic_stations=spec.evaluators.hydrostatic_stations,
        kinematic_viscosity_m2_s=spec.evaluators.kinematic_viscosity_m2_s,
    )
    computed = evaluate_with_context(hull, context, include_resistance=spec.evaluators.resistance)
    hydro = computed.hydrostatics
    resistance = computed.resistance
    stability = computed.stability if spec.evaluators.stability else None
    design_validity = evaluate_design_validity(
        hull, cp=hydro.Cp_actual, displaced_mass_kg=hydro.displaced_mass_kg, surface=("sweep",),
    )
    turning = None
    if spec.evaluators.turning_metrics:
        turning = evaluate_turning_metrics(
            hull, heel_deg=spec.evaluators.turning_metrics_heel_deg
        )
    evaluation = EvaluationResult(
        context=computed.context,
        hull_hash=hull.hash(),
        hydrostatics=hydro,
        resistance=resistance,
        stability=stability,
        turning_metrics=turning,
        design_validity=design_validity,
    )
    save_hull(hull, hull_path)
    save_evaluation(evaluation, eval_path)
    if store is not None:
        store.put_file("hull_json", hull_path, candidate_key=candidate_key)
        store.put_file("eval_result_json", eval_path, candidate_key=candidate_key)

    artifacts = {
        "hull": str(hull_path.relative_to(out)),
        "evaluation": str(eval_path.relative_to(out)),
    }
    warnings: list[str] = []
    if spec.evaluators.mesh_diagnostics:
        from kayakgen.eval.mesh_diagnostics import diagnose_mesh

        mesh_path = candidates_dir / f"{candidate_key}.mesh.json"
        mesh = diagnose_mesh(hull)
        write_text_atomic(mesh_path, mesh.model_dump_json(indent=2))
        if store is not None:
            store.put_file("mesh_quality_json", mesh_path, candidate_key=candidate_key)
        artifacts["mesh_diagnostics"] = str(mesh_path.relative_to(out))
        warnings.extend(mesh.warnings)

    stl_artifacts: StlArtifactSet | None = None
    if spec.evaluators.stl:
        candidate_dir = candidates_dir / candidate_key
        stl_artifacts = write_candidate_stl(hull, candidate_dir, out)
        artifacts["stl_hull"] = stl_artifacts.hull.path
        artifacts["stl_deck"] = stl_artifacts.deck.path
        if store is not None:
            store.put_file(
                "hull_stl",
                out / stl_artifacts.hull.path,
                candidate_key=candidate_key,
            )
            store.put_file(
                "deck_stl",
                out / stl_artifacts.deck.path,
                candidate_key=candidate_key,
            )

    high_angle_gz_artifact: HighAngleGzArtifact | None = None
    if spec.evaluators.high_angle_gz:
        heel_grid = (
            list(spec.evaluators.high_angle_gz_heel_grid_deg)
            if spec.evaluators.high_angle_gz_heel_grid_deg is not None
            else [float(angle) for angle in DEFAULT_GZ_HEEL_GRID_DEG]
        )
        gz_load_case = load_case
        block = build_high_angle_gz_block(hull, gz_load_case, heel_grid_deg=heel_grid)
        candidate_dir = candidates_dir / candidate_key
        high_angle_gz_artifact = write_candidate_high_angle_gz(block, candidate_dir, out)
        artifacts["high_angle_gz"] = high_angle_gz_artifact.path
        if store is not None:
            store.put_file(
                "high_angle_gz_artifact",
                out / high_angle_gz_artifact.path,
                candidate_key=candidate_key,
            )

    summary = {
        "displaced_mass_kg": hydro.displaced_mass_kg,
        "wetted_surface_m2": hydro.wetted_surface_m2,
        "GM0_m": hydro.GM0_m,
        "Cp_actual": hydro.Cp_actual,
    }
    if resistance is not None:
        summary["resistance_operating_context"] = evaluation.context.operating_comparison_inputs()
        summary["resistance_numerical_quality"] = resistance.metadata.numerical_quality.model_dump(mode="json")
        summary["resistance_use"] = ",".join(resistance.metadata.accepted_use)
        summary["resistance_claim_state"] = resistance.metadata.claim_state
        summary["resistance_accepted_uses"] = ",".join(resistance.metadata.accepted_uses)
        summary["resistance_warnings"] = ",".join(resistance.metadata.warnings)
        summary["Rt_N_last"] = resistance.Rt_N[-1] if resistance.Rt_N else None
    if stability is not None:
        summary["stability_method"] = stability.method
        summary["stability_status"] = stability.status
        summary["displacement_error_kg"] = stability.displacement_error_kg
        summary["initial_GM0_m"] = stability.initial_GM0_m
        summary["trim_angle_deg"] = stability.trim_angle_deg
        summary["moment_error_kg_m"] = stability.moment_error_kg_m
        summary["equilibrium_iterations"] = stability.equilibrium_iterations
        summary["stability_warnings"] = ",".join(stability.warnings)
    if turning is not None:
        # Surface only the numeric outputs (no embedded record). The
        # four metrics are registered as ``display_only`` in
        # OBJECTIVE_METADATA per RFC 0053; they will appear in
        # summary.csv via the registry pickup (turning_metrics are
        # display-only and therefore *not* eligible Pareto/search
        # objectives, but are emitted as candidate summary columns).
        summary["turning.edged_waterline_length_m"] = turning.edged_waterline_length_m
        summary["turning.upright_waterline_length_m"] = turning.upright_waterline_length_m
        summary["turning.lateral_plane_shift_m"] = turning.lateral_plane_shift_m
        summary["turning.rocker_weighted_maneuverability_signal"] = (
            turning.rocker_weighted_maneuverability_signal
        )

    return CandidateRecord(
        candidate_index=index,
        candidate_key=candidate_key,
        parameters=params,
        attempted_hull=attempted,
        status="complete",
        hull_hash=hull.hash(),
        artifacts=artifacts,
        evaluator_settings=spec.evaluators.model_dump(mode="json"),
        evaluator_versions={
            "sweep_schema": "1",
            "hull_schema": hull.schema_version,
            "resistance_model": resistance.metadata.model_family if resistance else "disabled",
            "stability_model": stability.method if stability else "disabled",
        },
        summary=summary,
        warnings=warnings,
        design_validity=design_validity,
        design_warning_count=design_validity.warning_count,
        design_unsupported_count=design_validity.unsupported_count,
        stl_artifacts=stl_artifacts,
        high_angle_gz_artifact=high_angle_gz_artifact,
    )


#: Non-registry summary columns that the sweep CSV has always carried for
#: parity with prior runs. Display-only high-angle GZ keys are kept out of the
#: header explicitly per RFC 0043 stage 3.
_LEGACY_SUMMARY_COLUMNS: tuple[str, ...] = (
    "displaced_mass_kg",
    "wetted_surface_m2",
    "GM0_m",
    "Cp_actual",
    "Rt_N_last",
    "stability_method",
    "stability_status",
    "displacement_error_kg",
    "initial_GM0_m",
    "trim_angle_deg",
    "moment_error_kg_m",
    "equilibrium_iterations",
)


def _registry_summary_columns(records: list[CandidateRecord]) -> list[str]:
    """Return any registry-known metric keys present on at least one record.

    Display-only high-angle GZ keys are filtered out so callers that register a
    display-only metric do not accidentally promote it into the CSV header.
    Other ``role="display_only"`` registry entries (e.g. RFC 0053 turning
    metrics) are admitted when at least one record's ``summary`` carries the
    key — display-only just means they cannot become Pareto/search
    objectives, not that they cannot appear in ``summary.csv``.
    The legacy column list is the seed; newly registered metrics with a hit on
    any record's ``summary`` are appended in registry declaration order so the
    column layout stays stable.
    """

    seen: set[str] = set(_LEGACY_SUMMARY_COLUMNS)
    extra: list[str] = []
    for metric, metadata in OBJECTIVE_METADATA.items():
        if metric in seen:
            continue
        if metric in HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS:
            continue
        if metadata.role == "display_only" and metadata.source_evaluator == "high_angle_gz":
            continue
        if not any(metric in record.summary for record in records):
            continue
        extra.append(metric)
        seen.add(metric)
    return [*_LEGACY_SUMMARY_COLUMNS, *extra]


def _write_summary(path: Path, records: list[CandidateRecord]) -> None:
    parameter_names = sorted({key for record in records for key in record.parameters})
    metric_columns = _registry_summary_columns(records)
    fieldnames = [
        "candidate_index",
        "candidate_key",
        "status",
        "hull_hash",
        "error",
        *[f"param_{name}" for name in parameter_names],
        *metric_columns,
    ]
    with io.StringIO(newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = {
                "candidate_index": record.candidate_index,
                "candidate_key": record.candidate_key,
                "status": record.status,
                "hull_hash": record.hull_hash or "",
                "error": record.error or "",
            }
            for name in parameter_names:
                row[f"param_{name}"] = record.parameters.get(name, "")
            for key in metric_columns:
                row[key] = record.summary.get(key, "")
            writer.writerow(row)
        write_text_atomic(path, fh.getvalue(), newline="")


def _write_failures(path: Path, failures: list[CandidateRecord]) -> None:
    write_text_atomic(path, "".join(failure.model_dump_json() + "\n" for failure in failures))


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
