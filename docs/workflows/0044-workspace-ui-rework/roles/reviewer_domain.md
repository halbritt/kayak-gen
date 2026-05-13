# Domain reviewer

Review claim, readiness, and CFD status semantics. Every chip and
persistent banner in the rework must mirror the existing
`ClaimState`, `ReadinessLevel`, and `CfdRunStatus` literals and never
introduce unsupported claims (no `cfd_ready` for current generated
packages, no `calibrated`/`validated`/`final prediction`/`design
fitness` for resistance, no hosted/cloud/OpenFOAM/SU2 language in
the CFD tab outside the no-hosted-worker notice).
