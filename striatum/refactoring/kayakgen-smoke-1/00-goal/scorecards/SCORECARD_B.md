---
schema_version: striatum.finding.v1
artifact_kind: finding
verdict_intent: accept
author: scorekeeper-agy-001
---

# Scorecard: Goal B (Split `kayakgen/ui/web/app.py` along the Generate-panel seam)

author: scorekeeper-agy-001

## Dimension Scores

### preservation_verifiability: High (8/10)
The web interface is backed by 4,798 lines of tests across 9 files (including Playwright `test_web_browser.py`) asserting layout structure and interactive behavior, ensuring any regression during the split is readily caught. The only external API surface is `create_app` and `KayakgenApp`, which remain unchanged.

### blast_radius: Low (3/10)
The refactoring is highly isolated, affecting only files within the `kayakgen/ui/web/` package. The sole cross-package reference is a single private import (`_default_generative_jobs_root_for_app`) in `kayakgen/cli/main.py:657`, which is minor and easily redirected.

### payoff: Very High (9/10)
Decomposing the codebase's largest module (2,550 lines) into modular siblings makes it substantially easier to understand, test, and maintain. App layout, handlers, and the rapidly growing Generate-panel will be isolated into focused, separately reviewable files.

### reversibility: High (8/10)
The proposal decomposes the work into 5 distinct, move-only slices. Each slice is independently landable and can be easily rolled back using standard git operations without affecting other parts of the repository.

### frozen_surface_risk: Low (2/10)
The web UI does not define or touch any JSON schemas, database schemas, claim vocabularies, or golden STL files. The private import in `cli/main.py` is the only minor touchpoint, which can be safely managed with a redirect.

### sliceability: Very High (9/10)
Decomposition into 5 logical, move-only slices (presentation constants, VTK scene helpers, job-wiring, layout, handlers) provides a clear step-by-step path where each slice is separately verifiable by the unit tests.

## Single Biggest Unverified Assumption

The single biggest unverified assumption is that the Playwright real-browser acceptance test suite (`pytest tests/test_web_browser.py -m browser_acceptance`) can be successfully executed and passes green in the current execution environment. If the execution environment lacks Playwright or browser binaries, verification for the layout and handler slices (slices 4 and 5) will be blocked.
