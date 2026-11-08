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
    SqliteIndex,
    reindex_run,
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
        help=(
            "Filter by run kind. Honored values: sweep | search | cfd | "
            "comparison. Matched against the 'kind' column of the SQLite "
            "runs table."
        ),
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        help="Max number of runs to print.",
    ),
    header: bool = typer.Option(
        False,
        "--header/--no-header",
        help=(
            "When --header is set, print a '#'-prefixed header line naming "
            "the row columns before emitting rows (default: --no-header for "
            "back-compat with scripts that parse the existing tab-separated "
            "output)."
        ),
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
    if header:
        typer.echo("# run_id\tkind\tcreated_at\tout_dir")
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
        help=(
            "Filter candidates as key:value (equality only); may be repeated. "
            "Honored keys: 'status' (e.g. accepted|rejected) and "
            "'hull_design_hash' (full identity, including a v2 scheme prefix). "
            "Other keys parse without error "
            "but match no rows and silently drop the candidate from the "
            "output. The filter is applied client-side after the SQLite "
            "candidates query."
        ),
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
        help=(
            "Filter by job state. Honored values: queued | running | "
            "succeeded | failed | cancelled | resumable. Matched against "
            "the 'state' column of the SQLite generative_jobs table."
        ),
    ),
    kind: str | None = typer.Option(
        None,
        "--kind",
        help=(
            "Filter by job kind. Honored values: sweep | search. Matched "
            "against the 'job_kind' column of the SQLite generative_jobs "
            "table."
        ),
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        help="Max number of jobs to print.",
    ),
    header: bool = typer.Option(
        False,
        "--header/--no-header",
        help=(
            "When --header is set, print a '#'-prefixed header line naming "
            "the row columns before emitting rows (default: --no-header for "
            "back-compat with scripts that parse the existing tab-separated "
            "output)."
        ),
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
    if header:
        typer.echo(
            "# job_id\tjob_kind\tstate\trealized/completed_c/failed_f\toutput_dir"
        )
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
        help="Run directory containing run.json; manifested runs restore recorded identity and hashes.",
    ),
    run_id: str | None = typer.Option(
        None,
        "--run-id",
        help="Set identity only for an unindexed legacy import; conflicts with established identity fail.",
    ),
) -> None:
    """Re-derive the SQLite index from a canonical run directory."""

    try:
        result = reindex_run(run_dir, run_id=run_id)
    except (OSError, ValueError, RuntimeError) as exc:
        typer.echo(f"reindex failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    if not result.provenance_complete:
        typer.echo(
            "warning: incomplete legacy provenance; unknown historical hashes remain unverified",
            err=True,
        )
    typer.echo(
        f"reindexed run_id={result.run_id} kind={result.kind} "
        f"candidates={result.candidate_count} artifacts={result.artifact_count} "
        f"provenance={'complete' if result.provenance_complete else 'incomplete'}"
    )


__all__ = [
    "runs_app",
    "runs_jobs_command",
    "runs_list_command",
    "runs_query_command",
    "runs_reindex_command",
]
