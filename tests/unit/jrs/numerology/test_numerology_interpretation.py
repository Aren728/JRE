"""Unit tests for the JRS Numerology interpretation layer.

Tests verify:
- Rule loading from TOML config
- Condition evaluation logic
- EvidenceRecord generation
- SystemAssessment building
- Classification metadata preservation
- Outcome taxonomy correctness
- No false positives from excluded concepts
"""

from __future__ import annotations

import pytest

from jrs.evidence.models import EvidenceDirection, EvidenceRecord, EvidenceStrength
from jrs.numerology.config import load_numerology_config, load_numerology_rules
from jrs.numerology.models import (
    NumerologyOutcomeTaxonomy,
    NumerologyRule,
    NumerologyRuleCatalog,
    build_system_assessment,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
    extract_facts_from_chart,
)
from numerology.service import NumerologyCalculationService

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def calc_svc() -> NumerologyCalculationService:
    """Create a NumerologyCalculationService instance."""
    return NumerologyCalculationService()


@pytest.fixture
def sample_chart(calc_svc: NumerologyCalculationService):
    """Create a sample chart."""
    return calc_svc.calculate(
        birth_date="1985-07-15",
        birth_name="John Adam Smith",
    )


@pytest.fixture
def all_rules() -> tuple[NumerologyRule, ...]:
    """Load all numerology rules from config."""
    return load_numerology_rules()


@pytest.fixture
def rule_catalog(all_rules: tuple[NumerologyRule, ...]) -> NumerologyRuleCatalog:
    """Create a NumerologyRuleCatalog from all rules."""
    return NumerologyRuleCatalog(rules=all_rules)


# ── Rule Loading Tests ───────────────────────────────────────────────────────


class TestRuleLoading:
    """Tests for loading rules from TOML config."""

    def test_rules_load_successfully(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Rules should load from the TOML config."""
        assert len(all_rules) > 0

    def test_minimum_30_rules(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Should have at least 30 rules as specified."""
        assert len(all_rules) >= 30

    def test_all_rules_have_rule_id(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Every rule must have a non-empty rule_id."""
        for rule in all_rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_all_rules_have_source(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Every rule must have a source_id."""
        for rule in all_rules:
            assert rule.source_id, f"Rule {rule.rule_id} missing source_id"

    def test_all_rules_have_description(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Every rule must have a description."""
        for rule in all_rules:
            assert rule.description, f"Rule {rule.rule_id} missing description"

    def test_all_rules_have_valid_outcome(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Every rule must have a valid NumerologyOutcomeTaxonomy outcome."""
        valid_outcomes = {e.value for e in NumerologyOutcomeTaxonomy}
        for rule in all_rules:
            assert rule.outcome.value in valid_outcomes, (
                f"Rule {rule.rule_id} has invalid outcome: {rule.outcome}"
            )

    def test_all_rules_have_valid_direction(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Every rule must have a valid EvidenceDirection."""
        for rule in all_rules:
            assert rule.direction in (
                EvidenceDirection.SUPPORT,
                EvidenceDirection.CONTRADICT,
            ), f"Rule {rule.rule_id} has invalid direction: {rule.direction}"

    def test_all_rules_have_valid_strength(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Every rule must have a valid EvidenceStrength."""
        valid_strengths = {e for e in EvidenceStrength}
        for rule in all_rules:
            assert rule.strength in valid_strengths, (
                f"Rule {rule.rule_id} has invalid strength: {rule.strength}"
            )

    def test_valid_sources_used(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Rules should use valid Pythagorean sources."""
        valid_sources = {"PYTHAGOREAN", "CHEIRO", "MILLMAN"}
        for rule in all_rules:
            assert rule.source_id in valid_sources, (
                f"Rule {rule.rule_id} uses invalid source: {rule.source_id}"
            )

    def test_no_duplicate_rule_ids(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Rule IDs must be unique."""
        ids = [r.rule_id for r in all_rules]
        assert len(ids) == len(set(ids))

    def test_config_loads(self) -> None:
        """Configuration should load correctly."""
        config = load_numerology_config()
        assert config.version == "1.0"
        assert config.source_id == "PYTHAGOREAN"


# ── Condition Evaluation Tests ───────────────────────────────────────────────


class TestConditionEvaluation:
    """Tests for condition evaluation logic."""

    def test_equality_condition(self) -> None:
        """Equality condition should match."""
        facts = {"life_path": "9", "destiny": "3"}
        assert evaluate_condition("life_path=9", facts) is True
        assert evaluate_condition("life_path=8", facts) is False

    def test_inequality_condition(self) -> None:
        """Inequality condition should match."""
        facts = {"life_path": "9"}
        assert evaluate_condition("life_path!=8", facts) is True
        assert evaluate_condition("life_path!=9", facts) is False

    def test_missing_fact_equality(self) -> None:
        """Missing fact for equality should return False."""
        facts = {"life_path": "9"}
        assert evaluate_condition("destiny=3", facts) is False

    def test_missing_fact_inequality(self) -> None:
        """Missing fact for inequality should return True."""
        facts = {"life_path": "9"}
        assert evaluate_condition("destiny!=3", facts) is True

    def test_case_insensitive_comparison(self) -> None:
        """Condition comparison should be case-insensitive."""
        facts = {"life_path_type": "HUMANITARIAN"}
        assert evaluate_condition("life_path_type=humanitarian", facts) is True


# ── Fact Extraction Tests ────────────────────────────────────────────────────


class TestFactExtraction:
    """Tests for extracting facts from NumerologyChart."""

    def test_extracts_life_path(self, sample_chart) -> None:
        """Should extract life_path fact."""
        facts = extract_facts_from_chart(sample_chart)
        assert "life_path" in facts
        assert facts["life_path"] == str(sample_chart.life_path.reduced)

    def test_extracts_destiny(self, sample_chart) -> None:
        """Should extract destiny fact."""
        facts = extract_facts_from_chart(sample_chart)
        assert "destiny" in facts
        assert facts["destiny"] == str(sample_chart.destiny.reduced)

    def test_extracts_soul_urge(self, sample_chart) -> None:
        """Should extract soul_urge fact."""
        facts = extract_facts_from_chart(sample_chart)
        assert "soul_urge" in facts
        assert facts["soul_urge"] == str(sample_chart.soul_urge.reduced)

    def test_extracts_personality(self, sample_chart) -> None:
        """Should extract personality fact."""
        facts = extract_facts_from_chart(sample_chart)
        assert "personality" in facts
        assert facts["personality"] == str(sample_chart.personality.reduced)

    def test_extracts_personal_year(self, sample_chart) -> None:
        """Should extract personal_year fact."""
        facts = extract_facts_from_chart(sample_chart)
        assert "personal_year" in facts
        assert facts["personal_year"] == str(sample_chart.personal_year.reduced)

    def test_extracts_life_path_type(self, sample_chart) -> None:
        """Should extract life_path_type fact."""
        facts = extract_facts_from_chart(sample_chart)
        assert "life_path_type" in facts


# ── Rule Evaluation Tests ────────────────────────────────────────────────────


class TestRuleEvaluation:
    """Tests for evaluating rules against facts."""

    def test_matching_rule_produces_record(
        self, all_rules: tuple[NumerologyRule, ...], sample_chart
    ) -> None:
        """A rule matching the chart should produce an EvidenceRecord."""
        facts = extract_facts_from_chart(sample_chart)
        records = evaluate_facts(all_rules, facts)
        # With life_path=9, destiny=9, soul_urge=8, personality=1
        # Several rules should fire
        assert len(records) > 0

    def test_record_has_correct_rule_id(
        self, all_rules: tuple[NumerologyRule, ...], sample_chart
    ) -> None:
        """EvidenceRecord should reference the correct rule_id."""
        facts = extract_facts_from_chart(sample_chart)
        records = evaluate_facts(all_rules, facts)
        for record in records:
            assert record.rule_id.startswith("N-")

    def test_record_has_source_id(
        self, all_rules: tuple[NumerologyRule, ...], sample_chart
    ) -> None:
        """EvidenceRecord should have a source_id."""
        facts = extract_facts_from_chart(sample_chart)
        records = evaluate_facts(all_rules, facts)
        for record in records:
            assert record.source_id

    def test_evaluate_single_rule(self) -> None:
        """Evaluate a single rule against matching facts."""
        rule = NumerologyRule(
            rule_id="N-TEST-001",
            description="Test rule",
            condition_facts=("life_path=9",),
            outcome=NumerologyOutcomeTaxonomy.PHILOSOPHICAL_DEPTH,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
            source_id="PYTHAGOREAN",
            location="Test",
        )
        facts = {"life_path": "9"}
        record = evaluate_rule(rule, facts)
        assert record is not None
        assert record.rule_id == "N-TEST-001"
        assert record.outcome_taxonomy == "PHILOSOPHICAL_DEPTH"

    def test_evaluate_non_matching_rule(self) -> None:
        """Evaluate a single rule against non-matching facts."""
        rule = NumerologyRule(
            rule_id="N-TEST-002",
            description="Test rule",
            condition_facts=("life_path=1",),
            outcome=NumerologyOutcomeTaxonomy.LEADERSHIP_AUTHORITY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
            source_id="PYTHAGOREAN",
            location="Test",
        )
        facts = {"life_path": "9"}
        record = evaluate_rule(rule, facts)
        assert record is None

    def test_multi_condition_rule_requires_all(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Multi-condition rules should require ALL conditions."""
        # Find a multi-condition rule
        multi_rules = [r for r in all_rules if len(r.condition_facts) > 1]
        if multi_rules:
            rule = multi_rules[0]
            # Provide only partial facts
            partial_facts = {}
            for cond in rule.condition_facts[:1]:
                if "=" in cond:
                    key, val = cond.split("=", 1)
                    partial_facts[key.strip()] = val.strip()
            record = evaluate_rule(rule, partial_facts)
            # Should NOT match (missing other conditions)
            # This depends on the actual rules; skip if ambiguous
            if record is not None:
                # If it matched with partial facts, the rule only has 1 condition
                assert len(rule.condition_facts) == 1


# ── System Assessment Tests ──────────────────────────────────────────────────


class TestSystemAssessment:
    """Tests for building SystemAssessment from evidence records."""

    def test_empty_records_neutral(self) -> None:
        """No records should produce NEUTRAL assessment."""
        assessment = build_system_assessment(())
        assert assessment.assessment_status == "NEUTRAL"
        assert assessment.outcome_taxonomy == "NO_MATCH"

    def test_single_support_record(self) -> None:
        """Single SUPPORT record should produce WEAKLY_SUPPORTED."""
        records = (
            EvidenceRecord(
                evidence_id="test-1",
                outcome_taxonomy="CAREER_PROMINENCE",
                supporting_fact_type="life_path=1",
                rule_id="N-TEST-001",
                source_id="PYTHAGOREAN",
                location="Test",
                direction=EvidenceDirection.SUPPORT,
                strength=EvidenceStrength.HIGH,
            ),
        )
        assessment = build_system_assessment(records)
        assert assessment.assessment_status == "WEAKLY_SUPPORTED"
        assert assessment.outcome_taxonomy == "CAREER_PROMINENCE"

    def test_multiple_support_records(self) -> None:
        """Multiple SUPPORT records for same outcome should produce SUPPORTED."""
        records = (
            EvidenceRecord(
                evidence_id="test-1",
                outcome_taxonomy="CAREER_PROMINENCE",
                supporting_fact_type="life_path=1",
                rule_id="N-TEST-001",
                source_id="PYTHAGOREAN",
                location="Test",
                direction=EvidenceDirection.SUPPORT,
                strength=EvidenceStrength.HIGH,
            ),
            EvidenceRecord(
                evidence_id="test-2",
                outcome_taxonomy="CAREER_PROMINENCE",
                supporting_fact_type="life_path=1",
                rule_id="N-TEST-002",
                source_id="PYTHAGOREAN",
                location="Test",
                direction=EvidenceDirection.SUPPORT,
                strength=EvidenceStrength.MODERATE,
            ),
        )
        assessment = build_system_assessment(records)
        assert assessment.assessment_status == "SUPPORTED"

    def test_assessment_has_numerology_provenance(self) -> None:
        """Assessment should have NUMEROLOGY system type."""
        assessment = build_system_assessment(())
        assert assessment.system_type.value == "NUMEROLOGY"

    def test_assessment_provenance_source(self) -> None:
        """Assessment should have PYTHAGOREAN source tradition."""
        assessment = build_system_assessment(())
        assert assessment.provenance is not None
        assert assessment.provenance.source_tradition == "PYTHAGOREAN"

    def test_strongly_supported(self) -> None:
        """3+ SUPPORT records with 0 CONTRADICT should produce STRONGLY_SUPPORTED."""
        records = tuple(
            EvidenceRecord(
                evidence_id=f"test-{i}",
                outcome_taxonomy="CREATIVE_TALENT",
                supporting_fact_type="life_path=3",
                rule_id=f"N-TEST-{i:03d}",
                source_id="PYTHAGOREAN",
                location="Test",
                direction=EvidenceDirection.SUPPORT,
                strength=EvidenceStrength.HIGH,
            )
            for i in range(3)
        )
        assessment = build_system_assessment(records)
        assert assessment.assessment_status == "STRONGLY_SUPPORTED"


# ── Outcome Taxonomy Tests ───────────────────────────────────────────────────


class TestOutcomeTaxonomy:
    """Tests for NumerologyOutcomeTaxonomy."""

    def test_all_outcomes_have_values(self) -> None:
        """All enum members should have string values."""
        for outcome in NumerologyOutcomeTaxonomy:
            assert isinstance(outcome.value, str)
            assert len(outcome.value) > 0

    def test_no_duplicate_values(self) -> None:
        """No two outcomes should have the same value."""
        values = [o.value for o in NumerologyOutcomeTaxonomy]
        assert len(values) == len(set(values))


# ── Rule Catalog Tests ───────────────────────────────────────────────────────


class TestRuleCatalog:
    """Tests for NumerologyRuleCatalog."""

    def test_catalog_from_rules(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """Catalog should be constructable from rules."""
        catalog = NumerologyRuleCatalog(rules=all_rules)
        assert len(catalog.rules) == len(all_rules)

    def test_get_rules_by_outcome(
        self, rule_catalog: NumerologyRuleCatalog
    ) -> None:
        """Should filter rules by outcome."""
        rules = rule_catalog.get_rules_by_outcome(
            NumerologyOutcomeTaxonomy.LEADERSHIP_AUTHORITY
        )
        for rule in rules:
            assert rule.outcome == NumerologyOutcomeTaxonomy.LEADERSHIP_AUTHORITY

    def test_catalog_serialization(
        self, rule_catalog: NumerologyRuleCatalog
    ) -> None:
        """to_dict should produce valid output."""
        d = rule_catalog.to_dict()
        assert "rules" in d
        assert "rule_count" in d
        assert d["rule_count"] == len(rule_catalog.rules)


# ── Exclusion Tests ──────────────────────────────────────────────────────────


class TestExclusions:
    """Tests verifying excluded modern concepts do NOT appear."""

    def test_no_mercury_retrograde_rules(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """No rules should reference Mercury retrograde pop-astrology."""
        for rule in all_rules:
            assert "mercury retrograde" not in rule.description.lower()
            assert "mercury retrograde" not in rule.rule_id.lower()

    def test_no_karmic_debt_rules(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """No rules should reference karmic debt (New Age concept)."""
        for rule in all_rules:
            assert "karmic debt" not in rule.description.lower()

    def test_no_spiritual_superiority_rules(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """No rules should claim master numbers are spiritually superior."""
        for rule in all_rules:
            assert "spiritually superior" not in rule.description.lower()

    def test_no_personality_type_rules(
        self, all_rules: tuple[NumerologyRule, ...]
    ) -> None:
        """No rules should use pop-psychology personality type language."""
        for rule in all_rules:
            assert "mbti" not in rule.description.lower()
            assert "personality type" not in rule.description.lower()
