---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-003
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_f3ced6361be64aa19c267dfbfa250e28
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_resistance_source_candidate_claude
lease: lease_ee6d5cd2730e4cb49b157718c8af93c0

# Panel Vote — Resistance Source Candidate

## Vote

**Option A — Edinburgh DataShare full source-review packet, with
`validation_fixture` as the only permitted positive promotion outcome and an
explicit `calibration_fixture` block. Reject Options B, C, and D as the
immediate decision.**

## Decision Sentence For `docs/DECISION_LOG.md`

Select the University of Edinburgh DataShare dataset
"Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls"
(DOI `10.7488/ds/3785`, CC BY 4.0) as the first measured resistance source to
receive a full RFC 0042 source-review packet, with the maximum allowed positive
outcome of `validation_fixture` only. Calibration-fixture promotion is
forbidden for this source under any subsequent workflow because the hull class
(Pacific-canoe-like slender models at fixed sink/trim) lies outside the
kayak/surfski design envelope from
`docs/design/kayak_hull_design_constraints.md`. The follow-up workflow must
complete the four `incomplete` checklist fields recorded in the workflow 0051
review packet (`extraction`, `units`, `uncertainty`, and the validation-fixture
metadata set required by
`ResistanceSourceRecord._validate_validation_fixture_metadata`) before any
verdict above `validation_candidate` may serialize. Runtime `SourceUse` stays
limited to the existing five literals in
`kayakgen/eval/calibration.py:13-19`; `rejected` remains a review-only outcome
that maps to `None` per `SOURCE_USE_BY_REVIEW_VERDICT`. Default resistance
output remains `uncalibrated_comparative` and no calibrated-prediction wording
is authorized until `claim_allows_calibrated_prediction` in
`kayakgen/eval/claims.py:195-210` is independently satisfied by a later
accepted-fit workflow with an in-envelope measured kayak source.

## Evidence

### Research-Packet Evidence

`striatum/0052-successor-decision-research/research/resistance_source_candidate/RESEARCH.md`
enumerates six external candidates accessed 2026-05-14 and recommends Option A.
The packet's external evidence table is internally consistent and supports the
chosen posture:

- Edinburgh DataShare full record cites CC BY 4.0 on the dataset and an MD5
  `ed88b247db4fe1ef62baeecfe7cc6daf` for the spreadsheet; the sheets cover
  `Averaged Data`, `Results vs speed`, `Results vs yaw`, `Prohaska`, and
  `Froude Scaling`, with model speeds 0.4–1.6 m/s and Fn ≈ 0.117–0.466 (research
  packet §"Current External Evidence", row 1).
- Tzabiras Sport Journal article is openly readable but the page asserts
  USSU/`United States Sports University` all-rights-reserved with no open data
  license (row 2).
- Gomes 2018 SUNY metadata records Informa/Taylor & Francis publisher
  copyright; no open data deposit (row 3).
- Sea Kayaker / Kanu.de PDF values are Taylor Standard Series model-derived at
  113.4 kg, not measured (row 4).
- Lazauskas/Winters/Tuck currently lacks a stable machine-readable source
  (SPONET bibliographic only; `cyberiad.net` redirects) (row 5).
- MDPI "On the Physics of Kayaking" is CC BY 4.0 but is not a fixture dataset
  (row 6).
- NIST CUU and BIPM JCGM 100:2008 define Type A vs Type B uncertainty and
  general expression rules — load-bearing for the uncertainty clause in the
  promotion threshold.

### Independent Check On Current Code

I verified the runtime contract the decision must preserve by reading the code
directly. Every load-bearing claim in the research packet is consistent with
what the repository actually enforces today:

- `kayakgen/eval/calibration.py:13-19` confirms the five-literal `SourceUse`
  (`citation_only`, `validation_candidate`, `validation_fixture`,
  `calibration_fixture_candidate`, `calibration_fixture`). No `rejected`
  literal. The decision must not introduce one.
- `kayakgen/eval/calibration.py:20-27` defines `SourceReviewVerdict` including
  `rejected`, and lines 45-52 keep `SOURCE_USE_BY_REVIEW_VERDICT["rejected"]
  = None`. The mapping the integrator must preserve is already mechanical.
- `kayakgen/eval/calibration.py:114-158` confirms
  `ResistanceSourceRecord._validate_calibration_fixture_metadata` requires
  `fixture_id`, `measured_quantity`, `measurement_units`, `hull_envelope`,
  `uncertainty_notes`, `validity_ranges`, `fixture_review_status="accepted"`,
  `rights_status`, `extraction_status`, and `measured_data=True`. The
  validation-fixture validator at `:145-158` requires a smaller but real set
  (`fixture_id`, `measured_quantity`, `measurement_units`, `rights_status`,
  `extraction_status`). The promotion thresholds in this vote are therefore
  not aspirational; they are the contract the code refuses to relax.
- `kayakgen/eval/calibration.py:222-259` confirms
  `ResistanceSourceReviewPacket._review_verdict_controls_promotion_metadata`
  enforces: rejected reviews cannot declare fixture metadata or validity
  envelope and must declare non-promotion reasons; candidate-source verdicts
  cannot declare fixture metadata or validity envelope and must declare
  non-promotion reasons; promotion verdicts require complete checklist
  evidence (no `incomplete`/`missing` fields), `measured_data=True`,
  `fixture_id` and `fixture_version` present, no `non_promotion_reasons`,
  and (for `calibration_fixture`) a `validity_envelope`. The Edinburgh
  packet's path to `validation_fixture` is mechanically defined.
- `kayakgen/eval/calibration.py:262-289` confirms the default registry's
  Edinburgh record carries
  `rights_status="cc_by_4_0_dataset_doi_10_7488_ds_3785"`,
  `intended_use="validation_candidate"`, `measured_data=True`, and warnings
  `pacific_canoe_not_sea_kayak`, `fixed_sink_trim`,
  `validation_not_calibration`. The follow-up workflow can move Edinburgh
  only as far as `validation_fixture`, not `calibration_fixture`, without
  removing or relaxing the existing warnings.
- `kayakgen/eval/calibration.py:360-450` shows the workflow 0051 applied
  packet for Edinburgh: `rights`, `measured_quantity`, `hull_envelope`, and
  `speed_froude_range` are already `accepted`; `extraction`, `units`, and
  `uncertainty` are `incomplete`. The next workflow's scope is precisely
  these three checklist gaps plus the validation-fixture metadata package
  (fixture ID/version, normalized `measurement_units`, accepted uses, and an
  article-vs-dataset rights record).
- `kayakgen/eval/claims.py:195-210` confirms the calibrated-prediction gate
  requires `claim_state == CALIBRATED_MODEL`, `ACCEPTED_USE_FINAL_PREDICTION`,
  non-empty `calibration_fixture_ids`, a `model_version`, a passing
  `fit_status`, fit metrics, a validity envelope, and zero
  `UNCALIBRATED_WARNING_CODES`. This gate is unchanged by the decision; no
  Edinburgh promotion path can satisfy it because Edinburgh cannot become a
  calibration fixture under this vote.

### Independent Domain Check

`docs/design/kayak_hull_design_constraints.md:72-86, :94-122` defines the
project's single-hull kayak/surfski envelope, including L/B_wl ratios from 5
to 15, target Fn 0.30/0.40/0.50, and explicit beam, draft, and class
boundaries. Cross-checking each candidate against that envelope:

- **Edinburgh DataShare**: geometrically outside the envelope (Pacific-canoe
  multi-hull side-force orientation; fixed sink/trim; model-scale tests at
  Fn ≈ 0.117–0.466). It can validate parser/report/holdout infrastructure
  but cannot calibrate kayak resistance under any subsequent workflow.
- **Tzabiras K-1**: inside the kayak family but in the sprint K-1 regime,
  not sea-kayak/surfski; rights blocked at source today.
- **Gomes 2018**: same envelope concern as Tzabiras, plus publisher-copyright
  rights gate.
- **Sea Kayaker / Kanu.de**: class-matching but Taylor Standard Series
  model-derived — model-to-model calibration risk per RFC 0042 §"Promotion
  Rules". Forbidden as a calibration source for ITTC/Michell.
- **Lazauskas/Winters/Tuck**: closest class match in principle, but current
  access is bibliographic/redirect; no machine-readable rows; rights unknown.
- **MDPI "On the Physics of Kayaking"**: open access modeling context, not
  primary measurement data.

This domain check independently confirms the research recommendation: the
registry contains no kayak-envelope measured source with open rights *today*,
so a calibration-fixture choice is not on the table; Edinburgh is the only
candidate whose rights/files/checksums actually support a full review packet
in this workflow's documentation-only scope.

### External-Source Check

External sources in the research packet were accessed 2026-05-14, the same
date as this vote. `WebFetch` is not in this session's tool surface; I did
not independently re-fetch the URLs. The vote does not depend on a contested
external fact: every load-bearing claim — runtime `SourceUse` taxonomy, the
validator's fixture-metadata enforcement, the kayak design envelope, the
calibrated-prediction gate, and the registry's `intended_use` values — is
verifiable against the local repository and was verified above. If the
integrator wants to harden one citation, the highest-leverage one is the
Edinburgh DataShare full item record, since CC BY 4.0 on the dataset (and
not on related article prose) is the load-bearing rights claim that
authorizes the validation-fixture path.

The workflow 0051 implementation already wrote the partial Edinburgh review
packet into `kayakgen/eval/calibration.py::default_resistance_source_review_packets`
at `validation_candidate` with named non-promotion reasons
(`extraction_schema_missing`, `unit_normalized_rows_not_checked_in`,
`uncertainty_treatment_missing`, `outside_sea_kayak_calibration_envelope`).
That packet is the artifact this decision authorizes the next workflow to
upgrade to `validation_fixture` — not to replace, and not to promote to
`calibration_fixture`.

## Why Rejected Alternatives Lose

### Option B — Permission-First K1 Packet (Tzabiras or Gomes)

Loses on three independent failure modes, any one of which is sufficient:

1. **Rights are real-world third-party negotiations.** Neither USSU
   (Tzabiras) nor Informa/Taylor & Francis (Gomes) has a documented open
   data path. Pursuing permission is a real-world legal/communications
   workstream, not a Striatum-implementable decision; the next workflow
   cannot land a full packet whose `rights` evidence is "negotiation
   pending."
2. **Envelope mismatch is permanent.** Even with rights cleared, sprint K-1
   is not the sea-kayak/surfski envelope. A K-1 validation fixture would
   still need a permanent envelope-mismatch warning and could not be
   promoted to `calibration_fixture` for the project's design space under
   any later workflow without a separate measured kayak-envelope source.
   Picking Option B does not advance the calibration-source question.
3. **Edinburgh is strictly better for the *first* full packet.** Edinburgh
   already has open rights, available source files with checksums, and a
   workflow 0051 review packet at `validation_candidate` waiting to be
   upgraded. The infrastructure exercise that the first full packet
   produces (extraction schema, unit-normalization manifest, uncertainty
   treatment, validation-fixture metadata path through the existing
   validator) is identical between Edinburgh and a hypothetical K-1
   source, but Edinburgh can land in this workflow's documentation cycle
   and K-1 cannot.

If rights ever clear for Tzabiras or Gomes, a future workflow can author a
*second* full packet then; this decision does not block that.

### Option C — Calibration-Source Search Before Any Fixture Packet

Loses as the *operating posture* for the same reason workflow 0050 rejected
it as a default for D005:

- It stalls useful, non-promoting infrastructure work that is already in
  scope. The source-review packet shape exists
  (`ResistanceSourceReviewPacket` at `kayakgen/eval/calibration.py:171-260`);
  the next full packet's incremental scope is the four `incomplete`
  Edinburgh checklist fields plus validation-fixture metadata. None of that
  work requires a calibration source.
- No current candidate satisfies the calibration bar (envelope and rights
  jointly), and no Striatum workflow can synthesize one. Waiting reproduces
  Option D's recovery problem without doing the validation-fixture
  infrastructure that is independently valuable under the
  `uncalibrated_comparative` posture.
- The decision must still preserve the calibration-fixture no-promotion
  gate (RFC 0027 acceptance gate, RFC 0042 promotion rules,
  `claim_allows_calibrated_prediction`). Option A already does that;
  Option C adds no protection beyond what is already enforced by code.

### Option D — Recover Class-Relevant Historical Sea-Kayak Evidence

Loses as the *first packet* target. Recovery work is real value, but it is
not a "first full source-review packet" candidate:

- Lazauskas/Winters/Tuck is bibliographic/redirect today; SPONET asserts
  all-rights-reserved and `cyberiad.net` redirects away. No reproducible
  rows exist to bind to a packet.
- Sea Kayaker / Kanu.de values are Taylor Standard Series model-derived;
  RFC 0042 §"Promotion Rules" explicitly forbids model-derived data from
  becoming a calibration fixture, and a validation fixture built on
  model-derived rows would be at best low-utility infrastructure exercise
  with high model-to-model misreading risk.
- Recovery and rights-discovery is an open-ended, real-world workstream
  that cannot be sized into the next implementation burn-down.

Option D may proceed as a *parallel*, separately-scoped recovery effort
(it is implicit in the roadmap's RFC 0042 sequencing), but it is not the
first packet.

### Pure-Option-A-Without-Validation-Fixture-Cap

A defensible variant of Option A would allow the next workflow to author the
packet without explicitly capping the maximum verdict at `validation_fixture`.
I reject that variant: without an explicit cap, the next workflow's
implementer might infer that a complete checklist permits any verdict that
the validator does not block, and the validator does not encode the
kayak-envelope rule. The cap must be explicit in this decision because the
envelope is a domain constraint, not a code-level metadata field.

## Implementation Gates That Must Remain In Force

These gates must not be relaxed by any workflow that consumes this decision:

1. **`SourceUse` literal preservation.** The five existing literals in
   `kayakgen/eval/calibration.py:13-19` are the only runtime values.
   `rejected` stays a `SourceReviewVerdict` outcome only and continues to
   map to `None` in `SOURCE_USE_BY_REVIEW_VERDICT`. Any later implementation
   must keep the validator at
   `_review_verdict_controls_promotion_metadata` intact and add or preserve
   a direct test that rejected reviews cannot serialize as `SourceUse`.

2. **Edinburgh maximum verdict.** The Edinburgh packet's allowed positive
   promotion is `validation_fixture` only. `calibration_fixture` is
   forbidden because the source is `pacific_canoe_like_slender_hulls`,
   outside the kayak/surfski design envelope. This is a decision-level
   constraint that the next workflow must preserve in commentary, in the
   packet's `non_promotion_reasons` for any future re-review, and in the
   registry record's `warnings` field
   (`pacific_canoe_not_sea_kayak`, `fixed_sink_trim`,
   `validation_not_calibration`).

3. **Checklist completion before promotion.** The four checklist fields
   currently `accepted` (`rights`, `measured_quantity`, `hull_envelope`,
   `speed_froude_range`) and the three currently `incomplete`
   (`extraction`, `units`, `uncertainty`) must all reach `accepted` before
   a `validation_fixture` verdict may serialize. The validator at
   `kayakgen/eval/calibration.py:245-250` already enforces this; the
   decision must not authorize bypassing it via
   `--allow-no-process-execution` or any escape hatch.

4. **Validation-fixture metadata package.** Promotion requires
   `fixture_id`, `fixture_version`, `measured_quantity`, `measurement_units`
   (m/s and N normalized; original units retained alongside),
   `rights_status`, and `extraction_status` per
   `_validate_validation_fixture_metadata` at lines 145-158. The next
   workflow must record at minimum:
   - the dataset DOI, persistent identifier, and CC BY 4.0 license URL;
   - the deposited spreadsheet checksum (MD5 reported by DataShare for the
     accessed file at access date 2026-05-14, plus a recomputed SHA-256
     for `kayakgen` use);
   - the IGES CAD checksum if those files are referenced;
   - the sheet/row filter (e.g., `Results vs speed`, zero-yaw rows only);
   - the original column units and normalized SI units; and
   - water-property and scale-basis assumptions (model-scale vs full-scale
     with `Lm` length basis).

5. **Article-vs-dataset rights separation.** CC BY 4.0 covers the
   DataShare dataset deposit. It does not cover related article prose,
   article tables, journal-side layout, or related publications. The
   validation-fixture record must cite only DataShare files and
   checksum-bound extracted rows. The CC BY 4.0 attribution obligations
   (author attribution, license URL, change marking, no-added-restrictions
   clause) must be recorded in `rights_status` and any UI surface that
   displays the fixture.

6. **Uncertainty treatment.** The `uncertainty` checklist field cannot
   become `accepted` on a hand-wave. Acceptance requires either a numeric
   row-level uncertainty (from repeatability/instrument analysis of the
   workbook's repeated runs) or a documented Type B uncertainty note
   covering instrument/source limitations, digitization precision, and
   model-scale-to-extracted-row conversion error, per NIST CUU and
   BIPM JCGM 100:2008.

7. **Calibration-fixture no-promotion bar (project-wide).** This decision
   does not authorize promotion of any source to `calibration_fixture`.
   The next workflow may not silently add a `calibration_fixture` record
   for any source — Edinburgh or otherwise — under any rationale,
   including "we found enough metadata." Such promotion remains gated on
   D006 plus a future kayak-envelope measured source plus a future
   accepted-fit workflow.

8. **Model-to-model bar.** Model-derived tables (e.g., Sea Kayaker /
   Kanu.de Taylor Standard Series at 113.4 kg) must not be promoted to
   `calibration_fixture` for an ITTC/Michell-shaped model under any later
   workflow, and the project must not synthesize a "calibration fixture"
   by fitting a calibrated model to another model's output.

9. **One source per workflow.** The next workflow's scope is the Edinburgh
   full packet only. It must not concurrently apply full packets to
   Tzabiras, Gomes, MDPI, Sea Kayaker/Kanu.de, or
   Lazauskas/Winters/Tuck. Additional packets, including any
   permission-first K-1 packet, require their own workflow with their own
   rights review.

10. **No-promotion-by-this-decision.** This decision promotes no source.
    It selects the next packet's target and caps its maximum verdict; it
    does not pre-commit any workflow to author a fixture, nor does it
    authorize a `validation_fixture` row to materialize today. Each later
    promotion is its own workflow with its own review record.

## No-Claims Language That Must Remain In Force

This decision relaxes none of the following. Every consuming workflow must
preserve them verbatim where they already appear in `docs/PRD.md`,
`docs/USER_GUIDE.md`, `docs/ROADMAP.md`, RFC 0025, RFC 0027, RFC 0042, and
D005/D006:

- Default resistance output remains `uncalibrated_comparative`. It is a raw
  comparative filter for candidate ranking, not a calibrated model, final
  prediction, design-fitness score, default optimization objective, or
  seaworthiness/safety statement (`docs/ROADMAP.md:38-40`,
  `docs/USER_GUIDE.md:102-104`, `kayakgen/eval/claims.py:UNCALIBRATED_COMPARATIVE`).
- Resistance output may stop saying uncalibrated *only* under
  `claim_allows_calibrated_prediction`: a selected named model version with
  `accepted_fit`, accepted `calibration_fixture_ids`, persisted fit metrics
  and residuals, a validity envelope containing the evaluated hull and
  speed, and no `UNCALIBRATED_WARNING_CODES` present
  (`kayakgen/eval/claims.py:195-210`).
- Validation fixtures may appear in reports, holdout metrics, or parser
  tests, but they must not be listed as `calibration_fixture_ids` for an
  accepted fit (RFC 0027 §"Stage 2", RFC 0042 §"Claim Boundaries").
- The PRD's "within 25% across the Fn 0.25–0.50 range" success criterion
  remains a calibration-roadmap criterion, not a present capability
  (`docs/PRD.md:90`).
- CFD fixture-adapter results (RFC 0026 fixture-local-command outputs)
  remain `raw_unvalidated` and remain excluded from measured-source
  calibration fixtures.
- This decision does not authorize: vendoring extracted measurement rows
  outside CC BY 4.0 attribution requirements; publishing any source PDF or
  digitized table outside its rights; changing resistance UI/copy;
  advancing high-angle `GZ` claims; advancing solver readiness; advancing
  hosted browser operation; or changing Pareto-default scoring or sweep
  ranking.
- Workflow 0050 D005 (source-review-first, no fixture promotion) and D006
  (calibrated-resistance no-promotion gate) remain in force. This vote
  selects a target for the *first* full source-review packet under D005;
  it does not amend D005 or D006.

## Confidence

**High.**

Rationale: the recommended posture aligns mechanically with every
load-bearing local artifact verified above —
the `SourceUse` literal at `kayakgen/eval/calibration.py:13-19`, the
`SourceReviewVerdict` enum at `:20-27`, the verdict-to-source-use mapping
at `:45-52`, the fixture-metadata validators at `:114-158`, the packet
validator at `:222-259`, the workflow 0051 applied Edinburgh packet at
`:360-450`, the calibrated-prediction gate at
`kayakgen/eval/claims.py:195-210`, RFC 0042 §"Promotion Rules" and
§"Claim Boundaries", RFC 0027 §"Stage 2/Stage 3", the No-Claims Rules at
`docs/ROADMAP.md:34-59`, Batch F sequencing at `docs/ROADMAP.md:218-245`,
D005/D006 at `docs/DECISION_LOG.md:38-39`, the design envelope at
`docs/design/kayak_hull_design_constraints.md:72-86, 94-122`, and the
workflow 0050 final-review evidence chain at
`striatum/0050-decision-panel-research/final/FINAL_REVIEW.md`.

The only meaningful unknown — whether and when a kayak-envelope measured
source with open rights will exist — is correctly deferred to a later
workflow rather than resolved here. The research packet's external
evidence is consistent with the decision's threshold language, and
nothing in the local code, RFC index, roadmap, or decision log
contradicts the external citations or the chosen verdict cap.

The risk of the chosen option is well-bounded: a fully completed Edinburgh
validation-fixture packet is documentation/contract work that exercises
existing validators, adds no runtime calibration claim, and is
fail-safe even if Edinburgh later proves unsuitable as a validation source
(the warnings and non-promotion-to-calibration cap survive any future
re-review).

## Sources Reviewed

Local:

- `AGENTS.md`
- `docs/PRD.md` (audience, in-scope/out-of-scope, success criteria)
- `docs/USER_GUIDE.md` (resistance evaluator claim boundaries, current limits)
- `docs/ROADMAP.md` (No-Claims Rules §34-59; Workflow 0050 Posture §61-95;
  Batch F §218-245)
- `docs/DECISION_LOG.md` (D005, D006)
- `docs/rfcs/README.md` (RFC index, RFC 0042 disposition)
- `docs/rfcs/0042-resistance-calibration-fixture-successor.md` (§86-103
  packet fields; §105-133 verdict mapping; §"Promotion Rules")
- `docs/rfcs/0027-resistance-calibration-acceptance.md` (§"Stage 1/2/3"
  acceptance; `claim_allows_calibrated_prediction`)
- `docs/design/kayak_hull_design_constraints.md` (envelope §72-86, beam
  §94-122; Fn target points)
- `docs/workflows/0052-successor-decision-research/SOURCES.md`
- `docs/workflows/0052-successor-decision-research/RUNBOOK.md`
- `docs/workflows/0052-successor-decision-research/prompts/panel_vote.md`
- `docs/workflows/0018-deferred-backlog/QUEUE.md` (history disposition only)
- `kayakgen/eval/calibration.py` (`SourceUse`, `SourceReviewVerdict`,
  `SOURCE_USE_BY_REVIEW_VERDICT`, fixture validators, packet validator,
  default registry, default review packets — verified directly)
- `kayakgen/eval/claims.py` (`claim_allows_calibrated_prediction`,
  `UNCALIBRATED_COMPARATIVE`)
- `striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md`
- `striatum/0050-decision-panel-research/final/FINAL_REVIEW.md`
- `striatum/0050-decision-panel-research/panels/resistance_sources/claude/VOTE.md`
  (workflow 0050 antecedent decision-shape only; not a basis for re-deciding
  D005)
- `striatum/0051-implementation-burndown-stage1/ledger/FINDINGS_LEDGER.md`
- `striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md`
- `striatum/0051-implementation-burndown-stage1/implementation/resistance_source_review/PATCH_SUMMARY.md`
- `striatum/0052-successor-decision-research/research/resistance_source_candidate/RESEARCH.md`

External claims (as cited in the research packet, accessed 2026-05-14; not
re-fetched in this session — see "External-Source Check" above):

- Edinburgh DataShare full record
  (`https://datashare.ed.ac.uk/handle/10283/4772?show=full`) — CC BY 4.0
  dataset, spreadsheet MD5 `ed88b247db4fe1ef62baeecfe7cc6daf`; supports
  Option A validation-fixture path conditional on schema, units, and
  uncertainty completion.
- CC BY 4.0 deed (`https://creativecommons.org/licenses/by/4.0/`) —
  attribution/change-marking obligations encoded in the rights-scope gate.
- Edinburgh Research Explorer entry
  (`https://www.research.ed.ac.uk/en/publications/hydrodynamics-of-three-slender-models-resembling-pacific-canoe-hu/`)
  — confirms the experiment frames Pacific canoe / catamaran side-force
  behavior; supports the envelope-mismatch finding.
- Tzabiras et al. Sport Journal article
  (`https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/`)
  — USSU all-rights-reserved; supports Option B rejection.
- Gomes 2018 SUNY Research Connect
  (`https://researchconnect.suny.edu/en/publications/effect-of-wetted-surface-area-on-friction-pressure-wave-and-total/`)
  — publisher copyright; supports Option B rejection.
- Sea Kayaker / Kanu.de PDF
  (`https://www.kanu.de/nuke/downloads/Resistance.pdf`) — Taylor Standard
  Series model-derived at 113.4 kg; supports the model-to-model bar.
- Lazauskas/Winters/Tuck SPONET record
  (`https://sponet.de/Record/4000729`) and `cyberiad.net` redirect — no
  stable machine-readable source; supports Option D rejection as first
  packet.
- MDPI "On the Physics of Kayaking"
  (`https://www.mdpi.com/2076-3417/12/18/8925`) — CC BY 4.0 article, no
  primary dataset; supports `citation_only` posture.
- NIST CUU (`https://pml.nist.gov/cuu/Uncertainty/basic.html`) and BIPM
  JCGM 100:2008 (`https://www.bipm.org/en/doi/10.59161/jcgm100-2008e`) —
  Type A vs Type B uncertainty; supports the uncertainty-treatment clause
  in the validation-fixture threshold.

## Sub-Agent Help

No sub-agents were spawned. Verification of the runtime `SourceUse`
taxonomy, the verdict-mapping table, the fixture validators, the packet
validator, the default registry and applied review packet contents, and
the `claim_allows_calibrated_prediction` gate was performed inline via
direct read-only inspection of `kayakgen/eval/calibration.py` and
`kayakgen/eval/claims.py`.
