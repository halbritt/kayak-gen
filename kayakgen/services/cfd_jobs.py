"""CFD job lifecycle service: prepare, status, run, logs, raw-result fetch.

Wraps :mod:`kayakgen.eval.cfd.jobs` with web-facing argument validation,
path containment, and bounded artifact serialization. Route handlers
translate :class:`CfdWebError` into structured JSON responses.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from kayakgen.eval.cfd.jobs import (
    CFD_RAW_RESULTS_WARNING,
    CfdDispatchError,
    CfdJobSpec,
    CfdRunRecord,
    load_cfd_run_record,
    prepare_cfd_job,
    run_cfd_job,
    solver_profile_by_name,
    solver_profiles,
)
from kayakgen.eval.mesh_package import MeshPackageManifest

CFD_JOBS_ROOT_ENV = "KAYAKGEN_WEB_CFD_JOBS_ROOT"
CFD_ARTIFACT_MAX_BYTES = 64 * 1024
CFD_LOCAL_FILESYSTEM_NOTICE = (
    "Local filesystem CFD jobs on this server only; no hosted worker is running."
)
_CFD_JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class CfdJobCreateRequest(BaseModel):
    """Validated JSON body for the first local web CFD job route."""

    mesh_package_ref: str = Field(min_length=1)
    solver_profile: str = Field(default="unavailable-open-wetted-surface", min_length=1)
    speed_mps: float = Field(gt=0)
    seawater_density_kg_m3: float = Field(default=1025.0, gt=0)
    kinematic_viscosity_m2_s: float = Field(default=1.19e-6, gt=0)
    hull_ref: str | None = None


class CfdWebError(Exception):
    """Structured CFD web error that route handlers can return as JSON."""

    def __init__(self, status: int, payload: dict[str, Any]) -> None:
        super().__init__(str(payload.get("message", payload.get("error", "CFD error"))))
        self.status = status
        self.payload = payload


class CfdWebStore:
    """Server-local, path-bounded root for web CFD job artifacts."""

    def __init__(self, jobs_root: str | Path | None = None) -> None:
        root = Path(jobs_root) if jobs_root is not None else _default_cfd_jobs_root()
        self.jobs_root = root.expanduser().resolve()

    def job_dir(self, job_id: str) -> Path:
        _validate_cfd_job_id(job_id)
        job_dir = (self.jobs_root / job_id).resolve()
        if not _is_relative_to(job_dir, self.jobs_root):
            raise CfdWebError(
                400,
                _cfd_error_payload(
                    "job_path_outside_root",
                    "CFD job id resolves outside the configured local job root.",
                    job_id=job_id,
                ),
            )
        return job_dir

    def existing_job_dir(self, job_id: str) -> Path:
        job_dir = self.job_dir(job_id)
        if not (job_dir / "job.json").is_file():
            raise CfdWebError(
                404,
                _cfd_error_payload("job_not_found", "CFD job record was not found.", job_id=job_id),
            )
        return job_dir


def cfd_profiles_payload(store: CfdWebStore | None = None) -> dict[str, Any]:
    """JSON payload for `GET /api/cfd/profiles`."""
    payload = _cfd_common_payload()
    payload.update(
        {
            "profiles": [profile.model_dump(mode="json") for profile in solver_profiles()],
            "local_filesystem": CFD_LOCAL_FILESYSTEM_NOTICE,
        }
    )
    if store is not None:
        payload["local_jobs_root"] = str(store.jobs_root)
    return payload


def cfd_profile_names() -> list[str]:
    """Return profile names for browser select controls."""
    return [profile.name for profile in solver_profiles()]


def create_cfd_job_payload(raw_payload: dict[str, Any], store: CfdWebStore) -> dict[str, Any]:
    """Prepare a local CFD job and return its web API read model."""
    request = _validate_cfd_create_payload(raw_payload)
    mesh_package = _resolve_mesh_package_ref(request.mesh_package_ref)
    profile = _solver_profile_for_web(request.solver_profile)
    manifest = _load_mesh_manifest_for_context(mesh_package)

    try:
        paths = prepare_cfd_job(
            mesh_package,
            store.jobs_root,
            solver_profile_name=profile.name,
            speed_mps=request.speed_mps,
            seawater_density_kg_m3=request.seawater_density_kg_m3,
            kinematic_viscosity_m2_s=request.kinematic_viscosity_m2_s,
            hull_ref=request.hull_ref,
        )
    except CfdDispatchError as exc:
        raise _cfd_dispatch_web_error(
            exc,
            solver_profile=profile.name,
            profile_required_readiness=profile.required_mesh_readiness,
            required_mesh_profile=profile.required_mesh_profile,
            manifest=manifest,
        ) from exc

    return _cfd_job_payload(paths.job, paths.run, paths.job_dir)


def cfd_job_status_payload(job_id: str, store: CfdWebStore) -> dict[str, Any]:
    """Return current job/run state for a prepared local CFD job."""
    job_dir = store.existing_job_dir(job_id)
    job = _load_cfd_job_spec(job_dir)
    run = _load_cfd_run(job_dir)
    return _cfd_job_payload(job, run, job_dir)


def run_cfd_job_payload(job_id: str, store: CfdWebStore) -> dict[str, Any]:
    """Run the selected local adapter synchronously and return the persisted state."""
    job_dir = store.existing_job_dir(job_id)
    try:
        run = run_cfd_job(job_dir)
    except CfdDispatchError as exc:
        raise CfdWebError(
            500,
            _cfd_error_payload(
                "cfd_dispatch_failed",
                f"CFD local dispatch failed: {exc}",
                job_id=job_id,
            ),
        ) from exc
    job = _load_cfd_job_spec(job_dir)
    return _cfd_job_payload(job, run, job_dir)


def cfd_job_logs_payload(job_id: str, store: CfdWebStore) -> dict[str, Any]:
    """Return bounded text log artifacts for a prepared local CFD job."""
    job_dir = store.existing_job_dir(job_id)
    job = _load_cfd_job_spec(job_dir)
    run = _load_cfd_run(job_dir)
    if not run.logs:
        raise CfdWebError(
            404,
            _cfd_error_payload(
                "logs_not_found",
                "No CFD logs are recorded for this job.",
                job_id=job_id,
            ),
        )

    logs: dict[str, dict[str, Any]] = {}
    for name, ref in sorted(run.logs.items()):
        path = _resolve_job_artifact_path(job_dir, ref)
        if not path.is_file():
            raise CfdWebError(
                404,
                _cfd_error_payload(
                    "log_not_found",
                    "A recorded CFD log artifact was not found.",
                    job_id=job_id,
                    log_name=name,
                    artifact_ref=ref,
                ),
            )
        logs[name] = _read_text_artifact(path, content_type="text/plain; charset=utf-8")
        logs[name]["path"] = ref

    payload = _cfd_common_payload()
    payload.update(
        {
            "job": job.model_dump(mode="json"),
            "run": run.model_dump(mode="json"),
            "logs": logs,
        }
    )
    return payload


def cfd_job_raw_result_payload(job_id: str, store: CfdWebStore) -> dict[str, Any]:
    """Return a bounded raw-result artifact wrapper for a prepared local CFD job."""
    job_dir = store.existing_job_dir(job_id)
    job = _load_cfd_job_spec(job_dir)
    run = _load_cfd_run(job_dir)
    if not run.output_manifest:
        raise CfdWebError(
            404,
            _cfd_error_payload(
                "raw_result_not_found",
                "No raw CFD result artifact is recorded for this job.",
                job_id=job_id,
            ),
        )

    path = _resolve_job_artifact_path(job_dir, run.output_manifest)
    if not path.is_file():
        raise CfdWebError(
            404,
            _cfd_error_payload(
                "raw_result_not_found",
                "The recorded raw CFD result artifact was not found.",
                job_id=job_id,
                artifact_ref=run.output_manifest,
            ),
        )

    size_bytes = path.stat().st_size
    if size_bytes > CFD_ARTIFACT_MAX_BYTES:
        raise CfdWebError(
            413,
            _cfd_error_payload(
                "raw_result_too_large",
                f"Raw CFD result exceeds the first-slice {CFD_ARTIFACT_MAX_BYTES} byte limit.",
                job_id=job_id,
                artifact_ref=run.output_manifest,
                size_bytes=size_bytes,
            ),
        )

    text = path.read_text()
    try:
        raw_result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CfdWebError(
            422,
            _cfd_error_payload(
                "malformed_raw_result",
                "Raw CFD result artifact is not valid JSON.",
                job_id=job_id,
                artifact_ref=run.output_manifest,
            ),
        ) from exc

    payload = _cfd_common_payload()
    payload.update(
        {
            "job": job.model_dump(mode="json"),
            "run": run.model_dump(mode="json"),
            "artifact": {
                "path": run.output_manifest,
                "content_type": "application/json",
                "size_bytes": size_bytes,
                "raw_result": raw_result,
            },
        }
    )
    return payload


def cfd_status_lines_from_payload(payload: dict[str, Any] | None) -> list[str]:
    """Text lines used by the compact browser CFD panel."""
    lines = [
        "CFD local job",
        CFD_RAW_RESULTS_WARNING,
        CFD_LOCAL_FILESYSTEM_NOTICE,
        "fixture-local-command is a deterministic checked-in test adapter, not real CFD.",
    ]
    if not payload:
        return [*lines, "No CFD job prepared."]

    job = payload.get("job", {})
    run = payload.get("run", {})
    status = str(run.get("status", "unknown"))
    lines.extend(
        [
            f"Job ID: {run.get('job_id') or job.get('job_id', '-')}",
            f"Status: {status}",
            f"Solver profile: {run.get('solver_profile') or job.get('solver_profile', '-')}",
        ]
    )
    if job.get("created_at"):
        lines.append(f"Created: {job['created_at']}")
    if run.get("started_at"):
        lines.append(f"Started: {run['started_at']}")
    if run.get("finished_at"):
        lines.append(f"Finished: {run['finished_at']}")
    if run.get("error_kind"):
        lines.append(f"Error kind: {run['error_kind']}")
    if run.get("error_message"):
        lines.append(f"Error message: {run['error_message']}")
    if status in {"unavailable", "failed"}:
        lines.append("Terminal problem state; this is not completed solver work.")
    if status == "succeeded":
        lines.append("Succeeded record is still raw solver output, not validated drag.")
    return lines


def cfd_error_lines_from_payload(
    payload: dict[str, Any],
    title: str = "CFD request failed",
) -> list[str]:
    """Browser lines for structured CFD API errors."""
    lines = [title, CFD_RAW_RESULTS_WARNING]
    if payload.get("message"):
        lines.append(str(payload["message"]))
    if payload.get("error"):
        lines.append(f"Error kind: {payload['error']}")
    if payload.get("solver_profile"):
        lines.append(f"Solver profile: {payload['solver_profile']}")
    if payload.get("required_mesh_readiness") or payload.get("observed_mesh_readiness"):
        lines.append(
            "Readiness: "
            f"required {payload.get('required_mesh_readiness', '-')}, "
            f"observed {payload.get('observed_mesh_readiness', '-')}"
        )
    mismatch = payload.get("mesh_profile_mismatch")
    if isinstance(mismatch, dict):
        lines.append(
            "Mesh profile mismatch: "
            f"required {mismatch.get('required', '-')}, observed {mismatch.get('observed', '-')}"
        )
    return lines


def cfd_logs_lines_from_payload(payload: dict[str, Any]) -> list[str]:
    """Browser lines for CFD log artifacts."""
    lines = ["CFD logs", CFD_RAW_RESULTS_WARNING]
    logs = payload.get("logs", {})
    if not logs:
        return [*lines, "No log artifacts are available."]
    for name, artifact in logs.items():
        suffix = " (truncated)" if artifact.get("truncated") else ""
        lines.append(f"{name}: {artifact.get('path', '-')}{suffix}")
        content = str(artifact.get("content", ""))
        if content:
            lines.extend(f"  {line}" for line in content.splitlines())
    return lines


def cfd_raw_result_lines_from_payload(payload: dict[str, Any]) -> list[str]:
    """Browser lines for raw CFD result artifacts."""
    lines = ["CFD raw artifact", CFD_RAW_RESULTS_WARNING]
    artifact = payload.get("artifact")
    if not isinstance(artifact, dict):
        return [*lines, "No raw-result artifact is available."]
    lines.append(f"Path: {artifact.get('path', '-')}")
    lines.append("Raw solver artifact only; not calibrated or validated.")
    lines.append(json.dumps(artifact.get("raw_result"), indent=2, sort_keys=True))
    return lines


def _default_cfd_jobs_root() -> Path:
    return Path(os.environ.get(CFD_JOBS_ROOT_ENV, ".kayakgen-web-cfd-jobs"))


def _cfd_common_payload() -> dict[str, str]:
    return {
        "result_semantics": "raw_unvalidated",
        "warning": CFD_RAW_RESULTS_WARNING,
    }


def _cfd_error_payload(error: str, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = _cfd_common_payload()
    payload.update({"error": error, "message": message})
    payload.update({key: value for key, value in extra.items() if value is not None})
    return payload


def _validate_cfd_job_id(job_id: str) -> None:
    if job_id in {".", ".."} or "/" in job_id or "\\" in job_id:
        raise CfdWebError(
            400,
            _cfd_error_payload(
                "invalid_job_id",
                "CFD job ids are local names, not filesystem paths.",
                job_id=job_id,
            ),
        )
    if not _CFD_JOB_ID_RE.fullmatch(job_id):
        raise CfdWebError(
            400,
            _cfd_error_payload(
                "invalid_job_id",
                "CFD job id contains unsupported characters.",
                job_id=job_id,
            ),
        )


def _validate_cfd_create_payload(raw_payload: dict[str, Any]) -> CfdJobCreateRequest:
    try:
        return CfdJobCreateRequest.model_validate(raw_payload)
    except ValidationError as exc:
        details = [
            {
                "field": ".".join(str(part) for part in err.get("loc", ())) or "payload",
                "message": str(err.get("msg", "invalid value")),
                "type": str(err.get("type", "value_error")),
            }
            for err in exc.errors()
        ]
        raise CfdWebError(
            400,
            _cfd_error_payload(
                "invalid_cfd_job_payload",
                "Invalid CFD job request payload.",
                details=details,
            ),
        ) from exc


def _resolve_mesh_package_ref(mesh_package_ref: str) -> Path:
    if "://" in mesh_package_ref:
        raise CfdWebError(
            400,
            _cfd_error_payload(
                "invalid_mesh_package_ref",
                "mesh_package_ref must be a server-local filesystem path.",
            ),
        )
    path = Path(mesh_package_ref).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def _solver_profile_for_web(name: str):
    try:
        return solver_profile_by_name(name)
    except CfdDispatchError as exc:
        raise CfdWebError(
            400,
            _cfd_error_payload(
                "unknown_solver_profile",
                str(exc),
                solver_profile=name,
                available_solver_profiles=cfd_profile_names(),
            ),
        ) from exc


def _load_mesh_manifest_for_context(mesh_package: Path) -> MeshPackageManifest | None:
    try:
        return MeshPackageManifest.model_validate_json((mesh_package / "manifest.json").read_text())
    except Exception:
        return None


def _cfd_dispatch_web_error(
    exc: CfdDispatchError,
    *,
    solver_profile: str,
    profile_required_readiness: str,
    required_mesh_profile: str | None,
    manifest: MeshPackageManifest | None,
) -> CfdWebError:
    message = str(exc)
    kind = _cfd_dispatch_error_kind(message)
    status = _cfd_dispatch_error_status(kind)
    extra: dict[str, Any] = {
        "solver_profile": solver_profile,
        "required_mesh_readiness": profile_required_readiness,
        "required_mesh_profile": required_mesh_profile,
    }
    if manifest is not None:
        observed_profile = manifest.solver_profile.profile_name
        extra.update(
            {
                "observed_mesh_readiness": manifest.readiness.level,
                "observed_mesh_profile": observed_profile,
                "mesh_warnings": list(manifest.warnings),
            }
        )
        if required_mesh_profile and observed_profile != required_mesh_profile:
            extra["mesh_profile_mismatch"] = {
                "required": required_mesh_profile,
                "observed": observed_profile,
            }
    return CfdWebError(status, _cfd_error_payload(kind, message, **extra))


def _cfd_dispatch_error_kind(message: str) -> str:
    lowered = message.lower()
    if "unknown solver profile" in lowered:
        return "unknown_solver_profile"
    if "solver profile mismatch" in lowered:
        return "solver_profile_mismatch"
    if "readiness below solver requirement" in lowered:
        return "mesh_readiness_rejected"
    if "watertight dispatch requires" in lowered:
        return "mesh_readiness_rejected"
    if "manifest not found" in lowered:
        return "mesh_package_not_found"
    if "malformed mesh package manifest" in lowered:
        return "malformed_mesh_package"
    if "missing referenced artifact" in lowered:
        return "mesh_package_artifact_missing"
    if "must be positive" in lowered:
        return "invalid_cfd_job_payload"
    return "cfd_dispatch_failed"


def _cfd_dispatch_error_status(kind: str) -> int:
    if kind in {"mesh_readiness_rejected", "solver_profile_mismatch"}:
        return 422
    if kind in {
        "invalid_cfd_job_payload",
        "malformed_mesh_package",
        "mesh_package_artifact_missing",
        "mesh_package_not_found",
        "unknown_solver_profile",
    }:
        return 400
    return 500


def _load_cfd_job_spec(job_dir: Path) -> CfdJobSpec:
    path = job_dir / "job.json"
    try:
        return CfdJobSpec.model_validate_json(path.read_text())
    except FileNotFoundError as exc:
        raise CfdWebError(
            404,
            _cfd_error_payload(
                "job_not_found",
                "CFD job spec was not found.",
                job_id=job_dir.name,
            ),
        ) from exc
    except ValidationError as exc:
        raise CfdWebError(
            500,
            _cfd_error_payload(
                "malformed_job_record",
                "CFD job spec is malformed.",
                job_id=job_dir.name,
            ),
        ) from exc


def _load_cfd_run(job_dir: Path) -> CfdRunRecord:
    path = job_dir / "run.json"
    try:
        return load_cfd_run_record(job_dir)
    except CfdDispatchError as exc:
        if not path.exists():
            raise CfdWebError(
                404,
                _cfd_error_payload(
                    "run_record_not_found",
                    "CFD run record was not found.",
                    job_id=job_dir.name,
                ),
            ) from exc
        raise CfdWebError(
            500,
            _cfd_error_payload(
                "malformed_run_record",
                "CFD run record is malformed.",
                job_id=job_dir.name,
            ),
        ) from exc


def _cfd_job_payload(job: CfdJobSpec, run: CfdRunRecord, job_dir: Path) -> dict[str, Any]:
    payload = _cfd_common_payload()
    payload.update(
        {
            "job_id": job.job_id,
            "status": run.status,
            "solver_profile": run.solver_profile,
            "job_dir": str(job_dir),
            "job": job.model_dump(mode="json"),
            "run": run.model_dump(mode="json"),
            "links": {
                "status": f"/api/cfd/jobs/{job.job_id}",
                "run": f"/api/cfd/jobs/{job.job_id}/run",
                "logs": f"/api/cfd/jobs/{job.job_id}/logs",
                "raw_result": f"/api/cfd/jobs/{job.job_id}/raw-result",
            },
        }
    )
    return payload


def _resolve_job_artifact_path(job_dir: Path, artifact_ref: str) -> Path:
    ref_path = Path(artifact_ref)
    if ref_path.is_absolute():
        raise CfdWebError(
            400,
            _cfd_error_payload(
                "artifact_path_outside_job",
                "CFD artifact references must be relative to the selected job.",
                job_id=job_dir.name,
                artifact_ref=artifact_ref,
            ),
        )
    resolved = (job_dir / ref_path).resolve()
    job_root = job_dir.resolve()
    if not _is_relative_to(resolved, job_root):
        raise CfdWebError(
            400,
            _cfd_error_payload(
                "artifact_path_outside_job",
                "CFD artifact reference resolves outside the selected job directory.",
                job_id=job_dir.name,
                artifact_ref=artifact_ref,
            ),
        )
    return resolved


def _read_text_artifact(path: Path, *, content_type: str) -> dict[str, Any]:
    size_bytes = path.stat().st_size
    with path.open("rb") as handle:
        data = handle.read(CFD_ARTIFACT_MAX_BYTES + 1)
    truncated = len(data) > CFD_ARTIFACT_MAX_BYTES
    if truncated:
        data = data[:CFD_ARTIFACT_MAX_BYTES]
    return {
        "content_type": content_type,
        "size_bytes": size_bytes,
        "truncated": truncated,
        "limit_bytes": CFD_ARTIFACT_MAX_BYTES,
        "content": data.decode("utf-8", errors="replace"),
    }


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
