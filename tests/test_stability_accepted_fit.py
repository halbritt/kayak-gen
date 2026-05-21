"""RFC 0058 stage 1: accepted stability-fit schema tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from kayakgen.eval.stability.accepted_fit import (
    FixtureRef,
    HullFamilyScope,
    ReviewerSignature,
    StabilityFitMetrics,
    StabilityFitRecord,
    StabilityFixturePromotionPacket,
)


def _signed_at() -> datetime:
    return datetime(2026, 5, 21, 2, 0, 0, tzinfo=timezone.utc)


def _fixture_ref(**overrides) -> FixtureRef:
    defaults = dict(
        fixture_id="msf-2026-001",
        fixture_path="data/stability/fixtures/msf-2026-001/manifest.json",
        fixture_sha256="a" * 64,
    )
    defaults.update(overrides)
    return FixtureRef(**defaults)


def _scope(**overrides) -> HullFamilyScope:
    defaults = dict(
        hull_class="sea kayak",
        design_hash_envelope=["design-hash-001"],
    )
    defaults.update(overrides)
    return HullFamilyScope(**defaults)


def _metrics(**overrides) -> StabilityFitMetrics:
    defaults = dict(
        rmse_m=0.004,
        mape_fraction=0.04,
        max_error_m=0.009,
        coverage_fraction=0.95,
    )
    defaults.update(overrides)
    return StabilityFitMetrics(**defaults)


def _reviewer(**overrides) -> ReviewerSignature:
    defaults = dict(
        reviewer_label="reviewer-1",
        reviewer_role="stability-fixture-reviewer",
        signed_at=_signed_at(),
    )
    defaults.update(overrides)
    return ReviewerSignature(**defaults)


def _fit_record(**overrides) -> StabilityFitRecord:
    defaults = dict(
        fit_id="stability-fit-001",
        analytical_evaluator_version="rfc-0043-generated-body-v1",
        hull_family_scope=_scope(),
        valid_heel_range_deg=(0.0, 70.0),
        fixtures=[_fixture_ref()],
        fit_metrics=_metrics(),
        acceptance_verdict="rejected",
        rejection_reasons=["operator has not promoted a real fit in stage 1"],
        reviewer_signature=_reviewer(),
        accepted_at=None,
        notes=["schema-only test record"],
        warnings=[],
    )
    defaults.update(overrides)
    return StabilityFitRecord(**defaults)


def _promotion_packet(**overrides) -> StabilityFixturePromotionPacket:
    defaults = dict(
        fixture_ref=_fixture_ref(),
        rights_review="accepted",
        hull_identity_review="accepted",
        calibration_drift_review="accepted",
        hysteresis_review="accepted",
        free_equilibrium_review="accepted",
        rig_design_match=True,
        promotion_target="validation_candidate",
        rejection_reasons=["no promotion in RFC 0058 stage 1"],
        reviewer_signature=_reviewer(),
    )
    defaults.update(overrides)
    return StabilityFixturePromotionPacket(**defaults)


def test_stability_fit_record_round_trips_canonical_json() -> None:
    record = _fit_record()

    blob = record.model_dump_json()
    rebuilt = StabilityFitRecord.model_validate_json(blob)

    assert rebuilt == record
    assert rebuilt.schema_version == "1"
    assert rebuilt.hull_family_scope.schema_version == "1"
    assert rebuilt.fit_metrics.schema_version == "1"
    assert rebuilt.reviewer_signature.schema_version == "1"


def test_stability_fit_record_strict_thresholds_refuse_bad_metrics() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _fit_record(fit_metrics=_metrics(rmse_m=0.006))

    assert "stability_fit_metrics_outside_default_thresholds" in str(exc_info.value)
    assert "rmse_m" in str(exc_info.value)


def test_stability_fit_record_strict_false_skips_thresholds_and_records_warning() -> None:
    record = _fit_record(
        fit_metrics=_metrics(
            rmse_m=0.006,
            mape_fraction=0.06,
            max_error_m=0.02,
            coverage_fraction=0.5,
        ),
        strict=False,
    )

    assert "strict_check_skipped" in record.warnings


def test_accepted_fit_requires_accepted_at_and_no_rejection_reasons() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _fit_record(
            acceptance_verdict="accepted",
            rejection_reasons=[],
            accepted_at=None,
        )
    assert "accepted_at" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        _fit_record(
            acceptance_verdict="accepted",
            rejection_reasons=["still blocked"],
            accepted_at=_signed_at(),
        )
    assert "rejection_reasons=[]" in str(exc_info.value)


def test_promotion_packet_refuses_non_accepted_review_verdict() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _promotion_packet(
            promotion_target="measured_stability_fixture",
            hull_identity_review="deferred",
            rejection_reasons=[],
        )

    assert "requires every review verdict to be 'accepted'" in str(exc_info.value)


def test_promotion_packet_refuses_non_matching_rig_design() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _promotion_packet(
            promotion_target="measured_stability_fixture",
            rig_design_match=False,
            rejection_reasons=[],
        )

    assert "rig_design_match=True" in str(exc_info.value)


def test_promotion_packet_refuses_rejection_reasons_for_promotion() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _promotion_packet(
            promotion_target="measured_stability_fixture",
            rejection_reasons=["reviewer kept blocker"],
        )

    assert "rejection_reasons=[]" in str(exc_info.value)


def test_fixture_ref_sha256_must_be_64_lowercase_hex() -> None:
    FixtureRef(
        fixture_id="ok",
        fixture_path="fixtures/ok.json",
        fixture_sha256="0123456789abcdef" * 4,
    )

    for bad_hash in (
        "a" * 63,
        "A" * 64,
        "g" * 64,
    ):
        with pytest.raises(ValidationError):
            _fixture_ref(fixture_sha256=bad_hash)


def test_hull_family_scope_requires_design_hash_envelope() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _scope(design_hash_envelope=[])

    assert "design_hash_envelope must contain at least one design hash" in str(
        exc_info.value
    )
