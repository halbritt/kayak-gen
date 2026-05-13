# Implement findings prompt

Implement the safe result of the findings ledger.

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent code, test, docs, and review tasks, but keep
one agent responsible for final integration.

Allowed outcomes:

- accepted source: add the calibration data/provenance contract, minimal fixture
  scaffolding if legally safe, and RFC/test updates needed for the next
  workflow;
- validation-only source: update the source registry, provenance notes, and
  tests without changing raw resistance calibration status;
- no accepted source: update RFC 0012 and queue artifacts so the project stays
  explicitly uncalibrated.

Write
`striatum/0023-resistance-calibration-dataset-vetting/implementation/PATCH_SUMMARY.md`.
