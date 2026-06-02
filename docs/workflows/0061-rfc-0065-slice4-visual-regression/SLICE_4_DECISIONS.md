# RFC 0065 Slice 4 — Visual-Regression Hard Gate + a11y + Lighthouse: Affirmed Decisions

These are the RFC-derived, operator-affirmed decisions that Slice 4 implements.
They are the authoritative spec for the implementer and the yardstick for every
reviewer. Source: `docs/rfcs/0065-ui-polish-redesign.md` §5 ("Visual-regression
harness in the browser-acceptance profile") + the "Slice 4 observable" Acceptance
Criteria, and DECISION_LOG row D047.

Slice 4 turns the Slice 0 advisory screenshot compare into a hard verification
gate, adds accessibility checks, records Lighthouse, updates the verification +
user docs, and ratifies D047. It is the **final core slice of RFC 0065**. It is
the **only** slice that touches `docs/USER_GUIDE.md`, `docs/WEB_VERIFICATION.md`,
and `docs/DECISION_LOG.md`. Each decision below is a hard gate.

## D1 — Regenerate baselines on the canonical env first, as an explained diff

Before flipping the compare to hard, regenerate the three committed PNG baselines
under `tests/visual_baselines/` (`1440x900`, `1024x768`, `960x720`) on **this
canonical render environment** (this host's Chromium build) via the existing
`--update-visual-baselines` path, so they capture the **post-Slice-2/3
appearance** (the currently committed PNGs are the pre-redesign Slice 0 capture
and will mismatch). The committed PNG change is a **reviewed, explained diff** —
the patch summary states what visibly changed (the Slice 2 reflow + Slice 3
states) and why — not unexplained binary churn. The 3D `VtkRemoteView` region
stays masked out of the capture/diff.

## D2 — Flip the visual compare from advisory to a HARD gate

In `tests/test_web_browser.py`, the screenshot compare in the browser-acceptance
profile becomes a **HARD FAILURE** when a viewport's pixel difference exceeds the
documented tolerance (D3). The VTK mask is retained. Missing Playwright/Chromium
stays a **SKIP** in the optional smoke and a **HARD FAILURE** in the acceptance
profile — unchanged from today and extended to the screenshot + a11y checks.

## D3 — Documented per-viewport pixel-difference tolerance

The compare uses a documented per-viewport tolerance that absorbs anti-aliasing /
font-hinting jitter without hiding real regressions (e.g. a bounded fraction of
differing pixels and/or a bounded per-channel delta). The exact tolerance and the
in-repo PNG storage choice are recorded in `docs/WEB_VERIFICATION.md` and the D047
ratification. The compare must demonstrably FAIL on an over-tolerance diff (not a
no-op).

## D4 — Accessibility checks (HARD in the acceptance profile)

Add to the acceptance profile: deterministic focus order across the shell; a
**visible focus ring** sourced from the Slice 1 `--state-focus-ring` token on the
focused control; a minimum hit-target size on interactive controls; and contrast
satisfying `CONTRAST_MANIFEST`. The `CONTRAST_MANIFEST` contrast check stays a
**mandatory pytest gate** that needs no browser and passes in both palettes; the
browser a11y checks SKIP in the optional smoke and HARD-FAIL in the acceptance
profile. `CONTRAST_MANIFEST` / `theme.py` are extended only **additively** if a
new a11y pair is needed. Any code fix to pass an a11y assertion is **minimal and
token-sourced** (e.g. a control gaining the focus ring or meeting the hit-target
min via existing `DENSITY` tokens) — not a layout redesign.

## D5 — Lighthouse Best-Practices ≥ 90 (recorded, not a mandatory pytest gate)

A Lighthouse Best-Practices ≥ 90 result is recorded (optional, tool-dependent:
Lighthouse + Chromium), matching how `WEB_VERIFICATION.md` frames it today
(workflow 0020 recorded 92). It is **not** a mandatory pytest gate.

## D6 — Retain every existing behavioural acceptance check

The behavioural checks the profile already makes must still pass after the
restyle: nonblank-3D **before and after** a representative control mutation;
Share-URL reload round-trip (same `Hull.hash()`); STL bytes via the browser-facing
API path (`POST /api/stl?part=hull`); and console / page-error / network
cleanliness. No new network-allowlist entry is added without the documented URL
pattern, expected status, rationale, and removal-condition note the profile
already requires.

## D7 — Claim line + RFC 0032 boundary intact

`CHIP_SPECS` / `CHIP_LABELS` / `CHIP_CLASSES` and every persistent caption are
byte-identical; no chip is recoloured; the regenerated screenshots bake no
unvalidated/raw result into a confident/validated/calibrated treatment. No new
REST route, no new `claim_state` / `Readiness` / `accepted_uses` literal, no new
evaluator or analysis surface; the RFC 0032 web-analysis boundary text in the docs
is unchanged. The RFC 0033 §8 no-go list stays absent from rendered output and
from the new docs prose.

## D8 — Docs updated + D047 ratified (Slice 4 owns this)

- `docs/WEB_VERIFICATION.md`: add the baseline-update procedure (the canonical
  OS + Chromium build, the regeneration command, the reviewed-diff expectation)
  and the mandatory-vs-optional gate table (screenshot regression / focus
  order-ring-hit-target / contrast / Lighthouse).
- `docs/USER_GUIDE.md`: describe the polish behaviour and the new verification
  gate (presentation only — no new capability/availability language).
- `docs/DECISION_LOG.md`: ratify **D047** (status `proposed` → `accepted`),
  recording the chosen per-viewport tolerance and the in-repo PNG storage choice.
- `CHANGELOG.md`: a Slice 4 entry.

The Slice 2/3 region/status/collapse/first-viewport contract and the
empty/loading/error hooks are preserved.

## Out of scope

Desktop visual polish (Slice 5, deferred, operator-gated per D009 / D021); any new
analysis capability, route, or claim literal; a hosted visual-diff SaaS (D047
chose committed PNG baselines). The pre-existing NB-2
`tests/test_services_boundaries.py` services→ui import-boundary failure is **out
of scope** (a separate hygiene follow-up). With Slice 4 landed, RFC 0065's core
(Slices 1–4) is complete.
