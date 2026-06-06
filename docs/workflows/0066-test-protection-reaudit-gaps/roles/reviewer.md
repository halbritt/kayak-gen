# Role: Reviewer (Re-audit gap remediation — G1-G6, G8-G10)

Review the nine gap closures with enforcement honesty as the primary lens:
the previous wave shipped a skip-count pin that existed only in prose
(audit G1, the repo's one clear instance of coverage theater). Your job is
to make sure this wave's mechanisms actually fire.

Non-negotiable checks:

- Scope: git diff main...HEAD touches ONLY the allowed paths (gate scripts,
  RELEASE_DISCIPLINE, DECISION_LOG, artifact_store.py, the four test files,
  CHANGELOG, workflow artifact dir). Anything else → needs_revision.
- G1: prove the pin fires — in scratch (never committed), force a wrong
  skip count and watch fast-gate.sh exit non-zero. Check the parse under
  set -euo pipefail, both summary shapes (skipped present/absent), and that
  full-gate.sh carries the identical pin.
- G2: trace every return out of _resolve_artifact — no path may serve bytes
  whose hash was not checked against ref.artifact_hash. The corrupt-both
  case raises; the equal-length bit-rot test would fail without the rehash.
- G6/G8/G9: deterministic (no chmod-000 root hazards, no wall-clock races);
  the TOCTOU test says honestly what it does not prove.
- G3/G5/G10: exit codes AND tokens pinned, not just no-crash; the 0063
  digest pin and boundary tests untouched.
- Run the FULL gate yourself via scripts/full-gate.sh so the new pin is
  exercised end-to-end (0 failed / exactly 4 documented skips; ruff clean).
  Findings file BEFORE the long run; heartbeat around it.

Verdicts: accept / accept_with_findings for apply-fixable issues;
needs_revision for scope violations, a red gate, or an unverified-read
escape; NEVER terminal reject.
