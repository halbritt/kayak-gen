"""Closed-volume schema records and policy types.

This module owns the serializable pydantic models, the literal type aliases,
and the policy-identity constructors that the rest of the closed-volume
package shares. The split keeps the schema layer free of geometry imports so
``ClosedVolumeBody`` and ``ClosedVolumeDiagnostics`` can be imported without
pulling in the self-intersection or topology algorithms.
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

ClosedVolumeReadinessLevel = Literal["invalid", "closed_volume"]
ClosedVolumeBodyType = Literal[
    "explicit_synthetic_triangle_mesh",
    "generated_hull_plus_deck_closed_body",
]
ClosedVolumeCapPolicy = Literal[
    "not_applicable_explicit_mesh",
    "explicit_bow_stern_endpoint_ring_caps",
]
ClosedVolumeDeckJoinPolicy = Literal[
    "not_applicable_explicit_mesh",
    "exact_shared_vertices_topside_sheerline_strip",
]
ClosedVolumeSelfIntersectionStatus = Literal[
    "not_checked", "passed", "failed", "inconclusive"
]
ClosedVolumeSelfIntersectionPolicy = Literal[
    "not_checked_rfc0016_compatibility",
    "required_rfc0021_conservative",
]
SelfIntersectionPairClassification = Literal["intersection", "near_contact"]

DEFAULT_VERTEX_WELD_TOLERANCE_M = 1e-6
DEFAULT_DEGENERATE_AREA_TOLERANCE_M2 = 1e-12
DEFAULT_SIGNED_VOLUME_TOLERANCE_M3 = 1e-12
DEFAULT_SELF_INTERSECTION_TOLERANCE_M = 1e-9
RFC0016_SYNTHETIC_PROFILE_NAME = "explicit_synthetic_closed_volume_v1"
RFC0021_SELF_INTERSECTION_PROFILE_NAME = (
    "explicit_synthetic_closed_volume_self_intersection_v1"
)
RFC0022_GENERATED_PROFILE_NAME = "generated_hull_plus_deck_closed_body_v1"
GENERATED_CLOSED_BODY_TYPE = "generated_hull_plus_deck_closed_body"
GENERATED_CLOSED_BODY_PART_NAME = "generated_hull_plus_deck"
DEFAULT_GENERATED_CLOSED_BODY_STATIONS = 16
DEFAULT_GENERATED_CLOSED_BODY_SECTION_POINTS = 16
SELF_INTERSECTION_NOT_CHECKED_ALGORITHM = "not_checked_rfc0016_compatibility"
SELF_INTERSECTION_ALGORITHM = "assembled_welded_aabb_triangle_pairs_v1"
MAX_SELF_INTERSECTION_EXAMPLE_PAIRS = 8


class ClosedVolumeTolerances(BaseModel):
    """Numeric tolerances used by closed-volume diagnostics."""

    model_config = ConfigDict(extra="forbid")

    vertex_weld_tolerance_m: float = Field(default=DEFAULT_VERTEX_WELD_TOLERANCE_M, gt=0)
    degenerate_area_tolerance_m2: float = Field(
        default=DEFAULT_DEGENERATE_AREA_TOLERANCE_M2, ge=0
    )
    signed_volume_tolerance_m3: float = Field(
        default=DEFAULT_SIGNED_VOLUME_TOLERANCE_M3, ge=0
    )
    self_intersection_tolerance_m: float = Field(
        default=DEFAULT_SELF_INTERSECTION_TOLERANCE_M, ge=0
    )
    cap_match_tolerance_m: float = Field(default=DEFAULT_VERTEX_WELD_TOLERANCE_M, ge=0)
    join_match_tolerance_m: float = Field(default=DEFAULT_VERTEX_WELD_TOLERANCE_M, ge=0)


class ClosedVolumePolicy(BaseModel):
    """Policy identity for a closed-volume diagnostic profile."""

    model_config = ConfigDict(extra="forbid")

    profile_name: str = RFC0016_SYNTHETIC_PROFILE_NAME
    body_type: ClosedVolumeBodyType = "explicit_synthetic_triangle_mesh"
    waterline_semantics: Literal["metadata_only"] = "metadata_only"
    cap_policy: ClosedVolumeCapPolicy = "not_applicable_explicit_mesh"
    deck_join_policy: ClosedVolumeDeckJoinPolicy = "not_applicable_explicit_mesh"
    normal_orientation: Literal["outward_positive_signed_volume"] = (
        "outward_positive_signed_volume"
    )
    cfd_readiness_policy: Literal["never_claim_cfd_ready"] = "never_claim_cfd_ready"
    self_intersection_policy: ClosedVolumeSelfIntersectionPolicy = (
        "not_checked_rfc0016_compatibility"
    )
    tolerances: ClosedVolumeTolerances = Field(default_factory=ClosedVolumeTolerances)

    @model_validator(mode="after")
    def _align_profile_policy(self) -> Self:
        if self.profile_name == RFC0021_SELF_INTERSECTION_PROFILE_NAME:
            self.self_intersection_policy = "required_rfc0021_conservative"
        if self.profile_name == RFC0022_GENERATED_PROFILE_NAME:
            self.body_type = GENERATED_CLOSED_BODY_TYPE
            self.cap_policy = "explicit_bow_stern_endpoint_ring_caps"
            self.deck_join_policy = "exact_shared_vertices_topside_sheerline_strip"
            self.self_intersection_policy = "required_rfc0021_conservative"
        return self


def explicit_synthetic_self_intersection_policy() -> ClosedVolumePolicy:
    """Return the RFC 0021 explicit synthetic profile requiring the check."""

    return ClosedVolumePolicy(
        profile_name=RFC0021_SELF_INTERSECTION_PROFILE_NAME,
        self_intersection_policy="required_rfc0021_conservative",
    )


def generated_hull_plus_deck_policy() -> ClosedVolumePolicy:
    """Return the RFC 0022 generated-body profile requiring the RFC 0021 check."""

    return ClosedVolumePolicy(
        profile_name=RFC0022_GENERATED_PROFILE_NAME,
        body_type=GENERATED_CLOSED_BODY_TYPE,
        cap_policy="explicit_bow_stern_endpoint_ring_caps",
        deck_join_policy="exact_shared_vertices_topside_sheerline_strip",
        self_intersection_policy="required_rfc0021_conservative",
    )


def _policy_requires_self_intersection(policy: ClosedVolumePolicy) -> bool:
    if policy.profile_name in (
        RFC0021_SELF_INTERSECTION_PROFILE_NAME,
        RFC0022_GENERATED_PROFILE_NAME,
    ):
        return True
    return policy.self_intersection_policy == "required_rfc0021_conservative"


class ClosedSurfacePart(BaseModel):
    """Serializable triangle-mesh part in a closed-volume body."""

    model_config = ConfigDict(extra="forbid")

    name: str
    vertices: tuple[tuple[float, float, float], ...]
    faces: tuple[tuple[int, int, int], ...]


class ClosedVolumeCoordinateSystem(BaseModel):
    """Machine-readable coordinate convention for closed evaluation bodies."""

    model_config = ConfigDict(extra="forbid")

    x: str = "longitudinal, stern positive, bow negative, spans -L/2 to +L/2"
    y: str = "port/starboard"
    z: str = "up positive"
    waterline_z_m: float = 0.0


class ClosedVolumeWaterlineMetadata(BaseModel):
    """Design waterline metadata recorded without cutting the generated body."""

    model_config = ConfigDict(extra="forbid")

    waterline_z_m: float = 0.0
    beam_wl_m: float


class ClosedVolumeBody(BaseModel):
    """Serializable closed-volume body."""

    model_config = ConfigDict(extra="forbid")

    body_id: str
    body_type: ClosedVolumeBodyType = "explicit_synthetic_triangle_mesh"
    source_hull_hash: str | None = None
    units: Literal["m"] = "m"
    coordinate_system: ClosedVolumeCoordinateSystem = Field(
        default_factory=ClosedVolumeCoordinateSystem
    )
    waterline_z_m: float = 0.0
    waterline_metadata: ClosedVolumeWaterlineMetadata | None = None
    policy: ClosedVolumePolicy = Field(default_factory=ClosedVolumePolicy)
    parts: tuple[ClosedSurfacePart, ...]

    @model_validator(mode="after")
    def _policy_body_type_matches(self) -> Self:
        if self.policy.body_type != self.body_type:
            raise ValueError("policy body_type must match body body_type")
        return self


class ClosedVolumeReadiness(BaseModel):
    """Closed-volume diagnostic result without CFD readiness claims."""

    model_config = ConfigDict(extra="forbid")

    level: ClosedVolumeReadinessLevel
    reasons: list[str] = Field(default_factory=list)


class ClosedSurfacePartDiagnostics(BaseModel):
    """Per-part topology and numeric diagnostics."""

    model_config = ConfigDict(extra="forbid")

    name: str
    vertex_count: int = Field(ge=0)
    face_count: int = Field(ge=0)
    raw_boundary_edges: int = Field(ge=0)
    raw_nonmanifold_edges: int = Field(ge=0)
    welded_boundary_edges: int = Field(ge=0)
    welded_nonmanifold_edges: int = Field(ge=0)
    degenerate_faces: int = Field(ge=0)
    nonfinite_vertices: int = Field(ge=0)
    nonfinite_faces: int = Field(ge=0)
    invalid_face_indices: int = Field(ge=0)


class ClosedVolumeTriangleReference(BaseModel):
    """Stable reference to an assembled-body triangle."""

    model_config = ConfigDict(extra="forbid")

    body_face_index: int = Field(ge=0)
    part_name: str
    part_face_index: int = Field(ge=0)


class ClosedVolumeSelfIntersectionPair(BaseModel):
    """Bounded example of a blocking non-adjacent triangle pair."""

    model_config = ConfigDict(extra="forbid")

    first: ClosedVolumeTriangleReference
    second: ClosedVolumeTriangleReference
    classification: SelfIntersectionPairClassification


class ClosedVolumeDiagnostics(BaseModel):
    """Authoritative body-level diagnostics for a closed-volume body."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    body_id: str
    body_type: ClosedVolumeBodyType
    profile_name: str
    source_hull_hash: str | None = None
    units: Literal["m"] = "m"
    coordinate_system: ClosedVolumeCoordinateSystem = Field(
        default_factory=ClosedVolumeCoordinateSystem
    )
    waterline_z_m: float = 0.0
    waterline_metadata: ClosedVolumeWaterlineMetadata | None = None
    policy: ClosedVolumePolicy
    readiness: ClosedVolumeReadiness
    part_diagnostics: list[ClosedSurfacePartDiagnostics]
    vertex_count: int = Field(ge=0)
    face_count: int = Field(ge=0)
    raw_boundary_edges: int = Field(ge=0)
    raw_nonmanifold_edges: int = Field(ge=0)
    welded_boundary_edges: int = Field(ge=0)
    welded_nonmanifold_edges: int = Field(ge=0)
    degenerate_faces: int = Field(ge=0)
    nonfinite_vertices: int = Field(ge=0)
    nonfinite_faces: int = Field(ge=0)
    invalid_face_indices: int = Field(ge=0)
    signed_volume_m3: float
    self_intersection_status: ClosedVolumeSelfIntersectionStatus
    self_intersection_algorithm: str
    self_intersection_tolerance_m: float = Field(ge=0)
    self_intersection_pair_count: int = Field(ge=0)
    self_intersection_example_pairs: list[ClosedVolumeSelfIntersectionPair] = Field(
        default_factory=list
    )
    warnings: list[str] = Field(default_factory=list)
    cfd_ready: Literal[False] = False

    @model_validator(mode="after")
    def _rfc0021_closed_volume_requires_passed_self_intersection(self) -> Self:
        if (
            self.readiness.level == "closed_volume"
            and _policy_requires_self_intersection(self.policy)
            and self.self_intersection_status != "passed"
        ):
            raise ValueError(
                "RFC 0021 closed-volume readiness requires passed "
                "self-intersection diagnostics"
            )
        return self
