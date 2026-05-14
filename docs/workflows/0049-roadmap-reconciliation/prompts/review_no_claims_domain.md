Review workflow 0049 for no-claims and domain boundaries.

Read `docs/ROADMAP.md`, `docs/rfcs/README.md`, and the RFCs named by any
roadmap entry that appears to risk a domain claim.

Verify:

- The roadmap does not imply calibrated resistance, accepted real CFD,
  watertight `cfd_ready`, final prediction, final design fitness, production
  volume meshing, or real high-angle `GZ` before supporting evidence exists.
- `raw_unvalidated`, `uncalibrated_comparative`, `fixture_only`, and
  `unavailable` boundaries remain visible where relevant.
- Dependencies between geometry readiness, solver adapters, calibration, and
  stability are technically plausible.
- `git diff --check` passes.

Do not edit repo files. Publish a finding artifact at
`striatum/0049-roadmap-reconciliation/no_claims_domain/REVIEW_NO_CLAIMS_DOMAIN.md`
with Striatum `finding` front matter and a clear verdict.
