# RFC 0046: Non-env-gated OpenFOAM Succeeded Path

Status: landed three-mechanism opt-in (profile flag > persistent setting > env knob) + audit trail; defaults unchanged
Date: 2026-05-16
Context: successor to RFC 0041 / D012 / D022. The cowboy 2026-05-16
session landed a real `openfoam-v2512-interfoam-local` `succeeded` path
behind two opt-in environment variables (`KAYAKGEN_OPENFOAM_LOCAL_RUN=1`
plus `KAYAKGEN_OPENFOAM_SMOKE=1` for the integration test) and a third
optional `KAYAKGEN_OPENFOAM_BASHRC` override. This RFC asks whether the
env-knob mechanism is the right long-term gate.

## Problem

The env-knob gate exists for a real reason: even with the v2512
toolchain installed, a default `kayakgen cfd run` invocation against an
`openfoam-v2512-interfoam-local` job should not silently start a multi-
second real solver process unless the operator opts in. The env knob is
the safest possible default for the cowboy-session landing.

It is also a usability problem. A repeated workflow ("run the same case
under interFoam") needs the env variable set on every invocation, every
shell, every CI job. Operators end up writing wrapper scripts. The
`KAYAKGEN_OPENFOAM_SMOKE` variant is a second knob that only the
integration test reads; it adds confusion about which variable does
what.

A per-profile config flag inside the solver profile JSON (or a
deliberate persistent setting under `~/.config/kayakgen/`) would express
the same operator-opt-in intent with less per-invocation overhead and a
clearer audit trail.

## Goals

- Provide an opt-in path that survives across invocations without
  re-typing an env variable.
- Make the opt-in *visible* in the run record: the resulting
  `CfdRunRecord` should say which mechanism allowed the run (env knob,
  profile config, persistent setting).
- Preserve the default-conservative posture: a freshly-installed
  kayakgen with the v2512 toolchain available must still refuse to run
  interFoam until the operator says so.
- Preserve the D012 evidence gates. Provenance probe, case-template
  lock, parser strictness, raw_unvalidated payload, and locked
  case_template_version remain authoritative.

## Non-Goals

- No change to the case template, renderer, runner, or evidence binder.
- No change to `claim_state`. It stays `raw_unvalidated`.
- No new claim state, no validation/calibration/final-prediction
  wording.
- No automatic execution at job-creation time. The opt-in is for
  `kayakgen cfd run`, not for `kayakgen cfd prepare`.
- No hosted/distributed execution. RFC 0023 / RFC 0041 boundaries
  remain.
- No web UI for opting in. Web stays read-only.

## Dependencies

- RFC 0041 / D012 / D022 (the env-gated landing).
- `kayakgen/eval/cfd/openfoam_v2512_interfoam/runner.py:is_openfoam_available`
  (toolchain check).
- `kayakgen/eval/cfd/jobs.py:OpenFoamLocalAdapter` (the adapter that
  branches into `_attempt_real_succeeded_path`).
- Decisions D012 and D022 stay authoritative.

## Proposal

### Three opt-in mechanisms, ranked by precedence

1. **Per-job profile flag** (highest precedence). When the operator runs
   `kayakgen cfd prepare`, they may pass
   `--allow-real-solver-execution` which writes
   `allow_real_solver_execution: true` into the job's `profile.json`.
   This is the most explicit opt-in: it lives in the job artifact and
   travels with it.
2. **Persistent operator setting**. `~/.config/kayakgen/cfd.json` with
   `{"allow_real_solver_execution_profiles": ["openfoam-v2512-interfoam-local"]}`
   admits any job whose `profile.name` matches an entry in the list.
   Set once per workstation; survives across shells.
3. **Env knob** (backwards compatible). `KAYAKGEN_OPENFOAM_LOCAL_RUN=1`
   continues to work exactly as today. The
   `KAYAKGEN_OPENFOAM_SMOKE=1` variable is retained as a test-only
   override; user-facing docs deprecate mentioning it.

If none of the three mechanisms admit the run, the adapter falls back
to today's `error_kind=solver_success_blocked` path.

### Audit trail

When the real path runs, the resulting `CfdRunRecord` carries:

- a new field `real_solver_execution_opt_in: Literal["profile_flag",
  "persistent_setting", "env_knob"]`
- a `solver_execution_audit` block recording the toolchain bashrc path,
  the provenance probe result, the case-template version, and the
  wall-clock seconds for meshing and solve.

The existing fixture/blocked path keeps the field as `None`.

### What lands and what does not

Lands:
- `--allow-real-solver-execution` flag on `kayakgen cfd prepare`.
- `~/.config/kayakgen/cfd.json` loader with strict schema validation.
- Precedence resolution: profile flag > persistent setting > env knob.
- `real_solver_execution_opt_in` field on `CfdRunRecord`.
- `solver_execution_audit` block on succeeded records.
- Tests:
  - profile flag admits run, persistent setting absent.
  - persistent setting admits run, profile flag absent.
  - env knob still works.
  - no mechanism set → `solver_success_blocked` (regression of D012).
  - tampered persistent setting JSON rejected with a structured error.
  - audit block carries non-empty fields on a real succeeded run.

Does not land:
- No automatic discovery of installed solvers. The operator names the
  profile explicitly.
- No env-knob deprecation. Removing
  `KAYAKGEN_OPENFOAM_SMOKE` / `KAYAKGEN_OPENFOAM_LOCAL_RUN` is a
  separate decision.

## Acceptance Criteria

- Default behavior (no env knob, no flag, no persistent setting) stays
  `solver_success_blocked`.
- `kayakgen cfd prepare ... --allow-real-solver-execution` writes the
  flag into `profile.json`; subsequent `kayakgen cfd run` succeeds
  end-to-end when the toolchain is present.
- A `~/.config/kayakgen/cfd.json` entry for
  `openfoam-v2512-interfoam-local` admits the run for every freshly
  prepared job of that profile.
- `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` continues to admit runs (backwards
  compatible).
- Succeeded records expose `real_solver_execution_opt_in` and a
  `solver_execution_audit` block with non-empty contents.
- `claim_state` stays `raw_unvalidated`; `accepted_uses` stays `[]`;
  `case_template_version` stays the locked literal.

## Open Questions

- Should the persistent setting also allow per-job overrides via
  `~/.config/kayakgen/jobs/<job_id>.json`?
- Should the precedence be reversed (env knob is most explicit and
  should win)?
- Should we deprecate `KAYAKGEN_OPENFOAM_SMOKE` immediately, or keep
  it through one release?
- Should there be a `kayakgen cfd opt-in --profile <name>` command that
  edits the persistent setting?

## Implementation Path

1. Add the `--allow-real-solver-execution` flag to `kayakgen cfd
   prepare` and persist it on the job's `profile.json`.
2. Add the persistent settings loader at
   `kayakgen.eval.cfd.config:load_kayakgen_cfd_config` with strict
   Pydantic validation.
3. Extend `OpenFoamLocalAdapter._attempt_real_succeeded_path` to accept
   any of the three opt-in mechanisms with precedence resolution.
4. Add the `real_solver_execution_opt_in` + `solver_execution_audit`
   fields on `CfdRunRecord` (additive, default `None`).
5. Update `docs/USER_GUIDE.md` to document the new flag and config
   file; keep the env-knob section.

## Domain Modeling

Boundary clarification. The opt-in mechanism is a *policy* layer above
the existing adapter aggregate. It does not change the adapter's
contract; it changes how the adapter consents to running. No new
aggregate, no new value object beyond a small `KayakgenCfdConfig`
record, no new domain event.

The `solver_execution_audit` block is local-to-run provenance, not a
cross-run domain event stream.

Cite `DDD.md § "Adding to the model"`: this is a *policy* refinement
over the existing adapter aggregate.
