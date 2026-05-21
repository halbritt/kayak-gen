# Final Review Prompt

Read the runbook, RFC 0058, `STAGE_1_DECISIONS.md`, implementation
summaries, review artifacts, findings ledger, remediation summary,
changed files, and validation evidence.

Verify:

- the five new Pydantic records (`HullFamilyScope`,
  `StabilityFitMetrics`, `ReviewerSignature`, `StabilityFitRecord`,
  `StabilityFixturePromotionPacket`) + `FixtureRef` live under
  `kayakgen/eval/stability/accepted_fit.py` with `ConfigDict(extra="forbid")`
  and `schema_version: Literal["1"]`;
- threshold constants are module-level and enforced via a
  `model_validator(mode="after")` on `StabilityFitRecord` respecting
  the `strict` field;
- `StabilityFixturePromotionPacket` refuses promotion unless every
  review verdict is "accepted" and `rig_design_match=True`;
- RFC 0058 status flipped to `landed (schemas only)` in the index;
- no fixture or fit is promoted by this RFC;
- RFC 0043's `unvalidated_hydrostatic_comparison` label is untouched;
- full repo suite green; ruff + forbidden-copy + ui-theme orphan +
  import-boundary + services-boundary scans all pass.

The verdict is binary: `accept` only when every line in
`STAGE_1_DECISIONS.md` is reflected and every must-fix is closed.
Otherwise `needs_revision` with a precise list.

Publish a final finding artifact with proper striatum.finding.v1
front matter and verdict.
