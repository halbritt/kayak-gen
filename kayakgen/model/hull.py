"""Hull aggregate root: serializable design parameters."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kayakgen.model.distribution_v2 import DistributionV2Spec

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

    bow_rake: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description=(
            "0 = plumb bow, 1 = legacy raked bow. Legacy bow_rake-only "
            "inputs seed stern_rake to the same value. RFC 0028."
        ),
    )
    stern_rake: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="0 = plumb stern, 1 = legacy raked stern. RFC 0028.",
    )
    LCB_frac: float = Field(default=0.50, ge=0, le=1, description="Reserved by RFC 0006; not yet honoured by the loft.")
    rocker_bow_m: float = Field(default=0.0, ge=0)
    rocker_stern_m: float = Field(default=0.0, ge=0)

    geometry_kind: Literal["lofted", "distribution_v2"] = "lofted"
    distribution_v2: DistributionV2Spec | None = None

    hull_class: str | None = Field(
        default=None,
        description=(
            "Hull-family tag drawn from the calibration vocabulary "
            "(``sea_kayak``, ``sprint_k1``, ``kayak_general``, "
            "``pacific_canoe_like_slender``, …). RFC 0043 stage 4: a real "
            "value is REQUIRED for the analytical high-angle GZ label to "
            "flip to ``validated_hydrostatic_comparison``. ``None`` (the "
            "safe default) keeps the label unvalidated regardless of "
            "fit-registry contents — this preserves the threat-model "
            "invariant in ``resolve_analytical_claim_label``."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _seed_legacy_symmetric_stern_rake(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        if "bow_rake" in data and "stern_rake" not in data:
            return {**data, "stern_rake": data["bow_rake"]}
        return data

    @model_validator(mode="after")
    def _validate_beam_wl(self) -> "Hull":
        if self.beam_wl_m is None:
            return self
        if self.beam_wl_m <= 0:
            raise ValueError("beam_wl_m must be positive when provided")
        if self.beam_wl_m > self.beam_oa_m:
            raise ValueError("beam_wl_m must be less than or equal to beam_oa_m")
        return self

    @model_validator(mode="after")
    def _validate_distribution_v2_coupling(self) -> "Hull":
        if self.geometry_kind == "distribution_v2":
            if self.distribution_v2 is None:
                raise ValueError(
                    "geometry_kind='distribution_v2' requires a distribution_v2 spec"
                )
            # RFC 0048 open-question decision: bow_rake / stern_rake are
            # legacy lofted-loft controls. They are preserved on the
            # record for backwards-compat reporting but are refused when
            # the hull declares distribution_v2 geometry.
            if self.bow_rake != 1.0 or self.stern_rake != 1.0:
                raise ValueError(
                    "geometry_kind='distribution_v2' refuses non-default bow_rake / "
                    "stern_rake; rake is reported but does not drive the V2 loft"
                )
        return self

    def record_hash(self) -> str:
        """SHA-256 over this hull's full serialized record (RFC 0049).

        Equivalent to today's :meth:`hash` and byte-stable with it. Owns
        the "record identity" half of the RFC 0049 vocabulary: differs
        whenever any field — including ``name`` — differs.
        """

        return hashlib.sha256(self.model_dump_json().encode("utf-8")).hexdigest()

    def design_hash(self) -> str:
        """SHA-256 over this hull's physical design inputs only (RFC 0049).

        Invariant under renaming the hull or reordering JSON keys; changes
        whenever any physical input (``length_m``, ``Cp``, ...) changes.
        Delegates to :func:`kayakgen.services.identity.design_hash_for_hull`.
        """

        from kayakgen.services.identity import design_hash_for_hull

        return design_hash_for_hull(self)

    def hash(self) -> str:
        """Backwards-compat alias for :meth:`record_hash` (RFC 0049)."""

        return self.record_hash()

    def to_geometry(self) -> "HullGeometry":
        """Construct the geometry implementation declared by ``geometry_kind``."""
        from kayakgen.model.geometry import DistributionV2Geometry, LoftedHullGeometry

        if self.geometry_kind == "lofted":
            return LoftedHullGeometry(self)
        if self.geometry_kind == "distribution_v2":
            return DistributionV2Geometry(self)
        raise ValueError(f"unknown geometry_kind: {self.geometry_kind!r}")
