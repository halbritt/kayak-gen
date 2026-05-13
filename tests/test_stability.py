"""Initial stability load-case contract."""

from __future__ import annotations

import pytest

from kayakgen.eval.contract import EvaluationResult, LoadCase
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval import stability as stability_eval
from kayakgen.eval.stability import (
    GZNotImplementedError,
    evaluate_gz_curve,
    evaluate_initial_stability,
)
from kayakgen.model.hull import Hull


def _load_for_equilibrium_draft(
    hull: Hull,
    draft_m: float,
    *,
    seawater_density_kg_m3: float = 1025.0,
) -> LoadCase:
    hydro = evaluate_hydrostatics(hull.model_copy(update={"draft_m": draft_m}))
    total_mass_kg = hydro.displaced_volume_m3 * seawater_density_kg_m3
    return LoadCase(
        paddler_mass_kg=total_mass_kg - 18.0,
        hull_mass_kg=18.0,
        cargo_mass_kg=0.0,
        seawater_density_kg_m3=seawater_density_kg_m3,
    )


def test_load_case_total_mass_and_round_trip() -> None:
    load = LoadCase(paddler_mass_kg=80, hull_mass_kg=17, cargo_mass_kg=5)
    assert load.total_mass_kg == 102
    assert LoadCase.model_validate_json(load.model_dump_json()) == load


def test_default_initial_stability_preserves_hydrostatics_gm0() -> None:
    hull = Hull()
    stability = evaluate_initial_stability(hull)
    hydro = evaluate_hydrostatics(hull)
    assert stability.initial_GM0_m == hydro.GM0_m
    assert "design_waterline_initial_stability_only" in stability.warnings


def test_raising_baseline_kg_lowers_initial_gm0() -> None:
    hull = Hull()
    low = evaluate_initial_stability(hull, LoadCase(kg_above_keel_m=0.20))
    high = evaluate_initial_stability(hull, LoadCase(kg_above_keel_m=0.35))
    assert low.initial_GM0_m is not None
    assert high.initial_GM0_m is not None
    assert high.initial_GM0_m < low.initial_GM0_m


def test_waterline_kg_reference_normalizes_to_keel_height() -> None:
    hull = Hull(draft_m=0.12)
    keel_ref = evaluate_initial_stability(hull, LoadCase(kg_above_keel_m=0.32))
    waterline_ref = evaluate_initial_stability(
        hull,
        LoadCase(
            kg_reference="waterline",
            kg_reference_value_m=0.20,
        ),
    )
    assert waterline_ref.initial_GM0_m == keel_ref.initial_GM0_m
    assert "kg_reference_normalized_to_keel" in waterline_ref.warnings


def test_seat_kg_reference_requires_seat_height() -> None:
    hull = Hull()
    with pytest.raises(ValueError, match="seat-referenced"):
        evaluate_initial_stability(
            hull,
            LoadCase(kg_reference="seat", kg_reference_value_m=0.12),
        )


def test_seat_kg_reference_normalizes_to_keel_height() -> None:
    hull = Hull()
    keel_ref = evaluate_initial_stability(hull, LoadCase(kg_above_keel_m=0.25))
    seat_ref = evaluate_initial_stability(
        hull,
        LoadCase(
            kg_reference="seat",
            kg_reference_value_m=0.05,
            seat_height_above_keel_m=0.20,
        ),
    )
    assert seat_ref.initial_GM0_m == keel_ref.initial_GM0_m


def test_wider_waterline_beam_increases_initial_gm0() -> None:
    narrow = evaluate_initial_stability(Hull(beam_oa_m=0.60, beam_wl_m=0.45))
    wide = evaluate_initial_stability(Hull(beam_oa_m=0.60, beam_wl_m=0.60))
    assert narrow.initial_GM0_m is not None
    assert wide.initial_GM0_m is not None
    assert wide.initial_GM0_m > narrow.initial_GM0_m


def test_evaluation_result_carries_stability_result() -> None:
    hull = Hull()
    result = EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=evaluate_hydrostatics(hull),
        stability=evaluate_initial_stability(hull),
    )
    loaded = EvaluationResult.model_validate_json(result.model_dump_json())
    assert loaded.stability is not None
    assert loaded.stability.load_case.name == "default"


def test_high_angle_gz_is_explicitly_not_implemented() -> None:
    with pytest.raises(GZNotImplementedError):
        evaluate_gz_curve(Hull(), LoadCase())


def test_equilibrium_converges_to_mass_balance_within_tolerance() -> None:
    hull = Hull(draft_m=0.12)
    target_draft_m = 0.135
    load = _load_for_equilibrium_draft(hull, target_draft_m)

    result = stability_eval.evaluate_equilibrium_stability(
        hull,
        load,
        tolerance_kg=0.05,
        max_iterations=80,
    )

    assert result.status == "converged"
    assert result.equilibrium_draft_m == pytest.approx(target_draft_m, abs=5e-4)
    assert abs(result.displacement_error_kg) <= 0.05
    assert result.equilibrium_tolerance_kg == 0.05
    assert 0 < result.equilibrium_iterations <= 80


def test_equilibrium_result_declares_method_status_and_trim_warning() -> None:
    hull = Hull(draft_m=0.12)
    load = _load_for_equilibrium_draft(hull, 0.13)

    result = stability_eval.evaluate_equilibrium_stability(hull, load)

    assert result.method == "equilibrium_sinkage"
    assert result.status == "converged"
    assert result.trim_angle_deg == pytest.approx(0.0)
    assert "generalized_trim_not_implemented" in result.warnings
    assert "high_angle_gz_not_implemented" in result.warnings


def test_equilibrium_waterline_kg_reference_uses_solved_draft() -> None:
    hull = Hull(draft_m=0.12)
    target_draft_m = 0.14
    base_load = _load_for_equilibrium_draft(hull, target_draft_m)
    waterline_load = base_load.model_copy(
        update={
            "kg_reference": "waterline",
            "kg_reference_value_m": 0.10,
        }
    )

    waterline = stability_eval.evaluate_equilibrium_stability(
        hull,
        waterline_load,
        tolerance_kg=0.05,
    )

    assert waterline.equilibrium_draft_m == pytest.approx(target_draft_m, abs=5e-4)
    solved_keel_ref = base_load.model_copy(
        update={
            "kg_above_keel_m": waterline.equilibrium_draft_m + 0.10,
            "kg_reference": "keel",
            "kg_reference_value_m": None,
        }
    )
    solved_keel = stability_eval.evaluate_equilibrium_stability(
        hull,
        solved_keel_ref,
        tolerance_kg=0.05,
    )
    assert waterline.initial_GM0_m == pytest.approx(solved_keel.initial_GM0_m, abs=1e-9)
    assert "kg_reference_normalized_to_keel" in waterline.warnings


def test_equilibrium_out_of_bracket_returns_non_converged_status() -> None:
    result = stability_eval.evaluate_equilibrium_stability(
        Hull(),
        LoadCase(paddler_mass_kg=10_000.0, hull_mass_kg=0.0, cargo_mass_kg=0.0),
        tolerance_kg=0.5,
        max_iterations=20,
    )

    assert result.status == "not_converged"
    assert result.equilibrium_draft_m is None
    assert abs(result.displacement_error_kg) > 0.5
    assert result.equilibrium_iterations == 0
    assert "equilibrium_mass_out_of_bracket" in result.warnings
