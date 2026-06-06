"""RFC 0054 calibration-campaign ingest, acceptance, and artifact tests."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.calibration import (
    ResistanceSourceReviewPacket,
    default_resistance_source_review_packets,
)
from kayakgen.eval.calibration.campaigns import (
    AcceptedFitRecord,
    AcceptedFitRejection,
    GeometryReference,
    IncliningTestCampaign,
    IncliningTestRun,
    TankTestCampaign,
    TankTestRun,
    evaluate_fit_against_threshold,
    inclining_test_campaign_from_csv,
    tank_test_campaign_from_csv,
)
from kayakgen.eval.calibration.rights import RightsChecklist
from kayakgen.io.json import save_hull
from kayakgen.model.hull import Hull
from kayakgen.services.calibration_artifacts import write_residual_plot

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "calibration_campaigns"
TANK_CSV = FIXTURE_DIR / "tank_test_synthetic.csv"
INCLINING_CSV = FIXTURE_DIR / "inclining_test_synthetic.csv"


def _rights() -> RightsChecklist:
    return RightsChecklist(
        license_identifier="CC BY 4.0",
        attribution="Test Lab synthetic campaign 2026",
        source_locator="https://example.invalid/synthetic-campaign",
        redistribution_authorized=True,
        attribution_required=True,
        notes=["synthetic data for unit tests"],
    )


def _geometry(hash_value: str = "synthetic-hull-hash") -> GeometryReference:
    return GeometryReference(
        geometry_path="synthetic.json",
        hull_design_hash=hash_value,
    )


def _accepted_fit(
    *,
    fit_id: str = "fit-synthetic-001",
    fit_metric: str = "RMSE",
    fit_value: float = 0.5,
    holdout_rms_n: float = 20.0,
) -> AcceptedFitRecord:
    return AcceptedFitRecord(
        fit_id=fit_id,
        model_version="model-v1.0.0",
        fit_metric=fit_metric,  # type: ignore[arg-type]
        fit_value=fit_value,
        holdout_rms_n=holdout_rms_n,
        residuals=[(0.5, 0.1), (1.0, -0.2), (1.5, 0.05), (2.0, -0.15)],
        validity_envelope={"speed_ms": (0.0, 2.0)},
        accepted_at="2026-05-17T12:00:00Z",
        accepted_by="pytest",
    )


# ---------------------------------------------------------------------------
# Round-trip tests


def test_tank_test_campaign_round_trips_via_json() -> None:
    campaign = TankTestCampaign(
        source_id="synthetic-tank-001",
        rights_checklist=_rights(),
        geometry_reference=_geometry(),
        rows=[
            TankTestRun(
                source_id="synthetic-tank-001",
                hull_design_hash="synthetic-hull-hash",
                speed_ms=1.0,
                total_drag_n=7.8,
                drag_uncertainty_n=0.12,
                trim_deg=0.15,
                sink_mm=1.10,
                water_temperature_c=15.0,
                notes=["calm"],
            )
        ],
        uncertainty_method="Type_A_repeatability",
    )
    blob = campaign.model_dump_json()
    loaded = TankTestCampaign.model_validate_json(blob)
    assert loaded == campaign


def test_inclining_test_campaign_round_trips_via_json() -> None:
    campaign = IncliningTestCampaign(
        source_id="synthetic-inclining-001",
        rights_checklist=_rights(),
        geometry_reference=_geometry(),
        rows=[
            IncliningTestRun(
                source_id="synthetic-inclining-001",
                hull_design_hash="synthetic-hull-hash",
                heel_deg=4.0,
                applied_moment_nm=25.1,
                applied_moment_uncertainty_nm=0.5,
                sealed_body=True,
                cockpit_flooded=False,
                paddler_state="absent",
                notes=[],
            )
        ],
    )
    blob = campaign.model_dump_json()
    loaded = IncliningTestCampaign.model_validate_json(blob)
    assert loaded == campaign


def test_accepted_fit_record_round_trips_via_json() -> None:
    record = _accepted_fit()
    blob = record.model_dump_json()
    loaded = AcceptedFitRecord.model_validate_json(blob)
    assert loaded == record
    assert loaded.fit_metric == "RMSE"
    assert loaded.validity_envelope == {"speed_ms": (0.0, 2.0)}


def test_campaign_row_source_id_must_match_campaign() -> None:
    with pytest.raises(ValidationError, match="must all carry the campaign source_id"):
        TankTestCampaign(
            source_id="synthetic-tank-001",
            rights_checklist=_rights(),
            geometry_reference=_geometry(),
            rows=[
                TankTestRun(
                    source_id="wrong-id",
                    hull_design_hash="x",
                    speed_ms=0.5,
                    total_drag_n=1.0,
                    trim_deg=0.0,
                    sink_mm=0.0,
                    water_temperature_c=15.0,
                )
            ],
            uncertainty_method="Type_A_repeatability",
        )


# ---------------------------------------------------------------------------
# CSV ingest happy path


def test_tank_test_csv_ingest_emits_valid_campaign() -> None:
    campaign = tank_test_campaign_from_csv(
        TANK_CSV,
        source_id="synthetic-tank-001",
        hull_design_hash="synthetic-hull-hash",
        rights_checklist=_rights(),
        geometry_reference=_geometry(),
        uncertainty_method="Type_A_repeatability",
    )
    assert isinstance(campaign, TankTestCampaign)
    assert len(campaign.rows) == 4
    assert campaign.rows[0].speed_ms == pytest.approx(0.5)
    assert campaign.rows[-1].notes == ["calm", "repeat"]


def test_inclining_test_csv_ingest_emits_valid_campaign() -> None:
    campaign = inclining_test_campaign_from_csv(
        INCLINING_CSV,
        source_id="synthetic-inclining-001",
        hull_design_hash="synthetic-hull-hash",
        rights_checklist=_rights(),
        geometry_reference=_geometry(),
    )
    assert isinstance(campaign, IncliningTestCampaign)
    assert len(campaign.rows) == 4
    assert campaign.rows[0].sealed_body is True
    assert campaign.rows[0].cockpit_flooded is False
    assert campaign.rows[0].paddler_state == "absent"


# ---------------------------------------------------------------------------
# Threshold evaluation


def test_evaluate_fit_passes_when_rmse_within_threshold() -> None:
    record = _accepted_fit(fit_value=0.5, holdout_rms_n=20.0)
    # 5% of 20.0 = 1.0; fit_value 0.5 <= 1.0 → passes.
    evaluate_fit_against_threshold(record, measured_baseline=20.0, threshold_pct=5.0)


def test_evaluate_fit_rejects_when_rmse_above_threshold() -> None:
    record = _accepted_fit(fit_value=3.0, holdout_rms_n=20.0)
    with pytest.raises(AcceptedFitRejection) as excinfo:
        evaluate_fit_against_threshold(
            record, measured_baseline=20.0, threshold_pct=5.0
        )
    assert excinfo.value.reason == "fit_above_rmse_threshold"


# Audit G5 (workflow 0066): the MAPE and R2 branches are reachable from the
# D006 promotion gate — `_validate_accepted_fit_ref_on_disk` forwards
# whatever `fit_metric` the on-disk record carries — but neither branch's
# direction was pinned by any test.


def test_evaluate_fit_rejects_when_mape_above_threshold() -> None:
    # MAPE treats threshold_pct as the MAXIMUM admissible percent.
    record = _accepted_fit(fit_metric="MAPE", fit_value=7.5)
    with pytest.raises(AcceptedFitRejection) as excinfo:
        evaluate_fit_against_threshold(
            record, measured_baseline=20.0, threshold_pct=5.0
        )
    assert excinfo.value.reason == "fit_above_mape_threshold"


def test_evaluate_fit_passes_when_mape_within_threshold() -> None:
    record = _accepted_fit(fit_metric="MAPE", fit_value=4.0)
    evaluate_fit_against_threshold(record, measured_baseline=20.0, threshold_pct=5.0)


def test_evaluate_fit_rejects_when_r2_below_minimum() -> None:
    # R2 treats threshold_pct as a MINIMUM admissible value (higher passes).
    record = _accepted_fit(fit_metric="R2", fit_value=0.85)
    with pytest.raises(AcceptedFitRejection) as excinfo:
        evaluate_fit_against_threshold(
            record, measured_baseline=20.0, threshold_pct=0.9
        )
    assert excinfo.value.reason == "fit_below_r2_threshold"


def test_evaluate_fit_passes_when_r2_above_minimum() -> None:
    record = _accepted_fit(fit_metric="R2", fit_value=0.95)
    evaluate_fit_against_threshold(record, measured_baseline=20.0, threshold_pct=0.9)


def test_r2_record_under_default_threshold_refuses_every_fit() -> None:
    """Audit G5 semantic quirk, pinned as INTENDED (workflow 0066 decision).

    The D006 promotion gate defaults ``acceptance_threshold_pct`` to 5.0
    and forwards it as ``threshold_pct`` regardless of fit_metric. For an
    R2 record that minimum is unsatisfiable — R2 <= 1.0 < 5.0 — so EVERY
    R2 fit refuses under the default, even a perfect one. Fail-closed:
    claims discipline holds, and promoting an R2 fit requires an explicit
    per-fixture ``acceptance_threshold_pct`` in the validity envelope.
    Whether R2 deserves its own default is a recorded open question
    (workflow 0066 draft artifact), not something this test decides."""

    perfect = _accepted_fit(fit_metric="R2", fit_value=1.0)
    with pytest.raises(AcceptedFitRejection) as excinfo:
        evaluate_fit_against_threshold(
            perfect, measured_baseline=20.0, threshold_pct=5.0
        )
    assert excinfo.value.reason == "fit_below_r2_threshold"


# ---------------------------------------------------------------------------
# CLI: accept-fit threshold


def test_cli_accept_fit_rejects_below_threshold(tmp_path: Path) -> None:
    runner = CliRunner()
    record = _accepted_fit(fit_value=10.0, holdout_rms_n=20.0)  # 50% RMSE → reject
    fit_path = tmp_path / "fit.json"
    fit_path.write_text(record.model_dump_json())
    out_dir = tmp_path / "accepted"
    result = runner.invoke(
        app,
        [
            "calibration",
            "accept-fit",
            "synthetic-fixture-001",
            "--fit",
            str(fit_path),
            "--rmse-threshold",
            "5",
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 1, result.output
    assert "fit_above_rmse_threshold" in result.output


def test_cli_accept_fit_writes_record_when_above_threshold(tmp_path: Path) -> None:
    runner = CliRunner()
    record = _accepted_fit(fit_value=0.5, holdout_rms_n=20.0)
    fit_path = tmp_path / "fit.json"
    fit_path.write_text(record.model_dump_json())
    out_dir = tmp_path / "accepted"
    result = runner.invoke(
        app,
        [
            "calibration",
            "accept-fit",
            "synthetic-fixture-001",
            "--fit",
            str(fit_path),
            "--rmse-threshold",
            "5",
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out_dir / f"{record.fit_id}.accepted_fit.json").is_file()


# ---------------------------------------------------------------------------
# CLI: ingest happy paths


def test_cli_ingest_tank_test_writes_campaign(tmp_path: Path) -> None:
    runner = CliRunner()
    hull_path = tmp_path / "hull.json"
    save_hull(Hull(), hull_path)
    rights_path = tmp_path / "rights.json"
    rights_path.write_text(_rights().model_dump_json())
    out_dir = tmp_path / "campaign"
    result = runner.invoke(
        app,
        [
            "calibration",
            "ingest-tank-test",
            str(TANK_CSV),
            "--hull",
            str(hull_path),
            "--rights",
            str(rights_path),
            "--out",
            str(out_dir),
            "--source-id",
            "synthetic-tank-001",
        ],
    )
    assert result.exit_code == 0, result.output
    campaign_path = out_dir / "synthetic-tank-001.campaign.json"
    assert campaign_path.is_file()
    loaded = TankTestCampaign.model_validate_json(campaign_path.read_text())
    assert loaded.source_id == "synthetic-tank-001"
    assert len(loaded.rows) == 4


def test_cli_ingest_inclining_test_writes_campaign(tmp_path: Path) -> None:
    runner = CliRunner()
    hull_path = tmp_path / "hull.json"
    save_hull(Hull(), hull_path)
    out_dir = tmp_path / "campaign"
    result = runner.invoke(
        app,
        [
            "calibration",
            "ingest-inclining-test",
            str(INCLINING_CSV),
            "--hull",
            str(hull_path),
            "--out",
            str(out_dir),
            "--source-id",
            "synthetic-inclining-001",
        ],
    )
    assert result.exit_code == 0, result.output
    campaign_path = out_dir / "synthetic-inclining-001.campaign.json"
    assert campaign_path.is_file()


# ---------------------------------------------------------------------------
# Residual plot SVG


def test_residual_plot_produces_parseable_svg(tmp_path: Path) -> None:
    record = _accepted_fit()
    out = tmp_path / "residuals.svg"
    write_residual_plot(record, out)
    assert out.is_file()
    tree = ET.parse(out)
    root = tree.getroot()
    # SVG root must use the standard namespace.
    assert root.tag.endswith("svg")
    text = out.read_text()
    assert "zero-line" in text
    assert "residual-stems" in text
    # One stem per residual point.
    stems = [el for el in root.iter() if el.tag.endswith("line")]
    # zero-line + grid lines + one stem per residual; just assert > 0.
    assert len(stems) >= len(record.residuals)


def test_cli_residual_plot_writes_svg(tmp_path: Path) -> None:
    runner = CliRunner()
    record = _accepted_fit()
    fit_path = tmp_path / "fit.json"
    fit_path.write_text(record.model_dump_json())
    svg_path = tmp_path / "residuals.svg"
    result = runner.invoke(
        app,
        [
            "calibration",
            "residual-plot",
            str(fit_path),
            "--out",
            str(svg_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert svg_path.is_file()
    ET.parse(svg_path)


# ---------------------------------------------------------------------------
# Calibration fixture promotion through accepted-fit ref on disk


def _synthetic_calibration_packet_payload(accepted_fit_ref: str) -> dict[str, object]:
    """Build a calibration_fixture review packet for a SYNTHETIC source.

    The synthetic source is NOT a real entry in
    ``default_resistance_source_registry()`` — it exists only to exercise
    the RFC 0054 strict-resolve gate without widening any real source's
    claim state. Edinburgh in particular MUST remain capped at
    ``validation_fixture``.
    """
    evidence = {"status": "accepted", "summary": "synthetic evidence"}
    return {
        "source_id": "synthetic_calibration_source_unittest",
        "title": "Synthetic calibration source",
        "citation": "Synthetic test fixture",
        "locator": "https://example.invalid/synthetic-calibration",
        "source_type": "tow_tank_measurement",
        "measured_data": True,
        "hull_class": "sea_kayak",
        "rights": evidence,
        "extraction": evidence,
        "measured_quantity": evidence,
        "units": evidence,
        "hull_envelope": evidence,
        "speed_froude_range": evidence,
        "uncertainty": evidence,
        "reviewer": "pytest",
        "review_date": "2026-05-17",
        "review_verdict": "calibration_fixture",
        "reasons": ["synthetic test path"],
        "non_promotion_reasons": [],
        "warnings": [],
        "fixture_id": "synthetic-calibration-fixture-001",
        "fixture_version": "v1",
        "validity_envelope": {"speed_ms": [0.0, 2.0]},
        "source_checksum_sha256": "b" * 64,
        "extraction_script_ref": "kayakgen/eval/calibration/extractors/synthetic.py",
        "accepted_fit_ref": accepted_fit_ref,
    }


def test_calibration_fixture_promotion_resolves_accepted_fit_on_disk(
    tmp_path: Path,
) -> None:
    """A SYNTHETIC source with a real .json accepted_fit_ref must validate."""
    record = _accepted_fit(fit_value=0.4, holdout_rms_n=20.0)  # well below 5%
    fit_path = tmp_path / "fits" / "fit-synthetic-001.accepted_fit.json"
    fit_path.parent.mkdir(parents=True, exist_ok=True)
    fit_path.write_text(record.model_dump_json())

    packet = ResistanceSourceReviewPacket.model_validate(
        _synthetic_calibration_packet_payload(str(fit_path))
    )
    assert packet.review_verdict == "calibration_fixture"
    assert packet.calibration_promotion_blockers() == []


def test_calibration_fixture_promotion_rejects_unresolved_accepted_fit(
    tmp_path: Path,
) -> None:
    bogus = tmp_path / "does_not_exist.accepted_fit.json"
    with pytest.raises(ValidationError, match="accepted_fit_unresolved"):
        ResistanceSourceReviewPacket.model_validate(
            _synthetic_calibration_packet_payload(str(bogus))
        )


def test_calibration_fixture_promotion_rejects_below_threshold_fit(
    tmp_path: Path,
) -> None:
    """A real on-disk fit whose RMSE exceeds 5% of holdout_rms_n is refused."""
    record = _accepted_fit(fit_value=10.0, holdout_rms_n=20.0)  # 50% RMSE
    fit_path = tmp_path / "bad_fit.accepted_fit.json"
    fit_path.write_text(record.model_dump_json())
    with pytest.raises(ValidationError, match="fit_above_rmse_threshold"):
        ResistanceSourceReviewPacket.model_validate(
            _synthetic_calibration_packet_payload(str(fit_path))
        )


def test_edinburgh_packet_remains_validation_fixture_under_rfc_0054(tmp_path: Path) -> None:
    """RFC 0054 must NOT widen the Edinburgh claim state.

    Edinburgh stays a validation_fixture; its accepted_fit_ref stays
    null; calibration promotion remains blocked by the envelope reason.
    Nothing in this test writes a calibration-promotion payload for the
    real Edinburgh source.
    """
    edinburgh = default_resistance_source_review_packets()[0]
    assert edinburgh.review_verdict == "validation_fixture"
    assert edinburgh.accepted_fit_ref is None
    # Sanity: writing an arbitrary .json file does not magically promote
    # Edinburgh; the registry default is unchanged.
    side_effect = tmp_path / "would-promote-edinburgh.accepted_fit.json"
    side_effect.write_text(_accepted_fit().model_dump_json())
    edinburgh_again = default_resistance_source_review_packets()[0]
    assert edinburgh_again.review_verdict == "validation_fixture"


def test_accepted_fit_record_writes_json_byte_stably_across_two_invocations(
    tmp_path: Path,
) -> None:
    """``model_dump_json`` is the byte-stable serialization channel."""
    record = _accepted_fit()
    blob_a = record.model_dump_json()
    blob_b = record.model_dump_json()
    assert blob_a == blob_b
    # Round-trip stability through a file:
    path_a = tmp_path / "a.json"
    path_b = tmp_path / "b.json"
    path_a.write_text(blob_a)
    path_b.write_text(blob_b)
    assert json.loads(path_a.read_text()) == json.loads(path_b.read_text())
