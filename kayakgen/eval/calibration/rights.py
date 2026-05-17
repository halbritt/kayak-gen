"""Rights-checklist record for calibration-campaign artifacts.

RFC 0054 deferred open question: ``RightsChecklist`` lives here, alongside
the existing calibration vocabulary, rather than in a generic provenance
module. This keeps the calibration aggregate cohesive and avoids dragging
the rights schema into modules that do not need it (e.g. resistance,
hydrostatics, mesh).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RightsChecklist(BaseModel):
    """License / attribution evidence for a calibration-campaign artifact.

    The record is intentionally minimal but pinned: every field that
    matters for whether a downstream consumer may redistribute the
    artifact is bound at validation time. ``notes`` carries any
    qualifying remarks (e.g. "redistribution allowed only with this
    attribution string", "embargoed until 2027-01-01").
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    license_identifier: str = Field(min_length=1)
    attribution: str = Field(min_length=1)
    source_locator: str = Field(min_length=1)
    redistribution_authorized: bool
    attribution_required: bool
    notes: list[str] = Field(default_factory=list)
