author: remediator-codex-gpt-5.5-001
schema_version: striatum.patch_summary.v1
kind: patch_summary
logical_name: patch_summary
workflow_id: 0059-rfc-0065-slice2-shell-layout
role: remediator

# Patch Summary — RFC 0065 Slice 2 Remediation

## Remediated Findings

- M1: removed the Slice 3 `:focus-visible` control-state rule group from
  `kayakgen/ui/web/app.py`. Slice 2 still consumes layout, density, spacing,
  radius, border, elevation, state-surface, and typography tokens, but no longer
  applies focus-ring behavior to toolbar/status/Generate controls.
- M2: extended `tests/test_web_layout.py` with positive assertions for the
  status-bar hook contract and the Generate pick/action render hooks:
  `workspace-status-bar`, generated `status-{package|readiness|resistance|cfd}`
  names, status render-site templates, `kg-generate-pick`, and
  `kg-generate-pick-action`.

## Boundary Checks

- Claim/readiness/status copy and chip semantics were not changed.
- `docs/USER_GUIDE.md`, `docs/WEB_VERIFICATION.md`, and
  `docs/DECISION_LOG.md` were not touched.
- D047 remains proposed; no baseline or browser-acceptance procedure was
  ratified in this remediation.

## Verification

- `.venv/bin/python -m pytest tests/test_web_layout.py tests/test_web_inline_help.py -q`
  — 44 passed.
- `.venv/bin/python -m pytest tests/test_ui_theme.py -q` — 12 passed.
- `.venv/bin/python -m pytest tests/test_desktop_layout.py -q` — 4 passed.
- `git diff --check` — clean.
- `.venv/bin/python -m pytest -q` — 1302 passed, 4 skipped, 1 failed.

The full-suite failure is the known ledger S2 successor item:
`tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
detects `kayakgen/services/evaluation.py` importing
`kayakgen.ui.hydrostatics_metadata`. That path is outside this remediation's
write scope and was not changed.
