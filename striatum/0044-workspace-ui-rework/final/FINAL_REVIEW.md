# Final Review

## Verdict

`accept_with_findings`

The implementation lands the ledger's safe-now RFC 0033 scope conservatively.
The three-region workspace shell, theme module, structured `Advisory` record,
status/chip read models, persistent claim/readiness/CFD copy, bounded desktop
touch-ups, and regression tests are all present and consistent with the
findings ledger. The patch summary's deferral list matches the ledger's
explicit residual-risk list. No blocking findings; the items below are
follow-up gaps that should be tracked in a successor RFC rather than blocking
this slice.

## Findings

### F1 — Web class preset does not reseed or narrow sliders

`kayakgen/ui/web/app.py:614-695` exposes the class preset radio purely as a
state-bound input. There is no `on_change` handler analogous to
`KayakGUI._on_class_select` that reseeds `length_m`, `beam_oa_m`, `beam_wl_m`,
`draft_m`, `Cp` from `KayakClass.*.default` or narrows slider ranges to the
class envelope. RFC 0033 §2 calls this out explicitly in the acceptance
criteria. Severity: follow-up.

### F2 — Validity badge is static placeholder

`kayakgen/ui/web/app.py:691-695` renders a fixed `VChip` with the literal
"Custom (L/B_wl from current hull)" regardless of hull state. RFC 0033 §2
requires the badge to derive one of `In <class> envelope`,
`Custom — sub-touring`, `Custom — beyond elite`, or
`Custom (L/B_wl=X.X)` from the active hull, mirroring `desktop._classify`.
Severity: follow-up.

### F3 — Resistance card omits sweep table and target row

`kayakgen/ui/web/app.py:778-786` renders only the heading, caption, detail
copy, and the `uncalibrated_comparative` chip. RFC 0033 §4 Resistance
requires the sweep table at `[2.0, 3.0, 4.0, 5.0, 6.0] kt`, the target-speed
row highlighted with `--state-focus-row`, and the `kt | Fn | Rv N | Rw N |
Rt N` columns. `resistance_table_view_model` exists in
`kayakgen/ui/web/controllers.py:200-259` and is tested
(`tests/test_web_read_models.py:126-146`), but it is not wired to the
resistance card. The Hydro tab's analysis pre-block carries the sweep text,
so the data is reachable; the dedicated card is just not bound. Severity:
follow-up.

### F4 — Mesh tab does not render live diagnostics

`kayakgen/ui/web/app.py:788-819` only renders static descriptive text and the
readiness chip. `mesh_diagnostics_lines_from_state` and
`mesh_package_view_model` (controllers lines 309-411) are exercised by
`tests/test_web_read_models.py` but are not bound into the mesh card.
Welded-primary counts and warnings therefore do not appear in the UI today.
Severity: follow-up.

### F5 — Toolbar Export menu is incomplete

`kayakgen/ui/web/app.py:623-632` exposes only `Export Hull STL` and
`Export Deck STL`. RFC 0033 §5 specifies `Export ▾` with `Hull STL`,
`Deck STL`, `Hydro JSON`, `Stability JSON`, and `Mesh package…`. The
two STL routes work as before; the additional JSON/mesh-package export
entries are missing. Severity: follow-up.

### F6 — Forbidden-string grep test is narrower than RFC 0033 §8

`tests/test_web_layout.py:94-100` asserts `GZ_max`, `heel_angle_max_deg`,
and `cfd_ready` count, but not the other listed no-go strings (`OpenFOAM`,
`SU2`, `cloud`, `worker queue`, `calibrated drag`, `final prediction`,
`design fitness`). A grep of `kayakgen/ui` confirms none of those strings
appears in normal UI output today, but the regression contract framed in
RFC 0033 §8 expects each to convert into a grep-style assertion. Severity:
follow-up.

### F7 — Patch summary's CHANGELOG note disagrees with branch diff

`striatum/0044-workspace-ui-rework/implementation/PATCH_SUMMARY.md:90-91`
states "Root `CHANGELOG.md` was not edited because it is outside this job's
write scope." The branch diff shows six added lines in `CHANGELOG.md` for
this workflow (`git diff --stat main..HEAD`). Most likely the landing
commit added the entry separately; the patch summary should be reconciled
on the next pass. Cosmetic mismatch; no behavioural impact. Severity:
cosmetic.

### F8 — Desktop region/test-id parity is intentionally absent

`final_review.md` asks that "the desktop GUI uses the same regions" with
test ids. The ledger P1 deliberately scoped desktop to safe touch-ups and
called out that a full `QMainWindow`/`QTabWidget` rewrite was future work;
`kayakgen/ui/desktop.py` consequently has no DOM-style region ids. Treating
this as an explicit deferral that matches the ledger's stated boundary
(`Patch Summary > Explicit Deferrals` and `Ledger > Residual Risks`),
rather than as a blocking gap. Severity: deferred (already named).

## Evidence

### Required inputs read

- `AGENTS.md`
- `docs/PRD.md`
- `docs/rfcs/0033-workspace-ui-rework.md` (canonical scope / copy / acceptance)
- `striatum/0044-workspace-ui-rework/ledger/FINDINGS.md`
- `striatum/0044-workspace-ui-rework/implementation/PATCH_SUMMARY.md`
- `docs/USER_GUIDE.md`
- `CHANGELOG.md` (head, RFC 0033 entry)

### Implementation files inspected

- `kayakgen/ui/theme.py` (single colour authority, contrast manifest, VTK
  background helper, matplotlib rcParams helper, Vuetify config helper,
  chip specs, typography tokens).
- `kayakgen/model/advisory.py` (immutable `Advisory` record additive to
  `DesignAdvisory`; `warnings: tuple[str, ...]` preserved).
- `kayakgen/ui/desktop.py` (`Cm` slider, `Export STLs` label with
  unchanged filenames, theme-routed plot colours, four-segment status
  vocabulary; PyVista docking explicitly deferred).
- `kayakgen/ui/gui_params.py` (Cm wired through `GUI_TO_HULL`).
- `kayakgen/ui/pv_window.py` (VTK background and hull/deck colours
  sourced from `kayakgen.ui.theme`).
- `kayakgen/ui/web/app.py` (three-region shell with `region-params`,
  `region-geometry`, `region-review` test ids, parameter rail grouping
  matching the ledger, five review tabs in Hydro/Mesh/Comparison/CFD/
  Advisories order, status-bar segments with click-to-tab focus, exact
  persistent banner / chip copy, hidden share-state probe replacing the
  pinned URL field).
- `kayakgen/ui/web/controllers.py` (`evaluation_summary`,
  `mesh_diagnostics_lines_from_state`, `mesh_package_view_model`,
  `resistance_table_view_model`, profile label↔ID mapping, REST routes
  unchanged).
- New / modified tests: `tests/test_advisory.py`,
  `tests/test_gui_params.py`, `tests/test_ui_theme.py`,
  `tests/test_web_layout.py`, `tests/test_web_read_models.py`, and
  `tests/test_web_browser.py` (Hydrostatics / GM0 / comparative_filter_only
  copy added).

### Validation commands run

| Command | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q` | `291 passed in 56.69s` |
| `.venv/bin/python -m pytest tests/test_web.py tests/test_web_layout.py tests/test_ui_theme.py tests/test_advisory.py tests/test_gui_params.py tests/test_web_read_models.py -q` | `55 passed in ~2s` |
| `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q` | `1 passed in 5.44s` |
| Grep `GZ_max\|heel_angle_max_deg\|OpenFOAM\|SU2\|worker queue\|hosted worker\|\\bcloud\\b\|calibrated drag` over `kayakgen/ui` | No hits outside the allowed "no hosted worker is running" notice in `controllers.py`. |
| Grep `cfd_ready` over `kayakgen/ui` | Only `theme.py` chip spec (vocabulary entry) and the allowed negation `not watertight cfd_ready` in `app.py`. |

This distinguishes the browser-acceptance result from the silent-skip case
flagged in the ledger's residual risks: Playwright and Chromium were
available in this environment and the lane actually executed.

### Specific spot checks

- The browser test (`tests/test_web_browser.py:307-397`) waits for
  "Hydrostatics", "Displacement", "GM0", "Resistance curve (raw
  comparative filter)", and "comparative_filter_only" — the persistent
  resistance warning code surfaced via
  `analysis_lines_from_state` → `resistance.metadata.warnings`. Confirms
  the live `uncalibrated_comparative` claim string is anchored on every
  resistance render.
- `evaluation_summary` returns a `cfd_status` derived from
  `cfd_payload.run.status`, `state['cfd_status']`, or the rendered status
  line, matching the ledger's status-bar plumbing requirement.
- `resistance_table_view_model` correctly inserts a sorted target-speed
  row outside the 0.05 kt tolerance and otherwise marks the nearest fixed
  row as focus (`tests/test_web_read_models.py:126-146`).
- Mesh profile mapping in `MESH_PROFILE_LABEL_TO_ID` is symmetric and
  surfaced in both `_mesh_profile_options()` and the workspace
  `mesh_profile_options` state; `watertight-solid` is disabled with the
  ledger's exact tooltip.

## Residual Risk

- **Dynamic wiring of mesh diagnostics, resistance sweep table, and
  validity badge.** Read models exist; the workspace cards display static
  scaffolding. A user sees correct claim/readiness/CFD chips, but the
  per-tab data shape promised by RFC 0033 §4 (welded primary counts in
  mesh, sweep+target-row table in resistance, dynamic L/B_wl validity
  badge) is not yet rendered. None of the existing surfaces overclaim —
  the gap is conservatism, not falsified readiness — but it is the most
  natural follow-up RFC lane.
- **Web preset interaction parity.** Selecting a class preset in the web
  rail does not reseed or narrow sliders, so the web rail's "preset →
  envelope" behaviour silently lags the desktop GUI. Class chips appear
  consistent, but the slider envelopes do not actually change.
- **Forbidden-string regression breadth.** The grep test does not yet
  cover every RFC 0033 §8 no-go string. The code happens to be clean
  today, so the risk is regression detection, not current claim leakage.
- **Desktop conceptual parity is intentionally bounded.** The matplotlib
  GUI cannot match the chip / tab / focus-ring behaviour of the web
  workspace; deeper desktop parity must wait for a Qt main-window rewrite
  (already named as deferred in the ledger and the patch summary).
- **High-angle GZ, calibrated drag, watertight `cfd_ready`, hosted CFD,
  Pareto plot widget, multi-variant 2D overlay** remain explicit
  deferrals as the ledger requires.
- **Browser-acceptance environment dependency.** This review verified the
  acceptance lane passes locally with Playwright/Chromium installed;
  future runs in environments without those extras must continue to
  treat skips as missing coverage rather than success.

### Sub-agent and parallel-helper use

This pass used direct file reads and greps in parallel against the
implementation tree rather than spawning helper agents — the verification
surface (one RFC, one ledger, one patch summary, ~10 implementation
files, three test files) fit within the main session context and the
patch summary already enumerated its own sub-agent helpers. Parallel
tool calls were used to read source/test/doc files concurrently where
they were independent.
