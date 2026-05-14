Read `docs/workflows/0047-ui-follow-up-cleanup/SOURCES.md`, especially the
workflow 0045 and 0046 final-review artifacts.

Draft `docs/rfcs/0035-ui-follow-up-cleanup.md` as a proposed successor RFC
that is limited to cleanup findings already recorded by workflows 0045 and
0046. Also update `docs/rfcs/README.md`, this workflow's
`OPERATOR_REPORT.md`, and `CHANGELOG.md` as needed for the RFC/scaffold
record.

Do not implement runtime behavior. Do not change `kayakgen/` or `tests/`.

The RFC should cover only reviewable UI cleanup and maintenance items such as:

- preset and validity-badge semantics left by workflow 0045 final review;
- likely dead or duplicated web UI state/export row logic left by workflow
  0045 final review;
- the workflow 0046 final-review follow-ups around slider-label CSS, wrapper
  accessibility semantics, and desktop slider fallback maintenance;
- focused tests and docs/changelog updates.

Explicitly defer desktop parity rewrite, new backend capabilities, hosted CFD,
real solver adapters, calibrated drag, final prediction, high-angle `GZ`,
web-side mesh-package authoring beyond existing safe entries, and watertight
`cfd_ready` promotion.

Use concise artifact front matter accepted by Striatum for a `synthesis`
artifact. Do not add bylines or co-author trailers unless Striatum supplies an
exact expected author line in the packet. Record what changed in
`striatum/0047-ui-follow-up-cleanup/rfc_scope/RFC_SCOPE.md`.
