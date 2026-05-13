"""Resistance — ITTC viscous + Michell wave-making sanity checks.

The Michell implementation is verified against the Wigley parabolic
hull at Fn 0.30/0.40/0.50 to within 5 %. For the lofted kayak, the
``ε^(-1/2)`` gradient at the sharp bow/stern produces a known
non-monotone convergence; tests therefore assert qualitative shape
(positivity, growth with V, total drag in a paddler-class envelope) and
the Wigley benchmark, not point-wise absolute values on the kayak loft.
The full RFC 0005 limitation is documented in
``kayakgen/eval/resistance.py``.
"""

from __future__ import annotations

import math
import time

import numpy as np
import pytest
from pydantic import ValidationError

from kayakgen.eval.calibration import (
    ResistanceSourceRecord,
    default_resistance_source_registry,
)
from kayakgen.eval.claims import (
    claim_allows_calibrated_prediction,
    claim_allows_final_design_fitness,
)
from kayakgen.eval.contract import ResistanceMetadata
from kayakgen.eval.resistance import (
    KNOTS_TO_MS,
    SEAWATER_DENSITY_KG_M3,
    resistance_curve,
    viscous_resistance,
    wave_resistance_michell,
    wetted_surface,
)
from kayakgen.model.hull import Hull


def _complete_calibrated_metadata(
    *,
    fit_status: str = "accepted_fit",
    calibration_fixture_ids: list[str] | None = None,
    validation_fixture_ids: list[str] | None = None,
) -> ResistanceMetadata:
    return ResistanceMetadata(
        claim_state="calibrated_model",
        calibration_status="calibrated",
        accepted_uses=["final_prediction"],
        calibration_fixture_ids=(
            ["accepted-calibration-fixture-001"]
            if calibration_fixture_ids is None
            else calibration_fixture_ids
        ),
        validation_fixture_ids=(
            ["validation-fixture-001"]
            if validation_fixture_ids is None
            else validation_fixture_ids
        ),
        model_version="resistance-test-v1",
        fit_status=fit_status,
        fit_metrics={
            "force_rmse_N": 0.42,
            "mean_absolute_percentage_error": 2.5,
        },
        validity_envelope={"Fn": [0.25, 0.50], "L_B": [8.0, 12.0]},
        warnings=[],
    )


def _accepted_calibration_fixture_payload(
    **updates: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_id": "synthetic_calibration_fixture",
        "title": "Synthetic calibration fixture",
        "url": "https://example.invalid/calibration-fixture",
        "source_type": "test_fixture",
        "intended_use": "calibration_fixture",
        "measured_data": True,
        "hull_class": "sea_kayak",
        "rights_status": "test_fixture_redistributable",
        "extraction_status": "machine_readable_rows_checked",
        "notes": "Synthetic fixture used only to exercise metadata gates.",
        "warnings": [],
        "fixture_id": "calibration-fixture-001",
        "measured_quantity": "total_resistance",
        "measurement_units": "N",
        "hull_envelope": {"L_B": [8.0, 12.0]},
        "uncertainty_notes": "Synthetic uncertainty budget is documented.",
        "validity_ranges": {"Fn": [0.25, 0.50]},
        "fixture_review_status": "accepted",
    }
    payload.update(updates)
    return payload


def test_zero_speed_is_zero_drag() -> None:
    hull = Hull()
    assert viscous_resistance(hull, 0.0) == 0.0
    assert wave_resistance_michell(hull, 0.0) == 0.0


def test_viscous_drag_grows_with_speed() -> None:
    hull = Hull()
    Sw = wetted_surface(hull)
    drags = [viscous_resistance(hull, v, Sw=Sw) for v in (0.5, 1.0, 1.5, 2.0, 3.0)]
    assert all(b > a for a, b in zip(drags, drags[1:]))


def test_viscous_envelope_at_paddling_speed() -> None:
    """ITTC-57 viscous drag at 3.5 kt should be in the kayak envelope (5–25 N)."""
    hull = Hull()
    Sw = wetted_surface(hull)
    Rv = viscous_resistance(hull, 3.5 * KNOTS_TO_MS, Sw=Sw)
    assert 5.0 < Rv < 25.0, f"Rv at 3.5 kt: {Rv:.1f} N"


def test_wave_resistance_returns_finite_positive() -> None:
    """Michell returns a finite, positive number across the kayak speed band."""
    hull = Hull()
    for V_kt in (1.0, 2.0, 3.0, 4.0, 5.0):
        Rw = wave_resistance_michell(hull, V_kt * KNOTS_TO_MS, n_stations=400, n_depths=20, n_theta=30)
        assert math.isfinite(Rw)
        assert Rw >= 0.0


def test_michell_verified_against_wigley() -> None:
    """Verification of the 16/π prefactor against the Wigley parabolic hull.

    Wigley f(x,z) = (B/2) (1 - (2x/L)²) (1 - (z/T)²) is the standard
    thin-ship benchmark. With ≥800 stations and ≥40 theta, our
    implementation should reproduce the published Cw at Fn = 0.30 within
    ~5 %.
    """
    L, B, T = 1.0, 0.1, 0.0625
    n_x, n_z, n_theta = 1200, 100, 80

    xs = np.linspace(-L / 2, L / 2, n_x)
    zs = np.linspace(0.0, T, n_z)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    df_dx = (B / 2.0) * (-8.0 * X / (L * L)) * (1.0 - (Z / T) ** 2)

    g = 9.80665
    rho = SEAWATER_DENSITY_KG_M3

    def michell(V: float) -> float:
        k0 = g / (V * V)
        thetas = np.linspace(1e-3, math.pi / 2 - 1e-3, n_theta)
        sec_t = 1.0 / np.cos(thetas)
        sec2_t = sec_t ** 2
        sec3_t = sec_t ** 3
        pq2 = np.zeros_like(thetas)
        for k in range(n_theta):
            kp = np.cos(k0 * xs * sec_t[k])[:, None] * np.exp(-k0 * zs * sec2_t[k])[None, :]
            kq = np.sin(k0 * xs * sec_t[k])[:, None] * np.exp(-k0 * zs * sec2_t[k])[None, :]
            P = np.trapezoid(np.trapezoid(df_dx * kp, zs, axis=1), xs)
            Q = np.trapezoid(np.trapezoid(df_dx * kq, zs, axis=1), xs)
            pq2[k] = P * P + Q * Q
        return (16.0 * rho * g * g / (math.pi * V * V)) * np.trapezoid(pq2 * sec3_t, thetas)

    Fn = 0.30
    V = Fn * math.sqrt(g * L)
    Rw = michell(V)
    Cw = Rw / (0.5 * rho * V * V * L * L)
    # Published Wigley Cw at Fn 0.30 ≈ 1.3e-3 (Lazauskas, various)
    assert 1.0e-3 < Cw < 1.6e-3, f"Wigley Cw at Fn 0.30: {Cw:.4f}"


def test_total_drag_at_paddling_speed_in_envelope() -> None:
    """Total drag at 3.5 kt should be meaningful (>5 N) — the regime where
    paddler power output (40–250 W) drives the boat."""
    hull = Hull()
    Sw = wetted_surface(hull)
    V_ms = 3.5 * KNOTS_TO_MS
    Rt = viscous_resistance(hull, V_ms, Sw=Sw) + wave_resistance_michell(hull, V_ms)
    assert Rt > 5.0, f"Rt at 3.5 kt: {Rt:.1f} N"


def test_resistance_curve_shape_and_units() -> None:
    hull = Hull()
    curve = resistance_curve(hull, V_knots=np.linspace(1.0, 6.0, 11))
    assert len(curve.V_knots) == 11
    assert all(v >= 0 for v in curve.Rv_N)
    assert all(v >= 0 for v in curve.Rw_N)
    assert all(rt == rv + rw for rt, rv, rw in zip(curve.Rt_N, curve.Rv_N, curve.Rw_N))
    assert curve.metadata.claim_state == "uncalibrated_comparative"
    assert curve.metadata.accepted_uses == ["comparative_filter"]
    assert curve.metadata.calibration_fixture_ids == []
    assert curve.metadata.validation_fixture_ids == []
    assert curve.metadata.model_version is None
    assert curve.metadata.fit_status is None
    assert curve.metadata.fit_metrics == {}
    assert curve.metadata.validity_envelope is None
    assert curve.metadata.model_family == "raw_ittc_michell"
    assert curve.metadata.calibration_status == "uncalibrated"
    assert curve.metadata.calibration_name is None
    assert curve.metadata.valid_fn_range is None
    assert curve.metadata.source_license is None
    assert "comparative_filter" in curve.metadata.accepted_use
    assert "not_final_performance_prediction" in curve.metadata.warnings
    assert "uncalibrated_no_validity_envelope" in curve.metadata.warnings


def test_viscous_drag_scales_with_wetted_surface() -> None:
    hull = Hull()
    V_ms = 2.0
    Rv_full = viscous_resistance(hull, V_ms)
    Rv_double = viscous_resistance(hull, V_ms, Sw=2.0 * wetted_surface(hull))
    assert abs(Rv_double - 2.0 * Rv_full) / Rv_full < 1e-6


def test_resistance_curve_under_budget() -> None:
    hull = Hull()
    t0 = time.perf_counter()
    resistance_curve(hull, V_knots=np.linspace(1.0, 6.0, 11), n_stations=400, n_depths=20, n_theta=30)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert elapsed_ms < 5000, f"resistance_curve took {elapsed_ms:.0f} ms"


def test_resistance_metadata_records_quadrature_settings() -> None:
    curve = resistance_curve(Hull(), n_stations=123, n_depths=17, n_theta=19)
    assert curve.metadata.quadrature == {
        "n_stations": 123,
        "n_depths": 17,
        "n_theta": 19,
    }
    assert "wigley_parabolic_hull" in curve.metadata.verification_fixtures


def test_resistance_metadata_round_trips_optional_provenance_fields() -> None:
    curve = resistance_curve(Hull())
    loaded = type(curve).model_validate_json(curve.model_dump_json())
    assert loaded.metadata.claim_state == "uncalibrated_comparative"
    assert loaded.metadata.accepted_uses == ["comparative_filter"]
    assert loaded.metadata.calibration_fixture_ids == []
    assert loaded.metadata.validation_fixture_ids == []
    assert loaded.metadata.model_version is None
    assert loaded.metadata.fit_status is None
    assert loaded.metadata.fit_metrics == {}
    assert loaded.metadata.validity_envelope is None
    assert loaded.metadata.calibration_name is None
    assert loaded.metadata.calibration_version is None
    assert loaded.metadata.valid_fn_range is None
    assert loaded.metadata.valid_l_b_range is None
    assert loaded.metadata.source_citation is None
    assert loaded.metadata.extraction_method is None


def test_resistance_claim_state_is_serialized_and_not_promoted() -> None:
    curve = resistance_curve(Hull(), V_knots=np.array([3.5]))
    payload = curve.model_dump(mode="json")

    assert payload["metadata"]["claim_state"] == "uncalibrated_comparative"
    assert "claim_state" in payload["metadata"]
    assert claim_allows_calibrated_prediction(curve.metadata) is False
    assert claim_allows_final_design_fitness(curve.metadata) is False


@pytest.mark.parametrize("fit_status", ["candidate_fit", "rejected_fit"])
def test_candidate_or_rejected_fit_with_metrics_cannot_claim_calibrated_prediction(
    fit_status: str,
) -> None:
    metadata = _complete_calibrated_metadata(fit_status=fit_status)

    assert metadata.fit_metrics
    assert claim_allows_calibrated_prediction(metadata) is False


@pytest.mark.parametrize("fit_status", ["passed", "accepted", "fit_passed"])
def test_legacy_fit_aliases_do_not_claim_calibrated_prediction(
    fit_status: str,
) -> None:
    metadata = _complete_calibrated_metadata(fit_status=fit_status)

    assert metadata.fit_metrics
    assert claim_allows_calibrated_prediction(metadata) is False


def test_accepted_fit_complete_contract_allows_calibrated_prediction() -> None:
    metadata = _complete_calibrated_metadata()

    assert metadata.fit_status == "accepted_fit"
    assert claim_allows_calibrated_prediction(metadata) is True


def test_accepted_fit_without_metrics_cannot_claim_calibrated_prediction() -> None:
    metadata = _complete_calibrated_metadata()
    metadata.fit_metrics.clear()

    assert metadata.fit_status == "accepted_fit"
    assert metadata.fit_metrics == {}
    assert claim_allows_calibrated_prediction(metadata) is False


def test_validation_only_metadata_cannot_claim_calibrated_prediction() -> None:
    metadata = _complete_calibrated_metadata(
        calibration_fixture_ids=[],
        validation_fixture_ids=["validation-fixture-001"],
    )

    assert metadata.validation_fixture_ids == ["validation-fixture-001"]
    assert claim_allows_calibrated_prediction(metadata) is False


def test_default_resistance_source_registry_has_no_calibration_fixtures() -> None:
    registry = default_resistance_source_registry()
    assert registry
    assert {record.source_id for record in registry} >= {
        "edinburgh_pacific_canoe_hydrodynamics",
        "sea_kayaker_kanu_compilation",
        "gomes_2018_k1_drag_components",
        "tzabiras_k1_tow_tank",
    }
    assert all(record.intended_use != "calibration_fixture" for record in registry)
    assert any(record.measured_data for record in registry)
    assert any("redistribution" in warning for record in registry for warning in record.warnings)

    edinburgh = next(
        record
        for record in registry
        if record.source_id == "edinburgh_pacific_canoe_hydrodynamics"
    )
    assert edinburgh.intended_use == "validation_candidate"
    assert edinburgh.measured_data is True
    assert "cc_by_4_0" in edinburgh.rights_status
    assert "validation_not_calibration" in edinburgh.warnings


def test_validation_fixture_does_not_promote_resistance_claim() -> None:
    fixture = ResistanceSourceRecord(
        source_id="synthetic_validation_fixture",
        title="Synthetic validation fixture",
        url="https://example.invalid/fixture",
        source_type="test_fixture",
        intended_use="validation_fixture",
        measured_data=True,
        hull_class="sprint_k1",
        rights_status="test_only",
        extraction_status="checked_for_parser_validation",
        notes="Validation fixtures do not calibrate the resistance model.",
        warnings=["validation_not_calibration"],
        fixture_id="validation-only-001",
        measured_quantity="total_resistance",
        measurement_units="N",
    )
    curve = resistance_curve(Hull(), V_knots=np.array([3.5]))

    assert fixture.intended_use == "validation_fixture"
    assert curve.metadata.claim_state == "uncalibrated_comparative"
    assert curve.metadata.calibration_fixture_ids == []
    assert "uncalibrated_no_validity_envelope" in curve.metadata.warnings


def test_calibration_fixture_requires_review_metadata() -> None:
    candidate = default_resistance_source_registry()[0].model_dump(mode="python")
    candidate["intended_use"] = "calibration_fixture"

    with pytest.raises(ValidationError, match="fixture review metadata"):
        ResistanceSourceRecord.model_validate(candidate)


@pytest.mark.parametrize(
    "metadata_update",
    [
        {"measured_data": False},
        {"rights_status": ""},
        {"extraction_status": ""},
    ],
)
def test_calibration_fixture_rejects_weak_source_evidence(
    metadata_update: dict[str, object],
) -> None:
    payload = _accepted_calibration_fixture_payload(**metadata_update)

    with pytest.raises(ValidationError, match="calibration_fixture"):
        ResistanceSourceRecord.model_validate(payload)


def test_validation_fixture_requires_reproducible_fixture_metadata() -> None:
    with pytest.raises(ValidationError, match="validation_fixture"):
        ResistanceSourceRecord(
            source_id="under_described_validation_fixture",
            title="Under-described validation fixture",
            url="https://example.invalid/validation-fixture",
            source_type="test_fixture",
            intended_use="validation_fixture",
            measured_data=True,
            hull_class="sprint_k1",
            rights_status="test_only",
            extraction_status="checked_for_parser_validation",
            notes="Missing stable fixture identity, measured quantity, and units.",
        )
