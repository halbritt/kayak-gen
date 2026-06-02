# Implementation Prompt

Read the packet objective, write scope, context docs, and:

- `docs/rfcs/0065-ui-polish-redesign.md` — the Slice 0 line in the Implementation
  Path and §5 (the visual-regression harness this slice scaffolds).
- `docs/workflows/0058-rfc-0065-slice0-prebaseline/SLICE_0_DECISIONS.md`
  (S0-D1…S0-D6) — your spec.
- `tests/test_web_browser.py` (the browser-acceptance profile, the settle /
  nonblank-3D waits, the `geometry-vtk-view` hook) and `tests/conftest.py`
  (the `--browser-acceptance` flag).

Implement Slice 0 only:

- Add screenshot capture at 1440×900, 1024×768, and a ≤960 px width, masking the
  3D `VtkRemoteView` region (S0-D1/S0-D2).
- Add a compare-with-tolerance helper (current vs committed baseline, masked
  region excluded) that writes actual + diff PNGs on mismatch — **advisory** in
  Slice 0 (SKIP without Playwright/Chromium; mismatch reports, not a hard
  failure) (S0-D4). Add `--update-visual-baselines` to `tests/conftest.py`.
- Capture and commit the current shell's baselines under
  `tests/visual_baselines/<viewport>.png` + a `README.md` with the canonical env
  + regen command (S0-D3).
- Add a `CHANGELOG.md` entry.

Hard invariants (S0-D5): no `kayakgen/ui/` source change; no hook rename; no
`CHIP_*` / caption / claim-state change; the baseline is of the current shell;
do not touch `USER_GUIDE.md` / `WEB_VERIFICATION.md` (S0-D6).

Prove it: run `pytest tests/test_web_browser.py -m browser_acceptance
--browser-acceptance -q` and confirm capture works + the existing behavioural
checks stay green. If deterministic capture is too flaky (font hinting / AA),
record it precisely and escalate the tolerance/canonical-env choice in the patch
summary rather than committing a baseline that false-positives on every diff.
Heartbeat your lease during long Playwright runs. Publish the patch summary with
the exact byline: files changed, capture/compare tests, the capture invocation,
the committed baselines + their canonical env, and any flake/tolerance escalation.
