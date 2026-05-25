# Sources for workflow 0039 — Hydro tab description rendering

> Operator: this file is the per-run context manifest. Each job
> reads it as required context. Keep entries short and link to the
> canonical source rather than duplicating it.

## Audit batch in scope

- [`docs/audits/2026-05-25-full-repo-code-doc-audit/REMEDIATION_PLAN.md`](../../audits/2026-05-25-full-repo-code-doc-audit/REMEDIATION_PLAN.md)
  batch R2 closes:

  | ID | Severity | Theme |
  |---|---|---|
  | AUD-O-003 | medium | RFC 0062 descriptions registered but not rendered |

  The finding lives at
  [`docs/audits/2026-05-25-full-repo-code-doc-audit/operator-adoption/FINDINGS.md`](../../audits/2026-05-25-full-repo-code-doc-audit/operator-adoption/FINDINGS.md).

## Antecedent RFC + decision row

- [`docs/rfcs/0062-hydrostatics-row-metadata-registry.md`](../../rfcs/0062-hydrostatics-row-metadata-registry.md)
  — landed the `HydrostaticsRowMetadata` value object + registry
  with 7 rows, each carrying a `description` field. The registry
  is presentation-only; the form's submitted JSON payload remains
  byte-stable.
- D044 in
  [`docs/DECISION_LOG.md`](../../DECISION_LOG.md) records the
  presentation-layer registry pattern for hydrostatics rows
  (mirroring D043 for hull parameters).

## The gap this workflow closes

`HYDROSTATICS_ROW_METADATA` ships seven row descriptions:

```
displacement     — "Displaced mass at the design waterline. Equals the kayak's weight…"
wetted_surface   — "Hull surface area below the waterline. Drives viscous resistance…"
waterplane_area  — "Cross-section area at the waterline. Influences pitch and heave…"
gm0              — "Initial metacentric height. Larger values mean stiffer initial…"
cp_actual        — "Prismatic coefficient computed from the current hull geometry…"
cm_actual        — "Midship coefficient computed from the current hull geometry…"
l_over_bwl       — "Length-to-beam ratio at the waterline. Used by the class-envelope…"
```

`analysis_view_model::hydro_rows` consumes the registry's `label`
and `unit` fields, and `hydro_rows_from_state` passes those
through to the web Hydro tab as `{label, value}` dicts. The
template renders only `{{ row.label }}` and `{{ row.value }}` —
the `description` field is unread.

## Source files modified by this workflow

| Path | Why |
|---|---|
| `kayakgen/services/evaluation.py` | Widen `hydro_rows_from_state` to include a `"description"` key in each emitted dict (sourced from `HYDROSTATICS_ROW_METADATA[key].description`; empty string for Warning rows). |
| `kayakgen/ui/web/app.py` | Wrap the Hydro-tab table row in a `v-tooltip` slot bound to `{{ row.description }}`, suppressed when the description is empty. |
| `tests/test_hydrostatics_row_metadata.py` | Update the byte-stable regression to include the new `description` key; this is an intentional widening, not a relaxation. The pre-rendering wire-payload assertion remains on `label` + `value` shape. |
| `tests/test_hydro_tab_descriptions.py` (new) | Render-verification test asserting each registered row's description appears in the rendered HTML (as `title=` attribute or v-tooltip slot text). |

## Source files NOT touched

The workflow's `forbidden_paths` encodes the read-only contract:

- `CHANGELOG.md`, `docs/USER_GUIDE.md`, `docs/DECISION_LOG.md`,
  `docs/SPEC.md`, `docs/PRD.md`, `docs/ROADMAP.md`,
  `docs/ARCHITECTURE_MAP.md`, `docs/UBIQUITOUS_LANGUAGE.md`,
  `docs/WEB_VERIFICATION.md`, `docs/audits/README.md`, all audit
  SYNTHESIS / REMEDIATION_PLAN / FINDINGS files — parent agent.
- `docs/rfcs/` — no new RFC; the existing RFC 0062 covers this.
- `kayakgen/ui/hydrostatics_metadata.py` — read-only registry.
- `kayakgen/ui/parameter_metadata.py` — read-only sibling.
- `kayakgen/ui/web/generate_spec_form.py`,
  `kayakgen/ui/web/generate_frontier_view.py`,
  `kayakgen/ui/web/controllers.py` — out of scope.
- `kayakgen/ui/desktop.py`, `kayakgen/ui/desktop_slider_ranges.py`,
  `kayakgen/ui/gui_params.py` — desktop has no Hydro-tab analog;
  unaffected.

## Test introspection pattern

`tests/test_web_inline_help.py` and `tests/test_web_layout.py`
provide the canonical pattern for asserting on rendered Trame
layout: scan the serialised HTML (via `app._html`) for
`data-testid` or content markers and assert their presence.

## Wire-payload stability

`build_spec_from_form_state(state)` is NOT touched by this
workflow. The change is in the read-model surface
(`hydro_rows_from_state`), not the spec submission. The byte-
stable regression in `tests/test_hydrostatics_row_metadata.py`
is widened to include the new `description` key — this is an
intentional schema widening recorded in the test fixture, not a
relaxation of the existing label/value pinning.

## Where the artifacts land

`docs/audits/2026-05-25-full-repo-code-doc-audit/follow-ups/0039/`:

```
PATCH_SUMMARY.md   # written by `implement`
REVIEW.md          # written by `review`
```
