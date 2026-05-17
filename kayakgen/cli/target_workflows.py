"""CLI subcommands for RFC 0050 target-displacement / target-trim workflows.

This module owns the ``kayakgen target-draft`` and ``kayakgen target-trim``
Typer command callbacks. ``kayakgen/cli/main.py`` registers them with a
single import + two ``app.command(...)`` lines to keep merge collision risk
low while other RFC-impl branches land in parallel.
"""

from __future__ import annotations

from pathlib import Path

import typer

from kayakgen.eval.contract import LoadCase
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.io.json import load_hull
from kayakgen.services.evaluation import (
    solve_target_draft,
    solve_target_trim,
    target_draft_load_mismatch,
)

_UNPHYSICAL_LOAD_MULTIPLIER = 2.0


def _load_load_case(load_path: Path) -> LoadCase:
    return LoadCase.model_validate_json(load_path.read_text())


def _reject_unphysical_load(hull, load_case: LoadCase) -> None:
    """Echo a structured error and exit if the load exceeds the physical envelope."""
    hydro_full = evaluate_hydrostatics(hull)
    max_displaced_mass_kg = float(
        hydro_full.displaced_volume_m3 * load_case.seawater_density_kg_m3
    )
    threshold_kg = _UNPHYSICAL_LOAD_MULTIPLIER * max_displaced_mass_kg
    if load_case.total_mass_kg > threshold_kg:
        typer.echo(
            "target-workflow failed: load_unphysical "
            f"(load_total_mass_kg={load_case.total_mass_kg:.3f}, "
            f"max_displaced_mass_kg={max_displaced_mass_kg:.3f}, "
            f"threshold_kg={threshold_kg:.3f}, "
            f"multiplier={_UNPHYSICAL_LOAD_MULTIPLIER})",
            err=True,
        )
        raise typer.Exit(code=1)


def target_draft_command(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    load: Path = typer.Option(
        ...,
        "--load",
        exists=True,
        dir_okay=False,
        help="Path to a LoadCase JSON document.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output path for the StabilityResult or TargetDraftMismatchReport JSON.",
    ),
    draft: float | None = typer.Option(
        None,
        "--draft",
        help=(
            "If provided with --report-only, compute the load-mismatch report "
            "for this fixed draft instead of solving equilibrium."
        ),
    ),
    report_only: bool = typer.Option(
        False,
        "--report-only",
        help=(
            "Skip the equilibrium solve and write a TargetDraftMismatchReport "
            "for the supplied --draft."
        ),
    ),
) -> None:
    """Solve upright sinkage for a given load, or report load mismatch at a fixed draft."""
    hull = load_hull(hull_path)
    load_case = _load_load_case(load)

    if report_only:
        if draft is None:
            typer.echo(
                "target-draft --report-only requires --draft <meters>",
                err=True,
            )
            raise typer.Exit(code=1)
        if draft <= 0:
            typer.echo(
                "target-draft --draft must be positive",
                err=True,
            )
            raise typer.Exit(code=1)
        report = target_draft_load_mismatch(hull, draft, load_case)
        out.write_text(report.model_dump_json(indent=2))
        typer.echo(f"wrote {out}")
        return

    if draft is not None:
        typer.echo(
            "target-draft: --draft is only meaningful with --report-only",
            err=True,
        )
        raise typer.Exit(code=1)

    _reject_unphysical_load(hull, load_case)
    result = solve_target_draft(hull, load_case)
    out.write_text(result.model_dump_json(indent=2))
    typer.echo(f"wrote {out}")


def target_trim_command(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    load: Path = typer.Option(
        ...,
        "--load",
        exists=True,
        dir_okay=False,
        help="Path to a LoadCase JSON document.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output path for the StabilityResult JSON.",
    ),
) -> None:
    """Solve draft + trim for a load case with non-zero longitudinal CG."""
    hull = load_hull(hull_path)
    load_case = _load_load_case(load)

    _reject_unphysical_load(hull, load_case)
    result = solve_target_trim(hull, load_case)
    out.write_text(result.model_dump_json(indent=2))
    typer.echo(f"wrote {out}")
