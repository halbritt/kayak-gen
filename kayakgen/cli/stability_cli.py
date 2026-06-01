"""RFC 0043 stage 4 / RFC 0058 stability-rig CLI surface.

Five subcommands:

- ``ingest-rig-run`` — validate a ``MeasuredStabilityFixture`` JSON and write
  the canonical manifest to ``data/stability/fixtures/<id>/manifest.json``.
- ``promote-fixture`` — validate a ``StabilityFixturePromotionPacket`` whose
  ``fixture_ref.fixture_sha256`` hash-binds it to the on-disk manifest, and
  write it verbatim to ``data/stability/fixtures/<id>/promotion.json``. The
  manifest is NEVER mutated; ``promotion.json`` IS the canonical
  ``AcceptedStabilityFixtureRecord``.
- ``accept-fit`` — validate a ``StabilityFitRecord`` against the cited fixture
  directory's manifest + promotion packet, then write the record to ``--out``.
  Signature: ``--fit-record <path> --fixture-id <id> --out <path>``. The prior
  ``--packet`` flag was REMOVED — pass ``--fixture-id`` instead.
- ``claim-status`` — read-only resolver that prints the analytical high-angle
  GZ claim label for a hull under the current accepted-fit registry.
- ``residual-plot`` — write an RFC 0058 stage-3 SVG residual placeholder.

Gate refusals emit one structured JSON line carrying the ``REASON_*`` code +
the operator-facing ``next_action`` template from
``kayakgen.eval.stability.registry.REASON_NEXT_ACTION``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import NoReturn

from typer.core import TyperGroup
import typer

from kayakgen.eval.stability.accepted_fit import (
    StabilityFitRecord,
    StabilityFixturePromotionPacket,
)
from kayakgen.eval.stability.evaluator import ANALYTICAL_EVALUATOR_VERSION
from kayakgen.eval.stability.high_angle_contracts import (
    resolve_analytical_claim_label,
)
from kayakgen.eval.stability.measured_fixture import MeasuredStabilityFixture
from kayakgen.eval.stability.registry import (
    REASON_EVALUATOR_VERSION_MISMATCH,
    REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH,
    REASON_FIT_METRICS_OUT_OF_THRESHOLDS,
    REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE,
    REASON_FIXTURE_MANIFEST_MISSING,
    REASON_FIXTURE_NOT_PROMOTED,
    REASON_FIXTURE_SHA256_MISMATCH,
    REASON_NEXT_ACTION,
    REASON_PROMOTION_PACKET_MISSING,
    REASON_STRICT_CHECK_SKIPPED,
    REASON_VALID_HEEL_RANGE_DISJOINT,
    fixture_canonical_sha256,
    load_stability_fit_registry,
)


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
    help=(
        "RFC 0043 stage 4 / RFC 0058 stability-rig pipeline: ingest, promote, "
        "accept, inspect measured-stability fixtures and the accepted-fit "
        "registry that flips the high-angle GZ claim label."
    ),
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


def _refuse(
    reason: str,
    *,
    fixture_id: str | None = None,
    **details: object,
) -> NoReturn:
    """Emit one structured JSON refusal line and exit non-zero.

    The shape matches the §E.3 contract: ``{ok, code, fixture_id, details,
    next_action}`` with ``next_action`` looked up from
    :data:`REASON_NEXT_ACTION`.
    """

    payload = {
        "ok": False,
        "code": reason,
        "fixture_id": fixture_id,
        "details": details,
        "next_action": REASON_NEXT_ACTION.get(reason, ""),
    }
    typer.echo(json.dumps(payload, sort_keys=True))
    raise typer.Exit(code=1)


def _heel_ranges_overlap(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return max(a[0], b[0]) <= min(a[1], b[1])


def _resolve_fits_root_display(fits_root: Path | None) -> str:
    if fits_root is not None:
        return str(fits_root)
    env = os.environ.get("KAYAKGEN_STABILITY_FITS_ROOT")
    if env:
        return env
    return str(_DEFAULT_FITS_DIR)


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
        help="StabilityFixturePromotionPacket JSON whose fixture_sha256 hash-binds the on-disk manifest.",
    ),
) -> None:
    """Persist a validated promotion packet alongside a fixture manifest.

    Writes the packet verbatim to
    ``data/stability/fixtures/<fixture_id>/promotion.json`` (the canonical
    ``AcceptedStabilityFixtureRecord``). The manifest at
    ``data/stability/fixtures/<fixture_id>/manifest.json`` is NEVER mutated.
    Re-running with byte-identical packet bytes is a clean no-op.
    """
    fixture_dir = _DEFAULT_FIXTURES_DIR / fixture_id
    manifest_path = fixture_dir / "manifest.json"
    promotion_path = fixture_dir / "promotion.json"

    if not manifest_path.is_file():
        _refuse(
            REASON_FIXTURE_MANIFEST_MISSING,
            fixture_id=fixture_id,
            manifest_path=str(manifest_path),
        )

    # Persist the SUBMITTED bytes verbatim — re-promote-with-identical-bytes
    # must compare against the operator's original packet, not a canonicalized
    # rewrite. (Threat-model review, finding 4.)
    try:
        packet_text = packet.read_text(encoding="utf-8")
        promotion_packet = StabilityFixturePromotionPacket.model_validate_json(
            packet_text
        )
    except Exception as exc:
        typer.echo(f"promote-fixture failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    try:
        manifest_bytes = manifest_path.read_text(encoding="utf-8")
        manifest = MeasuredStabilityFixture.model_validate_json(manifest_bytes)
    except Exception as exc:
        typer.echo(f"promote-fixture failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if manifest.fixture_id != fixture_id:
        typer.echo(
            "promote-fixture failed: fixture_id mismatch: path requested "
            f"{fixture_id!r}, manifest carries {manifest.fixture_id!r}",
            err=True,
        )
        raise typer.Exit(code=1)

    manifest_sha = fixture_canonical_sha256(manifest)
    if promotion_packet.fixture_ref.fixture_sha256 != manifest_sha:
        _refuse(
            REASON_FIXTURE_SHA256_MISMATCH,
            fixture_id=fixture_id,
            expected_sha256=manifest_sha,
            actual_sha256=promotion_packet.fixture_ref.fixture_sha256,
        )

    if promotion_path.exists():
        if promotion_path.read_text(encoding="utf-8") == packet_text:
            typer.echo(f"no-op {promotion_path}")
            return
        typer.echo(
            "promote-fixture failed: refusing to overwrite existing artifact: "
            f"{promotion_path}",
            err=True,
        )
        raise typer.Exit(code=1)

    promotion_path.parent.mkdir(parents=True, exist_ok=True)
    promotion_path.write_text(packet_text, encoding="utf-8")
    # Defense in depth: confirm we did not perturb the manifest bytes.
    assert manifest_path.read_text(encoding="utf-8") == manifest_bytes
    typer.echo(f"wrote {promotion_path}")


@stability_app.command("accept-fit")
def accept_fit(
    fit_record_path: Path = typer.Option(
        ...,
        "--fit-record",
        exists=True,
        dir_okay=False,
        help="StabilityFitRecord JSON to validate and persist.",
    ),
    fixture_id: str = typer.Option(
        ...,
        "--fixture-id",
        help=(
            "Fixture id under data/stability/fixtures/<fixture_id>/ that the "
            "fit cites; its co-located promotion.json is the canonical "
            "acceptance source-of-truth."
        ),
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output path for the accepted StabilityFitRecord JSON.",
    ),
    packet: str | None = typer.Option(
        None,
        "--packet",
        hidden=True,
        help="REMOVED in RFC 0043 stage 4 — pass --fixture-id instead.",
    ),
) -> None:
    """Validate a stability-fit record and persist canonical JSON.

    Signature: ``--fit-record <path> --fixture-id <id> --out <path>``.

    The prior ``--packet`` flag was REMOVED in RFC 0043 stage 4. Acceptance is
    now anchored on the fixture directory's co-located ``promotion.json`` (the
    canonical ``AcceptedStabilityFixtureRecord``); pass the fixture id with
    ``--fixture-id`` instead. The output record carries
    ``acceptance_verdict='accepted'`` and ``strict=True``; any other shape is
    refused with a structured JSON refusal naming the failing gate.
    """
    if packet is not None:
        typer.echo(
            "accept-fit failed: --packet was REMOVED in RFC 0043 stage 4. "
            "Pass --fixture-id <id> instead; the fixture's co-located "
            "promotion.json is the canonical acceptance source-of-truth.",
            err=True,
        )
        raise typer.Exit(code=2)

    fixture_dir = _DEFAULT_FIXTURES_DIR / fixture_id
    manifest_path = fixture_dir / "manifest.json"
    promotion_path = fixture_dir / "promotion.json"

    if not manifest_path.is_file():
        _refuse(
            REASON_FIXTURE_MANIFEST_MISSING,
            fixture_id=fixture_id,
            manifest_path=str(manifest_path),
        )
    if not promotion_path.is_file():
        _refuse(
            REASON_PROMOTION_PACKET_MISSING,
            fixture_id=fixture_id,
            promotion_path=str(promotion_path),
        )

    try:
        fit_record = StabilityFitRecord.model_validate_json(
            fit_record_path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        typer.echo(f"accept-fit failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    try:
        promotion_packet = StabilityFixturePromotionPacket.model_validate_json(
            promotion_path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        typer.echo(f"accept-fit failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    try:
        manifest = MeasuredStabilityFixture.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        typer.echo(f"accept-fit failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    manifest_sha = fixture_canonical_sha256(manifest)
    if promotion_packet.fixture_ref.fixture_sha256 != manifest_sha:
        _refuse(
            REASON_FIXTURE_SHA256_MISMATCH,
            fixture_id=fixture_id,
            expected_sha256=manifest_sha,
            actual_sha256=promotion_packet.fixture_ref.fixture_sha256,
        )

    if promotion_packet.promotion_target != "measured_stability_fixture":
        _refuse(
            REASON_FIXTURE_NOT_PROMOTED,
            fixture_id=fixture_id,
            promotion_target=promotion_packet.promotion_target,
        )

    cited = next(
        (
            ref for ref in fit_record.fixtures
            if ref.fixture_id == fixture_id and ref.fixture_sha256 == manifest_sha
        ),
        None,
    )
    if cited is None:
        _refuse(
            REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE,
            fixture_id=fixture_id,
            expected_sha256=manifest_sha,
            fit_fixtures=[
                {"fixture_id": r.fixture_id, "fixture_sha256": r.fixture_sha256}
                for r in fit_record.fixtures
            ],
        )

    # Bind the fit's scope to the measured fixture's hull identity. Without
    # this, a strict accepted fit anchored to a sea_kayak fixture could declare
    # a sprint_k1 scope + a sprint hull's design hash and flip a sprint hull
    # against a sea-kayak measurement. (Threat-model review, finding 1.)
    if (
        fit_record.hull_family_scope.hull_class
        != manifest.hull_identity.hull_class
    ):
        _refuse(
            REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH,
            fixture_id=fixture_id,
            fit_hull_class=fit_record.hull_family_scope.hull_class,
            fixture_hull_class=manifest.hull_identity.hull_class,
        )

    if not _heel_ranges_overlap(
        fit_record.valid_heel_range_deg, manifest.valid_heel_range_deg
    ):
        _refuse(
            REASON_VALID_HEEL_RANGE_DISJOINT,
            fixture_id=fixture_id,
            fit_valid_heel_range_deg=list(fit_record.valid_heel_range_deg),
            fixture_valid_heel_range_deg=list(manifest.valid_heel_range_deg),
        )

    if fit_record.analytical_evaluator_version != ANALYTICAL_EVALUATOR_VERSION:
        _refuse(
            REASON_EVALUATOR_VERSION_MISMATCH,
            fixture_id=fixture_id,
            fit_evaluator_version=fit_record.analytical_evaluator_version,
            runtime_evaluator_version=ANALYTICAL_EVALUATOR_VERSION,
        )

    if not fit_record.strict:
        _refuse(
            REASON_STRICT_CHECK_SKIPPED,
            fixture_id=fixture_id,
            fit_id=fit_record.fit_id,
        )

    if fit_record.acceptance_verdict != "accepted":
        _refuse(
            REASON_FIT_METRICS_OUT_OF_THRESHOLDS,
            fixture_id=fixture_id,
            acceptance_verdict=fit_record.acceptance_verdict,
        )

    try:
        _write_json_refusing_overwrite(out, _canonical_json(fit_record))
    except FileExistsError as exc:
        typer.echo(f"accept-fit failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"wrote {out}")


@stability_app.command("claim-status")
def claim_status(
    hull_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        help="Hull JSON to resolve the analytical high-angle GZ claim label for.",
    ),
    fits_root: Path | None = typer.Option(
        None,
        "--fits-root",
        help=(
            "Accepted-fit registry root; defaults to KAYAKGEN_STABILITY_FITS_ROOT "
            "or data/stability/fits."
        ),
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Include a `diagnostics` list of dropped fits + their reason codes.",
    ),
) -> None:
    """Print the resolved analytical high-angle GZ claim label for a hull under the current accepted-fit registry."""
    from kayakgen.io.json import load_hull

    try:
        hull = load_hull(hull_path)
    except Exception as exc:
        typer.echo(f"claim-status failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if debug:
        fits, diagnostics = load_stability_fit_registry(
            fits_root, with_diagnostics=True
        )
    else:
        fits = load_stability_fit_registry(fits_root)
        diagnostics = ()

    label = resolve_analytical_claim_label(hull, fits)

    hull_class = getattr(hull, "hull_class", None)
    design_hash = hull.design_hash() if hasattr(hull, "design_hash") else None

    covering_fit_id: str | None = None
    if isinstance(hull_class, str) and isinstance(design_hash, str):
        for fit in fits:
            scope = fit.hull_family_scope
            if (
                scope.hull_class == hull_class
                and design_hash in scope.design_hash_envelope
            ):
                covering_fit_id = fit.fit_id
                break

    payload: dict[str, object] = {
        "hull_class": hull_class,
        "design_hash": design_hash,
        "claim_label": label,
        "covering_fit_id": covering_fit_id,
        "fits_root": _resolve_fits_root_display(fits_root),
        "fits_loaded": len(fits),
        "dropped_fit_count": len(diagnostics),
    }
    if debug:
        payload["diagnostics"] = [
            {
                "fit_id": d.fit_id,
                "fit_path": str(d.fit_path),
                "reason_code": d.reason_code,
                "detail": d.detail,
            }
            for d in diagnostics
        ]
    typer.echo(json.dumps(payload, sort_keys=True))


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
