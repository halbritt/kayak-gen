# RFC 0065 Slice 2 — Shell Layout & Information Hierarchy: Affirmed Decisions

These are the RFC-derived, operator-affirmed decisions that Slice 2 implements.
They are the authoritative spec for the implementer and the yardstick for every
reviewer. Source: `docs/rfcs/0065-ui-polish-redesign.md` §2 ("Information
hierarchy across the shell") and the "Slice 2 observable" Acceptance Criteria.

Slice 2 is a **presentation-only re-flow**. It restyles how the shell is laid out
and how its hierarchy reads; it changes no behaviour and no claim copy. It builds
on the Slice 1 token vocabulary (`SPACING` / `DENSITY` / `RADII` / `ELEVATION` /
`BORDERS` / focus-ring / state) and the existing `TYPOGRAPHY` roles. Each decision
below is a hard gate.

## D1 — Token-only styling (no new orphan literals)

Every spacing, padding, gap, radius, elevation, border, density, and colour value
in the re-flowed shell references a Slice 1 token (or an existing `theme.py`
token). The implementer adds **no new inline dimension / radius / elevation /
border / colour literal** anywhere under `kayakgen/ui/`; the widened
`tests/test_ui_theme.py` orphan-literal lint stays green. If a genuine token gap
appears, it is added **additively** to `kayakgen/ui/theme.py` per Slice 1 D1
(rename / remove / re-type no existing token), resolved in both palettes where
colour-bearing, covered by `CONTRAST_MANIFEST` where colour-bearing, and the lint
is extended to match. Adding tokens is the exception, not the default — prefer the
tokens Slice 1 already ships.

## D2 — One typographic hierarchy

Apply the existing `TYPOGRAPHY` roles — `type-display`, `type-heading`,
`type-label`, `type-body`, `type-caption`, `type-metric` — consistently across the
Parameters rail, the Geometry metrics strip + 2D accordion, the five Review tabs
(Hydro / Mesh / Comparison / CFD / Advisories), the toolbar, the status bar, and
the Generate panel's build / watch / pick modes. After the slice, heading weight
signals section importance the same way in every panel; a section title is a
`type-heading`, a field label is a `type-label`, a numeric readout is a
`type-metric`, etc. No panel keeps a bespoke heading weight / casing that
contradicts the shared scale.

## D3 — Region and status-bar contract preserved

The shell keeps the three region hooks `region-params`, `region-geometry`,
`region-review` (the `LAYOUT_TEST_IDS` values) and the four status-bar segments
`package`, `readiness`, `resistance`, `cfd` — `data-testid="workspace-status-bar"`
plus `data-testid="status-{package|readiness|resistance|cfd}"`, each still routing
to its target Review tab. Their geometry and density may be restyled; their
identity and routing may not be dropped.

## D4 — First-viewport + collapse contract (conservative mobile)

At 1440×900 the first viewport still shows the full Parameters rail, the 3D
viewport, the metrics strip, the first Review tab, and the status bar. Below
960 px the collapse behaviour is **retained and restyled, not removed**:
`kg-collapse-under-960` (rail → accordion), `kg-geometry-accordion-under-960`,
`kg-review-body-under-960` (Review becomes the body), and
`kg-status-wrap-under-960` all survive with their behaviour intact. Mobile posture
stays **conservative** per the locked operator decision: restyle the ≤960 px
collapse only; introduce no new mobile-editing affordance and no new responsive
breakpoint beyond the existing 960 px collapse.

## D5 — Hook discipline (every rename reflected in the same slice)

`data-testid` and `kg-*` class hooks are an internal test contract, not a public
API (per `docs/WEB_VERIFICATION.md` and RFC 0065 §6). Slice 2 MAY rename, move, or
remove any hook **except** the D3 region/status hooks and the D4 collapse hooks —
but **every** renamed / moved / removed hook MUST be reflected in
`tests/test_web_layout.py` in this same slice (and in `tests/test_web_inline_help.py`
when an inline-help hook moves), so no assertion is left pointing at a hook that no
longer exists and every new hook name has a positive assertion. A hook change that
is not reflected in the tests is a Slice 2 defect.

## D6 — Claim line is byte-stable (cross-cutting)

`CHIP_SPECS` / `CHIP_LABELS` / `CHIP_CLASSES` text and semantic class
(`kg-chip--raw` / `--info` / `--advisory` / `--success` / `--error`) are
byte-identical; no chip is recoloured into the success palette. Every persistent
caption is byte-identical after the reflow: the resistance "Raw comparative
filter; not final prediction." and uncalibrated caption; the high-angle GZ
"Unvalidated hydrostatic comparison; not safety, seaworthiness, calibrated,
validated, or final-prediction claim."; the CFD "Local filesystem CFD jobs on this
server only; no hosted worker is running." and "Raw solver artifact only; not
calibrated or validated."; the "not watertight cfd_ready" negation. The RFC 0033
§8 no-go list stays absent from rendered output, and the forbidden-copy scan stays
green. No re-flow may move an unvalidated/raw result into a position or treatment
that reads as a confident, validated, or calibrated claim.

## D7 — RFC 0032 boundary intact

No new REST route, no new `claim_state` / `Readiness` / `accepted_uses` literal, no
new evaluator or analysis surface. This is a presentation re-flow of the data the
shell already shows.

## D8 — Docs footprint is CHANGELOG only

Slice 2 updates `CHANGELOG.md` and this workflow's `OPERATOR_REPORT.md` only.
`docs/USER_GUIDE.md` and `docs/WEB_VERIFICATION.md` are **not** touched (Slice 4),
and DECISION_LOG row **D047** is **not** ratified here (Slice 4).

## Out of scope (later slices)

Control hover/focus/active/disabled states and explicit per-panel
empty/loading/error states (Slice 3); the Playwright/Chromium visual-regression +
a11y harness, the hard visual-regression gate, and the D047 baseline procedure
(Slice 4); desktop visual polish (Slice 5, deferred, operator-gated per
D009 / D021). Slice 2 produces a **reviewable visual diff** against the Slice 0
advisory baseline; the baseline narrow viewport may need regeneration on the
canonical env after the collapse reflow (kept advisory until Slice 4).
