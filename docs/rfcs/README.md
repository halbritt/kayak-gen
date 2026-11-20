# RFCs

Each RFC records a design decision, its acceptance criteria, and the scope of
the work. The status in each document describes how much landed. For available
commands and examples, see the [user guide](../USER_GUIDE.md). Outstanding work
and its evidence requirements are in the [roadmap](../ROADMAP.md).

## Index

| RFC | Status | Topic |
| --- | --- | --- |
| [0001](0001-template.md) | template | RFC template — copy for new RFCs |
| [0002](0002-gui-usability.md) | landed | GUI usability improvements |
| [0003](0003-layout-and-station-view.md) | landed | Window layout and station-view slider |
| [0004](0004-plumb-bow.md) | superseded by RFC 0028 | Plumb bow support (`bow_rake` parameter) — exact plumb-stem closure semantics owned by 0028; cleanup by RFC 0064 |
| [0005](0005-cfd-resistance.md) | landed raw-filter | Resistance estimation (Michell + ITTC) |
| [0006](0006-design-constraints.md) | landed | Hull design constraints — canonical parameter space + 4 class presets + beam_wl validation; richer surfacing absorbed by RFC 0031 / 0048 / 0061; cleanup by RFC 0064 |
| [0007](0007-architectural-revisit.md) | landed | Architectural revisit — extract `kayakgen` package before more parameters land |
| [0008](0008-web-frontend.md) | superseded by RFC 0032 | Portable web frontend via Trame — web-analysis safe-slice landed; hosted demo deferred per D023; cleanup by RFC 0064 |
| [0009](0009-sweep-run-records.md) | superseded by RFC 0057 | Sweep and candidate run records — deterministic runner + records landed; pending lifecycle + generative jobs owned by 0057; cleanup by RFC 0064 |
| [0010](0010-cfd-ready-mesh-contract.md) | landed package/profile | CFD-ready mesh contract |
| [0011](0011-hydrostatic-stability-load-cases.md) | landed equilibrium-sinkage + trim-slice | Hydrostatic stability and load cases |
| [0012](0012-resistance-model-calibration.md) | superseded by RFC 0054 + D006 | Resistance model calibration — tooling complete (`kayakgen calibration`); kayak-envelope measured-resistance source tracked by D006; cleanup by RFC 0064 |
| [0013](0013-pareto-frontier-comparison-ui.md) | landed report/web-slice | Pareto frontier and candidate comparison UI |
| [0014](0014-generalized-trim-and-gz-stability.md) | superseded by RFC 0043 | Generalized trim and high-angle GZ stability — trim equilibrium landed; high-angle GZ owned by 0043; cleanup by RFC 0064 |
| [0015](0015-cfd-solver-dispatch-and-jobs.md) | superseded by RFC 0041 | CFD solver dispatch and job artifacts — local dispatch landed; real OpenFOAM in 0041; cleanup by RFC 0064 |
| [0016](0016-closed-volume-geometry.md) | landed synthetic-contract safe-slice | Closed-volume geometry contract |
| [0017](0017-first-real-cfd-adapter.md) | superseded by RFC 0041 | First real CFD adapter — successor 0041 landed; cleanup by RFC 0064 |
| [0018](0018-web-cfd-job-routes.md) | landed | Web CFD job routes — local dispatch + browser CFD panel; hosted variant deferred per D023; cleanup by RFC 0064 |
| [0019](0019-resistance-calibration-fixtures.md) | superseded by RFC 0042 | Resistance calibration fixtures — successor 0042 landed; cleanup by RFC 0064 |
| [0020](0020-high-angle-gz-secondary-stability.md) | superseded by RFC 0024 + RFC 0043 | High-angle GZ and secondary stability — successors landed; cleanup by RFC 0064 |
| [0021](0021-closed-volume-self-intersection-diagnostics.md) | landed synthetic-diagnostic | Closed-volume self-intersection diagnostics |
| [0022](0022-generated-closed-body-construction.md) | landed generated-body safe-slice | Generated hull-plus-deck closed-body construction |
| [0023](0023-watertight-volume-mesh-handoff.md) | landed fixture-handoff | Watertight volume mesh and `cfd_ready` handoff |
| [0024](0024-high-angle-gz-generated-body-handoff.md) | landed structured-unavailable handoff | High-angle GZ generated-body handoff |
| [0025](0025-cfd-calibration-claim-gates.md) | landed claim-gates | CFD and calibration claim gates |
| [0026](0026-first-real-cfd-fixture-adapter.md) | landed fixture-local-command | First real CFD fixture adapter |
| [0027](0027-resistance-calibration-acceptance.md) | landed acceptance-gates | Resistance calibration acceptance |
| [0028](0028-plumb-stem-closure-semantics.md) | landed | Plumb-stem closure semantics — independent stern_rake + cap construction + plumb-aware diagnostics; manufacturing thickness out of scope; cleanup by RFC 0064 |
| [0029](0029-design-constraint-surfacing.md) | superseded by RFC 0031 | Design constraint surfacing and validity metadata — implementation landed via 0031; cleanup by RFC 0064 |
| [0030](0030-web-hosted-browser-acceptance.md) | deferred per D023 | Web hosted and browser acceptance — public hosted demo deferred indefinitely; cleanup by RFC 0064 |
| [0031](0031-design-constraint-surfacing-revision.md) | landed validity-metadata slice | Design constraint surfacing revision |
| [0032](0032-web-hosted-browser-acceptance-revision.md) | landed local-browser-docs | Web hosted browser acceptance revision |
| [0033](0033-workspace-ui-rework.md) | superseded by RFC 0034 + RFC 0035 | Workspace UI rework — three-region web shell, semantic theme, claim/readiness/status chips; follow-ups by 0034/0035/0057; cleanup by RFC 0064 |
| [0034](0034-workspace-ui-follow-up.md) | landed safe-slice | Workspace UI follow-up — dynamic presets, review-card wiring, export menu, and forbidden-copy tests |
| [0035](0035-ui-follow-up-cleanup.md) | landed safe-slice | UI follow-up cleanup — validity semantics, export/state hygiene, slider-label maintenance |
| [0036](0036-trame-seed-listener-proof.md) | landed retain-with-trame-state-proof | Trame seed listener proof |
| [0037](0037-export-row-schema-consolidation.md) | landed subtitle-only-schema | Export row schema consolidation |
| [0038](0038-export-menu-disabled-copy-polish.md) | landed disabled-copy-polish | Export menu disabled copy polish |
| [0039](0039-web-snapshot-schema-unification.md) | landed shared-schema-unification | Web snapshot schema unification |
| [0040](0040-closed-volume-solver-readiness-roadmap.md) | superseded by RFC 0041 + RFC 0045 | Closed-volume solver readiness roadmap — generated-body hardening + snappyHexMesh evidence (opt-in) landed; real solver + ordinary-package promotion in 0041 / 0045; cleanup by RFC 0064 |
| [0041](0041-real-cfd-adapter-successor.md) | landed real openfoam-v2512-interfoam-local succeeded path (opt-in env-gated); claim_state stays raw_unvalidated | Real CFD adapter successor |
| [0042](0042-resistance-calibration-fixture-successor.md) | superseded by RFC 0054 + D006 | Resistance calibration fixture successor — source-review + Edinburgh acquisition + D025 promotion landed; kayak-envelope source tracked by D006; cleanup by RFC 0064 |
| [0043](0043-high-angle-gz-successor.md) | landed stages 1-3 + stage-4 claim-integrity pipeline | High-angle GZ successor — stages 1-3 + the stage-4 accepted-fit registry (`kayakgen/eval/stability/registry.py`, 13-gate provenance chain) that flips the analytical high-angle GZ label; first promotion of a real measured fixture still gated on D007/D014 rig data. Built via workflow 0043. |
| [0044](0044-active-hull-design-search.md) | landed v1 NSGA-II + kayakgen search CLI (additive opt-in; defaults unchanged) | Active hull-design search |
| [0045](0045-ordinary-package-solver-readiness-promotion.md) | landed kayakgen mesh-evidence + mesh-package --bind-evidence (hash-bound; defaults unchanged) | Ordinary-package solver-readiness promotion |
| [0046](0046-non-env-gated-openfoam-succeeded-path.md) | landed three-mechanism opt-in + audit trail; defaults unchanged | Non-env-gated OpenFOAM succeeded path |
| [0047](0047-active-search-v2-successor-algorithms.md) | landed v2 EHVI over vendored Cholesky GP (1-3 objectives; additive opt-in; defaults unchanged) | Active search v2 — EHVI/GP Bayesian successor |
| [0048](0048-geometry-v2-distribution-model.md) | landed v1 distribution_v2 + 6 cross-section families + hydrostatic cross-check + migrate-geometry CLI | Geometry V2 — explicit distribution model + canonical closed-body loft |
| [0049](0049-artifact-store-and-identity.md) | landed Hull.{record,design}_hash + FilesystemArtifactStore + SqliteIndex + kayakgen runs CLI | Artifact store + identity normalization |
| [0050](0050-target-displacement-and-trim-workflows.md) | landed kayakgen target-draft + target-trim subcommands | Target-displacement and target-trim design workflows |
| [0051](0051-builder-oriented-exports.md) | landed kayakgen build-export + 7 artifact writers under [builder] extras | Builder-oriented exports (DXF/SVG/offsets) |
| [0052](0052-sensitivity-and-uncertainty-views.md) | landed kayakgen sensitivity + ConvergenceFlag + pairwise-noise advisory | Sensitivity and uncertainty views |
| [0053](0053-turning-and-edged-waterline-metrics.md) | landed TurningMetrics + opt-in --turning flag + sweep evaluator | Turning and edged-waterline metrics |
| [0054](0054-calibration-campaign-tooling.md) | landed kayakgen calibration sub-app + tank/inclining/AcceptedFitRecord schemas + accepted-fit gate wiring | Calibration-campaign tooling |
| [0055](0055-design-report-export.md) | landed kayakgen design-report + jinja2 template + forbidden-copy scan + optional [report] PDF extras | Single-file design report export |
| [0056](0056-strain-gauged-gz-rig.md) | landed schemas + stage-4 acceptance pipeline | Strain-gauged moment-arm rig for measured high-angle GZ — `MeasuredStabilityFixture` schema + validators (`kayakgen/eval/stability/measured_fixture.py`) plus the RFC 0043 stage-4 registry gate-chain that consumes them; first promotion of a real measured fixture still gated on D007/D014 rig data. |
| [0057](0057-generative-search-jobs-and-web-workspace.md) | landed | Generative-search jobs and web workspace — records, in-process + subprocess managers, /api/generative-jobs/* routes, Trame Generate panel with form-builder + 2D Pareto scatter + auto-poll + fork-with-seed + log redaction (stages 1-4) |
| [0058](0058-stability-calibration-acceptance.md) | landed | Stability calibration acceptance and CFD-in-loop graduation — stages 1-3 landed stability fit schemas, `resolve_analytical_claim_label`, `cfd_in_loop_evaluator_status`, schema-only `kayakgen stability` commands, and Generate-panel read-model wiring; Stage 4 first promotion remains gated on physical rig data |
| 0059 | retired | Periodic audit workflow (decision D041). |
| [0060](0060-web-generate-panel-form-labels-and-tooltips.md) | landed | Shared labels and tooltips for web Generate form parameters and objectives. |
| [0061](0061-desktop-sliders-on-hull-parameter-metadata.md) | landed | Desktop slider labels use the hull metadata registry. Slider ranges and view-only parameters have their own catalogs. |
| [0062](0062-hydrostatics-row-metadata-registry.md) | landed | Hydrostatics row labels and units come from a shared registry. |
| [0063](0063-nested-key-search-variables.md) | landed | Nested-key search variables — dotted-path syntax (`distribution_v2.cross_section_family`, `distribution_v2.deadrise_deg`) for `SearchSpec.search_space` keys so the active-search runner can sweep nested fields. Today's `_hull_from_genome` flat-overlays genome onto base_hull, so categorical / nested distribution_v2 knobs are unreachable from NSGA-II / EHVI. Motivated by the 2026-05-30 Epic 18X Sport exercise that had to fall back to hand-authored hull JSONs + `kayakgen evaluate` per cross-section family. Landed via workflow 0040. |
| [0064](0064-outstanding-rfc-cleanup.md) | landed | Outstanding-RFC cleanup — disposition table for the 14 non-cleanly-landed RFCs as of 2026-05-31, flipping each to `landed` / `superseded by …` / `deferred per D023` to match the actual codebase state. Stability-rig pair (RFC 0043 stage 4, RFC 0056 fixture promotion) remains deferred per operator's standing decision. Doc-only; no code changes. |
| [0065](0065-ui-polish-redesign.md) | proposed | UI polish redesign — a coherent visual-system pass over the landed workspace: extend `kayakgen/ui/theme.py` with spacing/density/radius/elevation/focus-ring/state tokens, one information hierarchy across the three-region shell + Generate panel, uniform control and empty/loading/error states, and accessible focus/keyboard behaviour. Sequenced into safe slices (theme tokens → shell layout → per-panel states → Playwright/Chromium committed-baseline visual-regression harness + a11y/Lighthouse gates). Preserves every claim/readiness/status chip and the RFC 0032 web-analysis boundary; adds no analysis capability or claim-state literal. Desktop polish deferred (Slice 5, operator-gated per D009/D021). Docs-only; authorises no behaviour change. Adds DECISION_LOG row D047 (committed screenshot baselines). |
| [0066](0066-artifact-occurrence-bindings.md) | landed occurrence bindings + transactional v1 migration | Separate content identity from current run/path bindings |
| [0067](0067-run-manifest-recovery.md) | landed run manifests + honest index reconstruction | Durable run instance identity, expected hashes and explicit legacy recovery limits |
| [0068](0068-versioned-v2-design-identity.md) | landed versioned v2 physical identity | Complete distribution identity with an explicit scheme and unchanged legacy evidence |
| [0069](0069-geometry-export-capabilities.md) | landed shared geometry exports + staged builder bundles | Common mesh/section capabilities for lofted and v2 exports; complete-bundle publication |
| [0070](0070-cfd-attempt-replay.md) | landed idempotent preparation + explicit retained attempts | Preserve CFD request replay and execution history |
| [0071](0071-streamed-command-deadline.md) | landed streamed deadlines + bounded capture | Bound staged command lifetime while consuming output |
| [0072](0072-numerical-evidence-admission.md) | landed conservative numerical status and admission | Numerical evidence and resistance objective admission |
| [0073](0073-evaluation-context.md) | landed shared context and selected-result reporting | Immutable evaluation context and selected-result reports |
| [0074](0074-fixed-body-operating-pose.md) | landed fixed-body immersion + v2 load equilibrium | Rigid operating pose, common wetted geometry and actual-body mass/trim brackets |
| [0075](0075-subprocess-attempt-ownership.md) | landed local subprocess ownership and fenced state publication | Runner-held lease, attempt/process identity and proven-dead successor admission |
| [0076](0076-verified-candidate-reuse.md) | landed verified candidate reuse + explicit sweep scope | Preserve outcomes, verify cached evidence and report requested versus processed work |
| [0077](0077-resistance-quadrature-policy.md) | landed exact linear depth + explicit interval screening policy | Correct depth quadrature and measured resistance screening uncertainty |
| [0078](0078-installed-runtime-templates.md) | landed installed runtime templates | Installed runtime templates |
| [0079](0079-completion-admission.md) | landed terminal audit and declared receipt admission | Guard completion actions with terminal audits and source-bound evidence |
| [0080](0080-installed-runtime-lifecycle.md) | landed installed runtime lifecycle acceptance | Installed idle controls and read-only persistent service lifetime |
| [0081](0081-semantic-preflight.md) | landed selected semantic preflight | Source-bound shared-input contract checks before full release gates |
| [0082](0082-verified-gate-renderers.md) | landed verified full/fast renderer admission | Actual Mesa software evidence and coordinated NVIDIA hardware gates |
| [0083](0083-maintained-release-verification.md) | landed maintained installed release verification | Source-bound wheel staging and actual installed workflows |
| [0084](0084-source-bound-full-gate.md) | landed full pytest then Ruff + persistent receipts | Fixed full-check sequence and actual candidate source identity |
| [0086](0086-citation-closure.md) | landed phase/packet-bound citation closure | Bind doctrine citations to the phase and packet that served them |
| [0087](0087-ledger-current-acceptance.md) | landed receipt-applicability ledger view and proposed finalization | Current ledger acceptance versus historical pending flags |
| [0088](0088-v2-topsides.md) | landed optional topsides record | Above-waterline hull sides and flare for `distribution_v2` hulls |
| [0089](0089-section-fullness-and-form-metrics.md) | landed stages 1 to 8 | Fuller `round` sections, class ratio and catch-zone beam, righting arms at several loads; tumblehome, fair sheer plan, deck crown, search admission; foot room; section knuckles; rounded shoulder; upright section sides; longitudinal ramp; plan-outline hollow |

## Template

Start from the [RFC template](0001-template.md). Record accepted decisions in
the [decision log](../DECISION_LOG.md) and update the [specification](../SPEC.md)
when the implementation contract changes.
