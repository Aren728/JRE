"""Shared test fixtures and builders for wealth domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.wealth.models import (
    WealthConfig,
    WealthOutcomeTaxonomy,
    WealthRule,
    WealthRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> WealthConfig:
    """A minimal WealthConfig for testing."""
    return WealthConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[WealthRule, ...]:
    """A set of wealth rules for testing."""
    return (
        WealthRule(
            rule_id="R-TEST-001",
            description="2nd lord in 11th — wealth accumulation",
            condition_facts=("2nd_lord_in_11th=true",),
            outcome=WealthOutcomeTaxonomy.WEALTH_ACCUMULATION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        WealthRule(
            rule_id="R-TEST-002",
            description="Saturn afflicting 2nd lord — financial loss",
            condition_facts=("saturn_afflicts_2nd_lord=true",),
            outcome=WealthOutcomeTaxonomy.SUDDEN_FINANCIAL_LOSS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        WealthRule(
            rule_id="R-TEST-003",
            description="Mercury strong with 7th connection — business wealth",
            condition_facts=("mercury_strong=true", "mercury_7th_or_10th_connection=true"),
            outcome=WealthOutcomeTaxonomy.BUSINESS_WEALTH,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        WealthRule(
            rule_id="R-TEST-004",
            description="Saturn in 2nd with malefic — debt burden",
            condition_facts=("saturn_in_2nd=true", "malefic_conjunction_2nd=true"),
            outcome=WealthOutcomeTaxonomy.DEBT_BURDEN,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        WealthRule(
            rule_id="R-TEST-005",
            description="Jupiter mitigates Saturn debt burden",
            condition_facts=("saturn_in_2nd=true", "jupiter_aspecting_2nd=true"),
            outcome=WealthOutcomeTaxonomy.DEBT_BURDEN,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[WealthRule, ...],
) -> WealthRuleCatalog:
    """A WealthRuleCatalog for testing."""
    return WealthRuleCatalog(rules=sample_rules)


def make_wealth_rule(
    rule_id: str = "R-001",
    outcome: WealthOutcomeTaxonomy = WealthOutcomeTaxonomy.WEALTH_ACCUMULATION,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> WealthRule:
    """Builder for WealthRule test objects."""
    return WealthRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
