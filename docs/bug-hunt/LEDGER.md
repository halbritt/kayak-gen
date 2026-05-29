# Bug-hunt ledger

Append-only list of bugs found by the bug-hunt loop. See
`README.md` for the cadence and `COVERAGE.md` for the surface
inventory.

Finding entry shape (mirrors the audit `AUD-*` shape from RFC
0059 §3):

```markdown
### BUG-001: Short title

severity: critical | high | medium | low | info
category: claim_gate | implementation_gap | test_gap | security | dead_code | math | concurrency | error_path
status: open
surface: kayakgen/<...>
discovered: YYYY-MM-DD <tick-N>
claim: One sentence describing the bug.
evidence:
- path/to/file.ext:line - concise excerpt
- failing test or repro command, when relevant
impact: What goes wrong for an operator or for the project's
  claim discipline.
recommended_action: What should happen next.
follow_up: existing TODO/RFC/decision | new striatum workflow |
  docs fix | wontfix
```

---


### BUG-001: Missing kind field on StabilityFitRecord blocks CFD-in-loop graduation

severity: critical
category: claim_gate
status: open
surface: kayakgen/eval/stability/
discovered: 2026-05-29 tick-1
claim: RFC 0058 defers the `kind` discriminator field to a successor RFC, but `cfd_in_loop_evaluator_status` requires records to carry `kind` to determine graduation eligibility, causing all fits without the field to be silently rejected.
evidence:
- kayakgen/eval/stability/accepted_fit.py:105-123 - StabilityFitRecord has no `kind` field
- kayakgen/services/generative_jobs.py:86-90 - cfd_in_loop_evaluator_status checks `getattr(record, "kind", None)` expecting "analytical" or "cfd_in_loop"
- docs/rfcs/0058-stability-calibration-acceptance.md:331-336 - Q5 explicitly defers `kind` discriminator to successor RFC
- tests/test_cfd_in_loop_evaluator_status.py:21-30 - tests use SimpleNamespace with `kind` field, never test actual StabilityFitRecord instances
impact: When RFC 0058 stage 4 promotes the first real StabilityFitRecord, `cfd_in_loop_evaluator_status` will always return "opt_in_only" because no promoted fit can declare its kind. CFD-in-loop evaluator will remain permanently behind the explicit acknowledgement gate despite the fit record technically satisfying the analytical-path requirement.
recommended_action: Either (1) add `kind` field to StabilityFitRecord now with a default or required discriminator, or (2) defer `cfd_in_loop_evaluator_status` landing to the successor RFC that formally introduces the `kind` field, or (3) redesign the check to not require the `kind` field and instead rely solely on structural presence of required scope fields.
follow_up: RFC successor to 0058 (Q5 resolution) | redesign_cfd_status_logic

### BUG-002: StabilityFixturePromotionPacket lacks validator for constrained-trace fixtures

severity: high
category: implementation_gap
status: open
surface: kayakgen/eval/stability/
discovered: 2026-05-29 tick-1
claim: RFC 0058 requires promotion packets to refuse fixtures with constrained trim/heave at validation time, but the validator is not implemented.
evidence:
- kayakgen/eval/stability/accepted_fit.py:205-231 - StabilityFixturePromotionPacket validator only checks review verdicts, rig_design_match, and rejection_reasons
- docs/rfcs/0058-stability-calibration-acceptance.md:246-248 - "A packet that promotes a fixture whose FreeEquilibriumTrace has constrained_trim or constrained_heave is refused at validate time"
- kayakgen/eval/stability/measured_fixture.py:295-307 - MeasuredStabilityFixture already enforces this constraint; promotion packet should mirror it
impact: An operator can construct a StabilityFixturePromotionPacket that promotes a fixture with constrained trim/heave to "measured_stability_fixture", violating the RFC contract that such fixtures cannot promote beyond "validation_candidate" state.
recommended_action: Add a model_validator to StabilityFixturePromotionPacket that loads the cited fixture via FixtureRef, checks FreeEquilibriumTrace.constrained_trim and .constrained_heave, and raises ValueError if promotion_target=="measured_stability_fixture" and either flag is true.
follow_up: new striatum workflow


### BUG-003: Dead code in OpenFOAM adapter opt-in check

severity: low
category: dead_code
status: open
surface: kayakgen/eval/cfd/
discovered: 2026-05-29 tick-2
claim: The function `_openfoam_succeeded_path_enabled()` is defined but never called, suggesting it is leftover from an earlier design iteration.
evidence:
- kayakgen/eval/cfd/adapters/openfoam_v2512.py:186-206 - function definition
- grep -r "_openfoam_succeeded_path_enabled" returns only the definition, no call sites
impact: Dead code increases maintenance burden and can confuse future readers about the opt-in mechanism. The function duplicates logic present in `resolve_real_solver_execution_opt_in()`.
recommended_action: Remove the `_openfoam_succeeded_path_enabled()` function entirely; the opt-in logic is now centralized in `resolve_real_solver_execution_opt_in()` which is the authoritative RFC 0046 implementation.
follow_up: wontfix or code cleanup

### BUG-004: Missing test coverage for environment variable validation strictness

severity: medium
category: test_gap
status: open
surface: kayakgen/eval/cfd/
discovered: 2026-05-29 tick-2
claim: The opt-in resolver correctly enforces strict "1" matching for KAYAKGEN_OPENFOAM_LOCAL_RUN, but the test suite does not explicitly verify that other truthy-looking values ("true", "yes", "on", "True", "YES") are rejected.
evidence:
- kayakgen/eval/cfd/adapters/openfoam_v2512.py:305 - strict equality check: `env_map.get(OPENFOAM_LOCAL_RUN_ENV_VAR) == "1"`
- tests/test_cfd_opt_in_resolver.py - all tests use exactly "1"; no negative tests for other values
- RFC 0046 does not explicitly document the string-matching strictness
impact: Future maintainers may unknowingly change the check to truthy-style validation (e.g., `if os.environ.get(...)`), silently accepting "true", "yes", "on" and defeating the three-mechanism precedence contract. The test gap allows this regression to slip through.
recommended_action: Add negative test cases to `test_cfd_opt_in_resolver.py` that verify env vars set to "true", "yes", "True", "1.0", "1 ", and "" are all rejected and do not trigger the env_knob mechanism.
follow_up: new striatum workflow


### BUG-005: Path traversal in polyMesh artifact validation

severity: high
category: security
status: open
surface: kayakgen/eval/evidence/
discovered: 2026-05-29 tick-3
claim: The `bind_evidence_to_mesh_package` function does not sanitize artifact names from the evidence JSON before constructing file paths, allowing a malicious evidence record to include keys like `../../../etc/passwd` that traverse outside the polymesh_dir and potentially read arbitrary files.
evidence:
- kayakgen/eval/snappy_hex_mesh.py:707 - `(polymesh_dir / name).is_file()` where `name` comes from `evidence.artifact_checksums` without path validation
- kayakgen/eval/snappy_hex_mesh.py:644 - `polymesh_dir / name` in `_recompute_polymesh_checksums` also lacks sanitization
- Path('/tmp/polyMesh') / '../../../etc/passwd' resolves to '/etc/passwd' and `is_file()` will find it if it exists
- tests/test_mesh_evidence_binding.py - no test coverage for path traversal attacks
impact: An attacker who can control the evidence JSON (e.g. via tampering or replay) can craft artifact_checksums with traversal paths to read arbitrary files on the system during the polymesh drift check, disclosing sensitive data (SSH keys, config files, etc.) via timing or error side-channels.
recommended_action: Sanitize each artifact name before path construction: reject names containing '..', '/', or leading '/', and raise MeshEvidenceBindError with code='invalid_artifact_name' if any traversal attempt is detected.
follow_up: new striatum workflow

### BUG-006: dispatch_state validation occurs after hash checks

severity: medium
category: claim_gate
status: open
surface: kayakgen/eval/evidence/
discovered: 2026-05-29 tick-3
claim: The `bind_evidence_to_mesh_package` function validates `body_ref_hash` and `body_profile` at lines 684-699 before checking if `dispatch_state == "evidence_recorded"` at line 729, allowing incomplete evidence with non-"evidence_recorded" state to pass hash validation and only fail downstream.
evidence:
- kayakgen/eval/snappy_hex_mesh.py:684-699 - body_profile and body_ref_hash checked first
- kayakgen/eval/snappy_hex_mesh.py:729 - dispatch_state checked after hash validation
- RFC 0045 § Promotion gate states "Returns `None` unless `dispatch_state == 'evidence_recorded'"
- docs/rfcs/0045-ordinary-package-solver-readiness-promotion.md:107 - dispatch_state is a prerequisite gate
impact: Evidence with dispatch_state="pending_evidence" but correct body hashes will pass the binding function's hash gates and only fail at line 729 with "evidence_not_recorded". This violates the RFC's gate ordering and leaks information about which hashes match to an attacker who can observe error codes.
recommended_action: Move the dispatch_state check (line 729) to the beginning of the function, immediately after the body_profile check at line 684, so that incomplete evidence is rejected before any hash validation.
follow_up: new striatum workflow

### BUG-007: Path traversal in promote-fixture fixture_id argument

severity: high
category: security
status: open
surface: kayakgen/cli/
discovered: 2026-05-29 tick-4
claim: The `stability promote-fixture` subcommand accepts an arbitrary `fixture_id` argument without path-validation, allowing traversal to arbitrary filesystem locations via paths like `"../../../etc/passwd"`.
evidence:
- kayakgen/cli/stability_cli.py:96 - `fixture_path = _DEFAULT_FIXTURES_DIR / fixture_id / "manifest.json"` where fixture_id is unsanitized positional argument
- kayakgen/cli/stability_cli.py:83-85 - fixture_id is a Typer Argument() with no validation
- Proof: `Path("data/stability/fixtures") / "../../../etc" / "manifest.json"` resolves outside the intended directory
- tests/test_cli_stability.py - no test coverage for path traversal attacks
impact: An operator running `kayakgen stability promote-fixture ../../../etc/passwd --packet ...` can write arbitrary files (via the fixture_path.write_text at line 117) to locations outside the intended fixtures directory, potentially overwriting system files or injecting malicious JSON into trusted locations.
recommended_action: Sanitize fixture_id by rejecting any value containing "..", "/", or starting with "/" before constructing the path. Alternatively, use Path(fixture_id).resolve() and verify the result is within _DEFAULT_FIXTURES_DIR; raise ValueError if not.
follow_up: new striatum workflow

### BUG-008: Unrestricted host binding in serve command

severity: medium
category: implementation_gap
status: open
surface: kayakgen/cli/
discovered: 2026-05-29 tick-4
claim: The `kayakgen serve` command accepts `--host` and `--port` arguments without validation, allowing a user (or a script) to accidentally bind to 0.0.0.0 (all interfaces) or an out-of-range port without warning or refusal.
evidence:
- kayakgen/cli/main.py:634 - `host: str = typer.Option("127.0.0.1", "--host", help="Bind host.")`
- kayakgen/cli/main.py:635 - `port: int = typer.Option(8080, "--port", help="Bind port.")`
- kayakgen/cli/main.py:675 - `web.server.start(host=host, port=port)` passes unsanitized values directly to the web framework
- No validation of host against a restricted list (localhost, 127.0.0.1, ::1) or explicit allowlist
- No validation of port against range [1, 65535] or privileged-port warnings
impact: An operator might accidentally run `kayakgen serve --host 0.0.0.0` intending a local-only server and unintentionally expose the web interface to all network interfaces, violating the documented intent ("Run the Trame web frontend locally"). Similarly, `--port 70000` silently fails or produces cryptic errors rather than rejecting invalid port numbers upfront.
recommended_action: Add validation in the `serve` command body to reject `--host` values other than "127.0.0.1", "localhost", or "::1" with a clear error message. Validate `--port` is in range [1, 65535]; emit a warning if it is below 1024 (privileged ports).
follow_up: new striatum workflow

### BUG-009: Unrestricted n_stations parameter in build-export

severity: low
category: implementation_gap
status: open
surface: kayakgen/cli/
discovered: 2026-05-29 tick-4
claim: The `kayakgen build-export` command accepts `--n-stations` without range validation, allowing a user to specify arbitrarily large values (e.g., `--n-stations 1000000`) that cause excessive memory or CPU consumption.
evidence:
- kayakgen/cli/main.py:777-781 - `n_stations: int = typer.Option(32, "--n-stations", ...)` accepts any int without bounds
- kayakgen/cli/main.py:796 - `BuildExportSpec(n_stations=n_stations)` passes unsanitized value to the service layer
- RFC 0051 (USER_GUIDE.md line 465) does not document a maximum or recommended range
- Practical limit is unknown; no test for malformed values
impact: A user running `kayakgen build-export hull.json --out . --n-stations 1000000` could exhaust memory or hang the process without a helpful error message. The CLI should refuse obviously-unreasonable values or document the practical bounds.
recommended_action: Add validation to reject n_stations values outside a reasonable range (e.g., [1, 1000]). Emit a clear error message if the value exceeds the range, mentioning the practical constraint.
follow_up: new striatum workflow

### BUG-010: Undocumented tolerance_percent behavior in migrate-geometry

severity: low
category: implementation_gap
status: open
surface: kayakgen/cli/
discovered: 2026-05-29 tick-4
claim: The `kayakgen migrate-geometry` command accepts `--tolerance-percent` without bounds validation, and negative or extreme values (e.g., `--tolerance-percent -100` or `--tolerance-percent 1e9`) are silently accepted and produce confusing drift results.
evidence:
- kayakgen/cli/migrate_geometry_cli.py:134-143 - `tolerance_percent: float = typer.Option(1.0, ...)` accepts any float
- kayakgen/cli/migrate_geometry_cli.py:165 - `tolerance_frac = float(tolerance_percent) / 100.0` (no validation before division)
- kayakgen/cli/migrate_geometry_cli.py:169 - comparison `if drifts[metric] > tolerance_frac` with an invalid threshold produces nonsensical results
- USER_GUIDE.md line 449 states "tolerance-percent 1.0" but does not constrain valid input range
impact: Passing `--tolerance-percent -50` or `--tolerance-percent 0` will cause the migration to report failures that do not match the operator's intent. Passing `--tolerance-percent 1e9` will accept all drift values (even 100% drift) silently.
recommended_action: Validate that `tolerance_percent` is a positive float in a sensible range (e.g., [0.01, 100]). Emit a clear error and exit(1) if outside bounds.
follow_up: new striatum workflow

### BUG-011: ResistanceSourceReviewPacket admits fixture promotion without "reasons"

severity: high
category: claim_gate
status: open
surface: kayakgen/eval/calibration/
discovered: 2026-05-29 tick-5
claim: RFC 0042 requires promotion to require "review verdict that names the fixture ID, version, accepted use, validity envelope, and reasons", but the validator does not enforce non-empty `reasons` list for fixtures.
evidence:
- kayakgen/eval/calibration/__init__.py:370-371 - fixture verdicts check `fixture_id` and `fixture_version` but not `reasons`
- kayakgen/eval/calibration/__init__.py:244 - `reasons: list[str] = Field(default_factory=list)` with no min_length constraint
- tests/test_calibration.py - no test coverage for empty reasons on fixtures; all test helpers set `"reasons": ["..."]`
- RFC 0042 § Promotion Rules states "review verdict that names ... reasons" as a requirement
impact: An operator can construct a validation_fixture or calibration_fixture packet with an empty `reasons` list, violating the RFC contract that promotion requires documented rationale. Downstream code and auditors will not see documented decision-making for the promotion.
recommended_action: Add a model_validator that requires `reasons` to be a non-empty list when `review_verdict` is "validation_fixture" or "calibration_fixture", matching the RFC 0042 contract.
follow_up: new striatum workflow

### BUG-012: Path traversal in accepted_fit_ref resolution

severity: high
category: security
status: open
surface: kayakgen/eval/calibration/
discovered: 2026-05-29 tick-5
claim: The `_validate_accepted_fit_ref_on_disk()` method resolves relative paths from `accepted_fit_ref` without sanitizing ".." components, allowing a malicious fixture review packet to construct traversal paths like `"../../../etc/passwd.json"` and check whether files exist outside the intended directory.
evidence:
- kayakgen/eval/calibration/__init__.py:419-421 - constructs `Path(ref)` then joins with `Path.cwd() / path` for relative refs, allowing ".." traversal
- kayakgen/eval/calibration/__init__.py:422 - `path.is_file()` on the traversed path confirms file existence via side-channel
- accepted_fit_ref is a string field in ResistanceSourceReviewPacket (line 262) that can be set by operators in JSON packets
- Path("/cwd") / "../../../etc/passwd.json" resolves to "/etc/passwd.json" and is_file() returns True if /etc/passwd exists
impact: An attacker who can control the fixture review packet (e.g., via tampering, replay, or operator error) can craft an `accepted_fit_ref` with traversal paths to probe for files outside the intended directory, disclosing whether sensitive files (SSH keys, config files) exist via timing or error side-channels.
recommended_action: Sanitize each `accepted_fit_ref` path before resolution: reject values containing "..", "~", or leading "/", and use `.resolve()` to normalize the path before checking if it is within an expected base directory.
follow_up: new striatum workflow

### BUG-013: non_promotion_reasons tokens not validated against known set

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/calibration/
discovered: 2026-05-29 tick-5
claim: Per D025, `validation_fixture` review packets may carry `non_promotion_reasons` that describe blockers against calibration-fixture promotion, but the validator does not enforce that these tokens match a known/registered set, allowing typos or invented tokens to pass validation.
evidence:
- kayakgen/eval/calibration/__init__.py:343-378 - validator checks that validation_fixture CAN have non_promotion_reasons but does not validate the content
- Edinburgh packet uses token `"outside_sea_kayak_calibration_envelope"` (line 702) with no centralized registry or validation
- A misspelled token like `"outside_sea_kay_calibration_envelope"` would pass validation but be invisible to downstream blockers checks
- RFC 0042 and D025 do not define a canonical token registry, leaving the check contract implicit
impact: A typo in a non-promotion reason (e.g., `"outside_sea_kayak_calibration_envelope"` → `"outside_sea_kayak_calibration_envelop"`) would silently bypass the intent to block calibration promotion, making the fixture appear promotable when it should be blocked.
recommended_action: Either (1) define a module-level registry of valid non_promotion_reason tokens as named constants (similar to the existing `VALIDATION_FIXTURE_ADMITS_CALIBRATION_BLOCKERS` token), and validate each non_promotion_reason against the registry, or (2) document the known tokens in an RFC note and add a validator that checks for exact membership in a static set.
follow_up: docs fix or new striatum workflow

### BUG-014: Hull lacks deck_height_m >= draft_m cross-field validator

severity: critical
category: claim_gate
status: open
surface: kayakgen/model/
discovered: 2026-05-29 tick-6
claim: `Hull` declares `draft_m` and `deck_height_m` with only `gt=0` field-level constraints; no `model_validator` enforces `deck_height_m >= draft_m`, yet downstream geometry construction assumes the difference is non-negative.
evidence:
- kayakgen/model/hull.py:37-38 — `draft_m` and `deck_height_m` each carry `gt=0` but no cross-field validator
- kayakgen/model/hull.py:77-101 — `_validate_beam_wl` and `_validate_distribution_v2_coupling` are present; no equivalent `_validate_deck_above_draft`
- kayakgen/model/geometry.py:207 — `local_Deck = (self.H - self.T) * deck_scale` (H = deck_height_m, T = draft_m); a Hull with `deck_height_m < draft_m` produces a negative `local_Deck` and inverts the deck-section curvature silently
- kayakgen/model/geometry.py:311 — `zs = np.array([(self.H - self.T) * self._get_deck_height_scaling(x) for x in xs])` (same subtraction; same vulnerability)
impact: An operator can construct `Hull(deck_height_m=0.1, draft_m=0.2)` directly (or via deserialisation of a maliciously crafted hull JSON), pass Pydantic validation, and propagate an inverted-deck geometry through sweep / search / CFD evaluations. The bad geometry produces wrong hydrostatics, wrong resistance, and a `record_hash` that downstream consumers treat as legitimate. No surface today catches the violation.
recommended_action: Add a `model_validator(mode="after")` to `Hull` named `_validate_deck_above_draft` (or similar) that raises `ValueError` when `self.deck_height_m < self.draft_m`. The default values (0.23 vs 0.12) satisfy this trivially, so existing hulls round-trip. Add a regression test pinning the new gate. Per `feedback_striatum_required`, route through a striatum workflow.
follow_up: new striatum workflow

### BUG-015: Distribution-v2 rake check uses float equality

severity: medium
category: math
status: open
surface: kayakgen/model/
discovered: 2026-05-29 tick-6
claim: `Hull._validate_distribution_v2_coupling` refuses any V2 hull whose `bow_rake` or `stern_rake` is not exactly `1.0`, using `!=` on floats. Hulls round-tripped through JSON or constructed from a near-1.0 value get rejected despite matching the documented intent.
evidence:
- kayakgen/model/hull.py:97 — `if self.bow_rake != 1.0 or self.stern_rake != 1.0:` (exact float equality)
- kayakgen/model/hull.py:45-63 — `bow_rake` and `stern_rake` are `float` in `[0, 1]`; round-trip through JSON or display rounding can perturb a stored 1.0 to 0.9999999999999999
impact: A legitimate distribution-v2 hull whose rake values have been touched by serialisation noise (export → import, or a slider widget that rounds for display) will be rejected at validation time with the message "geometry_kind='distribution_v2' refuses non-default bow_rake / stern_rake; rake is reported but does not drive the V2 loft". The operator sees a confusing error on a hull they did not modify.
recommended_action: Replace the `!=` checks with `not math.isclose(self.bow_rake, 1.0)` etc. Pick a tolerance consistent with the rake's documented precision (1e-9 or 1e-6 depending on the slider step). Add a regression test that round-trips a `distribution_v2` hull through `.model_dump_json()` → `.model_validate_json()` and asserts it survives.
follow_up: new striatum workflow

### BUG-016: Hull is frozen=False without a documented reason

severity: low
category: implementation_gap
status: open
surface: kayakgen/model/
discovered: 2026-05-29 tick-6
claim: `Hull` sets `model_config = ConfigDict(frozen=False, extra="forbid")`, but the class docstring describes Hull as "the aggregate root [that] owns no derived state" with a Pydantic round-trip contract — a description that reads as if the model should be immutable. No comment explains why `frozen=False`. Downstream consumers (`record_hash`, `design_hash`, `claim_state` linkage) compute at call-time, so post-construction mutation produces a Hull whose hash no longer matches any previously-recorded identity.
evidence:
- kayakgen/model/hull.py:29 — `model_config = ConfigDict(frozen=False, extra="forbid")`
- kayakgen/model/hull.py:104-129 — `record_hash`, `design_hash`, and the backward-compat `.hash()` alias all compute deterministically from current field values
- Sibling Pydantic models in the project (e.g. `HydrostaticsRowMetadata`, `HullParameterMetadata`) all use `frozen=True`; Hull is the odd one out
impact: A library caller who mutates `hull.length_m = 10` after construction silently invalidates any cached `record_hash` recorded earlier. The artifact-store (RFC 0049) would see the new hash on the next access and treat the previously-stored record as orphaned. No surface today warns about this.
recommended_action: Either (a) flip `frozen=True` and update the form-builder / desktop slider paths to construct fresh Hull instances on edits (this matches the "aggregate root owns no derived state" docstring), or (b) keep `frozen=False` and add a comment explaining the form-builder mutation requirement plus a regression test asserting downstream hash recomputation. Document the choice in `kayakgen/model/hull.py` and reflect it in `docs/UBIQUITOUS_LANGUAGE.md` if there's an operator-visible concept involved.
follow_up: docs fix or new striatum workflow


### BUG-017: EHVI runner bounds-check via assertion instead of explicit error

severity: low
category: implementation_gap
status: open
surface: kayakgen/search/active/
discovered: 2026-05-29 tick-7
claim: The EHVI runner (RFC 0047 v2) initializes the candidate pool LHS and iterates to select the best EHVI candidate, but guards the result with `assert best_genome is not None` (line 1199) rather than an explicit validation error. While the loop is guaranteed to execute at least once (per `algorithm.candidate_pool_size >= 1` from the spec validator), using assert in production code is bad practice and obscures the invariant from readers.
evidence:
- kayakgen/search/active/runner.py:1199 — `assert best_genome is not None`
- kayakgen/search/active/runner.py:1175-1176 — the candidate pool is guaranteed non-empty by spec validator
- kayakgen/search/active/spec.py:84 — `candidate_pool_size: int = Field(default=256, ge=1)`
impact: If the loop precondition ever becomes unsound (spec validator relaxed, pool construction changed), the assertion will crash the runner with a bare AssertionError instead of a structured error message. This violates the RFC 0044 / RFC 0047 contract that all failure paths are traceable via structured error codes.
recommended_action: Replace the assert with an explicit error: `if best_genome is None: raise RuntimeError("EHVI candidate pool iteration produced no result")` or similar, or document the invariant and suppress the lint warning if the assertion is intentional.
follow_up: wontfix or code cleanup (low priority; does not affect correctness or reproducibility)

### BUG-018: kayakgen/services/ — searched, no actionable bugs (positive baseline)

severity: info
category: claim_gate
status: open
surface: kayakgen/services/
discovered: 2026-05-29 tick-8
claim: Tick 8 searched all 15 service modules; no actionable runtime bugs surfaced beyond the prior findings (BUG-001 through BUG-017).
evidence:
- kayakgen/services/identity.py — `design_hash_for_hull()` uses canonical JSON (`sort_keys=True`); deterministic and stable
- kayakgen/services/evaluation.py:114 — `_row()` closure correctly produces the 4-tuple `(label, value, unit, description)`; downstream consumers (`hydro_rows_from_state` at line 440, `hydro_lines_from_state`) unpack correctly. The workflow 0037/0038/0039 widening is honoured end-to-end.
- kayakgen/services/generative_jobs.py:983 — `SubprocessGenerativeJobManager._spawn()` uses list-based argv (no shell=True), with `start_new_session=True` for isolation. No command injection.
- Subprocess env-var inheritance: `_spawn()` does not pass an explicit `env=` parameter, so the worker subprocess inherits the parent environment. This is a documented Python default, not a bug per se; the worker code does not log env-var values today. Recorded as a known-architectural-fact rather than a finding so future audits don't re-surface it.
impact: No new risks identified. The audit's pipeline-integrity lane (12 positive null findings from the 2026-05-25 full_repo audit) is corroborated by this deeper bug-hunt pass on the same surface.
recommended_action: Optional follow-up tick: future bug-hunt cycles could focus on the lighter-coverage modules (`cfd_jobs.py`, `build_export.py`, `artifact_store.py`, `design.py`) where this tick's depth was thinner.
follow_up: wontfix (positive baseline; defer to next audit's pipeline-integrity lane)

### BUG-019: Exact float equality for bow_rake/stern_rake plumb detection

severity: medium
category: math
status: open
surface: kayakgen/eval/closed_volume/
discovered: 2026-05-29 tick-9
claim: Lines 132-133 of `generated_body.py` use exact float equality `hull.bow_rake == 0.0` and `hull.stern_rake == 0.0` to detect plumb endpoints, but the RFC 0028 specification allows values to be round-tripped through JSON serialisation, which can introduce IEEE 754 perturbations that defeat the exact comparison.
evidence:
- kayakgen/eval/closed_volume/generated_body.py:132-133 — `bow_plumb = hull.bow_rake == 0.0` and `stern_plumb = hull.stern_rake == 0.0` use exact float equality
- kayakgen/model/hull.py:45-63 — `bow_rake` and `stern_rake` are `float` fields that round-trip through JSON
- RFC 0028 § Acceptance Criteria — "With bow_rake = 0.0, the generated closed-body path has non-zero terminal bow section area"
- BUG-015 (discovered tick-6) establishes precedent: distribution_v2 rake checks failed on round-tripped values
impact: A hull with `bow_rake = 0.0` or `stern_rake = 0.0` that is serialized to JSON and deserialized may see the rake perturbed to 0.9999999999999999 or 1.0000000000000002, causing the plumb-endpoint detection to fail silently. The generated body will treat the endpoint as raked rather than plumb, violating the exact-plumb-endpoint closure contract.
recommended_action: Replace exact float equality with `math.isclose(hull.bow_rake, 0.0)` and `math.isclose(hull.stern_rake, 0.0)` at lines 132-133. Use a tolerance consistent with the model's documented precision (suggest `rel_tol=1e-9, abs_tol=1e-12` to match the existing degenerate-area tolerance). Add a regression test round-tripping a hull with plumb endpoints through JSON and asserting the generated body honours the plumb-endpoint closure.
follow_up: new striatum workflow

### BUG-020: dispatch_evidence_satisfies_profile always returns False

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/closed_volume/
discovered: 2026-05-29 tick-9
claim: The `dispatch_evidence_satisfies_profile()` function at lines 120-138 of `diagnostics.py` unconditionally returns False regardless of whether the evidence matches the required profile and readiness level. Lines 136-138 check `if required_mesh_readiness == "cfd_ready": return False` then `return False`, making the function unable to ever return True.
evidence:
- kayakgen/eval/closed_volume/diagnostics.py:136-138 — `if required_mesh_readiness == "cfd_ready": return False` followed unconditionally by `return False`
- kayakgen/eval/closed_volume/diagnostics.py:133-135 — earlier checks on `required_mesh_profile` also return False, leaving no path to True
- tests/test_generated_closed_body.py:464-472 — tests assert the function always returns False
- RFC 0027 documents that "closed-volume diagnostics are safe-slice synthetic-only and never claim cfd_ready"
impact: Any downstream code expecting `dispatch_evidence_satisfies_profile()` to distinguish valid closed-volume evidence from invalid evidence cannot do so. The function is useless for its documented purpose of allowing "dispatch code to distinguish contract-aware rejection from blind manifest trust" (docstring line 129-130). Dead code path represents either an incomplete implementation or a misunderstood requirement.
recommended_action: Either (1) remove the function if RFC 0027's safe-slice guarantees the function will never return True, or (2) fix the logic to return True when profile and readiness checks pass (e.g., return True when `required_mesh_profile is None or diagnostics.profile_name == required_mesh_profile` and `required_mesh_readiness != "cfd_ready"`), or (3) document why the function must always return False and add a comment explaining the contract for future readers.
follow_up: docs fix or new striatum workflow

### BUG-021: Generated closed body inherits inverted deck from BUG-014

severity: high
category: claim_gate
status: open
surface: kayakgen/eval/closed_volume/
discovered: 2026-05-29 tick-9
claim: The RFC 0022 generated closed-body builder (`generated_hull_plus_deck_mesh`) consumes the parametric `Hull` without validating that `deck_height_m >= draft_m` (see BUG-014). If the upstream `Hull` has an inverted geometry (deck below draft), the generated body will silently construct an inverted closed-body geometry with the wrong orientation and negative signed volume, which the diagnostics then "fix" by flipping face winding. The fix masks the upstream invariant violation.
evidence:
- kayakgen/eval/closed_volume/generated_body.py:127 — `geometry = hull.to_geometry()` consumes Hull directly
- kayakgen/eval/closed_volume/generated_body.py:174-175 — if signed volume is negative, face winding is flipped: `if _signed_volume(...) < 0.0: face_array = face_array[:, [0, 2, 1]]`
- kayakgen/model/hull.py:37-38 — (BUG-014) Hull has no `deck_height_m >= draft_m` cross-field validator
- kayakgen/model/geometry.py:207, 311 — deck calculation `(self.H - self.T) * deck_scale` silently produces negative results when inverted
impact: An operator can construct or deserialize a `Hull` with `deck_height_m < draft_m`, trigger the closed-body builder, and obtain a closed body with correct topology but inverted physical meaning. The downstream diagnostics report no error because the geometry is manifold (just flipped). The CFD workflow would receive geometry with wrong volume signs and wrong hydrostatics.
recommended_action: Add validation to `generated_hull_plus_deck_mesh` to check that `hull.deck_height_m >= hull.draft_m` before starting geometry construction, raising `ValueError` with a clear message. Alternatively, require the upstream BUG-014 fix (cross-field validator on `Hull`) as a prerequisite and assume the invariant here. Document the dependency on Hull validation in the docstring.
follow_up: new striatum workflow (coordinated with BUG-014 remediation)

### BUG-022: Path.read_text() and Path.write_text() lack explicit UTF-8 encoding

severity: medium
category: implementation_gap
status: open
surface: kayakgen/io/
discovered: 2026-05-29 tick-10
claim: The `load_hull()`, `save_hull()`, and `save_evaluation()` functions use `Path.read_text()` and `Path.write_text()` without explicitly specifying `encoding="utf-8"`, relying on system locale defaults. This can cause failures on Windows or non-UTF-8 systems (e.g., Windows-1252 or ASCII-only environments).
evidence:
- kayakgen/io/json.py:12 - `Path(path).read_text()` (no encoding parameter)
- kayakgen/io/json.py:16 - `Path(path).write_text(...)` (no encoding parameter)
- kayakgen/io/json.py:20 - `Path(path).write_text(...)` (no encoding parameter)
- Python pathlib docs: "If encoding is not specified, locale.getpreferredencoding(False) is used instead"
- This is locale-dependent and may differ from UTF-8 on Windows
impact: A system administrator deploying kayak-gen on Windows with non-UTF-8 locale encoding or on a non-UTF-8 filesystem may see Hull JSON files fail to read or write with encoding errors. JSON files containing non-ASCII characters (e.g., names with diacritics, special units) will be silently corrupted or rejected depending on the locale.
recommended_action: Add explicit `encoding="utf-8"` to all `Path.read_text()` and `Path.write_text()` calls in `kayakgen/io/json.py`. This is the best practice per PEP 597 and ensures portable behavior across systems.
follow_up: new striatum workflow

### BUG-023: ResistanceCurve and Hydrostatics lack NaN/Infinity validators

severity: medium
category: implementation_gap
status: open
surface: kayakgen/io/
discovered: 2026-05-29 tick-10
claim: The `ResistanceCurve` (lines 102-106) and `Hydrostatics` (lines 64-74) models accept `list[float]` and `float` fields without validators to reject NaN or Infinity values. This contrasts with `GZCurve` and `GZHeelPointMetadata` which enforce finite-value constraints. An attacker or buggy upstream code can construct invalid evaluation records that serialize to JSON with null values, causing downstream deserialization to silently accept incomplete data.
evidence:
- kayakgen/eval/contract.py:102-106 - ResistanceCurve has fields `V_knots`, `Fn`, `Rv_N`, `Rw_N`, `Rt_N` with no validators
- kayakgen/eval/hydrostatics.py:64-74 - Hydrostatics has fields `displaced_volume_m3`, `displaced_mass_kg`, etc. with only `ge=0` constraints, no finite-value checks
- kayakgen/eval/contract.py:196-200 - GZCurve enforces `_curve_values_must_be_finite()` on its array fields
- kayakgen/eval/contract.py:127-139 - GZHeelPointMetadata enforces `_finite_or_none()` on float fields
impact: A ResistanceCurve with NaN in `Rv_N[0]` will serialize to `{"Rv_N":[null, ...]}` and deserialize successfully, leaving downstream resistance calculations to silently skip or misinterpret the null value. Hydrostatics with NaN in `displaced_volume_m3` will round-trip through JSON and silently become null, violating the claim that hydrostatics are always present and valid.
recommended_action: Add `field_validator` decorators to ResistanceCurve for `V_knots`, `Fn`, `Rv_N`, `Rw_N`, `Rt_N` (and `metadata.fit_metrics`, `metadata.constants`) to reject NaN/Infinity. Add similar validators to Hydrostatics for all float fields and array fields (e.g., `gz_curve`). Use the same pattern as GZCurve's `_curve_values_must_be_finite()`.
follow_up: new striatum workflow

### BUG-024: JSON writes lack atomic write pattern; partial corruption possible

severity: low
category: implementation_gap
status: open
surface: kayakgen/io/
discovered: 2026-05-29 tick-10
claim: The `save_hull()` and `save_evaluation()` functions use `Path.write_text()` directly without atomic write semantics (write-to-temp + os.rename). If serialization fails or the process is killed mid-write, the destination file is left in a partially-written state, corrupting the artifact.
evidence:
- kayakgen/io/json.py:16 - `Path(path).write_text(hull.model_dump_json(indent=2))` - single direct write
- kayakgen/io/json.py:20 - `Path(path).write_text(result.model_dump_json(indent=2))` - single direct write
- The serialization call (model_dump_json) can fail or be interrupted; a process crash or SIGKILL during serialization leaves the file half-written
- Repeated save_hull calls to the same path will overwrite previous versions non-atomically
impact: A crash or power failure during a long serialization (e.g., an EvaluationResult with large mesh arrays) will leave a corrupted hull.json or evaluation.json that downstream readers will fail to parse. A subsequent run starting from the corrupted file will fail rather than safely recovering.
recommended_action: Use the atomic write pattern: serialize to a temporary file in the same directory (or tmpdir), then use os.replace (or shutil.move on Windows) to atomically move the temp file to the target path. Example: `tmp_path = Path(path).with_suffix('.tmp'); tmp_path.write_text(...); os.replace(tmp_path, path)`. This ensures the original file is only updated atomically.
follow_up: new striatum workflow

### BUG-025: Print statement in generate_stl violates structured logging

severity: low
category: implementation_gap
status: open
surface: kayakgen/io/
discovered: 2026-05-29 tick-10
claim: The `generate_stl()` method at line 360 of `kayakgen/model/geometry.py` calls `print(f"Saved {filename}")` instead of using structured logging. This violates the project's logging discipline and can interfere with scripts that capture stdout.
evidence:
- kayakgen/model/geometry.py:360 - `print(f"Saved {filename}")`
- kayakgen/io/stl.py:16 calls `geom.generate_stl(part, str(path))` which triggers the print
- The rest of the codebase uses `logging` module (e.g., kayakgen/cli/main.py, kayakgen/services/*.py)
impact: A script that invokes `write_stl()` and reads stdout for other purposes (e.g., progress reporting, JSON output) will see unexpected print output. Automated test runs may capture this output as noise. The I/O success is not recorded in the project's structured logs, making it invisible to log aggregation systems.
recommended_action: Replace the print statement with a structured log message: `logger.info(f"STL written: {filename}")`. Ensure `logger = logging.getLogger(__name__)` is defined in `geometry.py`. Update tests to suppress or ignore this log line if they assert on stdout.
follow_up: wontfix (low priority) or new striatum workflow


### BUG-026: Compare report skips claim-state admissibility gate

severity: high
category: claim_gate
status: open
surface: kayakgen/search/
discovered: 2026-05-29 tick-11
claim: RFC 0044 requires `ensure_objectives_claim_admissible_for_search` to be called from "every entry point (sweep planner, active search, comparison runner)" to refuse `raw_unvalidated` and `uncalibrated_comparative` objectives unless opt-in is set. The comparison report in `kayakgen/search/compare.py:build_comparison_report()` calls `ensure_objectives_not_high_angle_gz()` but never calls the claim-state admissibility gate.
evidence:
- kayakgen/search/compare.py:188, 196 - only `ensure_objectives_not_high_angle_gz()` is called
- kayakgen/search/pareto.py:135-154 - function exists, expects `explicit_exploratory` parameter
- RFC 0044 §Objective-claim gating lines 186-195 - gate requirement stated for "every entry point"
- tests/test_compare.py:363-410 - test `test_raw_resistance_objective_is_exploratory_and_requires_provenance()` implies the gate should be applied in comparison
impact: An operator can run `kayakgen compare -o Rt_N_last:min run_dir/` where `Rt_N_last` is a `raw_unvalidated` metric, and the comparison report will accept it and compute a Pareto frontier over raw resistance values without the `explicit_exploratory` opt-in and without marking the report as `exploratory`. This violates the RFC 0044 contract that allows `raw_unvalidated` objectives only under exploratory mode.
recommended_action: Add a call to `ensure_objectives_claim_admissible_for_search(selected_objectives, explicit_exploratory=False)` in `build_comparison_report()` immediately after line 196, where `ensure_objectives_not_high_angle_gz(selected_objectives)` is called. The gate will refuse any `raw_unvalidated` or `uncalibrated_comparative` metric unless the operator explicitly opts in (which is a future CLI feature for the comparison tool).
follow_up: new striatum workflow

### BUG-027: Float precision in Pareto dominance comparison lacks tolerance

severity: medium
category: math
status: open
surface: kayakgen/search/
discovered: 2026-05-29 tick-11
claim: The `dominates()` function in `kayakgen/search/pareto.py:236-265` uses exact float comparison (`left_value < right_value`, `left_value > right_value`) without tolerance for floating-point round-trip error. Per BUG-015 and BUG-019, objectives often round-trip through JSON serialization, introducing IEEE 754 perturbations. A candidate that is truly non-dominated on a metric (e.g., drag=1.2345 vs drag=1.2345) may be incorrectly considered dominated if the float encoding differs by less than the last significant bit.
evidence:
- kayakgen/search/pareto.py:256-263 - exact comparisons `left_value < right_value` and `left_value > right_value`
- BUG-015 established float-equality risk in rake checks
- BUG-019 established float-equality risk in plumb endpoint detection
- No `math.isclose()` tolerance applied to objective comparison
- Pareto frontier members are returned in input order (line 280-284), so dominance order matters
impact: Two candidates with objective values that differ by less than machine epsilon (or after lossy JSON round-trip) may incorrectly dominate/be dominated, causing incorrect Pareto frontiers. A candidate that should appear on the frontier may be filtered out, or vice versa. The effect is subtle because it only triggers when candidates have nearly-equal objective values, but the Pareto result becomes non-reproducible across serialization formats.
recommended_action: Add a tolerance parameter (e.g., `rel_tol=1e-9, abs_tol=1e-12`) to the `dominates()` function and use `math.isclose()` for all four comparisons at lines 257, 259, 261, 263. The tolerance should match the precision documented in `OBJECTIVE_METADATA[...].display_format` or a project-wide constant (e.g., RFC 0052 noise threshold). Add a regression test that round-trips two near-equal candidates through JSON and verifies they remain non-dominated.
follow_up: new striatum workflow

### BUG-028: Survey completed without actionable findings

severity: info
category: claim_gate
status: open
surface: kayakgen/search/
discovered: 2026-05-29 tick-11
claim: Tick 11 surveyed all non-active files in kayakgen/search/ (objectives.py, pareto.py, sweep.py, compare.py, __init__.py). Beyond BUG-026 (missing claim gate in compare) and BUG-027 (float tolerance in dominance), no other actionable bugs surfaced. Variable enumeration in `sweep.py:expand_candidates()` uses itertools.product correctly (line 168); parameter expansion via `np.linspace()` is correct (line 66); candidate hashing is deterministic (line 180); and claim-state aggregation is present (resistance metadata on line 466). The high-angle GZ display-only token is properly respected throughout the surface.
evidence:
- kayakgen/search/sweep.py:62-66 - `np.linspace()` correctly expands parameter ranges with specified count
- kayakgen/search/sweep.py:164-182 - `expand_candidates()` uses `itertools.product()` to enumerate all combinations; order is stable
- kayakgen/search/sweep.py:466 - resistance claim_state is carried in summary for downstream visibility
- kayakgen/search/pareto.py:22-46 - HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN and SEARCH_REFUSED_CLAIM_STATES are well-defined
- No call to `ensure_objectives_claim_admissible_for_search()` is expected in sweep.py (sweep is pre-search infrastructure)
impact: None; this is a positive baseline scan.
recommended_action: No action needed for this surface beyond the two issues already logged (BUG-026, BUG-027). Future audits can mark this surface as settled unless RFC 0044 successor lands new objective-admissibility rules.
follow_up: wontfix (positive baseline)

### BUG-029: validity_badge_title_for() renders NaN / inf in tooltip text

severity: low
category: implementation_gap
status: open
surface: kayakgen/ui/web/app.py
discovered: 2026-05-29 tick-12
claim: `validity_badge_title_for(badge)` extracts a ratio string from a badge of the form `Custom (L/B_wl=X.X)` via string slicing and embeds it in the tooltip without finite-number validation. If upstream `l_over_bwl` is NaN / inf (which requires Hull validation bypass), the rendered tooltip reads "Hull length-to-beam ratio is nan; ...".
evidence:
- kayakgen/ui/web/app.py:324 — `def validity_badge_title_for(badge: str) -> str`
- kayakgen/ui/web/app.py:349-350 — `if badge.startswith("Custom (L/B_wl="): ratio_part = badge[len("Custom (L/B_wl=") :].rstrip(")")`
- kayakgen/ui/web/app.py:504, 885 — Hull-validation-bypassed paths construct `"Custom (L/B_wl=0.0)"` as a fallback
- Parent thread verified the call-site structure via grep
impact: Cosmetic tooltip glitch only. Hull's `gt=0` validator on `beam_wl_m` normally prevents the NaN-producing upstream. Not a claim-state leak; not a security issue.
recommended_action: Guard `ratio_part` against `inf` / `nan` by parsing it as a float and falling back to a generic message if non-finite. Or upstream: ensure the formatter clamps before formatting. Low priority; cosmetic only.
follow_up: docs fix or new striatum workflow (low priority)

### BUG-030: Comparison-source toggle leaks state across mode switch

severity: medium
category: implementation_gap
status: open
surface: kayakgen/ui/web/app.py
discovered: 2026-05-29 tick-12
claim: The Comparison-tab `live_frontier` ↔ `imported_report` toggle does not clear comparison state on mode switch. Switching modes can pair stale candidate lists with empty / new JSON, producing silent failures.
evidence:
- kayakgen/ui/web/app.py:1722-1774 — the toggle handler updates `comparison_source` but does not reset `comparison_json`, `comparison_candidate_options`, `selected_candidate_index`
impact: Operator confusion at minimum; a silently-failed candidate load can look identical to a successful no-op, hiding that the previously-imported report is no longer relevant.
recommended_action: Add a clear-state action to the toggle `on_change` handler that resets `comparison_json` / `comparison_candidate_options` / `selected_candidate_index`. Add a render-verification test that toggling `live_frontier → imported_report → live_frontier` leaves the state at its initial values.
follow_up: new striatum workflow

### BUG-031: Hydro-tab description binding pattern note (positive baseline)

severity: info
category: implementation_gap
status: open
surface: kayakgen/ui/web/app.py
discovered: 2026-05-29 tick-12
claim: The Hydro-tab tooltip wiring `:title='row.description'` (workflow 0039) does not HTML-escape the description. Safe today because `HYDROSTATICS_ROW_METADATA` descriptions are hardcoded literals; worth documenting for any future surface that sources descriptions from operator input.
evidence:
- kayakgen/ui/web/app.py:1587 — `:title='row.description'` binding
- kayakgen/ui/hydrostatics_metadata.py — descriptions are frozen literals; no operator-controlled paths feed them
impact: No current risk; recorded as a pattern note so the next audit knows this binding-shape is safe today but would not be if the registry stopped being hardcoded.
recommended_action: Documentation only — add a comment near the binding noting "safe because HYDROSTATICS_ROW_METADATA descriptions are hardcoded; revisit if descriptions ever source from operator input."
follow_up: docs fix (low priority)



### BUG-032: Infinity values in frontier z-metric not filtered, producing NaN color ratios

severity: low
category: implementation_gap
status: open
surface: kayakgen/ui/web/generate_frontier_view.py
discovered: 2026-05-29 tick-13
claim: The `_coerce_float()` function at lines 159-168 guards against NaN but not infinity. Infinity values in the third objective (z-metric) can propagate through the color-ratio calculation and produce NaN when z_low and z_high are both infinity, resulting in SVG data attributes containing the string "nan".
evidence:
- kayakgen/ui/web/generate_frontier_view.py:166 — `if result != result:` (NaN check only; misses infinity)
- kayakgen/ui/web/generate_frontier_view.py:280-282 — infinity values pass through and are included in z_values list
- kayakgen/ui/web/generate_frontier_view.py:283-284 — `z_low = min(z_values)` and `z_high = max(z_values)` with infinity values
- kayakgen/ui/web/generate_frontier_view.py:140 — `(value - low) / span` produces NaN when span is NaN (all z_values are infinity)
- kayakgen/ui/web/generate_frontier_view.py:430 — NaN ratio is HTML-escaped and rendered as the string "nan" in SVG
impact: Cosmetic rendering issue; SVG data attributes contain the string "nan" instead of a numeric ratio. This could confuse debugging and is inconsistent with the NaN guard applied to the result. No claim-state leak or calculation error, but asymmetric handling of NaN vs infinity.
recommended_action: Extend the guard in `_coerce_float()` to also reject infinity: `if result != result or math.isinf(result): return None`. Add a regression test that rounds a candidate with infinity in z-metric through the view-model and asserts it does not produce NaN in the ratio.
follow_up: new striatum workflow (low priority)

### BUG-033: Substring matching in FORBIDDEN_METRIC_TOKENS allows false negatives

severity: low
category: implementation_gap
status: open
surface: kayakgen/ui/web/generate_frontier_view.py
discovered: 2026-05-29 tick-13
claim: Line 150 uses substring matching (`token in lowered for token in FORBIDDEN_METRIC_TOKENS`) to detect display-only metrics. This is safe for the six token values (max_gz_m, heel_at_max_gz_deg, etc.) but the pattern is fragile. If a metric name like `my_max_gz_m_custom` exists, it would match and be filtered (acceptable). However, if a metric is added that starts with the same prefix but has additional characters (e.g., "gz_m_wrapper" vs "gz_m"), the substring match could produce unexpected behaviour — metrics intended to be allowed might match a forbidden token by accident.
evidence:
- kayakgen/ui/web/generate_frontier_view.py:45-52 — FORBIDDEN_METRIC_TOKENS defined as (max_gz_m, heel_at_max_gz_deg, range_positive_stability_deg, area_under_positive_gz_m_deg, righting_moment_nm, gz_m)
- kayakgen/ui/web/generate_frontier_view.py:148-150 — `_is_forbidden_metric_key` uses substring containment: `any(token in lowered for token in FORBIDDEN_METRIC_TOKENS)`
- RFC 0057 stage 4 decision D-6 requires "high-angle GZ display-only metrics" to be dropped, but does not specify substring vs exact-match semantics
impact: Low risk today because the FORBIDDEN_METRIC_TOKENS are all short and specific. But if a new metric like "area_under_positive_gz_m_deg_wrapper" is added, the substring match would incorrectly filter it. Alternatively, a metric like "my_area_under_positive_gz_m_deg_extra" would also be filtered, which is the safe direction but may hide operator mistakes. No current violation, but the pattern is implicit rather than explicit.
recommended_action: Document the substring-match rationale as a comment near the function. Alternatively, switch to exact-match semantics using a set lookup for clarity: `metric.lower() in {t.lower() for t in FORBIDDEN_METRIC_TOKENS}`. This trades substring flexibility for precision and makes the contract explicit. No regression risk because all tokens today have no common prefixes across the set.
follow_up: docs fix or new striatum workflow (low priority)


### BUG-034: Surface audit — kayakgen/ui/web/controllers.py — Positive baseline

severity: info
category: claim_gate
status: open
surface: kayakgen/ui/web/controllers.py
discovered: 2026-05-29 tick-14
claim: Comprehensive audit of the controllers.py re-export/glue module found no actionable runtime bugs, validator gaps, or state-management issues.
evidence:
- kayakgen/ui/web/controllers.py:99-161 — __all__ list contains 61 names, all of which are imported from services modules or defined locally (verified against lines 16-96)
- kayakgen/ui/web/controllers.py:210-300 — route handlers consistently use try/except blocks with structured error responses (validation_error_payload, cfd_error_response, generative_error_response)
- kayakgen/ui/web/controllers.py:428-473 — fork endpoint validates new_seed type correctly (line 451: `isinstance(new_seed, int) or isinstance(new_seed, bool)` correctly rejects bools)
- kayakgen/ui/web/controllers.py:164-499 — register_rest_routes function is idempotent and safe to call multiple times; new stores/managers are created each time
- kayakgen/ui/web/app.py:932 — re-entrancy guard `_applying_class_preset` prevents state-listener loops when class_preset is changed during hull param changes
- kayakgen/ui/web/generate_state_listener.py:135-147 — stop_generate_state_listener correctly cleans up the listener thread and restores the original callback
impact: None. This is a positive baseline scan. The module functions correctly as a thin re-export and REST-route-mounting glue layer.
recommended_action: No action needed. The surface is settled and can be marked as searched without further follow-up unless the module is modified with new logic.
follow_up: wontfix (positive baseline)

### BUG-035: Class-preset slider narrowing lacks synchronization guard

severity: medium
category: concurrency
status: open
surface: kayakgen/ui/desktop.py
discovered: 2026-05-29 tick-15
claim: When a class preset is selected, `_on_class_select` narrows slider ranges via `_apply_slider_ranges(kc)` (line 190) before seeding the 5 parameter sliders with new values via `slider.set_val(val)` (line 196). Each `set_val()` call fires `_on_change` callback synchronously, which reads raw slider values from all sliders in the loop at lines 318-319. If a slider's old value was outside the newly-narrowed range, matplotlib may not have clamped it yet, causing `self.params` to be populated with out-of-range values that violate the class constraint.
evidence:
- kayakgen/ui/desktop.py:190-196 - `_apply_slider_ranges(kc)` narrows ranges, then loop sets only 5 seed values; other sliders unchanged
- kayakgen/ui/desktop.py:212-218 - range narrowing modifies `slider.valmin` and `slider.valmax` but does not clamp current slider.val
- kayakgen/ui/desktop.py:318-319 - `_on_change` reads all slider values indiscriminately, capturing out-of-range values if matplotlib did not clamp
- matplotlib Slider documentation notes that `valmin`/`valmax` are advisory and do not retroactively clamp `val` on update
impact: An operator selecting a class preset may see hull parameters that violate the class envelope after the selection completes, if any non-seeded slider had a value outside the new narrowed range. The params dict is populated with out-of-range values, and downstream consumers (hydrostatics evaluation, geometry construction) may silently accept them or produce incorrect results.
recommended_action: After narrowing ranges in `_apply_slider_ranges(kc)`, immediately clamp all slider values to the new range before seeding: for each slider, set `slider.val = np.clip(slider.val, slider.valmin, slider.valmax)` (without triggering the callback). Alternatively, collect all slider updates into a batch and apply `_on_change` once at the end after all ranges and values are synchronized.
follow_up: new striatum workflow

### BUG-036: PyVista window lacks explicit cleanup on close

severity: low
category: implementation_gap
status: open
surface: kayakgen/ui/desktop.py + kayakgen/ui/pv_window.py
discovered: 2026-05-29 tick-15
claim: The PyVista 3D preview window (`PyVistaWindow`) is created on-demand in `_on_open_3d` (line 390) but the window has no explicit close event handler or resource cleanup path. When the user closes the window, the `_pv_window` reference in `KayakGUI` is not cleared, and the next call to `_on_open_3d` attempts to reuse the closed window object instead of creating a fresh one. This can leave PyVista plotter resources allocated even after the window is visually closed.
evidence:
- kayakgen/ui/desktop.py:384-393 - `_on_open_3d` checks `if self._pv_window is None or not self._pv_window.isVisible()` but does not call a cleanup method
- kayakgen/ui/pv_window.py:56-147 - `PyVistaWindow` (subclass of `QMainWindow`) has no `closeEvent` override or destructor to clean up `self._plotter`
- kayakgen/ui/desktop.py:327, 396 - checks `self._pv_window.isVisible()` but assumes the window can be reused if visible
impact: Repeated open/close cycles of the 3D preview may accumulate PyVista plotter resources (OpenGL contexts, mesh renderers) without releasing them, leading to gradual memory leaks and potential GPU resource exhaustion on long sessions.
recommended_action: Add a `closeEvent` handler to `PyVistaWindow` that calls `self._plotter.close()` or equivalent cleanup. Set `self._pv_window = None` in `_on_open_3d` if `isVisible()` returns False, ensuring a fresh window is created on the next open.
follow_up: new striatum workflow

### BUG-037: STL export path is not normalised before write

severity: low
category: implementation_gap
status: open
surface: kayakgen/ui/desktop.py
discovered: 2026-05-29 tick-15
claim: The `_on_generate` method (line 367) uses `QFileDialog.getSaveFileName` to prompt the user for an export path, then constructs hull/deck STL filenames by stripping suffixes and appending `_hull.stl` and `_deck.stl`. The path is not normalised before being passed to `generate_stl`, so a relative `../foo/bar` typed into the dialog writes outside the dialog's initial directory.
evidence:
- kayakgen/ui/desktop.py:370-381 - `QFileDialog.getSaveFileName` returns the path string verbatim
- kayakgen/ui/desktop.py:375 - `stem = path.removesuffix("_hull.stl").removesuffix(".stl")` (no `Path.resolve()`)
- kayakgen/ui/desktop.py:379-380 - `geom.generate_stl("hull", f"{stem}_hull.stl")` writes to the unsanitized stem location
impact: **This is not a security boundary issue** — the path is operator-supplied via a save dialog; there is no untrusted JSON / external file driving the write. The threat model differs from BUG-005, BUG-007, and BUG-012 (which were attacker-controlled paths feeding into validation/loading). The actual risk here is operator footgun: typing `../foo/bar` into the dialog writes to a location the operator probably didn't intend. Parent-thread downgrade: subagent classified as `medium/security`; reclassified as `low/implementation_gap` to reflect the trust boundary.
recommended_action: Normalise the path via `Path(path).resolve()` before passing to `generate_stl`. Optionally clamp to a permitted parent (e.g., the dialog's initial directory) and emit a warning if the resolved path escapes. Low priority; this is defensive ergonomics, not a security fix.
follow_up: docs fix or new striatum workflow (low priority)

### BUG-038: Slider re-entrance during class-preset seeding lacks protection

severity: low
category: concurrency
status: open
surface: kayakgen/ui/desktop.py
discovered: 2026-05-29 tick-15
claim: During class-preset seeding (`_on_class_select` lines 189-197), the code sets `_applying_class = True` as a re-entrance guard and then calls `slider.set_val(val)` five times in a loop. Each call triggers `_on_change` callback, which checks `_applying_class` at line 315 to short-circuit the custom-class flip. However, the guard does not prevent the full `_on_change` logic (plots, 3D timer, metrics refresh) from executing 5 times, resulting in expensive redundant work. The comment at line 191-192 acknowledges this ("Cheap because we set five values") but it is not actually cheap.
evidence:
- kayakgen/ui/desktop.py:189-197 - loop executes 5 times, each calling `set_val` which triggers `_on_change`
- kayakgen/ui/desktop.py:315-329 - `_on_change` runs plots, 3D timer, and metrics refresh every call, even during class preset
- kayakgen/ui/desktop.py:326 - `self.update_plots()` is O(geometry computation), called 5 times redundantly
- kayakgen/ui/desktop.py:329 - `self._refresh_metrics()` is O(hydrostatics evaluation), called 5 times redundantly
impact: Class-preset selection is visibly slower than necessary because plots and metrics are recomputed 5 times instead of once. On slow machines or with high-resolution geometries, this can cause UI lag.
recommended_action: Extend the `_applying_class` guard to skip the expensive `update_plots()` and `_refresh_metrics()` calls during seeding. After all 5 values are set, call `self.update_plots()` and `self._refresh_metrics()` once explicitly. This matches the web version's `_applying_class_preset` guard pattern (documented at kayakgen/ui/web/app.py:932).
follow_up: new striatum workflow (performance optimization, medium priority)

### BUG-039: Field-level min_length validator allows whitespace-only strings

severity: low
category: implementation_gap
status: open
surface: kayakgen/ui/parameter_metadata.py + kayakgen/ui/hydrostatics_metadata.py
discovered: 2026-05-29 tick-16
claim: Both registry models use `Field(min_length=1)` on `parameter`, `label`, and `description` fields, but this validator only checks string length, not content. A whitespace-only string like `"   "` (three spaces) passes validation with length=3, but becomes empty when stripped. The regression tests correctly catch this (they assert `label.strip() == label`), so this is defense-in-depth, not a live bug.
evidence:
- kayakgen/ui/parameter_metadata.py:30-33 - `parameter`, `label`, `description` use `Field(min_length=1)`
- kayakgen/ui/hydrostatics_metadata.py:37-40 - same pattern
- Pydantic ValidationError only rejects empty strings (length=0), not whitespace-only strings
- tests/test_hull_parameter_metadata.py:54-61 - test correctly asserts `label.strip() == label and label.strip() != ""`
- A hypothetical direct construction like `HullParameterMetadata(parameter='test', label='   ', unit=None, description='OK')` passes Pydantic validation
impact: If a developer manually constructs a registry entry with whitespace-only copy, Pydantic accepts it. The test suite catches the mistake at assertion time, but the validator itself is not a sufficient first-line defense. No operator-facing risk because the registries are hardcoded in source, not user-configurable.
recommended_action: Add a custom `field_validator` to both models that rejects whitespace-only strings (e.g., `if not value.strip(): raise ValueError('must be non-empty after strip')`). This is a belt-and-suspenders improvement; the test is already correct, but the validator should match the test's intent.
follow_up: new striatum workflow (optional; test coverage is already adequate)


### BUG-040: Path.read_text() lack explicit UTF-8 encoding in cfd_jobs.py

severity: medium
category: implementation_gap
status: open
surface: kayakgen/services/
discovered: 2026-05-29 tick-17
claim: The `cfd_job_raw_result_payload()` function at line 247 of `cfd_jobs.py` calls `path.read_text()` without explicitly specifying `encoding="utf-8"`, relying on system locale defaults. This mirrors BUG-022 (same pattern in `kayakgen/io/`), but extends across multiple services modules (`generative_jobs.py`, `generative_jobs_fork.py`, `generative_jobs_runner.py`, etc.). Consistent with PEP 597, all pathlib `read_text()` and `write_text()` calls should specify `encoding="utf-8"` for portable cross-platform behavior.
evidence:
- kayakgen/services/cfd_jobs.py:247 - `text = path.read_text()` (no encoding parameter)
- kayakgen/services/generative_jobs_runner.py:121 - `spec_payload = json.loads((job_dir / "spec.json").read_text())`
- kayakgen/services/generative_jobs_fork.py:92 - `source_spec = json.loads(spec_path.read_text())`
- kayakgen/services/evaluation.py:318, 363 - `manifest_path.read_text()` and `report_path.read_text()` (no encoding)
- kayakgen/services/generative_jobs.py:300, 319, 761, 1291 - multiple read_text() calls without encoding
- Python pathlib docs: "If encoding is not specified, locale.getpreferredencoding(False) is used instead"
- This is locale-dependent and may differ from UTF-8 on Windows or non-UTF-8 systems
impact: On systems deployed with non-UTF-8 locale encoding (Windows-1252, ASCII), JSON files and spec records containing non-ASCII characters will fail to read or write with encoding errors. Downstream CFD job loading, generative job recovery, and mesh-package parsing will silently skip or corrupt non-ASCII data depending on the locale.
recommended_action: Add explicit `encoding="utf-8"` to ALL `Path.read_text()` and `Path.write_text()` calls across the services modules. This is a bulk edit affecting ~20 call sites in cfd_jobs.py, evaluation.py, generative_jobs.py, generative_jobs_fork.py, generative_jobs_runner.py, build_export.py, calibration_artifacts.py. Consider creating a service helper: `def load_json_file(path: Path) -> dict` that centralizes the encoding parameter.
follow_up: new striatum workflow

### BUG-041: Race condition in FilesystemArtifactStore._put_bytes write atomicity

severity: medium
category: concurrency
status: open
surface: kayakgen/services/
discovered: 2026-05-29 tick-17
claim: The `FilesystemArtifactStore._put_bytes()` method at lines 648-650 uses a check-then-act pattern without file-locking: `if not store_path.exists(): ... store_path.write_bytes(data)`. If two concurrent `put_*()` calls for the same artifact hash race, both threads will see the file doesn't exist, and both will attempt to write simultaneously. On Windows or networked filesystems (NFS, SMB), concurrent writes can result in data loss, corruption, or the store containing a partial artifact.
evidence:
- kayakgen/services/artifact_store.py:648-650 - TOCTOU race: exists-check followed by write without synchronization
- kayakgen/services/artifact_store.py:769-770 - similar pattern in `_resolve_artifact()` during recovery
- RFC 0049 does not document concurrency guarantees or per-artifact locks
- No mutex or file-locking mechanism protects the store_path write
- Two concurrent sweep/search workers calling `put_json()` with the same hull candidate could trigger this
impact: In multi-worker sweep/search scenarios (RFC 0057 generative jobs), if two workers produce identical candidates and simultaneously try to store their results, the artifact store may end up with incomplete, corrupted, or partially-written files. Downstream reads will fail with JSON decode errors or silent data corruption. The store's content-addressed design masks which worker's data was lost.
recommended_action: Replace the exists-check with an atomic write pattern: use `open(store_path, 'wb', os.O_EXCL | os.O_CREAT)` on POSIX (or `os.open()` equivalent) to ensure only one writer succeeds atomically. On platforms without O_EXCL support, use a tempfile + rename pattern: write to `store_path.with_suffix('.tmp.<random>')`, then `os.replace(tmp_path, store_path)` (atomic on all platforms). Document the concurrency guarantee in the class docstring.
follow_up: new striatum workflow

### BUG-042: BuildExportSpec lacks bounds validation on n_stations

severity: medium
category: implementation_gap
status: open
surface: kayakgen/services/
discovered: 2026-05-29 tick-17
claim: The `BuildExportSpec` dataclass at line 43-53 of `build_export.py` accepts `n_stations: int` with no bounds validation. A caller (including the CLI layer after BUG-009 fix) can pass `n_stations=0` or negative values, which will propagate to `_station_xs()` at line 93 where the check `if n_stations < 2` catches only zero/one, but not negative. Additionally, there is no upper bound, so `n_stations=1000000` can be passed and cause `np.linspace()` to allocate gigabytes of memory per hull section cut. The service layer should validate at entry time, not expect the CLI to be perfect.
evidence:
- kayakgen/services/build_export.py:43-53 - `BuildExportSpec` has no field_validator or __post_init__ for n_stations
- kayakgen/services/build_export.py:91-94 - validation only checks `n_stations < 2`, rejecting 0 and 1, but allows negatives silently
- kayakgen/services/build_export.py:560-569 - write_build_export passes spec.n_stations directly to all writers
- kayakgen/model/geometry.py (lofted geometry) - no clamping or early rejection of extreme n_stations values
- Default is 32; practical limit for builder exporting is likely 100-1000; no documented bounds
impact: A malicious caller or buggy upstream code can pass `BuildExportSpec(n_stations=-100)` which propagates silently, or `n_stations=1e9` which exhausts memory and hangs the process without clear error messaging. The service should refuse obviously-invalid values upfront.
recommended_action: Convert `BuildExportSpec` to a Pydantic `BaseModel` (not a plain dataclass) and add field validation: `n_stations: int = Field(default=DEFAULT_N_STATIONS, ge=2, le=1000)`. Document the bounds in the class docstring referencing RFC 0051 acceptance criteria. Add a regression test passing out-of-bounds values and asserting they are rejected at construction time.
follow_up: new striatum workflow

### BUG-043: FreeEquilibriumPoint / FreeEquilibriumTrace lack NaN/Infinity validators

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/stability/
discovered: 2026-05-29 tick-18
claim: `FreeEquilibriumPoint` float fields (`theta_deg`, `trim_deg`, `heave_m`) and `FreeEquilibriumTrace.points` accept NaN / inf values without rejection. A fixture with NaN values serialises to JSON `null` and round-trips silently, corrupting downstream GZ comparisons.
evidence:
- kayakgen/eval/stability/measured_fixture.py:149-176 — no `isfinite()` checks on theta_deg / trim_deg / heave_m
- Contrast: GZCurve validators in kayakgen/eval/contract.py reject non-finite values
impact: Asymmetric validator coverage extending BUG-023's pattern (which found the same gap on ResistanceCurve / Hydrostatics). A NaN-bearing fixture passes acceptance, then propagates corrupt data into the accepted-fit registry; downstream consumers compute on NaN and produce nonsensical results.
recommended_action: Add `field_validator` or `model_validator(mode="after")` on `FreeEquilibriumPoint` that rejects non-finite values for `theta_deg`, `trim_deg`, `heave_m`. Bundle with BUG-023 and BUG-045 into a single sweep adding finite-value validators across all RFC 0056/0058 numeric schemas.
follow_up: new striatum workflow (bundle with BUG-023 / BUG-045)

### BUG-044: FreeEquilibriumTrace.points lacks monotonicity validator

severity: high
category: implementation_gap
status: open
surface: kayakgen/eval/stability/
discovered: 2026-05-29 tick-18
claim: `FreeEquilibriumTrace.points` is `Field(min_length=3)` with no model_validator enforcing that `points[].theta_deg` is monotonically increasing. RFC 0056's docstring says the trace "varies smoothly with theta_deg", but the schema admits any order — including duplicates and decreasing sequences.
evidence:
- kayakgen/eval/stability/measured_fixture.py:159-176 — `class FreeEquilibriumTrace` body has no @model_validator
- kayakgen/eval/stability/measured_fixture.py:173 — `points: list[FreeEquilibriumPoint] = Field(min_length=3)` (only length constraint)
- Parent thread verified by reading the full class body
impact: A malformed or maliciously-constructed fixture with points in random order (0°, 90°, 45°) passes validation. Downstream consumers that iterate `trace.points` assuming monotonic order produce wrong GZ comparisons. The `smoothness_failures: list[str]` field is filled by an external check, not by the validator — so a fixture can have an empty `smoothness_failures` list AND non-monotonic points simultaneously, hiding the violation.
recommended_action: Add a `model_validator(mode="after")` on `FreeEquilibriumTrace` that walks `self.points` and raises `ValueError` if any adjacent pair has `points[i+1].theta_deg <= points[i].theta_deg`. Add a regression test passing a non-monotonic fixture and asserting refusal.
follow_up: new striatum workflow

### BUG-045: MeasuredStabilityRow lacks NaN/Infinity validators

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/stability/
discovered: 2026-05-29 tick-18
claim: `MeasuredStabilityRow` float fields (`theta_deg`, `gz_m`) accept NaN / inf. Same shape as BUG-043 + BUG-023; this is the third schema in the project with this gap.
evidence:
- kayakgen/eval/stability/measured_fixture.py:203-210 — no `isfinite()` checks
impact: NaN values round-trip through JSON as `null`, then downstream GZ-comparison math produces NaN — silently corrupting the acceptance verdict.
recommended_action: Bundle with BUG-023 + BUG-043 into a single sweep adding `field_validator` for `isfinite` across all RFC 0056/0058 numeric schemas.
follow_up: new striatum workflow (bundle with BUG-023 + BUG-043)

### BUG-046: StabilityFitMetrics threshold validators use bare-float comparison

severity: medium
category: math
status: open
surface: kayakgen/eval/stability/
discovered: 2026-05-29 tick-18
claim: `StabilityFitMetrics` float fields use `ge` field constraints but the strict-threshold validator in `accepted_fit.py:157` compares with bare `>` operators on bare floats. Combined with BUG-043/045, a near-threshold metric can flip pass/fail based on float-precision noise.
evidence:
- kayakgen/eval/stability/measured_fixture.py:82-91 — `StabilityFitMetrics` only has `ge` field constraints, no finite-value validator
- kayakgen/eval/stability/accepted_fit.py:157 — `>` comparison without tolerance
impact: A fit-metric value at exactly the threshold (e.g., RMSE=0.05 with a `<0.05` rule) can flip pass/fail depending on float-precision in the upstream computation. Same float-equality pattern family as BUG-015/019/027/032/047 — this is the 5th instance.
recommended_action: Replace bare-float comparisons with `math.isclose(a, b, abs_tol=PROJECT_TOLERANCE)` or document an explicit precision contract (e.g., "thresholds are exclusive bounds; metric values must be lower by at least `eps=1e-9`").
follow_up: new striatum workflow (bundle with the float-equality pattern fix)

### BUG-047: LoadingConfiguration._paddler_mass_matches_state uses float equality

severity: medium
category: math
status: open
surface: kayakgen/eval/stability/
discovered: 2026-05-29 tick-18
claim: `LoadingConfiguration._paddler_mass_matches_state` at line 103 uses `self.paddler_mass_kg != 0.0` — exact float equality on a JSON-round-trippable field. A paddler mass perturbed by float precision (e.g., 1e-12 after slider rounding) fails the `paddler_state == "absent"` check despite intending zero.
evidence:
- kayakgen/eval/stability/measured_fixture.py:103 — `if self.paddler_state == "absent" and self.paddler_mass_kg != 0.0:`
- Parent thread verified directly
impact: Same family as BUG-015 / BUG-019 / BUG-027 / BUG-032 / BUG-046 — 6th float-equality instance. A LoadingConfiguration with `paddler_state="absent"` and `paddler_mass_kg=1e-12` raises a confusing error: "paddler_state='absent' requires paddler_mass_kg=0; got paddler_mass_kg=1e-12".
recommended_action: Replace with `if self.paddler_state == "absent" and abs(self.paddler_mass_kg) > PROJECT_TOLERANCE:`. Document the tolerance in a project-wide constants module (now a strong candidate for its own RFC slice given 6 instances of the pattern).
follow_up: new striatum workflow (bundle into the float-equality sweep)

### BUG-048: StabilityFitRecord.accepted_at has no range validation

severity: low
category: implementation_gap
status: open
surface: kayakgen/eval/stability/
discovered: 2026-05-29 tick-18
claim: `StabilityFitRecord.accepted_at` timestamp validator at accepted_fit.py:120/138 checks `is None` but not range bounds. A future timestamp (year 3000) or a timestamp before the fixture's data collection passes validation.
evidence:
- kayakgen/eval/stability/accepted_fit.py:120, 138 — None-check only
impact: Audit trail integrity. A fit accepted with `accepted_at=year-3000` looks legitimate to downstream consumers reading the record. Low impact today (no current operator would construct this maliciously), but documents an audit-trail gap.
recommended_action: Add range validation: reject timestamps in the future or before a project-epoch constant (e.g., 2025-01-01). Document the epoch in the class docstring.
follow_up: docs fix or new striatum workflow (low priority)

### BUG-049: Edinburgh extractor uses hardcoded column indices instead of header-based lookup

severity: high
category: implementation_gap
status: open
surface: kayakgen/eval/calibration/
discovered: 2026-05-29 tick-19
claim: The Edinburgh DataShare extractor at `kayakgen/eval/calibration/extractors/edinburgh_datashare_pacific_canoe.py:274-312` iterates over spreadsheet rows and extracts values by hardcoded column index (raw[0]=Day, raw[1]=Model, raw[5]=Stbd Drag, etc.) without reading or validating the header row. If a workbook maintainer renames or reorders columns, the extractor silently pulls wrong data into the normalized output without detecting the schema drift.
evidence:
- kayakgen/eval/calibration/extractors/edinburgh_datashare_pacific_canoe.py:117-140 — WORKBOOK_HEADER_ROW and EXPECTED_SOURCE_COLUMNS are defined but never used in the extract() function
- kayakgen/eval/calibration/extractors/edinburgh_datashare_pacific_canoe.py:274-312 — no call to read header row; iteration uses iter_rows(min_row=WORKBOOK_DATA_START_ROW, ...) and hardcoded indices raw[0], raw[1], raw[3]...raw[13]
- A hypothetical workbook edit swapping "Stbd Drag Force" and "Port Drag Force" columns would result in stbd and port values being reversed; the extractor would not detect this
- tests/test_calibration.py:515-535 — test validates output schema keys but not that the correct values are extracted from the correct columns
impact: Silent data corruption. An operator could receive incorrect extracted rows (e.g., starboard drag confused with port drag, or speeds confused with yaw angles) without any error or warning. The normalized output would pass validation (keys present, types correct), and downstream resistance-fit code would train on the corrupted data, producing a calibration fixture with systematically wrong drag coefficients.
recommended_action: Refactor extract() to (1) read the header row at WORKBOOK_HEADER_ROW, (2) validate that it matches EXPECTED_SOURCE_COLUMNS in order, and (3) use the validated column indices to extract row values. Raise ValueError with a structured error code (e.g., 'header_mismatch') if the header does not match. Add a regression test that creates a workbook with reordered columns and verifies the extractor raises an error (or detects the drift).
follow_up: new striatum workflow

### BUG-050: Edinburgh extractor silently converts NaN / missing cells to 0.0

severity: high
category: implementation_gap
status: open
surface: kayakgen/eval/calibration/
discovered: 2026-05-29 tick-19
claim: The _coerce_float() helper at lines 200-212 of `edinburgh_datashare_pacific_canoe.py` silently converts NaN and None to 0.0. When openpyxl parses a missing or NaN cell in a drag or force column, the extractor emits a zero value instead of rejecting the row or raising an error. This allows incomplete data rows (e.g., a row missing the Stbd Drag Force value) to be treated as zero-force measurements, silently corrupting the calibration dataset.
evidence:
- kayakgen/eval/calibration/extractors/edinburgh_datashare_pacific_canoe.py:200-212 — `if value is None: return 0.0` and `if math.isnan(value): return 0.0`
- openpyxl returns None or NaN for missing/empty cells; _coerce_float converts both to 0.0 without raising an error
- Rows with missing drag values are not filtered (unlike rows with missing Day/Model/Test); they pass through as zero-drag measurements
- Impact: A partially-populated row in the workbook (e.g., a measurement with speed and yaw but no recorded drag) becomes a valid zero-drag point in the calibration data
impact: Data integrity and calibration accuracy. A row with an accidentally-blank drag cell becomes a zero-drag measurement, biasing the resistance fit. This is especially damaging for validation_fixture promotion, where the source credibility is supposed to be high and downstream consumers expect complete, well-formed measurements.
recommended_action: Change _coerce_float() to raise ValueError for None and NaN inputs (or return None to mark invalid rows for later filtering). Alternatively, filter rows with any NaN/None force fields before appending to the output. Add a row-level validator that checks for missing critical fields (speed, total_drag, heave, pitch, velocity) and skips the row with a warning if any are NaN/None.
follow_up: new striatum workflow

### BUG-051: TankTestRun and AcceptedFitRecord lack NaN/Infinity validators on numeric fields

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/calibration/
discovered: 2026-05-29 tick-19
claim: The `TankTestRun` (campaigns.py:59-73) and `AcceptedFitRecord` (campaigns.py:138-160) models declare float and list[float] fields (total_drag_n, drag_uncertainty_n, fit_value, holdout_rms_n, residuals) with only basic constraints (e.g., `ge=0` on speed_ms) but no validators to reject NaN or Infinity values. A deserialized JSON record with `{"total_drag_n": null}` or `{"fit_value": NaN}` passes Pydantic validation and propagates into downstream calculations. This contrasts with `ResistanceCurve` and `Hydrostatics` in kayakgen/eval/contract.py, which lack the same validators (BUG-023).
evidence:
- kayakgen/eval/calibration/campaigns.py:59-73 — TankTestRun has `total_drag_n: float`, `drag_uncertainty_n: float | None`, no validator
- kayakgen/eval/calibration/campaigns.py:138-160 — AcceptedFitRecord has `fit_value: float`, `holdout_rms_n: float`, `residuals: list[tuple[float, float]]`, no validator
- kayakgen/eval/contract.py:196-200 — GZCurve enforces `_curve_values_must_be_finite()` as a model_validator; TankTestRun / AcceptedFitRecord do not
- `evaluate_fit_against_threshold()` at campaigns.py:335-382 compares fit_value numerically without checking if fit_value is finite; NaN comparisons would silently fail
impact: Silent data corruption and incorrect validation. An AcceptedFitRecord with NaN in fit_value would serialize to JSON with `"fit_value": null`, deserialize successfully, and propagate through `evaluate_fit_against_threshold()` where NaN comparisons produce false results (NaN > x is always false). This violates the RFC 0054 contract that AcceptedFitRecord is immutable and trustworthy.
recommended_action: Add @field_validator decorators to TankTestRun and AcceptedFitRecord to reject NaN/Infinity on all float fields. Use the same pattern as GZCurve in contract.py. For optional float fields (drag_uncertainty_n), allow None but reject NaN/Infinity if the value is non-None.
follow_up: new striatum workflow (bundle with BUG-023 remediation)

### BUG-052: ResistanceSourceReviewPacket accepts empty accepted_uses for fixture verdicts

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/calibration/
discovered: 2026-05-29 tick-19
claim: The `accepted_uses` field at `kayakgen/eval/calibration/__init__.py:249` is declared with `Field(default_factory=list)`, making it optional and defaulting to an empty list. The validator `_review_verdict_controls_promotion_metadata()` enforces many cross-field constraints for `validation_fixture` and `calibration_fixture` verdicts (e.g., fixture_id, fixture_version, accepted_fit_ref), but does not enforce that `accepted_uses` is non-empty. An operator can construct a validation_fixture packet with `accepted_uses=[]`, violating the implicit RFC 0042 contract that a fixture verdict names the intended use(s) (e.g., "validation_only", "calibration_candidate").
evidence:
- kayakgen/eval/calibration/__init__.py:249 — `accepted_uses: list[str] = Field(default_factory=list)` (optional, defaults to [])
- kayakgen/eval/calibration/__init__.py:314-392 — _review_verdict_controls_promotion_metadata() enforces fixture_id, fixture_version, accepted_fit_ref but never checks `if not self.accepted_uses`
- kayakgen/eval/calibration/__init__.py:711 — default_resistance_source_review_packets() sets `accepted_uses=["validation_only"]` for the Edinburgh packet, showing the intent
- No test in test_calibration.py validates that accepted_uses is required for fixtures
impact: Incomplete promotion records. A fixture packet with empty accepted_uses leaves downstream consumers without guidance on the intended use case, violating the RFC's goal of explicit, documented promotion rationale.
recommended_action: Add a check in `_review_verdict_controls_promotion_metadata()` that requires `accepted_uses` to be non-empty when `review_verdict` is "validation_fixture" or "calibration_fixture_candidate" or "calibration_fixture". Raise ValueError if `self.review_verdict in {"validation_fixture", "calibration_fixture_candidate", "calibration_fixture"} and not self.accepted_uses`.
follow_up: new striatum workflow

### BUG-053: Calibration surface verified clean beyond tick 5 findings (info, null finding)

severity: info
category: claim_gate
status: open
surface: kayakgen/eval/calibration/
discovered: 2026-05-29 tick-19
claim: Tick 19 re-searched the calibration surface with focus on extractors, NaN/Infinity validators, cross-module integration, float-equality, and validator gaps. Beyond the three bugs already recorded from tick 5 (BUG-011: empty-reasons gap on fixtures, BUG-012: path traversal in accepted_fit_ref resolution, BUG-013: unchecked non_promotion_reasons tokens), tick 19 found four new bugs (BUG-049 through BUG-052): hardcoded column indices in the Edinburgh extractor, silent NaN-to-0.0 conversion in the extractor, missing NaN/Infinity validators on TankTestRun / AcceptedFitRecord numeric fields, and missing empty-acceptance-uses validation. The `_validate_accepted_fit_ref_on_disk()` path-traversal fix (BUG-012) is the same family as BUG-005/007; extractor gaps (BUG-049/050) establish a new vendor-specific pattern. All validator gaps follow the precedent from tick 18's stability surface (BUG-043/044/045) and earlier float-equality instances (BUG-015/019/027/046). The surface should NOT be marked settled; four new actionable bugs warrant a third search pass.
evidence:
- BUG-049: hardcoded column indices in extractor
- BUG-050: silent NaN conversion in extractor
- BUG-051: missing NaN/Infinity validators on campaign/fit models
- BUG-052: empty accepted_uses allowed for fixture verdicts
impact: Multiple pathways to silent data corruption in the calibration pipeline: wrong columns extracted, missing data treated as zero, NaN values accepted into immutable fit records, and incomplete promotion packets. Not settled.
recommended_action: Implement the fixes for BUG-049 through BUG-052 before tick 19's successor. This is the deepest audit of the calibration module to date and surfaces previously-hidden extractor and validator vulnerabilities.
follow_up: new striatum workflow (for each of BUG-049/050/051/052)

### BUG-054: Exact float equality for bow_rake/stern_rake plumb detection in LoftedHullGeometry

severity: medium
category: math
status: open
surface: kayakgen/model/
discovered: 2026-05-29 tick-20
claim: Lines 157-159 of `kayakgen/model/geometry.py` use exact float equality `self.hull.bow_rake == 0.0` and `self.hull.stern_rake == 0.0` to detect plumb endpoints, but these values can be round-tripped through JSON serialisation, introducing IEEE 754 perturbations that defeat the exact comparison. This is a sibling to BUG-015 (distribution_v2 rake checks) and BUG-019 (generated_body.py plumb detection), indicating a systematic float-equality pattern on rake values across the geometry layer.
evidence:
- kayakgen/model/geometry.py:155-160 — `_is_exact_plumb_endpoint()` method uses `self.hull.bow_rake == 0.0` and `self.hull.stern_rake == 0.0` for exact plumb detection
- kayakgen/model/hull.py:45-59 — `bow_rake` and `stern_rake` are `float` fields in `[0, 1]` that round-trip through JSON
- BUG-015 (tick-6) established the pattern: distribution_v2 rake checks reject valid hulls after JSON round-trip
- BUG-019 (tick-9) established the same issue in `generated_body.py:132-133` for closed-body plumb detection
- `section_for_closed_body()` at geometry.py:253-266 calls `_is_exact_plumb_endpoint()` to determine whether to snap the section to exact plumb-stem closure
impact: A hull with `bow_rake = 0.0` or `stern_rake = 0.0` that is serialized to JSON and deserialized may see the rake perturbed to -1e-16 or 1e-16, causing `_is_exact_plumb_endpoint()` to return False when it should return True. The generated section will not snap to the plumb-stem ring, violating the exact-plumb-endpoint closure contract that RFC 0028 promises.
recommended_action: Replace exact float equality with `math.isclose(self.hull.bow_rake, 0.0)` and `math.isclose(self.hull.stern_rake, 0.0)` at lines 157 and 159. Use a tolerance consistent with the model's documented precision (suggest `rel_tol=1e-9, abs_tol=1e-12` to match RFC 0028 tolerance in geometry.py:156 for x position). Add a regression test that round-trips a hull with plumb endpoints through JSON and asserts the closed-body geometry honours the plumb-endpoint closure.
follow_up: new striatum workflow (coordinate with BUG-015 and BUG-019 fixes to apply the same tolerance pattern systematically)

### BUG-055: UniformDistribution and PolynomialDistribution lack NaN/Infinity validators on value/coefficients

severity: medium
category: implementation_gap
status: open
surface: kayakgen/model/
discovered: 2026-05-29 tick-20
claim: The `UniformDistribution` (distribution_v2.py:42-56) and `PolynomialDistribution` (distribution_v2.py:59-77) models declare float and list[float] fields (`value` and `coefficients`) without validators to reject NaN or Infinity values. A maliciously crafted or corrupted JSON file can deserialize a distribution with `{"kind":"uniform","value":NaN}` or `{"kind":"polynomial","coefficients":[1.0,NaN]}` that passes Pydantic validation. The `.sample()` methods will then propagate NaN through the loft calculations, producing malformed geometry with NaN section points that silently corrupt downstream STL / CFD workflows.
evidence:
- kayakgen/model/distribution_v2.py:52 — `value: float` with no validator
- kayakgen/model/distribution_v2.py:70 — `coefficients: list[float] = Field(min_length=1)` with no validator
- kayakgen/model/distribution_v2.py:54-56 — `sample()` returns `np.full_like(xi_arr, float(self.value), dtype=float)` without checking if `self.value` is finite
- kayakgen/model/distribution_v2.py:72-77 — `sample()` loops over `self.coefficients` and accumulates results without checking if coefficients contain NaN/Infinity
- BUG-023 (tick-10) established precedent: ResistanceCurve and Hydrostatics models lack NaN validators, representing a systematic gap
impact: A distribution-v2 hull with NaN coefficients will produce malformed geometry sections with NaN coordinates. The downstream closed-body builder, CFD meshing, and hydrostatics integration will silently propagate NaN, producing wrong results that a downstream consumer might accept if they don't check for NaN in the mesh array.
recommended_action: Add @field_validator decorators to UniformDistribution and PolynomialDistribution to reject NaN/Infinity. For `value`, reject if `not math.isfinite(value)`. For `coefficients`, reject if `any(not math.isfinite(c) for c in coefficients)`. Use the same pattern as GZCurve's `_curve_values_must_be_finite()` in contract.py. Raise ValueError with a clear message on validation failure.
follow_up: new striatum workflow (bundle with BUG-023 remediation as a systematic NaN-validator sweep)

### BUG-056: DistributionV2Spec distribution fields lack NaN/Infinity validators on their values

severity: medium
category: implementation_gap
status: open
surface: kayakgen/model/
discovered: 2026-05-29 tick-20
claim: The `DistributionV2Spec` (distribution_v2.py:178-218) declares five mandatory `LongitudinalDistribution` fields (`waterline_half_breadth`, `draft_profile`, `section_area_curve`, `deck_freeboard`, `rocker`) without validators to ensure the contained distribution values are finite. Since `LongitudinalDistribution` is a discriminated union of `UniformDistribution`, `PolynomialDistribution`, and `KeyPointsDistribution` (each with numeric fields), and these inner types lack NaN validators (see BUG-055), a malformed DistributionV2Spec can carry NaN in any of the five distributions. Additionally, the scalar fields `deadrise_deg` and `chine_radius_m` (which can be `float` or `LongitudinalDistribution`) are not validated for finite values. This represents a multi-level validator gap that compounds the BUG-055 gap.
evidence:
- kayakgen/model/distribution_v2.py:202-206 — five mandatory `LongitudinalDistribution` fields with no validator
- kayakgen/model/distribution_v2.py:214-215 — `deadrise_deg: Union[float, LongitudinalDistribution] = 0.0` and `chine_radius_m: Union[float, LongitudinalDistribution] = 0.02` without finite-value constraints
- kayakgen/model/distribution_v2.py:216 — `bow_flare_deg: float = 0.0` without validator (scalar float field in a spec)
- kayakgen/model/distribution_v2.py:208-211 — rocker_bow_m, rocker_stern_m, lcb_target_frac, max_beam_position_frac carry `ge=0` and range constraints but no NaN checks
- DistributionV2Geometry consumes spec fields directly in `_half_breadth_at()`, `_draft_at()`, `_deck_height_at()`, `_rocker_at()`, `_deadrise_rad_at()`, `_chine_radius_at()` without finite-value guards
impact: A DistributionV2Spec with NaN in any distribution will produce malformed geometry sections. The geometry construction code does not guard against NaN, so NaN coordinates propagate into the mesh, STL, and CFD workflows, silently corrupting results.
recommended_action: Add @model_validator(mode="after") to DistributionV2Spec that recursively checks all distribution values for finiteness. For scalar fields (`deadrise_deg`, `chine_radius_m`, `bow_flare_deg`, rocker_bow_m, rocker_stern_m), check `math.isfinite()`. For discriminated distributions, assert that the underlying values (via `.sample(0.0)`) return finite arrays or define a helper validator on the LongitudinalDistribution union itself. Raise ValueError if any field contains NaN/Infinity.
follow_up: new striatum workflow (part of systematic BUG-055/056 NaN-validator sweep)

### BUG-057: DesignAdvisory l_over_bwl and displaced_mass_kg lack NaN/Infinity validators

severity: medium
category: implementation_gap
status: open
surface: kayakgen/model/
discovered: 2026-05-29 tick-20
claim: The `DesignAdvisory` dataclass (advisory.py:32-41) carries fields `l_over_bwl: float`, `cp: float`, and `displaced_mass_kg: float | None` without validators to reject NaN or Infinity. These are derived metrics computed from `design_advisory()` (advisory.py:44-78) and reflect the upstream Hull validation state. However, if downstream code mutates a Hull or if a deserialization path bypasses validators, `DesignAdvisory` can be constructed with NaN values. The `design_validity` report (validity.py:75-99) embedded in the advisory also carries float fields (`value`, `bounds.min`, `bounds.max`) via `DesignValidityFinding` that lack NaN guards. These advisories are surfaced to the UI in `validity_badge_title_for()` (tick-12's BUG-029) and other advisory renderers, where NaN values produce malformed display text.
evidence:
- kayakgen/model/advisory.py:32-41 — `DesignAdvisory` dataclass has `l_over_bwl: float`, `cp: float`, `displaced_mass_kg: float | None` with no validator
- kayakgen/model/advisory.py:44-78 — `design_advisory()` computes `l_over_bwl = hull.length_m / beam_wl` and optional `displaced_mass_kg` without asserting non-NaN results
- kayakgen/model/validity.py:58-73 — `DesignValidityFinding` carries `parameters` tuple but also allows extra fields via `extra="allow"`, including numeric `value` and `bounds` dicts that are unvalidated
- kayakgen/model/validity.py:236-258 — `_finding()` helper constructs findings with arbitrary `**extra` kwargs; if caller passes `value=float('nan')`, it passes through
- tick-12's BUG-029 (ui/web/app.py:349-350) demonstrated that NaN in a badge string causes incorrect tooltip text
impact: Advisory UI components render NaN values, creating confusing messages for operators. A design advisory tooltip might read "L/B_wl is nan" instead of a valid ratio, misleading the operator about the design's classification (touring vs. surfski vs. custom).
recommended_action: Add a `@model_validator(mode="after")` to `DesignAdvisory` that checks `math.isfinite(self.l_over_bwl)` and `math.isfinite(self.cp)`. For optional `displaced_mass_kg`, check `self.displaced_mass_kg is None or math.isfinite(self.displaced_mass_kg)`. Add a similar validator to `DesignValidityFinding` or to the `evaluate_design_validity()` and `_finding()` helper to guard against NaN in the `value` and `bounds` fields. Raise ValueError with a clear message if any metric is non-finite, rather than silently accepting and rendering NaN in the UI.
follow_up: new striatum workflow


### BUG-058: NaN/Infinity not validated on CheckMeshSummary float fields

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/evidence/
discovered: 2026-05-29 tick-22 (re-search 2)
claim: CheckMeshSummary (lines 106-123 of snappy_hex_mesh.py) accepts float fields `max_non_orthogonality_deg`, `max_skewness`, `aspect_ratio_max` with only `ge=0.0` constraints and no finite-value validators. These fields can be deserialized with NaN or Infinity from JSON, corrupting downstream mesh diagnostics that assume valid numeric values. This mirrors BUG-023 (ResistanceCurve/Hydrostatics) and BUG-048 (stability metrics).
evidence:
- kayakgen/eval/snappy_hex_mesh.py:106-123 - CheckMeshSummary fields lack finite-value validators
- kayakgen/eval/snappy_hex_mesh.py:120-122 - `max_non_orthogonality_deg`, `max_skewness`, `aspect_ratio_max` have only `ge=0.0`, not `finite=True`
- kayakgen/eval/snappy_hex_mesh.py:557-558 - downstream code embeds these floats in VolumeMeshDiagnostic without validation
- kayakgen/eval/contract.py:196-200 - GZCurve enforces `_curve_values_must_be_finite()`, showing the pattern is known
- Tests may construct CheckMeshSummary directly with NaN and see it round-trip to null in JSON serialization
impact: A mesh evidence record with NaN in `max_skewness` will serialize to JSON with null, deserialize back to NaN, and propagate to the VolumeMeshDiagnostic. Downstream CFD solvers consuming the diagnostic may misinterpret NaN as a sentinel value or crash on unexpected non-finite numeric fields.
recommended_action: Add `field_validator` to CheckMeshSummary for all float fields to reject NaN/Infinity using `math.isfinite()` or Pydantic's `finite=True` constraint. Match the pattern in GZCurve at line 196-200.
follow_up: new striatum workflow

### BUG-059: Hash comparison lacks case normalization and format validation

severity: high
category: security
status: open
surface: kayakgen/eval/evidence/
discovered: 2026-05-29 tick-22 (re-search 2)
claim: The `bind_evidence_to_mesh_package` function at line 692 compares `evidence.body_ref_hash` directly against `closed_body_hash` using `!=` without normalizing case or validating the hex format. An evidence record with uppercase hex digits (e.g., `"A1B2C3..."`) will not match a lowercase hash (e.g., `"a1b2c3..."`), causing valid evidence to be rejected. Additionally, hashes with leading/trailing whitespace (e.g., `"  a1b2c3... "`from JSON parsing or manual entry) will fail the comparison silently.
evidence:
- kayakgen/eval/snappy_hex_mesh.py:692 - `evidence.body_ref_hash != closed_body_hash` (direct string comparison, no case normalization)
- kayakgen/eval/snappy_hex_mesh.py:719 - artifact checksum comparison `actual.get(name) != recorded.get(name)` also lacks normalization
- No `.lower()` or `.strip()` applied to hash values before comparison
- SHA256 hex digests are produced by `hashlib.sha256().hexdigest()` (lowercase) per line 358, but evidence JSON may come from external sources with mixed case
impact: An evidence record with uppercase or whitespace-padded hash values will be rejected even if the hash is cryptographically correct, blocking legitimate evidence binding. An attacker (or buggy upstream) could craft evidence with uppercase hashes to cause false negatives on hash validation.
recommended_action: Normalize hashes before comparison: `evidence.body_ref_hash.lower().strip() != closed_body_hash.lower().strip()`. Additionally, validate hash format (64 hex digits) at evidence deserialization time using a Pydantic field_validator that checks `re.match(r"^[a-fA-F0-9]{64}$", value)` and rejects invalid formats.
follow_up: new striatum workflow

### BUG-060: Empty artifact_checksums allowed in evidence_recorded state

severity: medium
category: claim_gate
status: open
surface: kayakgen/eval/evidence/
discovered: 2026-05-29 tick-22 (re-search 2)
claim: The evidence validator at lines 152-175 allows `dispatch_state == "evidence_recorded"` even when `artifact_checksums` is an empty dict `{}`. The blocker check at line 443 flags empty checksums, but the conditional at line 401 only sets `dispatch_state = "evidence_recorded"` when `not blockers`, creating an inconsistency: an operator can construct SnappyHexMeshEvidence with empty `artifact_checksums` and explicitly set `dispatch_state = "evidence_recorded"` manually in JSON, and the validator will accept it if no other blockers are present.
evidence:
- kayakgen/eval/snappy_hex_mesh.py:147 - `artifact_checksums: dict[str, str] = Field(default_factory=dict)` allows empty dict
- kayakgen/eval/snappy_hex_mesh.py:443-444 - `if not artifact_checksums: missing.append("missing_artifact_checksums")`
- kayakgen/eval/snappy_hex_mesh.py:152-175 - validator only checks gates when `dispatch_state != "evidence_recorded"` (line 154), so manually-set `evidence_recorded` state bypasses the blocker list check
- RFC 0045 requires "artifact checksums present" as a binding gate; empty dict should always block evidence_recorded state
impact: An operator can construct evidence JSON with `{"dispatch_state": "evidence_recorded", "artifact_checksums": {}, ...}` and it will pass validation, allowing incomplete evidence to propagate to downstream code expecting valid artifact hashes. The bind_evidence_to_mesh_package function assumes artifact_checksums is non-empty (line 702), and an empty dict will cause downstream logic failures.
recommended_action: Add a model_validator that checks: `if self.dispatch_state == "evidence_recorded" and not self.artifact_checksums: raise ValueError("evidence_recorded state requires non-empty artifact_checksums")`. Enforce this at deserialization time so manually-constructed JSON records cannot bypass the gate.
follow_up: new striatum workflow

### BUG-061: Hash whitespace vulnerability in artifact checksum comparison

severity: medium
category: security
status: open
surface: kayakgen/eval/evidence/
discovered: 2026-05-29 tick-22 (re-search 2)
claim: Line 719 of `bind_evidence_to_mesh_package` compares artifact checksums without stripping whitespace: `actual.get(name) != recorded.get(name)`. If evidence JSON is hand-edited or if upstream hash computation inadvertently includes leading/trailing whitespace (e.g., from a malformed JSON file with formatting), the comparison will fail even though the hash is correct. This is the same whitespace-handling gap as BUG-059 but applied to artifact_checksums dict values rather than body_ref_hash.
evidence:
- kayakgen/eval/snappy_hex_mesh.py:719 - checksum comparison without `.strip()` or `.lower()`
- kayakgen/eval/cfd/openfoam_v2512_interfoam/evidence.py:113 - checksums produced by `sha256_of_path()` (line 37) which correctly produces lowercase hex with no whitespace
- JSON round-trip through a human-edited file can introduce trailing/leading spaces
impact: Artifact checksums with whitespace will fail validation and block evidence binding, even though the underlying artifact is correct. An operator debugging a failed checksum comparison will see a cryptic error message and have no easy way to determine if the issue is whitespace or a real hash mismatch.
recommended_action: Normalize both actual and recorded hashes before comparison: `actual.get(name, "").lower().strip() != recorded.get(name, "").lower().strip()`. Apply the same normalization pattern introduced in BUG-059.
follow_up: new striatum workflow

### BUG-062: Patch name and marker allow special characters without sanitization

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/evidence/
discovered: 2026-05-29 tick-22 (re-search 2)
claim: SnappyHexMeshPatchEntry fields `name` and `marker` (lines 92-93) carry only `min_length=1` constraints and no character-set validation. These fields are extracted from polyMesh boundary files by `read_poly_mesh_patches()` and can contain arbitrary characters including newlines, quotes, and special characters. When embedded in OpenFOAM case files or downstream diagnostic serialization, unvalidated patch names can cause injection vulnerabilities or confusing error messages.
evidence:
- kayakgen/eval/snappy_hex_mesh.py:92-93 - `name: str = Field(min_length=1)`, `marker: str = Field(min_length=1)` with no regex/character-set validation
- kayakgen/eval/cfd/openfoam_v2512_interfoam/evidence.py:75-102 - `read_poly_mesh_patches()` parses name and marker from regex groups without further validation
- Line 67-71 regex `_PATCH_BLOCK_RE` and `_TYPE_RE` can match names containing special characters (e.g., "hull-v2", "inlet.main")
- downstream code at line 520 creates `boundary_markers = {patch.name: patch.marker for patch in boundary_patches}` without encoding/escaping
impact: Patch names with newlines or quotes could be injected into case files or logs, breaking formatting. Marker names with special characters could cause OpenFOAM parser failures or confusing error messages if case files are regenerated from evidence.
recommended_action: Add `field_validator` to SnappyHexMeshPatchEntry to validate `name` and `marker` against a safe character set (e.g., alphanumeric + underscore + dash, matching OpenFOAM naming conventions). Reject names/markers with quotes, newlines, or other shell-special characters.
follow_up: new striatum workflow


### BUG-063: CfdOpenFoamForceDatSample lacks NaN/Infinity validators on numeric fields

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/cfd/
discovered: 2026-05-29 tick-22 (re-search 2)
claim: The `CfdOpenFoamForceDatSample` (parsers/openfoam_forces.py:32-52) accepts float and tuple[float, ...] fields (`time_s`, `pressure_force_n`, `viscous_force_n`, `porous_force_n`, `total_force_n`, `drag_force_n`) without validators to reject NaN or Infinity values. These fields are parsed from force.dat by regex (line 80) and can contain NaN if OpenFOAM writes NaN values (due to solver divergence, uninitialized variables, or corrupted output). The parsed samples serialize to JSON with null and propagate NaN through downstream evaluation code.
evidence:
- kayakgen/eval/cfd/parsers/openfoam_forces.py:46-51 - float and tuple[float, float, float] fields with no finite-value validators
- kayakgen/eval/cfd/parsers/openfoam_forces.py:80 - regex parsing does not filter NaN: `float(match.group(0))` can produce NaN from string "nan"
- kayakgen/eval/cfd/parsers/openfoam_forces.py:175 - last_sample of type CfdOpenFoamForceDatSample is returned without validation
- kayakgen/eval/contract.py:196-200 - GZCurve enforces _curve_values_must_be_finite(), showing the pattern is known
- Contrast: tick-21 (BUG-058) found the same gap on CheckMeshSummary; tick-10 (BUG-023) found it on ResistanceCurve
impact: A force.dat file containing NaN drag values will be parsed successfully, serialize to JSON, and propagate corrupt data into downstream resistance calculations. The raw_unvalidated claim fields do not guarantee numeric integrity, but schema-level validators should still reject obviously-invalid NaN values.
recommended_action: Add @field_validator to CfdOpenFoamForceDatSample for all float fields to reject NaN/Infinity using `math.isfinite()`. For tuple fields, validate each element: `if any(not math.isfinite(v) for v in value): raise ValueError(...)`. Raise ValueError with a clear message. Bundle with BUG-023, BUG-058 into a comprehensive sweep adding finite-value validators across all numeric schemas.
follow_up: new striatum workflow (bundle with BUG-023 / BUG-058 remediation)

### BUG-064: Case-render write_text() lacks explicit UTF-8 encoding

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/cfd/
discovered: 2026-05-29 tick-22 (re-search 2)
claim: The case-render functions in `openfoam_v2512_interfoam/case_render.py` (lines 261, 304, 308, 312, 324) and `openfoam_v2512_interfoam/evidence.py` (line 78) use `Path.read_text()` and `Path.write_text()` without explicitly specifying `encoding="utf-8"`. This mirrors BUG-022 and BUG-040 patterns found in other surfaces; on systems with non-UTF-8 locale encoding, OpenFOAM case dictionaries and boundary files with non-ASCII characters (e.g. comments with diacritics) will fail to read/write.
evidence:
- kayakgen/eval/cfd/openfoam_v2512_interfoam/case_render.py:261 - `template_path.read_text()` (no encoding parameter)
- kayakgen/eval/cfd/openfoam_v2512_interfoam/case_render.py:304, 308, 312, 324 - `write_text(...)` calls (no encoding parameter)
- kayakgen/eval/cfd/openfoam_v2512_interfoam/evidence.py:78 - `Path(boundary_path).read_text()` (no encoding parameter)
- kayakgen/eval/cfd/openfoam_v2512_interfoam/runner.py:319 - `log_path.write_text(...)` (no encoding parameter)
- Python pathlib docs: "If encoding is not specified, locale.getpreferredencoding(False) is used instead" (locale-dependent, not UTF-8)
impact: On Windows or non-UTF-8 systems, OpenFOAM case files and logs with non-ASCII content will fail to read/write. OpenFOAM boundary files parsed from polyMesh/boundary (evidence.py:78) may be corrupted if they contain non-ASCII characters, blocking evidence binding.
recommended_action: Add explicit `encoding="utf-8"` to all `Path.read_text()` and `Path.write_text()` calls in case_render.py (lines 261, 304, 308, 312, 324) and evidence.py (line 78) and runner.py (line 319). This is a bulk edit affecting ~5 call sites in the openfoam_v2512_interfoam module. Merge with BUG-022 and BUG-040 fixes in a single sweep.
follow_up: new striatum workflow (bundle with BUG-022 / BUG-040 remediation)

### BUG-065: force.dat parser does not validate field count against expected layout

severity: high
category: implementation_gap
status: open
surface: kayakgen/eval/cfd/
discovered: 2026-05-29 tick-22 (re-search 2)
claim: The `_parse_openfoam_force_dat_line()` function at line 82-95 validates that the field count is either 10 or 13 (v2512 standard vs. with porous), but a forward-compatible OpenFOAM v2606+ release might add additional columns (e.g., poro_x, poro_y, poro_z, extra_x, ...). If a force.dat from a newer OpenFOAM version with 16 fields is encountered, the parser will reject it as malformed, even though the first 10 (or 13) fields contain valid data. This is a hard rejection that treats version drift as fatal rather than tolerant.
evidence:
- kayakgen/eval/cfd/parsers/openfoam_forces.py:22-29 - two magic constants: _OPENFOAM_V2512_FORCE_DAT_FIELDS=10, _OPENFOAM_V2512_FORCE_DAT_FIELDS_WITH_POROUS=13
- kayakgen/eval/cfd/parsers/openfoam_forces.py:82-95 - strict check: `if len(values) == 10: ... elif len(values) == 13: ... else: raise CfdDispatchError(...)`
- No tolerance for extra fields; no log warning if field count exceeds expected range
impact: A legitimate force.dat from v2606+ OpenFOAM with forward-compatible extra columns will be rejected, preventing valid evidence collection from newer solver versions. This is a forward-compatibility gap that violates the "raw_unvalidated" contract's intent to accept real solver output without strict schema enforcement.
recommended_action: Relax the parser to accept field counts >= 10 (or >= 13 if porous is detected) and log a warning if extra fields are present. Extract only the first 10 (or 13) fields and ignore the rest. This allows forward-compatible parsing while still catching truly-malformed output (< 10 fields). Alternatively, document the hard v2512 requirement and raise the error message to mention "v2606+ builds may require a different parser".
follow_up: new striatum workflow

### BUG-066: Evidence record produced by CFD adapter may lack required fields

severity: high
category: implementation_gap
status: open
surface: kayakgen/eval/cfd/
discovered: 2026-05-29 tick-22 (re-search 2)
claim: Tick 21 (BUG-058/059/060/061) identified gaps in how SnappyHexMeshEvidence is constructed and validated. The CFD adapter's evidence binding path in `openfoam_v2512_interfoam/evidence.py:build_snappy_hex_mesh_evidence_from_case()` constructs evidence by reading on-disk polyMesh artifacts and hashing them (lines 105-118). However, if the meshing stage fails to write all required artifacts (e.g., missing "points" or "boundary" file), the checksums dict will be incomplete, yet the function raises FileNotFoundError only when required artifacts are missing (lines 114-117). The adapter then passes this potentially-incomplete evidence to downstream binding logic. No cross-field validator on the evidence ensures that all required checklist items are present before dispatch_state is set to "evidence_recorded".
evidence:
- kayakgen/eval/cfd/openfoam_v2512_interfoam/evidence.py:114-118 - FileNotFoundError only raised if "points" or "boundary" is missing; other artifacts may be silently omitted
- kayakgen/eval/cfd/openfoam_v2512_interfoam/evidence.py:134-176 - build_snappy_hex_mesh_evidence_from_case() passes artifact_checksums to builder with no validation
- kayakgen/eval/snappy_hex_mesh.py:152-175 - SnappyHexMeshEvidence validator checks for blockers only when dispatch_state != "evidence_recorded" (line 154), allowing operator-constructed records to bypass the checklist
- Tick 21 (BUG-060) found that empty artifact_checksums can be set to "evidence_recorded" manually
impact: A CFD run where snappyHexMesh crashed mid-write could produce an evidence record with incomplete artifact_checksums. If the run_record's dispatch_state is manually set to "evidence_recorded" in JSON (or if the binding logic sets it prematurely), downstream mesh consumers will assume the artifact set is complete but will encounter missing checksums during access, causing silent failures or misinterpretation of the evidence state.
recommended_action: Add a model_validator to SnappyHexMeshEvidence that checks: `if self.dispatch_state == "evidence_recorded": verify all required artifacts in REQUIRED_ARTIFACT_NAMES are present in artifact_checksums`. Define REQUIRED_ARTIFACT_NAMES (e.g., {"points", "boundary", "faces", "owner", "neighbour"}) based on RFC 0045's artifact contract. Raise ValueError if any required artifact is missing. This complements BUG-060's fix.
follow_up: new striatum workflow (coordinated with BUG-060 fix)


### BUG-067: signed_volume_m3 lacks NaN/Infinity validator

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/closed_volume/
discovered: 2026-05-29 tick-23 (re-search 2)
claim: The `ClosedVolumeDiagnostics.signed_volume_m3` field (line 266 of schemas.py) is a bare `float` with no validator to reject NaN or Infinity values. This contrasts with the principle established in BUG-023 (ResistanceCurve and Hydrostatics lack finite-value validators). If `_signed_volume()` in topology.py encounters degenerate geometry or numerical instability (e.g., zero-area faces, colinear vertices), the floating-point sum at line 208 could produce NaN or Infinity, which then serializes to JSON as `null` or invalid JSON, silently corrupting the evidence record.
evidence:
- kayakgen/eval/closed_volume/schemas.py:266 — `signed_volume_m3: float` with no validator
- kayakgen/eval/closed_volume/topology.py:202-208 — `_signed_volume()` computes `np.einsum(...).sum() / 6.0` without NaN/Infinity guard
- kayakgen/eval/closed_volume/diagnostics.py:42 — signed_volume computed and passed directly to ClosedVolumeDiagnostics constructor
- kayakgen/eval/contract.py:196-200 — GZCurve establishes precedent with `_curve_values_must_be_finite()` validator on array fields
impact: A malformed closed-volume body with degenerate faces or numerical edge cases could produce a diagnostics record with `signed_volume_m3=NaN`, which serializes to JSON null and silently loses the diagnostic signal. Downstream code expecting a float will encounter null and either crash or ignore the value, violating the claim that diagnostics are always present and valid.
recommended_action: Add a `field_validator` to `ClosedVolumeDiagnostics` that enforces `math.isfinite(value)` on `signed_volume_m3`, raising ValueError if NaN or Infinity is encountered. Alternatively, validate at the `_readiness_reasons()` entry point (diagnostics.py:160) and convert NaN to zero or reject the body upfront. Use the same pattern as GZCurve's `_curve_values_must_be_finite()`.
follow_up: new striatum workflow

### BUG-068: ClosedVolumeWaterlineMetadata.beam_wl_m lacks finite-value and cross-field constraints

severity: medium
category: implementation_gap
status: open
surface: kayakgen/eval/closed_volume/
discovered: 2026-05-29 tick-23 (re-search 2)
claim: The `ClosedVolumeWaterlineMetadata.beam_wl_m` field (line 163 of schemas.py) is a bare `float` with no `gt=0` or finite-value validator. Per RFC 0022, beam_wl_m is the design waterline beam, which must be positive and non-zero. If upstream Hull.beam_wl_m is mutated post-construction (violating BUG-016's observation that Hull is frozen=False) or set to 0, the generated_hull_plus_deck_body will pass a zero or NaN beam into the waterline_metadata, and the diagnostics will not catch it.
evidence:
- kayakgen/eval/closed_volume/schemas.py:157-164 — ClosedVolumeWaterlineMetadata has `beam_wl_m: float` with no constraints
- kayakgen/eval/closed_volume/generated_body.py:77-83 — beam_wl_m copied from hull.beam_wl_m without post-copy validation
- kayakgen/model/hull.py:41 — `beam_wl_m: float | None` with only `gt=0` if present; None is allowed
- RFC 0022 § Waterline semantics states "beam at the design waterline; required for non-None metadata"
impact: A ClosedVolumeBody with `waterline_metadata.beam_wl_m=0.0` or `beam_wl_m=NaN` will serialize and round-trip through JSON without error. Downstream CFD or hydrostatics code expecting a positive beam value will encounter zero or NaN, causing division-by-zero or silent corruption of normalized ratios (e.g., L/B_wl).
recommended_action: Add `gt=0` and `math.isfinite()` validators to `ClosedVolumeWaterlineMetadata.beam_wl_m`. Ensure `generated_hull_plus_deck_body()` rejects hulls with `beam_wl_m is None or beam_wl_m <= 0` before passing the beam to waterline_metadata (line 79-82). Add a regression test round-tripping a closed body with waterline_metadata and verifying beam_wl_m is finite and positive.
follow_up: new striatum workflow

### BUG-069: Float equality for normal_length == 0.0 in point-triangle distance

severity: medium
category: math
status: open
surface: kayakgen/eval/closed_volume/
discovered: 2026-05-29 tick-23 (re-search 2)
claim: Line 502 of self_intersection.py uses exact float equality `if normal_length == 0.0` to detect colinear triangles (degenerate case), but `normal_length` is the result of `np.linalg.norm(normal)` where `normal = np.cross(ab, ac)`. Numerically, a nearly-colinear but not-exactly-colinear triangle can have a cross-product magnitude extremely close to zero (e.g., 1e-16) that rounds to 0.0 in IEEE 754 double precision. The exact equality check may miss this case and return a point-in-triangle distance that is incorrect for the degenerate boundary.
evidence:
- kayakgen/eval/closed_volume/self_intersection.py:500-508 — `normal_length = float(np.linalg.norm(normal))` followed by `if normal_length == 0.0:`
- Establishes precedent with BUG-019 (exact float equality for rake), BUG-015 (exact float equality for rake in Hull)
- No tolerance parameter; no `math.isclose()` call
- RFC 0021 § Self-intersection diagnostics requires conservative handling of edge cases
impact: A triangle with vertices that are nearly-colinear (e.g., three points on a line differing by < 1e-15 m) could be misclassified during the self-intersection diagnostic. The distance calculation would use the fallback `min(distance_to_vertices)` instead of the correct plane-distance formula, potentially reporting a false negative in the self-intersection check.
recommended_action: Replace `if normal_length == 0.0` with `if normal_length < 1e-12` (or a tolerance matched to the degenerate_area_tolerance_m2 constant). Alternatively, use `math.isclose(normal_length, 0.0, abs_tol=1e-12)`. Add a regression test creating a nearly-colinear triangle and verifying the distance calculation is robust.
follow_up: new striatum workflow

### BUG-070: No cross-field validator for signed_volume vs. readiness level coherence

severity: high
category: claim_gate
status: open
surface: kayakgen/eval/closed_volume/
discovered: 2026-05-29 tick-23 (re-search 2)
claim: The `ClosedVolumeDiagnostics` model validator at line 277-288 enforces that RFC 0021 self-intersection status must be "passed" when readiness.level is "closed_volume". However, there is no symmetric cross-field validator ensuring that when readiness.level is "closed_volume", the signed_volume_m3 must be positive (> signed_volume_tolerance_m3). Per diagnostics.py:160-161, the readiness determination itself checks `if signed_volume <= policy.tolerances.signed_volume_tolerance_m3: reasons.append(...)`, but an operator or buggy upstream code could construct a ClosedVolumeDiagnostics record with readiness.level="closed_volume" while signed_volume_m3 is negative or zero, violating the invariant.
evidence:
- kayakgen/eval/closed_volume/schemas.py:277-288 — model_validator only checks self_intersection_status, not signed_volume coherence
- kayakgen/eval/closed_volume/diagnostics.py:160-161 — readiness determination logic checks signed_volume, but validator does not enforce the inverse
- kayakgen/eval/closed_volume/diagnostics.py:50-59 — readiness.reasons computed at construction; operator could manually override reasons list post-construction if frozen=False
- RFC 0016 § Readiness gate states "readiness.level='closed_volume' requires positive signed volume and correct orientation"
impact: An operator can construct a ClosedVolumeDiagnostics record (or craft a JSON payload) with readiness.level="closed_volume" but signed_volume_m3=-5.0, violating the contract. Downstream code expecting "closed_volume" readiness will assume the geometry is valid and produce incorrect CFD setup or hydrostatics, causing silent corruption.
recommended_action: Add a model_validator to ClosedVolumeDiagnostics that enforces: `if self.readiness.level == "closed_volume": assert self.signed_volume_m3 > self.policy.tolerances.signed_volume_tolerance_m3` and `assert self.self_intersection_status == "passed"`. This complements the existing self-intersection check and ensures both conditions hold together. Document the coherence contract in the docstring.
follow_up: new striatum workflow


### BUG-071: STL export silently falls back to deck when part parameter is invalid

severity: low
category: implementation_gap
status: open
surface: kayakgen/ui/web/app.py
discovered: 2026-05-29 tick-24
claim: The REST endpoint `/api/stl?part=<value>` accepts any string value for `part`, but the geometry layer silently treats non-"hull" values as "deck" (see geometry.py line 193: `return (self.B_wl if part == "hull" else self.B) / 2.0`). An operator or external tool passing `part=ballast` or `part=invalid` will receive a deck STL without error or warning.
evidence:
- kayakgen/ui/web/controllers.py:218 — `part = request.query.get("part", "hull")` accepts any string
- kayakgen/ui/web/controllers.py:221 — `stl_bytes_for_part(state, part)` passes unsanitized part to service layer
- kayakgen/model/geometry.py:193 — `return (self.B_wl if part == "hull" else self.B) / 2.0` silently treats invalid parts as deck
- kayakgen/services/artifacts.py type signature uses `part: str` (not a literal enum)
impact: Low. An operator requesting an invalid part receives a geometry file with a wrong part name encoded in the response, but the geometry itself (deck mesh) is valid. This is a usability issue rather than a data-loss or claim-state leak. The PartType hint in geometry.py documents the intent; enforcement is missing in the REST layer.
recommended_action: Add explicit validation in post_stl() to reject part values outside {"hull", "deck"}. Example: `if part not in ("hull", "deck"): raise CfdWebError(400, {"error": "invalid_part", "message": f"part must be 'hull' or 'deck', not {part}"})`. Alternatively, use a Literal type or enum for part in the service signature and validate upfront.
follow_up: new striatum workflow

### BUG-072: Tick 24 second-pass survey completed (positive baseline)

severity: info
category: implementation_gap
status: open
surface: kayakgen/ui/web/app.py
discovered: 2026-05-29 tick-24
claim: Tick 24 executed a deeper second-pass search on app.py focusing on REST handlers, WebSocket state-binding, cross-field validators, float-equality edge cases, NaN handling, and cross-mode state leaks. Beyond BUG-071 (STL part parameter validation), no new actionable bugs surfaced. All REST handlers have structured error responses (controllers.py lines 181-209); CfdWebStore validates job_id paths (services/cfd_jobs.py line 69); float equality in preset-seed comparison uses tolerance (app.py line 694). The NaN/infinity rendering in _resistance_table_html and _refresh_metrics (f-string formatting like `{row['Rt_N']:.1f}`) is cosmetic only and already covered by the BUG-029 pattern (validity_badge_title_for NaN/inf).
evidence:
- kayakgen/ui/web/controllers.py:181-209 — request_json, cfd_error_response, cfd_unexpected_response all return structured errors
- kayakgen/ui/web/controllers.py:216-228 — post_stl error paths return validation_error_payload(exc) with status 400
- kayakgen/services/cfd_jobs.py:68-69 — CfdWebStore.get_job_dir() validates `if not _is_relative_to(job_dir, self.jobs_root)`
- kayakgen/ui/web/app.py:467-471 — NaN/inf render as "nan"/"inf" in HTML table (cosmetic, already noted in BUG-029)
- kayakgen/ui/web/app.py:694 — uses tolerance-based float comparison (1e-9), not exact equality
impact: None; positive baseline. No new claim-state leaks, security gaps, or silent corruptions identified. The surface is well-protected against the patterns identified in prior ticks.
recommended_action: Optional follow-up: mark app.py as "settled for tick 24 scope" in COVERAGE.md. No remediation needed beyond BUG-071 (STL part validation).
follow_up: wontfix (positive baseline)

### BUG-073: Float parameters in cfd_prepare lack bounds validation

severity: medium
category: implementation_gap
status: open
surface: kayakgen/cli/
discovered: 2026-05-29 tick-25
claim: The `kayakgen cfd prepare` command accepts `--speed-mps`, `--seawater-density-kg-m3`, and `--kinematic-viscosity-m2-s` as float arguments without validating that they are positive, finite, and within physically-reasonable ranges. An operator can pass `--speed-mps -1.0` or `--speed-mps nan` and the values are silently accepted and written to the CFD job spec.
evidence:
- kayakgen/cli/main.py:411-420 - three float Option parameters with no field validators
- kayakgen/cli/main.py:434-441 - values passed directly to prepare_cfd_job() without validation
- No check for positive values, finite values (NaN/inf rejection), or physical bounds
- A CFD job spec with `speed_mps=nan` or `seawater_density_kg_m3=-1.0` will be accepted at prepare time and only fail downstream during simulation
impact: An operator can construct malformed CFD job specs that appear valid (job directory created, status written) but will fail at run time with cryptic OpenFOAM errors rather than early CLI validation. Negative density or viscosity values violate physical law and should be rejected at the CLI boundary.
recommended_action: Add validation in the `cfd_prepare` function body to check that `speed_mps > 0`, `seawater_density_kg_m3 > 0`, and `kinematic_viscosity_m2_s > 0`. Also reject NaN/inf for all three parameters using `math.isnan()` and `math.isinf()`. Emit a clear error message and exit(1) if any constraint is violated.
follow_up: new striatum workflow

### BUG-074: read_text() calls lack explicit UTF-8 encoding in CLI

severity: medium
category: implementation_gap
status: open
surface: kayakgen/cli/
discovered: 2026-05-29 tick-25
claim: Nine calls to `Path.read_text()` in the CLI modules lack explicit `encoding="utf-8"` parameter, relying on system locale defaults. This can cause failures on Windows or non-UTF-8 systems. The CLI modules are entry points where non-ASCII input (fixture manifests, load cases, rights checklists) is common.
evidence:
- kayakgen/cli/runs_cli.py:223, 246 - two read_text() calls without encoding
- kayakgen/cli/main.py:198, 567, 860, 930, 997, 1034 - six read_text() calls without encoding
- kayakgen/cli/target_workflows.py:28 - one read_text() call without encoding
- BUG-022 (tick-10) established precedent for this pattern in kayakgen/io/json.py
- Python pathlib docs: "If encoding is not specified, locale.getpreferredencoding(False) is used"
impact: A system deployed on Windows with non-UTF-8 locale or on a non-UTF-8 filesystem may see CLI commands fail to read JSON files with encoding errors. JSON files containing diacritics or special characters (e.g., names, notes) will be silently corrupted or rejected depending on locale.
recommended_action: Add explicit `encoding="utf-8"` to all nine `Path.read_text()` calls in the CLI modules. This is the best practice per PEP 597 and ensures portable behavior across systems.
follow_up: new striatum workflow

### BUG-075: stability legacy command JSON output lacks sort_keys

severity: low
category: math
status: open
surface: kayakgen/cli/
discovered: 2026-05-29 tick-25
claim: The `kayakgen stability legacy` command at line 595 of main.py uses `json.dumps(payload, indent=2)` without `sort_keys=True` when writing high-angle-GZ augmented stability results. This produces non-deterministic JSON key order across Python versions and serialization contexts, violating the project's commitment to deterministic canonical JSON (RFC 0049 / RFC 0051).
evidence:
- kayakgen/cli/main.py:595 - `json.dumps(payload, indent=2)` without sort_keys=True
- kayakgen/cli/runs_cli.py:135 - contrast: same operation uses `json.dumps(payload, sort_keys=True)` correctly
- kayakgen/services/identity.py - canonical JSON everywhere uses sort_keys=True
- RFC 0049 § Canonical JSON: "artifact identity depends on key order stability"
impact: A stability result with high-angle-GZ augmentation written on Python 3.10 may differ in key order from the same data written on Python 3.11+, producing different JSON hashes when downstream processes reserialize (though the content is identical). Archive integrity and audit trails may show spurious differences.
recommended_action: Change line 595 to `json.dumps(payload, indent=2, sort_keys=True)`. This is a one-line fix and matches the pattern used elsewhere in the codebase.
follow_up: new striatum workflow

### BUG-076: Positive float parameters lack NaN/inf validation in CLI

severity: medium
category: implementation_gap
status: open
surface: kayakgen/cli/
discovered: 2026-05-29 tick-25
claim: Four float CLI parameters accept NaN/inf without validation: `--turning-heel-deg`, `--rmse-threshold`, and the unnamed `--step` in sensitivity, and `--tolerance-percent` in migrate-geometry. An operator can pass `--turning-heel-deg nan` or `--rmse-threshold inf` and the values silently propagate to the service layer.
evidence:
- kayakgen/cli/main.py:98-102 - `turning_heel_deg: float` with no NaN/inf check before line 117 usage
- kayakgen/cli/main.py:973-981 - `rmse_threshold: float` with no NaN/inf check before line 1001 usage
- kayakgen/cli/sensitivity_cli.py:36-43 - `step: float | None` accepts NaN without validation
- kayakgen/cli/migrate_geometry_cli.py:134-143 - `tolerance_percent: float` accepts NaN/negative without validation
- Each parameter is passed to service functions that expect valid positive floats
impact: NaN values propagate silently through evaluations and produce confusing downstream results (NaN drift calculations, NaN threshold comparisons). An operator will see "tolerance exceeded" reports with NaN values rather than a clear error at the CLI boundary.
recommended_action: For each parameter, add a guard after it is parsed: check `math.isnan(param)` and `math.isinf(param)` and emit a clear error and exit(1) if either is true. For parameters that must be positive (all four), also check `param <= 0` and reject if true. Examples: `if tolerance_percent <= 0 or math.isnan(tolerance_percent) or math.isinf(tolerance_percent): raise ValueError("tolerance_percent must be positive and finite")`.
follow_up: new striatum workflow

### BUG-077: Encoding gaps in calibration and target-workflow CLI reads

severity: low
category: implementation_gap
status: open
surface: kayakgen/cli/
discovered: 2026-05-29 tick-25
claim: The calibration CLI commands (`ingest-tank-test`, `ingest-inclining-test`, `accept-fit`) and target-workflow commands read JSON files with `Path.read_text()` without explicit UTF-8 encoding. While part of the broader BUG-074 family, these commands process domain-critical files (RightsChecklist, AcceptedFitRecord) where encoding safety is critical for audit integrity.
evidence:
- BUG-074 already identified 9 encoding gaps; this consolidates and highlights the critical paths
- kayakgen/cli/main.py:860, 930, 997, 1034 — RightsChecklist and AcceptedFitRecord reads
- kayakgen/cli/target_workflows.py:28 — LoadCase.model_validate_json(load_path.read_text())
- These records form the chain of custody for calibration work; encoding errors silently corrupt metadata
impact: A RightsChecklist or AcceptedFitRecord with diacritics (e.g., Italian names, Unicode symbols) may silently corrupt on a non-UTF-8 system, breaking the audit trail and potentially hiding attribution errors.
recommended_action: Apply the UTF-8 encoding fix from BUG-074 to all calibration and target-workflow reads. This is part of the same striatum workflow.
follow_up: consolidate with BUG-074 striatum workflow

