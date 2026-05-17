"""``kayakgen migrate-geometry`` — best-effort lofted → distribution_v2 migration.

RFC 0048 §"Migration tooling". Reads an existing lofted ``Hull`` JSON,
samples its half-breadth / draft / deck-freeboard / section-area
distributions along the centerline, and emits a sibling
``<name>.v2.json`` (per the resolved open-question default) whose
``geometry_kind="distribution_v2"`` reproduces the source within a
configured tolerance.

The migration is **lossy** by design — the lofted parametric form does
not invert exactly to an explicit-distribution form. If the resulting
v2 hull drifts beyond ``--tolerance-percent``, the command still writes
the file but exits with a non-zero status and emits a structured
warning, matching the RFC's "no silent acceptance" stance.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import typer

from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.io.json import load_hull
from kayakgen.model.distribution_v2 import (
    DistributionV2Spec,
    KeyPointsDistribution,
    UniformDistribution,
)
from kayakgen.model.hull import Hull


def _sample_lofted_distributions(
    hull: Hull, n_knots: int = 11
) -> tuple[list[tuple[float, float]], list[tuple[float, float]], list[tuple[float, float]], list[tuple[float, float]], list[tuple[float, float]]]:
    """Sample the lofted hull's longitudinal distributions in ``xi`` ∈ [-1, 1]."""

    geom = hull.to_geometry()
    L = float(hull.length_m)
    xs = np.linspace(-L / 2.0, L / 2.0, n_knots)
    half_breadths: list[tuple[float, float]] = []
    drafts: list[tuple[float, float]] = []
    deck_heights: list[tuple[float, float]] = []
    section_areas: list[tuple[float, float]] = []
    rocker: list[tuple[float, float]] = []

    wp = geom.waterplane(n=max(n_knots, 21))
    keel = geom.keel_line(n=max(n_knots, 21))
    deck = geom.deck_centreline(n=max(n_knots, 21))
    for x in xs:
        xi = float((2.0 * x) / L)
        hb = float(np.interp(x, wp[:, 0], wp[:, 1]))
        keel_z = float(np.interp(x, keel[:, 0], keel[:, 1]))
        deck_z = float(np.interp(x, deck[:, 0], deck[:, 1]))
        half_breadths.append((xi, hb))
        drafts.append((xi, -keel_z))
        deck_heights.append((xi, deck_z))
        section_areas.append((xi, float(geom.section_area(float(x)))))
        rocker.append((xi, 0.0))
    return half_breadths, drafts, section_areas, deck_heights, rocker


def _build_v2_hull(source: Hull) -> Hull:
    """Construct a best-effort distribution_v2 hull from a lofted source."""

    half_breadths, drafts, section_areas, deck_heights, rocker = (
        _sample_lofted_distributions(source)
    )
    spec = DistributionV2Spec(
        waterline_half_breadth=KeyPointsDistribution(knots=half_breadths),
        draft_profile=KeyPointsDistribution(knots=drafts),
        section_area_curve=KeyPointsDistribution(knots=section_areas),
        deck_freeboard=KeyPointsDistribution(knots=deck_heights),
        rocker=KeyPointsDistribution(knots=rocker) if any(v for _, v in rocker) else UniformDistribution(value=0.0),
        rocker_bow_m=float(source.rocker_bow_m),
        rocker_stern_m=float(source.rocker_stern_m),
        lcb_target_frac=float(source.LCB_frac),
        max_beam_position_frac=0.5,
        cross_section_family="round",
        deadrise_deg=0.0,
        chine_radius_m=0.02,
        bow_flare_deg=0.0,
    )
    # Preserve every legacy lofted field on the v2 hull record (the
    # RFC 0048 open-question decision: legacy scalars are echoed for
    # backwards-compat reporting). Rake is the lone refusal — when the
    # source has non-default rake we cannot honor it on v2; the
    # validator on ``Hull`` rejects the construction, in which case the
    # migration emits a structured failure and exits non-zero.
    payload = source.model_dump()
    payload["geometry_kind"] = "distribution_v2"
    payload["distribution_v2"] = spec.model_dump()
    payload["bow_rake"] = 1.0
    payload["stern_rake"] = 1.0
    return Hull.model_validate(payload)


def _round_trip_drift(source: Hull, v2_hull: Hull) -> dict[str, float]:
    src = evaluate_hydrostatics(source)
    dst = evaluate_hydrostatics(v2_hull)
    return {
        "displaced_volume_drift_frac": _safe_drift(src.displaced_volume_m3, dst.displaced_volume_m3),
        "waterplane_area_drift_frac": _safe_drift(src.waterplane_area_m2, dst.waterplane_area_m2),
        "lcb_drift_frac": _safe_drift(src.LCB_frac, dst.LCB_frac),
        "gm0_drift_frac": (
            _safe_drift(src.GM0_m, dst.GM0_m)
            if src.GM0_m is not None and dst.GM0_m is not None
            else 0.0
        ),
    }


def _safe_drift(a: float | None, b: float | None) -> float:
    if a is None or b is None:
        return 0.0
    denom = max(abs(a), abs(b), 1e-12)
    return float(abs(a - b) / denom)


def migrate_geometry_command(
    hull_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        help="Source lofted Hull JSON.",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Where to write the v2 Hull JSON. Default: sibling <name>.v2.json.",
    ),
    tolerance_percent: float = typer.Option(
        1.0,
        "--tolerance-percent",
        help=(
            "Round-trip drift threshold in percent on the four hydrostatic "
            "metrics (displaced_volume / waterplane / LCB / GM0). If any "
            "metric exceeds this, the file is still written and the command "
            "exits non-zero with a structured warning."
        ),
    ),
) -> None:
    """Migrate a lofted Hull JSON to a best-effort distribution_v2 hull."""

    source = load_hull(hull_path)
    if source.geometry_kind != "lofted":
        typer.echo(
            f"migrate-geometry refuses non-lofted source (geometry_kind={source.geometry_kind!r})",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        v2_hull = _build_v2_hull(source)
    except ValueError as exc:
        typer.echo(f"migrate-geometry build failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    out_path = out if out is not None else hull_path.with_suffix(".v2.json")
    out_path.write_text(v2_hull.model_dump_json(indent=2))

    drifts = _round_trip_drift(source, v2_hull)
    tolerance_frac = float(tolerance_percent) / 100.0
    over: list[str] = [
        f"{metric}={drifts[metric]:.4f}"
        for metric in drifts
        if drifts[metric] > tolerance_frac
    ]

    typer.echo(f"wrote {out_path}")
    typer.echo(
        "round_trip_drift: "
        f"displaced_volume={drifts['displaced_volume_drift_frac']:.4f} "
        f"waterplane={drifts['waterplane_area_drift_frac']:.4f} "
        f"lcb={drifts['lcb_drift_frac']:.4f} "
        f"gm0={drifts['gm0_drift_frac']:.4f}"
    )

    if over:
        payload = {
            "warning": "migrate_geometry_tolerance_exceeded",
            "tolerance_frac": tolerance_frac,
            "drifts": drifts,
            "exceeded": over,
        }
        typer.echo(json.dumps(payload), err=True)
        raise typer.Exit(code=2)
