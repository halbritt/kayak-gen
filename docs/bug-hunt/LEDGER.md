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
