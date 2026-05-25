# Role: implementer

You close audit batch R2 (AUD-O-001/002/003/004/006 + the in-app copy
side of AUD-O-007) from the 2026-05-25 release_candidate audit by
adding inline-help / tooltip / disabled-reason surfaces to the
post-`b82b544` web workspace.

You edit:

- `kayakgen/ui/web/app.py` — validity-badge `title=` / popover with
  plain-text four-state explanation; comparison-source toggle
  subtitle distinguishing `live_frontier` vs `imported_report`; mesh
  chip-pair tooltip explaining the "no package built" + live
  readiness relationship; high-angle GZ alert copy rewrite that
  drops the `RFC 0020 / RFC 0024` citations in favor of an operator-
  facing recovery path (point at `kayakgen stability --high-angle-gz`
  and the Comparison-tab import).

- `kayakgen/ui/web/generate_spec_form.py` — wire the kind-aware Submit
  button's `disabled` attribute to a derived `submit_blocking_reason`
  state field, add an `aria-describedby` pointing at a visible span
  that renders the reason ("Requires at least one variable",
  "Objectives not admissible for the conservative scope", etc.), and
  populate the reason from the existing validation hooks
  (`refused_objectives`, `variable_rows` cardinality, etc.).

- `kayakgen/services/evaluation.py` — `mesh_diagnostics_rows_from_state`
  label rewrite from raw dict keys (`boundary_edges`,
  `nonmanifold_edges`, `bad_edges`, `open_faces`, `thin_triangles`)
  to operator-facing labels with threshold guidance baked into the
  label or as a separate `hint` column. **You MUST NOT touch
  `hydro_rows_from_state` — that change lives in workflow 0038 (R3).**

- `tests/test_web_inline_help.py` — NEW. Render-verification tests
  mirroring the introspection pattern in `tests/test_web_layout.py`.
  At minimum, one test per closed finding plus a wire-payload
  stability regression test that constructs two states (one valid,
  one invalid) and asserts `build_spec_from_form_state(state)`
  returns the same dict shape across the inline-help additions.

You do not touch the read-only paths
(`CHANGELOG.md`, `docs/USER_GUIDE.md`, `docs/DECISION_LOG.md`,
`docs/audits/2026-05-25-code-doc-audit/SYNTHESIS.md`,
`REMEDIATION_PLAN.md`, any `FINDINGS.md`, `docs/rfcs/`,
`docs/rfcs/README.md`, `docs/audits/README.md`,
`kayakgen/ui/web/generate_frontier_view.py`,
`kayakgen/ui/web/controllers.py`,
`kayakgen/ui/parameter_metadata.py`) — those are the parent agent's
job, or belong to a different workflow.

Use the maximal number of useful sub-agents with disjoint write
scopes if you split the work between the app-level copy edits, the
form-state wiring, and the evaluation-helper label rewrite, but keep
one integrator responsible for the final pytest run and the patch
summary.

## Operator-facing copy rules

- Plain English at the point of use; assume the operator has never
  read an RFC. No "RFC 0020", no "claim_state", no "convergence_flag"
  in tooltip / aria-label / alert copy.
- Threshold guidance for mesh diagnostics should be embedded in the
  label or hint string, not relegated to USER_GUIDE.md: e.g.
  "Non-manifold edges (must be 0)" or "Open faces (must be 0)".
- The validity badge title must cover all four states ("In
  &lt;class&gt; envelope", "Custom — sub-touring", "Custom — beyond
  elite", "Custom (L/B_wl=X.X)") in plain text and explain in one
  sentence what each means.
- The comparison-source toggle subtitle should say: live frontier is
  candidates from this session; imported report is a saved
  design-report JSON loaded into the workspace.
- The submit-button blocking-reason span MUST be visible (not just
  aria-live) so sighted users without screen readers see the same
  signal.

## Forbidden behavior changes

- Wire payload of `build_spec_from_form_state` MUST remain byte-
  stable. Add a regression test that constructs two states and
  asserts the dict shape is unchanged.
- No new `claim_state` literal labels. No promotion of the
  `unavailable` readiness state past evidence (the chip pair already
  resolves this honestly; do not collapse it back into a single
  chip).
- No backend capability added. The mesh-diagnostic label rewrite
  changes how rows are presented, not the underlying diagnostic
  computation.
