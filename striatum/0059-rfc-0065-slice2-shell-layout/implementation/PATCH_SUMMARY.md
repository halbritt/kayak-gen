author: implementer-codex-gpt-5.5-001

# Patch Summary

## Scope

- Reflowed the web workspace shell onto a shared token-backed stylesheet
  covering Parameters, Geometry, Review, status bar, and Generate surfaces.
- Added one additive density token for the existing 960px collapse breakpoint
  so the Slice 2 media query stays source-tokenized.
- Marked Generate build/watch/pick regions with stable internal classes and
  kept the existing region/status test IDs and collapse hooks intact.
- Updated focused layout/theme tests and the changelog entry for RFC 0065
  Slice 2.

## Verification

- `.venv/bin/python -m pytest tests/test_ui_theme.py tests/test_web_layout.py tests/test_web_inline_help.py -q`
  passed: 54 tests.
