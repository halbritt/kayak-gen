---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

author: reviewer-ops-tests-claude-opus-4.8-001
schema_version: striatum.finding.v1
kind: finding
logical_name: review
session: sess_38b3860d978f797fc96b86494048448e
date: 2026-06-02

# Ops And Tests Review — Workflow 0058 (RFC 0065 Slice 0, pre-redesign baseline)

## Provenance

This supersedes the earlier operator stopgap finalize at this path
(`author: operator [self-declared: 0058-opstests-fin]`, verdict `accept`), which
was written because this `reviewer_ops_tests` lane was requeued on an
`agent_lease_heartbeat` stall while it ran the long browser-acceptance command,
before it could write its artifact. This is the re-dispatched lane completing the
genuine review. The verdict still lands the slice (`accept_with_findings` ⊂
accept); the difference is two env-fragility findings (O1, O2) the stopgap did
not surface.

## Verdict

`accept_with_findings`

The Slice 0 scaffold meets every affirmed decision (S0-D1..D6). Capture runs at
all three viewports with the live 3D region genuinely masked, the compare path
is advisory (SKIP without tooling, skip-on-mismatch with artifacts), the
`--update-visual-baselines` path regenerates byte-stably on this host, the
committed PNGs are the current pre-redesign shell, and the existing behavioural
browser-acceptance checks stay green. The findings are non-blocking: O1/O2 are
the env-fragility risks the role asked me to flag (mask placement under
`full_page` capture, and size-mismatch diffs on the next slice's reflow) and are
fixable / partly Slice-4-deferred; O6 is a pre-existing, out-of-scope suite
failure I am surfacing only so it is not mis-attributed to this slice.

## Validation (all run on this dev host)

- `pytest tests/test_web_browser.py::test_web_workspace_visual_baseline -m browser_acceptance --browser-acceptance` → **3 passed** (1440×900, 1024×768, 960×720). Playwright + Chromium are present here, so the full capture→mask→compare round-trip ran and passed within tolerance — direct evidence the mask excludes the live VTK frame (otherwise run-to-run VTK pixels would exceed the 2% ratio).
- `--update-visual-baselines` (run against a backup, then committed bytes restored; sha256 verified identical) → **3 passed**; regenerated PNGs were byte-size-identical to committed (169741 / 160684 / 167942). Repo left pristine — I am review-only and did not alter the committed baselines.
- `pytest tests/test_web_browser.py::test_kayakgen_serve_browser_acceptance -m browser_acceptance --browser-acceptance` → **1 passed** (nonblank 3D, slider label-geometry + a11y, class-preset, Share reload, hull/deck STL byte checks, console/page-error/network cleanliness).
- `git diff --check` → clean. Full collection → **1304 tests**; `browser_acceptance` marker registered (no `PytestUnknownMarkWarning` even under `-W error`).
- Visually inspected the three committed PNGs: the `Geometry`/VTK region is a flat fill and the shell is the **current** pre-redesign layout (Parameters rail, Metrics, Hydrostatics, Stability, Resistance) — confirms S0-D2 masking and S0-D5 "current shell".
- Scope guard: `git status` confirms only `CHANGELOG.md`, `tests/conftest.py`, `tests/test_web_browser.py` modified plus untracked `tests/visual_baselines/` and `striatum/0058.../`. `kayakgen/ui/`, `docs/USER_GUIDE.md`, `docs/WEB_VERIFICATION.md`, `docs/DECISION_LOG.md` are all untouched (S0-D5/D6; D047 not ratified).
- Full non-browser suite (`pytest -m "not browser_acceptance"`) → **1295 passed, 4 skipped (opt-in OpenFOAM smoke), 1 failed** — the failure is pre-existing and unrelated (see O6).

## Findings

### O1 — `position: fixed` mask + `full_page=True` capture is scroll/host-fragile  (severity: medium, accept_with_findings)

**Where:** `tests/test_web_browser.py:255-291` (`_mask_vtk_viewport`), `:294-299` (`_capture_masked_workspace_png`), `:243` (`_assert_nonblank_3d` element screenshot).

The mask overlays a `position: fixed` div positioned from viewport-relative
`getBoundingClientRect()` coordinates, but the capture is
`page.screenshot(full_page=True)`. Under full-page capture Chromium anchors
fixed elements to the layout viewport at scroll 0, so the mask only lines up
when the VTK region is within the initial viewport at mask time. Immediately
before masking, `_assert_nonblank_3d` calls `candidate.screenshot()`, which
scrolls the VTK element into view — on a host/viewport where the workspace shell
overflows and the VTK region sits below the fold, the fixed mask can land at the
wrong `y` and leave live VTK pixels in the captured full-page image. That would
silently defeat S0-D2 and false-positive the Slice-2 diff. It happens to align
on this host (tests pass), which is exactly the env-fragility this role is asked
to flag.

**Suggested remediation:** anchor the mask to document coordinates with
`position: absolute` (`rect.left + window.scrollX`, `rect.top + window.scrollY`),
or capture a fixed `clip` region instead of `full_page`. Either makes mask
placement independent of scroll state. Tunable/hardenable in Slice 4, but cheap
to fix now.

### O2 — full-page size mismatch short-circuits to a non-reviewable diff  (severity: medium, accept_with_findings)

**Where:** `tests/test_web_browser.py:330-339` (`_compare_visual_png` size guard).

When `actual.size != expected.size` the helper returns `mismatch_ratio=1.0` and
writes a solid-magenta diff. Because captures are `full_page=True`, image height
tracks content height — and the Slice-2/3 layout reflow this baseline exists to
make reviewable will almost certainly change page height. The result is a
100%-magenta diff with zero spatial information, the opposite of the
"reviewable visual diffs" goal in `SLICE_0_DECISIONS.md`. Advisory in Slice 0,
but it undercuts the slice's stated purpose for the next slice.

**Suggested remediation:** compare within a fixed-size viewport `clip` (stable
region, no `full_page`), or align top-left and diff the overlapping bounding box
so a height change still yields a spatially meaningful diff. Reasonable to land
the clip approach now or to flag it explicitly for Slice 4's gate design; at
minimum, note the magenta-on-resize behaviour so Slice 2/3 reviewers expect it.

### O3 — one wall-clock sleep remains in the capture path  (severity: low, accept_with_findings)

**Where:** `tests/test_web_browser.py:298` (`page.wait_for_timeout(250)`).

The role calls out "no wall-clock-sleep flakiness." The mask div is appended
synchronously inside the `evaluate` call, so the 250 ms fixed settle is the one
nondeterministic wait in the new path. (The other waits — `_wait_for_http`'s
`time.sleep(0.25)` and the Playwright `wait_for_function`/`wait_for` calls — are
bounded polling, which is fine.)

**Suggested remediation:** replace with a deterministic settle, e.g.
`page.wait_for_selector("[data-testid='visual-vtk-mask']")` or a double
`requestAnimationFrame` inside the mask `evaluate` before returning. Low impact
(the value is generous and the masked region is static), but it removes the last
fixed delay.

### O4 — tolerance values are not documented where S0-D3 asks  (severity: low, accept_with_findings)

**Where:** `tests/test_web_browser.py:42-43` (`VISUAL_PIXEL_CHANNEL_TOLERANCE = 8`,
`VISUAL_MISMATCH_PIXEL_RATIO = 0.02`); `tests/visual_baselines/README.md`.

S0-D3 calls for "a permissive, **documented** tolerance." The README documents
the canonical env and the regen command well, but the actual tolerance Slice 4
is meant to refine lives only as code constants. A one-line note in the README
(channel-delta ≤ 8, mismatch-ratio ≤ 2%, pointing at the constants) closes the
loop and gives Slice 4 a documented starting point.

### O5 — pure-Python per-pixel diff loop  (severity: low / perf, non-blocking)

**Where:** `tests/test_web_browser.py:341-351` (`_compare_visual_png` loop).

The mismatch count iterates every pixel in Python over full-page (~1.3M+ px)
images. Pillow is already a dependency, so `ImageChops.difference(...)` +
`point(threshold)` + a histogram (or `getbbox()` on the thresholded mask) would
compute the same ratio far faster and avoid hundreds of ms of per-run CPU. Only
runs in the acceptance profile with tooling present, so non-blocking; worth
folding into the Slice-4 gate work.

### O6 — pre-existing suite failure, OUT OF SCOPE for this slice  (severity: informational)

**Where:** `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
→ `kayakgen/services/evaluation.py:33` imports `HYDROSTATICS_ROW_METADATA`
from `kayakgen.ui.hydrostatics_metadata` (services layer must not import `ui`).

This fails the "rest of the suite stays green" precondition, but it is **not** a
Slice-0 regression: the offending import was introduced 2026-05-25 (commit
`313dfdd`, workflows 0037+0038) and reproduces with all Slice-0 working changes
stashed (`1 failed, 14 passed`). This slice touches none of `kayakgen/services/`
or `kayakgen/ui/`. I surface it only so the operator knows the base branch
carries a layering violation predating RFC 0065 and so it is not mis-attributed
to workflow 0058. It does not block Slice 0 acceptance; it warrants its own
remediation workflow.

## Env-fragility assessment (role-requested)

The baseline is reproducible on the canonical host (compare and re-capture both
byte-stable here), so Slice-0's own gate is sound. The cross-host / next-slice
fragility lives in **O1** (mask placement under `full_page`) and **O2** (height
change → magenta diff). Recommended path: move the comparison off `full_page`
to a fixed viewport `clip` and switch the mask to document-anchored
`position: absolute`; keep the permissive committed tolerance (channel ≤ 8,
ratio ≤ 2%) but document it (O4). That combination keeps the Slice-2/3 diffs
spatially reviewable and font-hinting tolerant, and hands Slice 4 a clean,
documented tolerance/canonical-env starting point — without changing any
`kayakgen/ui/` source in Slice 0.

## Non-Findings (confirmed good)

- Mask targets the real hooks `[data-testid='geometry-vtk-view'], .kg-vtk-viewport`
  (matches `kayakgen/ui/web/app.py:1511,1517`, untouched) and is genuine overlay
  masking, not crop-by-luck; it throws if no viewport is found; 3D liveness is
  asserted separately via `_assert_nonblank_3d` (S0-D2 satisfied).
- Advisory posture is correct (S0-D4): the visual test uses the
  `_load_playwright_optional` / `_launch_chromium_optional` SKIP variants and
  `pytest.skip` on mismatch with actual+diff paths, while the behavioural test
  keeps the hard-fail `_load_playwright` / `_launch_chromium` stance — the
  divergence is intentional and matches the decision.
- No module-level side effects in the new code; the `conftest.py` change is two
  additive `addoption`s only.
- Server lifecycle is clean: Playwright is checked before `_start_server`, and
  `_stop_server` runs in `finally` even when an optional loader skips.
- Patch-summary cross-check: implementer's recorded runs (3 passed update /
  3 passed compare / ruff clean / 4 passed acceptance) reproduce here.
