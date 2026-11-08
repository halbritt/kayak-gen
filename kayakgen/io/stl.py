"""STL writer for Hull artifacts."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

import numpy as np
from stl import mesh as numpy_stl_mesh

from kayakgen.model.hull import Hull

PartType = Literal["hull", "deck"]


def write_stl(hull: Hull, part: PartType, path: str | Path) -> None:
    """Generate ``part`` of ``hull`` and write a binary STL to ``path``."""
    vertices, faces = hull.to_geometry().mesh(part)
    mesh_obj = numpy_stl_mesh.Mesh(np.zeros(len(faces), dtype=numpy_stl_mesh.Mesh.dtype))
    mesh_obj.vectors[:] = vertices[faces]
    destination = Path(path)
    # Keep a prior artifact intact if serialization fails before replacement.
    with TemporaryDirectory(dir=destination.parent, prefix=".kayakgen-stl-") as staging:
        temporary_path = Path(staging) / destination.name
        mesh_obj.save(str(temporary_path))
        temporary_path.replace(destination)
