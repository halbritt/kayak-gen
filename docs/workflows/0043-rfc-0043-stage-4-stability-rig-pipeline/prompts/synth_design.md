# Synthesis prompt — workflow 0043

You read the three panel designs at
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/design/{claude,codex,gemini}/DESIGN.md`
and produce a single accepted design at
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/synthesis/DESIGN_SYNTHESIS.md`.

Your job is **convergence**, not arbitration. Where the three
panel designs agree, the synthesis records the consensus. Where they
diverge, you pick a disposition AND record what you ruled out plus
why. Never silently drop a panel signal.

## Structure your synthesis like this

### 1. Where the panel converged

For each of A–E from the design prompt (CLI shape, acceptance gate,
claim_state resolution, test surface, operator-facing copy),
declare the consensus. Cite each panel design's section verbatim
once per cited consensus point.

### 2. Where the panel diverged

For each load-bearing disagreement, document:

- **Issue.** One sentence naming the design point.
- **Panel positions.** One bullet per lane, summarizing each
  lane's position in under 30 words.
- **Chosen disposition.** Which position the synthesizer adopts.
- **Rejected positions and why.** Each non-chosen position gets
  one sentence on why the synthesizer ruled against it. Do not
  use "less preferable" — name the structural defect.
- **Open question carry-forward.** If the disposition is
  provisional (you chose A but B has a defensible case), mark it
  as an Open Question in the synthesis Open Questions block so
  the design reviewers see it.

### 3. Final accepted design

Write the accepted design as a single coherent specification, NOT
a diff against the panel. The implementer reads this section
linearly and turns it into code; they should not need to
back-reference the panel designs to understand what to build.

The accepted design covers exactly the five surfaces A–E from the
design prompt:

- **A. CLI shape** — exact command names, flag signatures, JSON
  shapes (cite RFC 0056 schema fields).
- **B. Acceptance-gate criteria** — every gate the implementer
  must encode, in order. Name structured rejection-code constants.
- **C. Claim-state resolution** — the lookup rule + flip
  semantics + UI propagation path.
- **D. Test surface** — function names + one-line objectives.
- **E. Operator-facing copy** — `--help` text + USER_GUIDE.md
  subsection.

### 4. Open Questions

List every load-bearing decision the panel did not unanimously
agree on and the synthesizer's provisional disposition for each.
Number them OQ-1, OQ-2, …. The design reviewers explicitly
adjudicate each OQ; their `needs_revision` verdicts cite OQ
numbers.

### 5. What this synthesis explicitly does NOT do

Echo the design prompt's "What you are NOT doing" block so the
implementer doesn't reach into out-of-scope areas. Add anything
the panel uncovered that should also be excluded.

## Output

One file: `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/synthesis/DESIGN_SYNTHESIS.md`.

Under 3500 words. The accepted design (section 3) is the part the
implementer reads; spend disproportionate care on it. Sections 1
and 2 are evidence; section 4 is the design reviewers' agenda.
