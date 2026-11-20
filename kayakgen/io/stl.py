"""STL writer for Hull artifacts."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

import numpy as np
from stl import Mode, mesh as numpy_stl_mesh

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
        mesh_obj.save(str(temporary_path), mode=Mode.BINARY)
        header = f"sha256:{hull.record_hash()} m {part}".encode("ascii").ljust(80, b" ")
        with temporary_path.open("r+b") as artifact:
            artifact.write(header)
        temporary_path.replace(destination)


def write_closed_body_stl(body, path: Path) -> None:
    """Export the same generated closed body used to identify a bound mesh."""
    triangles = [np.asarray(part.vertices)[np.asarray(part.faces, dtype=int)] for part in body.parts]
    vectors = np.concatenate(triangles)
    mesh = numpy_stl_mesh.Mesh(np.zeros(len(vectors), dtype=numpy_stl_mesh.Mesh.dtype))
    mesh.vectors[:] = vectors
    mesh.save(str(path), mode=Mode.BINARY)
    # numpy-stl puts its write time in the header. Prepared jobs hash their inputs.
    with path.open("r+b") as stream:
        stream.write(b"kayakgen generated closed body".ljust(80, b" "))
