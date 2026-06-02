# Role: Reviewer — Tests, determinism, and the gate posture

Verify:

- The regenerated baselines (`1440x900`/`1024x768`/`960x720`) match the current
  post-redesign render so the HARD compare passes within the documented tolerance,
  AND the compare actually FAILS on an injected over-tolerance diff (not a no-op);
  the VTK region is masked.
- Missing Playwright/Chromium SKIPs the optional smoke and HARD-FAILS the
  acceptance profile — for the screenshot AND the a11y checks.
- The a11y checks (focus order, visible focus ring, hit-target min, contrast) are
  deterministic and assert real conditions; the `CONTRAST_MANIFEST` pytest gate
  passes in BOTH palettes and any new pair is additive.
- The retained behavioural checks still pass (nonblank-3D before/after, Share
  reload round-trip, STL via `POST /api/stl?part=hull`, console/network
  cleanliness); the Lighthouse result is recorded, not a hard pytest gate.
- The full repo suite (minus env-gated smoke) is green except the known
  pre-existing NB-2 `tests/test_services_boundaries.py` services→ui
  import-boundary failure (out of scope); `git diff --check` passes; no test
  depends on wall-clock sleeps.

If the canonical browser-acceptance run cannot execute in this lane, run a SHORT
targeted verification, publish the verdict while the lease is warm, THEN run the
longer suite (operator hazard: a single long foreground command expires the
lease). Findings cite file paths. Use `accept_with_findings` for issues the
remediation lane can fix.
