---
schema_version: striatum.finding.v1
artifact_kind: finding
verdict_intent: accept
---

author: final-reviewer-claude-opus-4.8-001

# Workflow 0059 Final Review — RFC 0065 Slice 2 (Shell Layout & Information Hierarchy)

**Verdict:** `accept` (with one documented, pre-existing, out-of-scope test
carve-out — see §4 and the Operator Action below).

Slice 2 is a presentation-only re-flow of the Trame workspace shell onto the
Slice 1 token vocabulary and the existing `TYPOGRAPHY` roles. Every Slice 2
gate (D1–D8) is met, both must-fix ledger items (M1, M2) are closed, the
focused suites and the orphan lint are green, and the claim line / RFC 0032
boundary / docs footprint are intact. The only red test in the full repo suite
is a pre-existing services-layer import-boundary defect that this slice neither
introduced, touched, nor is scoped to fix (logged as successor item S2).

I re-verified independently against the working tree on
`striatum/0059-rfc-0065-slice2-shell-layout` (diffed against `main`); I did not
rely solely on the upstream summaries.

## 1. Decision fidelity (D1–D8)

| Decision | Verdict | Independently confirmed evidence |
| --- | --- | --- |
| **D1 — token-only styling, no new orphan literals** | ✓ | The only `theme.py` edit is one additive line, `DENSITY["collapse-breakpoint"] = "960px"` (`theme.py:192`); no existing token renamed/removed/re-typed. It is non-colour (no `CONTRAST_MANIFEST`/dual-palette obligation) and the lint is extended (`test_ui_theme.py:175`). The `960px` reaches the media query only via runtime `... % theme.DENSITY["collapse-breakpoint"]` (`app.py:479`), so the AST orphan lint sees `%s`, not a literal. `test_no_orphan_visual_literals_under_kayakgen_ui` passes. A diff scan for added raw colour/`#hex`/`px` literals (excluding `var(...)`/`%s`) returns none. |
| **D2 — one typographic hierarchy** | ✓ | All six roles (`type-display/-heading/-label/-body/-caption/-metric`) appear in `WORKSPACE_SHELL_CSS` and are applied across rail, geometry/metrics, review cards/tables, toolbar, status bar, and Generate build/watch/pick. Enforced positively by `test_shell_and_generate_sections_share_typography_and_token_density` (passing), which asserts each `var(--type-*)` role and the shared section selectors are present. |
| **D3 — region + status-bar contract preserved** | ✓ | `LAYOUT_TEST_IDS` still `region-params/-geometry/-review` (`app.py:229-231`); `workspace-status-bar` testid present (`app.py:2289`); the four `status-{package\|readiness\|resistance\|cfd}` segments preserved and asserted (`test_web_layout.py:213-217`). Identity and routing untouched by the diff. |
| **D4 — first-viewport + ≤960 px collapse** | ✓ | All four collapse hooks (`kg-collapse-under-960`, `kg-geometry-accordion-under-960`, `kg-review-body-under-960`, `kg-status-wrap-under-960`) survive in `REGION_CLASSES`/`RESPONSIVE_CLASS_HOOKS` and are **restyled** (radius/margin/wrap), not removed, inside the single `@media (max-width: 960px)` block (`app.py:467-478`). No new breakpoint, no new mobile-editing affordance — posture stays conservative. |
| **D5 — hook discipline (renames reflected same slice)** | ✓ | No D3/D4 hook renamed/removed. New layout hooks each carry a positive render-site assertion: `kg-generate-build`/`-watch` (`test_web_layout.py:185-186`), `kg-generate-pick` element-binding (`test_web_layout.py:803` — closes traceability F3), `kg-generate-pick-action` element-binding (`test_web_layout.py:806` — closes F2). No orphaned assertion points at a removed hook. |
| **D6 — claim line byte-stable** | ✓ | Diff scan of `kayakgen/ui/` finds no `CHIP_SPECS`/`CHIP_LABELS`/`CHIP_CLASSES` or persistent-caption constant on any changed line; no `kg-chip--*` semantic class altered; no chip recoloured into the success palette (chip selectors receive only `border-radius` + `font: var(--type-caption)`). Corroborated by the claims review. |
| **D7 — RFC 0032 boundary intact** | ✓ | Added-line scan finds no new `.route(`/`add_url_rule`, and no new `claim_state`/`Readiness(`/`accepted_uses` literal. `controllers.py` is untouched. |
| **D8 — docs footprint is CHANGELOG only** | ✓ | `git diff main` for `docs/USER_GUIDE.md`, `docs/WEB_VERIFICATION.md`, `docs/DECISION_LOG.md` is empty. `CHANGELOG.md` carries the Slice 2 entry; `OPERATOR_REPORT.md` (this workflow) updated. DECISION_LOG row **D047** is still `proposed` (`DECISION_LOG.md:79`) — not ratified here. |

## 2. Must-fix ledger items — both closed

- **M1 (remove premature Slice 3 `:focus-visible` control-state CSS)** — closed.
  `git grep "focus-visible" kayakgen/ui/web/app.py` returns nothing. A
  regression guard was added: `test_slice2_defers_control_focus_state_application_to_slice3`
  asserts `:focus-visible` and `outline: var(--state-focus-ring-width)` are
  absent from `WORKSPACE_SHELL_CSS`. The successor pass (S1) to reintroduce
  uniform focus styling in Slice 3 is recorded.
- **M2 (positive D3/D5 assertions for status-bar + Generate hooks)** — closed.
  `test_web_layout.py` now asserts `workspace-status-bar`, all four generated
  `status-*` segment names, the `status-{label}`/`kg-status-segment` render-site
  templates, and both Generate pick hooks with element bindings.

## 3. Boundary & no-claims checks

- Claim line preserved (D6) — independently scanned; chip semantics and all
  persistent captions (resistance raw-comparative + uncalibrated, high-angle GZ,
  CFD local-jobs + raw-artifact, not-watertight-`cfd_ready`) are byte-stable.
- RFC 0032 web-analysis boundary intact (D7); RFC 0033 §8 no-go list stays
  absent (claims review + diff scan).
- `docs/USER_GUIDE.md` / `docs/WEB_VERIFICATION.md` untouched; D047 not ratified
  (D8).

## 4. Validation evidence (re-run locally)

- Focused suite: `.venv/bin/python -m pytest tests/test_web_layout.py
  tests/test_web_inline_help.py tests/test_ui_theme.py tests/test_desktop_layout.py -q`
  → **60 passed** (includes the widened orphan lint and the desktop rendered-bbox
  tests).
- Full repo suite: `.venv/bin/python -m pytest -q` →
  **1302 passed, 4 skipped, 1 failed** in 468s. The 4 skips are the env-gated
  OpenFOAM smoke tests (`KAYAKGEN_OPENFOAM_SMOKE`), i.e. the env-gated smoke the
  gate excludes by design.
- `git diff --check` — clean (verified upstream; no whitespace/conflict markers
  in the diff).

### The single failing test — pre-existing, out-of-scope, tracked as S2

`tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
fails because `kayakgen/services/evaluation.py:33` imports
`HYDROSTATICS_ROW_METADATA` from `kayakgen.ui.hydrostatics_metadata`. I verified:

- `kayakgen/services/evaluation.py` is **unchanged** in this branch
  (`git diff main -- kayakgen/services/evaluation.py` is empty).
- The offending import was introduced by earlier landings (workflows 0037–0039,
  commits `b82b544`/`313dfdd`/`e182c35`), **before** this branch existed — it is
  a genuinely pre-existing defect, not a Slice 2 regression.
- The file sits **outside every write scope** in this workflow (neither the
  implementer nor the remediator scope includes `kayakgen/services/`), and a fix
  (relocating the metadata registry to a lower-level package) is design scope
  that would violate D7's presentation-only boundary and the Slice 2 source list.

This is logged as non-blocking successor item **S2** in the findings ledger,
which explicitly anticipated this verdict point.

## 5. Verdict rationale

Every Slice 2 acceptance gate holds: D1–D8 are faithfully reflected in the
shipped change, M1/M2 are closed, the orphan lint + focused layout/inline-help +
desktop rendered-bbox tests are green, the region/status/collapse contract and
the 1440×900 first-viewport contract are preserved, the claim line and RFC 0032
boundary are intact, the docs footprint is CHANGELOG-only, and D047 is not
ratified. Slice 2 introduced **zero** test regressions.

The "full repo suite green" condition has exactly one exception, and it is
orthogonal to this slice: a pre-existing, out-of-scope services-layer import
violation that no Slice 2 change caused and no in-scope Slice 2 change can fix.
Returning `needs_revision` would be futile — the bounded one-round remediation
lane cannot touch `kayakgen/services/`, and forcing the fix would itself breach
the presentation-only D7 boundary. The correct disposition is to **accept** the
Slice 2 deliverable and route the orphan failure to its own hygiene workflow, as
the ledger recommends.

### Operator action (informational, not a Slice 2 revision)

Open the S2 follow-up hygiene/architecture workflow to relocate
`HYDROSTATICS_ROW_METADATA` out of `kayakgen.ui` into a lower-level shared
package so `test_services_boundaries.py` returns to green repo-wide. This is
tracked and is not blocking acceptance of Workflow 0059.
