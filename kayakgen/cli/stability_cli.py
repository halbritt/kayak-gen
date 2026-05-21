"""RFC 0058 stability-calibration CLI surface."""

from __future__ import annotations

from pathlib import Path

from typer.core import TyperGroup
import typer

from kayakgen.eval.stability.accepted_fit import (
    StabilityFitRecord,
    StabilityFixturePromotionPacket,
)
from kayakgen.eval.stability.measured_fixture import MeasuredStabilityFixture

class LegacyStabilityGroup(TyperGroup):
    """Route ``kayakgen stability <hull>`` to the legacy evaluator command."""

    def parse_args(self, ctx, args):
        if self._should_route_to_legacy(args):
            args = ["legacy", *args]
        return super().parse_args(ctx, args)

    def _should_route_to_legacy(self, args) -> bool:
        if not args or args[0] in {"--help", "-h"}:
            return False
        first_positional = next((arg for arg in args if not arg.startswith("-")), None)
        if first_positional is None:
            return True
        return first_positional not in self.commands


stability_app = typer.Typer(
    cls=LegacyStabilityGroup,
    no_args_is_help=True,
    help="Stability rig fixture and accepted-fit artifact writers (RFC 0058).",
)

_DEFAULT_FIXTURES_DIR = Path("data/stability/fixtures")
_DEFAULT_FITS_DIR = Path("data/stability/fits")


def _write_json_refusing_overwrite(path: Path, payload: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _canonical_json(model) -> str:
    return model.model_dump_json(indent=2) + "\n"


@stability_app.command("ingest-rig-run")
def ingest_rig_run(
    manifest_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        help="MeasuredStabilityFixture manifest JSON to validate and ingest.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Fixture output directory; writes manifest.json inside it.",
    ),
) -> None:
    """Validate a measured-stability fixture manifest and persist canonical JSON."""
    try:
        fixture = MeasuredStabilityFixture.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        out_path = out / "manifest.json"
        _write_json_refusing_overwrite(out_path, _canonical_json(fixture))
    except Exception as exc:
        typer.echo(f"ingest-rig-run failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"wrote {out_path} ({fixture.intended_use})")


@stability_app.command("promote-fixture")
def promote_fixture(
    fixture_id: str = typer.Argument(
        ...,
        help="Fixture id under data/stability/fixtures/<fixture_id>/manifest.json.",
    ),
    packet: Path = typer.Option(
        ...,
        "--packet",
        exists=True,
        dir_okay=False,
        help="StabilityFixturePromotionPacket JSON.",
    ),
) -> None:
    """Apply a validated promotion packet to a fixture manifest."""
    fixture_path = _DEFAULT_FIXTURES_DIR / fixture_id / "manifest.json"
    try:
        promotion_packet = StabilityFixturePromotionPacket.model_validate_json(
            packet.read_text(encoding="utf-8")
        )
        fixture = MeasuredStabilityFixture.model_validate_json(
            fixture_path.read_text(encoding="utf-8")
        )
        if fixture.fixture_id != fixture_id:
            raise ValueError(
                f"fixture_id mismatch: path requested {fixture_id!r}, "
                f"manifest carries {fixture.fixture_id!r}"
            )

        if promotion_packet.promotion_target in {
            "measured_stability_fixture",
            "rejected",
        }:
            payload = fixture.model_dump()
            payload["intended_use"] = promotion_packet.promotion_target
            fixture = MeasuredStabilityFixture.model_validate(payload)
            fixture_path.write_text(_canonical_json(fixture), encoding="utf-8")
            typer.echo(f"wrote {fixture_path} ({fixture.intended_use})")
            return
    except Exception as exc:
        typer.echo(f"promote-fixture failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"no-op {fixture_path} ({fixture.intended_use})")


@stability_app.command("accept-fit")
def accept_fit(
    fit_record_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        help="StabilityFitRecord JSON to validate and persist.",
    ),
    packet: Path = typer.Option(
        ...,
        "--packet",
        exists=True,
        dir_okay=False,
        help="Accepted StabilityFixturePromotionPacket JSON for the cited fixture.",
    ),
) -> None:
    """Validate a stability-fit record and persist canonical JSON."""
    try:
        fit_record = StabilityFitRecord.model_validate_json(
            fit_record_path.read_text(encoding="utf-8")
        )
        promotion_packet = StabilityFixturePromotionPacket.model_validate_json(
            packet.read_text(encoding="utf-8")
        )
        if promotion_packet.promotion_target != "measured_stability_fixture":
            raise ValueError(
                "accept-fit requires a packet with "
                "promotion_target='measured_stability_fixture'"
            )
        out_path = _DEFAULT_FITS_DIR / f"{fit_record.fit_id}.json"
        _write_json_refusing_overwrite(out_path, _canonical_json(fit_record))
    except Exception as exc:
        typer.echo(f"accept-fit failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"wrote {out_path}")


@stability_app.command("residual-plot")
def residual_plot(
    fit_record_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        help="StabilityFitRecord JSON file to summarize.",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output SVG file path; defaults to <fit_id>.svg next to the input.",
    ),
) -> None:
    """Write an RFC 0058 stage-3 SVG residual placeholder."""
    try:
        fit_record = StabilityFitRecord.model_validate_json(
            fit_record_path.read_text(encoding="utf-8")
        )
        out_path = out if out is not None else fit_record_path.with_name(
            f"{fit_record.fit_id}.svg"
        )
        _write_json_refusing_overwrite(
            out_path,
            _residual_plot_svg(fit_record),
        )
    except Exception as exc:
        typer.echo(f"residual-plot failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"wrote {out_path}")


def _residual_plot_svg(fit_record: StabilityFitRecord) -> str:
    metrics = fit_record.fit_metrics
    hull_class = fit_record.hull_family_scope.hull_class
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
            'width="160mm" height="80mm" viewBox="0 0 160 80">',
            f"<title>Stability residual placeholder for {fit_record.fit_id}</title>",
            "<desc>validation_candidate vs reference</desc>",
            '<rect x="5" y="5" width="150" height="70" '
            'fill="none" stroke="#000000" stroke-width="0.3"/>',
            '<text x="10" y="18" font-family="sans-serif" font-size="5">',
            f"fit_id={fit_record.fit_id}",
            "</text>",
            '<text x="10" y="28" font-family="sans-serif" font-size="4">',
            f"hull_class={hull_class}",
            "</text>",
            '<text x="10" y="40" font-family="sans-serif" font-size="4">',
            "validation_candidate vs reference",
            "</text>",
            '<text x="10" y="52" font-family="sans-serif" font-size="4">',
            f"rmse_m={metrics.rmse_m} mape_fraction={metrics.mape_fraction}",
            "</text>",
            '<text x="10" y="62" font-family="sans-serif" font-size="4">',
            f"max_error_m={metrics.max_error_m} "
            f"coverage_fraction={metrics.coverage_fraction}",
            "</text>",
            "</svg>",
            "",
        ]
    )
