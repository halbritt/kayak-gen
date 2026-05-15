"""Helpers for sweep-side artifact emission (e.g. per-candidate STL inspection files).

The sweep runner uses these helpers to keep its main loop focused on lifecycle
bookkeeping. STL emission goes through the same ``kayakgen.io.stl.write_stl``
path used by ``kayakgen generate`` so the bytes are equivalent.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from kayakgen.io.stl import write_stl
from kayakgen.model.hull import Hull

STL_HASH_ALGORITHM = "sha256"


class StlArtifact(BaseModel):
    """One STL file produced for a candidate."""

    model_config = ConfigDict(extra="forbid")

    path: str
    bytes: int
    sha256: str


class StlArtifactSet(BaseModel):
    """Sweep-side STL artifacts for one candidate."""

    model_config = ConfigDict(extra="forbid")

    hull: StlArtifact
    deck: StlArtifact


def write_candidate_stl(hull: Hull, candidate_dir: Path, out_root: Path) -> StlArtifactSet:
    """Emit ``hull.stl`` and ``deck.stl`` under ``candidate_dir`` and return artifact records.

    Paths returned in :class:`StlArtifact` records are relative to ``out_root``
    so callers can store them alongside other candidate artifacts.
    """
    candidate_dir.mkdir(parents=True, exist_ok=True)
    hull_path = candidate_dir / "hull.stl"
    deck_path = candidate_dir / "deck.stl"
    write_stl(hull, "hull", hull_path)
    write_stl(hull, "deck", deck_path)
    return StlArtifactSet(
        hull=_artifact(hull_path, out_root),
        deck=_artifact(deck_path, out_root),
    )


def _artifact(path: Path, out_root: Path) -> StlArtifact:
    data = path.read_bytes()
    return StlArtifact(
        path=str(path.relative_to(out_root)),
        bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )
