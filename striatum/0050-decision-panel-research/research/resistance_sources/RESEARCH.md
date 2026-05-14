---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-006
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: research
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_11fb125eb2324aaf8e151077ed714193
job: job_run_dc0a506896094745b380fd3ad2535d59_research_resistance_sources

# Research - Resistance Source Acceptance Decision

## Decision Question

What evidence must a measured resistance source provide before kayakgen may promote it from candidate source to validation fixture or calibration fixture, and should any current source be promoted before validation/calibration fixture work proceeds?

## Local Project Constraints

- Current resistance output is `uncalibrated_comparative`: a raw comparative filter, not calibrated prediction, final design fitness, or a default optimization objective (`docs/ROADMAP.md:38-40`, `docs/USER_GUIDE.md:102-104`, `docs/USER_GUIDE.md:458-459`).
- RFC 0042 narrows resistance work to source review and fixture promotion, not fitting, row check-in, calibrated output, final prediction, or design-fitness scoring (`docs/rfcs/0042-resistance-calibration-fixture-successor.md:16-21`, `:54-66`).
- The required source-review packet already has the right shape: stable source ID/citation, locator, rights, source type, measured quantity and units, hull description/envelope, speed/Froude range, assumptions, extraction method, uncertainty notes, and verdict (`docs/rfcs/0042-resistance-calibration-fixture-successor.md:86-103`).
- Runtime source-use values must remain the five existing `SourceUse` values: `citation_only`, `validation_candidate`, `validation_fixture`, `calibration_fixture_candidate`, and `calibration_fixture`; `rejected` is a review outcome only, not a runtime fixture state (`docs/rfcs/0042-resistance-calibration-fixture-successor.md:105-133`, `kayakgen/eval/calibration.py:13-19`).
- Validation fixtures can support parser/report/holdout behavior, but cannot fit the default model or remove uncalibrated warnings; calibration fixtures require accepted source review, stable fixture ID/version, normalized rows, and declared fitting scope (`docs/rfcs/0027-resistance-calibration-acceptance.md:43-72`).
- Calibrated-prediction wording is gated by `claim_allows_calibrated_prediction`: `calibrated_model`, final-prediction accepted use, calibration fixture IDs, model version, `accepted_fit`, fit metrics, validity envelope, and no uncalibrated warning codes (`kayakgen/eval/claims.py:195-210`).
- The kayak design envelope is single-hull kayak/surfski oriented: `L_oa` 4.0-6.5 m, `B_wl` 0.36-0.58 m, draft 0.10-0.16 m, `Cp` 0.50-0.62, target resistance points around Fn 0.30, 0.40, and 0.50 (`docs/design/kayak_hull_design_constraints.md:72-86`, `:224-250`).
- The current registry records Edinburgh, Sea Kayaker/Kanu, Gomes, Tzabiras, and MDPI sources, and explicitly contains no accepted calibration fixture (`kayakgen/eval/calibration.py:107-204`).

## Current External Evidence

Access date for external sources: 2026-05-14.

| Source | Rights and extraction | Measured quantity / units | Hull and speed envelope | Fixture implication |
| --- | --- | --- | --- | --- |
| University of Edinburgh DataShare, "Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls" | DataShare full record lists rights as Creative Commons Attribution 4.0 and provides spreadsheet, CAD, README, license files, and checksums. CC BY 4.0 allows sharing/adaptation with attribution, license link, change marking, and no added restrictions. | Dataset description says it contains raw towing-tank hydrodynamic forces, force coefficients/plots, and CAD models. Local workbook inspection found measured drag/side-force/heave/pitch fields, resistance in N, speed in m/s, density, Reynolds number, Froude number, and full-scale equivalent speed. | Research Explorer article context says the tests concern ancient Pacific multi-hull/catamaran-style vessels, side-force/leeway/yaw, and three slender models at fixed sink and trim. Workbook Froude-scaling rows span model speeds 0.4-1.6 m/s and Fn about 0.117-0.466. | Strong validation-candidate source. Promote to `validation_fixture` only after an extraction/attribution schema exists. Do not promote to kayak calibration fixture because the hull class and test setup are outside the sea-kayak design envelope. |
| Gomes et al. 2018, Sports Biomechanics, DOI `10.1080/14763141.2017.1357748` | SUNY metadata records publisher copyright by Informa/Taylor & Francis; no open fixture redistribution right was found. | Metadata says total passive drag values were based on experimental data collected in a single-seat kayak, with simulated kayaker weights 65, 75, and 85 kg; drag components include friction, pressure, and wave contributions. | Single sprint K1 article; top tested velocity in the metadata is 5.56 m/s. It is relevant to high-performance kayak drag but narrow relative to touring/sea-kayak and surfski class coverage. | Keep as `validation_candidate` by citation. It may become a validation fixture only with permission or a reusable data deposit and extraction metadata. It should not calibrate a general kayak model now. |
| Tzabiras et al. 2010, The Sport Journal, Olympic K-1 flat-water racing kayak | Article is openly readable, but page footer states United States Sports University copyright/all rights reserved; no open fixture/data license was found. | The article reports total resistance, dynamic trim, CG rise, and towing speed; tables provide speed, Froude number, and total resistance in kgf/kp and N. | Olympic K1 medium weight category; displacement 86.8 kg, fresh water at 15 C, calm-water speeds 0.244-5.153 m/s and Fn 0.035-0.730. | Useful validation-candidate citation because it has explicit measured rows and broad speed/Fn coverage, but not a checked-in fixture without rights review. Sprint K1/load-case specificity blocks general sea-kayak calibration. |
| Sea Kayaker / Kanu.de resistance compilation | Public PDF is a compilation attributed to Sea Kayaker review data; no open redistribution license was found. | PDF footnotes state water resistance vs speed values are calculated by Matt Broze using Taylor Standard Series at 113.4 kg payload; units are kg versus knots. | Broad sea-kayak hull coverage and class relevance, but values are model-derived rather than primary measured resistance. | `citation_only` context. It is the best class-matching comparison source, but model-to-model calibration and rights risk make it unsuitable for validation or calibration fixture promotion. |
| MDPI "On the Physics of Kayaking" | Article is CC BY 4.0, but the data availability statement says there are no additional data. | Provides modeling context for skin friction, wave drag, aerodynamic drag, on-water deceleration, and simplified Michell/ITTC-style reasoning. | General kayak physics context, not a fixture dataset. | `citation_only` modeling context only. It can support explanatory docs but not source acceptance for measured resistance fixtures. |
| NIST / GUM uncertainty guidance | NIST summarizes uncertainty expression based on TN 1297 / ISO GUM; BIPM JCGM 100:2008 establishes general rules for evaluating and expressing measurement uncertainty. | NIST distinguishes Type A uncertainty from statistical observations and Type B uncertainty from other information; each component is represented as standard uncertainty. | Applies to any measured-source packet where original uncertainty, instrument specs, calibration data, or digitization error need to be represented. | Acceptance packets should require source-provided uncertainty when available, otherwise a documented qualitative/Type B uncertainty note. Missing numeric uncertainty should block calibration fixture promotion unless final review accepts stricter fit thresholds. |

External source URLs:

- Edinburgh DataShare dataset: https://datashare.ed.ac.uk/handle/10283/4772
- Edinburgh DataShare full item record: https://datashare.ed.ac.uk/handle/10283/4772?show=full
- CC BY 4.0 deed: https://creativecommons.org/licenses/by/4.0/
- Edinburgh Research Explorer article metadata: https://www.research.ed.ac.uk/en/publications/hydrodynamics-of-three-slender-models-resembling-pacific-canoe-hu/
- Gomes SUNY metadata: https://researchconnect.buffalo.edu/en/publications/effect-of-wetted-surface-area-on-friction-pressure-wave-and-total/
- Tzabiras Sport Journal article: https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/
- Sea Kayaker / Kanu.de PDF: https://www.kanu.de/nuke/downloads/Resistance.pdf
- MDPI "On the Physics of Kayaking": https://www.mdpi.com/2076-3417/12/18/8925
- NIST uncertainty summary: https://pml.nist.gov/cuu/Uncertainty/basic.html
- BIPM JCGM 100:2008 page: https://www.bipm.org/en/doi/10.59161/jcgm100-2008e

## Acceptance Fields Required Before Promotion

Minimum source-review packet fields:

- `source_id`, title, citation, DOI/URL/archive locator, access date, source-file checksums when files are downloaded.
- Rights for original material and derived rows, including license URL, attribution text, any restrictions, and whether row extraction/check-in is allowed.
- Source type: tow-tank measurement, passive-drag experiment, on-water measurement, model-derived table, secondary citation, or CFD/model output.
- Measured quantity and provenance: total resistance, drag force, coefficients, passive drag, added resistance, decomposition, or calculated/model-derived values.
- Original units and normalized SI units: speed, resistance/force, coefficients, displacement/load, length, density, viscosity, temperature, and fresh/seawater assumption.
- Hull envelope: class, dimensions, L/B, draft/displacement/load, available offsets/CAD/lines, section type, appendages, paddler/fixture state, trim/sinkage policy.
- Speed/Froude range: original speeds, converted m/s and knots as needed, Froude formula and length basis, covered Fn bands relative to project targets around 0.30/0.40/0.50.
- Extraction metadata: extractor, date, source file/table/sheet, row filters, tooling/script version, conversions, rounding, digitization method if applicable, and reproducibility instructions.
- Uncertainty: source uncertainty, instrument/calibration notes, repeatability/statistical notes, digitization uncertainty, Type B assumptions where source uncertainty is absent, and whether uncertainty is numeric or qualitative.
- Review metadata: reviewer, date, verdict, reasons, source-use mapping, fixture ID/version if promoted, warnings, accepted uses, validity envelope, and explicit non-promotion reasons.

Promotion thresholds:

- `validation_candidate`: citation/rights are known enough to track, but rows may be unavailable, rights incomplete, source out of envelope, or extraction not done.
- `validation_fixture`: rights, units, extraction, rows, and fixture metadata are adequate for parser/report/holdout checks. Hull may be out of kayak calibration envelope, but warnings must make that explicit.
- `calibration_fixture_candidate`: source appears kayak-envelope-relevant but still lacks accepted review, extraction, row schema, or uncertainty treatment.
- `calibration_fixture`: accepted rights for checked-in or reproducibly derived machine-readable rows, measured resistance/drag rather than model-derived values, kayak-envelope applicability, displacement/load and speed/Froude coverage, unit normalization, uncertainty treatment, fixture ID/version, and intended fit parameters or a statement that fitting remains deferred.
- `rejected`: terminal review outcome only. Do not serialize it as `SourceUse`, fixture input, fit input, or claim-gate participant.

## Viable Options

### Option A - Conservative Default: Source-Review Packet First, No Fixture Promotion

Add only the source-review packet/checklist and source-use mapping tests, then apply it to one candidate source such as Edinburgh without promoting it unless every required field is complete.

Pros: aligns directly with RFC 0042 and roadmap Batch F; keeps current warnings intact; handles negative outcomes cleanly; avoids rights and envelope overclaim.
Cons: does not add numeric validation rows immediately.

### Option B - Edinburgh Validation Fixture After Extraction Schema

Define an attribution/extraction schema and promote Edinburgh from `validation_candidate` to `validation_fixture` only after machine-readable rows are reproducibly extracted with source-file checksum, sheet/row filters, units, scale, uncertainty notes, and warnings.

Pros: uses the strongest open measured dataset currently known; tests fixture ingest and unit normalization on real data.
Cons: validation-only because Pacific-canoe/fixed-sink-trim conditions are outside the default kayak calibration envelope; needs careful article-vs-dataset rights separation.

### Option C - K1 Validation Fixture By Permission

Pursue permission or open data deposits for Gomes and/or Tzabiras sprint-K1 data, then promote only to `validation_fixture` if rights and extraction metadata pass.

Pros: closer craft type than Edinburgh and directly useful for high-performance kayak trend checks.
Cons: sprint K1 bias remains; rights are currently insufficient; still not broad sea-kayak calibration.

### Option D - Wait For Kayak-Envelope Calibration Source

Keep all reviewed sources as registry/citation context until a measured sea-kayak or close kayak-envelope source with open rights, geometry/load metadata, speeds near Fn 0.30-0.50, and uncertainty is found.

Pros: strongest protection against model-to-model or out-of-envelope calibration.
Cons: stalls validation-fixture ingest and parser/report infrastructure that could be safely exercised with validation-only sources.

## Risks And Unknowns

- Rights can be source-specific: Edinburgh dataset rows are CC BY 4.0, while the related 2025 article metadata is SNAME copyright/all rights reserved. The packet must not transfer article rights onto dataset rows or copy article tables/prose.
- Unit conversions are high-risk: Sea Kayaker uses kg vs knots, Tzabiras uses kgf/kp and N, Edinburgh workbook has model and full-scale speed fields, and sources may mix coefficients with dimensional force.
- Froude range must record the length basis. Model-scale Fn and full-scale equivalent speed are not interchangeable without explicit scale metadata.
- Hull-envelope mismatch is the main calibration blocker. Edinburgh is open and measured but canoe/multihull-oriented; Gomes and Tzabiras are kayak measured sources but sprint K1-specific.
- Missing numeric uncertainty should not be silently accepted for calibration. It can be acceptable for citation, candidate, or possibly validation-fixture work with warnings, but calibration fitting needs either numeric uncertainty or stricter residual/holdout thresholds accepted by review.
- Model-derived tables are tempting because they cover many sea kayaks. They should not calibrate Michell/ITTC output because that would tune one model against another model.
- UI/report/sweep code must not treat validation fixtures as calibration fixture IDs or treat calibrated resistance as final design fitness.

## Implementation Gates

1. Add a source-review packet template under the RFC 0042 successor workflow, with the fields listed above.
2. Add source-use mapping tests proving the five runtime `SourceUse` values remain unchanged and `rejected` stays review-only.
3. Add validation rules equivalent to the current model requirements: validation fixtures require fixture ID, measured quantity, measurement units, rights status, and extraction status; calibration fixtures additionally require hull envelope, uncertainty notes, validity ranges, accepted review status, and measured data.
4. Add a unit-normalization and row-validation test plan before ingesting rows: monotonic speed ordering, force units, original-unit retention, m/s conversion, Fn recomputation, displacement/load presence, and water-property assumptions.
5. Promote no source to `calibration_fixture` until a measured kayak-envelope source passes review and the fixture names a validity envelope and fit scope.
6. Keep all ordinary resistance outputs `uncalibrated_comparative` until a later accepted-fit workflow satisfies `claim_allows_calibrated_prediction`.

## Recommendation

Use Option A as the immediate decision: require a source-review packet and mapping tests before any fixture promotion, apply the packet to one candidate source, and do not promote any current source to calibration fixture.

If implementation bandwidth allows a second step, Option B is the safest validation-only follow-up: Edinburgh can become a validation fixture only after extraction/attribution metadata lands. The evidence does not support calibrated kayak prediction, calibrated wording, or default resistance-based optimization from any currently reviewed source.
