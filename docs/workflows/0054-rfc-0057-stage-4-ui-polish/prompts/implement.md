# Implementation Prompt

Read the packet objective, write scope, context docs, and:

- `docs/rfcs/0057-generative-search-jobs-and-web-workspace.md` — the parent
  RFC for the Generate-panel feature.
- `docs/workflows/0054-rfc-0057-stage-4-ui-polish/STAGE_4_DECISIONS.md` — the
  12 operator-affirmed decisions this stage implements.
- The existing stage 1-3 surfaces under `kayakgen/services/generative_jobs.py`,
  `kayakgen/services/generative_jobs_runner.py`,
  `kayakgen/ui/web/app.py`, `kayakgen/ui/web/controllers.py`,
  `kayakgen/cli/main.py`, and the corresponding tests.

Implement only the assigned slice.

Before editing, split your work into the maximal useful number of sub-agent
tasks with disjoint file ownership inside the packet's write scope. Ask
sub-agents to edit directly only inside their assigned files and to report
changed paths. Integrate their work and run focused validation.

Requirements:

- Stay strictly inside the allowed paths. The runner enforces
  `require_disjoint_write_scopes: true`; the other tracks are running in
  parallel and any out-of-scope edit will be rejected.
- The other tracks may not have completed yet. Do not import from a
  module that hasn't been written by another track — your module must stand
  alone until the integrator wires everything together.
- Preserve every existing no-claims boundary and forbidden-copy guard
  (`tests/test_web_layout.py`, `tests/test_web_read_models.py`,
  `tests/test_ui_theme.py`). Display-only metrics (RFC 0043), high-angle
  GZ surfacing copy, hosted-worker negation phrase, and the existing
  `result_semantics: "raw_unvalidated"` envelope are all load-bearing.
- Live-validate spec inputs against the existing
  `ensure_objectives_not_high_angle_gz` (RFC 0043) and
  `ensure_objectives_claim_admissible_for_search` (RFC 0044) gates. The
  UI must never offer a display-only metric in an objective picklist;
  claim-admissibility refusals must surface inline next to the offending
  row, not just on submit.
- Add focused tests proportional to the touched surface. New modules must
  be import-safe on a cold start (no module-level network or fs calls).
- Do not start real solver execution, calibrated fitting, fixture promotion,
  hosted deployment, production readiness, or safety/design-fitness claims.

Publish the required patch summary artifact with the exact Striatum front
matter and byline. The patch summary must enumerate (a) the files actually
changed, (b) the focused tests added, (c) the targeted test invocation that
proved your slice green, and (d) any decision you escalated to the integrator
because it depended on another track.
