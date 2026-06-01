"""RFC 0043 stage 4 — end-to-end claim-state flip + CLI + web integration tests.

These exercise the full provenance chain: a real :class:`Hull` with a
``hull_class`` plus an accepted fit whose ``hull_family_scope`` covers it flips
``GeneratedBodyGZCurve.result_semantics`` from
``unvalidated_hydrostatic_comparison`` to
``validated_hydrostatic_comparison``. The web frontier-view colour token
flips with it; the desktop chip stays minimal per D014.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.stability import registry as reg
from kayakgen.eval.stability.high_angle_contracts import (
    resolve_analytical_claim_label,
)
from kayakgen.model.hull import Hull

from tests.conftest import (
    StabilityAcceptanceTriple,
    make_stability_acceptance_triple,
    stage_acceptance_triple,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    reg.clear_registry_cache()
    yield
    reg.clear_registry_cache()


def _hull(hull_class: str | None = "sea_kayak") -> Hull:
    return Hull(name="test-hull", hull_class=hull_class)


def _triple_for_hull(hull: Hull, *, fit_id: str = "fit-001") -> StabilityAcceptanceTriple:
    return make_stability_acceptance_triple(
        hull_class=hull.hull_class or "sea_kayak",
        design_hash=hull.design_hash(),
        fit_id=fit_id,
    )


def _set_fits_root(
    monkeypatch: pytest.MonkeyPatch, fits_root: Path | None
) -> None:
    if fits_root is None:
        monkeypatch.delenv("KAYAKGEN_STABILITY_FITS_ROOT", raising=False)
    else:
        monkeypatch.setenv("KAYAKGEN_STABILITY_FITS_ROOT", str(fits_root))


# ---------------------------------------------------------------------------
# Resolver-level flip tests (the load-bearing semantic surface)
# ---------------------------------------------------------------------------


def test_claim_label_flips_when_fit_covers_hull(tmp_path: Path) -> None:
    hull = _hull()
    triple = _triple_for_hull(hull)
    root = stage_acceptance_triple(tmp_path, triple)
    fits = reg.load_stability_fit_registry(root)

    assert resolve_analytical_claim_label(hull, fits) == "validated_hydrostatic_comparison"


def test_claim_label_unchanged_when_no_fit_covers_hull(tmp_path: Path) -> None:
    # Stage a fit for sea_kayak, then ask about a sprint_k1 hull.
    triple = make_stability_acceptance_triple(hull_class="sea_kayak")
    root = stage_acceptance_triple(tmp_path, triple)
    fits = reg.load_stability_fit_registry(root)
    other_hull = Hull(name="other", hull_class="sprint_k1")

    assert (
        resolve_analytical_claim_label(other_hull, fits)
        == "unvalidated_hydrostatic_comparison"
    )


def test_claim_label_unchanged_for_hull_with_no_hull_class(tmp_path: Path) -> None:
    # The safety invariant: a hull with hull_class=None never flips.
    hull = Hull(name="raw")
    triple = make_stability_acceptance_triple(
        hull_class="sea_kayak", design_hash=hull.design_hash()
    )
    root = stage_acceptance_triple(tmp_path, triple)
    fits = reg.load_stability_fit_registry(root)

    assert (
        resolve_analytical_claim_label(hull, fits)
        == "unvalidated_hydrostatic_comparison"
    )


def test_claim_label_unchanged_for_strict_skipped_fit(tmp_path: Path) -> None:
    hull = _hull()
    triple = make_stability_acceptance_triple(
        hull_class=hull.hull_class or "sea_kayak",
        design_hash=hull.design_hash(),
        strict=False,
    )
    root = stage_acceptance_triple(tmp_path, triple)
    fits = reg.load_stability_fit_registry(root)

    assert fits == ()
    assert (
        resolve_analytical_claim_label(hull, fits)
        == "unvalidated_hydrostatic_comparison"
    )


# ---------------------------------------------------------------------------
# Registry memoization + env-var resolution
# ---------------------------------------------------------------------------


def test_registry_loader_memoizes_until_mtime_change(tmp_path: Path) -> None:
    hull = _hull()
    triple = _triple_for_hull(hull)
    root = stage_acceptance_triple(tmp_path, triple)

    first = reg.load_stability_fit_registry(root)
    second = reg.load_stability_fit_registry(root)
    assert first is second

    # Bump the fits-dir mtime by writing another valid fit.
    second_triple = _triple_for_hull(hull, fit_id="fit-002")
    (root / "fit-002.json").write_text(
        second_triple.fit.model_dump_json(), encoding="utf-8"
    )
    bump = os.stat(root).st_mtime_ns + 1_000_000_000
    os.utime(root, ns=(bump, bump))

    third = reg.load_stability_fit_registry(root)
    assert third is not first
    assert {fit.fit_id for fit in third} == {"fit-001", "fit-002"}


def test_registry_loader_skips_invalid_fit_with_diagnostic(tmp_path: Path) -> None:
    triple = make_stability_acceptance_triple()
    root = stage_acceptance_triple(tmp_path, triple, write_fit=False)
    (root / "garbage.json").write_text("{not valid json", encoding="utf-8")
    fits, diags = reg.load_stability_fit_registry(root, with_diagnostics=True)

    assert fits == ()
    assert any(d.reason_code == reg.REASON_FIT_RECORD_UNREADABLE for d in diags)


def test_registry_loader_uses_env_var_then_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    triple = make_stability_acceptance_triple()
    env_root = stage_acceptance_triple(tmp_path / "env", triple)
    explicit_root = stage_acceptance_triple(tmp_path / "explicit", triple)
    monkeypatch.setenv("KAYAKGEN_STABILITY_FITS_ROOT", str(env_root))

    via_env = reg.load_stability_fit_registry()
    via_explicit = reg.load_stability_fit_registry(explicit_root)

    assert len(via_env) == 1
    assert len(via_explicit) == 1
    # Both succeed; the explicit argument wins over the env override.
    assert via_env[0].fit_id == "fit-001"
    assert via_explicit[0].fit_id == "fit-001"


# ---------------------------------------------------------------------------
# claim-status CLI integration
# ---------------------------------------------------------------------------


def test_claim_status_command_reports_resolved_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    hull = _hull()
    triple = _triple_for_hull(hull)
    root = stage_acceptance_triple(tmp_path, triple)
    hull_path = tmp_path / "hull.json"
    hull_path.write_text(hull.model_dump_json(), encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["stability", "claim-status", str(hull_path), "--fits-root", str(root)],
    )

    assert result.exit_code == 0, result.output
    body = json.loads(result.output)
    assert body["hull_class"] == "sea_kayak"
    assert body["claim_label"] == "validated_hydrostatic_comparison"
    assert body["covering_fit_id"] == "fit-001"
    assert body["fits_loaded"] == 1
    assert body["dropped_fit_count"] == 0


def test_claim_status_debug_lists_dropped_fit_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    triple = make_stability_acceptance_triple(
        evaluator_version="some-stale-version"
    )
    root = stage_acceptance_triple(tmp_path, triple)
    hull = _hull()
    hull_path = tmp_path / "hull.json"
    hull_path.write_text(hull.model_dump_json(), encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "stability",
            "claim-status",
            str(hull_path),
            "--fits-root",
            str(root),
            "--debug",
        ],
    )

    assert result.exit_code == 0, result.output
    body = json.loads(result.output)
    assert body["claim_label"] == "unvalidated_hydrostatic_comparison"
    assert body["dropped_fit_count"] == 1
    assert body["diagnostics"][0]["reason_code"] == reg.REASON_EVALUATOR_VERSION_MISMATCH


# ---------------------------------------------------------------------------
# Evaluator + web frontier-view propagation
# ---------------------------------------------------------------------------


def test_evaluator_flips_result_semantics_under_loaded_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from kayakgen.eval.stability import evaluator as ev

    hull = _hull()
    triple = _triple_for_hull(hull)
    root = stage_acceptance_triple(tmp_path, triple)
    _set_fits_root(monkeypatch, root)
    reg.clear_registry_cache()

    fits = ev._loaded_fit_registry()
    assert resolve_analytical_claim_label(hull, fits) == "validated_hydrostatic_comparison"


def test_generate_frontier_view_color_token_flips_under_loaded_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from kayakgen.ui.web import generate_frontier_view as gfv

    hull = _hull()
    triple = _triple_for_hull(hull)
    root = stage_acceptance_triple(tmp_path, triple)
    _set_fits_root(monkeypatch, root)
    reg.clear_registry_cache()

    fits = gfv._loaded_fit_registry()
    label = resolve_analytical_claim_label(hull, fits)
    assert label == "validated_hydrostatic_comparison"


# ---------------------------------------------------------------------------
# Provenance + chain-completeness invariants (synthesis §D)
# ---------------------------------------------------------------------------


def test_provenance_chain_holds_under_manifest_tamper(tmp_path: Path) -> None:
    hull = _hull()
    triple = _triple_for_hull(hull)
    root = stage_acceptance_triple(tmp_path, triple)
    first = reg.load_stability_fit_registry(root)
    assert len(first) == 1

    # Tamper the manifest bytes after acceptance.
    manifest_path = (
        root.parent / "fixtures" / triple.fixture.fixture_id / "manifest.json"
    )
    payload = json.loads(manifest_path.read_text())
    payload["warnings"] = ["tampered_after_sign"]
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    bump = os.stat(root).st_mtime_ns + 1_000_000_000
    os.utime(root, ns=(bump, bump))

    second = reg.load_stability_fit_registry(root)
    assert second == ()


def test_accepted_fixture_alone_does_not_flip_label(tmp_path: Path) -> None:
    hull = _hull()
    triple = _triple_for_hull(hull)
    # Stage manifest + promotion.json, but no fit record.
    root = stage_acceptance_triple(tmp_path, triple, write_fit=False)
    fits = reg.load_stability_fit_registry(root)

    assert fits == ()
    assert (
        resolve_analytical_claim_label(hull, fits)
        == "unvalidated_hydrostatic_comparison"
    )


@pytest.mark.parametrize("drop", ["manifest", "promotion", "fit"])
def test_full_chain_required_for_flip(tmp_path: Path, drop: str) -> None:
    hull = _hull()
    triple = _triple_for_hull(hull)
    root = stage_acceptance_triple(
        tmp_path,
        triple,
        write_promotion=(drop != "promotion"),
        write_fit=(drop != "fit"),
    )
    if drop == "manifest":
        manifest = root.parent / "fixtures" / triple.fixture.fixture_id / "manifest.json"
        manifest.unlink()

    fits = reg.load_stability_fit_registry(root)
    assert (
        resolve_analytical_claim_label(hull, fits)
        == "unvalidated_hydrostatic_comparison"
    )


def test_registry_drops_fit_when_scope_hull_class_diverges_from_fixture(
    tmp_path: Path,
) -> None:
    """Gate 8a (threat-model review, finding 1): an accepted fit whose
    ``hull_family_scope.hull_class`` disagrees with the measured fixture's
    ``hull_identity.hull_class`` is dropped from the registry. Without this
    gate a strict accepted fit anchored to a sea_kayak rig run could declare
    ``hull_family_scope.hull_class="sprint_k1"`` + a sprint hull's design
    hash and flip a sprint hull against a sea-kayak measurement."""
    sea_hull = Hull(name="sea", hull_class="sea_kayak")
    sprint_hull = Hull(name="sprint", hull_class="sprint_k1")
    fixture_triple = _triple_for_hull(sea_hull)
    # Override the fit's hull_family_scope to sprint_k1 + sprint hull's design
    # hash; the registry must drop it because the manifest is sea_kayak.
    from kayakgen.eval.stability.accepted_fit import HullFamilyScope, StabilityFitRecord

    payload = fixture_triple.fit.model_dump()
    payload["hull_family_scope"] = HullFamilyScope(
        hull_class="sprint_k1",
        design_hash_envelope=[sprint_hull.design_hash()],
    ).model_dump()
    sprint_scope_fit = StabilityFitRecord.model_validate(payload)
    crossed = StabilityAcceptanceTriple(
        fixture=fixture_triple.fixture,
        packet=fixture_triple.packet,
        fit=sprint_scope_fit,
    )
    root = stage_acceptance_triple(tmp_path, crossed)
    fits, diags = reg.load_stability_fit_registry(root, with_diagnostics=True)

    assert fits == ()
    assert len(diags) == 1
    assert diags[0].reason_code == reg.REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH
    # Resolver must NOT flip a sprint hull even though the dropped fit's scope
    # would have covered it.
    assert (
        resolve_analytical_claim_label(sprint_hull, fits)
        == "unvalidated_hydrostatic_comparison"
    )


def test_accept_fit_refuses_hull_class_fixture_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same gate at the CLI level, so the cross-class fit never lands."""
    from kayakgen.eval.stability.accepted_fit import HullFamilyScope, StabilityFitRecord
    from typer.testing import CliRunner

    sea_hull = Hull(name="sea", hull_class="sea_kayak")
    sprint_hull = Hull(name="sprint", hull_class="sprint_k1")
    triple = _triple_for_hull(sea_hull)
    payload = triple.fit.model_dump()
    payload["hull_family_scope"] = HullFamilyScope(
        hull_class="sprint_k1",
        design_hash_envelope=[sprint_hull.design_hash()],
    ).model_dump()
    crossed_fit = StabilityFitRecord.model_validate(payload)
    monkeypatch.chdir(tmp_path)
    # Stage manifest + promotion only; the fit goes via --fit-record.
    fixture_dir = (
        tmp_path / "data" / "stability" / "fixtures" / triple.fixture.fixture_id
    )
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "manifest.json").write_text(
        triple.fixture.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    (fixture_dir / "promotion.json").write_text(
        triple.packet.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    fit_path = tmp_path / "fit.json"
    fit_path.write_text(crossed_fit.model_dump_json(), encoding="utf-8")
    out = tmp_path / "out.json"

    result = CliRunner().invoke(
        app,
        [
            "stability",
            "accept-fit",
            "--fit-record",
            str(fit_path),
            "--fixture-id",
            triple.fixture.fixture_id,
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 1
    body = json.loads(
        next(line for line in result.output.splitlines() if line.startswith("{"))
    )
    assert body["code"] == reg.REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH
    assert not out.exists()


def test_registry_cache_invalidates_on_evaluator_version_change(
    tmp_path: Path,
) -> None:
    """Threat-model review, finding 2: the cache key includes evaluator
    version, so a second load under a stale runtime version must NOT return
    a tuple cached under the matching version."""
    hull = _hull()
    triple = _triple_for_hull(hull)
    root = stage_acceptance_triple(tmp_path, triple)

    matching = reg.load_stability_fit_registry(root)
    assert len(matching) == 1

    stale = reg.load_stability_fit_registry(
        root, runtime_evaluator_version="some-stale-version-v0"
    )
    assert stale == ()

    # And confirm the matching version still memoizes (same object on repeat).
    again = reg.load_stability_fit_registry(root)
    assert again is matching


def test_evaluator_version_mismatch_real_hull_through_loaded_registry(
    tmp_path: Path,
) -> None:
    """Production-path coverage (threat-model review, finding 3): a real
    :class:`Hull` resolved through the loaded registry stays
    ``unvalidated_hydrostatic_comparison`` when the fit's
    ``analytical_evaluator_version`` differs from the runtime."""
    hull = _hull()
    triple = make_stability_acceptance_triple(
        hull_class=hull.hull_class or "sea_kayak",
        design_hash=hull.design_hash(),
        evaluator_version="some-stale-version-v0",
    )
    root = stage_acceptance_triple(tmp_path, triple)
    fits = reg.load_stability_fit_registry(root)

    assert fits == ()
    assert (
        resolve_analytical_claim_label(hull, fits)
        == "unvalidated_hydrostatic_comparison"
    )


def test_registry_cache_invalidates_when_trace_evidence_disappears(
    tmp_path: Path,
) -> None:
    """Threat-model review revision 1 (P1): a cached passing fit must drop on
    the next non-diagnostic load when its calibration-trace evidence (non-JSON
    files like ``cal/pre.csv``) is removed. Gate 3 fails on a fresh scan when
    the trace is missing; the cache key MUST include the evidence tree so the
    fresh scan runs."""
    hull = _hull()
    triple = _triple_for_hull(hull)
    root = stage_acceptance_triple(tmp_path, triple)
    first = reg.load_stability_fit_registry(root)
    assert len(first) == 1

    # Delete the pre-run trace evidence (non-JSON) WITHOUT touching any JSON
    # file and WITHOUT manually clearing the cache.
    pre_csv = (
        root.parent / "fixtures" / triple.fixture.fixture_id / "cal" / "pre.csv"
    )
    pre_csv.unlink()

    second = reg.load_stability_fit_registry(root)
    assert second == ()


def test_registry_drops_fit_with_loose_self_declared_bounds(tmp_path: Path) -> None:
    triple = make_stability_acceptance_triple()
    payload = triple.fixture.model_dump()
    payload["calibration_trace"] = {
        **payload["calibration_trace"],
        "drift_bound_fraction": 0.05,
    }
    from kayakgen.eval.stability.measured_fixture import MeasuredStabilityFixture

    tampered = MeasuredStabilityFixture.model_validate(payload)
    triple_loose = StabilityAcceptanceTriple(
        fixture=tampered, packet=triple.packet, fit=triple.fit
    )
    # The packet's fixture_sha256 no longer matches; we expect either the bounds
    # gate or the sha gate to drop it — both are valid drops.
    root = stage_acceptance_triple(tmp_path, triple_loose)
    fits, diags = reg.load_stability_fit_registry(root, with_diagnostics=True)
    assert fits == ()
    assert diags[0].reason_code in (
        reg.REASON_FIXTURE_BOUNDS_TOO_LOOSE,
        reg.REASON_FIXTURE_SHA256_MISMATCH,
    )
