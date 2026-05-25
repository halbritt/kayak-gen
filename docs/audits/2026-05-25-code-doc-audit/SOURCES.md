# Sources for audit run — 2026-05-25

## Preset

`release_candidate` — the upstream second-pass web UI rework
(`b82b544 Land WEB_UI_REWORK_2026-05-22 second-pass redesign`) landed
after the 2026-05-23 release-candidate audit closed, so it has not yet
been audited. This run is the release-candidate sanity pass on that
single commit before any external operator relies on the new tab
structure / chip-style validity badge / kind-aware submit copy.

## Run scope

The single upstream commit between the previous release_candidate audit
and the current HEAD:

```
b82b544 Land WEB_UI_REWORK_2026-05-22 second-pass redesign
```

Range: `fcb8040..b82b544` (excludes the prior audit's own landing in
`fcb8040` and the subsequent audit-closure workflows in `2d14cff`).

Files touched (6, +600/-135):

```
kayakgen/services/evaluation.py            +54   (new helpers)
kayakgen/ui/web/app.py                     +310/-138
kayakgen/ui/web/controllers.py             +4
kayakgen/ui/web/generate_frontier_view.py  +12
kayakgen/ui/web/generate_spec_form.py      +130/-138
tests/test_web_layout.py                   +225  (11 new §9.3 checks)
```

The commit message asserts: *"Presentation-only rework per the 2026-05-22
brief. No backend capability added; build_spec_from_form_state wire output
unchanged."* This audit's adversarial question is: does the diff hold up
that claim?

This is the third `code_doc_audit` run. Prior runs:

- `docs/audits/2026-05-22-code-doc-audit/` — `full_repo` dogfood; 13
  findings, all closed.
- `docs/audits/2026-05-23-code-doc-audit/` — `release_candidate` on the
  RFC 0059/0060/0061 set; 0 critical · 0 high · 2 medium · 5 low · 1 info;
  all actionable findings closed by workflows 0035 + 0036.

## Lane inputs

| Lane | Inputs |
|---|---|
| pipeline-integrity | The two new helpers in `kayakgen/services/evaluation.py` (`hydro_rows_from_state`, `mesh_diagnostics_rows_from_state`) — verify they admit no stronger claim than the underlying state. The mesh readiness chip change (the "unavailable" contradiction fix) — verify the new copy and `status_readiness` wiring still respects mesh-evidence and CFD-in-loop acceptance contracts (RFC 0046/0058). The `FORBIDDEN_METRIC_TOKENS → plain literals with # noqa: kg-orphan-color` change in `generate_frontier_view.py` — verify the orphan-color check still has coverage (or document the deliberate suppression). `build_spec_from_form_state` wire-output stability claim — verify against `tests/test_web_layout.py` and the pre-existing form-state tests. |
| docs-decision-drift | `RELEASE_DISCIPLINE.md` checklist applied to b82b544. Does any central doc need an update for the UI rework? `CHANGELOG.md` — has the rework been recorded under `## Changed`? `USER_GUIDE.md` — do the documented Generate-panel / Comparison-tab / Mesh-tab surface descriptions still match? `ARCHITECTURE_MAP.md` — its date is 2026-05-22; should it be bumped if the UI surfaces are now meaningfully different? `ROADMAP.md` — is there a track row for the rework, or is it folded into the existing "Web Generate-panel form labels" row? `UBIQUITOUS_LANGUAGE.md` — do new presentation concepts (validity badge, comparison source toggle, kind-aware submit) need glossary entries? `docs/WEB_VERIFICATION.md` — does it still describe the Trame workspace accurately? The `prompts/web_ui_second_pass_rework_2026-05-22.md` brief vs the landed implementation. |
| operator-adoption | Run `kayakgen serve` against HEAD and exercise the rework surfaces: param-rail class chip + validity badge (`data-testid="validity-badge"`); Hydro tab key/value table replacement of `<pre>`; Hydro high-angle GZ tonal warning; Mesh tab key/value diagnostics; Mesh readiness chip showing "No package built"; Comparison tab `ComparisonSourceToggle` (live_frontier / imported_report); Generate tab kind-aware submit (`data-testid="generative-submit"`); variable rows VDataTable; objective rows refusal VAlert; advisory banner v_show; jobs index VDataTable; two-column form layout; the renamed "Raw JSON (advanced)". Verify each surface is discoverable from `--help` / docs / hover-tooltips alone, that the disabled-copy on the submit button explains *why* it's disabled, and that the `data-testid` hooks are documented or at least consistent. Cross-reference against `prompts/web_ui_second_pass_rework_2026-05-22.md`. |

## RFCs in scope

- RFC 0060 (web Generate-panel form labels and tooltips; `landed`) — the
  rework continues to consume `HullParameterMetadata` via the existing
  registry path. Verify nothing in the redesign bypasses or duplicates
  the registry.
- RFC 0061 (desktop sliders on `HullParameterMetadata`; `landed`) — not
  directly touched by the rework but listed here because it shares the
  same presentation-layer registry pattern; verify cross-surface
  consistency is preserved.

## Decision rows in scope

- D043 (`HullParameterMetadata` presentation-layer pattern) — the rework
  must continue to honor this; new presentation copy should sit in the
  registry where possible rather than being hard-coded in the form.

## Adversary framing per lane

- pipeline-integrity → look for *claim-state drift* in the new
  evaluation helpers (`hydro_rows_from_state`,
  `mesh_diagnostics_rows_from_state`) and the mesh readiness chip copy.
  Does the rework promote any result label past its evidence? Does the
  `# noqa: kg-orphan-color` suppression hide a real coverage gap?
- docs-decision-drift → look for *honest-prose drift*: did the central
  docs (CHANGELOG, USER_GUIDE, ARCHITECTURE_MAP, ROADMAP) keep up with
  the rework, or do they still describe the pre-rework surfaces?
- operator-adoption → look for *invisible-mechanism drift*: a useful
  control surface that exists in the new layout but is undiscoverable
  from docs / `--help` / hover-tooltips. Pay special attention to the
  kind-aware submit, the comparison-source toggle, and the validity
  badge — these are new vocabulary the operator has to learn.

## Where the audit run artifacts will land

`docs/audits/2026-05-25-code-doc-audit/`:

```
pipeline-integrity/FINDINGS.md
docs-decision-drift/FINDINGS.md
operator-adoption/FINDINGS.md
SYNTHESIS.md
REMEDIATION_PLAN.md
```
