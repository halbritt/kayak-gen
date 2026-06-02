# Final Review Prompt

Read the runbook, RFC 0065 §3 + the "Slice 3 observable" Acceptance Criteria,
`SLICE_3_DECISIONS.md`, the implementer and remediation patch summaries, the
review artifacts, the findings ledger, the changed files, and the validation
evidence.

Verify:

- every Slice 3 decision (D1–D8) is reflected in the shipped change, byte-for-byte
  where the decision is a byte-stability gate;
- uniform control states (default/hover/focus/active/disabled) derive from the
  Slice 1 tokens and apply across all controls (including the reintroduced
  focus-ring treatment); honestly-disabled controls stay disabled with byte-stable
  copy;
- every panel renders an explicit empty/loading/error state with a stable, tested
  hook; state copy is byte-stable; no failed/empty state reads as a successful
  claim;
- the forbidden-copy / no-go scan was extended to every new rendered string and
  stays green; styling is token-only (orphan lint green); the Slice 2
  region/status/collapse/first-viewport contract holds;
- every hook change is reflected in `tests/test_web_layout.py` +
  `tests/test_web_inline_help.py`;
- the claim line and RFC 0032 boundary are intact (no new route / claim-state /
  readiness literal; no recoloured chip; the §8 no-go list absent);
- `docs/USER_GUIDE.md` / `docs/WEB_VERIFICATION.md` were not touched and D047 was
  not ratified;
- `git diff --check` passes and the full repo suite (minus the env-gated smoke) is
  green except the known pre-existing NB-2 `tests/test_services_boundaries.py`
  services→ui import-boundary failure (documented, out of scope).

Publish a final finding artifact and verdict.
