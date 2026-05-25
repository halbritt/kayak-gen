# Pipeline-Integrity Audit Findings — Commit b82b544

Audit date: 2026-05-25  
Scope: Single commit `b82b544` ("Land WEB_UI_REWORK_2026-05-22 second-pass redesign")  
Claim: "Presentation-only rework per the 2026-05-22 brief. No backend capability added; build_spec_from_form_state wire output unchanged."

---

### AUD-P-001: hydro_rows_from_state and mesh_diagnostics_rows_from_state are pure presentation transformers

severity: info
category: claim_gate
status: open

claim: The two new helpers in evaluation.py admit no stronger claim than the underlying state; they do not fabricate readiness claims.

evidence:
- kayakgen/services/evaluation.py:435–449 — `hydro_rows_from_state` iterates over `analysis_view_model(state)["hydro_rows"]` and repackages tuples as dicts. Source data comes from `evaluate_hydrostatics(hull)`, which is an existing evaluator with no claim promotion in this commit.
- kayakgen/services/evaluation.py:452–486 — `mesh_diagnostics_rows_from_state` calls `diagnose_mesh(hull, part=part)` and extracts `diagnostics.readiness.level` (line 468). The readiness value is the live hull's mesh readiness, not a package readiness claim. The function never labels a status "ready" unless the underlying diagnostics object supports it.
- Both helpers are called only from app.py render callbacks that populate state fields for UI display (hydro_table_rows, mesh_hull_diagnostic_rows, mesh_deck_diagnostic_rows). They do not enter the submission or wire payload path.

impact: The new helpers preserve the RFC 0025 / 0027 claim-state invariant. No stronger label is emitted than the evidence supports.

recommended_action: No action. The claim holds.

follow_up: info

---

### AUD-P-002: Mesh readiness chip fix respects RFC 0046/0058 acceptance contract

severity: info
category: claim_gate
status: open

claim: The mesh readiness chip's two-chip rendering (when no package is selected) does not promote any readiness claim past evidence.

evidence:
- kayakgen/ui/web/app.py:1583–1601 — The template renders two chips when `mesh_package_status === 'No mesh package selected.'`: (1) a neutral "No package built" chip and (2) a `{{ status_readiness }}` chip that reads the live value from `evaluation_summary`.
- kayakgen/services/evaluation.py:228–234 — When no package is loaded, `evaluation_summary` explicitly returns `readiness["display"]: "unavailable"` and `readiness["reasons"]: ["No mesh package selected."]`. The "unavailable" label is data-backed and honest about the package state.
- kayakgen/ui/web/app.py:806–810 — `status_readiness` is populated from `evaluation_summary(state)["readiness"].get("display")` or `.get("level")` or defaults to "unavailable" on exception. The live chip always reads this value; it never hardcodes "ready" when a package is absent.
- tests/test_web_layout.py:595–610 — Test explicitly verifies that both `mesh-no-package-chip` and `mesh-live-readiness-chip` are present and that the status is "No mesh package selected."

impact: RFC 0046 (mesh opt-in gates) and RFC 0058 (CFD-in-loop acceptance contract) both require that a "no package built" state never admits a readiness claim stronger than the evidence. The fix resolves the prior "unavailable" contradiction by showing the live status alongside a neutral "No package built" label. The chip never claims readiness where there is none.

recommended_action: No action. The fix holds.

follow_up: info

---

### AUD-P-003: FORBIDDEN_METRIC_TOKENS noqa suppression does not hide coverage gap

severity: info
category: claim_gate
status: open

claim: The `# noqa: kg-orphan-color` suppression on FORBIDDEN_METRIC_TOKENS literals in generate_frontier_view.py does not bypass the orphan-color linter.

evidence:
- kayakgen/ui/web/generate_frontier_view.py:44–51 — Six string literals (`"max_gz_m"`, `"heel_at_max_gz_deg"`, etc.) each carry `# noqa: kg-orphan-color` comment.
- tests/test_ui_theme.py:165–174 — The `test_no_orphan_color_literals_under_kayakgen_ui` test scans all Python files under `kayakgen/ui/` (except theme.py) for color-literal constants. The test logic does not inspect or filter by `# noqa` comments; it reports all color literals found via AST walk.
- The six tokens are *not* color literals: they are metric key-name strings. The test will not flag them as offenders because `HEX_COLOR_RE.fullmatch()`, `normalized in COLOR_NAME_LITERALS`, and `GRAYSCALE_COLOR_RE.fullmatch()` all fail (they are alphanumeric underscore strings like `"max_gz_m"`, not hex codes, color names, or grayscale numerics).
- The refactoring from `"_".join(("max", "gz", "m"))` to `"max_gz_m"` is more readable and does not introduce a linter violation; the `# noqa` comment is defensive/precautionary because the prior form (tuple unpacking with string join) explicitly avoided the appearance of a bare string literal.

impact: The orphan-color linter still has full coverage of the file. The `# noqa` suppression is cosmetic and harmless. No real coverage gap exists.

recommended_action: Optional: The `# noqa: kg-orphan-color` comments are redundant for metric tokens but do no harm. A future refactor can remove them for clarity, but they do not hide a real issue.

follow_up: info

---

### AUD-P-004: build_spec_from_form_state wire output unchanged across tab/layout refactoring

severity: info
category: claim_gate
status: open

claim: The diff to `generate_spec_form.py` and its integration into `app.py` is layout and presentation only; the JSON payload shape, key names, and value types remain stable.

evidence:
- kayakgen/ui/web/generate_spec_form.py:599–696 — The `build_spec_from_form_state` function logic is unchanged: base_hull, variables, evaluators, objectives, algorithm, and budget are still extracted and serialized to the same Pydantic spec models (SweepSpec or SearchSpec). No dict keys were renamed, no value types promoted or demoted.
- kayakgen/ui/web/generate_spec_form.py:973–1042 — Variable rows now render as an HTML table (`<table class='kg-generate-variable-table'>`), but the v-model bindings (`row.name`, `row.kind`, `row.min`, `row.max`, `row.count`, `row.values`) are identical. The form still calls the same `_variable_to_sweep_payload` and `_variable_to_search_payload` functions to transform rows into the wire dict.
- kayakgen/ui/web/generate_spec_form.py:1133–1172 — Objective rendering uses a new HTML div structure with v-alert refusal blocks, but `generative_objective_directions[metric]` state bindings are unchanged. The `_objectives_block(state)` function (which builds the wire payload) is unmodified.
- kayakgen/ui/web/generate_spec_form.py:1215, 1266 — Label-only changes: "CFD-in-loop (opt-in)" → "CFD-in-loop evaluator (opt-in)" and "Raw JSON spec" → "Raw JSON (advanced)". No payload keys affected.
- tests/test_web_layout.py:671–677 — `test_generate_single_submit_button` verifies that the two submit buttons both carry the same `data-testid="generative-submit"` and check for both label strings but do not test wire payload (that's covered by pre-existing form-state tests, which remain unchanged).
- No changes to the return value of `build_spec_from_form_state` in this commit.

impact: RFC 0057 D-1 (wire format stability) is preserved. Integration tests and form-state round-trip tests continue to pin the payload structure.

recommended_action: No action. The claim holds.

follow_up: info

---

### AUD-P-005: controllers.py changes are pure import and export glue

severity: info
category: claim_gate
status: open

claim: The +4 lines in controllers.py are only new import and export statements; no control-plane state or logic is added.

evidence:
- kayakgen/ui/web/controllers.py diff lines show:
  - Line ~79: import `hydro_rows_from_state` (new)
  - Line ~81: import `mesh_diagnostics_rows_from_state` (new)
  - Lines ~147, ~151: add both to `__all__` export list
  - No new route handlers, no new state mutations, no new evaluator calls.

impact: The module's public API surface is extended to expose the two new helpers to the app layer, but no new processing or claim logic enters the controller.

recommended_action: No action. The change is mechanical.

follow_up: info

---

### AUD-P-006: App.py layout changes do not promote claim-state labels

severity: info
category: claim_gate
status: open

claim: The +310/-138 in app.py restructures tabs, replaces <pre> blocks with tables, and wires new helper outputs to state; no place promotes a result label past evidence.

evidence:
- kayakgen/ui/web/app.py:432–443 — New state fields are initialized: `mesh_hull_diagnostic_rows`, `mesh_deck_diagnostic_rows`, `hydro_table_rows`, `comparison_source`, `generative_jobs_table_rows`. All are presentation-only accumulators.
- kayakgen/ui/web/app.py:710–711 — `hydro_table_rows` is populated by calling `hydro_rows_from_state(state)` (see AUD-P-001).
- kayakgen/ui/web/app.py:743–756 — `mesh_hull_diagnostic_rows` and `mesh_deck_diagnostic_rows` are populated by calling `mesh_diagnostics_rows_from_state(state, part=...)` (see AUD-P-002).
- kayakgen/ui/web/app.py:1484–1507 — Hydro tab: the <pre> block is replaced with an HTML table that renders `hydro_table_rows` (no claim promotion; same underlying data).
- kayakgen/ui/web/app.py:1537–1557 — Mesh tabs: <pre> blocks replaced with HTML tables for `mesh_hull_diagnostic_rows` and `mesh_deck_diagnostic_rows` (no claim promotion).
- kayakgen/ui/web/app.py:1583–1601 — Mesh readiness chip: template v-if/v-else renders either two chips (when no package) or one readiness chip (when package loaded). Both cases draw their values from live state (status_readiness or mesh_readiness_level), never hardcoded labels.
- kayakgen/ui/web/app.py:1615–1650 — Comparison tab: new VBtnToggle for `comparison_source` (live_frontier vs. imported_report), with v_show blocks for each. Both blocks render pre-existing content; no new evaluator output or claim is introduced.
- kayakgen/ui/web/app.py:1845–1859 — Jobs index: <pre> block replaced with VDataTable rendering `generative_jobs_table_rows`. No claim state in job records; only metadata (job_id, job_kind, state).
- Spot-check: nowhere in app.py does the rework label a result `claim_state="validated"` or similar when the underlying record is `raw_unvalidated`. The chip/badge copy changes are purely presentational.

impact: The layout restructuring preserves the RFC 0025 / 0027 / 0058 invariants: no result surface is promoted past its evidence.

recommended_action: No action. No claim-state drift found.

follow_up: info

---

### AUD-P-007: Validity badge state binding and aria-labels respect accessibility contract

severity: info
category: claim_gate
status: open

claim: The new validity badge is wired correctly to the underlying state; it does not claim a validity status that is not computed.

evidence:
- kayakgen/ui/web/app.py:799–800 — `validity_badge` and `validity_badge_aria_label` are set by `_refresh_validity_badge(badge)`, which draws the badge string from the pre-existing `evaluate_design_validity(...)` function call.
- kayakgen/ui/web/app.py:1354–1368 — The badge is rendered as a VChip with:
  - text: `{{ validity_badge }}` (live binding to state)
  - aria-label: `("validity_badge_aria_label",)` (live binding to state)
  - role="status" and aria-live="polite" (correct accessibility semantics)
  - classes conditional on validity badge text start (success vs. warning color).
- tests/test_web_layout.py:544–557 — Test verifies that:
  - The validity badge is present in the parameter rail region.
  - At runtime, `web.state.validity_badge` is initialized to a truthy value.
  - The rendering order is correct (after region-params, before first VWindowItem).

impact: The badge is a live, state-backed indicator of design validity. It does not hardcode a validity claim; it reads the live badge value.

recommended_action: No action. The implementation is correct.

follow_up: info

---

## Summary

The commit b82b544 ("Land WEB_UI_REWORK_2026-05-22 second-pass redesign") is a genuine presentation-only rework. All six findings are informational (`severity: info`) because the audited invariants hold:

1. **Evaluation helpers** (`hydro_rows_from_state`, `mesh_diagnostics_rows_from_state`) are pure view-model transformers that do not promote claims.
2. **Mesh readiness fix** correctly renders two honest chips when no package is built; no readiness claim is fabricated.
3. **Orphan-color suppression** does not hide a real coverage gap; the metric tokens are not color literals.
4. **Wire output** (JSON payloads from `build_spec_from_form_state`) is unchanged; all keys and types are stable.
5. **Controllers** additions are mechanical imports/exports only.
6. **App.py layout changes** replace <pre> blocks with tables and wire new helpers; no claim-state drift is introduced.
7. **Validity badge** is correctly wired to live state with proper accessibility semantics.

**No critical, high, or medium findings.** The "presentation-only" claim holds under adversarial review.

