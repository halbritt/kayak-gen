# RFC 0065 Slice 0 — Pre-redesign Screenshot Baseline: Affirmed Decisions

RFC-derived spec for Slice 0 (RFC 0065 Implementation Path, "Slice 0 —
Pre-redesign baseline"). Slice 0 lands the screenshot-capture scaffolding and a
committed baseline of **today's** (pre-redesign) shell, so the Slice 2/3 reflow
produces reviewable visual diffs. **No appearance, layout, or claim change.**

Operator scope decisions for this slice (2026-06-02): proceed to Slice 2 with a
Slice 0 baseline first; dark/light stays OS-preference-only (no toggle); mobile
keeps the conservative ≤960 px restyle-collapse-only posture.

## S0-D1 — Capture scaffolding in the browser-acceptance profile

Add Playwright/Chromium screenshot capture to the RFC 0032 browser-acceptance
profile (`tests/test_web_browser.py`, run with
`-m browser_acceptance --browser-acceptance`). Capture the three-region
workspace at representative viewports — at minimum **1440×900** (desktop-first),
**1024×768** (intermediate), and a **≤960 px** collapsed width — after the page
has settled (reuse the existing settle/`_assert_nonblank_3d` waits).

## S0-D2 — Mask the nondeterministic 3D region

Before each capture, **mask the `VtkRemoteView` region** (the
`data-testid="geometry-vtk-view"` / `.kg-vtk-viewport` canvas) — overlay it with
a solid fill or exclude its bounding box from the diff — so the live 3D frame
never enters the pixel comparison. Its liveness stays asserted separately by the
existing nonblank-3D check.

## S0-D3 — Committed in-repo PNG baselines (D047)

Commit PNG baselines of today's shell **in-repo** (D047: committed baselines +
tolerance), under `tests/visual_baselines/<viewport>.png`. Record the canonical
render environment (this dev host's OS + Chromium build) and a regeneration
command (e.g. `pytest … --update-visual-baselines`) in a
`tests/visual_baselines/README.md`. **Provisional:** the exact per-viewport pixel
tolerance and canonical-env hardening (font-hinting is the usual flake source)
are refined in **Slice 4**; Slice 0 commits the baseline + a permissive,
documented tolerance and the regeneration path.

## S0-D4 — Compare scaffold is advisory in Slice 0, a hard gate in Slice 4

Land a compare-with-tolerance helper (current capture vs committed baseline, 3D
region masked) that, on mismatch, writes the actual + diff PNGs to a test-output
dir. In Slice 0 this is **advisory** (SKIP if Playwright/Chromium absent; a
mismatch is reported, not yet a hard failure) so Slice 2/3 diffs are reviewable;
the **HARD-FAILURE gate** lands in Slice 4. The existing behavioural
browser-acceptance checks (nonblank 3D, Share reload, STL bytes, console/network
cleanliness) stay green and unchanged.

## S0-D5 — No appearance / layout / claim change

Slice 0 only **adds** test infrastructure and baseline fixtures. No
`kayakgen/ui/` source change, no `data-testid` / `kg-*` hook rename, no
`CHIP_*` / caption / claim-state change, RFC 0032 boundary intact. The captured
baseline is of the **current** shell.

## S0-D6 — Docs footprint

`CHANGELOG.md` + the new `tests/visual_baselines/README.md` (canonical env +
regen command) only. Do **not** touch `docs/USER_GUIDE.md` or
`docs/WEB_VERIFICATION.md` — the harness/baseline-update procedure those docs
will describe lands in **Slice 4**. DECISION_LOG D047 is **not** ratified here
(Slice 4 ratifies it in practice).

## Out of scope (later slices)

Shell layout & information-hierarchy reflow (Slice 2); control + empty/loading/
error states (Slice 3); the HARD-FAILURE visual-regression gate, focus-order /
visible-ring / hit-target / contrast a11y checks, Lighthouse, and the
`WEB_VERIFICATION.md` baseline-update procedure (Slice 4); desktop polish
(Slice 5, deferred).
