Read `docs/workflows/0048-successor-rfc-backlog/SOURCES.md` first.

Draft four proposed UI successor RFCs, and only those RFC files:

- `docs/rfcs/0036-trame-seed-listener-proof.md`
- `docs/rfcs/0037-export-row-schema-consolidation.md`
- `docs/rfcs/0038-export-menu-disabled-copy-polish.md`
- `docs/rfcs/0039-web-snapshot-schema-unification.md`

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent source analysis, RFC drafting, acceptance
criteria, and artifact drafting, but keep one agent responsible for final
integration of this job's files.

Source scope:

- Workflow 0047 final-review finding: stronger Trame browser proof or removal
  for the retained `_state_matches_preset_seed` / preset seed-listener branch.
- Workflow 0047 final-review finding: export-row `subtitle` vs `description`
  schema consolidation.
- Workflow 0047 final-review finding: optional disabled export row copy polish
  around `Mesh package...` ellipsis.
- Workflow 0047 final-review finding: future snapshot-schema unification.

Constraints:

- Do not implement runtime behavior.
- Do not edit `kayakgen/` or `tests/`.
- Do not update `docs/rfcs/README.md`; the integration job owns the index.
- Keep each RFC proposed, narrow, testable, and explicit about non-goals.
- Do not add bylines or co-author trailers unless Striatum supplies an exact
  expected author line in the packet.

Publish a synthesis artifact at
`striatum/0048-successor-rfc-backlog/rfc_ui/RFC_SCOPE_UI.md` with Striatum
`synthesis` front matter and a concise summary of files changed and open
questions.
