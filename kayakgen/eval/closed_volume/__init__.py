"""Closed-volume contract models and diagnostics for closed evaluation bodies.

This package accepts caller-supplied synthetic meshes and the RFC 0022 generated
hull-plus-deck evaluation body. It never promotes a body to ``cfd_ready``.

Module layout
-------------
* :mod:`kayakgen.eval.closed_volume.schemas` — pydantic records, literal
  aliases, default-tolerance constants and policy constructors.
* :mod:`kayakgen.eval.closed_volume.generated_body` — explicit-mesh and
  RFC 0022 hull-plus-deck body builders plus the array-shape helpers.
* :mod:`kayakgen.eval.closed_volume.topology` — per-array diagnostics,
  edge counts, welding and signed-volume routines.
* :mod:`kayakgen.eval.closed_volume.self_intersection` — RFC 0021
  triangle-pair scan and supporting geometry kernels.
* :mod:`kayakgen.eval.closed_volume.diagnostics` —
  :func:`diagnose_closed_volume_body` and dispatch helpers that compose the
  topology and self-intersection layers.

This ``__init__`` is the byte-stable import surface for every name the
single-file module exposed; downstream code continues to import them as
``kayakgen.eval.closed_volume.X``.
"""

from __future__ import annotations

from kayakgen.eval.closed_volume.diagnostics import (
    diagnose_closed_volume_body,
    dispatch_evidence_satisfies_profile,
)
from kayakgen.eval.closed_volume.generated_body import (
    explicit_synthetic_body,
    generated_hull_plus_deck_body,
    generated_hull_plus_deck_closed_body,
)
from kayakgen.eval.closed_volume.schemas import (
    DEFAULT_DEGENERATE_AREA_TOLERANCE_M2,
    DEFAULT_GENERATED_CLOSED_BODY_SECTION_POINTS,
    DEFAULT_GENERATED_CLOSED_BODY_STATIONS,
    DEFAULT_SELF_INTERSECTION_TOLERANCE_M,
    DEFAULT_SIGNED_VOLUME_TOLERANCE_M3,
    DEFAULT_VERTEX_WELD_TOLERANCE_M,
    GENERATED_CLOSED_BODY_PART_NAME,
    GENERATED_CLOSED_BODY_TYPE,
    MAX_SELF_INTERSECTION_EXAMPLE_PAIRS,
    RFC0016_SYNTHETIC_PROFILE_NAME,
    RFC0021_SELF_INTERSECTION_PROFILE_NAME,
    RFC0022_GENERATED_PROFILE_NAME,
    SELF_INTERSECTION_ALGORITHM,
    SELF_INTERSECTION_NOT_CHECKED_ALGORITHM,
    ClosedSurfacePart,
    ClosedSurfacePartDiagnostics,
    ClosedVolumeBody,
    ClosedVolumeBodyType,
    ClosedVolumeCapPolicy,
    ClosedVolumeCoordinateSystem,
    ClosedVolumeDeckJoinPolicy,
    ClosedVolumeDiagnostics,
    ClosedVolumePolicy,
    ClosedVolumeReadiness,
    ClosedVolumeReadinessLevel,
    ClosedVolumeSelfIntersectionPair,
    ClosedVolumeSelfIntersectionPolicy,
    ClosedVolumeSelfIntersectionStatus,
    ClosedVolumeTolerances,
    ClosedVolumeTriangleReference,
    ClosedVolumeWaterlineMetadata,
    SelfIntersectionPairClassification,
    explicit_synthetic_self_intersection_policy,
    generated_hull_plus_deck_policy,
)

__all__ = [
    "DEFAULT_DEGENERATE_AREA_TOLERANCE_M2",
    "DEFAULT_GENERATED_CLOSED_BODY_SECTION_POINTS",
    "DEFAULT_GENERATED_CLOSED_BODY_STATIONS",
    "DEFAULT_SELF_INTERSECTION_TOLERANCE_M",
    "DEFAULT_SIGNED_VOLUME_TOLERANCE_M3",
    "DEFAULT_VERTEX_WELD_TOLERANCE_M",
    "GENERATED_CLOSED_BODY_PART_NAME",
    "GENERATED_CLOSED_BODY_TYPE",
    "MAX_SELF_INTERSECTION_EXAMPLE_PAIRS",
    "RFC0016_SYNTHETIC_PROFILE_NAME",
    "RFC0021_SELF_INTERSECTION_PROFILE_NAME",
    "RFC0022_GENERATED_PROFILE_NAME",
    "SELF_INTERSECTION_ALGORITHM",
    "SELF_INTERSECTION_NOT_CHECKED_ALGORITHM",
    "ClosedSurfacePart",
    "ClosedSurfacePartDiagnostics",
    "ClosedVolumeBody",
    "ClosedVolumeBodyType",
    "ClosedVolumeCapPolicy",
    "ClosedVolumeCoordinateSystem",
    "ClosedVolumeDeckJoinPolicy",
    "ClosedVolumeDiagnostics",
    "ClosedVolumePolicy",
    "ClosedVolumeReadiness",
    "ClosedVolumeReadinessLevel",
    "ClosedVolumeSelfIntersectionPair",
    "ClosedVolumeSelfIntersectionPolicy",
    "ClosedVolumeSelfIntersectionStatus",
    "ClosedVolumeTolerances",
    "ClosedVolumeTriangleReference",
    "ClosedVolumeWaterlineMetadata",
    "SelfIntersectionPairClassification",
    "diagnose_closed_volume_body",
    "dispatch_evidence_satisfies_profile",
    "explicit_synthetic_body",
    "explicit_synthetic_self_intersection_policy",
    "generated_hull_plus_deck_body",
    "generated_hull_plus_deck_closed_body",
    "generated_hull_plus_deck_policy",
]
