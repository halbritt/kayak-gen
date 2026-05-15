# Implementation Prompt

Read the packet objective, write scope, context docs, and the relevant RFC(s).
Implement only the assigned accepted slice.

Before editing, split your work into the maximal useful number of sub-agent
tasks with disjoint file ownership. Ask sub-agents to edit directly only inside
their assigned files and to report changed paths. Integrate their work and run
focused validation.

Requirements:

- Stay inside the allowed paths.
- Preserve roadmap no-claims wording and behavior.
- Add focused tests proportional to the touched surface.
- Do not start real solver execution, calibrated fitting, fixture promotion,
  hosted deployment, production readiness, or safety/design-fitness claims.
- Publish the required patch summary artifact with exact Striatum front matter
  and byline.
