# Workflow 0056 Operator Report

Workflow: `0056-rfc-0058-stage2-3-burndown`
Started: 2026-05-21

## Operator Notes

- 2026-05-21: scaffolded RFC 0058 stages 2 + 3 + workflow 0054's
  NB-1 stepped-clock seam against `STAGE_2_3_DECISIONS.md`. Six
  parallel author tracks (claim-label contract, CFD-in-loop
  graduation, `kayakgen stability` CLI sub-app, frontier-view
  colour wiring, NB-1 clock seam, integrator), plus docs sync,
  three reviews, ledger, remediate, final. `review_claims` is
  assigned to `codex` for this run to dodge the upstream
  gemini-wrapper missing-verdict bug (striatum issue #36). The
  workflow uses the canonical `.striatum/bin/*-supervised-wrapper.sh`
  from striatum 1.57.0 across all three lanes.
- 2026-05-21: `--allow-same-model-pairing` override recorded.
  Rationale: upstream striatum issue #36 (gemini-wrapper review jobs
  complete via `striatum complete` without recording a verdict)
  effectively removes gemini as a review lane for this run. With
  only codex + claude as usable review lanes and 5+ upstream author
  tracks, at least one same-model author/reviewer pairing is
  unavoidable. The override is scoped to this workflow only and is
  removed once #36 lands a fix or a workaround.
- Defaults remain byte-stable: every contract returns the value
  the codebase already produces when the fit registry is empty.
  RFC 0043's analytical GZCurve label still resolves to
  `unvalidated_hydrostatic_comparison` until a future workflow
  lands the first accepted `StabilityFitRecord`. No fixture is
  promoted by this workflow.
- 2026-05-21 docs sync: updated `CHANGELOG.md`,
  `docs/DECISION_LOG.md` (D039), `docs/ROADMAP.md`,
  `docs/rfcs/README.md`, and RFC 0058 for the stages 2 + 3
  landing. The docs now mark RFC 0058 as `landed`, resolve/defer
  the five open questions, keep the Stage-4 first-promotion gate on
  D007/D014 physical rig data, and preserve the existing no-claim
  boundary.
- 2026-05-21 remediation: fixed MF-1 from the workflow findings
  ledger. `build_spec_from_form_state()` now mirrors the renderer's
  first-class CFD-in-loop branch: if
  `generative_cfd_in_loop_status == "first_class"`, the hidden
  acknowledgement is treated as implicit. The default `opt_in_only`
  branch still refuses unacknowledged CFD-in-loop requests.
