# Sources for audit run — 2026-05-25 full_repo

## Preset

`full_repo` — quarterly cadence per D041. The previous `full_repo`
run was 2026-05-22 (the dogfood that produced RFC 0059 and closed
13 findings via workflows 0030-0034). Three months later, D041
calls for a fresh full-state pass to catch drift that the
narrower release_candidate cycles between 2026-05-22 and now may
have missed.

## Run scope

Whole repository at HEAD `313dfdd` (working tree clean). Not a
commit range: the audit reads current state, not a diff.

Cumulative landings since the prior `full_repo` audit:

```
313dfdd Land workflows 0037 + 0038 — close 2026-05-25 audit AUD-O-001..007
4b1faac Run release_candidate code+doc audit on b82b544 + R1 docs batch
2d14cff Land workflows 0035 + 0036 — close 2026-05-23 audit AUD-O-009..012
b82b544 Land WEB_UI_REWORK_2026-05-22 second-pass redesign  (upstream)
fcb8040 Run release_candidate code+doc audit + R1 + R2 batches
3a7f2de Move CLAUDE_DESIGN_UI_REWORK_PROMPT.md into prompts/
8659fb0 Add RFC 0061 + land workflow 0034 — desktop sliders on registry
c052ddd Untrack .claude/skills/* — already gitignored
f2b366f Fix workflow.json schema compliance — cycles field + lane diversity
8769124 Promote RFC 0059 + add D041-D043 + ROADMAP entries
b4a494e Add RFC 0060 + land workflow 0033 — close audit AUD-O-003
5c658ea Land workflow 0032 — close audit AUD-O-004/005/006
2a260bd Land workflow 0031 — close audit AUD-P-003 + AUD-P-004
bf4179f Land workflow 0030 — close audit AUD-P-001 + AUD-P-002
130a42e Add RFC 0059 + workflow 0029 + run dogfood audit + R1 docs
```

Two `release_candidate` audits already covered narrower slices:

- 2026-05-23: covered `f78e478..3a7f2de` (RFC 0059 / 0060 / 0061 +
  workflows 0029-0034).
- 2026-05-25: covered the single upstream commit `b82b544` (web UI
  second-pass rework).

Their findings and closures are part of the canonical record this
audit reads as background; it does NOT re-audit the closed
findings, but it may flag any regressions introduced by the
closures.

This is the fourth `code_doc_audit` run.

## Lane inputs

All three lanes have full-repo coverage. The 2026-05-22 dogfood's
lane briefs apply unchanged; see
`docs/workflows/0029-code-doc-audit/prompts/` for each lane's
role.

| Lane | Inputs (high level) |
|---|---|
| pipeline-integrity | Whole repo at HEAD. RFCs 0025 / 0027 / 0046 / 0049 / 0054 / 0058 / 0044 invariants. `claim_state` literals across `kayakgen/`. `result_semantics` labels on resistance + GZ outputs. Accepted-fit records and reviewer-signature contracts. `MeshDiagnostics` + `StabilityFixturePromotionPacket` validators. Artifact-store identity (`Hull.record_hash`, `design_hash`, `FilesystemArtifactStore`, `SqliteIndex`). Public Pydantic schemas — `schema_version`, field name / type / default. Evaluator subprocess isolation + generative-search job records. Log redaction (RFC 0057). All claim-gate boundary tests (`tests/test_vocabulary_coverage.py`, golden tests, mesh evidence + `--bind-evidence`). Examples / fixtures that might teach retired behavior. The two new presentation-layer registries (RFC 0060 hull parameters, RFC 0062 hydrostatics rows) — verify they remain presentation-only and do not leak into claim-gate paths. |
| docs-decision-drift | RELEASE_DISCIPLINE.md checklist applied across the full repo. `docs/SPEC.md` as product-boundary truth. `docs/PRD.md` scope and status assertions. `docs/DECISION_LOG.md` 44 rows including the recent D041 / D042 / D043 / D044 additions. `docs/ROADMAP.md` track rows and Future-Striatum-Batches disposition. `docs/rfcs/README.md` 62 RFC status headers — every "proposed background; successor NNNN", "partial landed ...", and "landed ..." must match source. `CHANGELOG.md` Added / Changed / Fixed entries against actual landings (the file has grown substantially since 2026-05-22). `docs/ARCHITECTURE_MAP.md` package layout, CLI list, durable-artifact table. `docs/UBIQUITOUS_LANGUAGE.md` plus `tests/test_vocabulary_coverage.py` drift. `docs/USER_GUIDE.md` surface descriptions (just rewritten in R1 of the 2026-05-25 release_candidate audit — verify it now matches HEAD source). `docs/WEB_VERIFICATION.md` claims (gained a `data-testid` hook contract section). RFCs that are half-implemented or blocked on operator action (D006 / D007 / D014). Inter-doc conflicts. |
| operator-adoption | Whole-repo first-adopter sweep. Day-zero install (`pyproject.toml` extras, `[builder]` / `[report]` deps, opt-in CFD env knobs). `kayakgen` CLI subcommand discoverability and `--help` clarity across the 20+ subcommands (now including the post-workflow-0036 `runs jobs --header` and `runs list --kind` help-text polish). Desktop GUI flows (`kayakgen/ui/desktop.py`, `pyvista_view.py`, post-RFC-0061 slider registry consumption). Trame web workspace and Generate panel (post-`b82b544` second-pass layout + post-workflow-0037 inline-help additions). Validity badge tooltip, comparison-source toggle subtitle, mesh chip-pair tooltips, submit-button disabled-reason wiring, mesh-diagnostic threshold guidance — verify each is operator-discoverable as documented. Hydrostatics rows under the new RFC 0062 registry — verify the descriptions render where appropriate or document that they don't render today. Export menu / disabled-copy correctness. Error messages, recovery paths, first-run smoke. Overly complex areas that need a simpler adapter or guide. Places where file-based artifacts are useful but should not become the control plane. |

## RFCs in scope

Effectively all 62 RFCs in `docs/rfcs/`. The lanes prioritise:

- Latest landings: RFC 0059 (audit cadence), 0060 (hull-parameter
  registry), 0061 (desktop sliders), 0062 (hydrostatics rows). These
  are the youngest and most likely to have residual drift.
- Status-header consistency: RFCs marked `proposed background;
  successor NNNN` — confirm the successor exists and the body is
  obsolete in current source.
- Long-lived partials: RFC 0008, 0009, 0013, 0014, 0015, 0018, 0028,
  0029, 0031, 0033 — verify the "partial" qualifier still describes
  current source.

## Decision rows in scope

All 44 rows. Focus on `accepted` / `superseded` / `obsoleted` flags
matching current source behavior. Particular attention to:

- D006 / D007 / D014 — operator-blocked fixture campaigns. Has any
  new data landed?
- D041 (audit cadence) — this run IS the quarterly cadence
  application; verify the cadence rule itself is honored.
- D042 (`EMPTY_STABILITY_FIT_REGISTRY` constant) — confirm the
  three call sites still consume the constant; no regression.
- D043 (`HullParameterMetadata` pattern) — confirm RFC 0060/0061
  consumers still source from the registry.
- D044 (`HydrostaticsRowMetadata` pattern, accepted today) —
  brand-new; this audit is the first chance to flag any wiring
  oversight.

## Adversary framing per lane

- pipeline-integrity → look for *claim-state drift* anywhere in
  the cumulative landings, especially the new presentation-layer
  registries (could they accidentally widen a claim?) and the
  inline-help additions in workflow 0037 (do any of the new
  tooltip / disabled-reason copy strings make a claim the
  underlying state doesn't support?).
- docs-decision-drift → look for *honest-prose drift* across the
  six new additions: D044, RFC 0062, the two workflow scaffolds
  (0037 / 0038), the WEB_VERIFICATION `data-testid` hook contract
  section, and the now-rewritten USER_GUIDE serve section. Also
  apply the standing RELEASE_DISCIPLINE checklist to the
  cumulative state, not just the latest landing.
- operator-adoption → look for *invisible-mechanism drift* in the
  fuller surface area. The 2026-05-25 release_candidate audit
  covered just `b82b544`; this audit reads the whole workspace
  fresh. Are there day-zero install gaps, CLI subcommand surfaces
  that are still undocumented, error messages that name internal
  vocabulary, or recovery paths that dead-end?

## Where the audit run artifacts will land

`docs/audits/2026-05-25-full-repo-code-doc-audit/`:

```
pipeline-integrity/FINDINGS.md
docs-decision-drift/FINDINGS.md
operator-adoption/FINDINGS.md
SYNTHESIS.md
REMEDIATION_PLAN.md
```

The directory name carries the `full-repo` prefix to distinguish
it from the same-day 2026-05-25 release_candidate run at
`docs/audits/2026-05-25-code-doc-audit/`.
