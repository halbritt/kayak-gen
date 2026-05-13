# Roadmap review - RFCs 0009-0013

author: operator
Verdict recommendation: accept_with_findings

The roadmap is coherent and truthful about RFC 0004-0008 partial status. It
should be accepted as a draft set, but several dependency and acceptance details
must be corrected before treating the RFCs as implementation-ready.

## Findings

### F-ROAD-001 - High - RFC 0009 depends on RFC 0010 mesh diagnostics

RFC 0009 includes `mesh_diagnostics` and writes `<hull_hash>.mesh.json`, but
mesh diagnostics are defined in RFC 0010. Either make mesh diagnostics optional
post-0010 in RFC 0009 or explicitly sequence RFC 0010 before mesh-producing
parts of RFC 0009.

### F-ROAD-002 - Medium - Invalid sweep candidates cannot require `hull_hash`

RFC 0009 requires invalid `Hull` candidates to be recorded, but invalid hulls
cannot have `Hull.hash()`. Add `candidate_index` or `candidate_key` as the
primary identity, make `hull_hash` optional, and store attempted parameters plus
validation errors for failures.

### F-ROAD-003 - High - RFC 0011 load cases need displacement semantics

RFC 0011 introduces paddler/hull/cargo mass but only accepts KG and beam
sensitivity. Add total mass, displaced-mass error reporting, and either
draft/waterline solving or an explicit design-waterline-only warning.

### F-ROAD-004 - Medium - RFC 0011 conflicts with current `EvaluationResult.stability`

The draft proposes `StabilityResult`, while current code reserves
`EvaluationResult.stability` as `GZCurve | None`. Make the target contract
explicit: `stability: StabilityResult | None`, with `gz_curve` nested inside.

### F-ROAD-005 - Medium - RFC 0012 warning criteria lack v1 ranges

RFC 0012 requires validity warnings but does not declare provisional raw-model
ranges. Define provisional envelopes or require a permanent
`uncalibrated_no_validity_envelope` warning until human-selected ranges exist.

### F-ROAD-006 - Medium - RFC 0013 omits RFC 0010 dependency

RFC 0013 uses mesh diagnostic problem count but does not list RFC 0010 in its
context. Add RFC 0010 and make mesh objectives optional when reports are absent.

### F-ROAD-007 - Medium - RFC 0013 title promises UI but acceptance is report-only

Either retitle RFC 0013 toward candidate comparison reports or add minimal web
acceptance criteria that are explicitly gated behind RFC 0008 completion.
