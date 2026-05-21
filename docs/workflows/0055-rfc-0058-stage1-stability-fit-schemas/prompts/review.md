# Review Prompt

Read the workflow runbook, changed files, the implementer's
PATCH_SUMMARY.md, `STAGE_1_DECISIONS.md`, RFC 0058, RFC 0056
(`measured_fixture.py` sibling pattern), and the project's no-claims
rules.

Review for your role's concern. Findings must be actionable and
grounded in file paths or artifacts. Use `accept_with_findings` for
issues the remediation lane can fix. Use `needs_revision` only when
the workflow scope is invalid, unsafe, or impossible to remediate.

Stage-1 specific review concerns:

- Every record uses `ConfigDict(extra="forbid")` and pinned
  `schema_version: Literal["1"]`.
- Threshold defaults match D-5 (`rmse_m ≤ 0.005`,
  `mape_fraction ≤ 0.05`, `max_error_m ≤ 0.01`,
  `coverage_fraction ≥ 0.9`).
- `StabilityFitRecord.strict=False` skips threshold enforcement and
  records `strict_check_skipped` in `warnings`.
- `StabilityFixturePromotionPacket` refuses promotion unless every
  review verdict is `"accepted"` AND `rig_design_match=True` AND
  `rejection_reasons=[]`.
- `FixtureRef.fixture_sha256` rejects non-64-char or uppercase hex.
- No fixture or fit is promoted. No claim-state literal changes. RFC
  0043's `unvalidated_hydrostatic_comparison` label is untouched.
- Forbidden-claim scrub list in `tests/test_web_layout.py` is unaffected.

Publish the required finding artifact with the proper
striatum.finding.v1 front matter and verdict.
