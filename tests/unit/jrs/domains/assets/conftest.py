"""Shared test fixtures and builders for assets domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.assets.models import (
    AssetsConfig,
    AssetsOutcomeTaxonomy,
    AssetsRule,
    AssetsRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> AssetsConfig:
    """A minimal AssetsConfig for testing."""
    return AssetsConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[AssetsRule, ...]:
    """A set of assets rules for testing."""
    return (
        AssetsRule(
            rule_id="ASST-TEST-001",
            description="4th lord strong with benefic — vehicle acquisition",
            condition_facts=("4th_lord_strong=true", "benefic_aspects_4th=true"),
            outcome=AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        AssetsRule(
            rule_id="ASST-TEST-002",
            description="Venus strong in 4th — luxury assets",
            condition_facts=("venus_strong=true", "venus_in_4th=true"),
            outcome=AssetsOutcomeTaxonomy.LUXURY_ASSETS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        AssetsRule(
            rule_id="ASST-TEST-003",
            description="4th lord debilitated with malefic — asset loss",
            condition_facts=("4th_lord_debilitated=true", "malefic_4th=true"),
            outcome=AssetsOutcomeTaxonomy.ASSET_LOSS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        AssetsRule(
            rule_id="ASST-TEST-004",
            description="Mars afflicting 4th with Saturn — vehicle accidents",
            condition_facts=("mars_afflicting_4th=true", "saturn_in_4th=true"),
            outcome=AssetsOutcomeTaxonomy.VEHICLE_ACCIDENTS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        AssetsRule(
            rule_id="ASST-TEST-005",
            description="4th lord strong with multiple benefic — multiple vehicles",
            condition_facts=("4th_lord_strong=true", "multiple_benefics_4th=true"),
            outcome=AssetsOutcomeTaxonomy.MULTIPLE_VEHICLES,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        AssetsRule(
            rule_id="ASST-TEST-006",
            description="4th lord in Kendra with Venus — real estate",
            condition_facts=("4th_lord_in_kendra=true", "venus_strong=true"),
            outcome=AssetsOutcomeTaxonomy.REAL_ESTATE_ASSETS,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        AssetsRule(
            rule_id="ASST-TEST-M1",
            description="Jupiter mitigates Mars vehicle accident risk",
            condition_facts=("mars_afflicting_4th=true", "jupiter_aspecting_4th=true"),
            outcome=AssetsOutcomeTaxonomy.VEHICLE_ACCIDENTS,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[AssetsRule, ...],
) -> AssetsRuleCatalog:
    """An AssetsRuleCatalog for testing."""
    return AssetsRuleCatalog(rules=sample_rules)


def make_assets_rule(
    rule_id: str = "ASST-001",
    outcome: AssetsOutcomeTaxonomy = AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> AssetsRule:
    """Builder for AssetsRule test objects."""
    return AssetsRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
