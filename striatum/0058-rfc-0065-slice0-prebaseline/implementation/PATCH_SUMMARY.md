author: implementer-codex-gpt-5.5-001

# Patch Summary

## Scope

Landed RFC 0065 Slice 0 visual-baseline scaffolding inside the existing
browser-acceptance profile.

Changed files:

- `tests/conftest.py`
- `tests/test_web_browser.py`
- `tests/visual_baselines/README.md`
- `tests/visual_baselines/1440x900.png`
- `tests/visual_baselines/1024x768.png`
- `tests/visual_baselines/960x720.png`
- `CHANGELOG.md`

No `kayakgen/ui/` source files were changed. No `data-testid` / `kg-*` hooks,
chip literals, captions, or claim-state literals were renamed or edited.

## Implementation Notes

- Added `--update-visual-baselines`.
- Added an advisory visual browser test parametrized at `1440x900`,
  `1024x768`, and `960x720`.
- Reuses the existing local `kayakgen serve` startup and browser-failure
  collection path.
- Waits for rendered workspace text and independently asserts nonblank 3D
  before screenshot capture.
- Masks `[data-testid='geometry-vtk-view'], .kg-vtk-viewport` with a solid
  overlay before taking the full-page screenshot.
- Compares current PNGs against committed baselines with a provisional Slice 0
  tolerance:
  - per-channel pixel threshold: `8`
  - mismatch-ratio threshold: `0.02`
- On mismatch, writes `<viewport>.actual.png` and `<viewport>.diff.png` under
  the pytest temporary directory, then skips as advisory. Slice 4 remains the
  hard-gate/tolerance-ratification slice.

## Baseline Environment

Canonical capture environment is documented in
`tests/visual_baselines/README.md`:

- Linux `proximal` kernel `6.8.0-111-generic`
- Python `3.12`
- Playwright `1.60.0`
- Chrome for Testing / Chromium `148.0.7778.96`
- Capture date `2026-06-02`

No deterministic-capture blocker was observed on this host after masking the
VTK region.

## Verification

Commands run:

```bash
/tmp/kayakgen-visual-venv/bin/python -m pytest \
  tests/test_web_browser.py::test_web_workspace_visual_baseline \
  --update-visual-baselines -q
```

Result: `3 passed in 19.17s`

```bash
/tmp/kayakgen-visual-venv/bin/python -m pytest \
  tests/test_web_browser.py::test_web_workspace_visual_baseline -q
```

Result: `3 passed in 20.63s`

```bash
/tmp/kayakgen-visual-venv/bin/python -m ruff check \
  tests/test_web_browser.py tests/conftest.py
```

Result: `All checks passed!`

```bash
/tmp/kayakgen-visual-venv/bin/python -m pytest \
  tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q
```

Result: `4 passed in 36.06s`
