author: remediator-codex-gpt-5.5-001

# Remediation Patch Summary

## Scope

Remediated ledger M1 for RFC 0065 Slice 0: narrow visual baselines now reflect
their configured viewport widths.

Changed files:

- `tests/test_web_browser.py`
- `tests/visual_baselines/README.md`
- `tests/visual_baselines/1440x900.png`
- `tests/visual_baselines/1024x768.png`
- `tests/visual_baselines/960x720.png`
- `CHANGELOG.md`
- `docs/workflows/0058-rfc-0065-slice0-prebaseline/OPERATOR_REPORT.md`
- `striatum/0058-rfc-0065-slice0-prebaseline/remediation/PATCH_SUMMARY.md`

No `kayakgen/ui/` source was changed. No application `data-testid` / `kg-*`
hook, chip literal, caption, claim-state literal, `docs/USER_GUIDE.md`, or
`docs/WEB_VERIFICATION.md` was changed.

## Implementation Notes

- Changed the visual-baseline screenshot capture from full-page capture to
  viewport-clipped capture (`full_page=False`).
- Added `_png_size(...)` over the PNG IHDR chunk and assert each captured PNG
  matches its `VisualViewport` dimensions before it is written or compared.
- Regenerated all three committed baselines after the capture change.
- Updated the baseline README to document viewport-clipped screenshots instead
  of the previous full-page-overflow behavior.

Regenerated baseline dimensions:

- `1440x900.png`: 1440x900
- `1024x768.png`: 1024x768
- `960x720.png`: 960x720

## Verification

```bash
/tmp/kayakgen-visual-venv/bin/python -m pytest \
  tests/test_web_browser.py::test_web_workspace_visual_baseline \
  --update-visual-baselines -q
```

Result: `3 passed in 19.72s`

```bash
/tmp/kayakgen-visual-venv/bin/python -m pytest \
  tests/test_web_browser.py::test_web_workspace_visual_baseline -q
```

Result: `3 passed in 20.20s`

```bash
/tmp/kayakgen-visual-venv/bin/python -m pytest \
  tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q
```

Result: `4 passed in 35.98s`

```bash
./.venv/bin/python -m ruff check tests/test_web_browser.py tests/conftest.py
```

Result: `All checks passed!`

```bash
./.venv/bin/python -m pytest --ignore=tests/test_openfoam_v2512_smoke.py -q
```

Result: `1299 passed, 2 skipped, 1 failed in 482.76s`

Failure:

- `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
  reports that `kayakgen/services/evaluation.py` imports
  `kayakgen.ui.hydrostatics_metadata`. The remediation did not touch
  `kayakgen/services/evaluation.py` or `tests/test_services_boundaries.py`.
  Fixing that boundary violation is outside this packet's allowed write scope.
