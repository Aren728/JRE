"""Unit tests for RI-007 Vetted Classical Primary Wealth Rules.

Each test verifies that a specific fact combination deterministically triggers
the correct WealthOutcomeTaxonomy and EvidenceDirection for the rules added
in the RI-007 controlled integration.

Tests also verify that excluded (modern/unsupported) configurations do NOT
trigger false positives.
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


# ── Saravali Planet-Specific 11th House Gains ────────────────────────────────


class TestSaravali11thHouseGains:
    """Tests for Saravali planet-specific 11th house wealth rules (RI007-001 to 008)."""

    def test_sun_in_11th_wealth(self) -> None:
        """RI007-001: Sun in 11th → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "sun_in_11th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-001")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_sun_not_in_11th_no_fire(self) -> None:
        """RI007-001: Sun not in 11th → no fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "sun_in_11th": False,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-001")
        assert len(matches) == 0

    def test_moon_in_11th_wealth(self) -> None:
        """RI007-002: Moon in 11th → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "moon_in_11th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-002")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_mars_in_11th_wealth(self) -> None:
        """RI007-003: Mars in 11th → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "mars_in_11th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-003")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_mercury_in_11th_multiple_streams(self) -> None:
        """RI007-004: Mercury in 11th → MULTIPLE_INCOME_STREAMS."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "mercury_in_11th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-004")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "MULTIPLE_INCOME_STREAMS"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_jupiter_in_11th_wealth(self) -> None:
        """RI007-005: Jupiter in 11th → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "jupiter_in_11th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-005")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_venus_in_11th_wealth(self) -> None:
        """RI007-006: Venus in 11th → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "venus_in_11th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-006")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_saturn_in_11th_wealth(self) -> None:
        """RI007-007: Saturn in 11th → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "saturn_in_11th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-007")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_rahu_in_11th_wealth(self) -> None:
        """RI007-008: Rahu in 11th → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "rahu_in_11th": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-008")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT


# ── BPHS Ch.13 2nd House Rules ───────────────────────────────────────────────


class TestBPHSCh13SecondHouseRules:
    """Tests for BPHS Ch.13 2nd house wealth rules (RI007-009 to 011)."""

    def test_jupiter_in_2nd_wealth(self) -> None:
        """RI007-009: Jupiter in 2nd → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "jupiter_in_2nd": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-009")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_jupiter_not_in_2nd_no_fire(self) -> None:
        """RI007-009: Jupiter not in 2nd → no fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "jupiter_in_2nd": False,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-009")
        assert len(matches) == 0

    def test_jupiter_2nd_lord_high_dignity(self) -> None:
        """RI007-010: Jupiter as 2nd lord in own sign → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "jupiter_lord_of_2nd": True,
            "jupiter_dignity_high": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-010")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_mercury_2nd_lord_strong(self) -> None:
        """RI007-011: Mercury as 2nd lord strong → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "mercury_lord_of_2nd": True,
            "mercury_strong": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-011")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT


# ── BPHS Ch.41 Dhana Yogas ───────────────────────────────────────────────────


class TestBPHSCh41DhanaYogas:
    """Tests for BPHS Ch.41 opulence yogas (RI007-012 to 013)."""

    def test_5th_11th_lord_own_houses(self) -> None:
        """RI007-012: 5th lord + 11th lord in own houses → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "5th_lord_in_own_house": True,
            "11th_lord_in_own_house": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-012")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_benefics_in_2nd_susubha(self) -> None:
        """RI007-013: Benefics in 2nd without malefic aspect → WEALTH_ACCUMULATION."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "benefics_in_2nd": True,
            "malefic_aspects_2nd": False,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-013")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "WEALTH_ACCUMULATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_benefics_in_2nd_with_malefic_no_fire(self) -> None:
        """RI007-013: Benefics in 2nd WITH malefic aspect → no fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({
            "benefics_in_2nd": True,
            "malefic_aspects_2nd": True,
        })
        matches = _get_records_for_rule(records, "R-WEALTH-RI007-013")
        assert len(matches) == 0


# ── False Positive Prevention ────────────────────────────────────────────────


class TestWealthRI007FalsePositivePrevention:
    """Tests that excluded configurations do NOT trigger false positives."""

    def test_rahu_technology_not_in_ri007_rules(self) -> None:
        """Rahu-technology wealth (Modern Interpretation) should not be an RI-007 rule."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_wealth_rules()
        # No RI-007 rule should mention "technology" in its description
        ri007_tech_rules = [
            r for r in catalog.rules
            if r.rule_id.startswith("R-WEALTH-RI007-")
            and "technology" in r.description.lower()
        ]
        assert len(ri007_tech_rules) == 0

    def test_ketu_crypto_not_in_catalog(self) -> None:
        """Ketu-crypto wealth (UNSUPPORTED) should not be a rule."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_wealth_rules()
        crypto_rules = [
            r for r in catalog.rules
            if "crypto" in r.description.lower()
        ]
        assert len(crypto_rules) == 0

    def test_fashion_industry_not_in_catalog(self) -> None:
        """Venus-Mercury fashion (UNSUPPORTED) should not be a rule."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_wealth_rules()
        fashion_rules = [
            r for r in catalog.rules
            if "fashion" in r.description.lower()
        ]
        assert len(fashion_rules) == 0

    def test_banking_not_in_catalog(self) -> None:
        """Jupiter-Saturn banking (UNSUPPORTED) should not be a rule."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_wealth_rules()
        banking_rules = [
            r for r in catalog.rules
            if "banking" in r.description.lower()
        ]
        assert len(banking_rules) == 0

    def test_empty_facts_no_ri007_rules_fire(self) -> None:
        """With no facts, zero RI-007 rules should fire."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_wealth_facts({})
        ri007_records = [
            r for r in records if r.rule_id.startswith("R-WEALTH-RI007-")
        ]
        assert len(ri007_records) == 0


# ── Integration Tests ────────────────────────────────────────────────────────


class TestWealthRI007Integration:
    """Integration tests for RI-007 wealth rules."""

    def test_ri007_rules_loaded(self) -> None:
        """All 13 RI-007 rules should be present in the catalog."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_wealth_rules()
        ri007_rules = [
            r for r in catalog.rules if r.rule_id.startswith("R-WEALTH-RI007-")
        ]
        assert len(ri007_rules) == 13

    def test_unique_rule_ids(self) -> None:
        """All rule IDs across the full catalog should be unique."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_wealth_rules()
        ids = [r.rule_id for r in catalog.rules]
        assert len(ids) == len(set(ids))

    def test_multi_planet_ri007_firing(self) -> None:
        """Multiple RI-007 rules can fire from a single fact set."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        facts = {
            "sun_in_11th": True,
            "moon_in_11th": True,
            "mars_in_11th": True,
            "jupiter_in_2nd": True,
        }
        records = svc.evaluate_wealth_facts(facts)
        ri007_records = [
            r for r in records if r.rule_id.startswith("R-WEALTH-RI007-")
        ]
        assert len(ri007_records) >= 4
        outcomes = {r.outcome_taxonomy for r in ri007_records}
        assert "WEALTH_ACCUMULATION" in outcomes

    def test_ri007_coexist_with_existing_rules(self) -> None:
        """RI-007 rules should fire alongside existing wealth rules."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        facts = {
            # Existing rule: PW-001
            "jupiter_strong": True,
            "jupiter_in_5th_or_9th": True,
            # RI-007 rule: RI007-009
            "jupiter_in_2nd": True,
        }
        records = svc.evaluate_wealth_facts(facts)
        all_rule_ids = [r.rule_id for r in records]
        assert "R-WEALTH-PW-001" in all_rule_ids
        assert "R-WEALTH-RI007-009" in all_rule_ids

    def test_deterministic_output(self) -> None:
        """Evaluating the same facts twice yields identical rule_ids."""
        svc = WealthDomainService(config_path=_CONFIG_PATH)
        facts = {
            "sun_in_11th": True,
            "mercury_in_11th": True,
            "jupiter_in_2nd": True,
        }
        r1 = svc.evaluate_wealth_facts(facts)
        r2 = svc.evaluate_wealth_facts(facts)
        ids1 = [e.rule_id for e in r1]
        ids2 = [e.rule_id for e in r2]
        assert ids1 == ids2
