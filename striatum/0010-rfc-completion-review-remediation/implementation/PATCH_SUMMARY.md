# Patch summary

author: operator
run: run_c772654b565847dfa738ca8b90eb690b
job: implement_findings

## Scope

This implementation round remediated the actionable-now findings from
`ledger/FINDINGS.md` where the repo could be made cleaner without inventing
unreviewed domain decisions. It also converted unmet RFC acceptance language
into explicit status notes or xfailed tests where the behavior is still future
work.

## Findings addressed

- F-001: Updated `AGENTS.md`, `docs/rfcs/README.md`, and RFC status lines so the
  repo no longer presents partial work as landed.
- F-002: Replaced divergent desktop and PyVista GUI parameter conversion with a
  shared helper so `beam_wl` and `bow_rake` are preserved in both preview paths.
- F-003: Added RFC 0008 REST scaffolding for evaluate, STL generation, hull
  persistence, and explicit job-stub endpoints.
- F-004: Added page-load query decoding for shared hull links.
- F-005: Added explicit `beam_wl_m` validation for non-positive and greater than
  overall beam values while preserving the existing `None` default behavior.
- F-006: Added `GM0_m` hydrostatics output and changed `Cm_actual` to use
  waterline beam when provided.
- F-011: Added reserved RFC 0007 package/schema surfaces and a `kayakgen sweep`
  CLI stub that exits clearly as not implemented.
- F-012: Fixed the Docker packaging context by copying `AGENTS.md`; verified
  image build and CLI startup.

## Partial or deferred findings

- F-007: Resistance now uses a public geometry sampling API instead of reaching
  through private implementation details. The RFC 0005 low-Froude and 200 ms
  acceptance criteria remain unimplemented and are now marked by xfailed tests
  plus RFC status notes.
- F-008: Desktop class presets now update slider ranges and restore global
  ranges when returning to Custom. This was covered structurally by tests but
  not manually confirmed in a live GUI session.
- F-009: The RFC 0004 exact-stem/watertight wording conflict still requires a
  human design decision.
- F-010: RFC 0008 plot tabs, browser validation, and Lighthouse parity remain
  follow-up work.
- F-013: The workflow was created on a dirty/untracked worktree despite
  `allow_dirty:false`; this is recorded as a process finding, not a code fix.

## Verification

- `.venv/bin/python -m pytest -q` -> 69 passed, 2 xfailed.
- `.venv/bin/kayakgen --help` showed the `sweep` command.
- Import smoke for `kayakgen.model.schema` and `kayakgen.eval.cfd` succeeded.
- `docker build -t kayakgen-striatum-check .` succeeded.
- `docker run --rm kayakgen-striatum-check kayakgen --help` succeeded.
- `.venv/bin/ruff check .` could not be run because Ruff is not installed in the
  repo virtual environment.
