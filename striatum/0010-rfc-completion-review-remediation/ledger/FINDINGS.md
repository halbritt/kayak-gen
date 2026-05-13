# Findings ledger - 0010

author: operator
Date: 2026-05-12
Review inputs: traceability, arch/domain, interface/ops

## Stats

- Source findings: 19
- Deduplicated findings: 13
- By severity: blocker 0 / major 10 / minor 3 / nit 0
- Actionable now: 8
- Needs human decision: 1

## Findings

### F-001 - RFC status and contributor guidance are stale

- Source: F-TRACE-001
- Severity: major
- Classification: docs-only
- RFC(s): 0002-0008
- File(s): `docs/rfcs/README.md`, `AGENTS.md`
- Statement: The RFC index still says every non-template RFC through 0008 is
  proposed, while the repo has landed substantial package, CLI, test, web, and
  Docker work. AGENTS also still tells agents to expect the old flat-file
  layout and that RFC 0007 has not landed.
- Suggested remediation: Update RFC statuses to distinguish landed, partial,
  and still-open work. Update AGENTS current direction to say RFC 0007 is
  mostly landed but RFC 0004/0005/0006/0008 acceptance remains partial.

### F-002 - PyVista preview drops `beam_wl` and `bow_rake`

- Source: F-TRACE-002, F-ARCH-005, F-OPS-004
- Severity: major
- Classification: actionable-now
- RFC(s): 0002, 0004, 0006, 0007
- File(s): `kayakgen/ui/desktop.py`, `kayakgen/ui/pv_window.py`
- Statement: Desktop 2D plots and metrics include `beam_wl` and `bow_rake`,
  but the PyVista preview reconstructs `Hull` from a separate mapping that
  omits both. The 3D preview can therefore disagree with sliders, metrics,
  and STL export.
- Suggested remediation: Centralize GUI-parameter-to-`Hull` conversion or add
  the missing fields to the PyVista mapping. Add a focused test for the
  conversion path.

### F-003 - RFC 0008 REST API and job stubs are missing

- Source: F-TRACE-005, F-OPS-002
- Severity: major
- Classification: actionable-now
- RFC(s): 0008
- File(s): `kayakgen/ui/web/app.py`, `kayakgen/ui/web/controllers.py`,
  `tests/test_web.py`
- Statement: RFC 0008 promises `/api/evaluate`, `/api/stl`, `/api/hulls`, and
  heavy-CFD job stubs. The code has pure controller helpers but no route
  registration and no job-stub behavior.
- Suggested remediation: Add route registration helpers around the Trame
  server's aiohttp app, implement in-memory hull storage and 501 job stubs,
  and add route-level tests with a fake aiohttp app if a full server smoke is
  not practical in this round.

### F-004 - URL share/page-load behavior is helper-only

- Source: F-OPS-003, F-TRACE-005
- Severity: major
- Classification: actionable-now
- RFC(s): 0008
- File(s): `kayakgen/ui/web/app.py`, `tests/test_web.py`
- Statement: `load_from_query()` exists and tests call it manually, but the
  Trame app does not parse the initial browser query string during startup.
  Share only writes a relative `?hull=...` value to state.
- Suggested remediation: Add an `initial_query` or equivalent startup hook to
  `create_app` so query decoding is part of app initialization, and add a
  test. Full clipboard behavior can be deferred if documented.

### F-005 - `beam_wl` accepts invalid values and has unclear default semantics

- Source: F-ARCH-001
- Severity: major
- Classification: actionable-now
- RFC(s): 0006, 0007
- File(s): `kayakgen/model/hull.py`, `kayakgen/model/geometry.py`,
  `tests/test_classes.py`
- Statement: The model accepts negative `beam_wl_m` and values greater than
  `beam_oa_m`. RFC 0006 also says default waterline beam should be about
  `0.92 * beam`, while the current compatibility default `None` falls back to
  overall beam.
- Suggested remediation: Add validation for any explicit `beam_wl_m` value.
  Keep legacy default behavior unless intentionally updating goldens, but
  document the compatibility choice and add tests.

### F-006 - Hydrostatics omits `GM0_m` and computes `Cm_actual` against overall beam

- Source: F-ARCH-004
- Severity: major
- Classification: actionable-now
- RFC(s): 0006, 0007
- File(s): `kayakgen/eval/hydrostatics.py`, `tests/test_hydrostatics.py`
- Statement: `GM0_m` is in the read model but is never populated, despite RFC
  0006 specifying a placeholder KG. `Cm_actual` divides submerged midship
  area by overall beam even when the submerged section uses `beam_wl_m`.
- Suggested remediation: Compute an initial-transverse-GM estimate from
  waterplane second moment, displacement volume, KB, and KG=0.25 m. Compute
  `Cm_actual` with waterline beam when present. Add tests for both.

### F-007 - Resistance evaluator crosses geometry abstraction and misses RFC 0005 acceptance

- Source: F-TRACE-003, F-ARCH-003, F-ARCH-006
- Severity: major
- Classification: actionable-now
- RFC(s): 0005, 0007
- File(s): `kayakgen/eval/resistance.py`, `tests/test_resistance.py`
- Statement: Resistance calls a private `LoftedHullGeometry` helper and
  reconstructs the loft formula, so it is not geometry-implementation-neutral.
  Tests do not enforce the RFC's low-Fn/high-Fn wave/viscous criteria, beam
  sensitivity, or 200 ms target.
- Suggested remediation: Add a public geometry sampling method or build the
  breadth grid from `section()`. Add acceptance-aligned tests. If the Michell
  implementation still fails low-Fn physics, gate or document it as a
  non-accepted exploratory metric rather than claiming RFC 0005 acceptance.

### F-008 - RFC 0006 GUI class ranges/advisory are only partially landed

- Source: F-TRACE-004
- Severity: major
- Classification: actionable-now
- RFC(s): 0006
- File(s): `kayakgen/ui/desktop.py`, `docs/rfcs/0002-0003-audit.md`
- Statement: Class presets seed values, but selecting a class does not update
  slider ranges and no advisory/validation banner exists. The audit says this
  was left out, but RFC 0006 still presents it as required behavior.
- Suggested remediation: Add range mutation and a concise advisory string, or
  update RFC 0006 to mark that UI behavior deferred. Prefer implementation if
  it can be done with low risk.

### F-009 - RFC 0004 exact stem/watertight wording conflicts with current mesh model

- Source: F-TRACE-002, F-ARCH-002
- Severity: major
- Classification: needs-human-decision
- RFC(s): 0004
- File(s): `docs/rfcs/0004-plumb-bow.md`, `kayakgen/model/geometry.py`,
  `tests/test_plumb_bow.py`
- Statement: The exact station at x = -L/2 has zero section area and the mesh
  is an open surface with boundary edges, while the RFC says the plumb stem
  should have non-zero exact-end area and watertight STL at all `bow_rake`
  values. Changing this would alter geometry/goldens and may require an
  explicit end-cap design decision.
- Suggested remediation: Do not guess in this remediation round. Record the
  mismatch, update RFC status to partial, and open a follow-up design decision
  for exact plumb stem/end-cap semantics.

### F-010 - RFC 0008 plot tabs/browser/Lighthouse parity remains unproven

- Source: F-TRACE-005, F-TRACE-006
- Severity: major
- Classification: defer-follow-up
- RFC(s): 0008
- File(s): `kayakgen/ui/web/app.py`, `tests/test_web.py`
- Statement: The web app lacks the cross-section/sheer/plan plot tabs from
  the RFC, and tests explicitly reserve full Trame/Playwright coverage for
  later. Lighthouse and Docker-run acceptance are also unproven.
- Suggested remediation: Mark web frontend status as partial in docs and keep
  route/share fixes in this round. Treat plot tabs and browser/Lighthouse
  verification as follow-up work.

### F-011 - RFC 0007 reserved package/schema/CLI surfaces are incomplete

- Source: F-ARCH-007, F-OPS-005
- Severity: minor
- Classification: actionable-now
- RFC(s): 0007
- File(s): `kayakgen/cli/main.py`, package tree
- Statement: The main package exists, but RFC 0007 mentioned `search/`,
  `model/schema.py`, `eval/cfd.py`, and a `kayakgen sweep` command. These are
  absent or unstubbed.
- Suggested remediation: Add a clear `sweep` CLI stub and minimal reserved
  module stubs where low risk, or update RFC status to say those surfaces are
  deferred.

### F-012 - Dockerfile/readme packaging risk is unresolved

- Source: F-OPS-001
- Severity: minor
- Classification: actionable-now
- RFC(s): 0008
- File(s): `Dockerfile`, `pyproject.toml`
- Statement: `pyproject.toml` names `AGENTS.md` as the readme, but the
  Dockerfile does not copy it before install. A local editable dry-run did not
  reproduce a failure, so this is a low-risk packaging hygiene finding rather
  than a confirmed blocker.
- Suggested remediation: Copy `AGENTS.md` before `pip install` and add a note
  to the patch summary that actual Docker build was not run unless available.

### F-013 - Workflow run started from a dirty/untracked workflow setup

- Source: F-OPS-006
- Severity: minor
- Classification: process-only
- RFC(s): workflow hygiene
- File(s): `.codex/`, `docs/workflows/0010-rfc-completion-review-remediation/`
- Statement: The workflow declares `allow_dirty: false`, but setup files and
  the workflow directory were untracked when the run was prepared and started.
  Striatum allowed branch confirmation, but the operator report must be honest
  about the state.
- Suggested remediation: Keep OPERATOR_REPORT updated. Commit or explicitly
  leave the workflow artifacts uncommitted at the end based on operator
  preference.
