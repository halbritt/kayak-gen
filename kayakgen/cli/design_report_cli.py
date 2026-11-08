"""CLI surface for ``kayakgen design-report`` (RFC 0055).

The renderer lives under :mod:`kayakgen.services.design_report`; this
module is intentionally thin and only handles option parsing, hull I/O,
and error formatting. ``kayakgen/cli/main.py`` registers a single
``design_report_command`` symbol.
"""

from __future__ import annotations

from pathlib import Path

import typer

from kayakgen.io.json import load_hull


def design_report_command(
    hull_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        help="Hull JSON to render a design report for.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Where to write the rendered HTML report.",
    ),
    pdf: bool = typer.Option(
        False,
        "--pdf",
        help=(
            "Also write a sibling PDF (replaces the HTML suffix with .pdf). "
            "Requires the optional weasyprint dependency from the "
            "`kayakgen[report]` extras group."
        ),
    ),
    evaluation_path: Path | None = typer.Option(
        None, "--evaluation", exists=True, dir_okay=False,
        help="Render a saved evaluation without recomputing numerical results.",
    ),
    load_case_path: Path | None = typer.Option(
        None, "--load-case", exists=True, dir_okay=False,
        help="Explicitly evaluate this load, save a sibling evaluation and render it.",
    ),
    from_run: Path | None = typer.Option(
        None,
        "--from-run",
        exists=True,
        file_okay=False,
        help=(
            "Sweep or search run directory; when set the report adds a "
            "comparison-position section locating this hull on the run's "
            "frontier (or an honest 'not in run' notice)."
        ),
    ),
) -> None:
    """Render an RFC 0055 design report."""

    try:
        from kayakgen.services.design_report import (
            ReportForbiddenCopyError,
            render_design_report,
        )
    except ImportError as exc:
        typer.echo(
            f"design-report extras not installed (pip install 'kayakgen[report]'): {exc}",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    if evaluation_path is not None and load_case_path is not None:
        typer.echo("Choose --evaluation or --load-case, not both.", err=True)
        raise typer.Exit(code=2)
    try:
        hull = load_hull(hull_path)
        evaluation = None
        if evaluation_path is not None:
            from kayakgen.eval.contract import EvaluationResult
            evaluation = EvaluationResult.model_validate_json(evaluation_path.read_text())
        elif load_case_path is not None:
            from kayakgen.eval.contract import EvaluationContext, LoadCase
            from kayakgen.services.evaluation import evaluate_with_context
            from kayakgen.io.json import save_evaluation
            load = LoadCase.model_validate_json(load_case_path.read_text())
            context = EvaluationContext.for_hull(hull, load_case=load, input_origin="supplied", equilibrium=True)
            evaluation = evaluate_with_context(hull, context)
            save_evaluation(evaluation, out.with_suffix(".eval.json"))
    except (ValueError, OSError) as exc:
        typer.echo(f"design-report input failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    pdf_out = out.with_suffix(".pdf") if pdf else None
    try:
        result = render_design_report(
            hull,
            from_run=from_run,
            html_out=out,
            pdf_out=pdf_out,
            hull_source_path=hull_path,
            evaluation=evaluation,
        )
    except ReportForbiddenCopyError as exc:
        typer.echo(f"design-report refused: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except (RuntimeError, ValueError) as exc:
        typer.echo(f"design-report failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"wrote {result.html_path} ({result.html_size_bytes} bytes)")
    if result.pdf_path is not None:
        typer.echo(f"wrote {result.pdf_path}")
