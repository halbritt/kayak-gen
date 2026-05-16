"""Initial stability and load-case helpers.

This package exposes design-waterline initial stability, the legacy centered
sinkage-equilibrium mode, and a bounded fixed-body upright trim slice for
explicit longitudinal load components. The high-angle GZ boundary now returns
an RFC 0024 result envelope, but real kayak curves remain unavailable unless a
generated closed body passes diagnostics and a later heeled-volume solver lands.

The implementation is split into sibling modules — ``load_case``, ``initial``,
``upright_equilibrium``, ``trim_equilibrium``, ``high_angle_contracts``,
``heeled_section_integrator``, ``warnings``, and ``evaluator`` — but every
name historically importable from ``kayakgen.eval.stability`` continues to be
re-exported here for byte-stable public imports.
"""

from __future__ import annotations

from kayakgen.eval.stability.evaluator import (
    _body_diagnostic_ref,
    _closed_body_fixture_warnings,
    _closed_volume_readiness_warnings,
    _diagnostics_for_body,
    _fixture_gz_curve,
    _generated_body_gz_curve,
    _generated_body_gz_gate_warnings,
    _gz_summary_metrics,
    _skipped_heel_metadata,
    _unavailable_generated_body_gz_curve,
    _unavailable_gz_curve,
    evaluate_gz_curve,
)
from kayakgen.eval.stability.heeled_section_integrator import (
    GZ_SINKAGE_MAX_ITERATIONS,
    GZ_SINKAGE_TOLERANCE_KG,
    GZ_SINKAGE_WATERLINE_TOLERANCE_M,
    _generated_body_station_sections,
    _heel_section,
    _heeled_displacement_state,
    _heeled_z_bounds,
    _load_cg_for_gz,
    _solve_generated_body_heel_point,
)
from kayakgen.eval.stability.high_angle_contracts import (
    DEFAULT_GZ_HEEL_GRID_DEG,
    GZ_HEEL_GRID_MAX_DEG,
    GZ_HEEL_GRID_MIN_DEG,
    GeneratedBodyGZCurve,
    GZNotImplementedError,
    _normalize_heel_grid,
)
from kayakgen.eval.stability.initial import evaluate_initial_stability
from kayakgen.eval.stability.load_case import (
    COMPAT_KG_ABOVE_KEEL_M,
    GRAVITY_M_S2,
    _gm0_for_load_case,
    _mass_for_load_case,
)
from kayakgen.eval.stability.trim_equilibrium import (
    DEFAULT_MAX_TRIM_ANGLE_DEG,
    TRIM_DRAFT_TOLERANCE_M,
    TRIM_STATIONS,
    _clip_section_to_waterline,
    _clipped_section_area,
    _clipped_section_properties,
    _evaluate_trim_equilibrium,
    _polygon_area,
    _section_area_centroid,
    _solve_midship_draft_for_trim,
    _trim_hydrostatic_state,
)
from kayakgen.eval.stability.upright_equilibrium import (
    DEFAULT_EQUILIBRIUM_MAX_ITERATIONS,
    DEFAULT_EQUILIBRIUM_TOLERANCE_KG,
    EQUILIBRIUM_DRAFT_TOLERANCE_M,
    evaluate_equilibrium_stability,
)
from kayakgen.eval.stability.warnings import (
    GZ_FIXTURE_ASSUMPTIONS,
    GZ_GENERATED_BODY_ASSUMPTIONS,
    GZ_GENERATED_BODY_WARNINGS,
    GZ_UNAVAILABLE_ASSUMPTIONS,
    _dedupe,
)

__all__ = [
    "COMPAT_KG_ABOVE_KEEL_M",
    "DEFAULT_EQUILIBRIUM_MAX_ITERATIONS",
    "DEFAULT_EQUILIBRIUM_TOLERANCE_KG",
    "DEFAULT_GZ_HEEL_GRID_DEG",
    "DEFAULT_MAX_TRIM_ANGLE_DEG",
    "EQUILIBRIUM_DRAFT_TOLERANCE_M",
    "GRAVITY_M_S2",
    "GZ_FIXTURE_ASSUMPTIONS",
    "GZ_GENERATED_BODY_ASSUMPTIONS",
    "GZ_GENERATED_BODY_WARNINGS",
    "GZ_HEEL_GRID_MAX_DEG",
    "GZ_HEEL_GRID_MIN_DEG",
    "GZ_SINKAGE_MAX_ITERATIONS",
    "GZ_SINKAGE_TOLERANCE_KG",
    "GZ_SINKAGE_WATERLINE_TOLERANCE_M",
    "GZ_UNAVAILABLE_ASSUMPTIONS",
    "GeneratedBodyGZCurve",
    "GZNotImplementedError",
    "TRIM_DRAFT_TOLERANCE_M",
    "TRIM_STATIONS",
    "evaluate_equilibrium_stability",
    "evaluate_gz_curve",
    "evaluate_initial_stability",
    # Private symbols re-exported for byte-stable import compatibility with the
    # pre-split single-module ``kayakgen.eval.stability``.
    "_body_diagnostic_ref",
    "_clip_section_to_waterline",
    "_clipped_section_area",
    "_clipped_section_properties",
    "_closed_body_fixture_warnings",
    "_closed_volume_readiness_warnings",
    "_dedupe",
    "_diagnostics_for_body",
    "_evaluate_trim_equilibrium",
    "_fixture_gz_curve",
    "_generated_body_gz_curve",
    "_generated_body_gz_gate_warnings",
    "_generated_body_station_sections",
    "_gm0_for_load_case",
    "_gz_summary_metrics",
    "_heel_section",
    "_heeled_displacement_state",
    "_heeled_z_bounds",
    "_load_cg_for_gz",
    "_mass_for_load_case",
    "_normalize_heel_grid",
    "_polygon_area",
    "_section_area_centroid",
    "_skipped_heel_metadata",
    "_solve_generated_body_heel_point",
    "_solve_midship_draft_for_trim",
    "_trim_hydrostatic_state",
    "_unavailable_generated_body_gz_curve",
    "_unavailable_gz_curve",
]
