# Sources — Workflow 0061 (RFC 0065 Slice 4)

- `docs/rfcs/0065-ui-polish-redesign.md` — authoritative spec. Slice 4 = §5
  ("Visual-regression harness in the browser-acceptance profile") + the "Slice 4
  observable" Acceptance Criteria + the mandatory-vs-optional gate table.
- `docs/rfcs/README.md` — RFC index entry 0065.
- `docs/DECISION_LOG.md` — **D047** (committed-baseline visual-regression
  strategy), currently `proposed`; Slice 4 ratifies it (`proposed` → `accepted`).
- `docs/WEB_VERIFICATION.md` — the verification doc Slice 4 extends with the
  baseline-update procedure and the mandatory-vs-optional gate table.
- `docs/USER_GUIDE.md` — updated to describe the polish behaviour + the new gate.
- `tests/test_web_browser.py` — the RFC 0032 browser-acceptance profile
  (`-m browser_acceptance --browser-acceptance`): the Slice 0
  `test_web_workspace_visual_baseline` (3 viewports, VTK-masked, advisory compare,
  `--update-visual-baselines`) Slice 4 flips to hard; plus the retained
  behavioural checks (nonblank-3D, Share reload, STL via `POST /api/stl?part=hull`,
  console/network cleanliness).
- `tests/visual_baselines/` — the committed PNG baselines (regenerated on the
  canonical env in Slice 4) + `README.md`.
- `kayakgen/ui/theme.py` — `CONTRAST_MANIFEST` (extended additively only if a new
  a11y pair is needed) and the `--state-focus-ring` token the visible-ring check
  asserts; `tests/test_ui_theme.py` — `test_contrast_manifest_clears_thresholds`
  (the mandatory contrast pytest gate, light + dark).
- `docs/workflows/0058-rfc-0065-slice0-prebaseline/` — the Slice 0 baseline
  scaffolding Slice 4 builds the hard gate on.
- `docs/workflows/0061-rfc-0065-slice4-visual-regression/SLICE_4_DECISIONS.md` —
  the affirmed Slice 4 decisions (D1–D8).
