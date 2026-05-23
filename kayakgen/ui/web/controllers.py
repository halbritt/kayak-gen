"""Thin route/state glue for the kayakgen web UI.

The orchestration logic lives in :mod:`kayakgen.services`. This module
holds the aiohttp route handlers, translates HTTP requests into service
calls, and translates service responses into HTTP responses. It also
re-exports the public service API under the historical
``kayakgen.ui.web.controllers`` namespace so existing imports (tests,
``app.py`` Trame callbacks) keep working byte-stably.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kayakgen.eval.cfd.jobs import CFD_RAW_RESULTS_WARNING
from kayakgen.services.artifacts import (
    HullStore,
    job_stub_payload,
    load_hull_payload,
    stl_bytes_for_part,
    store_hull_payload,
)
from kayakgen.services.cfd_jobs import (
    CFD_ARTIFACT_MAX_BYTES,
    CFD_JOBS_ROOT_ENV,
    CfdJobCreateRequest,
    CfdWebError,
    CfdWebStore,
    cfd_error_lines_from_payload,
    cfd_job_logs_payload,
    cfd_job_raw_result_payload,
    cfd_job_status_payload,
    cfd_logs_lines_from_payload,
    cfd_profile_names,
    cfd_profiles_payload,
    cfd_raw_result_lines_from_payload,
    cfd_status_lines_from_payload,
    create_cfd_job_payload,
    run_cfd_job_payload,
)
from kayakgen.services.generative_jobs import (
    GenerativeJobManager,
    GenerativeJobWebError,
    InProcessGenerativeJobManager,
    cancel_generative_job_payload,
    fork_generative_job_payload,
    generative_job_frontier_payload,
    generative_job_full_payload,
    generative_job_list_payload,
    generative_job_log_payload,
    resume_generative_job_payload,
    start_generative_job_payload,
)
from kayakgen.services.comparison import (
    candidate_state_from_report_json,
    comparison_view_model_from_json,
)
from kayakgen.services.design import (
    CLASS_PRESET_HULL_FIELDS,
    clamp_beam_wl_state,
    class_preset_options,
    class_preset_read_model,
    hull_from_web_state,
    validation_error_payload,
    validity_badge_from_state,
)
from kayakgen.services.evaluation import (
    DISPLAY_CURVE_SPEEDS_KT,
    MESH_PROFILE_ID_TO_LABEL,
    MESH_PROFILE_LABEL_TO_ID,
    WATERTIGHT_SOLID_DISABLED_TOOLTIP,
    analysis_lines_from_state,
    analysis_view_model,
    evaluation_for_state,
    evaluation_payload,
    evaluation_summary,
    hydro_lines_from_state,
    hydro_rows_from_state,
    mesh_diagnostics_lines_from_state,
    mesh_diagnostics_rows_from_state,
    mesh_package_view_model,
    metrics_from_state,
    resistance_table_view_model,
)

# Re-declared as a local literal so RFC 0034 / 0036 surface-copy guards
# (tests/test_web_layout.py) can find this string by scanning ``controllers.py``
# directly. The canonical constant lives in :mod:`kayakgen.services.cfd_jobs`;
# this literal must stay byte-equal to it.
CFD_LOCAL_FILESYSTEM_NOTICE = (
    "Local filesystem CFD jobs on this server only; no hosted worker is running."
)

GENERATIVE_JOBS_ROOT_ENV = "KAYAKGEN_GENERATIVE_JOBS_ROOT"
"""Env var for the in-process generative-job manager's on-disk root."""


__all__ = [
    "CFD_ARTIFACT_MAX_BYTES",
    "CFD_JOBS_ROOT_ENV",
    "CFD_LOCAL_FILESYSTEM_NOTICE",
    "CFD_RAW_RESULTS_WARNING",
    "GENERATIVE_JOBS_ROOT_ENV",
    "GenerativeJobManager",
    "GenerativeJobWebError",
    "InProcessGenerativeJobManager",
    "CLASS_PRESET_HULL_FIELDS",
    "DISPLAY_CURVE_SPEEDS_KT",
    "MESH_PROFILE_ID_TO_LABEL",
    "MESH_PROFILE_LABEL_TO_ID",
    "WATERTIGHT_SOLID_DISABLED_TOOLTIP",
    "CfdJobCreateRequest",
    "CfdWebError",
    "CfdWebStore",
    "HullStore",
    "analysis_lines_from_state",
    "analysis_view_model",
    "candidate_state_from_report_json",
    "cfd_error_lines_from_payload",
    "cfd_job_logs_payload",
    "cfd_job_raw_result_payload",
    "cfd_job_status_payload",
    "cfd_logs_lines_from_payload",
    "cfd_profile_names",
    "cfd_profiles_payload",
    "cfd_raw_result_lines_from_payload",
    "cfd_status_lines_from_payload",
    "cancel_generative_job_payload",
    "fork_generative_job_payload",
    "clamp_beam_wl_state",
    "class_preset_options",
    "class_preset_read_model",
    "comparison_view_model_from_json",
    "create_cfd_job_payload",
    "evaluation_for_state",
    "generative_job_frontier_payload",
    "generative_job_full_payload",
    "generative_job_list_payload",
    "generative_job_log_payload",
    "resume_generative_job_payload",
    "start_generative_job_payload",
    "evaluation_payload",
    "evaluation_summary",
    "hull_from_web_state",
    "hydro_lines_from_state",
    "hydro_rows_from_state",
    "job_stub_payload",
    "load_hull_payload",
    "mesh_diagnostics_lines_from_state",
    "mesh_diagnostics_rows_from_state",
    "mesh_package_view_model",
    "metrics_from_state",
    "register_rest_routes",
    "resistance_table_view_model",
    "run_cfd_job_payload",
    "stl_bytes_for_part",
    "store_hull_payload",
    "validation_error_payload",
    "validity_badge_from_state",
]


def register_rest_routes(
    aiohttp_app: Any,
    store: HullStore | None = None,
    cfd_store: CfdWebStore | None = None,
    cfd_jobs_root: str | Path | None = None,
    generative_manager: GenerativeJobManager | None = None,
    generative_jobs_root: str | Path | None = None,
) -> HullStore:
    """Mount the RFC 0008, local RFC 0018, and RFC 0057 REST APIs on an aiohttp app."""
    from aiohttp import web

    store = store or HullStore()
    cfd_store = cfd_store or CfdWebStore(cfd_jobs_root)
    if generative_manager is None:
        resolved_root = generative_jobs_root or _default_generative_jobs_root()
        generative_manager = InProcessGenerativeJobManager(jobs_root=resolved_root)

    async def request_json(request: Any) -> dict[str, Any]:
        try:
            payload = await request.json()
        except Exception as exc:
            raise CfdWebError(
                400,
                _cfd_invalid_json_payload("Request body must be valid JSON."),
            ) from exc
        if not isinstance(payload, dict):
            raise CfdWebError(
                400,
                _cfd_invalid_json_payload("Request body must be a JSON object."),
            )
        return payload

    def cfd_json_response(payload: dict[str, Any], status: int = 200) -> Any:
        return web.json_response(payload, status=status)

    def cfd_error_response(exc: CfdWebError) -> Any:
        return web.json_response(exc.payload, status=exc.status)

    def cfd_unexpected_response(exc: Exception) -> Any:
        return web.json_response(
            _cfd_unexpected_payload(
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
                headers={
                    "Content-Disposition": f'attachment; filename="kayak_{part}.stl"'
                },
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

    def generative_error_response(exc: GenerativeJobWebError) -> Any:
        return web.json_response(exc.payload, status=exc.status)

    def generative_unexpected_response(exc: Exception) -> Any:
        return web.json_response(
            {
                "result_semantics": "raw_unvalidated",
                "error": "generative_dispatch_failed",
                "message": f"Unexpected generative-job route failure: {type(exc).__name__}",
            },
            status=500,
        )

    async def get_generative_jobs(request: Any) -> Any:
        try:
            state = request.query.get("state")
            kind = request.query.get("kind")
            return web.json_response(
                generative_job_list_payload(
                    generative_manager,
                    state=state,  # type: ignore[arg-type]
                    job_kind=kind,  # type: ignore[arg-type]
                )
            )
        except GenerativeJobWebError as exc:
            return generative_error_response(exc)
        except Exception as exc:
            return generative_unexpected_response(exc)

    async def post_generative_search(request: Any) -> Any:
        try:
            body = await request.json()
            return web.json_response(
                start_generative_job_payload(
                    body, generative_manager, job_kind="search"
                ),
                status=201,
            )
        except GenerativeJobWebError as exc:
            return generative_error_response(exc)
        except Exception as exc:
            return generative_unexpected_response(exc)

    async def post_generative_sweep(request: Any) -> Any:
        try:
            body = await request.json()
            return web.json_response(
                start_generative_job_payload(
                    body, generative_manager, job_kind="sweep"
                ),
                status=201,
            )
        except GenerativeJobWebError as exc:
            return generative_error_response(exc)
        except Exception as exc:
            return generative_unexpected_response(exc)

    async def get_generative_job(request: Any) -> Any:
        try:
            return web.json_response(
                generative_job_full_payload(
                    generative_manager, request.match_info["job_id"]
                )
            )
        except GenerativeJobWebError as exc:
            return generative_error_response(exc)
        except Exception as exc:
            return generative_unexpected_response(exc)

    async def get_generative_job_log(request: Any) -> Any:
        try:
            since_raw = request.query.get("since")
            since_byte = 0
            if since_raw is not None:
                try:
                    since_byte = int(since_raw)
                except ValueError:
                    since_byte = 0
            return web.json_response(
                generative_job_log_payload(
                    generative_manager,
                    request.match_info["job_id"],
                    since_byte=since_byte,
                )
            )
        except GenerativeJobWebError as exc:
            return generative_error_response(exc)
        except Exception as exc:
            return generative_unexpected_response(exc)

    async def get_generative_job_frontier(request: Any) -> Any:
        try:
            return web.json_response(
                generative_job_frontier_payload(
                    generative_manager, request.match_info["job_id"]
                )
            )
        except GenerativeJobWebError as exc:
            return generative_error_response(exc)
        except Exception as exc:
            return generative_unexpected_response(exc)

    async def post_generative_cancel(request: Any) -> Any:
        try:
            return web.json_response(
                cancel_generative_job_payload(
                    generative_manager, request.match_info["job_id"]
                )
            )
        except GenerativeJobWebError as exc:
            return generative_error_response(exc)
        except Exception as exc:
            return generative_unexpected_response(exc)

    async def post_generative_resume(request: Any) -> Any:
        try:
            return web.json_response(
                resume_generative_job_payload(
                    generative_manager, request.match_info["job_id"]
                )
            )
        except GenerativeJobWebError as exc:
            return generative_error_response(exc)
        except Exception as exc:
            return generative_unexpected_response(exc)

    async def post_generative_fork(request: Any) -> Any:
        try:
            try:
                body = await request.json()
            except Exception as exc:
                raise GenerativeJobWebError(
                    400,
                    {
                        "result_semantics": "raw_unvalidated",
                        "error": "invalid_json",
                        "message": "Request body must be valid JSON.",
                    },
                ) from exc
            if not isinstance(body, dict):
                raise GenerativeJobWebError(
                    400,
                    {
                        "result_semantics": "raw_unvalidated",
                        "error": "invalid_request_body",
                        "message": "Request body must be a JSON object.",
                    },
                )
            new_seed = body.get("new_seed")
            if not isinstance(new_seed, int) or isinstance(new_seed, bool):
                raise GenerativeJobWebError(
                    400,
                    {
                        "result_semantics": "raw_unvalidated",
                        "error": "missing_new_seed",
                        "message": (
                            "Request body must include integer 'new_seed'."
                        ),
                    },
                )
            return web.json_response(
                fork_generative_job_payload(
                    generative_manager,
                    request.match_info["job_id"],
                    new_seed=new_seed,
                ),
                status=201,
            )
        except GenerativeJobWebError as exc:
            return generative_error_response(exc)
        except Exception as exc:
            return generative_unexpected_response(exc)

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
    router.add_get("/api/generative-jobs", get_generative_jobs)
    router.add_post("/api/generative-jobs/search", post_generative_search)
    router.add_post("/api/generative-jobs/sweep", post_generative_sweep)
    router.add_get("/api/generative-jobs/{job_id}", get_generative_job)
    router.add_get("/api/generative-jobs/{job_id}/log", get_generative_job_log)
    router.add_get(
        "/api/generative-jobs/{job_id}/frontier", get_generative_job_frontier
    )
    router.add_post("/api/generative-jobs/{job_id}/cancel", post_generative_cancel)
    router.add_post("/api/generative-jobs/{job_id}/resume", post_generative_resume)
    router.add_post("/api/generative-jobs/{job_id}/fork", post_generative_fork)
    return store


def _default_generative_jobs_root() -> Path:
    """Default jobs root for the in-process generative manager.

    Honors ``KAYAKGEN_GENERATIVE_JOBS_ROOT`` for tests/operators that
    want to relocate the on-disk root; otherwise falls back to
    ``~/.local/share/kayakgen/generative_jobs/``.
    """

    import os

    override = os.environ.get(GENERATIVE_JOBS_ROOT_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".local" / "share" / "kayakgen" / "generative_jobs"


def _cfd_invalid_json_payload(message: str) -> dict[str, Any]:
    """Replicate the cfd_jobs error envelope for request-body parsing errors."""
    return {
        "result_semantics": "raw_unvalidated",
        "warning": CFD_RAW_RESULTS_WARNING,
        "error": "invalid_json",
        "message": message,
    }


def _cfd_unexpected_payload(message: str) -> dict[str, Any]:
    """Replicate the cfd_jobs error envelope for unexpected route failures."""
    return {
        "result_semantics": "raw_unvalidated",
        "warning": CFD_RAW_RESULTS_WARNING,
        "error": "cfd_dispatch_failed",
        "message": message,
    }
