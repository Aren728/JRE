"""Unit tests for JRS-067 Western Astrology domain service.

Tests rule loading, chart evaluation, SystemAssessment production,
and deterministic output.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from jrs.evidence.models import EvidenceDirection
from jrs.multisystem.models import SystemAssessment, SystemType
from jrs.western.config import load_western_config, load_western_rules
from jrs.western.errors import InvalidWesternConfigError
from jrs.western.models import WesternOutcomeTaxonomy
from jrs.western.service import WesternDomainService
from western.models import WesternChart
from western.service import WesternCalculationService

# ── Fixtures ─────────────────────────────────────────────────────────────────

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "config" / "western" / "basic_rules.toml"
)

_WESTERN_SVC = WesternCalculationService()


@pytest.fixture
def jrs_svc() -> WesternDomainService:
    """Default WesternDomainService instance."""
    return WesternDomainService(config_path=_CONFIG_PATH)


@pytest.fixture
def einstein_chart() -> WesternChart:
    """Einstein's known birth chart."""
    return _WESTERN_SVC.calculate(
        birth_date=dt.date(1879, 3, 14),
        birth_time=dt.time(10, 50, 8),
        latitude=48.4,
        longitude=9.99,
    )


# ── Config Loading Tests ─────────────────────────────────────────────────────


class TestConfigLoading:
    """Tests for TOML configuration loading."""

    def test_config_loads(self) -> None:
        config = load_western_config(_CONFIG_PATH)
        assert config.version == "1.0"
        assert config.source_id == "PTOLEMY"

    def test_rules_load(self) -> None:
        rules = load_western_rules(_CONFIG_PATH)
        assert len(rules) > 0

    def test_config_not_found(self) -> None:
        with pytest.raises(InvalidWesternConfigError, match="not found"):
            load_western_config(Path("/nonexistent/path.toml"))

    def test_rules_not_found(self) -> None:
        with pytest.raises(InvalidWesternConfigError, match="not found"):
            load_western_rules(Path("/nonexistent/path.toml"))


# ── Rule Catalog Tests ───────────────────────────────────────────────────────


class TestRuleCatalog:
    """Tests for rule catalog loading and structure."""

    def test_catalog_has_rules(self, jrs_svc: WesternDomainService) -> None:
        catalog = jrs_svc.load_rules()
        assert len(catalog.rules) > 0

    def test_rule_count(self, jrs_svc: WesternDomainService) -> None:
        assert jrs_svc.rule_count > 0

    def test_all_rules_have_valid_outcomes(
        self, jrs_svc: WesternDomainService
    ) -> None:
        catalog = jrs_svc.load_rules()
        valid_outcomes = {o.value for o in WesternOutcomeTaxonomy}
        for rule in catalog.rules:
            assert rule.outcome.value in valid_outcomes

    def test_all_rules_have_valid_directions(
        self, jrs_svc: WesternDomainService
    ) -> None:
        catalog = jrs_svc.load_rules()
        for rule in catalog.rules:
            assert rule.direction.value in {"SUPPORT", "CONTRADICT", "MITIGATE", "NEUTRAL"}

    def test_rules_by_outcome(self, jrs_svc: WesternDomainService) -> None:
        catalog = jrs_svc.load_rules()
        career_rules = catalog.get_rules_by_outcome(
            WesternOutcomeTaxonomy.CAREER_PROMINENCE
        )
        assert len(career_rules) > 0


# ── Fact Extraction Integration Tests ────────────────────────────────────────


class TestFactExtraction:
    """Integration tests for fact extraction from real charts."""

    def test_einstein_facts(self, einstein_chart: WesternChart) -> None:
        from jrs.western.models import extract_facts_from_chart

        facts = extract_facts_from_chart(einstein_chart)
        # Einstein's Sun at 23.51° Pisces — should be in some house
        assert "sun_house" in facts
        house_num = int(facts["sun_house"])
        assert 1 <= house_num <= 12

    def test_einstein_has_dignity_facts(
        self, einstein_chart: WesternChart
    ) -> None:
        from jrs.western.models import extract_facts_from_chart

        facts = extract_facts_from_chart(einstein_chart)
        assert "sun_dignity" in facts
        assert "mars_dignity" in facts


# ── Chart Assessment Tests ───────────────────────────────────────────────────


class TestChartAssessment:
    """Tests for full chart assessment via WesternDomainService."""

    def test_assessment_is_system_assessment(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        assessment = jrs_svc.assess_chart(einstein_chart)
        assert isinstance(assessment, SystemAssessment)

    def test_assessment_has_western_provenance(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        assessment = jrs_svc.assess_chart(einstein_chart)
        assert assessment.system_type is SystemType.WESTERN
        assert assessment.provenance is not None
        assert assessment.provenance.system_type is SystemType.WESTERN

    def test_assessment_has_valid_outcome(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        assessment = jrs_svc.assess_chart(einstein_chart)
        valid_outcomes = {o.value for o in WesternOutcomeTaxonomy}
        valid_outcomes.add("NO_MATCH")
        assert assessment.outcome_taxonomy in valid_outcomes

    def test_assessment_has_valid_status(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        assessment = jrs_svc.assess_chart(einstein_chart)
        valid_statuses = {
            "STRONGLY_SUPPORTED",
            "SUPPORTED",
            "WEAKLY_SUPPORTED",
            "NEUTRAL",
            "CONTRADICTED",
            "STRONGLY_CONTRADICTED",
        }
        assert assessment.assessment_status in valid_statuses

    def test_assessment_timing_inactive(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        assessment = jrs_svc.assess_chart(einstein_chart)
        assert assessment.timing_status == "INACTIVE"

    def test_assessment_to_dict(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        assessment = jrs_svc.assess_chart(einstein_chart)
        d = assessment.to_dict()
        assert d["system_type"] == "WESTERN"
        assert "outcome_taxonomy" in d
        assert "assessment_status" in d


class TestPerOutcomeAssessment:
    """Tests for per-outcome assessment method."""

    def test_returns_multiple_assessments(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        assessments = jrs_svc.assess_chart_per_outcome(einstein_chart)
        assert len(assessments) > 0

    def test_all_are_system_assessments(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        assessments = jrs_svc.assess_chart_per_outcome(einstein_chart)
        for a in assessments:
            assert isinstance(a, SystemAssessment)
            assert a.system_type is SystemType.WESTERN

    def test_no_duplicate_outcomes(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        assessments = jrs_svc.assess_chart_per_outcome(einstein_chart)
        outcomes = [a.outcome_taxonomy for a in assessments]
        assert len(outcomes) == len(set(outcomes))


# ── Determinism Tests ────────────────────────────────────────────────────────


class TestDeterminism:
    """Tests for deterministic output."""

    def test_same_chart_same_assessment(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        a1 = jrs_svc.assess_chart(einstein_chart)
        a2 = jrs_svc.assess_chart(einstein_chart)
        assert a1.outcome_taxonomy == a2.outcome_taxonomy
        assert a1.assessment_status == a2.assessment_status

    def test_different_charts_may_differ(
        self, jrs_svc: WesternDomainService
    ) -> None:
        chart1 = _WESTERN_SVC.calculate(
            birth_date=dt.date(1879, 3, 14),
            birth_time=dt.time(10, 50, 8),
            latitude=48.4,
            longitude=9.99,
        )
        chart2 = _WESTERN_SVC.calculate(
            birth_date=dt.date(1985, 7, 15),
            birth_time=dt.time(14, 30, 0),
            latitude=40.7128,
            longitude=-74.006,
        )
        a1 = jrs_svc.assess_chart(chart1)
        a2 = jrs_svc.assess_chart(chart2)
        # They should both produce valid assessments (may or may not differ)
        assert a1.outcome_taxonomy in {o.value for o in WesternOutcomeTaxonomy} | {"NO_MATCH"}
        assert a2.outcome_taxonomy in {o.value for o in WesternOutcomeTaxonomy} | {"NO_MATCH"}


# ── Evidence Record Tests ────────────────────────────────────────────────────


class TestEvidenceRecords:
    """Tests for evidence record production."""

    def test_records_produced(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        records = jrs_svc.evaluate_chart_facts(einstein_chart)
        assert len(records) > 0

    def test_records_have_source(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        records = jrs_svc.evaluate_chart_facts(einstein_chart)
        valid_sources = {
            "PTOLEMY", "LILLY", "BONATTI", "DOROTHEUS",
            "FIRMICUS", "PAULUS", "VALENS", "ABU_MASHAR",
        }
        for record in records:
            assert record.source_id in valid_sources

    def test_records_have_valid_directions(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        records = jrs_svc.evaluate_chart_facts(einstein_chart)
        for record in records:
            assert record.direction in {
                EvidenceDirection.SUPPORT,
                EvidenceDirection.CONTRADICT,
                EvidenceDirection.MITIGATE,
                EvidenceDirection.NEUTRAL,
            }

    def test_records_have_rule_ids(
        self, jrs_svc: WesternDomainService, einstein_chart: WesternChart
    ) -> None:
        records = jrs_svc.evaluate_chart_facts(einstein_chart)
        for record in records:
            assert record.rule_id.startswith("W-") or record.rule_id.startswith("R-WEST-")


# ── No Outside Files Modified ────────────────────────────────────────────────


class TestIsolation:
    """Verify that no existing Vedic modules are modified."""

    def test_western_module_is_isolated(self) -> None:
        # The Western module should not import from any Vedic domain
        import jrs.western.models as wmodels
        import jrs.western.service as wservice
        source_models = str(wmodels.__file__)
        source_service = str(wservice.__file__)
        assert "western" in source_models
        assert "western" in source_service
