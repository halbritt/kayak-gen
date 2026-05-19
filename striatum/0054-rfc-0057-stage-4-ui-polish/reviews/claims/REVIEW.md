---
kind: finding
workflow_id: 0054-rfc-0057-stage-4-ui-polish
role: reviewer_claims
verdict: accept
authored_by: claude-opus-4-7 (cowboy mode; striatum runner blocked by halbritt/striatum#24)
---

# Workflow 0054 Claims and User-Facing Boundaries Review

## Scope

Reviewed every new UI string, payload field, and route response for
overclaiming. Confirmed the forbidden-claim scrub-list in
`tests/test_web_layout.py` line 304-323 stays authoritative; no new
allowed-phrase exceptions were introduced.

## Findings

### Accepted

- **CFD-in-loop acknowledgement copy** — exact text "I accept
  evaluation may take orders of magnitude longer" is pre-vetted and
  passes the scrub. No mention of calibration, validated prediction,
  design fitness, or seaworthiness.
- **Fork-with-seed button labels** — "Fork with new seed" carries no
  validation or calibration implication. The forked job inherits the
  source's `result_semantics: "raw_unvalidated"` envelope; the new
  `forked_from` field is informational only.
- **Pareto-frontier captions and tooltips** —
  `kayakgen/ui/web/generate_frontier_view.py::FORBIDDEN_METRIC_TOKENS`
  defensively drops `max_gz_m`, `heel_at_max_gz_deg`,
  `range_positive_stability_deg`, `area_under_positive_gz_m_deg`,
  `righting_moment_nm`, `gz_m` from every row's `summary` before the
  view-model serialises. Verified by
  `tests/test_generate_frontier_view.py::test_*_forbidden_metric_tokens*`.
- **Generate-panel banner** — string contains the allowed phrase
  "no hosted worker is running"; `tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`
  confirms this is the only "hosted" mention in the rendered source.
- **Log redaction surface** — strips `$HOME` and `<jobs_root>` before
  payloads leave the manager; no operator-filesystem leak.
- **`kayakgen serve` startup line** — "generative jobs will run as
  detached subprocesses" / "in-process threads" are operational
  statements, not claims about validation or calibration.

### No banned tokens introduced

Grepped the new modules
(`generate_spec_form.py`, `generate_frontier_view.py`,
`generate_state_listener.py`, `generate_fork_button.py`,
`generative_jobs_fork.py`, redaction additions in
`generative_jobs.py`) for the banned tokens. All clean:

- `max_gz_m`, `heel_at_max_gz_deg`, `range_positive_stability_deg`,
  `area_under_positive_gz_m_deg`, `righting_moment_nm`, `gz_m`
  — absent from UI text; present only in
  `FORBIDDEN_METRIC_TOKENS` defensive scrub set as Python identifiers.
- `fixture_only`, `OpenFOAM`, `SU2`, `worker queue`, `calibrated drag`,
  `design fitness`, `cfd_ready` — absent.
- `final prediction`, `hosted` (outside the allowed phrase), `cloud` — absent.

## Verdict

`accept`. The forbidden-claim scrub stays the enforcement point;
nothing new tripped it. No remediation needed for claim wording.
