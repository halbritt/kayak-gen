# Review Prompt

Read the workflow runbook, the changed files, the implementer patch summary,
`SLICE_4_DECISIONS.md`, RFC 0065 §5 + the mandatory-vs-optional gate table, D047,
and the project's no-claims rules.

Review for your role's concern. Findings must be actionable and grounded in file
paths or artifacts. Use `accept_with_findings` for issues the remediation lane
can fix. Use `needs_revision` only when the workflow scope is invalid, unsafe, or
impossible to remediate in the current run.

Slice-4-specific checks to verify against your role:

- Baselines were regenerated on the canonical env (the PNG diff is explained,
  not unexplained churn) BEFORE the compare was flipped to hard (D1).
- The visual compare is a HARD FAILURE in the acceptance profile with a documented
  per-viewport tolerance; the VTK region is masked; missing Playwright/Chromium
  SKIPs optional smoke and HARD-FAILS the acceptance profile; the compare fails on
  an over-tolerance diff, not a no-op (D2, D3).
- The a11y checks (focus order, visible focus ring from the Slice 1 token,
  hit-target min, `CONTRAST_MANIFEST` contrast) are present and deterministic; the
  contrast check is a mandatory pytest gate passing in both palettes; any
  `theme.py`/`CONTRAST_MANIFEST` change is additive; a11y code fixes are minimal
  and token-sourced (D4).
- Lighthouse ≥ 90 is recorded, not a mandatory pytest gate (D5).
- Every retained behavioural check still passes (nonblank-3D before/after, Share
  reload, STL via `POST /api/stl?part=hull`, console/network cleanliness) (D6).
- Claim line byte-stable; no chip recoloured; no raw result baked into a confident
  visual treatment; no new route/claim/readiness literal; RFC 0032 boundary text
  unchanged; §8 no-go list absent from rendered output and the new docs (D7).
- `docs/WEB_VERIFICATION.md` has the baseline-update procedure + the
  mandatory-vs-optional table; `docs/USER_GUIDE.md` describes only polish + the
  gate; DECISION_LOG D047 is ratified (`proposed` → `accepted`) (D8).
- The known NB-2 services-import-boundary failure stays out of scope.

If a long browser-acceptance run is needed, do a SHORT targeted verification and
publish the verdict while the lease is warm, THEN run the longer suite (operator
hazard: a single long foreground command expires the lease).

Publish the required finding artifact and verdict.
