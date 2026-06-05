---
schema_version: striatum.finding.v1
artifact_kind: finding
verdict_intent: accept
author: operator
---

# Scorecard: Goal C (Migrate in-package importers off compatibility shims to canonical homes)

author: operator

## Dimension Scores

### preservation_verifiability: High (8/10)
Behavior preservation is highly verifiable. The shims for `jobs.py` and `high_angle_gz.py` are pure re-exports, meaning redirected call sites bind identical objects. For `generator.py`, the `KayakGenerator` legacy positional constructor must map correctly to the canonical `Hull` and `LoftedHullGeometry` construction. Slice 1 introduces a characterization test (asserting shim-canonical identity and that `KayakGenerator` produces a mesh byte-identical to `LoftedHullGeometry`), which acts as a verification gate before edits. Verification is done via full pytest and golden test assertions.

### blast_radius: Low (2/10)
The blast radius is exceptionally small, restricted to editing only static import lines across 12 files in the `kayakgen/` package. The shim files themselves are left completely unmodified to support legacy external consumers, and no functional code or public-facing command endpoints are edited.

### payoff: Moderate (6/10)
The payoff is structural and developer-facing. By removing internal traffic through shims and eliminating shim-through-shim layering, it creates a truthful dependency graph that de-risks future refactorings. The boundary ratchet test ensures no future regression is possible, though it doesn't simplify complex modules or provide user-visible behavior changes.

### reversibility: Very High (10/10)
Since the change consists entirely of non-functional edits to import blocks and the addition of test rules, any slice or the entirety of the goal can be trivially and safely rolled back with a one-commit revert without leaving any stale state or requiring database/schema changes.

### frozen_surface_risk: Low (2/10)
The work touches files adjacent to the legacy import path compatibility surface (unmodified shim files) but never modifies the shims themselves. It has zero proximity to public JSON schemas, Pydantic models, or generated golden STL files.

### sliceability: Very High (9/10)
The work decomposes naturally into five independent, risk-ascending, and separately verifiable slices (characterization tests, cfd redirects, services/ui redirects, golden test redirects, and ratchet rule). Each slice can be safely landed, linted, and verified separately without sequence constraints.

## Single Biggest Unverified Assumption
The single biggest unverified assumption is that `LoftedHullGeometry(Hull(defaults))` is a drop-in replacement for `KayakGenerator(defaults)` across all test assertions in `tests/test_golden.py`. While the implementation of `KayakGenerator` subclass only adapts the constructor parameters, any subtle difference in defaults, keyword argument handling, or type-checking in downstream assertions could cause test failures. This assumption remains unverified until Slice 4 is implemented.
