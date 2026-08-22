"""Shared test fixtures and builders for property domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.property.models import (
    PropertyConfig,
    PropertyOutcomeTaxonomy,
    PropertyRule,
    PropertyRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> PropertyConfig:
    """A minimal PropertyConfig for testing."""
    return PropertyConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[PropertyRule, ...]:
    """A set of property rules for testing."""
    return (
        PropertyRule(
            rule_id="R-TEST-001",
            description="4th lord strong — property acquisition",
            condition_facts=("4th_lord_strong=true",),
            outcome=PropertyOutcomeTaxonomy.PROPERTY_ACQUISITION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        PropertyRule(
            rule_id="R-TEST-002",
            description="Mars afflicting 4th — property disputes",
            condition_facts=("mars_afflicting_4th=true",),
            outcome=PropertyOutcomeTaxonomy.DISPUTES_OVER_PROPERTY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        PropertyRule(
            rule_id="R-TEST-003",
            description="Venus strong in 4th — real estate wealth",
            condition_facts=("venus_strong=true", "venus_in_4th=true"),
            outcome=PropertyOutcomeTaxonomy.REAL_ESTATE_WEALTH,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        PropertyRule(
            rule_id="R-TEST-004",
            description="4th lord debilitated — loss of property",
            condition_facts=("4th_lord_debilitated=true",),
            outcome=PropertyOutcomeTaxonomy.LOSS_OF_PROPERTY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        PropertyRule(
            rule_id="R-TEST-005",
            description="Jupiter mitigates Mars disputes",
            condition_facts=("mars_afflicting_4th=true", "jupiter_aspecting_4th=true"),
            outcome=PropertyOutcomeTaxonomy.DISPUTES_OVER_PROPERTY,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[PropertyRule, ...],
) -> PropertyRuleCatalog:
    """A PropertyRuleCatalog for testing."""
    return PropertyRuleCatalog(rules=sample_rules)


def make_property_rule(
    rule_id: str = "R-001",
    outcome: PropertyOutcomeTaxonomy = PropertyOutcomeTaxonomy.PROPERTY_ACQUISITION,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> PropertyRule:
    """Builder for PropertyRule test objects."""
    return PropertyRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
