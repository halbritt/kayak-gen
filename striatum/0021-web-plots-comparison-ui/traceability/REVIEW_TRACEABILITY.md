author: operator [self-declared: operator-traceability-review]

# Traceability review - web plots and comparison UI

Verdict intent: accept_with_findings

## Findings

### T-001 - RFC 0008 plot tabs are still absent from the web app

RFC 0008 specifies sheer-plan, cross-section, and metrics/plot tabs below the
3D view. The current Trame app has sliders, VTK view, metrics text, share, REST,
STL export, and browser smoke coverage, but no tabbed analysis area.

Required action: add the smallest plot/data view slice below the 3D view. It
should let users inspect hydrostatics and resistance curves/rows without
rewriting the UI or changing core evaluators.

### T-002 - RFC 0013 web comparison follow-up is not started

RFC 0013's CLI/report slice has landed, but its web follow-up requires loading
a comparison report, showing candidates, showing Pareto membership, and loading
a candidate into the editor. No web state, controller helper, REST helper, or UI
surface currently consumes `ComparisonReport`.

Required action: add a small comparison report view backed by the existing
`ComparisonReport` model. It can accept pasted/uploaded JSON or a helper-backed
fixture path, but it must not invent a new report format.

### T-003 - Candidate reload needs an explicit safe contract

Comparison summaries contain `parameters`, `hull_hash`, `artifacts`, metrics,
warnings, and status. Reloading from arbitrary artifact paths would couple the
web UI to local filesystem state, while reloading from `parameters` is safe but
partial because it applies only sweep variables over the current/base hull.

Required action: implement candidate reload only from report summary parameters
or explicitly defer it. The UI/docs must say what is reloaded and what is not.

### T-004 - RFC status will need another partial-status update

Even a successful 0021 slice will not complete hosted demo, mobile view-only
mode, console-clean Lighthouse, full plot parity, optimizer, or solver dispatch.

Required action: update RFC 0008, RFC 0013, and the RFC index to name the exact
landed web-analysis slice and keep larger follow-up work visible.

## Required gate

Proceed to ledger. Implementation should target a coherent web analysis slice:
analysis tabs, comparison report display, Pareto/candidate visibility, and
truthful status wording. It should not attempt a full frontend redesign.
