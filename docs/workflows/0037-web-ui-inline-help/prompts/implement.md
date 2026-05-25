# Implement prompt — workflow 0037

You are closing audit batch R2 from the 2026-05-25 release_candidate
audit: five operator-facing inline-help gaps in the post-`b82b544`
web workspace, plus the in-app copy side of AUD-O-007 (high-angle GZ
alert).

Read first:

- `docs/audits/2026-05-25-code-doc-audit/REMEDIATION_PLAN.md` (batch R2)
- `docs/audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md`
  for the finding IDs in scope.
- `docs/audits/2026-05-25-code-doc-audit/SYNTHESIS.md` for cross-lane
  context.
- `docs/workflows/0037-web-ui-inline-help/SOURCES.md` for the per-run
  context manifest.
- `kayakgen/ui/web/app.py` end-to-end — pay attention to the
  validity-badge VChip (around `_refresh_validity_badge` / state field
  `validity_badge`), the ComparisonSourceToggle (search for
  `comparison_source`), the mesh chip pair (search for
  `mesh-no-package-chip` and `mesh-live-readiness-chip`), and the
  high-angle GZ alert (search for `HIGH_ANGLE_GZ_COPY` or the
  `RFC 0020` literal).
- `kayakgen/ui/web/generate_spec_form.py` end-to-end — pay attention
  to the kind-aware Submit button (search for `generative-submit`)
  and the existing validation surfaces (`refused_objectives`,
  `generative_form_state`, `_objectives_block`).
- `kayakgen/services/evaluation.py` — `mesh_diagnostics_rows_from_state`
  (around line 452) and the underlying `MeshDiagnostics` /
  `_mesh_diagnostics_counts` helpers (around line 572). **DO NOT
  TOUCH `hydro_rows_from_state` (around line 435) — that belongs to
  workflow 0038.**
- `tests/test_web_layout.py` — pattern for inspecting the rendered
  layout via the serialised HTML / data-testid hooks.

## Deliverables

### 1. `kayakgen/ui/web/app.py` edits

**(a) AUD-O-001 — validity badge tooltip.** The current VChip
renders `{{ validity_badge }}` text with role="status" and
aria-live="polite". Add a `title=` attribute (or v-tooltip wrapper
producing one) that carries plain-text explanations for all four
envelope states:

- `In <class> envelope`: "Hull dimensions fit the <class>
  surfski-class envelope. Advisory — does not certify seaworthiness
  or solver readiness."
- `Custom — sub-touring`: "Hull is below the touring class
  envelope. The class selector falls back to custom; advisory only."
- `Custom — beyond elite`: "Hull exceeds the elite-surfski class
  envelope. The class selector falls back to custom; advisory only."
- `Custom (L/B_wl=X.X)`: "Hull length-to-beam ratio is X.X; not
  matched by any standard class envelope. Custom design."

The simplest implementation is to add a `validity_badge_title` state
field computed by `_refresh_validity_badge` (already populates
`validity_badge_aria_label`) and bind the VChip `title` prop to it.
The state field stays in lock-step with the existing aria-label.

**(b) AUD-O-002 — comparison-source toggle subtitle.** Below the
VBtnToggle (or as a tooltip on each button), add a short subtitle
that distinguishes the two modes in plain text:

- "Live frontier: candidates from this session's jobs index."
- "Imported report: a saved design-report JSON loaded into the
  workspace for comparison."

If `v-tooltip` on the buttons is cleaner than an inline subtitle,
use that — but the operator must be able to discover the meaning
without clicking the toggle.

**(c) AUD-O-003 — mesh chip-pair tooltip.** The two chips
(`mesh-no-package-chip` and `mesh-live-readiness-chip`) need
tooltips clarifying:

- "No package built" chip: "No CFD mesh package has been generated
  for this hull yet."
- live readiness chip: "Live hull/deck readiness reported by the
  mesh diagnostic, independent of whether a mesh package exists."

Bind these via `v-tooltip` or `title=` so the operator sees them
on hover.

**(d) AUD-O-007 — high-angle GZ alert copy.** Find the constant
holding the alert copy (likely `HIGH_ANGLE_GZ_COPY` or similar) and
rewrite it to drop the `RFC 0020 / RFC 0024` citations in favour of
plain recovery copy:

> "High-angle GZ (stability at large heel angles) is not rendered
> in the workspace. Use `kayakgen stability --high-angle-gz` or
> load a design report on the Comparison tab to inspect this data."

The alert's `title="High-angle GZ unavailable"` can stay.

### 2. `kayakgen/ui/web/generate_spec_form.py` edits

**AUD-O-004 — submit-button disabled reason.** Wire a derived
`submit_blocking_reason` state field (or two: one for the disabled
boolean, one for the reason string). The field should be derived
inside the existing form-state refresh hook (search for places where
`generative_submit_disabled` or `refused_objectives` is computed —
if no such hook exists, add one alongside the existing form-state
refresh).

The reason string covers at least these blocking causes (extend with
any others surfaced by existing validation):

- No variables defined: "Requires at least one variable in the
  variables table."
- All objectives refused: "All selected objectives are not
  admissible for the current claim scope. Choose admissible
  objectives or relax the scope."
- No objective selected: "Select at least one objective."
- (Any other validation gate the existing code enforces.)

On the kind-aware VBtn:

- Add `:disabled="submit_disabled"` (binding the boolean field).
- Add `aria-describedby="submit-blocking-reason-{kind}"` (one for
  search, one for sweep).
- Add a visible `<span :id="submit-blocking-reason-{kind}">`
  rendering `{{ submit_blocking_reason }}` directly below the
  button, with `v-show="submit_disabled"` so it only appears when
  the button is disabled.

### 3. `kayakgen/services/evaluation.py` edits

**AUD-O-006 — mesh-diagnostic threshold guidance.** Note: the
existing labels in `mesh_diagnostics_rows_from_state` are already
English ("Boundary edges", "Non-manifold edges", "Degenerate faces",
"Vertices", etc.). Lane 3 cited the wrong line range and misread —
the actual labels are at lines 466-485 and they are not raw dict
keys. What is missing is **threshold guidance** explaining what
value the operator should expect for each diagnostic. Extend the
labels to embed threshold context (preserve the current dict shape;
only update the `label` strings):

| Existing label | Updated label |
|---|---|
| `Boundary edges` | `Boundary edges (perimeter; acceptable)` |
| `Non-manifold edges` | `Non-manifold edges (must be 0)` |
| `Degenerate faces` | `Degenerate faces (must be 0)` |
| `Readiness` | `Readiness level` |
| `Vertices` / `Welded vertices` | (unchanged; raw counts) |
| `Part` | (unchanged) |
| `Warning` | (unchanged) |

The change is additive English in the existing `label` slot. The
`{"label": ..., "value": ...}` row shape stays. If
`tests/test_web_layout.py` pins any of these label strings
verbatim, update the test in the same diff (this is a presentation
copy change, not a structural one). **DO NOT touch
`hydro_rows_from_state`** — it stays as the `b82b544`
implementation until workflow 0038 (R3) lands.

### 4. `tests/test_web_inline_help.py` (new)

Mirror the introspection pattern from `tests/test_web_layout.py`.
Use `pytest.importorskip("trame", reason="kayakgen[web] not installed")`
and `pytest.importorskip("vtk", ...)`. Add tests:

- **`test_validity_badge_title_covers_all_states`** — seeds
  `web.state.validity_badge` to each of the four documented values
  via `_refresh_validity_badge` and asserts the corresponding
  `validity_badge_title` is non-empty and contains an operator-
  facing explanation (not internal jargon).

- **`test_comparison_source_toggle_subtitle_present`** — asserts
  the rendered HTML for the comparison-source toggle includes the
  plain-text subtitle for both live_frontier and imported_report.

- **`test_mesh_chip_pair_tooltips_present`** — asserts both
  `mesh-no-package-chip` and `mesh-live-readiness-chip` carry a
  tooltip (`v-tooltip` template or `title=` attribute) with the
  expected explanation strings.

- **`test_submit_disabled_when_no_variables`** — seeds a state
  with empty variables; asserts `submit_disabled` is True,
  `submit_blocking_reason` is the variables-required string, and
  the rendered span text matches.

- **`test_submit_enabled_when_form_valid`** — seeds a complete
  valid state; asserts `submit_disabled` is False, the reason
  string is empty (or null), and the span has `v-show="false"`.

- **`test_mesh_diagnostics_rows_have_operator_facing_labels`** —
  calls `mesh_diagnostics_rows_from_state` on a known fixture and
  asserts no label contains an underscore (presentation labels
  must be English, not snake_case dict keys).

- **`test_high_angle_gz_alert_drops_rfc_citations`** — locates the
  high-angle GZ alert constant; asserts it does not contain
  `RFC 0020` or `RFC 0024`.

- **`test_build_spec_from_form_state_wire_payload_stable`** —
  constructs two states (valid + invalid) and asserts
  `build_spec_from_form_state(state)` returns the expected dict
  shape (top-level keys + value types) unchanged. This pins the
  audit's AUD-P-004 invariant across the R2 edits.

## Verification

Run in the project venv:

```bash
.venv/bin/pytest \
  tests/test_web_inline_help.py \
  tests/test_web_layout.py \
  tests/test_web.py \
  tests/test_ui_theme.py \
  tests/test_vocabulary_coverage.py \
  -q
```

All must pass.

## Scope discipline

You MUST NOT touch:

- `CHANGELOG.md`
- `docs/USER_GUIDE.md` (R1 already updated)
- `docs/DECISION_LOG.md`
- `docs/audits/2026-05-25-code-doc-audit/SYNTHESIS.md`,
  `REMEDIATION_PLAN.md`, any `FINDINGS.md`, `docs/audits/README.md`
- `docs/rfcs/` and `docs/rfcs/README.md`
- `kayakgen/ui/web/generate_frontier_view.py`
- `kayakgen/ui/web/controllers.py`
- `kayakgen/ui/parameter_metadata.py`
- `kayakgen/services/evaluation.py::hydro_rows_from_state` (this
  function lives in evaluation.py but the function body stays read-
  only for this workflow — that change is owned by workflow 0038).

The workflow's `forbidden_paths` encodes the path-level contract;
the `hydro_rows_from_state` carve-out is enforced by code review.

## Artifact

Write
`docs/audits/2026-05-25-code-doc-audit/follow-ups/0037/PATCH_SUMMARY.md`
with:

- Files changed (paths only).
- Test counts per file (from `pytest --collect-only -q`).
- One-line description of each new tooltip / disabled-reason
  surface and the file:line where it lands.
- Confirmation that `hydro_rows_from_state` is unchanged.
- Confirmation that `build_spec_from_form_state` wire output is
  byte-stable (cite the regression test).
- Confirmation that the verification suite passes.
