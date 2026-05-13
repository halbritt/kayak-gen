Read `docs/workflows/0020-browser-acceptance-demo/SOURCES.md`, especially
`kayakgen/ui/web/app.py`, `tests/test_web.py`, `docs/WEB_VERIFICATION.md`, and
current environment notes in the operator report.

Produce `striatum/0020-browser-acceptance-demo/browser/REVIEW_BROWSER.md` with:

- author line: `author: operator [self-declared: operator-browser-review]`
- verdict intent
- findings `B-001`, `B-002`, ...
- required action for each finding

Focus on:

- whether app construction exercises enough VTK/Trame rendering to catch blank
  scene regressions in headless tests;
- what can be smoke-verified without Playwright;
- what a future browser/Lighthouse test should require;
- whether the visual layout or metrics panel has obvious runtime risks;
- how to document skipped browser checks truthfully.
