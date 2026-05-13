"""Action handlers for the Trame app: rebuild mesh, evaluate, export STL.

These are pure functions of the state dict + a server handle so they can
be unit-tested without a running Vue client.
"""

from __future__ import annotations

import io
from typing import Any

import numpy as np
from pydantic import ValidationError
from stl import mesh as numpy_stl_mesh

from kayakgen.eval.contract import EvaluationResult, ResistanceCurve
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.resistance import KNOTS_TO_MS, evaluate_resistance
from kayakgen.model.advisory import design_advisory
from kayakgen.model.hull import Hull
from kayakgen.ui.web.state import hull_from_state_dict


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
    advisory = design_advisory(hull, cp=h.Cp_actual, displaced_mass_kg=h.displaced_mass_kg)
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
        "advisory_warnings": advisory.warnings,
    }


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
    return EvaluationResult(hull_hash=hull.hash(), hydrostatics=h, resistance=rc)


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


def register_rest_routes(aiohttp_app: Any, store: HullStore | None = None) -> HullStore:
    """Mount the RFC 0008 REST API on an aiohttp application."""
    from aiohttp import web

    store = store or HullStore()

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

    router = aiohttp_app.router
    router.add_post("/api/evaluate", post_evaluate)
    router.add_post("/api/stl", post_stl)
    router.add_post("/api/hulls", post_hulls)
    router.add_get("/api/hulls/{id}", get_hull)
    router.add_post("/api/jobs", post_job)
    router.add_get("/api/jobs/{id}", get_job)
    return store
