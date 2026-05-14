author: reviewer-traceability-claude-opus-4.7-002
kind: finding
logical_name: review
schema_version: striatum.finding.v1
run: run_c1de081e76f14cd1a81194e306338ac2
session: sess_c19ee602ae4c4d68b90d06c059f4b654
job: job_run_c1de081e76f14cd1a81194e306338ac2_review_traceability
lease: lease_d3cdf6785fb64bc3bd3e15d79550d444
date: 2026-05-14

# Review - Traceability for Workflow 0048 Successor RFC Backlog

## Verdict Intent

`accept_with_findings`

Every proposed RFC in the 0036-0043 set traces to either a named workflow
0047 final-review finding (FR1-FR4 in
`striatum/0047-ui-follow-up-cleanup/final/FINAL_REVIEW.md`) or to an
explicit deferred backlog item in
`docs/workflows/0018-deferred-backlog/QUEUE.md` plus a predecessor RFC
named in `docs/workflows/0048-successor-rfc-backlog/SOURCES.md`. The
three RFC scoping artifacts under
`striatum/0048-successor-rfc-backlog/rfc_*` are internally consistent
with the drafted RFCs and with the workflow 0047 ledger at
`striatum/0047-ui-follow-up-cleanup/ledger/FINDINGS.md`.

No proposed RFC promotes a deferred capability (real solver, calibrated
resistance, real high-angle `GZ`, watertight readiness, web-side
mesh-package authoring, or hosted CFD) into landed behavior; each
explicitly preserves RFC 0024, RFC 0025, and RFC 0027 claim/handoff
gates. All eight drafts carry `Status: proposed` and `Date: 2026-05-14`,
which matches the workflow-level expectation that the RFC index update
is owned by the integration job rather than these RFC drafts (recorded
in `striatum/0048-successor-rfc-backlog/rfc_ui/RFC_SCOPE_UI.md`).

The findings below are non-blocking traceability gaps the integrator
and later workflows should resolve. None block landing the RFC drafts.

## Source Mapping

| RFC | Primary source(s) | Notes |
| --- | --- | --- |
| 0036 Trame Seed Listener Proof | W0047 FR1 (`FINAL_REVIEW.md:31-56`); ledger F2 (`FINDINGS.md:76-107`) | Two-outcome scope (retain with browser proof or remove) matches the ledger's stated "remove the branch or add a focused event-sequence test." |
| 0037 Export Row Schema Consolidation | W0047 FR2 (`FINAL_REVIEW.md:58-72`); ledger F3 (`FINDINGS.md:109-141`) | Acceptance preserves byte-identical subtitles and the conservative `subtitle`/`description` collapse path. |
| 0038 Export Menu Disabled Copy Polish | W0047 FR3 (`FINAL_REVIEW.md:74-81`); ledger F3 deferred polish (`FINDINGS.md:130-134`, `301`) | The deferred `Mesh package...` label change is explicitly the W0047 ledger "optional and requires an explicit changelog note" item. |
| 0039 Web Snapshot Schema Unification | W0047 FR4 (`FINAL_REVIEW.md:83-98`); ledger F4 (`FINDINGS.md:143-172`) | Preserves REST shapes and legacy aliases (`cfd_status`, `status`, `cfd_payload`, etc.) without route changes. |
| 0040 Closed-Volume Solver Readiness Roadmap | QUEUE.md 0027 closed-volume contract and 0028 real CFD adapter (`QUEUE.md:92-158`); RFCs 0010, 0015, 0016, 0021, 0022, 0023, 0026, 0028 (`SOURCES.md:19-25`) | Roadmap layered above existing closed-volume/solver-readiness RFCs; no runtime behavior. |
| 0041 Real CFD Adapter Successor | QUEUE.md 0028 real CFD adapter (`QUEUE.md:126-158`); RFC 0017 (`SOURCES.md:20`); RFC 0026 fixture adapter; RFC 0025/0027 claim gates | Explicitly consumes RFC 0040's profile gate when watertight input is required. |
| 0042 Resistance Calibration Fixture Successor | QUEUE.md 0030 resistance calibration fixture (`QUEUE.md:196-225`); RFC 0019 (`SOURCES.md:21`); RFC 0027 acceptance gate | Maps source-use verdicts onto the existing RFC 0027 `SourceUse` enum rather than creating a parallel taxonomy. |
| 0043 High-Angle GZ Successor | QUEUE.md 0031 high-angle GZ (`QUEUE.md:227-257`); RFCs 0020, 0024 (`SOURCES.md:22, 24`) | Preserves the RFC 0024 unavailable boundary; defers heeled-integration model decisions to a later workflow. |

## Findings

Ordered by severity. None block landing the RFC drafts; each is a
traceability or successor-relationship clarification that the
integrator or a follow-up RFC index update should land.

### FT1 - Successor RFCs do not name the disposition of their predecessor RFCs (medium)

RFC 0041 declares itself "successor to RFC 0017"; RFC 0042 declares
itself "successor to RFC 0019"; RFC 0043 declares itself "successor to
RFC 0020 and RFC 0024." In every case the predecessor is either still
`proposed` (0017, 0019, 0020) or `landed` only as a partial slice
(0024). None of the new RFCs explicitly state whether the predecessor
RFC should be marked `superseded`, `revised`, or kept `proposed` and
narrowed by reference.

The RFC index in `docs/rfcs/README.md:33-44` is the only place this
disposition is tracked. Without an explicit successor relationship in
the RFC text, the integrator (or a later reader) has to infer status
changes from context. The W0048 RFC scoping artifact for UI
(`rfc_ui/RFC_SCOPE_UI.md`) already records that "the RFC index was not
updated; that remains owned by the integration job"; the
geometry/solver and calibration/stability scoping artifacts make no
equivalent statement.

Why this matters: the project already has a working pattern for
explicit supersedes/revises wording. RFC 0031 supersedes RFC 0029
(`docs/rfcs/README.md:146-148`) and RFC 0032 revises the RFC 0030
successor path (`docs/rfcs/README.md:160-165`). Reusing that pattern
for the new successor RFCs would prevent the same status-mismatch
class of bug the ledger explicitly warns about.

How to apply (integrator or follow-up): either add a one-line
"Disposition of predecessor" paragraph to RFCs 0041, 0042, and 0043,
or record the predecessor disposition in the RFC index update commit
alongside the 0036-0043 listings.

### FT2 - RFC 0040 is a roadmap aggregating eight RFCs but does not name its index status (medium)

RFC 0040 explicitly consolidates the closed-volume/solver-readiness
dependency spine of RFC 0010, RFC 0015, RFC 0016, RFC 0021, RFC 0022,
RFC 0023, RFC 0026, and RFC 0028. The RFC index entries for those RFCs
in `docs/rfcs/README.md:26-44` already describe their landed slices,
and `docs/rfcs/README.md:136-144` already calls the closed-volume side
a dependency spine. RFC 0040 is therefore a meta-roadmap rather than a
peer RFC.

The RFC text does not say whether it should be indexed as a roadmap, a
proposed scope, a supersession of the older RFCs, or a parent that
those RFCs should later cite back. The current `Status: proposed` line
treats it like any other peer RFC, which risks future readers
treating RFC 0040 as a competing scope rather than as the integration
view.

Why this matters: the project's README explicitly tracks the
closed-volume dependency spine narrative
(`docs/rfcs/README.md:136-144`). If RFC 0040 lands as a peer "proposed"
RFC without a marker, that narrative now lives in three places: the
README spine paragraph, RFC 0040, and each underlying RFC. Drift is
then the default.

How to apply (integrator or follow-up): add a one-line "Index
treatment" note to RFC 0040 stating it is a roadmap layered above the
named RFCs and does not supersede them, then update
`docs/rfcs/README.md` to either (a) replace the spine paragraph with a
pointer to RFC 0040, or (b) extend the spine paragraph with a "See RFC
0040 for the full readiness ladder." line.

### FT3 - RFC 0036 acceptance criteria allow both retention and removal but do not state how the decision is recorded (low)

RFC 0036 acceptance criteria
(`docs/rfcs/0036-trame-seed-listener-proof.md:68-82`) correctly mirror
the W0047 FR1 two-outcome path: keep `_state_matches_preset_seed` only
with a browser-driven proof, or remove it and keep regression coverage.
The RFC does not say where the chosen outcome is recorded
(implementation patch summary, ledger, or final-review verdict line).
The W0047 ledger expected "a focused test documenting the exact
reachable same-value/seed event sequence" if retained
(`FINDINGS.md:95-98`); RFC 0036 does not require that the test name or
test docstring carry the same wording.

Why this matters: if the implementation lane chooses to retain the
branch but the browser proof later regresses or is deleted, the
RFC-level audit trail of "which acceptable outcome was chosen and why"
disappears.

How to apply (later implementation workflow): require the patch
summary or final-review artifact to record (a) the outcome chosen,
(b) the browser test path if retained, and (c) the deleted helper line
range if removed.

### FT4 - RFC 0038 references but does not constrain the adjacent disabled-row subtitle (low)

RFC 0038 proposes the visible label change to `Mesh package (CLI only)`
and notes ("Open Questions" §) that the disabled-row subtitle "may
continue to point users to `kayakgen mesh-package`." The W0047 final
review (`FINAL_REVIEW.md:76-80`) and the W0047 ledger
(`FINDINGS.md:130-134`) explicitly fold the disabled-row subtitle into
the same row schema RFC 0037 is consolidating. RFC 0038 does not say
whether updating the label requires touching the subtitle in the same
workflow, or whether the subtitle is locked by RFC 0037.

Why this matters: the row schema lives in one literal
(`EXPORT_MENU_ROWS`), and a workflow that lands RFC 0038 alone could
ship a label/subtitle copy mismatch.

How to apply (later implementation workflow): cite RFC 0037 in the
implementation acceptance, and require the patch summary to record the
exact subtitle value carried into the renamed row.

### FT5 - RFC 0041 mesh-readiness gates name RFC 0040 as a dependency but RFC 0040 is still proposed (low)

RFC 0041 §Dependencies and §Mesh Readiness require
`watertight_solid_resistance_v1` evidence that satisfies the RFC 0040
profile gate
(`docs/rfcs/0041-real-cfd-adapter-successor.md:69-77`, `168-179`).
RFC 0040 is itself only `proposed` and explicitly says it contains no
runtime implementation. The two RFCs therefore form a hard
implementation-order constraint that is documented as a dependency
line but not as an explicit blocking acceptance criterion.

Why this matters: the workflow queue
(`docs/workflows/0018-deferred-backlog/QUEUE.md:126-158`) already says
real adapter work depends on closed-volume work. If RFC 0041 lands
implementation before RFC 0040's readiness report exists, the adapter
may fall back to fixture evidence in a way that hides the gate.

How to apply (later implementation workflow): RFC 0041 acceptance
criteria should include an explicit prerequisite that RFC 0040's
readiness ladder (or its predecessor RFC 0023 watertight-handoff
evidence) is accepted before any real solver `succeeded` state is
allowed for a watertight-required profile.

### FT6 - RFC 0042 source-use verdict list adds a new terminal value (low)

RFC 0042 §Source Review Packet lists five source-use verdicts
(`citation_only`, `validation_candidate`, `validation_fixture`,
`calibration_fixture_candidate`, `calibration_fixture`) plus a terminal
`rejected` outcome. The RFC says these "must map losslessly onto the
existing RFC 0027 `SourceUse` values." RFC 0027 is named as a
dependency but RFC 0042 does not enumerate RFC 0027's current
`SourceUse` values inline, so the mapping is implied rather than
visible.

Why this matters: a later implementation workflow could mis-map
`validation_candidate` (a review-time state) onto RFC 0027 enum members
intended for runtime use, or could add `rejected` to the runtime enum
even though RFC 0042 explicitly says `rejected` is a review outcome
and not a runtime source-use value.

How to apply (later implementation workflow): include the RFC 0027
`SourceUse` enum members verbatim in the review packet, and add a test
that fails if any new review verdict cannot be expressed in the
existing enum.

### FT7 - Scoping artifacts split byline conventions (very low)

The three RFC scoping artifacts under
`striatum/0048-successor-rfc-backlog/rfc_*` use three different
self-declared author identifiers
(`rfc-scoper-codex-gpt-5.5-007`, `-008`, `-009`) without front-matter
indicating the model-run mapping. This is internally consistent, and
the work-packet author lines (`author: operator`) are correct for the
review artifacts, but the scoping artifact bylines do not match the
W0047 scoping-author style used in
`striatum/0047-ui-follow-up-cleanup/ledger/FINDINGS.md:1`. Cosmetic;
flagged only because the workflow byline rule is a stated gate in the
work packet.

How to apply (operator): no action required for this review; future
scoping packets may want a single byline convention to keep
traceability artifacts consistent.

## Scope And No-Claims Verification

Spot-checked each RFC's Non-Goals/No-Claims sections against
`striatum/0047-ui-follow-up-cleanup/ledger/FINDINGS.md:249-269` and the
existing forbidden-copy/persistent-copy test surface:

- RFCs 0036, 0037, 0038, 0039 each restrict themselves to web UI
  presentation/schema; none imply new REST routes, backend capability,
  hosted services, solver behavior, mesh-package authoring, or
  readiness promotions.
- RFC 0040 explicitly preserves RFC 0025 claim gates and forbids
  promotion of synthetic/open/fixture evidence to watertight readiness;
  it does not validate solver outputs.
- RFC 0041 keeps every real-solver output `raw_unvalidated`; explicitly
  rejects calibrated CFD, final prediction, design fitness, container
  execution, and hosted workers.
- RFC 0042 keeps current resistance output uncalibrated, keeps
  fixture-local-command results raw, and forbids treating CFD fixture
  adapter output as measured hydrodynamic data.
- RFC 0043 preserves RFC 0024's unavailable boundary; no `GZ`,
  `GZ_max`, capsize range, or seaworthiness claim is implied.

No proposed RFC contradicts the workflow 0047 forbidden-copy or
persistent-copy gates named in `FINDINGS.md:294-297`.

## Status And Acceptance-Criteria Spot Check

- All eight RFCs carry `Status: proposed` and `Date: 2026-05-14`.
- Each RFC includes Goals, Non-Goals, Proposal, Acceptance Criteria,
  Open Questions, Implementation Path, and Domain Modeling sections
  per the RFC 0001 template (`docs/rfcs/0001-template.md`).
- Acceptance criteria are concrete enough to drive a future
  implementation workflow except where flagged above (FT3, FT5, FT6).
- No RFC contains numerical claims, calibrated wording, watertight
  promotion, or hosted-service language.
- The RFC index in `docs/rfcs/README.md` is not yet updated; the UI
  RFC scoping artifact explicitly defers that to the integration job,
  which is the correct ordering.

## Residual Risk

The largest residual risk is the predecessor-disposition gap captured
in FT1 and FT2. If the integration job lands RFC 0036-0043 in the index
without an explicit supersedes/revises/roadmap marker, a future
workflow could reopen the same scope under the older RFC numbers
(0017, 0019, 0020) and waste review effort. The fix is small (one
paragraph per successor RFC plus an index-paragraph touch) and belongs
in the integration job or a focused follow-up.
