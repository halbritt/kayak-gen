"""Local CFD job dispatch contracts.

This module records solver-dispatch state only. It does not validate or
calibrate solver physics, and every result record is marked raw/unvalidated.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from kayakgen.eval.claims import RawUnvalidatedClaimFields, WARNING_RAW_CFD_UNVALIDATED
from kayakgen.eval.mesh_diagnostics import ReadinessLevel
from kayakgen.eval.mesh_package import MeshPackageManifest

CfdRunStatus = Literal["queued", "running", "succeeded", "failed", "unavailable"]
CfdAdapterName = Literal["unavailable", "mock_local_command", "fixture_local_command"]
CFD_RAW_RESULTS_WARNING = "CFD results are raw and unvalidated."
CFD_FIXTURE_RESULTS_WARNING = (
    "Fixture CFD output is not calibrated, validated, or final design fitness."
)
FIXTURE_CASE_TEMPLATE_VERSION = "fixture-local-command-v1"
FIXTURE_RAW_OUTPUT = "raw-result.json"

READINESS_ORDER: dict[ReadinessLevel, int] = {
    "invalid": 0,
    "display": 1,
    "stl_surface": 2,
    "cfd_surface_candidate": 3,
    "cfd_ready": 4,
}


class CfdDispatchError(ValueError):
    """Raised when a local CFD job cannot be prepared or read."""


class SolverProfile(RawUnvalidatedClaimFields):
    """Solver dispatch profile used to gate mesh readiness and choose an adapter."""

    model_config = ConfigDict(extra="forbid")

    name: str
    required_mesh_readiness: ReadinessLevel
    adapter_name: CfdAdapterName
    container_image: str | None = None
    command_template: list[str] = Field(default_factory=list)
    required_mesh_profile: str | None = None
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
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


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
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


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


class SolverAdapter(Protocol):
    """Narrow boundary for local solver adapters."""

    def prepare(self, case: PreparedSolverCase) -> PreparedSolverCase:
        """Prepare solver-specific files."""

    def run(self, case: PreparedSolverCase) -> SolverRawResult:
        """Run solver-specific work and return raw status."""

    def collect(self, case: PreparedSolverCase, result: SolverRawResult) -> CfdRunRecord:
        """Collect a result into a run record."""


def unavailable_open_surface_profile() -> SolverProfile:
    """Return an unavailable profile that accepts current open-surface packages."""
    return SolverProfile(
        name="unavailable-open-wetted-surface",
        required_mesh_readiness="cfd_surface_candidate",
        adapter_name="unavailable",
        required_mesh_profile="open_wetted_surface_resistance_v1",
    )


def unavailable_watertight_solid_profile() -> SolverProfile:
    """Return an unavailable future profile requiring watertight CFD readiness."""
    return SolverProfile(
        name="unavailable-watertight-solid",
        required_mesh_readiness="cfd_ready",
        adapter_name="unavailable",
        required_mesh_profile="watertight_solid_resistance_v1",
    )


def mock_failing_local_command_profile() -> SolverProfile:
    """Return a local-command profile that deliberately fails for dispatch tests."""
    return SolverProfile(
        name="mock-failing-local-command",
        required_mesh_readiness="cfd_surface_candidate",
        adapter_name="mock_local_command",
        command_template=[
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.stdout.write('mock CFD command starting\\n'); "
                "sys.stderr.write('mock CFD command failed intentionally\\n'); "
                "sys.exit(7)"
            ),
        ],
        required_mesh_profile="open_wetted_surface_resistance_v1",
    )


def fixture_local_command_profile() -> SolverProfile:
    """Return the deterministic fixture profile for local command dispatch."""
    return SolverProfile(
        name="fixture-local-command",
        required_mesh_readiness="cfd_surface_candidate",
        adapter_name="fixture_local_command",
        command_template=[
            sys.executable,
            "-m",
            "kayakgen.eval.cfd.fixture_command",
            "--case",
            "case/fixture-case.json",
            "--out",
            FIXTURE_RAW_OUTPUT,
        ],
        required_mesh_profile="open_wetted_surface_resistance_v1",
    )


def solver_profile_names() -> tuple[str, ...]:
    """Return the names of built-in local dispatch profiles."""
    return tuple(sorted(_solver_profiles()))


def solver_profiles() -> tuple[SolverProfile, ...]:
    """Return built-in local dispatch profiles in deterministic name order."""
    profiles = _solver_profiles()
    return tuple(profiles[name] for name in sorted(profiles))


def solver_profile_by_name(name: str) -> SolverProfile:
    """Return a built-in local dispatch profile by public name or accepted alias."""
    return _solver_profile_by_name(name)


def prepare_cfd_job(
    mesh_package: Path,
    out_dir: Path,
    *,
    solver_profile_name: str,
    speed_mps: float,
    seawater_density_kg_m3: float = 1025.0,
    kinematic_viscosity_m2_s: float = 1.19e-6,
    hull_ref: str | None = None,
) -> CfdJobPaths:
    """Prepare a local CFD job using a named built-in solver profile."""
    profile = _solver_profile_by_name(solver_profile_name)
    job = prepare_local_job(
        mesh_package,
        out_dir,
        profile,
        hull_ref=hull_ref,
        speed_mps=speed_mps,
        seawater_density_kg_m3=seawater_density_kg_m3,
        kinematic_viscosity_m2_s=kinematic_viscosity_m2_s,
    )
    return CfdJobPaths(
        job_dir=job.job_dir,
        job=job.job_spec,
        run=job.run_record,
        job_path=job.job_dir / "job.json",
        run_path=job.job_dir / "run.json",
    )


def run_cfd_job(job_dir: Path) -> CfdRunRecord:
    """Run a prepared local CFD job."""
    return run_local_job(job_dir)


def load_cfd_run_record(job_dir: Path) -> CfdRunRecord:
    """Load the current run record for a prepared local CFD job directory."""
    return load_run_record(job_dir / "run.json")


def prepare_local_job(
    mesh_package_dir: str | Path,
    jobs_dir: str | Path,
    solver_profile: SolverProfile,
    *,
    hull_ref: str | None = None,
    speed_mps: float,
    seawater_density_kg_m3: float = 1025.0,
    kinematic_viscosity_m2_s: float = 1.19e-6,
    created_at: str | None = None,
) -> LocalCfdJob:
    """Validate a mesh package and write deterministic local job records."""
    _validate_positive_job_inputs(
        speed_mps=speed_mps,
        seawater_density_kg_m3=seawater_density_kg_m3,
        kinematic_viscosity_m2_s=kinematic_viscosity_m2_s,
    )
    mesh_dir = Path(mesh_package_dir)
    manifest = _load_mesh_manifest(mesh_dir)
    _validate_mesh_package(mesh_dir, manifest, solver_profile)

    job_id = _job_id(
        manifest=manifest,
        solver_profile=solver_profile,
        speed_mps=speed_mps,
        seawater_density_kg_m3=seawater_density_kg_m3,
        kinematic_viscosity_m2_s=kinematic_viscosity_m2_s,
    )
    job_dir = Path(jobs_dir) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    mesh_package_ref = _relative_ref(mesh_dir, job_dir)
    input_manifest = _join_ref(mesh_package_ref, "manifest.json")
    job_spec = CfdJobSpec(
        job_id=job_id,
        hull_ref=hull_ref or _join_ref(mesh_package_ref, manifest.hull_json),
        mesh_package_ref=mesh_package_ref,
        solver_profile=solver_profile.name,
        speed_mps=speed_mps,
        seawater_density_kg_m3=seawater_density_kg_m3,
        kinematic_viscosity_m2_s=kinematic_viscosity_m2_s,
        created_at=created_at or _utc_now(),
        input_manifest=input_manifest,
        mesh_readiness=manifest.readiness.level,
        mesh_warnings=list(manifest.warnings),
    )
    run_record = _initial_run_record(job_spec)

    _write_json(job_dir / "profile.json", solver_profile)
    _write_json(job_dir / "job.json", job_spec)
    _write_json(job_dir / "run.json", run_record)

    if solver_profile.adapter_name == "fixture_local_command":
        prepared_case = PreparedSolverCase(
            job_dir=job_dir,
            job_spec=job_spec,
            solver_profile=solver_profile,
            mesh_manifest=manifest,
        )
        _adapter_for(solver_profile).prepare(prepared_case)

    return LocalCfdJob(
        job_dir=job_dir,
        job_spec=job_spec,
        solver_profile=solver_profile,
        mesh_manifest=manifest,
        run_record=run_record,
    )


def run_local_job(job_dir: str | Path) -> CfdRunRecord:
    """Run a prepared local job with its configured adapter."""
    case = _load_prepared_case(Path(job_dir))
    adapter = _adapter_for(case.solver_profile)
    prepared = adapter.prepare(case)

    running = _run_record_from_result(
        prepared.job_spec,
        SolverRawResult(status="running"),
        started_at=_utc_now(),
        finished_at=None,
    )
    _write_json(prepared.job_dir / "run.json", running)

    result = adapter.run(prepared)
    record = adapter.collect(prepared, result)
    _write_json(prepared.job_dir / "run.json", record)
    return record


def read_local_status(job_dir: str | Path) -> CfdRunRecord:
    """Read a prepared local job's current run record."""
    return load_run_record(Path(job_dir) / "run.json")


def load_run_record(path: str | Path) -> CfdRunRecord:
    """Load and parse a CFD run record."""
    try:
        return CfdRunRecord.model_validate_json(Path(path).read_text())
    except FileNotFoundError as exc:
        raise CfdDispatchError(f"run record not found: {Path(path)}") from exc
    except ValidationError as exc:
        raise CfdDispatchError(f"malformed run record: {Path(path)}") from exc


class UnavailableSolverAdapter:
    """Adapter for solver profiles that are known to be unavailable."""

    def prepare(self, case: PreparedSolverCase) -> PreparedSolverCase:
        return case

    def run(self, case: PreparedSolverCase) -> SolverRawResult:
        return SolverRawResult(
            status="unavailable",
            error_kind="solver_unavailable",
            error_message=(
                f"solver profile {case.solver_profile.name!r} is unavailable; "
                "results remain raw and unvalidated"
            ),
        )

    def collect(self, case: PreparedSolverCase, result: SolverRawResult) -> CfdRunRecord:
        return _run_record_from_result(
            case.job_spec,
            result,
            started_at=_utc_now(),
            finished_at=_utc_now(),
        )


class MockFailingLocalCommandAdapter:
    """Adapter that runs a known local command and records command failure."""

    def prepare(self, case: PreparedSolverCase) -> PreparedSolverCase:
        logs_dir = case.job_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        return case

    def run(self, case: PreparedSolverCase) -> SolverRawResult:
        completed = subprocess.run(
            case.solver_profile.command_template,
            cwd=case.job_dir,
            capture_output=True,
            check=False,
            text=True,
        )
        logs = _write_command_logs(case.job_dir, completed)
        if completed.returncode != 0:
            message = (
                f"solver command exited with code {completed.returncode}; "
                "raw solver output is unvalidated"
            )
            if completed.stderr.strip():
                message = f"{message}: {completed.stderr.strip()}"
            return SolverRawResult(
                status="failed",
                error_kind="command_failed",
                error_message=message,
                logs=logs,
                raw_records={"returncode": completed.returncode},
            )

        output_path = case.job_dir / "raw-result.json"
        raw_records = {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        output_path.write_text(json.dumps(raw_records, indent=2, sort_keys=True) + "\n")
        return SolverRawResult(
            status="succeeded",
            output_manifest=output_path.name,
            logs=logs,
            raw_records=raw_records,
        )

    def collect(self, case: PreparedSolverCase, result: SolverRawResult) -> CfdRunRecord:
        return _run_record_from_result(
            case.job_spec,
            result,
            started_at=_utc_now(),
            finished_at=_utc_now(),
        )


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


def _load_mesh_manifest(mesh_dir: Path) -> MeshPackageManifest:
    manifest_path = mesh_dir / "manifest.json"
    try:
        return MeshPackageManifest.model_validate_json(manifest_path.read_text())
    except FileNotFoundError as exc:
        raise CfdDispatchError(f"mesh package manifest not found: {manifest_path}") from exc
    except ValidationError as exc:
        raise CfdDispatchError(f"malformed mesh package manifest: {manifest_path}") from exc


def _validate_mesh_package(
    mesh_dir: Path,
    manifest: MeshPackageManifest,
    solver_profile: SolverProfile,
) -> None:
    if solver_profile.required_mesh_profile:
        actual_profile = manifest.solver_profile.profile_name
        if actual_profile != solver_profile.required_mesh_profile:
            raise CfdDispatchError(
                "mesh package solver profile mismatch: "
                f"expected {solver_profile.required_mesh_profile!r}, got {actual_profile!r}"
            )

    actual = READINESS_ORDER[manifest.readiness.level]
    required = READINESS_ORDER[solver_profile.required_mesh_readiness]
    if actual < required:
        raise CfdDispatchError(
            "mesh package readiness below solver requirement: "
            f"readiness {manifest.readiness.level} is below required "
            f"{solver_profile.required_mesh_readiness}"
        )

    refs = [
        manifest.hull_json,
        *manifest.quality_reports.values(),
        *manifest.surfaces.values(),
    ]
    missing = sorted(ref for ref in refs if not (mesh_dir / ref).is_file())
    if missing:
        raise CfdDispatchError(
            "mesh package is missing referenced artifact(s): " + ", ".join(missing)
        )

    if _solver_profile_requires_watertight_evidence(solver_profile, manifest):
        evidence = _watertight_dispatch_evidence(mesh_dir, manifest, solver_profile)
        if not evidence.accepted:
            detail = f": {evidence.reason}" if evidence.reason else ""
            raise CfdDispatchError(
                "watertight dispatch requires profile-scoped closed-volume "
                f"diagnostic evidence{detail}"
            )


class _WatertightDispatchEvidence(BaseModel):
    """Internal result for profile-scoped closed-volume dispatch evidence."""

    accepted: bool
    reason: str | None = None


def _solver_profile_requires_watertight_evidence(
    solver_profile: SolverProfile,
    manifest: MeshPackageManifest,
) -> bool:
    if solver_profile.required_mesh_readiness == "cfd_ready":
        return True
    if solver_profile.required_mesh_profile == "watertight_solid_resistance_v1":
        return True
    return bool(manifest.solver_profile.requires_watertight)


def _watertight_dispatch_evidence(
    mesh_dir: Path,
    manifest: MeshPackageManifest,
    solver_profile: SolverProfile,
) -> _WatertightDispatchEvidence:
    diagnostic_refs = _profile_diagnostic_refs(manifest)
    if not diagnostic_refs:
        return _WatertightDispatchEvidence(
            accepted=False,
            reason="no referenced diagnostics were found",
        )

    reasons: list[str] = []
    for ref in diagnostic_refs:
        path = mesh_dir / ref
        try:
            evidence = json.loads(path.read_text())
        except json.JSONDecodeError:
            reasons.append(f"{ref}: malformed diagnostic JSON")
            continue

        module_result = _closed_volume_module_accepts(evidence, solver_profile)
        if module_result.accepted:
            return module_result
        if module_result.reason:
            reasons.append(f"{ref}: {module_result.reason}")
            continue

        reasons.append(
            f"{ref}: no closed-volume contract validator accepted diagnostic evidence"
        )

    return _WatertightDispatchEvidence(accepted=False, reason="; ".join(reasons))


def _profile_diagnostic_refs(manifest: MeshPackageManifest) -> list[str]:
    manifest_data = manifest.model_dump(mode="python")
    refs: list[str] = []
    refs.extend(str(ref) for ref in manifest.quality_reports.values())
    refs.extend(_diagnostic_refs_from_mapping(manifest_data))
    return list(dict.fromkeys(refs))


def _diagnostic_refs_from_mapping(value: Any, *, parent_key: str = "") -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            combined_key = f"{parent_key}.{key_text}" if parent_key else key_text
            refs.extend(_diagnostic_refs_from_mapping(child, parent_key=combined_key))
    elif isinstance(value, (list, tuple)):
        for child in value:
            refs.extend(_diagnostic_refs_from_mapping(child, parent_key=parent_key))
    elif isinstance(value, str) and "diagnostic" in parent_key.lower():
        refs.append(value)
    return refs


def _closed_volume_module_accepts(
    evidence: dict[str, Any],
    solver_profile: SolverProfile,
) -> _WatertightDispatchEvidence:
    try:
        from kayakgen.eval import closed_volume
    except ImportError:
        return _WatertightDispatchEvidence(accepted=False)

    validator = getattr(closed_volume, "dispatch_evidence_satisfies_profile", None)
    if validator is None:
        return _WatertightDispatchEvidence(accepted=False)

    try:
        accepted = bool(
            validator(
                evidence,
                solver_profile.required_mesh_profile,
                solver_profile.required_mesh_readiness,
            )
        )
    except (TypeError, ValueError, AttributeError) as exc:
        return _WatertightDispatchEvidence(accepted=False, reason=str(exc))

    if accepted:
        return _WatertightDispatchEvidence(accepted=True)
    return _WatertightDispatchEvidence(
        accepted=False,
        reason="closed-volume module rejected diagnostic evidence",
    )


def _validate_positive_job_inputs(
    *,
    speed_mps: float,
    seawater_density_kg_m3: float,
    kinematic_viscosity_m2_s: float,
) -> None:
    invalid = []
    if speed_mps <= 0:
        invalid.append("speed_mps")
    if seawater_density_kg_m3 <= 0:
        invalid.append("seawater_density_kg_m3")
    if kinematic_viscosity_m2_s <= 0:
        invalid.append("kinematic_viscosity_m2_s")
    if invalid:
        raise CfdDispatchError("CFD job inputs must be positive: " + ", ".join(invalid))


def _load_prepared_case(job_dir: Path) -> PreparedSolverCase:
    job_path = job_dir / "job.json"
    profile_path = job_dir / "profile.json"
    try:
        job_spec = CfdJobSpec.model_validate_json(job_path.read_text())
        solver_profile = SolverProfile.model_validate_json(profile_path.read_text())
    except FileNotFoundError as exc:
        raise CfdDispatchError(f"prepared CFD job record not found in {job_dir}") from exc
    except ValidationError as exc:
        raise CfdDispatchError(f"malformed CFD job record in {job_dir}") from exc

    manifest_path = (job_dir / job_spec.input_manifest).resolve()
    try:
        manifest = MeshPackageManifest.model_validate_json(manifest_path.read_text())
    except FileNotFoundError as exc:
        raise CfdDispatchError(f"mesh package manifest not found: {manifest_path}") from exc
    except ValidationError as exc:
        raise CfdDispatchError(f"malformed mesh package manifest: {manifest_path}") from exc

    return PreparedSolverCase(
        job_dir=job_dir,
        job_spec=job_spec,
        solver_profile=solver_profile,
        mesh_manifest=manifest,
    )


def _adapter_for(solver_profile: SolverProfile) -> SolverAdapter:
    if solver_profile.adapter_name == "unavailable":
        return UnavailableSolverAdapter()
    if solver_profile.adapter_name == "mock_local_command":
        return MockFailingLocalCommandAdapter()
    if solver_profile.adapter_name == "fixture_local_command":
        return FixtureLocalCommandAdapter()
    raise CfdDispatchError(f"unsupported solver adapter: {solver_profile.adapter_name}")


def _solver_profiles() -> dict[str, SolverProfile]:
    profiles = (
        unavailable_open_surface_profile(),
        unavailable_watertight_solid_profile(),
        mock_failing_local_command_profile(),
        fixture_local_command_profile(),
    )
    return {profile.name: profile for profile in profiles}


def _solver_profile_by_name(name: str) -> SolverProfile:
    profiles = _solver_profiles()
    aliases = {
        "unavailable_open_wetted_surface_v1": "unavailable-open-wetted-surface",
        "unavailable_watertight_solid_v1": "unavailable-watertight-solid",
        "mock_failing_local_command_v1": "mock-failing-local-command",
        "fixture_local_command_v1": "fixture-local-command",
    }
    name = aliases.get(name, name)
    try:
        return profiles[name]
    except KeyError as exc:
        available = ", ".join(sorted(profiles))
        raise CfdDispatchError(
            f"unknown solver profile {name!r}; available profiles: {available}"
        ) from exc


def _job_id(
    *,
    manifest: MeshPackageManifest,
    solver_profile: SolverProfile,
    speed_mps: float,
    seawater_density_kg_m3: float,
    kinematic_viscosity_m2_s: float,
) -> str:
    identity = {
        "hull_hash": manifest.hull_hash,
        "mesh_profile": manifest.solver_profile.profile_name,
        "solver_profile": solver_profile.name,
        "speed_mps": speed_mps,
        "seawater_density_kg_m3": seawater_density_kg_m3,
        "kinematic_viscosity_m2_s": kinematic_viscosity_m2_s,
    }
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "cfd-" + hashlib.sha256(encoded).hexdigest()[:16]


def _initial_run_record(job_spec: CfdJobSpec) -> CfdRunRecord:
    return CfdRunRecord(
        job_id=job_spec.job_id,
        status="queued",
        solver_profile=job_spec.solver_profile,
        input_manifest=job_spec.input_manifest,
        mesh_warnings=list(job_spec.mesh_warnings),
    )


def _run_record_from_result(
    job_spec: CfdJobSpec,
    result: SolverRawResult,
    *,
    started_at: str | None,
    finished_at: str | None,
) -> CfdRunRecord:
    return CfdRunRecord(
        job_id=job_spec.job_id,
        status=result.status,
        solver_profile=job_spec.solver_profile,
        input_manifest=job_spec.input_manifest,
        output_manifest=result.output_manifest,
        started_at=started_at,
        finished_at=finished_at,
        error_kind=result.error_kind,
        error_message=result.error_message,
        logs=result.logs,
        mesh_warnings=list(job_spec.mesh_warnings),
        raw_records=result.raw_records,
        warnings=list(result.warnings),
    )


def _fixture_warnings() -> list[str]:
    return [WARNING_RAW_CFD_UNVALIDATED, CFD_FIXTURE_RESULTS_WARNING]


def _fixture_command_env() -> dict[str, str]:
    env = os.environ.copy()
    repo_root = Path(__file__).resolve().parents[3]
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(repo_root) if not existing else os.pathsep.join([str(repo_root), existing])
    )
    return env


def _write_command_logs(
    job_dir: Path,
    completed: subprocess.CompletedProcess[str],
) -> dict[str, str]:
    logs_dir = job_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    stdout = logs_dir / "stdout.log"
    stderr = logs_dir / "stderr.log"
    stdout.write_text(completed.stdout)
    stderr.write_text(completed.stderr)
    return {"stdout": _relative_ref(stdout, job_dir), "stderr": _relative_ref(stderr, job_dir)}


def _write_json(path: Path, model: BaseModel) -> None:
    path.write_text(model.model_dump_json(indent=2) + "\n")


def _relative_ref(path: Path, start: Path) -> str:
    return Path(os.path.relpath(path.resolve(), start.resolve())).as_posix()


def _join_ref(base: str, name: str) -> str:
    return (Path(base) / name).as_posix()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
