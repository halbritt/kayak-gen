Read `docs/workflows/0048-successor-rfc-backlog/SOURCES.md` first.

Draft two proposed successor RFCs, and only those RFC files:

- `docs/rfcs/0040-closed-volume-solver-readiness-roadmap.md`
- `docs/rfcs/0041-real-cfd-adapter-successor.md`

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent source analysis, dependency mapping, RFC
drafting, and artifact drafting, but keep one agent responsible for final
integration of this job's files.

Source scope:

- Existing closed-volume and solver dependency spine described in
  `docs/rfcs/README.md` and `docs/workflows/0018-deferred-backlog/QUEUE.md`.
- Existing RFCs 0016, 0017, 0023, 0026, and related landed safe slices.
- The named remaining backlog item: real CFD adapter.
- The named dependency work: related closed-volume/solver readiness needed
  before real solver and watertight/`cfd_ready` claims can advance.

Constraints:

- Do not implement runtime behavior.
- Do not edit `kayakgen/` or `tests/`.
- Do not update `docs/rfcs/README.md`; the integration job owns the index.
- Do not claim OpenFOAM/SU2 execution, production volume meshing, calibrated
  CFD, final prediction, or watertight readiness unless the RFC clearly
  identifies the missing evidence and acceptance gate.
- Do not add bylines or co-author trailers unless Striatum supplies an exact
  expected author line in the packet.

Publish a synthesis artifact at
`striatum/0048-successor-rfc-backlog/rfc_geometry_solver/RFC_SCOPE_GEOMETRY_SOLVER.md`
with Striatum `synthesis` front matter and a concise summary of files changed
and open questions.
