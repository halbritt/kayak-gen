---
schema_version: striatum.finding.v1
artifact_kind: finding
verdict_intent: accept_with_findings
severity: medium
tags:
  - test-protection
  - gate-integrity
  - serve-only-verified
author: operator
---

# Review — workflow 0066 (re-audit gap remediation, G1-G6 + G8-G10)

Verdict: **accept_with_findings**. One must-fix (MF-1, apply-scoped), two
should-fix notes. Every claimed protection was proven by execution, not
prose — the lens this workflow exists for.

## Review provenance

Supervised codex lane spawn is broken on this host (lane-sandbox posture
`STRIATUM_LANE_OS_USER=striatum-lane` adopted mid-run without the
repo-access provisioning step; three spawns died "child exited before
attach"). The review therefore ran through the operator claim loop:
first-party verification (claude, this session) + independent adversarial
pass by local `codex-cli 0.137.0` (`codex exec`, sandbox bypassed to match
the lane's own `--yolo` config, read-only instruction). Cross-model
property preserved; supervised-lane provenance is not.

## Scope — clean

`git diff 341d126..6abee0a --name-only` = exactly the 11 allowed paths
(2 gate scripts, RELEASE_DISCIPLINE, DECISION_LOG, artifact_store.py,
4 test files, CHANGELOG, workflow artifact dir). No forbidden path,
no audit-file edit, `git diff --check` clean.

## G1 — break-the-pin proof: the pin FIRES

Sabotaged copy of `fast-gate.sh` (`EXPECTED_SKIPS=5`, real subset run,
2026-06-07): `1087 passed, 4 skipped, 2 deselected in 197.50s` →
`[fast-gate] FAIL: 4 skipped, expected exactly 5` → **exit 1**.
Green path proven by the full-gate run below (parse found "4 skipped",
compared equal, exited 0). Parse holds under `set -euo pipefail`
(red/killed pytest fails the `tee` pipeline before the pin); absent
"skipped" defaults to 0 → fail-closed. `full-gate.sh` carries the
byte-identical pin block; RELEASE_DISCIPLINE.md cites it as the
mechanical form. Codex concurs: clean.

## G2 — read-path trace: one escape (MF-1)

Every return out of `_resolve_artifact` (artifact_store.py:878-950) is
rehash-verified or raises `ArtifactIntegrityError`; the old
warn-and-serve re-derive branch now fails closed; repair fires only when
canonical bytes rehash to the expected address; hard-link limitation
honestly documented.

**MF-1 (must-fix, apply-scoped)** — `get_json`
(kayakgen/services/artifact_store.py:956): serves
`path.read_text()` — a second read AFTER `_resolve_artifact` verified a
first read. The D050 claim is "every read path rehashes bytes before
serving"; the bytes served are not the bytes hashed. Found independently
by codex; confirmed first-party. Smallest fix: return (or decode) the
exact verified bytes — e.g. `_resolve_artifact` returns `(path, data)`
or a `_resolve_artifact_bytes` helper — plus a regression test that
mutates the file between resolve and decode (monkeypatch the second
read). Routed as accept_with_findings rather than needs_revision,
recorded reasoning: no pinned corruption scenario serves bytes (all
raise at resolve); the escape requires an external writer racing a
just-verified path within the same call; the fix and its regression
test sit inside the apply job's write scope. The run must not close
without MF-1 landed and the full gate re-run green.

## Per-item assertion honesty

- **G4**: manifest tests fail on renamed `--ignore` paths and
  non-collecting `--deselect` nodeids (subprocess `--collect-only`,
  return code + nodeid pinned). **SF-1 (note, codex)**: the pin-presence
  test (test_fast_gate_manifest.py:70) is textual — it would pass if the
  pin strings survived in dead code. Acceptable as a tripwire; apply may
  optionally script-test the parser against representative summaries.
- **G6**: stat-failure / read-failure branches pinned via monkeypatch
  (deterministic, root-safe). Clean.
- **G8**: future-stamp DB: rows survive, no rebuild warning, stamp not
  downgraded. Clean.
- **G9**: TOCTOU test proves the injected race happened
  (`competing_writes == [store_path]`) and pins identical-content
  last-writer-wins. **SF-2 (note, codex)**: it does not pin torn-write
  atomicity of `_atomic_write_bytes` itself; the in-test claim is
  correctly scoped, so this is a documented non-goal, not a defect.
- **G3**: CliRunner pair pins exit codes AND tokens AND
  no-report-on-refusal AND `report_kind == "exploratory_frontier"`.
  Clean.
- **G5**: both reason tokens pinned plus the explicit
  R2-under-default-threshold quirk test; campaigns.py untouched. Clean.
- **G10**: refusal messages asserted by content; inclining `source_id`
  mismatch mirrors the tank twin. Clean.
- 0063 digest-pin test and boundary tests: untouched (diff-verified).

## Full gate — executed by reviewer via the new script

`./scripts/full-gate.sh` (2026-06-07): ruff clean;
**1347 passed, 4 skipped, 1 warning in 561.01s (0:09:21)**;
`[full-gate] OK (4 skipped == expected 4)`; exit 0.

## Review-tooling contamination — remediated

Codex's MF-1 repro ran outside pytest (no isolation floor) and upserted
one row into the user-level `~/.local/share/kayakgen/index.sqlite`
(artifacts: hash 27b0a6ea…, run_id "toctou"). Detected by row-count
check, deleted, all six tables re-verified 0 rows. This is a live
demonstration of the exact risk audit R3's in-suite isolation floor
guards against; no standing invariant violated at review close.

## Findings ledger

| id | sev | where | what | disposition |
|---|---|---|---|---|
| MF-1 | must-fix | artifact_store.py:956 `get_json` | second unverified read after verification; D050 letter violated | apply MUST fix + regression test + full gate |
| SF-1 | note | test_fast_gate_manifest.py:70 | pin-presence test is textual | apply discretion |
| SF-2 | note | test_artifact_store.py:474 | G9 pins ordering, not torn-write atomicity | documented non-goal; no action required |
