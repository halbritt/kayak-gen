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
from kayakgen.eval.resistance import KNOTS_TO_MS, evaluate_resistance, resistance_curve
from kayakgen.model.advisory import design_advisory
from kayakgen.model.hull import Hull
from kayakgen.search.compare import ComparisonReport
from kayakgen.ui.web.state import HULL_STATE_FIELDS
from kayakgen.ui.web.state import hull_from_state_dict

DISPLAY_CURVE_SPEEDS_KT: tuple[float, ...] = (2.0, 3.0, 4.0, 5.0, 6.0)


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
    if model["warnings"]:
        lines.extend(["", "Warnings", *[f"  {warning}" for warning in model["warnings"]]])
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
