# RFC 0065 Slice 3 — Control + Empty/Loading/Error States: Affirmed Decisions

These are the RFC-derived, operator-affirmed decisions that Slice 3 implements.
They are the authoritative spec for the implementer and the yardstick for every
reviewer. Source: `docs/rfcs/0065-ui-polish-redesign.md` §3 ("Control states and
empty / loading / error states") and the "Slice 3 observable" Acceptance Criteria.

Slice 3 is a **presentation-only state pass**. It makes control interaction
states and per-panel empty/loading/error states uniform and explicit; it changes
no behaviour, no data, and no claim/availability copy. It builds on the Slice 1
tokens and the Slice 2 layout. Each decision below is a hard gate.

## D1 — Uniform control states from tokens

Every button, select, slider, toggle, and tab gets a uniform
default / hover / focus / active / disabled treatment sourced from the Slice 1
state and focus-ring tokens (`--state-hover-*`, `--state-active-*`,
`--state-disabled-*`, `--state-focus-ring`, `--state-focus-ring-width`). This
**reintroduces, uniformly, the control focus-ring / `:focus-visible` treatment
that was deliberately removed from Slice 2** (workflow 0059 ledger item S1, which
deferred control-interaction states to Slice 3) — now applied across all
controls, not a partial subset, as the authorised control-state pass.

## D2 — Honestly-disabled controls stay disabled and keep their copy

Disabling is a truthfulness affordance, not a style. The following stay disabled
and keep their explanatory copy **byte-identical**:

- the `watertight-solid` readiness profile option and its copy "Current generated
  packages do not satisfy watertight-solid readiness.";
- the disabled `EXPORT_MENU_ROWS` rows (keep `aria-disabled="true"` and their
  per-row copy);
- the Cm reserved-preset case;
- the `generative_submit_disabled` submit buttons and their blocking-reason copy
  (`submit-blocking-reason-search` / `-sweep`).

A restyle may change a disabled control's appearance; it may not enable it,
remove `aria-disabled`, or soften/drop its explanatory copy.

## D3 — Explicit, consistent empty/loading/error states with stable hooks

Each panel that waits on or can fail to load data renders an explicit, consistent
state with a **stable, tested `data-testid` hook**:

- **Generate jobs table** (`generative-jobs-table`): empty (no jobs), running
  (in-flight progress), failed (`GenerativeJobError.kind` surfaced), cancelled,
  resumable.
- **Pareto frontier scatter** (`frontier-view-section`): loading, empty (job not
  yet `succeeded`), rendered.
- **Comparison**: no-report vs report-present
  (`comparison-live-frontier-block` / `comparison-imported-report-block`).
- **Mesh**: `mesh-no-package-chip` vs `mesh-live-readiness-chip`.
- **CFD**: no-job vs status states, with **both persistent banners intact**.
- **Share-URL load** (`share-url-state`) and the invalid-hull-state banner
  (RFC 0033 §2).

These states are restyled for consistency; their **copy is unchanged**.

## D4 — Copy is byte-stable (cross-cutting claim line)

State messages, availability copy, and especially any claim copy are unchanged.
`CHIP_SPECS` / `CHIP_LABELS` / `CHIP_CLASSES` text and semantic class are
byte-identical; no chip (including a `failed`/empty-state chip) is recoloured into
the success palette. Every persistent caption is byte-identical: resistance "Raw
comparative filter; not final prediction." + uncalibrated caption; high-angle GZ
"Unvalidated hydrostatic comparison; not safety, seaworthiness, calibrated,
validated, or final-prediction claim."; CFD "Local filesystem CFD jobs on this
server only; no hosted worker is running." + "Raw solver artifact only; not
calibrated or validated."; the "not watertight cfd_ready" negation. No
empty/loading/error treatment may make an unvalidated/raw/failed result read as a
confident, validated, or successful claim.

## D5 — Hook discipline + token-only styling

`data-testid` / `kg-*` hooks may be renamed/moved/added, but **every** such change
MUST be reflected in `tests/test_web_layout.py` AND `tests/test_web_inline_help.py`
in this same slice, and every empty/loading/error hook in D3 has a positive
assertion. Styling is token-only: add no new inline dimension/radius/elevation/
border/colour literal; the widened `tests/test_ui_theme.py` orphan lint stays
green. If a genuine token gap appears, add it additively to `theme.py` per Slice 1
D1 (both palettes + `CONTRAST_MANIFEST` if colour-bearing; lint extended). Preserve
the Slice 2 layout contract: the `region-params`/`-geometry`/`-review` test-ids,
the four status segments, the 1440×900 first-viewport contract, and the ≤960 px
collapse hooks.

## D6 — Forbidden-copy scan extended to every new rendered string

The forbidden / no-go + caption regression scan in `tests/test_web_layout.py`
(`test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces` and
its neighbours) is **extended** so every NEW rendered string the slice introduces
— state messages, ARIA labels, tooltips — is covered. The RFC 0033 §8 no-go list
stays absent from rendered output and the scan stays green.

## D7 — RFC 0032 boundary intact

No new REST route, no new `claim_state` / `Readiness` / `accepted_uses` literal, no
new evaluator or analysis surface. The empty/loading/error states present the data
the panels already show; they add no analysis capability.

## D8 — Docs footprint is CHANGELOG only

Slice 3 updates `CHANGELOG.md` and this workflow's `OPERATOR_REPORT.md` only.
`docs/USER_GUIDE.md` and `docs/WEB_VERIFICATION.md` are **not** touched (Slice 4),
and DECISION_LOG row **D047** is **not** ratified here (Slice 4).

## Out of scope (later slices)

The Playwright/Chromium visual-regression hard gate, the focus-order /
visible-ring / hit-target / contrast a11y checks, the Lighthouse gate, the
`WEB_VERIFICATION.md` + `USER_GUIDE.md` updates, and the D047 ratification
(Slice 4); desktop visual polish (Slice 5, deferred, operator-gated per
D009 / D021). The pre-existing NB-2 `tests/test_services_boundaries.py`
services→ui import-boundary failure is **out of scope** (a separate hygiene
follow-up, per workflow 0059 ledger S2). Slice 3's loading-state styling produces
a reviewable visual diff against the Slice 0 advisory baseline; the baseline stays
advisory until Slice 4.
