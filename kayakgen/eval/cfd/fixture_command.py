"""Checked-in deterministic command used by the local CFD fixture adapter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from kayakgen.eval.cfd.jobs import (
    CfdFixtureCaseInput,
    CfdFixtureCommandOutput,
    FIXTURE_CASE_TEMPLATE_VERSION,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        fixture_case = CfdFixtureCaseInput.model_validate_json(args.case.read_text())
    except (OSError, ValidationError) as exc:
        print(f"fixture command could not read case input: {exc}", file=sys.stderr)
        return 2

    result = _fixture_result(fixture_case)
    try:
        args.out.write_text(result.model_dump_json(indent=2) + "\n")
    except OSError as exc:
        print(f"fixture command could not write raw output: {exc}", file=sys.stderr)
        return 3

    print(
        "fixture CFD command wrote raw unvalidated output "
        f"for {fixture_case.job_id}"
    )
    return 0


def _fixture_result(fixture_case: CfdFixtureCaseInput) -> CfdFixtureCommandOutput:
    speed = fixture_case.speed_mps
    density = fixture_case.seawater_density_kg_m3
    mesh_factor = (sum(ord(ch) for ch in fixture_case.mesh.hull_hash[:16]) % 100) / 10000
    reference_area_m2 = 0.018 + 0.002 * len(fixture_case.mesh.parts) + mesh_factor
    drag_force_n = 0.5 * density * speed * speed * reference_area_m2
    return CfdFixtureCommandOutput(
        job_id=fixture_case.job_id,
        speed_mps=speed,
        drag_force_n=round(drag_force_n, 6),
        residual_summary={
            "continuity_l2": round(1e-6 * (1.0 + speed), 12),
            "momentum_l2": round(2e-5 / (1.0 + speed), 12),
        },
        fixture_version=FIXTURE_CASE_TEMPLATE_VERSION,
    )


if __name__ == "__main__":
    raise SystemExit(main())
