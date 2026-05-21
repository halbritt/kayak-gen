"""Public high-angle GZ entry point and the diagnostic-gate helpers.

``evaluate_gz_curve`` is the RFC 0024 / RFC 0043 result-envelope facade.
This module composes the heel-grid validator, the closed-volume diagnostic
gate, the heeled-section integrator, and the fixture-only math path.
"""

from __future__ import annotations

from collections.abc import Sequence
import math

import numpy as np

from kayakgen.eval.closed_volume import (
    GENERATED_CLOSED_BODY_PART_NAME,
    GENERATED_CLOSED_BODY_TYPE,
    RFC0022_GENERATED_PROFILE_NAME,
    SELF_INTERSECTION_ALGORITHM,
    ClosedVolumeBody,
    ClosedVolumeDiagnostics,
    diagnose_closed_volume_body,
)
from kayakgen.eval.contract import GZCurve, GZHeelPointMetadata, LoadCase
from kayakgen.eval.stability.heeled_section_integrator import (
    GZ_SINKAGE_MAX_ITERATIONS,
    _generated_body_station_sections,
    _solve_generated_body_heel_point,
)
from kayakgen.eval.stability.high_angle_contracts import (
    GeneratedBodyGZCurve,
    _normalize_heel_grid,
    resolve_analytical_claim_label,
)
from kayakgen.eval.stability.load_case import GRAVITY_M_S2
from kayakgen.eval.stability.warnings import (
    GZ_FIXTURE_ASSUMPTIONS,
    GZ_GENERATED_BODY_ASSUMPTIONS,
    GZ_GENERATED_BODY_WARNINGS,
    GZ_UNAVAILABLE_ASSUMPTIONS,
    _dedupe,
)
from kayakgen.model.hull import Hull


def evaluate_gz_curve(
    hull: Hull,
    load_case: LoadCase | None = None,
    heel_grid_deg: Sequence[float] | None = None,
    body_ref: object | None = None,
    body_diagnostics: object | None = None,
    *,
    fixture_only: bool = False,
) -> GZCurve:
    """Return an RFC 0024 GZ result envelope.

    Real kayak GZ values are still unavailable in this slice. Generated closed
    bodies are validated so callers get specific unavailable diagnostics, while
    synthetic explicit bodies can exercise deterministic math only when
    ``fixture_only`` is explicitly set.
    """

    load_case = load_case or LoadCase()
    if load_case.total_mass_kg <= 0:
        raise ValueError("load case total mass must be positive")
    heel_grid = _normalize_heel_grid(heel_grid_deg)

    if body_ref is None:
        return _unavailable_gz_curve(
            heel_grid,
            warnings=["generated_closed_body_not_available", "body_ref_missing"],
        )

    if isinstance(body_ref, str):
        return _unavailable_gz_curve(
            heel_grid,
            body_ref=body_ref,
            body_type="unresolved",
            warnings=[
                "generated_closed_body_not_available",
                "body_ref_unresolved",
                "body_ref_must_be_generated_closed_volume_body",
            ],
        )

    try:
        body = ClosedVolumeBody.model_validate(body_ref)
    except Exception:
        return _unavailable_gz_curve(
            heel_grid,
            body_ref=str(body_ref),
            body_type="unsupported",
            warnings=[
                "generated_closed_body_not_available",
                "body_ref_not_closed_volume_body",
            ],
        )

    diagnostics, diagnostic_warnings = _diagnostics_for_body(body, body_diagnostics)
    diagnostic_ref = _body_diagnostic_ref(diagnostics) if diagnostics else None

    if body.body_type == "explicit_synthetic_triangle_mesh":
        if not fixture_only:
            return _unavailable_gz_curve(
                heel_grid,
                body_ref=body.body_id,
                body_type=body.body_type,
                body_diagnostic_ref=diagnostic_ref,
                warnings=[
                    "generated_closed_body_not_available",
                    "synthetic_body_not_allowed_for_real_gz",
                    *diagnostic_warnings,
                ],
            )
        fixture_warnings = _closed_body_fixture_warnings(body, diagnostics)
        if diagnostic_warnings or fixture_warnings:
            return _unavailable_gz_curve(
                heel_grid,
                body_ref=body.body_id,
                body_type=body.body_type,
                body_diagnostic_ref=diagnostic_ref,
                fixture_only=True,
                warnings=[
                    "fixture_only",
                    "fixture_closed_body_diagnostic_failed",
                    *diagnostic_warnings,
                    *fixture_warnings,
                ],
            )
        assert diagnostics is not None
        return _fixture_gz_curve(
            heel_grid,
            body=body,
            diagnostics=diagnostics,
            load_case=load_case,
        )

    generated_warnings = _generated_body_gz_gate_warnings(hull, body, diagnostics)
    if diagnostic_warnings or generated_warnings:
        return _unavailable_generated_body_gz_curve(
            heel_grid,
            body=body,
            diagnostics=diagnostics,
            heel_point_metadata=_skipped_heel_metadata(
                heel_grid,
                warnings=[
                    "generated_body_gate_failed",
                    *diagnostic_warnings,
                    *generated_warnings,
                ],
            ),
            warnings=[
                "generated_closed_body_not_available",
                *diagnostic_warnings,
                *generated_warnings,
            ],
        )

    assert diagnostics is not None
    return _generated_body_gz_curve(
        heel_grid,
        hull=hull,
        body=body,
        diagnostics=diagnostics,
        load_case=load_case,
    )


def _diagnostics_for_body(
    body: ClosedVolumeBody,
    body_diagnostics: object | None,
) -> tuple[ClosedVolumeDiagnostics | None, list[str]]:
    if body_diagnostics is None:
        try:
            return diagnose_closed_volume_body(body), []
        except Exception as exc:
            return None, [f"closed_volume_diagnostic_unavailable: {exc}"]
    try:
        diagnostics = ClosedVolumeDiagnostics.model_validate(body_diagnostics)
    except Exception as exc:
        return None, [f"closed_volume_diagnostic_invalid: {exc}"]
    return diagnostics, []


def _unavailable_gz_curve(
    heel_grid_deg: list[float],
    *,
    body_ref: str | None = None,
    body_type: str | None = None,
    body_diagnostic_ref: str | None = None,
    fixture_only: bool = False,
    assumptions: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> GZCurve:
    return GZCurve(
        status="unavailable",
        method="fixture_only_math" if fixture_only else "generated_body_handoff",
        fixture_only=fixture_only,
        body_ref=body_ref,
        body_type=body_type,
        body_diagnostic_ref=body_diagnostic_ref,
        heel_grid_deg=list(heel_grid_deg),
        assumptions=_dedupe([*GZ_UNAVAILABLE_ASSUMPTIONS, *assumptions]),
        warnings=_dedupe(warnings),
    )


def _body_diagnostic_ref(diagnostics: ClosedVolumeDiagnostics) -> str:
    return f"closed_volume_diagnostics:{diagnostics.body_id}:{diagnostics.profile_name}"


def _closed_body_fixture_warnings(
    body: ClosedVolumeBody,
    diagnostics: ClosedVolumeDiagnostics | None,
) -> list[str]:
    if diagnostics is None:
        return ["closed_volume_diagnostic_missing"]
    warnings = _closed_volume_readiness_warnings(diagnostics)
    if diagnostics.body_id != body.body_id:
        warnings.append("body_diagnostic_ref_mismatch")
    if diagnostics.body_type != body.body_type:
        warnings.append("body_diagnostic_type_mismatch")
    return warnings


def _generated_body_gz_gate_warnings(
    hull: Hull,
    body: ClosedVolumeBody,
    diagnostics: ClosedVolumeDiagnostics | None,
) -> list[str]:
    warnings: list[str] = []
    if body.body_type != GENERATED_CLOSED_BODY_TYPE:
        warnings.append("body_type_not_generated_hull_plus_deck_closed_body")
    if body.policy.profile_name != RFC0022_GENERATED_PROFILE_NAME:
        warnings.append("generated_body_profile_mismatch")
    if body.policy.body_type != GENERATED_CLOSED_BODY_TYPE:
        warnings.append("generated_body_policy_type_mismatch")
    if body.policy.cap_policy != "explicit_bow_stern_endpoint_ring_caps":
        warnings.append("generated_body_cap_policy_mismatch")
    if body.policy.deck_join_policy != "exact_shared_vertices_topside_sheerline_strip":
        warnings.append("generated_body_deck_join_policy_mismatch")
    if body.policy.self_intersection_policy != "required_rfc0021_conservative":
        warnings.append("generated_body_self_intersection_policy_mismatch")
    if body.policy.normal_orientation != "outward_positive_signed_volume":
        warnings.append("generated_body_normal_orientation_mismatch")
    if body.policy.waterline_semantics != "metadata_only":
        warnings.append("generated_body_waterline_semantics_mismatch")
    if len(body.parts) != 1 or body.parts[0].name != GENERATED_CLOSED_BODY_PART_NAME:
        warnings.append("generated_body_part_identity_mismatch")
    if body.source_hull_hash != hull.hash():
        warnings.append("source_hull_hash_mismatch")

    if diagnostics is None:
        warnings.append("closed_volume_diagnostic_missing")
        return warnings

    warnings.extend(_closed_volume_readiness_warnings(diagnostics))
    if diagnostics.body_id != body.body_id:
        warnings.append("body_diagnostic_ref_mismatch")
    if diagnostics.body_type != body.body_type:
        warnings.append("body_diagnostic_type_mismatch")
    if diagnostics.profile_name != body.policy.profile_name:
        warnings.append("body_diagnostic_profile_mismatch")
    if diagnostics.source_hull_hash != body.source_hull_hash:
        warnings.append("body_diagnostic_source_hull_hash_mismatch")
    if diagnostics.units != body.units:
        warnings.append("body_diagnostic_units_mismatch")
    if diagnostics.coordinate_system != body.coordinate_system:
        warnings.append("body_diagnostic_coordinate_system_mismatch")
    if diagnostics.waterline_z_m != body.waterline_z_m:
        warnings.append("body_diagnostic_waterline_mismatch")
    if diagnostics.waterline_metadata != body.waterline_metadata:
        warnings.append("body_diagnostic_waterline_metadata_mismatch")
    if diagnostics.policy != body.policy:
        warnings.append("body_diagnostic_policy_mismatch")
    if diagnostics.self_intersection_algorithm != SELF_INTERSECTION_ALGORITHM:
        warnings.append("self_intersection_algorithm_mismatch")
    if diagnostics.self_intersection_pair_count != 0:
        warnings.append("self_intersection_pairs_present")
    if diagnostics.part_diagnostics and len(diagnostics.part_diagnostics) == len(body.parts):
        for part, report in zip(body.parts, diagnostics.part_diagnostics, strict=True):
            if report.name != part.name:
                warnings.append("part_diagnostic_name_mismatch")
            if report.vertex_count != len(part.vertices):
                warnings.append("part_diagnostic_vertex_count_mismatch")
            if report.face_count != len(part.faces):
                warnings.append("part_diagnostic_face_count_mismatch")
    else:
        warnings.append("part_diagnostic_count_mismatch")
    return warnings


def _closed_volume_readiness_warnings(
    diagnostics: ClosedVolumeDiagnostics,
) -> list[str]:
    warnings: list[str] = []
    if diagnostics.readiness.level != "closed_volume":
        warnings.append("closed_volume_readiness_not_closed")
    if diagnostics.readiness.reasons:
        warnings.append("closed_volume_readiness_reasons_present")
    for field_name in (
        "raw_boundary_edges",
        "welded_boundary_edges",
        "raw_nonmanifold_edges",
        "welded_nonmanifold_edges",
        "degenerate_faces",
        "nonfinite_vertices",
        "nonfinite_faces",
        "invalid_face_indices",
    ):
        if getattr(diagnostics, field_name) != 0:
            warnings.append(f"{field_name}_nonzero")
    if (
        diagnostics.signed_volume_m3
        <= diagnostics.policy.tolerances.signed_volume_tolerance_m3
    ):
        warnings.append("signed_volume_not_positive_above_tolerance")
    if diagnostics.self_intersection_status != "passed":
        warnings.append(f"self_intersection_status_{diagnostics.self_intersection_status}")
    if diagnostics.cfd_ready is not False:
        warnings.append("closed_volume_diagnostic_must_not_claim_cfd_ready")
    return warnings


def _generated_body_gz_curve(
    heel_grid_deg: list[float],
    *,
    hull: Hull,
    body: ClosedVolumeBody,
    diagnostics: ClosedVolumeDiagnostics,
    load_case: LoadCase,
) -> GeneratedBodyGZCurve:
    try:
        sections = _generated_body_station_sections(body)
    except ValueError as exc:
        metadata = _skipped_heel_metadata(
            heel_grid_deg,
            warnings=[f"generated_body_section_reconstruction_failed: {exc}"],
        )
        return _unavailable_generated_body_gz_curve(
            heel_grid_deg,
            body=body,
            diagnostics=diagnostics,
            heel_point_metadata=metadata,
            assumptions=["generated_closed_body_diagnostic_gate_passed"],
            warnings=[
                "heeled_integration_model_unavailable_for_body",
                "waterline_clipping_failed",
            ],
        )

    heel_deg: list[float] = []
    gz_m: list[float] = []
    righting_moment_nm: list[float] = []
    heel_metadata: list[GZHeelPointMetadata] = []
    for heel in heel_grid_deg:
        gz, moment, metadata = _solve_generated_body_heel_point(
            sections,
            hull=hull,
            load_case=load_case,
            heel_deg=heel,
        )
        heel_metadata.append(metadata)
        if gz is not None and moment is not None and metadata.status == "computed":
            heel_deg.append(heel)
            gz_m.append(gz)
            righting_moment_nm.append(moment)

    if len(heel_deg) != len(heel_grid_deg):
        return _unavailable_generated_body_gz_curve(
            heel_grid_deg,
            body=body,
            diagnostics=diagnostics,
            heel_point_metadata=heel_metadata,
            assumptions=["generated_closed_body_diagnostic_gate_passed"],
            warnings=[
                "heel_point_non_converged",
                "secondary_stability_metrics_hidden_until_all_heel_points_converge",
            ],
        )

    warnings = list(GZ_GENERATED_BODY_WARNINGS)
    if load_case.kg_reference_value_m is not None and load_case.kg_reference != "keel":
        warnings.append("kg_reference_normalized_to_keel")
    result_semantics = resolve_analytical_claim_label(hull, fit_registry=())
    return GeneratedBodyGZCurve(
        status="computed",
        method="fixed_trim_generated_body_v1",
        fixture_only=False,
        body_ref=body.body_id,
        body_type=body.body_type,
        body_diagnostic_ref=_body_diagnostic_ref(diagnostics),
        heel_grid_deg=list(heel_grid_deg),
        heel_deg=heel_deg,
        gz_m=gz_m,
        righting_moment_nm=righting_moment_nm,
        assumptions=_dedupe(
            [
                *GZ_GENERATED_BODY_ASSUMPTIONS,
                "generated_closed_body_diagnostic_gate_passed",
            ]
        ),
        warnings=_dedupe(warnings),
        heel_point_metadata=heel_metadata,
        result_semantics=result_semantics,
        **_gz_summary_metrics(heel_deg, gz_m),
    )


def _skipped_heel_metadata(
    heel_grid_deg: list[float],
    *,
    warnings: Sequence[str],
) -> list[GZHeelPointMetadata]:
    return [
        GZHeelPointMetadata(
            heel_deg=heel,
            status="skipped",
            displacement_iterations=0,
            displacement_max_iterations=GZ_SINKAGE_MAX_ITERATIONS,
            clipping_status="skipped",
            warnings=list(warnings),
        )
        for heel in heel_grid_deg
    ]


def _unavailable_generated_body_gz_curve(
    heel_grid_deg: list[float],
    *,
    body: ClosedVolumeBody,
    diagnostics: ClosedVolumeDiagnostics | None,
    heel_point_metadata: list[GZHeelPointMetadata],
    assumptions: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> GeneratedBodyGZCurve:
    return GeneratedBodyGZCurve(
        status="unavailable",
        method="fixed_trim_generated_body_v1",
        fixture_only=False,
        body_ref=body.body_id,
        body_type=body.body_type,
        body_diagnostic_ref=_body_diagnostic_ref(diagnostics) if diagnostics else None,
        heel_grid_deg=list(heel_grid_deg),
        assumptions=_dedupe(
            [
                *GZ_UNAVAILABLE_ASSUMPTIONS,
                *GZ_GENERATED_BODY_ASSUMPTIONS,
                *assumptions,
            ]
        ),
        warnings=_dedupe([*warnings, *GZ_GENERATED_BODY_WARNINGS]),
        heel_point_metadata=heel_point_metadata,
    )


def _fixture_gz_curve(
    heel_grid_deg: list[float],
    *,
    body: ClosedVolumeBody,
    diagnostics: ClosedVolumeDiagnostics,
    load_case: LoadCase,
) -> GZCurve:
    heel_deg = list(heel_grid_deg)
    gz_m = [0.08 * math.sin(math.radians(2.0 * heel)) for heel in heel_deg]
    righting_moment_nm = [
        load_case.total_mass_kg * GRAVITY_M_S2 * gz for gz in gz_m
    ]
    summaries = _gz_summary_metrics(heel_deg, gz_m)
    return GZCurve(
        status="computed",
        method="fixture_only_math",
        fixture_only=True,
        body_ref=body.body_id,
        body_type=body.body_type,
        body_diagnostic_ref=_body_diagnostic_ref(diagnostics),
        heel_grid_deg=list(heel_grid_deg),
        heel_deg=heel_deg,
        gz_m=gz_m,
        righting_moment_nm=righting_moment_nm,
        assumptions=list(GZ_FIXTURE_ASSUMPTIONS),
        warnings=[
            "fixture_only",
            "synthetic_closed_body_not_generated_kayak",
            "not_user_facing_secondary_stability",
        ],
        summary_semantics="grid_bounded",
        result_semantics="unvalidated_hydrostatic_comparison",
        **summaries,
    )


def _gz_summary_metrics(heel_deg: list[float], gz_m: list[float]) -> dict[str, float | None]:
    if not gz_m:
        return {
            "max_gz_m": None,
            "heel_at_max_gz_deg": None,
            "range_positive_stability_deg": None,
            "area_under_positive_gz_m_deg": None,
        }
    max_index = max(range(len(gz_m)), key=lambda index: gz_m[index])
    positive_indices = [index for index, value in enumerate(gz_m) if value > 1e-12]
    positive_gz = [max(value, 0.0) for value in gz_m]
    return {
        "max_gz_m": gz_m[max_index],
        "heel_at_max_gz_deg": heel_deg[max_index],
        "range_positive_stability_deg": (
            heel_deg[positive_indices[-1]] if positive_indices else None
        ),
        "area_under_positive_gz_m_deg": float(np.trapezoid(positive_gz, heel_deg)),
    }
