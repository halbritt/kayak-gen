author: final-reviewer-claude-opus-4.8-001

# Final Review — Workflow 0061 (RFC 0065 Slice 4: visual-regression hard gate + a11y + Lighthouse)

date: 2026-06-02
run: run_1eca17c00dfe7aeeb104ae7f9ddc6f81
verdict: **accept**

## Verdict

**accept.** Every Slice 4 decision (D1–D8) in `SLICE_4_DECISIONS.md` is reflected
in the shipped change; the single must-fix (MF-1) is closed by committed
remediation; the claim line and RFC 0032 boundary are intact; the docs are
updated and DECISION_LOG **D047** is ratified (`proposed` → `accepted`); and the
full repo suite is green except the documented, out-of-scope NB-2 services-import
failure. **With Slice 4 landed, RFC 0065's core (Slices 1–4) is COMPLETE.** Slice 5
(desktop visual polish) remains deferred / operator-gated per D009 / D021.

This finding is the result of independent verification — not a synthesis of the
upstream review artifacts alone. Where I re-ran or re-inspected something
directly, it is marked **[verified]** below.

## Method

Read: RFC 0065 §5 (Slice 4 spec + acceptance criteria + mandatory-vs-optional
gate table), `SLICE_4_DECISIONS.md` (D1–D8), DECISION_LOG D047, RFC 0033 §8
forbidden-claim guard, the implementer + remediation `PATCH_SUMMARY.md`, the three
review artifacts (claims/ops_tests/traceability), the `FINDINGS_LEDGER.md`, and the
changed files. Independently re-ran the deterministic gates and the full suite;
re-inspected the working-tree diff of every changed file.

## Decision-by-decision verification

### D1 — Baselines regenerated on the canonical env, explained diff, before the hard flip — **PASS**

The three PNGs (`1440x900`, `1024x768`, `960x720`) were regenerated via the
`--update-visual-baselines` path. **[verified]** `git diff --stat` shows all three
as binary changes with growth consistent with the explained cause:
`1440x900` 118617→154476, `1024x768` 81526→92312, `960x720` 67489→74743. The
canonical env is recorded identically in `tests/visual_baselines/README.md` and
`docs/WEB_VERIFICATION.md` (Linux 6.8.0-111, Playwright Chromium `147.0.7727.15` /
chromium-1217, capture `2026-06-02`). The explained diff (PATCH_SUMMARY "Baseline
Diff Review") attributes the growth to the previously-inert token CSS now
rendering in Chromium (the Slice 2/3 tokenized shell) — not unexplained churn. The
VTK `VtkRemoteView` region is masked before capture (`_mask_vtk_viewport`,
`VISUAL_MASK_FILL = "#f3f4f6"`, targeting `[data-testid='geometry-vtk-view'],
.kg-vtk-viewport`). Ledger A-1 accepts the explained diff; no PNG flagged for
unexplained churn.

### D2 — Visual compare flipped advisory → HARD gate; SKIP/HARD posture — **PASS**

**[verified]** in `tests/test_web_browser.py`:
- Missing Playwright/Chromium → `pytest.fail` under `--browser-acceptance`
  (`_load_playwright`, `_launch_chromium`, lines 72–104), `pytest.skip` otherwise.
- Missing baseline → `pytest.fail` under acceptance, `pytest.skip` otherwise
  (`test_web_workspace_visual_baseline`, lines 916–923).
- Over-tolerance mismatch → `pytest.fail` under acceptance, advisory `pytest.skip`
  otherwise (lines 931–940).
- VTK mask retained in the capture path (`_capture_masked_workspace_png`).

### D3 — Documented per-viewport tolerance; demonstrably FAILs (not a no-op) — **PASS**

`VISUAL_PIXEL_CHANNEL_TOLERANCE = 8`, `VISUAL_MISMATCH_PIXEL_RATIO = 0.02`
(lines 44–45), documented in `WEB_VERIFICATION.md` ("Visual Baselines") and the
D047 row. Each viewport is compared independently (parametrized). The "must fail
on an over-tolerance diff" requirement — flagged by traceability F1 as resting on
manual evidence — is now **pinned by committed regression tests** (MF-1, below).
**[verified]** re-ran `test_compare_visual_png_fails_over_tolerance_and_writes_diff`
(3 differing px in a 10×10 → ratio 0.03 > 0.02 → `passed=False`, diff written) and
`test_compare_visual_png_passes_under_mismatch_ratio_without_diff` (1 px → ratio
0.01 ≤ 0.02 → `passed=True`, no diff written): **2 passed**.

### D4 — a11y checks (HARD in acceptance); theme additive; fix minimal/token-sourced — **PASS**

`_assert_workspace_focus_order_and_ring` (deterministic toolbar focus order +
ring resolved from the `--state-focus-ring` token), `_assert_workspace_hit_targets`
(`A11Y_MIN_HIT_TARGET_PX = 24`), and `_assert_contrast_manifest` (both
`COLORS_LIGHT` and `COLORS_DARK`) are wired into
`test_kayakgen_serve_browser_acceptance` (lines 969–971). The `CONTRAST_MANIFEST`
check also stays a no-browser mandatory pytest gate
(`test_ui_theme.py::test_contrast_manifest_clears_thresholds`). **[verified]**
re-ran that gate (parametrized over both palettes): passed.
**[verified]** `kayakgen/ui/theme.py` and `tests/test_ui_theme.py` are byte-identical
to HEAD (empty diff) → the `CONTRAST_MANIFEST`/`theme.py` additive constraint is
trivially satisfied. The only UI a11y fix is the focus-ring selector extension to
`.kg-toolbar-action` / `.kg-export-menu-under-1200` / `.kg-class-preset-select`
(`app.py:445–448`), using the existing Slice 1 `--state-focus-ring` token — minimal
and token-sourced, not a layout redesign.

### D5 — Lighthouse Best-Practices ≥ 90 recorded, not a pytest gate — **PASS**

`docs/WEB_VERIFICATION.md` records Best Practices `1.0` (100) on `2026-06-02`
(`npx --yes lighthouse@latest`, `CHROME_PATH` → Playwright Chromium
`147.0.7727.15`, local `kayakgen serve`). No pytest asserts Lighthouse; the gate
table marks it "Optional … do not make it a pytest gate." Ledger A-4 concurs.

### D6 — Retain every existing behavioural acceptance check — **PASS**

**[verified]** in the acceptance test: nonblank-3D before *and* after a
representative slider mutation (lines 972, 1028, 1077); Share-URL reload
round-trip with mutated metrics persisting and `shared_hull.length_m !=
Hull().length_m` (lines 1054–1076); STL bytes via `POST /api/stl?part=hull` and
`part=deck` with content-type/disposition/triangle-count assertions
(lines 1080–1123); console/page/network cleanliness via `_collect_browser_failures`
+ `_assert_no_browser_failures` (lines 901/904/1124). No new network-allowlist
entry was added.

### D7 — Claim line + RFC 0032 boundary intact — **PASS**

**[verified]** `kayakgen/ui/theme.py` unchanged (chip constants `CHIP_SPECS` /
`CHIP_LABELS` / `CHIP_CLASSES` byte-identical to HEAD). The `app.py` diff adds
**no** new REST route, `claim_state`, `Readiness`, or `accepted_uses` literal
(grep of added lines clean). The `workspace_style_html` rewrite changes only the
CSS *injection mechanism* — the `ROOT_THEME_CSS` / `PARAMETER_RAIL_CSS` strings are
byte-unchanged — so no chip is recoloured and no raw result is baked into a
confident treatment (claims review confirms this at the pixel level: PASS). A scan
of all newly-added doc/app lines for RFC 0033 §8 no-go terms (`hosted`, `cloud`,
`worker queue`, `SU2`, `validated CFD`, `calibrated resistance`, `final
design-fitness`) found only one "hosted" hit — in the D047 row's description of the
*rejected* hosted visual-diff SaaS alternative and its revisit condition, i.e.
decision-log prose about an option **not** chosen, not a capability/availability
claim in rendered output. The RFC 0032 web-analysis boundary text is unchanged; the
USER_GUIDE addition is explicitly presentation-only ("does not add routes,
evaluators, solver capability, or new claim/readiness states").

### D8 — Docs updated + D047 ratified — **PASS**

**[verified]** in the working-tree diff:
- `docs/WEB_VERIFICATION.md`: baseline-update procedure (canonical OS + Chromium
  build, regen command, reviewed-diff expectation) + the mandatory-vs-optional
  gate table (screenshot / focus-order-ring-hit-target / contrast / Lighthouse).
- `docs/USER_GUIDE.md`: polish behaviour + the new verification gate,
  presentation-only.
- `docs/DECISION_LOG.md`: **D047** `proposed` → `accepted`, with the chosen
  tolerance (delta `8`, ratio `0.02`) and the in-repo PNG storage choice recorded.
- `CHANGELOG.md`: a Slice 4 entry plus the MF-1 remediation entry.

## Findings ledger reconciliation

- **MF-1 (must-fix)** — committed no-browser self-test for `_compare_visual_png`:
  **CLOSED.** The remediation added two synthetic-PNG tests pinning both edges of
  the gate; I re-ran them (2 passed). This removes the F1 risk that a future
  refactor could silently neuter the comparator.
- **NB-1 / NB-2 (non-blocking)** — the pre-existing
  `tests/test_services_boundaries.py` services→ui import-boundary failure
  (`kayakgen/services/evaluation.py` importing
  `kayakgen.ui.hydrostatics_metadata`): correctly deferred to a separate hygiene
  follow-up; no Slice 4 file touches it.
- **A-1 … A-4** — accepted / no-action items (explained baseline diff, traceable
  CSS-injection rewrite, chip-colour delegated to claims, Lighthouse recorded-only):
  concur.

## Independent validation evidence

- **[verified]** `git diff --check`: clean.
- **[verified]** `git diff --stat HEAD`: 12 files, +401/−21; `kayakgen/ui/theme.py`
  and `tests/test_ui_theme.py` **not** in the diff.
- **[verified]** Comparator self-tests + `CONTRAST_MANIFEST` gate (both palettes):
  `4 passed in 0.04s`.
- **[verified]** Full repo suite, default profile (env-gated smoke excluded by
  default): `.venv/bin/python -m pytest -q` → **`1 failed, 1307 passed, 4 skipped
  in 463.92s`**. The 4 skips are all opt-in OpenFOAM env-gated tests. The sole
  failure is the documented, out-of-scope NB-2:
  `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`.
  This matches the implementer (1305+) and remediation (1307) recorded runs.
- Browser-acceptance profile (`-m browser_acceptance --browser-acceptance`):
  recorded `4 passed` by both the implementer and remediation lanes on this
  canonical host; not re-run here (heavy, requires live server + Chromium) — relied
  on the converging recorded evidence plus my source-level verification of the
  gate, mask, a11y, and behavioural-check wiring.

## RFC 0065 completion

Slice 4 is the final core slice and the only one touching `docs/USER_GUIDE.md`,
`docs/WEB_VERIFICATION.md`, and `docs/DECISION_LOG.md`. All eight decisions hold,
the must-fix is closed, the boundaries are intact, and the suite is green modulo
the documented out-of-scope NB-2. **RFC 0065's core (Slices 1–4) is COMPLETE.**
Remaining: Slice 5 desktop polish (deferred per D009 / D021) and the NB-2 services
import-boundary hygiene follow-up.
