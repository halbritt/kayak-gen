# Traceability review - watertight solid mesh profile

author: operator [self-declared: operator-traceability-review]
run: run_877488bcf83244479df1d95d7b420a65
job: review_traceability
date: 2026-05-13
verdict: accept_with_findings

## Findings

### T-001 - RFC 0010 package/profile slice is landed, but watertight readiness is still open

Workflow 0015 landed diagnostics, deterministic mesh package output, manifest
metadata, and the first open wetted-surface profile. RFC 0010 explicitly says
current packages are open-surface CFD candidates, not watertight `cfd_ready`
solids. This workflow can only close a watertight boundary if it keeps that
distinction visible.

Required action: add or clarify a named watertight-required profile without
changing the default open profile.

### T-002 - RFC 0015 can depend on a blocked watertight profile boundary

RFC 0015's dispatch contract needs solver profiles and readiness requirements.
It does not require current geometry to be watertight before the local dispatch
contract exists; it needs a profile name and readiness gate that can reject
insufficient mesh packages.

Required action: expose a stable profile identifier and manifest behavior that
future dispatch can check.

### T-003 - Status docs must not imply `cfd_ready`

If this workflow adds a watertight-required profile, RFC 0010 and the RFC index
must say the profile boundary exists but current generated packages remain
blocked below `cfd_ready`.

Required action: update RFC/status wording after implementation.

## Recommendation

Proceed with a small profile/readiness implementation. Do not attempt to land
actual watertight geometry generation in this workflow.
