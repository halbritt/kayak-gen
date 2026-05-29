# Bug-hunt surface coverage

| Surface | Last searched | Findings ids | Lookback notes |
|---|---|---|---|
| `kayakgen/cli/` | never | — | CLI subcommand argument validation, error-path coverage, exit codes. |
| `kayakgen/eval/calibration/` | never | — | Fixture promotion validators, source-review packet acceptance, extractor edge cases. |
| `kayakgen/eval/cfd/` | 2026-05-29 (search #1) | BUG-003 (low), BUG-004 (medium) | Adapter dispatch, env-knob precedence, subprocess error handling, force.dat / case-template parsing. Tick 2 confirmed `shlex.quote` on subprocess args, `RawUnvalidatedClaimFields` enforcement, and three-mechanism opt-in precedence are correct; found a dead `_openfoam_succeeded_path_enabled()` and missing negative-case tests for env-var coercion. Not settled (1 search). |
| `kayakgen/eval/closed_volume/` | never | — | Geometry construction, self-intersection diagnostics. |
| `kayakgen/eval/evidence/` | never | — | Evidence binding chains, `--bind-evidence` invariant gates. |
| `kayakgen/eval/stability/` | 2026-05-29 (search #1) | BUG-001 (critical), BUG-002 (high) | `EMPTY_STABILITY_FIT_REGISTRY` consumption, accepted-fit lookup, GZ contracts. Tick 1 found RFC 0058 / stage-4 discriminator gap (`kind` field) and a missing constrained-trim validator on `StabilityFixturePromotionPacket`. Not settled. |
| `kayakgen/io/` | never | — | File-format readers/writers; round-trip fidelity. |
| `kayakgen/model/` | never | — | Pydantic model validators (Hull, claim records, advisory). |
| `kayakgen/search/active/` | never | — | NSGA-II / EHVI math, seeded determinism, constraint refusal. |
| `kayakgen/search/` (non-active) | never | — | Pareto, objective admissibility, sweep planner. |
| `kayakgen/services/` | never | — | `evaluation.py` view-model helpers, identity / hash routes, design report. |
| `kayakgen/ui/desktop.py` | never | — | matplotlib slider wiring, PyQt event loop, deprecation shim. |
| `kayakgen/ui/web/app.py` | never | — | Trame state binding, REST handlers, web layout. |
| `kayakgen/ui/web/generate_*.py` | never | — | Form-builder, frontier rendering, spec submission. |
| `kayakgen/ui/web/controllers.py` | never | — | Controller glue, export menu, state listeners. |
| `kayakgen/ui/parameter_metadata.py` + `hydrostatics_metadata.py` | never | — | Registry shapes (RFC 0060/0062). |

## Cool-down rule

A surface that was searched in the last 60 minutes is skipped
for the next tick. A surface that has been searched 3+ times
total with no new actionable findings drops to "settled" and is
not re-searched until either (a) `git log -- <surface>` shows
new commits since the last search, or (b) the operator manually
resets it to "never" in this table.

Update this file at the end of each tick. The next tick reads
the top of the un-cooled-down list and dispatches against it.
