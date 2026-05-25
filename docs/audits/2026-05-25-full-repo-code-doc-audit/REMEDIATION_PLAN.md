# Remediation Plan — 2026-05-25 full_repo code+doc audit

Date: 2026-05-25
Audit: `docs/audits/2026-05-25-full-repo-code-doc-audit/`
Scope: whole repository at HEAD `313dfdd`.

Findings rolled up in [`SYNTHESIS.md`](SYNTHESIS.md): 0 critical ·
0 high · 1 medium · 3 low · 27 info, with 3 lane-hallucinated
findings discarded after parent-thread verification.

Every actionable finding is assigned one of the seven follow-up
classifications from RFC 0059 §4.

## R1 — Docs-only catch-up batch (in-place in audit commit)

**Findings closed**: AUD-D-001 (low), AUD-D-004 (low), and the
docs-fix side of AUD-O-003 (medium).

**Classification**: docs-only correction (RFC 0059 §4 row 4).

**Touched files**:

- `docs/ROADMAP.md` — bump header from `Updated: 2026-05-21` to
  `Updated: 2026-05-25` (AUD-D-001). Optionally re-walk the track
  rows to confirm the 2026-05-22 → 2026-05-25 batch of landings
  is reflected; from spot-check the existing rows for RFC 0059 /
  0060 / 0061 already describe the landings, so only the date
  needs updating.
- `docs/WEB_VERIFICATION.md` — add a sentence in the existing
  `data-testid Hook Contract` section pointing at the test file:
  e.g., `Tests in tests/test_web_layout.py and
  tests/test_web_inline_help.py pin the presence and placement
  of these hooks.` (AUD-D-004).
- `docs/USER_GUIDE.md` — add a single sentence in the Hydro tab
  description noting that per-row descriptions live in the RFC
  0062 registry but are not yet rendered in the workspace; point
  the operator at `kayakgen/ui/hydrostatics_metadata.py` until R2
  lands the tooltip surface (covers half of AUD-O-003).

**Why in-place**: pure docs edits; matches the precedent from R1
batches on the 2026-05-22 dogfood, 2026-05-23 release_candidate,
and 2026-05-25 release_candidate audits. No code surface change,
no test run, no striatum requirement.

**Verification**: visual inspection; no test changes.

## R2 — Hydro-tab description rendering (follow-up striatum workflow)

**Findings closed**: AUD-O-003 (medium).

**Classification**: source/test work (RFC 0059 §4 row 5).

**Touched files**:

- `kayakgen/services/evaluation.py::hydro_rows_from_state` —
  extend the returned `[{"label", "value"}]` dict to include a
  `"description"` key sourced from
  `HYDROSTATICS_ROW_METADATA[key].description`. The change is
  additive: existing consumers that read only `label` + `value`
  keep working; the new `description` key is available to the
  web template.
- `kayakgen/services/evaluation.py::analysis_view_model` — the
  `hydro_rows` tuple already passes `(label, value, unit)`. Decide
  whether to widen it to 4-tuple (with description) or keep the
  3-tuple shape and have `hydro_rows_from_state` look up the
  description independently. The 4-tuple approach is more
  consistent; the keep-3-tuple approach minimizes diff. Default
  to the keep-3-tuple approach — `hydro_rows_from_state` already
  imports `_HYDRO_META` indirectly via the analysis output; it can
  re-key against the registry by inverse-lookup on the label, or
  the function refactor to thread the row id alongside.
- `kayakgen/ui/web/app.py` — wrap the Hydro tab `<th>` or `<td>`
  in a `v-tooltip` so hovering the row reveals the
  description. Bind to `{{ row.description }}`. Bind only when
  the description is non-empty; the `"Warning"` rows currently
  appended by `hydro_rows_from_state` have no registry entry and
  should render without a tooltip.
- `tests/test_web_inline_help.py` (or a new
  `tests/test_hydro_tab_descriptions.py`) — assert each
  registered hydrostatics row's description appears in the
  rendered HTML (as a `title=` attribute on the row, or in a
  Vuetify tooltip slot).

**Wire-payload stability**: `build_spec_from_form_state` is not
touched; the change is in the *read-model* surface, not the spec
submission surface. The byte-stable `hydro_rows_from_state`
regression test from workflow 0038 will need updating to include
the new `description` key (intentional widening, not a regression).

**Workflow id candidate**: `0039-hydro-tab-description-rendering`.

**Defer rationale**: not urgent, but completes RFC 0062's
operator-facing intent. The registry's descriptions exist *because*
the RFC said the operator should be able to discover them; without
a render surface, they're effectively dead code.

## R3 — Wontfix / closed-as-invalid

**Findings classification**:

- **AUD-D-002**: invalid (hallucination). Mark as `closed —
  invalid` in next audit's baseline.
- **AUD-D-003**: info wontfix per Lane 2's own follow_up
  assignment.
- **AUD-O-011**: invalid (hallucination — USER_GUIDE.md:209-210
  already covers the stage-4 gate). Mark as `closed — invalid`.
- **AUD-O-012**: documented limitation per Lane 3's own
  follow_up assignment; wontfix.
- **AUD-O-015**: invalid (hallucination — workflow 0037 already
  landed threshold-guidance labels). Mark as `closed — invalid`.

No action needed; recorded so the next audit does not refind them.

## R4 — Null findings (no action, baseline)

**Findings recorded as positive baseline**:

- AUD-P-001..AUD-P-012 (12 info, all `closed`) — pipeline-
  integrity invariants verified.
- AUD-D-005..AUD-D-010 (6 info) — docs-honest baselines.
- AUD-O-001..AUD-O-002 (2 info), AUD-O-004..AUD-O-010 (7 info),
  AUD-O-013..AUD-O-014 (2 info) — operator-adoption baselines.

**Disposition**: leave statuses per each lane's own assignment.
The next audit can read these as the regression-protection set.

## Batch landing order

1. **R1** landed in audit commit `456cdad`. Audit index-table row
   added for the full_repo run.
2. **R3** closed inline via SYNTHESIS strikethroughs.
3. **R2** landed as workflow
   `docs/workflows/0039-hydro-tab-description-rendering/`. Closes
   AUD-O-003. PATCH_SUMMARY at
   `docs/audits/2026-05-25-full-repo-code-doc-audit/follow-ups/0039/PATCH_SUMMARY.md`.

## CHANGELOG entries

After R1 lands:

- `Added` — Fourth `code_doc_audit` run under
  `docs/audits/2026-05-25-full-repo-code-doc-audit/` (`full_repo`
  preset, whole repo at HEAD `313dfdd`); 31 findings (0
  critical / 0 high / 1 medium / 3 low / 27 info) plus 3
  hallucinated findings discarded after parent-thread
  verification. Lane 1 returned 12 positive null findings
  verifying claim-gate invariants. R1 docs-only batch lands in
  this commit closing AUD-D-001 (low, ROADMAP date) +
  AUD-D-004 (low, WEB_VERIFICATION test cite) and partially
  closing AUD-O-003 (medium, RFC 0062 descriptions). R2 (Hydro-
  tab description rendering for AUD-O-003) deferred to follow-up
  striatum workflow `0039-hydro-tab-description-rendering`.
  Documents the precedent that lane findings are verified by
  the parent thread before landing.

After R2 lands (in that workflow's own commit):

- `Changed` — Hydro tab now renders each row's RFC 0062 registry
  description as a hover tooltip. Closes AUD-O-003.
