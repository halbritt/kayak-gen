"""RFC 0043 stage 4 — ``kayakgen stability ingest-rig-run`` CLI tests.

Covers the schema-validator paths the ingest CLI surfaces verbatim plus the
manifest-immutability invariant after a ``promote-fixture`` round-trip
(``manifest.json`` MUST be byte-equal to the original ingest output — RFC 0043
§B.1).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.eval.stability.measured_fixture import (
    FreeEquilibriumPoint,
    FreeEquilibriumTrace,
    MeasuredStabilityFixture,
    MeasuredStabilityRow,
)

from tests.conftest import (
    StabilityAcceptanceTriple,
    make_stability_acceptance_triple,
)


def test_ingest_rig_run_writes_canonical_manifest(
    tmp_path: Path,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    source = tmp_path / "source.json"
    source.write_text(
        acceptance_triple.fixture.model_dump_json(), encoding="utf-8"
    )
    out_dir = tmp_path / "fixtures" / acceptance_triple.fixture.fixture_id

    result = CliRunner().invoke(
        app, ["stability", "ingest-rig-run", str(source), "--out", str(out_dir)]
    )

    assert result.exit_code == 0, result.output
    manifest_path = out_dir / "manifest.json"
    rebuilt = MeasuredStabilityFixture.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    assert rebuilt.fixture_id == acceptance_triple.fixture.fixture_id


def test_ingest_rig_run_does_not_mutate_intended_use(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_triple: StabilityAcceptanceTriple,
) -> None:
    monkeypatch.chdir(tmp_path)
    fixture_dir = (
        tmp_path / "data" / "stability" / "fixtures" / acceptance_triple.fixture.fixture_id
    )
    fixture_dir.mkdir(parents=True)
    # Write the canonical (indent=2) manifest, mirroring ingest-rig-run's writer.
    manifest = fixture_dir / "manifest.json"
    manifest_bytes = acceptance_triple.fixture.model_dump_json(indent=2) + "\n"
    manifest.write_text(manifest_bytes, encoding="utf-8")
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
    assert manifest.read_text(encoding="utf-8") == manifest_bytes


def test_ingest_rig_run_refuses_constrained_trace_promotion() -> None:
    triple = make_stability_acceptance_triple()
    payload = triple.fixture.model_dump()
    payload["free_equilibrium_trace"] = FreeEquilibriumTrace(
        points=[
            FreeEquilibriumPoint(theta_deg=0.0, trim_deg=0.0, heave_m=0.0),
            FreeEquilibriumPoint(theta_deg=15.0, trim_deg=0.5, heave_m=-0.005),
            FreeEquilibriumPoint(theta_deg=30.0, trim_deg=1.2, heave_m=-0.012),
        ],
        constrained_trim=True,
    ).model_dump()
    payload["intended_use"] = "measured_stability_fixture"

    with pytest.raises(ValidationError, match="constrained_trace_blocks_promotion"):
        MeasuredStabilityFixture.model_validate(payload)


def test_ingest_rig_run_refuses_rows_outside_valid_heel_range() -> None:
    triple = make_stability_acceptance_triple()
    payload = triple.fixture.model_dump()
    payload["valid_heel_range_deg"] = (0.0, 30.0)
    payload["rows"] = [
        MeasuredStabilityRow(theta_deg=0.0, gz_m=0.0).model_dump(),
        MeasuredStabilityRow(theta_deg=45.0, gz_m=0.05).model_dump(),
        MeasuredStabilityRow(theta_deg=60.0, gz_m=0.06).model_dump(),
    ]

    with pytest.raises(ValidationError, match="rows_outside_valid_heel_range"):
        MeasuredStabilityFixture.model_validate(payload)
