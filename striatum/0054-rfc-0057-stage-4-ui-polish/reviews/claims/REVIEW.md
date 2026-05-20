# Review: Claims and User-Facing Boundaries
author: reviewer-claims-gemini-pro-3.1-001
date: 2026-05-20

## Summary
The changes in workflow `0054-rfc-0057-stage-4-ui-polish` have been reviewed for overclaiming, user-facing copy, and forbidden-claim boundaries. The implementation strictly adheres to the standards defined in `tests/test_web_layout.py` and the operator-affirmed decisions in `STAGE_4_DECISIONS.md`.

## Detailed Findings

### 1. Generate Panel Banners and Copy
- **Acknowledgement Copy**: The CFD-in-loop acknowledgement in `kayakgen/ui/web/generate_spec_form.py` uses the exact string: `"I accept evaluation may take orders of magnitude longer"`. This matches the requirement in Decision D-4 and avoids any forbidden solver or worker-queue mentions.
- **Concurrency Advisory**: The soft warning banner uses: `"Multiple jobs in flight; submitting another may slow each."`. This is informational and avoids any claims about server capacity or hosted worker queues.
- **Objective Admissibility**: The form-builder uses `admissible_objective_metrics()` to filter out high-angle GZ display-only metrics and claim-gated metrics (e.g., raw resistance, design fitness). This ensures that the user cannot select forbidden objectives.
- **Inline Refusals**: Metrics not in the allowed set show a neutral refusal: `"Not admissible for the objective set."`.

### 2. Pareto-Frontier View
- **Metric Filtering**: `kayakgen/ui/web/generate_frontier_view.py` uses `FORBIDDEN_METRIC_TOKENS` (e.g., `max_gz_m`, `heel_at_max_gz_deg`) to strip high-angle stability metrics from the view-model summary and parameter maps.
- **Captions and Labels**:
    - Axis labels for forbidden metrics are collapsed to: `"(display-only metric hidden)"`.
    - Table headers and section headings use standard terminology: `"Pareto frontier"`, `"Candidate"`, `"Claim state"`, `"Convergence"`.
- **Claim States**: The view-model preserves the conservative `raw_unvalidated` or `uncalibrated_comparative` states. While `calibrated_model` is present in the color-mapping dictionary, it is not reachable by current backends and does not violate the "no calibrated drag/fitness" rule as it is a literal token, not a user-facing claim of "final prediction".

### 3. Fork Button and Seed Logic
- **Label**: The button label in `kayakgen/ui/web/generate_fork_button.py` is: `"Fork with new seed"`. This is functional and avoids any claims about "optimizing" or "improving" the design.
- **Seed Increment**: The deterministic seed increment (`+1`) is handled silently without promising "better" results.

### 4. Log Redaction (D-11)
- **Path Stripping**: `kayakgen/services/generative_jobs.py` correctly implements `_redact_log_text`, replacing `$HOME` with `~` and the `jobs_root` with `<jobs_root>`. This prevents leaking local filesystem structures and complies with the privacy/security posture of the tool.

### 5. Automated Verification
- `tests/test_web_layout.py` continues to pass, confirming that the central `app.py` and `controllers.py` modules have not regressed into forbidden-claim territory.

## Verdict: PASSED
All user-facing strings are honest, bounded, and respect the negative-claim discipline of the kayak-gen project.
