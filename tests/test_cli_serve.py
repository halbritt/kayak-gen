"""`kayakgen serve` CLI flag tests for the RFC 0057 stage-4 default flip."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner


def _serve_app():
    """Import the Typer app lazily so the test module loads without the web extras."""

    from kayakgen.cli.main import app

    return app


@pytest.fixture()
def mock_server_start():
    """Patch `KayakgenApp.server.start` so `serve` returns instead of blocking."""

    with patch("kayakgen.ui.web.app.KayakgenApp") as mock_app:
        mock_app.return_value.server.start.return_value = None
        yield mock_app


def test_serve_defaults_to_subprocess_manager(
    tmp_path: Path, monkeypatch, mock_server_start
) -> None:
    """Default: no flag → SubprocessGenerativeJobManager is used."""

    monkeypatch.setenv("KAYAKGEN_GENERATIVE_JOBS_ROOT", str(tmp_path / "jobs"))

    runner = CliRunner()
    result = runner.invoke(_serve_app(), ["serve"])

    assert result.exit_code == 0, result.output
    assert "detached subprocesses" in result.output
    assert "jobs_root=" in result.output
    # Characterization (plan §1.4): the echoed jobs_root resolves to the
    # KAYAKGEN_GENERATIVE_JOBS_ROOT override, not the home fallback.
    assert f"jobs_root={tmp_path / 'jobs'}" in result.output

    # KayakgenApp was constructed with the subprocess manager.
    construct_kwargs = mock_server_start.call_args.kwargs
    from kayakgen.services.generative_jobs import SubprocessGenerativeJobManager

    assert isinstance(
        construct_kwargs["generative_manager"], SubprocessGenerativeJobManager
    )


def test_serve_jobs_in_process_opt_in(
    tmp_path: Path, monkeypatch, mock_server_start
) -> None:
    """--jobs-in-process flips to the in-process thread manager."""

    monkeypatch.setenv("KAYAKGEN_GENERATIVE_JOBS_ROOT", str(tmp_path / "jobs"))

    runner = CliRunner()
    result = runner.invoke(_serve_app(), ["serve", "--jobs-in-process"])

    assert result.exit_code == 0, result.output
    assert "in-process threads" in result.output
    # Characterization (plan §1.4): same jobs_root pin for the in-process path.
    assert f"jobs_root={tmp_path / 'jobs'}" in result.output

    construct_kwargs = mock_server_start.call_args.kwargs
    from kayakgen.services.generative_jobs import InProcessGenerativeJobManager

    assert isinstance(
        construct_kwargs["generative_manager"], InProcessGenerativeJobManager
    )


def test_serve_help_documents_jobs_in_process(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(_serve_app(), ["serve", "--help"])
    assert result.exit_code == 0
    assert "--jobs-in-process" in result.output
    # The legacy --jobs-subprocess flag must not reappear.
    assert "--jobs-subprocess" not in result.output
