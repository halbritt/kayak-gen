"""`kayakgen runs` subcommands: list / query / reindex (RFC 0049).

This module wires three Typer commands onto the ``runs_app`` sub-app:

- ``runs_list_command`` — list run rows from the SQLite index in
  deterministic order.
- ``runs_query_command`` — fetch candidate rows for one run, optionally
  projecting named metrics.
- ``runs_reindex_command`` — re-derive the SQLite index from canonical
  run-directory bytes (best-effort; legacy directories without a
  ``_store/`` mirror are tolerated with warnings).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from kayakgen.services.artifact_store import (
    FilesystemArtifactStore,
    SqliteIndex,
    index_candidates,
    index_run_directory,
)

runs_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Cross-run inspection (RFC 0049): list runs, query candidates, rebuild the index.",
)


@runs_app.command("list")
def runs_list_command(
    kind: str | None = typer.Option(
        None,
        "--kind",
        help="Filter by run kind: sweep | search | cfd | comparison.",
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        help="Max number of runs to print.",
    ),
) -> None:
    """List runs from the SQLite index in deterministic order."""

    index = SqliteIndex()
    rows = index.list_runs(
        kind=kind,  # type: ignore[arg-type]
        limit=limit,
    )
    if not rows:
        typer.echo("(no runs indexed)")
        return
    for row in rows:
        typer.echo(
            f"{row['run_id']}\t{row['kind']}\t{row['created_at']}\t{row['out_dir']}"
        )


@runs_app.command("query")
def runs_query_command(
    run_id: str = typer.Argument(..., help="run_id (as recorded in the index)."),
    metric: list[str] | None = typer.Option(
        None,
        "--metric",
        help="Metric name to project. May be repeated.",
    ),
    filter_: list[str] | None = typer.Option(
        None,
        "--filter",
        help="Filter as key:value (eq only); may be repeated.",
    ),
) -> None:
    """Query the candidates of one run."""

    index = SqliteIndex()
    filters: dict[str, Any] = {}
    for raw in filter_ or []:
        if ":" not in raw:
            typer.echo(f"ignored --filter {raw!r} (expected key:value)", err=True)
            continue
        key, value = raw.split(":", 1)
        filters[key.strip()] = value.strip()
    metric_names = tuple(metric or [])
    rows = index.candidates_for_run(run_id, metrics=metric_names)
    if filters:
        rows = [
            row
            for row in rows
            if all(
                (k == "status" and row.status == v)
                or (k == "hull_design_hash" and row.hull_design_hash == v)
                for k, v in filters.items()
            )
        ]
    if not rows:
        typer.echo(f"(no candidates for run_id={run_id})")
        return
    for row in rows:
        payload = {
            "candidate_key": row.candidate_key,
            "status": row.status,
            "hull_design_hash": row.hull_design_hash,
            "hull_record_hash": row.hull_record_hash,
            "metrics": row.metrics,
        }
        typer.echo(json.dumps(payload, sort_keys=True))


@runs_app.command("jobs")
def runs_jobs_command(
    state: str | None = typer.Option(
        None,
        "--state",
        help="Filter by job state: queued | running | succeeded | failed | cancelled | resumable.",
    ),
    kind: str | None = typer.Option(
        None,
        "--kind",
        help="Filter by job kind: sweep | search.",
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        help="Max number of jobs to print.",
    ),
) -> None:
    """List long-lived generative jobs from the SQLite index (RFC 0057)."""

    index = SqliteIndex()
    rows = index.list_generative_jobs(
        state=state,
        job_kind=kind,
        limit=limit,
    )
    if not rows:
        typer.echo("(no generative jobs indexed)")
        return
    for row in rows:
        typer.echo(
            f"{row['job_id']}\t{row['job_kind']}\t{row['state']}\t"
            f"{row['realized_evaluations']}/{row['completed_count']}c/"
            f"{row['failed_count']}f\t{row['output_dir']}"
        )


@runs_app.command("reindex")
def runs_reindex_command(
    run_dir: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        help="Run directory to reindex (expects run.json + candidates/).",
    ),
    run_id: str | None = typer.Option(
        None,
        "--run-id",
        help="Override the run_id to upsert (defaults to run.json:name or directory name).",
    ),
) -> None:
    """Re-derive the SQLite index from a canonical run directory."""

    from pydantic import ValidationError  # local import keeps CLI lightweight

    from kayakgen.search.sweep import CandidateRecord
    from kayakgen.services.identity import record_hash

    run_json = run_dir / "run.json"
    if not run_json.exists():
        typer.echo(f"reindex failed: {run_json} not found", err=True)
        raise typer.Exit(code=1)

    payload = json.loads(run_json.read_text())
    name = payload.get("name") or run_dir.name
    spec_hash = payload.get("spec_hash") or record_hash(payload)
    resolved_run_id = run_id or f"reindex-{spec_hash[:16]}-{name}"
    kind = "search" if "search_metadata" in payload else "sweep"

    store = FilesystemArtifactStore(run_dir, run_id=resolved_run_id)
    db = index_run_directory(
        run_dir,
        run_id=resolved_run_id,
        kind=kind,
        spec_hash=spec_hash,
        run_hash_value=spec_hash,
        index=store.index,
    )

    candidates_dir = run_dir / "candidates"
    rows: list[dict[str, Any]] = []
    if candidates_dir.is_dir():
        from kayakgen.search.sweep import _index_row_for_candidate

        for path in sorted(candidates_dir.glob("*.record.json")):
            try:
                rec = CandidateRecord.model_validate_json(path.read_text())
            except (ValidationError, ValueError):
                typer.echo(f"warning: could not parse {path}", err=True)
                continue
            rows.append(_index_row_for_candidate(rec))
    index_candidates(run_id=resolved_run_id, candidate_rows=rows, index=db)
    typer.echo(
        f"reindexed run_id={resolved_run_id} kind={kind} candidates={len(rows)}"
    )


__all__ = [
    "runs_app",
    "runs_jobs_command",
    "runs_list_command",
    "runs_query_command",
    "runs_reindex_command",
]
