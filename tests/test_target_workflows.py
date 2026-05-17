"""Tests for RFC 0050 target-displacement and target-trim workflows."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.contract import LoadCase, LongitudinalLoadComponent
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.stability import evaluate_equilibrium_stability
from kayakgen.model.hull import Hull
from kayakgen.services.evaluation import (
    TargetDraftMismatchReport,
    solve_target_draft,
    solve_target_trim,
    target_draft_load_mismatch,
)


def _day_trip_load(hull: Hull, target_draft_m: float) -> LoadCase:
    hydro = evaluate_hydrostatics(hull.model_copy(update={"draft_m": target_draft_m}))
    total_mass_kg = hydro.displaced_volume_m3 * 1025.0
    return LoadCase(
        name="day-trip",
        paddler_mass_kg=total_mass_kg - 18.0,
        hull_mass_kg=18.0,
        cargo_mass_kg=0.0,
    )


def _offset_paddler_load() -> LoadCase:
    return LoadCase(
        name="offset-paddler",
        components=[
            LongitudinalLoadComponent(
                name="paddler",
                mass_kg=90.0,
                x_m=-0.30,
                kg_above_keel_m=0.25,
            )
        ],
    )


def test_solve_target_draft_matches_equilibrium_solver_within_one_mm() -> None:
    hull = Hull(draft_m=0.12)
    target_draft_m = 0.135
    load = _day_trip_load(hull, target_draft_m)

    target_result = solve_target_draft(hull, load)
    equilibrium_result = evaluate_equilibrium_stability(hull, load)

    assert target_result.status == "converged"
    assert equilibrium_result.status == "converged"
    assert target_result.equilibrium_draft_m is not None
    assert equilibrium_result.equilibrium_draft_m is not None
    assert target_result.equilibrium_draft_m == pytest.approx(
        equilibrium_result.equilibrium_draft_m, abs=1e-3
    )
    assert target_result.equilibrium_draft_m == pytest.approx(target_draft_m, abs=1e-3)


def test_solve_target_trim_produces_converged_trim_equilibrium() -> None:
    hull = Hull()
    load = _offset_paddler_load()

    result = solve_target_trim(hull, load)

    assert result.method == "equilibrium_trim"
    assert result.status == "converged"
    assert result.trim_angle_deg is not None
    assert result.load_lcg_m == pytest.approx(-0.30, abs=1e-9)
    assert result.draft_at_midship_m is not None
    assert result.moment_tolerance_kg_m is not None
    assert abs(result.moment_error_kg_m) <= result.moment_tolerance_kg_m
    assert result.equilibrium_tolerance_kg is not None
    assert abs(result.displacement_error_kg) <= result.equilibrium_tolerance_kg


def test_target_draft_load_mismatch_reports_zero_when_draft_matches_equilibrium() -> None:
    hull = Hull(draft_m=0.12)
    target_draft_m = 0.135
    load = _day_trip_load(hull, target_draft_m)

    report = target_draft_load_mismatch(hull, target_draft_m, load)

    assert isinstance(report, TargetDraftMismatchReport)
    assert report.schema_version == "1"
    assert report.hull_record_hash == hull.hash()
    assert report.assumed_draft_m == pytest.approx(target_draft_m)
    assert report.actual_displaced_mass_kg == pytest.approx(
        report.expected_displaced_mass_kg, abs=1.0
    )
    assert abs(report.mismatch_kg) <= 1.0
    assert "mismatch_within_one_kg" in report.notes


def test_target_draft_load_mismatch_signs_correctly_for_low_draft() -> None:
    hull = Hull(draft_m=0.12)
    target_draft_m = 0.135
    load = _day_trip_load(hull, target_draft_m)

    low = target_draft_load_mismatch(hull, target_draft_m * 0.5, load)
    high = target_draft_load_mismatch(hull, target_draft_m * 1.5, load)

    assert low.mismatch_kg < 0
    assert high.mismatch_kg > 0
    assert "hull_under_buoyant_at_assumed_draft" in low.notes
    assert "hull_over_buoyant_at_assumed_draft" in high.notes


def test_cli_target_draft_round_trips_default_hull_and_day_trip_load(tmp_path) -> None:
    hull_model = Hull(draft_m=0.12)
    target_draft_m = 0.135
    load_model = _day_trip_load(hull_model, target_draft_m)
    hull_path = tmp_path / "hull.json"
    load_path = tmp_path / "load.json"
    out_path = tmp_path / "target_draft.json"
    hull_path.write_text(hull_model.model_dump_json())
    load_path.write_text(load_model.model_dump_json())

    result = CliRunner().invoke(
        app,
        [
            "target-draft",
            str(hull_path),
            "--load",
            str(load_path),
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    data = json.loads(out_path.read_text())
    assert data["method"] == "equilibrium_sinkage"
    assert data["status"] == "converged"
    assert data["equilibrium_draft_m"] == pytest.approx(target_draft_m, abs=1e-3)


def test_cli_target_draft_report_only_writes_mismatch_report(tmp_path) -> None:
    hull_model = Hull(draft_m=0.12)
    target_draft_m = 0.135
    load_model = _day_trip_load(hull_model, target_draft_m)
    hull_path = tmp_path / "hull.json"
    load_path = tmp_path / "load.json"
    out_path = tmp_path / "mismatch.json"
    hull_path.write_text(hull_model.model_dump_json())
    load_path.write_text(load_model.model_dump_json())

    result = CliRunner().invoke(
        app,
        [
            "target-draft",
            str(hull_path),
            "--load",
            str(load_path),
            "--draft",
            str(target_draft_m),
            "--report-only",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    data = json.loads(out_path.read_text())
    assert data["schema_version"] == "1"
    assert data["hull_record_hash"] == hull_model.hash()
    assert data["assumed_draft_m"] == pytest.approx(target_draft_m)
    assert abs(data["mismatch_kg"]) <= 1.0
    assert "mismatch_within_one_kg" in data["notes"]


def test_cli_target_trim_round_trips_offset_paddler_load(tmp_path) -> None:
    hull_model = Hull()
    load_model = _offset_paddler_load()
    hull_path = tmp_path / "hull.json"
    load_path = tmp_path / "load.json"
    out_path = tmp_path / "target_trim.json"
    hull_path.write_text(hull_model.model_dump_json())
    load_path.write_text(load_model.model_dump_json())

    result = CliRunner().invoke(
        app,
        [
            "target-trim",
            str(hull_path),
            "--load",
            str(load_path),
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    data = json.loads(out_path.read_text())
    assert data["method"] == "equilibrium_trim"
    assert data["status"] == "converged"
    assert data["load_lcg_m"] == pytest.approx(-0.30, abs=1e-9)
    assert data["trim_angle_deg"] is not None


def test_cli_target_draft_rejects_unphysical_load(tmp_path) -> None:
    hull_model = Hull()
    # >2x max displaced mass: pick something far above the hull volume
    hydro = evaluate_hydrostatics(hull_model)
    max_mass_kg = hydro.displaced_volume_m3 * 1025.0
    huge_load = LoadCase(
        name="unphysical",
        paddler_mass_kg=max_mass_kg * 5.0,
        hull_mass_kg=0.0,
        cargo_mass_kg=0.0,
    )
    hull_path = tmp_path / "hull.json"
    load_path = tmp_path / "load.json"
    out_path = tmp_path / "out.json"
    hull_path.write_text(hull_model.model_dump_json())
    load_path.write_text(huge_load.model_dump_json())

    result = CliRunner().invoke(
        app,
        [
            "target-draft",
            str(hull_path),
            "--load",
            str(load_path),
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 1
    assert "load_unphysical" in result.stderr or "load_unphysical" in result.stdout
    assert not out_path.exists()


def test_cli_target_trim_rejects_unphysical_load(tmp_path) -> None:
    hull_model = Hull()
    hydro = evaluate_hydrostatics(hull_model)
    max_mass_kg = hydro.displaced_volume_m3 * 1025.0
    huge_load = LoadCase(
        name="unphysical-trim",
        components=[
            LongitudinalLoadComponent(
                name="paddler",
                mass_kg=max_mass_kg * 5.0,
                x_m=-0.30,
                kg_above_keel_m=0.25,
            )
        ],
    )
    hull_path = tmp_path / "hull.json"
    load_path = tmp_path / "load.json"
    out_path = tmp_path / "out.json"
    hull_path.write_text(hull_model.model_dump_json())
    load_path.write_text(huge_load.model_dump_json())

    result = CliRunner().invoke(
        app,
        [
            "target-trim",
            str(hull_path),
            "--load",
            str(load_path),
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 1
    assert "load_unphysical" in result.stderr or "load_unphysical" in result.stdout
    assert not out_path.exists()
