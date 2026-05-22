# Task — Lane 3: operator / adoption audit

Read `docs/rfcs/0059-three-lane-code-and-doc-audit-workflow.md` §2.3
(operator / adoption coverage list) and the items in
`docs/workflows/0029-code-doc-audit/SOURCES.md` for the current preset.

Audit the operator-facing surfaces for first-adopter ergonomics. Look for
*invisible-mechanism drift*: a useful control surface that exists in code
but is undiscoverable from docs, or an error message that names internal
vocabulary the user wouldn't recognize. Concrete coverage:

- day-zero setup (`pyproject.toml` extras, optional `[builder]` /
  `[report]` dependencies, opt-in CFD env knobs).
- `kayakgen` CLI subcommand discoverability and `--help` clarity across
  all 20+ subcommands.
- desktop GUI flows (`gui.py`, `pyvista_view.py`).
- Trame web workspace and Generate panel: form-builder, 2D Pareto
  scatter, auto-poll, fork-with-seed, log redaction, CFD-in-loop
  acknowledgement copy, accepted-fit-aware frontier colouring.
- export menu / disabled-copy correctness.
- error messages, recovery paths, and first-run smoke.
- overly complex areas that need a simpler adapter or guide.
- places where file-based artifacts are useful but should not become
  the control plane.
- UI / API gaps that block design exploration, evaluator selection, job
  observation, or recovery.

This lane is allowed to raise product-shape findings, not just doc bugs.
Each finding still needs evidence and a concrete recommendation. Do NOT
propose source changes inside this job — produce a `FINDINGS.md`
artifact only.

Write your findings at the path the runner gives you under
`docs/audits/<RUN_DATE>-code-doc-audit/operator-adoption/FINDINGS.md`. Use
the entry shape from RFC 0059 §3 with `AUD-O-NNN` ids:

```markdown
### AUD-O-001: Short title

severity: critical | high | medium | low | info
category: operator_ergonomics | implementation_gap | docs_drift
status: open
claim: One sentence describing the problem.
evidence:
- path/to/file.ext:line - concise evidence
- command output, when relevant
impact: Why this matters.
recommended_action: What should happen next.
follow_up: existing TODO/RFC/decision | new RFC | docs fix | source change |
  wontfix
```

Aim for 5-15 high-quality findings with file:line evidence. Findings
without concrete evidence are downgraded to observations. High and
critical findings require at least one source or docs reference and an
explicit recommended action. Null findings are valid and useful — record
them as `severity: info` if your investigation of a likely-drift area
produced no evidence of a real problem (e.g. "no file-based artifacts
used as control plane — verified").
