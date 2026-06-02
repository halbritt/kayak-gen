# Final Review Prompt

Read the runbook, RFC 0065 §5 + the "Slice 4 observable" Acceptance Criteria + the
mandatory-vs-optional gate table, `SLICE_4_DECISIONS.md`, D047, the implementer and
remediation patch summaries, the review artifacts, the findings ledger, the
changed files, and the validation evidence.

Verify (and confirm RFC 0065's core, Slices 1–4, is COMPLETE):

- every Slice 4 decision (D1–D8) is reflected in the shipped change;
- the baselines were regenerated on the canonical env (explained diff) before the
  compare was flipped; the visual compare is a HARD gate with a documented
  per-viewport tolerance and the VTK mask; missing Playwright/Chromium SKIPs
  optional smoke and HARD-FAILS the acceptance profile; the compare fails on an
  over-tolerance diff;
- the a11y checks (focus order, visible focus ring from the Slice 1 token,
  hit-target min, contrast) pass with the documented posture; the
  `CONTRAST_MANIFEST` pytest gate passes in both palettes; Lighthouse ≥ 90 is
  recorded (not a mandatory pytest gate);
- every retained behavioural check passes (nonblank-3D before/after, Share reload
  round-trip, STL via `POST /api/stl?part=hull`, console/network cleanliness);
- the claim line and RFC 0032 boundary are intact (no new route / claim-state /
  readiness literal; no recoloured chip; no raw result baked into a confident
  treatment; the §8 no-go list absent);
- `docs/WEB_VERIFICATION.md` documents the baseline-update procedure + the
  mandatory-vs-optional table; `docs/USER_GUIDE.md` is updated; DECISION_LOG D047
  is ratified (`proposed` → `accepted`);
- `git diff --check` passes and the full repo suite (minus the env-gated smoke) is
  green except the known pre-existing NB-2 `tests/test_services_boundaries.py`
  services→ui import-boundary failure (documented, out of scope).

Publish a final finding artifact and verdict.
