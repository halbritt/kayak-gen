author: operator [self-declared: 0061-impl]

# Patch Summary

## What Changed

- Regenerated the three committed visual baselines under
  `tests/visual_baselines/` for `1440x900`, `1024x768`, and `960x720`.
  The 3D `VtkRemoteView` region remains masked before capture.
- Flipped the visual compare from advisory to hard failure in the
  browser-acceptance profile. The documented tolerance is per-channel delta
  `8` with a per-viewport mismatch-pixel ratio of `0.02`.
- Added acceptance-profile a11y checks for deterministic toolbar focus order,
  visible focus ring sourced from `--state-focus-ring`, 24 px minimum hit
  targets, and `CONTRAST_MANIFEST` in both palettes.
- Wired the existing token CSS into the rendered Trame content via
  `workspace_style_html`, because the previous direct `html_widgets.Style(...)`
  calls were ignored by `SinglePageWithDrawerLayout` and the token variables
  were not present in Chromium.
- Extended the token focus-ring rule to the toolbar class select, Reset, Share,
  and Export controls. This is the only UI a11y fix; it uses the existing Slice
  1 focus-ring tokens.
- Updated `docs/WEB_VERIFICATION.md`, `docs/USER_GUIDE.md`,
  `docs/DECISION_LOG.md`, `CHANGELOG.md`, and
  `tests/visual_baselines/README.md`.

## Baseline Diff Review

The regenerated PNGs now reflect the post-Slice-2/3 tokenized shell that is
actually rendered in Chromium: the shared surface, border, radius, density,
hover/focus/state, and typography CSS is active in the browser rather than
being absent from the DOM. The visible changes are the intended RFC 0065 shell
polish and Slice 3 control/state treatments; no claim/readiness/status chip
copy or chip semantic class changed, and the VTK region is masked.

PNG size changes:

- `1440x900.png`: `118617` -> `154476` bytes
- `1024x768.png`: `81526` -> `92312` bytes
- `960x720.png`: `67489` -> `74743` bytes

## Hard-Compare Evidence

An injected over-tolerance diff against `1440x900.png` produced
`VisualCompareResult(passed=False, mismatch_ratio=0.07901234567901234,
max_channel_delta=255, ...)`, proving the compare is not a no-op and fails over
the documented `0.02` ratio tolerance.

## Lighthouse

Optional Lighthouse Best Practices ran on `2026-06-02` against a local
`kayakgen serve` instance with `CHROME_PATH` set to Playwright Chromium
`147.0.7727.15`. Best Practices scored `1.0` (100).

## Verification

- `.venv/bin/python -m pytest tests/test_web_browser.py::test_web_workspace_visual_baseline --update-visual-baselines -q`
  - `3 passed`
- `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q`
  - `4 passed in 36.19s`
- Injected over-tolerance visual diff check
  - `passed=False`, mismatch ratio `0.07901234567901234`
- `CHROME_PATH=/home/halbritt/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome npx --yes lighthouse@latest ... --only-categories=best-practices`
  - Best Practices `1.0`
- `.venv/bin/python -m pytest tests/test_ui_theme.py tests/test_web_layout.py -q`
  - `47 passed in 24.58s`
- `.venv/bin/python -m ruff check kayakgen/ui/web/app.py tests/test_web_browser.py tests/test_web_layout.py`
  - `All checks passed!`
- `git diff --check`
  - clean
- `.venv/bin/python -m pytest -q`
  - `1305 passed, 4 skipped, 1 failed in 476.84s`
  - failure is the known out-of-scope NB-2 services boundary:
    `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
    reports `kayakgen/services/evaluation.py` importing
    `kayakgen.ui.hydrostatics_metadata`.
