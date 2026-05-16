"""``fixture_local_command`` adapter and its deterministic case contracts.

Exercises successful local-command fixture plumbing without depending on
any external solver. Houses the fixture-only pydantic models
(``CfdFixtureMeshSummary``, ``CfdFixtureCaseInput``,
``CfdFixtureMeshSummaryFile``, ``CfdFixtureCommandSpec``,
``CfdFixtureCommandOutput``, ``CfdFixtureRawResult``) used by the
adapter and the checked-in fixture command.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from kayakgen.eval.claims import (
    RawUnvalidatedClaimFields,
    WARNING_RAW_CFD_UNVALIDATED,
)
from kayakgen.eval.cfd.job_store import (
    _run_record_from_result,
    _utc_now,
    _write_command_logs,
    _write_json,
)
from kayakgen.eval.cfd.profiles import (
    CFD_FIXTURE_RESULTS_WARNING,
    FIXTURE_CASE_TEMPLATE_VERSION,
    FIXTURE_RAW_OUTPUT,
)
from kayakgen.eval.cfd.records import (
    CfdRunRecord,
    PreparedSolverCase,
    SolverRawResult,
)
from kayakgen.eval.mesh_diagnostics import ReadinessLevel


class CfdFixtureMeshSummary(BaseModel):
    """Stable mesh metadata written into deterministic fixture cases."""

    model_config = ConfigDict(extra="forbid")

    manifest_ref: str
    mesh_package_ref: str
    hull_hash: str
    units: str
    readiness: ReadinessLevel
    solver_profile: str
    parts: list[str]
    quality_reports: dict[str, str]
    surfaces: dict[str, str]
    warnings: list[str] = Field(default_factory=list)


class CfdFixtureCaseInput(BaseModel):
    """Deterministic input record consumed by the checked-in fixture command."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    case_template_version: Literal["fixture-local-command-v1"] = (
        FIXTURE_CASE_TEMPLATE_VERSION
    )
    job_id: str
    solver_profile: str
    speed_mps: float = Field(gt=0)
    seawater_density_kg_m3: float = Field(gt=0)
    kinematic_viscosity_m2_s: float = Field(gt=0)
    raw_output: str = FIXTURE_RAW_OUTPUT
    mesh: CfdFixtureMeshSummary
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


class CfdFixtureMeshSummaryFile(BaseModel):
    """Compact standalone mesh summary for deterministic fixture cases."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    hull_hash: str
    mesh_readiness: ReadinessLevel
    mesh_solver_profile: str
    parts: list[str]
    quality_reports: dict[str, str]
    surfaces: dict[str, str]
    warnings: list[str] = Field(default_factory=list)


class CfdFixtureCommandSpec(BaseModel):
    """Deterministic command metadata written next to fixture case inputs."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    command: list[str]
    case_input: str
    raw_output: str
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


class CfdFixtureCommandOutput(BaseModel):
    """Schema emitted by the checked-in fixture command before normalization."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    job_id: str
    speed_mps: float = Field(gt=0)
    drag_force_n: float = Field(ge=0)
    residual_summary: dict[str, float] = Field(default_factory=dict)
    fixture_version: str


class CfdFixtureRawResult(RawUnvalidatedClaimFields):
    """Normalized raw fixture result persisted for CLI/web/sweep callers."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    job_id: str
    speed_mps: float = Field(gt=0)
    drag_force_n: float = Field(ge=0)
    residual_summary: dict[str, float] = Field(default_factory=dict)
    fixture_version: str
    command: list[str]
    returncode: int
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


def _fixture_warnings() -> list[str]:
    return [WARNING_RAW_CFD_UNVALIDATED, CFD_FIXTURE_RESULTS_WARNING]


def _fixture_command_env() -> dict[str, str]:
    env = os.environ.copy()
    repo_root = Path(__file__).resolve().parents[4]
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(repo_root) if not existing else os.pathsep.join([str(repo_root), existing])
    )
    return env


class FixtureLocalCommandAdapter:
    """Adapter that exercises successful local-command fixture plumbing."""

    def prepare(self, case: PreparedSolverCase) -> PreparedSolverCase:
        case_dir = case.job_dir / "case"
        logs_dir = case.job_dir / "logs"
        case_dir.mkdir(exist_ok=True)
        logs_dir.mkdir(exist_ok=True)

        fixture_case = CfdFixtureCaseInput(
            job_id=case.job_spec.job_id,
            solver_profile=case.job_spec.solver_profile,
            speed_mps=case.job_spec.speed_mps,
            seawater_density_kg_m3=case.job_spec.seawater_density_kg_m3,
            kinematic_viscosity_m2_s=case.job_spec.kinematic_viscosity_m2_s,
            mesh=CfdFixtureMeshSummary(
                manifest_ref=case.job_spec.input_manifest,
                mesh_package_ref=case.job_spec.mesh_package_ref,
                hull_hash=case.mesh_manifest.hull_hash,
                units=case.mesh_manifest.units,
                readiness=case.mesh_manifest.readiness.level,
                solver_profile=case.mesh_manifest.solver_profile.profile_name,
                parts=list(case.mesh_manifest.parts),
                quality_reports={
                    key: value for key, value in sorted(case.mesh_manifest.quality_reports.items())
                },
                surfaces={
                    key: value for key, value in sorted(case.mesh_manifest.surfaces.items())
                },
                warnings=list(case.mesh_manifest.warnings),
            ),
        )
        command_spec = CfdFixtureCommandSpec(
            command=list(case.solver_profile.command_template),
            case_input="case/fixture-case.json",
            raw_output=FIXTURE_RAW_OUTPUT,
        )
        mesh_summary = CfdFixtureMeshSummaryFile(
            hull_hash=case.mesh_manifest.hull_hash,
            mesh_readiness=case.mesh_manifest.readiness.level,
            mesh_solver_profile=case.mesh_manifest.solver_profile.profile_name,
            parts=list(case.mesh_manifest.parts),
            quality_reports={
                key: value for key, value in sorted(case.mesh_manifest.quality_reports.items())
            },
            surfaces={
                key: value for key, value in sorted(case.mesh_manifest.surfaces.items())
            },
            warnings=list(case.mesh_manifest.warnings),
        )
        _write_json(case_dir / "fixture-case.json", fixture_case)
        _write_json(case_dir / "mesh-summary.json", mesh_summary)
        _write_json(case_dir / "command.json", command_spec)
        return case

    def run(self, case: PreparedSolverCase) -> SolverRawResult:
        try:
            completed = subprocess.run(
                case.solver_profile.command_template,
                cwd=case.job_dir,
                capture_output=True,
                check=False,
                text=True,
                env=_fixture_command_env(),
            )
        except (FileNotFoundError, PermissionError) as exc:
            completed = subprocess.CompletedProcess(
                args=case.solver_profile.command_template,
                returncode=127,
                stdout="",
                stderr=str(exc),
            )
            logs = _write_command_logs(case.job_dir, completed)
            return SolverRawResult(
                status="unavailable",
                error_kind="solver_unavailable",
                error_message=f"solver command unavailable: {exc}",
                logs=logs,
                raw_records={"command": list(case.solver_profile.command_template)},
                warnings=_fixture_warnings(),
            )

        logs = _write_command_logs(case.job_dir, completed)
        if completed.returncode != 0:
            message = (
                f"fixture command exited with code {completed.returncode}; "
                "raw fixture output is unvalidated"
            )
            if completed.stderr.strip():
                message = f"{message}: {completed.stderr.strip()}"
            return SolverRawResult(
                status="failed",
                error_kind="command_failed",
                error_message=message,
                logs=logs,
                raw_records={"returncode": completed.returncode},
                warnings=_fixture_warnings(),
            )

        output_path = case.job_dir / FIXTURE_RAW_OUTPUT
        if not output_path.is_file():
            return SolverRawResult(
                status="failed",
                error_kind="missing_output",
                error_message=f"fixture command did not write required {FIXTURE_RAW_OUTPUT}",
                logs=logs,
                raw_records={"returncode": completed.returncode},
                warnings=_fixture_warnings(),
            )

        try:
            command_output = CfdFixtureCommandOutput.model_validate_json(
                output_path.read_text()
            )
        except ValidationError as exc:
            return SolverRawResult(
                status="failed",
                error_kind="malformed_output",
                error_message=f"{FIXTURE_RAW_OUTPUT} is malformed fixture raw output: {exc}",
                logs=logs,
                raw_records={"returncode": completed.returncode},
                warnings=_fixture_warnings(),
            )

        if command_output.job_id != case.job_spec.job_id:
            return SolverRawResult(
                status="failed",
                error_kind="malformed_output",
                error_message=(
                    "fixture raw output job_id mismatch: "
                    f"expected {case.job_spec.job_id!r}, got {command_output.job_id!r}"
                ),
                logs=logs,
                raw_records={"returncode": completed.returncode},
                warnings=_fixture_warnings(),
            )

        normalized = CfdFixtureRawResult(
            job_id=case.job_spec.job_id,
            speed_mps=command_output.speed_mps,
            drag_force_n=command_output.drag_force_n,
            residual_summary=dict(command_output.residual_summary),
            fixture_version=command_output.fixture_version,
            command=list(case.solver_profile.command_template),
            returncode=completed.returncode,
            warnings=_fixture_warnings(),
        )
        _write_json(output_path, normalized)
        return SolverRawResult(
            status="succeeded",
            output_manifest=FIXTURE_RAW_OUTPUT,
            logs=logs,
            raw_records=normalized.model_dump(mode="python"),
            warnings=list(normalized.warnings),
        )

    def collect(self, case: PreparedSolverCase, result: SolverRawResult) -> CfdRunRecord:
        return _run_record_from_result(
            case.job_spec,
            result,
            started_at=_utc_now(),
            finished_at=_utc_now(),
        )


__all__ = [
    "CfdFixtureCaseInput",
    "CfdFixtureCommandOutput",
    "CfdFixtureCommandSpec",
    "CfdFixtureMeshSummary",
    "CfdFixtureMeshSummaryFile",
    "CfdFixtureRawResult",
    "FixtureLocalCommandAdapter",
]
