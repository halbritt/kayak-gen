# Provenance review - 0012

author: operator [self-declared: operator-provenance-review]
run: run_b8d2bd2b94f345c1a30521671cf0ba67
job: review_provenance
verdict: accept_with_findings

## Summary

The source inventory is acceptable as a gate input, but no candidate source is
safe to vendor as checked-in calibration fixture data today.

## Findings

### P-001 - No candidate has clear fixture redistribution rights

- Severity: blocker
- Source: `SOURCE_INVENTORY.md`
- Statement: Sea Kayaker-derived tables, review PDFs, Gomes papers, and K1
  studies are useful citations, but their tabular data are copyrighted or have
  unclear redistribution terms.
- Required action: Do not check extracted numeric tables into this repository
  without explicit permission or a source license that permits redistribution.

### P-002 - Sea Kayaker-derived sources are compilation/model outputs

- Severity: high
- Statement: The Sea Kayaker/kanu.de sources are broad and sea-kayak-specific,
  but they are compiled magazine/model results rather than a primary open
  measurement dataset.
- Required action: Treat them as citation-only comparison context or
  model-to-model sanity checks.

### P-003 - Open-access modeling papers do not solve the data problem

- Severity: medium
- Statement: MDPI-style open-access kayak physics/modeling articles can provide
  reusable literature context with attribution, but they do not provide a
  canonical resistance calibration dataset.
- Required action: Keep them out of calibration fixtures unless the specific
  article publishes reusable numeric data.

## Gate recommendation

Proceed to ledger and implementation with a no-vendored-dataset gate result.
The safe implementation is a citation/provenance registry and stricter
calibration metadata, not numeric calibration.
