"""Shared test fixtures and builders for research module unit tests."""

from __future__ import annotations

import pytest

from jrs.research.models import RuleCitation


@pytest.fixture
def sample_citation() -> RuleCitation:
    """A sample RuleCitation for testing."""
    return RuleCitation(
        rule_id="R-TEST-001",
        source="BPHS",
        source_full="Brihat Parashara Hora Shastra",
        location="Chapter 14, Verse 5",
        claim="2nd lord in 11th house indicates wealth accumulation",
        evidence_class="wealth_accumulation",
        modern_normalization="2nd_lord_in_11th",
        domain="wealth",
    )


def make_rule_citation(
    rule_id: str = "R-001",
    source: str = "BPHS",
    source_full: str = "Brihat Parashara Hora Shastra",
    location: str = "Chapter 1, Verse 1",
    claim: str = "Test claim",
    evidence_class: str = "test_class",
    modern_normalization: str = "test_fact",
    domain: str = "test",
) -> RuleCitation:
    """Builder for RuleCitation test objects."""
    return RuleCitation(
        rule_id=rule_id,
        source=source,
        source_full=source_full,
        location=location,
        claim=claim,
        evidence_class=evidence_class,
        modern_normalization=modern_normalization,
        domain=domain,
    )
