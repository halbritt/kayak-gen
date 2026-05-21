---
schema_version: striatum.finding.v1
artifact_kind: finding
verdict_intent: accept_with_findings
---

author: reviewer-traceability-claude-opus-4.7-002

# Traceability Review — Workflow 0056 (RFC 0058 stage 2 + 3 + NB-1)

Reviewer: Claude Opus 4.7 (reviewer-traceability-claude-opus-4.7-002)
Date: 2026-05-21
Branch: `striatum/0056-rfc-0058-stage2-3-burndown`
Verdict: **accept_with_findings** — two minor undocumented decisions
flagged; no behavioural scope creep.

## Method

Walked the diff vs `main` (HEAD = `eedbd2e`, plus uncommitted working
copy) line-by-line, mapping every changed file to an explicit row in
`docs/workflows/0056-rfc-0058-stage2-3-burndown/STAGE_2_3_DECISIONS.md`
and to a section of `docs/rfcs/0058-stability-calibration-acceptance.md`.
Inputs: the decisions doc, RFC 0058, and direct reads of the modified
sources and tests.

## Summary

All 21 decision rows have concrete code or doc evidence. Defaults stay
byte-stable (empty registry → `unvalidated_hydrostatic_comparison` and
`opt_in_only`, as required by D-6 / D-13 / RFC 0058 stage 2 acceptance
criteria). No safety / seaworthiness / final-prediction / design-fitness
wording introduced. No new claim-state literal beyond the two already
named in RFC 0058. Stage 4 promotion remains gated.

Two undocumented engineering choices were made to make the new sub-app
land without breaking other surfaces. Neither changes runtime behaviour
beyond what the decisions imply, but both should be recorded — see
"Findings" below.

## Decision-by-decision traceability

### Stage 2 — contracts

| Row | Evidence | Maps to |
| --- | --- | --- |
| D-1 | `kayakgen/eval/stability/high_angle_contracts.py:60-86` defines `resolve_analytical_claim_label(hull, fit_registry)`. Re-exported from `kayakgen/eval/stability/__init__.py:50,110`. | RFC 0058 "Analytical-claim upgrade contract" |
| D-2 | `kayakgen/eval/stability/high_angle_contracts.py:24-27,49` — `AnalyticalClaimLabel = Literal[...]` with both literals; `GeneratedBodyGZCurve.result_semantics` typed as `AnalyticalClaimLabel`, default unchanged. | RFC 0058 acceptance criteria; round-trip covered by `tests/test_resolve_analytical_claim_label.py:125-131`. |
| D-3 | `high_angle_contracts.py:67-78` — `acceptance_verdict == "accepted"` AND `scope.hull_class == hull.hull_class` AND `hull_design_hash in scope.design_hash_envelope`. Hull `design_hash` resolution via `_hull_design_hash` (`high_angle_contracts.py:82-89`). | `tests/test_resolve_analytical_claim_label.py:84-122`. |
| D-4 | `_generated_body_gz_curve` (`kayakgen/eval/stability/evaluator.py:385`) passes `fit_registry=()`. No disk loading anywhere in `high_angle_contracts.py`. | Byte-stability guard: `tests/test_high_angle_stability_evaluator.py:25-42`. |
| D-5 | `kayakgen/services/generative_jobs.py:61-86` — signature `cfd_in_loop_evaluator_status(*, registry, hull_scope, persistent_opt_in=None)`; new module-level `CFDInLoopEvaluatorStatus = Literal["opt_in_only", "first_class"]` at `:39`. | RFC 0058 "CFD-in-loop graduation contract". |
| D-6 | Same function (`generative_jobs.py:75-94`): default `opt_in_only`; requires both `analytical` and `cfd_in_loop` accepted records covering scope; persistent opt-out short-circuits. | `tests/test_cfd_in_loop_evaluator_status.py:34-105`. |
| D-7 | `generative_jobs.py:84-90` reads structural `.kind` (`"analytical"` / `"cfd_in_loop"`) via `getattr`; no schema field added to `StabilityFitRecord`. | `tests/test_cfd_in_loop_evaluator_status.py:21-31` constructs records with `SimpleNamespace`. |
| D-8 | `generative_jobs.py:75-76` — `if persistent_opt_in is False: return "opt_in_only"` placed ahead of graduation check. | `tests/test_cfd_in_loop_evaluator_status.py:95-118`. |

### Stage 3 — CLI sub-app

| Row | Evidence | Maps to |
| --- | --- | --- |
| D-9 | `kayakgen/cli/stability_cli.py` exists; `app.add_typer(stability_app, name="stability")` at `kayakgen/cli/main.py:54`. Four named subcommands present (`ingest-rig-run`, `promote-fixture`, `accept-fit`, `residual-plot`) at `stability_cli.py:54,81,127,164`. | RFC 0058 "CLI surface". |
| D-10 | Each subcommand validates Pydantic records via `model_validate_json`; refuses overwrites via `_write_json_refusing_overwrite` (`stability_cli.py:43-51`); raises `typer.Exit(code=1)` on validation failure (`stability_cli.py:75-77, 120-122, 158-160, 190-192`). No physical sensor ingest, no real fit run. | `tests/test_cli_stability.py:158-188, 232-275, 278-324`. |
| D-11 | `_residual_plot_svg` (`stability_cli.py:196-227`) emits SVG with `fit_id`, `hull_class`, and the four metrics — no curve data. | `tests/test_cli_stability.py:327-342`. |
| D-12 | `stability_cli.py:39-40` defines `_DEFAULT_FIXTURES_DIR = Path("data/stability/fixtures")` and `_DEFAULT_FITS_DIR = Path("data/stability/fits")`. `.gitignore` adds `data/stability/`. Tests use `tmp_path` (`test_cli_stability.py:158, 196, 282`). | See **Finding F-2** for the `.gitignore` scope. |

### Stage 3 — read-model wiring

| Row | Evidence | Maps to |
| --- | --- | --- |
| D-13 | `kayakgen/ui/web/generate_frontier_view.py:29-32` imports `resolve_analytical_claim_label`; `_resolve_claim_label_color_token` (`:207-225`) calls it with `fit_registry`; `build_frontier_view_model` accepts `fit_registry=()` (`:230`); scatter and table rows carry `claim_label_color_token` (`:307, :328`); `refresh_frontier_view` passes `fit_registry=()` (`:554`); CSS map at `:84-92` reuses `state-success` / `state-raw` tokens; emitter at `:594-597`. No new claim-state literal, no new theme token. | `tests/test_generate_frontier_view.py:208-247`. |
| D-14 | `kayakgen/ui/web/generate_spec_form.py:798-814` builds `HullFamilyScope` from `base_hull`; `refresh_cfd_in_loop_status` (`:818-826`) calls `cfd_in_loop_evaluator_status(registry=(), hull_scope=scope)`; `render_spec_form_section` (`:874-878`) invokes it; the acknowledgement `VCheckbox` carries `v_show=("generative_cfd_in_loop_status === 'opt_in_only'",)` at `:1101-1104`. Toggle row above is unchanged. | `tests/test_generate_spec_form.py:330-359`. |
| D-15 | `refresh_cfd_in_loop_status` passes `registry=()` and no `persistent_opt_in`, so the form-builder relies on the default (`persistent_opt_in=None`). RFC 0046's persistent-setting API is untouched. | RFC 0058 "Read-model wiring". |

### Stage 3 — NB-1 stepped-clock seam (workflow 0054 carry-over)

| Row | Evidence | Maps to |
| --- | --- | --- |
| D-16 | `kayakgen/ui/web/generate_state_listener.py:60-95` — `time_provider` and `clock_step` parameters on `install_generate_state_listener`; `_PollHandle.clock` defaults to `time.monotonic`; when `clock_step is not None` no thread is started; `_refresh_jobs` and `_wrap_manual_refresh` use `handle.clock()` instead of `time.monotonic()` at `:183, :209, :225`. | RFC 0058 D-16 spec. |
| D-17 | `tests/test_generate_state_listener.py:285-523` adds stepped-clock variants for cadence (`test_stepped_clock_running_cadence_refreshes_each_tick`), idle (`test_stepped_clock_idle_cadence_refreshes_each_tick`), terminal-detail one-shot, coalesce (`test_stepped_clock_listener_coalesces_nearby_manual_refresh`), and reinstall (`test_stepped_clock_reinstall_replaces_handle`). Existing wall-clock tests untouched. `_ban_sleep` enforces "no `time.sleep` in stepped mode". | RFC 0058 D-17 spec. |

### Docs and gates

| Row | Evidence | Notes |
| --- | --- | --- |
| D-18 | RFC 0058 status `landed` (line 3), stages-2-3 implementation note added (lines 28-38), Open Questions section rewritten with Q1-Q5 (lines 314-336) — Q3 and Q5 marked resolved, Q1/Q2/Q4 deferred, first-promotion gate preserved in stage 4 caveat (lines 13-16). | Self-consistent with D-21 deferrals. |
| D-19 | `docs/DECISION_LOG.md:57` adds D039 (persistent-opt-out-wins + `fit_kind` deferral). `docs/ROADMAP.md:145` flips Stability calibration acceptance track to `landed`. | One artefact slightly off: D039 is inserted between D038 and the next sequential row D035 (which is the existing row above), so the visual ordering reads D038 → D039 → D035 → D034 → ... This is a doc-ordering oddity in the existing decision-log file (descending elsewhere), not a workflow regression — but worth a quick follow-up to keep the file scannable. Out of scope for this verdict. |
| D-20 | No new safety / seaworthiness / final-prediction / design-fitness wording in any modified file. SVG copy in `stability_cli.py:215` reads `"validation_candidate vs reference"` — already in the pre-vetted vocabulary. `CFD_IN_LOOP_ACK_LABEL` byte-stable (test at `tests/test_generate_spec_form.py:313-317`). | — |
| D-21 | No EvaluatorVersion struct, no `expires_at`, no fit-kind field on `StabilityFitRecord`, no real fit ingest, no per-point hover, no RFC 0046 changes. | Confirmed via diff scan; no surface added to `kayakgen/eval/stability/accepted_fit.py` in this workflow. |

## Findings

### F-1 (minor): undocumented backward-compat shim for `kayakgen stability <hull>`

`kayakgen/cli/main.py` previously hosted `@app.command()` named
`stability` (initial-stability evaluator). Registering the new
`stability_app` under the same name conflicts with that command at
Typer registration time, so the workflow:

1. Re-decorated the original function as
   `@stability_app.command("legacy", hidden=True)` at `main.py:505`.
2. Introduced a custom `LegacyStabilityGroup(TyperGroup)` in
   `stability_cli.py:16-30` whose `parse_args` rewrites
   `kayakgen stability <hull-path>` to `kayakgen stability legacy <hull-path>`
   when the first positional doesn't match a registered subcommand.

This is a real engineering decision (preserves the existing CLI surface
for downstream callers) but it is not anchored to any row in
STAGE_2_3_DECISIONS.md. D-9 says "Four subcommands" — the actually-landed
sub-app has four visible + one hidden `legacy` shim. The choice is sound
(the alternative was breaking `kayakgen stability hull.json` for
existing users), but a successor docs sync should add a D-row (or extend
D-9) recording the shim's existence and lifecycle.

Severity: minor. The shim is `hidden=True`, the routing helper is
narrowly scoped, and there is no observable breakage in the public CLI
contract.

Suggested follow-up (out of scope for this workflow): extend D-9 (or add
a D-22) noting "the prior top-level `stability` command is preserved as
a hidden `legacy` subcommand of the new sub-app via a custom TyperGroup;
remove when no downstream caller depends on it."

### F-2 (very minor): `.gitignore` broader than D-12 specifies

D-12 specifies `data/stability/fixtures/` and `data/stability/fits/`
gitignored. The diff adds `data/stability/` (the parent). Effect is the
same plus any sibling, but it widens the ignore footprint silently. No
behavioural impact in this workflow because no other `data/stability/`
sibling exists. Suggested follow-up: tighten to the two named subdirs,
or extend D-12 to authorise the broader pattern. Either is fine.

Severity: very minor.

### F-3 (advisory): `tick_generate_state_listener` and `GENERATIVE_REFRESH_COALESCE_SECONDS` re-export are unmentioned but consistent with D-16/D-17

D-16 introduces the seam parameters but doesn't name the test-driver
function. The workflow adds `tick_generate_state_listener` (a public
function on the module, exported in `__all__` at
`generate_state_listener.py:278`) and re-exports
`GENERATIVE_REFRESH_COALESCE_SECONDS` in the test import path. These are
mechanical enablers of D-16/D-17 (the seam needs a synchronous driver
to be usable). Calling it out as a minor scope expansion for the record;
no action required.

Severity: advisory only.

## Scope creep check (negative findings)

Walked every diff hunk for content that doesn't anchor to a decision
row. Items confirmed absent:

- No real measured-data ingest, no real fit computation, no real
  residual plotting.
- No `EvaluatorVersion`, no `expires_at`, no `fit_kind` field on
  `StabilityFitRecord` (D-21 deferrals intact).
- No safety / seaworthiness / final-prediction / design-fitness wording
  in CLI output, SVG content, UI strings, docs, or test assertions.
- No new claim-state literal beyond the two named in RFC 0058.
- No theme token additions in `kayakgen/ui/theme.py` (D-13 reuse).
- No change to RFC 0046's persistent-setting API (D-15).
- No fixture promoted, no fit accepted in this workflow.
- Default `unvalidated_hydrostatic_comparison` byte-stability preserved
  for the wired call site (`tests/test_high_angle_stability_evaluator.py`).
- Default `opt_in_only` byte-stability preserved for the form (initial
  state at `generate_spec_form.py:778` and computed result with
  empty registry).
- Existing forbidden-claim, ui-theme-orphan-scan, import-boundary-scan,
  and services-boundary-scan gates unmodified.

## Verdict

`accept_with_findings`. The implementation faithfully traces to all 21
decision rows and to RFC 0058's acceptance criteria. The two findings
are docs-only (F-1 is a backward-compat shim that should be named in a
decision row; F-2 is a `.gitignore` widening). Neither blocks the
landing; both deserve a follow-up docs sync, ideally rolled into the
next workflow that touches stability CLI or docs.
