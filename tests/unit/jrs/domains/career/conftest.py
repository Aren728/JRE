"""Shared test fixtures and builders for career domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.career.models import (
    CareerConfig,
    CareerOutcomeTaxonomy,
    CareerRule,
    CareerRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> CareerConfig:
    """A minimal CareerConfig for testing."""
    return CareerConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[CareerRule, ...]:
    """A set of career rules for testing."""
    return (
        CareerRule(
            rule_id="R-TEST-001",
            description="10th lord in kendra — career ascent",
            condition_facts=("10th_lord_in_kendra_or_trikona=true",),
            outcome=CareerOutcomeTaxonomy.CAREER_ASCENT,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        CareerRule(
            rule_id="R-TEST-002",
            description="10th lord debilitated — stagnation",
            condition_facts=("10th_lord_debilitated=true",),
            outcome=CareerOutcomeTaxonomy.PROFESSIONAL_STAGNATION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        CareerRule(
            rule_id="R-TEST-003",
            description="Strong Mercury + Jupiter — business success",
            condition_facts=("mercury_strong=true", "jupiter_aspecting_mercury=true"),
            outcome=CareerOutcomeTaxonomy.SUCCESSFUL_BUSINESS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        CareerRule(
            rule_id="R-TEST-004",
            description="Saturn + Sun on 10th — government service",
            condition_facts=("sun_10th_connection=true", "saturn_10th_connection=true"),
            outcome=CareerOutcomeTaxonomy.GOVERNMENT_SERVICE,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        CareerRule(
            rule_id="R-TEST-005",
            description="Jupiter mitigates Saturn obstacles",
            condition_facts=("saturn_afflicts_10th_lord=true", "jupiter_aspecting_10th=true"),
            outcome=CareerOutcomeTaxonomy.CAREER_OBSTACLES,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[CareerRule, ...],
) -> CareerRuleCatalog:
    """A CareerRuleCatalog for testing."""
    return CareerRuleCatalog(rules=sample_rules)


def make_career_rule(
    rule_id: str = "R-001",
    outcome: CareerOutcomeTaxonomy = CareerOutcomeTaxonomy.CAREER_ASCENT,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> CareerRule:
    """Builder for CareerRule test objects."""
    return CareerRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
