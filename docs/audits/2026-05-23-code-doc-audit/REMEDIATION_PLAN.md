# Remediation Plan — 2026-05-23 release_candidate audit

Date: 2026-05-23
Audit run: `docs/audits/2026-05-23-code-doc-audit/`

## Plan shape

8 open findings (2 medium, 5 low, 1 info / 1 partial-closed), grouped
into five remediation batches. Two land in-place from this audit (docs
only); three defer to follow-up striatum workflows.

## R1 — Audit index README

Severity: low
Findings: AUD-O-014
Owner surface: documentation only
Touched files: `docs/audits/README.md` (new).
Gating: none.
Follow-up classification: docs-only correction.
Status: **landed in the same change as this remediation plan**.

## R2 — Workflow 0029 SOURCES.md back-fill

Severity: low
Findings: AUD-O-015
Owner surface: documentation only
Touched files: `docs/workflows/0029-code-doc-audit/SOURCES.md`. Replace
the TODO placeholders with the canonical 2026-05-22 dogfood inputs,
flagged explicitly as "first-run record" so the template-vs-record
distinction is visible. The other workflow 0030-0034 SOURCES.md files
are intentionally minimal because each was driven by an agent prompt
with all inputs inline; their TODO-ness is by design.
Gating: none.
Follow-up classification: docs-only correction.
Status: **landed in the same change as this remediation plan**.

## R3 — Deprecation warning improvement

Severity: low
Findings: AUD-O-012
Owner surface: source (single string change)
Touched files: `kayakgen/ui/gui_params.py` deprecation warning message.
Add a pointer to RFC 0061 in the warning text so downstream consumers
who hit it have an actionable breadcrumb. Today's text already says
"deprecated by RFC 0061" but does not include a path; bump it to name
`docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md`.
Gating: `tests/test_gui_params.py::test_hull_from_gui_params_emits_rfc_0061_deprecation_warning` must still pass.
Follow-up classification: source change.
Status: **deferred to a follow-up striatum workflow** per
`feedback_striatum_required`. Bundle with R4 or R5.

## R4 — Render tests for RFC 0060 / 0061 label surfaces

Severity: medium
Findings: AUD-O-009 (web Vuetify `:hint` rendering),
AUD-O-010 (desktop matplotlib Slider label text).
Owner surface: tests only (no source change).
Touched files: new `tests/test_web_generate_panel_labels_render.py` (or
similar) verifying the `:hint` prop on each `VTextField` actually
receives the description string from the registry; new test in
`tests/test_desktop_layout.py` (or new file) verifying
`matplotlib.widgets.Slider(label=...)` actually receives
`label_with_unit(key)` for each row in `KayakGUI.SLIDERS`.
The web render test is tricky because Trame/Vuetify rendering is
client-side; the cheapest approach is to inspect the v3.VTextField
constructor arguments at form-build time. The desktop render test can
introspect the constructed `Slider` widget directly.
Gating: new tests must pass; existing test suites must remain green.
Follow-up classification: needs source/test work (test only, no
production source touched).
Status: **deferred to a follow-up striatum workflow**. Recommended
workflow `0035-render-tests-for-registry-labels`.

## R5 — `runs list` help-text symmetry with `runs jobs`

Severity: low (partial-closed)
Findings: AUD-O-011
Owner surface: CLI source (help-text addition only)
Touched files: `kayakgen/cli/runs_cli.py` — the `runs list` command
help text should enumerate the same `--kind sweep|search|cfd|comparison`
options that `runs jobs` already enumerates for `--state` and `--kind`.
Gating: existing `tests/test_cfd_jobs*.py` continue to pass.
Follow-up classification: source change (one Typer help string).
Status: **deferred to a follow-up striatum workflow**. Bundle with R3
into `0036-cli-help-text-polish` (or roll into R4's workflow if the
operator prefers a single landing).

## Follow-up workflow needs

R3 + R4 + R5 → one or two striatum workflows. Recommended split:

- `0035-render-tests-for-registry-labels` (R4 only; test-only)
- `0036-cli-help-text-polish` (R3 + R5; tiny CLI surface)

Both are small, single-implement+review-pair workflows; mirror the
shape of workflow 0034.

## Status closure rule

A finding's `status:` flips from `open` to `closed` when:

1. The named files are landed; AND
2. The gating tests pass (where applicable); AND
3. A `CHANGELOG.md` line references the finding ID; AND
4. The next audit (or the operator) confirms the close.

Conditions 1-3 trigger automatically when the in-place R1/R2 batch
lands or when the follow-up workflows for R3/R4/R5 ship. Condition 4
applies at the next `release_candidate` audit, which is the natural
checkpoint for this kind of remediation.
