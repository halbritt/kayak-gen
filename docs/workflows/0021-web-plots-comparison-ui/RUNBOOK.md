# Runbook - 0021 web plots and comparison UI

1. Review RFCs 0008 and 0013, the current Trame web app, comparison report
   models, CLI comparison command, and web/browser tests.
2. Run three review lanes:
   - RFC/status traceability for plot tabs and comparison UI;
   - domain semantics for plotted metrics, Pareto axes, warnings, and units;
   - ops/test coverage for state, fixtures, browser smoke, and performance risk.
3. Consolidate findings into a ledger that separates the smallest safe web
   analysis slice from larger UI redesign, hosted-demo, optimizer, or solver
   work.
4. Implement only the accepted slice: hydrostatics/resistance plot views,
   comparison report loading/views, candidate reload into the editor, API/test
   fixtures, and truthful RFC status updates as directed by the ledger.
5. Final review should accept only if users can inspect the landed analysis
   views reproducibly, tests cover the new views, and unsupported comparison
   actions remain explicit.
