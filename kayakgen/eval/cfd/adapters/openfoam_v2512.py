"""OpenFOAM.com v2512 ``interFoam`` skeleton adapter.

Houses the OpenFOAM adapter, its deterministic case contracts
(``CfdOpenFoamMeshSummary``, ``CfdOpenFoamCaseInput``,
``CfdOpenFoamCommandSpec``, ``CfdOpenFoamRawResult``), the
``_attempt_real_succeeded_path`` machinery, and the
``resolve_real_solver_execution_opt_in`` opt-in resolver.

Split out from the historical ``kayakgen.eval.cfd.jobs`` per Phase 3A
of ``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from kayakgen.eval.claims import (
    RawUnvalidatedClaimFields,
    WARNING_RAW_CFD_UNVALIDATED,
)
from kayakgen.eval.cfd.job_store import (
    _cap_text,
    _completed_from_timeout,
    _relative_ref,
    _run_record_from_result,
    _utc_now,
    _write_command_logs,
    _write_json,
    _write_text,
)
from kayakgen.eval.cfd.parsers.openfoam_forces import parse_openfoam_force_dat
from kayakgen.eval.cfd.profiles import (
    CFD_OPENFOAM_RESULTS_WARNING,
    OPENFOAM_CASE_INPUT,
    OPENFOAM_CASE_ROOT,
    OPENFOAM_CASE_TEMPLATE_VERSION,
    OPENFOAM_COMMAND_SPEC,
    OPENFOAM_COMMAND_TIMEOUT_SECONDS,
    OPENFOAM_FORCE_DAT_OUTPUT,
    OPENFOAM_LOCAL_RUN_ENV_VAR,
    OPENFOAM_LOG_LIMIT_BYTES,
    OPENFOAM_RAW_RESULT,
    OPENFOAM_REQUIRED_VERSION,
    OPENFOAM_SOLVER_NAME,
    OPENFOAM_SUCCEEDED_RAW_UNVALIDATED_WARNING,
    OPENFOAM_SUCCESS_BLOCKED_WARNING,
)
from kayakgen.eval.cfd.provenance import _first_nonempty_line
from kayakgen.eval.cfd.records import (
    CfdDispatchError,
    CfdRunRecord,
    PreparedSolverCase,
    RealSolverExecutionOptIn,
    SolverExecutionAudit,
    SolverProfile,
    SolverRawResult,
)
from kayakgen.eval.mesh_diagnostics import ReadinessLevel


class CfdOpenFoamMeshSummary(BaseModel):
    """Stable mesh metadata written into deterministic OpenFOAM skeleton cases."""

    model_config = ConfigDict(extra="forbid")

    manifest_ref: str
    mesh_package_ref: str
    hull_hash: str
    body_ref: str | None = None
    units: str
    readiness: ReadinessLevel
    solver_profile: str
    parts: list[str]
    quality_reports: dict[str, str]
    surfaces: dict[str, str]
    volume_mesh_diagnostic: str | None = None
    volume_mesh_artifacts: dict[str, str] = Field(default_factory=dict)
    evidence_hashes: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class CfdOpenFoamCaseInput(BaseModel):
    """Deterministic metadata for the OpenFOAM v2512 interFoam skeleton case."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    case_template_version: Literal["openfoam-v2512-interfoam-dtchull-v1"] = (
        OPENFOAM_CASE_TEMPLATE_VERSION
    )
    job_id: str
    solver_profile: str
    solver_name: str
    required_solver_version: str
    speed_mps: float = Field(gt=0)
    seawater_density_kg_m3: float = Field(gt=0)
    kinematic_viscosity_m2_s: float = Field(gt=0)
    expected_raw_outputs: list[str]
    mesh: CfdOpenFoamMeshSummary
    limitations: list[str]
    warnings: list[str] = Field(default_factory=list)
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


class CfdOpenFoamCommandSpec(BaseModel):
    """Deterministic command metadata written next to OpenFOAM skeleton cases."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    command: list[str]
    version_command: list[str]
    timeout_seconds: float = Field(gt=0)
    log_limit_bytes: int = Field(gt=0)
    expected_raw_outputs: list[str]
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


class CfdOpenFoamRawResult(RawUnvalidatedClaimFields):
    """Normalized raw OpenFOAM skeleton output.

    This model is available for parser fixtures and blocked local runs only.
    The adapter intentionally does not return a succeeded run record yet.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    job_id: str
    solver_name: str
    solver_version: str
    case_template_version: Literal["openfoam-v2512-interfoam-dtchull-v1"] = (
        OPENFOAM_CASE_TEMPLATE_VERSION
    )
    speed_mps: float = Field(gt=0)
    seawater_density_kg_m3: float = Field(gt=0)
    kinematic_viscosity_m2_s: float = Field(gt=0)
    mesh_profile: str
    mesh_readiness: ReadinessLevel
    drag_force_n: float | None = None
    residual_summary: dict[str, float] = Field(default_factory=dict)
    raw_output_refs: list[str] = Field(default_factory=list)
    command: list[str]
    version_command: list[str]
    returncode: int
    warnings: list[str] = Field(default_factory=list)
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


def _openfoam_warnings() -> list[str]:
    return [WARNING_RAW_CFD_UNVALIDATED, CFD_OPENFOAM_RESULTS_WARNING]


def _openfoam_timeout_seconds(profile: SolverProfile) -> float:
    return profile.timeout_seconds or OPENFOAM_COMMAND_TIMEOUT_SECONDS


def _openfoam_log_limit_bytes(profile: SolverProfile) -> int:
    return profile.log_limit_bytes or OPENFOAM_LOG_LIMIT_BYTES


def _clear_openfoam_run_outputs(case: PreparedSolverCase) -> None:
    case_root = case.job_dir / OPENFOAM_CASE_ROOT
    stale_paths = [
        case.job_dir / OPENFOAM_RAW_RESULT,
        case_root / "postProcessing" / "forces",
    ]
    for path in stale_paths:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def _openfoam_succeeded_path_enabled() -> bool:
    """Return True when the operator has opted into the real succeeded path.

    Both the ``KAYAKGEN_OPENFOAM_LOCAL_RUN=1`` env var and a real
    OpenFOAM-v2512 install (probed via the bashrc-sourced runner) must
    be present. Tests that do not set the env var see byte-equal
    historical ``solver_success_blocked`` behavior.
    """

    if os.environ.get(OPENFOAM_LOCAL_RUN_ENV_VAR) != "1":
        return False
    try:
        from kayakgen.eval.cfd.openfoam_v2512_interfoam.runner import (
            is_openfoam_available,
        )
    except ImportError:
        return False
    try:
        return bool(is_openfoam_available())
    except Exception:  # pragma: no cover - defensive
        return False


def _resolve_openfoam_bashrc_path() -> str:
    """Return a string representation of the OpenFOAM bashrc path used by the runner.

    Falls back to the runner's default when neither the env override nor
    a real install is present. The returned string is only used for the
    audit trail; it is not opened by this function.
    """
    try:
        from kayakgen.eval.cfd.openfoam_v2512_interfoam.runner import (
            OPENFOAM_BASHRC,
            OPENFOAM_BASHRC_ENV_VAR,
        )
    except ImportError:
        return ""
    override = os.environ.get(OPENFOAM_BASHRC_ENV_VAR)
    if override:
        return override
    return str(OPENFOAM_BASHRC)


def _build_solver_execution_audit(
    *,
    case: PreparedSolverCase,
    version: str | None,
    solve_seconds: float,
    mesh_seconds: float = 0.0,
    provenance_summary: dict[str, Any] | None = None,
) -> SolverExecutionAudit:
    """Build the audit block emitted alongside a real succeeded record.

    ``mesh_seconds`` defaults to ``0.0`` because the adapter executes a
    single solver command rather than a staged mesh + solve pipeline;
    callers that wrap the staged runner can pass real timings.
    """
    summary: dict[str, Any] = dict(provenance_summary or {})
    if version and "solver_version" not in summary:
        summary["solver_version"] = version
    return SolverExecutionAudit(
        bashrc_path=_resolve_openfoam_bashrc_path(),
        provenance_summary=summary,
        case_template_version=OPENFOAM_CASE_TEMPLATE_VERSION,
        mesh_seconds=mesh_seconds,
        solve_seconds=solve_seconds,
    )


def resolve_real_solver_execution_opt_in(
    job_dir: Path,
    env: dict[str, str] | None = None,
    *,
    config_path: Path | None = None,
) -> RealSolverExecutionOptIn | None:
    """Return the source label that admits a real-solver run, or ``None``.

    Precedence (highest first), per RFC 0046:

    1. ``profile_flag`` — ``profile.json`` carries
       ``allow_real_solver_execution: true``.
    2. ``persistent_setting`` — ``~/.config/kayakgen/cfd.json`` lists the
       job's profile name under ``allow_real_solver_execution_profiles``.
    3. ``env_knob`` — ``KAYAKGEN_OPENFOAM_LOCAL_RUN=1`` is set in
       ``env``.

    The resolver inspects the prepared job directory only; it does not
    probe the toolchain. The adapter is still responsible for checking
    toolchain availability before actually executing.
    """
    env_map = dict(env) if env is not None else dict(os.environ)
    profile_path = Path(job_dir) / "profile.json"
    profile_name: str | None = None
    profile_flag = False
    if profile_path.is_file():
        try:
            profile_payload = json.loads(profile_path.read_text())
        except (OSError, json.JSONDecodeError):
            profile_payload = None
        if isinstance(profile_payload, dict):
            raw_flag = profile_payload.get("allow_real_solver_execution")
            profile_flag = raw_flag is True
            name = profile_payload.get("name")
            if isinstance(name, str):
                profile_name = name

    if profile_flag:
        return "profile_flag"

    if profile_name is not None:
        from kayakgen.eval.cfd.config import load_kayakgen_cfd_config

        try:
            config = load_kayakgen_cfd_config(config_path)
        except Exception:
            config = None
        if config is not None and profile_name in config.allow_real_solver_execution_profiles:
            return "persistent_setting"

    if env_map.get(OPENFOAM_LOCAL_RUN_ENV_VAR) == "1":
        return "env_knob"

    return None


def _format_float(value: float) -> str:
    return f"{value:.12g}"


def _openfoam_control_dict(case: PreparedSolverCase) -> str:
    density = case.job_spec.seawater_density_kg_m3
    return (
        "/* kayakgen deterministic OpenFOAM skeleton controlDict */\n"
        f"// case_template_version {OPENFOAM_CASE_TEMPLATE_VERSION}\n"
        "application interFoam;\n"
        "startFrom startTime;\n"
        "startTime 0;\n"
        "stopAt endTime;\n"
        "endTime 1;\n"
        "deltaT 1;\n"
        "writeControl timeStep;\n"
        "writeInterval 1;\n"
        "purgeWrite 0;\n"
        "functions\n"
        "{\n"
        "    forces\n"
        "    {\n"
        "        type forces;\n"
        "        libs (\"libforces.so\");\n"
        "        patches (hull);\n"
        f"        rhoInf {_format_float(density)};\n"
        "        CofR (0 0 0);\n"
        "        writeControl timeStep;\n"
        "        writeInterval 1;\n"
        "    }\n"
        "}\n"
    )


def _openfoam_transport_properties(case: PreparedSolverCase) -> str:
    nu = case.job_spec.kinematic_viscosity_m2_s
    return (
        "/* kayakgen deterministic OpenFOAM skeleton transportProperties */\n"
        f"// case_template_version {OPENFOAM_CASE_TEMPLATE_VERSION}\n"
        f"nu [0 2 -1 0 0 0 0] {_format_float(nu)};\n"
    )


def _openfoam_gravity_dict() -> str:
    return (
        "/* kayakgen deterministic OpenFOAM skeleton gravity */\n"
        "dimensions [0 1 -2 0 0 0 0];\n"
        "value (0 0 -9.80665);\n"
    )


def _openfoam_turbulence_properties() -> str:
    return (
        "/* kayakgen deterministic OpenFOAM skeleton turbulenceProperties */\n"
        "simulationType laminar;\n"
    )


def _openfoam_fv_schemes() -> str:
    return (
        "/* kayakgen deterministic OpenFOAM skeleton fvSchemes */\n"
        "ddtSchemes { default Euler; }\n"
        "gradSchemes { default Gauss linear; }\n"
        "divSchemes { default none; }\n"
        "laplacianSchemes { default Gauss linear corrected; }\n"
        "interpolationSchemes { default linear; }\n"
        "snGradSchemes { default corrected; }\n"
    )


def _openfoam_fv_solution() -> str:
    return (
        "/* kayakgen deterministic OpenFOAM skeleton fvSolution */\n"
        "solvers { }\n"
        "PIMPLE { nCorrectors 1; nNonOrthogonalCorrectors 0; }\n"
    )


def _openfoam_velocity_field(case: PreparedSolverCase) -> str:
    speed = case.job_spec.speed_mps
    return (
        "/* kayakgen deterministic OpenFOAM skeleton U field */\n"
        "dimensions [0 1 -1 0 0 0 0];\n"
        f"internalField uniform ({_format_float(speed)} 0 0);\n"
        "boundaryField { }\n"
    )


def _openfoam_pressure_field() -> str:
    return (
        "/* kayakgen deterministic OpenFOAM skeleton p_rgh field */\n"
        "dimensions [1 -1 -2 0 0 0 0];\n"
        "internalField uniform 0;\n"
        "boundaryField { }\n"
    )


def _openfoam_alpha_field() -> str:
    return (
        "/* kayakgen deterministic OpenFOAM skeleton alpha.water field */\n"
        "dimensions [0 0 0 0 0 0 0];\n"
        "internalField uniform 1;\n"
        "boundaryField { }\n"
    )


def _openfoam_readme() -> str:
    return (
        "kayakgen OpenFOAM skeleton case\n"
        f"case_template_version: {OPENFOAM_CASE_TEMPLATE_VERSION}\n"
        "This is deterministic adapter scaffolding, not a validated CFD setup.\n"
        "Required CI uses fake commands and parser fixtures; OpenFOAM is not required.\n"
        "A real succeeded OpenFOAM run record is intentionally blocked in this slice.\n"
    )


def _probe_openfoam_version(
    case: PreparedSolverCase,
) -> tuple[str | None, dict[str, str], SolverRawResult | None]:
    version_command = list(case.solver_profile.solver_version_command)
    if not version_command:
        return (
            None,
            {},
            SolverRawResult(
                status="unavailable",
                error_kind="solver_unavailable",
                error_message="OpenFOAM solver version command is not configured",
                raw_records={"version_command": version_command},
                warnings=_openfoam_warnings(),
            ),
        )

    try:
        completed = subprocess.run(
            version_command,
            cwd=case.job_dir,
            capture_output=True,
            check=False,
            text=True,
            timeout=_openfoam_timeout_seconds(case.solver_profile),
        )
    except (FileNotFoundError, PermissionError) as exc:
        completed = subprocess.CompletedProcess(
            args=version_command,
            returncode=127,
            stdout="",
            stderr=str(exc),
        )
        logs = _write_command_logs(
            case.job_dir,
            completed,
            stdout_name="version_stdout.log",
            stderr_name="version_stderr.log",
            max_chars=_openfoam_log_limit_bytes(case.solver_profile),
        )
        return (
            None,
            logs,
            SolverRawResult(
                status="unavailable",
                error_kind="solver_unavailable",
                error_message=f"OpenFOAM version command unavailable: {exc}",
                logs=logs,
                raw_records={"version_command": version_command},
                warnings=_openfoam_warnings(),
            ),
        )
    except subprocess.TimeoutExpired as exc:
        completed = _completed_from_timeout(version_command, exc)
        logs = _write_command_logs(
            case.job_dir,
            completed,
            stdout_name="version_stdout.log",
            stderr_name="version_stderr.log",
            max_chars=_openfoam_log_limit_bytes(case.solver_profile),
        )
        return (
            None,
            logs,
            SolverRawResult(
                status="unavailable",
                error_kind="version_check_timeout",
                error_message=(
                    "OpenFOAM version command timed out after "
                    f"{_openfoam_timeout_seconds(case.solver_profile):g}s"
                ),
                logs=logs,
                raw_records={"version_command": version_command},
                warnings=_openfoam_warnings(),
            ),
        )

    logs = _write_command_logs(
        case.job_dir,
        completed,
        stdout_name="version_stdout.log",
        stderr_name="version_stderr.log",
        max_chars=_openfoam_log_limit_bytes(case.solver_profile),
    )
    version_text = "\n".join(
        part for part in (completed.stdout.strip(), completed.stderr.strip()) if part
    )
    version = _first_nonempty_line(version_text)
    if completed.returncode != 0:
        return (
            version,
            logs,
            SolverRawResult(
                status="unavailable",
                error_kind="version_check_failed",
                error_message=(
                    f"OpenFOAM version command exited with code {completed.returncode}"
                ),
                logs=logs,
                raw_records={
                    "version_command": version_command,
                    "returncode": completed.returncode,
                    "solver_version": version,
                },
                warnings=_openfoam_warnings(),
            ),
        )

    required = case.solver_profile.required_solver_version
    if required and required not in version_text:
        return (
            version,
            logs,
            SolverRawResult(
                status="unavailable",
                error_kind="version_mismatch",
                error_message=(
                    f"OpenFOAM version output did not include required {required!r}"
                ),
                logs=logs,
                raw_records={
                    "version_command": version_command,
                    "solver_version": version,
                    "required_solver_version": required,
                },
                warnings=_openfoam_warnings(),
            ),
        )

    return version, logs, None


class OpenFoamLocalAdapter:
    """OpenFOAM.com v2512 interFoam skeleton adapter.

    The adapter prepares deterministic case files and records dependency,
    command, timeout, and parser failures. It intentionally does not report a
    real ``succeeded`` state in this slice.
    """

    def prepare(self, case: PreparedSolverCase) -> PreparedSolverCase:
        case_root = case.job_dir / OPENFOAM_CASE_ROOT
        logs_dir = case.job_dir / "logs"
        for path in (
            case_root / "0",
            case_root / "constant",
            case_root / "system",
            logs_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

        openfoam_case = CfdOpenFoamCaseInput(
            job_id=case.job_spec.job_id,
            solver_profile=case.job_spec.solver_profile,
            solver_name=case.solver_profile.solver_name or OPENFOAM_SOLVER_NAME,
            required_solver_version=(
                case.solver_profile.required_solver_version or OPENFOAM_REQUIRED_VERSION
            ),
            speed_mps=case.job_spec.speed_mps,
            seawater_density_kg_m3=case.job_spec.seawater_density_kg_m3,
            kinematic_viscosity_m2_s=case.job_spec.kinematic_viscosity_m2_s,
            expected_raw_outputs=list(case.solver_profile.expected_raw_outputs),
            mesh=CfdOpenFoamMeshSummary(
                manifest_ref=case.job_spec.input_manifest,
                mesh_package_ref=case.job_spec.mesh_package_ref,
                hull_hash=case.mesh_manifest.hull_hash,
                body_ref=case.mesh_manifest.body_ref,
                units=case.mesh_manifest.units,
                readiness=case.mesh_manifest.readiness.level,
                solver_profile=case.mesh_manifest.solver_profile.profile_name,
                parts=list(case.mesh_manifest.parts),
                quality_reports={
                    key: value
                    for key, value in sorted(case.mesh_manifest.quality_reports.items())
                },
                surfaces={
                    key: value for key, value in sorted(case.mesh_manifest.surfaces.items())
                },
                volume_mesh_diagnostic=case.mesh_manifest.volume_mesh_diagnostic,
                volume_mesh_artifacts=dict(
                    sorted(case.mesh_manifest.volume_mesh_artifacts.items())
                ),
                evidence_hashes=dict(sorted(case.mesh_manifest.evidence_hashes.items())),
                warnings=list(case.mesh_manifest.warnings),
            ),
            limitations=list(case.solver_profile.known_limitations),
            warnings=_openfoam_warnings(),
        )
        command_spec = CfdOpenFoamCommandSpec(
            command=list(case.solver_profile.command_template),
            version_command=list(case.solver_profile.solver_version_command),
            timeout_seconds=_openfoam_timeout_seconds(case.solver_profile),
            log_limit_bytes=_openfoam_log_limit_bytes(case.solver_profile),
            expected_raw_outputs=list(case.solver_profile.expected_raw_outputs),
        )
        _write_json(case.job_dir / OPENFOAM_CASE_INPUT, openfoam_case)
        _write_json(case.job_dir / OPENFOAM_COMMAND_SPEC, command_spec)
        _write_text(case_root / "system" / "controlDict", _openfoam_control_dict(case))
        _write_text(
            case_root / "constant" / "transportProperties",
            _openfoam_transport_properties(case),
        )
        _write_text(case_root / "constant" / "g", _openfoam_gravity_dict())
        _write_text(
            case_root / "constant" / "turbulenceProperties",
            _openfoam_turbulence_properties(),
        )
        _write_text(case_root / "system" / "fvSchemes", _openfoam_fv_schemes())
        _write_text(case_root / "system" / "fvSolution", _openfoam_fv_solution())
        _write_text(case_root / "0" / "U", _openfoam_velocity_field(case))
        _write_text(case_root / "0" / "p_rgh", _openfoam_pressure_field())
        _write_text(case_root / "0" / "alpha.water", _openfoam_alpha_field())
        _write_text(case_root / "README.kayakgen.txt", _openfoam_readme())
        return case

    def run(self, case: PreparedSolverCase) -> SolverRawResult:
        version, version_logs, version_error = _probe_openfoam_version(case)
        if version_error is not None:
            return version_error

        try:
            _clear_openfoam_run_outputs(case)
        except OSError as exc:
            return SolverRawResult(
                status="failed",
                error_kind="output_cleanup_failed",
                error_message=f"OpenFOAM stale output cleanup failed: {exc}",
                logs=version_logs,
                raw_records={
                    "command": list(case.solver_profile.command_template),
                    "solver_version": version,
                },
                warnings=_openfoam_warnings(),
            )

        solve_start = time.monotonic()
        try:
            completed = subprocess.run(
                case.solver_profile.command_template,
                cwd=case.job_dir,
                capture_output=True,
                check=False,
                text=True,
                timeout=_openfoam_timeout_seconds(case.solver_profile),
            )
        except (FileNotFoundError, PermissionError) as exc:
            completed = subprocess.CompletedProcess(
                args=case.solver_profile.command_template,
                returncode=127,
                stdout="",
                stderr=str(exc),
            )
            command_logs = _write_command_logs(
                case.job_dir,
                completed,
                max_chars=_openfoam_log_limit_bytes(case.solver_profile),
            )
            return SolverRawResult(
                status="unavailable",
                error_kind="solver_unavailable",
                error_message=f"OpenFOAM solver command unavailable: {exc}",
                logs={**version_logs, **command_logs},
                raw_records={
                    "command": list(case.solver_profile.command_template),
                    "solver_version": version,
                },
                warnings=_openfoam_warnings(),
            )
        except subprocess.TimeoutExpired as exc:
            completed = _completed_from_timeout(
                case.solver_profile.command_template,
                exc,
            )
            command_logs = _write_command_logs(
                case.job_dir,
                completed,
                max_chars=_openfoam_log_limit_bytes(case.solver_profile),
            )
            return SolverRawResult(
                status="failed",
                error_kind="timeout",
                error_message=(
                    "OpenFOAM solver command timed out after "
                    f"{_openfoam_timeout_seconds(case.solver_profile):g}s; "
                    "raw solver output is unvalidated"
                ),
                logs={**version_logs, **command_logs},
                raw_records={
                    "command": list(case.solver_profile.command_template),
                    "solver_version": version,
                },
                warnings=_openfoam_warnings(),
            )

        command_logs = _write_command_logs(
            case.job_dir,
            completed,
            max_chars=_openfoam_log_limit_bytes(case.solver_profile),
        )
        logs = {**version_logs, **command_logs}
        if completed.returncode != 0:
            message = (
                f"OpenFOAM solver command exited with code {completed.returncode}; "
                "raw solver output is unvalidated"
            )
            if completed.stderr.strip():
                message = f"{message}: {_cap_text(completed.stderr.strip(), 500)}"
            return SolverRawResult(
                status="failed",
                error_kind="command_failed",
                error_message=message,
                logs=logs,
                raw_records={
                    "returncode": completed.returncode,
                    "solver_version": version,
                },
                warnings=_openfoam_warnings(),
            )

        force_path = case.job_dir / OPENFOAM_CASE_ROOT / OPENFOAM_FORCE_DAT_OUTPUT
        if not force_path.is_file():
            return SolverRawResult(
                status="failed",
                error_kind="missing_output",
                error_message=(
                    "OpenFOAM solver command did not write required "
                    f"{OPENFOAM_FORCE_DAT_OUTPUT}"
                ),
                logs=logs,
                raw_records={
                    "returncode": completed.returncode,
                    "solver_version": version,
                },
                warnings=_openfoam_warnings(),
            )

        try:
            force_result = parse_openfoam_force_dat(
                force_path,
                source_ref=_relative_ref(force_path, case.job_dir),
            )
        except CfdDispatchError as exc:
            return SolverRawResult(
                status="failed",
                error_kind=exc.code,
                error_message=f"{OPENFOAM_FORCE_DAT_OUTPUT} is malformed: {exc}",
                logs=logs,
                raw_records={
                    "returncode": completed.returncode,
                    "solver_version": version,
                },
                warnings=_openfoam_warnings(),
            )

        opt_in = self._attempt_real_succeeded_path(case)
        if opt_in is not None:
            normalized = CfdOpenFoamRawResult(
                job_id=case.job_spec.job_id,
                solver_name=case.solver_profile.solver_name or OPENFOAM_SOLVER_NAME,
                solver_version=version or "",
                speed_mps=case.job_spec.speed_mps,
                seawater_density_kg_m3=case.job_spec.seawater_density_kg_m3,
                kinematic_viscosity_m2_s=case.job_spec.kinematic_viscosity_m2_s,
                mesh_profile=case.mesh_manifest.solver_profile.profile_name,
                mesh_readiness=case.mesh_manifest.readiness.level,
                drag_force_n=force_result.last_sample.drag_force_n,
                raw_output_refs=[force_result.source_ref],
                command=list(case.solver_profile.command_template),
                version_command=list(case.solver_profile.solver_version_command),
                returncode=completed.returncode,
                warnings=[
                    *_openfoam_warnings(),
                    OPENFOAM_SUCCEEDED_RAW_UNVALIDATED_WARNING,
                ],
            )
            _write_json(case.job_dir / OPENFOAM_RAW_RESULT, normalized)
            audit = _build_solver_execution_audit(
                case=case,
                version=version,
                solve_seconds=max(0.0, time.monotonic() - solve_start),
            )
            return SolverRawResult(
                status="succeeded",
                output_manifest=OPENFOAM_RAW_RESULT,
                logs=logs,
                raw_records=normalized.model_dump(mode="python"),
                warnings=list(normalized.warnings),
                real_solver_execution_opt_in=opt_in,
                solver_execution_audit=audit,
            )

        normalized = CfdOpenFoamRawResult(
            job_id=case.job_spec.job_id,
            solver_name=case.solver_profile.solver_name or OPENFOAM_SOLVER_NAME,
            solver_version=version or "",
            speed_mps=case.job_spec.speed_mps,
            seawater_density_kg_m3=case.job_spec.seawater_density_kg_m3,
            kinematic_viscosity_m2_s=case.job_spec.kinematic_viscosity_m2_s,
            mesh_profile=case.mesh_manifest.solver_profile.profile_name,
            mesh_readiness=case.mesh_manifest.readiness.level,
            drag_force_n=force_result.last_sample.drag_force_n,
            raw_output_refs=[force_result.source_ref],
            command=list(case.solver_profile.command_template),
            version_command=list(case.solver_profile.solver_version_command),
            returncode=completed.returncode,
            warnings=[*_openfoam_warnings(), OPENFOAM_SUCCESS_BLOCKED_WARNING],
        )
        _write_json(case.job_dir / OPENFOAM_RAW_RESULT, normalized)
        return SolverRawResult(
            status="failed",
            output_manifest=OPENFOAM_RAW_RESULT,
            error_kind="solver_success_blocked",
            error_message=(
                "OpenFOAM command completed and force.dat parsed, but this skeleton "
                "does not enable real succeeded records until OpenFOAM-readable "
                "volume-mesh evidence is accepted"
            ),
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

    def _attempt_real_succeeded_path(
        self, case: PreparedSolverCase
    ) -> RealSolverExecutionOptIn | None:
        """Return the opt-in label that admits the real succeeded path.

        The resolver enforces RFC 0046 precedence: profile flag wins
        over persistent setting wins over the legacy env knob. If none
        admit the run, returns ``None`` and the adapter falls back to
        the historical ``solver_success_blocked`` path.
        """
        return resolve_real_solver_execution_opt_in(case.job_dir)


__all__ = [
    "CfdOpenFoamCaseInput",
    "CfdOpenFoamCommandSpec",
    "CfdOpenFoamMeshSummary",
    "CfdOpenFoamRawResult",
    "OpenFoamLocalAdapter",
    "resolve_real_solver_execution_opt_in",
]
