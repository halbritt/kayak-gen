---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-gemini-pro-3.1-002
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

# Vote: Sweep And Optimization Admissibility

**Vote:** Option A

**Decision Sentence:** We will record RFC 0009 as landed/partial for sweep run records, keep future optimizer work blocked until an objective registry is built, and preserve the current conservative default Pareto objectives (`GM0_m`, `displacement_error_kg`, and `mesh_problem_count`) while restricting raw resistance to explicitly requested exploratory comparison.

**Evidence and Citations:**
- **Local Constraints:** `docs/ROADMAP.md` rules dictate that comparison can only use metrics with explicit claim states and strictly forbids treating raw resistance, CFD, or advisory validity as a final design fitness score. Current defaults in `kayakgen/search/compare.py` already enforce this by limiting objectives to `GM0_m:max`, `displacement_error_kg:min`, and `mesh_problem_count:min`. Tests in `tests/test_compare.py` reject forged metadata and scalar validation-only resistance, enforcing the admissibility split.
- **External Evidence (NASA & ITTC):** NASA NTRS (NASA/TP-2016-219422) emphasizes tying credibility to accuracy and uncertainty limits, making provenance metadata a strict prerequisite for ranking metrics. ITTC Guidelines (7.5-02-02-01 and 7.5-02-02-02) demand rigorous uncertainty analysis and validation, confirming that raw analytical resistance must not be used as an implicit or default ranking metric without accepted calibration provenance.
- **External Optimization (pymoo & OpenMDAO):** Optimization libraries like pymoo and OpenMDAO require user-defined constraints and objectives but do not inherently validate the physical truth of the provided functions. This shifts the burden of metric admissibility entirely onto the kayak-gen application.

**Why Rejected Alternatives Lose:**
- **Option B (Explicit Objective Registry Before Search)** on its own is purely structural; it defines *how* to track metrics but doesn't immediately freeze the current whitelist, which could leave a gap for unvalidated metric promotion. However, it serves as a critical prerequisite for future work.
- **Option C (Evidence-Gated Promotion)** defines future rules but does not address the immediate status of RFC 0009 or explicitly freeze the current defaults, leaving current bounds ambiguous.
- **Option D (Scalar Fitness Postponed)** prevents a scalar fitness score but does not explicitly whitelist the currently accepted Pareto objectives, which is required to align with existing implementations in `kayakgen/search/compare.py`.

**Implementation Gates and No-Claims Language:**
- **RFC 0009 Status:** Reconcile RFC 0009's status as a landed/partial run-record slice in `docs/rfcs/README.md`.
- **No-Claims Language Maintained:** Raw analytical resistance output is `uncalibrated_comparative`, not a calibrated model or final design prediction. CFD output is local dispatch state and not validated success.
- **Future Optimizer Gates:** Optimization and search work remains strictly blocked until an explicit metric registry (as described in Option B) is implemented. This registry must classify claim-state requirements and ensure that unavailable or provenance-failed metrics result in warnings, not silent Pareto domination.

**Confidence:** High
