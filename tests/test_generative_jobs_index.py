"""SqliteIndex.generative_jobs table + `kayakgen runs jobs` CLI tests (RFC 0057)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from kayakgen.cli.runs_cli import runs_app
from kayakgen.services.artifact_store import SqliteIndex


def test_upsert_and_list_generative_jobs(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index = SqliteIndex(db)

    index.upsert_generative_job(
        job_id="job-a",
        job_kind="search",
        spec_hash="a" * 64,
        state="running",
        output_dir=str(tmp_path / "out-a"),
        started_at=1.0,
        realized_evaluations=4,
        completed_count=3,
        failed_count=1,
        updated_at=10,
    )
    index.upsert_generative_job(
        job_id="job-b",
        job_kind="sweep",
        spec_hash="b" * 64,
        state="succeeded",
        output_dir=str(tmp_path / "out-b"),
        started_at=2.0,
        completed_at=5.0,
        realized_evaluations=8,
        completed_count=8,
        updated_at=20,
    )

    rows = index.list_generative_jobs()
    assert [r["job_id"] for r in rows] == ["job-a", "job-b"]
    assert rows[0]["state"] == "running"
    assert rows[0]["completed_count"] == 3
    assert rows[1]["job_kind"] == "sweep"

    running = index.list_generative_jobs(state="running")
    assert [r["job_id"] for r in running] == ["job-a"]

    only_search = index.list_generative_jobs(job_kind="search")
    assert [r["job_id"] for r in only_search] == ["job-a"]

    limited = index.list_generative_jobs(limit=1)
    assert len(limited) == 1


def test_upsert_generative_job_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index = SqliteIndex(db)

    index.upsert_generative_job(
        job_id="job-x",
        job_kind="search",
        spec_hash="c" * 64,
        state="queued",
        output_dir=str(tmp_path / "x"),
    )
    index.upsert_generative_job(
        job_id="job-x",
        job_kind="search",
        spec_hash="c" * 64,
        state="running",
        output_dir=str(tmp_path / "x"),
        realized_evaluations=2,
    )

    rows = index.list_generative_jobs()
    assert len(rows) == 1
    assert rows[0]["state"] == "running"
    assert rows[0]["realized_evaluations"] == 2


def test_runs_jobs_cli_lists_indexed_jobs(
    tmp_path: Path, monkeypatch
) -> None:
    db = tmp_path / "index.sqlite"
    monkeypatch.setenv("KAYAKGEN_INDEX_DB", str(db))
    SqliteIndex(db).upsert_generative_job(
        job_id="cli-job-1",
        job_kind="search",
        spec_hash="d" * 64,
        state="succeeded",
        output_dir=str(tmp_path / "out"),
        realized_evaluations=12,
        completed_count=11,
        failed_count=1,
    )

    runner = CliRunner()
    result = runner.invoke(runs_app, ["jobs"])

    assert result.exit_code == 0, result.output
    assert "cli-job-1" in result.output
    assert "search" in result.output
    assert "succeeded" in result.output


def test_runs_jobs_cli_reports_empty_index(
    tmp_path: Path, monkeypatch
) -> None:
    db = tmp_path / "index.sqlite"
    monkeypatch.setenv("KAYAKGEN_INDEX_DB", str(db))
    SqliteIndex(db)  # create schema

    runner = CliRunner()
    result = runner.invoke(runs_app, ["jobs"])

    assert result.exit_code == 0, result.output
    assert "no generative jobs" in result.output


def test_runs_jobs_cli_state_filter(
    tmp_path: Path, monkeypatch
) -> None:
    db = tmp_path / "index.sqlite"
    monkeypatch.setenv("KAYAKGEN_INDEX_DB", str(db))
    idx = SqliteIndex(db)
    idx.upsert_generative_job(
        job_id="job-running",
        job_kind="search",
        spec_hash="e" * 64,
        state="running",
        output_dir=str(tmp_path / "r"),
    )
    idx.upsert_generative_job(
        job_id="job-done",
        job_kind="sweep",
        spec_hash="f" * 64,
        state="succeeded",
        output_dir=str(tmp_path / "d"),
    )

    runner = CliRunner()
    result = runner.invoke(runs_app, ["jobs", "--state", "running"])

    assert result.exit_code == 0, result.output
    assert "job-running" in result.output
    assert "job-done" not in result.output
