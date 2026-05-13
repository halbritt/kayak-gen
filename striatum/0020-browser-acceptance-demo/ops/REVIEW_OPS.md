author: operator [self-declared: operator-ops-review]

# Ops review - browser acceptance and demo

Verdict intent: accept_with_findings

## Findings

### O-001 - Browser acceptance has no reproducible command in the repo

`docs/WEB_VERIFICATION.md` names a future `tests/test_web_browser.py`, but the
file does not exist and `pyproject.toml` has no optional browser-acceptance
dependency group. A contributor cannot run the advertised browser smoke from a
fresh checkout.

Required action: add either the optional test file plus dependency guidance, or
a documented scriptable command that fails/skips clearly when browser tooling is
missing.

### O-002 - Lighthouse is only a prose suggestion

The docs suggest `npx lighthouse ...`, but no installed dependency, script, or
verification record exists. Because no Chrome/Chromium binary is available, a
Lighthouse check cannot pass in the current environment.

Required action: keep Lighthouse optional and document the browser prerequisite.
Do not add it to the mandatory test path unless the implementation also makes
the browser dependency reproducible.

### O-003 - Docker remains the only concrete demo artifact

The Dockerfile builds the web app image and starts `kayakgen serve --host
0.0.0.0 --port 8080`. There is no hosted demo URL, deployment manifest, or
operator evidence for a public deployment.

Required action: strengthen `docs/WEB_VERIFICATION.md` so Docker is clearly the
current demo artifact and hosted deployment remains future work. If a deploy
recipe is added, it should be labeled as a recipe, not as completed deployment.

### O-004 - Serve command should remain CI/Docker friendly

The current Typer command is scriptable because it starts the server without
opening a local browser. Changing that default would complicate container and
test automation.

Required action: preserve the default. Any browser-opening behavior should be an
explicit option and covered by tests or documentation.

## Required gate

Proceed to ledger. The safe implementation surface is tests/docs/status and
possibly an opt-in browser-open flag; mandatory browser or Lighthouse
dependencies should only land if the environment can install and run them
reproducibly.
