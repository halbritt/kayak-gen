"""Local CFD job preparation, persistence, and run dispatch helpers.

Provides ``prepare_cfd_job`` / ``prepare_local_job`` /  ``run_cfd_job`` /
``run_local_job`` and the on-disk persistence helpers used by every CFD
adapter (run records, JSON serialization, log capture, deterministic
timestamps, command-output text shaping, mesh package + job manifest
loaders, and the adapter dispatch table).

Split out from the historical ``kayakgen.eval.cfd.jobs`` per Phase 3A
of ``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md``.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ValidationError

from kayakgen.eval.cfd.manifest_validation import (
    _load_mesh_manifest,
    _validate_mesh_package,
    _validate_positive_job_inputs,
)
from kayakgen.eval.cfd.profiles import _solver_profile_by_name
from kayakgen.eval.cfd.records import (
    CfdDispatchError,
    CfdJobPaths,
    CfdJobSpec,
    CfdRunRecord,
    LocalCfdJob,
    PreparedSolverCase,
    SolverAdapter,
    SolverProfile,
    SolverRawResult,
)
from kayakgen.eval.mesh_package import MeshPackageManifest


def prepare_cfd_job(
    mesh_package: Path,
    out_dir: Path,
    *,
    solver_profile_name: str,
    speed_mps: float,
    seawater_density_kg_m3: float = 1025.0,
    kinematic_viscosity_m2_s: float = 1.19e-6,
    hull_ref: str | None = None,
    allow_real_solver_execution: bool = False,
) -> CfdJobPaths:
    """Prepare a local CFD job using a named built-in solver profile.

    ``allow_real_solver_execution`` writes
    ``allow_real_solver_execution: true`` into the prepared
    ``profile.json``. This is one of the three opt-in mechanisms for the
    OpenFOAM real-solver succeeded path (RFC 0046).
    """
    profile = _solver_profile_by_name(solver_profile_name)
    if allow_real_solver_execution:
        profile = profile.model_copy(update={"allow_real_solver_execution": True})
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
        mesh_evidence_hashes=dict(manifest.evidence_hashes),
    )
    run_record = _initial_run_record(job_spec)

    _write_json(job_dir / "profile.json", solver_profile)
    _write_json(job_dir / "job.json", job_spec)
    _write_json(job_dir / "run.json", run_record)

    if solver_profile.adapter_name in {"fixture_local_command", "openfoam_local"}:
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


def load_profile(job_dir: Path) -> SolverProfile:
    """Load and parse the prepared profile.json for a local CFD job."""
    profile_path = Path(job_dir) / "profile.json"
    try:
        return SolverProfile.model_validate_json(profile_path.read_text())
    except FileNotFoundError as exc:
        raise CfdDispatchError(
            f"prepared solver profile not found: {profile_path}"
        ) from exc
    except ValidationError as exc:
        raise CfdDispatchError(
            f"malformed solver profile: {profile_path}"
        ) from exc


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
    # Local imports to avoid a circular dependency between the adapters
    # (which depend on the persistence helpers in this module) and the
    # adapter dispatch table.
    from kayakgen.eval.cfd.adapters.fixture import FixtureLocalCommandAdapter
    from kayakgen.eval.cfd.adapters.mock import MockFailingLocalCommandAdapter
    from kayakgen.eval.cfd.adapters.openfoam_v2512 import OpenFoamLocalAdapter
    from kayakgen.eval.cfd.adapters.unavailable import UnavailableSolverAdapter

    if solver_profile.adapter_name == "unavailable":
        return UnavailableSolverAdapter()
    if solver_profile.adapter_name == "mock_local_command":
        return MockFailingLocalCommandAdapter()
    if solver_profile.adapter_name == "fixture_local_command":
        return FixtureLocalCommandAdapter()
    if solver_profile.adapter_name == "openfoam_local":
        return OpenFoamLocalAdapter()
    raise CfdDispatchError(f"unsupported solver adapter: {solver_profile.adapter_name}")


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
        "body_ref": manifest.body_ref,
        "readiness_authority": manifest.readiness_authority,
        "volume_mesh_artifacts": dict(sorted(manifest.volume_mesh_artifacts.items())),
        "evidence_hashes": dict(sorted(manifest.evidence_hashes.items())),
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
        real_solver_execution_opt_in=result.real_solver_execution_opt_in,
        solver_execution_audit=result.solver_execution_audit,
        warnings=list(result.warnings),
    )


def _completed_from_timeout(
    args: list[str],
    exc: subprocess.TimeoutExpired,
) -> subprocess.CompletedProcess[str]:
    stdout = _process_text(exc.stdout)
    stderr = _process_text(exc.stderr)
    if stderr:
        stderr = f"{stderr}\n"
    stderr = f"{stderr}timeout after {exc.timeout:g}s\n"
    return subprocess.CompletedProcess(
        args=args,
        returncode=124,
        stdout=stdout,
        stderr=stderr,
    )


def _process_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _cap_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    omitted = len(text) - max_chars
    return f"{text[:max_chars]}\n[truncated {omitted} chars]\n"


def _write_command_logs(
    job_dir: Path,
    completed: subprocess.CompletedProcess[str],
    *,
    stdout_name: str = "stdout.log",
    stderr_name: str = "stderr.log",
    max_chars: int | None = None,
) -> dict[str, str]:
    logs_dir = job_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    stdout = logs_dir / stdout_name
    stderr = logs_dir / stderr_name
    stdout_text = completed.stdout
    stderr_text = completed.stderr
    if max_chars is not None:
        stdout_text = _cap_text(stdout_text, max_chars)
        stderr_text = _cap_text(stderr_text, max_chars)
    stdout.write_text(stdout_text)
    stderr.write_text(stderr_text)
    return {
        Path(stdout_name).stem: _relative_ref(stdout, job_dir),
        Path(stderr_name).stem: _relative_ref(stderr, job_dir),
    }


def _write_json(path: Path, model: BaseModel) -> None:
    path.write_text(model.model_dump_json(indent=2) + "\n")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text)


def _relative_ref(path: Path, start: Path) -> str:
    return Path(os.path.relpath(path.resolve(), start.resolve())).as_posix()


def _join_ref(base: str, name: str) -> str:
    return (Path(base) / name).as_posix()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = [
    "load_cfd_run_record",
    "load_profile",
    "load_run_record",
    "prepare_cfd_job",
    "prepare_local_job",
    "read_local_status",
    "run_cfd_job",
    "run_local_job",
]
