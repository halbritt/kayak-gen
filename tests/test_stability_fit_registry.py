"""RFC 0043 stage 4: accepted-fit registry gate tests.

These exercise the load-bearing claim-integrity surface
(``kayakgen/eval/stability/registry.py``) the threat-model design review
(workflow 0043) converged on: the high-angle GZ label flips ONLY when the full
provenance chain — immutable manifest + hash-bound promotion packet + strict
accepted fit with a matching evaluator version — is intact. Any tampered or
missing link drops the fit from the registry.

All fixtures are built deterministically in-test; no physical rig data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from kayakgen.eval.calibration.rights import RightsChecklist
from kayakgen.eval.stability.accepted_fit import (
    FixtureRef,
    HullFamilyScope,
    ReviewerSignature,
    StabilityFitMetrics,
    StabilityFitRecord,
    StabilityFixturePromotionPacket,
)
from kayakgen.eval.stability.evaluator import ANALYTICAL_EVALUATOR_VERSION
from kayakgen.eval.stability.measured_fixture import (
    CalibrationTrace,
    FreeEquilibriumPoint,
    FreeEquilibriumTrace,
    HullIdentityRef,
    HysteresisBound,
    LoadingConfiguration,
    MeasuredStabilityFixture,
    MeasuredStabilityRow,
)
from kayakgen.eval.stability import registry as reg


# ---------------------------------------------------------------------------
# Deterministic in-test acceptance-triple factory
# ---------------------------------------------------------------------------


def _fixture(intended_use: str = "measured_stability_fixture", **overrides) -> MeasuredStabilityFixture:
    defaults = dict(
        fixture_id="fxt-001",
        title="Test rig run",
        source_citation="in-test rig, 2026",
        rights=RightsChecklist(
            license_identifier="CC BY 4.0",
            attribution="Test Lab",
            source_locator="https://example.org/rig",
            redistribution_authorized=True,
            attribution_required=True,
        ),
        extraction_method="strain_gauged_moment_arm_v1",
        hull_identity=HullIdentityRef(
            manufacturer="TestCo",
            model="Mk1",
            serial_or_year="2026",
            scan_hash="a" * 64,
            scan_method="Artec Eva",
            hull_class="sea_kayak",
        ),
        configuration="sealed_deck",
        loading=LoadingConfiguration(
            displacement_kg=110.0,
            paddler_state="rigid_manikin",
            paddler_mass_kg=85.0,
            paddler_cg_height_m=0.65,
        ),
        valid_heel_range_deg=(0.0, 30.0),
        rig_design_ref="docs/research/rig.md",
        geometry_manifest_ref="data/scan.json",
        calibration_trace=CalibrationTrace(
            pre_run_trace_path="cal/pre.csv",
            post_run_trace_path="cal/post.csv",
            dead_weight_kg=5.0,
            measured_arm_pre_m=0.3000,
            measured_arm_post_m=0.3003,
        ),
        free_equilibrium_trace=FreeEquilibriumTrace(
            points=[
                FreeEquilibriumPoint(theta_deg=0, trim_deg=0.0, heave_m=0.0),
                FreeEquilibriumPoint(theta_deg=15, trim_deg=0.5, heave_m=-0.005),
                FreeEquilibriumPoint(theta_deg=30, trim_deg=1.2, heave_m=-0.012),
            ],
        ),
        hysteresis_bound=HysteresisBound(observed_max_fraction=0.018, observed_at_theta_deg=22.0),
        rows=[
            MeasuredStabilityRow(theta_deg=0, gz_m=0.0, gz_std_m=0.0005),
            MeasuredStabilityRow(theta_deg=15, gz_m=0.045, gz_std_m=0.001),
            MeasuredStabilityRow(theta_deg=30, gz_m=0.062, gz_std_m=0.001),
        ],
        intended_use=intended_use,
    )
    defaults.update(overrides)
    return MeasuredStabilityFixture(**defaults)


def _packet(fixture: MeasuredStabilityFixture, **overrides) -> StabilityFixturePromotionPacket:
    sha = reg.fixture_canonical_sha256(fixture)
    defaults = dict(
        fixture_ref=FixtureRef(
            fixture_id=fixture.fixture_id,
            fixture_path=f"data/stability/fixtures/{fixture.fixture_id}/manifest.json",
            fixture_sha256=sha,
        ),
        rights_review="accepted",
        hull_identity_review="accepted",
        calibration_drift_review="accepted",
        hysteresis_review="accepted",
        free_equilibrium_review="accepted",
        rig_design_match=True,
        promotion_target="measured_stability_fixture",
        reviewer_signature=ReviewerSignature(
            reviewer_label="op", reviewer_role="naval_architect", signed_at=datetime(2026, 6, 1, tzinfo=timezone.utc)
        ),
    )
    defaults.update(overrides)
    return StabilityFixturePromotionPacket(**defaults)


def _fit(fixture: MeasuredStabilityFixture, **overrides) -> StabilityFitRecord:
    sha = reg.fixture_canonical_sha256(fixture)
    defaults = dict(
        fit_id="fit-001",
        analytical_evaluator_version=ANALYTICAL_EVALUATOR_VERSION,
        hull_family_scope=HullFamilyScope(hull_class="sea_kayak", design_hash_envelope=["deadbeef"]),
        valid_heel_range_deg=(0.0, 30.0),
        fixtures=[
            FixtureRef(
                fixture_id=fixture.fixture_id,
                fixture_path=f"data/stability/fixtures/{fixture.fixture_id}/manifest.json",
                fixture_sha256=sha,
            )
        ],
        fit_metrics=StabilityFitMetrics(
            rmse_m=0.003, mape_fraction=0.04, max_error_m=0.008, coverage_fraction=0.95
        ),
        acceptance_verdict="accepted",
        accepted_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        reviewer_signature=ReviewerSignature(
            reviewer_label="op", reviewer_role="naval_architect", signed_at=datetime(2026, 6, 1, tzinfo=timezone.utc)
        ),
        strict=True,
    )
    defaults.update(overrides)
    return StabilityFitRecord(**defaults)


def _stage(tmp_path: Path, fixture, packet, fit, *, stage_traces: bool = True) -> Path:
    """Write a fits/fixtures layout to disk. Returns the fits_root."""
    fits_root = tmp_path / "data" / "stability" / "fits"
    fixtures_root = tmp_path / "data" / "stability" / "fixtures"
    fits_root.mkdir(parents=True, exist_ok=True)
    if fixture is not None:
        fdir = fixtures_root / fixture.fixture_id
        fdir.mkdir(parents=True, exist_ok=True)
        (fdir / "manifest.json").write_text(fixture.model_dump_json(), encoding="utf-8")
        if stage_traces:
            (fdir / "cal").mkdir(exist_ok=True)
            (fdir / "cal" / "pre.csv").write_text("t,arm\n", encoding="utf-8")
            (fdir / "cal" / "post.csv").write_text("t,arm\n", encoding="utf-8")
        if packet is not None:
            (fdir / "promotion.json").write_text(packet.model_dump_json(), encoding="utf-8")
    if fit is not None:
        (fits_root / f"{fit.fit_id}.json").write_text(fit.model_dump_json(), encoding="utf-8")
    return fits_root


@pytest.fixture(autouse=True)
def _clear_cache():
    reg.clear_registry_cache()
    yield
    reg.clear_registry_cache()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_full_chain_loads_fit(tmp_path):
    fx = _fixture()
    root = _stage(tmp_path, fx, _packet(fx), _fit(fx))
    fits = reg.load_stability_fit_registry(root)
    assert len(fits) == 1
    assert fits[0].fit_id == "fit-001"


# ---------------------------------------------------------------------------
# codex P1: fixture/promotion presence alone never yields a loaded fit
# ---------------------------------------------------------------------------


def test_promoted_fixture_without_fit_loads_nothing(tmp_path):
    fx = _fixture()
    # manifest + promotion.json present, but NO fit record under fits/.
    root = _stage(tmp_path, fx, _packet(fx), None)
    fits, diags = reg.load_stability_fit_registry(root, with_diagnostics=True)
    assert fits == ()
    assert diags == ()  # no fit files to diagnose


@pytest.mark.parametrize(
    "drop",
    ["promotion", "fit", "manifest"],
)
def test_full_chain_required_for_load(tmp_path, drop):
    fx = _fixture()
    packet = None if drop == "promotion" else _packet(fx)
    fit = None if drop == "fit" else _fit(fx)
    fixture = None if drop == "manifest" else fx
    root = _stage(tmp_path, fixture, packet, fit)
    fits = reg.load_stability_fit_registry(root)
    assert fits == ()


# ---------------------------------------------------------------------------
# Gate rejections (each drops the fit with its reason code)
# ---------------------------------------------------------------------------


def _reason(tmp_path, fixture, packet, fit, **stage_kw) -> str:
    root = _stage(tmp_path, fixture, packet, fit, **stage_kw)
    fits, diags = reg.load_stability_fit_registry(root, with_diagnostics=True)
    assert fits == ()
    assert len(diags) == 1
    return diags[0].reason_code


def test_gate_sha256_mismatch(tmp_path):
    fx = _fixture()
    packet = _packet(fx, fixture_ref=FixtureRef(
        fixture_id=fx.fixture_id, fixture_path="x", fixture_sha256="0" * 64))
    assert _reason(tmp_path, fx, packet, _fit(fx)) == reg.REASON_FIXTURE_SHA256_MISMATCH


def test_gate_not_promoted(tmp_path):
    # The loader uses promotion.json as the source of truth, not the manifest's
    # intended_use hint. An idempotent (measured-default) manifest paired with a
    # promotion packet whose target is validation_candidate must NOT load.
    fx = _fixture()
    packet = _packet(fx, promotion_target="validation_candidate")
    assert _reason(tmp_path, fx, packet, _fit(fx)) == reg.REASON_FIXTURE_NOT_PROMOTED


def test_gate_missing_promotion_packet(tmp_path):
    fx = _fixture()
    assert _reason(tmp_path, fx, None, _fit(fx)) == reg.REASON_PROMOTION_PACKET_MISSING


def test_gate_evaluator_version_mismatch(tmp_path):
    fx = _fixture()
    fit = _fit(fx, analytical_evaluator_version="some-old-version")
    assert _reason(tmp_path, fx, _packet(fx), fit) == reg.REASON_EVALUATOR_VERSION_MISMATCH


def test_gate_strict_check_skipped(tmp_path):
    fx = _fixture()
    # strict=False with a loose-but-valid metric set: schema allows it, loader drops it.
    fit = _fit(
        fx,
        strict=False,
        fit_metrics=StabilityFitMetrics(rmse_m=0.02, mape_fraction=0.2, max_error_m=0.05, coverage_fraction=0.5),
    )
    assert _reason(tmp_path, fx, _packet(fx), fit) == reg.REASON_STRICT_CHECK_SKIPPED


def test_gate_disjoint_heel_range(tmp_path):
    fx = _fixture()  # fixture range (0, 30)
    fit = _fit(fx, valid_heel_range_deg=(40.0, 60.0))
    assert _reason(tmp_path, fx, _packet(fx), fit) == reg.REASON_VALID_HEEL_RANGE_DISJOINT


def test_gate_loose_self_declared_bounds(tmp_path):
    # drift_bound_fraction default is 0.005 (operator max). Widen it past the max.
    fx = _fixture(calibration_trace=CalibrationTrace(
        pre_run_trace_path="cal/pre.csv",
        post_run_trace_path="cal/post.csv",
        dead_weight_kg=5.0,
        measured_arm_pre_m=0.3000,
        measured_arm_post_m=0.3003,
        drift_bound_fraction=0.05,
    ))
    assert _reason(tmp_path, fx, _packet(fx), _fit(fx)) == reg.REASON_FIXTURE_BOUNDS_TOO_LOOSE


def test_gate_rights_not_redistributable(tmp_path):
    fx = _fixture(rights=RightsChecklist(
        license_identifier="proprietary",
        attribution="Lab",
        source_locator="x",
        redistribution_authorized=False,
        attribution_required=True,
    ))
    assert _reason(tmp_path, fx, _packet(fx), _fit(fx)) == reg.REASON_FIXTURE_RIGHTS_NOT_REDISTRIBUTABLE


def test_gate_smoothness_failures(tmp_path):
    fx = _fixture(free_equilibrium_trace=FreeEquilibriumTrace(
        points=[
            FreeEquilibriumPoint(theta_deg=0, trim_deg=0.0, heave_m=0.0),
            FreeEquilibriumPoint(theta_deg=15, trim_deg=0.5, heave_m=-0.005),
            FreeEquilibriumPoint(theta_deg=30, trim_deg=1.2, heave_m=-0.012),
        ],
        smoothness_failures=["wobble at 15deg"],
    ))
    assert _reason(tmp_path, fx, _packet(fx), _fit(fx)) == reg.REASON_FIXTURE_SMOOTHNESS_FAILURES


def test_gate_unresolved_trace_path(tmp_path):
    fx = _fixture()
    # Stage everything EXCEPT the trace evidence files.
    assert _reason(tmp_path, fx, _packet(fx), _fit(fx), stage_traces=False) == reg.REASON_FIXTURE_TRACE_PATH_UNRESOLVED


def test_post_sign_review_tamper_drops_fit(tmp_path):
    # Threat: a valid measured packet is signed, then its on-disk bytes are
    # edited to flip a review to non-accepted while keeping
    # promotion_target=measured. The StabilityFixturePromotionPacket validator
    # forbids that combination at construction, so the loader's re-parse of the
    # tampered bytes fails — gate 4 rejects it (promotion_packet_missing) before
    # the semantic gate 7 is reached. Either way the fit is DROPPED, which is the
    # load-bearing security property. (Gate 7 remains as defense-in-depth should
    # the schema validator ever loosen.)
    fx = _fixture()
    root = _stage(tmp_path, fx, _packet(fx), _fit(fx))
    promo_path = root.parent / "fixtures" / fx.fixture_id / "promotion.json"
    import json
    payload = json.loads(promo_path.read_text())
    payload["rights_review"] = "deferred"  # tamper: keep target=measured, break a review
    promo_path.write_text(json.dumps(payload), encoding="utf-8")
    reg.clear_registry_cache()
    fits, diags = reg.load_stability_fit_registry(root, with_diagnostics=True)
    assert fits == ()
    assert len(diags) == 1
    assert diags[0].reason_code in (
        reg.REASON_PROMOTION_PACKET_MISSING,
        reg.REASON_PROMOTION_PACKET_REVIEW_INCOMPLETE,
    )


# ---------------------------------------------------------------------------
# Memoization + diagnostics
# ---------------------------------------------------------------------------


def test_registry_memoizes_until_mtime_change(tmp_path):
    fx = _fixture()
    root = _stage(tmp_path, fx, _packet(fx), _fit(fx))
    first = reg.load_stability_fit_registry(root)
    second = reg.load_stability_fit_registry(root)
    assert first is second  # same cached tuple object

    # Add a second valid fit -> mtime advances -> registry rebuilds.
    fit2 = _fit(fx, fit_id="fit-002")
    (root / "fit-002.json").write_text(fit2.model_dump_json(), encoding="utf-8")
    import os
    bump = os.stat(root).st_mtime_ns + 1_000_000_000
    os.utime(root, ns=(bump, bump))
    third = reg.load_stability_fit_registry(root)
    assert third is not first
    assert {f.fit_id for f in third} == {"fit-001", "fit-002"}


def test_unreadable_fit_recorded_in_diagnostics(tmp_path):
    fx = _fixture()
    root = _stage(tmp_path, fx, _packet(fx), None)
    (root / "garbage.json").write_text("{not valid json", encoding="utf-8")
    fits, diags = reg.load_stability_fit_registry(root, with_diagnostics=True)
    assert fits == ()
    assert len(diags) == 1
    assert diags[0].reason_code == reg.REASON_FIT_RECORD_UNREADABLE


def test_every_reason_has_a_next_action():
    # Every gate constant the loader can emit has operator-facing remediation copy.
    emitted = {
        reg.REASON_FIXTURE_MANIFEST_MISSING,
        reg.REASON_FIXTURE_SMOOTHNESS_FAILURES,
        reg.REASON_FIXTURE_TRACE_PATH_UNRESOLVED,
        reg.REASON_FIXTURE_BOUNDS_TOO_LOOSE,
        reg.REASON_FIXTURE_RIGHTS_NOT_REDISTRIBUTABLE,
        reg.REASON_PROMOTION_PACKET_MISSING,
        reg.REASON_FIXTURE_SHA256_MISMATCH,
        reg.REASON_FIXTURE_NOT_PROMOTED,
        reg.REASON_PROMOTION_PACKET_REVIEW_INCOMPLETE,
        reg.REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE,
        reg.REASON_VALID_HEEL_RANGE_DISJOINT,
        reg.REASON_EVALUATOR_VERSION_MISMATCH,
        reg.REASON_STRICT_CHECK_SKIPPED,
        reg.REASON_FIT_METRICS_OUT_OF_THRESHOLDS,
    }
    for code in emitted:
        assert code in reg.REASON_NEXT_ACTION
