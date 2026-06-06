"""Comparison reports over deterministic sweep runs."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kayakgen.eval.claims import (
    claim_allows_calibrated_prediction,
    claim_allows_final_design_fitness,
    claim_metadata_from_fields,
)
from kayakgen.eval.contract import EvaluationResult
from kayakgen.model.validity import DesignValidityReport
from kayakgen.search.objectives import (
    OBJECTIVE_METADATA,
    ObjectiveMetadata,
    default_objectives,
    objective_metadata_for,
    objective_requires_accepted_use,
)
from kayakgen.search.pareto import (
    CandidatePoint,
    Direction,
    Objective,
    ensure_objectives_claim_admissible_for_search,
    ensure_objectives_not_high_angle_gz,
    pareto_front,
)
from kayakgen.search.sweep import CandidateRecord, SweepRunRecord

ReportKind = Literal["pareto_frontier", "exploratory_frontier"]

DEFAULT_OBJECTIVE_CANDIDATES: tuple[Objective, ...] = default_objectives()


class HighAngleGzDisplay(BaseModel):
    """Display-only mirror of a candidate's ``high_angle_gz.json`` artifact.

    Per RFC 0043 stage 3 (workflow 0052 staged surfacing), these values are
    rendered adjacent to body/load/trim provenance and warnings, but are NOT
    selectable as Pareto objectives. The shape stays additive so the report
    remains backwards-compatible when no candidate has the artifact.
    """

    model_config = ConfigDict(extra="forbid")

    available: bool
    body_profile: str
    result_semantics: str
    method: str | None = None
    body_ref: str | None = None
    body_type: str | None = None
    body_diagnostic_ref: str | None = None
    heel_grid_deg: list[float] = Field(default_factory=list)
    max_gz_m: float | None = None
    heel_at_max_gz_deg: float | None = None
    range_positive_stability_deg: float | None = None
    warnings: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unavailable_reason: dict[str, Any] | None = None
    artifact_path: str | None = None


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
    design_validity: DesignValidityReport = Field(default_factory=DesignValidityReport)
    design_warning_count: int = 0
    design_unsupported_count: int = 0
    error: str | None = None
    artifacts: dict[str, str] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    high_angle_gz_display: HighAngleGzDisplay | None = None

    @model_validator(mode="after")
    def _sync_design_validity_counts(self) -> "CandidateSummary":
        self.design_warning_count = self.design_validity.warning_count
        self.design_unsupported_count = self.design_validity.unsupported_count
        return self


class PairwiseNote(BaseModel):
    """RFC 0052 pairwise comparison advisory.

    Emitted when two Pareto-front candidates differ by less than the metric
    registry's ``within_evaluator_noise_threshold`` on every default-objective
    metric. The advisory is a *read-model* enhancement — it never gates
    frontier eligibility — and stays absent when no pair triggers it.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    left_key: str
    right_key: str
    within_evaluator_noise: bool = True
    metric_differences: dict[str, float] = Field(default_factory=dict)
    metric_thresholds: dict[str, float] = Field(default_factory=dict)


class ComparisonReport(BaseModel):
    """Machine-readable Pareto comparison report."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    run_name: str
    spec_hash: str
    report_kind: ReportKind
    objectives: list[Objective]
    objective_metadata: dict[str, ObjectiveMetadata] = Field(default_factory=dict)
    pareto_front_keys: list[str]
    candidate_summaries: list[CandidateSummary]
    warnings: list[str] = Field(default_factory=list)
    design_validity: dict[str, DesignValidityReport] = Field(default_factory=dict)
    design_warning_count: int = 0
    design_unsupported_count: int = 0
    # Present (true) when at least one candidate has a high-angle GZ display
    # artifact. Omitted (false) when no candidates do — keeps the report shape
    # backwards-compatible by absence. Display-only per RFC 0043 stage 3.
    high_angle_gz_columns: bool = False
    # RFC 0052: pairwise within-evaluator-noise advisories. Empty list when no
    # pareto pair satisfies the registry's tolerance map; the field stays in
    # the schema (default ``[]``) so consumers can iterate unconditionally.
    pairwise_notes: list[PairwiseNote] = Field(default_factory=list)

    @model_validator(mode="after")
    def _sync_design_validity_counts(self) -> "ComparisonReport":
        if self.candidate_summaries:
            self.design_warning_count = sum(
                summary.design_warning_count for summary in self.candidate_summaries
            )
            self.design_unsupported_count = sum(
                summary.design_unsupported_count for summary in self.candidate_summaries
            )
        else:
            self.design_warning_count = sum(
                report.warning_count for report in self.design_validity.values()
            )
            self.design_unsupported_count = sum(
                report.unsupported_count for report in self.design_validity.values()
            )
        return self


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
    *,
    explicit_exploratory: bool = False,
) -> ComparisonReport:
    """Build a comparison report from a sweep run directory.

    Per D048 / RFC 0044, objectives whose claim state is ``raw_unvalidated``
    or ``uncalibrated_comparative`` are refused with
    :data:`~kayakgen.search.pareto.SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN`
    unless ``explicit_exploratory=True``. The labeled ``exploratory_frontier``
    report (warnings + provenance annotations) survives behind that opt-in;
    default conservative objectives need no flag and are unchanged.
    """
    root = Path(run_dir)
    run = load_sweep_run(root)
    summaries = [_candidate_summary(root, record) for record in run.candidates]

    if objectives is not None:
        # Refuse high-angle GZ display-only metrics as objectives BEFORE any
        # work happens so the structured rejection is the only outcome.
        ensure_objectives_not_high_angle_gz(objectives)

    selected_objectives = (
        _normalize_objectives(objectives)
        if objectives is not None
        else _default_objectives(summaries)
    )
    # Defense-in-depth: defaults must never include a display-only key, and
    # per D048 claim-inadmissible objectives REFUSE without the exploratory
    # opt-in. The admissibility gate re-runs the display-only refusal first,
    # so the RFC 0043 token still wins for high-angle keys in both modes.
    ensure_objectives_claim_admissible_for_search(
        selected_objectives, explicit_exploratory=explicit_exploratory
    )
    report_kind: ReportKind = (
        "exploratory_frontier"
        if any(_is_claim_gated_metric(objective.metric) for objective in selected_objectives)
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
    if any(_is_resistance_metric(objective.metric) for objective in selected_objectives):
        report_warnings.append("exploratory frontier includes resistance objective")
    if any(_is_design_fitness_metric(objective.metric) for objective in selected_objectives):
        report_warnings.append("exploratory frontier includes final design-fitness objective")

    objective_metadata = {
        objective.metric: objective_metadata_for(objective)
        for objective in selected_objectives
    }

    high_angle_gz_columns = any(
        summary.high_angle_gz_display is not None for summary in candidate_summaries
    )

    pairwise_notes = _pairwise_noise_notes(
        candidate_summaries,
        pareto_keys=[point.id for point in front],
        objectives=selected_objectives,
    )

    return ComparisonReport(
        run_name=run.name,
        spec_hash=run.spec_hash,
        report_kind=report_kind,
        objectives=selected_objectives,
        objective_metadata=objective_metadata,
        pareto_front_keys=[point.id for point in front],
        candidate_summaries=candidate_summaries,
        warnings=report_warnings,
        design_validity={
            summary.candidate_key: summary.design_validity
            for summary in candidate_summaries
            if summary.design_validity.findings
        },
        design_warning_count=sum(
            summary.design_warning_count for summary in candidate_summaries
        ),
        design_unsupported_count=sum(
            summary.design_unsupported_count for summary in candidate_summaries
        ),
        high_angle_gz_columns=high_angle_gz_columns,
        pairwise_notes=pairwise_notes,
    )


def _pairwise_noise_notes(
    summaries: list[CandidateSummary],
    *,
    pareto_keys: list[str],
    objectives: list[Objective],
) -> list[PairwiseNote]:
    """RFC 0052 advisory: flag Pareto-front pairs within evaluator noise.

    For each unordered pair of Pareto-front candidates, gather every
    default-objective metric that has a registered
    ``within_evaluator_noise_threshold``; the pair is flagged when every such
    metric is present on both rows AND every pairwise difference is strictly
    less than the registered threshold. Empty when no such pair exists; the
    report consumer can iterate unconditionally.
    """

    if len(pareto_keys) < 2:
        return []
    summaries_by_key = {summary.candidate_key: summary for summary in summaries}
    tolerance_metrics: list[tuple[str, float]] = []
    for objective in objectives:
        registry_entry = OBJECTIVE_METADATA.get(objective.metric)
        if registry_entry is None:
            continue
        threshold = registry_entry.within_evaluator_noise_threshold
        if threshold is None or threshold <= 0:
            continue
        tolerance_metrics.append((objective.metric, float(threshold)))
    if not tolerance_metrics:
        return []

    notes: list[PairwiseNote] = []
    for i, left_key in enumerate(pareto_keys):
        for right_key in pareto_keys[i + 1 :]:
            left = summaries_by_key.get(left_key)
            right = summaries_by_key.get(right_key)
            if left is None or right is None:
                continue
            differences: dict[str, float] = {}
            thresholds: dict[str, float] = {}
            within_noise = True
            for metric, threshold in tolerance_metrics:
                left_value = left.metrics.get(metric)
                right_value = right.metrics.get(metric)
                if left_value is None or right_value is None:
                    within_noise = False
                    break
                if not (math.isfinite(left_value) and math.isfinite(right_value)):
                    within_noise = False
                    break
                difference = abs(float(left_value) - float(right_value))
                if difference >= threshold:
                    within_noise = False
                    break
                differences[metric] = difference
                thresholds[metric] = threshold
            if not within_noise or not differences:
                continue
            notes.append(
                PairwiseNote(
                    left_key=left_key,
                    right_key=right_key,
                    within_evaluator_noise=True,
                    metric_differences=differences,
                    metric_thresholds=thresholds,
                )
            )
    return notes


def write_comparison_report(
    run_dir: str | Path,
    out_path: str | Path,
    objectives: list[Objective] | None = None,
    *,
    explicit_exploratory: bool = False,
) -> ComparisonReport:
    """Build and write a comparison report."""
    report = build_comparison_report(
        run_dir, objectives=objectives, explicit_exploratory=explicit_exploratory
    )
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
    design_validity = record.design_validity

    if record.error:
        _append_once(warnings, "candidate error recorded")

    evaluation = _load_evaluation(root, record)
    if evaluation is not None and not design_validity.findings:
        design_validity = evaluation.design_validity
    resistance_claim = None
    if evaluation is not None and evaluation.resistance is not None:
        resistance = evaluation.resistance
        resistance_claim = claim_metadata_from_fields(resistance.metadata)
        accepted = claim_allows_calibrated_prediction(resistance_claim)
        provenance["Rt_N_last"] = {
            "accepted_use": accepted,
            "accepted_use_values": resistance.metadata.accepted_uses,
            "claim_state": resistance_claim.claim_state,
            "accepted_uses": resistance_claim.accepted_uses,
            "calibration_fixture_ids": resistance_claim.calibration_fixture_ids,
            "validation_fixture_ids": resistance_claim.validation_fixture_ids,
            "model_version": resistance_claim.model_version,
            "fit_status": resistance_claim.fit_status,
            "fit_metrics": resistance_claim.fit_metrics,
            "validity_envelope": resistance_claim.validity_envelope,
            "calibration_status": resistance.metadata.calibration_status,
            "model_family": resistance.metadata.model_family,
        }
        for warning in resistance.metadata.warnings:
            _append_once(warnings, f"resistance: {warning}")
    elif "resistance_use" in record.summary:
        provenance["Rt_N_last"] = {
            "accepted_use": False,
            "accepted_use_values": str(record.summary.get("resistance_use", "")).split(","),
            "claim_state": record.summary.get("resistance_claim_state", "unknown"),
            "calibration_status": "unknown",
        }
    if "design_fitness" in record.summary:
        provenance["design_fitness"] = {
            "accepted_use": claim_allows_final_design_fitness(resistance_claim),
            "claim_state": (
                resistance_claim.claim_state
                if resistance_claim is not None
                else "not_implemented"
            ),
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

    high_angle_gz_display = _load_high_angle_gz_display(root, record)

    return CandidateSummary(
        candidate_index=record.candidate_index,
        candidate_key=record.candidate_key,
        status=record.status,
        hull_hash=record.hull_hash,
        parameters=record.parameters,
        metrics=metrics,
        warnings=warnings,
        design_validity=design_validity,
        design_warning_count=design_validity.warning_count,
        design_unsupported_count=design_validity.unsupported_count,
        error=record.error,
        artifacts=record.artifacts,
        provenance=provenance,
        high_angle_gz_display=high_angle_gz_display,
    )


def _load_high_angle_gz_display(
    root: Path, record: CandidateRecord
) -> HighAngleGzDisplay | None:
    """Read ``high_angle_gz.json`` (if present) into a display-only mirror.

    Per RFC 0043 stage 3 / workflow 0052 staged surfacing, the comparison
    report surfaces high-angle GZ values plus body/load/trim provenance and
    warnings ADJACENT to each row, but never as Pareto objectives. Returns
    ``None`` when no artifact reference exists or the file is missing so the
    report stays additive.
    """

    artifact_ref: str | None = None
    if record.high_angle_gz_artifact is not None:
        artifact_ref = record.high_angle_gz_artifact.path
    elif "high_angle_gz" in record.artifacts:
        artifact_ref = record.artifacts["high_angle_gz"]

    if not artifact_ref:
        return None

    artifact_path = root / artifact_ref
    if not artifact_path.exists():
        return None

    try:
        block = json.loads(artifact_path.read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(block, dict):
        return None

    summary = block.get("summary") if isinstance(block.get("summary"), dict) else None
    unavailable_reason = (
        block.get("unavailable_reason")
        if isinstance(block.get("unavailable_reason"), dict)
        else None
    )
    warnings_raw = block.get("warnings") or []
    assumptions_raw = block.get("assumptions") or []
    heel_grid_raw = block.get("heel_grid_deg") or []

    return HighAngleGzDisplay(
        available=bool(block.get("available", False)),
        body_profile=str(block.get("body_profile", "")),
        result_semantics=str(block.get("result_semantics", "")),
        method=_optional_str(block.get("method")),
        body_ref=_optional_str(block.get("body_ref")),
        body_type=_optional_str(block.get("body_type")),
        body_diagnostic_ref=_optional_str(block.get("body_diagnostic_ref")),
        heel_grid_deg=[float(angle) for angle in heel_grid_raw if isinstance(angle, (int, float))],
        max_gz_m=_optional_float(summary.get("max_gz")) if summary else None,
        heel_at_max_gz_deg=_optional_float(summary.get("heel_at_max_gz")) if summary else None,
        range_positive_stability_deg=(
            _optional_float(summary.get("range_positive_stability_deg")) if summary else None
        ),
        warnings=[str(warning) for warning in warnings_raw],
        assumptions=[str(assumption) for assumption in assumptions_raw],
        unavailable_reason=unavailable_reason,
        artifact_path=artifact_ref,
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


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
        if (
            (_is_claim_gated_metric(objective.metric) or objective_requires_accepted_use(objective))
            and not objective.accepted_use_required
        ):
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


def _is_design_fitness_metric(metric: str) -> bool:
    return "fitness" in metric.lower()


def _is_claim_gated_metric(metric: str) -> bool:
    return _is_resistance_metric(metric) or _is_design_fitness_metric(metric)


def _append_once(warnings: list[str], warning: str) -> None:
    if warning not in warnings:
        warnings.append(warning)
