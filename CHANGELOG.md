# Changelog

Release notes for the kayakgen CLI, desktop and web frontends, and Python package.

## Unreleased

### Added

- `mise.toml` test tasks: `test` (focused pytest, selector required), `lint`,
  `test:fast` and `test:full` (the existing gate scripts, run through the
  host's `host:exec` for a deadline and child cleanup). `scripts/test-python.sh`
  finds the interpreter, including from a linked worktree.
- RFC 0089 stage 8: `FormMetrics` adds `plan_hollow_max_deg` and
  `plan_hollow_x_m`, summing degrees the starboard overall plan outline turns
  outboard from bow to stern within `knuckle_span_xi` (`0` for a convex plan
  silhouette). Sweeps and active searches gain `form.plan_hollow_max_deg` and
  `form.max_overall_beam_m` (`explicit_exploratory`, direction `min`).
- RFC 0089 stage 7: `LongitudinalDistribution` gains `RampDistribution`
  (`kind: "ramp"`, scalar `forward`, `aft`, `forward_xi`, `aft_xi`), a
  monotone `3 * t^2 - 2 * t^3` transition with zero slope at both transition
  stations and no spline overshoot. Longitudinal `deck_crown_exponent`,
  `sheer_height_frac`, `section_side_exponent` and `deck_freeboard` profiles
  can be varied directly by active search via RFC 0063 dotted keys.
- RFC 0089 stage 6: `distribution_v2.section_side_exponent` turns the side
  of a `round` section up so that it meets the waterline vertically at 2 and
  above (a U-shaped section) and eases the flare smoothly between 1 and 2.
  The section is fuller at the same draft.
- RFC 0089 stage 5: `topsides.shoulder_round_m` rounds the deck edge. The
  side leaves the waterline on the hull's line, takes half the sheer height
  to turn and blends into the deck, so the upper outline has no corner.
  The `form_metrics` block adds `upper_hollow_max_deg` for a side that
  waists inward (`form.upper_hollow_max_deg` in sweeps and searches).
- RFC 0089 stage 4: the `form_metrics` block reports section knuckles, the
  corner where hull meets topside (`waterline_knuckle_max_deg`) and the
  sharpest corner above it at the topside and deck edge
  (`upper_knuckle_max_deg`), each with its station. Sweeps and searches see
  `form.upper_knuckle_max_deg` and `form.waterline_knuckle_max_deg`, so a
  deck search can be held to a fair deck edge.
- RFC 0089 stage 3: the `form_metrics` block reports foot room, the largest
  centred box between hull and deck at a stated station forward of the
  reference station (`foot_clear_height_m`, `foot_clear_width_m`,
  `foot_station_beam_m`, `foot_station_depth_m`). Sweeps and searches see
  `form.foot_clear_height_m`, `form.foot_clear_width_m` and
  `form.foot_station_beam_m`; `kayakgen evaluate --form-metrics` takes
  `--foot-station-forward-m`, `--foot-box-width-m` and `--foot-box-height-m`.
- RFC 0089 stage 2: `topsides.sheer_beam_ratio` may go down to 0.6
  (tumblehome); `topsides.sheer_plan` draws the sheer as its own fair outline
  in plan view (`max_half_breadth_m`, `max_position_xi`, `forward_exponent`,
  `aft_exponent`), so it can be narrow where the paddle enters without a pinch;
  `topsides.deck_crown_exponent` sets how square the deck is. Form metrics add the beam above a stated height
  in the catch zone and the class beam as a fraction of overall length (the
  USCA limit). Form metrics can be search objectives under the explicit
  exploratory opt-in; per-load righting arms can bound a search as constraints
  and are refused as objectives. Topsides records without the new fields keep
  their bytes and identities.

- RFC 0089 stage 1: `distribution_v2` hulls accept an optional
  `section_exponent` (scalar or longitudinal distribution, 1.5 to 8) that sets
  how full the `round` section is below the waterline; unset keeps the previous
  parabola, bytes and identities. New opt-in form metrics report the race-class
  length-to-beam ratio at a stated draft and the overall beam in the paddle
  catch zone (`kayakgen evaluate --form-metrics`, sweep
  `evaluators.form_metrics`). A sweep can also evaluate righting arms under
  several named loads (`evaluators.high_angle_gz_load_cases`) and writes
  `load_case_gz.json` per candidate. The new measures are display-only. Not
  included: tumblehome, search admission, fullness for other section families,
  and any physical validation.

- RFC 0088: `distribution_v2` hulls accept an optional `topsides` record
  (`sheer_beam_ratio`, `sheer_height_frac`; scalar or longitudinal
  distribution) that adds wall-sided or flared hull sides between the design
  waterline and the sheer. The generated closed body, equilibrium hydrostatics,
  high-angle GZ and section exports use it; upright hydrostatics and
  design-waterline resistance are unchanged. Hulls without the record keep
  their geometry, serialized bytes and identities. Not included: lofted
  geometry, tumblehome, and any physical validation of GZ values.

- RFC 0080: installed runtime lifecycle verification exercises real
  idle controls and optionally observes a persistent local service. Acceptance
  requires effective timeout-zero/server policy, stable process identity and
  process-owned HTTP readiness before and after an explicit idle interval.

- RFC 0086: maintained `python -m kayakgen.operations.citation_closure`
  binds each doctrine citation closure to its phase and immutable packet through
  the installed Pincite classifier, refusing non-activated or unknown doctrine
  identifiers even when the classifier exits zero. Foreign repository/evidence
  locators remain external provenance. Attribution corrections keep the original
  refused closure, require a different-phase closure that actually cited the
  concept and create no runtime or acceptance evidence.

- RFC 0087: maintained `python -m kayakgen.operations.ledger_finalization`
  derives current ledger criterion status only from receipts applicable to each
  item's accepted source, using the RFC 0079 validator. A retained pending
  flag becomes history only when Git ancestry or recorded timestamps prove it
  is older. Newer, unordered, same-source and undeclared pending flags stay
  explicit conflicts. Future physical obligations stay open. `finalize` writes
  the exact original bytes and a proposed ledger to new paths.

- RFC 0083: maintained `python -m kayakgen.operations.release`
  builds an immutable source snapshot, stages a noneditable wheel and verifies
  installed bytes plus actual HTML/report/export and bounded real CFD workflows.
  Supplied hull/context inputs remain unchanged; absent inputs use a labelled
  smoke control. Expected resources derive from source, and HTML requires no PDF extra.

### Changed

- The `openfoam-interfoam-local` profile supports OpenCFD v2606 and records
  the selected solver release and build. `mesh-evidence` records its mesher
  release. Bound mesh packages retain the verified mesh files so the stock
  local profile can run `setFields` and `interFoam`. The historical v2512
  profile remains available for pinned jobs.

- Removed the retired Striatum workflows, prompts, review files, and generated
  build copies. The research notes link to the original thesis and background
  dataset. The Python package ships the public README as its description and
  includes the MIT license.

- Section knuckles are read on the generator's true outline instead of the
  79-point mesh ring, which showed a rounded edge and a corner alike as a
  few facets. Knuckle values of existing hulls change, and a tight bend no
  longer reads low.

### Fixed

- `distribution_v2.section_side_exponent` between 1 and 2 no longer puts an
  infinite-curvature bend on the waterline. A fractional root
  `(1 - u) ** (1 / m)` reached vertical with `d²y / dz² ~ (-z) ** (m - 2)`,
  which read as an 8–19 degree waterline knuckle over a 2 mm probe; the
  quadratic blend `(2 - m) * (-z / draft) + (m - 1) * (-z / draft) ** 2`
  eases the flare from stage 1 at 1 into the upright curve at 2 with finite
  curvature.

- `SqliteIndex` no longer raises `sqlite3.OperationalError: database is
  locked` when several sweeps or searches share `~/.local/share/kayakgen/index.sqlite`.
  Write methods acquire `BEGIN IMMEDIATE` under a 60-second busy timeout, and
  `index_candidates` writes a run's candidate and metric rows in one
  transaction instead of opening hundreds of back-to-back connections.

- `kayakgen.operations.gate.source_snapshot` no longer records a stale
  `tree_sha` when a tracked file was edited in place to the same byte length in
  the same wall-clock second as `.git/index`. Copying the index with
  `shutil.copyfile` gave the temporary index a newer `mtime` and bypassed Git's
  racy-git content check, which could later surface as a false `source_changed`
  gate failure once `.git/index` refreshed.

- `multi_chine` sections no longer carry a notch next to the keel and the
  waterline edge. The chine-smoothing pass averaged with zero padding, pulling
  the points beside each end toward the origin; it now extends the arc by point
  reflection. Hydrostatics of `multi_chine` hulls shift slightly as a result.

- RFC 0088 topsides no longer put a knuckle on the waterline. The strip left
  the waterline vertically, but only `shallow_arch` sections are vertical
  there; `round` sections arrive at 35-50 degrees, which showed as a chine
  along the waterline. The strip now leaves along the hull arc's own tangent
  for every section family. Hulls without `topsides` are unchanged.

- The full and pre-push gates, and any pytest session, now remove Git's
  repository-local environment (`GIT_DIR`, `GIT_INDEX_FILE` and the rest of
  `git rev-parse --local-env-vars`) before running checks. A pre-push hook in a
  linked worktree exports `GIT_DIR`; tests that build throwaway repositories
  inherited it and initialized, staged and committed into the real repository
  (setting `core.bare` and adding a `fixture` commit to the pushed branch).
  `kayakgen.operations.git_env`; `tests/test_git_env_isolation.py`.

- RFC 0084 acceptance correction: two default-refusal CFD tests
  explicitly disable their local-run opt-in for that test only. A complete
  opt-in run can therefore exercise both refusal controls and the enabled
  solver paths while preserving every assertion and all rendering coverage.

- RFC 0082: full and fast/pre-push gates verify actual rendering.
  Mesa software is the default and may overlap after capability/library checks;
  supported NVIDIA hardware holds the existing host lock. Failed or mismatched
  probes prevent check commands. Both fixed plans retain skip/source checks,
  persistent renderer evidence and existing test coverage.

- RFC 0087 review correction: ledger views refuse duplicate or
  missing item identities before aggregation, so an earlier pending entry
  cannot disappear behind another item with the same `work_id`.

- RFC 0084: the canonical full gate runs complete pytest and
  its skip pin before mandatory Ruff. Optional persistent JSON receipts bind
  actual staged/dirty candidate content, preserve failure/interruption
  outcomes and refuse changed source. Inherited `PYTEST_ADDOPTS` cannot
  silently narrow the full check; external-interpreter worktrees remain
  supported. Actual renderer absence remains explicit; RFC 0082 supplies actual observations.

- RFC 0073: evaluator no-rerun test guards share
  `tests/evaluator_guard.py`. It preloads by-name consumers before stubbing,
  keeps the strict no-evaluator assertion, and reports and repairs stub aliases
  captured during the guard. Order regressions run the parser guard and real
  operating-equilibrium consumers in both file orders. Test-only; no evaluator,
  schema or claim change.

- RFC 0069 follow-up: standalone binary STL headers carry the
  full source Hull record SHA-256, metres and part name. Existing triangle
  payloads and normal STL parser compatibility remain unchanged.

- RFC 0078: wheels include the design-report and OpenFOAM runtime templates,
  so installed packages can render reports and case dictionaries.

- RFC 0076: resume preserves completed candidate outcomes and
  frontier eligibility. Sweep records report requested/processed scope,
  cancellation, incomplete execution and reuse separately. Sweep and active
  search verify cached evidence and restore missing canonical files only from
  recorded trusted bytes; unavailable or corrupt evidence refuses reuse.
  Concurrent index initialization now serializes schema checks and mutations,
  preventing one opener from deleting another's freshly committed tables.

- Saved evaluation records refuse conflicting recorded context/curve numerical
  method versions. Matching historical methods and missing legacy method metadata
  remain readable; parsing does not execute or require the current evaluator.

- RFC0073/RFC0077 integration: sweep numerical budgets now reach the shared
  evaluator and saved result. Reported resistance comparisons preserve common
  physical operating requests and warn `incompatible_operating_inputs` for
  different or missing conditions. Web force labels use the actual sampled
  speed and disclose a view target missing from the supplied grid; the grid is
  preserved. Numerical refinement/budget alone is allowed
  to differ. Solved-pose solver settings remain comparison inputs.

- RFC0077: exact sampled linear-depth exponential integration
  removes the Michell depth endpoint artifact. Explicit method-specific numerical
  screening retains requested values, measured per-axis/reference evidence and
  achieved uncertainty. Reported comparison/search frontiers preserve unresolved
  intervals. Unsupported policy assertions remain diagnostic even as singleton
  frontiers; retained observations bind achieved bounds. Historical/unassessed
  curves remain diagnostic and physical claims
  remain unchanged; no default tolerance is introduced.

- RFC 0068: v2 physical identity now binds its complete nested
  distribution spec with the explicit `distribution_v2_v2:` scheme. Lofted,
  record and content hashes remain unchanged; old ambiguous v2 evidence is
  not automatically reaccepted. New calibration campaigns use design identity.

- RFC 0069: `generate` and builder exports consume shared geometry
  capabilities for both lofted and all admitted v2 families. Builder bundles
  preflight dependencies and publish from staging into a new/empty directory;
  failed writes preserve prior files and cannot leave a stale completion manifest.

- RFC 0072: finite evaluator output no longer implies numerical
  convergence. Resistance quality defaults to unknown; exploratory search and
  comparison retain diagnostics but require separate numerical evidence for
  ranked frontiers. Physical claim and display-only gates remain unchanged.
- RFC 0073: evaluation results retain immutable load, fluid, method, grid and operating-pose inputs. Reports can render a selected saved result without numerical recomputation; explicit new loads are recorded separately. Web/desktop adapters preserve supplied contexts.

- RFC 0071: staged streamed commands enforce a monotonic deadline
  while consuming output, terminate their owned process group on expiry, and
  retain a bounded output tail while preserving the complete selected disk log.

- RFC 0070: repeated CFD preparation and terminal run replay preserve
  committed results. Full input conflicts refuse; explicit new attempts retain old
  history. Local preparation/run admission is serialized and provisional
  directories are not executable published jobs.

- RFC 0074: v2 equilibrium moves a waterplane over its fixed
  canonical hull-plus-deck body. Hydrostatics and resistance accept the same
  rigid sinkage/trim pose, with actual-keel reference and explicit infeasible
  load bounds. No-pose legacy evaluations retain their existing behavior.

- RFC 0075: subprocess jobs retain a runner-held ownership lock
  across manager restarts. Proven-dead recovery, per-attempt identity/history
  and fenced state publication prevent duplicate resume and stale writes.
  Legacy or unknown ownership refuses automatic replacement.

- RFC 0067: manifest-backed sweep/search/CFD outputs preserve run
  identity and expected hashes across index reconstruction. Same-basename runs
  remain distinct; reindex reports incomplete legacy provenance explicitly.
  Manifest-backed CFD reads retain published expected hashes instead of
  adopting external edits; legacy reanchoring remains available.

- Search and comparison now enforce the objective registry's `display_only`
  refusal for all four turning metrics, including explicit exploratory mode.
  Generative jobs report the existing objective-admission error
  category before evaluating candidates. Existing GZ refusal tokens, conservative defaults, and
  exploratory controls are unchanged; turning values remain displayable.

- RFC 0066: identical artifact bytes retain separate run/path
  occurrences, so duplicate sweeps no longer disable verification of earlier
  runs. SQLite v1 indexes are backed up and migrated transactionally without
  recomputing trusted hashes from canonical files.

- The web Hydro card shares one hydrostatics result across its text and table
  views and remains available when resistance evaluation fails. Each analysis
  refresh computes only the target-aware resistance curve. The Resistance card
  now renders that curve as a table instead of showing literal HTML markup.

- The web review pane stays usable at 1024x768 and 960x720. Sharing or
  reloading preserves full `Hull` payloads until a slider edit explicitly converts unsupported
  fields to lofted geometry, Generate row controls have row-scoped accessible
  names, and the Generate submit blocker updates reactively as form state
  changes.

## 0.1.0 - 2026-06-08

### Fixed

- The release gates enforce the OpenFOAM skip count inside pytest. Comparison,
  reindexing, and CFD job readers verify recorded artifact hashes. Store reads
  skip corrupt copies and refuse references outside the run directory.

- `ArtifactStore.get_json` decodes the exact bytes whose hash passed
  verification. Missing or corrupt content can be repaired from an intact
  canonical copy. An unrecoverable mismatch raises `ArtifactIntegrityError`.

- `kayakgen runs list --kind` help now lists the supported run kinds. The
  desktop parameter metadata deprecation warning points to RFC 0061.

- RFC 0060 added friendly labels, units, and parameter descriptions to the
  web Generate panel's base hull, variable selectors, and objective list.
  The form serializes the existing hull parameter names.

- `kayakgen runs list` and `kayakgen runs jobs` accept `--header` to print
  column names. Help for run filtering lists `status` and `hull_design_hash`.
  CFD job preparation prints the next run command and opt-in choices.

- `GZCurve.result_semantics` accepts both supported hydrostatic comparison
  labels, so an accepted stability result can round-trip through evaluation JSON.

- Generate-panel form serialization now treats
  the CFD-in-loop acknowledgement as implicit when
  `generative_cfd_in_loop_status == "first_class"`, matching the rendered
  hidden-acknowledgement branch. The default `opt_in_only` path still requires
  the acknowledgement before submission.

- Hardened `parse_openfoam_force_dat` against the real OpenFOAM-v2512
  `forces` function-object tabular schema: rows are 10 numeric fields
  (`time` + total/pressure/viscous triples) by default, or 13 with porous
  contributions. The previous implementation assumed a combined
  19-field force+moment layout that the real v2512 binary does not emit
  (moments live in a separate `moment.dat`). Legacy parenthesised-tuple
  layouts remain rejected with `code='unsupported_layout'`. Fixtures
  under `tests/fixtures/openfoam_v2512/` and `tests/fixtures/openfoam/`
  were regenerated from a real interFoam smoke run; the
  `CfdOpenFoamForceDatSample` now reports a `porous_recorded: bool`.

- OpenFOAM local adapter
  reruns now clear stale per-run raw outputs before command execution, and the
  canonical `GZCurve`/`StabilityResult` contract now round-trips
  fixed-trim generated-body v1 heel metadata.

- Share URLs now reconstruct the saved web hull state without moving the
  slider rails.

### Changed

- Removed the unused `mypy` dependency from the development extras. Added
  closed-form hydrostatics checks, deterministic job-cancellation tests, and
  stability-fit coverage for hysteresis and heel-range boundaries.

- `kayakgen compare` requires `--explicit-exploratory` for raw or
  uncalibrated resistance objectives. `StabilityFitRecord.kind` distinguishes
  analytical fits (the default for existing records) from CFD-in-loop fits.

- RFC 0065 Slice 4 visual-regression hard gate: the browser-acceptance
  profile now hard-fails masked screenshot diffs above the documented
  tolerance (per-channel delta `8`, mismatch ratio `0.02`) against the
  committed in-repo PNG baselines at 1440x900, 1024x768, and 960x720.
  The same profile now checks deterministic toolbar focus order, a
  token-sourced `--state-focus-ring`, 24 px minimum hit targets, and
  `CONTRAST_MANIFEST` in both palettes while retaining nonblank-3D,
  Share reload, STL API, and browser-cleanliness checks. The web app now
  renders the existing token CSS through the Trame content slot so the
  Slice 2/3 visual-system styling is present in Chromium; regenerated
  baselines reflect that post-polish shell. D047 is ratified as accepted,
  and `docs/WEB_VERIFICATION.md` records the baseline procedure, gate
  table, and Lighthouse Best Practices 100 result.

- RFC 0065 Slice 3 control/state pass: the Trame shell and Generate
  panel now apply uniform token-sourced default/hover/focus/active/
  disabled treatment to buttons, tabs, selects, sliders, toggles, and
  native Generate-form controls. The Generate jobs table, Pareto
  frontier, Comparison, Mesh, CFD, Share URL state, and invalid-hull
  banners now expose explicit empty/loading/error/status hooks. Claim,
  readiness, disabled-control, CFD, resistance, high-angle GZ, and
  watertight-readiness copy is unchanged; no REST or analysis boundary
  changed.

- RFC 0065 Slice 2 shell-layout reflow: the Trame workspace shell now
  applies the Slice 1 spacing, density, radius, elevation, border,
  focus-ring, state, and typography tokens across the Parameters rail,
  Geometry viewport/metrics strip, Review cards/tabs, status bar, and
  Generate build/watch/pick surfaces. The existing three-region hooks,
  status segments, 960px collapse hooks, claim/readiness/status copy,
  REST boundary, and generated-analysis semantics are unchanged.

- The web Hydro tab shows each hydrostatics row's description on hover.

- The web parameter rail gains a chip-styled validity-badge header
  (`data-testid="validity-badge"`); the Hydro `<pre>` dump becomes a
  key/value table; high-angle GZ surfaces as a tonal `VAlert`; mesh
  diagnostics render as key/value tables; the mesh readiness chip pair
  shows `No package built` + live `status_readiness` when no package
  is loaded (resolves the "unavailable" contradiction); a new
  Comparison tab hosts the Pareto frontier with a
  `live_frontier / imported_report` `ComparisonSourceToggle`; the
  Generate panel collapses two Submit buttons into a single kind-aware
  button (`data-testid="generative-submit"`), renders variable rows as
  `VDataTable`, objective rows as `VList` + `VAlert` refusal, jobs as
  `VDataTable`; the raw-JSON escape hatch is renamed
  "Raw JSON (advanced)"; the CFD expansion title is updated. Two new
  helpers land in `kayakgen/services/evaluation.py`
  (`hydro_rows_from_state`, `mesh_diagnostics_rows_from_state`) — pure
  view-model transformers, no claim-state widening.
  `tests/test_web_layout.py` gains 11 new `§9.3` checks (#9-#18).

- `docs/USER_GUIDE.md` `### serve` section rewritten to describe the
  post-rework workspace (Param rail / Hydro / Mesh / Comparison /
  Generate tabs, two-column Generate form, kind-aware single Submit,
  Comparison-tab-hosted frontier with `ComparisonSourceToggle`,
  jobs-table columns, "Raw JSON (advanced)" intent, CFD-in-loop
  slowness rationale, responsive breakpoint, validity-badge
  accessibility).

- `docs/WEB_VERIFICATION.md` gains a "data-testid Hook Contract"
  section documenting the hooks as internal test-only contracts that
  may change without notice.

- Documented the search for measured kayak resistance and GZ-versus-heel
  datasets and the limitations of the available research references.

- Clarified that legacy `bow_rake` historically controlled both bow and stern
  and remains the symmetric compatibility behavior for older hull JSON that
  omits `stern_rake`.

- Hardened comparison-report accepted-use provenance so raw comparative
  resistance and forged legacy final-prediction strings cannot become accepted
  calibrated prediction without fixture IDs, model version, fit evidence, and a
  validity envelope.

- Hardened RFC 0027 resistance calibration acceptance gates so only
  `accepted_fit` records with metrics, accepted fixture IDs, model version, and
  validity envelopes can satisfy calibrated-prediction provenance, while weak
  calibration/validation fixture metadata remains rejected.

- `kayakgen evaluate` and compact web metrics now show visible warnings when
  resistance values are the current uncalibrated comparative filter.

### Added

- RFC 0079: maintained completion admission API and
  `python -m kayakgen.operations.completion` argv caller. Strict terminal audit,
  receipt byte/source bindings and task-declared JSON predicates gate one actual
  action invocation; refusals retain reasons and actions are never retried.

- RFC 0081: maintained selected semantic preflight reuses existing
  context, method, admission and display regressions plus the retained operating
  oracle; source-bound partial receipts keep the complete release gate required.

- The artifact store, hull files, and evaluation JSON now use atomic writes.
  The SQLite index records its schema version and rebuilds outdated indexes.
  Added an optional pre-push hook for the fast test suite.

- RFC 0065 Slice 1 theme-token foundation: `kayakgen/ui/theme.py` now
  exposes additive spacing, density, radius, elevation, border,
  focus-ring, and state-token maps; CSS/Vuetify helpers emit them for
  both palettes; contrast tests cover the new focus and state pairs.
  The web shell and Generate frontier view now route existing inline
  dimensions through those tokens with no intended layout or claim-copy
  change, and the UI orphan-literal lint now blocks raw dimension,
  radius, shadow, outline, and focus literals outside `theme.py`.

- RFC 0043 stage 4 — measured-stability accepted-fit registry. New
  `kayakgen/eval/stability/registry.py` lands the 13-gate provenance
  chain that flips the analytical high-angle GZ claim label
  (`unvalidated_hydrostatic_comparison` →
  `validated_hydrostatic_comparison`) only when the full chain is intact:
  immutable fixture manifest + hash-bound acceptance record
  (`promotion.json`) + strict-accepted `StabilityFitRecord` with a
  matching `ANALYTICAL_EVALUATOR_VERSION` and hull-family coverage.
  Fixture presence alone never flips the label. The evaluator call site
  consumes the live, mtime-memoized registry; defaults stay byte-stable
  (empty registry per D039) until a real fixture is promoted — which
  remains gated on D007/D014 physical rig data.

- RFC 0043 stage 4 — CLI + web + `hull_class` completion (closes the
  surface the registry core left open). `kayakgen stability`:
  `promote-fixture` now writes `data/stability/fixtures/<id>/promotion.json`
  verbatim **without** mutating the manifest; `accept-fit` switches to
  `--fit-record / --fixture-id / --out` (legacy `--packet` removed, with a
  pointer refusal); new read-only `claim-status hull.json [--fits-root]
  [--debug]`; every gate refusal emits one structured JSON line whose
  `next_action` comes from `registry.REASON_NEXT_ACTION`. The two web call
  sites (`generate_frontier_view.py`, `generate_spec_form.py`) swap
  `EMPTY_STABILITY_FIT_REGISTRY` for a lazy mtime-memoized loader.
  **`Hull` gains `hull_class: str | None = None`** so the analytical label
  flip works on real generated hulls (the `None` default keeps an untagged
  hull `unvalidated_hydrostatic_comparison`); a registry-cache key fix
  (`_dir_fingerprint` walks non-JSON trace evidence) closes a cache-freshness
  bypass.

- Added inline help for web validity badges, comparison sources, mesh
  readiness, and high-angle GZ. A disabled Generate button now explains which
  form input prevents submission.

- The web Hydro tab takes row labels, units, and descriptions from the
  shared `HydrostaticsRowMetadata` registry (RFC 0062).

- RFC 0061 moved the desktop hull sliders onto the shared parameter labels
  and units. The desktop adapter continues to produce a valid `Hull`.

- RFC 0058 added analytical stability claim labels and stability subcommands
  for ingesting rig runs, promoting fixtures, accepting fits, and plotting
  residuals. The Generate panel uses the label when displaying the frontier.
  The first measured promotion requires physical rig data.

- Landed RFC 0058 stage 1 as schemas only. New
  `kayakgen/eval/stability/accepted_fit.py` pins
  `FixtureRef`, `HullFamilyScope`, `StabilityFitMetrics`,
  `ReviewerSignature`, `StabilityFitRecord`, and
  `StabilityFixturePromotionPacket` with default fit-threshold
  validators and no filesystem fixture resolution. No fixture or fit is
  promoted; `resolve_analytical_claim_label`,
  `cfd_in_loop_evaluator_status`, the `kayakgen stability` sub-app,
  CFD-in-loop graduation, and any upgrade from
  `unvalidated_hydrostatic_comparison` remain deferred.

- Landed RFC 0056 schemas (status: `landed (schemas only)`). New
  `kayakgen/eval/stability/measured_fixture.py` ships
  `MeasuredStabilityFixture` plus value objects (`HullIdentityRef`,
  `LoadingConfiguration`, `CalibrationTrace`, `FreeEquilibriumTrace`,
  `HysteresisBound`, `MeasuredStabilityRow`) with validators enforcing
  the RFC 0056 acceptance gates: `intended_use` enumeration, hull
  identity (64-char SHA-256 scan hash), calibration drift below bound
  (default 0.5%), hysteresis bound (default 3% of GZ_max), free-
  equilibrium-trace presence, constrained-trace blocks promotion.
  Defaults to `intended_use="validation_candidate"`; no fixture is
  promoted by this RFC. +15 focused tests in
  `tests/test_measured_stability_fixture.py`.

- RFC 0057 added form-based generative job control to the web workspace.
  Six new modules under `kayakgen/ui/web/` and `kayakgen/services/`:
  - `generate_spec_form.py` — form-builder primary input (variables,
    NSGA-II/EHVI algorithm radio with per-algorithm sub-forms,
    objectives multi-select filtered live by claim-admissibility, RFC
    0046 CFD-in-loop opt-in row with the pre-vetted ack copy, soft
    advisory at >=4 in-flight jobs, base-hull defaults pre-filled from
    the current single-hull view) plus the collapsible raw-JSON
    escape hatch. `admissible_objective_metrics()` + the
    `GenerateSpecFormError` envelope let tests assert the live filter
    without driving Trame widgets.
  - `generate_frontier_view.py` — 2D scatter synced with a sortable
    table (matplotlib widget with an SVG fallback for headless),
    objective-pair selector + colour-mapped third axis for 3-objective
    EHVI runs, candidate handoff that loads a Pareto candidate into
    the single-hull view with a one-click undo toast.
  - `generate_state_listener.py` — auto-poll listener: 1 s cadence
    while any job is in `{queued, running}`, 10 s otherwise; pauses
    while the Generate tab is not the active review tab; cancellable.
  - `generate_fork_button.py` + `services/generative_jobs_fork.py` +
    new `POST /api/generative-jobs/{job_id}/fork` route — one-click
    "Fork with new seed" for succeeded jobs. The forked job carries a
    new `forked_from` field on `GenerativeJob`; sweep jobs refuse the
    fork (deterministic).
  - `services/generative_jobs._redact_log_text` — strips `$HOME` and
    rewrites paths under `jobs_root` to `<jobs_root>`; routed through
    `generative_job_log_payload`. Byte-stable for redaction-free logs.
  - `kayakgen serve` defaults flipped to the subprocess manager;
    `--jobs-in-process` is the new explicit in-process opt-in. Prints
    the chosen manager kind on startup.

- Landed RFC 0057 stage 3: subprocess manager + crash survival.
  `persist_job_to_dir` now writes ``job.json`` atomically (temp-file
  + ``os.replace``) so concurrent readers never observe a truncated
  payload — this also closes a latent race the in-process manager
  could hit when ``resume()`` raced against the worker thread's first
  write. New `SubprocessGenerativeJobManager` spawns each job as a
  detached Python subprocess invoking the new
  `kayakgen.services.generative_jobs_runner` entry point
  (`python -m kayakgen.services.generative_jobs_runner <job_id>
  <jobs_root> [--resume]`). The child reads `spec.json` + `job.json`,
  transitions to `running`, drives `run_search` / `run_sweep` with a
  file-backed cancel sink (polls `<job_dir>/cancel.flag`), and writes
  terminal state (`succeeded` / `failed` / `resumable`) back to disk.
  Parent reads are file-only — no IPC. The runner cleans up the
  `cancel.flag` on terminal write so a subsequent resume does not
  immediately re-cancel. Crash-survival: if the child is `SIGKILL`-ed,
  the parent's `get()` and `list()` detect a stale `running` state
  with no live process handle and reconcile to `resumable` on disk so
  a follow-up `resume()` can re-spawn against the persisted
  `state.json` checkpoint. File-store helpers
  (`read_job_from_dir`, `list_jobs_in_dir`, `tail_log_file`,
  `append_log_to_file`, `persist_job_to_dir`, `initialize_job_dir`,
  `classify_runner_error`) are now module-level so both managers and
  the subprocess runner share them. New `kayakgen serve
  --jobs-subprocess` flag threads a `SubprocessGenerativeJobManager`
  through `create_app` and `KayakgenApp`; default (no flag) keeps the
  in-process manager. +7 new tests in
  `tests/test_generative_jobs_subprocess.py` (sweep, search, cancel,
  resume, SIGKILL crash + resume, stale-running reconciliation in
  `list()`, direct resume of a stale-running job). RFC 0057 + web +
  boundary slice 211 passed.

- Landed RFC 0057 stage 2: web routes + Trame Generate panel.
  `register_rest_routes` now accepts a `GenerativeJobManager`
  (defaulting to a lazily-built `InProcessGenerativeJobManager` under
  `~/.local/share/kayakgen/generative_jobs/` or
  `KAYAKGEN_GENERATIVE_JOBS_ROOT`) and mounts eight new routes:
  `GET /api/generative-jobs`,
  `POST /api/generative-jobs/{search,sweep}`,
  `GET /api/generative-jobs/{job_id}`,
  `GET /api/generative-jobs/{job_id}/log`,
  `GET /api/generative-jobs/{job_id}/frontier`,
  `POST /api/generative-jobs/{job_id}/{cancel,resume}`. Every payload
  carries `result_semantics: "raw_unvalidated"`. Service-layer helpers
  (`start_generative_job_payload`, `generative_job_list_payload`,
  `generative_job_full_payload`, `generative_job_log_payload`,
  `generative_job_frontier_payload`, `cancel_generative_job_payload`,
  `resume_generative_job_payload`) plus a structured
  `GenerativeJobWebError` envelope mirror the RFC 0018 CFD-route
  pattern; rejection cases return 400/404/409 with explicit `error`
  tokens. The Trame workspace gains a new "Generate" tab (between CFD
  and Advisories) with a spec-JSON textarea, Submit Search / Submit
  Sweep / Refresh Jobs / Cancel / Resume / Load Log / Load Frontier
  buttons, and three bounded text panels for the jobs index, log
  tail, and resolved Pareto-frontier rows. Forbidden-claim scan stays
  green: no new banned tokens introduced; the panel banner reuses the
  existing "no hosted worker is running" allowed phrase. +13 new web
  tests in `tests/test_generative_jobs_web.py`; full RFC 0057 + web
  + boundary slice 203 passed.

- Landed RFC 0057 stage 1: long-lived generative-job foundation. New
  `kayakgen.services.generative_jobs` module ships `GenerativeJob`,
  `GenerativeJobProgress`, `GenerativeJobError`, `GenerativeJobSummary`
  Pydantic records (schema_version="1", canonical JSON byte-stable);
  the `GenerativeJobProgressSink` protocol; and
  `InProcessGenerativeJobManager` running each job in a background
  `threading.Thread` with cooperative cancel (via an internal
  `threading.Event`) and a bounded 256 KB `log.txt` ring buffer per
  job. `run_search` and `run_sweep` gain an optional
  `progress_sink: GenerativeJobProgressSink | None = None` argument
  that emits `candidate_completed` after every persisted record,
  `checkpoint` after every `state.json` write, and polls
  `should_cancel` between candidate emissions; cancellation maps to
  the existing `operator_stop` termination reason. Default
  (`progress_sink=None`) behavior is byte-equal to before across the
  active-search and sweep regression suites. `SqliteIndex` gains a
  `generative_jobs` table (job_id, kind, state, output_dir,
  run_id/run_hash, started_at, completed_at, evaluation counters,
  updated_at) plus `upsert_generative_job` / `list_generative_jobs`
  helpers; new `kayakgen runs jobs [--state] [--kind] [--limit]` CLI
  surface lists them. +30 tests across
  `tests/test_generative_jobs.py`,
  `tests/test_generative_jobs_progress_sink.py`,
  `tests/test_generative_jobs_index.py`, and
  `tests/test_generative_jobs_manager.py`; full suite previously 930
  passed + 2 skipped before this slice. Web routes + Trame panel land
  as stage 2; subprocess-manager + crash-survival lands as stage 3.

- Landed RFC 0045 ordinary-package solver-readiness promotion. New
  `kayakgen mesh-evidence <hull> --out <dir>` subcommand runs the
  OpenFOAM-v2512 meshing stage against a generated closed-body STL and
  emits a serialized `SnappyHexMeshEvidence` plus the polyMesh artifacts;
  refuses without `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` and a sourceable
  bashrc. New `kayakgen mesh-package --bind-evidence <path>` reads the
  evidence and embeds the resulting `VolumeMeshDiagnostic` into the
  manifest. A new `bind_evidence_to_mesh_package(evidence, *,
  closed_body_hash, polymesh_dir)` helper performs three hash checks
  with structured rejection codes (`closed_body_hash_mismatch`,
  `snappy_evidence_body_mismatch`, `polymesh_artifact_drift`, plus
  `evidence_not_recorded` and `evidence_translation_failed`). Default
  `kayakgen mesh-package` JSON is byte-equal to before when
  `--bind-evidence` is absent. +7 tests.

- Landed RFC 0046 non-env-gated OpenFOAM `succeeded` path. Three
  mechanisms admit the real-solver path in precedence order:
  per-job profile flag (`kayakgen cfd prepare
  --allow-real-solver-execution`), persistent setting
  (`~/.config/kayakgen/cfd.json` with
  `allow_real_solver_execution_profiles`), and the existing
  `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` env knob (backwards-compatible).
  Default behavior (no opt-in) stays `solver_success_blocked`.
  `CfdRunRecord` gains a `real_solver_execution_opt_in: Literal[
  "profile_flag","persistent_setting","env_knob"] | None` field and a
  `SolverExecutionAudit` block (bashrc path, provenance summary, locked
  case-template version, mesh seconds, solve seconds). `claim_state`
  stays `raw_unvalidated`; `accepted_uses` stays `[]`. +11 tests across
  `tests/test_cfd_config.py` and `tests/test_cfd_opt_in_resolver.py`.

- Landed RFC 0047 v2 EHVI active-search successor. New
  `kayakgen/search/active/gp.py` ships a vendored Cholesky-factorized
  Gaussian process with Matern 5/2 and RBF kernels and a vendored
  Nelder-Mead marginal-likelihood optimizer (numpy only; no scipy /
  scikit-learn / BoTorch / GPyTorch / scikit-optimize dependency).
  `kayakgen/search/active/ehvi.py` implements EHVI for 1, 2, and 3
  objectives via axis-aligned cell decomposition; raises
  `EhviDimensionError` for 4+. `SearchAlgorithmSpec.kind` accepts a new
  `"ehvi"` literal; `EhviAlgorithmConfig` carries
  `initial_population_size`, `iteration_budget`, `seed`, `gp_kernel`,
  `gp_noise_floor`, `reference_point`, `candidate_pool_size`. The
  runner dispatches on `isinstance(spec.algorithm, EhviAlgorithmConfig)`
  to the new `_run_ehvi_search` path; the RFC 0043 high-angle-GZ
  display-only refusal and the RFC 0044 claim-admissibility gate apply
  unchanged. Seeded determinism is enforced via a single
  `numpy.random.default_rng(seed)` thread through LHS sampling, GP fit,
  candidate-pool draw, and tie-breaking. The synthetic-landscape
  regression test verifies EHVI achieves >=5x hypervolume improvement
  vs random selection at equal budget. Surrogate predictions never
  appear in candidate `summary` or `run.json` objective fields. Default
  NSGA-II behavior is byte-equal. +19 tests across
  `tests/test_active_search_{gp,ehvi,v2_runner}.py`.

- Landed RFC 0043 stage 4 desktop minimal indicator: a new
  `high_angle_gz: cli_only_unvalidated_hydrostatic_comparison` segment
  in the desktop status block points users at the staged opt-in
  surfaces (`kayakgen stability --high-angle-gz`, sweep
  `evaluators.high_angle_gz`, comparison `high_angle_gz_display`, Trame
  web workspace). Per D021 the desktop does not render a curve; the
  segment is a labelled pointer. Forbidden-copy regression in
  `tests/test_desktop_layout.py` confirms no safety / seaworthiness /
  validated / calibrated / final-prediction / design-fitness wording
  leaks onto the desktop status surface.

- OpenFOAM runs now report named execution stages in `CfdRunRecord.stages`,
  from mesh readiness through raw-result parsing. Older records default to
  an empty list. The validation stage is recorded as skipped.

- Added geometry, analysis, and export features in RFCs 0048–0055.
  - **RFC 0048 Geometry V2 (landed v1)**: new
    `geometry_kind="distribution_v2"` on `Hull` with
    `DistributionV2Spec` carrying five `LongitudinalDistribution`
    records, six cross-section families
    (`round`, `shallow_arch`, `shallow_v`, `deep_v`, `hard_chine`,
    `multi_chine` with 2-4 chines), `DistributionV2Geometry`
    producing both canonical closed-body sections and derived open
    inspection surfaces, hydrostatic cross-check (1% volume / 1% Aw
    / 1% LCB / 0.5% GM0; advisory-only), and a
    `kayakgen migrate-geometry` CLI emitting a sibling `*.v2.json`.
    Non-default `bow_rake`/`stern_rake` refused on v2. +77 tests.
  - **RFC 0049 ArtifactStore (landed)**: `Hull.record_hash()` +
    `Hull.design_hash()` (existing `Hull.hash()` aliases
    `record_hash`, byte-stable). New `kayakgen.services.identity`
    (`record_hash`, `design_hash_for_hull`, `run_hash`) and
    `kayakgen.services.artifact_store` (`FilesystemArtifactStore`
    hard-link mirror under `_store/` with copy-on-cross-device
    fallback + missing-mirror warning, `SqliteIndex` auto-creating
    tables at `~/.local/share/kayakgen/index.sqlite` or
    `$KAYAKGEN_INDEX_DB`). Sweep, search, and CFD writers route
    through the store; canonical paths stay byte-stable. New
    `kayakgen runs {list,query,reindex}` Typer sub-app. +17 tests.
  - **RFC 0050 target-draft / target-trim (landed)**: two new CLI
    subcommands `kayakgen target-draft` and `kayakgen target-trim`
    wrapping the existing equilibrium solvers; `--report-only` flag
    on target-draft emits a `TargetDraftMismatchReport`. Refuses
    loads >2× max displaced mass with structured error. +9 tests.
  - **RFC 0051 builder-oriented exports (landed)**: new
    `kayakgen build-export` CLI under a new `[builder]` extras
    group (ezdxf). Seven artifacts: `offsets.csv`, `sections.dxf`,
    `sheer.svg`, `keel.svg`, `waterline.svg`,
    `deck_centreline.svg`, `station_molds.dxf`, plus
    `manifest.json` with per-artifact sha256+bytes. Deterministic
    modulo CAD-library timestamps. +11 tests.
  - **RFC 0052 sensitivity + uncertainty (landed)**: new
    `kayakgen sensitivity` CLI driving central-difference Jacobian
    over the existing evaluators (auto-step `1e-4 * baseline`
    clamped to `[1e-9, 1e-2]`). New `ConvergenceFlag` value object
    populated additively onto `EvaluationResult.convergence` for
    every evaluator. New `PairwiseNote` block on `ComparisonReport`
    flagging Pareto-front pairs whose default-objective metrics
    differ by less than the registry-side
    `within_evaluator_noise_threshold` (default per-metric
    thresholds in `OBJECTIVE_METADATA`). +11 tests.
  - **RFC 0053 turning + edged-waterline metrics (landed)**:
    `TurningMetrics` Pydantic record + `evaluate_turning_metrics`
    over heeled stations; opt-in `--turning [--turning-heel-deg]`
    on `kayakgen evaluate`; sweep `evaluators.turning_metrics`
    flag writes four numeric columns to `summary.csv`. All four
    metrics registered with `role="display_only"` so they are
    refused as Pareto/search objectives. +14 tests.
  - **RFC 0054 calibration-campaign tooling (landed)**: new
    `kayakgen calibration` sub-app with `ingest-tank-test`,
    `ingest-inclining-test`, `accept-fit`, `residual-plot`
    subcommands. New schemas `RightsChecklist`, `GeometryReference`,
    `TankTestRun`/`TankTestCampaign`, `IncliningTestRun`/
    `IncliningTestCampaign`, `AcceptedFitRecord`. The
    `ResistanceSourceReviewPacket` validator now resolves
    `accepted_fit_ref` on disk and refuses below-threshold fits
    with structured tokens. Edinburgh stays at
    `validation_fixture` (synthetic source used for the test).
    +19 tests.
  - **RFC 0055 design-report export (landed)**: new
    `kayakgen design-report` CLI under a new `[report]` extras
    group (jinja2 + optional weasyprint). 10-section single-file
    HTML report (header → parameters → rendered views →
    hydrostatics → stability → resistance → mesh readiness →
    optional comparison position via `--from-run` → artifact refs
    → claim-state explanations) with embedded base64 PNG preview,
    forbidden-copy scan + scrub (named constants
    `FORBIDDEN_COPY_TOKENS`, `FORBIDDEN_COPY_SCRUB_TOKENS`), and a
    structured `ReportForbiddenCopyError` refusal. +8 tests.

- Centralized the metric registry. `ObjectiveMetadata` gains
  `display_format`, `availability_conditions`, and
  `default_objective_eligible`. New helpers
  `register_objective_metadata(metadata)` (refuses duplicate
  registration) and `is_objective_metric_admissible(metric, *,
  explicit_exploratory)` return structured rejection codes
  (`objective_metric_unknown`, `high_angle_gz_display_only`,
  `objective_claim_state_not_admissible`). New `ObjectiveRole`
  literal `"display_only"` is applied to `max_gz_m`,
  `heel_at_max_gz_deg`, `range_positive_stability_deg`; the RFC 0043
  token still owns the refusal. `ensure_objectives_claim_admissible_
  for_search` raises `UnknownSearchObjectiveError` for unknown
  metrics unless `objectives_explicit_exploratory: true`. Sweep
  `summary.csv` now writes every registry-known metric the candidate
  reports (legacy ordering preserved); display-only metrics never
  leak in. Web `read_models._format_metric` consults the registry's
  `display_format`. +16 tests in `tests/test_objective_registry.py`.
  Full suite 733 + 2 skipped; ruff clean.

- Extracted evaluator implementations from the CLI, split CFD and stability
  services into modules, and added the public `HullGeometry.section_for_closed_body`
  accessor. Compatibility shims preserve existing Python imports.

- Promoted the Edinburgh DataShare Pacific-canoe source-review packet
  from `validation_candidate` to `validation_fixture` (RFC 0042 / D025).
  The `ResistanceSourceReviewPacket` validator relaxes in two narrow,
  named ways: `validation_fixture` may carry `non_promotion_reasons`
  describing calibration-fixture blockers (token
  `VALIDATION_FIXTURE_ADMITS_CALIBRATION_BLOCKERS`), and
  `validation_fixture` may have `uncertainty.status == "incomplete"`
  when `uncertainty_notes` is bound and `warnings` carries
  `uncertainty_documented_caveat` (token
  `VALIDATION_FIXTURE_ADMITS_DOCUMENTED_UNCERTAINTY_CAVEAT`).
  `calibration_fixture` still cannot carry non-promotion reasons.
  Edinburgh now binds full `ResistanceSourceRecord` fixture metadata
  (`fixture_id`, `fixture_version="1"`, `accepted_uses=["validation_only"]`,
  `validity_envelope`, `validity_ranges`, `fixture_review_status="accepted"`)
  and keeps `outside_sea_kayak_calibration_envelope` as the lone
  calibration blocker per D013. +2 new tests; the regenerated pinned
  packet JSON lives at
  `tests/fixtures/calibration/edinburgh_review_packet.json`.

- Landed RFC 0044 v1: additive opt-in `kayakgen search` CLI with a vendored
  NSGA-II multi-objective evolutionary algorithm (pure Python, no external
  optimization-library dependency). New subpackage
  `kayakgen/search/active/` ships `SearchSpec`/`SearchAlgorithmSpec`/
  `SearchConstraint`/`SearchBudget`/`SearchLimits`/`SearchVariable`/
  `ObjectiveSpec`/`SearchMetadata` Pydantic records (`spec.py`), the
  vendored NSGA-II implementation with SBX crossover (eta=15) and
  polynomial mutation (eta=20, per-gene probability `1/n_vars`) and binary
  tournament selection (`nsga2.py`), constraint enforcement
  (`constraints.py`), and an orchestrator that reuses the RFC 0009
  candidate-record writer and `pending` lifecycle (`runner.py`). A new
  `ensure_objectives_claim_admissible_for_search` gate in
  `kayakgen/search/pareto.py` (token
  `RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY`) refuses
  `raw_unvalidated` and `uncalibrated_comparative` objectives unless
  `objectives_explicit_exploratory: true` is set; the existing
  `ensure_objectives_not_high_angle_gz` gate always wins. Constraint
  violations produce `status="constraint_failed"` candidate records that
  stay frontier-ineligible. Seeded determinism is enforced by threading a
  single `random.Random(seed)` through every operator; two independent
  invocations of the same spec produce byte-identical
  `candidates/<key>/record.json`. +32 tests across
  `tests/test_active_search_{spec,nsga2,runner,cli,pareto_gate}.py`.
  Default `kayakgen sweep` and `kayakgen compare` behavior is unchanged
  (single one-line literal extension of `CandidateStatus`).

- Closed D012: landed the real `openfoam-v2512-interfoam-local` `succeeded`
  path under opt-in env knobs. New subpackage
  `kayakgen/eval/cfd/openfoam_v2512_interfoam/` ships a vendored case
  template (15 parameterised dicts derived from the proven OpenFOAM
  DTCHull-style smoke), an `OpenFoamCaseSpec`/`render_case` renderer that
  emits byte-deterministic case files, a `runner` that sources
  `/usr/lib/openfoam/openfoam2512/etc/bashrc` and runs
  `blockMesh + surfaceFeatureExtract + snappyHexMesh + checkMesh` (mesh
  stage) plus `setFields + interFoam` (solve stage), and an
  `evidence` module that binds the rendered dict hashes, real
  `constant/polyMesh/*` artifact checksums, parsed `CheckMeshSummary`,
  patch metadata, and the real `OpenFoamProvenanceProbe` (from
  `interFoam -help` banner) into a fully-populated `SnappyHexMeshEvidence`
  record. `OpenFoamLocalAdapter` now flips to `status="succeeded"` only
  when BOTH `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` and `is_openfoam_available()`
  hold; otherwise the historical `solver_success_blocked` path is
  byte-equal. The returned `CfdOpenFoamRawResult` preserves the locked
  `case_template_version="openfoam-v2512-interfoam-dtchull-v1"`,
  `claim_state="raw_unvalidated"`, and empty `accepted_uses`. +8
  binary-free tests under `tests/test_openfoam_v2512_case_render.py` and
  +2 env-gated tests under `tests/test_openfoam_v2512_smoke.py` (auto-skip
  unless `KAYAKGEN_OPENFOAM_SMOKE=1` and the bashrc is sourceable).
  Observed wall-clock: 6.8s mesh + 1.9s solve = ~10.7s end-to-end on a
  default `Hull()` closed body.

- Acquired the Edinburgh DataShare bundle (DOI 10.7488/ds/3785, CC BY 4.0,
  workbook SHA-256
  `dffbd5d4547c9e1c1f5597d6188dc2a1efffd316ab301451fb818e11a22acade`) and
  vendored it under `tests/fixtures/calibration/edinburgh/` with a
  `DATASHARE_PROVENANCE.md` manifest. Rewrote
  `kayakgen/eval/calibration/extractors/edinburgh_datashare_pacific_canoe.py`
  against the real workbook schema: `Averaged Data` sheet, header row 12,
  data from row 14, columns Day/Model/Test/Yaw/Speed/Stbd Drag/Port Drag/
  FWD Side/AFT Side/Heave/Pitch/Velocity/Time/Comment. The extractor filters
  setup/zero/negative test numbers and emits the pinned
  `EXPECTED_OUTPUT_COLUMNS` schema (58 accepted rows from the vendored
  bundle). The source-review packet for the Edinburgh source now binds the
  workbook checksum, removes `pending_data_acquisition` from
  non-promotion reasons, and reports `is_validation_fixture_ready() = True`;
  calibration promotion remains blocked by
  `outside_sea_kayak_calibration_envelope` per decision D013. `openpyxl` is
  now an optional dependency under the `calibration` extras (and pinned in
  `dev`). +5 calibration tests (replaced the stub-raises test).

- Landed RFC 0040 stage 2 `snappyHexMesh` evidence-harness contract in
  `kayakgen/eval/snappy_hex_mesh.py`: locked
  `SNAPPYHEXMESH_CASE_TEMPLATE_VERSION = "openfoam-v2512-snappyhexmesh-watertight-v1"`,
  `SnappyHexMeshEvidence` Pydantic record with required dictionary-hash set
  (`controlDict`, `snappyHexMeshDict`, `meshQualityDict`,
  `surfaceFeatureExtractDict`, `blockMeshDict`), deterministic scaffold builder
  hashed off the generated body identity, patch metadata, `CheckMeshSummary`,
  artifact checksums, and `OpenFoamProvenanceProbe`. A new
  `snappy_hex_mesh_volume_mesh_diagnostic` translator returns `None` for
  partial evidence and hands off into the existing watertight readiness gate;
  no new `cfd_ready` promotion path is opened. +15 tests in
  `tests/test_snappy_hex_mesh_harness.py`. No real `snappyHexMesh` execution.

- Extended RFC 0043 stage 3 to the web workspace: the Trame comparison panel
  now hides the high-angle GZ section when no candidate has artifacts and
  surfaces a "High-angle GZ (display-only)" section with the fixed caption
  "Unvalidated hydrostatic comparison; not safety, seaworthiness, calibrated,
  validated, or final-prediction claim" when at least one candidate carries a
  block. Each row includes body/load/trim provenance, summary metrics,
  warnings, assumptions, and any `unavailable_reason`. A new
  `kayakgen/ui/web/read_models.py` hosts the `WebHighAngleGzRows` view-model
  so the existing forbidden-claim scan on `app.py`/`controllers.py` stays
  green. +7 web tests across `tests/test_web.py` and
  `tests/test_web_read_models.py`. Desktop GUI is intentionally unchanged
  (stage 4 "desktop minimal"; decision recorded as D021).

- Landed RFC 0043 stage 2 (opt-in sweep evaluator) and stage 3 (display-only
  comparison) for high-angle GZ:
  - Sweep: `evaluators.high_angle_gz: bool` (+ optional
    `evaluators.high_angle_gz_heel_grid_deg`) writes per-candidate
    `candidates/<key>/high_angle_gz.json` via the existing stage-1 block
    builder. Records `high_angle_gz_artifact: {path, bytes, sha256}` on the
    candidate. Failed and pending candidates skip emission; resume preserves
    artifacts byte-for-byte. No high-angle key enters `summary.csv` or
    default Pareto objectives.
  - Comparison: `kayakgen compare` reads per-candidate `high_angle_gz.json`
    when present and attaches a `high_angle_gz_display` block to each row
    (body/load/trim provenance, `max_gz_m`, `heel_at_max_gz_deg`,
    `range_positive_stability_deg`, warnings, assumptions,
    `unavailable_reason`). Report adds a `high_angle_gz_columns: bool` flag
    (true only when at least one row has the block). Pareto frontier
    eligibility, default objectives, and resolved metadata are unchanged; a
    new `HighAngleGzObjectiveRefusedError` (token
    `RFC_0043_HIGH_ANGLE_GZ_DISPLAY_ONLY`) refuses any high-angle metric as a
    Pareto objective. +19 tests across `tests/test_sweep.py`,
    `tests/test_compare.py`, `tests/test_pareto.py`.

- Landed RFC 0040 generated-body parameter-matrix hardening: a new 55-case
  parametrized test surface (`tests/test_generated_closed_body_hardening.py`,
  11 hull cases × 5 invariant assertions) pins generated closed-body
  diagnostics across default, exact-plumb, mixed-rake, waterline-pinch,
  shallow/deep draft, low/high Cp, and low/high Cm cases. Hardening proves
  body-ref hash round-trip, RFC 0021 self-intersection `passed` (non-stub
  algorithm), positive signed volume, and that ordinary generated packages
  stay below `cfd_ready` with the expected `generated_body_missing` and
  `volume_mesh_missing` blockers on both open and watertight readiness
  reports. No new mesher or solver-readiness promotion landed.

- Landed RFC 0041 partial: locked the OpenFOAM-v2512 interFoam case-template
  constant (`openfoam-v2512-interfoam-dtchull-v1`), added a Pydantic
  `OpenFoamProvenanceProbe` plus injectable runner seam that requires
  application/build/API token evidence (explicitly refuses
  `$WM_PROJECT_VERSION`-only evidence), and hardened `parse_openfoam_force_dat`
  to require the v2512 19-field schema (`porous` header token); v2306 legacy
  layout and corrupt/short files are rejected with structured codes. The
  `succeeded` path stays blocked: the adapter still returns
  `error_kind=solver_success_blocked`, and the `CfdOpenFoamRawResult` Literal
  refuses non-locked case templates and non-`raw_unvalidated` payload classes.
  +12 tests under `tests/test_cfd_jobs_openfoam.py` with fixtures under
  `tests/fixtures/openfoam_v2512/`. No real OpenFOAM binary or solver success
  path was enabled.

- Landed RFC 0042 partial: restructured `kayakgen/eval/calibration.py` into a
  package with an `extractors/` subpackage, added 12 new packet fields
  (locators, access date, checksum/pending-reason, license, attribution,
  extraction-script ref, units, Froude basis, uncertainty notes, accepted-fit
  ref), and added validators that (a) refuse `rejected` as a runtime
  `SourceUse`, (b) require both `source_checksum_sha256` (lowercase hex) and
  `extraction_script_ref` before a packet can promote to
  `validation_fixture`, and (c) require `accepted_fit_ref` before any
  promotion to `calibration_fixture`. The Edinburgh DataShare Pacific-canoe
  extractor stub raises `NotImplementedError("requires Edinburgh DataShare
  download; pending data acquisition")`. +11 tests under
  `tests/test_calibration.py`; the Edinburgh packet remains a validation
  candidate with `pending_data_acquisition` and
  `outside_sea_kayak_calibration_envelope` non-promotion reasons.

- Landed RFC 0043 stage 1: opt-in `kayakgen stability --high-angle-gz`
  (optional `--heel-grid-deg`) emits a `high_angle_gz` JSON block with the
  fixed-trim generated-body v1 curve, per-heel records, summary metrics only
  when every required grid point converges, mandatory surface warnings, and a
  structured `unavailable_reason` for synthetic bodies. Default
  `kayakgen stability` output is byte-equal to the prior behavior. No web,
  desktop, sweep summary, or comparison-frontier surfaces changed.

- Landed RFC 0009 sweep-side STL artifact emission: `evaluators.stl: true`
  in a sweep spec writes `candidates/<key>/hull.stl` and
  `candidates/<key>/deck.stl` via the same `kayakgen generate` STL writer.
  Each successful candidate record gains `stl_artifacts.{hull,deck}` with
  `{path, bytes, sha256}`. Failed and pending candidates skip artifact
  emission; resume preserves existing STL files byte-for-byte without
  regeneration. Sweep STLs are open inspection surfaces only and do not
  promote any candidate to watertight `cfd_ready`.

- RFCs 0036–0039 refined web state and export controls.
  RFC 0036 retains `_state_matches_preset_seed` with a Trame-state listener
  proof that drives the same-seed event sequence end-to-end without invoking
  the private helper. RFC 0037's `EXPORT_MENU_ROWS` schema is subtitle-only
  with no duplicate guidance fields. RFC 0038 polished the disabled mesh-package
  label to "Mesh package (CLI only)". RFC 0039 unified web snapshot keys and
  CFD/mesh-package aliases onto a shared `WebStateSchema`. No backend
  capability, REST payload shape, calibration, watertight readiness,
  real-solver, or hosted operation changed.

- Updated web query initialization, pending-candidate sweep reporting, and the
  high-angle stability summary.

- RFC 0035 updated the web workspace. Its validity badges now
  classify the current hull against canonical web class envelopes before custom
  fallback, preset edit behavior is documented and test-pinned, export-menu
  rows and web state snapshots use declared source-of-truth schemas,
  slider-label CSS/accessibility checks preserve existing tokens and canonical
  labels, and the desktop Matplotlib slider fallback records its removal
  condition. This is maintenance cleanup only; no backend capability, REST
  payload shape, hosted CFD, real solver, calibration, final prediction,
  high-angle `GZ`, web-side mesh-package authoring, watertight `cfd_ready`
  promotion, or desktop parity rewrite landed.

- Web class presets now reseed canonical hull sliders and narrow their ranges
  (RFC 0034). Manual hull edits return the preset selector to `custom`, the validity badge derives from
  class/envelope state, Resistance and Mesh review cards render existing read
  models, and the Export menu exposes enabled STL rows plus honest local-data or
  unavailable JSON/package states. The slice preserves RFC 0033's no-new-backend
  capability boundary; calibrated drag, final prediction, design fitness,
  high-angle `GZ`, hosted/cloud CFD, real solver adapters, web-side
  mesh-package authoring, watertight `cfd_ready`, and desktop parity rewrite
  remain deferred.

- Landed RFC 0023 watertight volume-mesh handoff slice: typed manifest,
  diagnostic, artifact, hash, and path-bound evidence records now preserve
  conservative open-surface behavior while allowing `cfd_ready` only for
  matching generated-body fixture volume-mesh evidence. CLI and JSON dispatch
  surfaces expose structured rejection reasons for missing, stale, synthetic,
  mismatched, and unsafe handoff evidence.

- Desktop hull-parameter labels and value text now render without overlapping
  adjacent rows, and web parameter-rail slider labels no longer sit under
  persistent thumb labels while preserving the canonical label text.

- Added the RFC 0024 high-angle GZ handoff envelope: generated closed-body
  diagnostic validation, structured unavailable results, fixture-only synthetic
  math, provenance-safe GZ fields, and tests that keep unavailable or fixture
  curves out of CLI, web, and generated sweep secondary-stability claims.

- RFC 0033 introduced shared UI
  theme tokens, structured advisory records, web workspace regions/status
  copy, mesh/readiness read models, desktop `Cm`/Export STLs touch-ups, user
  guide updates, and regression tests. Current resistance, mesh, and CFD
  outputs remain raw/open-surface/local plumbing, not final prediction,
  watertight-solid, hosted-worker, or calibrated claims.

- RFC 0028 added independent
  `stern_rake`, explicit bow/stern coordinate convention, and exact-plumb
  endpoint/cap semantics for generated closed-body diagnostics while keeping
  open hull/deck STLs labeled as inspection surfaces.

- Added the RFC 0022 generated hull-plus-deck closed-volume
  evaluation body with serialized cap/join policy, waterline metadata,
  positive-volume diagnostics, and RFC 0021 self-intersection gating while
  keeping generated bodies below `cfd_ready`.

- Added RFC 0021 explicit synthetic closed-volume
  self-intersection diagnostics: serialized `not_checked`, `passed`,
  `failed`, and `inconclusive` status, assembled-body triangle-pair evidence,
  bounded examples, and a new profile that still keeps `cfd_ready` false.

- Added RFC 0025 claim-state metadata to resistance and raw local-CFD records,
  with forbidden-promotion tests for raw CFD, validation-only fixtures,
  uncalibrated resistance, calibrated prediction evidence, and final
  design-fitness claims.

- Added local web CFD jobs. The `/api/cfd/*` routes and a
  compact Trame panel now expose server-local CFD profiles, job preparation,
  status, synchronous local adapter runs, bounded logs, and raw-result lookup
  over RFC 0015 job records while keeping all output raw and unvalidated.

- Added the deterministic `fixture-local-command` CFD profile,
  fixture case files, local command execution, schema-validated raw-result
  parsing, persisted failure records, and CLI warning visibility, all kept
  raw/unvalidated with no solver validation or calibration claim.

- Added RFC 0031 design-validity metadata across evaluate JSON,
  web payloads, desktop/web warning helpers, sweeps, and comparison reports
  while preserving advisory-only behavior, existing validation boundaries, and
  deferred geometry/CFD claims.

- Added the local browser-acceptance profile, hosted-demo runbook
  documentation, exact `/paraview/` browser-probe handling, Share/STL/3D
  browser checks, and raw/unvalidated `/api/cfd/*` fixture-success coverage
  while keeping public hosting, real solver execution, validated CFD,
  calibrated resistance, and final design-fitness claims deferred.

## 2026-05-13

### Added

- Added the root `README.md` and `docs/USER_GUIDE.md`, documenting current CLI,
  desktop, web, mesh package, and local CFD dispatch behavior without claiming
  calibrated resistance, real solver execution, watertight solids, or high-angle
  stability.
- Added proposed RFCs 0016-0020 to split the remaining roadmap into
  closed-volume geometry, first real CFD adapter, web CFD job routes,
  resistance calibration fixtures, and high-angle secondary stability.
- Added deterministic local CFD dispatch records and CLI surfaces:
  `kayakgen cfd prepare`, `kayakgen cfd status`, `kayakgen cfd run`, and
  `kayakgen cfd profiles`.
- Added a named `watertight_solid_resistance_v1` mesh-readiness profile as a
  blocked future profile, while keeping current generated packages below
  `cfd_ready`.
- Added generalized load components and bounded fixed-body upright trim
  equilibrium for explicit load cases.
- Added compact web analysis and comparison views plus comparison report
  loading.
- Added headless and optional Playwright web verification coverage.
- Added mesh-package diagnostics, manifest/profile metadata, and CLI/test
  coverage for packaging generated hull surfaces.
- Added sweep/candidate report foundations for Pareto-style comparison and
  filtering.
- Added source/provenance metadata for the University of Edinburgh
  Pacific-canoe dataset as validation-only input; no kayak calibration fixture
  was accepted.

### Changed

- Reframed resistance output as an uncalibrated raw comparative filter rather
  than an accepted final prediction model.
- Marked RFC 0004 and RFC 0006 as partial safe slices after package/core work,
  with exact plumb-stem closure, asymmetric rake, watertight solid readiness,
  and remaining UI polish deferred.
- Marked RFC 0008 as partial: Trame shell, headless checks, and compact web
  analysis landed; full REST/browser/hosted-demo parity remains deferred.

### Deferred

- Real OpenFOAM/SU2/container/hosted CFD execution.
- Normalized or validated CFD physical outputs.
- Calibrated kayak resistance fixtures and calibrated product claims.
- Closed-volume hull-plus-deck geometry and watertight solid generation.
- High-angle `GZ` and secondary-stability curves.
- Web CFD job routes and full hosted browser acceptance.

## 2026-05-12

### Added

- Added RFC 0009-0015 covering sweep records, CFD-ready mesh contracts,
  hydrostatic load cases, resistance calibration, Pareto comparison UI,
  generalized trim/GZ, and CFD solver dispatch.
- Added the accepted RFC 0007 package extraction path:
  `kayakgen/`, CLI entry points, compatibility shims, evaluators, and golden
  regression tests.
- Added `KayakClass` presets and `beam_wl` wiring for design constraints.
- Added the analytical resistance evaluator using Michell-wave and ITTC-style
  components as an exploratory comparative model.
- Added plumb-bow support through the `bow_rake` parameter and blended
  end-decay behavior.
- Added the Trame web frontend shell.

### Changed

- Expanded the PRD from a single desktop hull generator toward a generative
  CFD/evaluation pipeline with desktop and web frontends.
- Audited and completed earlier GUI/layout work from RFC 0002 and RFC 0003,
  including class radio controls and plotting/layout cleanup.

## Initial History

### Added

- Added the original parametric kayak generator, desktop GUI, PyVista preview,
  and STL exports.
