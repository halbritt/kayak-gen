"""Bind real meshing output to :class:`SnappyHexMeshEvidence`.

After ``snappyHexMesh -overwrite`` finishes, the produced
``constant/polyMesh/{points,faces,owner,neighbour,boundary}`` artifacts
plus the rendered ``system/<dict>`` files are hashed and packaged into
the existing evidence record. The evidence record is then ready for
the watertight-handoff readiness gate or any downstream consumer that
expects fully-bound v2512 evidence.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from kayakgen.eval.cfd.jobs import OpenFoamProvenanceProbe
from kayakgen.eval.cfd.openfoam_v2512_interfoam.case_render import OpenFoamCaseSpec
from kayakgen.eval.cfd.openfoam_v2512_interfoam.runner import MeshingResult
from kayakgen.eval.snappy_hex_mesh import (
    REQUIRED_DICT_KEYS,
    SNAPPYHEXMESH_BODY_PROFILE,
    SNAPPYHEXMESH_REQUIRED_VERSION,
    SnappyHexMeshEvidence,
    SnappyHexMeshPatchEntry,
    build_snappy_hex_mesh_evidence,
)


def sha256_of_path(path: str | Path) -> str:
    """Return the SHA-256 hex digest of the file at ``path``."""

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_dict_filename(key: str) -> str:
    return key


def _patch_role(
    name: str,
    boundary_type: str,
) -> str:
    """Map a polyMesh boundary entry to a :class:`SnappyHexMeshPatchEntry` role."""

    lower = name.lower()
    boundary_lower = boundary_type.lower()
    if lower == "hull":
        return "wetted_body"
    if "inlet" in lower:
        return "inlet"
    if "outlet" in lower:
        return "outlet"
    if "atmosphere" in lower or "top" in lower:
        return "free_surface"
    if "symmetry" in boundary_lower or "leftside" in lower or "rightside" in lower:
        return "symmetry"
    if "bottom" in lower or "floor" in lower:
        return "farfield"
    return "other"


_PATCH_BLOCK_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z_][\w\-]*)\s*\{(?P<body>[^}]*)\}",
    re.MULTILINE | re.DOTALL,
)
_TYPE_RE = re.compile(r"type\s+([A-Za-z_][\w]*)\s*;")
_NFACES_RE = re.compile(r"nFaces\s+(\d+)\s*;")


def read_poly_mesh_patches(boundary_path: str | Path) -> list[SnappyHexMeshPatchEntry]:
    """Parse the ``constant/polyMesh/boundary`` file into patch entries."""

    text = Path(boundary_path).read_text()
    # Strip the leading FoamFile header dictionary so name/body regex starts
    # at the real patch list.
    foamfile = re.search(r"FoamFile\s*\{[^}]*\}", text, re.DOTALL)
    if foamfile is not None:
        text = text[foamfile.end():]
    entries: list[SnappyHexMeshPatchEntry] = []
    for match in _PATCH_BLOCK_RE.finditer(text):
        name = match.group("name")
        body = match.group("body")
        type_match = _TYPE_RE.search(body)
        nfaces_match = _NFACES_RE.search(body)
        if type_match is None or nfaces_match is None:
            continue
        face_count = int(nfaces_match.group(1))
        boundary_type = type_match.group(1)
        entries.append(
            SnappyHexMeshPatchEntry(
                name=name,
                marker=boundary_type,
                role=_patch_role(name, boundary_type),  # type: ignore[arg-type]
                face_count=face_count,
            )
        )
    return entries


def _poly_mesh_artifact_checksums(case_dir: Path) -> dict[str, str]:
    poly = case_dir / "constant" / "polyMesh"
    if not poly.is_dir():
        raise FileNotFoundError(f"polyMesh directory missing: {poly}")
    checksums: dict[str, str] = {}
    for name in ("points", "faces", "owner", "neighbour", "boundary"):
        candidate = poly / name
        if candidate.is_file():
            checksums[name] = sha256_of_path(candidate)
    if "points" not in checksums or "boundary" not in checksums:
        raise FileNotFoundError(
            f"polyMesh missing required artifacts under {poly}: have {sorted(checksums)}"
        )
    return checksums


def _system_dict_hashes(case_dir: Path) -> dict[str, str]:
    system_dir = case_dir / "system"
    hashes: dict[str, str] = {}
    for key in REQUIRED_DICT_KEYS:
        candidate = system_dir / _required_dict_filename(key)
        if not candidate.is_file():
            raise FileNotFoundError(
                f"required system dict not found in case: {candidate}"
            )
        hashes[key] = sha256_of_path(candidate)
    return hashes


def build_snappy_hex_mesh_evidence_from_case(
    case_dir: str | Path,
    spec: OpenFoamCaseSpec,
    meshing_result: MeshingResult,
    provenance: OpenFoamProvenanceProbe,
    *,
    body_ref_hash: str | None = None,
    body_profile: str = SNAPPYHEXMESH_BODY_PROFILE,
    required_version: str = SNAPPYHEXMESH_REQUIRED_VERSION,
) -> SnappyHexMeshEvidence:
    """Bundle case-on-disk hashes, checkMesh, patches, and provenance into one record.

    ``body_ref_hash`` defaults to the SHA-256 of the case's
    ``constant/triSurface/hull.stl`` (i.e. the input hull surface), which
    is the deterministic body identity used elsewhere when no upstream
    closed-volume diagnostic is supplied.
    """

    case_root = Path(case_dir)
    if not case_root.is_dir():
        raise FileNotFoundError(f"case directory does not exist: {case_root}")
    if meshing_result.check_mesh_summary is None:
        raise ValueError("meshing_result.check_mesh_summary is required to build evidence")

    hull_stl = case_root / "constant" / "triSurface" / "hull.stl"
    if not hull_stl.is_file():
        raise FileNotFoundError(f"hull STL not found in case: {hull_stl}")
    resolved_body_ref = body_ref_hash or sha256_of_path(hull_stl)

    dict_hashes = _system_dict_hashes(case_root)
    artifact_checksums = _poly_mesh_artifact_checksums(case_root)
    patch_metadata = read_poly_mesh_patches(case_root / "constant" / "polyMesh" / "boundary")

    return build_snappy_hex_mesh_evidence(
        body_ref_hash=resolved_body_ref,
        body_profile=body_profile,
        dictionary_hashes=dict_hashes,
        patch_metadata=patch_metadata,
        check_mesh=meshing_result.check_mesh_summary,
        artifact_checksums=artifact_checksums,
        openfoam_provenance=provenance,
        required_version=required_version,
    )


__all__ = [
    "build_snappy_hex_mesh_evidence_from_case",
    "read_poly_mesh_patches",
    "sha256_of_path",
]
