"""RFC 0058 stage 2 analytical-claim label resolver tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from kayakgen.eval.stability import (
    GeneratedBodyGZCurve,
    resolve_analytical_claim_label,
)
from kayakgen.eval.stability.accepted_fit import (
    FixtureRef,
    HullFamilyScope,
    ReviewerSignature,
    StabilityFitMetrics,
    StabilityFitRecord,
)

UNVALIDATED = "unvalidated_hydrostatic_comparison"
VALIDATED = "validated_hydrostatic_comparison"


@dataclass(frozen=True)
class _HullWithScope:
    hull_class: str = "sea kayak"
    hash_value: str = "design-hash-001"

    def design_hash(self) -> str:
        return self.hash_value


def _signed_at() -> datetime:
    return datetime(2026, 5, 21, 2, 0, 0, tzinfo=timezone.utc)


def _scope(**overrides) -> HullFamilyScope:
    defaults = dict(
        hull_class="sea kayak",
        design_hash_envelope=["design-hash-001"],
    )
    defaults.update(overrides)
    return HullFamilyScope(**defaults)


def _fit_record(**overrides) -> StabilityFitRecord:
    defaults = dict(
        fit_id="stability-fit-001",
        analytical_evaluator_version="rfc-0043-generated-body-v1",
        hull_family_scope=_scope(),
        valid_heel_range_deg=(0.0, 70.0),
        fixtures=[
            FixtureRef(
                fixture_id="msf-2026-001",
                fixture_path="data/stability/fixtures/msf-2026-001/manifest.json",
                fixture_sha256="a" * 64,
            )
        ],
        fit_metrics=StabilityFitMetrics(
            rmse_m=0.004,
            mape_fraction=0.04,
            max_error_m=0.009,
            coverage_fraction=0.95,
        ),
        acceptance_verdict="accepted",
        rejection_reasons=[],
        reviewer_signature=ReviewerSignature(
            reviewer_label="reviewer-1",
            reviewer_role="stability-fixture-reviewer",
            signed_at=_signed_at(),
        ),
        accepted_at=_signed_at(),
        notes=[],
        warnings=[],
    )
    defaults.update(overrides)
    return StabilityFitRecord(**defaults)


def test_empty_registry_defaults_to_unvalidated() -> None:
    assert resolve_analytical_claim_label(_HullWithScope(), ()) == UNVALIDATED


def test_hull_class_mismatch_stays_unvalidated() -> None:
    record = _fit_record(hull_family_scope=_scope(hull_class="sprint k1"))

    assert resolve_analytical_claim_label(_HullWithScope(), [record]) == UNVALIDATED


def test_design_hash_outside_envelope_stays_unvalidated() -> None:
    record = _fit_record(
        hull_family_scope=_scope(design_hash_envelope=["other-design-hash"])
    )

    assert resolve_analytical_claim_label(_HullWithScope(), [record]) == UNVALIDATED


def test_accepted_record_covering_hull_returns_validated() -> None:
    assert resolve_analytical_claim_label(_HullWithScope(), [_fit_record()]) == VALIDATED


def test_rejected_record_covering_hull_stays_unvalidated() -> None:
    record = _fit_record(
        acceptance_verdict="rejected",
        rejection_reasons=["operator rejected fit"],
        accepted_at=None,
    )

    assert resolve_analytical_claim_label(_HullWithScope(), [record]) == UNVALIDATED


def test_any_covering_accepted_record_returns_validated() -> None:
    non_covering = _fit_record(
        fit_id="stability-fit-001",
        hull_family_scope=_scope(design_hash_envelope=["other-design-hash"]),
    )
    covering = _fit_record(fit_id="stability-fit-002")

    assert (
        resolve_analytical_claim_label(_HullWithScope(), [non_covering, covering])
        == VALIDATED
    )


def test_generated_body_gz_curve_round_trips_with_both_claim_labels() -> None:
    for result_semantics in (UNVALIDATED, VALIDATED):
        curve = GeneratedBodyGZCurve(result_semantics=result_semantics)

        rebuilt = GeneratedBodyGZCurve.model_validate_json(curve.model_dump_json())

        assert rebuilt.result_semantics == result_semantics
