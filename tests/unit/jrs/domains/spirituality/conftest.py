"""Shared test fixtures and builders for spirituality domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.spirituality.models import (
    SpiritualityConfig,
    SpiritualityOutcomeTaxonomy,
    SpiritualityRule,
    SpiritualityRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> SpiritualityConfig:
    """A minimal SpiritualityConfig for testing."""
    return SpiritualityConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[SpiritualityRule, ...]:
    """A set of spirituality rules for testing."""
    return (
        SpiritualityRule(
            rule_id="R-TEST-001",
            description="Ketu strong with Jupiter — spiritual awakening",
            condition_facts=("ketu_strong=true", "jupiter_strong=true"),
            outcome=SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        SpiritualityRule(
            rule_id="R-TEST-002",
            description="Ketu in 1st with Saturn — renunciation",
            condition_facts=("ketu_in_1st=true", "saturn_strong=true"),
            outcome=SpiritualityOutcomeTaxonomy.RENUNCIATION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        SpiritualityRule(
            rule_id="R-TEST-003",
            description="Saturn in 8th with Ketu — ascetic",
            condition_facts=("saturn_in_8th=true", "ketu_8th_connection=true"),
            outcome=SpiritualityOutcomeTaxonomy.ASCETIC_TENDENCIES,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        SpiritualityRule(
            rule_id="R-TEST-004",
            description="Jupiter strong in Kendra — devotion",
            condition_facts=("jupiter_strong=true", "jupiter_in_kendra=true"),
            outcome=SpiritualityOutcomeTaxonomy.RELIGIOUS_DEVOTION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        SpiritualityRule(
            rule_id="R-TEST-005",
            description="Jupiter mitigates Saturn ascetic",
            condition_facts=("saturn_in_8th=true", "jupiter_aspects_8th=true"),
            outcome=SpiritualityOutcomeTaxonomy.ASCETIC_TENDENCIES,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[SpiritualityRule, ...],
) -> SpiritualityRuleCatalog:
    """A SpiritualityRuleCatalog for testing."""
    return SpiritualityRuleCatalog(rules=sample_rules)


def make_spirituality_rule(
    rule_id: str = "R-001",
    outcome: SpiritualityOutcomeTaxonomy = SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> SpiritualityRule:
    """Builder for SpiritualityRule test objects."""
    return SpiritualityRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
