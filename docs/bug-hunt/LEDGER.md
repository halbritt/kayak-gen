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
