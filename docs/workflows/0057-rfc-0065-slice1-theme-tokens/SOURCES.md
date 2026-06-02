# Sources — Workflow 0057 (RFC 0065 Slice 1)

- `docs/rfcs/0065-ui-polish-redesign.md` — authoritative spec. Slice 1 = §1
  ("Visual system: complete the theme module") + the "Slice 1 observable"
  Acceptance Criteria.
- `docs/rfcs/README.md` — RFC index entry 0065.
- `docs/DECISION_LOG.md` — D047 (committed-baseline visual-regression strategy;
  ratified at Slice 4, **not** here).
- RFC 0033 §6 (theme module = sole colour-literal authority; widened by Slice 1)
  and §8 (no-go claim list).
- `kayakgen/ui/theme.py` — the module Slice 1 extends.
- `tests/test_ui_theme.py` — the orphan-literal lint + contrast-manifest gate.
- `kayakgen/ui/web/app.py`, `kayakgen/ui/web/generate_frontier_view.py` — the two
  modules holding the inline dimension literals to migrate.
- `docs/workflows/0057-rfc-0065-slice1-theme-tokens/SLICE_1_DECISIONS.md` — the
  affirmed Slice 1 decisions (D1–D8).
