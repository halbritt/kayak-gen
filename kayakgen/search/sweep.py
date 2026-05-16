"""Deterministic sweep specs and run records."""

from __future__ import annotations

import csv
import hashlib
import json
from itertools import product
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from kayakgen.eval.contract import EvaluationResult
from kayakgen.eval.high_angle_gz import build_high_angle_gz_block
from kayakgen.eval.contract import LoadCase
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.resistance import resistance_curve
from kayakgen.eval.stability import DEFAULT_GZ_HEEL_GRID_DEG, evaluate_equilibrium_stability, evaluate_initial_stability
from kayakgen.eval.sweep_artifacts import (
    HighAngleGzArtifact,
    StlArtifactSet,
    write_candidate_high_angle_gz,
    write_candidate_stl,
)
from kayakgen.io.json import save_evaluation, save_hull
from kayakgen.model.hull import Hull
from kayakgen.model.validity import DesignValidityReport, evaluate_design_validity

ParameterKind = Literal["values", "linspace"]
CandidateStatus = Literal["pending", "complete", "failed", "skipped", "constraint_failed"]


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
    stability: bool = False
    stability_equilibrium: bool = False
    stability_load_case: dict[str, Any] = Field(default_factory=dict)
    stability_tolerance_kg: float = Field(default=1.0, gt=0)
    stability_moment_tolerance_kg_m: float | None = Field(default=None, gt=0)
    mesh_diagnostics: bool = False
    stl: bool = False
    high_angle_gz: bool = False
    high_angle_gz_heel_grid_deg: list[float] | None = None


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


def run_sweep(spec: SweepSpec, out_dir: str | Path, resume: bool = False) -> SweepRunRecord:
    """Run a deterministic sweep and write candidate/run artifacts."""
    out = Path(out_dir)
    candidates_dir = out / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    (out / "spec.json").write_text(spec.model_dump_json(indent=2))

    records: list[CandidateRecord] = []
    failures: list[CandidateRecord] = []
    for index, candidate_key, params, attempted in expand_candidates(spec):
        record_path = candidates_dir / f"{candidate_key}.record.json"
        if resume and record_path.exists():
            prior = CandidateRecord.model_validate_json(record_path.read_text())
            if prior.status == "complete":
                records.append(prior.model_copy(update={"status": "skipped"}))
                continue
            if prior.status == "pending":
                records.append(prior)
                continue

        try:
            hull = Hull(**attempted)
            record = _evaluate_candidate(
                hull=hull,
                spec=spec,
                index=index,
                candidate_key=candidate_key,
                params=params,
                attempted=attempted,
                out=out,
            )
        except (ValidationError, ValueError) as exc:
            record = CandidateRecord(
                candidate_index=index,
                candidate_key=candidate_key,
                parameters=params,
                attempted_hull=attempted,
                status="failed",
                evaluator_settings=spec.evaluators.model_dump(mode="json"),
                evaluator_versions={"sweep_schema": "1"},
                error=str(exc),
            )
            failures.append(record)

        record_path.write_text(record.model_dump_json(indent=2))
        records.append(record)

    run = SweepRunRecord(
        name=spec.name,
        spec_hash=spec.spec_hash(),
        candidate_count=len(records),
        pending_count=sum(1 for record in records if record.status == "pending"),
        completed_count=sum(1 for record in records if record.status == "complete"),
        failed_count=sum(1 for record in records if record.status == "failed"),
        skipped_count=sum(1 for record in records if record.status == "skipped"),
        candidates=records,
    )
    (out / "run.json").write_text(run.model_dump_json(indent=2))
    _write_summary(out / "summary.csv", records)
    _write_failures(out / "failures.jsonl", failures or [r for r in records if r.status == "failed"])
    return run


def _evaluate_candidate(
    hull: Hull,
    spec: SweepSpec,
    index: int,
    candidate_key: str,
    params: dict[str, Any],
    attempted: dict[str, Any],
    out: Path,
) -> CandidateRecord:
    candidates_dir = out / "candidates"
    hull_path = candidates_dir / f"{candidate_key}.hull.json"
    eval_path = candidates_dir / f"{candidate_key}.eval.json"

    hydro = evaluate_hydrostatics(hull)
    design_validity = evaluate_design_validity(
        hull,
        cp=hydro.Cp_actual,
        displaced_mass_kg=hydro.displaced_mass_kg,
        surface=("sweep",),
    )
    resistance = resistance_curve(hull) if spec.evaluators.resistance else None
    stability = None
    if spec.evaluators.stability:
        load_case = LoadCase.model_validate(spec.evaluators.stability_load_case)
        stability = (
            evaluate_equilibrium_stability(
                hull,
                load_case,
                tolerance_kg=spec.evaluators.stability_tolerance_kg,
                moment_tolerance_kg_m=spec.evaluators.stability_moment_tolerance_kg_m,
            )
            if spec.evaluators.stability_equilibrium
            else evaluate_initial_stability(hull, load_case)
        )
    evaluation = EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=hydro,
        resistance=resistance,
        stability=stability,
        design_validity=design_validity,
    )
    save_hull(hull, hull_path)
    save_evaluation(evaluation, eval_path)

    artifacts = {
        "hull": str(hull_path.relative_to(out)),
        "evaluation": str(eval_path.relative_to(out)),
    }
    warnings: list[str] = []
    if spec.evaluators.mesh_diagnostics:
        from kayakgen.eval.mesh_diagnostics import diagnose_mesh

        mesh_path = candidates_dir / f"{candidate_key}.mesh.json"
        mesh = diagnose_mesh(hull)
        mesh_path.write_text(mesh.model_dump_json(indent=2))
        artifacts["mesh_diagnostics"] = str(mesh_path.relative_to(out))
        warnings.extend(mesh.warnings)

    stl_artifacts: StlArtifactSet | None = None
    if spec.evaluators.stl:
        candidate_dir = candidates_dir / candidate_key
        stl_artifacts = write_candidate_stl(hull, candidate_dir, out)
        artifacts["stl_hull"] = stl_artifacts.hull.path
        artifacts["stl_deck"] = stl_artifacts.deck.path

    high_angle_gz_artifact: HighAngleGzArtifact | None = None
    if spec.evaluators.high_angle_gz:
        heel_grid = (
            list(spec.evaluators.high_angle_gz_heel_grid_deg)
            if spec.evaluators.high_angle_gz_heel_grid_deg is not None
            else [float(angle) for angle in DEFAULT_GZ_HEEL_GRID_DEG]
        )
        gz_load_case = (
            LoadCase.model_validate(spec.evaluators.stability_load_case)
            if spec.evaluators.stability_load_case
            else LoadCase()
        )
        block = build_high_angle_gz_block(hull, gz_load_case, heel_grid_deg=heel_grid)
        candidate_dir = candidates_dir / candidate_key
        high_angle_gz_artifact = write_candidate_high_angle_gz(block, candidate_dir, out)
        artifacts["high_angle_gz"] = high_angle_gz_artifact.path

    summary = {
        "displaced_mass_kg": hydro.displaced_mass_kg,
        "wetted_surface_m2": hydro.wetted_surface_m2,
        "GM0_m": hydro.GM0_m,
        "Cp_actual": hydro.Cp_actual,
    }
    if resistance is not None:
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


def _write_summary(path: Path, records: list[CandidateRecord]) -> None:
    parameter_names = sorted({key for record in records for key in record.parameters})
    fieldnames = [
        "candidate_index",
        "candidate_key",
        "status",
        "hull_hash",
        "error",
        *[f"param_{name}" for name in parameter_names],
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
    ]
    with path.open("w", newline="") as fh:
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
            for key in fieldnames[5 + len(parameter_names):]:
                row[key] = record.summary.get(key, "")
            writer.writerow(row)


def _write_failures(path: Path, failures: list[CandidateRecord]) -> None:
    with path.open("w") as fh:
        for failure in failures:
            fh.write(failure.model_dump_json() + "\n")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
