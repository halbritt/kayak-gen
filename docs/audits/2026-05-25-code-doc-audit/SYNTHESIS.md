# Audit Synthesis — 2026-05-25 code+doc audit (release_candidate)

Date: 2026-05-25
Workflow shape: `code_doc_audit` (RFC 0059)
Preset: `release_candidate`
Source-of-truth scope: single upstream commit `b82b544` ("Land
WEB_UI_REWORK_2026-05-22 second-pass redesign"). Range
`fcb8040..b82b544`. Six files changed (+600/-135), all in the web UI
surface plus two new presentation helpers in
`kayakgen/services/evaluation.py`.

## Lane-diversity caveat

Single-agent run (Claude Opus 4.7 main thread dispatched three parallel
`Explore` subagents). The provider-diversity that `0009-multi-lane-review`
achieved (claude / codex / gemini) was not achieved here, matching the
provenance footprint of the 2026-05-22 and 2026-05-23 audits. Each lane
kept a distinct reading posture and reported independently. The
synthesis trusts the lane outputs but flags this provenance.

## Findings rolled up

| ID | Lane | Severity | Category | Status |
|---|---|---|---|---|
| AUD-P-001 | pipeline-integrity | info | claim_gate | open — null finding, helpers are pure transformers |
| AUD-P-002 | pipeline-integrity | info | claim_gate | open — null finding, mesh chip respects acceptance contract |
| AUD-P-003 | pipeline-integrity | info | claim_gate | open — null finding, noqa suppression is harmless |
| AUD-P-004 | pipeline-integrity | info | claim_gate | open — null finding, wire output unchanged |
| AUD-P-005 | pipeline-integrity | info | claim_gate | open — null finding, controllers diff is glue |
| AUD-P-006 | pipeline-integrity | info | claim_gate | open — null finding, no claim-state drift in app.py |
| AUD-P-007 | pipeline-integrity | info | claim_gate | open — null finding, validity badge wired correctly |
| AUD-D-001 | docs-decision-drift | **medium** | docs_drift | closed by R1 — CHANGELOG entry added under `## Changed` |
| AUD-D-002 | docs-decision-drift | **medium** | docs_drift | closed by R1 — USER_GUIDE `### serve` rewritten |
| AUD-D-003 | docs-decision-drift | low | docs_drift | wontfix — UBIQUITOUS_LANGUAGE remains scoped to domain vocabulary (R4) |
| AUD-D-004 | docs-decision-drift | low | docs_drift | closed by R1 — `generate_frontier_view.py` docstring expanded |
| AUD-D-005 | docs-decision-drift | info | docs_drift | open — null finding, no new decision row needed |
| AUD-D-006 | docs-decision-drift | info | docs_drift | open — null finding, WEB_VERIFICATION still accurate |
| AUD-D-007 | docs-decision-drift | info | docs_drift | open — null finding, brief ↔ implementation aligned |
| AUD-D-008 | docs-decision-drift | info | docs_drift | closed by R1 — ARCHITECTURE_MAP date bumped to 2026-05-25 |
| AUD-D-009 | docs-decision-drift | info | docs_drift | open — null finding, ROADMAP correctly categorizes |
| AUD-O-001 | operator-adoption | **medium** | operator_ergonomics | closed by 0037 — validity-badge `title=` + helper land in `app.py` |
| AUD-O-002 | operator-adoption | **medium** | operator_ergonomics | closed by 0037 — comparison-toggle subtitle + per-button tooltips |
| AUD-O-003 | operator-adoption | low | implementation_gap | closed by 0037 — chip-pair `title=` tooltips |
| AUD-O-004 | operator-adoption | **medium** | operator_ergonomics | closed by 0037 — submit-button `disabled` + `aria-describedby` + visible reason span |
| AUD-O-005 | operator-adoption | low | operator_ergonomics | closed by 0038 — RFC 0062 + `HydrostaticsRowMetadata` registry, D044 recorded |
| AUD-O-006 | operator-adoption | low | operator_ergonomics | closed by 0037 — threshold guidance appended to existing English labels |
| AUD-O-007 | operator-adoption | info | operator_ergonomics | closed by 0037 — `HIGH_ANGLE_GZ_COPY` rewritten to drop RFC citations |
| AUD-O-008 | operator-adoption | low | docs_drift | closed by R1 — USER_GUIDE serve section names the Comparison tab as frontier home |
| AUD-O-009 | operator-adoption | info | operator_ergonomics | closed by R1 — jobs-table columns documented in USER_GUIDE |
| AUD-O-010 | operator-adoption | low | operator_ergonomics | closed by R1 — "Raw JSON (advanced)" intent documented in USER_GUIDE |
| AUD-O-011 | operator-adoption | info | operator_ergonomics | open — product-decision; revisit after R2 lands and operator feedback |
| AUD-O-012 | operator-adoption | low | operator_ergonomics | closed by R1 — CFD-in-loop slowness rationale documented in USER_GUIDE |
| AUD-O-013 | operator-adoption | info | docs_drift | closed by R1 — subsumed by AUD-D-001 CHANGELOG entry |
| AUD-O-014 | operator-adoption | low | operator_ergonomics | closed by R1 — responsive behavior documented in USER_GUIDE |
| AUD-O-015 | operator-adoption | info | implementation_gap | closed by R1 — `data-testid` hook contract documented in WEB_VERIFICATION.md |
| AUD-O-016 | operator-adoption | info | — | open — positive null finding (refusal alert copy is good) |

**Severity totals**: 0 critical · 0 high · 5 medium · 9 low · 18 info.

Lane 1 returned 7 positive null findings (`severity: info`) — the
"presentation-only rework" claim is verified under adversarial review.
The wire output is stable, the new helpers are pure transformers, the
mesh readiness chip respects the acceptance contract, and no claim-state
label is promoted past evidence.

The five medium findings cluster on two themes:

1. **Central docs did not catch up to the rework** (AUD-D-001 +
   AUD-D-002). CHANGELOG has no entry for b82b544 and the USER_GUIDE
   `### serve` section still describes the pre-rework form-builder
   layout, the old "Raw JSON spec" label, and places the Pareto
   frontier on the Generate tab.
2. **New operator-facing controls leak invisible mechanism** (AUD-O-001
   + AUD-O-002 + AUD-O-004). The validity badge, the comparison-source
   toggle, and the submit-button disabled state are all present but
   under-explained at the point of use. The aria-label / screen-reader
   path is good; the sighted-user hover-tooltip / inline-help path is
   missing.

## Cross-lane duplicates and overlap

- **AUD-D-001 (CHANGELOG unrecorded) ⊇ AUD-O-013 (validity badge not
  in CHANGELOG)**. AUD-O-013 is a narrower instance of AUD-D-001's
  umbrella claim; closing AUD-D-001 closes AUD-O-013 by construction.
- **AUD-D-002 (USER_GUIDE serve section predates rework) ⊇
  AUD-O-007 / AUD-O-008 / AUD-O-009 / AUD-O-010 / AUD-O-012 /
  AUD-O-014**. AUD-D-002 covers the umbrella claim that the serve
  section needs a rewrite; the AUD-O-* findings supply the specific
  bullet points the rewrite must cover (high-angle GZ alert copy,
  frontier-tab move, jobs-table columns, "Raw JSON (advanced)" intent,
  CFD-in-loop slowness, two-column layout behavior). Closing AUD-D-002
  with a USER_GUIDE rewrite that addresses every AUD-O-* bullet closes
  all of them together.

No other cross-lane duplicates. Lane 1's findings are disjoint from
Lanes 2-3 (claim-state invariants vs. docs/operator surfaces).

## Conflicts between lanes

None. Lane 1's "claim holds" findings are not in tension with Lanes 2-3's
"docs and operator-facing copy could be better" findings — the rework is
correctly scoped as presentation-only, *and* the presentation layer
itself has docs / copy gaps.

## Priority order

Highest leverage first:

1. **R1 — Docs-only catch-up batch** (AUD-D-001 + AUD-D-002 + AUD-D-004
   + AUD-O-007 + AUD-O-008 + AUD-O-009 + AUD-O-010 + AUD-O-012 +
   AUD-O-014 + AUD-O-013 + AUD-O-015). Single docs-only batch:
   - CHANGELOG.md: add a `## Changed` entry under `## Unreleased` for
     b82b544, naming the tab restructure, validity badge,
     comparison-source toggle, kind-aware submit, table rendering,
     "Raw JSON (advanced)" rename, and CFD expansion title update.
   - USER_GUIDE.md `### serve`: rewrite to describe the post-rework
     layout (two-column form, VDataTable variable rows, kind-aware
     submit, Comparison tab as frontier home, "Raw JSON (advanced)"
     intent, CFD-in-loop slowness rationale, jobs-table columns,
     responsive breakpoint, high-angle GZ alert).
   - `kayakgen/ui/web/generate_frontier_view.py`: module-level docstring
     paragraph explaining that `# noqa: kg-orphan-color` is correct
     because `FORBIDDEN_METRIC_TOKENS` contains metric-name strings,
     not color literals.
   - `docs/WEB_VERIFICATION.md` or `docs/ARCHITECTURE_MAP.md`: short
     paragraph documenting that `data-testid` hooks are an internal
     test-only contract and may change without notice.
   - Optional: bump `docs/ARCHITECTURE_MAP.md` date from 2026-05-22 to
     2026-05-25.

   No code changes; no striatum workflow needed; lands in the audit
   commit directly per the precedent from the 2026-05-22 R1 batch and
   the 2026-05-23 R1 + R2 batches.

2. **R2 — Tooltip / inline-help code batch** (AUD-O-001 + AUD-O-002 +
   AUD-O-003 + AUD-O-004 + AUD-O-006 + AUD-O-011). Touches
   `kayakgen/ui/web/app.py`, `kayakgen/ui/web/generate_spec_form.py`,
   and `kayakgen/services/evaluation.py`. Needs its own striatum
   workflow per `feedback_striatum_required`. Scope:
   - validity badge: add `title=` or popover that names the four envelope
     states in plain text.
   - comparison-source toggle: add subtitle / tooltip explaining
     "Live frontier" vs. "Imported report" and pointing at the
     report-import workflow.
   - mesh readiness chip pair: add tooltip explaining the relationship
     between "No package built" and the live `status_readiness` value.
   - submit button: wire `disabled` + `aria-describedby` to a span that
     names the blocking validation reason ("Requires at least one
     variable", "Objectives not admissible", etc.).
   - mesh diagnostic table: human-readable labels for `boundary_edges`,
     `nonmanifold_edges`, etc., with threshold guidance.
   - Optional: high-angle GZ alert copy (AUD-O-007) — rewording to
     drop the RFC citations in favor of operator-facing recovery copy.

3. **R3 — Hydro labels registry follow-up** (AUD-O-005). Lift the
   hardcoded hydro row labels from `kayakgen/services/evaluation.py`
   into a registry following the D043 / RFC 0060 pattern. Likely a
   new RFC slice or a `HullParameterMetadata`-style sibling registry
   (`HydrostaticsRowMetadata`?). Defer until R2 lands; can be its own
   striatum workflow afterwards.

4. **R4 — Wontfix** (AUD-D-003). UBIQUITOUS_LANGUAGE does not glossarize
   pure UI patterns (validity badge, kind-aware submit, etc.); these
   live in `docs/USER_GUIDE.md` instead. Close as `wontfix` with a
   one-line note.

Info / null findings (Lane 1's seven + AUD-D-005..009 + AUD-O-011 +
AUD-O-016) need no action; they record the positive state for the next
audit's baseline.

## Notes for the workflow scaffold

The `release_candidate` preset worked as intended on a narrow
single-commit scope. The three lanes converged on the expected shape:
Lane 1 verified the "presentation-only" claim with seven null findings,
Lane 2 surfaced the central-docs catch-up gap, Lane 3 surfaced the
inline-help gap. The single-agent caveat is the only methodological gap;
future release-candidate runs should still attempt cross-provider lane
assignment where the providers are available.

The audit also demonstrates that the cadence shape itself catches the
"merged before audit" case cleanly: `b82b544` landed upstream between
the 2026-05-23 release_candidate audit and this one, and this audit
correctly bounded scope to the gap commit without re-auditing prior work.
