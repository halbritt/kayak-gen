---
schema_version: striatum.finding.v1
artifact_kind: finding
verdict_intent: accept
author: operator
---

# Scorecard: Goal A (Retire internal traffic through compatibility shims)

author: operator

## Dimension Scores

### preservation_verifiability: Very High (9/10)
Behavior preservation is guaranteed by construction since each shim re-exports the exact same objects from their canonical homes, meaning redirected internal call sites bind identical classes and functions. The existing unit test suite (including golden tests and dependency boundary gates) plus standard linting provide robust verification, and a simple identity check can mechanically prove no names were missed.

### blast_radius: Low (2/10)
The blast radius is exceptionally small, restricted to editing only static import lines across 10 files in the `kayakgen/` package. The shim files themselves are left completely unmodified to support legacy external consumers, and no functional code or public-facing command endpoints are edited.

### payoff: Moderate (5/10)
The payoff is purely structural, clean-up-oriented, and developer-facing. By removing internal traffic through shims and eliminating shim-through-shim layering, it creates a truthful dependency graph that de-risks future refactorings, though it doesn't simplify complex modules or provide user-visible behavior changes.

### reversibility: Very High (10/10)
Since the change consists entirely of non-functional edits to import blocks, any slice or the entirety of the goal can be trivially and safely rolled back with a single Git command without leaving any stale state or requiring database/schema changes.

### frozen_surface_risk: Low (2/10)
The work touches files adjacent to the legacy import path compatibility surface (unmodified shim files) but never modifies the shims themselves. It has zero proximity to public JSON schemas, Pydantic models, or generated golden STL files.

### sliceability: Very High (9/10)
The work decomposes naturally into three independent, risk-ascending, and separately verifiable slices (eval-internal redirects, services/ui redirects, and CLI redirects). Each slice can be safely landed, linted, and verified separately without sequence constraints.

## Single Biggest Unverified Assumption
The single biggest unverified assumption is that the opt-in OpenFOAM local execution environment (specifically `test_openfoam_v2512_smoke.py`, which is recommended when touching provenance-probe and case-render imports in Slice 1) is fully functional and configured correctly on the target runner. If OpenFOAM is not installed or the local run flags fail, full integration verification of the OpenFOAM case-render neighborhood will be limited to dry-run unit tests.
