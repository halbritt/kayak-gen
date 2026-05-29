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

