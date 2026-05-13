"""Hull aggregate root: serializable design parameters."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from kayakgen.model.geometry import HullGeometry


class Hull(BaseModel):
    """The design-parameter aggregate root of the kayakgen domain.

    A Hull is the JSON-serializable record of every input the generator
    needs. Geometry, hydrostatics, and resistance are derivable; this
    object owns no derived state. Round-trip: ``Hull.model_validate_json`` ↔
    ``Hull.model_dump_json``.

    Field naming uses physical units (``length_m``) rather than the
    legacy single-letter names (``L``); the ``KayakGenerator`` shim in
    ``generator.py`` translates between them for the existing GUI.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    schema_version: Literal["1"] = "1"
    name: str = "untitled"

    length_m: float = Field(default=4.5, gt=0)
    beam_oa_m: float = Field(default=0.55, gt=0)
    beam_wl_m: float | None = Field(default=None, description="Beam at waterline; None falls back to beam_oa_m. RFC 0006.")
    draft_m: float = Field(default=0.12, gt=0)
    deck_height_m: float = Field(default=0.23, gt=0)

    Cp: float = Field(default=0.55, gt=0, lt=1)
    Cm: float = Field(default=0.85, gt=0, le=1)
    deck_flatness: float = Field(default=8.0, gt=0)
    center_box_ratio: float = Field(default=0.33, ge=0, le=1)

    bow_rake: float = Field(default=1.0, ge=0, le=1, description="0 = plumb, 1 = current raked behaviour. RFC 0004.")
    LCB_frac: float = Field(default=0.50, ge=0, le=1, description="Reserved by RFC 0006; not yet honoured by the loft.")
    rocker_bow_m: float = Field(default=0.0, ge=0)
    rocker_stern_m: float = Field(default=0.0, ge=0)

    geometry_kind: Literal["lofted"] = "lofted"

    @model_validator(mode="after")
    def _validate_beam_wl(self) -> "Hull":
        if self.beam_wl_m is None:
            return self
        if self.beam_wl_m <= 0:
            raise ValueError("beam_wl_m must be positive when provided")
        if self.beam_wl_m > self.beam_oa_m:
            raise ValueError("beam_wl_m must be less than or equal to beam_oa_m")
        return self

    def hash(self) -> str:
        """Stable cache key for this hull's design parameters."""
        return hashlib.sha256(self.model_dump_json().encode("utf-8")).hexdigest()

    def to_geometry(self) -> "HullGeometry":
        """Construct the geometry implementation declared by ``geometry_kind``."""
        from kayakgen.model.geometry import LoftedHullGeometry

        if self.geometry_kind == "lofted":
            return LoftedHullGeometry(self)
        raise ValueError(f"unknown geometry_kind: {self.geometry_kind!r}")
