"""Shared test fixtures and builders for migration domain unit tests."""

from __future__ import annotations

import pytest

from jrs.domains.migration.models import (
    MigrationConfig,
    MigrationOutcomeTaxonomy,
    MigrationRule,
    MigrationRuleCatalog,
)
from jrs.evidence.models import EvidenceDirection, EvidenceStrength


@pytest.fixture
def sample_config() -> MigrationConfig:
    """A minimal MigrationConfig for testing."""
    return MigrationConfig(
        version="1.0",
        source_id="BPHS",
        default_strength="MODERATE",
    )


@pytest.fixture
def sample_rules() -> tuple[MigrationRule, ...]:
    """A set of migration rules for testing."""
    return (
        MigrationRule(
            rule_id="R-TEST-001",
            description="Rahu in 12th — foreign settlement",
            condition_facts=("rahu_in_12th=true",),
            outcome=MigrationOutcomeTaxonomy.FOREIGN_SETTLEMENT,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        MigrationRule(
            rule_id="R-TEST-002",
            description="Saturn in 12th — delayed migration",
            condition_facts=("saturn_in_12th=true",),
            outcome=MigrationOutcomeTaxonomy.MIGRATION_DELAY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        MigrationRule(
            rule_id="R-TEST-003",
            description="Mercury strong with 12th — short term travel",
            condition_facts=("mercury_strong=true", "mercury_12th_connection=true"),
            outcome=MigrationOutcomeTaxonomy.SHORT_TERM_TRAVEL,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        MigrationRule(
            rule_id="R-TEST-004",
            description="Saturn afflicting 12th lord — visa obstacles",
            condition_facts=("saturn_afflicts_12th_lord=true", "benefic_protection_12th=false"),
            outcome=MigrationOutcomeTaxonomy.VISA_OBSTACLES,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
        ),
        MigrationRule(
            rule_id="R-TEST-005",
            description="Jupiter mitigates Saturn delay",
            condition_facts=("saturn_in_12th=true", "jupiter_aspecting_12th=true"),
            outcome=MigrationOutcomeTaxonomy.MIGRATION_DELAY,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
        ),
    )


@pytest.fixture
def sample_catalog(
    sample_rules: tuple[MigrationRule, ...],
) -> MigrationRuleCatalog:
    """A MigrationRuleCatalog for testing."""
    return MigrationRuleCatalog(rules=sample_rules)


def make_migration_rule(
    rule_id: str = "R-001",
    outcome: MigrationOutcomeTaxonomy = MigrationOutcomeTaxonomy.FOREIGN_SETTLEMENT,
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    condition_facts: tuple[str, ...] = ("test_fact=true",),
) -> MigrationRule:
    """Builder for MigrationRule test objects."""
    return MigrationRule(
        rule_id=rule_id,
        description=f"Test rule {rule_id}",
        condition_facts=condition_facts,
        outcome=outcome,
        direction=direction,
    )
