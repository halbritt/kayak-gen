"""``kayakgen`` console script."""

from __future__ import annotations

from pathlib import Path

import typer

from kayakgen.eval.contract import EvaluationResult
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.resistance import resistance_curve
from kayakgen.io.json import load_hull, save_evaluation, save_hull
from kayakgen.io.stl import write_stl
from kayakgen.model.hull import Hull

app = typer.Typer(no_args_is_help=True, add_completion=False, help="kayakgen pipeline CLI")


@app.command()
def init(
    out: Path = typer.Argument(..., help="Where to write the default Hull JSON."),
) -> None:
    """Write a default-parameter Hull JSON to ``out``."""
    save_hull(Hull(), out)
    typer.echo(f"wrote {out}")


@app.command()
def generate(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    stl_out: Path | None = typer.Option(None, "--stl-out", help="Output prefix; writes <prefix>_hull.stl and <prefix>_deck.stl."),
) -> None:
    """Generate hull and deck STL files from a Hull JSON."""
    hull = load_hull(hull_path)
    prefix = stl_out if stl_out is not None else hull_path.with_suffix("")
    hull_path_out = prefix.with_name(prefix.name + "_hull.stl")
    deck_path_out = prefix.with_name(prefix.name + "_deck.stl")
    write_stl(hull, "hull", hull_path_out)
    write_stl(hull, "deck", deck_path_out)
    typer.echo(f"wrote {hull_path_out}")
    typer.echo(f"wrote {deck_path_out}")


@app.command()
def evaluate(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path | None = typer.Option(None, "--out", help="Where to write the EvaluationResult JSON; default is <hull>.eval.json."),
    skip_resistance: bool = typer.Option(False, "--skip-resistance", help="Skip the Michell+ITTC sweep (faster)."),
) -> None:
    """Run all available evaluators on a hull and write the EvaluationResult."""
    hull = load_hull(hull_path)
    hydrostatics = evaluate_hydrostatics(hull)
    resistance = None if skip_resistance else resistance_curve(hull)
    result = EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=hydrostatics,
        resistance=resistance,
    )
    out_path = out if out is not None else hull_path.with_suffix(".eval.json")
    save_evaluation(result, out_path)
    typer.echo(f"wrote {out_path}")


@app.command()
def view(
    hull_path: Path | None = typer.Argument(
        None,
        help="Optional Hull JSON to load; defaults to the same defaults as `python gui.py`.",
    ),
) -> None:
    """Open the desktop GUI."""
    try:
        from kayakgen.ui.desktop import KayakGUI
    except ImportError as exc:
        typer.echo(f"desktop GUI extras not installed: {exc}", err=True)
        raise typer.Exit(code=1)

    if hull_path is not None:
        hull = load_hull(hull_path)
        KayakGUI(hull=hull)
    else:
        KayakGUI()


if __name__ == "__main__":
    app()
