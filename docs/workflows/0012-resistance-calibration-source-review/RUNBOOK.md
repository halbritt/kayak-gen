# Runbook - 0012 resistance calibration source review

1. Validate the workflow.
2. Prepare and start the run on `striatum/0012-resistance-calibration-source-review`.
3. Run source inventory first.
4. Run the three review lanes in parallel:
   - source/provenance/licensing;
   - domain/model-fit suitability;
   - implementation/testability.
5. Consolidate the findings.
6. Implement only the safe gate result:
   - if a source is acceptable, add the data/provenance contract and minimal
     fixtures needed for the next resistance-closure workflow;
   - if no source is acceptable, update RFC 0012 and the queue to keep
     resistance uncalibrated.
7. Final review gates whether to proceed to the next queued workflow.

Do not write `.striatum/state.sqlite3` directly. Use the Striatum CLI for run
state.
