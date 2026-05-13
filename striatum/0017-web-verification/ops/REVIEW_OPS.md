author: operator [self-declared: operator-ops-review]

# Ops review - web packaging and tests

Verdict intent: accept_with_findings

## Findings

### O-001 - Docker path exists but has no recorded verification procedure

`Dockerfile` installs `kayakgen[web]` and runs `kayakgen serve --host 0.0.0.0
--port 8080`, but the repo lacks a document with build/run/smoke commands.

Required action: add deployment/verification docs and run `docker build` if
practical in this workflow.

### O-002 - Optional browser tooling is absent and should stay optional

The environment has `trame`, `vtk`, Docker, npm, and npx, but lacks Playwright,
pytest-playwright, Lighthouse, Chrome, and Chromium.

Required action: do not add mandatory dev dependencies for this workflow. Add
documentation and optional commands instead.

### O-003 - REST/STL/share helpers have headless coverage

Existing `tests/test_web.py` covers state/query round trip, metrics parity, STL
bytes, REST route registration, and hull store helpers. This is a good base for
non-browser CI.

Required action: preserve these tests and add only the missing visual smoke
test.

### O-004 - RFC 0008 says local serve opens a browser, but CLI currently starts a server

`kayakgen serve` starts the Trame server on the requested host/port; it does not
open a browser tab. Auto-opening a browser would be undesirable in Docker and
CI without a separate opt-in flag.

Required action: document current behavior honestly. Do not change CLI default
semantics in this verification workflow.
