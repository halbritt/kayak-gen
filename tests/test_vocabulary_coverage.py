"""Regression: every claim/readiness/source-use literal exposed in code is
documented in ``docs/UBIQUITOUS_LANGUAGE.md``.

This is a Phase 1 deliverable of `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`.
If a new literal is introduced anywhere in code, it must land in the glossary
before this test passes.

The module also pins:

- The six RFC 0057/0058 aggregate-root terms named in the 2026-05-22 audit
  remediation plan (finding ``AUD-P-003``).
- The ``kayakgen runs jobs --state`` enum against the source ``JobState``
  Literal and the documented six-state list in ``docs/USER_GUIDE.md``
  (finding ``AUD-P-004``).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import get_args

import pytest

from kayakgen.eval.calibration import SourceReviewVerdict, SourceUse
from kayakgen.eval.claims import ClaimState
from kayakgen.services.generative_jobs import JobState

REPO_ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = REPO_ROOT / "docs" / "UBIQUITOUS_LANGUAGE.md"
USER_GUIDE = REPO_ROOT / "docs" / "USER_GUIDE.md"


@pytest.fixture(scope="module")
def glossary_text() -> str:
    return GLOSSARY.read_text()


@pytest.mark.parametrize("token", sorted(set(get_args(ClaimState))))
def test_claim_state_literal_documented_in_glossary(token: str, glossary_text: str) -> None:
    """Every ``ClaimState`` literal must appear in the glossary."""
    assert token in glossary_text, (
        f"claim-state literal {token!r} missing from docs/UBIQUITOUS_LANGUAGE.md"
    )


@pytest.mark.parametrize("token", sorted(set(get_args(SourceUse))))
def test_source_use_literal_documented_in_glossary(token: str, glossary_text: str) -> None:
    """Every runtime ``SourceUse`` literal must appear in the glossary."""
    assert token in glossary_text, (
        f"source-use literal {token!r} missing from docs/UBIQUITOUS_LANGUAGE.md"
    )


@pytest.mark.parametrize("token", sorted(set(get_args(SourceReviewVerdict))))
def test_source_review_verdict_documented_in_glossary(
    token: str, glossary_text: str
) -> None:
    """Every ``SourceReviewVerdict`` literal must appear in the glossary."""
    assert token in glossary_text, (
        f"source-review-verdict literal {token!r} missing from "
        f"docs/UBIQUITOUS_LANGUAGE.md"
    )


_READINESS_LITERALS = (
    "cfd_surface_candidate",
    "closed_volume",
    "cfd_ready",
    "solver_unavailable",
    "solver_success_blocked",
    "succeeded",
)


@pytest.mark.parametrize("token", _READINESS_LITERALS)
def test_readiness_literal_documented_in_glossary(
    token: str, glossary_text: str
) -> None:
    """Every readiness-state literal must appear in the glossary."""
    assert token in glossary_text, (
        f"readiness literal {token!r} missing from docs/UBIQUITOUS_LANGUAGE.md"
    )


_DECISION_TOKENS = (
    "CALIBRATION_PROMOTION_REQUIRES_ACCEPTED_FIT",
    "RFC_0043_HIGH_ANGLE_GZ_DISPLAY_ONLY",
    "RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY",
    "VALIDATION_FIXTURE_ADMITS_CALIBRATION_BLOCKERS",
    "VALIDATION_FIXTURE_ADMITS_DOCUMENTED_UNCERTAINTY_CAVEAT",
)


@pytest.mark.parametrize("token", _DECISION_TOKENS)
def test_named_decision_token_documented_in_glossary(
    token: str, glossary_text: str
) -> None:
    """Every named decision token referenced from code must appear in the
    glossary (so a reader can chase it back to the DECISION_LOG row)."""
    assert token in glossary_text, (
        f"decision token {token!r} missing from docs/UBIQUITOUS_LANGUAGE.md"
    )


_RFC_0057_0058_AGGREGATE_TERMS = (
    "GenerativeJob",
    "StabilityFitRecord",
    "StabilityFixturePromotionPacket",
    "MeasuredStabilityFixture",
    "cfd_in_loop_evaluator_status",
    "AnalyticalClaimLabel",
)


@pytest.mark.parametrize("term", _RFC_0057_0058_AGGREGATE_TERMS)
def test_rfc_0057_0058_aggregate_term_documented_in_glossary(
    term: str, glossary_text: str
) -> None:
    """RFC 0057/0058 aggregate-root terms must appear in the glossary.

    Closes ``AUD-P-003`` from the 2026-05-22 code+doc audit. If a term
    is missing here, fix ``docs/UBIQUITOUS_LANGUAGE.md`` (do not relax
    this test).
    """

    assert term in glossary_text, (
        f"RFC 0057/0058 aggregate term {term!r} missing from "
        f"docs/UBIQUITOUS_LANGUAGE.md"
    )


_RFC_0060_PRESENTATION_TERMS = (
    "HullParameterMetadata",
)


@pytest.mark.parametrize("term", _RFC_0060_PRESENTATION_TERMS)
def test_rfc_0060_presentation_term_documented_in_glossary(
    term: str, glossary_text: str
) -> None:
    """RFC 0060 presentation-layer terms must appear in the glossary.

    Closes ``AUD-O-003`` follow-up from the 2026-05-22 code+doc audit.
    ``HullParameterMetadata`` is the value object that drives the web
    Generate-panel friendly labels and tooltips; if it lands in code
    without a glossary entry, a reader cannot trace it back to RFC 0060.
    """

    assert term in glossary_text, (
        f"RFC 0060 presentation term {term!r} missing from "
        f"docs/UBIQUITOUS_LANGUAGE.md"
    )


_EXPECTED_RUNS_JOBS_STATES = frozenset(
    {"queued", "running", "succeeded", "failed", "cancelled", "resumable"}
)


def _parse_documented_runs_jobs_states(user_guide_text: str) -> frozenset[str]:
    """Extract the ``--state`` enum from the documented ``kayakgen runs jobs`` line.

    The user guide line looks like::

        kayakgen runs jobs [--state queued|running|succeeded|failed|cancelled|resumable] \\

    We pull the pipe-separated literal list after ``--state ``.
    """

    pattern = re.compile(
        r"kayakgen\s+runs\s+jobs[^\n]*--state\s+([A-Za-z0-9_|]+)"
    )
    match = pattern.search(user_guide_text)
    if match is None:
        raise AssertionError(
            "Could not find a `kayakgen runs jobs ... --state <enum>` line in "
            "docs/USER_GUIDE.md. The runs jobs state vocabulary regression "
            "test depends on that line; either restore it in the user guide "
            "or update _parse_documented_runs_jobs_states to match the new "
            "documented surface."
        )
    return frozenset(match.group(1).split("|"))


def test_runs_jobs_state_vocabulary_matches_source_and_docs() -> None:
    """Pin ``kayakgen runs jobs --state`` against source + docs.

    Closes ``AUD-P-004`` from the 2026-05-22 code+doc audit. The
    contract is bidirectional: if the runtime ``JobState`` Literal
    drifts from the documented six-state list, this test fails — do
    not "fix" docs to match source or vice versa here; route the fix
    through the parent workflow that owns whichever side actually
    changed.
    """

    runtime_states = frozenset(get_args(JobState))

    assert runtime_states == _EXPECTED_RUNS_JOBS_STATES, (
        "kayakgen.services.generative_jobs.JobState drifted from the "
        f"documented six-state vocabulary; runtime={sorted(runtime_states)!r} "
        f"expected={sorted(_EXPECTED_RUNS_JOBS_STATES)!r}"
    )

    documented_states = _parse_documented_runs_jobs_states(USER_GUIDE.read_text())

    assert documented_states == runtime_states, (
        "docs/USER_GUIDE.md `kayakgen runs jobs --state ...` enum drifted "
        f"from the source JobState Literal; documented={sorted(documented_states)!r} "
        f"runtime={sorted(runtime_states)!r}"
    )


def test_glossary_is_not_a_scaffold_placeholder(glossary_text: str) -> None:
    """Regression against the original ``striatum init`` placeholder bodies."""
    assert "TODO — first domain term" not in glossary_text
    assert "TODO — definition" not in glossary_text
