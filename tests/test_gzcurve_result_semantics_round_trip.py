"""Round-trip tests for ``GZCurve.result_semantics`` claim labels (R3 / AUD-P-001).

When stage 4 of RFC 0058 lands a non-empty fit registry, the analytical
claim-label resolver can return ``"validated_hydrostatic_comparison"`` and
``GeneratedBodyGZCurve.result_semantics`` will carry that value. The canonical
parent ``GZCurve`` schema (``StabilityResult.gz_curve: GZCurve | None``) must
accept both labels so a serialized ``GeneratedBodyGZCurve`` round-trips through
``EvaluationResult.model_validate_json(result.model_dump_json())`` without
losing the ``validated_*`` label.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kayakgen.eval.contract import (
    EvaluationResult,
    GZCurve,
    GZHeelPointMetadata,
    LoadCase,
    StabilityResult,
)
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.stability import GeneratedBodyGZCurve
from kayakgen.model.hull import Hull


def _skipped_heel_metadata(heel_deg: float) -> GZHeelPointMetadata:
    return GZHeelPointMetadata(
        heel_deg=heel_deg,
        status="skipped",
        displacement_iterations=0,
        displacement_max_iterations=16,
        clipping_status="skipped",
        warnings=["generated_body_gate_failed"],
    )


def test_generated_body_gz_curve_accepts_validated_label() -> None:
    """Constructing the subclass with the upgraded label must succeed."""

    curve = GeneratedBodyGZCurve(
        status="unavailable",
        method="fixed_trim_generated_body_v1",
        fixture_only=False,
        body_ref="generated/hull-plus-deck/test",
        body_type="generated_hull_plus_deck_closed_body",
        heel_grid_deg=[0.0, 5.0],
        heel_point_metadata=[
            _skipped_heel_metadata(0.0),
            _skipped_heel_metadata(5.0),
        ],
        result_semantics="validated_hydrostatic_comparison",
    )

    assert curve.result_semantics == "validated_hydrostatic_comparison"
    assert curve.summary_semantics == "grid_bounded"


def test_validated_label_round_trips_through_stability_result() -> None:
    """A ``GeneratedBodyGZCurve`` with the validated label survives the parent-class round-trip.

    ``StabilityResult.gz_curve`` is typed as ``GZCurve | None``, so the
    deserializer rehydrates the subclass payload through the parent schema.
    Before this fix the parent ``result_semantics`` Literal only admitted
    ``"unvalidated_hydrostatic_comparison"`` and the round-trip raised a
    Pydantic validation error.
    """

    hull = Hull()
    subclass_curve = GeneratedBodyGZCurve(
        status="unavailable",
        method="fixed_trim_generated_body_v1",
        fixture_only=False,
        body_ref="generated/hull-plus-deck/test",
        body_type="generated_hull_plus_deck_closed_body",
        heel_grid_deg=[0.0, 5.0],
        heel_point_metadata=[
            _skipped_heel_metadata(0.0),
            _skipped_heel_metadata(5.0),
        ],
        result_semantics="validated_hydrostatic_comparison",
    )

    canonical = GZCurve.model_validate(subclass_curve.model_dump())
    assert canonical.result_semantics == "validated_hydrostatic_comparison"

    wrapped = StabilityResult(
        load_case=LoadCase(),
        load_mass_kg=100.0,
        displaced_mass_kg=100.0,
        displacement_error_kg=0.0,
        gz_curve=canonical,
    )
    eval_result = EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=evaluate_hydrostatics(hull),
        stability=wrapped,
    )

    loaded = EvaluationResult.model_validate_json(eval_result.model_dump_json())

    assert loaded == eval_result
    assert loaded.stability is not None
    assert loaded.stability.gz_curve is not None
    assert (
        loaded.stability.gz_curve.result_semantics
        == "validated_hydrostatic_comparison"
    )


def test_gz_curve_rejects_unknown_result_semantics_label() -> None:
    """The parent contract must still refuse non-RFC-0058 labels."""

    with pytest.raises(ValidationError):
        GZCurve(
            status="unavailable",
            result_semantics="bogus_label",  # type: ignore[arg-type]
        )
