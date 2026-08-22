"""Shared test fixtures and builders for progeny domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.progeny.models import (
    ProgenyConfig,
    ProgenyOutcomeTaxonomy,
    ProgenyRule,
    ProgenyRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> ProgenyConfig:
    """A minimal ProgenyConfig for testing."""
    return ProgenyConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[ProgenyRule, ...]:
    """A set of progeny rules for testing."""
    return (
        ProgenyRule(
            rule_id="R-TEST-001",
            description="Jupiter strong with 5th lord in kendra — easy conception",
            condition_facts=("jupiter_strong=true", "5th_lord_in_kendra=true"),
            outcome=ProgenyOutcomeTaxonomy.EASY_CONCEPTION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        ProgenyRule(
            rule_id="R-TEST-002",
            description="Saturn in 5th — delayed progeny",
            condition_facts=("saturn_in_5th=true",),
            outcome=ProgenyOutcomeTaxonomy.DELAYED_PROGENY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        ProgenyRule(
            rule_id="R-TEST-003",
            description="Malefic in 5th without benefic — challenges",
            condition_facts=("malefic_in_5th=true", "benefic_protection_5th=false"),
            outcome=ProgenyOutcomeTaxonomy.CHALLENGES_WITH_CHILDREN,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        ProgenyRule(
            rule_id="R-TEST-004",
            description="Mars in 5th with malefic — miscarriage risk",
            condition_facts=("mars_in_5th=true", "malefic_conjunction_5th=true"),
            outcome=ProgenyOutcomeTaxonomy.MISCARRIAGE_RISK,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        ProgenyRule(
            rule_id="R-TEST-005",
            description="Jupiter mitigates Saturn delay",
            condition_facts=("saturn_in_5th=true", "jupiter_aspecting_5th=true"),
            outcome=ProgenyOutcomeTaxonomy.DELAYED_PROGENY,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[ProgenyRule, ...],
) -> ProgenyRuleCatalog:
    """A ProgenyRuleCatalog for testing."""
    return ProgenyRuleCatalog(rules=sample_rules)


def make_progeny_rule(
    rule_id: str = "R-001",
    outcome: ProgenyOutcomeTaxonomy = ProgenyOutcomeTaxonomy.EASY_CONCEPTION,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> ProgenyRule:
    """Builder for ProgenyRule test objects."""
    return ProgenyRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
