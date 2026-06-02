# Role: Implementer (RFC 0065 Slice 0 — pre-redesign screenshot baseline)

Land Slice 0 of RFC 0065: the screenshot-capture scaffolding + a committed
baseline of today's shell. Single coherent slice, one commit, no integrator.

Deliver, strictly inside the write scope:

- Screenshot capture in the browser-acceptance profile (`tests/test_web_browser.py`
  or a new `tests/web_visual.py` imported by it) at 1440×900, 1024×768, and a
  ≤960 px width, **masking the `geometry-vtk-view` / `.kg-vtk-viewport` 3D
  region** (S0-D1/S0-D2). Reuse the existing settle + nonblank-3D waits.
- A compare-with-tolerance helper (current vs committed baseline, masked region
  excluded) that writes actual + diff PNGs on mismatch (S0-D4). In Slice 0 this
  is **advisory** (SKIP without Playwright/Chromium; a mismatch is reported, not
  a hard failure). Add an `--update-visual-baselines` flag (in `tests/conftest.py`)
  that (re)writes the baselines.
- Committed PNG baselines under `tests/visual_baselines/<viewport>.png` of the
  **current** shell, plus `tests/visual_baselines/README.md` documenting the
  canonical render env (this host's OS + Chromium build) and the regeneration
  command (S0-D3).
- A `CHANGELOG.md` entry.

Hard invariants (S0-D5): **no `kayakgen/ui/` source change**, no `data-testid` /
`kg-*` rename, no `CHIP_*` / caption / claim-state change, RFC 0032 boundary
intact. The baseline is of the current (pre-redesign) shell. Do not touch
`docs/USER_GUIDE.md` or `docs/WEB_VERIFICATION.md` (S0-D6).

If deterministic full-shell capture proves too flaky in this env (font hinting /
AA), record that finding precisely and fall back to the most stable capture you
can commit (e.g. a tighter masked crop or a documented higher tolerance) rather
than committing a baseline that will false-positive on every Slice 2 diff —
escalate the tolerance/canonical-env choice to the operator via the patch
summary.

Run the browser-acceptance profile to prove the capture works and the existing
behavioural checks stay green. Publish the patch summary with the exact byline:
files changed, the capture/compare tests added, the exact capture invocation, the
committed baseline list + their canonical env, and any flake/tolerance escalation.
