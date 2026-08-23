"""Shared test fixtures and builders for traits domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.traits.models import (
    TraitOutcomeTaxonomy,
    TraitRule,
    TraitRuleCatalog,
    TraitsConfig,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> TraitsConfig:
    """A minimal TraitsConfig for testing."""
    return TraitsConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[TraitRule, ...]:
    """A set of trait rules for testing."""
    return (
        TraitRule(
            rule_id="R-TEST-001",
            description="Mercury hora — intellectual depth",
            condition_facts=("hora=MERCURY",),
            outcome=TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        TraitRule(
            rule_id="R-TEST-002",
            description="SHULA yoga — emotional volatility",
            condition_facts=("yoga=SHULA",),
            outcome=TraitOutcomeTaxonomy.EMOTIONAL_VOLATILITY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        TraitRule(
            rule_id="R-TEST-003",
            description="Saturn hora — practical groundedness",
            condition_facts=("hora=SATURN",),
            outcome=TraitOutcomeTaxonomy.PRACTICAL_GROUNDEDNESS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        TraitRule(
            rule_id="R-TEST-004",
            description="Jupiter hora — spiritual inclination",
            condition_facts=("hora=JUPITER",),
            outcome=TraitOutcomeTaxonomy.SPIRITUAL_INCLINATION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        TraitRule(
            rule_id="R-TEST-005",
            description="Sun hora — leadership tendency",
            condition_facts=("hora=SUN",),
            outcome=TraitOutcomeTaxonomy.LEADERSHIP_TENDENCY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        TraitRule(
            rule_id="R-TEST-006",
            description="Venus hora — adaptability",
            condition_facts=("hora=VENUS",),
            outcome=TraitOutcomeTaxonomy.ADAPTABILITY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[TraitRule, ...],
) -> TraitRuleCatalog:
    """A TraitRuleCatalog for testing."""
    return TraitRuleCatalog(rules=sample_rules)


def make_trait_rule(
    rule_id: str = "R-001",
    outcome: TraitOutcomeTaxonomy = TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> TraitRule:
    """Builder for TraitRule test objects."""
    return TraitRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
