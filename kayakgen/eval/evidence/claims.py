"""Claim-state contracts (shared with ``kayakgen.eval.claims``).

This module re-exports the RFC 0025 claim contract so new evidence-binding
modules can import it from the same ``kayakgen.eval.evidence`` namespace as
the OpenFOAM and checkMesh contracts.
"""

from __future__ import annotations

from kayakgen.eval.claims import (
    ClaimMetadata,
    ClaimState,
    RawUnvalidatedClaimFields,
    claim_allows_calibrated_prediction,
    claim_allows_final_design_fitness,
    claim_metadata_from_fields,
    raw_cfd_warnings,
    uncalibrated_resistance_warnings,
)

__all__ = [
    "ClaimMetadata",
    "ClaimState",
    "RawUnvalidatedClaimFields",
    "claim_allows_calibrated_prediction",
    "claim_allows_final_design_fitness",
    "claim_metadata_from_fields",
    "raw_cfd_warnings",
    "uncalibrated_resistance_warnings",
]
