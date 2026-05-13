# Operator report - workflow 0020

Updated: 2026-05-13

## Current state

- User asked to proceed through the structured workflows and keep this report
  updated before each workflow step.
- Workflow 0019 accepted and `main` was fast-forwarded/pushed through
  `d126e3b`.
- Queue item 0020 is `0020-browser-acceptance-demo`: real-browser or equivalent
  smoke coverage, Lighthouse checks only where practical, and truthful
  demo/deployment documentation for RFC 0008.
- Workflow 0017 landed headless web verification and `docs/WEB_VERIFICATION.md`
  but explicitly left browser automation, Lighthouse, and hosted demo acceptance
  open.
- This workflow is being scaffolded from clean `main`.
- Scaffold validation passed:
  `striatum --repo . workflow validate docs/workflows/0020-browser-acceptance-demo/workflow.json`.
- Whitespace validation passed: `git diff --check`.
- Workflow scaffold committed and pushed on `main` as `df77455`.
- Prepared Striatum run `run_bd1e5ad4453a45469b470dd7c2fc5ec2`.
- Confirmed branch `striatum/0020-browser-acceptance-demo` and checked it out.
- Started the run.
- Registered, claimed, and acked review sessions:
  - `review_traceability` as `sess_2d8a59ef4a24469aa0591a925ab73bbc`;
  - `review_browser` as `sess_ae97363c090a43d591499c84c8609e58`;
  - `review_ops` as `sess_1dc2fd324bae4b7c89e08977e7361c5d`.
- Wrote and submitted three review artifacts with `accept_with_findings`
  verdicts:
  - traceability `art_a8136670bfa04b0185a7c98cfa2e14b6`;
  - browser `art_0b7519b5bd99461eb15d609386d5b12c`;
  - ops `art_5e6580c2348e4afab127cc21b955b1e5`.
- Claimed and acked `findings_ledger` as
  `sess_66b92a489cdd48ce94116bca52d3f7b4`.
- Wrote findings ledger at
  `striatum/0020-browser-acceptance-demo/ledger/FINDINGS.md`.
- Ledger artifact was accepted as
  `art_daa7459e3a314d4199d64dbf07fade84`.
- Claimed and acked `implement_findings` as
  `sess_94a20386b789451898c71dbf76db81f6`.
- Attempted to spawn a documentation/status sub-agent for a disjoint write
  scope, but the active sub-agent limit was already reached; implementation is
  local.
- Implementation added:
  - optional `browser` extra with Playwright;
  - `tests/test_web_browser.py` real-browser smoke for `kayakgen serve`;
  - web verification docs for browser setup, Lighthouse, Docker demo artifact,
    and hosted-demo deferral;
  - RFC 0008/RFC index status updates to `partial browser-smoke`.
- Verification passed:
  - `pip install -e ".[web,browser]" --quiet`;
  - `python -m playwright install chromium`;
  - `.venv/bin/python -m pytest tests/test_web_browser.py -q` -> 1 passed;
  - Lighthouse via `npx --yes lighthouse@latest` with Playwright Chromium ->
    Best Practices 92, with console audit still reporting a Trame `/paraview/`
    405 network log;
  - `.venv/bin/python -m pytest tests/test_web.py tests/test_cli.py tests/test_web_browser.py -q`
    -> 24 passed;
  - `.venv/bin/python -m pytest -q` -> 134 passed;
  - `docker build -t kayakgen-web-verify-0020 .` -> passed;
  - container HTTP smoke on port 18083 returned 200 and a 1376-byte app response;
  - `git diff --check` -> clean.
- `striatum --repo . doctor` -> ok true, zero problems.
- `ruff` was not run successfully because it is not installed in the current
  virtualenv.
- Wrote implementation artifact at
  `striatum/0020-browser-acceptance-demo/implementation/PATCH_SUMMARY.md`.
- Implementation artifact was accepted as
  `art_fce4d5f69cae412187588c0a70d9fb9e`.
- Claimed and acked `final_review` as
  `sess_65ef430f487448adb70bc1ea0d9035b6`.
- Wrote final review artifact at
  `striatum/0020-browser-acceptance-demo/final/FINAL_REVIEW.md`.
- Final review accepted the workflow with findings:
  - artifact `art_cefe014421dc4cdd862487b9b2b347a7`;
  - verdict `verdict_f002e1d8550f4b4c8d093bed9f450efc`;
  - run state `completed`.

## Findings recorded

- Initial review findings: no automated browser test path, `kayakgen serve`
  wording conflict with RFC 0008, Lighthouse unavailable, hosted demo not
  deployed, and web parity/comparison UI still partial.
- Implementation leaves one explicit residual: Lighthouse score threshold
  passed, but console-clean Lighthouse acceptance remains partial due to the
  recorded Trame `/paraview/` 405 network log.

## Next action

- Commit workflow 0020, push the branch, fast-forward `main`, then continue to
  the next queued workflow.
