author: operator [self-declared: operator-ledger]

# Findings ledger - 0020 browser acceptance and demo

Run id: `run_bd1e5ad4453a45469b470dd7c2fc5ec2`  
Job: `findings_ledger`  
Gate result: proceed to implementation

## Stats

- Source artifacts: 3
- Source findings: 14
- Deduplicated findings: 5
- By severity: high 2 / medium 3 / low 0
- Safe-now findings: 5
- Deferred findings: 3

## Deduplicated Findings

### F-001 - Browser acceptance has no reproducible test entry point

- Sources: T-001, B-001, B-003, O-001
- Severity: high
- Classification: safe-now
- Files: `tests/test_web_browser.py`, `pyproject.toml`,
  `docs/WEB_VERIFICATION.md`
- Statement: RFC 0008 browser acceptance is still represented only by prose.
  Headless VTK tests are useful but do not prove a real browser can load the
  Trame client, connect to the server, see controls/viewer, and react to a user
  interaction.
- Required remediation: Add an optional Playwright-based browser smoke test or
  equivalent script that starts `kayakgen serve`, opens the page, checks core UI
  text, and exercises at least one slider/metrics interaction. If Playwright or
  browser binaries are unavailable, the test must skip with an actionable reason
  and setup command. Add optional dependency metadata for this browser
  acceptance path without making it part of the mandatory install.

### F-002 - Lighthouse acceptance is unavailable and should remain a named optional gate

- Sources: T-003, B-004, O-002
- Severity: high
- Classification: safe-now
- Files: `docs/WEB_VERIFICATION.md`, `docs/rfcs/0008-web-frontend.md`
- Statement: The environment has Node/npm/npx but lacks Lighthouse and a
  Chrome/Chromium binary. RFC 0008's Lighthouse score cannot be claimed.
- Required remediation: Update verification docs and RFC status to name
  Lighthouse as an optional, not-yet-run gate. Include a command and browser
  prerequisite, but do not add it to the mandatory test path.

### F-003 - `kayakgen serve` browser-opening semantics need truthful status wording

- Sources: T-002, O-004
- Severity: medium
- Classification: safe-now
- Files: `docs/WEB_VERIFICATION.md`, `docs/rfcs/0008-web-frontend.md`,
  `docs/rfcs/README.md`
- Statement: RFC 0008 says `kayakgen serve` opens a browser tab, while the
  current CLI intentionally starts a scriptable server and does not auto-open a
  browser.
- Required remediation: Preserve the scriptable default. Either add a small
  opt-in browser-open flag with tests, or update docs/status so the default
  server behavior is not falsely presented as satisfying the original tab-open
  acceptance criterion.

### F-004 - Hosted demo remains deferred; Docker is the current demo artifact

- Sources: T-004, O-003
- Severity: medium
- Classification: safe-now
- Files: `docs/WEB_VERIFICATION.md`, `docs/rfcs/0008-web-frontend.md`,
  `docs/rfcs/README.md`
- Statement: A hosted public demo URL does not exist. The repo has a Dockerfile
  and local/Docker verification path only.
- Required remediation: Document Docker as the reproducible demo artifact and
  keep hosted deployment listed as deferred until a real deployment URL exists.

### F-005 - Browser acceptance must not imply full RFC 0008 or RFC 0013 completion

- Sources: T-005
- Severity: medium
- Classification: safe-now
- Files: `docs/rfcs/0008-web-frontend.md`, `docs/rfcs/0013-pareto-frontier-comparison-ui.md`,
  `docs/rfcs/README.md`
- Statement: Plot tabs, class-selection parity, mobile polish, hosted demo, and
  web comparison UI remain outside this browser acceptance slice.
- Required remediation: Keep RFC/readme status wording precise after
  implementation. Do not mark RFC 0008 fully landed and do not claim RFC 0013
  web comparison views.

## Implementation Guidance

Safe now:

- Add `tests/test_web_browser.py` as an optional Playwright smoke test. It should
  be skipped with a useful reason when `playwright` or a browser binary is not
  available.
- Add optional packaging metadata for browser acceptance tooling, for example a
  `browser` or `web-acceptance` extra that installs the Python Playwright stack
  without making it mandatory.
- Try to install/run the optional browser stack in the current environment. If
  it succeeds, record the exact passing command. If it does not, record the exact
  skip/error and leave the test self-skipping.
- Update `docs/WEB_VERIFICATION.md` with the new browser smoke command,
  Playwright setup, Lighthouse prerequisite, Docker-as-demo status, and hosted
  demo deferral.
- Update RFC 0008, RFC 0013 if needed, and the RFC index so status text matches
  what actually lands.
- Run focused web/browser/CLI tests, the full suite, and `git diff --check`.
  Run Docker smoke and Lighthouse only if the required tooling is available.

Do not implement:

- A hosted public demo without an actual deployment URL.
- Mandatory Playwright/Lighthouse dependencies in the base install.
- A Trame replacement, UI redesign, plot tabs, or web comparison views.
- A default `kayakgen serve` browser auto-open behavior that breaks Docker/CI
  scripting.
