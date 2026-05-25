# Sources for workflow 0037 — web UI inline-help additions

> Operator: this file is the per-run context manifest. Each job reads
> it as required context. Keep entries short and link to the canonical
> source rather than duplicating it.

## Audit batch in scope

- [`docs/audits/2026-05-25-code-doc-audit/REMEDIATION_PLAN.md`](../../audits/2026-05-25-code-doc-audit/REMEDIATION_PLAN.md)
  batch R2. Findings closed by this workflow:

  | ID | Severity | Theme |
  |---|---|---|
  | AUD-O-001 | medium | validity-badge meaning not self-evident |
  | AUD-O-002 | medium | comparison-toggle "Imported report" ambiguity |
  | AUD-O-003 | low | mesh chip-pair relationship not explained |
  | AUD-O-004 | medium | submit button disabled-reason missing |
  | AUD-O-006 | low | mesh-diagnostic labels are raw dict keys |
  | AUD-O-007 (in-app copy) | info | high-angle GZ alert cites RFCs |

  Findings live at
  [`docs/audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md`](../../audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md).

## Antecedent commit + audit context

- Upstream `b82b544` ("Land WEB_UI_REWORK_2026-05-22 second-pass
  redesign") added the validity-badge, comparison-source toggle,
  kind-aware Submit, mesh chip pair, and the two new helpers
  (`hydro_rows_from_state`, `mesh_diagnostics_rows_from_state`).
- The 2026-05-25 release_candidate audit identified the inline-help
  gaps. R1 (docs catch-up) landed in the audit commit; R2 is this
  workflow.

## Source files modified by this workflow

| Path | Why |
|---|---|
| `kayakgen/ui/web/app.py` | Validity-badge `title=` / popover, comparison-toggle subtitle, mesh chip-pair tooltip, high-angle GZ alert copy rewrite. |
| `kayakgen/ui/web/generate_spec_form.py` | Submit-button `disabled` + `aria-describedby` wiring + visible blocking-reason span. |
| `kayakgen/services/evaluation.py` | `mesh_diagnostics_rows_from_state` label rewrite from raw dict keys to operator-facing labels with threshold guidance. **`hydro_rows_from_state` is read-only in this workflow** — that change lives in R3 / workflow 0038. |
| `tests/test_web_inline_help.py` | NEW — render-verification tests for each of the new surfaces. Mirror the introspection pattern from `tests/test_web_layout.py`. |

## Source files NOT touched

The workflow's `forbidden_paths` encodes the read-only contract:

- `CHANGELOG.md` (parent agent)
- `docs/USER_GUIDE.md` (R1 already updated)
- `docs/DECISION_LOG.md`
- `docs/audits/2026-05-25-code-doc-audit/SYNTHESIS.md`,
  `REMEDIATION_PLAN.md`, and any `FINDINGS.md`
- `docs/rfcs/` and `docs/rfcs/README.md`
- `kayakgen/ui/web/generate_frontier_view.py`
- `kayakgen/ui/web/controllers.py`
- `kayakgen/ui/parameter_metadata.py`

## Test introspection pattern

`tests/test_web_layout.py` (added by `b82b544`) provides the canonical
pattern for asserting on the post-rework Trame layout: it scans the
serialised layout HTML (via `app._html`) for `data-testid` markers and
checks adjacent text / template directives. The new
`tests/test_web_inline_help.py` should use the same pattern (no
Playwright, no Trame round-trip) so the workflow's verification
profile stays inside the existing headless `tests/test_web*.py`
performance envelope.

For state-seeded values (e.g. the rendered submit-button label, the
disabled-reason span text), seed `web.state` via `initialize_form_state`
in a fixture and read the values back from `web.state` after a
controlled mutation.

## Wire-payload stability

The implementer MUST verify with a test that
`build_spec_from_form_state(state)` returns the same dict structure
after the inline-help additions land. The audit's pipeline-integrity
lane (AUD-P-004) verified this for `b82b544`; R2 must not break it.
Add a regression assertion in `tests/test_web_inline_help.py` that
constructs two states (one valid, one invalid) and asserts the
returned spec dict has the expected keys and types.

## Where the artifacts land

`docs/audits/2026-05-25-code-doc-audit/follow-ups/0037/`:

```
PATCH_SUMMARY.md   # written by `implement`
REVIEW.md          # written by `review`
```
