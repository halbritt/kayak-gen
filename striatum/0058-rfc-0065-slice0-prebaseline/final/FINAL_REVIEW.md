---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

author: final-reviewer-claude-opus-4.8-001
schema_version: striatum.finding.v1
kind: finding
logical_name: final_review
session: sess_4c3ef9538188285d2f33408a87cf1575
date: 2026-06-02

# Final Review — Workflow 0058 (RFC 0065 Slice 0, pre-redesign baseline)

## Verdict

`accept_with_findings`

Slice 0 reflects every affirmed decision (S0-D1…S0-D6), holds the
no-appearance-change invariant byte-for-byte (zero `kayakgen/` diff), and the
must-fix ledger item **M1** is genuinely remediated. The browser-acceptance
profile is green on this canonical host and the full repo suite passes except
for one **pre-existing, out-of-scope** layering failure that predates RFC 0065
and that the packet's write scope cannot touch. The findings below are
non-blocking: one informational pre-existing failure (carry to its own
workflow) and a set of Slice-4 / Slice-2 successor concerns. Nothing here
warrants `needs_revision` — the one remediation round was spent correctly on
M1, and the residual suite failure is neither caused by nor fixable within this
slice.

## Method (independent verification on this dev host)

I re-derived every claim against the working tree and ran the tests myself
rather than trusting the upstream summaries. Commands and results are in
**Validation evidence** below. The remediation changed screenshot capture from
full-page to **viewport-clipped** (`full_page=False`) plus a per-PNG dimension
assertion; I reviewed the post-remediation code, not the implementer's original.

## Decision fidelity (S0-D1 … S0-D6)

| Decision | Requirement | Evidence (verified) | Status |
|---|---|---|---|
| **S0-D1** | Capture in the browser-acceptance profile at 1440×900 / 1024×768 / ≤960 px after settle | `test_web_browser.py:639-645` `@pytest.mark.browser_acceptance` + parametrized `VISUAL_VIEWPORTS` (`:53-57`: 1440×900, 1024×768, 960×720); `_capture_masked_workspace_png` (`:294-301`) reuses `_wait_for_workspace_shell` + `_assert_nonblank_3d` to settle | ✅ |
| **S0-D2** | Mask `geometry-vtk-view` / `.kg-vtk-viewport`; assert 3D liveness separately | `_mask_vtk_viewport` (`:255-291`) overlays `[data-testid='geometry-vtk-view'], .kg-vtk-viewport` with solid `#f3f4f6`, throws if no target; `_assert_nonblank_3d` (`:236-245`) runs **before** masking. Mask targets the real hooks at `kayakgen/ui/web/app.py:1511,1517` (untouched). Compare-within-tolerance passing run-to-run is direct proof the live frame is excluded | ✅ |
| **S0-D3** | Committed in-repo PNGs + README (canonical env + regen) | 3 PNGs under `tests/visual_baselines/` decode to **exactly** 1440×900 / 1024×768 / 960×720 (verified via IHDR); `README.md` records host/Python/Playwright/Chromium/date + the `--update-visual-baselines` regen command; `conftest.py:21-26` adds the flag | ✅ |
| **S0-D4** | Advisory compare; SKIP on missing tooling; HARD gate deferred to Slice 4 | Visual test uses `_load_playwright_optional` / `_launch_chromium_optional` (`:79-101`); `_compare_visual_png` (`:313-372`) skips on missing Pillow, and the test `pytest.skip`s on mismatch / missing-baseline with actual+diff paths (`:673-691`). The behavioural test keeps the hard-fail `_load_playwright` / `_launch_chromium` stance — intentional divergence | ✅ |
| **S0-D5** | No `kayakgen/ui/` source / hook / chip / caption / claim change; baseline is current shell | `git diff -- kayakgen/` and `git diff main…HEAD -- kayakgen/` both **empty**. No `@media`/responsive rule anywhere under `kayakgen/` (collapse is Slice 2). Committed PNGs render the present pre-redesign shell. The `kg-visual-mask` / `visual-vtk-mask` literals are runtime-only (`page.evaluate`), absent from `kayakgen/` | ✅ |
| **S0-D6** | Docs footprint = CHANGELOG + new README only; D047 not ratified | `CHANGELOG.md` gains a single `### Added` entry; `tests/visual_baselines/README.md` is new. `docs/USER_GUIDE.md`, `docs/WEB_VERIFICATION.md`, `docs/DECISION_LOG.md` all untouched (empty diff). D047 remains `proposed` in DECISION_LOG (added by the docs-only RFC commit `4b9558f`; ratifies "when RFC 0065 is accepted and Slice 4 lands") — this slice leaves it unratified | ✅ |

## No-appearance-change invariant

Held without qualification. The entire change is additive test infrastructure +
baseline fixtures + one CHANGELOG entry. No source under `kayakgen/`, no
`data-testid`/`kg-*` rename, no `CHIP_*`/caption/claim-state edit, RFC 0032
web-analysis boundary intact. The behavioural browser-acceptance test
(`test_kayakgen_serve_browser_acceptance`) — nonblank 3D before/after a control
mutation, slider label-geometry + a11y, class-preset bounds, Share-URL reload
round-trip, hull/deck STL bytes via `POST /api/stl`, console/page-error/network
cleanliness — is unchanged and passes.

## M1 remediation confirmed (and incidental O1/O2 resolution)

Ledger **M1** (narrow baselines must reflect their configured viewport widths)
is resolved: capture is now `full_page=False` (`:299`) with
`assert _png_size(png) == (viewport.width, viewport.height)` (`:300`,
`_png_size` at `:422-429`). The three committed PNGs now decode to distinct,
correct dimensions and the two narrow baselines are byte-distinct
(`cmp` differs) — previously they were pixel-identical.

The switch to viewport-clipped capture additionally **resolves** the two medium
ops-tests findings that were predicated on `full_page=True`:

- **O1** (fixed mask vs full-page capture misalignment): under a viewport clip,
  both the `position: fixed` mask and `getBoundingClientRect()` are
  viewport-relative, so placement is correct by construction regardless of
  scroll state. The passing compare on this host (where the VTK region renders)
  confirms alignment.
- **O2** (height change → 100%-magenta size-mismatch diff): clipped captures
  are always viewport-sized, so a Slice-2/3 reflow that changes content height
  no longer changes image dimensions, and the `_compare_visual_png` size guard
  (`:332-341`) will not short-circuit to a non-reviewable magenta diff on
  reflow.

## Validation evidence (run by me on this host)

- `pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance` →
  **4 passed in 34.84s** (3 parametrized visual-baseline compares against the
  committed PNGs within tolerance + the behavioural acceptance test). Playwright
  1.60.0 + Chromium 148 + Pillow 12.2 present, so the full
  capture→mask→compare round-trip ran.
- `pytest --ignore=tests/test_openfoam_v2512_smoke.py -m "not browser_acceptance"` →
  **1295 passed, 2 skipped, 1 failed, 4 deselected in 433.16s**. The 2 skips are
  the opt-in OpenFOAM smoke (env-gated). The 4 deselected are the
  browser-acceptance tests (run separately above). The single failure is the
  pre-existing one in **Finding 1**.
- `git diff --check` → clean. `git diff -- kayakgen/` and
  `git diff main…HEAD -- kayakgen/` → empty.
- `ruff check tests/test_web_browser.py tests/conftest.py` → All checks passed.
- IHDR dimension check on the three baselines → 1440×900 / 1024×768 / 960×720;
  the two narrow baselines are byte-distinct.
- DECISION_LOG: D047 present as `proposed`, untouched by this slice.

Repo left pristine: I am review-only (`repo_write: false`) and did **not** run
`--update-visual-baselines` (it would overwrite the committed PNGs). The
compare passing within tolerance already demonstrates the committed baselines
are reproducible on the canonical host; the ops-tests reviewer separately
verified byte-stable regeneration against a backup.

## Findings (non-blocking)

### Finding 1 — Pre-existing, out-of-scope suite failure (informational; own workflow)

`tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
fails because `kayakgen/services/evaluation.py:33` imports
`HYDROSTATICS_ROW_METADATA` from `kayakgen.ui.hydrostatics_metadata` (services
must not import `ui`). I confirmed via `git log -S` that this import was
introduced by commit **`313dfdd` (2026-05-25, workflows 0037+0038)** — over a
week before RFC 0065 and entirely outside this slice (which touches neither
`kayakgen/services/` nor `kayakgen/ui/`). It is therefore **not** a Slice-0
regression and was correctly declined by the remediator as outside the packet's
write scope. Surfaced only so it is not mis-attributed to workflow 0058; it
warrants its own remediation workflow.

### Finding 2 — Narrow baselines share the current shell layout until Slice 2 (successor: S1)

With no responsive `@media` collapse in source yet (Slice 2 scope), the 1024 and
960 viewports render the same intrinsic shell content, clipped to different
widths. After M1 they are byte-distinct and correctly dimensioned, satisfying
S0-D1/S0-D3 literally, but the ≤960 px bucket does not yet exercise a *distinct
collapsed layout*. Re-baseline and (optionally) assert pairwise distinctness
when the Slice-2 collapse lands. No action this slice.

### Finding 3 — Slice-4 polish carried forward (successors: S2/S3/S4 + O3/O4/O5)

Provisional and explicitly deferred per S0-D3/S0-D4: ratify the per-viewport
tolerance (currently `VISUAL_PIXEL_CHANNEL_TOLERANCE = 8`,
`VISUAL_MISMATCH_PIXEL_RATIO = 0.02` at `:42-43`) and canonical-env hardening;
flip the compare to a HARD gate; document the baseline-update procedure in
`docs/WEB_VERIFICATION.md`. Minor cleanups to fold into Slice 4: the one
remaining 250 ms wall-clock settle in the capture path (`:298`, **O3**); add the
provisional tolerance to `tests/visual_baselines/README.md` so it is documented
where S0-D3 asks, not only as code constants (**O4**); and replace the
pure-Python per-pixel diff loop (`:343-353`) with `ImageChops`-based counting
(**O5**, perf-only, acceptance-profile only). Re-check mask placement when a
Slice-2/3 reflow can move the VTK region (**S3**) — lower risk now that capture
is viewport-clipped.

## Env-fragility assessment (role-requested)

The baseline is reproducible on the canonical host (compare passes within
tolerance run-to-run). The largest cross-host / next-slice fragilities the
earlier review flagged (O1 mask placement, O2 magenta-on-resize) are
**resolved** by the remediation's move to viewport-clipped capture. The residual
forward risk is font-hinting jitter across hosts, which is exactly what the
permissive committed tolerance absorbs and what Slice 4 is chartered to harden
(canonical OS + Chromium build, documented per-viewport tolerance). No
`kayakgen/ui/` change was needed to reach this posture.

## Disposition

`accept_with_findings`. Scope is valid and fully traceable to S0-D1…S0-D6 with
no creep; the baseline is the current shell with the live 3D region masked; the
compare is advisory; M1 is remediated; the behavioural browser-acceptance checks
and the full repo suite (minus the env-gated smoke) are green except for one
documented pre-existing, out-of-scope failure. Slice 0 lands. Finding 1 → its
own workflow; Findings 2–3 → RFC 0065 Slice 2 / Slice 4.
