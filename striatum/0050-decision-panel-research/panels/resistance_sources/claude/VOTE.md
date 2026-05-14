---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-008
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_81b1557c9b53413f86aa87b04963de8f
job: job_run_dc0a506896094745b380fd3ad2535d59_panel_resistance_sources_claude
lease: lease_ae82a29f07b74dacbcbf2187f65c5eb4

# Panel Vote — Resistance Source Acceptance Evidence

## Vote

**Option A (Source-Review Packet First, No Fixture Promotion), with Option B
permitted only as a later, separately gated workflow. Reject Option C for this
decision. Reject Option D as the operating posture.**

## Decision Sentence For `docs/DECISION_LOG.md`

Adopt a source-review-and-fixture-promotion contract for kayak-gen resistance
sources before any further fixture promotion. The contract requires (1) a
source-review packet covering source ID/citation, durable locator, rights
(original material and derived rows), source type, measured quantity and units,
hull envelope, speed/Froude range, extraction method/metadata, uncertainty
treatment, and review verdict; (2) a source-use mapping that preserves the
existing five `SourceUse` literal values (`citation_only`,
`validation_candidate`, `validation_fixture`, `calibration_fixture_candidate`,
`calibration_fixture`) with `rejected` as a terminal review outcome only — not
a runtime `SourceUse` value, fixture input, fit input, or claim-gate
participant; (3) application of the packet to one candidate source without
promotion unless every required field is complete. No current source in
`kayakgen/eval/calibration.py::default_resistance_source_registry` is promoted
from `validation_candidate` or `citation_only` to `validation_fixture` or
`calibration_fixture` by this decision. Validation-fixture ingest may follow
in its own workflow once an attribution/extraction schema lands; calibration
fixture promotion requires a measured kayak-envelope source plus accepted
fixture review. Default resistance output remains `uncalibrated_comparative`,
and no calibrated-prediction wording is permitted until RFC 0027's
`claim_allows_calibrated_prediction` gate is independently satisfied by a
later accepted-fit workflow.

## Evidence

### Research-Packet Evidence

`striatum/0050-decision-panel-research/research/resistance_sources/RESEARCH.md`
recommends Option A as the immediate decision and Option B as a safe
validation-only follow-up. The packet cites Edinburgh DataShare (CC BY 4.0
dataset; Pacific-canoe-like slender hulls, fixed sink/trim, Fn ≈ 0.117–0.466),
Gomes et al. 2018 (publisher copyright; single-seat sprint K1 passive drag),
Tzabiras et al. 2010 (USSU all-rights-reserved; Olympic K-1 displacement
86.8 kg, fresh water 15 °C, Fn 0.035–0.730), the Sea Kayaker / Kanu.de PDF
(Matt Broze Taylor Standard Series modeled values, kg vs knots), MDPI "On the
Physics of Kayaking" (CC BY 4.0 but no data), and NIST/GUM uncertainty
guidance (Type A vs Type B). Local anchors include RFC 0042 §86-103 (review
packet fields), §105-133 (`SourceUse` taxonomy and `rejected` as terminal
review outcome), RFC 0027 §43-72 (three-stage acceptance over the existing
five `SourceUse` literals), `kayakgen/eval/claims.py:195-210` (the
`claim_allows_calibrated_prediction` gate), `docs/ROADMAP.md:38-40`
(`uncalibrated_comparative` posture) and `docs/ROADMAP.md:166-189`
(Batch F sequencing), and `docs/USER_GUIDE.md:102-104, 458-459` for the
uncalibrated warning copy.

### Independent Check On Current Code

I verified the runtime contract the decision must preserve by reading the
code directly:

- `kayakgen/eval/calibration.py:13-19` confirms the five-element `SourceUse`
  `Literal` exactly matches the research packet's enumeration: `citation_only`,
  `validation_candidate`, `validation_fixture`, `calibration_fixture_candidate`,
  `calibration_fixture`. There is no `rejected` literal. The decision must not
  introduce one.
- `kayakgen/eval/calibration.py:60-104` shows `ResistanceSourceRecord` already
  enforces that `calibration_fixture` records carry `fixture_id`,
  `measured_quantity`, `measurement_units`, `hull_envelope`,
  `uncertainty_notes`, `validity_ranges`, `fixture_review_status="accepted"`,
  `rights_status`, `extraction_status`, and `measured_data=True`. Validation
  fixtures require a thinner but still real metadata set (`fixture_id`,
  `measured_quantity`, `measurement_units`, `rights_status`,
  `extraction_status`). The packet's promotion-threshold language is therefore
  not aspirational — it is the documented contract the validator already
  refuses to relax.
- `kayakgen/eval/calibration.py:107-202` confirms `default_resistance_source_registry`
  carries exactly the five sources the research packet lists: Edinburgh
  (`validation_candidate`, CC BY 4.0, warnings include
  `pacific_canoe_not_sea_kayak`, `fixed_sink_trim`,
  `validation_not_calibration`); Sea Kayaker/Kanu.de (`citation_only`,
  `model_to_model_calibration_risk`, `redistribution_unclear`); Gomes 2018
  (`validation_candidate`, `sprint_k1_not_sea_kayak`,
  `redistribution_not_established`); Tzabiras (`validation_candidate`,
  `sprint_k1_not_sea_kayak`, `fixture_rights_not_established`); and MDPI
  (`citation_only`, `not_primary_resistance_dataset`). None has
  `intended_use="calibration_fixture"`. The decision must preserve that.
- `docs/rfcs/0042-resistance-calibration-fixture-successor.md:116-133`
  encodes the same mapping table the decision must honor and explicitly
  states `rejected` "must not be used to create a runtime fixture record
  that can participate in validation, fitting, or claim gates, and it must
  not be added as a runtime `SourceUse` enum member."
- `docs/rfcs/0027-resistance-calibration-acceptance.md:38-72` confirms the
  RFC 0027 acceptance gate is already landed: three normative stage labels
  group over the five existing `SourceUse` literals; the document explicitly
  forbids adding a `candidate_source` literal or parallel enum. This rules
  out any decision that introduces a new runtime taxonomy.

### Independent Domain Check

`docs/design/kayak_hull_design_constraints.md:72-86, :224-250` defines the
project's single-hull kayak/surfski envelope: `L_oa` 4.0–6.5 m, `B_wl`
0.36–0.58 m, draft 0.10–0.16 m, `Cp` 0.50–0.62, with target resistance points
near Fn 0.30, 0.40, and 0.50. Each currently-reviewed source falls outside
that envelope in a different way:

- Edinburgh is geometric outside (Pacific-canoe multi-hull, fixed sink and
  trim) and so is a strict validation-only candidate by class, even if its
  rights and measurement metadata are the strongest in the registry.
- Gomes 2018 and Tzabiras are inside the kayak family but in the sprint K1
  speed/load regime, not sea-kayak/surfski; they are still validation-only
  by envelope mismatch, with rights as the secondary block.
- The Sea Kayaker/Kanu.de compilation is the only class-matching source but
  is model-derived (Taylor Standard Series at fixed 113.4 kg payload), which
  would be model-to-model calibration if applied to ITTC/Michell — explicitly
  forbidden by RFC 0042's calibration definition.

This is the operative reason calibration-fixture promotion cannot happen
today regardless of how careful the review packet is: the registry does not
contain a kayak-envelope measured source with open rights. The decision must
not paper over that with a validation-fixture promotion that masquerades as
calibration.

### External-Source Check

Access date for the research packet's external evidence is 2026-05-14, which
matches the date on this vote. The citation-to-claim mapping is sound on its
face:

- The Edinburgh dataset entry on CC BY 4.0 supports row-extraction rights
  for the dataset (not for the related article/prose). The decision must
  preserve that article-vs-dataset rights separation.
- The Gomes SUNY metadata page and the Tzabiras Sport Journal article page
  jointly support the assertion that neither current source has an open
  fixture-redistribution license at the dataset level.
- The Sea Kayaker/Kanu.de PDF footnote stating values are computed using the
  Taylor Standard Series supports treating the compilation as model-derived
  and not measured.
- NIST CUU and BIPM JCGM 100:2008 support requiring source uncertainty
  representation, with Type B allowed as a fallback when source uncertainty
  is absent — which is what the decision's promotion-threshold uncertainty
  clause encodes.

`WebFetch` is not loaded in this session's tool surface; I did not
independently re-fetch the URLs. Nothing in the decision turns on a
contested external fact: the project's runtime taxonomy, the existing
registry's `intended_use` values, the kayak design envelope, and RFC
0027's claim-gate already make the conservative outcome correct, so a
URL re-fetch is not load-bearing for this vote. If the integrator wants
to harden any one citation it should be the Edinburgh DataShare full
item record, since that is the only currently-reviewed source whose
license would, on its own, support a future validation-fixture
promotion.

## Why Rejected Alternatives Lose

### Option B — Edinburgh Validation Fixture After Extraction Schema (rejected as the immediate decision; permitted as a later separately-gated workflow)

Option B is the *most defensible* validation-only follow-up, but it loses as
the *immediate* decision for three reasons:

1. It bundles two choices: "is the source-review packet authoritative?"
   and "do we ingest Edinburgh validation rows now?" The roadmap's Batch F
   ordering (`docs/ROADMAP.md:170-189`) is unambiguous: first the
   review packet/checklist, then a single source review without promotion,
   then mapping checks, then validation-fixture ingest. Voting Option B
   today would skip steps 1-3.
2. Edinburgh's article-vs-dataset rights split (CC BY 4.0 on the dataset;
   typically Informa/Taylor & Francis or similar on the article and tables)
   is the most likely place a careless extraction loses the rights position.
   No extraction/attribution schema yet exists in the repo; building one is
   exactly the work Option B presupposes is complete.
3. Edinburgh's fixed-sink/fixed-trim Pacific-canoe form is geometrically
   *outside* the project's design envelope. As a validation fixture it would
   still need a warning that it cannot be promoted to a calibration fixture
   under any later workflow without an envelope-mismatch finding. Building
   that warning shape is downstream work, not in scope today.

The decision explicitly permits Option B as a *later* workflow once a schema
lands. Picking A today does not block B; picking B today would skip A.

### Option C — K1 Validation Fixture By Permission

Loses on rights and envelope, simultaneously and independently:

- Gomes 2018 is publisher-copyright via Informa/Taylor & Francis; the SUNY
  metadata page does not reveal an open fixture-redistribution path. The
  research packet does not document a granted permission.
- Tzabiras's Sport Journal article reads as openly readable but the page
  asserts USSU all-rights-reserved; no open fixture/data license is
  documented.
- Even if rights cleared tomorrow, sprint K1 is not the project's design
  envelope. A K1-only validation fixture would have to ship with a permanent
  envelope-mismatch warning and cannot — under any later workflow — become
  a calibration fixture for sea kayaks without a separate measured
  kayak-envelope source.
- Pursuing permission is a real-world third-party negotiation; that is
  not a Striatum-implementable decision and cannot be voted into existence.

### Option D — Wait For Kayak-Envelope Calibration Source

Loses as the *operating posture* (it is reasonable as a goal). It blocks
useful, in-scope work today: the source-review packet is documentation
shape; source-use mapping tests are pure validation; the schema work that
makes Option B viable later is itself non-promoting. Refusing to land any
of that until a kayak-envelope source materializes stalls validation-fixture
infrastructure, parser/report exercise, holdout coverage, and rights/
unit-normalization discipline — all of which are independently valuable
under `uncalibrated_comparative` curves and the existing claim gate.
Option A captures everything Option D would protect (no promotion today,
no claim-wording change) while removing the unforced delay.

### Pure-Option-A-Only (skip the Option B permission)

Loses (compared to A with Option B explicitly permitted later) because it
would create the impression that even a validation-only Edinburgh ingest
would need re-litigation of the source-review packet contract. Naming
Option B as a permitted-later path documents the sequencing without
committing maintainer attention.

## Implementation Gates That Must Remain In Force

These gates must not be relaxed by any workflow consuming this decision:

1. **`SourceUse` literal preservation.** The five existing literals in
   `kayakgen/eval/calibration.py:13-19` are the only runtime values. The
   review packet's `rejected` outcome must remain documentation-only and
   must not become a sixth literal, an enum member, a serialized fixture
   field, or a claim-gate participant. Any later implementation must add
   a direct test that asserts the five literals are preserved and that
   `rejected` cannot serialize as `SourceUse`.
2. **Source-review packet completeness.** Before any source is promoted
   from `validation_candidate` or `citation_only`, the review must include:
   source ID and citation; durable locator (URL/DOI/archive ref) plus
   access date; rights status for original material *and* derived rows;
   license URL and attribution text; source type (tow-tank, passive-drag,
   on-water, model-derived, CFD, secondary citation); measured quantity and
   provenance (force, coefficient, decomposition, model output); original
   units and normalized SI units (speed, resistance, displacement/load,
   length, density, viscosity, temperature, fresh/seawater assumption);
   hull envelope (class, dimensions, draft/displacement, available
   offsets/CAD, sections, appendages, paddler/fixture state, trim/sinkage
   policy); speed/Froude range with length basis recorded; extraction
   metadata (extractor, date, tool version, conversions, rounding,
   digitization method, reproducibility instructions, source-file
   checksums); uncertainty treatment (numeric source uncertainty or a
   documented Type B note); and review metadata (reviewer, date, verdict,
   reasons, source-use mapping, fixture ID/version if promoted, accepted
   uses, validity envelope, explicit non-promotion reasons).
3. **Validation-fixture threshold.** A source may become a
   `validation_fixture` only when rights, units, extraction, rows, and
   fixture metadata are adequate for parser/report/holdout checks per the
   existing `_validate_validation_fixture_metadata` validator and an
   accompanying article-vs-dataset rights separation has been recorded.
   Validation fixtures must not remove uncalibrated warnings and must not
   appear as `calibration_fixture_ids` in any `ResistanceFitRecord`.
4. **Calibration-fixture threshold.** A source may become a
   `calibration_fixture` only when source review accepts: rights for
   checked-in or reproducibly derived machine-readable rows; *measured*
   resistance/drag rather than model-derived values; kayak-envelope hull
   applicability under the project's constraints document; displacement/
   load and speed/Froude coverage relative to Fn 0.30/0.40/0.50; unit
   normalization; uncertainty treatment; stable fixture ID and version;
   and declared fitting scope or an explicit statement that fitting
   remains deferred. The existing
   `_validate_calibration_fixture_metadata` validator must continue to
   refuse promotion when any required field is missing.
5. **Model-to-model bar.** Model-derived tables (e.g., Sea Kayaker/Kanu.de
   Taylor Standard Series computed values) must not be promoted to a
   calibration fixture for an ITTC/Michell-shaped model under any later
   workflow. This protects against tuning one model against another model
   and presenting it as measured-source calibration.
6. **Rights-scope discipline.** Article rights and dataset rights must
   be tracked separately. CC BY 4.0 on a DataShare dataset deposit does
   not transfer to article prose, article tables, or related publications.
   Article-side rights restrictions do not transfer to a separately
   CC-BY-licensed dataset. Any later validation-fixture ingest must record
   the licensed scope explicitly and must mark CC BY 4.0 compliance
   requirements (attribution text, license link, change marking,
   no-added-restrictions clause).
7. **Unit-normalization and row-validation gate.** Before any row ingest
   the later workflow must require monotonic speed ordering; original-unit
   retention; explicit conversion to m/s and N; Froude recomputation with
   length basis; displacement/load presence; water-property assumptions
   (fresh/sea, temperature); and a recorded scale convention (model vs
   full-scale) for sources that report Froude-scaled speeds.
8. **No-promotion-by-this-decision.** This decision promotes no source.
   It does not select a "first" calibration fixture, it does not name
   Edinburgh as a validation fixture, and it does not pre-commit any
   Striatum workflow to a specific source choice. Each later promotion
   is its own workflow with its own review record.

## No-Claims Language That Must Remain In Force

This decision does not relax any of the following, and consuming workflows
must preserve them verbatim where they already appear in `docs/PRD.md`,
`docs/USER_GUIDE.md`, `docs/ROADMAP.md`, RFC 0027, and RFC 0042:

- Default resistance output remains `uncalibrated_comparative`. It is a
  raw comparative filter for candidate ranking, not a calibrated model,
  final prediction, design-fitness score, default optimization objective,
  or seaworthiness statement.
- Resistance output may stop saying uncalibrated *only* under RFC 0027's
  `claim_allows_calibrated_prediction` gate: a selected named model
  version with `accepted_fit`, accepted `calibration_fixture_ids`,
  persisted fit metrics and residuals, a validity envelope containing
  the evaluated hull and speed, and no uncalibrated warning codes.
- Validation fixtures may appear in reports, holdout metrics, or parser
  tests, but they must not be listed as `calibration_fixture_ids` for an
  accepted fit.
- CFD fixture-adapter results (RFC 0026 fixture-local-command outputs)
  remain `raw_unvalidated` and remain excluded from measured-source
  calibration fixtures.
- The `25%`-band success criterion in `docs/PRD.md:90` remains a
  calibration-roadmap criterion, not a present capability.
- This decision does not select a calibration source, does not authorize
  vendoring extracted measurement rows, does not authorize publishing
  any source PDF or digitized table, does not change resistance UI/copy,
  does not advance high-angle `GZ`, does not advance solver readiness,
  and does not change Pareto-default scoring or sweep ranking.

## Confidence

**High.**

Rationale: the recommended posture is mechanically aligned with the runtime
`SourceUse` taxonomy in `kayakgen/eval/calibration.py:13-19`, with the existing
validator metadata enforcement in
`kayakgen/eval/calibration.py:60-104`, with RFC 0042's narrowed scope and
explicit `rejected`-stays-review-only rule (`:105-133`), with RFC 0027's
landed three-stage acceptance gate over the same five literals (`:43-72`),
with the No-Claims Rules in `docs/ROADMAP.md:34-59`, and with the Batch F
sequencing in `docs/ROADMAP.md:166-189`. The decision authorizes only
documentation-shaped scope (review packet) and contract-hardening scope
(source-use mapping tests) that do not promote any source, do not change
default claim wording, and do not pre-commit a calibration source choice.
The only meaningful unknown — whether and when a kayak-envelope measured
source with open rights will exist — is correctly deferred to a later
workflow rather than resolved here. The research packet's external
evidence (Edinburgh DataShare, Gomes, Tzabiras, Sea Kayaker/Kanu.de, MDPI,
NIST/BIPM uncertainty) is consistent with the decision's threshold
language, and nothing in the local code or roadmap contradicts the
external citations.

## Sources Reviewed

Local:

- `AGENTS.md`
- `docs/PRD.md`
- `docs/ROADMAP.md` (especially No-Claims Rules §34-59 and Batch F §166-189)
- `docs/workflows/0050-decision-panel-research/SOURCES.md`
- `docs/workflows/0050-decision-panel-research/prompts/panel_vote.md`
- `docs/rfcs/0042-resistance-calibration-fixture-successor.md`
- `docs/rfcs/0027-resistance-calibration-acceptance.md`
- `docs/design/kayak_hull_design_constraints.md` (§72-86, §224-250 envelope)
- `kayakgen/eval/calibration.py` (`SourceUse` literal, validator,
  `default_resistance_source_registry` — verified directly)
- `striatum/0050-decision-panel-research/research/resistance_sources/RESEARCH.md`

External claims (as cited in the research packet, accessed 2026-05-14;
not re-fetched in this session — see "External-Source Check" above):

- Edinburgh DataShare dataset (`https://datashare.ed.ac.uk/handle/10283/4772`)
  — CC BY 4.0 dataset; Pacific-canoe-like slender hulls; supports
  validation-only candidate posture and a future validation-fixture
  promotion path conditional on an attribution/extraction schema.
- Gomes et al. 2018 SUNY metadata
  (`https://researchconnect.buffalo.edu/...`) — publisher copyright;
  supports rejection of Option C for rights reasons.
- Tzabiras et al. 2010 Sport Journal article
  (`https://thesportjournal.org/...`) — USSU all-rights-reserved; supports
  rejection of Option C for rights and envelope reasons.
- Sea Kayaker / Kanu.de PDF
  (`https://www.kanu.de/nuke/downloads/Resistance.pdf`) — model-derived
  (Taylor Standard Series at 113.4 kg payload); supports the
  model-to-model bar.
- MDPI "On the Physics of Kayaking"
  (`https://www.mdpi.com/2076-3417/12/18/8925`) — CC BY 4.0 article, no
  primary dataset; supports `citation_only`.
- NIST CUU (`https://pml.nist.gov/cuu/Uncertainty/basic.html`) and BIPM
  JCGM 100:2008 (`https://www.bipm.org/en/doi/10.59161/jcgm100-2008e`) —
  Type A vs Type B uncertainty; supports the uncertainty-treatment clause
  in the validation/calibration thresholds.

## Sub-Agent Help

No sub-agents were spawned. Verification of the runtime `SourceUse` enum,
the validator metadata enforcement, the default registry contents, and the
RFC 0042/RFC 0027 mapping was performed inline via direct read-only
inspection of `kayakgen/eval/calibration.py` and the relevant RFCs.
