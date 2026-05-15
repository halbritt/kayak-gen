# Calibration data acquisition findings — 2026-05-16

This memo records the result of two parallel research investigations
into publicly-downloadable datasets that could close
`docs/DECISION_LOG.md` open gates:

- **D006** (calibrated resistance — needs an in-envelope measured kayak
  source + accepted-fit workflow)
- **D007 / D014** (real high-angle GZ — needs measured GZ-vs-heel curves
  for kayak-envelope hulls)

The bottom line is the same for both: **as of 2026-05-16, no public
in-envelope, per-row, machine-readable, measured dataset exists that
satisfies kayakgen's calibration_fixture validators** (decision D013,
`kayakgen/eval/calibration/__init__.py:_validate_calibration_fixture_metadata`).
The kayak literature is paper-published, not data-published, and the
existing "kayak stability curve" sources are computed-not-measured
(structurally identical to kayakgen's own RFC 0043 v1 model).

## Calibrated-resistance data (D006)

Channels searched: Zenodo, Figshare, OSF, Edinburgh DataShare, Mendeley,
Heriot-Watt, Newcastle, Aalborg, FEUP Porto, NTUA, MIT DeCoDe, Wolfson Unit,
ITTC, SNAME/MARIN/SSPA/NSWC public catalogues, Olympic and sport-science
repositories (AIS / EIS / INSEP / Magglingen / ICF technical reports),
manufacturer published data (Lazauskas / Cyberiad / Toxward), and
PhD/MSc theses on sprint kayak / sea kayak / surfski resistance.

Triaged ranking against D006 + D013 + the validators:

- **A — immediately downloadable + redistributable + in-envelope:** none.
- **B — in-envelope, rights need clearing:**
  - **Pendergast / Gomes et al.**, *Sports Biomechanics* 17(4),
    Nelo Quattro K1 M/ML/L, 21-89 N at 2.8-5.6 m/s, SD reported per row,
    Taylor & Francis paywall. Author outreach required.
    Geometry is Nelo proprietary.
    <https://doi.org/10.1080/14763141.2017.1357748>
  - **Tzabiras / NTUA LSMH** Olympic K1 towing-tank study, 0.25-5.15 m/s,
    drag in figures only (not tabulated rows), no deposit, on-request only.
    <https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/>
- **C — in-envelope, geometry proprietary, partial uncertainty:**
  - **Aalborg PhD** on sprint kayaking, Nelo Quattro M/ML/L hulls, PDF-only
    tabulated drag. Open access PDF vendored under
    `docs/research/aalborg_kayak_phd.pdf` for reference (SHA-256
    `e7ecbf17de9c861dfac281de2025ca3e1b75d8385edbf1a5111f88c55419e8c5`,
    3.59 MB). Nelo geometry is proprietary — cannot become a
    `calibration_fixture`; at most a `validation_fixture` if rows were
    extracted with author cooperation.
    <https://vbn.aau.dk/ws/files/549494319/PHD_KKK_E_pdf.pdf>
  - **FEUP Porto** kayak hull design thesis. Could not be reached during
    download (repository redirect failed); refer to original repository
    if needed: <https://repositorio-aberto.up.pt/handle/10216/78441>.
- **D — out of envelope, computed-only, or not findable:**
  - **Edinburgh DataShare** 10.7488/ds/3785 — Pacific outrigger canoes.
    Already vendored (`tests/fixtures/calibration/edinburgh/`) and
    envelope-blocked per D013.
  - **Lazauskas (Cyberiad)** sea kayak drag — Michlet thin-ship
    *predictions*, not measured.
  - **Baker (Newcastle)** surf-ski length optimization — thin-ship
    theory + ITTC '57 friction, not measured.
  - **SHIP-D / ShipGen (MIT DeCoDe)** — 30,000 hulls, parametric +
    potential-flow predictions; not measured.
    <https://github.com/noahbagz/ShipD>
  - **Mendeley Sailboat Hull Resistance Dataset (Delft / Il Moro / USS)**,
    1018 measured rows of dimensionless resistance, well-licensed
    (CC BY 4.0).
    *Out-of-envelope* (sailboat L/B regime, not kayak). Vendored as a
    schema reference at
    `tests/fixtures/research_references/sailboat_delft/` —
    SHA-256:
    - `sailboat_resistance_v01.csv` ⇒
      `369a2dc305032526e16708dd91dd143dcbdbdae63fde9ae6c9344989a01e7a01`
    - `sailboat_metadata_v01.csv` ⇒
      `d6bdb389fb90d97cce681758987169938e62d607198febc40bbf13c352ddbb9c`
    This dataset can **never** be promoted to a kayak
    `calibration_fixture` per D013; it is preserved only as a reference
    for the per-row schema (Rt·10³/Δ, Rn, Fn, Cp, Cm, Cb, Cw,
    Lwl/Bwl, Bwl/Tc, Lwl/Tc, Lwl/Vol^(1/3), LCB/Lwl, LCF/Lwl,
    LCB/LCF, Sc/Vol^(2/3), Aw/Vol^(2/3), Sc/Aw, Sc/Ax, Ax/Aw) that
    future kayak ingest packets should learn from.
    <https://data.mendeley.com/datasets/gw23dgzn6h/1>
  - **AMECRC**, **Wolfson Unit**, **ITTC**, **MARIN/SSPA/NSWC Carderock**,
    **Heriot-Watt** — no kayak-class public datasets surfaced.

### Realistic next step for D006

Direct author outreach to two groups: **Pendergast / Gomes (Buffalo +
Coimbra / Porto / Sydney)** and **Tzabiras / Diafas (NTUA LSMH)**,
requesting CC BY deposit of (a) raw per-run rows with uncertainty and
(b) hull offsets or a 3D scan. Until such outreach succeeds, raw
resistance stays `uncalibrated_comparative`. Edinburgh stays
`validation_candidate` (ready for `validation_fixture` promotion in code,
still calibration-blocked by envelope).

## Measured high-angle GZ data (D007 / D014)

Channels searched: ISO 12217-3, ASTM F3052, USCG / RYA / BCU certification
frameworks, Wolfson Unit small-craft reports, Guillemot Kayaks performance
graphs, Sea Kayaker magazine reviews (KAPER + hydrostatic stability
spreadsheets, Broze / Winters convention), Olympic / sprint biomechanics
literature (e-Kayak DAQ, Aalborg, Nakashima dynamic model), academic
repositories (Plymouth, Newcastle, MIT, Tokai, ENSTA Bretagne,
Strathclyde), and kayak manufacturer published data.

Triaged ranking:

- **A — measured, in-envelope, redistributable:** none.
- **B — measured, in-envelope, rights need clearing:** none.
- **C — proxy / partial / wrong-axis:**
  - **e-Kayak DAQ** (MDPI Sensors 2020) — dynamic on-water roll/pitch/yaw
    with small heel excursions, not static high-angle GZ. Open access
    paper. Could not be downloaded cleanly (MDPI cookie-gate); read at
    <https://pmc.ncbi.nlm.nih.gov/articles/PMC7014492/>.
  - **Aalborg PhD** dynamic measurements — same caveat.
- **D — computed only or out of scope:**
  - **Guillemot Kayaks performance graphs** — computed hydrostatic
    integration, idealized sealed body + rigid seated paddler CG 10"
    above seat. Not redistributable graphics.
    <https://guillemot-kayaks.com/performance-graphs-are-back>
  - **Sea Kayaker magazine reviews** (1984-2014, archived) — computed
    via KAPER + Broze / Winters stability spreadsheet, same idealizations.
    Magazine ceased; back-issue images not redistributable.
  - **ISO 12217-3** small craft stability (< 6 m): **kayaks and canoes
    are explicitly excluded from scope**; the standard does not require
    a measured GZ curve for kayaks.
    <https://www.iso.org/standard/79074.html>
  - **ASTM F3052** small boat air-inclining: targets power/sail small
    craft, does not address kayaks; no published kayak datasets cite
    this guide. <https://store.astm.org/f3052-14r20e01.html>
  - **Wolfson Unit (Univ. Southampton)** small-craft testing —
    client-confidential, no public kayak GZ reports surfaced.
  - **USCG / RYA / British Canoeing** — no measured GZ datasets; their
    standards address paddler skill or inspected-vessel categories,
    not kayak GZ.
  - **Manufacturers (P&H, Valley, Epic, Stellar, Nelo, Vajda)** — no
    published curves; any internal measurements are proprietary.

### Honest null statement

The only "kayak GZ curves" widely cited in the open literature
(Guillemot, Sea Kayaker, KayakFoundry, BearboatSP, FloatSoft) are
computational pipelines structurally similar to kayakgen's own RFC 0043
v1 model. Validating kayakgen against any of them would be
comparison-with-peers, not measured validation. To upgrade RFC 0043's
`result_semantics="unvalidated_hydrostatic_comparison"` label,
kayakgen needs **physically measured** GZ-vs-heel data on real
in-envelope hulls, and that data does not exist publicly today.

### Realistic next step for D007 / D014

Three measurement protocols in order of cost (also from the research
report):

1. **Pool / tank inclining-by-known-weight** on a real kayak. Calibrated
   weights, digital inclinometer, sealed-deck + flooded-cockpit
   protocols. $500-2 000 if a pool/tank is donated; 2-4 weeks lead
   time; ~1-2 deg heel uncertainty, ~3-5% GZ; good to ~60-70 deg before
   ingress/instability dominates.
2. **Force-arm rig with a single-axis or six-axis load cell** in a
   towing tank. $5 000-15 000 plus tank time ($500-2 000/day); 1-3
   months lead time; 0.5 deg, ~1-2% GZ; clean to 90 deg, with an
   inverted rig for 90-180 deg.
3. **University partnership** with a small-craft lab (Plymouth,
   Newcastle, Strathclyde, Edinburgh, Wolfson/Southampton, or the USNA
   EN400 student inclining-experiment lab). Single in-envelope hull,
   CC BY 4.0 deposit. ~$3-8k lab time plus a thesis cycle (3-6 months).

Any of these would unblock D007 / D014's "measured" gate. None can be
satisfied from public datasets.

## What this memo does *not* change

- No new fixture is promoted. Edinburgh remains the only
  `is_validation_fixture_ready() == True` packet, and only because of
  D018's earlier acquisition; it is still calibration-blocked.
- No claim state changes. Raw resistance stays
  `uncalibrated_comparative`. High-angle GZ stays
  `unvalidated_hydrostatic_comparison`.
- No new RFC dependency is implied. RFC 0042 and RFC 0043 stay at their
  current partial-landed states; this memo is research provenance
  attached to those gates, not new design scope.
