"""STL writer for Hull artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from kayakgen.model.hull import Hull

PartType = Literal["hull", "deck"]


def write_stl(hull: Hull, part: PartType, path: str | Path) -> None:
    """Generate ``part`` of ``hull`` and write a binary STL to ``path``."""
    geom = hull.to_geometry()
    geom.generate_stl(part, str(path))
