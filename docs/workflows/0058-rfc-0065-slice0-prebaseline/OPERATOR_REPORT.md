# Operator Report — Workflow 0058 (RFC 0065 Slice 0: pre-redesign baseline)

**Status:** remediated with residual unrelated suite failure.

## Scope

Slice 0 of RFC 0065: land the Playwright/Chromium screenshot-capture scaffolding
in the browser-acceptance profile and commit a baseline of **today's** shell at
1440×900 / 1024×768 / ≤960 px (masking the 3D `VtkRemoteView` region), so the
Slice 2/3 reflow produces reviewable visual diffs. No appearance/layout/claim
change. See `SLICE_0_DECISIONS.md` (S0-D1…S0-D6).

## Lanes

- Implement / ledger / remediate: `codex` (write lane; runs Playwright capture).
- Reviews (traceability, ops-tests) and final review: `claude` / `gemini`
  (reviews kept off the codex lane per the operator-hazard notes). No claims
  reviewer — Slice 0 changes no user-facing copy.

## Outcome

Slice 0 visual-baseline scaffold is present and the review ledger's must-fix
finding M1 is remediated.

- The screenshot capture path now uses viewport-clipped Playwright screenshots
  (`full_page=False`) and asserts that each PNG decodes to the configured
  viewport dimensions before writing or comparing.
- The committed baselines were regenerated and verified as:
  `1440x900.png` = 1440x900, `1024x768.png` = 1024x768,
  `960x720.png` = 960x720.
- No `kayakgen/ui/` source was changed. No application `data-testid` / `kg-*`
  hook, chip literal, caption, claim-state literal, `docs/USER_GUIDE.md`, or
  `docs/WEB_VERIFICATION.md` was changed.

Verification:

- `/tmp/kayakgen-visual-venv/bin/python -m pytest tests/test_web_browser.py::test_web_workspace_visual_baseline --update-visual-baselines -q`
  -> 3 passed.
- `/tmp/kayakgen-visual-venv/bin/python -m pytest tests/test_web_browser.py::test_web_workspace_visual_baseline -q`
  -> 3 passed.
- `/tmp/kayakgen-visual-venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q`
  -> 4 passed.
- `./.venv/bin/python -m ruff check tests/test_web_browser.py tests/conftest.py`
  -> clean.
- `./.venv/bin/python -m pytest --ignore=tests/test_openfoam_v2512_smoke.py -q`
  -> 1299 passed, 2 skipped, 1 failed. The failure is
  `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
  because `kayakgen/services/evaluation.py` imports
  `kayakgen.ui.hydrostatics_metadata`. This path was not touched by Slice 0
  remediation and fixing it would cross the packet's allowed write scope.
