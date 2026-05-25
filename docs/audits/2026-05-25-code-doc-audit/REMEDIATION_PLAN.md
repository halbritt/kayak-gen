# Remediation Plan — 2026-05-25 code+doc audit (release_candidate)

Date: 2026-05-25
Audit: `docs/audits/2026-05-25-code-doc-audit/`
Scope: single commit `b82b544` ("Land WEB_UI_REWORK_2026-05-22
second-pass redesign").

Findings rolled up in [`SYNTHESIS.md`](SYNTHESIS.md): 0 critical · 0
high · 5 medium · 9 low · 18 info.

Every finding is assigned one of the seven follow-up classifications
from RFC 0059 §4. Trivial bundles can land in-place; non-trivial source
changes go through striatum per `feedback_striatum_required`.

## R1 — Docs-only catch-up batch (in-place in audit commit)

**Findings closed**: AUD-D-001 (medium), AUD-D-002 (medium), AUD-D-004
(low), AUD-O-007 (info), AUD-O-008 (low), AUD-O-009 (info), AUD-O-010
(low), AUD-O-012 (low), AUD-O-013 (info), AUD-O-014 (low), AUD-O-015
(info). One umbrella docs-fix batch.

**Classification**: docs-only correction (RFC 0059 §4 row 4).

**Touched files**:

- `CHANGELOG.md` — add a `## Changed` block under `## Unreleased` for
  `b82b544`, naming each visible surface (tab restructure, validity
  badge, comparison-source toggle, kind-aware submit, Hydro/Mesh
  table rendering, "Raw JSON (advanced)" rename, CFD expansion title
  update).
- `docs/USER_GUIDE.md` — rewrite the `### serve` section (~lines
  869-939) to describe the post-rework layout. Cover:
  - two-column form layout + responsive behavior (AUD-O-014)
  - VDataTable variable rows (AUD-D-002)
  - kind-aware single Submit button + `data-testid="generative-submit"`
    convention (AUD-D-002)
  - Comparison tab as frontier home + `ComparisonSourceToggle`
    semantics (AUD-O-008)
  - jobs-table VDataTable columns (AUD-O-009)
  - "Raw JSON (advanced)" intent and when to use it (AUD-O-010)
  - CFD-in-loop slowness rationale and alternatives (AUD-O-012)
  - High-angle GZ alert: replace operator-facing RFC citations with
    plain recovery copy (AUD-O-007)
- `kayakgen/ui/web/generate_frontier_view.py` — module docstring or
  comment block explaining that the six `# noqa: kg-orphan-color`
  suppressions are correct because `FORBIDDEN_METRIC_TOKENS` contains
  RFC 0043 metric-name strings, not color literals (AUD-D-004).
- `docs/WEB_VERIFICATION.md` — short paragraph documenting that
  `data-testid` hooks are an internal test-only contract and may change
  without notice (AUD-O-015).
- `docs/ARCHITECTURE_MAP.md` — bump date to 2026-05-25 (AUD-D-008).

**Why in-place**: pure docs and one source-comment edit; matches the
2026-05-22 R1 and 2026-05-23 R1+R2 precedent. No code surface change,
no test runs, no striatum requirement. The
`kayakgen/ui/web/generate_frontier_view.py` edit is a comment-only
change which the `feedback_striatum_required` rule treats as a docs
edit, not a code change.

**Verification**: `pytest -k "vocabulary_coverage"` for glossary
side-effects; no other CI required.

## R2 — Inline-help / tooltip code batch (follow-up striatum workflow)

**Findings closed**: AUD-O-001 (medium), AUD-O-002 (medium), AUD-O-003
(low), AUD-O-004 (medium), AUD-O-006 (low), AUD-O-011 (info).

**Classification**: source/test work (RFC 0059 §4 row 5).

**Touched files**:

- `kayakgen/ui/web/app.py` — validity-badge title/popover, comparison-
  toggle subtitle, mesh-chip tooltip pair.
- `kayakgen/ui/web/generate_spec_form.py` — submit-button
  `disabled` + `aria-describedby` wiring; pre-validation reason
  surface for the disabled-state span.
- `kayakgen/services/evaluation.py` — `mesh_diagnostics_rows_from_state`
  label rewrite from raw dict keys (`boundary_edges`,
  `nonmanifold_edges`) to operator-facing labels with threshold
  guidance.
- `tests/test_web_layout.py` — new tests pinning the tooltip / disabled
  / submit-reason / mesh-label contracts.
- `docs/UBIQUITOUS_LANGUAGE.md` — only if any new term is introduced
  that warrants glossary placement (likely none, since these are
  presentation patterns — see R4).

**Why deferred to a follow-up workflow**: touches `kayakgen/ui/web/*`
source files; `feedback_striatum_required` applies. Estimated scope:
new workflow `0037-web-ui-inline-help-2026-05-25` or similar, with one
implementer lane and one reviewer lane (cross-provider). Validate the
workflow.json with `striatum workflow validate` before dispatch.

**Note**: AUD-O-005 (hydro labels not registry-sourced) is *not*
included in R2 — it's a larger structural pattern question, not a
one-shot copy fix, and lands in R3 below.

## R3 — Hydro labels registry follow-up (new RFC slice)

**Findings closed**: AUD-O-005 (low).

**Classification**: needs a new RFC (RFC 0059 §4 row 2).

**Touched files** (anticipated):

- New `docs/rfcs/0062-hydrostatics-row-metadata-registry.md` (or
  similar). Apply the D043 / RFC 0060 pattern to hydro row labels:
  define a `HydrostaticsRowMetadata` value object + registry (label,
  description, units, tolerance band where applicable).
- `kayakgen/services/evaluation.py` — `hydro_rows_from_state` consumes
  the new registry rather than hardcoding labels.
- `tests/test_hydrostatics_row_metadata.py` — registry coverage and
  label rendering.

**Why deferred to its own RFC**: this is a presentation-layer pattern
extension that mirrors RFC 0060's `HullParameterMetadata` and RFC
0061's desktop-slider migration. It belongs in its own RFC slice so
the registry contract is recorded once and any future sibling
registries (mesh diagnostics, evaluator status rows) can reuse the
pattern.

**Defer rationale**: not urgent (the current English labels are
correct, just not centralized), and the R2 inline-help batch should
land first so the next pass can see the full operator-facing surface
in one diff.

## R4 — Wontfix (close as accepted)

**Findings closed**: AUD-D-003 (low).

**Classification**: accepted risk / wontfix (RFC 0059 §4 row 7).

**Disposition**: `docs/UBIQUITOUS_LANGUAGE.md` is scoped to domain
concepts (claim_state, accepted_use, evaluators, etc.) and does not
glossarize pure UI patterns. Presentation vocabulary (validity badge,
chip, toggle, kind-aware submit) lives in `docs/USER_GUIDE.md`'s
`### serve` rewrite (R1) and in inline tooltips (R2). Close
AUD-D-003 with a one-line note in the audit's FINDINGS.md status
flip.

## R5 — Null findings (no action, baseline)

**Findings closed (by recording the positive state)**:

- AUD-P-001..AUD-P-007 — all seven pipeline-integrity null findings.
  "Presentation-only" claim verified under adversarial review.
- AUD-D-005..AUD-D-009 — central-docs items that did not drift.
- AUD-O-011 — sighted-user badge discovery is a product choice, not a
  bug; revisit if operator feedback flags it.
- AUD-O-016 — positive null finding on objective-refusal alert copy.

**Disposition**: leave status as `open` per the audit format convention
(null findings are not "closed" because there was no remediation to
close; they're "recorded as positive baseline"). The next audit can
re-use these to detect regression.

## Batch landing order

1. **R1** lands in the audit commit (this conversation). Tracks
   index-table update under `docs/audits/README.md`.
2. **R4** closes inline as a status note in the audit's CHANGELOG /
   FINDINGS entry; no separate workflow.
3. **R2** lands as a follow-up striatum workflow after the audit commit
   is on `main`. Workflow ID candidate: `0037-web-ui-inline-help-2026-05-25`.
4. **R3** lands as a new RFC + striatum workflow when the operator
   prioritizes it (no urgency).

## CHANGELOG entries

After R1 lands:

- `Changed` — Web UI second-pass redesign (b82b544): tab restructure,
  validity badge, comparison-source toggle, kind-aware submit,
  Hydro/Mesh key/value table rendering, "Raw JSON (advanced)" rename,
  CFD expansion title update.
- `Changed` — `docs/USER_GUIDE.md` `### serve` section rewritten to
  describe the post-rework Trame workspace.
- `Added` — `docs/audits/2026-05-25-code-doc-audit/`
  (release_candidate preset, scope `fcb8040..b82b544`); 32 findings
  total (0 critical · 0 high · 5 medium · 9 low · 18 info); five
  medium findings closed by R1 docs catch-up + R2 follow-up workflow.

After R2 lands (in that workflow's own commit):

- `Changed` — Web UI inline-help additions: validity-badge tooltip,
  comparison-toggle subtitle, mesh-chip tooltip, submit-button
  disabled-reason surface, mesh-diagnostics label rewrite. Closes
  AUD-O-001 / AUD-O-002 / AUD-O-003 / AUD-O-004 / AUD-O-006.
