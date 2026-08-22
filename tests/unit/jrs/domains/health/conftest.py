"""Shared test fixtures and builders for health domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.health.models import (
    HealthConfig,
    HealthOutcomeTaxonomy,
    HealthRule,
    HealthRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> HealthConfig:
    """A minimal HealthConfig for testing."""
    return HealthConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[HealthRule, ...]:
    """A set of health rules for testing."""
    return (
        HealthRule(
            rule_id="HLTH-TEST-001",
            description="1st lord strong in Kendra — high constitutional vitality",
            condition_facts=("1st_lord_strong=true", "1st_lord_in_kendra=true"),
            outcome=HealthOutcomeTaxonomy.HIGH_VITALITY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        HealthRule(
            rule_id="HLTH-TEST-002",
            description="Saturn in 6th with Rahu — chronic constitutional strain",
            condition_facts=("saturn_in_6th=true", "rahu_in_6th=true"),
            outcome=HealthOutcomeTaxonomy.CHRONIC_STRESS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        HealthRule(
            rule_id="HLTH-TEST-003",
            description="1st lord debilitated with malefic — reduced vitality",
            condition_facts=("1st_lord_debilitated=true", "malefic_lagna=true"),
            outcome=HealthOutcomeTaxonomy.LOW_VITALITY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        HealthRule(
            rule_id="HLTH-TEST-004",
            description="Jupiter aspecting 1st — strong recuperative capacity",
            condition_facts=("jupiter_aspecting_1st=true", "1st_lord_strong=true"),
            outcome=HealthOutcomeTaxonomy.STRONG_RECOVERY_CAPACITY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        HealthRule(
            rule_id="HLTH-TEST-005",
            description="Moon with Rahu — variable constitutional energy",
            condition_facts=("moon_with_rahu=true", "moon_waning=true"),
            outcome=HealthOutcomeTaxonomy.ENERGY_FLUCTUATIONS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        HealthRule(
            rule_id="HLTH-TEST-006",
            description="Lagna lord in own sign — strong traditional constitution",
            condition_facts=("1st_lord_own_sign=true", "ashtakavarga_high=true"),
            outcome=HealthOutcomeTaxonomy.TRADITIONAL_CONSTITUTION_INDICATORS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        HealthRule(
            rule_id="HLTH-TEST-M1",
            description="Jupiter mitigates Saturn chronic strain",
            condition_facts=("saturn_in_6th=true", "jupiter_aspecting_6th=true"),
            outcome=HealthOutcomeTaxonomy.CHRONIC_STRESS,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[HealthRule, ...],
) -> HealthRuleCatalog:
    """A HealthRuleCatalog for testing."""
    return HealthRuleCatalog(rules=sample_rules)


def make_health_rule(
    rule_id: str = "HLTH-001",
    outcome: HealthOutcomeTaxonomy = HealthOutcomeTaxonomy.HIGH_VITALITY,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> HealthRule:
    """Builder for HealthRule test objects."""
    return HealthRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
