# Draft Prompt — re-audit gap remediation

Read the packet objective, your role file, audit §4 (the gap ledger, rows
G1-G10) and §6 (the equal-length bit-rot sibling), and SOURCES.md.
Implement the nine items in packet order, one commit each, inside the
write scope. Key anchors:

- scripts/fast-gate.sh — the measured fast tail (1052 passed / 4 skipped /
  2 deselected) confirms the pin value is 4 for both gates; the skipping
  files are not in the ignore list.
- kayakgen/services/artifact_store.py:848-877 — _resolve_artifact: the
  store-glob return (:850-852) serves without rehash; the re-derive branch
  (:863-869) warns-and-serves on mismatch. Both must become
  serve-only-verified.
- tests/test_artifact_store.py:212-268 — the write-side corruption tests
  are the house style to mirror (planted bytes, pytest.warns / pytest.raises,
  inode checks, no-orphan-temp glob).
- tests/test_calibration_campaigns.py — the tank-side source_id mismatch
  test is the twin to mirror for inclining.

Slice gate after item 9: scripts/full-gate.sh → 0 failed, exactly 4
documented skips; ruff clean. md5 the user-level index.sqlite before and
after. Heartbeat before/after the long run.

Publish striatum/0066-test-protection-reaudit-gaps/DRAFT.md with per-item
shas + diffstat, the G2 decision + DECISION_LOG row id, the G5 pin
rationale + open question, refreshed gate-header numbers, successor
findings if any, and the full-gate tail. Use the packet's byline.
