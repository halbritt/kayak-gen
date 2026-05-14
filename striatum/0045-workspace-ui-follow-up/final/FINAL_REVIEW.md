# Final Review — Workflow 0045 (RFC 0034 Workspace UI Follow-Up)

## Verdict

`accept_with_findings`

The implementation commit (`1e2d6e5`) lands the ledger-approved safe slice
of RFC 0034 conservatively and consistently with the findings ledger and
patch summary. Class presets reseed canonical hull sliders and narrow
ranges, manual hull edits flip the rail back to `custom`, the validity
badge is derived from current hull/class state with the exact RFC 0033
string set, the Resistance card now renders the
`resistance_table_view_model` sweep with the target row, the Mesh tab
renders live `mesh_diagnostics_lines_from_state` data plus the
`mesh_package_view_model` for selected packages, a single Export menu
exposes Hull STL / Deck STL / Hydro JSON (enabled) and Stability JSON /
Mesh package (disabled with CLI guidance), the forbidden-copy regression
has been broadened with explicit allowed negations, and `docs/USER_GUIDE.md`
plus `CHANGELOG.md` describe only the safe behavior that actually landed.
No blocking finding remains; the follow-ups below are non-blocking
observations and successor-RFC seeds.

## Findings

Ordered by severity. None are blocking.

### F1 — Validity badge is keyed only to the selected preset, not all classes (low/follow-up)

`kayakgen/ui/web/controllers.py:128-141` derives the badge from the
currently selected class preset (`state["class_preset"]`). If the preset
is `custom` but the hull happens to satisfy the touring/performance/
surfski_int/surfski_elite envelope, the badge stays `Custom (L/B_wl=X.X)`
rather than `In <class> envelope`. RFC 0034 §Acceptance and ledger P1
allow this — the ledger requires "exactly one of" the allowed strings and
this is the case — but it intentionally diverges from
`desktop._classify` (`kayakgen/ui/desktop.py:362-376`), which scans all
classes. Treat as a successor consideration; do not block.

### F2 — `_state_matches_preset_seed` short-circuit in hull-param listener is effectively dead (very low)

`kayakgen/ui/web/app.py:688-704` includes a branch
(`if self._state_matches_preset_seed(...)`) that re-applies bounds and
refreshes the scene without flipping the preset. Reaching it requires
the listener to fire while the state already matches the seed exactly
and the guard is off, which does not normally happen because the user
just changed a slider. It is harmless (it cannot stay on a non-custom
preset after a non-seed value lands), but it is a small piece of
unreachable code that future maintenance can prune.

### F3 — Sliders outside the five canonical fields keep global bounds when a preset is active (low/follow-up)

`_apply_slider_bounds` (`kayakgen/ui/web/app.py:422-428`) restores the
global `SLIDER_DEFS` ranges for any slider not in
`CLASS_PRESET_HULL_FIELDS` (`deck_height_m`, `Cm`, `deck_flatness`,
`center_box_ratio`, `bow_rake`, `stern_rake`, `target_speed_kt`). That
matches the ledger P0 "seed five canonical hull sliders, narrow bounds"
scope and the patch-summary description, and the test
`test_class_preset_reseeds_bounds_and_manual_hull_edit_flips_custom`
expects target_speed bounds to remain global. It is worth flagging only
because a user editing one of those non-canonical sliders while a
preset is active will be flipped to `custom` (since the slider is in
`HULL_STATE_FIELDS`); the parameter-rail UX is consistent but the
implicit "edit anything in the rail outside the canonical five and you
lose your preset" semantics deserves a successor sentence in the user
guide.

### F4 — Export-row data table does not drive the menu render (low / docs cosmetic)

`EXPORT_MENU_ROWS` (`kayakgen/ui/web/app.py:103-137`) is currently the
authoritative read model for `tests/test_web_layout.py::
test_export_menu_rows_are_single_honest_menu_contract`, but
`_render_export_menu` (`kayakgen/ui/web/app.py:1039-1083`) re-states the
labels, subtitles, and disabled flags inline. Drift between the two is
already constrained by tests, but if a future change updates only one
side the menu and its data contract could diverge silently. Optional
follow-up: render the menu by iterating `EXPORT_MENU_ROWS`.

### F5 — `_state_snapshot` exposes ad-hoc state keys to controllers (very low / hygiene)

`_state_snapshot` (`kayakgen/ui/web/app.py:495-514`) hand-rolls the
list of keys to copy out of `self.state` (including legacy aliases like
`cfd_status`, `cfd_payload`, `cfd_job_payload`, `cfd_last_payload`).
Most are guarded by `hasattr` checks but the keys are duplicated across
`controllers._cfd_status_from_state`. As the web shell continues to
grow, this could be tightened to a single declared schema. Hygiene
follow-up; not load-bearing for this slice.

## Evidence Reviewed

Required reading:

- `AGENTS.md` (reading list and project conventions).
- `docs/PRD.md` (not re-read here; covered by prior workflow review).
- `docs/USER_GUIDE.md` (workflow 0045 additions at lines 365-414 describe
  preset reseed/narrow, validity badge, Resistance/Mesh review,
  Export menu honesty).
- `docs/design/kayak_hull_design_constraints.md` (not re-read; relevant
  domain copy is already gated through claim/readiness vocabulary).
- `docs/rfcs/0033-workspace-ui-rework.md` (acceptance §2 preset behavior,
  §4 Resistance/Mesh, §5 Export menu, §8 forbidden-claim guard).
- `docs/rfcs/0034-workspace-ui-follow-up.md` (problem, goals, AC1-AC6,
  non-goals, open questions).
- `striatum/0045-workspace-ui-follow-up/ledger/FINDINGS.md`
  (gate `accept_with_findings`, P0-P2 findings, safe-now scope, explicit
  deferrals, validation matrix, successor risks).
- `striatum/0045-workspace-ui-follow-up/implementation/PATCH_SUMMARY.md`
  (resolved findings, deferrals, validation results, proposed changelog).
- `striatum/0044-workspace-ui-rework/final/FINAL_REVIEW.md` (F1-F6 source).
- `striatum/0044-workspace-ui-rework/ledger/FINDINGS.md` (prior deferrals).
- `striatum/0044-workspace-ui-rework/implementation/PATCH_SUMMARY.md`
  (baseline for unchanged regions of the workspace shell).

Implementation surfaces inspected:

- `kayakgen/ui/web/app.py` — preset reseed (`_apply_class_preset`,
  `_apply_slider_bounds`), `_applying_class_preset` guard,
  `_on_hull_param_change` custom-flip semantics, `_on_view_param_change`
  for view-only `target_speed_kt`, validity badge rendering with
  `role="status"` / `aria-live="polite"`, Resistance card rendering
  `resistance_table_html` (target row marked
  `kg-resistance-row-target state-focus-row`), Mesh card rendering
  hull/deck diagnostics + warnings + disabled `watertight-solid` profile
  copy, single Export menu with five rows and honest disabled states,
  `EXPORT_MENU_ROWS` + `PERSISTENT_COPY` + responsive class hooks
  preserved from RFC 0033.
- `kayakgen/ui/web/controllers.py` — `class_preset_options`,
  `class_preset_read_model` (five canonical hull fields,
  per-field min/max/default), `validity_badge_from_state` (exact RFC
  string set), `resistance_table_view_model` (target-row sort and
  tolerance), `mesh_diagnostics_lines_from_state` (welded primary, raw
  detail, warnings), `mesh_package_view_model` (`_resolve_package_artifact_path`
  rejects absolute/parent-traversal/URI refs and writes
  `artifact_path_outside_package` errors), `evaluation_summary` for
  status-bar segments, REST routes unchanged, `_resolve_job_artifact_path`
  preserves CFD job containment.
- `tests/test_web_layout.py` — layout test ids, class preset enumeration
  with human labels, Export-row contract, broadened forbidden-copy
  assertions with documented allowed negations, preset reseed + bounds +
  manual-edit flip, target-speed view-only assertion, Resistance/Mesh/
  Export render-source checks.
- `tests/test_web_read_models.py` — class preset read model defaults
  and bounds, custom/unknown returns, exact validity badge strings,
  `evaluation_summary` with package + design advisories, mesh
  diagnostics line shape, mesh package view model with profile mapping
  and artifact containment.
- `tests/test_web_browser.py` — Playwright scenarios for the
  `surfski_elite` preset reseed, narrowed slider bounds, manual flip to
  `custom`, validity badge transitions, Mesh tab text, Export menu rows
  including CLI guidance, STL download header assertions.
- `docs/USER_GUIDE.md` (workspace section 365-414) — factual prose for
  preset reseed/narrow, badge advisory, Resistance/Mesh display, Export
  menu unavailable states, `kayakgen stability` / `kayakgen mesh-package`
  guidance, no claim of hosted storage or watertight cfd_ready.
- `CHANGELOG.md` — Unreleased entry matches the patch-summary proposed
  wording verbatim.
- `OPERATOR_REPORT.md` — implementation-launch and completion
  checkpoints added by the operator; not part of this review's write
  scope, but content is consistent with the patch summary's
  "implementation lane exited successfully" claim.

Spot-check verifications:

- Forbidden-copy grep across
  `kayakgen/ui/web/app.py` and `kayakgen/ui/web/controllers.py` returned
  only the four documented allowed phrases (`not final prediction`,
  `no accepted final-prediction`, `not watertight cfd_ready`,
  `no hosted worker is running`). No raw occurrences of `OpenFOAM`,
  `SU2`, `cloud`, `worker queue`, `calibrated drag`, `design fitness`,
  `GZ_max`, `heel_angle_max_deg`, or bare `cfd_ready` outside negations.
- `hydro_lines_from_state` no longer carries resistance sweep text
  (`controllers.py:530-542`), so the Hydrostatics card no longer
  duplicates the Resistance card content.
- `_resolve_package_artifact_path` rejects URI-like (`://`), absolute,
  and parent-traversal references; `mesh_package_view_model` now
  records `artifact_path_outside_package` and surfaces the issue in
  `warnings` and `artifact_errors`, with a regression test in
  `tests/test_web_read_models.py::
  test_mesh_package_view_model_rejects_manifest_refs_outside_package`.
- `EXPORT_MENU_ROWS[3].status == "unavailable"` (Stability JSON) and
  `EXPORT_MENU_ROWS[4].status == "unavailable"` (Mesh package…) with
  CLI guidance in their descriptions, matching ledger P0 export scope.
- The Export menu is a single keyboard-operable `VMenu` with five
  `VListItem` rows; disabled items use `disabled=True` plus
  `aria-disabled="true"`.
- The validity badge `VChip` is rendered on the parameter rail
  (`app.py:971-982`) with `role="status"`, `aria-live="polite"`, and a
  bound `aria-label` that includes the current badge text.
- `target_speed_kt` is wired through `_on_view_param_change`, not
  `_on_hull_param_change`; the test
  `test_target_speed_edit_does_not_flip_class_preset` confirms it does
  not flip the preset.

## Validation Commands

I personally ran the following from the repository root using the
project virtualenv (`.venv/bin/python`). All passed.

```bash
git diff --check                                                       # no output (clean)
.venv/bin/python -m pytest tests/test_web.py \
  tests/test_web_layout.py tests/test_web_read_models.py \
  tests/test_mesh_package.py -q -p no:cacheprovider                    # 58 passed in 13.52s
.venv/bin/python -m pytest tests/test_web_browser.py \
  -m browser_acceptance --browser-acceptance -q -p no:cacheprovider    # 1 passed in 10.43s
.venv/bin/python -m pytest -q -p no:cacheprovider                      # 299 passed in 69.17s
```

These reproduce the patch-summary "Validation" section exactly, with the
same pass counts. Playwright/Chromium were available in this environment
so the browser-acceptance lane actually executed rather than skipping
(matching the ledger validation matrix requirement that skips be treated
as missing coverage, not success).

Forbidden-copy and containment behavior were additionally exercised by
`tests/test_web_layout.py::
test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`
and `tests/test_web_read_models.py::
test_mesh_package_view_model_rejects_manifest_refs_outside_package`
inside the focused and full pytest runs above.

## Residual Risks And Follow-Up Work

- **Validity badge / class detection asymmetry.** F1 above. If a future
  RFC expects the badge to reflect any-class envelope membership rather
  than selected-class membership, a small change to
  `validity_badge_from_state` is required. Tracking as a follow-up only.
- **Web-side mesh-package authoring and Stability JSON download.**
  Explicitly deferred by RFC 0034 and the ledger. Both Export rows
  remain disabled with CLI guidance; promotion needs a successor RFC.
- **Watertight-solid readiness and bare `cfd_ready` promotion.**
  Deferred. The profile is rendered as visible-but-disabled with the
  existing tooltip.
- **Hosted/cloud CFD, OpenFOAM/SU2, real solver adapters, worker queues,
  calibrated drag, final-prediction validity envelopes, design fitness,
  high-angle `GZ`, `GZ_max`, `heel_angle_max_deg`, full capsize-range
  stability.** All deferred per RFC 0033/0034 and the ledger; current
  copy guarantees no claim leakage.
- **Per-row resistance claim variance.** Card-scope
  `uncalibrated_comparative` chip is correct for this slice; row-level
  variance needs a future calibration/claim RFC.
- **Desktop region/test-id parity, multi-variant overlay, Pareto plot
  widget, persistent pinned candidates, multi-user share, full mobile
  authoring.** All deferred and unchanged from workflow 0044's
  acceptance-with-findings state.
- **Patch-summary cosmetic hygiene.** The note in
  `PATCH_SUMMARY.md` says `OPERATOR_REPORT.md` was left untouched by
  Codex; the implementation commit does contain operator-authored
  updates to that file. This is consistent with the documented split
  (Codex job vs operator landing) but mirrors the cosmetic mismatch
  pattern flagged by workflow 0044 F7; no remediation is needed.
- **Slider scope outside the canonical five.** F3 above. Consider a
  one-sentence user-guide clarification in a future docs pass.

## Attribution Metadata Note

This artifact intentionally contains no `author:`, byline, frontmatter,
`Co-Authored-By:`, or other attribution metadata. The role is final
reviewer; the artifact is review-only and is not signed beyond its
location under `striatum/0045-workspace-ui-follow-up/final/`.
