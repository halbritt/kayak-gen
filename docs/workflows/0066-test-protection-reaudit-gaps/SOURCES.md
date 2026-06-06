# Sources — workflow 0066 (re-audit gap remediation)

1. `KAYAKGEN_TEST_COVERAGE_AUDIT_WHOLE_REPO_CLAUDE_OPUS_4_8_2026-06-06.md`
   (commit 0479484) — the work order. §4 ranked gap ledger rows G1-G7 with
   file:line, mechanism, and smallest closing test per row; §4 notes G8-G11;
   §6 names the equal-length bit-rot sibling of the write-side length
   screen. Verdict MIXED on exactly two grounds: the claimed-but-absent
   skip pin (G1) and the unverified read path (G2).
2. Morning chain (context, not work order):
   `KAYAKGEN_TEST_COVERAGE_AUDIT_CLAUDE_OPUS_4_8_2026-06-06.md` (R0-R12),
   `KAYAKGEN_TEST_PROTECTION_REMEDIATION_PLAN_CLAUDE_OPUS_4_8_2026-06-06.md`
   (P0/P1/P2, §7 deferrals, §8 answered questions D048/D049), workflows
   0062-0065 (commits 311853f..b38822e).
3. `docs/RELEASE_DISCIPLINE.md` — already states the policy the G1 pin
   enforces ("expected: 4 ... any other skip count means the run does not
   count as a gate"); commit fbfdf9e claims the pin in its subject.
4. Deferrals carried, not debt: G7 (CLI NaN negatives — lands with the
   bug-hunt NaN-validator sweep per workflow 0065 SUMMARY), G11
   (absolute-path evidence refs — until externally-authored fixtures,
   D006/D007).

Decisions made for this run (operator-authorized autonomous session):
G2 read contract = serve-only-verified with repair-from-intact-canonical,
structured raise otherwise (new DECISION_LOG row). G1 pin lands in BOTH
gates via new scripts/full-gate.sh (the release doc implies both). G5 =
pin the fail-closed R2-default quirk as intended; per-metric default
recorded as an open question, no product change.

Hard boundary: audit/report files at repo root are evidence — never edit
them. kayakgen/eval/ and kayakgen/cli/ are forbidden paths (G5/G3 are
test-only). The 0063 fixture-digest pin test must remain byte-identical.
