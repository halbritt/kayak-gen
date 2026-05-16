"""Artifact export service: STL bytes, hull ID storage, deferred job stubs.

These helpers package per-hull export bytes and read-models that route
handlers serve over the REST surface. They do not touch any HTTP / Trame
state object.
"""

from __future__ import annotations

import io
from typing import Any

import numpy as np
from stl import mesh as numpy_stl_mesh

from kayakgen.eval.cfd.jobs import CFD_RAW_RESULTS_WARNING
from kayakgen.model.hull import Hull
from kayakgen.services.design import hull_from_web_state


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


def store_hull_payload(state: dict[str, Any], store: HullStore) -> dict[str, str]:
    """Store a hull and return its stable ID payload."""
    return {"id": store.put(hull_from_web_state(state))}


def load_hull_payload(hull_id: str, store: HullStore) -> dict[str, Any] | None:
    """Return the stored hull JSON payload, or ``None`` if unknown."""
    hull = store.get(hull_id)
    if hull is None:
        return None
    return hull.model_dump(mode="json")


def job_stub_payload() -> dict[str, str]:
    """Stub payload for the deferred RFC 0008 heavy-job routes."""
    payload: dict[str, str] = {
        "result_semantics": "raw_unvalidated",
        "warning": CFD_RAW_RESULTS_WARNING,
    }
    payload["error"] = (
        "heavy CFD jobs are reserved by RFC 0008 and not implemented; "
        "RFC 0032 acceptance uses the local raw /api/cfd/* route surface"
    )
    return payload
