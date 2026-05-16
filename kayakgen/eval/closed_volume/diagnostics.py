"""Body-level closed-volume diagnostics and dispatch helpers.

This module composes the topology and self-intersection layers into the
single :func:`diagnose_closed_volume_body` entry point that callers use to
turn a :class:`ClosedVolumeBody` into a :class:`ClosedVolumeDiagnostics`
record. It also owns the safe-slice dispatch validator used by CFD
evidence routing.
"""

from __future__ import annotations

from kayakgen.eval.closed_volume.schemas import (
    ClosedSurfacePartDiagnostics,
    ClosedVolumeBody,
    ClosedVolumeDiagnostics,
    ClosedVolumePolicy,
    ClosedVolumeReadiness,
    ClosedVolumeSelfIntersectionStatus,
    _policy_requires_self_intersection,
)
from kayakgen.eval.closed_volume.self_intersection import (
    _diagnose_self_intersections,
)
from kayakgen.eval.closed_volume.topology import (
    _ArrayDiagnostics,
    _assemble_parts_with_refs,
    _diagnose_arrays,
    _diagnose_part,
    _signed_volume,
)


def diagnose_closed_volume_body(body: ClosedVolumeBody) -> ClosedVolumeDiagnostics:
    """Diagnose a closed-volume body at part and assembled-body levels."""

    if body.policy.body_type != body.body_type:
        raise ValueError("policy body_type must match body body_type")

    part_reports = [_diagnose_part(part, body.policy.tolerances) for part in body.parts]
    vertices, faces, face_refs = _assemble_parts_with_refs(body.parts)
    body_report = _diagnose_arrays(vertices, faces, body.policy.tolerances)
    signed_volume = _signed_volume(vertices, body_report.valid_faces)
    self_intersections = _diagnose_self_intersections(
        vertices,
        body_report.valid_faces,
        [face_refs[int(index)] for index in body_report.valid_face_indices],
        body.policy,
    )

    reasons = _readiness_reasons(
        body_report,
        signed_volume,
        body.policy,
        self_intersections.status,
    )
    readiness = ClosedVolumeReadiness(
        level="invalid" if reasons else "closed_volume",
        reasons=reasons,
    )
    warnings = list(reasons)
    if self_intersections.status == "not_checked":
        warnings.append(
            "self-intersection diagnostic not checked under RFC 0016 compatibility profile"
        )
    if readiness.level == "closed_volume":
        if body.body_type == "explicit_synthetic_triangle_mesh":
            warnings.append("closed-volume synthetic diagnostic only; not cfd_ready")
        else:
            warnings.append(
                "closed-volume generated evaluation body diagnostic only; not cfd_ready"
            )

    return ClosedVolumeDiagnostics(
        body_id=body.body_id,
        body_type=body.body_type,
        profile_name=body.policy.profile_name,
        source_hull_hash=body.source_hull_hash,
        units=body.units,
        coordinate_system=body.coordinate_system,
        waterline_z_m=body.waterline_z_m,
        waterline_metadata=body.waterline_metadata,
        policy=body.policy,
        readiness=readiness,
        part_diagnostics=[
            ClosedSurfacePartDiagnostics(
                name=part.name,
                vertex_count=report.vertex_count,
                face_count=report.face_count,
                raw_boundary_edges=report.raw_boundary_edges,
                raw_nonmanifold_edges=report.raw_nonmanifold_edges,
                welded_boundary_edges=report.welded_boundary_edges,
                welded_nonmanifold_edges=report.welded_nonmanifold_edges,
                degenerate_faces=report.degenerate_faces,
                nonfinite_vertices=report.nonfinite_vertices,
                nonfinite_faces=report.nonfinite_faces,
                invalid_face_indices=report.invalid_face_indices,
            )
            for part, report in zip(body.parts, part_reports, strict=True)
        ],
        vertex_count=body_report.vertex_count,
        face_count=body_report.face_count,
        raw_boundary_edges=body_report.raw_boundary_edges,
        raw_nonmanifold_edges=body_report.raw_nonmanifold_edges,
        welded_boundary_edges=body_report.welded_boundary_edges,
        welded_nonmanifold_edges=body_report.welded_nonmanifold_edges,
        degenerate_faces=body_report.degenerate_faces,
        nonfinite_vertices=body_report.nonfinite_vertices,
        nonfinite_faces=body_report.nonfinite_faces,
        invalid_face_indices=body_report.invalid_face_indices,
        signed_volume_m3=signed_volume,
        self_intersection_status=self_intersections.status,
        self_intersection_algorithm=self_intersections.algorithm,
        self_intersection_tolerance_m=self_intersections.tolerance_m,
        self_intersection_pair_count=self_intersections.pair_count,
        self_intersection_example_pairs=self_intersections.example_pairs,
        warnings=warnings,
    )


def dispatch_evidence_satisfies_profile(
    evidence: object,
    required_mesh_profile: str | None,
    required_mesh_readiness: str,
) -> bool:
    """Return whether this safe-slice evidence can satisfy CFD dispatch.

    Workflow 0027 deliberately never promotes synthetic closed-volume
    diagnostics to ``cfd_ready``. The validator still parses the evidence so
    dispatch code can distinguish contract-aware rejection from blind manifest
    trust.
    """

    diagnostics = ClosedVolumeDiagnostics.model_validate(evidence)
    if required_mesh_profile and diagnostics.profile_name != required_mesh_profile:
        return False
    if required_mesh_readiness == "cfd_ready":
        return False
    return False


def _readiness_reasons(
    report: _ArrayDiagnostics,
    signed_volume: float,
    policy: ClosedVolumePolicy,
    self_intersection_status: ClosedVolumeSelfIntersectionStatus,
) -> list[str]:
    reasons: list[str] = []
    if report.nonfinite_vertices:
        reasons.append("body contains non-finite vertices")
    if report.nonfinite_faces:
        reasons.append("body contains non-finite face indices")
    if report.invalid_face_indices:
        reasons.append("body contains out-of-range face indices")
    if report.degenerate_faces:
        reasons.append("body contains degenerate faces")
    if report.raw_boundary_edges or report.welded_boundary_edges:
        reasons.append("body has boundary edges and is not closed")
    if report.raw_nonmanifold_edges or report.welded_nonmanifold_edges:
        reasons.append("body has non-manifold edges")
    if signed_volume <= policy.tolerances.signed_volume_tolerance_m3:
        reasons.append("body signed volume is not positive with outward normals")
    if _policy_requires_self_intersection(policy) and self_intersection_status != "passed":
        reasons.append(
            f"body self-intersection diagnostic status is {self_intersection_status}"
        )
    return reasons
