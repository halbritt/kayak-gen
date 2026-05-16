"""Shared solver-evidence contracts.

Phase 2 step 5 of ``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`` collects
the evidence records that the CFD / mesh / claim layers share into a single
neutral namespace. The actual class bodies still live with their original
modules (so existing imports and pickled state stay byte-stable); this
package exposes them as a single import surface for new code.

Concretely::

    from kayakgen.eval.evidence import (
        OpenFoamProvenanceProbe,
        CheckMeshSummary,
        ClaimMetadata,
        RawUnvalidatedClaimFields,
        ClaimState,
    )

is the canonical import for new modules. ``kayakgen.eval.cfd.jobs``,
``kayakgen.eval.snappy_hex_mesh``, and ``kayakgen.eval.claims`` continue to
re-export the same names for backwards compatibility.
"""

from __future__ import annotations

from kayakgen.eval.evidence.check_mesh import CheckMeshSummary
from kayakgen.eval.evidence.claims import (
    ClaimMetadata,
    ClaimState,
    RawUnvalidatedClaimFields,
    claim_allows_calibrated_prediction,
    claim_allows_final_design_fitness,
    claim_metadata_from_fields,
    raw_cfd_warnings,
    uncalibrated_resistance_warnings,
)
from kayakgen.eval.evidence.openfoam import OpenFoamProvenanceProbe

__all__ = [
    "CheckMeshSummary",
    "ClaimMetadata",
    "ClaimState",
    "OpenFoamProvenanceProbe",
    "RawUnvalidatedClaimFields",
    "claim_allows_calibrated_prediction",
    "claim_allows_final_design_fitness",
    "claim_metadata_from_fields",
    "raw_cfd_warnings",
    "uncalibrated_resistance_warnings",
]
