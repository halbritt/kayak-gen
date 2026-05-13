# Deferred Workflow Queue

Updated: 2026-05-13

This queue structures the remaining known work after workflows 0012-0018. The
IDs below are proposed workflow IDs. They are ordered by dependency and
implementation leverage, not by RFC number.

Each implementation workflow should use three review lanes before coding:

- Traceability lane: verify RFC acceptance criteria, prior workflow findings,
  and status wording.
- Domain lane: verify kayak/geometry/hydrostatics/CFD assumptions and guard
  against false claims.
- Ops/test lane: verify package boundaries, CLI/web behavior, reproducibility,
  and test strategy.

For implementation jobs, use Codex by default for code changes unless a workflow
has a narrower reason to prefer another implementor. The implementor prompt for
each workflow must include: "Use the maximal number of useful sub-agents with
disjoint write scopes. Prefer parallel agents for independent code, test, docs,
and review tasks, but keep one agent responsible for final integration."

## 0019 - Legacy RFC Partial Closure

Target RFCs: 0004, 0006.

Purpose: close the old partially landed design-space work before more
generation, stability, and CFD logic depends on it. This includes plumb-bow
semantics, class presets, constraint validation, and truthful status updates.

Prerequisites: clean `main`; current golden tests passing.

Review lanes:

- Traceability: map every RFC 0004 and 0006 acceptance criterion to landed code,
  missing work, or explicit deferral.
- Domain: check bow/stern coordinate wording, class boundary definitions, and
  constraint ranges against `docs/design/kayak_hull_design_constraints.md`.
- Ops/test: check presets, validation errors, CLI/web/desktop propagation, and
  golden-test impact.

Implementation prompt:

```text
Implement the safe RFC 0004/0006 closure items from the findings ledger. Use the
maximal number of useful sub-agents with disjoint write scopes. Prefer parallel
agents for independent code, test, docs, and review tasks, but keep one agent
responsible for final integration. Suggested splits: domain model and presets;
CLI/serialization; web/desktop propagation; tests/docs/status. Do not rewrite
the hull generator unless a finding proves it is necessary.
```

Exit criteria: RFC 0004/0006 statuses are either landed or have sharply named
remaining deferrals; tests cover the accepted parameter-space behavior.

## 0020 - Browser Acceptance and Demo

Target RFC: 0008.

Purpose: finish the browser-facing acceptance gap left by workflow 0017:
Playwright or equivalent real-browser smoke coverage, optional Lighthouse checks
when tooling is available, and hosted demo/deployment instructions.

Prerequisites: workflow 0017 landed; VTK offscreen smoke remains passing.

Review lanes:

- Traceability: map RFC 0008 acceptance criteria to headless tests, real-browser
  tests, docs, and explicit unavailable tooling.
- Browser/domain: verify actual rendering state, first-screen usability,
  hull-view framing, and no false visual acceptance.
- Ops/test: verify dependency installation, Docker/runtime libraries,
  skip/xfail policy, and CI feasibility.

Implementation prompt:

```text
Implement real-browser web acceptance where the environment supports it and
document truthful skips where it does not. Use the maximal number of useful
sub-agents with disjoint write scopes. Prefer parallel agents for independent
code, test, docs, and review tasks, but keep one agent responsible for final
integration. Suggested splits: Playwright/pytest integration; Docker/CI/runtime
deps; deployment docs; RFC/status updates. Do not claim Lighthouse or hosted
demo success unless the command was actually run or the deployment exists.
```

Exit criteria: real-browser smoke tests are present or explicitly skipped with
actionable dependency reasons; RFC 0008 status is truthful.

## 0021 - Web Plots and Comparison UI

Target RFCs: 0008, 0013.

Purpose: move the web frontend from basic parameter/render verification toward
the analysis UI promised by RFCs 0008 and 0013: hydrostatics/resistance plot
tabs, comparison report loading, Pareto/candidate views, and candidate reload
into the editor.

Prerequisites: browser acceptance scaffolding from workflow 0020 or a documented
reason to defer browser automation.

Review lanes:

- Traceability: map web UI requirements from RFC 0008 and RFC 0013 to views and
  tests.
- Domain: verify plotted metrics, units, Pareto axes, and comparison wording.
- Ops/test: verify state management, fixture reports, browser/headless tests,
  and performance risk.

Implementation prompt:

```text
Implement the smallest coherent web analysis slice that satisfies the accepted
RFC 0008/0013 criteria. Use the maximal number of useful sub-agents with
disjoint write scopes. Prefer parallel agents for independent code, test, docs,
and review tasks, but keep one agent responsible for final integration.
Suggested splits: web state/controllers; plot/view components; comparison
fixtures and tests; docs/RFC status. Do not add decorative UI or marketing
pages; keep the app task-focused.
```

Exit criteria: users can inspect key curves/reports in the web app, tests cover
the new views, and unsupported comparison actions are explicit.

## 0022 - Generalized Trim and GZ Stability

Target RFCs: 0011, 0014.

Purpose: extend equilibrium stability beyond centered sinkage by adding
longitudinal load cases, trim solving, and a truthful path for high-angle GZ.

Prerequisites: RFC 0014 accepted or amended; workflow 0019 legacy coordinate
closure preferred.

Review lanes:

- Traceability: verify RFC 0011 deferrals and RFC 0014 acceptance criteria.
- Domain: verify load-position conventions, moment balance, fixed-paddler-CG
  assumption, and high-angle volume semantics.
- Ops/test: verify CLI/JSON compatibility, sweep record compatibility, numerical
  tolerances, and non-convergence tests.

Implementation prompt:

```text
Implement only the accepted stability slice from the findings ledger. Use the
maximal number of useful sub-agents with disjoint write scopes. Prefer parallel
agents for independent code, test, docs, and review tasks, but keep one agent
responsible for final integration. Suggested splits: load-case model and
serialization; trim solver; CLI/sweep integration; tests/docs/status. Do not
emit high-angle GZ values unless the closed-volume decision is accepted and
implemented with tests.
```

Exit criteria: trim equilibrium is computed or explicitly deferred with reasons;
high-angle stability remains unavailable unless backed by a named volume model.

## 0023 - Resistance Calibration Dataset Vetting

Target RFC: 0012.

Purpose: revisit resistance calibration only when a licensed and relevant source
dataset can be identified. Workflow 0012 found no acceptable source, so this is
a gated research-and-implementation workflow.

Prerequisites: candidate dataset or source family to vet; otherwise run as a
review-only workflow and record blockers.

Review lanes:

- Traceability: verify RFC 0012 acceptance requirements and prior workflow 0012
  findings.
- Domain/source: verify dataset hull class, measurement type, units, licensing,
  and applicability to kayak-scale slender hulls.
- Ops/test: verify fixture size, provenance metadata, reproducible fitting, and
  no calibrated-claim leakage.

Implementation prompt:

```text
If and only if the ledger accepts a dataset, implement the calibration ingest
and metadata slice. Use the maximal number of useful sub-agents with disjoint
write scopes. Prefer parallel agents for independent code, test, docs, and
review tasks, but keep one agent responsible for final integration. Suggested
splits: source/provenance docs; data ingestion; fitting/report code; tests/RFC
status. If no dataset is accepted, do not fabricate fixtures; record blockers.
```

Exit criteria: either a licensed calibration fixture lands with provenance and
tests, or RFC 0012 remains proposed with precise blockers.

## 0024 - Watertight Solid Mesh Profile

Target RFCs: 0010, 0015.

Purpose: add a named watertight solid readiness profile and package output that
future solver dispatch can depend on. This is separate from the already landed
open wetted-surface package/profile.

Prerequisites: workflow 0019 plumb/end-cap decisions preferred; mesh package
profile from workflow 0015 landed.

Review lanes:

- Traceability: verify RFC 0010 open questions and CFD-readiness claims.
- Domain/geometry: verify closure policy, deck/hull body semantics, normal
  orientation, manifold checks, and waterline handling.
- Ops/test: verify deterministic package artifacts, synthetic invalid meshes,
  CLI behavior, and downstream solver profile hooks.

Implementation prompt:

```text
Implement a named watertight solid mesh readiness profile only where the
geometry contract is explicit. Use the maximal number of useful sub-agents with
disjoint write scopes. Prefer parallel agents for independent code, test, docs,
and review tasks, but keep one agent responsible for final integration.
Suggested splits: geometry/profile design; diagnostics/package writer; CLI and
manifest tests; docs/RFC status. Do not relabel open surfaces as watertight.
```

Exit criteria: current packages remain honestly classified, and any new
watertight profile has tests proving manifold/closure behavior.

## 0025 - CFD Solver Dispatch and Jobs

Target RFC: 0015.

Purpose: introduce local CFD job specs, run records, solver profiles, and
unavailable/mock adapter behavior before any real external solver integration.

Prerequisites: RFC 0015 accepted or amended; workflow 0024 required for any
profile that needs watertight solid readiness.

Review lanes:

- Traceability: verify RFC 0015 acceptance criteria and RFC 0008 job-stub
  expectations.
- Domain/CFD: verify raw/unvalidated result wording, solver profile readiness
  requirements, speed/fluid inputs, and artifact provenance.
- Ops/test: verify local filesystem queue, failure capture, CLI status behavior,
  and no dependency on unavailable solver binaries for baseline tests.

Implementation prompt:

```text
Implement the local dispatch contract and unavailable/mock adapter first. Use
the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent code, test, docs, and review tasks, but keep one
agent responsible for final integration. Suggested splits: job/run models; CLI
commands; adapter/failure handling; web status/docs/tests. Do not integrate a
real solver until readiness and installation requirements are explicit.
```

Exit criteria: CLI/web can represent CFD job states without fake solver
success, and real solver integration is a separate accepted slice.
