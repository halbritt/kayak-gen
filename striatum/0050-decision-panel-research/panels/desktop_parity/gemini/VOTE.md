---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---
author: panelist-gemini-pro-3.1-003
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

# Vote: Desktop Parity Strategy

**Vote:** Option A (Conservative Default: Web Workspace Primary, Desktop Supporting)

**Decision Sentence:**
Make the Trame web workspace the primary surface for new UI composition and review workflows, while keeping the desktop GUI as a supported legacy/local surface without requiring full native desktop feature parity.

**Evidence and Citations:**
- The existing user guide (`docs/USER_GUIDE.md`) already documents a functional asymmetry: the web shell supports interactive hull inspection, compact analysis, comparison report loading, and a local CFD job panel, whereas the desktop GUI does not natively prepare mesh packages or start CFD jobs.
- The project roadmap (`docs/ROADMAP.md`) marks browser hosting and parity work as `partial`/`blocked` and advises splitting any "desktop parity rewrite or embedding" into independent work "only if still desired".
- RFC 0008 explicitly states in its non-goals that the desktop GUI stays and both web and desktop consume the same core (`docs/rfcs/0008-web-frontend.md`).
- External trame documentation (`https://kitware.github.io/trame/guide/`) confirms it is a robust framework for Python-backed web apps, capable of serving as a serious primary presentation layer without needing a native desktop replacement immediately.

**Why Rejected Alternatives Lose:**
- *Option C (Full Native Desktop Rewrite):* It carries the highest duplication risk. Requiring every new web feature to be manually replicated natively in PyQt/matplotlib/PyVista slows development velocity and competes with critical, blocked roadmap work (e.g., CFD solver dispatch, resistance evidence).
- *Option B (Web Primary Plus Thin Desktop Shell Later):* While a viable future path, pursuing this now prematurely introduces packaging and platform-specific build gates (e.g., PyInstaller, Qt WebEngine wrappers) that distract from core feature delivery.
- *Option D (Web-Only, Deprecate Desktop):* Deprecating the desktop GUI contradicts the explicit "desktop GUI stays" non-goal in RFC 0008 and removes existing, documented functionality (like the `kayakgen view` workflow and PyVista 3D preview) without sufficient user evidence to justify the removal.

**Implementation Gates and No-Claims Language:**
- **Parity Definition:** UI parity means "same core data, same claim boundaries, same implemented hull controls where surfaced", not pixel-matching every plot or duplicating every web workflow natively in the desktop GUI.
- **Web Limitations:** Making the web workspace primary does not imply a completed public hosted demo, full dashboard parity, hosted CFD workers, or a production hosted system. The web frontend remains local/browser-capable with runbook coverage.
- **Desktop Maintenance:** Desktop support remains strictly for local launch, implemented-field sliders, STL export, 3D preview, compatibility, and no-claim/status copy checks.
- **Browser Acceptance:** Web-primary changes still require explicit browser acceptance for initial render, mutation, nonblank 3D, Share reload, STL bytes, and console/network cleanliness before claiming closed browser behavior.
- **Backend Capabilities:** This UI direction does not grant or smuggle new backend capabilities. Mesh-package authoring, real solver execution, calibrated drag, and high-angle GZ stability remain constrained by their respective RFC tracks and separate evidence gates.

**Confidence:** High
