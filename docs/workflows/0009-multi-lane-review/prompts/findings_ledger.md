# Task — produce the consolidated findings ledger

Read every finding in:

- `striatum/0009-multi-lane-review/codex/REVIEW_MATH.md`
- `striatum/0009-multi-lane-review/gemini/REVIEW_ARCH.md`
- `striatum/0009-multi-lane-review/claude/REVIEW_INTEGRITY.md`

Write `striatum/0009-multi-lane-review/ledger/FINDINGS.md` using:

```markdown
# Findings ledger — 0009 multi-lane review

Run date: <YYYY-MM-DD>
Reviewers: codex (math), gemini (arch), claude (integrity + web).

## Stats

- Total findings raised: N
- After dedupe: M
- By severity: blocker N1 / major N2 / minor N3 / nit N4
- Integrity verdicts: accept N5 / accept-with-remediation N6 / reject N7
- Dissents: D rows where reviewers disagreed.

## Findings

### F-001 — <short title>
- Source: F-MATH-NNN (codex), F-ARCH-NNN (gemini)  *(if multiple raised it)*
- Severity: blocker | major | minor | nit | accept | accept-with-remediation | reject
- RFC / track: 0005 / math, 0007 §1 / arch, etc.
- File(s): kayakgen/eval/<file>.py:<line>, ...
- Statement: <2-4 sentences merged from the source(s)>
- Reviewer notes: <quoted snippets, if dissent or nuance>
- Suggested remediation: <if reviewer offered one>

### F-002 — ...
```

Rules:

1. **Merge identical findings.** If two reviewers raise the same
   issue (same file + same root cause), merge into one row crediting
   both source IDs.
2. **Preserve dissent.** If reviewers disagree on severity or on the
   right fix, record both views in `Reviewer notes` rather than
   averaging. Mark the row with a `(dissent)` tag.
3. **Stable IDs.** Number `F-001`, `F-002`, ... in reading order
   (math review first, then arch, then integrity, then merged
   duplicates). The synthesis job references these IDs.
4. **Do not edit the source review files.** This job is read-only on
   the lane reviews; it only writes to its own scope.
