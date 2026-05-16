"""Tests for ``CfdRunStage`` and the OpenFOAM adapter's stage emission.

Phase 7 of ``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`` models
the CFD execution pipeline as explicit, named stages on
``CfdRunRecord`` so consumers can see which stage failed without
parsing logs.

The tests split into:

* Binary-free regression coverage that ``stages`` defaults to ``[]``
  on a fresh record and stays empty on the historical
  ``solver_success_blocked`` path.
* Pydantic Literal refusal coverage for ``CfdRunStage.name`` and
  ``CfdRunStage.state``.
* A model round-trip on a hand-built ``CfdRunStage``.
* Env-gated coverage that the OpenFOAM-v2512 adapter emits the
  expected stage sequence on a real ``status='succeeded'`` record.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from kayakgen.eval.cfd.jobs import (
    OPENFOAM_LOCAL_RUN_ENV_VAR,
    OPENFOAM_PROFILE_NAME,
    CfdRunRecord,
    prepare_cfd_job,
    run_cfd_job,
)
from kayakgen.eval.cfd.openfoam_v2512_interfoam import is_openfoam_available
from kayakgen.eval.cfd.records import CfdRunStage
from kayakgen.eval.mesh_package import (
    write_watertight_volume_mesh_handoff_package,
)
from kayakgen.model.hull import Hull


_SMOKE_ENABLED = os.environ.get("KAYAKGEN_OPENFOAM_SMOKE") == "1"
_LOCAL_RUN_ENABLED = os.environ.get(OPENFOAM_LOCAL_RUN_ENV_VAR) == "1"
_OPENFOAM_AVAILABLE = is_openfoam_available()


# ---------------------------------------------------------------------------
# Binary-free regressions and Pydantic refusal coverage


def test_run_record_stages_default_empty() -> None:
    """A freshly-built ``CfdRunRecord`` carries an empty ``stages`` list."""
    record = CfdRunRecord(
        job_id="cfd-stages-default",
        status="queued",
        solver_profile="unavailable-open-wetted-surface",
        input_manifest="../mesh/manifest.json",
    )

    assert record.stages == []
    payload = json.loads(record.model_dump_json())
    assert payload["stages"] == []
    # Round-trip must preserve the empty default.
    assert CfdRunRecord.model_validate_json(record.model_dump_json()) == record


def test_stage_record_round_trips_through_json() -> None:
    """``CfdRunStage.model_dump_json`` round-trips with ``model_validate_json``."""
    stage = CfdRunStage(
        name="solver_execution",
        state="succeeded",
        started_at="2026-05-16T12:34:56Z",
        completed_at="2026-05-16T12:35:10Z",
        wall_clock_seconds=14.0,
        notes=["returncode=0"],
        error_kind=None,
    )

    encoded = stage.model_dump_json()
    decoded = CfdRunStage.model_validate_json(encoded)

    assert decoded == stage
    payload = json.loads(encoded)
    # Sanity: extra-forbid means no leaked keys.
    assert set(payload.keys()) == {
        "name",
        "state",
        "started_at",
        "completed_at",
        "wall_clock_seconds",
        "notes",
        "error_kind",
    }


def test_cfd_run_stage_rejects_unknown_name() -> None:
    """Pydantic must refuse stage names outside the ``CfdRunStageName`` literal."""
    with pytest.raises(ValidationError):
        CfdRunStage(name="not_a_real_stage", state="succeeded")


def test_cfd_run_stage_rejects_unknown_state() -> None:
    """Pydantic must refuse states outside the ``CfdRunStageState`` literal."""
    with pytest.raises(ValidationError):
        CfdRunStage(name="solver_execution", state="not_a_real_state")


# ---------------------------------------------------------------------------
# Blocked-path regression (binary-free)


def _prepare_openfoam_job(tmp_path: Path, *, speed_mps: float = 2.4):
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_watertight_volume_mesh_handoff_package(
        Hull(name="openfoam-stages"),
        mesh_dir,
        stations=8,
        closed_body_stations=8,
        include_fixture_volume_mesh=True,
    )
    return prepare_cfd_job(
        mesh_dir,
        jobs_dir,
        solver_profile_name=OPENFOAM_PROFILE_NAME,
        speed_mps=speed_mps,
    )


def _set_openfoam_profile_fields(job_dir: Path, **updates: object) -> None:
    profile_path = job_dir / "profile.json"
    profile = json.loads(profile_path.read_text())
    assert profile["name"] == OPENFOAM_PROFILE_NAME
    profile.update(updates)
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")


def _install_fake_solver(job_dir: Path) -> None:
    """Install a fake interFoam-equivalent command that emits a v2512 force.dat."""
    _set_openfoam_profile_fields(
        job_dir,
        solver_version_command=[
            sys.executable,
            "-c",
            "print('OpenFOAM-v2512')",
        ],
        command_template=[
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "p=Path('case/openfoam/postProcessing/forces/0/force.dat'); "
                "p.parent.mkdir(parents=True, exist_ok=True); "
                "p.write_text("
                "'# Force\\n"
                "# Time\\ttotal_x total_y total_z\\t"
                "pressure_x pressure_y pressure_z\\t"
                "viscous_x viscous_y viscous_z\\n"
                "0.0 3.5 0.0 0.0 1.0 0.0 0.0 2.5 0.0 0.0\\n'"
                "); "
                "print('fake interFoam completed')"
            ),
        ],
    )


def test_blocked_record_stages_remain_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without opt-in, the adapter's ``solver_success_blocked`` path leaves ``stages=[]``."""
    job = _prepare_openfoam_job(tmp_path)
    _install_fake_solver(job.job_dir)
    monkeypatch.delenv(OPENFOAM_LOCAL_RUN_ENV_VAR, raising=False)

    record = run_cfd_job(job.job_dir)

    assert record.status == "failed"
    assert record.error_kind == "solver_success_blocked"
    assert record.stages == []


# ---------------------------------------------------------------------------
# Env-gated real-binary coverage

_REAL_SUCCEEDED_PATH_AVAILABLE = (
    _SMOKE_ENABLED and _LOCAL_RUN_ENABLED and _OPENFOAM_AVAILABLE
)
_REAL_SUCCEEDED_PATH_SKIP_REASON = (
    "OpenFOAM-v2512 succeeded stage test is opt-in; set "
    "KAYAKGEN_OPENFOAM_SMOKE=1 and KAYAKGEN_OPENFOAM_LOCAL_RUN=1 and "
    "ensure /usr/lib/openfoam/openfoam2512/etc/bashrc is sourceable "
    "(override via KAYAKGEN_OPENFOAM_BASHRC)."
)


_EXPECTED_STAGE_NAMES = [
    "mesh_readiness_evidence",
    "case_render",
    "meshing",
    "mesh_evidence_binding",
    "solver_execution",
    "parser_post_processing",
    "raw_result",
    "validation_gate",
]
_EXPECTED_SKIPPED_STAGE_NAMES = {"mesh_evidence_binding", "validation_gate"}


@pytest.mark.skipif(
    not _REAL_SUCCEEDED_PATH_AVAILABLE,
    reason=_REAL_SUCCEEDED_PATH_SKIP_REASON,
)
def test_succeeded_record_emits_expected_stage_sequence(tmp_path: Path) -> None:
    """The real succeeded path emits the eight named stages in order."""
    job = _prepare_openfoam_job(tmp_path)
    # Env knob is set in the process env (see ``_LOCAL_RUN_ENABLED``);
    # the adapter's RFC 0046 resolver picks it up automatically.

    record = run_cfd_job(job.job_dir)

    assert record.status == "succeeded", (
        f"unexpected status={record.status}, error_kind={record.error_kind}, "
        f"error_message={record.error_message}"
    )
    assert [stage.name for stage in record.stages] == _EXPECTED_STAGE_NAMES
    by_name = {stage.name: stage for stage in record.stages}
    for name in _EXPECTED_STAGE_NAMES:
        stage = by_name[name]
        if name in _EXPECTED_SKIPPED_STAGE_NAMES:
            assert stage.state == "skipped", (
                f"expected {name} to be skipped, got {stage.state}"
            )
        else:
            assert stage.state == "succeeded", (
                f"expected {name} to be succeeded, got {stage.state}"
            )
    assert by_name["validation_gate"].notes == ["validation_gate_not_implemented"]


@pytest.mark.skipif(
    not _REAL_SUCCEEDED_PATH_AVAILABLE,
    reason=_REAL_SUCCEEDED_PATH_SKIP_REASON,
)
def test_succeeded_record_stage_wall_clocks_are_non_negative(tmp_path: Path) -> None:
    """Every emitted stage carries a non-negative or ``None`` wall-clock."""
    job = _prepare_openfoam_job(tmp_path)

    record = run_cfd_job(job.job_dir)

    assert record.status == "succeeded"
    assert record.stages, "expected stages to be populated on the succeeded path"
    for stage in record.stages:
        if stage.wall_clock_seconds is None:
            # Skipped stages legitimately carry no wall-clock.
            assert stage.state == "skipped", (
                f"unexpected None wall-clock on non-skipped stage {stage.name}"
            )
            continue
        assert stage.wall_clock_seconds >= 0.0, (
            f"negative wall-clock on stage {stage.name}: {stage.wall_clock_seconds}"
        )
