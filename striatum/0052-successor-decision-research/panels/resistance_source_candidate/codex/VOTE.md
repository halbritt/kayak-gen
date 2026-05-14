---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-003
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_d90bb6cd85024dfbb4cacf2fba8b5ff0
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_resistance_source_candidate_codex
lease: lease_ebb56451bab04c6db24071ae99bdd977

# Vote - Resistance Source Candidate Decision

Vote: Edinburgh validation-only full packet

## Decision Sentence

Select the University of Edinburgh DataShare Pacific-canoe hydrodynamics
dataset as the first full resistance source-review packet, with the only
possible positive promotion capped at `validation_fixture`; no current source
is selected for `calibration_fixture`, and ordinary resistance output remains
`uncalibrated_comparative`.

## Evidence

The workflow 0052 research packet asks which measured resistance source should
receive the first full source-review packet. Its local constraint set is the
right one: current resistance output is a raw comparative filter, RFC 0042
requires rights/extraction/measured-quantity/unit/envelope/Froude/uncertainty
review before promotion, runtime source-use vocabulary must remain the five
RFC 0027 values, and validation fixtures cannot remove uncalibrated warnings
(`striatum/0052-successor-decision-research/research/resistance_source_candidate/RESEARCH.md`).
The current code and tests match that posture: `SourceUse` is limited to
`citation_only`, `validation_candidate`, `validation_fixture`,
`calibration_fixture_candidate`, and `calibration_fixture`; `rejected` maps to
no runtime source use; and the applied Edinburgh packet is still only
`validation_candidate` with missing extraction, units, and uncertainty plus
`outside_sea_kayak_calibration_envelope` as a non-promotion reason
(`kayakgen/eval/calibration.py`, `tests/test_calibration.py`).

Edinburgh is the only candidate that is ready to justify a full packet today.
The DataShare record identifies a dataset by DOI `10.7488/ds/3785`, states
that it includes raw towing-tank hydrodynamic-force data for three slender
hulls plus CAD models, lists spreadsheet/CAD/license files, and publishes file
checksums including the spreadsheet MD5
`ed88b247db4fe1ef62baeecfe7cc6daf`
([DataShare simple record](https://datashare.ed.ac.uk/handle/10283/4772),
[DataShare full record](https://datashare.ed.ac.uk/handle/10283/4772?show=full),
accessed 2026-05-14). The full record names the rights as Creative Commons
Attribution 4.0 International Public License, and CC BY 4.0 allows sharing and
adaptation with attribution, license link, change marking, and no added
restrictions ([CC BY 4.0 deed](https://creativecommons.org/licenses/by/4.0/),
accessed 2026-05-14).

That same external check also confirms why Edinburgh must be validation-only.
The related article metadata frames the work as ancient Pacific multi-hull /
catamaran side-force research, with fixed-sink-and-trim towing-tank tests,
leeway/yaw emphasis, and keywords such as ancient Pacific canoes, catamarans,
side force, and upwind sailing
([Edinburgh Research Explorer](https://www.research.ed.ac.uk/en/publications/hydrodynamics-of-three-slender-models-resembling-pacific-canoe-hu/),
accessed 2026-05-14). That is outside the project calibration envelope for
single-hull kayak/surfski displacement craft with design interest near
Fn 0.30, 0.40, and 0.50 (`docs/design/kayak_hull_design_constraints.md`).

The more kayak-specific sources lose on current rights or source readiness.
The Tzabiras K1 article exposes useful measured calm-water resistance tables
for an Olympic K-1, including speed, Froude number, and total resistance, but
the page footer is copyright/all-rights-reserved rather than an open row-data
license
([The Sport Journal](https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/),
accessed 2026-05-14). Gomes et al. is closer to kayak drag physics, and SUNY
metadata says total passive-drag values were based on experimental
single-seat-kayak data, but the metadata also records publisher copyright by
Informa/Taylor & Francis, with no open fixture-row deposit found
([SUNY Research Connect](https://researchconnect.suny.edu/en/publications/effect-of-wetted-surface-area-on-friction-pressure-wave-and-total/),
accessed 2026-05-14). The Sea Kayaker/Kanu compilation has strong sea-kayak
class relevance, but its PDF says the water-resistance values are calculated
using Taylor Standard Series at a 113.4 kg payload, so it is not primary
measured resistance data
([Kanu.de PDF](https://www.kanu.de/nuke/downloads/Resistance.pdf), accessed
2026-05-14).

This vote is consistent with the accepted decision trail. D005 required source
review and promoted no current source; D006 preserved the no-promotion gate for
calibrated resistance; RFC 0042 makes the next resistance source work a
source-review and fixture-promotion successor rather than fitting or output
claim changes (`docs/DECISION_LOG.md`, `docs/rfcs/0042-resistance-calibration-fixture-successor.md`).
Workflow 0051 then added review-packet machinery and applied only a partial
Edinburgh packet, still without validation- or calibration-fixture promotion
(`striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md`).

## Rejected Alternatives

Permission-first K1 packet loses because it is currently blocked on rights.
Tzabiras and Gomes are better kayak-physics validation leads than Edinburgh,
but checked-in rows or reproducible derived row fixtures should not be built
from all-rights-reserved or publisher-copyright material without permission or
an open data deposit. Even after permission, sprint K1 is a narrow envelope and
should remain validation-only unless a later packet explicitly accepts a
narrow calibration scope.

Search-before-any-packet loses because it stalls useful infrastructure despite
one open measured dataset being ready for a safe validation-only packet. RFC
0027 and RFC 0042 allow validation fixtures to test extraction, parsers,
reports, and holdout behavior while preserving the calibrated-resistance gate.
Waiting for a perfect calibration fixture before exercising the packet path is
unnecessary as long as no calibration claim changes.

Class-relevant historical recovery loses as the immediate decision because the
currently accessible sea-kayak materials are either model-derived, rights
unclear, or not recovered as reusable measured rows. Lazauskas/Winters/Tuck and
Sea Kayaker-derived evidence may be valuable later, but they are recovery and
permission tasks, not the first full source packet.

Immediate calibration promotion loses outright. No current candidate has the
complete package required for calibration: measured kayak-envelope rows,
reusable rights, normalized units, displacement/load metadata, speed/Froude
coverage, uncertainty treatment, fixture ID/version, accepted validity
envelope, fit scope, and later accepted-fit evidence.

## Implementation Gates And No-Claims Language

- The Edinburgh packet must bind every source file to locator, access date,
  checksum, rights/license statement, and required attribution.
- Extraction must be deterministic and documented: workbook/sheet names, row
  filters, zero-yaw and zero-speed policy, sign conventions, model IDs, model
  length basis, water properties, original fields, normalized SI fields, and
  Froude recomputation.
- Promotion to `validation_fixture` requires fixture ID/version, row manifest,
  units, uncertainty notes, accepted uses, warnings, and non-calibration
  language. The accepted use should be parser/report/holdout validation only.
- The packet must preserve `outside_sea_kayak_calibration_envelope` or an
  equivalent calibration blocker unless a later decision explicitly changes
  the project envelope.
- No Edinburgh artifact may be listed as a calibration fixture ID, used for a
  default fitted model, or used to remove final-prediction and uncalibrated
  warnings.
- `SourceUse` must remain the RFC 0027 five-value runtime vocabulary;
  `rejected` remains review-only.
- Ordinary resistance curves stay `uncalibrated_comparative` and may not be
  described as calibrated prediction, final prediction, validated CFD,
  default optimization fitness, design fitness, safety, seaworthiness, or
  broad kayak calibration.

Confidence: high
