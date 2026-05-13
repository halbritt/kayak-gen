# Provenance review - resistance dataset vetting

author: operator [self-declared: operator-provenance-review]
run: run_6ca2095f019345e199943d5f46f0676f
job: review_provenance
date: 2026-05-13
verdict: accept_with_findings

## Scope

Reviewed the source inventory, RFC 0012 source requirements, and the current
source registry. This lane focuses only on access, rights, provenance, and
fixture check-in risk.

## Findings

### P1 - Edinburgh DataShare is legally usable, but attribution/extraction rules are required

The University of Edinburgh DataShare record declares CC BY 4.0 rights for the
dataset. The downloadable workbook and IGES geometry can therefore be reused,
adapted, and shared with attribution if the project preserves citation,
license, source URL, DOI, and extraction method. That is materially stronger
than the prior workflow-0012 sources.

Required before checking in numeric fixture rows:

- a fixture schema with source DOI, license, attribution, source-file URL, sheet
  name, row/filter rules, units, and extraction timestamp;
- a generated-data note if rows are extracted from the spreadsheet rather than
  vendoring the full workbook;
- a clear distinction between dataset license and article copyright.

Classification: actionable now for registry/provenance metadata; not enough
alone to justify calibration.

### P2 - The linked article is citation context, not fixture license

The University of Edinburgh Research Explorer article metadata points to a
Journal of Sailing Technology article and records copyright ownership by SNAME.
Use the article for context, but do not copy article tables or prose as fixture
data. The DataShare dataset license is the reusable source.

Classification: docs/provenance guardrail.

### P3 - Existing Sea Kayaker, Gomes, and Tzabiras classifications still stand

No new rights evidence was found that changes workflow 0012's conclusion:

- Sea Kayaker/KAPER-derived tables remain rights-unclear and model-derived.
- Gomes et al. remains a measured K1 paper without established fixture
  redistribution rights.
- Tzabiras et al. remains useful K1 context without an explicit open data
  fixture license.

Classification: no-go for checked-in calibration fixtures.

## Recommendation

Accept the Edinburgh DataShare source into the registry as a
`validation_candidate` with CC BY 4.0 rights and explicit warnings. Do not
check in extracted numeric fixture data in this workflow unless a fixture schema
and attribution contract land first. Do not mark any source as
`calibration_fixture`.
