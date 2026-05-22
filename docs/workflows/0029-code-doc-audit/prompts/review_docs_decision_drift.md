# Task — Lane 2: docs / decision-drift audit

Read `docs/rfcs/0059-three-lane-code-and-doc-audit-workflow.md` §2.2
(docs / decision-drift coverage list) and the items in
`docs/workflows/0029-code-doc-audit/SOURCES.md` for the current preset.

Audit the documentation surfaces against current source behavior and
current decision state. Look for *honest-prose drift*: a doc claim that no
longer matches source or accepted decisions. Concrete coverage:

- `docs/SPEC.md` as product-boundary source of truth.
- `docs/PRD.md` scope and status assertions.
- `docs/DECISION_LOG.md` accepted, superseded, and obsoleted rows.
- `docs/ROADMAP.md` track rows and Future-Striatum-Batches disposition.
- `docs/rfcs/README.md` status headers — RFCs marked "proposed
  background; successor NNNN", "partial landed ...", or "landed ..." must
  match source and tests.
- `CHANGELOG.md` `Added` / `Changed` / `Fixed` entries against actual
  landings.
- `docs/ARCHITECTURE_MAP.md` package layout, CLI list, and
  durable-artifact table.
- `docs/UBIQUITOUS_LANGUAGE.md` plus `tests/test_vocabulary_coverage.py`
  drift.
- `docs/USER_GUIDE.md` surface descriptions vs. actual CLI / GUI / web
  behavior.
- `docs/WEB_VERIFICATION.md` claims against the Trame workspace.
- `OPERATOR_REPORT.md` checkpoints for externally-relevant changes.
- half-implemented RFCs that need a Phase status, an explicit successor,
  an obsoletion note, or a follow-up RFC.
- conflicts between docs and source behavior.

Do not "clean up" historical fixtures. Distinguish frozen provenance
(`tests/golden/`, archived sweep records, the Edinburgh acquisition
packet, opt-in real-OpenFOAM artifacts) from current product
documentation. Do NOT propose docs changes inside this job — produce a
`FINDINGS.md` artifact only.

Write your findings at the path the runner gives you under
`docs/audits/<RUN_DATE>-code-doc-audit/docs-decision-drift/FINDINGS.md`.
Use the entry shape from RFC 0059 §3 with `AUD-D-NNN` ids:

```markdown
### AUD-D-001: Short title

severity: critical | high | medium | low | info
category: docs_drift | rfc_status | test_gap
status: open
claim: One sentence describing the problem.
evidence:
- path/to/file.ext:line - concise evidence
impact: Why this matters (cite the RELEASE_DISCIPLINE.md checklist row
  affected, if any).
recommended_action: What should happen next.
follow_up: existing TODO/RFC/decision | new RFC | DECISION_LOG row |
  docs fix | wontfix
```

Aim for 5-15 high-quality findings with file:line evidence. Findings
without concrete evidence are downgraded to observations. High and
critical findings require at least one cited doc/source pair and an
explicit recommended action. Null findings are valid and useful — record
them as `severity: info` if your investigation of a likely-drift area
produced no evidence of a real problem.
