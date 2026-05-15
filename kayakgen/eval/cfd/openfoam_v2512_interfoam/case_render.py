"""Deterministic OpenFOAM-v2512 case renderer.

Renders the vendored proven case templates into a working case directory:

* ``system/{blockMeshDict, controlDict, fvSchemes, fvSolution,
  meshQualityDict, snappyHexMeshDict, surfaceFeatureExtractDict,
  setFieldsDict}``
* ``constant/{transportProperties, turbulenceProperties, g,
  triSurface/hull.stl}``
* ``0.orig/{alpha.water, U, p_rgh}``

A separate "mesh stage" ``system/controlDict`` is rendered first
(``application blockMesh``) so meshing utilities can be driven from the
same case directory. The solve stage ``controlDict`` is rendered
afterwards (``application interFoam``) with the configured ``endTime``
and the v2512 ``forces`` function object over the hull patch.

The renderer is fully deterministic given an :class:`OpenFoamCaseSpec`:
the same spec produces byte-identical files.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from kayakgen.eval.cfd.jobs import OPENFOAM_CASE_TEMPLATE_VERSION

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# Files keyed by writer-tag. Values are (template-filename, relative-output-path).
_SYSTEM_FILES_MESH_STAGE: tuple[tuple[str, str], ...] = (
    ("system_blockMeshDict.template", "system/blockMeshDict"),
    ("system_controlDict_mesh.template", "system/controlDict"),
    ("system_fvSchemes.template", "system/fvSchemes"),
    ("system_fvSolution.template", "system/fvSolution"),
    ("system_meshQualityDict.template", "system/meshQualityDict"),
    ("system_snappyHexMeshDict.template", "system/snappyHexMeshDict"),
    ("system_surfaceFeatureExtractDict.template", "system/surfaceFeatureExtractDict"),
    ("system_setFieldsDict.template", "system/setFieldsDict"),
)
_SYSTEM_SOLVE_CONTROLDICT: tuple[str, str] = (
    "system_controlDict_solve.template",
    "system/controlDict",
)
_CONSTANT_FILES: tuple[tuple[str, str], ...] = (
    ("constant_g.template", "constant/g"),
    ("constant_transportProperties.template", "constant/transportProperties"),
    ("constant_turbulenceProperties.template", "constant/turbulenceProperties"),
)
_ZERO_ORIG_FILES: tuple[tuple[str, str], ...] = (
    ("zero_alpha_water.template", "0.orig/alpha.water"),
    ("zero_U.template", "0.orig/U"),
    ("zero_p_rgh.template", "0.orig/p_rgh"),
)


class OpenFoamCaseSpec(BaseModel):
    """Deterministic input record for an OpenFOAM-v2512 interFoam case.

    The bounding box and refinement settings are operator-supplied; the
    hull STL must already exist on disk at ``hull_stl_path`` and is copied
    into ``constant/triSurface/hull.stl`` during rendering.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    hull_stl_path: Path
    domain_bounds: tuple[float, float, float, float, float, float]
    background_cell_size_m: float = Field(default=0.25, gt=0.0)
    hull_refinement_levels: tuple[int, int] = (2, 3)
    refinement_box_min: tuple[float, float, float] | None = None
    refinement_box_max: tuple[float, float, float] | None = None
    location_in_mesh: tuple[float, float, float] = (-5.0, 0.0, 1.0)
    end_time_s: float = Field(default=0.05, gt=0.0)
    delta_t_s: float = Field(default=0.01, gt=0.0)
    write_interval_s: float | None = None
    inlet_speed_ms: float = Field(default=2.0, gt=0.0)
    forces_patch_name: Literal["hull"] = "hull"
    max_global_cells: int = Field(default=800_000, gt=0)
    max_local_cells: int = Field(default=200_000, gt=0)
    feature_edge_level: int = Field(default=3, ge=0)
    included_angle_deg: int = Field(default=150, ge=0, le=180)
    waterline_z_m: float = 0.0
    rho_inf_kg_m3: float = Field(default=1000.0, gt=0.0)
    cofr: tuple[float, float, float] = (0.0, 0.0, 0.0)
    water_nu_m2_s: float = Field(default=1.09e-6, gt=0.0)
    water_rho_kg_m3: float = Field(default=998.8, gt=0.0)
    air_nu_m2_s: float = Field(default=1.48e-5, gt=0.0)
    air_rho_kg_m3: float = Field(default=1.0, gt=0.0)


@dataclass(frozen=True)
class OpenFoamCaseRenderedPaths:
    """Stable filesystem paths for a rendered case."""

    case_dir: Path
    system_dir: Path
    constant_dir: Path
    zero_orig_dir: Path
    tri_surface_dir: Path
    hull_stl_path: Path


# ---------------------------------------------------------------------------
# STL bounding box utilities


def stl_bounding_box(
    stl_path: str | Path,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Return ``(min_xyz, max_xyz)`` for the triangle mesh at ``stl_path``."""

    from stl import mesh as stl_mesh  # imported lazily to keep cost out of import

    mesh = stl_mesh.Mesh.from_file(str(stl_path))
    vectors = mesh.vectors.reshape(-1, 3)
    if vectors.size == 0:
        raise ValueError(f"STL file has no triangles: {stl_path}")
    min_xyz = tuple(float(v) for v in np.min(vectors, axis=0))
    max_xyz = tuple(float(v) for v in np.max(vectors, axis=0))
    return min_xyz, max_xyz  # type: ignore[return-value]


def domain_bounds_from_stl(
    stl_path: str | Path,
    *,
    padding_x: tuple[float, float] = (3.0, 5.0),
    padding_y: float = 1.5,
    padding_below: float = 1.5,
    padding_above: float = 1.0,
) -> tuple[float, float, float, float, float, float]:
    """Return ``(x_min, x_max, y_min, y_max, z_min, z_max)`` with paddings.

    The defaults match the proven case: 3 m ahead and 5 m astern of the
    hull bow/stern, 1.5 m beam clearance, 1.5 m below keel, 1.0 m above
    the upper deck. All distances are in meters.
    """

    (min_x, min_y, min_z), (max_x, max_y, max_z) = stl_bounding_box(stl_path)
    return (
        min_x - padding_x[0],
        max_x + padding_x[1],
        min_y - padding_y,
        max_y + padding_y,
        min_z - padding_below,
        max_z + padding_above,
    )


# ---------------------------------------------------------------------------
# Substitution payload assembly


def _substitution_payload(spec: OpenFoamCaseSpec) -> dict[str, str]:
    """Build the full substitution dict used by every template.

    Combining all values into one dict keeps the renderer trivial; the
    ``string.Template`` engine ignores keys that are not referenced.
    Numeric values are formatted deterministically with the ``%g`` rule
    for floats and ``%d`` for ints so two equal specs produce identical
    bytes regardless of upstream provenance.
    """

    x_min, x_max, y_min, y_max, z_min, z_max = spec.domain_bounds
    if x_max <= x_min or y_max <= y_min or z_max <= z_min:
        raise ValueError(
            "OpenFoamCaseSpec.domain_bounds must satisfy x_max>x_min, y_max>y_min, "
            f"z_max>z_min; got ({x_min!r}, {x_max!r}, {y_min!r}, {y_max!r}, "
            f"{z_min!r}, {z_max!r})"
        )

    cell = spec.background_cell_size_m
    nx = max(1, int(round((x_max - x_min) / cell)))
    ny = max(1, int(round((y_max - y_min) / cell)))
    nz = max(1, int(round((z_max - z_min) / cell)))

    # Refinement box: default to a strip hugging the wetted zone.
    box_min = spec.refinement_box_min or (
        x_min + 0.25 * (x_max - x_min),
        y_min + 0.35 * (y_max - y_min),
        z_min + 0.35 * (z_max - z_min),
    )
    box_max = spec.refinement_box_max or (
        x_min + 0.75 * (x_max - x_min),
        y_min + 0.65 * (y_max - y_min),
        z_min + 0.65 * (z_max - z_min),
    )

    waterline = (
        spec.waterline_z_m
        if z_min < spec.waterline_z_m < z_max
        else 0.5 * (z_min + z_max)
    )
    write_interval = (
        spec.write_interval_s if spec.write_interval_s is not None else spec.delta_t_s
    )

    return {
        "case_template_version": OPENFOAM_CASE_TEMPLATE_VERSION,
        # blockMesh
        "x_min": _fmt(x_min),
        "x_max": _fmt(x_max),
        "y_min": _fmt(y_min),
        "y_max": _fmt(y_max),
        "z_min": _fmt(z_min),
        "z_max": _fmt(z_max),
        "nx": str(nx),
        "ny": str(ny),
        "nz": str(nz),
        # snappy
        "refinement_min_x": _fmt(box_min[0]),
        "refinement_min_y": _fmt(box_min[1]),
        "refinement_min_z": _fmt(box_min[2]),
        "refinement_max_x": _fmt(box_max[0]),
        "refinement_max_y": _fmt(box_max[1]),
        "refinement_max_z": _fmt(box_max[2]),
        "surface_level_min": str(int(spec.hull_refinement_levels[0])),
        "surface_level_max": str(int(spec.hull_refinement_levels[1])),
        "location_in_mesh_x": _fmt(spec.location_in_mesh[0]),
        "location_in_mesh_y": _fmt(spec.location_in_mesh[1]),
        "location_in_mesh_z": _fmt(spec.location_in_mesh[2]),
        "max_global_cells": str(int(spec.max_global_cells)),
        "max_local_cells": str(int(spec.max_local_cells)),
        "feature_edge_level": str(int(spec.feature_edge_level)),
        "included_angle_deg": str(int(spec.included_angle_deg)),
        # solve controlDict
        "end_time": _fmt(spec.end_time_s),
        "delta_t": _fmt(spec.delta_t_s),
        "write_interval": _fmt(write_interval),
        "rho_inf": _fmt(spec.rho_inf_kg_m3),
        "forces_patch_name": spec.forces_patch_name,
        "cofr_x": _fmt(spec.cofr[0]),
        "cofr_y": _fmt(spec.cofr[1]),
        "cofr_z": _fmt(spec.cofr[2]),
        # setFields waterline
        "waterline_z": _fmt(waterline),
        # transportProperties
        "water_nu": _fmt(spec.water_nu_m2_s),
        "water_rho": _fmt(spec.water_rho_kg_m3),
        "air_nu": _fmt(spec.air_nu_m2_s),
        "air_rho": _fmt(spec.air_rho_kg_m3),
        # zero/U
        "inlet_speed_ms": _fmt(spec.inlet_speed_ms),
    }


def _fmt(value: float) -> str:
    """Deterministic compact float formatter."""
    return f"{float(value):.12g}"


def _render_template(template_filename: str, substitutions: dict[str, str]) -> str:
    template_path = TEMPLATES_DIR / template_filename
    raw = template_path.read_text()
    # ``string.Template`` only substitutes ``${name}`` placeholders, leaving the
    # OpenFOAM-native ``$U`` / ``$p_rgh`` style alone.
    return Template(raw).safe_substitute(substitutions)


# ---------------------------------------------------------------------------
# Public renderer entry point


def render_case(
    spec: OpenFoamCaseSpec,
    case_dir: str | Path,
    *,
    stage: Literal["meshing", "solve"] = "meshing",
) -> OpenFoamCaseRenderedPaths:
    """Write the full case under ``case_dir`` based on ``spec``.

    ``stage`` selects which ``system/controlDict`` is written:

    * ``"meshing"`` writes the mesh-stage controlDict (``application
      blockMesh``); call this first when preparing the case.
    * ``"solve"`` overwrites ``system/controlDict`` with the interFoam
      stage version; call this after meshing succeeds.

    The hull STL is copied from ``spec.hull_stl_path`` to
    ``constant/triSurface/hull.stl`` only on the meshing stage. On the
    solve stage the STL copy is skipped to keep the renderer idempotent.
    """

    case_root = Path(case_dir)
    case_root.mkdir(parents=True, exist_ok=True)
    system_dir = case_root / "system"
    constant_dir = case_root / "constant"
    zero_orig_dir = case_root / "0.orig"
    tri_surface_dir = constant_dir / "triSurface"
    for path in (system_dir, constant_dir, zero_orig_dir, tri_surface_dir):
        path.mkdir(parents=True, exist_ok=True)

    substitutions = _substitution_payload(spec)

    if stage == "meshing":
        for template_filename, relative in _SYSTEM_FILES_MESH_STAGE:
            (case_root / relative).write_text(
                _render_template(template_filename, substitutions)
            )
        for template_filename, relative in _CONSTANT_FILES:
            (case_root / relative).write_text(
                _render_template(template_filename, substitutions)
            )
        for template_filename, relative in _ZERO_ORIG_FILES:
            (case_root / relative).write_text(
                _render_template(template_filename, substitutions)
            )
        hull_dest = tri_surface_dir / "hull.stl"
        hull_src = Path(spec.hull_stl_path)
        if not hull_src.is_file():
            raise FileNotFoundError(
                f"OpenFoamCaseSpec.hull_stl_path is not a file: {hull_src}"
            )
        shutil.copyfile(hull_src, hull_dest)
    elif stage == "solve":
        template_filename, relative = _SYSTEM_SOLVE_CONTROLDICT
        (case_root / relative).write_text(
            _render_template(template_filename, substitutions)
        )
    else:  # pragma: no cover - guarded by Literal
        raise ValueError(f"unsupported render stage: {stage!r}")

    return OpenFoamCaseRenderedPaths(
        case_dir=case_root,
        system_dir=system_dir,
        constant_dir=constant_dir,
        zero_orig_dir=zero_orig_dir,
        tri_surface_dir=tri_surface_dir,
        hull_stl_path=tri_surface_dir / "hull.stl",
    )


__all__ = [
    "OpenFoamCaseSpec",
    "OpenFoamCaseRenderedPaths",
    "render_case",
    "domain_bounds_from_stl",
    "stl_bounding_box",
    "TEMPLATES_DIR",
]
