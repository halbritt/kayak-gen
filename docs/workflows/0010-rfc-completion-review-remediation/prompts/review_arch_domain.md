# Task - architecture and domain review

Read `docs/workflows/0010-rfc-completion-review-remediation/SOURCES.md`,
RFCs 0004 through 0007, and the current `kayakgen/` package. Write:

`striatum/0010-rfc-completion-review-remediation/gemini/REVIEW_ARCH_DOMAIN.md`

Use this structure:

```markdown
# Architecture and domain review - 0010

Date: <YYYY-MM-DD>
Reviewer: gemini
Verdict intent: accept | accept_with_findings | needs_revision | reject

## Summary

<One concise paragraph.>

## Findings

### F-ARCH-001 - <short title>
- Severity: blocker | major | minor | nit
- RFC: 000N, section or criterion
- File(s): <paths and lines>
- What you found: <2-4 sentences>
- Suggested remediation: <specific fix or test>
- Evidence: <commands, equations, paths, or numerical checks>
```

Specific checks:

1. RFC 0007 package layout and boundary discipline: `model`, `eval`, `io`,
   `ui`, `cli`, and top-level compatibility shims.
2. Hull aggregate/schema behavior, geometry abstraction, mesh export, waterline
   semantics, and cache/hash assumptions.
3. Hydrostatics and resistance evaluators, including formulas, units, and
   tests for edge cases.
4. RFC 0006 class presets and parameter limits against the design constraints
   document.
5. Golden tests and regression tests: whether they protect the promised
   behavior or merely exercise happy paths.

Avoid duplicating UI polish findings unless they indicate a package or domain
boundary problem.
