"""RFC 0042 resistance source-review packet tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import get_args

import pytest
from pydantic import ValidationError

from kayakgen.eval.calibration import (
    CALIBRATION_PROMOTION_REQUIRES_ACCEPTED_FIT,
    SOURCE_REVIEW_CHECKLIST_FIELDS,
    SOURCE_USE_BY_REVIEW_VERDICT,
    SourceUse,
    ResistanceSourceReviewEvidence,
    ResistanceSourceReviewPacket,
    assert_runtime_source_use,
    default_resistance_source_registry,
    default_resistance_source_review_packets,
    source_use_for_review_verdict,
    stage_label_for_review_verdict,
)
from kayakgen.eval.calibration.extractors import edinburgh_datashare_pacific_canoe


def _evidence(status: str = "accepted") -> dict[str, str]:
    return {"status": status, "summary": f"{status} evidence"}


_TEST_CHECKSUM = "a" * 64
_TEST_EXTRACTOR_REF = (
    "kayakgen/eval/calibration/extractors/test_source.py"
)


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


def _fixture_packet_payload(**updates: object) -> dict[str, object]:
    """Build a payload that satisfies the fixture-grade promotion gate."""
    payload = _packet_payload(
        review_verdict="validation_fixture",
        fixture_id="fixture-001",
        fixture_version="v1",
        non_promotion_reasons=[],
        source_checksum_sha256=_TEST_CHECKSUM,
        extraction_script_ref=_TEST_EXTRACTOR_REF,
    )
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


def test_default_review_packet_promotes_edinburgh_to_validation_fixture() -> None:
    """Per D025, Edinburgh is now a validation_fixture with the documented
    uncertainty caveat; calibration_fixture promotion remains blocked by
    the Pacific-canoe envelope reason and the missing accepted-fit ref."""
    reviews = default_resistance_source_review_packets()
    registry = {
        source.source_id: source for source in default_resistance_source_registry()
    }

    assert [review.source_id for review in reviews] == [
        "edinburgh_pacific_canoe_hydrodynamics"
    ]
    edinburgh = reviews[0]
    assert edinburgh.review_verdict == "validation_fixture"
    assert edinburgh.source_use == "validation_fixture"
    assert edinburgh.stage_label == "validation_fixture"
    assert edinburgh.fixture_id == (
        "edinburgh-pacific-canoe-hydrodynamics-2022-11-14-v15-imv"
    )
    assert edinburgh.fixture_version == "1"
    assert edinburgh.accepted_uses == ["validation_only"]
    assert edinburgh.validity_envelope is not None
    assert edinburgh.validity_envelope["models"] == ["V1", "V2", "V3"]
    assert registry[edinburgh.source_id].intended_use == "validation_fixture"
    assert registry[edinburgh.source_id].fixture_review_status == "accepted"
    # The only admitted incomplete checklist entry is uncertainty (per D025).
    incomplete = edinburgh.incomplete_evidence_fields()
    assert incomplete == ["uncertainty"]
    # The documented-caveat warning is required for D025 admission.
    assert "uncertainty_documented_caveat" in edinburgh.warnings
    # The calibration envelope reason is preserved as a calibration blocker.
    assert edinburgh.non_promotion_reasons == [
        "outside_sea_kayak_calibration_envelope"
    ]


def test_default_review_packet_round_trips_as_validation_fixture() -> None:
    packet = default_resistance_source_review_packets()[0]
    payload = packet.model_dump(mode="json")
    loaded = ResistanceSourceReviewPacket.model_validate(payload)

    assert "source_use" not in payload
    assert loaded.review_verdict == "validation_fixture"
    assert loaded.source_use == "validation_fixture"
    assert loaded.stage_label == "validation_fixture"
    assert loaded.non_promotion_reasons == [
        "outside_sea_kayak_calibration_envelope",
    ]


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
            _fixture_packet_payload(
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
            _fixture_packet_payload(
                review_verdict="calibration_fixture",
                fixture_id="calibration-fixture-001",
                fixture_version="v1",
                non_promotion_reasons=[],
                accepted_fit_ref="fits/accepted-001",
            )
        )


def test_review_evidence_rejects_empty_summary() -> None:
    with pytest.raises(ValidationError, match="at least 1 character"):
        ResistanceSourceReviewEvidence(status="accepted", summary="")


def test_rejected_is_not_runtime_source_use() -> None:
    """`rejected` is a review-only verdict; it must never appear at runtime."""
    assert "rejected" not in get_args(SourceUse)
    assert SOURCE_USE_BY_REVIEW_VERDICT["rejected"] is None
    with pytest.raises(ValueError, match="review-only verdict"):
        assert_runtime_source_use("rejected")
    for runtime_value in get_args(SourceUse):
        assert assert_runtime_source_use(runtime_value) == runtime_value
    with pytest.raises(ValueError, match="not a recognized runtime SourceUse"):
        assert_runtime_source_use("not_a_real_value")


def test_edinburgh_review_packet_binds_provenance_fields() -> None:
    """Edinburgh's review packet must bind locators, license, attribution, ..."""
    edinburgh = default_resistance_source_review_packets()[0]
    assert edinburgh.source_id == "edinburgh_pacific_canoe_hydrodynamics"
    assert edinburgh.primary_locator == "https://datashare.ed.ac.uk/handle/10283/4772"
    assert edinburgh.secondary_locator == "https://doi.org/10.7488/ds/3785"
    assert edinburgh.access_date == "2026-05-15"
    assert edinburgh.source_checksum_sha256 == (
        "dffbd5d4547c9e1c1f5597d6188dc2a1efffd316ab301451fb818e11a22acade"
    )
    assert edinburgh.source_checksum_pending_reason is None
    assert edinburgh.license_identifier == "CC BY 4.0"
    assert "DOI 10.7488/ds/3785" in (edinburgh.attribution or "")
    assert edinburgh.extraction_script_ref == (
        "kayakgen/eval/calibration/extractors/"
        "edinburgh_datashare_pacific_canoe.py"
    )
    assert edinburgh.measurement_units == {
        "speed": "m/s",
        "drag": "N",
        "length_waterline": "m",
        "trim_pitch": "deg",
        "heave": "mm",
        "yaw": "deg",
    }
    assert edinburgh.froude_basis == "Fn = U / sqrt(g * Lwl)"
    assert edinburgh.uncertainty_notes is not None
    assert edinburgh.accepted_fit_ref is None


def test_edinburgh_packet_is_validation_fixture_after_promotion() -> None:
    """After the 2026-05-16 D025 promotion, Edinburgh is a
    validation_fixture; calibration promotion remains blocked by the
    Pacific-canoe envelope reason and the missing accepted-fit ref."""
    edinburgh = default_resistance_source_review_packets()[0]
    assert edinburgh.review_verdict == "validation_fixture"
    assert edinburgh.source_use == "validation_fixture"
    assert edinburgh.is_validation_fixture_ready() is True
    assert edinburgh.non_promotion_reasons == [
        "outside_sea_kayak_calibration_envelope"
    ]
    blockers = edinburgh.calibration_promotion_blockers()
    assert "pending_data_acquisition" not in blockers
    assert CALIBRATION_PROMOTION_REQUIRES_ACCEPTED_FIT in blockers


def test_validation_fixture_admits_documented_uncertainty_caveat() -> None:
    """Per D025, validation_fixture may carry uncertainty.status='incomplete'
    if uncertainty_notes is bound AND the warnings list contains
    'uncertainty_documented_caveat'. Removing the warning re-engages the
    'requires complete source-review evidence' refusal."""
    from kayakgen.eval.calibration import (
        VALIDATION_FIXTURE_ADMITS_DOCUMENTED_UNCERTAINTY_CAVEAT,
    )

    packet = default_resistance_source_review_packets()[0]
    assert "uncertainty_documented_caveat" in packet.warnings
    # Sanity: the documented token exists as a referenceable constant.
    assert VALIDATION_FIXTURE_ADMITS_DOCUMENTED_UNCERTAINTY_CAVEAT == (
        "validation_fixture_admits_documented_uncertainty_caveat"
    )

    # Reconstruct without the documented-caveat warning: the validator must
    # refuse, citing the token.
    payload = packet.model_dump(mode="json")
    payload["warnings"] = [w for w in payload["warnings"] if w != "uncertainty_documented_caveat"]
    with pytest.raises(
        ValidationError,
        match="validation_fixture_admits_documented_uncertainty_caveat",
    ):
        ResistanceSourceReviewPacket.model_validate(payload)


def test_validation_fixture_admits_calibration_blockers_in_non_promotion_reasons() -> None:
    """Per D025, validation_fixture may carry non_promotion_reasons that
    describe calibration-fixture blockers (e.g.
    outside_sea_kayak_calibration_envelope). calibration_fixture itself
    still cannot carry non_promotion_reasons because there is no further
    promotion."""
    edinburgh = default_resistance_source_review_packets()[0]
    assert edinburgh.review_verdict == "validation_fixture"
    assert edinburgh.non_promotion_reasons == [
        "outside_sea_kayak_calibration_envelope"
    ]


def test_validation_fixture_requires_checksum_and_extractor() -> None:
    """A fixture verdict cannot land without checksum AND extractor bound."""
    with pytest.raises(
        ValidationError,
        match="requires source_checksum_sha256 and extraction_script_ref",
    ):
        ResistanceSourceReviewPacket.model_validate(
            _fixture_packet_payload(
                source_checksum_sha256=None,
                extraction_script_ref=None,
            )
        )
    with pytest.raises(
        ValidationError,
        match="requires source_checksum_sha256 and extraction_script_ref",
    ):
        ResistanceSourceReviewPacket.model_validate(
            _fixture_packet_payload(source_checksum_sha256=None)
        )
    with pytest.raises(
        ValidationError,
        match="requires source_checksum_sha256 and extraction_script_ref",
    ):
        ResistanceSourceReviewPacket.model_validate(
            _fixture_packet_payload(extraction_script_ref=None)
        )


def test_validation_fixture_promotes_when_checksum_and_extractor_bound() -> None:
    packet = ResistanceSourceReviewPacket.model_validate(_fixture_packet_payload())
    assert packet.review_verdict == "validation_fixture"
    assert packet.source_use == "validation_fixture"
    assert packet.stage_label == "validation_fixture"
    assert packet.is_validation_fixture_ready() is True


def test_checksum_sha256_must_be_lowercase_hex_when_bound() -> None:
    with pytest.raises(ValidationError, match="64-character lowercase hex"):
        ResistanceSourceReviewPacket.model_validate(
            _fixture_packet_payload(source_checksum_sha256="ZZZ")
        )
    with pytest.raises(
        ValidationError,
        match="pending_reason must be null when source_checksum_sha256 is bound",
    ):
        ResistanceSourceReviewPacket.model_validate(
            _fixture_packet_payload(
                source_checksum_pending_reason="should_not_be_set",
            )
        )


def test_calibration_promotion_blocked_without_accepted_fit() -> None:
    """A review packet alone cannot promote to calibration_fixture."""
    with pytest.raises(
        ValidationError,
        match=CALIBRATION_PROMOTION_REQUIRES_ACCEPTED_FIT,
    ):
        ResistanceSourceReviewPacket.model_validate(
            _fixture_packet_payload(
                review_verdict="calibration_fixture",
                fixture_id="calibration-fixture-001",
                fixture_version="v1",
                non_promotion_reasons=[],
                validity_envelope={"speed_ms": [0.4, 1.6]},
                accepted_fit_ref=None,
            )
        )


def test_calibration_promotion_allowed_with_accepted_fit() -> None:
    packet = ResistanceSourceReviewPacket.model_validate(
        _fixture_packet_payload(
            review_verdict="calibration_fixture",
            fixture_id="calibration-fixture-001",
            fixture_version="v1",
            non_promotion_reasons=[],
            validity_envelope={"speed_ms": [0.4, 1.6]},
            accepted_fit_ref="fits/accepted-001",
        )
    )
    assert packet.review_verdict == "calibration_fixture"
    assert packet.calibration_promotion_blockers() == []


EDINBURGH_FIXTURE_WORKBOOK = (
    Path(__file__).parent
    / "fixtures"
    / "calibration"
    / "edinburgh"
    / "FixedSink_and_TrimDataAnalysis20221114V15_IMV.xlsx"
)


def test_edinburgh_extractor_module_pins_output_schema() -> None:
    module = edinburgh_datashare_pacific_canoe
    assert module.EXTRACTOR_SOURCE_ID == "edinburgh_pacific_canoe_hydrodynamics"
    assert module.EXPECTED_OUTPUT_COLUMNS == (
        "source_id",
        "day",
        "model",
        "run_id",
        "yaw_deg",
        "speed_ms",
        "stbd_drag_n",
        "port_drag_n",
        "total_drag_n",
        "fwd_side_force_n",
        "aft_side_force_n",
        "heave_mm",
        "pitch_deg",
        "velocity_ms",
        "Lwl_m",
        "Fn",
        "time",
        "comment",
    )
    assert module.EXPECTED_SOURCE_COLUMNS == (
        "Day",
        "Model",
        "Test",
        "Yaw",
        "Speed",
        "Stbd Drag Force",
        "Port Drag Force",
        "FWD Side Force",
        "AFT Side Force",
        "Heave",
        "Pitch",
        "Velocity",
        "Time",
        "Comment",
    )
    assert module.WORKBOOK_SHEET == "Averaged Data"
    assert module.MODEL_LWL_M == {"V1": 1.2, "V2": 1.2, "V3": 1.2}
    assert module.FROUDE_BASIS == "Fn = U / sqrt(g * Lwl)"
    assert module.GRAVITY_M_S2 == pytest.approx(9.80665)
    docstring = module.__doc__ or ""
    # Pin the docstring schema so future edits cannot silently change it.
    for token in (
        "stbd_drag_n",
        "port_drag_n",
        "total_drag_n",
        "Lwl_m",
        "Fn = U / sqrt(g * Lwl)",
        "10.7488/ds/3785",
    ):
        assert token in docstring, f"missing {token!r} in extractor docstring"


def test_edinburgh_extractor_raises_when_workbook_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        edinburgh_datashare_pacific_canoe.extract(tmp_path / "nope.xlsx")


@pytest.mark.skipif(
    not EDINBURGH_FIXTURE_WORKBOOK.is_file(),
    reason="Edinburgh workbook fixture not vendored",
)
def test_edinburgh_extractor_emits_expected_columns_for_vendored_workbook() -> None:
    pytest.importorskip("openpyxl", reason="extractor needs openpyxl")
    rows = edinburgh_datashare_pacific_canoe.extract(EDINBURGH_FIXTURE_WORKBOOK)
    assert rows, "extractor should yield at least one accepted row"
    assert (
        set(rows[0].keys())
        == set(edinburgh_datashare_pacific_canoe.EXPECTED_OUTPUT_COLUMNS)
    )
    assert all(row["source_id"] == "edinburgh_pacific_canoe_hydrodynamics" for row in rows)
    assert all(row["run_id"] >= 1 for row in rows)
    assert all(row["model"] in {"V1", "V2", "V3"} for row in rows)
    assert all(row["Lwl_m"] == 1.2 for row in rows)
    # Filtered rows: setup/zero/negative tests are excluded, so the run-id
    # set has no <=0 entries and the dataset's documented model id set is
    # exactly V1/V2/V3.
    assert {row["model"] for row in rows} == {"V1", "V2", "V3"}


@pytest.mark.skipif(
    not EDINBURGH_FIXTURE_WORKBOOK.is_file(),
    reason="Edinburgh workbook fixture not vendored",
)
def test_edinburgh_extractor_total_drag_equals_stbd_plus_port() -> None:
    pytest.importorskip("openpyxl", reason="extractor needs openpyxl")
    rows = edinburgh_datashare_pacific_canoe.extract(EDINBURGH_FIXTURE_WORKBOOK)
    for row in rows:
        assert row["total_drag_n"] == pytest.approx(
            row["stbd_drag_n"] + row["port_drag_n"]
        )


@pytest.mark.skipif(
    not EDINBURGH_FIXTURE_WORKBOOK.is_file(),
    reason="Edinburgh workbook fixture not vendored",
)
def test_edinburgh_extractor_fn_matches_velocity_sqrt_g_lwl() -> None:
    import math

    pytest.importorskip("openpyxl", reason="extractor needs openpyxl")
    rows = edinburgh_datashare_pacific_canoe.extract(EDINBURGH_FIXTURE_WORKBOOK)
    g = edinburgh_datashare_pacific_canoe.GRAVITY_M_S2
    for row in rows:
        if row["velocity_ms"] > 0:
            expected = row["velocity_ms"] / math.sqrt(g * row["Lwl_m"])
            assert row["Fn"] == pytest.approx(expected)
        else:
            assert row["Fn"] == 0.0


@pytest.mark.skipif(
    not EDINBURGH_FIXTURE_WORKBOOK.is_file(),
    reason="Edinburgh workbook fixture not vendored",
)
def test_edinburgh_workbook_sha256_matches_packet_record() -> None:
    import hashlib

    edinburgh = default_resistance_source_review_packets()[0]
    digest = hashlib.sha256(EDINBURGH_FIXTURE_WORKBOOK.read_bytes()).hexdigest()
    assert digest == edinburgh.source_checksum_sha256


def test_edinburgh_packet_matches_pinned_fixture_json() -> None:
    fixture_path = (
        Path(__file__).parent / "fixtures" / "calibration" / "edinburgh_review_packet.json"
    )
    payload = json.loads(fixture_path.read_text())
    loaded = ResistanceSourceReviewPacket.model_validate(payload)
    edinburgh = default_resistance_source_review_packets()[0]
    assert loaded.model_dump(mode="json") == edinburgh.model_dump(mode="json")
