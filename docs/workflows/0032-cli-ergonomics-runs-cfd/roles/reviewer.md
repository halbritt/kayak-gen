# Role: Reviewer

Review the implement job's patch for R4 + R5 (audit findings
AUD-O-004, AUD-O-005, AUD-O-006).

Check the seven boundaries named in `prompts/review.md` — write
scope, back-compat, header columns matching row format, honest
filter-key vocabulary, verbatim copy of the two appended lines,
tight USER_GUIDE addition, green pytest suite.

Publish a finding artifact with `striatum.finding.v1` front matter
and one of the four verdicts: `accept`, `accept_with_findings`,
`needs_revision`, `reject`. Use `needs_revision` for any boundary
violation; `accept_with_findings` only for non-blocking polish notes.
