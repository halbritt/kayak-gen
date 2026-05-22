# Operator / Adoption Audit — Findings

Date: 2026-05-22
Lane: Operator / adoption
Auditor: Claude Opus 4.7 (single-agent run via Explore subagent + main-thread verification)
Scope: `full_repo` preset, current `main` at commit f78e478
Sources of truth read: `README.md`, `docs/USER_GUIDE.md`, `pyproject.toml`,
`kayakgen/cli/main.py`, `kayakgen/cli/{runs_cli,stability_cli,target_workflows,sensitivity_cli,design_report_cli,migrate_geometry_cli}.py`,
`kayakgen/ui/{desktop,theme}.py`,
`kayakgen/ui/web/{generate_spec_form,generate_frontier_view,controllers,app}.py`,
`kayakgen/services/{cfd_jobs,generative_jobs}.py`,
`kayakgen/eval/cfd/job_store.py`.

## Findings

### AUD-O-001: `kayakgen mesh-evidence` is wired in the CLI but missing from `docs/USER_GUIDE.md`

severity: high
category: docs_drift
status: open
claim: `kayakgen mesh-evidence` is a documented RFC 0045 surface that runs
a real snappyHexMesh-evidence harness; it is gated on
`KAYAKGEN_OPENFOAM_LOCAL_RUN` and emits structured `binding_code` error
tokens. None of this appears in the USER_GUIDE; only `mesh-package` is
documented in the Mesh-and-CFD-readiness section.
evidence:
- `kayakgen/cli/main.py:229` — `@app.command("mesh-evidence")` with body
  spanning to line ~315.
- `kayakgen/cli/main.py:279` — emits `mesh-evidence refuses to run: set ...`
  error with internal `binding_code` token.
- `docs/USER_GUIDE.md` — `grep "mesh-evidence"` returns no results
  (verified); only `mesh-package` (line 536) and the cfd subgroup (line
  603+) are documented.
- `docs/rfcs/0045-ordinary-package-solver-readiness-promotion.md` — names
  the command.
impact: Operators discover the command via `kayakgen --help` but cannot find
the preconditions, the env-var gate, or recovery from the `binding_code`
errors anywhere in the guide.
recommended_action: Add a `#### mesh-evidence (RFC 0045)` subsection under
`## Mesh And CFD Readiness Caveats` that documents the env-var gate, the
three-mechanism opt-in cross-reference, and one example invocation.
follow_up: docs fix (driven by this remediation plan).

### AUD-O-002: USER_GUIDE documents only the env-var opt-in for OpenFOAM; the RFC 0046 three-mechanism contract is invisible

severity: high
category: docs_drift
status: open
claim: RFC 0046 specifies three opt-in mechanisms ranked by precedence
(profile flag, persistent setting, env knob). The USER_GUIDE only mentions
`KAYAKGEN_OPENFOAM_LOCAL_RUN`. Operators reading the guide cannot discover
the more auditable `--allow-real-solver-execution` flag on
`kayakgen cfd prepare` or the persistent `~/.config/kayakgen/cfd.json`
setting; the structured opt-in audit trail RFC 0046 ships becomes
unreachable from documentation.
evidence:
- `docs/rfcs/0046-non-env-gated-openfoam-succeeded-path.md:69-85` — names
  three mechanisms ranked by precedence.
- `docs/USER_GUIDE.md:660` — documents `KAYAKGEN_OPENFOAM_LOCAL_RUN` only;
  no mention of `--allow-real-solver-execution` or `cfd.json` (verified
  via grep).
- `kayakgen/cli/main.py:414-421` — `cfd_prepare` exposes
  `--allow-real-solver-execution` with no RFC 0046 cross-reference in its
  help text.
- `kayakgen/eval/cfd/job_store.py` — reads
  `~/.config/kayakgen/cfd.json` for the persistent path.
impact: The preferred (most explicit, most auditable) mechanism is invisible;
operators using the env knob get no information about the precedence rules
that would help them debug a flag-set-but-env-unset situation.
recommended_action: In the `### cfd prepare` and "Opt-in environment
variables" sections of USER_GUIDE, document all three mechanisms with their
precedence order and cross-reference RFC 0046.
follow_up: docs fix (driven by this remediation plan).

### AUD-O-003: Web Generate-panel form labels are raw JSON parameter names

severity: medium
category: operator_ergonomics
status: closed (RFC 0060 + workflow 0033, see CHANGELOG ### Fixed)
claim: The web Generate-panel form uses raw hull-JSON parameter names
(`beam_wl_m`, `Cp`, `center_box_ratio`) as field labels in the
variable-selector picklist, with no tooltips or user-facing glossary. The
desktop GUI has user-friendly labels for the same parameters
("Beam WL (m)", "Prismatic Coeff").
evidence:
- `kayakgen/ui/web/generate_spec_form.py:86-92` — `BASE_HULL_KEYS` tuple
  lists JSON parameter names verbatim.
- `kayakgen/ui/desktop.py:83-96` — `SLIDERS` table has friendly labels.
- `kayakgen/ui/web/generate_spec_form.py:1016-1050` — objective metrics
  picklist shows raw metric names with no description.
impact: A non-developer kayak designer using the web workspace has to
cross-reference the hull JSON spec to understand what each variable
controls; the desktop GUI has the better UX and the gap is visible to
anyone who uses both.
recommended_action: Define a small label-and-description map for the
Generate-panel form (could reuse the desktop `SLIDERS` table); render it
as field labels + tooltips.
follow_up: implementation_gap → new RFC (UX-scope, not a quick fix).

### AUD-O-004: `kayakgen runs list` / `runs jobs` print tab-separated columns with no header

severity: medium
category: operator_ergonomics
status: closed (workflow 0032, see CHANGELOG ### Fixed)
claim: `runs_list_command` and `runs_jobs_command` write tab-separated rows
with no header row and no `--header` flag. The `--filter key:value` help is
terse and does not enumerate valid keys.
evidence:
- `kayakgen/cli/runs_cli.py:59-62` — `f"{row['run_id']}\t{row['kind']}\t..."`.
- `kayakgen/cli/runs_cli.py:144-149` — same pattern.
- `kayakgen/cli/runs_cli.py:74-76` — "Filter as key:value (eq only); may be
  repeated" with no key list.
impact: Operator piping to `awk` has to deduce column order from source;
operator using `--filter` has to guess valid keys or read the SqliteIndex
schema.
recommended_action: Add `--header` flag (default off for backward
compatibility), enumerate valid `--filter` keys in the help text and in
USER_GUIDE.
follow_up: implementation_gap → small workflow (CLI + USER_GUIDE).

### AUD-O-005: `mesh-evidence` error message names `binding_code` but does not cross-reference RFC 0046

severity: medium
category: operator_ergonomics
status: closed (workflow 0032, see CHANGELOG ### Fixed)
claim: When the env var is missing, the command emits
`mesh-evidence refuses to run: set KAYAKGEN_OPENFOAM_LOCAL_RUN=1 in the
operator shell ...` and a `binding_code: openfoam_local_run_env_required`
token. The message explains the env var but does not mention the other two
RFC 0046 mechanisms, so an operator who would prefer the auditable
`--allow-real-solver-execution` path has no breadcrumb to it.
evidence:
- `kayakgen/cli/main.py:273-291` — the error-emission block.
- `kayakgen/cli/main.py:241-248` — command docstring explains the env
  precondition without naming RFC 0046 or the three mechanisms.
impact: Operators are pushed onto the env-knob path even when the flag
path is preferred for their context (e.g. CI runs that want a per-job
audit trail).
recommended_action: Add one line to the error message naming RFC 0046 and
the three mechanisms; same fix to the docstring.
follow_up: source change (small slice, three lines).

### AUD-O-006: `cfd prepare` success path emits `status: pending` with no next-step guidance

severity: low
category: operator_ergonomics
status: closed (workflow 0032, see CHANGELOG ### Fixed)
claim: After a successful prepare, the CLI echoes `wrote <dir>` and
`status: pending` followed by the raw-CFD warning, but never names
`kayakgen cfd run <dir>` as the next step or the three opt-in mechanisms
that may need to be configured first.
evidence:
- `kayakgen/cli/main.py:438-441` — echo block.
- `kayakgen/cli/main.py:441` — `CFD_RAW_RESULTS_WARNING` is the only
  trailing message.
impact: Operator-facing onboarding friction; not a correctness issue.
recommended_action: Append one line: "Next: `kayakgen cfd run <dir>`. The
real-solver path requires an RFC 0046 opt-in (env / flag / persistent)."
follow_up: source change (one line) + docs fix.

### AUD-O-007: `kayakgen stability legacy` is `hidden=True` by design (D040); USER_GUIDE should record the rationale

severity: low
category: operator_ergonomics
status: open
claim: D040 records that the legacy `kayakgen stability <hull>` form is
preserved via a hidden `legacy` subcommand + Typer parse shim. The
DECISION_LOG row is correct; the USER_GUIDE does not note that
`stability --help` will not show the most-common invocation form an existing
user already knows. A new reader looking only at `--help` will think the
legacy command is gone.
evidence:
- `docs/DECISION_LOG.md:58` — D040 records the routing shim and intent.
- `kayakgen/cli/stability_cli.py:16-31` — `LegacyStabilityGroup` router.
- `kayakgen/cli/main.py:505` — `@stability_app.command("legacy", hidden=True)`.
- `docs/USER_GUIDE.md:148-195` — the stability section does not mention
  the routing shim or the `legacy` subcommand.
impact: Low — the legacy form still works. But surprise factor is real:
`--help` shows four new subcommands and hides the one that "used to be"
the command.
recommended_action: Add one sentence to the stability USER_GUIDE section:
"The bare-form `kayakgen stability hull.json` invocation is preserved via
a hidden `legacy` subcommand (see D040); `kayakgen stability --help`
intentionally hides it to surface the new RFC 0058 sub-app."
follow_up: docs fix (driven by this remediation plan, paired with AUD-D-002).

### AUD-O-008: No file-based artifacts used as control plane

severity: info
category: operator_ergonomics
status: open
claim: Lane 3 looked specifically for places where operators have to
manually edit a JSON for the pipeline to advance (the
"file-as-control-plane" anti-pattern named in RFC 0059 §2). None found.
CFD `profile.json` carries the `allow_real_solver_execution` flag but the
write surface is the CLI flag, not direct file editing; manifest JSONs are
inputs, not control plane.
evidence:
- `kayakgen/eval/cfd/job_store.py` — reads profile.json but the write
  surface for the opt-in field is `kayakgen cfd prepare
  --allow-real-solver-execution`.
- No `cfd.json` / `profile.json` instruction in USER_GUIDE asks the
  operator to hand-edit a file to advance the pipeline.
impact: None — recording the null finding so future audits can confirm.
recommended_action: None.
follow_up: wontfix (positive null finding).
