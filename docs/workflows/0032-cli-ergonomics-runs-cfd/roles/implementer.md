# Role: Implementer

Land R4 (runs CLI header + filter docs) and R5 (CFD CLI polish) per
`docs/audits/2026-05-22-code-doc-audit/REMEDIATION_PLAN.md`. Stay
inside the packet's write scope.

This is a small, additive ergonomics packet. The hard contracts:

- Default output of `kayakgen runs list` and `kayakgen runs jobs`
  stays byte-identical (the `--header` flag is opt-in).
- No new claim-state literal, safety claim, or readiness vocabulary
  is introduced — only operator-facing help text and one appended
  line each on two existing CLI surfaces.
- The appended `mesh-evidence` and `cfd prepare` lines are verbatim
  per the implement prompt; do not paraphrase.
- The filter-key list documented in `--filter` help and in
  `docs/USER_GUIDE.md` enumerates only keys the implementation
  actually honors. If unknown keys are silently dropped, document
  that — do not invent restrictions.

Use sub-agents for parallel reading of `runs_cli.py`,
`artifact_store.py`, and `cli/main.py` if helpful. Run focused tests
before publishing.

Publish the required patch summary at
`docs/audits/2026-05-22-code-doc-audit/follow-ups/0032/PATCH_SUMMARY.md`
with the exact filter-key list, the exact appended lines, the file
list, and the pytest pass/fail counts.
