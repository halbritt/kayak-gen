Read `SOURCES.md`. Produce
`striatum/0034-watertight-volume-mesh-handoff/domain/REVIEW_DOMAIN.md`.

Use the maximal number of useful sub-agents or parallel helpers for independent
domain checks. Keep helpers read-only. Do not edit product code, Striatum
state, or non-artifact files. Do not add `author:`, byline, or
`Co-Authored-By:` metadata.

Verdict semantics: this is a pre-implementation review for a queued RFC slice.
Use `accept_with_findings` for implementable code, test, docs, or evidence gaps,
including "not implemented yet" findings. Use `needs_revision` only when the
RFC/workflow scaffold is internally contradictory, missing required context, or
unsafe/impossible to send to ledger without an RFC/workflow correction first.

Focus on generated-body readiness, self-intersection blockers, volume-mesh
evidence, profile-scoped `cfd_ready` semantics, and fixture boundaries.
