# Audit Synthesis — 2026-05-25 full_repo code+doc audit

Date: 2026-05-25
Workflow shape: `code_doc_audit` (RFC 0059)
Preset: `full_repo`
Scope: whole repository at HEAD `313dfdd` (working tree clean).

This is the fourth `code_doc_audit` run and the second `full_repo`
pass after the 2026-05-22 dogfood. Three release_candidate audits
ran in between (2026-05-23 on the RFC 0059/0060/0061 cluster,
2026-05-25 on the b82b544 web UI rework). The cadence per D041
calls for `full_repo` quarterly; this run is early at the
operator's request, primarily to validate that the recent burst
of audit-driven closures (workflows 0030-0038, RFCs 0059-0062)
did not introduce regressions.

## Lane-diversity caveat

Single-agent run (Claude Opus 4.7 main thread dispatched three
parallel `Explore` subagents — Lane 1 on Claude Opus 4.7, Lane 2
on Claude Opus 4.7, Lane 3 on Claude Haiku 4.5 per the
subagent's own header). The provider-diversity that
`0009-multi-lane-review` achieved (claude / codex / gemini) was
not achieved here. Each lane kept a distinct reading posture and
reported independently. The synthesis trusts the lane outputs
where confirmed, but flags two hallucinated findings (AUD-D-002,
AUD-O-011, AUD-O-015) where lane evidence did not survive
parent-thread verification.

## Findings rolled up

| ID | Lane | Severity | Category | Status |
|---|---|---|---|---|
| AUD-P-001..AUD-P-012 | pipeline-integrity | info × 12 | claim_gate | all closed — positive baselines (RawUnvalidatedClaimFields validators, D042 consumption, RFC 0058 unvalidated_hydrostatic_comparison default, presentation-layer isolation, inline-help no-claim-promotion, RFC 0046 opt-in, RFC 0049 hash stability, RFC 0057 subprocess isolation, RFC 0056 measured-fixture validators, test-coverage completeness) |
| AUD-D-001 | docs-decision-drift | low | docs_drift | closed by R1 — `docs/ROADMAP.md` header bumped to 2026-05-25 in audit commit `456cdad` |
| ~~AUD-D-002~~ | docs-decision-drift | ~~high~~ | ~~docs_drift~~ | **invalid** — lane claimed RFC 0060/0061 body files missing; parent thread verified files exist on disk (`docs/rfcs/0060-web-generate-panel-form-labels-and-tooltips.md` 12994B, `docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md` 14948B). Hallucinated; do not act on |
| AUD-D-003 | docs-decision-drift | info | docs_drift | closed (wontfix) — D043/D044 scope clarification; the RFC 0059 §2.2 brief reads correctly as-is and is treated as a historical record per the lane's own follow_up assignment |
| AUD-D-004 | docs-decision-drift | low | docs_drift | closed by R1 — `docs/WEB_VERIFICATION.md` `data-testid` section now cites `tests/test_web_layout.py` + `tests/test_web_inline_help.py` as enforcement (audit commit `456cdad`) |
| AUD-D-005..AUD-D-010 | docs-decision-drift | info × 6 | docs_drift | all closed — positive baselines (USER_GUIDE serve section, RFC successor citations, D042/D043/D044 consumption verified, CHANGELOG entries detailed) |
| AUD-O-001..AUD-O-002 | operator-adoption | info × 2 | operator_ergonomics | closed — positive (install extras, inline-help wired) |
| AUD-O-003 | operator-adoption | **medium** | implementation_gap | closed by 0039 — `hydro_rows_from_state` widened with `description` key (4-tuple in `analysis_view_model`); Hydro-tab `<tr>` carries `:title='row.description'`; new `tests/test_hydro_tab_descriptions.py` (3 render-verification tests) pins the contract |
| AUD-O-004..AUD-O-010 | operator-adoption | info × 7 | operator_ergonomics | closed — positive baselines (submit disabled-reason, RFC 0061 desktop sliders, CLI discoverability, error messages, export menu, first-run smoke, CFD opt-in path) |
| ~~AUD-O-011~~ | operator-adoption | ~~medium~~ | ~~implementation_gap~~ | **invalid** — lane recommended adding stage-4 promotion gate note to USER_GUIDE; parent thread verified USER_GUIDE.md:209-210 already contains "Stage 4 first promotion remains gated on D007 / D014 physical rig data." Hallucinated; do not act on |
| AUD-O-012 | operator-adoption | low | operator_ergonomics | closed (wontfix) — watertight-solid mesh profile not selectable in web form is a documented limitation per the lane's own follow_up; future web feature, not a current gap |
| AUD-O-013..AUD-O-014 | operator-adoption | info × 2 | operator_ergonomics | closed — positive baselines |
| ~~AUD-O-015~~ | operator-adoption | ~~medium~~ | ~~operator_ergonomics~~ | **invalid** — lane claimed mesh-diagnostic labels are raw dict keys (`boundary_edges`, `nonmanifold_edges`, etc.). Parent thread verified the labels in `kayakgen/services/evaluation.py::mesh_diagnostics_rows_from_state` are already operator-facing English with threshold guidance ("Non-manifold edges (must be 0)", "Boundary edges (perimeter; acceptable)", "Degenerate faces (must be 0)") — workflow 0037 landed this. Hallucinated; do not act on |

**Severity totals (after invalid removal)**: 0 critical · 0 high · 1
medium · 3 low · 27 info.

The clean shape vindicates the audit cadence: the cumulative
closures from workflows 0030-0038 produced a repository that the
three lanes converge on as a positive baseline, with only one
medium-severity residual (a brand-new RFC's description fields
written but not yet rendered) and three low-severity
docs-grooming items.

## Lane-quality note

Lane 1 returned 12 positive null findings — all evidence-backed,
all verified by parent thread. Lane 2 returned 10 findings of
which 1 (AUD-D-002) was a clear hallucination (the missing-RFC
claim was contradicted by `ls`). Lane 3 returned 15 findings of
which 2 (AUD-O-011, AUD-O-015) were hallucinations (both based
on misreading the current source or USER_GUIDE).

**Lane 3's hallucination rate (2 / 15 = 13%) is the highest of
this run.** The Lane 3 agent header self-reported "Claude Haiku
4.5" while the other lanes ran on Claude Opus 4.7; the lane-
diversity caveat now also flags model-tier diversity. Future
audit runs should consider rerunning Lane 3 on Opus if the same
pattern recurs, or restructure the Lane 3 prompt to require
verbatim source quotes for every finding to constrain reasoning
to evidence.

The hallucinated findings are recorded in this synthesis with
strikethrough and the verification evidence, so the next audit
has a baseline of "these were wrong, don't refind them."

## Cross-lane duplicates and overlap

- **AUD-O-003 (RFC 0062 descriptions not rendered) ⊂ AUD-D-009
  positive baseline** — Lane 2 confirmed D044 wiring works in
  evaluation.py; Lane 3 surfaced that the wiring stops at the
  label / unit fields and the description is gated behind a
  future UI affordance. The two findings agree on facts but
  disagree on whether the gap counts as drift. Lane 3 is right:
  the registry's descriptions are operator-facing copy and a
  registry without a render is a half-feature.

No other cross-lane duplicates. The three lanes' valid findings
are disjoint.

## Conflicts between lanes

None. Lane 1 (claim-gate invariants hold), Lane 2 (docs honest,
1 minor stale date), Lane 3 (1 real ergonomics gap on
descriptions) are mutually consistent.

## Priority order

Highest leverage first:

1. **R1 — docs-only catch-up** (in-place in audit commit):
   AUD-D-001 (ROADMAP date) + AUD-D-004 (WEB_VERIFICATION test
   cite) + USER_GUIDE note about RFC 0062 descriptions not yet
   surfaced (covers half of AUD-O-003's recommendation).

2. **R2 — Hydro-tab description rendering** (follow-up striatum
   workflow): wire `HydrostaticsRowMetadata.description` into
   `hydro_rows_from_state` and the Hydro tab template so the
   descriptions render as tooltips on hover. Closes AUD-O-003.
   Likely workflow id `0039-hydro-tab-description-rendering`.

3. **R3 — Wontfix / closed**:
   - AUD-D-002 (invalid; hallucination)
   - AUD-D-003 (info wontfix)
   - AUD-O-011 (invalid; hallucination)
   - AUD-O-012 (documented limitation; wontfix)
   - AUD-O-015 (invalid; hallucination)

4. **Null findings** (Lane 1's 12, Lane 2's 6 positive baselines,
   Lane 3's 12 positive baselines): no action; record as
   regression baseline for the next audit.

## Notes for the workflow scaffold

This `full_repo` run took roughly 3 minutes wall-clock for the
three parallel lanes to complete. Single-provider Lane 3 produced
two hallucinated findings (~13% of its output), which the parent
thread caught via direct verification of the cited evidence. The
workflow's "evidence-backed findings" discipline is what made
the catches possible — both hallucinations were testable in
seconds.

Future audit runs should:

1. Strongly prefer cross-provider lanes if available.
2. Continue to verify each high / medium finding's evidence
   before landing remediation; the lane PATCH_SUMMARYs cannot
   be the sole input to a follow-up workflow.
3. Consider rerunning a hallucinating lane on a stronger model
   if the same pattern recurs.

This is the first audit where a lane's findings were partially
discarded; the precedent is now set.
