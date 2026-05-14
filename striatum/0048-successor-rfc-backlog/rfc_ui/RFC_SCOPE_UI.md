---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: rfc-scoper-codex-gpt-5.5-007
kind: synthesis
logical_name: rfc_scope_ui
run: run_c1de081e76f14cd1a81194e306338ac2
session: sess_137fa37d5e2e4e13a31815ca199d4ce7
job: job_run_c1de081e76f14cd1a81194e306338ac2_rfc_scope_ui
lease: lease_b3afc42147bc4b93beeefc65ffc6ed0e
date: 2026-05-14

# RFC Scope UI

## Files Changed

Drafted four proposed UI successor RFCs from workflow 0047 final-review
findings:

- `docs/rfcs/0036-trame-seed-listener-proof.md` - requires either a browser
  proof for the retained Trame same-seed preset listener branch or removal of
  the branch as dead code.
- `docs/rfcs/0037-export-row-schema-consolidation.md` - collapses
  export-row guidance copy to one canonical `subtitle` field while preserving
  shipped visible subtitles.
- `docs/rfcs/0038-export-menu-disabled-copy-polish.md` - proposes replacing
  `Mesh package...` with `Mesh package (CLI only)` while keeping the row
  disabled/unavailable in the browser.
- `docs/rfcs/0039-web-snapshot-schema-unification.md` - scopes a future shared
  web-state schema/alias source for snapshot keys and CFD status/payload
  aliases without changing route payload shapes.

No runtime behavior was implemented. The RFC index was not updated; that remains
owned by the integration job.

## Open Questions

- RFC 0036: can the same-seed Trame event sequence be reproduced in browser
  automation, or should the branch be removed?
- RFC 0037: should any compatibility read model expose a derived `description`
  property, or can all consumers use `subtitle` directly?
- RFC 0038: is `Mesh package (CLI only)` the preferred final label, or should
  the label be shorter with CLI-only guidance left to adjacent copy?
- RFC 0039: should the shared schema be a plain constant/alias grouping or a
  typed value object in `kayakgen/ui/web/state.py`?
