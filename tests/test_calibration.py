"""RFC 0042 resistance source-review packet tests."""

from __future__ import annotations

from typing import get_args

import pytest
from pydantic import ValidationError

from kayakgen.eval.calibration import (
    SOURCE_REVIEW_CHECKLIST_FIELDS,
    SOURCE_USE_BY_REVIEW_VERDICT,
    SourceUse,
    ResistanceSourceReviewEvidence,
    ResistanceSourceReviewPacket,
    default_resistance_source_registry,
    default_resistance_source_review_packets,
    source_use_for_review_verdict,
    stage_label_for_review_verdict,
)


def _evidence(status: str = "accepted") -> dict[str, str]:
    return {"status": status, "summary": f"{status} evidence"}


def _packet_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_id": "test_source",
        "title": "Test source",
        "citation": "Test citation",
        "locator": "https://example.invalid/test-source",
        "source_type": "tow_tank_measurement",
        "measured_data": True,
        "hull_class": "sea_kayak",
        "rights": _evidence(),
        "extraction": _evidence(),
        "measured_quantity": _evidence(),
        "units": _evidence(),
        "hull_envelope": _evidence(),
        "speed_froude_range": _evidence(),
        "uncertainty": _evidence(),
        "reviewer": "pytest",
        "review_date": "2026-05-14",
        "review_verdict": "validation_candidate",
        "reasons": ["candidate source"],
        "non_promotion_reasons": ["not promoted by test review"],
        "warnings": [],
    }
    payload.update(updates)
    return payload


def test_runtime_source_use_values_remain_rfc_0027_vocabulary() -> None:
    assert set(get_args(SourceUse)) == {
        "citation_only",
        "validation_candidate",
        "validation_fixture",
        "calibration_fixture_candidate",
        "calibration_fixture",
    }
    assert "rejected" not in get_args(SourceUse)
    assert SOURCE_USE_BY_REVIEW_VERDICT["rejected"] is None


@pytest.mark.parametrize(
    ("review_verdict", "stage_label", "source_use"),
    [
        ("citation_only", "candidate_source", "citation_only"),
        ("validation_candidate", "candidate_source", "validation_candidate"),
        (
            "calibration_fixture_candidate",
            "candidate_source",
            "calibration_fixture_candidate",
        ),
        ("validation_fixture", "validation_fixture", "validation_fixture"),
        ("calibration_fixture", "calibration_fixture", "calibration_fixture"),
        ("rejected", "rejected_review", None),
    ],
)
def test_review_verdicts_map_to_source_use_without_runtime_rejected_state(
    review_verdict: str,
    stage_label: str,
    source_use: str | None,
) -> None:
    assert source_use_for_review_verdict(review_verdict) == source_use
    assert stage_label_for_review_verdict(review_verdict) == stage_label


def test_source_review_checklist_covers_rfc_0042_promotion_fields() -> None:
    assert SOURCE_REVIEW_CHECKLIST_FIELDS == (
        "rights",
        "extraction",
        "measured_quantity",
        "units",
        "hull_envelope",
        "speed_froude_range",
        "uncertainty",
    )

    packet = ResistanceSourceReviewPacket.model_validate(_packet_payload())

    assert set(packet.checklist()) == set(SOURCE_REVIEW_CHECKLIST_FIELDS)
    assert packet.incomplete_evidence_fields() == []


def test_default_review_packet_applies_to_edinburgh_without_fixture_promotion() -> None:
    reviews = default_resistance_source_review_packets()
    registry = {
        source.source_id: source for source in default_resistance_source_registry()
    }

    assert [review.source_id for review in reviews] == [
        "edinburgh_pacific_canoe_hydrodynamics"
    ]
    edinburgh = reviews[0]
    assert edinburgh.review_verdict == "validation_candidate"
    assert edinburgh.source_use == "validation_candidate"
    assert edinburgh.stage_label == "candidate_source"
    assert edinburgh.fixture_id is None
    assert edinburgh.fixture_version is None
    assert edinburgh.validity_envelope is None
    assert edinburgh.accepted_uses == []
    assert registry[edinburgh.source_id].intended_use == "validation_candidate"
    assert registry[edinburgh.source_id].intended_use not in {
        "validation_fixture",
        "calibration_fixture",
    }
    assert "extraction" in edinburgh.incomplete_evidence_fields()
    assert "units" in edinburgh.incomplete_evidence_fields()
    assert "uncertainty" in edinburgh.incomplete_evidence_fields()
    assert "extraction_schema_missing" in edinburgh.non_promotion_reasons
    assert "outside_sea_kayak_calibration_envelope" in edinburgh.non_promotion_reasons


def test_candidate_review_requires_non_promotion_reasons() -> None:
    with pytest.raises(ValidationError, match="candidate source reviews require"):
        ResistanceSourceReviewPacket.model_validate(
            _packet_payload(non_promotion_reasons=[])
        )


def test_rejected_review_serializes_only_as_review_outcome() -> None:
    packet = ResistanceSourceReviewPacket.model_validate(
        _packet_payload(
            review_verdict="rejected",
            rights=_evidence("missing"),
            extraction=_evidence("missing"),
            measured_quantity=_evidence("missing"),
            units=_evidence("missing"),
            hull_envelope=_evidence("missing"),
            speed_froude_range=_evidence("missing"),
            uncertainty=_evidence("missing"),
            non_promotion_reasons=["rights_unknown", "model_derived_values"],
        )
    )
    payload = packet.model_dump(mode="json")

    assert packet.source_use is None
    assert packet.stage_label == "rejected_review"
    assert payload["review_verdict"] == "rejected"
    assert "intended_use" not in payload
    assert payload["non_promotion_reasons"] == [
        "rights_unknown",
        "model_derived_values",
    ]


def test_rejected_review_cannot_declare_fixture_metadata() -> None:
    with pytest.raises(ValidationError, match="rejected source reviews cannot declare"):
        ResistanceSourceReviewPacket.model_validate(
            _packet_payload(
                review_verdict="rejected",
                fixture_id="fixture-001",
                fixture_version="v1",
                non_promotion_reasons=["rights_unknown"],
            )
        )


def test_fixture_verdict_requires_complete_checklist_evidence() -> None:
    with pytest.raises(ValidationError, match="requires complete source-review evidence"):
        ResistanceSourceReviewPacket.model_validate(
            _packet_payload(
                review_verdict="validation_fixture",
                extraction=_evidence("incomplete"),
                fixture_id="validation-fixture-001",
                fixture_version="v1",
                non_promotion_reasons=[],
            )
        )


def test_calibration_fixture_requires_validity_envelope() -> None:
    with pytest.raises(ValidationError, match="calibration_fixture requires a validity envelope"):
        ResistanceSourceReviewPacket.model_validate(
            _packet_payload(
                review_verdict="calibration_fixture",
                fixture_id="calibration-fixture-001",
                fixture_version="v1",
                non_promotion_reasons=[],
            )
        )


def test_review_evidence_rejects_empty_summary() -> None:
    with pytest.raises(ValidationError, match="at least 1 character"):
        ResistanceSourceReviewEvidence(status="accepted", summary="")
