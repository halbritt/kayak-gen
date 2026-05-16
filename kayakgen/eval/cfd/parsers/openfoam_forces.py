"""OpenFOAM v2512 ``forces`` function-object ``force.dat`` parser.

Split out from the historical ``kayakgen.eval.cfd.jobs`` per Phase 3A
of ``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from kayakgen.eval.claims import (
    RawUnvalidatedClaimFields,
    WARNING_RAW_CFD_UNVALIDATED,
)
from kayakgen.eval.cfd.profiles import CFD_OPENFOAM_RESULTS_WARNING
from kayakgen.eval.cfd.records import CfdDispatchError

_FLOAT_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
_OPENFOAM_V2512_HEADER_TOKENS = ("forces", "pressure", "viscous", "porous")
# v2512 ``forces`` FO writes a tabular force.dat. Rows have 10 fields by
# default (time + total + pressure + viscous components) and 13 fields when
# porous contributions are written. moments live in a separate moment.dat
# file and are not parsed by parse_openfoam_force_dat.
_OPENFOAM_V2512_FORCE_DAT_FIELDS = 10
_OPENFOAM_V2512_FORCE_DAT_FIELDS_WITH_POROUS = 13


class CfdOpenFoamForceDatSample(BaseModel):
    """One parsed OpenFOAM v2512 ``forces`` function-object sample.

    The v2512 ``forces`` FO writes a separate ``force.dat`` and ``moment.dat``
    under ``postProcessing/<name>/<startTime>/``. Each ``force.dat`` data row
    has 10 numeric fields by default
    (``time total_x total_y total_z pressure_x pressure_y pressure_z
    viscous_x viscous_y viscous_z``) and 13 fields when the case has porous
    zones and the FO is configured to write porous contributions
    (``... porous_x porous_y porous_z``).
    """

    model_config = ConfigDict(extra="forbid")

    time_s: float
    pressure_force_n: tuple[float, float, float]
    viscous_force_n: tuple[float, float, float]
    porous_force_n: tuple[float, float, float]
    total_force_n: tuple[float, float, float]
    drag_force_n: float
    porous_recorded: bool = False


class CfdOpenFoamForceDatResult(RawUnvalidatedClaimFields):
    """Parsed raw force.dat values from the selected OpenFOAM adapter scope."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    source_ref: str
    sample_count: int = Field(ge=1)
    last_sample: CfdOpenFoamForceDatSample
    result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"


def _openfoam_warnings() -> list[str]:
    return [WARNING_RAW_CFD_UNVALIDATED, CFD_OPENFOAM_RESULTS_WARNING]


def _vector3(values: list[float]) -> tuple[float, float, float]:
    return (values[0], values[1], values[2])


def _parse_openfoam_force_dat_line(
    line: str,
    *,
    line_number: int,
) -> CfdOpenFoamForceDatSample:
    values = [float(match.group(0)) for match in _FLOAT_RE.finditer(line)]
    porous_recorded = False
    if len(values) == _OPENFOAM_V2512_FORCE_DAT_FIELDS:
        porous_recorded = False
    elif len(values) == _OPENFOAM_V2512_FORCE_DAT_FIELDS_WITH_POROUS:
        porous_recorded = True
    else:
        raise CfdDispatchError(
            (
                f"OpenFOAM force.dat line {line_number} has {len(values)} numeric "
                f"fields; v2512 tabular layout requires "
                f"{_OPENFOAM_V2512_FORCE_DAT_FIELDS} fields "
                f"({_OPENFOAM_V2512_FORCE_DAT_FIELDS_WITH_POROUS} with porous)"
            ),
            code="malformed_output",
        )

    total = _vector3(values[1:4])
    pressure = _vector3(values[4:7])
    viscous = _vector3(values[7:10])
    if porous_recorded:
        porous = _vector3(values[10:13])
    else:
        porous = (0.0, 0.0, 0.0)
    return CfdOpenFoamForceDatSample(
        time_s=values[0],
        pressure_force_n=pressure,
        viscous_force_n=viscous,
        porous_force_n=porous,
        total_force_n=total,
        drag_force_n=total[0],
        porous_recorded=porous_recorded,
    )


def parse_openfoam_force_dat(
    path: str | Path,
    *,
    source_ref: str | None = None,
) -> CfdOpenFoamForceDatResult:
    """Parse a v2512 ``forces`` function-object ``force.dat`` file.

    The accepted layout is the tabular v2512 ``forces`` FO format. Each data
    row carries 10 numeric fields by default
    (``time total_x total_y total_z pressure_x pressure_y pressure_z
    viscous_x viscous_y viscous_z``) and 13 numeric fields when the case has
    porous zones and the FO is configured to write porous contributions
    (``... porous_x porous_y porous_z``).

    Older Foam-extend / pre-v2306 parenthesised-tuple layouts
    (``((px py pz) (vx vy vz))``) are rejected with
    ``code='unsupported_layout'`` so a stale solver build is not silently
    accepted as v2512 evidence.

    Moments are written to a separate ``moment.dat`` file by the same FO
    and are not parsed here.
    """
    force_path = Path(path)
    try:
        text = force_path.read_text()
    except FileNotFoundError as exc:
        raise CfdDispatchError(
            f"OpenFOAM force.dat not found: {force_path}",
            code="missing_output",
        ) from exc

    lines = text.splitlines()
    header_lines = [line for line in lines if line.strip().startswith("#")]
    header_blob = "\n".join(header_lines).lower()
    has_tabular_header = "total_x" in header_blob or (
        "pressure_x" in header_blob and "viscous_x" in header_blob
    )
    has_legacy_paren_header = "forces(pressure" in header_blob or "(pressure viscous" in header_blob
    if has_legacy_paren_header and not has_tabular_header:
        raise CfdDispatchError(
            (
                f"OpenFOAM force.dat header is not v2512 tabular layout "
                f"(legacy parenthesised-tuple format): {force_path}"
            ),
            code="unsupported_layout",
        )

    samples: list[CfdOpenFoamForceDatSample] = []
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        samples.append(_parse_openfoam_force_dat_line(stripped, line_number=line_number))

    if not samples:
        raise CfdDispatchError(
            f"OpenFOAM force.dat contains no data rows: {force_path}",
            code="malformed_output",
        )

    return CfdOpenFoamForceDatResult(
        source_ref=source_ref or force_path.as_posix(),
        sample_count=len(samples),
        last_sample=samples[-1],
        warnings=_openfoam_warnings(),
    )


__all__ = [
    "CfdOpenFoamForceDatResult",
    "CfdOpenFoamForceDatSample",
    "parse_openfoam_force_dat",
]
