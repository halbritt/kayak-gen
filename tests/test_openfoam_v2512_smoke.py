"""Opt-in real OpenCFD meshing, evidence binding, and local solver dispatch."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.cfd.jobs import (
    CfdOpenFoamRawResult, CfdRunRecord, OPENFOAM_CASE_TEMPLATE_VERSION, OPENFOAM_PROFILE_NAME,
    OpenFoamProvenanceProbe, parse_openfoam_force_dat, probe_openfoam_provenance,
)
from kayakgen.eval.cfd.openfoam_v2512_interfoam.runner import (
    OpenFoamProbeBashrcRunner, is_openfoam_available, probe_commands_for_bashrc_runner,
)
from kayakgen.eval.snappy_hex_mesh import SnappyHexMeshEvidence
from kayakgen.io.json import save_hull
from kayakgen.model.hull import Hull

pytestmark = pytest.mark.skipif(
    os.environ.get("KAYAKGEN_OPENFOAM_SMOKE") != "1" or not is_openfoam_available(),
    reason="Set KAYAKGEN_OPENFOAM_SMOKE=1 and select an OpenCFD installation for the real smoke",
)


def test_full_pipeline_produces_succeeded_record(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("KAYAKGEN_OPENFOAM_LOCAL_RUN", "1")
    hull = tmp_path / "hull.json"
    save_hull(Hull(), hull)
    runner = CliRunner()
    evidence_dir, package, jobs = (tmp_path / name for name in ("mesh", "package", "jobs"))
    def invoke(*args):
        result = runner.invoke(app, [str(arg) for arg in args])
        assert result.exit_code == 0, result.output

    invoke("mesh-evidence", hull, "--out", evidence_dir)
    evidence_path = evidence_dir / "evidence.json"
    evidence = SnappyHexMeshEvidence.model_validate_json(evidence_path.read_text())
    assert evidence.dispatch_state == "evidence_recorded", evidence.dispatch_blocker_codes
    assert evidence.check_mesh.passed and evidence.check_mesh.n_cells > 0
    assert "controlDict" in evidence.dictionary_hashes and "points" in evidence.artifact_checksums
    probe = OpenFoamProvenanceProbe.model_validate_json((evidence_dir / "provenance.json").read_text())
    assert evidence.solver_release == probe.release and probe.build
    invoke("mesh-package", hull, "--out", package, "--solver-profile", "watertight-solid",
           "--bind-evidence", evidence_path)
    assert json.loads((package / "manifest.json").read_text())["readiness"]["level"] == "cfd_ready"
    invoke("cfd", "prepare", "--mesh-package", package, "--out", jobs, "--speed-mps", "2",
           "--solver-profile", OPENFOAM_PROFILE_NAME, "--allow-real-solver-execution")
    job, = jobs.glob("cfd-*")
    invoke("cfd", "run", job)
    record = CfdRunRecord.model_validate_json((job / "run.json").read_text())
    assert record.status == "succeeded", record.error_message
    raw = CfdOpenFoamRawResult.model_validate_json((job / "openfoam-raw-result.json").read_text())
    assert raw.solver_release == record.solver_execution_audit.provenance_summary["solver_release"] == probe.release
    assert raw.solver_build == probe.build
    assert raw.case_template_version == OPENFOAM_CASE_TEMPLATE_VERSION
    assert raw.claim_state == record.claim_state == "raw_unvalidated"
    assert raw.accepted_uses == record.accepted_uses == []
    forces = parse_openfoam_force_dat(job / "case/openfoam/postProcessing/forces/0/force.dat")
    assert forces.sample_count > 0 and raw.drag_force_n == forces.last_sample.drag_force_n
    invoke("cfd", "run", job)
    assert CfdRunRecord.model_validate_json((job / "run.json").read_text()) == record


def test_provenance_probe_against_real_binary() -> None:
    """The bashrc-sourced probe must identify the installed release from the real banner."""

    probe = probe_openfoam_provenance(
        runner=OpenFoamProbeBashrcRunner(),
        commands=probe_commands_for_bashrc_runner(),
    )
    assert isinstance(probe, OpenFoamProvenanceProbe)
    accepted, reason = probe.matches_required()
    assert accepted, f"solver provenance probe rejected: {reason}; probe={probe.model_dump()}"
    assert probe.application.startswith("Using: OpenFOAM-" + probe.release[1:])
    assert probe.build
