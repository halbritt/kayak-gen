author: operator [self-declared: operator-ops-review]

# Ops review - web plots and comparison UI

Verdict intent: accept_with_findings

## Findings

### O-001 - New web view logic needs pure helpers before UI wiring

Current web tests work because state encoding, metrics, STL, REST, and route
helpers are pure functions or app-factory smoke tests. A comparison UI will be
hard to test if parsing, view-model construction, and candidate reload are
embedded only in Trame layout callbacks.

Required action: add controller/view-model helpers for analysis rows, comparison
report parsing, candidate rows, and candidate reload state before wiring them to
the Trame layout.

### O-002 - Fixture reports should be generated in tests, not checked in as large artifacts

`tests/test_compare.py` already creates deterministic tiny sweep runs using
`run_sweep`. That is enough to build comparison reports without adding bulky
fixtures.

Required action: use small generated fixtures in tests unless the ledger proves
a static fixture is necessary.

### O-003 - Browser smoke should cover discoverability of the new surface

Workflow 0020 added optional Playwright coverage for the existing page. A new
analysis/comparison UI should either extend that smoke test to assert the tabs
or add focused headless tests that instantiate the app and verify the new state.

Required action: add focused `tests/test_web.py` coverage and update the
browser smoke only where selectors are stable.

### O-004 - Resistance curves can be expensive if recomputed on every render

`resistance_curve()` defaults to 21 speeds and relatively high Michell
quadrature settings. Recomputing it on every state change could make the web UI
sluggish.

Required action: keep the first slice lightweight. Use reduced samples for
display, reuse existing at-speed metrics where possible, or compute curve data
only on explicit view refresh.

## Required gate

Proceed to ledger. Implementation should avoid new frontend dependencies,
large fixtures, or long-running plot computations in the default slider path.
