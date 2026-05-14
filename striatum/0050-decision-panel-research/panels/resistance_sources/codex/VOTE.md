---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-008
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_3f6385031aed410db3a485110c7abb43
job: job_run_dc0a506896094745b380fd3ad2535d59_panel_resistance_sources_codex
lease: lease_0bfd54bdc6964e1ab60d5fb989178c4a

# Vote - Resistance Source Acceptance Decision

Vote: Source-review first; no current fixture promotion

## Decision Sentence

Require a documented resistance-source review packet before any measured source
can be promoted, keep `rejected` as review-only rather than a runtime
`SourceUse`, and promote no current source to `validation_fixture` or
`calibration_fixture` until rights, extraction, units, uncertainty, hull
envelope, source-use mapping, and accepted-review metadata pass.

## Evidence

RFC 0042 defines the remaining resistance work as a source-review and
fixture-promotion successor, not calibration, fitting, default-output changes,
or final prediction (`docs/rfcs/0042-resistance-calibration-fixture-successor.md:16-21`,
`:54-66`, `:80-84`). Its packet fields cover the right minimum evidence:
durable locator, rights, source type, measured quantity and units, hull
description, speed/Froude range, assumptions, extraction method, uncertainty,
and verdict (`docs/rfcs/0042-resistance-calibration-fixture-successor.md:86-103`).

The runtime vocabulary is already narrow and should stay that way. RFC 0042
maps source-review verdicts onto the five RFC 0027 `SourceUse` values and says
`rejected` must not become runtime fixture state (`docs/rfcs/0042-resistance-calibration-fixture-successor.md:105-133`).
The code currently has exactly those five literals (`kayakgen/eval/calibration.py:13-19`)
and already requires reproducible metadata for `validation_fixture` plus
accepted review and envelope metadata for `calibration_fixture`
(`kayakgen/eval/calibration.py:60-104`). RFC 0027 likewise keeps candidate,
validation, and calibration stages as groupings over `SourceUse`, states that
validation fixtures cannot remove uncalibrated warnings, and requires explicit
review metadata for calibration fixtures (`docs/rfcs/0027-resistance-calibration-acceptance.md:38-72`).

The roadmap sequence supports this conservative decision: add the checklist,
apply it to one source without promotion unless evidence is complete, add
source-use mapping checks, ingest validation fixtures only after rights and
extraction pass, and ingest calibration fixtures only after a kayak-envelope
measured source is accepted (`docs/ROADMAP.md:166-189`). Current resistance
curves must remain `uncalibrated_comparative`, not calibrated prediction,
design-fitness score, or default optimization objective (`docs/ROADMAP.md:38-40`).
The implementation claim gate also requires calibrated model state, final
prediction accepted use, calibration fixture IDs, model version, accepted fit,
fit metrics, validity envelope, and no uncalibrated warnings before calibrated
prediction is allowed (`kayakgen/eval/claims.py:195-210`).

The research packet's current-source review is consistent with my independent
checks. Edinburgh DataShare is the strongest open measured candidate: its
record identifies a dataset, DOI, raw towing-tank hydrodynamic-force data, CAD
models, Creative Commons Attribution 4.0 rights, and file checksums
(https://datashare.ed.ac.uk/handle/10283/4772 and
https://datashare.ed.ac.uk/handle/10283/4772?show=full, accessed
2026-05-14). CC BY 4.0 permits sharing and adaptation with attribution,
license link, change marking, and no added restrictions
(https://creativecommons.org/licenses/by/4.0/, accessed 2026-05-14). That
supports future validation-fixture review after an extraction/attribution
schema, but the registry and packet both flag the hull class as
Pacific-canoe-like, fixed-sink/trim, validation-not-calibration
(`kayakgen/eval/calibration.py:113-134`;
`striatum/0050-decision-panel-research/research/resistance_sources/RESEARCH.md:38`).

The kayak design envelope is single-hull kayak/surfski oriented, with length,
beam, draft, Cp, and Fn targets around 0.30, 0.40, and 0.50
(`docs/design/kayak_hull_design_constraints.md:222-250`). Current K1 sources
are relevant validation candidates but not fixtures yet. SUNY's Gomes metadata
confirms experimental single-seat kayak passive-drag data, simulated weights,
and drag components, while also recording Taylor and Francis publisher
copyright (https://researchconnect.buffalo.edu/en/publications/effect-of-wetted-surface-area-on-friction-pressure-wave-and-total/,
accessed 2026-05-14). The Sport Journal Tzabiras article reports measured
total resistance over 0.25 to 5.15 m/s and tabulated speeds/Froude/resistance,
but the page footer is copyright/all-rights-reserved
(https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/,
accessed 2026-05-14). Those rights gaps block checked-in fixture rows now.

The Sea Kayaker/Kanu source is class-relevant but not primary measured
resistance: the PDF attributes the table to Sea Kayaker and says the
water-resistance values are calculated using Taylor Standard Series at
113.4 kg payload (https://www.kanu.de/nuke/downloads/Resistance.pdf, accessed
2026-05-14). That makes it useful citation context, not validation or
calibration evidence. NIST uncertainty guidance reinforces that promotion
packets should capture uncertainty sources and Type A/Type B treatment rather
than silently accepting rows without uncertainty metadata
(https://pml.nist.gov/cuu/Uncertainty/basic.html, accessed 2026-05-14).

## Rejected Alternatives

Option B, Edinburgh validation fixture immediately after extraction-schema
work, is the right follow-up but the wrong immediate decision. Edinburgh has
open rights and measured rows, yet RFC 0042 requires source-review metadata and
says no current source is promoted by the RFC alone
(`docs/rfcs/0042-resistance-calibration-fixture-successor.md:203-220`). It
should remain `validation_candidate` until the review packet, extraction
schema, checksums, unit normalization, uncertainty notes, and warnings pass.

Option C, K1 validation fixture by permission, is not actionable now because
permission or reusable data deposits are not in hand. Even after rights pass,
sprint K1 scope remains narrower than the sea-kayak/surfski envelope, so it
would be validation-only unless a later review accepts a specific narrower
validity envelope.

Option D, wait for a kayak-envelope calibration source before any fixture work,
is too strict. It protects calibration claims, but it would also block useful
validation-infrastructure work that RFC 0027 allows so long as validation
fixtures cannot remove warnings or become calibration fixture IDs
(`docs/rfcs/0027-resistance-calibration-acceptance.md:59-64`, `:137-142`).

## Implementation Gates And No-Claims Language

- Add a source-review packet/checklist with the fields in RFC 0042 and the
  research packet: rights, extraction, measured quantity, original and SI
  units, hull envelope, speed/Froude range, uncertainty, verdict, source-use
  mapping, and explicit non-promotion reasons.
- Add tests proving the runtime `SourceUse` literals stay exactly
  `citation_only`, `validation_candidate`, `validation_fixture`,
  `calibration_fixture_candidate`, and `calibration_fixture`; `rejected` may
  serialize only as a review outcome.
- Promote no source to `validation_fixture` until rights, extraction, rows,
  units, fixture ID/version, uncertainty notes, and warnings are reproducible.
- Promote no source to `calibration_fixture` until a measured kayak-envelope
  source has accepted rights for machine-readable rows, review metadata,
  normalized units, displacement/load and Fn coverage, uncertainty treatment,
  validity envelope, and fit-scope statement.
- Keep validation fixtures out of `calibration_fixture_ids`; they may support
  parser/report/holdout behavior only.
- Keep all ordinary resistance output labeled `uncalibrated_comparative` until
  a later accepted-fit workflow satisfies `claim_allows_calibrated_prediction`.
- Do not describe resistance as calibrated prediction, final prediction,
  design fitness, seaworthiness evidence, default optimization fitness, or
  validation of raw CFD output.

Confidence: high
