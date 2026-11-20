# Roadmap

The main open questions are how accurately the evaluators describe a measured
kayak and which hull shapes the search can explore. The [RFC index](rfcs/README.md)
records the individual design decisions. The [user guide](USER_GUIDE.md)
describes the commands available today.

## Evidence still needed

| Area | Available today | What would advance it |
| --- | --- | --- |
| Resistance | The analytical estimate supports raw comparisons. The Edinburgh Pacific-canoe measurements provide a validation fixture with a documented uncertainty caveat. | Calibration needs measured resistance from a kayak or surfski inside the target envelope, rights to use the data, a reproducible extraction, and an accepted fit with residuals and a validity envelope. See [calibration source research](research/CALIBRATION_DATA_FINDINGS_2026-05-16.md) and decisions D006, D013 and D025. |
| Stability | High-angle righting arms on generated closed bodies are opt-in hydrostatic comparisons. The calibration tools can ingest rig measurements and evaluate a fit. | Measure righting arm against heel under known loads, then pass the fixture and fit acceptance gates. Until then the curves carry the `unvalidated_hydrostatic_comparison` label. See the [rig design](research/STRAIN_GAUGED_GZ_RIG_DESIGN_2026-05-16.md) and [stability acceptance criteria](rfcs/0058-stability-calibration-acceptance.md). |
| CFD | The local OpenFOAM-v2512 adapter can run `interFoam` on an explicitly enabled, evidence-bound package. Open hull/deck STLs are inspection surfaces. Solver readiness requires matching mesh diagnostics, artifact hashes, and the solver profile. | A successful run yields `raw_unvalidated` output. A validated physical prediction still requires measured comparison and an accepted calibration. See [mesh evidence binding](rfcs/0045-ordinary-package-solver-readiness-promotion.md) and [solver opt-in](rfcs/0046-non-env-gated-openfoam-succeeded-path.md). |

The numerical study records convergence behavior, estimates numerical
uncertainty and supports interval-aware frontier comparisons. Its results
apply to the measured methods and grids. Physical calibration requires the
measurements above. See the [quadrature study](research/rfc0077/README.md).

## Hull geometry and search

The search supports parameter sweeps, NSGA-II and EHVI. Objective admission
depends on the metric and its claim state. Raw resistance requires explicit
exploratory use. Per-load righting arms can constrain a search, while the
form metrics describe hull geometry. Advisory badges and class checks do
not establish seaworthiness.

The distribution model supports six section families and optional topsides.
RFC 0089 added round-section fullness, tumblehome, sheer-plan and deck-crown
controls, rounded shoulders, and searchable longitudinal ramps. Sweeps can
report foot room, shaft clearance, section knuckles, plan-outline hollow,
overall beam and righting arms at several loads. Scalar search controls for
the waterline outline and draft, and searches that hold displacement fixed,
remain open. The current foot-room measure uses the outer hull and deck
surfaces. Knee room, shell thickness and a modeled seat position remain
outside it. See [RFC 0089](rfcs/0089-section-fullness-and-form-metrics.md).

## Interfaces and deployment

The Trame workspace is the primary design interface. The desktop interface
supports local editing, 3D preview and STL export. Full desktop parity and
the deferred desktop visual redesign have no scheduled release.

The public hosted demo is deferred under D023. Reopening it requires a
service owner, budget cap, deployment revision, hosted smoke check,
persistence limits and a cleanup procedure. The local web application and
Docker entry point are documented in [web verification](WEB_VERIFICATION.md).

## Durable results

Sweep and search runs retain candidate outcomes, execution scope and
comparison eligibility on verified resume. The artifact store indexes
content and reconstructs run manifests from recorded evidence. Local Linux
job ownership protects process recovery with leases and per-attempt state.
Distributed writers, cross-host execution and power-loss recovery guarantees
are separate work. See [verified candidate reuse](rfcs/0076-verified-candidate-reuse.md)
and [subprocess ownership](rfcs/0075-subprocess-attempt-ownership.md).
