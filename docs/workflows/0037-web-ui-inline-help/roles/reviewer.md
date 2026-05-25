# Role: reviewer

You verify the implementer's inline-help additions close audit batch
R2 (AUD-O-001/002/003/004/006 + the in-app copy side of AUD-O-007)
from the 2026-05-25 release_candidate audit.

You confirm:

- **AUD-O-001 (validity badge)** — `kayakgen/ui/web/app.py` adds a
  `title=` attribute (or `v-tooltip`) on the validity-badge chip
  that covers all four envelope states in plain text. The new test
  in `tests/test_web_inline_help.py` captures the rendered title
  string and asserts every documented state appears.

- **AUD-O-002 (comparison-source toggle)** — the `VBtnToggle` now
  carries a subtitle / hint / `v-tooltip` distinguishing
  `live_frontier` from `imported_report` in plain text. The test
  asserts the subtitle string is present and not internal jargon.

- **AUD-O-003 (mesh chip pair)** — the two chips now carry a
  shared `v-tooltip` (or per-chip tooltips) explaining that "No
  package built" is the package-state chip and the live readiness
  chip reports the hull/deck geometry readiness independently. The
  test verifies the tooltip text on both chips.

- **AUD-O-004 (submit button disabled reason)** — the kind-aware
  Submit button's `disabled` attribute is bound to a derived
  `submit_blocking_reason` (or equivalent) state field, an
  `aria-describedby` points at a visible span, and the visible span
  text changes per blocking cause ("Requires at least one variable",
  "Objectives not admissible", etc.). The test seeds two state
  configurations (valid / invalid) and asserts the disabled
  attribute and reason text both flip correctly.

- **AUD-O-006 (mesh-diagnostic labels)** —
  `mesh_diagnostics_rows_from_state` no longer emits raw dict-key
  labels (`boundary_edges`, `nonmanifold_edges`, etc.). The labels
  are operator-facing with embedded threshold guidance. The test
  enumerates the returned rows for a known fixture and asserts each
  label is human-readable English (no underscored snake_case in the
  presentation label).

- **AUD-O-007 (in-app copy)** — the high-angle GZ alert in
  `kayakgen/ui/web/app.py` no longer cites `RFC 0020` or `RFC 0024`
  in operator-facing copy. The new copy points at the actual
  recovery paths (CLI `kayakgen stability --high-angle-gz` and the
  Comparison-tab import). The test asserts the rendered alert
  string does not contain `RFC 0020` or `RFC 0024`.

- **Wire-payload stability.** The new test in
  `tests/test_web_inline_help.py` includes a regression assertion
  that constructs two states (valid + invalid) and asserts
  `build_spec_from_form_state(state)` returns the expected dict
  shape (keys + value types) unchanged from the b82b544 baseline.
  This is the audit's pipeline-integrity invariant (AUD-P-004).

- **Scope discipline.** The implementer touched ONLY
  `kayakgen/ui/web/app.py`,
  `kayakgen/ui/web/generate_spec_form.py`,
  `kayakgen/services/evaluation.py`,
  `tests/test_web_inline_help.py`, and files under
  `docs/audits/2026-05-25-code-doc-audit/follow-ups/0037/`. No
  diffs on `CHANGELOG.md`, `docs/USER_GUIDE.md`, `docs/DECISION_LOG.md`,
  audit SYNTHESIS / REMEDIATION_PLAN / FINDINGS files,
  `docs/rfcs/`, `docs/audits/README.md`,
  `kayakgen/ui/web/generate_frontier_view.py`,
  `kayakgen/ui/web/controllers.py`, or
  `kayakgen/ui/parameter_metadata.py`. **Specifically verify
  `hydro_rows_from_state` is unchanged** — that change belongs to
  workflow 0038.

- **Verification suite passes.** Run

  ```bash
  .venv/bin/pytest \
    tests/test_web_inline_help.py \
    tests/test_web_layout.py \
    tests/test_web.py \
    tests/test_ui_theme.py \
    tests/test_vocabulary_coverage.py \
    -q
  ```

  in the implementer's venv. All must pass.

You do not write code. You write a single `REVIEW.md` with a verdict
(accept | needs_revision) and per-criterion check results (pass /
fail with file:line evidence).
