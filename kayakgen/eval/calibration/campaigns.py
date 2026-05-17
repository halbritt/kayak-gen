"""Calibration-campaign aggregate roots (RFC 0054).

Three aggregates live here:

- ``TankTestCampaign`` (with row aggregate ``TankTestRun``): the on-disk
  schema for a commissioned towing-tank drag campaign.
- ``IncliningTestCampaign`` (with row aggregate ``IncliningTestRun``):
  the on-disk schema for a commissioned inclining-experiment campaign.
- ``AcceptedFitRecord``: the immutable acceptance record that gates
  promotion of a ``ResistanceSourceReviewPacket`` to
  ``calibration_fixture`` per D006.

Hull-geometry binding is by hash, per the RFC 0054 deferred decision
(``hull_design_hash``). RFC 0049 introduces a stable ``Hull.design_hash()``
that we will eventually consume; until that lands, callers should use
``Hull.hash()`` as the placeholder (see ``GeometryReference`` notes).
"""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kayakgen.eval.calibration.rights import RightsChecklist

UncertaintyMethod = Literal[
    "Type_A_repeatability",
    "Type_B_uncertainty_budget",
    "documented_caveat",
]
PaddlerState = Literal["absent", "rigid_manikin", "active_paddler"]
FitMetric = Literal["RMSE", "MAPE", "R2"]


class GeometryReference(BaseModel):
    """Pointer from a campaign row to the hull it was run against.

    The primary identity is ``hull_design_hash`` (per RFC 0049
    vocabulary). A CAD/STL/offsets path is an additional, optional
    locator so a reviewer can fetch the actual surface the lab measured
    — it is NOT a substitute for the hash.

    Until ``Hull.design_hash()`` lands as part of RFC 0049 (a parallel
    effort), operators should populate ``hull_design_hash`` with
    ``Hull.hash()`` and document the transition in the campaign notes.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    geometry_path: str = Field(min_length=1)
    hull_design_hash: str | None = None


class TankTestRun(BaseModel):
    """One operating-point row from a towing-tank drag campaign."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    source_id: str = Field(min_length=1)
    hull_design_hash: str = Field(min_length=1)
    speed_ms: float = Field(ge=0)
    total_drag_n: float
    drag_uncertainty_n: float | None = None
    trim_deg: float
    sink_mm: float
    water_temperature_c: float
    notes: list[str] = Field(default_factory=list)


class TankTestCampaign(BaseModel):
    """Aggregate root for a towing-tank drag campaign."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    source_id: str = Field(min_length=1)
    rights_checklist: RightsChecklist
    geometry_reference: GeometryReference
    rows: list[TankTestRun] = Field(default_factory=list)
    uncertainty_method: UncertaintyMethod

    @model_validator(mode="after")
    def _rows_share_source_id(self) -> "TankTestCampaign":
        mismatched = [r.source_id for r in self.rows if r.source_id != self.source_id]
        if mismatched:
            raise ValueError(
                "TankTestCampaign rows must all carry the campaign source_id; "
                f"saw {sorted(set(mismatched))!r} alongside {self.source_id!r}"
            )
        return self


class IncliningTestRun(BaseModel):
    """One operating-point row from an inclining-experiment campaign."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    source_id: str = Field(min_length=1)
    hull_design_hash: str = Field(min_length=1)
    heel_deg: float
    applied_moment_nm: float
    applied_moment_uncertainty_nm: float | None = None
    sealed_body: bool
    cockpit_flooded: bool
    paddler_state: PaddlerState
    notes: list[str] = Field(default_factory=list)


class IncliningTestCampaign(BaseModel):
    """Aggregate root for an inclining-experiment campaign."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    source_id: str = Field(min_length=1)
    rights_checklist: RightsChecklist
    geometry_reference: GeometryReference
    rows: list[IncliningTestRun] = Field(default_factory=list)

    @model_validator(mode="after")
    def _rows_share_source_id(self) -> "IncliningTestCampaign":
        mismatched = [r.source_id for r in self.rows if r.source_id != self.source_id]
        if mismatched:
            raise ValueError(
                "IncliningTestCampaign rows must all carry the campaign source_id; "
                f"saw {sorted(set(mismatched))!r} alongside {self.source_id!r}"
            )
        return self


class AcceptedFitRecord(BaseModel):
    """Immutable acceptance record for a calibration fit (D006 gate).

    ``model_version`` is treated as immutable: once an
    ``AcceptedFitRecord`` is written, the underlying fitted model may
    not be re-trained without minting a new ``fit_id`` /
    ``model_version`` pair. The validator does not enforce immutability
    on disk (that is an operational property); it pins the field shape
    so a downstream consumer can rely on the contract.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    fit_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    fit_metric: FitMetric
    fit_value: float
    holdout_rms_n: float
    residuals: list[tuple[float, float]] = Field(default_factory=list)
    validity_envelope: dict[str, tuple[float, float]] = Field(default_factory=dict)
    accepted_at: str = Field(min_length=1)
    accepted_by: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# CSV ingest helpers (pure-eval; no CLI imports).
#
# The ingest helpers parse a small, documented CSV row shape into the
# respective ``*Run`` records. The CLI calls them after loading the
# rights / geometry pieces. The helpers refuse extra/missing columns at
# the row level — schema drift is caught at validation, not at ingest.


_TANK_TEST_COLUMNS: tuple[str, ...] = (
    "speed_ms",
    "total_drag_n",
    "drag_uncertainty_n",
    "trim_deg",
    "sink_mm",
    "water_temperature_c",
    "notes",
)
_INCLINING_TEST_COLUMNS: tuple[str, ...] = (
    "heel_deg",
    "applied_moment_nm",
    "applied_moment_uncertainty_nm",
    "sealed_body",
    "cockpit_flooded",
    "paddler_state",
    "notes",
)


def _coerce_optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return float(stripped)


def _coerce_bool(value: str) -> bool:
    stripped = value.strip().lower()
    if stripped in {"true", "1", "yes", "y", "t"}:
        return True
    if stripped in {"false", "0", "no", "n", "f"}:
        return False
    raise ValueError(f"cannot coerce {value!r} to bool")


def _split_notes(value: str | None) -> list[str]:
    if value is None:
        return []
    stripped = value.strip()
    if not stripped:
        return []
    return [piece.strip() for piece in stripped.split(";") if piece.strip()]


def _read_csv(csv_path: Path, required_columns: tuple[str, ...]) -> list[dict[str, str]]:
    text = csv_path.read_text()
    reader = csv.DictReader(StringIO(text))
    fieldnames = tuple(reader.fieldnames or ())
    missing = [c for c in required_columns if c not in fieldnames]
    extra = [c for c in fieldnames if c not in required_columns]
    if missing:
        raise ValueError(
            f"CSV {csv_path} is missing required columns: {missing!r} "
            f"(expected {list(required_columns)!r})"
        )
    if extra:
        raise ValueError(
            f"CSV {csv_path} declares unrecognised columns: {extra!r} "
            f"(expected exactly {list(required_columns)!r})"
        )
    return list(reader)


def tank_test_campaign_from_csv(
    csv_path: Path,
    *,
    source_id: str,
    hull_design_hash: str,
    rights_checklist: RightsChecklist,
    geometry_reference: GeometryReference,
    uncertainty_method: UncertaintyMethod,
) -> TankTestCampaign:
    """Ingest a tank-test CSV into a validated ``TankTestCampaign``.

    Required CSV columns: speed_ms, total_drag_n, drag_uncertainty_n,
    trim_deg, sink_mm, water_temperature_c, notes (notes is a
    semicolon-separated string).
    """
    raw_rows = _read_csv(csv_path, _TANK_TEST_COLUMNS)
    rows = [
        TankTestRun(
            source_id=source_id,
            hull_design_hash=hull_design_hash,
            speed_ms=float(row["speed_ms"]),
            total_drag_n=float(row["total_drag_n"]),
            drag_uncertainty_n=_coerce_optional_float(row.get("drag_uncertainty_n")),
            trim_deg=float(row["trim_deg"]),
            sink_mm=float(row["sink_mm"]),
            water_temperature_c=float(row["water_temperature_c"]),
            notes=_split_notes(row.get("notes")),
        )
        for row in raw_rows
    ]
    return TankTestCampaign(
        source_id=source_id,
        rights_checklist=rights_checklist,
        geometry_reference=geometry_reference,
        rows=rows,
        uncertainty_method=uncertainty_method,
    )


def inclining_test_campaign_from_csv(
    csv_path: Path,
    *,
    source_id: str,
    hull_design_hash: str,
    rights_checklist: RightsChecklist,
    geometry_reference: GeometryReference,
) -> IncliningTestCampaign:
    """Ingest an inclining-test CSV into a validated ``IncliningTestCampaign``.

    Required CSV columns: heel_deg, applied_moment_nm,
    applied_moment_uncertainty_nm, sealed_body, cockpit_flooded,
    paddler_state, notes (semicolon-separated).
    """
    raw_rows = _read_csv(csv_path, _INCLINING_TEST_COLUMNS)
    rows = [
        IncliningTestRun(
            source_id=source_id,
            hull_design_hash=hull_design_hash,
            heel_deg=float(row["heel_deg"]),
            applied_moment_nm=float(row["applied_moment_nm"]),
            applied_moment_uncertainty_nm=_coerce_optional_float(
                row.get("applied_moment_uncertainty_nm")
            ),
            sealed_body=_coerce_bool(row["sealed_body"]),
            cockpit_flooded=_coerce_bool(row["cockpit_flooded"]),
            paddler_state=row["paddler_state"].strip(),  # type: ignore[arg-type]
            notes=_split_notes(row.get("notes")),
        )
        for row in raw_rows
    ]
    return IncliningTestCampaign(
        source_id=source_id,
        rights_checklist=rights_checklist,
        geometry_reference=geometry_reference,
        rows=rows,
    )


# ---------------------------------------------------------------------------
# Acceptance helpers


class AcceptedFitRejection(ValueError):
    """Raised when an accept-fit request fails the operator-set threshold.

    The structured ``reason`` token is suitable for inclusion in error
    payloads, and the human-readable message includes both the recorded
    metric value and the configured threshold.
    """

    reason: str

    def __init__(self, *, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def evaluate_fit_against_threshold(
    record: AcceptedFitRecord,
    *,
    measured_baseline: float,
    threshold_pct: float,
) -> None:
    """Raise ``AcceptedFitRejection`` if the fit is below the threshold.

    The default acceptance rule (D006-aligned) is ``RMSE <= threshold_pct
    of measured-row baseline``. For ``MAPE`` we treat ``threshold_pct``
    as the maximum admissible MAPE in percent. For ``R2`` we treat
    ``threshold_pct`` as a *minimum* admissible value (so a higher R2
    passes).
    """
    if threshold_pct <= 0:
        raise ValueError("threshold_pct must be positive")
    if record.fit_metric == "RMSE":
        if measured_baseline <= 0:
            raise ValueError(
                "RMSE threshold requires a positive measured_baseline"
            )
        ceiling = measured_baseline * (threshold_pct / 100.0)
        if record.fit_value > ceiling:
            raise AcceptedFitRejection(
                reason="fit_above_rmse_threshold",
                message=(
                    f"RMSE {record.fit_value} exceeds threshold "
                    f"{ceiling} ({threshold_pct}% of baseline "
                    f"{measured_baseline})"
                ),
            )
    elif record.fit_metric == "MAPE":
        if record.fit_value > threshold_pct:
            raise AcceptedFitRejection(
                reason="fit_above_mape_threshold",
                message=(
                    f"MAPE {record.fit_value} exceeds threshold "
                    f"{threshold_pct}"
                ),
            )
    elif record.fit_metric == "R2":
        if record.fit_value < threshold_pct:
            raise AcceptedFitRejection(
                reason="fit_below_r2_threshold",
                message=(
                    f"R2 {record.fit_value} below minimum {threshold_pct}"
                ),
            )
