"""Shared test fixtures and builders for litigation domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.litigation.models import (
    LitigationConfig,
    LitigationOutcomeTaxonomy,
    LitigationRule,
    LitigationRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> LitigationConfig:
    """A minimal LitigationConfig for testing."""
    return LitigationConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[LitigationRule, ...]:
    """A set of litigation rules for testing."""
    return (
        LitigationRule(
            rule_id="LIT-TEST-001",
            description="6th lord strong with benefic aspect — legal victory",
            condition_facts=("6th_lord_strong=true", "benefic_aspects_6th=true"),
            outcome=LitigationOutcomeTaxonomy.LEGAL_VICTORY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        LitigationRule(
            rule_id="LIT-TEST-002",
            description="Saturn aspecting 7th with Rahu — prolonged litigation",
            condition_facts=("saturn_aspecting_7th=true", "rahu_in_12th=true"),
            outcome=LitigationOutcomeTaxonomy.PROLONGED_LITIGATION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        LitigationRule(
            rule_id="LIT-TEST-003",
            description="6th lord debilitated with malefic — legal defeat",
            condition_facts=("6th_lord_debilitated=true", "malefic_6th=true"),
            outcome=LitigationOutcomeTaxonomy.LEGAL_DEFEAT,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        LitigationRule(
            rule_id="LIT-TEST-004",
            description="Venus strong with 7th connection — settlement",
            condition_facts=("venus_strong=true", "7th_lord_connection=true"),
            outcome=LitigationOutcomeTaxonomy.SETTLEMENT_OUT_OF_COURT,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        LitigationRule(
            rule_id="LIT-TEST-005",
            description="Rahu afflicting 6th lord — false accusations",
            condition_facts=("rahu_afflicting_6th_lord=true", "jupiter_weak=true"),
            outcome=LitigationOutcomeTaxonomy.FALSE_ACCUSATION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        LitigationRule(
            rule_id="LIT-TEST-006",
            description="Mars-Saturn conjunction in 6th — criminal litigation",
            condition_facts=("mars_saturn_conjunction_6th=true", "12th_lord_afflicted=true"),
            outcome=LitigationOutcomeTaxonomy.CRIMINAL_LITIGATION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        LitigationRule(
            rule_id="LIT-TEST-M1",
            description="Jupiter mitigates Saturn prolonged litigation",
            condition_facts=("saturn_aspecting_7th=true", "jupiter_aspecting_7th=true"),
            outcome=LitigationOutcomeTaxonomy.PROLONGED_LITIGATION,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[LitigationRule, ...],
) -> LitigationRuleCatalog:
    """A LitigationRuleCatalog for testing."""
    return LitigationRuleCatalog(rules=sample_rules)


def make_litigation_rule(
    rule_id: str = "LIT-001",
    outcome: LitigationOutcomeTaxonomy = LitigationOutcomeTaxonomy.LEGAL_VICTORY,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> LitigationRule:
    """Builder for LitigationRule test objects."""
    return LitigationRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
