"""Compat shim — the hydrostatics row registry moved to ``kayakgen.metadata``.

Workflow 0062 (P0-BOUNDARY-FIX, audit R0): ``kayakgen.services.evaluation``
consumes the registry, but the services layer must not import ``kayakgen.ui``
(``tests/test_services_boundaries.py``). The registry is pure presentation
data with no UI imports, so it now lives at
:mod:`kayakgen.metadata.hydrostatics_rows`; this shim keeps every existing
``kayakgen.ui.hydrostatics_metadata`` import working unchanged (repo shim
pattern, see ``generator.py``).
"""

from __future__ import annotations

from kayakgen.metadata.hydrostatics_rows import (
    HYDROSTATICS_ROW_METADATA,
    HydrostaticsRowMetadata,
)

__all__ = [
    "HYDROSTATICS_ROW_METADATA",
    "HydrostaticsRowMetadata",
]
