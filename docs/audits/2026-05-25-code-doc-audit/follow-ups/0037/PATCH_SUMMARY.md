# Workflow 0037 — Inline-help additions (audit R2) — Patch Summary

Date: 2026-05-25
Workflow: `0037-web-ui-inline-help`
Closes: AUD-O-001 · AUD-O-002 · AUD-O-003 · AUD-O-004 · AUD-O-006 · AUD-O-007 (in-app copy)

## Files changed

| Path | Change |
|---|---|
| `kayakgen/ui/web/app.py` | Validity-badge `title=` binding + `validity_badge_title_for` helper; comparison-source toggle subtitle + per-button `title` tooltips; mesh chip-pair `title` tooltips; high-angle GZ alert copy rewrite (drops RFC 0020 / RFC 0024 citations). |
| `kayakgen/ui/web/generate_spec_form.py` | `compute_submit_blocking_reason` + `refresh_submit_blocking_reason` helpers; new `SUBMIT_BLOCKING_REASON_*` copy constants; seeded `generative_submit_blocking_reason` + `generative_submit_disabled` state fields. |
| `kayakgen/services/evaluation.py` | `mesh_diagnostics_rows_from_state` label rewrite — threshold guidance embedded in the existing English `label` slot (`Non-manifold edges (must be 0)`, `Degenerate faces (must be 0)`, `Boundary edges (perimeter; acceptable)`, `Readiness level`). Row order + `{label, value}` shape unchanged. |
| `tests/test_web_inline_help.py` | NEW — 11 render-verification tests mirroring `tests/test_web_layout.py`. |

## New / changed surfaces (path · line)

| Finding | Surface | File:line |
|---|---|---|
| AUD-O-001 | `validity_badge_title_for(badge)` helper | `kayakgen/ui/web/app.py:324` |
| AUD-O-001 | VChip `title=` binding to `validity_badge_title` | `kayakgen/ui/web/app.py:1464` |
| AUD-O-001 | State seed in `_refresh_validity_badge` | `kayakgen/ui/web/app.py:888` |
| AUD-O-002 | Per-button `title` tooltips on the toggle | `kayakgen/ui/web/app.py:1732,1740` |
| AUD-O-002 | Visible `comparison-source-help` subtitle block | `kayakgen/ui/web/app.py:1745-1758` |
| AUD-O-003 | `mesh-no-package-chip` `title` attribute | `kayakgen/ui/web/app.py:1688` |
| AUD-O-003 | `mesh-live-readiness-chip` `title` attribute | `kayakgen/ui/web/app.py:1692` |
| AUD-O-004 | `compute_submit_blocking_reason(state)` | `kayakgen/ui/web/generate_spec_form.py:903` |
| AUD-O-004 | `refresh_submit_blocking_reason(app)` | `kayakgen/ui/web/generate_spec_form.py:964` |
| AUD-O-004 | Submit button `disabled` + `aria-describedby` | `kayakgen/ui/web/app.py:1929-1950` |
| AUD-O-004 | Visible `submit-blocking-reason-{kind}` span | `kayakgen/ui/web/app.py:1951-1973` |
| AUD-O-006 | Threshold guidance in row labels | `kayakgen/services/evaluation.py:473-487` |
| AUD-O-007 | `HIGH_ANGLE_GZ_COPY` rewrite (no RFC citations) | `kayakgen/ui/web/app.py:272-276` |

## Test counts (per `pytest --collect-only -q`)

`tests/test_web_inline_help.py` — 11 tests:

1. `test_validity_badge_title_covers_all_states` (AUD-O-001)
2. `test_validity_badge_chip_binds_title_attribute` (AUD-O-001)
3. `test_comparison_source_toggle_subtitle_present` (AUD-O-002)
4. `test_mesh_chip_pair_tooltips_present` (AUD-O-003)
5. `test_submit_disabled_when_no_variables` (AUD-O-004)
6. `test_submit_enabled_when_form_valid` (AUD-O-004)
7. `test_submit_disabled_when_no_objective_selected` (AUD-O-004)
8. `test_submit_button_has_aria_describedby` (AUD-O-004)
9. `test_mesh_diagnostics_rows_have_operator_facing_labels` (AUD-O-006)
10. `test_high_angle_gz_alert_drops_rfc_citations` (AUD-O-007 in-app copy)
11. `test_build_spec_from_form_state_wire_payload_stable` (AUD-P-004 regression)

## Forbidden-path scope confirmation

The following paths were NOT touched (per the workflow's `forbidden_paths`
contract):

- `CHANGELOG.md`
- `docs/USER_GUIDE.md`
- `docs/DECISION_LOG.md`
- `docs/audits/2026-05-25-code-doc-audit/SYNTHESIS.md`
- `docs/audits/2026-05-25-code-doc-audit/REMEDIATION_PLAN.md`
- `docs/audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md`
- `docs/audits/README.md`
- `docs/rfcs/` (any path)
- `kayakgen/ui/web/generate_frontier_view.py`
- `kayakgen/ui/web/controllers.py`
- `kayakgen/ui/parameter_metadata.py`

In addition, the function-level carve-out for `evaluation.py` is respected:

- `kayakgen/services/evaluation.py::hydro_rows_from_state` — UNCHANGED.
  Workflow 0038 (R3) owns that function. The diff in `evaluation.py` is
  contained to `mesh_diagnostics_rows_from_state` (lines 466-486).
- `kayakgen/services/evaluation.py::analysis_view_model` — UNCHANGED.

## Wire-payload stability (AUD-P-004 regression)

`build_spec_from_form_state(state)` returns the same top-level dict keys
and value types after the inline-help additions land. This is pinned by
`test_build_spec_from_form_state_wire_payload_stable`, which:

- Builds a valid search-kind state and asserts the returned dict has the
  full RFC-pinned key set
  `{schema_version, name, base_hull, search_space, algorithm, objectives, evaluators, budget}`
  with the expected value types.
- Builds a valid sweep-kind state and asserts the returned dict has
  `{schema_version, name, base_hull, variables, evaluators}` with the
  expected value types.
- Confirms the existing `no_variables` gate still raises
  `GenerateSpecFormError` (presentation-only blocking-reason copy does
  not weaken the build-time gate).

The new state fields (`generative_submit_disabled`,
`generative_submit_blocking_reason`, `validity_badge_title`) are
presentation-only — they are written by reactive refresh hooks and are
never read by `build_spec_from_form_state`.

## Verification

Run in the project venv:

```bash
cd /home/halbritt/git/kayak-gen && .venv/bin/pytest \
  tests/test_web_inline_help.py \
  tests/test_web_layout.py \
  tests/test_web.py \
  tests/test_ui_theme.py \
  tests/test_vocabulary_coverage.py \
  -q
```

Result: **116 passed** (105 baseline + 11 new).
