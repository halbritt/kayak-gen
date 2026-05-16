"""Tests for the RFC 0046 real-solver-execution opt-in resolver.

The resolver applies three opt-in mechanisms in precedence order:

1. Profile flag (``allow_real_solver_execution: true`` in ``profile.json``)
2. Persistent setting (``~/.config/kayakgen/cfd.json`` profile allowlist)
3. Env knob (``KAYAKGEN_OPENFOAM_LOCAL_RUN=1``)

The tests cover precedence, audit-trail wiring on the succeeded
``CfdRunRecord``, and a regression that the historical
``solver_success_blocked`` path still leaves the new fields ``None``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from kayakgen.eval.cfd.config import KayakgenCfdConfig
from kayakgen.eval.cfd.jobs import (
    OPENFOAM_CASE_TEMPLATE_VERSION,
    OPENFOAM_LOCAL_RUN_ENV_VAR,
    OPENFOAM_PROFILE_NAME,
    OPENFOAM_RAW_RESULT,
    SolverExecutionAudit,
    prepare_cfd_job,
    resolve_real_solver_execution_opt_in,
    run_cfd_job,
)
from kayakgen.eval.mesh_package import (
    write_watertight_volume_mesh_handoff_package,
)
from kayakgen.model.hull import Hull


def _prepare_openfoam_job(tmp_path: Path, *, speed_mps: float = 2.4):
    mesh_dir = tmp_path / "mesh"
    jobs_dir = tmp_path / "jobs"
    write_watertight_volume_mesh_handoff_package(
        Hull(name="openfoam-rfc0046"),
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


def _write_persistent_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    profiles: list[str],
) -> Path:
    """Point ``load_kayakgen_cfd_config`` at a temp-dir cfd.json with ``profiles``."""
    config_path = tmp_path / "cfd.json"
    config_path.write_text(
        json.dumps({"allow_real_solver_execution_profiles": profiles}) + "\n"
    )
    import kayakgen.eval.cfd.config as config_module

    monkeypatch.setattr(
        config_module,
        "DEFAULT_KAYAKGEN_CFD_CONFIG_PATH",
        config_path,
    )
    return config_path


# ---------------------------------------------------------------------------
# Resolver precedence


def test_opt_in_resolver_profile_flag_wins_over_persistent_and_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    job = _prepare_openfoam_job(tmp_path)
    _set_openfoam_profile_fields(job.job_dir, allow_real_solver_execution=True)
    _write_persistent_config(monkeypatch, tmp_path, [OPENFOAM_PROFILE_NAME])
    monkeypatch.setenv(OPENFOAM_LOCAL_RUN_ENV_VAR, "1")

    label = resolve_real_solver_execution_opt_in(job.job_dir)

    assert label == "profile_flag"


def test_opt_in_resolver_persistent_setting_wins_over_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    job = _prepare_openfoam_job(tmp_path)
    # Profile flag NOT set; persistent setting and env knob both set.
    _write_persistent_config(monkeypatch, tmp_path, [OPENFOAM_PROFILE_NAME])
    monkeypatch.setenv(OPENFOAM_LOCAL_RUN_ENV_VAR, "1")

    label = resolve_real_solver_execution_opt_in(job.job_dir)

    assert label == "persistent_setting"


def test_opt_in_resolver_env_knob_still_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    job = _prepare_openfoam_job(tmp_path)
    # Neither profile flag nor persistent setting; env knob alone.
    _write_persistent_config(monkeypatch, tmp_path, [])
    monkeypatch.setenv(OPENFOAM_LOCAL_RUN_ENV_VAR, "1")

    label = resolve_real_solver_execution_opt_in(job.job_dir)

    assert label == "env_knob"


def test_opt_in_resolver_returns_none_when_nothing_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    job = _prepare_openfoam_job(tmp_path)
    _write_persistent_config(monkeypatch, tmp_path, [])
    monkeypatch.delenv(OPENFOAM_LOCAL_RUN_ENV_VAR, raising=False)

    label = resolve_real_solver_execution_opt_in(job.job_dir)

    assert label is None


# ---------------------------------------------------------------------------
# Audit trail wiring on succeeded record


def test_succeeded_record_carries_opt_in_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The persistent-setting opt-in produces a succeeded record stamped accordingly."""
    job = _prepare_openfoam_job(tmp_path)
    _install_fake_solver(job.job_dir)
    _write_persistent_config(monkeypatch, tmp_path, [OPENFOAM_PROFILE_NAME])
    monkeypatch.delenv(OPENFOAM_LOCAL_RUN_ENV_VAR, raising=False)

    record = run_cfd_job(job.job_dir)

    assert record.status == "succeeded"
    assert record.error_kind is None
    assert record.output_manifest == OPENFOAM_RAW_RESULT
    assert record.real_solver_execution_opt_in == "persistent_setting"
    # claim_state and accepted_uses stay locked.
    assert record.claim_state == "raw_unvalidated"
    assert record.accepted_uses == []


def test_succeeded_record_carries_solver_execution_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The audit block records the case-template lock and wall-clock timings."""
    job = _prepare_openfoam_job(tmp_path)
    _install_fake_solver(job.job_dir)
    _set_openfoam_profile_fields(job.job_dir, allow_real_solver_execution=True)
    monkeypatch.delenv(OPENFOAM_LOCAL_RUN_ENV_VAR, raising=False)

    record = run_cfd_job(job.job_dir)

    assert record.status == "succeeded"
    assert record.real_solver_execution_opt_in == "profile_flag"
    audit = record.solver_execution_audit
    assert isinstance(audit, SolverExecutionAudit)
    assert audit.case_template_version == OPENFOAM_CASE_TEMPLATE_VERSION
    assert audit.mesh_seconds >= 0.0
    assert audit.solve_seconds >= 0.0
    # bashrc_path is populated from the runner's resolution helper.
    assert isinstance(audit.bashrc_path, str)
    # provenance_summary at minimum carries the solver_version surface.
    assert "solver_version" in audit.provenance_summary


def test_blocked_record_has_none_opt_in_and_none_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: the historical blocked path leaves the new fields as ``None``."""
    job = _prepare_openfoam_job(tmp_path)
    _install_fake_solver(job.job_dir)
    # No profile flag, no persistent setting, no env knob.
    _write_persistent_config(monkeypatch, tmp_path, [])
    monkeypatch.delenv(OPENFOAM_LOCAL_RUN_ENV_VAR, raising=False)

    record = run_cfd_job(job.job_dir)

    assert record.status == "failed"
    assert record.error_kind == "solver_success_blocked"
    assert record.real_solver_execution_opt_in is None
    assert record.solver_execution_audit is None
