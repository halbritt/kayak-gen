"""CLI surface checks for the opt-in ``--high-angle-gz`` flag (RFC 0043 stage 1)."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import Result
from typer.testing import CliRunner

from kayakgen.cli import high_angle_gz as cli_high_angle_gz  # noqa: F401 — kept for compat smoke
from kayakgen.eval import high_angle_gz as eval_high_angle_gz
from kayakgen.cli.high_angle_gz import (
    HIGH_ANGLE_GZ_BODY_PROFILE,
    HIGH_ANGLE_GZ_RESULT_SEMANTICS,
    HIGH_ANGLE_GZ_SURFACE_WARNINGS,
)
from kayakgen.cli.main import app
from kayakgen.eval.closed_volume import (
    explicit_synthetic_body,
    explicit_synthetic_self_intersection_policy,
)
from kayakgen.model.hull import Hull


def _write_hull(tmp_path, *, name: str = "high-angle-cli", **overrides) -> Path:
    hull = tmp_path / f"{name}.json"
    hull.write_text(Hull(name=name, bow_rake=0.0, stern_rake=0.0, **overrides).model_dump_json())
    return hull


def _run_stability(args: list[str]) -> Result:
    return CliRunner().invoke(app, args)


def test_stability_cli_high_angle_default_unchanged(tmp_path) -> None:
    """Without --high-angle-gz the JSON output is byte-equal to current behavior."""
    hull = _write_hull(tmp_path, name="default-unchanged")
    baseline_out = tmp_path / "baseline.json"
    augmented_out = tmp_path / "augmented.json"

    baseline = _run_stability(["stability", str(hull), "--out", str(baseline_out)])
    augmented = _run_stability(["stability", str(hull), "--out", str(augmented_out)])

    assert baseline.exit_code == 0
    assert augmented.exit_code == 0
    # Golden-style byte equality across two default invocations.
    assert baseline_out.read_bytes() == augmented_out.read_bytes()

    payload = json.loads(baseline_out.read_text())
    assert "high_angle_gz" not in payload
    assert payload["method"] == "design_waterline_initial"
    assert payload["gz_curve"] is None
    assert "high_angle_gz_not_implemented" in payload["warnings"]


def test_stability_cli_high_angle_includes_curve(tmp_path) -> None:
    """Flag emits the expected high_angle_gz block keys and RFC 0024 warnings."""
    hull = _write_hull(tmp_path, name="includes-curve")
    out = tmp_path / "stability.json"

    result = _run_stability(
        ["stability", str(hull), "--high-angle-gz", "--out", str(out)],
    )

    assert result.exit_code == 0
    payload = json.loads(out.read_text())
    assert "high_angle_gz" in payload
    block = payload["high_angle_gz"]
    assert block["available"] is True
    assert block["result_semantics"] == HIGH_ANGLE_GZ_RESULT_SEMANTICS
    assert block["body_profile"] == HIGH_ANGLE_GZ_BODY_PROFILE
    assert block["heel_grid_deg"][0] == 0.0
    assert block["heel_grid_deg"][-1] == 90.0
    # Default 0..90 by 5 deg => 19 points.
    assert len(block["heel_grid_deg"]) == 19
    assert len(block["heel_points"]) == len(block["heel_grid_deg"])

    record = block["heel_points"][0]
    for key in (
        "heel_deg",
        "gz_m",
        "sinkage_m",
        "iterations",
        "status",
        "residual_displacement_kg",
        "residual_longitudinal_moment_kg_m",
    ):
        assert key in record

    for surface_warning in HIGH_ANGLE_GZ_SURFACE_WARNINGS:
        assert surface_warning in block["warnings"]

    # Summary block presence depends on whether every grid point converged.
    if block["summary"] is not None:
        for key in ("max_gz", "heel_at_max_gz", "range_positive_stability_deg"):
            assert key in block["summary"]


def test_stability_cli_high_angle_custom_grid(tmp_path) -> None:
    """A strictly-increasing custom grid is echoed verbatim into the JSON."""
    hull = _write_hull(tmp_path, name="custom-grid")
    out = tmp_path / "stability.json"
    grid = "0,5,10,15"

    result = _run_stability(
        [
            "stability",
            str(hull),
            "--high-angle-gz",
            "--heel-grid-deg",
            grid,
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(out.read_text())
    block = payload["high_angle_gz"]
    assert block["heel_grid_deg"] == [0.0, 5.0, 10.0, 15.0]
    assert [point["heel_deg"] for point in block["heel_points"]] == [
        0.0,
        5.0,
        10.0,
        15.0,
    ]


def test_stability_cli_high_angle_rejects_nonincreasing_grid(tmp_path) -> None:
    """A non-strictly-increasing custom grid fails with a clear CLI error."""
    hull = _write_hull(tmp_path, name="bad-grid")
    out = tmp_path / "stability.json"

    result = _run_stability(
        [
            "stability",
            str(hull),
            "--high-angle-gz",
            "--heel-grid-deg",
            "0,5,5,10",
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 1
    assert "strictly increasing" in result.stderr
    assert not out.exists()


def test_stability_cli_high_angle_unavailable_for_synthetic(tmp_path, monkeypatch) -> None:
    """When the generated body is unavailable (synthetic only), available=false."""
    hull_path = _write_hull(tmp_path, name="synthetic-unavailable")
    out = tmp_path / "stability.json"

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
    synthetic = explicit_synthetic_body(
        vertices,
        faces,
        body_id="cli-synthetic-fixture",
        policy=explicit_synthetic_self_intersection_policy(),
    )
    # The real read-model lives in ``kayakgen.eval.high_angle_gz`` after the
    # Phase 2 move; monkeypatch the eval module's call site rather than the
    # cli compatibility shim.
    monkeypatch.setattr(
        eval_high_angle_gz,
        "generated_hull_plus_deck_body",
        lambda hull, **_kwargs: synthetic,
    )

    result = _run_stability(
        ["stability", str(hull_path), "--high-angle-gz", "--out", str(out)],
    )

    assert result.exit_code == 0
    payload = json.loads(out.read_text())
    block = payload["high_angle_gz"]
    assert block["available"] is False
    assert block["result_semantics"] == HIGH_ANGLE_GZ_RESULT_SEMANTICS
    assert block["body_profile"] == HIGH_ANGLE_GZ_BODY_PROFILE
    assert block["summary"] is None
    assert block["heel_points"] == []
    assert block["unavailable_reason"]["code"] == "synthetic_body_not_allowed_for_real_gz"
    assert isinstance(block["unavailable_reason"]["detail"], str)
    for surface_warning in HIGH_ANGLE_GZ_SURFACE_WARNINGS:
        assert surface_warning in block["warnings"]
