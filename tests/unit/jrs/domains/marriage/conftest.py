"""Shared test fixtures and builders for marriage domain unit tests."""

from __future__ import annotations

from typing import Any

import pytest

from jrs.domains.marriage.models import (
    MarriageConfig,
    MarriageOutcomeTaxonomy,
    MarriageRule,
    MarriageRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> MarriageConfig:
    """A minimal MarriageConfig for testing."""
    return MarriageConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[MarriageRule, ...]:
    """A set of marriage rules for testing."""
    return (
        MarriageRule(
            rule_id="R-TEST-001",
            description="7th lord in kendra — timely marriage",
            condition_facts=("7th_lord_in_kendra_or_trikona=true",),
            outcome=MarriageOutcomeTaxonomy.MARRIAGE_FORMATION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        MarriageRule(
            rule_id="R-TEST-002",
            description="Saturn aspects 7th lord — delayed marriage",
            condition_facts=("saturn_aspects_7th_lord=true",),
            outcome=MarriageOutcomeTaxonomy.DELAYED_MARRIAGE,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        MarriageRule(
            rule_id="R-TEST-003",
            description="7th lord in 8th — spouse loss risk",
            condition_facts=("7th_lord_in_8th=true",),
            outcome=MarriageOutcomeTaxonomy.SPOUSE_LOSS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.MODERATE,
        ),
        MarriageRule(
            rule_id="R-TEST-004",
            description="Venus-Mars connection — love marriage",
            condition_facts=("venus_mars_connection=true",),
            outcome=MarriageOutcomeTaxonomy.LOVE_MARRIAGE,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.MODERATE,
        ),
        MarriageRule(
            rule_id="R-TEST-005",
            description="Jupiter mitigates Saturn delay",
            condition_facts=("saturn_aspects_7th_lord=true", "jupiter_aspects_7th=true"),
            outcome=MarriageOutcomeTaxonomy.DELAYED_MARRIAGE,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
        MarriageRule(
            rule_id="R-TEST-006",
            description="Venus bala threshold for marriage",
            condition_facts=("venus_bala>6.0",),
            outcome=MarriageOutcomeTaxonomy.MARRIAGE_FORMATION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[MarriageRule, ...],
) -> MarriageRuleCatalog:
    """A MarriageRuleCatalog for testing."""
    return MarriageRuleCatalog(rules=sample_rules)


def make_marriage_rule(
    rule_id: str = "R-001",
    outcome: MarriageOutcomeTaxonomy = MarriageOutcomeTaxonomy.MARRIAGE_FORMATION,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> MarriageRule:
    """Builder for MarriageRule test objects."""
    return MarriageRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
