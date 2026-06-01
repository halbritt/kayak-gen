"""RFC 0043 stage 4 — ``promote-fixture`` + ``accept-fit`` CLI gate tests.

Each refusal path the §B gate list names has a test. The acceptance triple
factory is in ``tests/conftest.py``; failing variants are derived by overriding
a single keyword argument.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.stability.accepted_fit import (
    FixtureRef,
    StabilityFitMetrics,
    StabilityFitRecord,
    StabilityFixturePromotionPacket,
)
from kayakgen.eval.stability.measured_fixture import MeasuredStabilityFixture
from kayakgen.eval.stability.registry import (
    REASON_EVALUATOR_VERSION_MISMATCH,
    REASON_FIT_METRICS_OUT_OF_THRESHOLDS,
    REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE,
    REASON_FIXTURE_MANIFEST_MISSING,
    REASON_FIXTURE_NOT_PROMOTED,
    REASON_FIXTURE_SHA256_MISMATCH,
    REASON_NEXT_ACTION,
    REASON_PROMOTION_PACKET_MISSING,
    REASON_STRICT_CHECK_SKIPPED,
    REASON_VALID_HEEL_RANGE_DISJOINT,
    fixture_canonical_sha256,
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


def _refusal(output: str) -> dict[str, object]:
    """Parse the structured JSON refusal line from CLI output."""

    line = next((s for s in output.splitlines() if s.startswith("{")), None)
    assert line is not None, f"no JSON refusal in output: {output!r}"
    return json.loads(line)


# ---------------------------------------------------------------------------
# promote-fixture
# ---------------------------------------------------------------------------


def test_promote_fixture_writes_accepted_fixture_record(
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
    promotion_path = fixture_dir / "promotion.json"
    rebuilt = StabilityFixturePromotionPacket.model_validate_json(
        promotion_path.read_text(encoding="utf-8")
    )
    assert rebuilt == acceptance_triple.packet
    assert (fixture_dir / "manifest.json").read_bytes() == manifest_bytes


def test_promote_fixture_refuses_sha256_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    fixture_dir = _stage_fixture_dir(tmp_path, acceptance_triple)
    # Tamper the manifest AFTER computing the legitimate sha by appending a
    # benign warning — Pydantic round-trip still validates but the canonical
    # bytes change, so the packet's fixture_sha256 no longer matches.
    payload = json.loads((fixture_dir / "manifest.json").read_text())
    payload["warnings"] = ["tampered_after_sign"]
    tampered = MeasuredStabilityFixture.model_validate(payload)
    (fixture_dir / "manifest.json").write_text(
        tampered.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
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

    assert result.exit_code == 1
    body = _refusal(result.output)
    assert body["code"] == REASON_FIXTURE_SHA256_MISMATCH
    assert body["next_action"] == REASON_NEXT_ACTION[REASON_FIXTURE_SHA256_MISMATCH]
    assert not (fixture_dir / "promotion.json").exists()


def test_promote_fixture_refuses_unaccepted_reviews() -> None:
    triple = make_stability_acceptance_triple()
    payload = triple.packet.model_dump()
    payload["rights_review"] = "deferred"

    with pytest.raises(ValidationError, match="every review verdict to be 'accepted'"):
        StabilityFixturePromotionPacket.model_validate(payload)


def test_promote_fixture_refuses_rig_design_mismatch() -> None:
    triple = make_stability_acceptance_triple()
    payload = triple.packet.model_dump()
    payload["rig_design_match"] = False

    with pytest.raises(ValidationError, match="rig_design_match=True"):
        StabilityFixturePromotionPacket.model_validate(payload)


def test_promote_fixture_persists_submitted_bytes_verbatim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    """Threat-model review, finding 4: the on-disk promotion.json bytes MUST
    equal the submitted packet bytes byte-for-byte; the CLI is not allowed to
    canonicalize the operator's signed bytes (or "re-promote = no-op" loses
    its meaning)."""
    monkeypatch.chdir(tmp_path)
    fixture_dir = _stage_fixture_dir(tmp_path, acceptance_triple)
    packet_path = tmp_path / "packet.json"
    # Deliberately UNINDENTED single-line bytes (the CLI's previous
    # implementation canonicalized to indent=2).
    packet_text = acceptance_triple.packet.model_dump_json()
    packet_path.write_text(packet_text, encoding="utf-8")

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
    on_disk = (fixture_dir / "promotion.json").read_text(encoding="utf-8")
    assert on_disk == packet_text


def test_promote_fixture_re_promote_identical_packet_is_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, acceptance_triple)
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(
        acceptance_triple.packet.model_dump_json(), encoding="utf-8"
    )
    runner = CliRunner()
    args = [
        "stability",
        "promote-fixture",
        acceptance_triple.fixture.fixture_id,
        "--packet",
        str(packet_path),
    ]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "no-op" in second.output


# ---------------------------------------------------------------------------
# accept-fit happy path + gate refusals
# ---------------------------------------------------------------------------


def _write_fit(tmp_path: Path, fit: StabilityFitRecord) -> Path:
    fit_path = tmp_path / "fit.json"
    fit_path.write_text(fit.model_dump_json(), encoding="utf-8")
    return fit_path


def test_accept_fit_binds_to_promoted_fixture_happy_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, acceptance_triple, write_promotion=True)
    fit_path = _write_fit(tmp_path, acceptance_triple.fit)
    out = tmp_path / "out" / "stability-fit-001.json"

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
        ],
    )

    assert result.exit_code == 0, result.output
    rebuilt = StabilityFitRecord.model_validate_json(out.read_text(encoding="utf-8"))
    assert rebuilt.acceptance_verdict == "accepted"
    assert rebuilt.strict is True


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
    fit_path = _write_fit(tmp_path, acceptance_triple.fit)
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
        ],
    )

    assert result.exit_code == 1
    assert _refusal(result.output)["code"] == REASON_FIXTURE_NOT_PROMOTED


def test_accept_fit_refuses_missing_promotion_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, acceptance_triple)
    fit_path = _write_fit(tmp_path, acceptance_triple.fit)
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
        ],
    )

    assert result.exit_code == 1
    assert _refusal(result.output)["code"] == REASON_PROMOTION_PACKET_MISSING


def test_accept_fit_refuses_missing_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    fit_path = _write_fit(tmp_path, acceptance_triple.fit)
    out = tmp_path / "out.json"

    result = CliRunner().invoke(
        app,
        [
            "stability",
            "accept-fit",
            "--fit-record",
            str(fit_path),
            "--fixture-id",
            "does-not-exist",
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 1
    assert _refusal(result.output)["code"] == REASON_FIXTURE_MANIFEST_MISSING


def test_accept_fit_refuses_evaluator_version_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    triple = make_stability_acceptance_triple(
        evaluator_version="some-stale-version-v0"
    )
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, triple, write_promotion=True)
    fit_path = _write_fit(tmp_path, triple.fit)
    out = tmp_path / "out.json"

    result = CliRunner().invoke(
        app,
        [
            "stability",
            "accept-fit",
            "--fit-record",
            str(fit_path),
            "--fixture-id",
            triple.fixture.fixture_id,
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 1
    assert _refusal(result.output)["code"] == REASON_EVALUATOR_VERSION_MISMATCH


def test_accept_fit_refuses_disjoint_heel_range(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    triple = make_stability_acceptance_triple(fit_heel_range=(40.0, 60.0))
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, triple, write_promotion=True)
    fit_path = _write_fit(tmp_path, triple.fit)
    out = tmp_path / "out.json"

    result = CliRunner().invoke(
        app,
        [
            "stability",
            "accept-fit",
            "--fit-record",
            str(fit_path),
            "--fixture-id",
            triple.fixture.fixture_id,
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 1
    assert _refusal(result.output)["code"] == REASON_VALID_HEEL_RANGE_DISJOINT


@pytest.mark.parametrize(
    "metric_overrides",
    [
        {"rmse_m": 0.02},  # exceeds 0.005
        {"mape_fraction": 0.2},  # exceeds 0.05
        {"max_error_m": 0.05},  # exceeds 0.01
        {"coverage_fraction": 0.5},  # below 0.9
    ],
)
def test_accept_fit_refuses_below_strict_thresholds(metric_overrides: dict) -> None:
    triple = make_stability_acceptance_triple()
    payload = triple.fit.model_dump()
    payload["fit_metrics"] = {
        **payload["fit_metrics"],
        **metric_overrides,
    }

    with pytest.raises(
        ValidationError, match="stability_fit_metrics_outside_default_thresholds"
    ):
        StabilityFitRecord.model_validate(payload)


def test_accept_fit_refuses_strict_check_skipped_with_accepted_verdict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    triple = make_stability_acceptance_triple(strict=False)
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, triple, write_promotion=True)
    fit_path = _write_fit(tmp_path, triple.fit)
    out = tmp_path / "out.json"

    result = CliRunner().invoke(
        app,
        [
            "stability",
            "accept-fit",
            "--fit-record",
            str(fit_path),
            "--fixture-id",
            triple.fixture.fixture_id,
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 1
    assert _refusal(result.output)["code"] == REASON_STRICT_CHECK_SKIPPED


def test_accept_fit_refuses_fit_record_does_not_cite_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, acceptance_triple, write_promotion=True)
    # Build a fit that cites a different fixture id.
    payload = acceptance_triple.fit.model_dump()
    payload["fixtures"] = [
        FixtureRef(
            fixture_id="some-other-fixture",
            fixture_path="data/stability/fixtures/some-other-fixture/manifest.json",
            fixture_sha256=fixture_canonical_sha256(acceptance_triple.fixture),
        ).model_dump()
    ]
    other_cite = StabilityFitRecord.model_validate(payload)
    fit_path = _write_fit(tmp_path, other_cite)
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
        ],
    )

    assert result.exit_code == 1
    assert _refusal(result.output)["code"] == REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE


def test_accept_fit_refuses_legacy_packet_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    fit_path = _write_fit(tmp_path, acceptance_triple.fit)
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
            "old-packet.json",
        ],
    )

    assert result.exit_code == 2
    assert "--packet was REMOVED" in result.output
    assert "--fixture-id" in result.output


def test_accept_fit_writes_record_byte_stable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, acceptance_triple, write_promotion=True)
    fit_path = _write_fit(tmp_path, acceptance_triple.fit)
    out1 = tmp_path / "fits" / "first.json"
    out2 = tmp_path / "fits" / "second.json"
    runner = CliRunner()

    runner.invoke(
        app,
        [
            "stability",
            "accept-fit",
            "--fit-record",
            str(fit_path),
            "--fixture-id",
            acceptance_triple.fixture.fixture_id,
            "--out",
            str(out1),
        ],
    )
    runner.invoke(
        app,
        [
            "stability",
            "accept-fit",
            "--fit-record",
            str(fit_path),
            "--fixture-id",
            acceptance_triple.fixture.fixture_id,
            "--out",
            str(out2),
        ],
    )

    assert out1.read_bytes() == out2.read_bytes()


def test_accept_fit_refuses_fit_metrics_out_of_thresholds_on_rejected_verdict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    _stage_fixture_dir(tmp_path, acceptance_triple, write_promotion=True)
    payload = acceptance_triple.fit.model_dump()
    payload["acceptance_verdict"] = "rejected"
    payload["rejection_reasons"] = ["operator rejected"]
    payload["accepted_at"] = None
    payload["fit_metrics"] = {
        **payload["fit_metrics"],
        "rmse_m": 0.02,  # exceed strict to allow rejection
    }
    payload["strict"] = False
    rejected_fit = StabilityFitRecord.model_validate(payload)
    fit_path = _write_fit(tmp_path, rejected_fit)
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
        ],
    )

    # strict=False is refused first (gate 11 first arm).
    assert result.exit_code == 1
    code = _refusal(result.output)["code"]
    assert code in {REASON_STRICT_CHECK_SKIPPED, REASON_FIT_METRICS_OUT_OF_THRESHOLDS}


# Helper kept here so callers in this file can stage a custom metrics fit
# without touching the conftest factory's strict default.
def test_strict_metrics_threshold_constants_are_synthesis_aligned() -> None:
    metrics = StabilityFitMetrics(
        rmse_m=0.005,
        mape_fraction=0.05,
        max_error_m=0.01,
        coverage_fraction=0.9,
    )
    assert metrics.rmse_m == 0.005
