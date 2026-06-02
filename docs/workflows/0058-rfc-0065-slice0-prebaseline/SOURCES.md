# Sources — Workflow 0058 (RFC 0065 Slice 0)

- `docs/rfcs/0065-ui-polish-redesign.md` — spec. Slice 0 = Implementation Path
  "Slice 0 — Pre-redesign baseline" + §5 (visual-regression harness, the parts
  Slice 0 scaffolds) + the Acceptance-Criteria masking/viewport notes.
- `docs/DECISION_LOG.md` — D047 (committed screenshot baselines + tolerance;
  ratified in practice at Slice 4, scaffolded here).
- `tests/test_web_browser.py` — the RFC 0032 browser-acceptance profile to extend
  (`_browser_acceptance_required`, the settle/nonblank-3D waits, the
  `geometry-vtk-view` hook to mask).
- `tests/conftest.py` — the `--browser-acceptance` flag registration; add the
  `--update-visual-baselines` flag here.
- `kayakgen/ui/web/app.py` — the shell (`region-params`/`-geometry`/`-review`,
  `kg-vtk-viewport`, the ≤960 px collapse classes) being captured — read-only in
  Slice 0.
- `docs/workflows/0058-rfc-0065-slice0-prebaseline/SLICE_0_DECISIONS.md` — the
  affirmed Slice 0 decisions (S0-D1…S0-D6).
