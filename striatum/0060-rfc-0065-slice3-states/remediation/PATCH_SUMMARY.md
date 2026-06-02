author: remediator-codex-gpt-5.5-001

# RFC 0065 Slice 3 Remediation Patch Summary

## Must-fix item closed

- MF-1: extended the forbidden-copy/no-go scrub in `tests/test_web_layout.py` so
  the actual scrub runs over the rendered-string bundle that includes the
  `kayakgen/ui/web/generate_frontier_view.py` render-hook section.

## Scope kept unchanged

- No rendered state copy changed.
- No claim/readiness/status chip copy or semantic class changed.
- No disabled control was enabled or had explanatory copy removed.
- No REST route, evaluator, claim-state literal, readiness literal, accepted-use
  literal, or analysis surface was added.
- `docs/USER_GUIDE.md`, `docs/WEB_VERIFICATION.md`, and
  `docs/DECISION_LOG.md` were not touched; D047 remains proposed.

## Verification

- Focused suite: `.venv/bin/python -m pytest tests/test_web_layout.py tests/test_web_inline_help.py tests/test_ui_theme.py tests/test_desktop_layout.py -q`
- Full suite minus env-gated smoke:
  `.venv/bin/python -m pytest -q --ignore=tests/test_openfoam_v2512_smoke.py`
- Whitespace: `git diff --check`

The full-suite run still reports the known out-of-scope
`tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
failure from workflow 0059 NB-2.
