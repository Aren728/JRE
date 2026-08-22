"""Shared test fixtures and builders for business domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.business.models import (
    BusinessConfig,
    BusinessOutcomeTaxonomy,
    BusinessRule,
    BusinessRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> BusinessConfig:
    """A minimal BusinessConfig for testing."""
    return BusinessConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[BusinessRule, ...]:
    """A set of business rules for testing."""
    return (
        BusinessRule(
            rule_id="BIZ-TEST-001",
            description="Mercury strong with 10th connection — successful entrepreneurship",
            condition_facts=("mercury_strong=true", "10th_lord_connection=true"),
            outcome=BusinessOutcomeTaxonomy.SUCCESSFUL_ENTREPRENEURSHIP,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        BusinessRule(
            rule_id="BIZ-TEST-002",
            description="7th lord in 10th with Mercury — business partnership",
            condition_facts=("7th_lord_in_10th=true", "mercury_strong=true"),
            outcome=BusinessOutcomeTaxonomy.BUSINESS_PARTNERSHIP,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        BusinessRule(
            rule_id="BIZ-TEST-003",
            description="Saturn afflicting 7th and 10th — business failure",
            condition_facts=("saturn_afflicting_7th=true", "saturn_afflicting_10th=true"),
            outcome=BusinessOutcomeTaxonomy.BUSINESS_FAILURE,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        BusinessRule(
            rule_id="BIZ-TEST-004",
            description="Mars strong in 3rd with Mercury — self employment",
            condition_facts=("mars_in_3rd=true", "mercury_strong=true"),
            outcome=BusinessOutcomeTaxonomy.SELF_EMPLOYMENT,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        BusinessRule(
            rule_id="BIZ-TEST-005",
            description="4th lord strong with 10th connection — family business",
            condition_facts=("4th_lord_strong=true", "10th_lord_connection=true"),
            outcome=BusinessOutcomeTaxonomy.FAMILY_BUSINESS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        BusinessRule(
            rule_id="BIZ-TEST-M1",
            description="Jupiter aspecting 7th mitigates failure risk",
            condition_facts=("jupiter_aspecting_7th=true", "saturn_afflicting_7th=true"),
            outcome=BusinessOutcomeTaxonomy.BUSINESS_FAILURE,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[BusinessRule, ...],
) -> BusinessRuleCatalog:
    """A BusinessRuleCatalog for testing."""
    return BusinessRuleCatalog(rules=sample_rules)


def make_business_rule(
    rule_id: str = "BIZ-001",
    outcome: BusinessOutcomeTaxonomy = BusinessOutcomeTaxonomy.SUCCESSFUL_ENTREPRENEURSHIP,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> BusinessRule:
    """Builder for BusinessRule test objects."""
    return BusinessRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
