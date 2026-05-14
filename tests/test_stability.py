"""Initial stability load-case contract."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kayakgen.eval.closed_volume import (
    ClosedVolumeReadiness,
    diagnose_closed_volume_body,
    explicit_synthetic_body,
    explicit_synthetic_self_intersection_policy,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.contract import (
    EvaluationResult,
    GZCurve,
    LoadCase,
    LongitudinalLoadComponent,
)
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval import stability as stability_eval
from kayakgen.eval.stability import (
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


def _tetrahedron() -> tuple[list[list[float]], list[list[int]]]:
    vertices = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    faces = [
        [0, 2, 1],
        [0, 1, 3],
        [1, 2, 3],
        [2, 0, 3],
    ]
    return vertices, faces


def test_load_case_total_mass_and_round_trip() -> None:
    load = LoadCase(paddler_mass_kg=80, hull_mass_kg=17, cargo_mass_kg=5)
    assert load.total_mass_kg == 102
    assert LoadCase.model_validate_json(load.model_dump_json()) == load


def test_longitudinal_components_round_trip_and_normalize() -> None:
    load = LoadCase(
        components=[
            LongitudinalLoadComponent(name="paddler", mass_kg=80, x_m=-0.20),
            LongitudinalLoadComponent(name="cargo", mass_kg=20, x_m=0.40, kg_above_keel_m=0.15),
        ],
        kg_above_keel_m=0.30,
    )

    loaded = LoadCase.model_validate_json(load.model_dump_json())

    assert loaded == load
    assert loaded.total_mass_kg == 100
    assert loaded.load_lcg_m_for_draft(0.12) == pytest.approx(-0.08)
    assert loaded.load_kg_above_keel_m_for_draft(0.12) == pytest.approx(0.27)


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


def test_high_angle_gz_missing_body_ref_returns_structured_unavailable() -> None:
    result = evaluate_gz_curve(Hull(), LoadCase(), heel_grid_deg=[0.0, 10.0, 20.0])

    assert result.status == "unavailable"
    assert result.fixture_only is False
    assert result.heel_grid_deg == [0.0, 10.0, 20.0]
    assert result.heel_deg == []
    assert result.gz_m == []
    assert result.righting_moment_nm == []
    assert result.max_gz_m is None
    assert result.heel_at_max_gz_deg is None
    assert result.range_positive_stability_deg is None
    assert result.area_under_positive_gz_m_deg is None
    assert "generated_closed_body_not_available" in result.warnings
    assert "body_ref_missing" in result.warnings


def test_high_angle_gz_unresolved_body_ref_does_not_claim_values() -> None:
    result = evaluate_gz_curve(
        Hull(),
        LoadCase(),
        heel_grid_deg=[0.0, 5.0],
        body_ref="mesh-package/open-wetted-surface",
    )

    assert result.status == "unavailable"
    assert result.body_ref == "mesh-package/open-wetted-surface"
    assert result.body_type == "unresolved"
    assert result.gz_m == []
    assert "body_ref_unresolved" in result.warnings


def test_high_angle_gz_rejects_synthetic_body_as_real_kayak_gz() -> None:
    vertices, faces = _tetrahedron()
    body = explicit_synthetic_body(
        vertices,
        faces,
        body_id="synthetic-fixture",
        policy=explicit_synthetic_self_intersection_policy(),
    )

    result = evaluate_gz_curve(
        Hull(),
        LoadCase(),
        heel_grid_deg=[0.0, 10.0, 20.0],
        body_ref=body,
    )

    assert result.status == "unavailable"
    assert result.fixture_only is False
    assert result.body_type == "explicit_synthetic_triangle_mesh"
    assert result.gz_m == []
    assert "synthetic_body_not_allowed_for_real_gz" in result.warnings


def test_fixture_only_gz_curve_round_trips_and_derives_summaries() -> None:
    vertices, faces = _tetrahedron()
    body = explicit_synthetic_body(
        vertices,
        faces,
        body_id="fixture-tetrahedron",
        policy=explicit_synthetic_self_intersection_policy(),
    )
    diagnostics = diagnose_closed_volume_body(body)
    grid = [0.0, 30.0, 60.0, 90.0]

    result = evaluate_gz_curve(
        Hull(),
        LoadCase(paddler_mass_kg=82.0),
        heel_grid_deg=grid,
        body_ref=body,
        body_diagnostics=diagnostics,
        fixture_only=True,
    )
    loaded = GZCurve.model_validate_json(result.model_dump_json())

    assert loaded == result
    assert result.status == "computed"
    assert result.fixture_only is True
    assert result.heel_grid_deg == grid
    assert result.heel_deg == grid
    assert len(result.gz_m) == len(grid)
    assert len(result.righting_moment_nm) == len(grid)
    assert result.max_gz_m == pytest.approx(max(result.gz_m))
    assert result.heel_at_max_gz_deg == pytest.approx(30.0)
    assert result.area_under_positive_gz_m_deg is not None
    assert result.area_under_positive_gz_m_deg > 0.0
    assert "fixture_only" in result.warnings
    assert "not_kayak_stability_evidence" in result.assumptions


def test_fixture_only_open_body_returns_unavailable_without_values() -> None:
    vertices, faces = _tetrahedron()
    body = explicit_synthetic_body(
        vertices,
        faces[:-1],
        body_id="open-fixture",
        policy=explicit_synthetic_self_intersection_policy(),
    )

    result = evaluate_gz_curve(
        Hull(),
        LoadCase(),
        heel_grid_deg=[0.0, 15.0],
        body_ref=body,
        fixture_only=True,
    )

    assert result.status == "unavailable"
    assert result.fixture_only is True
    assert result.gz_m == []
    assert result.max_gz_m is None
    assert "fixture_closed_body_diagnostic_failed" in result.warnings
    assert "closed_volume_readiness_not_closed" in result.warnings


def test_generated_body_gate_passes_but_real_curve_remains_unavailable() -> None:
    hull = Hull(name="gz-generated-pass", bow_rake=0.0, stern_rake=0.0)
    body = generated_hull_plus_deck_body(hull, stations=4)
    diagnostics = diagnose_closed_volume_body(body)

    result = evaluate_gz_curve(
        hull,
        LoadCase(),
        heel_grid_deg=[0.0, 5.0, 10.0],
        body_ref=body,
        body_diagnostics=diagnostics,
    )

    assert result.status == "unavailable"
    assert result.body_ref == body.body_id
    assert result.body_type == "generated_hull_plus_deck_closed_body"
    assert result.gz_m == []
    assert result.max_gz_m is None
    assert "generated_closed_body_diagnostic_gate_passed" in result.assumptions
    assert "high_angle_gz_generated_body_solver_not_implemented" in result.warnings


def test_generated_body_hull_hash_mismatch_returns_unavailable() -> None:
    body_hull = Hull(name="body-source")
    request_hull = Hull(name="different-source")
    body = generated_hull_plus_deck_body(body_hull, stations=4)
    diagnostics = diagnose_closed_volume_body(body)

    result = evaluate_gz_curve(
        request_hull,
        LoadCase(),
        body_ref=body,
        body_diagnostics=diagnostics,
    )

    assert result.status == "unavailable"
    assert result.gz_m == []
    assert "generated_closed_body_not_available" in result.warnings
    assert "source_hull_hash_mismatch" in result.warnings


def test_generated_body_failed_diagnostics_returns_unavailable() -> None:
    hull = Hull(name="failed-diagnostics")
    body = generated_hull_plus_deck_body(hull, stations=4)
    diagnostics = diagnose_closed_volume_body(body).model_copy(
        update={
            "readiness": ClosedVolumeReadiness(
                level="invalid",
                reasons=["forced test failure"],
            )
        }
    )

    result = evaluate_gz_curve(
        hull,
        LoadCase(),
        body_ref=body,
        body_diagnostics=diagnostics,
    )

    assert result.status == "unavailable"
    assert result.gz_m == []
    assert result.max_gz_m is None
    assert "closed_volume_readiness_not_closed" in result.warnings
    assert "closed_volume_readiness_reasons_present" in result.warnings


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [0.0, 10.0, 10.0],
        [0.0, float("nan")],
    ],
)
def test_high_angle_gz_validates_heel_grid(grid: list[float]) -> None:
    with pytest.raises(ValueError, match="heel_grid_deg"):
        evaluate_gz_curve(Hull(), LoadCase(), heel_grid_deg=grid)


def test_gz_curve_rejects_legacy_minimal_payload_without_provenance() -> None:
    with pytest.raises(ValidationError, match="legacy GZCurve"):
        GZCurve.model_validate({"angles_deg": [0.0], "gz_m": [0.0]})


def test_gz_curve_rejects_unavailable_payload_with_values() -> None:
    with pytest.raises(ValidationError, match="unavailable GZ results"):
        GZCurve(
            status="unavailable",
            heel_grid_deg=[0.0],
            heel_deg=[0.0],
            gz_m=[0.0],
            righting_moment_nm=[0.0],
        )


def test_legacy_hydrostatics_null_gz_curve_still_round_trips() -> None:
    hull = Hull()
    result = EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=evaluate_hydrostatics(hull),
    )
    payload = result.model_dump(mode="json")
    payload["hydrostatics"]["gz_curve"] = None

    loaded = EvaluationResult.model_validate(payload)

    assert loaded.hydrostatics.gz_curve is None


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
    assert result.draft_at_midship_m is not None
    assert result.trim_angle_deg == pytest.approx(0.0)
    assert result.load_lcg_m == pytest.approx(0.0)
    assert result.buoyancy_lcb_m == pytest.approx(0.0)
    assert result.moment_error_kg_m == pytest.approx(0.0)
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


def _component_load(mass_kg: float, x_m: float) -> LoadCase:
    return LoadCase(
        name=f"component-{x_m}",
        components=[
            LongitudinalLoadComponent(
                name="test-load",
                mass_kg=mass_kg,
                x_m=x_m,
                kg_above_keel_m=0.25,
            )
        ],
    )


def test_forward_component_lcg_produces_bow_down_trim() -> None:
    result = stability_eval.evaluate_equilibrium_stability(
        Hull(),
        _component_load(90.0, -0.30),
        tolerance_kg=0.2,
        max_iterations=60,
    )

    assert result.method == "equilibrium_trim"
    assert result.status == "converged"
    assert result.trim_angle_deg is not None and result.trim_angle_deg < 0.0
    assert result.load_lcg_m == pytest.approx(-0.30)
    assert result.buoyancy_lcb_m == pytest.approx(result.load_lcg_m, abs=2e-3)
    assert abs(result.displacement_error_kg) <= 0.2
    assert abs(result.moment_error_kg_m or 0.0) <= (result.moment_tolerance_kg_m or 0.0)
    assert "trim_sign_positive_stern_down" in result.warnings
    assert "equilibrium_trim_solved" in result.warnings


def test_aft_component_lcg_produces_stern_down_trim() -> None:
    result = stability_eval.evaluate_equilibrium_stability(
        Hull(),
        _component_load(90.0, 0.30),
        tolerance_kg=0.2,
        max_iterations=60,
    )

    assert result.method == "equilibrium_trim"
    assert result.status == "converged"
    assert result.trim_angle_deg is not None and result.trim_angle_deg > 0.0
    assert result.load_lcg_m == pytest.approx(0.30)
    assert result.buoyancy_lcb_m == pytest.approx(result.load_lcg_m, abs=2e-3)


def test_trim_equilibrium_max_iterations_reports_non_convergence() -> None:
    result = stability_eval.evaluate_equilibrium_stability(
        Hull(),
        _component_load(90.0, 0.30),
        tolerance_kg=0.01,
        moment_tolerance_kg_m=0.001,
        max_iterations=1,
    )

    assert result.method == "equilibrium_trim"
    assert result.status == "not_converged"
    assert result.equilibrium_iterations == 1
    assert "max_iterations_exceeded" in result.warnings


def test_trim_equilibrium_keeps_too_heavy_component_out_of_bracket() -> None:
    result = stability_eval.evaluate_equilibrium_stability(
        Hull(),
        _component_load(1_000.0, 0.20),
        tolerance_kg=0.5,
        max_iterations=20,
    )

    assert result.method == "equilibrium_trim"
    assert result.status == "not_converged"
    assert result.draft_at_midship_m is None
    assert result.trim_angle_deg is None
    assert "equilibrium_mass_out_of_bracket" in result.warnings
