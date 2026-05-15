"""End-to-end OpenFOAM-v2512 smoke test.

This test invokes the REAL OpenFOAM-v2512 binaries via the bashrc-sourced
runner and is skipped unless both:

* ``KAYAKGEN_OPENFOAM_SMOKE=1`` is set, AND
* :func:`is_openfoam_available` returns True for the configured bashrc.

Default CI must not run this test; only the operator-driven smoke runs
(typically with ``KAYAKGEN_OPENFOAM_SMOKE=1 KAYAKGEN_OPENFOAM_LOCAL_RUN=1``)
should exercise it.

Pipeline exercised end-to-end:

1. Generate a closed-volume body from a default ``Hull()``.
2. Stitch the body parts into an STL on disk.
3. Render the OpenFOAM case (mesh stage).
4. Run ``blockMesh`` + ``surfaceFeatureExtract`` + ``snappyHexMesh
   -overwrite`` + ``checkMesh``.
5. Probe v2512 provenance via the bashrc runner.
6. Build a :class:`SnappyHexMeshEvidence` record from the case directory.
7. Render the solve-stage controlDict, run ``setFields`` + ``interFoam``.
8. Parse the produced ``force.dat``.
9. Assert a ``CfdRunRecord(status='succeeded', claim_state='raw_unvalidated')``
   can be constructed end-to-end.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest
from stl import mesh as stl_mesh

from kayakgen.eval.cfd.jobs import (
    CfdOpenFoamRawResult,
    CfdRunRecord,
    OPENFOAM_CASE_TEMPLATE_VERSION,
    OPENFOAM_PROFILE_NAME,
    OPENFOAM_REQUIRED_VERSION,
    OpenFoamProvenanceProbe,
    parse_openfoam_force_dat,
    probe_openfoam_provenance,
)
from kayakgen.eval.cfd.openfoam_v2512_interfoam import (
    MeshingResult,
    OpenFoamCaseSpec,
    OpenFoamProbeBashrcRunner,
    SolverResult,
    domain_bounds_from_stl,
    is_openfoam_available,
    render_case,
    run_meshing_stage,
    run_solver_stage,
)
from kayakgen.eval.cfd.openfoam_v2512_interfoam.evidence import (
    build_snappy_hex_mesh_evidence_from_case,
)
from kayakgen.eval.cfd.openfoam_v2512_interfoam.runner import (
    probe_commands_for_bashrc_runner,
)
from kayakgen.eval.generated_closed_body import (
    generated_hull_plus_deck_closed_body,
)
from kayakgen.eval.snappy_hex_mesh import SnappyHexMeshEvidence
from kayakgen.model.hull import Hull


_SMOKE_ENABLED = os.environ.get("KAYAKGEN_OPENFOAM_SMOKE") == "1"
_OPENFOAM_AVAILABLE = is_openfoam_available()

pytestmark = pytest.mark.skipif(
    not (_SMOKE_ENABLED and _OPENFOAM_AVAILABLE),
    reason=(
        "OpenFOAM-v2512 smoke test is opt-in; set KAYAKGEN_OPENFOAM_SMOKE=1 "
        "and ensure /usr/lib/openfoam/openfoam2512/etc/bashrc is sourceable "
        "with interFoam on PATH (override via KAYAKGEN_OPENFOAM_BASHRC)."
    ),
)


def _write_closed_body_stl(target: Path) -> Path:
    """Stitch a generated closed-volume body's parts into a single STL file."""

    hull = Hull()
    body = generated_hull_plus_deck_closed_body(hull)
    vertex_blocks: list[np.ndarray] = []
    face_blocks: list[np.ndarray] = []
    offset = 0
    for part in body.parts:
        verts = np.asarray(part.vertices, dtype=float)
        faces = np.asarray(part.faces, dtype=np.int64)
        vertex_blocks.append(verts)
        face_blocks.append(faces + offset)
        offset += verts.shape[0]
    vertices = np.concatenate(vertex_blocks, axis=0)
    faces = np.concatenate(face_blocks, axis=0)
    mesh_obj = stl_mesh.Mesh(np.zeros(faces.shape[0], dtype=stl_mesh.Mesh.dtype))
    for i, face in enumerate(faces):
        for j in range(3):
            mesh_obj.vectors[i][j] = vertices[face[j], :]
    target.parent.mkdir(parents=True, exist_ok=True)
    mesh_obj.save(str(target))
    return target


def test_full_pipeline_produces_succeeded_record(tmp_path: Path) -> None:
    """Drive case render -> meshing -> evidence -> solver -> succeeded record."""

    hull_stl = _write_closed_body_stl(tmp_path / "hull.stl")
    bounds = domain_bounds_from_stl(hull_stl)
    spec = OpenFoamCaseSpec(
        hull_stl_path=hull_stl,
        domain_bounds=bounds,
        background_cell_size_m=0.25,
        hull_refinement_levels=(2, 3),
        location_in_mesh=(bounds[0] + 0.5, 0.0, bounds[5] - 0.5),
        end_time_s=0.05,
        delta_t_s=0.01,
        inlet_speed_ms=2.0,
        max_global_cells=800_000,
        waterline_z_m=0.0,
    )
    case_dir = tmp_path / "case"
    render_case(spec, case_dir, stage="meshing")

    meshing = run_meshing_stage(case_dir, timeout_s=900)
    assert isinstance(meshing, MeshingResult)
    print(f"meshing seconds: {meshing.seconds:.2f}")
    assert meshing.succeeded, f"meshing failed: {meshing.failure_reason}\n" + "\n".join(
        f"--- {step.name} (rc={step.returncode}) ---\n{step.stdout[-400:]}"
        for step in meshing.steps
    )
    assert meshing.check_mesh_summary is not None
    assert meshing.check_mesh_summary.passed
    assert meshing.check_mesh_summary.n_cells > 0

    probe = probe_openfoam_provenance(
        runner=OpenFoamProbeBashrcRunner(),
        commands=probe_commands_for_bashrc_runner(),
    )
    accepted, reason = probe.matches_required(OPENFOAM_REQUIRED_VERSION)
    assert accepted, f"v2512 provenance probe rejected: {reason}; probe={probe.model_dump()}"

    evidence = build_snappy_hex_mesh_evidence_from_case(
        case_dir,
        spec,
        meshing,
        probe,
    )
    assert isinstance(evidence, SnappyHexMeshEvidence)
    assert evidence.dispatch_state == "evidence_recorded", (
        evidence.dispatch_blocker_codes
    )
    assert evidence.check_mesh is not None and evidence.check_mesh.passed
    assert "controlDict" in evidence.dictionary_hashes
    assert "points" in evidence.artifact_checksums
    assert evidence.openfoam_provenance is not None

    # Solve stage: rewrite controlDict, run setFields + interFoam.
    render_case(spec, case_dir, stage="solve")
    solver = run_solver_stage(case_dir, timeout_s=1800)
    assert isinstance(solver, SolverResult)
    print(f"solver seconds: {solver.seconds:.2f}")
    assert solver.succeeded, f"solver failed: {solver.failure_reason}\n" + "\n".join(
        f"--- {step.name} (rc={step.returncode}) ---\n{step.stdout[-400:]}"
        for step in solver.steps
    )
    assert solver.force_dat_path is not None and solver.force_dat_path.is_file()

    force_result = parse_openfoam_force_dat(solver.force_dat_path)
    assert force_result.sample_count >= 1
    print(
        "force.dat last sample drag (N):",
        force_result.last_sample.drag_force_n,
    )

    raw_result = CfdOpenFoamRawResult(
        job_id="smoke-d012",
        solver_name="OpenFOAM.com OpenFOAM-v2512 interFoam",
        solver_version=probe.application or "OpenFOAM-2512",
        speed_mps=spec.inlet_speed_ms,
        seawater_density_kg_m3=1000.0,
        kinematic_viscosity_m2_s=spec.water_nu_m2_s,
        mesh_profile="watertight_solid_resistance_v1",
        mesh_readiness="cfd_ready",
        drag_force_n=force_result.last_sample.drag_force_n,
        raw_output_refs=[str(solver.force_dat_path)],
        command=["interFoam"],
        version_command=["interFoam", "-help"],
        returncode=0,
    )
    assert raw_result.case_template_version == OPENFOAM_CASE_TEMPLATE_VERSION
    assert raw_result.claim_state == "raw_unvalidated"
    assert raw_result.accepted_uses == []

    record = CfdRunRecord(
        job_id="smoke-d012",
        status="succeeded",
        solver_profile=OPENFOAM_PROFILE_NAME,
        input_manifest=str(hull_stl),
        output_manifest=str(solver.force_dat_path),
        raw_records=raw_result.model_dump(mode="python"),
    )
    assert record.status == "succeeded"
    assert record.raw_records["claim_state"] == "raw_unvalidated"
    assert record.raw_records["accepted_uses"] == []
    assert record.raw_records["case_template_version"] == OPENFOAM_CASE_TEMPLATE_VERSION


def test_provenance_probe_against_real_binary() -> None:
    """The bashrc-sourced probe must accept v2512 from the real banner."""

    probe = probe_openfoam_provenance(
        runner=OpenFoamProbeBashrcRunner(),
        commands=probe_commands_for_bashrc_runner(),
    )
    assert isinstance(probe, OpenFoamProvenanceProbe)
    accepted, reason = probe.matches_required(OPENFOAM_REQUIRED_VERSION)
    assert accepted, f"v2512 provenance probe rejected: {reason}; probe={probe.model_dump()}"
    # Solver-reported probe channels must mention v2512; env-only is not enough.
    application = probe.application or ""
    assert "2512" in application, f"application banner missing v2512: {application!r}"
