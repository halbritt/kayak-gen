author: operator [self-declared: operator-implementer-temp]

# Patch summary - 0017 web verification

## Files changed

- `Dockerfile`
- `docs/WEB_VERIFICATION.md`
- `docs/rfcs/0008-web-frontend.md`
- `docs/rfcs/0013-pareto-frontier-comparison-ui.md`
- `docs/rfcs/README.md`
- `kayakgen/ui/web/app.py`
- `tests/test_web.py`
- `docs/workflows/0017-web-verification/OPERATOR_REPORT.md`

## Findings addressed

- F-001: updated RFC 0008 and the RFC index to `partial verified-headless`.
- F-002: added an offscreen VTK visual smoke test that checks actors, render
  interactor, image dimensions, and nonblank pixels.
- F-003: documented skipped Playwright/Lighthouse checks and future commands in
  `docs/WEB_VERIFICATION.md`.
- F-004: documented local and Docker web verification commands.
- F-005: documented current `kayakgen serve` behavior without changing its
  default server-start semantics.
- F-006: preserved web comparison UI as deferred in RFC 0013/README language.
- Additional runtime fix: attached a `vtkRenderWindowInteractor` to the Trame
  render window so `VtkRemoteView.update()` works when the server starts.
- Additional Docker fix: installed EGL/OSMesa/Xcursor runtime libraries needed
  for VTK offscreen rendering in the container.

## Verification

- `.venv/bin/python -m pytest tests/test_web.py tests/test_cli.py -q`
  -> 19 passed.
- `.venv/bin/python -m pytest -q` -> 122 passed.
- `docker build -t kayakgen-web-verify .` -> passed.
- Container HTTP smoke:
  `docker run -d --name kayakgen-web-verify-0017 -p 18080:8080 kayakgen-web-verify`
  then `curl -fsSL http://127.0.0.1:18080/` -> 1376-byte app response.
- `git diff --check` -> clean.
- `ruff` was not run because it is not installed in the current virtualenv.
- Playwright and Lighthouse were not run because their tooling/browser
  prerequisites are not installed in the current environment.
