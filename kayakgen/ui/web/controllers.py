"""Action handlers for the Trame app: rebuild mesh, evaluate, export STL.

These are pure functions of the state dict + a server handle so they can
be unit-tested without a running Vue client.
"""

from __future__ import annotations

import io
import struct
from pathlib import Path
from typing import Any

import numpy as np
from stl import mesh as numpy_stl_mesh

from kayakgen.eval.contract import EvaluationResult, ResistanceCurve
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.resistance import KNOTS_TO_MS, evaluate_resistance
from kayakgen.model.hull import Hull
from kayakgen.ui.web.state import HULL_STATE_FIELDS, hull_from_state_dict


def metrics_from_state(state: dict[str, Any], stations: int = 60) -> dict[str, float]:
    """Single-shot read model: hydrostatics + at-speed resistance."""
    hull = hull_from_state_dict(state)
    h = evaluate_hydrostatics(hull, stations=stations)
    target_kt = float(state.get("target_speed_kt", 3.5))
    V_ms = target_kt * KNOTS_TO_MS
    r = evaluate_resistance(
        hull, V_ms, Sw=h.wetted_surface_m2, n_stations=400, n_depths=20, n_theta=30
    )
    return {
        "displaced_mass_kg": h.displaced_mass_kg,
        "wetted_surface_m2": h.wetted_surface_m2,
        "waterplane_area_m2": h.waterplane_area_m2,
        "Cp_actual": h.Cp_actual,
        "Cm_actual": h.Cm_actual,
        "Fn": r["Fn"],
        "Rv_N": r["Rv_N"],
        "Rw_N": r["Rw_N"],
        "Rt_N": r["Rt_N"],
    }


def stl_bytes_for_part(state: dict[str, Any], part: str) -> bytes:
    """Generate a binary STL of ``part`` and return its bytes."""
    hull = hull_from_state_dict(state)
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
    hull = hull_from_state_dict(state)
    h = evaluate_hydrostatics(hull)
    from kayakgen.eval.resistance import resistance_curve

    rc: ResistanceCurve | None
    try:
        rc = resistance_curve(hull)
    except Exception:
        rc = None
    return EvaluationResult(hull_hash=hull.hash(), hydrostatics=h, resistance=rc)
