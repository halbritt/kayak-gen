---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-gemini-pro-3.1-010
schema_version: striatum.synthesis.v1
artifact_kind: synthesis
logical_name: vote

# Vote on OpenFOAM Success Gate

**Vote:** Option A

**Decision:**
The `openfoam-v2512-interfoam-local` profile shall remain blocked from returning a `succeeded` status until complete implementation gates for mesh evidence, installed-solver provenance, case rendering, and force parser correctness are simultaneously satisfied, maintaining its `raw_unvalidated` no-claims boundary.

**Evidence and Citations:**
- As noted in the research packet citing RFC 0023 and RFC 0040, `cfd_ready` readiness demands strict evidence bindings including hashes, checksums, and metadata for a specific generated body and volume mesh.
- The OpenFOAM-v2512 `forces.C` source code indicates that force outputs are grouped as total, pressure, and viscous forces. The current kayakgen parser misinterprets the first component, which necessitates fixing the parser before permitting a success state.
- Upstream OpenFOAM tutorials (e.g., DTCHull) require proper two-phase transport setups and `polyMesh` artifacts, meaning a skeleton dictionary does not suffice for actual success.

**Why Rejected Alternatives Lose:**
- *Option B (Fixture-Only Success Profile)* would dilute the value of the primary profile and require extra warning semantics just to avoid confusion.
- *Option C (Two-Stage Local Smoke Result)* introduces unnecessary state-machine complexity for what is essentially a developer diagnostic tool.
- *Option D (OpenFOAM Case Generation First, Solver Success Later)* still does not provide a path to a true `succeeded` result and leaves the primary issue unaddressed while complicating the codebase with partial case rendering.

**Implementation Gates and No-Claims Language:**
- A production, OpenFOAM-readable `watertight_solid_resistance_v1` volume-mesh package must pass existing evidence checks and include verified `polyMesh` and hull patch metadata.
- OpenFOAM.com v2512 `interFoam` provenance must be recorded from probes beyond `$WM_PROJECT_VERSION`.
- The case must be deterministic, featuring a `forces` function object and bounded smoke execution.
- The force parser must be corrected to the v2512 schema.
- All successful records must carry the `raw_unvalidated` state with empty `accepted_uses`, warning that completion is not validation, calibration, or design fitness.

**Confidence:**
High