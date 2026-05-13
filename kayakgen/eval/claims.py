"""Shared RFC 0025 claim-state contract for evaluation outputs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ClaimState = Literal[
    "raw_unvalidated",
    "uncalibrated_comparative",
    "validation_fixture",
    "calibration_fixture_candidate",
    "calibration_fixture",
    "calibrated_model",
    "validated_design_fitness",
]

RAW_UNVALIDATED = "raw_unvalidated"
UNCALIBRATED_COMPARATIVE = "uncalibrated_comparative"
VALIDATION_FIXTURE = "validation_fixture"
CALIBRATION_FIXTURE_CANDIDATE = "calibration_fixture_candidate"
CALIBRATION_FIXTURE = "calibration_fixture"
CALIBRATED_MODEL = "calibrated_model"
VALIDATED_DESIGN_FITNESS = "validated_design_fitness"

ACCEPTED_USE_COMPARATIVE_FILTER = "comparative_filter"
ACCEPTED_USE_FINAL_PREDICTION = "final_prediction"
ACCEPTED_USE_FINAL_DESIGN_FITNESS = "final_design_fitness"

WARNING_COMPARATIVE_FILTER_ONLY = "comparative_filter_only"
WARNING_NOT_FINAL_PERFORMANCE_PREDICTION = "not_final_performance_prediction"
WARNING_UNCALIBRATED_NO_VALIDITY_ENVELOPE = "uncalibrated_no_validity_envelope"
WARNING_RAW_CFD_UNVALIDATED = "raw_cfd_unvalidated"

PASSED_FIT_STATUSES = frozenset({"passed", "accepted", "fit_passed"})
UNCALIBRATED_WARNING_CODES = frozenset(
    {
        WARNING_COMPARATIVE_FILTER_ONLY,
        WARNING_NOT_FINAL_PERFORMANCE_PREDICTION,
        WARNING_UNCALIBRATED_NO_VALIDITY_ENVELOPE,
    }
)


class ClaimMetadata(BaseModel):
    """Machine-readable claim metadata required by RFC 0025."""

    model_config = ConfigDict(extra="forbid")

    claim_state: ClaimState
    accepted_uses: list[str] = Field(default_factory=list)
    calibration_fixture_ids: list[str] = Field(default_factory=list)
    validation_fixture_ids: list[str] = Field(default_factory=list)
    model_version: str | None = None
    fit_status: str | None = None
    fit_metrics: dict[str, float] = Field(default_factory=dict)
    validity_envelope: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)


class RawUnvalidatedClaimFields(BaseModel):
    """Top-level RFC 0025 fields for current raw CFD-style records."""

    model_config = ConfigDict(extra="forbid")

    claim_state: Literal["raw_unvalidated"] = RAW_UNVALIDATED
    accepted_uses: list[str] = Field(default_factory=list)
    calibration_fixture_ids: list[str] = Field(default_factory=list)
    validation_fixture_ids: list[str] = Field(default_factory=list)
    model_version: str | None = None
    fit_status: str | None = None
    fit_metrics: dict[str, float] = Field(default_factory=dict)
    validity_envelope: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=lambda: [WARNING_RAW_CFD_UNVALIDATED])

    @model_validator(mode="after")
    def _raw_claim_must_not_promote(self) -> "RawUnvalidatedClaimFields":
        if self.accepted_uses:
            raise ValueError("raw_unvalidated records cannot declare accepted uses")
        if self.calibration_fixture_ids or self.validation_fixture_ids:
            raise ValueError("raw_unvalidated records cannot declare fixture IDs")
        if self.model_version or self.fit_status or self.fit_metrics:
            raise ValueError("raw_unvalidated records cannot declare fit evidence")
        if self.validity_envelope is not None:
            raise ValueError("raw_unvalidated records cannot declare validity envelopes")
        return self


def uncalibrated_resistance_warnings() -> list[str]:
    """Warnings attached to today's raw analytical resistance output."""
    return [
        WARNING_COMPARATIVE_FILTER_ONLY,
        WARNING_NOT_FINAL_PERFORMANCE_PREDICTION,
        WARNING_UNCALIBRATED_NO_VALIDITY_ENVELOPE,
    ]


def raw_cfd_warnings() -> list[str]:
    """Warnings attached to today's raw local CFD dispatch records."""
    return [WARNING_RAW_CFD_UNVALIDATED]


def claim_metadata_from_fields(value: Any) -> ClaimMetadata:
    """Build the shared claim model from a Pydantic model or mapping.

    Legacy field names are copied only as aliases. They never promote a record
    to a stronger claim state without the first-class RFC 0025 fields.
    """
    if isinstance(value, ClaimMetadata):
        return value
    if hasattr(value, "model_dump"):
        data = value.model_dump(mode="python")
    elif isinstance(value, Mapping):
        data = dict(value)
    else:
        raise TypeError(f"cannot read claim metadata from {type(value).__name__}")

    if "accepted_uses" not in data and "accepted_use" in data:
        data["accepted_uses"] = data["accepted_use"]
    if "model_version" not in data and "calibration_version" in data:
        data["model_version"] = data["calibration_version"]

    claim_fields = {
        "claim_state": data.get("claim_state"),
        "accepted_uses": data.get("accepted_uses", []),
        "calibration_fixture_ids": data.get("calibration_fixture_ids", []),
        "validation_fixture_ids": data.get("validation_fixture_ids", []),
        "model_version": data.get("model_version"),
        "fit_status": data.get("fit_status"),
        "fit_metrics": data.get("fit_metrics", {}),
        "validity_envelope": data.get("validity_envelope"),
        "warnings": data.get("warnings", []),
    }
    return ClaimMetadata.model_validate(claim_fields)


def claim_allows_calibrated_prediction(value: Any) -> bool:
    """Return whether a resistance value may be treated as calibrated prediction."""
    try:
        claim = claim_metadata_from_fields(value)
    except Exception:
        return False
    return (
        claim.claim_state == CALIBRATED_MODEL
        and ACCEPTED_USE_FINAL_PREDICTION in claim.accepted_uses
        and bool(claim.calibration_fixture_ids)
        and bool(claim.model_version)
        and (claim.fit_status in PASSED_FIT_STATUSES or bool(claim.fit_metrics))
        and bool(claim.validity_envelope)
        and not UNCALIBRATED_WARNING_CODES.intersection(claim.warnings)
    )


def claim_allows_final_design_fitness(value: Any) -> bool:
    """Return whether a value may be used as final design fitness.

    No current kayakgen output satisfies this; the helper exists so future
    scoring work has an explicit gate instead of reusing calibrated drag.
    """
    try:
        claim = claim_metadata_from_fields(value)
    except Exception:
        return False
    return (
        claim.claim_state == VALIDATED_DESIGN_FITNESS
        and ACCEPTED_USE_FINAL_DESIGN_FITNESS in claim.accepted_uses
        and bool(claim.validity_envelope)
    )
