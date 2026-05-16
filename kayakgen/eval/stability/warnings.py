"""RFC 0024 warning and assumption constants for stability evaluators.

These tuples are intentionally module-level so that callers can reference the
exact strings in tests and downstream callers without inlining their content.
"""

from __future__ import annotations

from collections.abc import Sequence

GZ_UNAVAILABLE_ASSUMPTIONS: tuple[str, ...] = (
    "cg_model_fixed_to_hull_coordinates_unresolved_for_real_gz",
    "trim_policy_at_heel_unresolved_for_real_gz",
    "deck_immersion_and_flooding_not_modeled",
    "secondary_stability_metrics_hidden_until_generated_body_handoff_passes",
)
GZ_GENERATED_BODY_ASSUMPTIONS: tuple[str, ...] = (
    "fixed_upright_trim_generated_body_v1",
    "hull_fixed_passive_cg",
    "per_heel_sinkage_displacement_solve",
    "closed_waterline_clipping_capping_v1",
    "grid_bounded_summary_metrics",
    "unvalidated_hydrostatic_comparison_curve",
)
GZ_GENERATED_BODY_WARNINGS: tuple[str, ...] = (
    "sealed_deck_profile_no_cockpit_opening",
    "deck_immersion_assumption",
    "flooding_not_modeled",
    "downflooding_not_modeled",
    "active_paddler_response_not_modeled",
    "not_safety_or_seaworthiness_claim",
)
GZ_FIXTURE_ASSUMPTIONS: tuple[str, ...] = (
    "fixture_only_synthetic_righting_arm_math",
    "cg_fixed_to_hull_coordinates_fixture",
    "fixed_upright_trim_fixture",
    "grid_bounded_summary_metrics",
    "not_kayak_stability_evidence",
)


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
