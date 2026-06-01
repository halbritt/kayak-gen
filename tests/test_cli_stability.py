"""RFC 0058 stage 3 / RFC 0043 stage 4 ``kayakgen stability`` CLI smoke tests.

The deep gate coverage lives in
``tests/test_measured_stability_acceptance.py`` and
``tests/test_claim_state_measured_promotion.py``. This file keeps the
high-level smoke tests for the four commands that survived stage 4:

- ``ingest-rig-run`` — canonical-manifest writer + overwrite refusal
- ``promote-fixture`` — writes ``promotion.json`` (the on-disk
  ``AcceptedStabilityFixtureRecord``); never mutates ``manifest.json``
- ``accept-fit`` — RFC 0043 stage 4 signature ``--fit-record --fixture-id
  --out``; the prior ``--packet`` flag refuses with an explicit pointer
- ``residual-plot`` — SVG placeholder
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.stability.accepted_fit import (
    StabilityFitRecord,
    StabilityFixturePromotionPacket,
)
from kayakgen.eval.stability.measured_fixture import MeasuredStabilityFixture
from kayakgen.eval.stability.registry import (
    REASON_FIXTURE_NOT_PROMOTED,
    REASON_FIXTURE_SHA256_MISMATCH,
)

from tests.conftest import (
    StabilityAcceptanceTriple,
    make_stability_acceptance_triple,
)


def _stage_fixture_dir(
    tmp_path: Path,
    triple: StabilityAcceptanceTriple,
    *,
    write_promotion: bool = False,
) -> Path:
    fixture_dir = (
        tmp_path
        / "data"
        / "stability"
        / "fixtures"
        / triple.fixture.fixture_id
    )
    fixture_dir.mkdir(parents=True, exist_ok=True)
    (fixture_dir / "manifest.json").write_text(
        triple.fixture.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    if write_promotion:
        (fixture_dir / "promotion.json").write_text(
            triple.packet.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
    return fixture_dir


# ---------------------------------------------------------------------------
# ingest-rig-run
# ---------------------------------------------------------------------------


def test_ingest_rig_run_writes_canonical_manifest_and_refuses_overwrite(
    tmp_path: Path,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    source = tmp_path / "source.json"
    source.write_text(
        acceptance_triple.fixture.model_dump_json(), encoding="utf-8"
    )
    out = tmp_path / "fixtures" / acceptance_triple.fixture.fixture_id
    runner = CliRunner()

    first = runner.invoke(
        app, ["stability", "ingest-rig-run", str(source), "--out", str(out)]
    )
    assert first.exit_code == 0, first.output
    rebuilt = MeasuredStabilityFixture.model_validate_json(
        (out / "manifest.json").read_text()
    )
    assert rebuilt.fixture_id == acceptance_triple.fixture.fixture_id

    second = runner.invoke(
        app, ["stability", "ingest-rig-run", str(source), "--out", str(out)]
    )
    assert second.exit_code == 1
    assert "refusing to overwrite" in second.output


def test_ingest_rig_run_refuses_invalid_manifest(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"fixture_id": "missing-required-fields"}', encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["stability", "ingest-rig-run", str(bad), "--out", str(tmp_path / "out")],
    )

    assert result.exit_code == 1
    assert "ingest-rig-run failed" in result.output
    assert not (tmp_path / "out" / "manifest.json").exists()


# ---------------------------------------------------------------------------
# promote-fixture
# ---------------------------------------------------------------------------


def test_promote_fixture_writes_promotion_json_without_mutating_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    fixture_dir = _stage_fixture_dir(tmp_path, acceptance_triple)
    manifest_bytes = (fixture_dir / "manifest.json").read_bytes()
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(
        acceptance_triple.packet.model_dump_json(), encoding="utf-8"
    )

    result = CliRunner().invoke(
        app,
        [
            "stability",
            "promote-fixture",
            acceptance_triple.fixture.fixture_id,
            "--packet",
            str(packet_path),
        ],
    )

    assert result.exit_code == 0, result.output
    promotion = fixture_dir / "promotion.json"
    rebuilt = StabilityFixturePromotionPacket.model_validate_json(
        promotion.read_text()
    )
    assert rebuilt == acceptance_triple.packet
    assert (fixture_dir / "manifest.json").read_bytes() == manifest_bytes


def test_promote_fixture_refuses_sha256_mismatch_with_structured_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    triple = make_stability_acceptance_triple()
    other_triple = make_stability_acceptance_triple(scan_hash="b" * 64)
    # Stage triple's manifest, but pass other_triple's packet (its
    # fixture_sha256 cites a different manifest's bytes).
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, triple)
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(other_triple.packet.model_dump_json(), encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "stability",
            "promote-fixture",
            triple.fixture.fixture_id,
            "--packet",
            str(packet_path),
        ],
    )

    assert result.exit_code == 1
    body = json.loads(
        next(line for line in result.output.splitlines() if line.startswith("{"))
    )
    assert body["code"] == REASON_FIXTURE_SHA256_MISMATCH
    assert (
        tmp_path
        / "data"
        / "stability"
        / "fixtures"
        / triple.fixture.fixture_id
        / "promotion.json"
    ).exists() is False


def test_promote_fixture_refuses_invalid_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, acceptance_triple)
    packet = tmp_path / "invalid-packet.json"
    payload = json.loads(acceptance_triple.packet.model_dump_json())
    payload["rig_design_match"] = False
    packet.write_text(json.dumps(payload), encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "stability",
            "promote-fixture",
            acceptance_triple.fixture.fixture_id,
            "--packet",
            str(packet),
        ],
    )

    assert result.exit_code == 1
    assert "rig_design_match=True" in result.output


# ---------------------------------------------------------------------------
# accept-fit (RFC 0043 stage 4 signature)
# ---------------------------------------------------------------------------


def test_accept_fit_writes_record_and_refuses_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, acceptance_triple, write_promotion=True)
    fit_path = tmp_path / "fit.json"
    fit_path.write_text(acceptance_triple.fit.model_dump_json(), encoding="utf-8")
    out = tmp_path / "data" / "stability" / "fits" / "stability-fit-001.json"
    runner = CliRunner()

    first = runner.invoke(
        app,
        [
            "stability",
            "accept-fit",
            "--fit-record",
            str(fit_path),
            "--fixture-id",
            acceptance_triple.fixture.fixture_id,
            "--out",
            str(out),
        ],
    )

    assert first.exit_code == 0, first.output
    rebuilt = StabilityFitRecord.model_validate_json(out.read_text())
    assert rebuilt.fit_id == acceptance_triple.fit.fit_id
    assert rebuilt.acceptance_verdict == "accepted"
    assert rebuilt.strict is True

    second = runner.invoke(
        app,
        [
            "stability",
            "accept-fit",
            "--fit-record",
            str(fit_path),
            "--fixture-id",
            acceptance_triple.fixture.fixture_id,
            "--out",
            str(out),
        ],
    )
    assert second.exit_code == 1
    assert "refusing to overwrite" in second.output


def test_accept_fit_refuses_unpromoted_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    fixture_dir = _stage_fixture_dir(tmp_path, acceptance_triple)
    candidate_packet = StabilityFixturePromotionPacket.model_validate({
        **acceptance_triple.packet.model_dump(),
        "promotion_target": "validation_candidate",
        "rejection_reasons": ["keep as candidate"],
    })
    (fixture_dir / "promotion.json").write_text(
        candidate_packet.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    fit_path = tmp_path / "fit.json"
    fit_path.write_text(acceptance_triple.fit.model_dump_json(), encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "stability",
            "accept-fit",
            "--fit-record",
            str(fit_path),
            "--fixture-id",
            acceptance_triple.fixture.fixture_id,
            "--out",
            str(tmp_path / "out.json"),
        ],
    )

    assert result.exit_code == 1
    body = json.loads(
        next(line for line in result.output.splitlines() if line.startswith("{"))
    )
    assert body["code"] == REASON_FIXTURE_NOT_PROMOTED


def test_accept_fit_legacy_packet_flag_refuses_with_pointer_to_fixture_id(
    tmp_path: Path,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    fit_path = tmp_path / "fit.json"
    fit_path.write_text(acceptance_triple.fit.model_dump_json(), encoding="utf-8")
    out = tmp_path / "out.json"

    result = CliRunner().invoke(
        app,
        [
            "stability",
            "accept-fit",
            "--fit-record",
            str(fit_path),
            "--fixture-id",
            acceptance_triple.fixture.fixture_id,
            "--out",
            str(out),
            "--packet",
            "legacy.json",
        ],
    )

    assert result.exit_code == 2
    assert "--packet was REMOVED" in result.output
    assert "--fixture-id" in result.output


# ---------------------------------------------------------------------------
# residual-plot
# ---------------------------------------------------------------------------


def test_residual_plot_writes_svg_stub_with_metrics(
    tmp_path: Path,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    fit = tmp_path / "fit.json"
    fit.write_text(acceptance_triple.fit.model_dump_json(), encoding="utf-8")
    out = tmp_path / "residuals.svg"

    result = CliRunner().invoke(
        app, ["stability", "residual-plot", str(fit), "--out", str(out)]
    )

    assert result.exit_code == 0, result.output
    svg = out.read_text(encoding="utf-8")
    assert "<svg" in svg
    assert acceptance_triple.fit.fit_id in svg
    assert "validation_candidate vs reference" in svg
