"""Edinburgh DataShare Pacific-canoe hydrodynamics extractor.

Reads the workbook
``FixedSink_and_TrimDataAnalysis20221114V15_IMV.xlsx`` (DOI
``10.7488/ds/3785``) into a normalized list of per-run measured rows.

The workbook is operator-supplied. The package bundles a checksum-bound copy
under ``tests/fixtures/calibration/edinburgh/`` for reproducible tests, but
the runtime extractor only requires a local path; it does no network access.

Per RFC 0042 / decision D013, this dataset is reviewed as a
``validation_candidate`` capped at ``validation_fixture``. The
``outside_sea_kayak_calibration_envelope`` non-promotion reason still applies
because the models are slender Pacific outrigger / canoe hulls, not sea
kayak / surfski hulls.

Source workbook structure
-------------------------
Sheet ``Averaged Data`` (78 rows; multi-row header on rows 9-12).
Data rows start at row 14. Column order, with the units row in row 12:

============= =============== ========= ==================================
column name   units row token kind      meaning
============= =============== ========= ==================================
Day           (none)          str       e.g. ``D1``, ``D2`` (test day)
Model         shape           str       model id: ``V1``, ``V2``, ``V3``
                                        (the three slender hulls)
Test          number          int       per-day run number; <1 marks
                                        setup / rejected runs
Yaw           deg             float     heading angle in degrees
Speed         m/s             float     set carriage speed
Stbd Drag     N               float     starboard towing post drag force
Port Drag     N               float     port towing post drag force
FWD Side      N               float     forward side force
AFT Side      N               float     aft side force
Heave         mm              float     model vertical displacement
Pitch         deg             float     model trim angle (fixed during run)
Velocity      m/s             float     measured carriage velocity
Time          (free)          str/None  optional clock or duration note
Comment       (free)          str/None  free-form run notes
============= =============== ========= ==================================

The ``Froude Scaling`` sheet records the model waterline length
``Lm = 1.2 m`` and full-scale length ``Lfs = 12 m``; that ``Lm`` is the
Froude basis for all three models.

Normalized output schema
------------------------
One dict per data row (after filtering setup / non-test rows, see below).
Output column order is pinned by ``EXPECTED_OUTPUT_COLUMNS``.

==================== ======== =================================================
key                  type     definition
==================== ======== =================================================
``source_id``        str      ``"edinburgh_pacific_canoe_hydrodynamics"``
``day``              str      copied from ``Day``
``model``            str      copied from ``Model`` (``V1``/``V2``/``V3``)
``run_id``           int      copied from ``Test``
``yaw_deg``          float    copied from ``Yaw``
``speed_ms``         float    copied from ``Speed`` (set carriage speed)
``stbd_drag_n``      float    copied from ``Stbd Drag Force``
``port_drag_n``      float    copied from ``Port Drag Force``
``total_drag_n``     float    ``stbd_drag_n + port_drag_n``
``fwd_side_force_n`` float    copied from ``FWD Side Force``
``aft_side_force_n`` float    copied from ``AFT Side Force``
``heave_mm``         float    copied from ``Heave``
``pitch_deg``        float    copied from ``Pitch``
``velocity_ms``      float    copied from ``Velocity`` (measured)
``Lwl_m``            float    ``1.2`` for every row (per Froude Scaling sheet)
``Fn``               float    Froude number ``Fn = U / sqrt(g * Lwl)``
                              with ``U = velocity_ms``; ``0.0`` when
                              ``velocity_ms <= 0``
``time``             str|None copied from ``Time``
``comment``          str|None copied from ``Comment``
==================== ======== =================================================

Filtering
---------
Rows are filtered out when *any* of:

- ``Day`` is missing (separator / notes-only rows);
- ``Model`` is missing;
- ``Test`` is missing, non-numeric, or ``< 1`` (setup, zero, or rejected
  records marked with negative test numbers — see comments in the workbook).

Zero-speed and zero-yaw rows are kept because the source workbook treats
them as part of the test program; downstream callers decide how to
interpret them.

This extractor never modifies the source workbook.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

__all__ = [
    "EXTRACTOR_SOURCE_ID",
    "EXPECTED_OUTPUT_COLUMNS",
    "EXPECTED_SOURCE_COLUMNS",
    "FROUDE_BASIS",
    "GRAVITY_M_S2",
    "MODEL_LWL_M",
    "WORKBOOK_SHEET",
    "WORKBOOK_HEADER_ROW",
    "WORKBOOK_DATA_START_ROW",
    "ExtractedRows",
    "extract",
]

EXTRACTOR_SOURCE_ID = "edinburgh_pacific_canoe_hydrodynamics"

WORKBOOK_SHEET = "Averaged Data"

#: 1-based row index of the column-name header in the source workbook.
WORKBOOK_HEADER_ROW = 12

#: 1-based row index of the first data row.
WORKBOOK_DATA_START_ROW = 15

#: Source column order in the workbook's ``Averaged Data`` sheet.
EXPECTED_SOURCE_COLUMNS: tuple[str, ...] = (
    "Day",
    "Model",
    "Test",
    "Yaw",
    "Speed",
    "Stbd Drag Force",
    "Port Drag Force",
    "FWD Side Force",
    "AFT Side Force",
    "Heave",
    "Pitch",
    "Velocity",
    "Time",
    "Comment",
)

#: Normalized output column order. Pinned by tests.
EXPECTED_OUTPUT_COLUMNS: tuple[str, ...] = (
    "source_id",
    "day",
    "model",
    "run_id",
    "yaw_deg",
    "speed_ms",
    "stbd_drag_n",
    "port_drag_n",
    "total_drag_n",
    "fwd_side_force_n",
    "aft_side_force_n",
    "heave_mm",
    "pitch_deg",
    "velocity_ms",
    "Lwl_m",
    "Fn",
    "time",
    "comment",
)

#: Froude basis used for the normalized ``Fn`` column.
FROUDE_BASIS: str = "Fn = U / sqrt(g * Lwl)"

#: Gravitational acceleration in m/s^2 used for the Froude basis.
GRAVITY_M_S2: float = 9.80665

#: Per-model waterline length in metres. The Froude Scaling sheet records
#: ``Lm = 1.2`` for the three vendored models V1/V2/V3.
MODEL_LWL_M: dict[str, float] = {"V1": 1.2, "V2": 1.2, "V3": 1.2}


ExtractedRows = list[dict[str, Any]]


def _coerce_run_id(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if not float(value).is_integer():
            return None
        return int(value)
    return None


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return str(value)


def _coerce_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return 0.0
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _froude(velocity_ms: float, lwl_m: float) -> float:
    if velocity_ms <= 0.0 or lwl_m <= 0.0:
        return 0.0
    return velocity_ms / math.sqrt(GRAVITY_M_S2 * lwl_m)


def extract(workbook_path: Path) -> ExtractedRows:
    """Extract normalized rows from the Edinburgh DataShare workbook.

    Parameters
    ----------
    workbook_path:
        Local path to a previously downloaded copy of
        ``FixedSink_and_TrimDataAnalysis20221114V15_IMV.xlsx``. The caller
        is responsible for verifying the file's SHA-256 against the
        kayakgen source-review packet before invoking the extractor.

    Returns
    -------
    ExtractedRows
        Sequence of dictionaries with the keys listed in
        ``EXPECTED_OUTPUT_COLUMNS``, one per accepted source row. Filtering
        rules are documented in the module docstring.

    Raises
    ------
    FileNotFoundError
        If ``workbook_path`` does not exist.
    ImportError
        If the optional ``openpyxl`` dependency is not installed; install
        ``kayakgen[calibration]`` or add ``openpyxl`` to the active
        environment.
    """

    workbook_path = Path(workbook_path)
    if not workbook_path.is_file():
        raise FileNotFoundError(f"Edinburgh workbook not found at {workbook_path}")

    try:
        import openpyxl  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - dependency check
        raise ImportError(
            "Edinburgh extractor requires the 'openpyxl' package. "
            "Install kayakgen[calibration] or add openpyxl to the environment."
        ) from exc

    workbook = openpyxl.load_workbook(
        workbook_path,
        data_only=True,
        read_only=True,
    )
    try:
        sheet = workbook[WORKBOOK_SHEET]
    except KeyError as exc:
        raise ValueError(
            f"Edinburgh workbook is missing required sheet '{WORKBOOK_SHEET}'."
        ) from exc

    rows: ExtractedRows = []
    for raw in sheet.iter_rows(
        min_row=WORKBOOK_DATA_START_ROW,
        max_col=len(EXPECTED_SOURCE_COLUMNS),
        values_only=True,
    ):
        day = _coerce_str(raw[0])
        model = _coerce_str(raw[1])
        run_id = _coerce_run_id(raw[2])
        if day is None or model is None or run_id is None or run_id < 1:
            continue

        speed_ms = _coerce_float(raw[4])
        stbd = _coerce_float(raw[5])
        port = _coerce_float(raw[6])
        velocity_ms = _coerce_float(raw[11])
        lwl_m = MODEL_LWL_M.get(model, 1.2)

        rows.append(
            {
                "source_id": EXTRACTOR_SOURCE_ID,
                "day": day,
                "model": model,
                "run_id": run_id,
                "yaw_deg": _coerce_float(raw[3]),
                "speed_ms": speed_ms,
                "stbd_drag_n": stbd,
                "port_drag_n": port,
                "total_drag_n": stbd + port,
                "fwd_side_force_n": _coerce_float(raw[7]),
                "aft_side_force_n": _coerce_float(raw[8]),
                "heave_mm": _coerce_float(raw[9]),
                "pitch_deg": _coerce_float(raw[10]),
                "velocity_ms": velocity_ms,
                "Lwl_m": lwl_m,
                "Fn": _froude(velocity_ms, lwl_m),
                "time": _coerce_str(raw[12]),
                "comment": _coerce_str(raw[13]),
            }
        )

    workbook.close()
    return rows
