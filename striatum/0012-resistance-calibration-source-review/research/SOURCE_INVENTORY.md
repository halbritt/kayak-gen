# Source inventory - resistance calibration

author: operator [self-declared: operator-source-inventory]
run: run_b8d2bd2b94f345c1a30521671cf0ba67
job: source_inventory
date: 2026-05-13

## Gate recommendation

No published source found in this pass should be promoted directly to the
canonical `calibrated_kayak_v1` dataset or checked into this repository as raw
fixture data.

The safest result is to keep the current resistance output `raw_ittc_michell`,
`uncalibrated`, and `comparative_filter_only`, while adding a source/provenance
contract and citation-only candidate registry for future calibration work. The
candidate sources are valuable, but they split into two imperfect groups:

- broad sea-kayak tables that are model-derived and have unclear redistribution
  rights;
- measured sprint-K1 data that are narrow, copyrighted, and not representative
  enough to calibrate touring/sea-kayak resistance generally.

## Candidate table

| Candidate | Data type | Coverage | Strength | Risk | Gate result |
|---|---|---|---|---|---|
| Sea Kayaker / kanu.de resistance compilation | Sea-kayak resistance table at standard knots, attributed to Sea Kayaker and Matt Broze/Taylor calculations | Broad sea-kayak hull list, typical touring speeds, 113.4 kg payload | Best class match and broadest hull coverage | Model-derived rather than measured; copyrighted magazine/third-party compilation; no clear open data license | Citation-only sanity/reference source, not calibration fixture |
| Individual Sea Kayaker review PDFs | Review pages with hull dimensions and resistance tables | Sea kayak / touring kayak specific | Often includes LWL, BWL, draft/displacement context, speed points | Magazine pages mirrored by vendors; copyrighted; resistance is often KAPER/Broze model output | Citation-only, do not vendor extracted tables |
| Gomes et al. 2018, Sports Biomechanics | Experimental total passive drag plus theoretical friction/pressure/wave decomposition for K1 Quattro M | Single sprint K1, 65/75/85 kg simulated paddler weights, up to 5.56 m/s | Direct kayak drag data with load sensitivity and wetted/frontal area values | Taylor & Francis copyright; accessible PDF mirror does not establish redistribution rights; sprint K1 geometry and speed regime | Validation/holdout candidate only, no checked-in extracted data |
| Gomes et al. 2015 passive-drag paper | Experimental sprint kayak passive drag across K1 sizes and simulated paddler weights | Sprint K1 class | Strong technical candidate if data can be obtained | Full data not openly licensed; likely publisher/author permission required | Candidate to request from authors, not current fixture |
| Tzabiras et al. K1 tow-tank study | Tow-tank total resistance, trim, CG rise, and numerical comparisons | Olympic K1, displacement 86.8 kg, 0.25 to 5.15 m/s | Measured data, broad speed range, discusses ITTC friction and residual/wave behavior | Sprint K1 only; web article figures/tables are not an open dataset declaration | Validation/guardrail candidate, not general calibration |
| KAPER / Winters method references | Kayak/canoe resistance prediction method | Kayak/canoe-specific empirical/model method | Historically important and used by Sea Kayaker | Method/formula rather than calibration data; licensing of spreadsheets/books unclear | Separate clean-room design question, not calibration data |
| Broze/Taylor/Mariner spreadsheet references | Model method used in Sea Kayaker context | Sea-kayak model estimates | Context for published tables | Spreadsheet/data rights unclear; model-to-model calibration risk | Citation-only |
| Mantha et al. K1 CFD study | CFD drag data for sprint K1 hulls | Sprint K1 | Useful high-performance context | CFD output rather than measured calibration; copyright restrictions | Literature context only |
| Delgado/Ruiz or MDPI kayak physics articles | Open-access modeling papers | Kayak propulsion/physics context | CC BY article text and formulas may be reusable with attribution | Not a primary resistance dataset; no additional data in at least one MDPI article | Reusable literature/model context, not calibration source |

## Evidence notes

Sea Kayaker / kanu.de:

- The kanu.de PDF identifies the values as published by Sea Kayaker and lists
  resistance versus speed for many sea kayaks.
- Its footnotes say the resistance values are calculated by Matt Broze using the
  Taylor Standard Series at a 113.4 kg payload.
- The same notes say the data are from Sea Kayaker magazine and selected from
  kayak reviews, which creates redistribution and compilation-rights risk.
- Later notes state the values are computer-model results that substantially
  agreed with some water-tank measurements, but the table itself is not primary
  measurement data.

Gomes et al. 2018:

- SUNY metadata identifies the article as peer-reviewed Sports Biomechanics,
  with DOI `10.1080/14763141.2017.1357748`.
- The abstract states total passive drag values were based on experimental data
  from a single-seat kayak with simulated paddler weights of 65, 75, and 85 kg.
- The accessible PDF reports a 5.2 m K1 Quattro M model, wetted surface/frontal
  submerged areas, and drag-component decomposition.
- Publisher copyright is Taylor & Francis/Informa; the PDF mirror is not enough
  to establish a right to check extracted tabular data into this repository.

Tzabiras et al.:

- The Sport Journal article reports calm-water towing-tank tests over 0.25 to
  5.15 m/s, K1 displacement 86.8 kg, dynamic trim/CG-rise measurements, ITTC'57
  friction decomposition, and residual/wave behavior.
- It is a strong K1 validation source because it includes measured total
  resistance and a speed range that overlaps and exceeds the kayak design band.
- It is still an Olympic K1 case, not a touring or sea-kayak population.

MDPI physics/modeling articles:

- At least one MDPI kayak physics article is CC BY 4.0, so article-derived
  formulas or examples may be reusable with attribution.
- Its data availability statement says there are no additional data, so it does
  not solve the calibration dataset problem.

## Calibration implication

The current raw model should not become `calibrated_kayak_v1` from these
sources. A defensible calibration source should provide, at minimum:

- measured total resistance at known speeds;
- water temperature/density or enough information to normalize;
- LWL, BWL, draft/displacement/load case, wetted surface, and preferably Cp;
- hull class labels and enough geometry/offsets to approximate the model input;
- clear license/provenance that allows either checked-in fixtures or a
  reproducible extraction script.

## Review questions for the next lanes

- Is a citation-only source registry useful enough to land now?
- Should Tzabiras/Gomes be modeled as K1 validation cases even without checked-in
  numeric fixtures?
- Should RFC 0005's xfailed acceptance criteria be revised before any
  calibration wrapper exists?
