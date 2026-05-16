"""CFD job and run record contracts.

Pydantic data contracts for the local CFD dispatch surface. These models
describe what a job *is* (``CfdJobSpec``), what a run *did*
(``CfdRunRecord``), the real-solver opt-in audit block
(``SolverExecutionAudit``), and the prepared-case and adapter result
wrappers consumed by the local adapter implementations.

Split out from the historical ``kayakgen.eval.cfd.jobs`` per Phase 3A
of ``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md``. The original
module continues to re-export every public name from here unchanged so
existing ``from kayakgen.eval.cfd.jobs import ...`` imports keep
working byte-stably.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from kayakgen.eval.claims import RawUnvalidatedClaimFields
from kayakgen.eval.mesh_diagnostics import ReadinessLevel
from kayakgen.eval.mesh_package import MeshPackageManifest

CfdRunStatus = Literal["queued", "running", "succeeded", "failed", "unavailable"]
CfdAdapterName = Literal[
    "unavailable",
    "mock_local_command",
    "fixture_local_command",
    "openfoam_local",
]

RealSolverExecutionOptIn = Literal["profile_flag", "persistent_setting", "env_knob"]


class CfdDispatchError(ValueError):
    """Raised when a local CFD job cannot be prepared or read."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "cfd_dispatch_error",
    ) -> None:
        super().__init__(message)
        self.code = code


class SolverProfile(RawUnvalidatedClaimFields):
    """Solver dispatch profile used to gate mesh readiness and choose an adapter."""

    model_config = ConfigDict(extra="forbid")

    name: str
    required_mesh_readiness: ReadinessLevel
    adapter_name: CfdAdapterName
    container_image: str | None = None
    command_template: list[str] = Field(default_factory=list)
    solver_name: str | None = None
    solver_version_command: list[str] = Field(default_factory=list)
    required_solver_version: str | None = None
    case_template_version: str | None = None
    supported_platforms: list[str] = Field(default_factory=list)
    supported_speed_range_mps: tuple[float, float] | None = None
    supported_fluid_model: str | None = None
    expected_raw_outputs: list[str] = Field(default_factory=list)
    install_notes: str | None = None
    known_limitations: list[str] = Field(default_factory=list)
    timeout_seconds: float | None = Field(default=None, gt=0)
    log_limit_bytes: int | None = Field(default=None, gt=0)
    required_mesh_profile: str | None = None
    allow_real_solver_execution: bool = False
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


class CfdJobSpec(RawUnvalidatedClaimFields):
    """Serializable CFD job specification."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    job_id: str
    hull_ref: str
    mesh_package_ref: str
    solver_profile: str
    speed_mps: float = Field(gt=0)
    seawater_density_kg_m3: float = Field(gt=0)
    kinematic_viscosity_m2_s: float = Field(gt=0)
    created_at: str
    input_manifest: str
    mesh_readiness: ReadinessLevel
    mesh_warnings: list[str] = Field(default_factory=list)
    mesh_evidence_hashes: dict[str, str] = Field(default_factory=dict)
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


class SolverExecutionAudit(BaseModel):
    """Audit trail for a real-solver succeeded run.

    Populated only on the OpenFOAM ``succeeded`` path admitted by the
    RFC 0046 opt-in resolver. The block records local-to-run provenance
    so the run record explains *which* toolchain produced the raw
    payload. The existing fixture/blocked path leaves the field as
    ``None`` on its run record.
    """

    model_config = ConfigDict(extra="forbid")

    bashrc_path: str
    provenance_summary: dict[str, Any] = Field(default_factory=dict)
    case_template_version: str
    mesh_seconds: float = Field(ge=0.0)
    solve_seconds: float = Field(ge=0.0)


class CfdRunRecord(RawUnvalidatedClaimFields):
    """Serializable run-status record for raw external solver output."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    job_id: str
    status: CfdRunStatus
    solver_profile: str
    input_manifest: str
    output_manifest: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    error_kind: str | None = None
    error_message: str | None = None
    logs: dict[str, str] = Field(default_factory=dict)
    mesh_warnings: list[str] = Field(default_factory=list)
    raw_records: dict[str, Any] = Field(default_factory=dict)
    real_solver_execution_opt_in: RealSolverExecutionOptIn | None = None
    solver_execution_audit: SolverExecutionAudit | None = None
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


class LocalCfdJob(BaseModel):
    """Prepared local filesystem job."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    job_dir: Path
    job_spec: CfdJobSpec
    solver_profile: SolverProfile
    mesh_manifest: MeshPackageManifest
    run_record: CfdRunRecord


class CfdJobPaths(BaseModel):
    """Stable paths for a prepared local CFD job."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    job_dir: Path
    job: CfdJobSpec
    run: CfdRunRecord
    job_path: Path
    run_path: Path


class PreparedSolverCase(BaseModel):
    """Inputs passed to local solver adapters."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    job_dir: Path
    job_spec: CfdJobSpec
    solver_profile: SolverProfile
    mesh_manifest: MeshPackageManifest


class SolverRawResult(RawUnvalidatedClaimFields):
    """Adapter result wrapper for raw, unvalidated solver records."""

    model_config = ConfigDict(extra="forbid")

    status: CfdRunStatus
    output_manifest: str | None = None
    error_kind: str | None = None
    error_message: str | None = None
    logs: dict[str, str] = Field(default_factory=dict)
    raw_records: dict[str, Any] = Field(default_factory=dict)
    real_solver_execution_opt_in: RealSolverExecutionOptIn | None = None
    solver_execution_audit: SolverExecutionAudit | None = None
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


class SolverAdapter(Protocol):
    """Narrow boundary for local solver adapters."""

    def prepare(self, case: PreparedSolverCase) -> PreparedSolverCase:
        """Prepare solver-specific files."""

    def run(self, case: PreparedSolverCase) -> SolverRawResult:
        """Run solver-specific work and return raw status."""

    def collect(self, case: PreparedSolverCase, result: SolverRawResult) -> CfdRunRecord:
        """Collect a result into a run record."""


__all__ = [
    "CfdAdapterName",
    "CfdDispatchError",
    "CfdJobPaths",
    "CfdJobSpec",
    "CfdRunRecord",
    "CfdRunStatus",
    "LocalCfdJob",
    "PreparedSolverCase",
    "RealSolverExecutionOptIn",
    "SolverAdapter",
    "SolverExecutionAudit",
    "SolverProfile",
    "SolverRawResult",
]
