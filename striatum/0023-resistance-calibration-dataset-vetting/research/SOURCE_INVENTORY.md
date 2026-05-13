# Source inventory - resistance calibration dataset vetting

author: operator [self-declared: operator-source-inventory]
run: run_6ca2095f019345e199943d5f46f0676f
job: source_inventory
date: 2026-05-13

## Gate recommendation

Do not promote any reviewed source directly to `calibrated_kayak_v1`.

The University of Edinburgh DataShare record for "Hydrodynamics of Three
Slender Models Resembling Pacific Canoe Hulls" is the strongest newly found
dataset because it is a real dataset, not only an article; it includes raw
towing-tank force data plus CAD models; and the repository declares CC BY 4.0
rights. It should proceed to review as a validation-fixture candidate, not as a
general kayak calibration fixture, because its hulls are Pacific-canoe-like
multi-hull/catamaran forms tested at fixed sink and trim, not touring or sea
kayaks in the project design envelope.

The older candidates keep their workflow-0012 classifications:
Sea Kayaker/KAPER-derived resistance tables are broad but model-derived and
rights-unclear; Gomes and Tzabiras K1 studies are measured kayak references but
publisher/article rights and sprint-K1 bias block checked-in general
calibration fixtures; MDPI/open physics articles are useful context but not
primary calibration datasets.

## Candidate table

| Candidate | Data type | Coverage | Access and rights | Strength | Risk | Gate classification |
|---|---|---|---|---|---|---|
| University of Edinburgh DataShare, "Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls" | Dataset with spreadsheet, raw towing-tank forces, force coefficients, plots, and IGES CAD | Three slender Pacific-canoe-like hull models; fixed sink and trim; speed/yaw data | Dataset page declares CC BY 4.0; DOI `10.7488/ds/3785`; spreadsheet and CAD downloadable | Measured forces plus geometry, reusable license, clear provenance, current 2025 peer-reviewed article context | Not a kayak/sea-kayak class; multi-hull sailing-canoe motivation; fixed sink/trim; yaw/side-force focus; model scale and hull-section bias | Validation candidate only; do not calibrate general kayak resistance |
| Flay, Irwin, Viola 2025 Journal of Sailing Technology article | Peer-reviewed article tied to the Edinburgh dataset | Same three canoe-like models; towing-tank tests at fixed sink and trim | Article metadata says SNAME copyright; dataset remains separate CC BY 4.0 | Useful domain interpretation and confirms the experiment's purpose | Article text is not the fixture license; article emphasizes side-force/leeway and Pacific canoe evolution | Citation/context for the dataset |
| Sea Kayaker / kanu.de resistance compilation | Compiled resistance tables attributed to Sea Kayaker and Broze/Taylor/KAPER calculations | Broad sea-kayak hull list at typical touring speeds | Public PDF, but redistribution and original compilation rights are unclear | Best class match and broadest hull coverage | Model-derived values; not primary measured data; model-to-model calibration risk | Citation-only, no checked-in extracted tables |
| Individual Sea Kayaker review PDFs | Review pages with dimensions and resistance tables | Sea kayak / touring kayak specific | Vendor/magazine mirrors; copyright not open | Potentially useful dimensions and class context | Copyright and extracted-table rights unclear; values often KAPER/Broze model outputs | Citation-only |
| Gomes et al. 2018, Sports Biomechanics | Experimental total passive drag plus theoretical drag decomposition | Single sprint K1 kayak, simulated paddler weights 65/75/85 kg, up to 5.56 m/s | Publisher copyright Taylor & Francis/Informa; SUNY metadata confirms article details | Direct kayak drag data with load sensitivity | Sprint K1 only; fixture redistribution not established | Validation candidate if permission/data are obtained; no checked-in fixture now |
| Tzabiras et al. K1 tow-tank study | Towing-tank total resistance, trim, CG-rise, numerical comparisons | Olympic K1, displacement 86.8 kg, 0.25-5.15 m/s | Article available on The Sport Journal; no explicit open fixture license found | Measured K1 data over useful speed band | Sprint K1 only; data extraction and rights remain unclear | Validation candidate by citation only |
| MDPI "On the Physics of Kayaking" | Open-access physics/modeling article | General kayak physics context | Article is open access, but its data availability states no additional data | Reusable equations/context with attribution | Not a primary resistance dataset | Citation-only |

## Evidence notes

### University of Edinburgh DataShare dataset

- DataShare identifies the record as a dataset, available 2022-12-01, created
  by Flay R., Irwin G.J., and Viola I.M., published by the University of
  Edinburgh, with citation `https://doi.org/10.7488/ds/3785`.
- The DataShare description says the dataset includes raw hydrodynamic forces
  measured in a towing tank for three slender hulls, computed force
  coefficients/plots, and CAD models.
- The full item record lists the rights as Creative Commons Attribution 4.0
  International Public License, and the license text grants reuse/share/adapt
  rights subject to attribution.
- Local inspection of the downloaded workbook found sheets named `Averaged
  Data`, `Results vs speed`, `Results vs yaw`, `Prohaska`, and
  `Froude Scaling`. The visible headers include model identifiers, yaw, speed,
  measured heave/pitch, total drag, resistance, side force, coefficients,
  model length, wetted surface, density, Reynolds number, Froude number, and
  full-scale equivalent velocity. This is strong enough for later validation
  fixture design.
- The linked 2025 Journal of Sailing Technology article describes towing-tank
  tests on three slender models at fixed sink and trim. Its abstract focuses on
  ancient Pacific multi-hull vessels, side-force generation, leeway/yaw, and
  rounded versus Vee sections.

### Older workflow-0012 candidates

- SUNY Research Connect metadata for Gomes et al. says total passive drag was
  based on experimental data from a single-seat kayak and tested simulated
  weights of 65, 75, and 85 kg. The same metadata records publisher copyright
  by Taylor & Francis/Informa.
- Workflow 0012 already classified the Sea Kayaker/KAPER-derived tables as
  broad sea-kayak context but not primary open measurements.
- Workflow 0012 already classified Gomes and Tzabiras as K1 validation
  candidates rather than general sea-kayak calibration anchors.

## Calibration implication

The Edinburgh dataset improves the project’s validation-source landscape, but
does not solve calibrated sea-kayak prediction. A defensible calibration source
for this project still needs measured total resistance for kayak/touring
classes, known displacement/load cases, speed/Froude coverage matching the PRD
design space, hull geometry or offsets that can be represented by `kayakgen`,
and fixture rights that allow checked-in derived data.

The safe next implementation, if reviews agree, is to add the Edinburgh dataset
to `default_resistance_source_registry()` as a `validation_candidate` with
CC BY 4.0 rights and warnings such as `pacific_canoe_not_sea_kayak`,
`fixed_sink_trim`, and `validation_not_calibration`. Do not add calibrated
metadata to current resistance curves, and do not add extracted numeric
fixtures until a dedicated fixture schema records attribution, extraction
method, scale, model geometry, and row-level provenance.

## Review questions

- Should the Edinburgh dataset be listed only in the source registry, or should
  a future RFC define an external-download validation fixture format?
- Is a Pacific-canoe-like slender-hull dataset close enough to guard Michell
  wave/resistance trends, or should it be kept as source context until a
  touring/sea-kayak measured dataset appears?
- If a validation fixture is later accepted, should it validate raw component
  trends only, or should it be used to bound a separate `calibrated_canoe_v1`
  profile that is explicitly not the kayak profile?

## Source links

- University of Edinburgh DataShare dataset:
  https://datashare.ed.ac.uk/handle/10283/4772
- DataShare license text:
  https://datashare.ed.ac.uk/bitstream/handle/10283/4772/license_text?isAllowed=y&sequence=3
- University of Edinburgh Research Explorer article metadata:
  https://www.research.ed.ac.uk/en/publications/hydrodynamics-of-three-slender-models-resembling-pacific-canoe-hu/
- SUNY Research Connect metadata for Gomes et al.:
  https://researchconnect.suny.edu/en/publications/effect-of-wetted-surface-area-on-friction-pressure-wave-and-total/
