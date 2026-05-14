---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-005
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: research
date: 2026-05-14
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_73662ac0769044dda7cebb2c9718c452
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_research_resistance_source_candidate
lease: lease_39704c2a13094f9fa2e2ba31d3c0323b

# Research - Resistance Source Candidate Decision

## Decision Question

Which measured resistance source, if any, should receive the first full source-review packet for validation or calibration fixture promotion?

## Local Constraints And No-Claims Boundaries

- Current resistance output remains `uncalibrated_comparative`: useful only as a raw comparative filter, not a calibrated final prediction, design-fitness score, default optimization objective, or validated CFD result (`docs/PRD.md`, `docs/USER_GUIDE.md`, `docs/ROADMAP.md`, RFCs 0005, 0025, 0027, 0042).
- RFC 0042 requires source-review evidence before fixture promotion: rights, extraction, measured quantity, units, hull envelope, speed/Froude range, uncertainty, verdict, and non-promotion reasons.
- Runtime source-use vocabulary must stay limited to the five RFC 0027 values in `kayakgen/eval/calibration.py`: `citation_only`, `validation_candidate`, `validation_fixture`, `calibration_fixture_candidate`, and `calibration_fixture`. `rejected` is review-only.
- A validation fixture may test extraction, row parsing, reporting, or holdout behavior, but cannot remove uncalibrated warnings or satisfy calibration fixture IDs.
- A calibration fixture requires measured resistance/drag data, reusable row rights, kayak-envelope applicability, displacement/load and speed/Froude coverage, unit normalization, uncertainty treatment, fixture ID/version, and review-accepted fit scope.
- The design envelope is kayak/surfski single-hull displacement craft: roughly `L_oa` 4.0-6.5 m, `B_wl` 0.36-0.58 m, draft 0.10-0.16 m, `Cp` 0.50-0.62, and resistance interest near Fn 0.30, 0.40, and 0.50 (`docs/design/kayak_hull_design_constraints.md`).
- Workflow 0051 already added source-review packet models and applied a partial Edinburgh packet as `validation_candidate`; it did not promote any source to `validation_fixture` or `calibration_fixture` (`striatum/0051-implementation-burndown-stage1/implementation/resistance_source_review/PATCH_SUMMARY.md`).

## Current External Evidence

External sources accessed on 2026-05-14.

| Candidate | Rights | Extraction And Availability | Hull Envelope | Measured Quantity And Units | Uncertainty | Review Implication |
| --- | --- | --- | --- | --- | --- | --- |
| University of Edinburgh DataShare, "Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls" | DataShare full record lists `Creative Commons Attribution 4.0 International Public License`; the CC BY 4.0 deed permits reuse with attribution and change marking. The record also exposes source-file checksums. Sources: [DataShare full record](https://datashare.ed.ac.uk/handle/10283/4772?show=full), [CC BY 4.0 deed](https://creativecommons.org/licenses/by/4.0/). | Files are available directly: spreadsheet, IGES hull geometries, README, license text, and license file. I downloaded the spreadsheet from the DataShare bitstream and inspected workbook structure locally. Sheets include `Averaged Data`, `Results vs speed`, `Results vs yaw`, `Prohaska`, and `Froude Scaling`; DataShare records the spreadsheet MD5 as `ed88b247db4fe1ef62baeecfe7cc6daf`. Source: [DataShare simple record](https://datashare.ed.ac.uk/handle/10283/4772). | Three slender Pacific-canoe-like hull models at fixed sink and trim. Related article metadata frames the experiment around ancient Pacific multi-hull/catamaran side-force and yaw/leeway behavior, not sea kayaks. Source: [Edinburgh Research Explorer](https://www.research.ed.ac.uk/en/publications/hydrodynamics-of-three-slender-models-resembling-pacific-canoe-hu/). | DataShare says the dataset includes raw towing-tank hydrodynamic forces plus force coefficients and CAD. Workbook headers include drag force, side force, heave, pitch, velocity, total drag, resistance, total lift, sideforce, dynamic pressure, and coefficients. Units visible in workbook include `m/s`, `N`, `mm`, `deg`, and `N/m2`; Froude scaling sheet shows model speeds 0.4-1.6 m/s with Fr about 0.117-0.466. | No accepted row-level uncertainty treatment is currently bound to extracted rows. The workbook has repeated runs and comments, but the packet still needs a repeatability/instrument/digitization uncertainty note before fixture promotion. | Best first full packet for `validation_fixture` decision because rights and files are strongest. Not a calibration fixture because hull class/test purpose are outside kayak calibration envelope. |
| Tzabiras et al., "Experimental and Numerical Study of the Flow Past the Olympic Class K-1 Flat Water Racing Kayak at Steady Speed" | Article is openly readable on The Sport Journal, but the site footer states United States Sports University copyright/all rights reserved. No reusable data license was found. Source: [The Sport Journal](https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/). | Tables are extractable from HTML, but extraction would derive rows from an all-rights-reserved article page unless permission is obtained. | Olympic flat-water racing K1, medium athlete category, displacement 86.8 kg, fresh water at 15 C, heave/trim free in the towing setup. Sources: [methods section](https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/), [calm-water results](https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/). | Table 2 reports measured calm-water total resistance in `Nt`, speed in `m/s`, and Froude number from 0.244 to 5.153 m/s and Fn 0.035-0.730. It also reports coefficients and residual resistance. Source: [Table 2](https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/). | No source uncertainty table found on the page. The paper reports deviations between numerical and experimental resistance, but that is not measurement uncertainty. | Strong kayak validation candidate by physics and envelope, but not first fixture packet unless rights/permission are secured. Too sprint-K1-specific for general sea-kayak calibration. |
| Gomes et al. 2018, "Effect of wetted surface area on friction, pressure, wave and total drag of a kayak" | SUNY metadata records publisher copyright by Informa/Taylor & Francis. No open data deposit or reusable row license was found. Source: [SUNY Research Connect](https://researchconnect.suny.edu/en/publications/effect-of-wetted-surface-area-on-friction-pressure-wave-and-total/). | Metadata and DOI are stable; article rows are not openly available as fixture data. | Single-seat kayak, sprint/K1-style context, simulated kayaker weights. | SUNY abstract states total passive drag values were based on experimental data from a single-seat kayak, with drag decomposed into friction, pressure, and wave components. Source: [SUNY Research Connect](https://researchconnect.suny.edu/en/publications/effect-of-wetted-surface-area-on-friction-pressure-wave-and-total/). | Metadata does not expose reusable uncertainty rows. | Keep as `validation_candidate` and possible permission target. Do not select as first full packet while rights and row availability are missing. |
| Sea Kayaker / Kanu.de resistance compilation | Public PDF has no open redistribution/license statement for extracted rows. | The PDF is available, but its notes say the values are calculated from Taylor Standard Series at 113.4 kg payload. Source: [Kanu.de PDF](https://www.kanu.de/nuke/downloads/Resistance.pdf). | Broad sea-kayak coverage; best class match. | Resistance is in `kg` versus speed in knots, but model-derived rather than measured. | No measurement uncertainty because it is not primary measured data. | `citation_only`. Useful context, not a measured validation/calibration fixture candidate. |
| Lazauskas / Winters / Tuck sea-kayak drag notes | SPONET bibliographic record states copyright all rights reserved. The original `cyberiad.net` source now redirects to unrelated content in this browser session. Sources: [SPONET record](https://sponet.de/Record/4000729), [cyberiad redirect](https://www.cyberiad.net/library/kayaks/skmag/skmag.htm). | Current durable access is bibliographic/summary only, not a stable machine-readable data source. | Four popular single-seat sea kayaks, class-relevant if the original report and rights could be recovered. | SPONET summary says predicted calm-water resistance was compared with experimental results, but no reusable measured rows are currently available from the primary source. | Unknown. | Not first packet until source recovery and rights review succeed. It may be worth an archive/author-permission search later because it is the most class-relevant measured-context lead. |
| MDPI "On the Physics of Kayaking" | Article is CC BY 4.0. Source: [MDPI article](https://www.mdpi.com/2076-3417/12/18/8925). | Article is available, but it is not a fixture dataset. | K1 physics/modeling and on-water trials. | It includes modeling context and experimental trial descriptions, not a primary tow-tank fixture row set for resistance calibration. | Not applicable as fixture uncertainty. | `citation_only` modeling context. |

## Viable Options

### Option A - Conservative Default: Edinburgh Full Packet For Validation Decision Only

Run the first complete review packet against the Edinburgh DataShare source, but limit the possible positive outcome to `validation_fixture`. The packet should fill source-file checksums, extraction script/row filters, attribution, units, scale/Froude basis, and uncertainty notes. It should preserve `outside_sea_kayak_calibration_envelope` as a calibration blocker.

Pros:

- Only reviewed candidate with open measured files, CAD, license text, and checksums available today.
- Exercises real extraction and manifest infrastructure without claiming kayak calibration.
- Fits current code posture: Edinburgh is already the single applied review packet and remains `validation_candidate`.

Cons:

- Validation-only; the hulls are Pacific-canoe-like and yaw/side-force oriented.
- Requires careful separation between CC BY dataset rights and all-rights-reserved article text.

### Option B - Permission-First K1 Packet

Choose Tzabiras or Gomes for the first full packet only after rights work: obtain permission or an open data deposit for extracted rows, then review as a K1 `validation_fixture` candidate.

Pros:

- Closer to kayak/surfski hydrodynamics than Edinburgh.
- Tzabiras covers a useful Fn band including the project target range; Gomes includes drag decomposition and load sensitivity.

Cons:

- Rights are currently insufficient for checked-in rows.
- Sprint K1 is still not broad touring/sea-kayak calibration.
- Packet may end in `validation_candidate` or `rejected` until rights are solved.

### Option C - Calibration-Source Search Before Any Fixture Packet

Do not promote or fully packet any current source; instead search for a measured sea-kayak or close surfski dataset with open rights, geometry/load metadata, Fn 0.30-0.50 coverage, and uncertainty.

Pros:

- Highest protection against out-of-envelope calibration.
- Avoids spending fixture effort on data that cannot calibrate the product envelope.

Cons:

- Blocks validation-fixture infrastructure despite having one open measured source ready for a safe validation-only path.
- No known current source satisfies the calibration bar.

### Option D - Recover Class-Relevant Historical Sea-Kayak Evidence

Treat Lazauskas/Winters/Tuck and Sea Kayaker-derived material as a source-recovery and rights-discovery task before any fixture review.

Pros:

- Potentially strongest class fit if original experimental rows and permissions can be recovered.

Cons:

- Current access is either model-derived, all-rights-reserved, or unavailable/redirected.
- Not a measured source packet today.

## Risks And Unknowns

- The first full packet can be misread as promotion. The artifact should name the allowed target state up front: Edinburgh may become `validation_fixture`, never `calibration_fixture`, unless a later decision changes the kayak-envelope rule.
- CC BY covers the DataShare dataset, not necessarily article prose, article tables, figures, or journal layout. The packet should cite DataShare files and checksum-bound extracted rows, not copy article material.
- Extraction needs a reproducible row policy: sheet names, row filters, zero-speed handling, yaw filtering, sign convention for drag/resistance, model IDs, scale basis, water density, and unit normalization.
- Froude range needs a recorded length basis. Edinburgh workbook uses model-scale speeds and has an `Lm` field; full-scale equivalent speed must not be mixed with model velocity.
- Uncertainty remains incomplete for all candidates. NIST summarizes Type A uncertainty as statistical analysis of observations and Type B as other information, with each component represented as standard uncertainty; BIPM JCGM 100:2008 establishes general rules for evaluating and expressing uncertainty. Sources: [NIST uncertainty definitions](https://pml.nist.gov/cuu/Uncertainty/basic.html), [BIPM JCGM 100:2008](https://www.bipm.org/en/doi/10.59161/jcgm100-2008e).
- K1 sources are tempting because they are kayaks, but sprint K1 load/geometry differs from the sea-kayak and surfski design envelope. They are validation candidates unless a future envelope-specific model is defined.
- Model-derived sea-kayak tables are class-relevant but must not calibrate the raw ITTC/Michell model against another prediction method.

## Implementation Gates For The First Packet

1. Bind every downloaded source file to locator, access date, checksum, and license/rights statement.
2. Create a deterministic extraction script or documented parser for the selected source. For Edinburgh, start with `Results vs speed` and zero-yaw rows; preserve original workbook fields and normalized SI fields.
3. Record original units, normalized units, sign conventions, water properties, model length, full-scale conversion fields, and Froude recomputation.
4. Add uncertainty notes before promotion. Numeric uncertainty is preferred; if absent, include a Type B uncertainty note covering instrument/source limitations and extraction precision.
5. For `validation_fixture`, declare accepted uses as parser/report/holdout only and include out-of-envelope warnings.
6. Forbid `calibration_fixture` verdict unless the selected source is kayak-envelope measured data with accepted rights, extraction, uncertainty, validity envelope, fixture ID/version, and fit-scope metadata.
7. Keep all ordinary resistance outputs `uncalibrated_comparative` until a later accepted-fit workflow satisfies RFC 0027 claim gates.

## Recommendation

Select the Edinburgh DataShare source for the first full source-review packet, but only as a validation-fixture candidate. It is the only measured candidate currently combining open reusable rights, source-file availability, CAD availability, explicit file checksums, and enough workbook structure to support reproducible extraction.

Do not select any current source for calibration fixture promotion. Tzabiras and Gomes are better kayak-envelope validation leads, but their row rights/source availability are not ready. Sea Kayaker, Lazauskas/Winters/Tuck, and MDPI sources should remain citation or recovery targets until measured rows and rights are established.

