"""Action handlers for the Trame app: rebuild mesh, evaluate, export STL.

These are pure functions of the state dict + a server handle so they can
be unit-tested without a running Vue client.
"""

from __future__ import annotations

import io
import json
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field, ValidationError
from stl import mesh as numpy_stl_mesh

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
from kayakgen.eval.contract import EvaluationResult, ResistanceCurve, ResistanceMetadata
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.mesh_package import MeshPackageManifest
from kayakgen.eval.resistance import KNOTS_TO_MS, evaluate_resistance, resistance_curve
from kayakgen.model.advisory import design_advisory
from kayakgen.model.hull import Hull
from kayakgen.model.validity import evaluate_design_validity
from kayakgen.search.compare import ComparisonReport
from kayakgen.ui.web.state import HULL_STATE_FIELDS
from kayakgen.ui.web.state import hull_from_state_dict

DISPLAY_CURVE_SPEEDS_KT: tuple[float, ...] = (2.0, 3.0, 4.0, 5.0, 6.0)
CFD_JOBS_ROOT_ENV = "KAYAKGEN_WEB_CFD_JOBS_ROOT"
CFD_ARTIFACT_MAX_BYTES = 64 * 1024
CFD_LOCAL_FILESYSTEM_NOTICE = (
    "Local filesystem CFD jobs on this server only; no hosted worker is running."
)
_CFD_JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def clamp_beam_wl_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with web ``beam_wl_m`` constrained to ``beam_oa_m``."""
    normalized = dict(state)
    beam_oa = normalized.get("beam_oa_m")
    beam_wl = normalized.get("beam_wl_m")
    if beam_oa is None or beam_wl is None:
        return normalized
    try:
        beam_oa_f = float(beam_oa)
        beam_wl_f = float(beam_wl)
    except (TypeError, ValueError):
        return normalized
    if beam_wl_f > beam_oa_f:
        normalized["beam_wl_m"] = beam_oa_f
    return normalized


def hull_from_web_state(state: dict[str, Any]) -> Hull:
    """Build a Hull from web state after applying UI-level normalization."""
    return hull_from_state_dict(clamp_beam_wl_state(state))


def validation_error_payload(exc: Exception) -> dict[str, Any]:
    """Controlled JSON payload for invalid web state."""
    details: list[dict[str, str]] = []
    if isinstance(exc, ValidationError):
        for err in exc.errors():
            loc = ".".join(str(part) for part in err.get("loc", ())) or "state"
            details.append(
                {
                    "field": loc,
                    "message": str(err.get("msg", "invalid value")),
                    "type": str(err.get("type", "value_error")),
                }
            )
    else:
        details.append(
            {
                "field": "state",
                "message": "invalid hull state",
                "type": type(exc).__name__,
            }
        )
    return {"error": "invalid_hull_state", "details": details}


def metrics_from_state(state: dict[str, Any], stations: int = 60) -> dict[str, Any]:
    """Single-shot read model: hydrostatics + at-speed resistance."""
    hull = hull_from_web_state(state)
    h = evaluate_hydrostatics(hull, stations=stations)
    target_kt = float(state.get("target_speed_kt", 3.5))
    V_ms = target_kt * KNOTS_TO_MS
    r = evaluate_resistance(
        hull, V_ms, Sw=h.wetted_surface_m2, n_stations=400, n_depths=20, n_theta=30
    )
    resistance_claim = ResistanceMetadata()
    advisory = design_advisory(
        hull,
        cp=h.Cp_actual,
        displaced_mass_kg=h.displaced_mass_kg,
    )
    return {
        "displaced_mass_kg": h.displaced_mass_kg,
        "wetted_surface_m2": h.wetted_surface_m2,
        "waterplane_area_m2": h.waterplane_area_m2,
        "Cp_actual": h.Cp_actual,
        "Cm_actual": h.Cm_actual,
        "l_over_bwl": advisory.l_over_bwl,
        "Fn": r["Fn"],
        "Rv_N": r["Rv_N"],
        "Rw_N": r["Rw_N"],
        "Rt_N": r["Rt_N"],
        "resistance_claim_state": resistance_claim.claim_state,
        "resistance_accepted_uses": resistance_claim.accepted_uses,
        "resistance_warnings": resistance_claim.warnings,
        "advisory_warnings": advisory.warnings,
        "design_validity": advisory.design_validity.model_dump(mode="json"),
        "design_warning_codes": tuple(
            finding.code
            for finding in advisory.design_validity.findings
            if finding.level == "advisory" and finding.severity == "warning"
        ),
    }


def analysis_view_model(state: dict[str, Any]) -> dict[str, Any]:
    """Build unit-labeled analysis rows for the current web hull state."""
    hull = hull_from_web_state(state)
    hydro = evaluate_hydrostatics(hull, stations=60)
    resistance = resistance_curve(
        hull,
        V_knots=np.array(DISPLAY_CURVE_SPEEDS_KT, dtype=float),
        n_stations=400,
        n_depths=20,
        n_theta=30,
    )
    advisory = design_advisory(
        hull,
        cp=hydro.Cp_actual,
        displaced_mass_kg=hydro.displaced_mass_kg,
    )
    hydro_rows = [
        ("Displacement", f"{hydro.displaced_mass_kg:.1f}", "kg"),
        ("Wetted surface", f"{hydro.wetted_surface_m2:.3f}", "m^2"),
        ("Waterplane area", f"{hydro.waterplane_area_m2:.3f}", "m^2"),
        ("GM0", f"{hydro.GM0_m:.3f}", "m"),
        ("Cp actual", f"{hydro.Cp_actual:.3f}", ""),
        ("Cm actual", f"{hydro.Cm_actual:.3f}", ""),
        ("L/B wl", f"{advisory.l_over_bwl:.2f}", ""),
    ]
    resistance_rows = [
        {
            "speed_kt": speed,
            "Fn": fn,
            "Rv_N": rv,
            "Rw_N": rw,
            "Rt_N": rt,
        }
        for speed, fn, rv, rw, rt in zip(
            resistance.V_knots,
            resistance.Fn,
            resistance.Rv_N,
            resistance.Rw_N,
            resistance.Rt_N,
            strict=True,
        )
    ]
    return {
        "hydro_rows": hydro_rows,
        "resistance_rows": resistance_rows,
        "design_warnings": list(advisory.warnings),
        "design_validity": advisory.design_validity.model_dump(mode="json"),
        "resistance_warnings": list(resistance.metadata.warnings),
        "warnings": [*advisory.warnings, *resistance.metadata.warnings],
        "resistance_metadata": resistance.metadata.model_dump(mode="json"),
    }


def analysis_lines_from_state(state: dict[str, Any]) -> list[str]:
    """Text view of :func:`analysis_view_model` for the current Trame UI."""
    model = analysis_view_model(state)
    lines = ["Hydrostatics"]
    lines.extend(
        f"  {label:<16} {value:>10} {unit}".rstrip()
        for label, value, unit in model["hydro_rows"]
    )
    lines.append("")
    lines.append("Resistance curve (raw comparative filter)")
    lines.append("  kt     Fn     Rv N     Rw N     Rt N")
    lines.extend(
        f"  {row['speed_kt']:>3.1f}  {row['Fn']:>5.2f}  {row['Rv_N']:>7.1f}  "
        f"{row['Rw_N']:>7.1f}  {row['Rt_N']:>7.1f}"
        for row in model["resistance_rows"]
    )
    if model["design_warnings"]:
        lines.extend(
            ["", "Design warnings", *[f"  {warning}" for warning in model["design_warnings"]]]
        )
    if model["resistance_warnings"]:
        lines.extend(
            [
                "",
                "Resistance warnings",
                *[f"  {warning}" for warning in model["resistance_warnings"]],
            ]
        )
    return lines


def comparison_view_model_from_json(payload: str) -> dict[str, Any]:
    """Parse a ``ComparisonReport`` JSON string into display rows."""
    if not payload.strip():
        return {
            "status": "Paste a comparison report JSON to inspect candidates.",
            "lines": [],
            "candidate_options": [],
        }
    try:
        report = ComparisonReport.model_validate_json(payload)
    except Exception as exc:
        return {
            "status": f"Invalid comparison report: {exc}",
            "lines": [],
            "candidate_options": [],
        }

    pareto = set(report.pareto_front_keys)
    lines = [
        f"Report: {report.run_name}",
        f"Kind: {report.report_kind}",
        f"Spec hash: {report.spec_hash[:12]}",
        "",
        "Objectives",
    ]
    if report.objectives:
        lines.extend(
            f"  {objective.metric} ({objective.direction})"
            for objective in report.objectives
        )
    else:
        lines.append("  none")
    if report.warnings:
        lines.extend(["", "Report warnings", *[f"  {warning}" for warning in report.warnings]])

    lines.extend(["", "Candidates", "  idx  status    pareto  key       warnings"])
    for summary in report.candidate_summaries:
        marker = "yes" if summary.candidate_key in pareto else "no"
        warning_text = "; ".join(summary.warnings) if summary.warnings else "-"
        if summary.error:
            warning_text = f"{warning_text}; error: {summary.error}"
        lines.append(
            f"  {summary.candidate_index:>3}  {summary.status:<8}  "
            f"{marker:<6}  {summary.candidate_key[:8]}  {warning_text}"
        )
    return {
        "status": (
            f"{len(report.candidate_summaries)} candidates, "
            f"{len(report.pareto_front_keys)} pareto"
        ),
        "lines": lines,
        "candidate_options": [
            summary.candidate_index for summary in report.candidate_summaries
        ],
    }


def candidate_state_from_report_json(
    payload: str,
    candidate_index: int | str,
    current_state: dict[str, Any],
) -> dict[str, Any]:
    """Apply one report candidate's sweep parameters to current web state."""
    report = ComparisonReport.model_validate_json(payload)
    index = int(candidate_index)
    for summary in report.candidate_summaries:
        if summary.candidate_index != index:
            continue
        updated = dict(current_state)
        for key, value in summary.parameters.items():
            if key in HULL_STATE_FIELDS:
                updated[key] = value
        return clamp_beam_wl_state(updated)
    raise ValueError(f"unknown candidate index: {candidate_index}")


def stl_bytes_for_part(state: dict[str, Any], part: str) -> bytes:
    """Generate a binary STL of ``part`` and return its bytes."""
    hull = hull_from_web_state(state)
    geom = hull.to_geometry()
    vertices, faces = geom.mesh(part)
    data = np.zeros(len(faces), dtype=numpy_stl_mesh.Mesh.dtype)
    obj = numpy_stl_mesh.Mesh(data)
    for i, f in enumerate(faces):
        for j in range(3):
            obj.vectors[i][j] = vertices[f[j], :]
    buf = io.BytesIO()
    obj.save("buf", fh=buf)
    return buf.getvalue()


def evaluation_for_state(state: dict[str, Any]) -> EvaluationResult:
    """Run all evaluators on the state — used by the REST `/api/evaluate` route."""
    hull = hull_from_web_state(state)
    h = evaluate_hydrostatics(hull)
    from kayakgen.eval.resistance import resistance_curve

    rc: ResistanceCurve | None
    try:
        rc = resistance_curve(hull)
    except Exception:
        rc = None
    design_validity = evaluate_design_validity(
        hull,
        cp=h.Cp_actual,
        displaced_mass_kg=h.displaced_mass_kg,
        surface=("web",),
    )
    return EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=h,
        resistance=rc,
        design_validity=design_validity,
    )


class HullStore:
    """Ephemeral in-memory store for RFC 0008 share/API hull IDs."""

    def __init__(self) -> None:
        self._hulls: dict[str, Hull] = {}

    def put(self, hull: Hull) -> str:
        hull_id = hull.hash()
        self._hulls[hull_id] = hull
        return hull_id

    def get(self, hull_id: str) -> Hull | None:
        return self._hulls.get(hull_id)


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
    lines = ["CFD local job", CFD_RAW_RESULTS_WARNING, CFD_LOCAL_FILESYSTEM_NOTICE]
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


def evaluation_payload(state: dict[str, Any]) -> dict[str, Any]:
    """JSON-serializable payload for `POST /api/evaluate`."""
    return evaluation_for_state(state).model_dump(mode="json")


def store_hull_payload(state: dict[str, Any], store: HullStore) -> dict[str, str]:
    """Store a hull and return its stable ID payload."""
    return {"id": store.put(hull_from_web_state(state))}


def load_hull_payload(hull_id: str, store: HullStore) -> dict[str, Any] | None:
    hull = store.get(hull_id)
    if hull is None:
        return None
    return hull.model_dump(mode="json")


def job_stub_payload() -> dict[str, str]:
    return {"error": "heavy CFD jobs are reserved by RFC 0008 and not implemented"}


def register_rest_routes(
    aiohttp_app: Any,
    store: HullStore | None = None,
    cfd_store: CfdWebStore | None = None,
    cfd_jobs_root: str | Path | None = None,
) -> HullStore:
    """Mount the RFC 0008 and local RFC 0018 REST APIs on an aiohttp app."""
    from aiohttp import web

    store = store or HullStore()
    cfd_store = cfd_store or CfdWebStore(cfd_jobs_root)

    async def request_json(request: Any) -> dict[str, Any]:
        try:
            payload = await request.json()
        except Exception as exc:
            raise CfdWebError(
                400,
                _cfd_error_payload(
                    "invalid_json",
                    "Request body must be valid JSON.",
                ),
            ) from exc
        if not isinstance(payload, dict):
            raise CfdWebError(
                400,
                _cfd_error_payload(
                    "invalid_json",
                    "Request body must be a JSON object.",
                ),
            )
        return payload

    def cfd_json_response(payload: dict[str, Any], status: int = 200) -> Any:
        return web.json_response(payload, status=status)

    def cfd_error_response(exc: CfdWebError) -> Any:
        return web.json_response(exc.payload, status=exc.status)

    def cfd_unexpected_response(exc: Exception) -> Any:
        return web.json_response(
            _cfd_error_payload(
                "cfd_dispatch_failed",
                f"Unexpected CFD route failure: {type(exc).__name__}",
            ),
            status=500,
        )

    async def post_evaluate(request: Any) -> Any:
        try:
            return web.json_response(evaluation_payload(await request.json()))
        except Exception as exc:
            return web.json_response(validation_error_payload(exc), status=400)

    async def post_stl(request: Any) -> Any:
        state = await request.json()
        part = request.query.get("part", "hull")
        try:
            return web.Response(
                body=stl_bytes_for_part(state, part),
                content_type="application/sla",
            )
        except Exception as exc:
            return web.json_response(validation_error_payload(exc), status=400)

    async def post_hulls(request: Any) -> Any:
        try:
            return web.json_response(store_hull_payload(await request.json(), store))
        except Exception as exc:
            return web.json_response(validation_error_payload(exc), status=400)

    async def get_hull(request: Any) -> Any:
        payload = load_hull_payload(request.match_info["id"], store)
        if payload is None:
            raise web.HTTPNotFound(text="unknown hull id")
        return web.json_response(payload)

    async def post_job(_request: Any) -> Any:
        return web.json_response(job_stub_payload(), status=501)

    async def get_job(_request: Any) -> Any:
        return web.json_response(job_stub_payload(), status=501)

    async def get_cfd_profiles(_request: Any) -> Any:
        return cfd_json_response(cfd_profiles_payload(cfd_store))

    async def post_cfd_job(request: Any) -> Any:
        try:
            return cfd_json_response(
                create_cfd_job_payload(await request_json(request), cfd_store),
                status=201,
            )
        except CfdWebError as exc:
            return cfd_error_response(exc)
        except Exception as exc:
            return cfd_unexpected_response(exc)

    async def get_cfd_job(request: Any) -> Any:
        try:
            return cfd_json_response(
                cfd_job_status_payload(request.match_info["job_id"], cfd_store)
            )
        except CfdWebError as exc:
            return cfd_error_response(exc)
        except Exception as exc:
            return cfd_unexpected_response(exc)

    async def post_cfd_run(request: Any) -> Any:
        try:
            return cfd_json_response(
                run_cfd_job_payload(request.match_info["job_id"], cfd_store)
            )
        except CfdWebError as exc:
            return cfd_error_response(exc)
        except Exception as exc:
            return cfd_unexpected_response(exc)

    async def get_cfd_logs(request: Any) -> Any:
        try:
            return cfd_json_response(
                cfd_job_logs_payload(request.match_info["job_id"], cfd_store)
            )
        except CfdWebError as exc:
            return cfd_error_response(exc)
        except Exception as exc:
            return cfd_unexpected_response(exc)

    async def get_cfd_raw_result(request: Any) -> Any:
        try:
            return cfd_json_response(
                cfd_job_raw_result_payload(request.match_info["job_id"], cfd_store)
            )
        except CfdWebError as exc:
            return cfd_error_response(exc)
        except Exception as exc:
            return cfd_unexpected_response(exc)

    router = aiohttp_app.router
    router.add_post("/api/evaluate", post_evaluate)
    router.add_post("/api/stl", post_stl)
    router.add_post("/api/hulls", post_hulls)
    router.add_get("/api/hulls/{id}", get_hull)
    router.add_post("/api/jobs", post_job)
    router.add_get("/api/jobs/{id}", get_job)
    router.add_get("/api/cfd/profiles", get_cfd_profiles)
    router.add_post("/api/cfd/jobs", post_cfd_job)
    router.add_get("/api/cfd/jobs/{job_id}", get_cfd_job)
    router.add_post("/api/cfd/jobs/{job_id}/run", post_cfd_run)
    router.add_get("/api/cfd/jobs/{job_id}/logs", get_cfd_logs)
    router.add_get("/api/cfd/jobs/{job_id}/raw-result", get_cfd_raw_result)
    return store
