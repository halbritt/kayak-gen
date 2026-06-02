# Role: Implementer (RFC 0065 Slice 4 — visual-regression hard gate + a11y + Lighthouse)

Implement Slice 4 of RFC 0065 — the final core slice. Turn the Slice 0 advisory
screenshot compare into a hard verification gate, add accessibility checks, record
Lighthouse, update the verification + user docs, and ratify D047. This is a single
coherent slice landing as one commit.

Deliver, strictly inside the write scope, in order:

1. Regenerate the three committed PNG baselines (`1440x900`/`1024x768`/`960x720`)
   on this canonical env via `--update-visual-baselines` so they capture the
   post-Slice-2/3 appearance; VTK masked; the PNG change is an explained diff (D1).
2. Flip the compare to a HARD FAILURE with a documented per-viewport tolerance;
   keep the VTK mask; keep the SKIP(optional)/HARD(acceptance) posture for missing
   Playwright/Chromium; make it fail on an over-tolerance diff (D2, D3).
3. Add the a11y checks — focus order, visible focus ring from `--state-focus-ring`,
   hit-target min, `CONTRAST_MANIFEST` contrast (mandatory pytest gate, both
   palettes); extend `CONTRAST_MANIFEST`/`theme.py` additively only; a11y code
   fixes minimal + token-sourced (D4).
4. Record Lighthouse Best-Practices ≥ 90 (optional/tool-dependent; not a mandatory
   pytest gate) (D5).
5. Retain every behavioural check (nonblank-3D before/after, Share reload, STL via
   `POST /api/stl?part=hull`, console/network cleanliness); no undocumented
   network-allowlist entry (D6).
6. Update `docs/WEB_VERIFICATION.md` (baseline-update procedure + mandatory-vs-
   optional table), `docs/USER_GUIDE.md` (polish + gate), `docs/DECISION_LOG.md`
   (D047 `proposed` → `accepted`), `CHANGELOG.md` (D8).

Hard invariants: claim line byte-stable; no chip recoloured; no raw result baked
into a confident treatment; RFC 0032 boundary intact (no new route/claim/readiness
literal, no analysis surface); the docs add no new capability/availability/no-go
language; the Slice 2/3 region/status/collapse/first-viewport contract and
empty/loading/error hooks preserved (D7).

The baseline-regeneration and browser-acceptance runs are long; codex
self-heartbeats — keep them progressing. Run the targeted tests, the
`CONTRAST_MANIFEST` gate, the desktop rendered-bbox tests, the browser-acceptance
profile (`-m browser_acceptance --browser-acceptance`), and the full repo suite
(minus the env-gated smoke; NB-2 is pre-existing/out of scope). Publish the patch
summary with the exact byline; enumerate (a) regenerated baselines + explained
diff, (b) the tolerance + how the hard compare was verified to fail on an
over-tolerance diff, (c) a11y checks + any minimal token-sourced fix, (d) the
Lighthouse score, (e) the docs edits + D047 ratification, (f) the test invocations
proving the slice green.
