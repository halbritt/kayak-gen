"""Shared pytest options + factories for local and acceptance test profiles."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def pytest_addoption(parser):
    parser.addoption(
        "--browser-acceptance",
        action="store_true",
        default=False,
        help="Fail instead of skipping when required Playwright/Chromium tooling is missing.",
    )


# ---------------------------------------------------------------------------
# RFC 0043 stage 4: shared acceptance-triple factory
# ---------------------------------------------------------------------------

import pytest  # noqa: E402

from kayakgen.eval.calibration.rights import RightsChecklist  # noqa: E402
from kayakgen.eval.stability.accepted_fit import (  # noqa: E402
    FixtureRef,
    HullFamilyScope,
    ReviewerSignature,
    StabilityFitMetrics,
    StabilityFitRecord,
    StabilityFixturePromotionPacket,
)
from kayakgen.eval.stability.evaluator import (  # noqa: E402
    ANALYTICAL_EVALUATOR_VERSION,
)
from kayakgen.eval.stability.measured_fixture import (  # noqa: E402
    CalibrationTrace,
    FreeEquilibriumPoint,
    FreeEquilibriumTrace,
    HullIdentityRef,
    HysteresisBound,
    LoadingConfiguration,
    MeasuredStabilityFixture,
    MeasuredStabilityRow,
)
from kayakgen.eval.stability.registry import (  # noqa: E402
    clear_registry_cache,
    fixture_canonical_sha256,
)


@dataclass(frozen=True)
class StabilityAcceptanceTriple:
    """Three byte-stable records that share fixture id + design hash + version."""

    fixture: MeasuredStabilityFixture
    packet: StabilityFixturePromotionPacket
    fit: StabilityFitRecord


def _signed_at() -> datetime:
    return datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)


def _rights() -> RightsChecklist:
    return RightsChecklist(
        license_identifier="CC BY 4.0",
        attribution="Kayak Lab, 2026",
        source_locator="https://example.org/stability/fxt-001",
        redistribution_authorized=True,
        attribution_required=True,
    )


def _reviewer() -> ReviewerSignature:
    return ReviewerSignature(
        reviewer_label="op",
        reviewer_role="stability-fixture-reviewer",
        signed_at=_signed_at(),
    )


def make_stability_acceptance_triple(
    *,
    fixture_id: str = "fxt-001",
    hull_class: str = "sea_kayak",
    design_hash: str = "deadbeef",
    scan_hash: str | None = None,
    evaluator_version: str | None = None,
    strict: bool = True,
    intended_use: str = "measured_stability_fixture",
    fixture_heel_range: tuple[float, float] = (0.0, 30.0),
    fit_heel_range: tuple[float, float] = (0.0, 30.0),
    fit_id: str = "fit-001",
) -> StabilityAcceptanceTriple:
    """Deterministic in-test ``(fixture, packet, fit)`` triple (DESIGN_SYNTHESIS §D).

    The three records share ``fixture_id`` + ``design_hash`` + evaluator
    version + scan hash so the full §B gate chain passes by default. Tests
    derive failing variants by overriding a single keyword argument (e.g.
    ``evaluator_version="some-old-version"`` for the version-mismatch gate).
    """

    scan = scan_hash if scan_hash is not None else ("a" * 64)
    evaluator = (
        evaluator_version
        if evaluator_version is not None
        else ANALYTICAL_EVALUATOR_VERSION
    )

    fixture = MeasuredStabilityFixture(
        fixture_id=fixture_id,
        title="Test rig run",
        source_citation="in-test rig, 2026",
        rights=_rights(),
        extraction_method="strain_gauged_moment_arm_v1",
        hull_identity=HullIdentityRef(
            manufacturer="TestCo",
            model="Mk1",
            serial_or_year="2026",
            scan_hash=scan,
            scan_method="Artec Eva",
            hull_class=hull_class,
        ),
        configuration="sealed_deck",
        loading=LoadingConfiguration(
            displacement_kg=110.0,
            paddler_state="rigid_manikin",
            paddler_mass_kg=85.0,
            paddler_cg_height_m=0.65,
        ),
        valid_heel_range_deg=fixture_heel_range,
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
                FreeEquilibriumPoint(theta_deg=0.0, trim_deg=0.0, heave_m=0.0),
                FreeEquilibriumPoint(theta_deg=15.0, trim_deg=0.5, heave_m=-0.005),
                FreeEquilibriumPoint(theta_deg=30.0, trim_deg=1.2, heave_m=-0.012),
            ],
        ),
        hysteresis_bound=HysteresisBound(
            observed_max_fraction=0.018, observed_at_theta_deg=22.0
        ),
        rows=[
            MeasuredStabilityRow(theta_deg=0.0, gz_m=0.0, gz_std_m=0.0005),
            MeasuredStabilityRow(theta_deg=15.0, gz_m=0.045, gz_std_m=0.001),
            MeasuredStabilityRow(theta_deg=30.0, gz_m=0.062, gz_std_m=0.001),
        ],
        intended_use=intended_use,
    )

    fixture_sha256 = fixture_canonical_sha256(fixture)
    fixture_ref = FixtureRef(
        fixture_id=fixture.fixture_id,
        fixture_path=f"data/stability/fixtures/{fixture.fixture_id}/manifest.json",
        fixture_sha256=fixture_sha256,
    )

    packet = StabilityFixturePromotionPacket(
        fixture_ref=fixture_ref,
        rights_review="accepted",
        hull_identity_review="accepted",
        calibration_drift_review="accepted",
        hysteresis_review="accepted",
        free_equilibrium_review="accepted",
        rig_design_match=True,
        promotion_target="measured_stability_fixture",
        rejection_reasons=[],
        reviewer_signature=_reviewer(),
    )

    fit_metrics = (
        StabilityFitMetrics(
            rmse_m=0.003,
            mape_fraction=0.04,
            max_error_m=0.008,
            coverage_fraction=0.95,
        )
        if strict
        else StabilityFitMetrics(
            rmse_m=0.02,
            mape_fraction=0.2,
            max_error_m=0.05,
            coverage_fraction=0.5,
        )
    )

    fit = StabilityFitRecord(
        fit_id=fit_id,
        analytical_evaluator_version=evaluator,
        hull_family_scope=HullFamilyScope(
            hull_class=hull_class,
            design_hash_envelope=[design_hash],
        ),
        valid_heel_range_deg=fit_heel_range,
        fixtures=[fixture_ref],
        fit_metrics=fit_metrics,
        acceptance_verdict="accepted",
        rejection_reasons=[],
        reviewer_signature=_reviewer(),
        accepted_at=_signed_at(),
        strict=strict,
    )

    return StabilityAcceptanceTriple(fixture=fixture, packet=packet, fit=fit)


def stage_acceptance_triple(
    tmp_path: Path,
    triple: StabilityAcceptanceTriple,
    *,
    stage_traces: bool = True,
    write_promotion: bool = True,
    write_fit: bool = True,
) -> Path:
    """Stage a ``(manifest, promotion, fit)`` layout under ``tmp_path``.

    Returns the fits root (``tmp_path/data/stability/fits``). The fixtures
    tree is at ``tmp_path/data/stability/fixtures/<fixture_id>/``.
    """

    fits_root = tmp_path / "data" / "stability" / "fits"
    fixtures_root = tmp_path / "data" / "stability" / "fixtures"
    fits_root.mkdir(parents=True, exist_ok=True)

    fixture_dir = fixtures_root / triple.fixture.fixture_id
    fixture_dir.mkdir(parents=True, exist_ok=True)
    (fixture_dir / "manifest.json").write_text(
        triple.fixture.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    if stage_traces:
        (fixture_dir / "cal").mkdir(exist_ok=True)
        (fixture_dir / "cal" / "pre.csv").write_text("t,arm\n", encoding="utf-8")
        (fixture_dir / "cal" / "post.csv").write_text("t,arm\n", encoding="utf-8")
    if write_promotion:
        (fixture_dir / "promotion.json").write_text(
            triple.packet.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
    if write_fit:
        (fits_root / f"{triple.fit.fit_id}.json").write_text(
            triple.fit.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
    return fits_root


@pytest.fixture
def acceptance_triple() -> StabilityAcceptanceTriple:
    """Default in-test acceptance triple (DESIGN_SYNTHESIS §D)."""

    return make_stability_acceptance_triple()


@pytest.fixture
def stage_triple(tmp_path: Path):
    """Stage helper that takes a triple + flags and returns the fits root."""

    def _stage(
        triple: StabilityAcceptanceTriple,
        *,
        stage_traces: bool = True,
        write_promotion: bool = True,
        write_fit: bool = True,
    ) -> Path:
        return stage_acceptance_triple(
            tmp_path,
            triple,
            stage_traces=stage_traces,
            write_promotion=write_promotion,
            write_fit=write_fit,
        )

    return _stage


@pytest.fixture
def clear_stability_registry_cache():
    """Opt-in fixture to drop the registry memoization across a single test."""

    clear_registry_cache()
    yield
    clear_registry_cache()
