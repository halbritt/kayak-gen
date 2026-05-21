"""RFC 0058 stage 3 stability CLI tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.calibration.rights import RightsChecklist
from kayakgen.eval.stability.accepted_fit import (
    FixtureRef,
    HullFamilyScope,
    ReviewerSignature,
    StabilityFitMetrics,
    StabilityFitRecord,
    StabilityFixturePromotionPacket,
)
from kayakgen.eval.stability.measured_fixture import (
    CalibrationTrace,
    FreeEquilibriumPoint,
    FreeEquilibriumTrace,
    HullIdentityRef,
    HysteresisBound,
    LoadingConfiguration,
    MeasuredStabilityFixture,
    MeasuredStabilityRow,
)


def _signed_at() -> datetime:
    return datetime(2026, 5, 21, 3, 0, 0, tzinfo=timezone.utc)


def _rights() -> RightsChecklist:
    return RightsChecklist(
        license_identifier="CC BY 4.0",
        attribution="Kayak Lab, 2026",
        source_locator="https://example.org/stability/msf-2026-001",
        redistribution_authorized=True,
        attribution_required=True,
    )


def _fixture(**overrides) -> MeasuredStabilityFixture:
    defaults = dict(
        fixture_id="msf-2026-001",
        title="Sterling Reflection sealed-deck rig run",
        source_citation="Kayak Lab internal rig, 2026-05",
        rights=_rights(),
        extraction_method="strain_gauged_moment_arm_v1",
        hull_identity=HullIdentityRef(
            manufacturer="Sterling",
            model="Reflection",
            serial_or_year="2017",
            scan_hash="a" * 64,
            scan_method="structured light scan",
            hull_class="sea kayak",
        ),
        configuration="sealed_deck",
        loading=LoadingConfiguration(
            displacement_kg=110.0,
            paddler_state="rigid_manikin",
            paddler_mass_kg=85.0,
            paddler_cg_height_m=0.65,
        ),
        valid_heel_range_deg=(0.0, 30.0),
        rig_design_ref="docs/research/STRAIN_GAUGED_GZ_RIG_DESIGN_2026-05-16.md",
        geometry_manifest_ref="data/stability/scans/sterling_reflection.json",
        calibration_trace=CalibrationTrace(
            pre_run_trace_path="cal/pre.csv",
            post_run_trace_path="cal/post.csv",
            dead_weight_kg=5.0,
            measured_arm_pre_m=0.3000,
            measured_arm_post_m=0.3003,
        ),
        free_equilibrium_trace=FreeEquilibriumTrace(
            points=[
                FreeEquilibriumPoint(theta_deg=0.0, trim_deg=0.0, heave_m=0.0),
                FreeEquilibriumPoint(theta_deg=15.0, trim_deg=0.4, heave_m=-0.004),
                FreeEquilibriumPoint(theta_deg=30.0, trim_deg=1.1, heave_m=-0.012),
            ],
        ),
        hysteresis_bound=HysteresisBound(
            observed_max_fraction=0.018,
            observed_at_theta_deg=20.0,
        ),
        rows=[
            MeasuredStabilityRow(theta_deg=0.0, gz_m=0.0, gz_std_m=0.0005),
            MeasuredStabilityRow(theta_deg=15.0, gz_m=0.045, gz_std_m=0.001),
            MeasuredStabilityRow(theta_deg=30.0, gz_m=0.062, gz_std_m=0.001),
        ],
        non_promotion_reasons=["awaiting promotion-review packet"],
    )
    defaults.update(overrides)
    return MeasuredStabilityFixture(**defaults)


def _reviewer() -> ReviewerSignature:
    return ReviewerSignature(
        reviewer_label="reviewer-1",
        reviewer_role="stability-fixture-reviewer",
        signed_at=_signed_at(),
    )


def _fixture_ref() -> FixtureRef:
    return FixtureRef(
        fixture_id="msf-2026-001",
        fixture_path="data/stability/fixtures/msf-2026-001/manifest.json",
        fixture_sha256="b" * 64,
    )


def _promotion_packet(**overrides) -> StabilityFixturePromotionPacket:
    defaults = dict(
        fixture_ref=_fixture_ref(),
        rights_review="accepted",
        hull_identity_review="accepted",
        calibration_drift_review="accepted",
        hysteresis_review="accepted",
        free_equilibrium_review="accepted",
        rig_design_match=True,
        promotion_target="measured_stability_fixture",
        rejection_reasons=[],
        reviewer_signature=_reviewer(),
    )
    defaults.update(overrides)
    return StabilityFixturePromotionPacket(**defaults)


def _fit_record(**overrides) -> StabilityFitRecord:
    defaults = dict(
        fit_id="stability-fit-001",
        analytical_evaluator_version="rfc-0043-generated-body-v1",
        hull_family_scope=HullFamilyScope(
            hull_class="sea kayak",
            design_hash_envelope=["design-hash-001"],
        ),
        valid_heel_range_deg=(0.0, 70.0),
        fixtures=[_fixture_ref()],
        fit_metrics=StabilityFitMetrics(
            rmse_m=0.004,
            mape_fraction=0.04,
            max_error_m=0.009,
            coverage_fraction=0.95,
        ),
        acceptance_verdict="accepted",
        rejection_reasons=[],
        reviewer_signature=_reviewer(),
        accepted_at=_signed_at(),
    )
    defaults.update(overrides)
    return StabilityFitRecord(**defaults)


def test_ingest_rig_run_writes_candidate_and_refuses_overwrite(tmp_path) -> None:
    source = tmp_path / "source.json"
    source.write_text(_fixture().model_dump_json(), encoding="utf-8")
    out = tmp_path / "fixtures" / "msf-2026-001"
    runner = CliRunner()

    result = runner.invoke(app, ["stability", "ingest-rig-run", str(source), "--out", str(out)])

    assert result.exit_code == 0, result.output
    manifest = out / "manifest.json"
    assert manifest.exists()
    rebuilt = MeasuredStabilityFixture.model_validate_json(manifest.read_text())
    assert rebuilt.intended_use == "validation_candidate"

    second = runner.invoke(app, ["stability", "ingest-rig-run", str(source), "--out", str(out)])
    assert second.exit_code == 1
    assert "refusing to overwrite" in second.output


def test_ingest_rig_run_refuses_invalid_manifest(tmp_path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"fixture_id": "missing-required-fields"}', encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["stability", "ingest-rig-run", str(bad), "--out", str(tmp_path / "out")],
    )

    assert result.exit_code == 1
    assert "ingest-rig-run failed" in result.output
    assert not (tmp_path / "out" / "manifest.json").exists()


def test_promote_fixture_updates_intended_use_and_noops_candidate(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    fixture_dir = tmp_path / "data" / "stability" / "fixtures" / "msf-2026-001"
    fixture_dir.mkdir(parents=True)
    manifest = fixture_dir / "manifest.json"
    manifest.write_text(_fixture().model_dump_json(), encoding="utf-8")
    packet = tmp_path / "packet.json"
    packet.write_text(_promotion_packet().model_dump_json(), encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["stability", "promote-fixture", "msf-2026-001", "--packet", str(packet)],
    )

    assert result.exit_code == 0, result.output
    promoted = MeasuredStabilityFixture.model_validate_json(manifest.read_text())
    assert promoted.intended_use == "measured_stability_fixture"

    manifest.write_text(_fixture().model_dump_json(), encoding="utf-8")
    no_op_packet = tmp_path / "noop-packet.json"
    no_op_packet.write_text(
        _promotion_packet(
            promotion_target="validation_candidate",
            rejection_reasons=["keep as candidate"],
        ).model_dump_json(),
        encoding="utf-8",
    )
    no_op = runner.invoke(
        app,
        ["stability", "promote-fixture", "msf-2026-001", "--packet", str(no_op_packet)],
    )

    assert no_op.exit_code == 0, no_op.output
    unchanged = MeasuredStabilityFixture.model_validate_json(manifest.read_text())
    assert unchanged.intended_use == "validation_candidate"


def test_promote_fixture_refuses_invalid_packet(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    fixture_dir = tmp_path / "data" / "stability" / "fixtures" / "msf-2026-001"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "manifest.json").write_text(_fixture().model_dump_json(), encoding="utf-8")
    packet = tmp_path / "invalid-packet.json"
    packet.write_text(
        """
{
  "schema_version": "1",
  "fixture_ref": {
    "fixture_id": "msf-2026-001",
    "fixture_path": "data/stability/fixtures/msf-2026-001/manifest.json",
    "fixture_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  },
  "rights_review": "accepted",
  "hull_identity_review": "accepted",
  "calibration_drift_review": "accepted",
  "hysteresis_review": "accepted",
  "free_equilibrium_review": "accepted",
  "rig_design_match": false,
  "promotion_target": "measured_stability_fixture",
  "rejection_reasons": [],
  "reviewer_signature": {
    "schema_version": "1",
    "reviewer_label": "reviewer-1",
    "reviewer_role": "stability-fixture-reviewer",
    "signed_at": "2026-05-21T03:00:00+00:00"
  }
}
""".strip(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        ["stability", "promote-fixture", "msf-2026-001", "--packet", str(packet)],
    )

    assert result.exit_code == 1
    assert "rig_design_match=True" in result.output


def test_accept_fit_writes_record_and_refuses_overwrite(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    fit = tmp_path / "fit.json"
    fit.write_text(_fit_record().model_dump_json(), encoding="utf-8")
    packet = tmp_path / "packet.json"
    packet.write_text(_promotion_packet().model_dump_json(), encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(app, ["stability", "accept-fit", str(fit), "--packet", str(packet)])

    assert result.exit_code == 0, result.output
    out = tmp_path / "data" / "stability" / "fits" / "stability-fit-001.json"
    assert out.exists()
    rebuilt = StabilityFitRecord.model_validate_json(out.read_text())
    assert rebuilt.fit_id == "stability-fit-001"

    second = runner.invoke(app, ["stability", "accept-fit", str(fit), "--packet", str(packet)])
    assert second.exit_code == 1
    assert "refusing to overwrite" in second.output


def test_accept_fit_refuses_packet_that_does_not_accept_fixture(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    fit = tmp_path / "fit.json"
    fit.write_text(_fit_record().model_dump_json(), encoding="utf-8")
    packet = tmp_path / "candidate-packet.json"
    packet.write_text(
        _promotion_packet(
            promotion_target="validation_candidate",
            rejection_reasons=["keep as candidate"],
        ).model_dump_json(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        ["stability", "accept-fit", str(fit), "--packet", str(packet)],
    )

    assert result.exit_code == 1
    assert "promotion_target='measured_stability_fixture'" in result.output


def test_residual_plot_writes_svg_stub_with_metrics(tmp_path) -> None:
    fit = tmp_path / "fit.json"
    fit.write_text(_fit_record().model_dump_json(), encoding="utf-8")
    out = tmp_path / "residuals.svg"

    result = CliRunner().invoke(
        app,
        ["stability", "residual-plot", str(fit), "--out", str(out)],
    )

    assert result.exit_code == 0, result.output
    svg = out.read_text(encoding="utf-8")
    assert "<svg" in svg
    assert "stability-fit-001" in svg
    assert "rmse_m=0.004" in svg
    assert "validation_candidate vs reference" in svg
