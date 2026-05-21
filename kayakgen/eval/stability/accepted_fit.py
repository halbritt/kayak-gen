"""Accepted stability-fit schemas (RFC 0058 stage 1).

This module pins the data-record shape for a future measured-stability
acceptance workflow. It intentionally does not resolve fixture paths on disk,
promote fixtures, or upgrade RFC 0043 analytical GZ result semantics.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DEFAULT_STABILITY_FIT_RMSE_M = 0.005
DEFAULT_STABILITY_FIT_MAPE_FRACTION = 0.05
DEFAULT_STABILITY_FIT_MAX_ERROR_M = 0.01
DEFAULT_STABILITY_FIT_COVERAGE_FRACTION = 0.9

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

ReviewVerdict = Literal["accepted", "rejected", "deferred"]
StabilityFitVerdict = Literal["accepted", "rejected"]
StabilityFixturePromotionTarget = Literal[
    "measured_stability_fixture",
    "validation_candidate",
    "rejected",
]


class FixtureRef(BaseModel):
    """Reference to a measured-stability fixture manifest.

    Existence-on-disk is deliberately not checked in stage 1. Later promotion
    stages own manifest resolution and intended-use validation.
    """

    model_config = ConfigDict(extra="forbid")

    fixture_id: str = Field(min_length=1)
    fixture_path: str = Field(min_length=1)
    fixture_sha256: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def _fixture_sha256_is_lower_hex(self) -> "FixtureRef":
        if not _SHA256_RE.fullmatch(self.fixture_sha256):
            raise ValueError(
                "fixture_sha256 must be exactly 64 lowercase hexadecimal characters"
            )
        return self


class HullFamilyScope(BaseModel):
    """Hull-family envelope covered by a stability fit."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    hull_class: str = Field(min_length=1)
    design_hash_envelope: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _design_hash_envelope_non_empty(self) -> "HullFamilyScope":
        if not self.design_hash_envelope:
            raise ValueError("design_hash_envelope must contain at least one design hash")
        return self


class StabilityFitMetrics(BaseModel):
    """Error and coverage metrics for analytical-vs-measured GZ fitting."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    rmse_m: float = Field(ge=0)
    mape_fraction: float = Field(ge=0)
    max_error_m: float = Field(ge=0)
    coverage_fraction: float = Field(ge=0, le=1)


class ReviewerSignature(BaseModel):
    """Minimal reviewer attestation without required personal identity."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    reviewer_label: str = Field(min_length=1)
    reviewer_role: str = Field(min_length=1)
    signed_at: datetime


class StabilityFitRecord(BaseModel):
    """Immutable candidate or accepted stability-fit record."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    fit_id: str = Field(min_length=1)
    analytical_evaluator_version: str = Field(min_length=1)
    hull_family_scope: HullFamilyScope
    valid_heel_range_deg: tuple[float, float]
    fixtures: list[FixtureRef] = Field(min_length=1)
    fit_metrics: StabilityFitMetrics
    acceptance_verdict: StabilityFitVerdict
    rejection_reasons: list[str] = Field(default_factory=list)
    reviewer_signature: ReviewerSignature
    accepted_at: datetime | None = None
    notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    strict: bool = True

    @model_validator(mode="after")
    def _valid_heel_range_ordered(self) -> "StabilityFitRecord":
        low, high = self.valid_heel_range_deg
        if not low < high:
            raise ValueError(
                "valid_heel_range_deg requires low < high; "
                f"got ({low}, {high})"
            )
        return self

    @model_validator(mode="after")
    def _accepted_verdict_has_acceptance_metadata(self) -> "StabilityFitRecord":
        if self.acceptance_verdict == "accepted":
            if self.accepted_at is None:
                raise ValueError(
                    "acceptance_verdict='accepted' requires accepted_at to be set"
                )
            if self.rejection_reasons:
                raise ValueError(
                    "acceptance_verdict='accepted' requires rejection_reasons=[]"
                )
        return self

    @model_validator(mode="after")
    def _strict_thresholds(self) -> "StabilityFitRecord":
        if not self.strict:
            if "strict_check_skipped" not in self.warnings:
                self.warnings.append("strict_check_skipped")
            return self

        metrics = self.fit_metrics
        failures: list[str] = []
        if metrics.rmse_m > DEFAULT_STABILITY_FIT_RMSE_M:
            failures.append(
                "rmse_m "
                f"{metrics.rmse_m} exceeds {DEFAULT_STABILITY_FIT_RMSE_M}"
            )
        if metrics.mape_fraction > DEFAULT_STABILITY_FIT_MAPE_FRACTION:
            failures.append(
                "mape_fraction "
                f"{metrics.mape_fraction} exceeds "
                f"{DEFAULT_STABILITY_FIT_MAPE_FRACTION}"
            )
        if metrics.max_error_m > DEFAULT_STABILITY_FIT_MAX_ERROR_M:
            failures.append(
                "max_error_m "
                f"{metrics.max_error_m} exceeds "
                f"{DEFAULT_STABILITY_FIT_MAX_ERROR_M}"
            )
        if metrics.coverage_fraction < DEFAULT_STABILITY_FIT_COVERAGE_FRACTION:
            failures.append(
                "coverage_fraction "
                f"{metrics.coverage_fraction} below "
                f"{DEFAULT_STABILITY_FIT_COVERAGE_FRACTION}"
            )
        if failures:
            raise ValueError(
                "stability_fit_metrics_outside_default_thresholds: "
                + "; ".join(failures)
            )
        return self


class StabilityFixturePromotionPacket(BaseModel):
    """Review packet for future fixture promotion to measured-stability fixture."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    fixture_ref: FixtureRef
    rights_review: ReviewVerdict
    hull_identity_review: ReviewVerdict
    calibration_drift_review: ReviewVerdict
    hysteresis_review: ReviewVerdict
    free_equilibrium_review: ReviewVerdict
    rig_design_match: bool
    promotion_target: StabilityFixturePromotionTarget
    rejection_reasons: list[str] = Field(default_factory=list)
    reviewer_signature: ReviewerSignature

    @model_validator(mode="after")
    def _measured_fixture_promotion_requires_all_reviews(
        self,
    ) -> "StabilityFixturePromotionPacket":
        if self.promotion_target != "measured_stability_fixture":
            return self
        verdicts = (
            self.rights_review,
            self.hull_identity_review,
            self.calibration_drift_review,
            self.hysteresis_review,
            self.free_equilibrium_review,
        )
        if any(verdict != "accepted" for verdict in verdicts):
            raise ValueError(
                "measured_stability_fixture promotion requires every review "
                "verdict to be 'accepted'"
            )
        if not self.rig_design_match:
            raise ValueError(
                "measured_stability_fixture promotion requires rig_design_match=True"
            )
        if self.rejection_reasons:
            raise ValueError(
                "measured_stability_fixture promotion requires rejection_reasons=[]"
            )
        return self


__all__ = [
    "DEFAULT_STABILITY_FIT_COVERAGE_FRACTION",
    "DEFAULT_STABILITY_FIT_MAPE_FRACTION",
    "DEFAULT_STABILITY_FIT_MAX_ERROR_M",
    "DEFAULT_STABILITY_FIT_RMSE_M",
    "FixtureRef",
    "HullFamilyScope",
    "ReviewVerdict",
    "ReviewerSignature",
    "StabilityFitMetrics",
    "StabilityFitRecord",
    "StabilityFitVerdict",
    "StabilityFixturePromotionPacket",
    "StabilityFixturePromotionTarget",
]
