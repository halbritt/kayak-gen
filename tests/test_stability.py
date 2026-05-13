"""Initial stability load-case contract."""

from __future__ import annotations

import pytest

from kayakgen.eval.contract import EvaluationResult, LoadCase
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.stability import GZNotImplementedError, evaluate_gz_curve, evaluate_initial_stability
from kayakgen.model.hull import Hull


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
