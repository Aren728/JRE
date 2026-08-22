"""Shared test fixtures and builders for transitions domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.transitions.models import (
    TransitionConfig,
    TransitionOutcomeTaxonomy,
    TransitionRule,
    TransitionRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> TransitionConfig:
    """A minimal TransitionConfig for testing."""
    return TransitionConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[TransitionRule, ...]:
    """A set of transitions rules for testing."""
    return (
        TransitionRule(
            rule_id="R-TEST-001",
            description="Saturn return — life phase shift",
            condition_facts=("saturn_return=true",),
            outcome=TransitionOutcomeTaxonomy.LIFE_PHASE_SHIFT,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        TransitionRule(
            rule_id="R-TEST-002",
            description="Rahu-Ketu axis activated — sudden upheaval",
            condition_facts=("rahu_ketu_axis=true", "rahu_ketu_transit_activation=true"),
            outcome=TransitionOutcomeTaxonomy.SUDDEN_UPHEAVAL,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        TransitionRule(
            rule_id="R-TEST-003",
            description="Saturn slow transit — gradual evolution",
            condition_facts=("saturn_slow_transit_kendra=true",),
            outcome=TransitionOutcomeTaxonomy.GRADUAL_EVOLUTION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        TransitionRule(
            rule_id="R-TEST-004",
            description="8th house activations with benefic — crisis recovery",
            condition_facts=("8th_house_activations=true", "benefic_aspects_8th=true"),
            outcome=TransitionOutcomeTaxonomy.CRISIS_RECOVERY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        TransitionRule(
            rule_id="R-TEST-005",
            description="Jupiter mitigates Rahu-Ketu upheaval",
            condition_facts=("rahu_ketu_axis=true", "jupiter_aspects_rahu_ketu=true"),
            outcome=TransitionOutcomeTaxonomy.SUDDEN_UPHEAVAL,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[TransitionRule, ...],
) -> TransitionRuleCatalog:
    """A TransitionRuleCatalog for testing."""
    return TransitionRuleCatalog(rules=sample_rules)


def make_transition_rule(
    rule_id: str = "R-001",
    outcome: TransitionOutcomeTaxonomy = TransitionOutcomeTaxonomy.LIFE_PHASE_SHIFT,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> TransitionRule:
    """Builder for TransitionRule test objects."""
    return TransitionRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
