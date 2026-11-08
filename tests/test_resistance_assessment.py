"""A declared screening budget never changes requested resistance values."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from kayakgen.eval.numerical_resistance import assess_resistance
from kayakgen.eval.resistance import resistance_curve
from kayakgen.model.hull import Hull


def _hull(number: int = 6) -> Hull:
    path = Path(__file__).parent / f"fixtures/numerical/fast-tourer-{number:02d}.json"
    return Hull.model_validate_json(path.read_text())


def test_refinement_preserves_reported_points_and_exposes_achieved_uncertainty() -> None:
    hull = _hull()
    curve = resistance_curve(
        hull, np.array([4.0, 4.5, 5.0, 5.5, 6.0]), n_stations=400, n_depths=25, n_theta=40
    )
    before = curve.model_dump_json()
    assessment = assess_resistance(hull, curve, 0.01)
    assert curve.model_dump_json() == before
    assert assessment["status"] == "not_converged"
    assert max(assessment["relative_changes"]) > 0.01
    assert len(assessment["observations"]) == 8
    assert len(assessment["input_fingerprint"]) == 64
    assert len(assessment["absolute_uncertainty_N"]) == 5
    assert assessment["observations"][0]["total_resistance_N"] == curve.Rt_N


def test_finer_requested_grid_can_meet_same_declared_budget() -> None:
    hull = _hull()
    curve = resistance_curve(
        hull, np.array([4.0, 4.5, 5.0, 5.5, 6.0]), n_stations=800, n_depths=50, n_theta=80
    )
    assessment = assess_resistance(hull, curve, 0.01)
    assert assessment["status"] == "converged"
    assert max(assessment["relative_changes"]) < 0.01
    assert assessment["speeds_knots"] == curve.V_knots
    assert all(x > 0 for x in assessment["absolute_uncertainty_N"])


def test_numerical_reference_scope_is_explicit_without_dropping_speed_points() -> None:
    hull = _hull()
    curve = resistance_curve(hull, np.array([1.0, 4.0, 6.0]))
    assessment = assess_resistance(hull, curve, 0.01)
    assert assessment["status"] == "unknown"
    assert "outside_numerical_reference_fn_scope" in assessment["evidence"]
    assert assessment["speeds_knots"] == [1.0, 4.0, 6.0]
    assert curve.V_knots == [1.0, 4.0, 6.0]
    assert assessment["absolute_uncertainty_N"] == []


@pytest.mark.parametrize("tolerance", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_declared_budget_is_refused(tolerance: float) -> None:
    hull = _hull()
    curve = resistance_curve(hull, np.array([5.0]))
    with pytest.raises(ValueError, match="finite and positive"):
        assess_resistance(hull, curve, tolerance)


def test_public_curve_budget_attaches_exact_speed_bound_evidence() -> None:
    speeds = np.array([4.0, 5.0, 6.0])
    curve = resistance_curve(
        _hull(8), speeds, n_stations=400, n_depths=25, n_theta=40, numerical_relative_tolerance=0.01
    )
    evidence = curve.metadata.numerical_quality
    assert evidence.status == "converged"
    assert evidence.speeds_knots == speeds.tolist()
    assert evidence.observations[0].total_resistance_N == curve.Rt_N
    assert [o.stations for o in evidence.surface_observations] == [60, 120, 240]
    assert evidence.surface_observations[0].viscous_resistance_N == curve.Rv_N
    assert all(value > 0 for value in evidence.viscous_uncertainty_N)
    assert all(
        total > viscous
        for total, viscous in zip(
            evidence.absolute_uncertainty_N, evidence.viscous_uncertainty_N, strict=True
        )
    )
    assert curve.metadata.numerical_method_version == "michell_linear_depth_v2"
    assert curve.metadata.model_version is None

    from pydantic import ValidationError
    from kayakgen.eval.contract import ResistanceCurve

    contradictory = curve.model_dump(mode="json")
    contradictory["metadata"]["numerical_quality"]["absolute_uncertainty_N"][0] *= 2
    with pytest.raises(ValidationError, match="relative and absolute uncertainty must agree"):
        ResistanceCurve.model_validate(contradictory)


def test_assessment_schema_rejects_relabelled_speed_grid() -> None:
    from pydantic import ValidationError
    from kayakgen.eval.contract import ResistanceCurve

    curve = resistance_curve(_hull(8), np.array([5.0]), numerical_relative_tolerance=0.01)
    payload = curve.model_dump(mode="json")
    payload["metadata"]["numerical_quality"]["speeds_knots"] = [5.5]
    with pytest.raises(ValidationError, match="exact requested speed grid"):
        ResistanceCurve.model_validate(payload)


def test_owner_close_pair_is_unresolved_while_wider_pair_separates() -> None:
    from kayakgen.search.pareto import CandidatePoint, Objective, dominates

    def measured(number: int, speed: float) -> CandidatePoint:
        curve = resistance_curve(
            _hull(number),
            np.array([speed]),
            n_stations=400,
            n_depths=25,
            n_theta=40,
            numerical_relative_tolerance=0.01,
        )
        assert curve.metadata.numerical_quality.status == "converged"
        return CandidatePoint(
            id=str(number),
            metrics={"Rt_N_last": curve.Rt_N[-1]},
            provenance={
                "Rt_N_last": {
                    "numerical_quality": curve.metadata.numerical_quality.model_dump(mode="json")
                }
            },
        )

    objectives = [Objective(metric="Rt_N_last", direction="min")]
    a, b = measured(6, 4.0), measured(18, 4.0)
    assert not dominates(a, b, objectives)
    assert not dominates(b, a, objectives)
    a, b = measured(6, 5.0), measured(8, 5.0)
    assert dominates(a, b, objectives) or dominates(b, a, objectives)


def test_grid_below_recorded_study_scope_stays_diagnostic() -> None:
    curve = resistance_curve(
        _hull(),
        np.array([5.0]),
        n_stations=100,
        n_depths=10,
        n_theta=20,
        numerical_relative_tolerance=0.01,
    )
    assert curve.metadata.numerical_quality.status == "unknown"
    assert "resolution_scope" in curve.metadata.numerical_quality.evidence
    assert curve.Rt_N[0] > 0


def test_assessment_binds_actual_fluid_and_fixed_body_pose() -> None:
    from kayakgen.model.operating_state import OperatingPose

    hull = _hull(8)
    speeds = np.array([5.0])
    plain = resistance_curve(
        hull, speeds, n_stations=400, n_depths=25, n_theta=40, numerical_relative_tolerance=0.01
    )
    posed = resistance_curve(
        hull,
        speeds,
        n_stations=400,
        n_depths=25,
        n_theta=40,
        pose=OperatingPose(0.005, 0.2),
        rho=1000.0,
        nu=1.4e-6,
        numerical_relative_tolerance=0.01,
    )
    quality = posed.metadata.numerical_quality
    assert quality.status in {"converged", "not_converged"}
    assert quality.observations[0].total_resistance_N == posed.Rt_N
    assert quality.input_fingerprint != plain.metadata.numerical_quality.input_fingerprint
    assert posed.metadata.constants["seawater_density_kg_m3"] == 1000.0
    assert posed.metadata.constants["seawater_kinematic_viscosity_m2_s"] == 1.4e-6
    wrong_pose = assess_resistance(hull, posed, 0.01)
    assert wrong_pose["status"] == "unknown"
    assert wrong_pose["evidence"] == "reported_viscous_values_do_not_match_assessed_inputs"


def test_scope_uses_actual_speed_instead_of_relabelled_froude_number() -> None:
    hull = _hull(8)
    curve = resistance_curve(hull, np.array([10.0]), n_stations=400, n_depths=25, n_theta=40)
    assert curve.Fn[0] > 0.5
    curve.Fn = [0.3]
    evidence = assess_resistance(hull, curve, 1.0)
    assert evidence["status"] == "unknown"
    assert evidence["evidence"] == "reported_fn_does_not_match_assessed_inputs"
    assert evidence["observations"] == []


@pytest.fixture(scope="module")
def bound_assessment_curve():
    return resistance_curve(
        _hull(8),
        np.array([5.0]),
        n_stations=400,
        n_depths=25,
        n_theta=40,
        numerical_relative_tolerance=0.01,
    )


@pytest.mark.parametrize("change", ["total", "viscous", "viscosity", "method", "quadrature", "fn"])
def test_serialized_assessment_cannot_survive_changed_curve_inputs(
    bound_assessment_curve, change
) -> None:
    from pydantic import ValidationError
    from kayakgen.eval.contract import ResistanceCurve

    payload = bound_assessment_curve.model_dump(mode="json")
    if change == "total":
        payload["Rt_N"][0] += 1000
    elif change == "viscous":
        payload["Rv_N"][0] += 1
    elif change == "viscosity":
        payload["metadata"]["constants"]["seawater_kinematic_viscosity_m2_s"] = 2e-6
    elif change == "method":
        payload["metadata"]["numerical_method_version"] = "depth_trapezoid_v1"
    elif change == "quadrature":
        payload["metadata"]["quadrature"]["n_stations"] = 401
    else:
        payload["Fn"] = [0.3]
    with pytest.raises(ValidationError):
        ResistanceCurve.model_validate(payload)


@pytest.mark.parametrize(
    "change",
    ["zero_error", "reference_allowance", "scope", "floor", "wave_observation", "surface_level"],
)
def test_published_policy_cannot_undercount_or_reinterpret_retained_evidence(
    bound_assessment_curve, change
) -> None:
    from pydantic import ValidationError
    from kayakgen.eval.contract import ResistanceCurve

    payload = bound_assessment_curve.model_dump(mode="json")
    quality = payload["metadata"]["numerical_quality"]
    if change == "zero_error":
        quality["absolute_uncertainty_N"] = [0.0]
        quality["relative_changes"] = [0.0]
    elif change == "reference_allowance":
        quality["reference_relative_allowance"] = 0.0
    elif change == "scope":
        quality["reference_fn_range"] = [0.0, 1.0]
    elif change == "floor":
        quality["reference_resolution_floor"]["n_stations"] = 100
    elif change == "wave_observation":
        quality["observations"][3]["total_resistance_N"][0] += 1.0
    else:
        quality["surface_observations"][2]["stations"] = 241
    with pytest.raises(ValidationError):
        ResistanceCurve.model_validate(payload)
