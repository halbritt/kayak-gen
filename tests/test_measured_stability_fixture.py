"""RFC 0056: MeasuredStabilityFixture schema + validator tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from kayakgen.eval.calibration.rights import RightsChecklist
from kayakgen.eval.stability.measured_fixture import (
    CalibrationTrace,
    FreeEquilibriumPoint,
    FreeEquilibriumTrace,
    HullIdentityRef,
    HysteresisBound,
    LoadingConfiguration,
    MeasuredStabilityFixture,
    MeasuredStabilityRow,
    validate_measured_stability_fixture_path,
)


def _hull_identity(**overrides) -> HullIdentityRef:
    defaults = dict(
        manufacturer="Sterling",
        model="Reflection",
        serial_or_year="2017",
        scan_hash="a" * 64,
        scan_method="Artec Eva, 0.1 mm resolution, 1.2 M points",
        hull_class="sea kayak",
        notes=["acquired second-hand; assumed original tooling"],
    )
    defaults.update(overrides)
    return HullIdentityRef(**defaults)


def _loading(**overrides) -> LoadingConfiguration:
    defaults = dict(
        displacement_kg=110.0,
        paddler_state="rigid_manikin",
        paddler_mass_kg=85.0,
        paddler_cg_height_m=0.65,
    )
    defaults.update(overrides)
    return LoadingConfiguration(**defaults)


def _calibration_trace(**overrides) -> CalibrationTrace:
    defaults = dict(
        pre_run_trace_path="cal/pre.csv",
        post_run_trace_path="cal/post.csv",
        dead_weight_kg=5.0,
        measured_arm_pre_m=0.3000,
        measured_arm_post_m=0.3003,
    )
    defaults.update(overrides)
    return CalibrationTrace(**defaults)


def _free_equilibrium_trace(**overrides) -> FreeEquilibriumTrace:
    defaults = dict(
        points=[
            FreeEquilibriumPoint(theta_deg=0, trim_deg=0.0, heave_m=0.0),
            FreeEquilibriumPoint(theta_deg=15, trim_deg=0.5, heave_m=-0.005),
            FreeEquilibriumPoint(theta_deg=30, trim_deg=1.2, heave_m=-0.012),
        ],
    )
    defaults.update(overrides)
    return FreeEquilibriumTrace(**defaults)


def _hysteresis_bound(**overrides) -> HysteresisBound:
    defaults = dict(
        observed_max_fraction=0.018,
        observed_at_theta_deg=22.0,
    )
    defaults.update(overrides)
    return HysteresisBound(**defaults)


def _rights() -> RightsChecklist:
    return RightsChecklist(
        license_identifier="CC BY 4.0",
        attribution="Kayak Lab, 2026",
        source_locator="https://example.org/rig-runs/2026-05",
        redistribution_authorized=True,
        attribution_required=True,
    )


def _rows() -> list[MeasuredStabilityRow]:
    return [
        MeasuredStabilityRow(theta_deg=0, gz_m=0.000, gz_std_m=0.0005),
        MeasuredStabilityRow(theta_deg=15, gz_m=0.045, gz_std_m=0.001),
        MeasuredStabilityRow(theta_deg=30, gz_m=0.062, gz_std_m=0.001),
    ]


def _fixture(**overrides) -> MeasuredStabilityFixture:
    defaults = dict(
        fixture_id="msf-2026-001",
        title="Sterling Reflection — sealed deck — manikin",
        source_citation="Halbritt Lab internal rig, 2026-05",
        rights=_rights(),
        extraction_method="strain_gauged_moment_arm_v1",
        hull_identity=_hull_identity(),
        configuration="sealed_deck",
        loading=_loading(),
        valid_heel_range_deg=(0.0, 30.0),
        rig_design_ref="docs/research/STRAIN_GAUGED_GZ_RIG_DESIGN_2026-05-16.md",
        geometry_manifest_ref="data/stability/scans/sterling_reflection_2017.json",
        calibration_trace=_calibration_trace(),
        free_equilibrium_trace=_free_equilibrium_trace(),
        hysteresis_bound=_hysteresis_bound(),
        rows=_rows(),
        intended_use="validation_candidate",
        non_promotion_reasons=["pilot run; awaiting promotion-review packet"],
    )
    defaults.update(overrides)
    return MeasuredStabilityFixture(**defaults)


# ---------------------------------------------------------------------------


def test_validation_candidate_fixture_round_trips() -> None:
    fixture = _fixture()
    blob = fixture.model_dump_json()
    rebuilt = MeasuredStabilityFixture.model_validate_json(blob)
    assert rebuilt == fixture
    assert rebuilt.is_promoted() is False
    assert rebuilt.gz_max_m() == pytest.approx(0.062, abs=1e-6)


def test_promotion_requires_no_constrained_trace() -> None:
    fixture = _fixture(
        free_equilibrium_trace=_free_equilibrium_trace(constrained_trim=True),
        non_promotion_reasons=[],
    )
    # Validation-candidate is fine.
    assert fixture.intended_use == "validation_candidate"

    with pytest.raises(ValidationError) as exc_info:
        _fixture(
            free_equilibrium_trace=_free_equilibrium_trace(constrained_trim=True),
            intended_use="measured_stability_fixture",
        )
    assert "constrained_trace_blocks_promotion" in str(exc_info.value)


def test_calibration_drift_above_bound_refused() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _calibration_trace(
            measured_arm_pre_m=0.3000,
            measured_arm_post_m=0.3500,  # >0.5% drift
            drift_bound_fraction=0.005,
        )
    assert "calibration_drift_above_bound" in str(exc_info.value)


def test_hysteresis_above_bound_refused() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _hysteresis_bound(observed_max_fraction=0.05, bound_fraction=0.03)
    assert "hysteresis_above_bound" in str(exc_info.value)


def test_paddler_absent_must_be_zero_mass() -> None:
    with pytest.raises(ValidationError):
        _loading(paddler_state="absent", paddler_mass_kg=70.0)


def test_paddler_present_must_have_mass() -> None:
    with pytest.raises(ValidationError):
        _loading(paddler_state="rigid_manikin", paddler_mass_kg=0.0)


def test_hull_identity_scan_hash_must_be_sha256() -> None:
    with pytest.raises(ValidationError):
        _hull_identity(scan_hash="short_hash")
    with pytest.raises(ValidationError):
        _hull_identity(scan_hash="z" * 65)


def test_valid_heel_range_must_be_ordered() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _fixture(valid_heel_range_deg=(30.0, 30.0))
    assert "valid_heel_range_deg requires low < high" in str(exc_info.value)


def test_rows_must_lie_inside_valid_heel_range() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _fixture(
            valid_heel_range_deg=(0.0, 20.0),
            rows=_rows(),  # contains a row at 30 deg
        )
    assert "rows_outside_valid_heel_range" in str(exc_info.value)


def test_validation_candidate_without_reasons_emits_warning() -> None:
    fixture = _fixture(
        intended_use="validation_candidate",
        non_promotion_reasons=[],
    )
    assert "validation_candidate_without_recorded_reasons" in fixture.warnings


def test_intended_use_promotion_requires_explicit_set() -> None:
    """Default for ``intended_use`` is ``validation_candidate``; no auto-promotion."""

    fixture_a = _fixture()
    assert fixture_a.intended_use == "validation_candidate"

    # Explicit promotion works only when the rig run is unconstrained.
    fixture_b = _fixture(intended_use="measured_stability_fixture")
    assert fixture_b.is_promoted() is True


def test_rejected_intended_use_drops_from_comparisons() -> None:
    fixture = _fixture(intended_use="rejected")
    assert fixture.is_promoted() is False
    # Rejected fixtures are preserved on disk but excluded from comparisons.
    # Acceptance is just that the literal value is admitted.


def test_validate_measured_stability_fixture_path_round_trip(
    tmp_path: Path,
) -> None:
    fixture = _fixture()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(fixture.model_dump_json())

    rebuilt = validate_measured_stability_fixture_path(manifest_path)
    assert rebuilt == fixture


def test_validate_measured_stability_fixture_path_refuses_bad_manifest(
    tmp_path: Path,
) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps({"fixture_id": "missing-everything"}))

    with pytest.raises(ValidationError):
        validate_measured_stability_fixture_path(bad_path)


def test_no_fixture_promoted_by_default() -> None:
    """RFC 0056 acceptance criterion: no fixture is promoted by this module."""

    fixture = _fixture()
    assert fixture.intended_use == "validation_candidate"
    assert fixture.is_promoted() is False
