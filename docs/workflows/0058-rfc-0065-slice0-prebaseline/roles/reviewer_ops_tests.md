# Role: Reviewer — Tests and operational behaviour

Verify:

- The capture runs at all three viewports (1440×900, 1024×768, ≤960 px) and the
  3D `VtkRemoteView` region (`geometry-vtk-view` / `.kg-vtk-viewport`) is masked
  out of the pixel comparison (not merely cropped by luck).
- The compare helper is deterministic and **advisory in Slice 0** — a mismatch
  reports actual + diff artifacts, it is not yet a hard failure; missing
  Playwright/Chromium is a SKIP, matching the existing profile.
- `--update-visual-baselines` cleanly (re)writes the baselines; the committed
  PNGs are the current shell and reasonable in size; the
  `tests/visual_baselines/README.md` records the canonical env + regen command.
- The existing behavioural browser-acceptance checks (nonblank 3D, Share reload,
  STL bytes, console / page-error / network cleanliness) still pass.
- No wall-clock-sleep flakiness; no module-level side effects; `git diff --check`
  clean; the rest of the suite (minus env-gated smoke) stays green.

If the baseline looks env-fragile (likely to false-positive on the next slice's
diff), say so and recommend a tolerance/canonical-env path. Findings cite file
paths; use `accept_with_findings` for fixable issues.
