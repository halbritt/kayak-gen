"""Edinburgh DataShare Pacific-canoe hydrodynamics extractor stub.

This module is a placeholder for the eventual extraction script that converts
the Edinburgh DataShare workbook for "Hydrodynamics of Three Slender Models
Resembling Pacific Canoe Hulls" (DOI ``10.7488/ds/3785``) into a normalized
kayakgen resistance row schema.

No network calls are made by this module. The actual workbook download is an
operator step that must precede invocation; the file is then passed in as a
local ``Path``.

Expected source workbook row schema
-----------------------------------
The DataShare workbook publishes per-model measured runs. The expected
columns, in source order, are:

- ``model_id``         (str)   one of ``M1``, ``M2``, ``M3`` for the three
                                slender Pacific-canoe-like hulls.
- ``run_id``           (str)   identifier of the towing-tank run.
- ``speed_knots``      (float) towed speed in knots (source unit).
- ``drag_n``           (float) measured total drag force in newtons (N).
- ``water_temp_c``     (float) tank water temperature in degrees Celsius.
- ``trim_deg``         (float) fixed trim setting in degrees (sink/trim are
                                held fixed in the source experiment).
- ``sink_mm``          (float) fixed sinkage in millimetres.

Unit conversions applied by the extractor
-----------------------------------------
- ``speed_knots`` is converted to ``speed_ms`` using the kayakgen
  constant ``KNOTS_TO_MS``.
- ``drag_n`` is preserved as ``drag_n`` (no conversion); newtons is the
  kayakgen-internal unit for resistance.
- A model-specific waterline length ``Lwl_m`` is attached per ``model_id``
  from the dataset's CAD/geometry manifest (also part of the DOI deposit).
- Froude number ``Fn = U / sqrt(g * Lwl)`` is computed with ``g = 9.80665``
  m/s^2 and the model-specific ``Lwl_m``. This matches the RFC 0042
  Froude basis recorded on the source-review packet.

Expected normalized output columns (one row per source run)
-----------------------------------------------------------
- ``source_id``  (str)   constant ``"edinburgh_pacific_canoe_hydrodynamics"``.
- ``model_id``   (str)
- ``run_id``     (str)
- ``speed_ms``   (float) converted from ``speed_knots``.
- ``drag_n``     (float) preserved.
- ``Lwl_m``      (float) model-specific waterline length.
- ``Fn``         (float) ``speed_ms / sqrt(g * Lwl_m)``.
- ``trim_deg``   (float)
- ``sink_mm``    (float)
- ``water_temp_c`` (float)

The extractor must also stamp the workbook checksum (sha256) it ingested
into the output manifest so the kayakgen registry can refuse stale runs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

__all__ = ["EXTRACTOR_SOURCE_ID", "ExtractedRows", "extract"]

EXTRACTOR_SOURCE_ID = "edinburgh_pacific_canoe_hydrodynamics"

#: Normalized output column order. Tested by the calibration test-suite to
#: pin the schema even before the workbook is acquired.
EXPECTED_OUTPUT_COLUMNS: tuple[str, ...] = (
    "source_id",
    "model_id",
    "run_id",
    "speed_ms",
    "drag_n",
    "Lwl_m",
    "Fn",
    "trim_deg",
    "sink_mm",
    "water_temp_c",
)

#: Expected source workbook columns, in the order the script will read them.
EXPECTED_SOURCE_COLUMNS: tuple[str, ...] = (
    "model_id",
    "run_id",
    "speed_knots",
    "drag_n",
    "water_temp_c",
    "trim_deg",
    "sink_mm",
)

#: Froude basis used for the normalized ``Fn`` column.
FROUDE_BASIS: str = "Fn = U / sqrt(g * Lwl)"

#: Gravitational acceleration in m/s^2 used for the Froude basis.
GRAVITY_M_S2: float = 9.80665


ExtractedRows = list[dict[str, Any]]


def extract(workbook_path: Path) -> ExtractedRows:
    """Extract normalized rows from the Edinburgh DataShare workbook.

    Parameters
    ----------
    workbook_path:
        Local path to the previously downloaded DataShare workbook. The
        operator is responsible for verifying the checksum against the
        kayakgen source-review packet before calling this function.

    Returns
    -------
    ExtractedRows
        Sequence of dictionaries keyed by ``EXPECTED_OUTPUT_COLUMNS``.

    Raises
    ------
    NotImplementedError
        Until the workbook is acquired, checksum-bound, and a real
        extraction implementation lands, the stub raises with the
        ``pending data acquisition`` reason so callers cannot silently
        skip the review-packet gate.
    """
    raise NotImplementedError(
        "requires Edinburgh DataShare download; pending data acquisition"
    )
