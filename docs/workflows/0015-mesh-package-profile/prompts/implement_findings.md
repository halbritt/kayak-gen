Implement the safe-now findings from
`striatum/0015-mesh-package-profile/ledger/FINDINGS.md`.

Write `striatum/0015-mesh-package-profile/implementation/PATCH_SUMMARY.md`
with:

- author line: `author: operator [self-declared: operator-implementer]`
- files changed
- findings addressed
- verification commands and results

Implementation constraints:

- Prefer Codex for implementation.
- Use sub-agents where useful for bounded, parallel, disjoint work.
- Add a manifest/package module near `kayakgen/eval/mesh_diagnostics.py` unless
  the ledger justifies another boundary.
- Add `kayakgen mesh-package hull.json --out mesh-package/`.
- Write manifest, hull JSON, quality reports, and STL surfaces.
- Attach or expose the first open wetted-surface profile without promoting
  current surfaces to watertight `cfd_ready`.
- Do not add solver dispatch, OpenFOAM/SU2 integration, volume meshing, or new
  dependencies.
- Run focused tests, the full suite, and `git diff --check`.
