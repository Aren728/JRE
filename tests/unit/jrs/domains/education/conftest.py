"""Shared test fixtures and builders for education domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.education.models import (
    EducationConfig,
    EducationOutcomeTaxonomy,
    EducationRule,
    EducationRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> EducationConfig:
    """A minimal EducationConfig for testing."""
    return EducationConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[EducationRule, ...]:
    """A set of education rules for testing."""
    return (
        EducationRule(
            rule_id="R-TEST-001",
            description="4th lord in kendra — higher education",
            condition_facts=("4th_lord_in_kendra=true",),
            outcome=EducationOutcomeTaxonomy.HIGHER_EDUCATION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        EducationRule(
            rule_id="R-TEST-002",
            description="Saturn in 4th — education disruption",
            condition_facts=("saturn_in_4th=true",),
            outcome=EducationOutcomeTaxonomy.EDUCATION_DISRUPTION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        EducationRule(
            rule_id="R-TEST-003",
            description="Mercury strong with 4th — early success",
            condition_facts=("mercury_strong=true", "mercury_4th_connection=true"),
            outcome=EducationOutcomeTaxonomy.EARLY_EDUCATION_SUCCESS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        EducationRule(
            rule_id="R-TEST-004",
            description="Ketu in 4th with Jupiter — research",
            condition_facts=("ketu_in_4th=true", "jupiter_strong=true"),
            outcome=EducationOutcomeTaxonomy.RESEARCH_ACADEMIA,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        EducationRule(
            rule_id="R-TEST-005",
            description="Jupiter mitigates Saturn disruption",
            condition_facts=("saturn_in_4th=true", "jupiter_aspecting_4th=true"),
            outcome=EducationOutcomeTaxonomy.EDUCATION_DISRUPTION,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[EducationRule, ...],
) -> EducationRuleCatalog:
    """An EducationRuleCatalog for testing."""
    return EducationRuleCatalog(rules=sample_rules)


def make_education_rule(
    rule_id: str = "R-001",
    outcome: EducationOutcomeTaxonomy = EducationOutcomeTaxonomy.HIGHER_EDUCATION,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> EducationRule:
    """Builder for EducationRule test objects."""
    return EducationRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
