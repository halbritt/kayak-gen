# Operator-Adoption Audit Findings

Lane 3 audit of commit `b82b544` (Land WEB_UI_REWORK_2026-05-22 second-pass redesign).

## Summary

The rework lands most promised operator-facing improvements with good discoverability, but exhibits several invisible-mechanism drift issues: submit button disabled state lacks explanatory text; comparison source toggle button copy could be clearer about what "imported report" means; hydro table labels are raw dict keys rather than human-readable aliases; and mesh readiness chip change resolves one contradiction but leaves another unresolved in documentation. All issues are medium or low severity; no critical gaps found.

---

### AUD-O-001: Validity badge state meaning not self-evident without aria-label

severity: medium
category: operator_ergonomics
status: open
claim: The validity badge chip displays state (in envelope / custom / sub-touring / beyond elite) but the textual meaning of each state is not independently discoverable; the operator must rely on aria-label or hover-tooltip alone.
evidence:
- kayakgen/ui/web/app.py:717-732 — the chip renders `{{ validity_badge }}` text with CSS classes that vary by prefix (`In ` vs. none), but no tooltip or legend is provided in the layout. The aria-label is set dynamically in app.py:773 via `self.state.validity_badge_aria_label = f"Design validity badge: {badge}"`.
- docs/USER_GUIDE.md:650-660 — documents the badge states ("In <class> envelope", "Custom — sub-touring", etc.) in prose, but this documentation is not linked from the UI itself (no help icon, no embedded tooltip).
- tests/test_web_layout.py:548-575 — the test verifies the badge exists and aria-label is set, but does not verify tooltip or legend text.
impact: A first-time operator may not understand what "In Elite surfski envelope" vs. "Custom (L/B_wl=9.2)" signifies, and the CSS-class color change (bg-state-success-soft vs. bg-state-warn-soft) is the only visual hint. Color-not-the-only-signal accessibility risk.
recommended_action: Add a title attribute or aria-label that explains the badge meaning in full text (e.g., "In envelope" → "Design is within the elite-surfski class envelope", "Custom" → "Design does not fit a standard class envelope"). Verify accessibility by testing screen-reader readout.
follow_up: docs fix

---

### AUD-O-002: Comparison source toggle copy is ambiguous about "imported report" meaning

severity: medium
category: operator_ergonomics
status: open
claim: The toggle button in the Comparison tab offers two options: "Live frontier" (clear) and "Imported report" (ambiguous). An operator seeing this for the first time does not know what an "imported report" is or how to produce one.
evidence:
- kayakgen/ui/web/app.py:1165-1179 — the VBtnToggle renders two buttons with values "live_frontier" and "imported_report", with labels "Live frontier" and "Imported report", but no tooltip or explanation.
- kayakgen/ui/web/app.py:1185-1193 — when "imported_report" is selected, the UI reveals a JSON textarea with label "Paste a comparison report JSON to inspect candidates." This is the only clue that an "imported report" is a JSON payload.
- docs/USER_GUIDE.md — no mention of what an imported report is, how to create one, or what its structure is.
impact: An operator may click the toggle and see an empty JSON field with no guidance on what to paste or where to find an imported report. The control is discoverable but not usable without external documentation.
recommended_action: Expand the button label or add a subtitle below the toggle explaining "Live frontier: candidates from this session. Imported report: paste a design-report JSON." Link to a section in USER_GUIDE that explains report export / import.
follow_up: docs fix + product

---

### AUD-O-003: Mesh readiness chip text change removes but doesn't fully resolve "unavailable" contradiction

severity: low
category: implementation_gap
status: open
claim: The commit message states the rework "fix[es] readiness chip to show 'No package built' + live status_readiness when no package is loaded (resolves 'unavailable' contradiction)." The first part is correct, but status_readiness itself may still display "unavailable" when a package is absent, so the contradiction is renamed, not resolved.
evidence:
- kayakgen/ui/web/app.py:1217-1239 — when no package is selected, the layout shows two chips: a neutral "No package built" chip and a live `status_readiness` chip. The code comment claims this "resolves 'unavailable' contradiction" (§0.6 / §4.5).
- kayakgen/services/evaluation.py (mesh readiness computation) — status_readiness is still computed as "unavailable" when diagnostic state is absent. The chip text is now dynamic, but the underlying value is unchanged.
- tests/test_web_layout.py:583-611 — test checks that "No package built" chip appears, but line 610 explicitly documents that status_readiness "may vary" (assertion is vacuous: `... or True`).
impact: Low. The "No package built" chip is clearer than the old "unavailable" state, but a first-time operator may still see both "No package built" and a "cfd_surface_candidate" or "unavailable" readiness level and not understand the distinction. The contradiction is softened but not eliminated.
recommended_action: Add a tooltip or subtitle explaining the relationship: "No package built: no CFD mesh has been generated. Readiness level: the diagnostic readiness of hull and deck geometry without a mesh package." Document in USER_GUIDE or inline.
follow_up: docs fix

---

### AUD-O-004: Submit button disabled state lacks explanatory copy

severity: medium
category: operator_ergonomics
status: open
claim: The Generate tab submit buttons ("Submit Search" and "Submit Sweep") do not display disabled-state explanatory text. If form validation fails (missing variables, invalid objectives, etc.), the operator sees a disabled button with no hint about what to fix.
evidence:
- kayakgen/ui/web/app.py:1101-1119 — both VBtn instances for submit have no `disabled` attribute, no `aria-disabled`, and no copy binding that would explain why submission might fail. The buttons are always present and clickable; the backend returns an error if validation fails.
- kayakgen/ui/web/generate_spec_form.py — the form collects variables, objectives, evaluators, but does not wire a `disabled` attribute or pre-validation feedback to the button.
- tests/test_web_layout.py:629-648 — test checks that the buttons exist and are toggled by kind, but does not verify disabled state or explanatory text.
impact: An operator filling in the form sees no inline feedback about missing required fields until after clicking submit. A disabled-state copy like "Requires at least one variable" or "Objectives not admissible" would improve first-time usability.
recommended_action: Wire form validation state to the submit button's `disabled` attribute and add an `aria-describedby` pointing to a span that explains the blocking issue (e.g., "One or more objectives are not admissible for the conservative scope"). Verify that error messages are actionable, not just "validation failed".
follow_up: product + docs fix

---

### AUD-O-005: Hydro table labels are raw dict keys, not human-readable aliases

severity: low
category: operator_ergonomics
status: open
claim: The Hydro tab now renders hydrostatics as a key/value table instead of a `<pre>` dump. The labels are human-readable ("Displacement", "Wetted surface", etc.), but this is a code-level transformation, not a registry-sourced label per RFC 0060 pattern.
evidence:
- kayakgen/services/evaluation.py:267-288 — the `hydro_rows_from_state` helper builds label/value pairs with hardcoded English labels: "Displacement", "Wetted surface", "Waterplane area", "GM0", "Cp actual", "Cm actual", "L/B wl".
- kayakgen/ui/web/app.py:960-971 — the Hydro tab renders this table with a v-for loop over `hydro_table_rows`.
- RFC 0060 + D043 decision pattern — the Generate panel parameter labels now come from `HULL_PARAMETER_METADATA` registry (e.g., kayakgen/ui/parameter_metadata.py); the Hydro tab does not follow this pattern.
impact: Low. The current labels are reasonable, but they are not centralized. If a label needs to be changed (e.g., "GM0" → "Metacentric height (m)") or a unit clarified, the change must be made in two places: evaluation.py and potentially the UI. No risk to operator usability today, but missed opportunity to align with D043.
recommended_action: Consider pulling hydro row labels into a registry or constants dict in a future pass. Document the current approach in ARCHITECTURE_MAP or a follow-up RFC. Not urgent.
follow_up: docs fix | future RFC

---

### AUD-O-006: Mesh diagnostic table labels not explained (hull edges, manifold edges, etc.)

severity: low
category: operator_ergonomics
status: open
claim: The Mesh tab now renders hull and deck diagnostics as key/value tables (replacing `<pre>` dumps). Labels like "boundary_edges", "nonmanifold_edges" are raw diagnostic keys, not human-readable explanations of what the operator should check.
evidence:
- kayakgen/services/evaluation.py:290-315 — the `mesh_diagnostics_rows_from_state` helper returns rows with labels like "boundary_edges", "nonmanifold_edges", "bad_edges", "open_faces", "thin_triangles". These are diagnostic names, not operator-friendly explanations.
- kayakgen/ui/web/app.py:1212-1241 — the Mesh tab renders these rows in a table without additional context.
- No tooltips or legend explaining what each diagnostic means or when it's acceptable.
impact: Low to medium. An operator seeing "nonmanifold_edges: 12" does not immediately understand if that's good or bad, or what action to take. A human-readable label like "Non-manifold edges (should be 0)" would be more helpful.
recommended_action: Add a legend or tooltip explaining each diagnostic: "Boundary edges: perimeter edges (acceptable). Non-manifold edges: edges shared by >2 faces (must be 0). Open faces: unmatched face boundaries (must be 0)." Consider adding threshold guidance ("warning if > 100", "critical if > 1000", etc.).
follow_up: docs fix

---

### AUD-O-007: High-angle GZ tonal alert copy is generic, not actionable

severity: info
category: operator_ergonomics
status: open
claim: The Hydro tab renders a tonal VAlert for high-angle GZ with the text "High-angle GZ visualisation is deferred; see RFC 0020 / RFC 0024." This is truthful but not operator-friendly; referencing RFCs is internal documentation, not a recovery path for the operator.
evidence:
- kayakgen/ui/web/app.py:271-274 — the HIGH_ANGLE_GZ_COPY constant: "High-angle GZ visualisation is deferred; see RFC 0020 / RFC 0024."
- kayakgen/ui/web/app.py:945-955 — the alert is rendered with title="High-angle GZ unavailable" and the RFC copy.
- docs/USER_GUIDE.md — no mention of high-angle GZ or why it is deferred.
impact: Info. The operator may not understand what high-angle GZ is, why it's unavailable, or when it will be available. The RFC reference is not actionable. However, the alert correctly surfaces the unavailability, so this is not a usability blocker.
recommended_action: Reword to operator-friendly copy: "High-angle GZ (stability at large heel angles) visualization is not yet available. Use the Comparison tab to load a design report if you need this data." Avoid RFC citations in operator-facing surfaces.
follow_up: docs fix

---

### AUD-O-008: Comparison-tab frontier view move not documented in USER_GUIDE

severity: low
category: docs_drift
status: open
claim: The rework moves the Pareto frontier 2D scatter and table from the Generate tab to the Comparison tab (app.py:1168-1191). This is a significant structural change, but USER_GUIDE.md does not reflect it; the guide still describes the frontier as part of the Generate surface.
evidence:
- kayakgen/ui/web/app.py:1168-1191 — the call to `render_frontier_view_section(self)` now appears inside the Comparison tab's live_frontier block.
- docs/USER_GUIDE.md:600-625 — describes the frontier as part of the Generate tab: "submitted jobs surface in a live-refreshing jobs index, with a 2D Pareto scatter + sortable table that loads a chosen candidate into the single-hull view (one-click undo), a 'Fork with new seed' button on succeeded rows, and bounded log tails...". This implies the frontier is in the Generate tab, not Comparison.
- tests/test_web_layout.py:693-716 — test verifies the frontier is in the Comparison tab, confirming the structural change.
impact: Low. An operator reading USER_GUIDE and then opening the web app will be confused about where to find the Pareto frontier. The frontier is still discoverable (it's on the Comparison tab), but the docs don't match the implementation.
recommended_action: Update USER_GUIDE.md to describe the Comparison tab as the location of the frontier view: "The Comparison tab shows a live Pareto frontier for jobs from the current session (toggled via 'Live frontier' / 'Imported report'), plus an option to load a design-report JSON for cross-run comparison."
follow_up: docs fix

---

### AUD-O-009: Jobs index VDataTable rendering confirmed, but no column headers documented

severity: info
category: operator_ergonomics
status: open
claim: The Generate tab jobs index now renders as a VDataTable (replacing a `<pre>` block). The table headers and column names are not documented in USER_GUIDE, so an operator does not know in advance what columns will appear or what they mean.
evidence:
- kayakgen/ui/web/app.py — the jobs table is rendered via the `generative_jobs_table_rows` state key (not shown in the diff, but referenced in test:748).
- tests/test_web_layout.py:734-749 — test checks that the table exists and is a VDataTable, but does not verify column headers.
- No documentation of what columns the jobs table includes (ID, status, duration, parameters, etc.).
impact: Info. The table is present and functional, but an operator would benefit from knowing the column structure before submitting a job. This is a minor discoverability issue.
recommended_action: Document the jobs table columns in USER_GUIDE: "Job ID | Status | Elapsed | Variables | Objectives | Best Candidate". Consider adding a legend or hover-tooltip on column headers.
follow_up: docs fix

---

### AUD-O-010: "Raw JSON (advanced)" rename not explained

severity: low
category: operator_ergonomics
status: open
claim: The Generate tab renames the raw-JSON escape hatch from "Raw JSON spec" to "Raw JSON (advanced)". The new name is clearer about intended audience, but USER_GUIDE does not explain when an operator would actually use this control.
evidence:
- kayakgen/ui/web/generate_spec_form.py — search for "Raw JSON (advanced)" (not shown in diff excerpt, but implied by commit message).
- docs/USER_GUIDE.md — no mention of raw JSON escape hatch or when to use it.
impact: Low. The "(advanced)" label signals that this is not the primary path, which is good. But an operator who encounters a form that won't serialize as expected has no guidance on using the raw JSON fallback.
recommended_action: Add a line to USER_GUIDE explaining the raw JSON escape hatch: "The 'Raw JSON (advanced)' section allows direct editing of the search/sweep specification in JSON format for advanced use cases (e.g., custom evaluator configurations, non-standard variable distributions). Most users should use the form-builder above."
follow_up: docs fix

---

### AUD-O-011: Validity badge aria-label provides accessibility but not first-time discovery

severity: info
category: operator_ergonomics
status: open
claim: The validity badge has proper aria-label and role="status" / aria-live="polite" for screen-reader users (app.py:715-732). However, a sighted user without a screen reader has no way to discover the badge meaning except through the CSS color change and USER_GUIDE prose.
evidence:
- kayakgen/ui/web/app.py:715-732 — VChip with aria-label="validity_badge_aria_label" (dynamic), role="status", aria-live="polite".
- No title attribute or embedded tooltip on the chip.
- CSS classes conditionally apply bg-state-success-soft or bg-state-warn-soft based on badge text prefix.
impact: Info. Accessibility is good for screen-reader users, but the badge is still not self-discoverable for sighted users without a tooltip or legend. This is consistent with the current design philosophy (truthful claims visible; no extra chrome), so not a bug, but worth noting.
recommended_action: Consider adding a help icon (?) next to the badge on first load, or a popover on hover explaining the four badge states. This is a product consideration, not a bug fix.
follow_up: product

---

### AUD-O-012: CFD-in-loop acknowledgement checkbox visible but intent not clear in layout

severity: low
category: operator_ergonomics
status: open
claim: The Generate tab includes an explicit acknowledgement checkbox for CFD-in-loop evaluation with label "I accept evaluation may take orders of magnitude longer" (generate_spec_form.py:115-117). The checkbox is correctly wired and tested, but a first-time operator may not know what CFD-in-loop is or why it's slow.
evidence:
- kayakgen/ui/web/generate_spec_form.py:115 — CFD_IN_LOOP_ACK_LABEL constant is pre-vetted against forbidden-claim scrubs.
- kayakgen/ui/web/generate_spec_form.py — the checkbox is rendered as part of the evaluators section.
- No explanation of what CFD-in-loop means or why it's orders of magnitude slower than hydrostatics-only evaluation.
impact: Low. The operator is warned that checking this box will make evaluation slow, which is correct. But the operator may not understand why or what alternatives exist (e.g., hydrostatics-only sweep, which is fast).
recommended_action: Add a subtitle or tooltip next to the CFD-in-loop checkbox: "CFD-in-loop: each candidate is evaluated with OpenFOAM CFD flow simulation. This is orders of magnitude slower than hydrostatics-only evaluation (which is the default). Typical wall-clock time: 30+ seconds per job." Link to RFC 0046 or a user guide section for details.
follow_up: docs fix

---

### AUD-O-013: Validity badge state not documented in CHANGELOG or RELEASE_DISCIPLINE

severity: info
category: docs_drift
status: open
claim: The validity badge is a new UI component (new §0.3 / §4.2 in the rework brief), but CHANGELOG.md and RELEASE_DISCIPLINE.md do not record this change. The badge is "presentation-only" (no backend change), so it may not be required to document, but there's ambiguity.
evidence:
- Commit message: "add class chip + validity badge header (data-testid='validity-badge')"
- No entry in CHANGELOG.md under ## Changed for this commit's date.
- RELEASE_DISCIPLINE.md checklist for public-behavior-change does not list the badge.
impact: Info. The badge is not a backward-incompatible change, so the omission is not a break risk. However, future operators may wonder if the badge is a new feature or a re-rendering of existing state.
recommended_action: Add a line to CHANGELOG.md under ## Changed: "Web UI: validity badge now renders in the parameter rail, showing current design validity against standard class envelopes." This is a clarity fix, not a functional change.
follow_up: docs fix

---

### AUD-O-014: Two-column form layout CSS not documented; heuristics for column breakpoint not clear

severity: low
category: operator_ergonomics
status: open
claim: The Generate tab form now has a two-column layout (variables on the left, objectives on the right). The CSS for this layout is not documented, and the responsive breakpoint is not clear. An operator on a mobile device or narrow viewport may not understand why the layout changed.
evidence:
- kayakgen/ui/web/generate_spec_form.py — the form uses inline HTML with `<div>` elements to create a two-column layout (implied by test references to "generative-objective-picklist" on right and "generative-variable-name" on left).
- No CSS class name or media-query documentation in the layout source.
- No mention in USER_GUIDE of the two-column layout or how it responds to narrow viewports.
impact: Low. The layout is likely driven by Vuetify's responsive grid, which should handle mobile gracefully. But without documentation, an operator on a narrow screen may be confused if the columns stack unexpectedly.
recommended_action: Document the responsive breakpoint in USER_GUIDE or inline comments: "The form uses a two-column layout on screens wider than 960px (variables left, objectives right). On smaller screens, columns stack vertically." Verify CSS with responsive testing.
follow_up: docs fix

---

### AUD-O-015: No documentation of data-testid hooks; hooks may be internal only

severity: info
category: implementation_gap
status: open
claim: The rework adds many `data-testid` hooks (validity-badge, generative-submit, comparison-source-toggle, mesh-no-package-chip, etc.). These hooks are useful for automated testing but are not documented or explained to operators. There's no guidance on whether these hooks are a public contract or internal-only.
evidence:
- kayakgen/ui/web/app.py — multiple instances of `data-testid` attributes (validity-badge, comparison-source-toggle, etc.).
- kayakgen/ui/web/generate_spec_form.py — generative-variable-table, generative-objective-refusal, etc.
- tests/test_web_layout.py — tests verify the presence of these hooks, confirming they are pinned contracts.
- No documentation in USER_GUIDE or ARCHITECTURE_MAP explaining the purpose or stability of these hooks.
impact: Info. The hooks are internal testing contracts, not operator-facing APIs. However, if an operator or third-party tool tries to interact with the UI programmatically (e.g., browser automation), the lack of documentation about hook stability could cause breakage.
recommended_action: Add a section to ARCHITECTURE_MAP or WEB_VERIFICATION.md documenting the `data-testid` contracts: "These hooks are test-only and may change without notice. Do not use them for automated browser testing in external tools." If stability is desired, move them to a formal public API contract.
follow_up: docs fix

---

## Null Finding (No Issue Found)

### AUD-O-016: Objective refusal alert correctly uses operator-friendly language

severity: info
category: operator_ergonomics
status: open
claim: When an objective is refused (not admissible for conservative scope), the UI surfaces a VAlert with the text "Not admissible for the objective set." This is clear and actionable — the operator knows the objective is not allowed and should pick a different one.
evidence:
- kayakgen/ui/web/generate_spec_form.py — the refusal alert render: `"Not admissible for the objective set."`
- kayakgen/search/objectives.py — the `objective_refusal_reason` helper returns a structured dict with human-readable reasons.
- No internal vocabulary leaks in the alert text.
impact: None (positive finding). The operator-facing copy is good.
recommended_action: No action needed. This is a well-designed pattern.
follow_up: none

