"""Unit tests for MigrationDomainService."""

from __future__ import annotations

from pathlib import Path

import pytest

from jrs.domains.migration.errors import InvalidFactError
from jrs.domains.migration.models import (
    MigrationConfig,
    MigrationOutcomeTaxonomy,
    MigrationRuleCatalog,
)
from jrs.domains.migration.service import MigrationDomainService
from jrs.evidence.models import EvidenceDirection

_CONFIG_PATH = (
    Path(__file__).resolve()
    .parent.parent.parent.parent.parent.parent
    / "config" / "domains" / "migration.toml"
)


class TestMigrationDomainServiceInit:
    """Tests for MigrationDomainService initialization."""

    def test_default_config(self) -> None:
        svc = MigrationDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = MigrationConfig(source_id="Phaladeepika")
        svc = MigrationDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestMigrationDomainServiceLoadRules:
    """Tests for the load_migration_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = MigrationDomainService()
        catalog = svc.load_migration_rules()
        assert isinstance(catalog, MigrationRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = MigrationDomainService()
        catalog = svc.load_migration_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, MigrationOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = MigrationDomainService()
        catalog = svc.load_migration_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = MigrationDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = MigrationDomainService()
        c1 = svc.load_migration_rules()
        c2 = svc.load_migration_rules()
        assert c1.rules is c2.rules


class TestMigrationDomainServiceEvaluateFacts:
    """Tests for the evaluate_migration_facts method."""

    def test_evaluate_foreign_settlement(self) -> None:
        svc = MigrationDomainService()
        facts = {"rahu_in_12th": True}
        records = svc.evaluate_migration_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert MigrationOutcomeTaxonomy.FOREIGN_SETTLEMENT.value in outcomes

    def test_evaluate_visa_obstacles(self) -> None:
        svc = MigrationDomainService()
        facts = {"saturn_afflicts_12th_lord": True, "benefic_protection_12th": False}
        records = svc.evaluate_migration_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert MigrationOutcomeTaxonomy.VISA_OBSTACLES.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = MigrationDomainService()
        records = svc.evaluate_migration_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = MigrationDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_migration_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = MigrationDomainService()
        facts = {"rahu_in_12th": True}
        r1 = svc.evaluate_migration_facts(facts)
        r2 = svc.evaluate_migration_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = MigrationDomainService()
        facts = {"rahu_in_12th": True}
        records = svc.evaluate_migration_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestMigrationDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = MigrationDomainService()
        fset_rules = svc.get_rules_for_outcome(MigrationOutcomeTaxonomy.FOREIGN_SETTLEMENT)
        assert len(fset_rules) > 0
        for rule in fset_rules:
            assert rule.outcome is MigrationOutcomeTaxonomy.FOREIGN_SETTLEMENT

    def test_get_outcome_taxonomies(self) -> None:
        svc = MigrationDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert MigrationOutcomeTaxonomy.FOREIGN_SETTLEMENT in outcomes
        assert MigrationOutcomeTaxonomy.VISA_OBSTACLES in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = MigrationDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)
