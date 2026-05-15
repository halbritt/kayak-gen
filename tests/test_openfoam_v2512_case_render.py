"""Binary-free unit tests for the OpenFOAM-v2512 case renderer.

These tests never invoke OpenFOAM. They check the rendered case-tree
shape, byte-determinism, parameter substitution, the controlDict
forces function object wiring, and that the locked
``OPENFOAM_CASE_TEMPLATE_VERSION`` module constant flows through to
every system dictionary.
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

import numpy as np
import pytest
from stl import mesh as stl_mesh

from kayakgen.eval.cfd.jobs import OPENFOAM_CASE_TEMPLATE_VERSION
from kayakgen.eval.cfd.openfoam_v2512_interfoam.case_render import (
    OpenFoamCaseSpec,
    OpenFoamCaseRenderedPaths,
    domain_bounds_from_stl,
    render_case,
    stl_bounding_box,
)


def _write_unit_cube_stl(target: Path) -> Path:
    """Write a tiny 8-triangle cube STL so tests do not require a real hull."""

    vertices = np.array(
        [
            [-1.0, -0.5, -0.3],
            [1.0, -0.5, -0.3],
            [1.0, 0.5, -0.3],
            [-1.0, 0.5, -0.3],
            [-1.0, -0.5, 0.3],
            [1.0, -0.5, 0.3],
            [1.0, 0.5, 0.3],
            [-1.0, 0.5, 0.3],
        ],
        dtype=float,
    )
    faces = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],
            [4, 6, 5],
            [4, 7, 6],
            [0, 4, 5],
            [0, 5, 1],
            [1, 5, 6],
            [1, 6, 2],
            [2, 6, 7],
            [2, 7, 3],
            [3, 7, 4],
            [3, 4, 0],
        ],
        dtype=np.int64,
    )
    cube = stl_mesh.Mesh(np.zeros(faces.shape[0], dtype=stl_mesh.Mesh.dtype))
    for i, face in enumerate(faces):
        for j in range(3):
            cube.vectors[i][j] = vertices[face[j], :]
    target.parent.mkdir(parents=True, exist_ok=True)
    cube.save(str(target))
    return target


def _make_spec(hull_stl: Path) -> OpenFoamCaseSpec:
    return OpenFoamCaseSpec(
        hull_stl_path=hull_stl,
        domain_bounds=(-7.0, 9.0, -2.0, 2.0, -1.5, 1.5),
        background_cell_size_m=0.25,
        hull_refinement_levels=(2, 3),
        location_in_mesh=(-5.0, 0.0, 1.0),
        end_time_s=0.05,
        delta_t_s=0.01,
        inlet_speed_ms=2.0,
        max_global_cells=800_000,
        waterline_z_m=0.0,
    )


def test_render_case_writes_full_case_tree(tmp_path: Path) -> None:
    hull_stl = _write_unit_cube_stl(tmp_path / "hull.stl")
    spec = _make_spec(hull_stl)
    case_dir = tmp_path / "case"
    rendered = render_case(spec, case_dir)
    assert isinstance(rendered, OpenFoamCaseRenderedPaths)
    expected = [
        "system/blockMeshDict",
        "system/controlDict",
        "system/fvSchemes",
        "system/fvSolution",
        "system/meshQualityDict",
        "system/snappyHexMeshDict",
        "system/surfaceFeatureExtractDict",
        "system/setFieldsDict",
        "constant/g",
        "constant/transportProperties",
        "constant/turbulenceProperties",
        "constant/triSurface/hull.stl",
        "0.orig/alpha.water",
        "0.orig/U",
        "0.orig/p_rgh",
    ]
    for rel in expected:
        assert (case_dir / rel).is_file(), f"missing rendered file: {rel}"


def test_render_case_is_deterministic_given_same_spec(tmp_path: Path) -> None:
    hull_stl = _write_unit_cube_stl(tmp_path / "hull.stl")
    spec = _make_spec(hull_stl)
    case_a = tmp_path / "case_a"
    case_b = tmp_path / "case_b"
    render_case(spec, case_a)
    render_case(spec, case_b)
    for rel in (
        "system/blockMeshDict",
        "system/controlDict",
        "system/snappyHexMeshDict",
        "system/setFieldsDict",
        "0.orig/U",
        "constant/transportProperties",
    ):
        assert (case_a / rel).read_bytes() == (case_b / rel).read_bytes(), rel


def test_blockmesh_dict_contains_domain_bounds(tmp_path: Path) -> None:
    hull_stl = _write_unit_cube_stl(tmp_path / "hull.stl")
    spec = _make_spec(hull_stl)
    case_dir = tmp_path / "case"
    render_case(spec, case_dir)
    text = (case_dir / "system" / "blockMeshDict").read_text()
    # Vertices line for the lower-left corner must carry the configured bounds.
    assert "(-7 -2 -1.5)" in text
    assert "(9 2 1.5)" in text
    # 16/0.25 = 64, 4/0.25 = 16, 3/0.25 = 12 background cells.
    assert "(64 16 12)" in text


def test_snappy_dict_contains_locked_case_template_version_via_module_constant(
    tmp_path: Path,
) -> None:
    hull_stl = _write_unit_cube_stl(tmp_path / "hull.stl")
    spec = _make_spec(hull_stl)
    case_dir = tmp_path / "case"
    render_case(spec, case_dir)
    snappy = (case_dir / "system" / "snappyHexMeshDict").read_text()
    assert OPENFOAM_CASE_TEMPLATE_VERSION in snappy
    # Surface refinement levels and locationInMesh substituted correctly.
    assert "level (2 3)" in snappy
    assert "locationInMesh  (-5 0 1)" in snappy
    assert "maxGlobalCells      800000" in snappy


def test_controldict_carries_forces_function_object_over_hull_patch(
    tmp_path: Path,
) -> None:
    hull_stl = _write_unit_cube_stl(tmp_path / "hull.stl")
    spec = _make_spec(hull_stl)
    case_dir = tmp_path / "case"
    # The default meshing-stage controlDict does NOT carry the forces FO;
    # only the solve-stage controlDict does, which is rendered second.
    render_case(spec, case_dir, stage="meshing")
    mesh_stage = (case_dir / "system" / "controlDict").read_text()
    assert "application     blockMesh;" in mesh_stage
    assert "forces" not in mesh_stage

    render_case(spec, case_dir, stage="solve")
    solve_stage = (case_dir / "system" / "controlDict").read_text()
    assert "application     interFoam;" in solve_stage
    assert "type            forces;" in solve_stage
    assert "patches         (hull);" in solve_stage
    assert "endTime         0.05;" in solve_stage
    assert "deltaT          0.01;" in solve_stage
    assert OPENFOAM_CASE_TEMPLATE_VERSION in solve_stage


def test_renderer_substitutes_inlet_speed_in_U_field(tmp_path: Path) -> None:
    hull_stl = _write_unit_cube_stl(tmp_path / "hull.stl")
    spec = OpenFoamCaseSpec(
        hull_stl_path=hull_stl,
        domain_bounds=(-7.0, 9.0, -2.0, 2.0, -1.5, 1.5),
        inlet_speed_ms=3.25,
    )
    case_dir = tmp_path / "case"
    render_case(spec, case_dir)
    u_field = (case_dir / "0.orig" / "U").read_text()
    assert "internalField   uniform (3.25 0 0)" in u_field
    assert "value           uniform (3.25 0 0)" in u_field


def test_stl_bounding_box_and_default_domain_bounds(tmp_path: Path) -> None:
    hull_stl = _write_unit_cube_stl(tmp_path / "hull.stl")
    min_xyz, max_xyz = stl_bounding_box(hull_stl)
    assert min_xyz == pytest.approx((-1.0, -0.5, -0.3))
    assert max_xyz == pytest.approx((1.0, 0.5, 0.3))
    bounds = domain_bounds_from_stl(hull_stl)
    assert bounds[0] == pytest.approx(-4.0)
    assert bounds[1] == pytest.approx(6.0)
    assert bounds[2] == pytest.approx(-2.0)
    assert bounds[3] == pytest.approx(2.0)
    assert bounds[4] == pytest.approx(-1.8)
    assert bounds[5] == pytest.approx(1.3)


def test_render_case_solve_stage_does_not_overwrite_hull_stl(tmp_path: Path) -> None:
    hull_stl = _write_unit_cube_stl(tmp_path / "hull.stl")
    spec = _make_spec(hull_stl)
    case_dir = tmp_path / "case"
    render_case(spec, case_dir, stage="meshing")
    hull_dest = case_dir / "constant" / "triSurface" / "hull.stl"
    hull_hash_before = hashlib.sha256(hull_dest.read_bytes()).hexdigest()
    render_case(spec, case_dir, stage="solve")
    hull_hash_after = hashlib.sha256(hull_dest.read_bytes()).hexdigest()
    assert hull_hash_before == hull_hash_after
