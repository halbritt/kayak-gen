"""Comparison reports over deterministic sweep runs."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from kayakgen.eval.contract import EvaluationResult
from kayakgen.search.pareto import CandidatePoint, Direction, Objective, pareto_front
from kayakgen.search.sweep import CandidateRecord, SweepRunRecord

ReportKind = Literal["pareto_frontier", "exploratory_frontier"]

DEFAULT_OBJECTIVE_CANDIDATES: tuple[Objective, ...] = (
    Objective(metric="GM0_m", direction="max"),
    Objective(metric="displacement_error_kg", direction="min"),
    Objective(metric="mesh_problem_count", direction="min"),
)


class CandidateSummary(BaseModel):
    """Serializable comparison summary for one sweep candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_index: int
    candidate_key: str
    status: str
    hull_hash: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    objective_values: dict[str, float | None] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    artifacts: dict[str, str] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)


class ComparisonReport(BaseModel):
    """Machine-readable Pareto comparison report."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    run_name: str
    spec_hash: str
    report_kind: ReportKind
    objectives: list[Objective]
    pareto_front_keys: list[str]
    candidate_summaries: list[CandidateSummary]
    warnings: list[str] = Field(default_factory=list)


def parse_objective(value: str) -> Objective:
    """Parse ``metric:direction`` CLI syntax."""
    metric, sep, direction = value.partition(":")
    if not sep or direction not in ("min", "max"):
        raise ValueError("objective must be formatted as metric:min or metric:max")
    return Objective(metric=metric, direction=cast(Direction, direction))


def load_sweep_run(run_dir: str | Path) -> SweepRunRecord:
    """Load a sweep run from ``run.json``."""
    run_path = Path(run_dir) / "run.json"
    if not run_path.exists():
        raise ValueError(f"missing sweep run record: {run_path}")
    return SweepRunRecord.model_validate_json(run_path.read_text())


def build_comparison_report(
    run_dir: str | Path,
    objectives: list[Objective] | None = None,
) -> ComparisonReport:
    """Build a comparison report from a sweep run directory."""
    root = Path(run_dir)
    run = load_sweep_run(root)
    summaries = [_candidate_summary(root, record) for record in run.candidates]

    selected_objectives = (
        _normalize_objectives(objectives)
        if objectives is not None
        else _default_objectives(summaries)
    )
    report_kind: ReportKind = (
        "exploratory_frontier"
        if any(_is_resistance_metric(objective.metric) for objective in selected_objectives)
        else "pareto_frontier"
    )

    points = [
        CandidatePoint(
            id=summary.candidate_key,
            metrics=summary.metrics,
            warnings=tuple(summary.warnings),
            provenance=summary.provenance,
        )
        for summary in summaries
        if summary.status == "complete"
    ]
    front = pareto_front(points, selected_objectives)
    warnings_by_key = {point.id: list(point.warnings) for point in front}

    candidate_summaries: list[CandidateSummary] = []
    for summary in summaries:
        objective_values = {
            objective.metric: summary.metrics.get(objective.metric)
            for objective in selected_objectives
        }
        warnings = list(summary.warnings)
        if summary.status == "complete":
            warnings = warnings_by_key.get(
                summary.candidate_key,
                _objective_warnings(summary.metrics, summary.provenance, selected_objectives, warnings),
            )
        else:
            _append_once(warnings, f"candidate status not eligible for pareto: {summary.status}")
        candidate_summaries.append(
            summary.model_copy(
                update={
                    "objective_values": objective_values,
                    "warnings": warnings,
                }
            )
        )

    report_warnings: list[str] = []
    if not selected_objectives:
        report_warnings.append("no default objectives available")
    for objective in selected_objectives:
        if not any(
            summary.status == "complete" and objective.metric in summary.metrics
            for summary in summaries
        ):
            report_warnings.append(f"unsupported objective: {objective.metric}")
    if report_kind == "exploratory_frontier":
        report_warnings.append("exploratory frontier includes resistance objective")

    return ComparisonReport(
        run_name=run.name,
        spec_hash=run.spec_hash,
        report_kind=report_kind,
        objectives=selected_objectives,
        pareto_front_keys=[point.id for point in front],
        candidate_summaries=candidate_summaries,
        warnings=report_warnings,
    )


def write_comparison_report(
    run_dir: str | Path,
    out_path: str | Path,
    objectives: list[Objective] | None = None,
) -> ComparisonReport:
    """Build and write a comparison report."""
    report = build_comparison_report(run_dir, objectives=objectives)
    Path(out_path).write_text(report.model_dump_json(indent=2))
    return report


def _candidate_summary(root: Path, record: CandidateRecord) -> CandidateSummary:
    metrics = {
        key: float(value)
        for key, value in record.summary.items()
        if isinstance(value, (int, float)) and math.isfinite(float(value))
    }
    warnings = list(record.warnings)
    provenance: dict[str, Any] = {}

    if record.error:
        _append_once(warnings, "candidate error recorded")

    evaluation = _load_evaluation(root, record)
    if evaluation is not None and evaluation.resistance is not None:
        resistance = evaluation.resistance
        accepted = (
            resistance.metadata.calibration_status != "uncalibrated"
            and "final_prediction" in resistance.metadata.accepted_use
        )
        provenance["Rt_N_last"] = {
            "accepted_use": accepted,
            "accepted_use_values": resistance.metadata.accepted_use,
            "calibration_status": resistance.metadata.calibration_status,
            "model_family": resistance.metadata.model_family,
        }
        for warning in resistance.metadata.warnings:
            _append_once(warnings, f"resistance: {warning}")
    elif "resistance_use" in record.summary:
        provenance["Rt_N_last"] = {
            "accepted_use": False,
            "accepted_use_values": str(record.summary.get("resistance_use", "")).split(","),
            "calibration_status": "unknown",
        }

    if "mesh_diagnostics" in record.artifacts:
        mesh_path = root / record.artifacts["mesh_diagnostics"]
        if mesh_path.exists():
            mesh = json.loads(mesh_path.read_text())
            metrics["mesh_problem_count"] = float(
                sum(
                    int(mesh.get(key, 0))
                    for key in (
                        "raw_boundary_edges",
                        "raw_nonmanifold_edges",
                        "welded_boundary_edges",
                        "welded_nonmanifold_edges",
                        "degenerate_faces",
                        "nonfinite_vertices",
                        "nonfinite_faces",
                    )
                )
            )

    return CandidateSummary(
        candidate_index=record.candidate_index,
        candidate_key=record.candidate_key,
        status=record.status,
        hull_hash=record.hull_hash,
        parameters=record.parameters,
        metrics=metrics,
        warnings=warnings,
        error=record.error,
        artifacts=record.artifacts,
        provenance=provenance,
    )


def _load_evaluation(root: Path, record: CandidateRecord) -> EvaluationResult | None:
    eval_rel = record.artifacts.get("evaluation")
    if not eval_rel:
        return None
    eval_path = root / eval_rel
    if not eval_path.exists():
        return None
    return EvaluationResult.model_validate_json(eval_path.read_text())


def _default_objectives(summaries: list[CandidateSummary]) -> list[Objective]:
    available = {
        metric
        for summary in summaries
        if summary.status == "complete"
        for metric in summary.metrics
    }
    return [
        objective
        for objective in DEFAULT_OBJECTIVE_CANDIDATES
        if objective.metric in available
    ]


def _normalize_objectives(objectives: list[Objective]) -> list[Objective]:
    normalized: list[Objective] = []
    for objective in objectives:
        if _is_resistance_metric(objective.metric) and not objective.accepted_use_required:
            normalized.append(objective.model_copy(update={"accepted_use_required": True}))
        else:
            normalized.append(objective)
    return normalized


def _objective_warnings(
    metrics: dict[str, float],
    provenance: dict[str, Any],
    objectives: list[Objective],
    existing: list[str],
) -> list[str]:
    warnings = list(existing)
    for objective in objectives:
        if objective.metric not in metrics:
            _append_once(warnings, f"missing metric: {objective.metric}")
        elif objective.accepted_use_required and not _has_accepted_use(provenance, objective.metric):
            _append_once(warnings, f"metric requires accepted-use provenance: {objective.metric}")
    return warnings


def _has_accepted_use(provenance: dict[str, Any], metric: str) -> bool:
    metric_provenance = provenance.get(metric)
    return isinstance(metric_provenance, dict) and metric_provenance.get("accepted_use") is True


def _is_resistance_metric(metric: str) -> bool:
    normalized = metric.lower()
    return normalized.startswith("rt_") or "resistance" in normalized


def _append_once(warnings: list[str], warning: str) -> None:
    if warning not in warnings:
        warnings.append(warning)
