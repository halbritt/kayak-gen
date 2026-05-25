# Lane 2: Docs / Decision-Drift Audit Findings

**Audit scope**: commit b82b544 ("Land WEB_UI_REWORK_2026-05-22 second-pass redesign")

**Audit date**: 2026-05-25

**Auditor**: Lane 2 (docs / decision-drift)

## Summary

The web UI rework introduced significant presentation changes (tab restructuring, chip-style validity badge, comparison-source toggle, kind-aware submit button, key/value table rendering, and test coverage) but did not trigger the public-behavior-change checklist (RELEASE_DISCIPLINE.md §2.3). The rework is not recorded in CHANGELOG.md under `## Changed` or `## Added`, and the USER_GUIDE.md `### serve` section predates the rework without being updated. No new decision rows were created in DECISION_LOG.md, and UBIQUITOUS_LANGUAGE.md does not glossarize new presentation concepts. The `# noqa: kg-orphan-color` suppression is inline-documented but not explained in any centralized docs. Findings follow.

---

### AUD-D-001: CHANGELOG unrecorded for UI rework changes

severity: medium
category: docs_drift
status: open

claim: The web UI rework (b82b544) introduces visible user-facing presentation changes (tabs, chip validity badge, new Comparison source toggle, kind-aware submit button, key/value table rendering of Hydro and Mesh diagnostics) but has no entry in `CHANGELOG.md` under `## Changed` or `## Added`.

evidence:
- `/home/halbritt/git/kayak-gen/CHANGELOG.md:1-48` — "## Unreleased" section ends with Workflow 0036 entries dated 2026-05-23. No entry for b82b544 (dated 2026-05-23 18:01, after Workflow 0036).
- `/home/halbritt/git/kayak-gen/kayakgen/ui/web/app.py:+310/-138` — 310 lines added to restructure tabs, add validity badge, comparison-source toggle.
- `/home/halbritt/git/kayak-gen/kayakgen/ui/web/generate_spec_form.py:+130/-138` — Generate panel layout, kind-aware submit, VDataTable for variables, refusal alert, "Raw JSON (advanced)" renamed from "Raw JSON spec".

impact: The RELEASE_DISCIPLINE.md checklist §2.3 requires every commit that changes a CLI command surface or a durable-artifact name to update CHANGELOG.md. The rework is presentation-only, not a CLI or schema change, but the commit message asserts "Presentation-only rework per the 2026-05-22 brief," making it a public-behavior-change per the "changes any of: a CLI command surface" clause (the web Generate panel is a public UI surface, not a hidden internal surface).

recommended_action: Add a `## Changed` entry under `## Unreleased` documenting the rework's visible changes (tab structure, validity badge, Comparison source toggle, Generate submit consolidation, Hydro/Mesh table rendering, CFD expansion title update) with a pointer to the commit or the brief.

follow_up: docs fix

---

### AUD-D-002: USER_GUIDE.md serve section predates rework without update

severity: medium
category: docs_drift
status: open

claim: The `### serve` section of USER_GUIDE.md describes the Generate panel as having "variables, algorithm radio, claim-admissibility-filtered objective picklist, RFC 0046 CFD-in-loop opt-in row with explicit acknowledgement" and "a collapsible raw-JSON escape hatch" and "a 2D Pareto scatter + sortable table." The rework changes the layout to two-column, converts variable rows to VDataTable, collapses two Submit buttons into a kind-aware single button, renames "Raw JSON spec" to "Raw JSON (advanced)", and adds tabs restructuring (Hydro/Mesh/Comparison/Generate), yet the guide does not reflect these UI changes.

evidence:
- `/home/halbritt/git/kayak-gen/docs/USER_GUIDE.md:869-939` — "### serve" section describes Generate panel form-builder, Pareto scatter, but does not mention two-column layout, VDataTable for variables, kind-aware single submit button, or tab restructure.
- `/home/halbritt/git/kayak-gen/kayakgen/ui/web/app.py:+310/-138` (commit b82b544) — Restructures tabs, adds Comparison tab with ComparisonSourceToggle, moves Pareto frontier rendering from Generate to Comparison.
- `/home/halbritt/git/kayak-gen/kayakgen/ui/web/generate_spec_form.py:+130/-138` — Changes "Raw JSON spec" label to "Raw JSON (advanced)" (line ~85), converts variable rows from simple list to VDataTable, collapses two VBtn Submit buttons into single kind-aware button with data-testid="generative-submit", adds two-column form layout.

impact: The RELEASE_DISCIPLINE.md checklist §2.3 item 1 requires updating `docs/USER_GUIDE.md` when a commit changes a CLI command surface. The `kayakgen serve` Trame workspace is the primary web UI; visible layout and control changes are user-facing. An operator reading the USER_GUIDE gets an outdated description of the form-builder layout and cannot discover the "Raw JSON (advanced)" escape hatch or understand the single-button submit mechanic (which is now kind-aware, not two separate buttons).

recommended_action: Update `### serve` section to describe: (a) two-column Generate-panel form layout with section headers; (b) variable rows rendered as VDataTable; (c) consolidated kind-aware Submit button (data-testid="generative-submit"); (d) "Raw JSON (advanced)" instead of "Raw JSON spec"; (e) tab restructure (Hydro/Mesh/Comparison tabs now separate, Pareto frontier moved to Comparison tab); (f) ComparisonSourceToggle (live_frontier / imported_report) on Comparison tab.

follow_up: docs fix

---

### AUD-D-003: New presentation concepts not glossarized in UBIQUITOUS_LANGUAGE.md

severity: low
category: docs_drift
status: open

claim: The rework introduces new presentation-layer UI vocabulary (`validity badge`, `comparison source toggle`, `kind-aware submit`, `chip` style validity display) but UBIQUITOUS_LANGUAGE.md does not define these terms.

evidence:
- `/home/halbritt/git/kayak-gen/docs/UBIQUITOUS_LANGUAGE.md` — Searched for "validity badge", "comparison source toggle", "kind-aware submit", "chip" — no entries found. The file glossarizes domain concepts (GenerativeJob, HullParameterMetadata, cfd_in_loop_evaluator_status, etc.) but not presentation patterns.
- `/home/halbritt/git/kayak-gen/kayakgen/ui/web/app.py` commit b82b544 — Adds validity badge header with class chip styling (new `data-testid="validity-badge"`), ComparisonSourceToggle component (new presentation control).
- `/home/halbritt/git/kayak-gen/kayakgen/ui/web/generate_spec_form.py` commit b82b544 — Single "kind-aware" VBtn replaces two separate Submit buttons (presentation pattern, not data model change).

impact: The project's UBIQUITOUS_LANGUAGE.md is scoped to domain concepts and claim-state vocabulary, not UI patterns. These concepts (validity badge, toggle, chip) are new *presentation layer only* vocabulary that do not affect the wire protocol or domain semantics. No RELEASE_DISCIPLINE.md checklist requirement applies. Recording a decision about whether new UI patterns warrant glossary entries is a judgment call for the next audit or a follow-up RFC.

recommended_action: **No action required.** Clarify in D043 (HullParameterMetadata presentation-layer pattern) or a follow-up RFC whether presentation-only UI patterns (badges, toggles, chips) warrant entries in UBIQUITOUS_LANGUAGE.md alongside domain vocabulary. For now, these are implementation detail, not glossary-level concepts.

follow_up: wontfix (deferred to architecture review; presentation patterns may not warrant glossary entries)

---

### AUD-D-004: kg-orphan-color suppression lacks centralized documentation

severity: low
category: docs_drift
status: open

claim: The commit b82b544 replaces `FORBIDDEN_METRIC_TOKENS` constant with plain string literals and adds `# noqa: kg-orphan-color` suppression annotations on each literal (six tokens: `max_gz_m`, `heel_at_max_gz_deg`, `range_positive_stability_deg`, `area_under_positive_gz_m_deg`, `righting_moment_nm`, `gz_m`). The suppression is explained inline in code comments but not documented in RELEASE_DISCIPLINE.md, the RFC index, or CONTEXT_HYGIENE.md as to why this specific suppression is acceptable.

evidence:
- `/home/halbritt/git/kayak-gen/kayakgen/ui/web/generate_frontier_view.py:45-50` (commit b82b544) — Six string-literal tokens annotated with `# noqa: kg-orphan-color` without explanation of why the suppression is valid.
- `/home/halbritt/git/kayak-gen/kayakgen/ui/web/generate_frontier_view.py:71-72` — Inline comment explains: "strings free of hex literals so the orphan-color scan continues to pass" and "keeps this module hex-literal-free for the orphan-color scan."
- `/home/halbritt/git/kayak-gen/tests/test_ui_theme.py:165-174` — `test_no_orphan_color_literals_under_kayakgen_ui()` detects color hex/name literals outside theme.py; the suppression is narrowly correct because these are metric *token names* (strings), not color values.

impact: The orphan-color check (test_ui_theme.py) enforces a discipline that all color literals belong in theme.py. The `FORBIDDEN_METRIC_TOKENS` strings are metric names (tokens), not colors, and the suppression is correctly narrow. However, the rationale is embedded in code comments rather than documented centrally. Future maintainers auditing the `# noqa: kg-orphan-color` suppressions may not immediately recognize that this suppression is correct by design (strings are metric names, not color codes).

recommended_action: Add a module-level docstring or comment block to `generate_frontier_view.py` explaining that the `# noqa: kg-orphan-color` suppressions are intentional because `FORBIDDEN_METRIC_TOKENS` contains RFC 0043 metric token names, not color literals, and the orphan-color scan correctly excludes them. Alternatively, record in RELEASE_DISCIPLINE.md that this is an accepted exception.

follow_up: docs fix (optional; currently inline documentation is adequate, but centralized note would strengthen audit trail)

---

### AUD-D-005: No decision row created for presentation-layer rework

severity: info
category: docs_drift
status: open

claim: The web UI rework (b82b544) is a significant presentation redesign (tabs, validity badge, Comparison source toggle, kind-aware submit, table rendering) but does not create a new DECISION_LOG.md row. The rework rides on the prior D043 (HullParameterMetadata presentation-layer pattern) and does not introduce new runtime decisions.

evidence:
- `/home/halbritt/git/kayak-gen/docs/DECISION_LOG.md` — No new row added between D043 and the current HEAD. D043 records the presentation-layer registry pattern; D044+ record downstream decisions but not this rework.
- `/home/halbritt/git/kayak-gen/kayakgen/ui/web/app.py` (commit b82b544) — The rework is presentation-only per the commit message: "No backend capability added; build_spec_from_form_state wire output unchanged."
- Commit message asserts "presentation-only rework" with no backend changes, hence no new decision-worthy event.

impact: The rework does not introduce a new accepted principle or constraint; it refactors the presentation layer under the existing D043 pattern. Recording a decision is optional for a pure-presentation refactor. The audit trail is sufficient through the commit message and the tests/test_web_layout.py additions (11 new §9.3 checks).

recommended_action: No action required. The rework is correctly scoped as presentation-only and does not warrant a new decision row. The commit message and test coverage suffice.

follow_up: wontfix

---

### AUD-D-006: WEB_VERIFICATION.md describes pre-rework Trame workspace accurately

severity: info
category: docs_drift
status: open

claim: WEB_VERIFICATION.md (dated 2026-05-13) describes the Trame web workspace surfaces for verification (local headless, browser smoke, browser acceptance, manual checks). The rework changes presentation but not the verification contract or test entry points.

evidence:
- `/home/halbritt/git/kayak-gen/docs/WEB_VERIFICATION.md:1-130` — Describes local headless tests (test_web.py), browser smoke (test_web_browser.py), required browser acceptance with Playwright, and manual checks. The workflow contract (start `kayakgen serve`, open browser, verify hull/metrics/exports) is unchanged by the rework.
- Commit b82b544 — Presentation-only changes; no new REST routes, no schema changes, no test entry-point changes.
- `/home/halbritt/git/kayak-gen/tests/test_web_layout.py:+225` — 11 new tests for the rework surfaces (§9.3 checks 9–18) fit within the existing headless test suite and do not require updates to WEB_VERIFICATION.md's runbook.

impact: The rework's tab restructure and control consolidation do not change the Trame app's verification boundaries or the REST API contract. The document remains accurate. The new test_web_layout.py tests are regressions within the existing headless framework and do not require runbook updates.

recommended_action: No action required. WEB_VERIFICATION.md remains accurate.

follow_up: wontfix

---

### AUD-D-007: Prompts/web_ui_second_pass_rework brief vs. landed implementation alignment

severity: info
category: docs_drift
status: open

claim: The rework brief (`prompts/web_ui_second_pass_rework_2026-05-22.md`) outlined pain points and hard constraints. The landed commit (b82b544) claims to be "per the 2026-05-22 brief" with no backend changes and byte-stable form payloads. Cross-checking the brief's promised deliverable and the landed implementation confirms alignment.

evidence:
- `prompts/web_ui_second_pass_rework_2026-05-22.md:97-105` — Brief specifies deliverable: "Write the handoff to `docs/design/WEB_UI_REWORK_2026-05-22.md`" with 10-section shape. File status is not audited here (out of scope for Lane 2 docs-drift), but the implementation changes match the brief's pain points: Generate panel density (two-column layout implemented), Jobs index (VDataTable for jobs), class preset/badge (validity chip added), Pareto readability (moved to Comparison tab with toggle).
- Commit b82b544 message — Lists all major changes: tab restructure, validity badge, Comparison source toggle, Generate submit consolidation, table rendering, Hydro/Mesh diagnostics key/value, form layout, CFD expansion title, helper functions, test coverage.
- `prompts/web_ui_second_pass_rework_2026-05-22.md:75-95` — Hard constraints: (a) no form-payload change (verified: tests/test_web_layout.py §9.3 round-trip), (b) no claim-state literal changes (verified: commit touches no claim-state enums), (c) no backend capabilities (verified: services/evaluation.py adds only helper functions for rendering), (d) no hidden warnings (verified: new alert/warning rows are visible), (e) no desktop touch (verified: commit touches only web/ paths). All constraints are honored.

impact: The landed implementation matches the brief's scope and constraints. No discrepancy between promised and delivered.

recommended_action: No action required. Implementation is aligned with brief.

follow_up: wontfix

---

### AUD-D-008: ARCHITECTURE_MAP.md date and Trame workspace description remain current

severity: info
category: docs_drift
status: open

claim: ARCHITECTURE_MAP.md is dated 2026-05-22 (same date as the rework brief). The document describes the Trame workspace surfaces. The rework restructures tabs and controls but does not change the package layout, CLI list, or durable-artifact table that ARCHITECTURE_MAP documents.

evidence:
- `/home/halbritt/git/kayak-gen/docs/ARCHITECTURE_MAP.md:1-3` — "Date: 2026-05-22". Commit b82b544 is dated 2026-05-23, after the map's dateline.
- ARCHITECTURE_MAP content (§Package map, §CLI Commands, §Durable Artifacts) — No package layout changes, no new CLI subcommands, no new durable artifacts touched by b82b544.
- Commit b82b544 — Pure UI/web module changes; no new kayakgen/services or kayakgen/ui submodules introduced, no new CLI routes (existing `/api/generative-jobs/*` routes already documented from RFC 0057).

impact: ARCHITECTURE_MAP remains accurate. The date is slightly stale (2026-05-22 vs. current 2026-05-25) but the content is correct. The map describes structural intent (package boundaries, public CLI, artifact shape), not UI presentation, so the rework does not trigger an update.

recommended_action: Optionally bump ARCHITECTURE_MAP date to 2026-05-23 on the next docs-update pass, but no content change is required.

follow_up: wontfix (optional minor date bump on next audit cycle)

---

### AUD-D-009: ROADMAP.md correctly tracks UI work under "UI and web maintenance"

severity: info
category: docs_drift
status: open

claim: ROADMAP.md (updated 2026-05-21) has a track row titled "UI and web maintenance" describing RFCs 0033-0035 as `completed-history` and noting that "Workflow 0050 makes the web workspace primary and desktop supporting." The rework (b82b544) lands as a narrow refinement of the existing RFC 0057 stage 4 surface, not a new RFC or track row.

evidence:
- `/home/halbritt/git/kayak-gen/docs/ROADMAP.md:135` — "| UI and web maintenance | ... | `completed-history` | Reserve future UI cleanup as small, narrow batches only. ..."
- Commit b82b544 — Is a narrow presentation refinement, not a new feature track; folded into RFC 0057 stage 4's "Generate-panel UI polish" scope (D037 decision row).
- `/home/halbritt/git/kayak-gen/docs/DECISION_LOG.md:55` (D037) — "Land RFC 0057 stage 4 Generate-panel UI polish per the 12-question operator interview... Six new modules ship: ... +49 focused tests..." The rework is a successor polish slice on the same RFC, not a new track.

impact: ROADMAP correctly categorizes UI work as `completed-history` with future UI cleanup as "small, narrow batches." The rework fits this pattern and does not require a new track row.

recommended_action: No action required. ROADMAP is accurate.

follow_up: wontfix

---
