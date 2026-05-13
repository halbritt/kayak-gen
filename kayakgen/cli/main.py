"""``kayakgen`` console script."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import typer

from kayakgen.eval.contract import EvaluationResult
from kayakgen.eval.contract import LoadCase
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.resistance import resistance_curve
from kayakgen.eval.stability import evaluate_equilibrium_stability, evaluate_initial_stability
from kayakgen.eval.mesh_package import write_mesh_package
from kayakgen.io.json import load_hull, save_evaluation, save_hull
from kayakgen.io.stl import write_stl
from kayakgen.model.geometry import PartType
from kayakgen.model.hull import Hull
from kayakgen.search.compare import parse_objective, write_comparison_report

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


@app.command("mesh-check")
def mesh_check(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Where to write mesh diagnostics JSON.",
    ),
    part: str = typer.Option("hull", "--part", help="Mesh part to diagnose: hull or deck."),
) -> None:
    """Diagnose generated surface mesh quality without promoting CFD readiness."""
    from kayakgen.eval.mesh_diagnostics import diagnose_mesh

    if part not in ("hull", "deck"):
        typer.echo("--part must be hull or deck", err=True)
        raise typer.Exit(code=1)
    diagnostics = diagnose_mesh(load_hull(hull_path), part=cast(PartType, part))
    out_path = out if out is not None else hull_path.with_suffix(f".{part}.mesh.json")
    out_path.write_text(diagnostics.model_dump_json(indent=2))
    typer.echo(f"wrote {out_path}")


@app.command("mesh-package")
def mesh_package(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output directory for the mesh package.",
    ),
) -> None:
    """Write manifest, quality reports, and STL surfaces for a Hull."""
    try:
        manifest = write_mesh_package(load_hull(hull_path), out)
    except Exception as exc:
        typer.echo(f"mesh-package failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"wrote {out / 'manifest.json'} ({manifest.readiness.level})")


@app.command()
def stability(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path | None = typer.Option(None, "--out", help="Where to write stability JSON."),
    load_case: Path | None = typer.Option(
        None,
        "--load-case",
        exists=True,
        dir_okay=False,
    ),
    equilibrium: bool = typer.Option(
        False,
        "--equilibrium",
        help="Solve load-case sinkage equilibrium before reporting initial stability.",
    ),
    tolerance_kg: float = typer.Option(
        1.0,
        "--tolerance-kg",
        help="Mass tolerance for equilibrium convergence.",
    ),
    moment_tolerance_kg_m: float | None = typer.Option(
        None,
        "--moment-tolerance-kg-m",
        help="Moment tolerance for trim equilibrium convergence; defaults from hull length.",
    ),
    max_iterations: int = typer.Option(
        60,
        "--max-iterations",
        help="Maximum equilibrium bisection iterations.",
    ),
) -> None:
    """Evaluate initial stability for a load case."""
    load = (
        LoadCase.model_validate_json(load_case.read_text())
        if load_case is not None
        else LoadCase()
    )
    hull = load_hull(hull_path)
    if equilibrium:
        result = evaluate_equilibrium_stability(
            hull,
            load,
            tolerance_kg=tolerance_kg,
            moment_tolerance_kg_m=moment_tolerance_kg_m,
            max_iterations=max_iterations,
        )
    else:
        result = evaluate_initial_stability(hull, load)
    out_path = out if out is not None else hull_path.with_suffix(".stability.json")
    out_path.write_text(result.model_dump_json(indent=2))
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


@app.command()
def serve(
    hull_path: Path | None = typer.Argument(
        None,
        help="Optional Hull JSON to seed initial state; defaults to Hull().",
    ),
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host."),
    port: int = typer.Option(8080, "--port", help="Bind port."),
) -> None:
    """Run the Trame web frontend (RFC 0008) locally."""
    try:
        from kayakgen.ui.web.app import create_app
    except ImportError as exc:
        typer.echo(f"web extras not installed (pip install 'kayakgen[web]'): {exc}", err=True)
        raise typer.Exit(code=1)

    initial_hull = load_hull(hull_path) if hull_path is not None else None
    web = create_app(initial_hull=initial_hull)
    web.server.start(host=host, port=port)


@app.command()
def sweep(
    sweep_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output directory for generated candidates.",
    ),
    resume: bool = typer.Option(False, "--resume", help="Skip completed candidate records."),
) -> None:
    """Run a deterministic JSON sweep and write candidate records."""
    from kayakgen.search.sweep import load_sweep_spec, run_sweep

    try:
        run = run_sweep(load_sweep_spec(sweep_path), out, resume=resume)
    except Exception as exc:
        typer.echo(f"sweep failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(
        f"wrote {out} ({run.completed_count} complete, {run.failed_count} failed, "
        f"{run.skipped_count} skipped)"
    )


@app.command()
def compare(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, help="Sweep run directory."),
    out: Path = typer.Option(..., "--out", help="Where to write comparison report JSON."),
    objective: list[str] | None = typer.Option(
        None,
        "--objective",
        "-o",
        help="Objective as metric:min or metric:max. May be repeated.",
    ),
) -> None:
    """Compare a sweep run and write a Pareto frontier report."""
    try:
        objectives = [parse_objective(item) for item in objective] if objective else None
        report = write_comparison_report(run_dir, out, objectives=objectives)
    except Exception as exc:
        typer.echo(f"compare failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"wrote {out} ({len(report.pareto_front_keys)} pareto candidates)")


if __name__ == "__main__":
    app()
