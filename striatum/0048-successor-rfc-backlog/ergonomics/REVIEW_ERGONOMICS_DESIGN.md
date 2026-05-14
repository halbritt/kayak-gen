---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

author: reviewer-ergonomics-design-claude-opus-4.7-002
kind: finding
logical_name: review
run: run_c1de081e76f14cd1a81194e306338ac2
session: sess_2c196f50ca354e31bb962df368ec2fe5
job: job_run_c1de081e76f14cd1a81194e306338ac2_review_ergonomics_design
lease: lease_0f5a7860ec1444ef8d00904cd92e50fd
date: 2026-05-14

# Review — Ergonomics & Design (Workflow 0048 UI Successor RFCs)

## Verdict

`accept_with_findings`

RFCs 0036-0039 each successor-track one of the four 0047 final-review findings
(FR1-FR4) and stay inside the RFC 0033/0034/0035 no-overclaim envelope. Every
RFC names a user-facing surface or visible acceptance step, every visible-copy
decision is anchored to the existing accepted vocabulary, and no RFC reopens
hosted CFD, real solvers, calibration, high-angle stability, watertight
readiness, or web-side mesh-package authoring. Findings below are non-blocking
ergonomic refinements; none change scope or require RFC rewrites.

## Source Material Reviewed

- `docs/workflows/0048-successor-rfc-backlog/SOURCES.md`
- `docs/rfcs/0033-workspace-ui-rework.md` (parameter rail, review tabs, export
  menu, status bar, RFC 0033 §8 no-go copy list)
- `docs/rfcs/0034-workspace-ui-follow-up.md` (preset reseed/narrow, resistance
  card, mesh tab, export-menu rows)
- `docs/rfcs/0035-ui-follow-up-cleanup.md` (validity classifier, preset edit
  model, dead-branch cleanup, export single-source, snapshot schema, slider
  CSS/accessibility, desktop fallback)
- `docs/rfcs/0036-trame-seed-listener-proof.md`
- `docs/rfcs/0037-export-row-schema-consolidation.md`
- `docs/rfcs/0038-export-menu-disabled-copy-polish.md`
- `docs/rfcs/0039-web-snapshot-schema-unification.md`
- `striatum/0048-successor-rfc-backlog/rfc_ui/RFC_SCOPE_UI.md`
- `striatum/0047-ui-follow-up-cleanup/final/FINAL_REVIEW.md`
- `striatum/0047-ui-follow-up-cleanup/ledger/FINDINGS.md`

## Per-RFC Ergonomics Assessment

### RFC 0036 — Trame Seed Listener Proof

User-facing surface: web class-preset rail interaction with Trame slider
events (retained `_state_matches_preset_seed` branch noted by 0047 FR1).

- **Observable behavior named.** The proposal restates the accepted preset
  contract verbatim (five-field reseed/narrow only; hull-shaping edits flip to
  `custom`; `target_speed_kt` is view state) and adds a real browser gesture:
  "select a class preset, drive a hull slider away from and then back to
  within the implementation tolerance of the preset seed, and assert that the
  preset remains non-custom only for the same-seed path." That is a user
  action, not a private-helper assertion.
- **Either-or outcome is symmetric on accepted vocabulary.** Both branches
  (retain with browser proof; remove as dead code) preserve the preset/badge
  strings and the RFC 0033 §8 forbidden-copy boundary.
- **Browser acceptance bar correctly excludes private-helper invocation.**
  Acceptance reads "without direct private-helper invocation," which closes
  the gap 0047 FR1 flagged at `tests/test_web_layout.py:374-388`.

### RFC 0037 — Export Row Schema Consolidation

User-facing surface: web export menu rendered from `EXPORT_MENU_ROWS`.

- **Visible copy frozen.** Subtitles must remain byte-identical to the
  shipped UI. Any read-model `description` consumer derives from the
  canonical `subtitle` at the read-model boundary, not as a second stored
  row-schema field. That removes the duplication 0047 FR2 flagged without
  changing any visible string.
- **Row availability preserved.** Enabled rows remain Hull STL, Deck STL,
  Hydro JSON. Stability JSON and Mesh package stay unavailable. No new
  enabled exports.
- **Drift gate present.** Static tests must fail on label, disabled-state,
  row-class, action-key, availability, or guidance-copy drift from
  `EXPORT_MENU_ROWS`. That preserves the existing single-source-of-truth
  contract from RFC 0035 F3.

### RFC 0038 — Export Menu Disabled Copy Polish

User-facing surface: the disabled `Mesh package...` row label.

- **Honest signal upgrade.** Replacing the trailing ellipsis with
  `(CLI only)` removes the "opens a dialog/follow-up flow" affordance for a
  permanently disabled browser row. That matches the user-guide framing that
  mesh-package authoring is a CLI/local workflow.
- **Row stays disabled.** Acceptance explicitly keeps the row unavailable in
  the browser and forbids any implication that the web UI can create mesh
  packages, hosted artifacts, or watertight solver-ready packages. No new
  enabled exports, no new route shape, no readiness promotion.
- **Changelog/user-guide discipline preserved.** The visible label change is
  recorded as visible-copy polish only — consistent with the 0047 ledger F3
  requirement that any `Mesh package...` change get an explicit changelog
  note.

### RFC 0039 — Web Snapshot Schema Unification

User-facing surface: indirect. The change is a presentation-layer schema
contract, but it controls observable behavior of the CFD review tab's
status chips, status-lines block, and artifact panel via
`_cfd_status_from_state` and the snapshot fed to read models.

- **Public payloads preserved.** Acceptance pins `/api/evaluate`, `/api/stl`,
  `/api/cfd/*`, and `/api/hulls/*` JSON shapes unchanged. All legacy aliases
  (`cfd_status`, `status`, `cfd_payload`, `cfd_job_payload`,
  `cfd_last_payload`, `cfd_status_lines`, `mesh_package_ref`,
  `cfd_mesh_package_ref`) remain compatible by default. The CFD tab is
  behaviorally identical from the user's perspective.
- **Drift gate named.** A focused test that fails when app snapshot keys and
  controller alias handling diverge mirrors the existing coverage at
  `tests/test_web_read_models.py:135-153` and closes the duplication 0047
  FR4 flagged.
- **Compatibility-by-default.** Alias removal requires explicit
  unreachability proof. Appropriate, since aliases were retained for exactly
  this drift risk.

## Findings (Non-Blocking)

Ordered by severity. None block landing.

### E1 — RFC 0036 should require the same browser gesture in the "remove" branch (low)

The retain branch lists a concrete browser gesture (slider away-and-back
inside seed tolerance, assert preset stays non-custom). The remove branch
only requires that "existing preset/browser coverage remains green and a
focused regression proves preset reseed/bounds behavior does not create an
unintended custom flip."

Why this matters: ergonomics review needs the same observable UX bar in
either outcome — otherwise an implementation could choose the cheaper
removal path while leaving the same-seed user gesture unproven.

How to apply (implementation, not RFC rewrite): if removal is chosen, add the
same slider away-and-back gesture as a browser-acceptance check and assert
the preset stays non-custom. The RFC permits this; it just does not require
it.

### E2 — RFC 0038 should resolve the subtitle-coordination question before implementation (very low)

The RFC's open question asks whether the disabled-row subtitle should be
adjusted alongside the label. The current subtitle points users to
`kayakgen mesh-package`; the new `(CLI only)` label suffix carries the same
guidance. The combination should not become repetitive.

How to apply: implementation should pick one — keep the existing subtitle
and rely on the new label suffix, or shorten the subtitle to avoid
duplication. Either preserves the no-overclaim boundary. Recording the
choice in the implementation patch summary is enough.

### E3 — RFC 0037 leaves the "byte-identical" reference fixture implicit (very low)

"Byte-for-byte" preservation is a strong claim, but the RFC delegates the
fixture choice to implementation. The current shipped subtitles are pinned
at `tests/test_web_layout.py:191-197`.

How to apply: implementation should reuse the existing test fixture as the
canonical reference. No copy edit is required for the RFC itself.

### E4 — RFC 0039 should call out CFD-tab browser acceptance in the implementation path (very low)

The RFC correctly excludes public route payload changes, but the
user-visible side-effect surface is the CFD review tab (status chips,
status-lines block, artifact panel). The Implementation Path lists "focused
web layout/read-model/browser tests" but does not explicitly name the CFD
tab acceptance check.

How to apply: implementation should run the existing browser CFD acceptance
checks unchanged and record this in the patch summary. No RFC text change
required.

## No-Overclaim Boundary Check

All four RFCs preserve the existing forbidden-copy and persistent-copy gates:

- **No new backend capability.** No hosted CFD, worker queue, cloud storage,
  auth, cancellation, real solver adapter (OpenFOAM/SU2/Docker), calibrated
  drag, accepted final prediction, or design fitness language.
- **No stability/readiness drift.** No real `GZ_max`,
  `heel_angle_max_deg`, capsize-range claim, watertight-solid promotion, or
  bare `cfd_ready` promotion. RFC 0038 explicitly forbids implying watertight
  or hosted artifacts from the disabled mesh-package row.
- **No web-side mesh-package authoring.** RFCs 0037 and 0038 keep the mesh
  package row disabled/unavailable. RFC 0039 explicitly excludes web-side
  mesh-package authoring.
- **No new domain concepts.** All four RFCs explicitly state they are
  presentation-boundary clarifications, not new aggregates or value objects.
- **Persistent claim copy preserved.** Resistance "Raw comparative filter;
  not final prediction.", CFD "Local filesystem CFD jobs on this server
  only; no hosted worker is running." and "Raw solver artifact only; not
  calibrated or validated.", and the "High-angle GZ unavailable" block
  remain unaffected.

## Conflicts With Current UI Scope

None. Each RFC inherits one workflow 0047 final-review finding (FR1-FR4) and
stays inside the matching ledger boundary (`F2`-`F4` plus the "Explicit
Deferrals" list). The RFCs do not reopen the desktop parity rewrite,
Qt-native slider replacement, `QMainWindow` migration, toolbar/drawer
preset-selector consolidation, rail visual-marker scope, or any deferred
backend/solver/calibration item.

## Internal-Only Cleanup Without Visible Acceptance?

- **RFC 0036:** No — the retain branch has a browser gesture; the remove
  branch has existing browser coverage at minimum (see E1 for the gap).
- **RFC 0037:** Largely an internal schema collapse, but acceptance pins
  rendered subtitle byte-identity and browser-observed enabled/unavailable
  rows, so the visible surface is gated.
- **RFC 0038:** Visible label polish with explicit changelog requirement.
- **RFC 0039:** Predominantly internal schema consolidation, but acceptance
  pins public REST payload shapes and CFD read-model behavior, both of which
  are user-observable through the CFD review tab. See E4 for the
  implementation-path nudge.

No RFC is purely internal cleanup without any user-observable acceptance
criterion.

## Residual Risk / Successor Notes

- E1's "remove" branch must land an equivalent browser gesture if
  implementation chooses removal; otherwise the same-seed UX invariant is
  proven only in the retain branch.
- RFC index (`docs/rfcs/README.md`) update is owned by the integration job
  per the rfc_ui synthesis, correctly out of scope for this review.
- Larger deferrals from RFC 0035 §Non-Goals and the 0047 ledger
  "Explicit Deferrals" list remain unchanged: desktop parity rewrite,
  Qt-native slider, `QMainWindow` migration, hosted CFD, real OpenFOAM/SU2
  adapters, calibrated drag, final prediction, design fitness, real
  high-angle GZ / `GZ_max` / `heel_angle_max_deg` / capsize range, web-side
  mesh-package authoring beyond existing safe entries, and watertight
  `cfd_ready` promotion.
