---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-gemini-pro-3.1-008
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

# Vote: Solver Path Decision

**Vote:** Option A - Conservative Default: OpenFOAM.com v2512 `interFoam`

**Decision:**
Select OpenFOAM.com v2512 `interFoam` (derived from the DTCHull pattern) as the first real external CFD solver target, bounded by a `watertight_solid_resistance_v1` mesh profile and `cfd_ready` readiness gate, with raw `forces` post-processing parsing.

**Evidence and Citations:**
*   **OpenFOAM Relevance:** OpenFOAM.com v2512 (released 2025-12-22, https://www.openfoam.com/current-release) offers the most relevant domain fit for kayak free-surface resistance.
*   **Maintained Template:** The official DTCHull tutorial path provides a strong, maintained template family for ship-hull/free-surface workflow using `interFoam` and a `forces` function object (https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/Allrun and .../system/controlDict).
*   **SU2 Limitations:** While SU2 has a cleaner install story and history output (https://su2code.github.io/docs_v7/Theory/), the maintained sources support generic incompressible/external-flow work rather than a comparable first-party ship/free-surface resistance workflow.

**Why Rejected Alternatives Lose:**
*   **Option B (Incremental OpenFOAM open-surface adapter):** Proceeding with an open-surface adapter risks implying more physical validity than the current open hull/deck surfaces support, lacking proof of physical and operational coherence.
*   **Option C (SU2 incompressible external-flow adapter):** Choosing SU2 prioritizes adapter maintainability over domain fidelity, as it lacks direct evidence for a maintained free-surface kayak/ship resistance workflow.
*   **Option D (Defer real external solver, harden RFC 0040 first):** Deferring the decision leaves the RFC 0041 solver-selection blocked, providing no clear target case template, parser, or installation surface for future adapter development. Option A provides this direction while respecting the `watertight` prerequisite.

**Implementation Gates and No-Claims Language:**
*   **No-Claims:** All real-solver outputs must remain strictly `raw_unvalidated`. They are not to be claimed as calibrated resistance, final prediction, design fitness, Pareto-default scoring, or proof of seaworthiness (per RFC 0025).
*   **Readiness Gate:** No real `succeeded` solver path is permitted until the production volume-mesh/readiness gate is fully implemented. The adapter must verify matching generated-body, self-intersection, and volume-mesh diagnostic evidence (`cfd_ready`).
*   **Adapter Boundary:** The adapter must reside outside `Hull` and geometry models, focusing solely on translating `CfdJobSpec` and `MeshPackageManifest` to a case directory, and raw outputs back to `CfdRunRecord`/raw-result records.
*   **CI Strategy:** Required CI tests must not depend on the external solver binary. They must use fake commands and fixture files (e.g., `force.dat`, logs) to cover profile registration, readiness rejection, unavailable dependency, missing/malformed output, and parser success. Installed-solver tests must be optional and flag-gated.
*   **Version Pinning:** The integration must pin exactly to the OpenFOAM.com v2512 release line to mitigate case drift risk.

**Confidence:** High
