"""``kayakgen sensitivity`` CLI command (RFC 0052).

Thin Typer adapter over :func:`kayakgen.services.sensitivity.compute_sensitivity`.
The CLI module owns only argument parsing, file IO, and stdout messaging;
the actual finite-difference loop lives in the services layer.
"""

from __future__ import annotations

from pathlib import Path

import typer

from kayakgen.io.json import load_hull
from kayakgen.services.sensitivity import compute_sensitivity


def sensitivity_command(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    metric: list[str] = typer.Option(
        ...,
        "--metric",
        help=(
            "Summary metric to differentiate (e.g. GM0_m, displaced_mass_kg). "
            "Repeat for each requested metric."
        ),
    ),
    param: list[str] = typer.Option(
        ...,
        "--param",
        help=(
            "Hull parameter to perturb (e.g. length_m, beam_oa_m). "
            "Repeat for each requested parameter."
        ),
    ),
    step: float | None = typer.Option(
        None,
        "--step",
        help=(
            "Optional global perturbation step (same units as the parameter). "
            "When omitted the service uses 1e-4 * baseline_value per "
            "parameter, clamped to [1e-9, 1e-2]."
        ),
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Where to write the SensitivityResult JSON; default is <hull>.sensitivity.json.",
    ),
) -> None:
    """RFC 0052: write a local finite-difference Jacobian for a hull."""

    hull = load_hull(hull_path)
    result = compute_sensitivity(hull, metrics=list(metric), params=list(param), step=step)
    out_path = out if out is not None else hull_path.with_suffix(".sensitivity.json")
    out_path.write_text(result.model_dump_json(indent=2))
    typer.echo(f"wrote {out_path}")
    if result.non_finite_partials:
        typer.echo(
            f"non_finite_partials: {len(result.non_finite_partials)} "
            "(see file for (metric, param, reason) entries)"
        )
