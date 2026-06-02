# Web Visual Baselines

RFC 0065 Slice 0 commits the current web workspace shell as advisory
Playwright/Chromium screenshots. The live 3D `VtkRemoteView` region is masked
before capture; 3D liveness remains covered separately by the browser
acceptance test.

## Canonical Render Environment

- Host: `Linux proximal 6.8.0-111-generic #111-Ubuntu SMP PREEMPT_DYNAMIC Sat Apr 11 23:16:02 UTC 2026 x86_64`
- Python: `3.12`
- Playwright: `1.60.0`
- Chromium: Chrome for Testing `148.0.7778.96` (`playwright chromium v1223`)
- Capture date: `2026-06-02`

The committed files are:

- `1440x900.png`
- `1024x768.png`
- `960x720.png`

The viewport names are the requested browser viewport sizes. The capture
scaffold uses viewport-clipped screenshots and asserts that each PNG decodes to
the named dimensions, so narrow baselines remain governed by their configured
widths even when the rendered shell overflows the viewport.

## Regeneration

Install the browser extras and Chromium, then regenerate:

```bash
python -m pip install -e '.[web,browser,dev]'
python -m playwright install chromium
python -m pytest tests/test_web_browser.py::test_web_workspace_visual_baseline \
  --update-visual-baselines -q
```

Without `--update-visual-baselines`, the test compares the current masked
screenshots against these files. Slice 0 mismatches are advisory skips that
write actual and diff PNGs to the pytest temporary directory; Slice 4 is
expected to decide the hard-failure gate and final tolerance.
