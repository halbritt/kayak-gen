---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: operator [self-declared: operator-0052-panel-wave1-gemini-3]
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_014e97023e9b405ead3d2b4f95bb2037
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_resistance_source_candidate_gemini
lease: lease_cdcc3607cd2c4d538727808c7a84c0f2

# Vote — Resistance Source Candidate Decision

## Vote

**Option A — Edinburgh DataShare full source-review packet for validation only.** The dataset will be eligible for promotion to `validation_fixture` but strictly forbidden from `calibration_fixture`. Reject Options B, C, and D.

## Decision Sentence

Select the University of Edinburgh DataShare dataset "Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls" (DOI `10.7488/ds/3785`, CC BY 4.0) to receive the first full RFC 0042 resistance source-review packet, with a maximum allowable verdict of `validation_fixture`. Promotion to `calibration_fixture` is prohibited because the models reside outside the sea kayak/surfski design envelope. Default resistance output remains `uncalibrated_comparative`.

## Evidence

The `striatum/0052-successor-decision-research/research/resistance_source_candidate/RESEARCH.md` artifact recommends Option A and provides the critical constraint framework:

- **Rights & Reproducibility**: Edinburgh DataShare provides the only candidate with a verified CC BY 4.0 license, available source files (spreadsheet, IGES), and checksums (e.g., MD5 `ed88b247db4fe1ef62baeecfe7cc6daf`). This supports an open, reproducible extraction pipeline.
- **Envelope & Calibration Limits**: The Edinburgh models are Pacific canoes tested at fixed sink and trim, prioritizing side-force and yaw. This explicitly falls outside the defined single-hull kayak/surfski envelope (`docs/design/kayak_hull_design_constraints.md`). Therefore, it cannot safely calibrate the project's kayak models, enforcing a strict cap at `validation_fixture`.
- **Runtime Consistency**: The codebase restricts `SourceUse` to five literals: `citation_only`, `validation_candidate`, `validation_fixture`, `calibration_fixture_candidate`, and `calibration_fixture` (`kayakgen/eval/calibration.py`). The next workflow will complete the missing checklist items (extraction, units, uncertainty) to move Edinburgh from `validation_candidate` to `validation_fixture`, cleanly exercising the RFC 0042 validation pipeline without violating calibration integrity.

## Rejected Alternatives

- **Option B (Permission-First K1 Packet)**: Tzabiras and Gomes offer superior kayak physics, but their data is trapped behind USSU and Informa/Taylor & Francis publisher copyrights. We cannot commit to a first full packet based on a pending rights negotiation, nor check in rows from all-rights-reserved articles.
- **Option C (Calibration-Source Search Before Any Fixture Packet)**: Waiting for a perfect calibration source stalls the implementation of independently valuable validation infrastructure. We can test parsers, reports, and holdout mechanisms now with Edinburgh.
- **Option D (Recover Class-Relevant Historical Evidence)**: Sources like Lazauskas/Winters/Tuck are currently inaccessible or model-derived (Sea Kayaker / Kanu.de using Taylor Standard Series). Model-to-model calibration is forbidden. Recovery is a valid future task, but not a candidate for the first concrete packet.

## Implementation Gates And No-Claims Language

To preserve project integrity, the next workflow must observe these bounds:

- **Maximum Verdict**: The Edinburgh packet must explicitly record `outside_sea_kayak_calibration_envelope` and limit its positive promotion to `validation_fixture`.
- **Extraction Protocol**: The packet must securely bind source files via checksums, define a reproducible extraction script (e.g., zero-yaw filtering from `Results vs speed`), and explicitly normalize SI units and Froude ranges based on model length.
- **Uncertainty**: The `uncertainty` field requires documented Type A or Type B reasoning per NIST/BIPM guidelines; it cannot be trivially bypassed.
- **Strict Separation of Claims**: Default resistance output must remain `uncalibrated_comparative`. Validation fixtures may only validate infrastructure (parsers/reports/holdouts) and cannot clear uncalibrated warnings or satisfy calibration requirements.

## Confidence

**High.** The recommendation logically flows from the intersection of available rights, design envelope constraints, and the existing code contract. Option A exercises the necessary validation infrastructure safely, while correctly deferring calibration to a future workflow with an appropriate source.

## Sources Reviewed

Local:
- `docs/ROADMAP.md`
- `docs/DECISION_LOG.md`
- `docs/design/kayak_hull_design_constraints.md`
- `docs/rfcs/0042-resistance-calibration-fixture-successor.md`
- `kayakgen/eval/calibration.py`
- `striatum/0052-successor-decision-research/research/resistance_source_candidate/RESEARCH.md`

External (via research artifact, accessed 2026-05-14):
- Edinburgh DataShare full record (DOI `10.7488/ds/3785`, CC BY 4.0)
- The Sport Journal (Tzabiras, USSU copyright)
- SUNY Research Connect (Gomes, Taylor & Francis copyright)
- NIST CUU and BIPM JCGM 100:2008 (Uncertainty definitions)

## Sub-Agent Help

No sub-agents were used in drafting this response.
