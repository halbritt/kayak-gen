# Docs / Decision-Drift Audit — Findings

Date: 2026-05-22
Lane: Docs / decision drift
Auditor: Claude Opus 4.7 (single-agent run via Explore subagent + main-thread verification)
Scope: `full_repo` preset, current `main` at commit f78e478
Sources of truth read: `docs/SPEC.md`, `docs/PRD.md`, `docs/DECISION_LOG.md`
(rows D001-D040), `docs/ROADMAP.md`, `docs/USER_GUIDE.md`,
`docs/ARCHITECTURE_MAP.md`, `docs/UBIQUITOUS_LANGUAGE.md`,
`docs/RELEASE_DISCIPLINE.md`, `docs/rfcs/README.md`, `CHANGELOG.md`,
`tests/test_vocabulary_coverage.py`, `kayakgen/cli/` subcommand modules.

## Findings

### AUD-D-001: `docs/ARCHITECTURE_MAP.md` is dated 2026-05-16, three days before RFC 0057 stage 4 and RFC 0058 stages 2-3 landed; the new CLI commands are missing

severity: high
category: docs_drift
status: open
claim: `ARCHITECTURE_MAP.md` carries `Date: 2026-05-16` and its public-CLI
section does not list the `kayakgen runs jobs` subcommand (RFC 0057 stage 4,
landed 2026-05-18) or the four `kayakgen stability {ingest-rig-run,
promote-fixture, accept-fit, residual-plot}` subcommands (RFC 0058 stages 2-3,
landed 2026-05-21). `RELEASE_DISCIPLINE.md` requires `ARCHITECTURE_MAP.md`
updates whenever the CLI list changes.
evidence:
- `docs/ARCHITECTURE_MAP.md:3` — `Date: 2026-05-16`.
- `docs/ARCHITECTURE_MAP.md:132-167` — public-CLI section lists `runs list/query/reindex` but not `runs jobs`; lists no stability subcommands.
- `kayakgen/cli/runs_cli.py` — defines `@runs_app.command("jobs")`.
- `kayakgen/cli/stability_cli.py:120-200` — defines `ingest-rig-run`, `promote-fixture`, `accept-fit`, `residual-plot`.
- `docs/RELEASE_DISCIPLINE.md:53` — checklist item 7 mandates `ARCHITECTURE_MAP.md` updates "when the package layout, CLI list, or durable-artifact table changes".
impact: New contributors orient via `ARCHITECTURE_MAP`. Missing the most
recent CLI commands forces them to triage three different doc surfaces to
build a current mental model; the public-behavior-change checklist that should
have caught this also looks like it wasn't followed for the most recent
landings.
recommended_action: Bump the date header to 2026-05-22, add `runs jobs` and
the four `stability` subcommands to the CLI section, cross-link RFC 0057 / RFC 0058.
follow_up: docs fix (driven by this remediation plan).

### AUD-D-002: `docs/USER_GUIDE.md` stability section documents only the legacy `kayakgen stability hull.json` flow; the four RFC 0058 subcommands are not mentioned

severity: high
category: docs_drift
status: open
claim: The `### stability` section in USER_GUIDE walks through
`kayakgen stability hull.json --out ...` and the `--high-angle-gz` flag, but
does not mention the four RFC 0058 sub-app commands
(`ingest-rig-run`, `promote-fixture`, `accept-fit`, `residual-plot`). The
`calibration` section nearby (line 496+) documents its four analogous
subcommands in detail — the pattern exists; it just wasn't applied to the
stability sub-app when RFC 0058 stages 2-3 landed.
evidence:
- `docs/USER_GUIDE.md:148-195` — `### stability` body covers only the legacy command + `--high-angle-gz`.
- `docs/USER_GUIDE.md:496+` — `### calibration` shows the parallel pattern for the four RFC 0054 subcommands.
- `kayakgen/cli/stability_cli.py` — the four subcommands exist and are not `hidden=True`.
- `docs/DECISION_LOG.md:58` — D040 explicitly notes the legacy/new boundary on the CLI but does not propagate to USER_GUIDE.
impact: Operators trying to land a stability-fit workflow have nothing in the
USER_GUIDE to read; they must read RFC 0058 + the CLI module directly.
recommended_action: Add a `#### Stability fixtures (RFC 0058)` subsection
under the existing `### stability` heading documenting the four-command
workflow, parallel to the calibration subsection.
follow_up: docs fix (driven by this remediation plan).

### AUD-D-003: `docs/UBIQUITOUS_LANGUAGE.md` is missing RFC 0057/0058 aggregate-root terms

severity: medium
category: docs_drift
status: open
claim: `GenerativeJob` (RFC 0057), `StabilityFitRecord` /
`StabilityFixturePromotionPacket` / `MeasuredStabilityFixture` /
`cfd_in_loop_evaluator_status` (RFC 0058) are all absent from the project
glossary. The glossary explicitly says "every term here is *load-bearing*"
and the parallel RFC 0054 aggregates (`TankTestCampaign`,
`IncliningTestRun`, `AcceptedFitRecord`) are present at lines 64-66.
evidence:
- `docs/UBIQUITOUS_LANGUAGE.md` — `grep "GenerativeJob\|StabilityFitRecord\|cfd_in_loop_evaluator_status\|MeasuredStabilityFixture"` returns no results (verified).
- `docs/UBIQUITOUS_LANGUAGE.md:64-66` — established pattern for fit/campaign aggregates.
- `tests/test_vocabulary_coverage.py:73+` — `_DECISION_TOKENS` covers named decision tokens but does not enforce coverage for these new schema-level aggregates (cross-references AUD-P-003).
impact: New work using these terms (e.g. RFC 0057 fork-with-seed lineage,
RFC 0058 stage-4 promotion) drifts from a glossary that is explicitly meant
to be the load-bearing source of truth.
recommended_action: Add glossary rows for `GenerativeJob`,
`StabilityFitRecord`, `StabilityFixturePromotionPacket`,
`MeasuredStabilityFixture`, and `cfd_in_loop_evaluator_status` in the
existing "Sweep, search, and comparison" + "Claim and source vocabulary"
sections.
follow_up: docs fix (driven by this remediation plan) + couple it with the
test-coverage extension from AUD-P-003.

### AUD-D-004: `docs/PRD.md` high-angle GZ section does not surface RFC 0058's analytical-label upgrade contract

severity: low
category: docs_drift
status: open
claim: `docs/PRD.md:76` calls out that "the current surface remains
`unvalidated_hydrostatic_comparison`" and points at RFC 0056 for the rig
design, but does not name the RFC 0058 `StabilityFitRecord` /
`resolve_analytical_claim_label` contract that defines the path from
unvalidated to validated. A reader of the PRD alone cannot answer "what would
it take to graduate the label?" without leaving for RFC 0058.
evidence:
- `docs/PRD.md:75-76` — references RFC 0056 + the unvalidated literal, no mention of RFC 0058.
- `docs/ROADMAP.md:145` — names the RFC 0058 contracts explicitly; PRD does not.
- `docs/DECISION_LOG.md:57-58` — D039 and D040 record RFC 0058 stages 2-3 but PRD does not echo them.
impact: Lowest-severity drift. Surfaces only when someone reads PRD as the
single source for "current and projected scope."
recommended_action: Add one sentence in the relevant PRD bullet:
"RFC 0058's `StabilityFitRecord` + `resolve_analytical_claim_label` define
the path from `unvalidated_hydrostatic_comparison` to
`validated_hydrostatic_comparison` once measured rig data and an accepted fit
land."
follow_up: docs fix.

### AUD-D-005: RFC 0056 README index row reads "landed (schemas only)" but does not name the on-disk module path

severity: info
category: rfc_status
status: open
claim: `docs/rfcs/README.md:73` row for RFC 0056 reads "landed (schemas only)
— MeasuredStabilityFixture schema + validators landed under
`kayakgen/eval/stability/measured_fixture.py`; no fixture promoted by this
RFC". This is correct and complete. Recording as an info-level positive
finding: the RFC index row format demonstrated by 0056 is the standard the
other "partial landed" rows should follow.
evidence:
- `docs/rfcs/README.md:73` — the index row text.
- `kayakgen/eval/stability/measured_fixture.py` — the module exists.
- Compare with `docs/rfcs/README.md:34` (RFC 0017) which uses the shorter
  "proposed background; successor 0041" pattern without naming an on-disk
  artifact — also acceptable, but less informative.
impact: None — recording as a positive example for future RFC index hygiene.
recommended_action: None for RFC 0056. When future audits flag a "landed"
RFC row that does not name the on-disk module(s), this row is the template.
follow_up: wontfix (positive null finding).
