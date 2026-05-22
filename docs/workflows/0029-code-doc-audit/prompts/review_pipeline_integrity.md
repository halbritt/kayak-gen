# Task — Lane 1: pipeline-integrity / claim-gate audit

Read `docs/rfcs/0059-three-lane-code-and-doc-audit-workflow.md` §2.1
(pipeline-integrity coverage list) and the items in
`docs/workflows/0029-code-doc-audit/SOURCES.md` for the current preset.

Audit the kayakgen pipeline for claim-state, accepted-use, readiness, and
acceptance-gate invariants. Look for *claim-state drift*: somewhere code
admits a stronger claim than the evidence supports. Concrete coverage:

- `claim_state` literals (`raw_unvalidated`, `validated`, etc.) — no
  surface promotes a result past its evidence; RFC 0025 / RFC 0027 /
  RFC 0058 acceptance contracts hold.
- `result_semantics` labels on resistance and `GZ` outputs (RFC 0043
  `unvalidated_hydrostatic_comparison` → `validated_hydrostatic_comparison`
  only via an accepted `StabilityFitRecord`).
- opt-in CFD / mesh / GZ gates: env knobs (RFC 0041 / RFC 0046
  three-mechanism opt-in), `--bind-evidence` chains (RFC 0045), and the
  `cfd_in_loop_evaluator_status` contract (RFC 0058).
- accepted-fit records and reviewer signatures (RFC 0027 / RFC 0054 /
  RFC 0058).
- `MeasuredStabilityFixture` / `StabilityFixturePromotionPacket`
  validators (RFC 0056).
- artifact-store identity: `Hull.record_hash` / `design_hash`,
  `FilesystemArtifactStore`, `SqliteIndex` (RFC 0049).
- public Pydantic schemas — `schema_version`, field name / type /
  default — and the metric registry (Phase 5).
- evaluator subprocess isolation, generative-search job records, and log
  redaction (RFC 0057).
- tests that pin a claim-gate boundary
  (`tests/test_vocabulary_coverage.py`, golden tests, the mesh
  evidence + `--bind-evidence` chain).
- examples / fixtures that might teach retired behavior.

Prefer source, generated schemas, tests, and current evaluator metadata
over prose. Do NOT propose source changes inside this job — produce a
`FINDINGS.md` artifact only.

Write your findings at the path the runner gives you under
`docs/audits/<RUN_DATE>-code-doc-audit/pipeline-integrity/FINDINGS.md`. Use
the entry shape from RFC 0059 §3:

```markdown
### AUD-P-001: Short title

severity: critical | high | medium | low | info
category: claim_gate | implementation_gap | test_gap
status: open
claim: One sentence describing the problem.
evidence:
- path/to/file.ext:line - concise evidence
- command or test result, when relevant
impact: Why this matters (cite the claim-state / accepted-use / readiness
  invariant affected).
recommended_action: What should happen next.
follow_up: existing TODO/RFC/decision | new RFC | DECISION_LOG row |
  docs fix | test coverage | wontfix
```

Aim for 5-15 high-quality findings with file:line evidence. Findings
without concrete evidence are downgraded to observations. High and
critical findings require at least one source reference plus an explicit
recommended action. Null findings are valid and useful — record them as
`severity: info` if your investigation of a likely-drift area produced no
evidence of a real problem.
