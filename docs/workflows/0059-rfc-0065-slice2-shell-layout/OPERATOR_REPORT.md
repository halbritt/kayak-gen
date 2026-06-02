# Operator Report — Workflow 0059 (RFC 0065 Slice 2: shell layout & information hierarchy)

**Status:** scaffolded, pending run.

## Scope

Slice 2 of RFC 0065: re-flow the three-region web shell (`region-params` /
`region-geometry` / `region-review`), the toolbar, the four status-bar segments
(package / readiness / resistance / cfd), and the Generate panel onto the Slice 1
theme tokens and one typographic hierarchy (the `TYPOGRAPHY` roles), with
consistent section rhythm and card/strip density — no behaviour change, no claim
change. Preserve the 1440×900 first-viewport contract and the ≤960 px collapse;
reflect every renamed/moved `data-testid` / `kg-*` hook in
`tests/test_web_layout.py` (+ `tests/test_web_inline_help.py`). See
`SLICE_2_DECISIONS.md` (D1–D8).

## Lanes

- Implement / ledger / remediate: `codex` (write lane).
- Reviews (traceability, claims, ops-tests) and final review: `claude` / `gemini`
  (reviews kept off the codex lane per the operator-hazard note that the codex
  reviewer lane can wedge a run with a terminal `reject`). Gemini reviews
  (`review_claims`, `review_ops_tests`) are dispatched **one at a time** to avoid
  the concurrency 429 → stale-lease requeue hazard.

## Outcome

Implemented and remediated. Slice 2 re-flowed the web workspace shell and
Generate build/watch/pick surfaces onto the Slice 1 visual tokens while
preserving the three-region hooks, status-bar identity, 960 px collapse hooks,
claim/readiness/status copy, and RFC 0032 web-analysis boundary.

Remediation closed both must-fix ledger items:

- M1: removed the premature Slice 3 `:focus-visible` control-state CSS from
  `kayakgen/ui/web/app.py`.
- M2: added positive `tests/test_web_layout.py` assertions for
  `workspace-status-bar`, the four generated `status-*` segment hook names, the
  status render-site templates, `kg-generate-pick`, and
  `kg-generate-pick-action`.

Focused verification completed:

- `.venv/bin/python -m pytest tests/test_web_layout.py tests/test_web_inline_help.py -q`
  — 44 passed.
- `.venv/bin/python -m pytest tests/test_ui_theme.py -q` — 12 passed.
- `.venv/bin/python -m pytest tests/test_desktop_layout.py -q` — 4 passed.
- `git diff --check` — clean.

Full-suite verification was run:

- `.venv/bin/python -m pytest -q` — 1302 passed, 4 skipped, 1 failed.

The failed test is the known successor item S2 from
`striatum/0059-rfc-0065-slice2-shell-layout/ledger/FINDINGS_LEDGER.md`:
`tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
reports `kayakgen/services/evaluation.py` importing
`kayakgen.ui.hydrostatics_metadata`. This remediation did not touch
`kayakgen/services/`; moving that metadata boundary is outside the Slice 2
presentation-only write scope.
