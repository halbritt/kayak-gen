"""EvaluationResult — the integration object that joins evaluator outputs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from kayakgen.eval.hydrostatics import Hydrostatics


class ResistanceCurve(BaseModel):
    """Reserved by RFC 0005; populated when the resistance evaluator lands."""

    model_config = ConfigDict(extra="forbid")

    V_knots: list[float]
    Fn: list[float]
    Rv_N: list[float]
    Rw_N: list[float]
    Rt_N: list[float]


class GZCurve(BaseModel):
    """Reserved for a future stability evaluator."""

    model_config = ConfigDict(extra="forbid")

    angles_deg: list[float]
    gz_m: list[float]


class CfdResult(BaseModel):
    """Reserved for the heavy-CFD tier (RFC 0008 §6 job stub)."""

    model_config = ConfigDict(extra="forbid")

    solver: str
    drag_N: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    """Read-side join of evaluator outputs sharing a single hull."""

    model_config = ConfigDict(extra="forbid")

    hull_hash: str
    hydrostatics: Hydrostatics
    resistance: ResistanceCurve | None = None
    stability: GZCurve | None = None
    cfd: CfdResult | None = None
    timings_ms: dict[str, float] = Field(default_factory=dict)
