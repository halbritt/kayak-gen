# Draft Prompt - gate altitude + verified reads

Read the packet objective, role file, SOURCES.md, the 0066 operator report
pre-merge findings, REVIEW.md, D050, and the named source files.

Implement in packet order:

1. Add the explicit-env in-suite skip pin in `tests/conftest.py`. Export
   `KAYAKGEN_ENFORCE_SKIP_PIN=1` from both gates. Derive expected skips from
   OpenFOAM opt-in env, preserve partial pytest legitimacy, guard script
   `cd`, anchor summary parsing, and harden malformed parse output.
2. Adopt verified artifact reads in the named production readers wherever a
   hash-bearing record/ref exists. Record remaining path-only surfaces.
3. Harden `FilesystemArtifactStore` for read OSError fallthrough,
   corrupt-sibling fallback, equal-length write-side rehashing,
   relative-path containment, and `ArtifactIntegrityError` export.
4. Add focused regression tests and update docs/changelog/decision log as
   needed.

Gate: focused tests, `ruff check kayakgen tests`, and `scripts/full-gate.sh`.
Check the user-level `~/.local/share/kayakgen/index.sqlite` remains
empty/unchanged.

Publish `striatum/0067-gate-altitude-verified-reads/DRAFT.md` with design
decisions, commits/diffstat, tests run, any remaining legacy read surfaces,
and the gate tail.
