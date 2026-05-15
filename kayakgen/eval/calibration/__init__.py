"""Resistance calibration source registry.

These records describe candidate sources. They do not imply that current
resistance output is calibrated.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
#: Calibration promotion must arrive via a separate accepted-fit workflow.
#: A review packet alone (no accepted-fit gate) cannot legitimately claim
#: ``calibration_fixture`` — the gate is preserved here so callers can refer
#: to a single named token from tests.
CALIBRATION_PROMOTION_REQUIRES_ACCEPTED_FIT: str = "calibration_promotion_requires_accepted_fit"

SourceUse = Literal[
    "citation_only",
    "validation_candidate",
    "validation_fixture",
    "calibration_fixture_candidate",
    "calibration_fixture",
]
SourceReviewVerdict = Literal[
    "citation_only",
    "validation_candidate",
    "validation_fixture",
    "calibration_fixture_candidate",
    "calibration_fixture",
    "rejected",
]
SourceReviewStageLabel = Literal[
    "candidate_source",
    "validation_fixture",
    "calibration_fixture",
    "rejected_review",
]
SourceReviewEvidenceStatus = Literal["accepted", "incomplete", "missing", "not_applicable"]

SOURCE_REVIEW_CHECKLIST_FIELDS = (
    "rights",
    "extraction",
    "measured_quantity",
    "units",
    "hull_envelope",
    "speed_froude_range",
    "uncertainty",
)
SOURCE_USE_BY_REVIEW_VERDICT: dict[SourceReviewVerdict, SourceUse | None] = {
    "citation_only": "citation_only",
    "validation_candidate": "validation_candidate",
    "validation_fixture": "validation_fixture",
    "calibration_fixture_candidate": "calibration_fixture_candidate",
    "calibration_fixture": "calibration_fixture",
    "rejected": None,
}
STAGE_LABEL_BY_REVIEW_VERDICT: dict[SourceReviewVerdict, SourceReviewStageLabel] = {
    "citation_only": "candidate_source",
    "validation_candidate": "candidate_source",
    "calibration_fixture_candidate": "candidate_source",
    "validation_fixture": "validation_fixture",
    "calibration_fixture": "calibration_fixture",
    "rejected": "rejected_review",
}


def source_use_for_review_verdict(verdict: SourceReviewVerdict) -> SourceUse | None:
    """Map an RFC 0042 review verdict onto the existing runtime source-use value.

    ``rejected`` is intentionally review-only and therefore maps to ``None``.
    """
    return SOURCE_USE_BY_REVIEW_VERDICT[verdict]


def stage_label_for_review_verdict(verdict: SourceReviewVerdict) -> SourceReviewStageLabel:
    """Return the RFC 0027 grouping for a source-review verdict."""
    return STAGE_LABEL_BY_REVIEW_VERDICT[verdict]


def assert_runtime_source_use(value: str) -> SourceUse:
    """Validate that ``value`` is a runtime ``SourceUse`` token.

    ``rejected`` is an RFC 0042 review verdict only — it cannot appear as a
    runtime ``SourceUse`` because rejected sources are dropped from the
    registry instead of being given a runtime role. This helper exists so
    callers (and tests) can refuse ``rejected`` at the boundary without
    importing the literal definition.
    """
    if value == "rejected":
        raise ValueError(
            "'rejected' is a review-only verdict and cannot be used as a "
            "runtime SourceUse value"
        )
    allowed = set(SourceUse.__args__)  # type: ignore[attr-defined]
    if value not in allowed:
        raise ValueError(f"{value!r} is not a recognized runtime SourceUse value")
    return value  # type: ignore[return-value]


def _metadata_value_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (dict, list, tuple, set)):
        return len(value) == 0
    return False


def _missing_metadata_fields(values: dict[str, Any]) -> list[str]:
    return sorted(name for name, value in values.items() if _metadata_value_missing(value))


class ResistanceSourceRecord(BaseModel):
    """Citation/provenance record for a candidate resistance source."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str
    url: str
    source_type: str
    intended_use: SourceUse
    measured_data: bool
    hull_class: str
    rights_status: str
    extraction_status: str
    notes: str
    warnings: list[str] = Field(default_factory=list)
    fixture_id: str | None = None
    measured_quantity: str | None = None
    measurement_units: str | None = None
    hull_envelope: dict[str, Any] | None = None
    uncertainty_notes: str | None = None
    validity_ranges: dict[str, Any] | None = None
    fixture_review_status: Literal["accepted", "candidate", "not_reviewed"] | None = None

    @model_validator(mode="after")
    def _fixture_records_require_metadata(self) -> "ResistanceSourceRecord":
        if self.intended_use == "calibration_fixture":
            self._validate_calibration_fixture_metadata()
        elif self.intended_use == "validation_fixture":
            self._validate_validation_fixture_metadata()
        return self

    def _validate_calibration_fixture_metadata(self) -> None:
        required_values = {
            "fixture_id": self.fixture_id,
            "measured_quantity": self.measured_quantity,
            "measurement_units": self.measurement_units,
            "hull_envelope": self.hull_envelope,
            "uncertainty_notes": self.uncertainty_notes,
            "validity_ranges": self.validity_ranges,
            "fixture_review_status": self.fixture_review_status,
            "rights_status": self.rights_status,
            "extraction_status": self.extraction_status,
        }
        missing = _missing_metadata_fields(required_values)
        if self.measured_data is not True:
            missing.append("measured_data=True")
        if self.fixture_review_status != "accepted":
            missing.append("fixture_review_status=accepted")
        if missing:
            raise ValueError(
                "calibration_fixture requires fixture review metadata: "
                + ", ".join(dict.fromkeys(missing))
            )

    def _validate_validation_fixture_metadata(self) -> None:
        required_values = {
            "fixture_id": self.fixture_id,
            "measured_quantity": self.measured_quantity,
            "measurement_units": self.measurement_units,
            "rights_status": self.rights_status,
            "extraction_status": self.extraction_status,
        }
        missing = _missing_metadata_fields(required_values)
        if missing:
            raise ValueError(
                "validation_fixture requires reproducible fixture metadata: "
                + ", ".join(missing)
            )


class ResistanceSourceReviewEvidence(BaseModel):
    """One checklist item in an RFC 0042 source-review packet."""

    model_config = ConfigDict(extra="forbid")

    status: SourceReviewEvidenceStatus
    summary: str = Field(min_length=1)
    refs: list[str] = Field(default_factory=list)


class ResistanceSourceReviewPacket(BaseModel):
    """Review packet for deciding whether a candidate source may be promoted."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str
    citation: str
    locator: str
    source_type: str
    measured_data: bool
    hull_class: str
    rights: ResistanceSourceReviewEvidence
    extraction: ResistanceSourceReviewEvidence
    measured_quantity: ResistanceSourceReviewEvidence
    units: ResistanceSourceReviewEvidence
    hull_envelope: ResistanceSourceReviewEvidence
    speed_froude_range: ResistanceSourceReviewEvidence
    uncertainty: ResistanceSourceReviewEvidence
    reviewer: str
    review_date: str
    review_verdict: SourceReviewVerdict
    reasons: list[str] = Field(default_factory=list)
    non_promotion_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    fixture_id: str | None = None
    fixture_version: str | None = None
    accepted_uses: list[str] = Field(default_factory=list)
    validity_envelope: dict[str, Any] | None = None
    primary_locator: str | None = None
    secondary_locator: str | None = None
    access_date: str | None = None
    source_checksum_sha256: str | None = None
    source_checksum_pending_reason: str | None = None
    license_identifier: str | None = None
    attribution: str | None = None
    extraction_script_ref: str | None = None
    measurement_units: dict[str, str] | None = None
    froude_basis: str | None = None
    uncertainty_notes: str | None = None
    accepted_fit_ref: str | None = None

    @property
    def source_use(self) -> SourceUse | None:
        """Runtime source-use mapping, or ``None`` for rejected review outcomes."""
        return source_use_for_review_verdict(self.review_verdict)

    @property
    def stage_label(self) -> SourceReviewStageLabel:
        """RFC 0027 stage grouping derived from the review verdict."""
        return stage_label_for_review_verdict(self.review_verdict)

    def checklist(self) -> dict[str, ResistanceSourceReviewEvidence]:
        """Return the evidence checklist fields that gate fixture promotion."""
        return {name: getattr(self, name) for name in SOURCE_REVIEW_CHECKLIST_FIELDS}

    def incomplete_evidence_fields(self) -> list[str]:
        """Checklist fields that are not accepted for fixture promotion."""
        return [
            name
            for name, evidence in self.checklist().items()
            if evidence.status != "accepted"
        ]

    def is_validation_fixture_ready(self) -> bool:
        """Return True when both checksum and extractor are bound.

        Edinburgh-style sources may only be promoted from
        ``validation_candidate`` to ``validation_fixture`` once the source
        file checksum and an extraction-script reference are both bound.
        Calibration promotion requires an additional accepted-fit gate that
        is intentionally not satisfiable from a review packet alone.
        """
        return bool(self.source_checksum_sha256) and bool(self.extraction_script_ref)

    def calibration_promotion_blockers(self) -> list[str]:
        """Return reasons (if any) why calibration promotion is blocked.

        A review packet alone cannot promote a source to
        ``calibration_fixture``; promotion requires a separately-recorded
        accepted-fit reference. This method returns an empty list only when
        the full set of gates is satisfied.
        """
        blockers: list[str] = []
        if not self.is_validation_fixture_ready():
            blockers.append("pending_data_acquisition")
        if not self.accepted_fit_ref:
            blockers.append(CALIBRATION_PROMOTION_REQUIRES_ACCEPTED_FIT)
        if self.incomplete_evidence_fields():
            blockers.append("incomplete_source_review_evidence")
        return blockers

    @model_validator(mode="after")
    def _review_verdict_controls_promotion_metadata(
        self,
    ) -> "ResistanceSourceReviewPacket":
        self._validate_checksum_binding()
        if self.review_verdict == "rejected":
            if self.fixture_id or self.fixture_version or self.accepted_uses:
                raise ValueError("rejected source reviews cannot declare fixture metadata")
            if self.validity_envelope is not None:
                raise ValueError("rejected source reviews cannot declare validity envelopes")
            if not self.non_promotion_reasons:
                raise ValueError("rejected source reviews require non-promotion reasons")
            if self.accepted_fit_ref is not None:
                raise ValueError("rejected source reviews cannot declare accepted_fit_ref")
            return self

        if self.stage_label == "candidate_source":
            if self.fixture_id or self.fixture_version or self.accepted_uses:
                raise ValueError("candidate source reviews cannot declare fixture metadata")
            if self.validity_envelope is not None:
                raise ValueError("candidate source reviews cannot declare validity envelopes")
            if not self.non_promotion_reasons:
                raise ValueError("candidate source reviews require non-promotion reasons")
            if self.accepted_fit_ref is not None:
                raise ValueError("candidate source reviews cannot declare accepted_fit_ref")
            return self

        incomplete = self.incomplete_evidence_fields()
        if incomplete:
            raise ValueError(
                f"{self.review_verdict} requires complete source-review evidence: "
                + ", ".join(incomplete)
            )
        if not self.measured_data:
            raise ValueError(f"{self.review_verdict} requires measured source data")
        if not self.fixture_id or not self.fixture_version:
            raise ValueError(f"{self.review_verdict} requires fixture ID and version")
        if self.non_promotion_reasons:
            raise ValueError(f"{self.review_verdict} cannot carry non-promotion reasons")
        if not self.source_checksum_sha256 or not self.extraction_script_ref:
            raise ValueError(
                f"{self.review_verdict} requires source_checksum_sha256 and "
                "extraction_script_ref to be bound"
            )
        if self.review_verdict == "calibration_fixture":
            if self.validity_envelope is None:
                raise ValueError("calibration_fixture requires a validity envelope")
            if not self.accepted_fit_ref:
                raise ValueError(
                    "calibration_fixture requires an accepted_fit_ref "
                    f"({CALIBRATION_PROMOTION_REQUIRES_ACCEPTED_FIT})"
                )
        return self

    def _validate_checksum_binding(self) -> None:
        if self.source_checksum_sha256 is not None:
            if not _SHA256_HEX_RE.match(self.source_checksum_sha256):
                raise ValueError(
                    "source_checksum_sha256 must be a 64-character lowercase hex string"
                )
            if self.source_checksum_pending_reason is not None:
                raise ValueError(
                    "source_checksum_pending_reason must be null when "
                    "source_checksum_sha256 is bound"
                )
        else:
            if (
                self.source_checksum_pending_reason is not None
                and not self.source_checksum_pending_reason.strip()
            ):
                raise ValueError(
                    "source_checksum_pending_reason cannot be an empty string"
                )


def default_resistance_source_registry() -> tuple[ResistanceSourceRecord, ...]:
    """Return candidate sources reviewed by workflows 0012 and 0023.

    None of these records is currently accepted as a calibration fixture.
    """
    return (
        ResistanceSourceRecord(
            source_id="edinburgh_pacific_canoe_hydrodynamics",
            title="Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls",
            url="https://datashare.ed.ac.uk/handle/10283/4772",
            source_type="open_measured_towing_tank_dataset",
            intended_use="validation_candidate",
            measured_data=True,
            hull_class="pacific_canoe_like_slender_hulls",
            rights_status="cc_by_4_0_dataset_doi_10_7488_ds_3785",
            extraction_status="no_checked_in_numeric_fixture_until_schema",
            notes=(
                "Open measured towing-tank force dataset with CAD models for "
                "three slender Pacific-canoe-like hulls. Useful for validation "
                "source tracking, but not representative enough for general "
                "sea-kayak resistance calibration."
            ),
            warnings=[
                "pacific_canoe_not_sea_kayak",
                "fixed_sink_trim",
                "validation_not_calibration",
            ],
        ),
        ResistanceSourceRecord(
            source_id="sea_kayaker_kanu_compilation",
            title="Sea Kayaker-derived sea-kayak resistance compilation",
            url="https://www.kanu.de/nuke/downloads/Resistance.pdf",
            source_type="compiled_model_results",
            intended_use="citation_only",
            measured_data=False,
            hull_class="sea_kayak",
            rights_status="copyrighted_compilation_unclear_redistribution",
            extraction_status="do_not_vendor_extracted_tables",
            notes=(
                "Broad sea-kayak coverage, but values are Sea Kayaker-derived "
                "model outputs rather than primary open measurement data."
            ),
            warnings=["model_to_model_calibration_risk", "redistribution_unclear"],
        ),
        ResistanceSourceRecord(
            source_id="gomes_2018_k1_drag_components",
            title="Effect of wetted surface area on friction, pressure, wave and total drag of a kayak",
            url="https://doi.org/10.1080/14763141.2017.1357748",
            source_type="peer_reviewed_experimental_and_decomposition",
            intended_use="validation_candidate",
            measured_data=True,
            hull_class="sprint_k1",
            rights_status="publisher_copyright_no_fixture_rights",
            extraction_status="citation_only_until_permission",
            notes=(
                "Direct kayak passive-drag data for a sprint K1 with simulated "
                "paddler weights, but too narrow for general sea-kayak calibration."
            ),
            warnings=["sprint_k1_not_sea_kayak", "redistribution_not_established"],
        ),
        ResistanceSourceRecord(
            source_id="tzabiras_k1_tow_tank",
            title="Experimental and Numerical Study of the Flow Past the Olympic Class K-1 Flat Water Racing Kayak",
            url=(
                "https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-"
                "the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/"
            ),
            source_type="tow_tank_experimental_and_numerical",
            intended_use="validation_candidate",
            measured_data=True,
            hull_class="sprint_k1",
            rights_status="article_available_no_open_fixture_license",
            extraction_status="citation_only_until_permission",
            notes=(
                "Measured K1 resistance over a useful speed band, but hull class "
                "and load case do not represent the broader sea-kayak design space."
            ),
            warnings=["sprint_k1_not_sea_kayak", "fixture_rights_not_established"],
        ),
        ResistanceSourceRecord(
            source_id="mdpi_physics_of_kayaking",
            title="On the Physics of Kayaking",
            url="https://www.mdpi.com/2076-3417/12/18/8925",
            source_type="open_access_modeling_context",
            intended_use="citation_only",
            measured_data=False,
            hull_class="kayak_general",
            rights_status="cc_by_article_context",
            extraction_status="no_primary_calibration_dataset",
            notes=(
                "Open-access literature context may be reusable with attribution, "
                "but it does not provide primary calibration fixture data."
            ),
            warnings=["not_primary_resistance_dataset"],
        ),
    )


def default_resistance_source_review_packets() -> tuple[ResistanceSourceReviewPacket, ...]:
    """Return applied RFC 0042 source-review packets.

    Edinburgh is reviewed only as a validation candidate. The packet records
    why it is not promoted to a validation fixture or calibration fixture.
    """
    return (
        ResistanceSourceReviewPacket(
            source_id="edinburgh_pacific_canoe_hydrodynamics",
            title="Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls",
            citation=(
                "University of Edinburgh DataShare dataset, Hydrodynamics of "
                "Three Slender Models Resembling Pacific Canoe Hulls, "
                "DOI 10.7488/ds/3785"
            ),
            locator="https://datashare.ed.ac.uk/handle/10283/4772",
            source_type="open_measured_towing_tank_dataset",
            measured_data=True,
            hull_class="pacific_canoe_like_slender_hulls",
            rights=ResistanceSourceReviewEvidence(
                status="accepted",
                summary=(
                    "Registry and workflow 0050 research record the dataset as "
                    "CC BY 4.0; this covers dataset evidence, not article prose."
                ),
                refs=["doi:10.7488/ds/3785"],
            ),
            extraction=ResistanceSourceReviewEvidence(
                status="incomplete",
                summary=(
                    "No checked-in extraction schema, source-file checksum binding, "
                    "sheet/row filter, unit-normalization script, or row manifest "
                    "has landed."
                ),
            ),
            measured_quantity=ResistanceSourceReviewEvidence(
                status="accepted",
                summary=(
                    "Workflow 0050 research identifies measured hydrodynamic force "
                    "and resistance fields in the DataShare workbook."
                ),
            ),
            units=ResistanceSourceReviewEvidence(
                status="incomplete",
                summary=(
                    "Source units are identified in research, but kayakgen has no "
                    "accepted normalized row schema or conversion manifest."
                ),
            ),
            hull_envelope=ResistanceSourceReviewEvidence(
                status="accepted",
                summary=(
                    "The source covers Pacific-canoe-like slender hull models at "
                    "fixed sink and trim, outside the sea-kayak calibration envelope."
                ),
            ),
            speed_froude_range=ResistanceSourceReviewEvidence(
                status="accepted",
                summary=(
                    "Workflow 0050 research records model speeds around 0.4-1.6 m/s "
                    "and Fn about 0.117-0.466; length basis remains part of the "
                    "future extraction manifest."
                ),
            ),
            uncertainty=ResistanceSourceReviewEvidence(
                status="incomplete",
                summary=(
                    "No accepted uncertainty treatment, repeatability summary, or "
                    "digitization/Type B uncertainty note is bound to fixture rows."
                ),
            ),
            reviewer="workflow-0051-implementation-burndown-stage1",
            review_date="2026-05-14",
            review_verdict="validation_candidate",
            reasons=[
                "open_measured_dataset",
                "validation_source_context_only",
            ],
            non_promotion_reasons=[
                "pending_data_acquisition",
                "extraction_schema_missing",
                "unit_normalized_rows_not_checked_in",
                "uncertainty_treatment_missing",
                "outside_sea_kayak_calibration_envelope",
            ],
            warnings=[
                "validation_not_calibration",
                "pacific_canoe_not_sea_kayak",
                "fixture_promotion_deferred",
            ],
            primary_locator="https://datashare.ed.ac.uk/handle/10283/4772",
            secondary_locator="https://doi.org/10.7488/ds/3785",
            access_date="2026-05-14",
            source_checksum_sha256=None,
            source_checksum_pending_reason="pending_data_acquisition",
            license_identifier="CC BY 4.0",
            attribution=(
                "University of Edinburgh DataShare, Hydrodynamics of Three "
                "Slender Models Resembling Pacific Canoe Hulls (DOI "
                "10.7488/ds/3785), CC BY 4.0."
            ),
            extraction_script_ref=(
                "kayakgen/eval/calibration/extractors/"
                "edinburgh_datashare_pacific_canoe.py"
            ),
            measurement_units={
                "speed": "knots",
                "drag": "N",
                "length_waterline": "m",
                "trim": "deg",
                "sink": "mm",
                "water_temperature": "C",
            },
            froude_basis="Fn = U / sqrt(g * Lwl)",
            uncertainty_notes=(
                "Source repeatability and Type B / digitization uncertainty "
                "are not yet bound to fixture rows; pending data acquisition."
            ),
            accepted_fit_ref=None,
        ),
    )
