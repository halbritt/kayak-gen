"""RFC 0045 CLI tests for ``kayakgen mesh-evidence``.

These tests do not invoke OpenFOAM binaries. They verify that the
``mesh-evidence`` subcommand refuses to run without the
``KAYAKGEN_OPENFOAM_LOCAL_RUN=1`` env knob and refuses even with the
env knob set when ``is_openfoam_available()`` returns False (e.g. the
toolchain is not on PATH).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.cfd.jobs import OPENFOAM_LOCAL_RUN_ENV_VAR
from kayakgen.io.json import save_hull
from kayakgen.model.hull import Hull


@pytest.fixture
def hull_path(tmp_path: Path) -> Path:
    path = tmp_path / "hull.json"
    save_hull(Hull(), path)
    return path


def test_mesh_evidence_cli_refuses_without_env_knobs(
    hull_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without ``KAYAKGEN_OPENFOAM_LOCAL_RUN=1`` the command refuses."""
    monkeypatch.delenv(OPENFOAM_LOCAL_RUN_ENV_VAR, raising=False)

    runner = CliRunner()
    out_dir = tmp_path / "evidence"
    result = runner.invoke(
        app,
        ["mesh-evidence", str(hull_path), "--out", str(out_dir)],
    )

    assert result.exit_code != 0
    assert "openfoam_local_run_env_required" in result.output
    assert OPENFOAM_LOCAL_RUN_ENV_VAR in result.output
    assert not (out_dir / "evidence.json").exists()


def test_mesh_evidence_cli_refuses_when_openfoam_not_available(
    hull_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With env knob but no toolchain, the command refuses with a structured code."""
    monkeypatch.setenv(OPENFOAM_LOCAL_RUN_ENV_VAR, "1")
    # Force ``is_openfoam_available`` to return False so the test never
    # tries to source a real bashrc or call interFoam.
    monkeypatch.setattr(
        "kayakgen.eval.cfd.openfoam_v2512_interfoam.runner.is_openfoam_available",
        lambda *_args, **_kwargs: False,
    )

    runner = CliRunner()
    out_dir = tmp_path / "evidence"
    result = runner.invoke(
        app,
        ["mesh-evidence", str(hull_path), "--out", str(out_dir)],
    )

    assert result.exit_code != 0
    assert "openfoam_toolchain_unavailable" in result.output
    assert "OpenFOAM-v2512" in result.output
    assert not (out_dir / "evidence.json").exists()
