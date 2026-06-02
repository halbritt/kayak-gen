# Implementation Prompt

Read the packet objective, write scope, context docs, and:

- `docs/rfcs/0065-ui-polish-redesign.md` — §5 and the "Slice 4 observable"
  Acceptance Criteria + the mandatory-vs-optional gate table.
- `docs/workflows/0061-rfc-0065-slice4-visual-regression/SLICE_4_DECISIONS.md` —
  the affirmed Slice 4 decisions (D1–D8); these are your spec.
- `tests/test_web_browser.py` (the Slice 0 `test_web_workspace_visual_baseline`,
  the VTK mask, `--update-visual-baselines`, the retained behavioural checks),
  `tests/visual_baselines/README.md`, `kayakgen/ui/theme.py` (`CONTRAST_MANIFEST`,
  `--state-focus-ring`), `docs/WEB_VERIFICATION.md`, `docs/USER_GUIDE.md`,
  `docs/DECISION_LOG.md` (D047).

Implement Slice 4 only, in this order (D1 first is load-bearing):

1. **Regenerate baselines on the canonical env** (`--update-visual-baselines`) so
   the three committed PNGs capture the post-Slice-2/3 appearance; the VTK region
   stays masked. Treat the PNG change as an explained, reviewed diff (D1).
2. **Flip the compare to a HARD gate** with a documented per-viewport tolerance;
   keep the VTK mask; keep missing Playwright/Chromium a SKIP in optional smoke
   and a HARD FAILURE in the acceptance profile (D2, D3). Make it demonstrably
   fail on an over-tolerance diff.
3. **Add a11y checks** (focus order, visible focus ring from the Slice 1 token,
   hit-target min, `CONTRAST_MANIFEST` contrast); the contrast check stays a
   mandatory pytest gate, the browser checks SKIP/HARD per the matrix; extend
   `CONTRAST_MANIFEST`/`theme.py` only additively; any code fix is minimal and
   token-sourced (D4).
4. **Record Lighthouse Best-Practices ≥ 90** (optional/tool-dependent; not a
   mandatory pytest gate) (D5).
5. **Retain every behavioural check** (nonblank-3D before/after, Share reload,
   STL via `POST /api/stl?part=hull`, console/network cleanliness); add no
   network-allowlist entry without the documented note (D6).
6. **Update docs + ratify D047** (Slice 4 owns this): `docs/WEB_VERIFICATION.md`
   (baseline-update procedure + mandatory-vs-optional table), `docs/USER_GUIDE.md`
   (polish + gate, no new capability language), `docs/DECISION_LOG.md` (D047
   `proposed` → `accepted` recording the tolerance + in-repo PNG storage),
   `CHANGELOG.md` (D8).

Hard invariants: claim line byte-stable (no `CHIP_*`/caption change, no chip
recoloured, no raw result baked into a confident treatment) (D7); RFC 0032
boundary intact (no new route/claim/readiness/accepted_uses literal, no analysis
surface); the docs introduce no new capability/availability/no-go language;
preserve the Slice 2/3 region/status/collapse/first-viewport contract and
empty/loading/error hooks.

The browser-acceptance / baseline-regeneration runs are long — codex self-
heartbeats, but keep them progressing. Publish the patch summary with the exact
Striatum byline; enumerate (a) the regenerated baselines and the explained diff,
(b) the chosen tolerance + how the hard compare was verified to fail on an
over-tolerance diff, (c) the a11y checks added + any minimal token-sourced code
fix, (d) the Lighthouse score recorded, (e) the docs edits + the D047 ratification,
and (f) the targeted + acceptance-profile test invocations proving the slice green.
