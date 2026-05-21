# Review Prompt — workflow 0056

You are reviewing one slice of workflow 0056 — RFC 0058 stages 2 +
3 + workflow 0054's NB-1 successor. Read `STAGE_2_3_DECISIONS.md`,
RFC 0058, every implementation patch summary, the integration
patch summary, the docs-sync patch summary, and the changed files.

Your review responsibility depends on your role:

**Traceability reviewer** — Trace every decision row in
`STAGE_2_3_DECISIONS.md` to a concrete file/line in the patch.
Verify that:
- `resolve_analytical_claim_label` lives where D-1 says and is
  exported from `kayakgen/eval/stability/__init__.py`;
- `result_semantics` Literal widening matches D-2 exactly;
- `cfd_in_loop_evaluator_status` lives where D-5 says and accepts
  the three named arguments in D-5;
- the CLI sub-app exposes exactly the four subcommands in D-9;
- the integrator wires both contracts at the call sites named in
  the integrate prompt;
- the docs-sync touches exactly the files listed in `docs_sync.md`
  and flips RFC 0058 status correctly;
- the NB-1 seam matches D-16 (opt-in keywords, defaults preserve
  existing behavior).

**Claims-and-boundaries reviewer** — Verify that no new
claim-state literal, safety claim, seaworthiness claim, calibrated
claim, or final-prediction claim is introduced. Re-run (mentally
or via grep) the forbidden-claim scan list against every changed
file. Confirm the frontier-view colour wiring only uses the two
existing theme tokens (`kg-state-validated`, `kg-state-raw`).
Confirm the form-builder acknowledgement copy is unchanged in
`opt_in_only` mode (the default with empty registry).

**Ops/tests reviewer** — Run the full repo suite minus the
env-gated OpenFOAM smoke. Run ruff. Run any boundary scans the
repo provides (forbidden-claim, ui-theme-orphan, import-boundary,
services-boundary). Confirm focused tests cover every contract
branch, every CLI subcommand happy/refuse path, the frontier-view
colour wiring, the form-builder hide branch, and the NB-1 clock-
seam variants. Verify the existing wall-clock tests in
`tests/test_generate_state_listener.py` still pass.

The verdict vocabulary is `accept`, `accept_with_findings`,
`needs_revision`, or `reject`. Use `accept_with_findings` only
when a finding is non-blocking; use `needs_revision` when any
decision row in `STAGE_2_3_DECISIONS.md` is unmet or any boundary
scan is broken. Publish a finding artifact with proper
`striatum.finding.v1` front matter and your verdict.
