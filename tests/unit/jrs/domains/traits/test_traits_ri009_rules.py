"""Unit tests for RI-009 Phase 1: Avastha (Planetary State) Trait Modifiers.

Each test verifies that specific BirthSignature + Avastha fact combinations
deterministically trigger the correct TraitOutcomeTaxonomy adjustments.

The 15 Avastha rules are loaded from config/domains/traits.toml and
evaluated against JRE facts (JRE-003 Avastha + JRE-027 BirthSignature).
"""

from __future__ import annotations

from pathlib import Path

from jrs.domains.traits.models import TraitOutcomeTaxonomy
from jrs.domains.traits.service import TraitsDomainService
from jrs.evidence.models import EvidenceDirection

# Path to the TOML config for full-service loading tests.
_CONFIG_PATH = (
    Path(__file__).resolve()
    .parent.parent.parent.parent.parent.parent
    / "config" / "domains" / "traits.toml"
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_records_for_rule(
    records: tuple,
    rule_id: str,
) -> list:
    """Return evidence records matching a specific rule_id."""
    return [r for r in records if r.rule_id == rule_id]


# ── Avastha Rule Loading Tests ───────────────────────────────────────────────


class TestAvasthaRuleLoading:
    """Tests that Avastha rules are correctly loaded from TOML."""

    def test_avastha_rules_loaded(self) -> None:
        """All 15 Avastha rules should be present in the catalog."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        avastha_rules = [
            r for r in catalog.rules if r.rule_id.startswith("R-TRAIT-AVA-")
        ]
        assert len(avastha_rules) == 15

    def test_total_rule_count_increased(self) -> None:
        """Total rule count should be 46 (31 original + 15 Avastha)."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        assert len(catalog.rules) == 46

    def test_avastha_rules_have_valid_outcomes(self) -> None:
        """All Avastha rules must map to valid TraitOutcomeTaxonomy."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        avastha_rules = [
            r for r in catalog.rules if r.rule_id.startswith("R-TRAIT-AVA-")
        ]
        for rule in avastha_rules:
            assert isinstance(rule.outcome, TraitOutcomeTaxonomy)

    def test_avastha_rules_have_direction(self) -> None:
        """All Avastha rules must have SUPPORT or OPPOSE direction."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        avastha_rules = [
            r for r in catalog.rules if r.rule_id.startswith("R-TRAIT-AVA-")
        ]
        for rule in avastha_rules:
            assert rule.direction in (EvidenceDirection.SUPPORT, EvidenceDirection.CONTRADICT)


# ── Sun Avastha Tests ────────────────────────────────────────────────────────


class TestSunAvasthaTraitModifiers:
    """Tests for Sun Avastha modification rules (AVA-001 to AVA-003)."""

    def test_sun_exalted_amplifies_leadership(self) -> None:
        """AVA-001: Sun exalted → SUPPORT LEADERSHIP_TENDENCY."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"sun_avastha": "EXALTED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-001")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "LEADERSHIP_TENDENCY"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_sun_debilitated_opposes_leadership(self) -> None:
        """AVA-002: Sun debilitated → OPPOSE LEADERSHIP_TENDENCY."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"sun_avastha": "DEBILITATED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-002")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "LEADERSHIP_TENDENCY"
        assert matches[0].direction is EvidenceDirection.CONTRADICT

    def test_sun_own_sign_supports_leadership(self) -> None:
        """AVA-003: Sun in own sign → SUPPORT LEADERSHIP_TENDENCY."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"sun_avastha": "OWN_SIGN"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-003")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "LEADERSHIP_TENDENCY"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_sun_exalted_no_fire_when_absent(self) -> None:
        """AVA-001: Sun not exalted → no fire."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"sun_avastha": "DEBILITATED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-001")
        assert len(matches) == 0


# ── Moon Avastha Tests ───────────────────────────────────────────────────────


class TestMoonAvasthaTraitModifiers:
    """Tests for Moon Avastha modification rules (AVA-004 to AVA-005)."""

    def test_moon_exalted_opposes_volatility(self) -> None:
        """AVA-004: Moon exalted → OPPOSE EMOTIONAL_VOLATILITY (stabilizes)."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"moon_avastha": "EXALTED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-004")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "EMOTIONAL_VOLATILITY"
        assert matches[0].direction is EvidenceDirection.CONTRADICT

    def test_moon_debilitated_amplifies_volatility(self) -> None:
        """AVA-005: Moon debilitated → SUPPORT EMOTIONAL_VOLATILITY (destabilizes)."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"moon_avastha": "DEBILITATED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-005")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "EMOTIONAL_VOLATILITY"
        assert matches[0].direction is EvidenceDirection.SUPPORT


# ── Mercury Avastha Tests ────────────────────────────────────────────────────


class TestMercuryAvasthaTraitModifiers:
    """Tests for Mercury Avastha modification rules (AVA-006 to AVA-007)."""

    def test_mercury_exalted_amplifies_intellect(self) -> None:
        """AVA-006: Mercury exalted → SUPPORT INTELLECTUAL_DEPTH."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"mercury_avastha": "EXALTED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-006")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "INTELLECTUAL_DEPTH"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_mercury_debilitated_opposes_intellect(self) -> None:
        """AVA-007: Mercury debilitated → OPPOSE INTELLECTUAL_DEPTH."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"mercury_avastha": "DEBILITATED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-007")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "INTELLECTUAL_DEPTH"
        assert matches[0].direction is EvidenceDirection.CONTRADICT


# ── Jupiter Avastha Tests ────────────────────────────────────────────────────


class TestJupiterAvasthaTraitModifiers:
    """Tests for Jupiter Avastha modification rules (AVA-008 to AVA-009)."""

    def test_jupiter_exalted_amplifies_spiritual(self) -> None:
        """AVA-008: Jupiter exalted → SUPPORT SPIRITUAL_INCLINATION."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"jupiter_avastha": "EXALTED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-008")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "SPIRITUAL_INCLINATION"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_jupiter_debilitated_opposes_spiritual(self) -> None:
        """AVA-009: Jupiter debilitated → OPPOSE SPIRITUAL_INCLINATION."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"jupiter_avastha": "DEBILITATED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-009")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "SPIRITUAL_INCLINATION"
        assert matches[0].direction is EvidenceDirection.CONTRADICT


# ── Venus Avastha Tests ──────────────────────────────────────────────────────


class TestVenusAvasthaTraitModifiers:
    """Tests for Venus Avastha modification rules (AVA-010 to AVA-011)."""

    def test_venus_exalted_amplifies_adaptability(self) -> None:
        """AVA-010: Venus exalted → SUPPORT ADAPTABILITY."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"venus_avastha": "EXALTED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-010")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "ADAPTABILITY"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_venus_debilitated_opposes_adaptability(self) -> None:
        """AVA-011: Venus debilitated → OPPOSE ADAPTABILITY."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"venus_avastha": "DEBILITATED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-011")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "ADAPTABILITY"
        assert matches[0].direction is EvidenceDirection.CONTRADICT


# ── Mars Avastha Tests ───────────────────────────────────────────────────────


class TestMarsAvasthaTraitModifiers:
    """Tests for Mars Avastha modification rules (AVA-012 to AVA-013)."""

    def test_mars_exalted_amplifies_leadership(self) -> None:
        """AVA-012: Mars exalted → SUPPORT LEADERSHIP_TENDENCY."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"mars_avastha": "EXALTED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-012")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "LEADERSHIP_TENDENCY"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_mars_debilitated_opposes_leadership(self) -> None:
        """AVA-013: Mars debilitated → OPPOSE LEADERSHIP_TENDENCY."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"mars_avastha": "DEBILITATED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-013")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "LEADERSHIP_TENDENCY"
        assert matches[0].direction is EvidenceDirection.CONTRADICT


# ── Saturn Avastha Tests ─────────────────────────────────────────────────────


class TestSaturnAvasthaTraitModifiers:
    """Tests for Saturn Avastha modification rules (AVA-014 to AVA-015)."""

    def test_saturn_exalted_amplifies_groundedness(self) -> None:
        """AVA-014: Saturn exalted → SUPPORT PRACTICAL_GROUNDEDNESS."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"saturn_avastha": "EXALTED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-014")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "PRACTICAL_GROUNDEDNESS"
        assert matches[0].direction is EvidenceDirection.SUPPORT

    def test_saturn_debilitated_opposes_groundedness(self) -> None:
        """AVA-015: Saturn debilitated → OPPOSE PRACTICAL_GROUNDEDNESS."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"saturn_avastha": "DEBILITATED"})
        matches = _get_records_for_rule(records, "R-TRAIT-AVA-015")
        assert len(matches) == 1
        assert matches[0].outcome_taxonomy == "PRACTICAL_GROUNDEDNESS"
        assert matches[0].direction is EvidenceDirection.CONTRADICT


# ── False Positive Prevention Tests ──────────────────────────────────────────


class TestAvasthaFalsePositivePrevention:
    """Tests that excluded configurations do NOT trigger false positives."""

    def test_empty_facts_no_avastha_rules_fire(self) -> None:
        """With no facts, zero Avastha rules should fire."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({})
        avastha_records = [
            r for r in records if r.rule_id.startswith("R-TRAIT-AVA-")
        ]
        assert len(avastha_records) == 0

    def test_introvert_not_in_catalog(self) -> None:
        """Introvert/extrovert should not appear in any rule."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        introvert_rules = [
            r for r in catalog.rules
            if "introvert" in r.description.lower()
            or "extrovert" in r.description.lower()
        ]
        assert len(introvert_rules) == 0

    def test_adhd_not_in_catalog(self) -> None:
        """ADHD should not appear in any rule."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        adhd_rules = [
            r for r in catalog.rules
            if "adhd" in r.description.lower()
            or "attention deficit" in r.description.lower()
        ]
        assert len(adhd_rules) == 0

    def test_narcissist_not_in_catalog(self) -> None:
        """Narcissist should not appear in any rule."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        narc_rules = [
            r for r in catalog.rules
            if "narciss" in r.description.lower()
        ]
        assert len(narc_rules) == 0

    def test_twin_flame_not_in_catalog(self) -> None:
        """Twin flame should not appear in any rule."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        tf_rules = [
            r for r in catalog.rules
            if "twin flame" in r.description.lower()
            or "soul mate" in r.description.lower()
        ]
        assert len(tf_rules) == 0

    def test_physical_traits_not_in_avastha_rules(self) -> None:
        """Physical appearance terms should not appear in Avastha rules."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        avastha_rules = [
            r for r in catalog.rules if r.rule_id.startswith("R-TRAIT-AVA-")
        ]
        physical_terms = ["height", "weight", "complexion", "eyes", "nose"]
        for rule in avastha_rules:
            for term in physical_terms:
                assert term not in rule.description.lower(), (
                    f"Rule {rule.rule_id} contains physical term: {term}"
                )

    def test_analytical_thinker_not_in_catalog(self) -> None:
        """Analytical thinker should not appear in any rule."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        at_rules = [
            r for r in catalog.rules
            if "analytical thinker" in r.description.lower()
        ]
        assert len(at_rules) == 0

    def test_burnout_not_in_catalog(self) -> None:
        """Burnout should not appear in any rule."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        burnout_rules = [
            r for r in catalog.rules
            if "burnout" in r.description.lower()
        ]
        assert len(burnout_rules) == 0


# ── Multi-Avastha Combination Tests ──────────────────────────────────────────


class TestMultiAvasthaCombinations:
    """Tests for multiple Avastha rules firing simultaneously."""

    def test_sun_exalted_moon_debilitated(self) -> None:
        """Sun exalted + Moon debilitated → leadership amplified, volatility amplified."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({
            "sun_avastha": "EXALTED",
            "moon_avastha": "DEBILITATED",
        })
        avastha_records = [
            r for r in records if r.rule_id.startswith("R-TRAIT-AVA-")
        ]
        assert len(avastha_records) >= 2
        outcomes = {r.outcome_taxonomy for r in avastha_records}
        assert "LEADERSHIP_TENDENCY" in outcomes
        assert "EMOTIONAL_VOLATILITY" in outcomes

    def test_all_planets_exalted(self) -> None:
        """All planets exalted → 7 EXALTED rules fire (one per planet)."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({
            "sun_avastha": "EXALTED",
            "moon_avastha": "EXALTED",
            "mercury_avastha": "EXALTED",
            "jupiter_avastha": "EXALTED",
            "venus_avastha": "EXALTED",
            "mars_avastha": "EXALTED",
            "saturn_avastha": "EXALTED",
        })
        avastha_records = [
            r for r in records if r.rule_id.startswith("R-TRAIT-AVA-")
        ]
        # 7 planets × 1 EXALTED rule each = 7 rules fire
        assert len(avastha_records) == 7
        outcomes = {r.outcome_taxonomy for r in avastha_records}
        assert len(outcomes) == 6

    def test_all_planets_debilitated(self) -> None:
        """All planets debilitated → 7 DEBILITATED rules fire (one per planet)."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({
            "sun_avastha": "DEBILITATED",
            "moon_avastha": "DEBILITATED",
            "mercury_avastha": "DEBILITATED",
            "jupiter_avastha": "DEBILITATED",
            "venus_avastha": "DEBILITATED",
            "mars_avastha": "DEBILITATED",
            "saturn_avastha": "DEBILITATED",
        })
        avastha_records = [
            r for r in records if r.rule_id.startswith("R-TRAIT-AVA-")
        ]
        # 7 planets × 1 DEBILITATED rule each = 7 rules fire
        assert len(avastha_records) == 7
        # Most debilitated rules are CONTRADICT (weakening their outcome),
        # but Moon debilitated SUPPORTs EMOTIONAL_VOLATILITY (increases it).
        directions = {r.rule_id: r.direction for r in avastha_records}
        assert directions["R-TRAIT-AVA-002"] is EvidenceDirection.CONTRADICT  # Sun
        assert directions["R-TRAIT-AVA-005"] is EvidenceDirection.SUPPORT   # Moon
        assert directions["R-TRAIT-AVA-007"] is EvidenceDirection.CONTRADICT  # Mercury
        assert directions["R-TRAIT-AVA-009"] is EvidenceDirection.CONTRADICT  # Jupiter
        assert directions["R-TRAIT-AVA-011"] is EvidenceDirection.CONTRADICT  # Venus
        assert directions["R-TRAIT-AVA-013"] is EvidenceDirection.CONTRADICT  # Mars
        assert directions["R-TRAIT-AVA-015"] is EvidenceDirection.CONTRADICT  # Saturn


# ── Avastha + Hora Compound Tests ────────────────────────────────────────────


class TestAvasthaHoraCompound:
    """Tests for Avastha + Hora compound effects."""

    def test_mercury_hora_mercury_exalted(self) -> None:
        """Mercury Hora + Mercury exalted → double INTELLECTUAL_DEPTH boost."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({
            "hora": "MERCURY",
            "mercury_avastha": "EXALTED",
        })
        intel_records = [
            r for r in records
            if r.outcome_taxonomy == "INTELLECTUAL_DEPTH"
        ]
        # Should have at least 2 records: one from Hora, one from Avastha
        assert len(intel_records) >= 2
        rule_ids = {r.rule_id for r in intel_records}
        assert "R-TRAIT-INT-001" in rule_ids  # Mercury Hora
        assert "R-TRAIT-AVA-006" in rule_ids  # Mercury exalted

    def test_jupiter_hora_jupiter_exalted(self) -> None:
        """Jupiter Hora + Jupiter exalted → double SPIRITUAL_INCLINATION boost."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({
            "hora": "JUPITER",
            "jupiter_avastha": "EXALTED",
        })
        spiritual_records = [
            r for r in records
            if r.outcome_taxonomy == "SPIRITUAL_INCLINATION"
        ]
        assert len(spiritual_records) >= 2
        rule_ids = {r.rule_id for r in spiritual_records}
        assert "R-TRAIT-SPI-001" in rule_ids  # Jupiter Hora
        assert "R-TRAIT-AVA-008" in rule_ids  # Jupiter exalted

    def test_sun_hora_sun_debilitated(self) -> None:
        """Sun Hora + Sun debilitated → leadership gains then loses."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({
            "hora": "SUN",
            "sun_avastha": "DEBILITATED",
        })
        leadership_records = [
            r for r in records
            if r.outcome_taxonomy == "LEADERSHIP_TENDENCY"
        ]
        assert len(leadership_records) >= 2
        directions = {r.direction for r in leadership_records}
        # Should have both SUPPORT (from Hora) and OPPOSE (from Avastha)
        assert EvidenceDirection.SUPPORT in directions
        assert EvidenceDirection.CONTRADICT in directions


# ── Integration Tests ────────────────────────────────────────────────────────


class TestAvasthaIntegration:
    """Integration tests for Avastha trait modifiers."""

    def test_deterministic_output(self) -> None:
        """Evaluating the same facts twice yields identical rule_ids."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        facts = {
            "sun_avastha": "EXALTED",
            "jupiter_avastha": "DEBILITATED",
            "hora": "MERCURY",
        }
        r1 = svc.evaluate_traits_facts(facts)
        r2 = svc.evaluate_traits_facts(facts)
        ids1 = [r.rule_id for r in r1]
        ids2 = [r.rule_id for r in r2]
        assert ids1 == ids2

    def test_rule_ids_unique(self) -> None:
        """All rule IDs across the full catalog should be unique."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        ids = [r.rule_id for r in catalog.rules]
        assert len(ids) == len(set(ids))

    def test_records_have_correct_fields(self) -> None:
        """All Avastha evidence records have correct fields populated."""
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_traits_facts({"sun_avastha": "EXALTED"})
        avastha_records = [
            r for r in records if r.rule_id.startswith("R-TRAIT-AVA-")
        ]
        for record in avastha_records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)
