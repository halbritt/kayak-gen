# RFC 0055: Design Report Export

Status: landed kayakgen design-report + jinja2 template + forbidden-copy scan + optional [report] PDF extras
Date: 2026-05-16
Context: Phase 8 item 6 of
`ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`. Today's outputs
are atomic JSON files — `EvaluationResult`, `StabilityResult`,
mesh manifests, comparison reports. A designer wanting to share a
single "this is my hull" artifact must zip a directory by hand or
screenshot individual UI panels.

## Problem

A design report is the cross-section of every other artifact: the
hull parameters, rendered views, hydrostatics, stability,
resistance warnings, mesh / readiness status, comparison position
(when run in a sweep / search), and the claim-state explanations
that govern how each number may be read. The pieces all exist; no
command stitches them.

## Goals

- Land a `kayakgen design-report <hull.json> --out report.html`
  command that produces a single self-contained HTML file (CSS
  inline, images embedded) plus a sibling `report.pdf` via headless
  rendering (optional).
- Preserve every no-claim boundary on the rendered surface (no
  safe / seaworthy / validated / calibrated / final-prediction /
  design-fitness wording).
- Embed artifact references + SHA-256 hashes so a recipient can
  re-derive every number.
- Reuse existing evaluators; the report command is a renderer, not a
  new evaluator.

## Non-Goals

- No new claim state, no new evaluator.
- No multi-hull report (that's the comparison report).
- No interactive HTML (the artifact is a static snapshot).
- No hosted publishing.

## Proposal

### Report sections

1. **Header**: hull name (if any), `Hull.record_hash()`,
   `Hull.design_hash()` (RFC 0049), kayakgen version pin, timestamp.
2. **Parameters**: every Hull field with its value, units, and a
   sourced note (default, class preset, operator override).
3. **Rendered views**: hull + deck 3D preview (PNG embedded),
   sheer plan, cross-section, plan view.
4. **Hydrostatics**: every metric from
   `kayakgen.eval.hydrostatics.evaluate`, with the registry's
   `display_format` (Phase 5).
5. **Stability**: upright and trim equilibrium results; opt-in
   high-angle GZ block (display-only with all RFC 0024 warnings
   adjacent).
6. **Resistance**: speed sweep curve with the
   `uncalibrated_comparative` warning prominent.
7. **Mesh / readiness status**: per-part diagnostics + the
   readiness label.
8. **Comparison position** (optional, when a sweep/search run is
   referenced via `--from-run <run>`): the candidate's rank on the
   Pareto frontier, with the display-only high-angle GZ rows
   adjacent if present.
9. **Artifact refs**: a table of every output the report cites,
   with relative path + SHA-256.
10. **Claim-state explanations**: a section that names every
    claim state on every number in the report and links back to the
    relevant decision (D006/D012/D014/D018/D022/D025/D026/D027/D028).

### CLI surface

```bash
kayakgen design-report hull.json --out report.html
kayakgen design-report hull.json --out report.html --pdf
kayakgen design-report hull.json --out report.html --from-run runs/demo
```

### No-claim enforcement

The renderer scans the assembled report text against the same
forbidden-copy regex used by `tests/test_desktop_layout.py` and
`tests/test_web_read_models.py`. The forbidden tokens are
`safe`, `seaworthy`, `validated`, `calibrated`,
`final prediction`, `design fitness`. The test scrubs the explicit
negated forms (`unvalidated_*`, `uncalibrated_*`) before scanning.

## Acceptance Criteria

- `kayakgen design-report default.json --out report.html` writes a
  self-contained HTML file ≤ 5 MB on a default hull.
- The file passes the forbidden-copy regression on the desktop
  test surface pattern.
- `--from-run runs/demo` produces a comparison section when the
  hull's design hash matches a candidate in the run; otherwise an
  honest "this hull was not in the referenced run" notice.
- `--pdf` produces a PDF when wkhtmltopdf or weasyprint is
  installed; otherwise an honest "PDF dependency not available"
  message.
- Default kayakgen behavior unchanged elsewhere.

## Open Questions

- HTML rendering library: jinja2 (pure-Python, well-known) or a
  hand-rolled string template? Probably jinja2 as an optional dep.
- PDF: weasyprint or wkhtmltopdf? Both are heavy installs; gating
  the PDF behind an optional `report` extras group keeps the core
  install thin.
- Should the report embed the STL preview as a small PNG or as a
  link to an external file? Embedded keeps it self-contained;
  external keeps the HTML small.

## Implementation Path

1. Land `kayakgen/services/design_report.py` with the section
   assemblers (reuse services from Phase 3D wherever possible).
2. Land the jinja2 template under
   `kayakgen/services/design_report/templates/`.
3. Add the `kayakgen design-report` Typer subcommand.
4. Land forbidden-copy regression on the assembled report text.
5. Add `jinja2 >= 3` to a new `kayakgen[report]` extras group.
6. Update `docs/USER_GUIDE.md`.

## Domain Modeling

`design-report` is a *renderer* (read-model) over the existing Hull
aggregate plus the existing evaluator results. It introduces no new
aggregate, no value object beyond a small `DesignReportRequest`,
and no domain event. The HTML/PDF artifacts are durable per the
existing artifact catalogue in `docs/SPEC.md`.
