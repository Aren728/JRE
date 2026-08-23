"""Unit tests for JRS-058: Wealth Planetary Pathways (R-WEALTH-PW-* rules).

Each test verifies that a specific fact combination deterministically triggers
the correct WealthOutcomeTaxonomy and EvidenceDirection for one of the 23
planetary pathway rules added in config/domains/wealth.toml.
"""

from __future__ import annotations

from pathlib import Path

from jrs.domains.wealth.service import WealthDomainService
from jrs.evidence.models import EvidenceDirection, EvidenceRecord

# Path to the TOML config for full-service loading tests.
_CONFIG_PATH = (
    Path(__file__).resolve()
    .parent.parent.parent.parent.parent.parent
    / "config" / "domains" / "wealth.toml"
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_records_for_rule(
    records: tuple[EvidenceRecord, ...],
    rule_id: str,
) -> list[EvidenceRecord]:
    """Return evidence records matching a specific rule_id."""
    return [r for r in records if r.rule_id == rule_id]


# ── Jupiter Pathways ─────────────────────────────────────────────────────────


class TestJupiterPathways:
    """Tests for Jupiter wealth pathway rules (R-WEALTH-PW-001 to 003)."""

    def test_jupiter_wisdom_wealth(self) -> None:
        """PW-001: Jupiter strong in 5th/9th → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "jupiter_strong": True,
            "jupiter_in_5th_or_9th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-001")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_jupiter_wisdom_no_match_when_weak(self) -> None:
        """PW-001: Jupiter weak → rule should not fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "jupiter_strong": False,
            "jupiter_in_5th_or_9th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-001")
        assert len(matches) == 0

    def test_jupiter_dharmic_counsel(self) -> None:
        """PW-002: Jupiter as 2nd/11th lord in kendra → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "jupiter_lord_of_2nd_or_11th": True,
            "jupiter_in_kendra": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-002")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_jupiter_dharmic_counsel_partial(self) -> None:
        """PW-002: Only one condition met → rule should not fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "jupiter_lord_of_2nd_or_11th": True,
            "jupiter_in_kendra": False,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-002")
        assert len(matches) == 0

    def test_jupiter_mentorship_stability(self) -> None:
        """PW-003: Jupiter strong aspecting 11th → FINANCIAL_STABILITY."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "jupiter_aspecting_11th": True,
            "jupiter_strong": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-003")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "FINANCIAL_STABILITY"
        assert matches[0].direction is EvidenceDirection.SUPPORT


# ── Saturn Pathways ──────────────────────────────────────────────────────────


class TestSaturnPathways:
    """Tests for Saturn wealth pathway rules (R-WEALTH-PW-004 to 007)."""

    def test_saturn_land_wealth(self) -> None:
        """PW-004: Saturn strong in 4th + Mars → PROPERTY_WEALTH."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "saturn_strong": True,
            "saturn_in_4th": True,
            "mars_4th_connection": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-004")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "PROPERTY_WEALTH"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_saturn_land_wealth_no_match_without_mars(self) -> None:
        """PW-004: Saturn in 4th but no Mars connection → no fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "saturn_strong": True,
            "saturn_in_4th": True,
            "mars_4th_connection": False,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-004")
        assert len(matches) == 0

    def test_saturn_labor_wealth(self) -> None:
        """PW-005: Saturn in 10th strong + benefic → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "saturn_in_10th": True,
            "saturn_strong": True,
            "benefic_aspects_10th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-005")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_saturn_delayed_accumulation(self) -> None:
        """PW-006: Saturn as 11th lord in 11th → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "saturn_in_11th": True,
            "saturn_lord_of_11th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-006")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_saturn_financial_recovery_via_jupiter(self) -> None:
        """PW-007: Saturn afflicts 2nd lord + Jupiter aspect → FINANCIAL_RECOVERY."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "saturn_afflicts_2nd_lord": True,
            "jupiter_aspecting_2nd": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-007")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "FINANCIAL_RECOVERY"
        assert matches[0].direction is EvidenceDirection.SUPPORT


# ── Rahu Pathways ────────────────────────────────────────────────────────────


class TestRahuPathways:
    """Tests for Rahu wealth pathway rules (R-WEALTH-PW-008 to 011)."""

    def test_rahu_foreign_speculative(self) -> None:
        """PW-008: Rahu in 12th with foreign sources → SPECULATIVE_GAINS."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "rahu_in_12th": True,
            "rahu_foreign_sources": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-008")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "SPECULATIVE_GAINS"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_rahu_multiple_income_mercury_11th(self) -> None:
        """PW-009: Rahu in 11th + 11th lord=MERCURY → MULTIPLE_INCOME_STREAMS."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "rahu_in_11th": True,
            "11th_lord": "MERCURY",
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-009")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "MULTIPLE_INCOME_STREAMS"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_rahu_wrong_lord_no_match(self) -> None:
        """PW-009: Rahu in 11th but 11th lord=JUPITER → no fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "rahu_in_11th": True,
            "11th_lord": "JUPITER",
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-009")
        assert len(matches) == 0

    def test_rahu_mercury_business(self) -> None:
        """PW-010: Rahu with Mercury in 7th → BUSINESS_WEALTH."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "rahu_with_mercury_in_7th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-010")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "BUSINESS_WEALTH"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_rahu_speculative_5th(self) -> None:
        """PW-011: Rahu in 5th with speculative → SPECULATIVE_GAINS."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "rahu_in_5th": True,
            "rahu_speculative": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-011")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "SPECULATIVE_GAINS"
        assert matches[0].direction is EvidenceDirection.SUPPORT


# ── Ketu Pathways ────────────────────────────────────────────────────────────


class TestKetuPathways:
    """Tests for Ketu wealth pathway rules (R-WEALTH-PW-012 to 014)."""

    def test_ketu_windfall(self) -> None:
        """PW-012: Ketu in 8th with Jupiter → UNEXPECTED_WINDFALL."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "ketu_in_8th": True,
            "ketu_with_jupiter": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-012")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "UNEXPECTED_WINDFALL"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_ketu_inheritance(self) -> None:
        """PW-013: Ketu in 8th + 8th lord strong → INHERITANCE."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "ketu_in_8th": True,
            "8th_lord_strong": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-013")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "INHERITANCE"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_ketu_charitable(self) -> None:
        """PW-014: Ketu in 12th with detachment → CHARITABLE_DISPOSITION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "ketu_in_12th": True,
            "ketu_detachment": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-014")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "CHARITABLE_DISPOSITION"
        assert matches[0].direction is EvidenceDirection.SUPPORT


# ── Mars Pathways ────────────────────────────────────────────────────────────


class TestMarsPathways:
    """Tests for Mars wealth pathway rules (R-WEALTH-PW-015 to 017)."""

    def test_mars_engineering_wealth(self) -> None:
        """PW-015: Mars strong in 10th → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "mars_strong": True,
            "mars_in_10th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-015")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_mars_engineering_no_match_when_weak(self) -> None:
        """PW-015: Mars weak in 10th → no fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "mars_strong": False,
            "mars_in_10th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-015")
        assert len(matches) == 0

    def test_mars_courage_business(self) -> None:
        """PW-016: Mars as 3rd lord in 3rd → BUSINESS_WEALTH."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "mars_in_3rd": True,
            "mars_lord_of_3rd": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-016")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "BUSINESS_WEALTH"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_mars_property_wealth(self) -> None:
        """PW-017: Mars strong in 4th → PROPERTY_WEALTH."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "mars_strong": True,
            "mars_in_4th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-017")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "PROPERTY_WEALTH"
        assert matches[0].direction is EvidenceDirection.SUPPORT


# ── Mercury Pathways ─────────────────────────────────────────────────────────


class TestMercuryPathways:
    """Tests for Mercury wealth pathway rules (R-WEALTH-PW-018 to 020)."""

    def test_mercury_trade_business(self) -> None:
        """PW-018: Mercury strong in 7th with trade → BUSINESS_WEALTH."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "mercury_strong": True,
            "mercury_in_7th": True,
            "mercury_trade": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-018")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "BUSINESS_WEALTH"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_mercury_trade_partial_no_fire(self) -> None:
        """PW-018: Mercury strong + trade but not in 7th → no fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "mercury_strong": True,
            "mercury_in_7th": False,
            "mercury_trade": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-018")
        assert len(matches) == 0

    def test_mercury_writing_multiple_streams(self) -> None:
        """PW-019: Mercury in 3rd + Jupiter strong → MULTIPLE_INCOME_STREAMS."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "mercury_in_3rd": True,
            "jupiter_strong": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-019")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "MULTIPLE_INCOME_STREAMS"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_mercury_2nd_lord_accumulation(self) -> None:
        """PW-020: Mercury as 2nd lord strong → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "mercury_lord_of_2nd": True,
            "mercury_strong": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-020")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT


# ── Moon Pathways ────────────────────────────────────────────────────────────


class TestMoonPathways:
    """Tests for Moon wealth pathway rules (R-WEALTH-PW-021 to 023)."""

    def test_moon_public_favor_wealth(self) -> None:
        """PW-021: Moon strong in 10th → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "moon_strong": True,
            "moon_in_10th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-021")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_moon_public_favor_no_match_when_weak(self) -> None:
        """PW-021: Moon weak in 10th → no fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "moon_strong": False,
            "moon_in_10th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-021")
        assert len(matches) == 0

    def test_moon_maternal_property(self) -> None:
        """PW-022: Moon strong with 4th connection → PROPERTY_WEALTH."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "moon_strong": True,
            "moon_4th_connection": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-022")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "PROPERTY_WEALTH"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_moon_maternal_inheritance(self) -> None:
        """PW-023: Moon in 4th + 4th lord strong → INHERITANCE."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "moon_in_4th": True,
            "4th_lord_strong": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-PW-023")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "INHERITANCE"
        assert matches[0].direction is EvidenceDirection.SUPPORT


# ── Integration / Cross-Planet Tests ─────────────────────────────────────────


class TestPlanetaryPathwaysIntegration:
    """Integration tests: multiple planetary pathways firing together."""

    def test_all_pw_rules_loaded(self) -> None:
        """All 23 planetary pathway rules should be present in the catalog."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_wealth_rules()
        pw_rules = [
            r for r in catalog.rules if r.rule_id.startswith("R-WEALTH-PW-")
        ]
        assert len(pw_rules) == 23

    def test_unique_rule_ids(self) -> None:
        """All rule IDs across the full catalog should be unique."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_wealth_rules()
        ids = [r.rule_id for r in catalog.rules]
        assert len(ids) == len(set(ids))

    def test_multi_planet_firing(self) -> None:
        """Multiple planetary pathways can fire from a single fact set."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        facts = {
            # Jupiter PW-001
            "jupiter_strong": True,
            "jupiter_in_5th_or_9th": True,
            # Mars PW-015
            "mars_strong": True,
            "mars_in_10th": True,
            # Moon PW-021
            "moon_strong": True,
            "moon_in_10th": True,
        }
        records = svc.evaluate_wealth_facts(facts)
        pw_records = [r for r in records if r.rule_id.startswith("R-WEALTH-PW-")]
        assert len(pw_records) >= 3
        outcomes = {r.outcome_taxonomy for r in pw_records}
        assert "WEALTH_ACCUMULATION" in outcomes

    def test_empty_facts_no_pw_rules_fire(self) -> None:
        """With no facts, zero planetary pathway rules should fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({})
        pw_records = [r for r in records if r.rule_id.startswith("R-WEALTH-PW-")]
        assert len(pw_records) == 0

    def test_deterministic_output(self) -> None:
        """Evaluating the same facts twice yields identical rule_ids."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        facts = {
            "rahu_in_11th": True,
            "11th_lord": "MERCURY",
            "ketu_in_8th": True,
            "ketu_with_jupiter": True,
        }
        r1 = svc.evaluate_wealth_facts(facts)
        r2 = svc.evaluate_wealth_facts(facts)
        ids1 = [e.rule_id for e in r1]
        ids2 = [e.rule_id for e in r2]
        assert ids1 == ids2
