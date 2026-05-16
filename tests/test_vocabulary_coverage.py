"""Regression: every claim/readiness/source-use literal exposed in code is
documented in ``docs/UBIQUITOUS_LANGUAGE.md``.

This is a Phase 1 deliverable of `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`.
If a new literal is introduced anywhere in code, it must land in the glossary
before this test passes.
"""

from __future__ import annotations

from pathlib import Path
from typing import get_args

import pytest

from kayakgen.eval.calibration import SourceReviewVerdict, SourceUse
from kayakgen.eval.claims import ClaimState

REPO_ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = REPO_ROOT / "docs" / "UBIQUITOUS_LANGUAGE.md"


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


def test_glossary_is_not_a_scaffold_placeholder(glossary_text: str) -> None:
    """Regression against the original ``striatum init`` placeholder bodies."""
    assert "TODO — first domain term" not in glossary_text
    assert "TODO — definition" not in glossary_text
