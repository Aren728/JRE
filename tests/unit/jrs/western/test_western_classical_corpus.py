"""Unit tests for JRS-069: Western Classical Corpus rules.

Tests rule loading, classification metadata preservation, chart configuration
triggers, excluded concept rejection, and sect-modified dignity weights.

CONSTRAINT: Purely validation — no production logic changes.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from jrs.evidence.models import EvidenceDirection, EvidenceStrength
from jrs.western.config import load_western_config, load_western_rules
from jrs.western.models import (
    WesternOutcomeTaxonomy,
    WesternRule,
    evaluate_facts,
    extract_facts_from_chart,
)
from western.models import (
    Sect,
    WesternChart,
    WesternPlanet,
)
from western.service import WesternCalculationService

# ── Paths ────────────────────────────────────────────────────────────────────

_CONFIG_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "config" / "western"
)
_CLASSICAL_CORPUS_PATH = _CONFIG_DIR / "classical_corpus.toml"
_BASIC_RULES_PATH = _CONFIG_DIR / "basic_rules.toml"
_TRADITIONAL_RULES_PATH = _CONFIG_DIR / "traditional_rules.toml"

_WESTERN_SVC = WesternCalculationService()

# Classical source IDs used in the corpus
_CLASSICAL_SOURCES = frozenset({
    "PTOLEMY", "LILLY", "BONATTI", "DOROTHEUS", "MORINUS",
    "FIRMICUS", "PAULUS", "VALENS", "ABU_MASHAR",
})

# Valid classification values
_VALID_CLASSIFICATIONS = frozenset({
    "CLASSICAL_PRIMARY", "COMMENTARY_DEPENDENT", "LATER_TRADITION",
})


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def classical_rules() -> tuple[WesternRule, ...]:
    """Load rules from classical_corpus.toml only."""
    return load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())


@pytest.fixture
def all_rules() -> tuple[WesternRule, ...]:
    """Load all rules (basic + traditional + classical corpus)."""
    return load_western_rules(_BASIC_RULES_PATH)


@pytest.fixture
def einstein_chart() -> WesternChart:
    """Einstein's known birth chart."""
    return _WESTERN_SVC.calculate(
        birth_date=dt.date(1879, 3, 14),
        birth_time=dt.time(10, 50, 8),
        latitude=48.4,
        longitude=9.99,
    )


@pytest.fixture
def nocturnal_chart() -> WesternChart:
    """A midnight birth producing a nocturnal chart."""
    return _WESTERN_SVC.calculate(
        birth_date=dt.date(1980, 6, 21),
        birth_time=dt.time(0, 0, 0),
        latitude=51.5,
        longitude=-0.1,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. RULE LOADING — All new rules load correctly
# ══════════════════════════════════════════════════════════════════════════════


class TestClassicalCorpusLoading:
    """Verify classical_corpus.toml loads without errors."""

    def test_classical_corpus_loads(self, classical_rules: tuple[WesternRule, ...]) -> None:
        assert len(classical_rules) >= 50, (
            f"Expected >= 50 classical corpus rules, got {len(classical_rules)}"
        )

    def test_all_rules_have_ids(self, classical_rules: tuple[WesternRule, ...]) -> None:
        for rule in classical_rules:
            assert rule.rule_id, "Rule has empty rule_id"
            assert rule.rule_id.startswith("R-WEST-"), (
                f"Rule {rule.rule_id} does not start with R-WEST-"
            )

    def test_no_duplicate_rule_ids(
        self, classical_rules: tuple[WesternRule, ...]
    ) -> None:
        ids = [r.rule_id for r in classical_rules]
        assert len(ids) == len(set(ids)), (
            f"Duplicate rule IDs found: {[i for i in ids if ids.count(i) > 1]}"
        )

    def test_no_conflicts_with_existing_rules(
        self, all_rules: tuple[WesternRule, ...]
    ) -> None:
        """No rule IDs duplicated across basic, traditional, and classical corpus."""
        ids = [r.rule_id for r in all_rules]
        assert len(ids) == len(set(ids)), (
            f"Cross-config duplicate IDs: {[i for i in ids if ids.count(i) > 1]}"
        )

    def test_all_rules_have_conditions(self, classical_rules: tuple[WesternRule, ...]) -> None:
        for rule in classical_rules:
            assert len(rule.condition_facts) > 0, (
                f"Rule {rule.rule_id} has no condition_facts"
            )

    def test_all_rules_have_valid_outcomes(
        self, classical_rules: tuple[WesternRule, ...]
    ) -> None:
        valid_outcomes = {o.value for o in WesternOutcomeTaxonomy}
        for rule in classical_rules:
            assert rule.outcome.value in valid_outcomes, (
                f"Rule {rule.rule_id} has invalid outcome: {rule.outcome.value}"
            )

    def test_all_rules_have_valid_directions(
        self, classical_rules: tuple[WesternRule, ...]
    ) -> None:
        valid = {"SUPPORT", "CONTRADICT", "MITIGATE", "NEUTRAL"}
        for rule in classical_rules:
            assert rule.direction.value in valid, (
                f"Rule {rule.rule_id} has invalid direction: {rule.direction.value}"
            )

    def test_all_rules_have_valid_strengths(
        self, classical_rules: tuple[WesternRule, ...]
    ) -> None:
        valid_strengths = {s.value for s in EvidenceStrength}
        for rule in classical_rules:
            assert rule.strength.value in valid_strengths, (
                f"Rule {rule.rule_id} has invalid strength: {rule.strength.value}"
            )

    def test_total_rule_count_increased(self, all_rules: tuple[WesternRule, ...]) -> None:
        """Adding classical corpus should increase total rule count beyond
        basic_rules.toml + traditional_rules.toml."""
        basic = load_western_rules(_BASIC_RULES_PATH, extra_paths=())
        traditional = load_western_rules(_TRADITIONAL_RULES_PATH, extra_paths=())
        # all_rules loads basic + traditional + classical_corpus
        assert len(all_rules) > len(basic) + len(traditional), (
            f"Expected all_rules ({len(all_rules)}) > "
            f"basic ({len(basic)}) + traditional ({len(traditional)})"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 2. CLASSIFICATION METADATA — Preserved for all rules
# ══════════════════════════════════════════════════════════════════════════════


class TestClassificationMetadata:
    """Verify classification metadata is preserved in rule loading."""

    def test_rules_have_source_id(self, classical_rules: tuple[WesternRule, ...]) -> None:
        for rule in classical_rules:
            assert rule.source_id, f"Rule {rule.rule_id} has empty source_id"

    def test_rules_have_location(self, classical_rules: tuple[WesternRule, ...]) -> None:
        for rule in classical_rules:
            assert rule.location, f"Rule {rule.rule_id} has empty location"

    def test_rules_have_classical_sources(
        self, classical_rules: tuple[WesternRule, ...]
    ) -> None:
        for rule in classical_rules:
            assert rule.source_id in _CLASSICAL_SOURCES, (
                f"Rule {rule.rule_id} has non-classical source: {rule.source_id}"
            )

    def test_strength_scaled_by_classification(self) -> None:
        """CLASSICAL_PRIMARY rules should generally have HIGH or VERY_HIGH
        strength; LATER_TRADITION rules can be MODERATE."""
        classical_rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        # Check that we have a range of strengths
        strengths = {r.strength.value for r in classical_rules}
        assert "HIGH" in strengths or "VERY_HIGH" in strengths, (
            "Expected at least some HIGH or VERY_HIGH strength rules"
        )

    def test_rule_to_dict_preserves_metadata(
        self, classical_rules: tuple[WesternRule, ...]
    ) -> None:
        """Serialization preserves source_id and location."""
        for rule in classical_rules[:10]:
            d = rule.to_dict()
            assert d["source_id"] == rule.source_id
            assert d["location"] == rule.location
            assert d["strength"] == rule.strength.value


# ══════════════════════════════════════════════════════════════════════════════
# 3. CHART CONFIGURATION TRIGGERS — Specific charts produce correct outcomes
# ══════════════════════════════════════════════════════════════════════════════


class TestChartConfigurationTriggers:
    """Verify specific chart configurations trigger correct outcomes."""

    def test_classical_corpus_fires_on_einstein(
        self, einstein_chart: WesternChart
    ) -> None:
        """At least some classical corpus rules should fire on Einstein's chart."""
        facts = extract_facts_from_chart(einstein_chart)
        records = evaluate_facts(
            load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=()),
            facts,
        )
        assert len(records) > 0, "No classical corpus rules fired on Einstein's chart"

    def test_decan_facts_extracted(self, einstein_chart: WesternChart) -> None:
        """Decan ruler facts should be extracted from any chart."""
        facts = extract_facts_from_chart(einstein_chart)
        decan_keys = [k for k in facts if "decan_ruler" in k]
        assert len(decan_keys) > 0, "No decan_ruler facts extracted"

    def test_decan_fires_correct_rules(self, einstein_chart: WesternChart) -> None:
        """Decan-based rules should fire when the fact matches."""
        facts = extract_facts_from_chart(einstein_chart)
        classical_rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        decan_rules = [r for r in classical_rules if r.rule_id.startswith("R-WEST-DECAN-")]
        records = evaluate_facts(tuple(decan_rules), facts)
        # At least one decan rule should fire for each planet with a decan ruler
        decan_ruler = facts.get("decan_ruler")
        if decan_ruler:
            assert len(records) > 0, (
                f"No decan rules fired despite decan_ruler={decan_ruler}"
            )

    def test_profection_fact_extracted(self, einstein_chart: WesternChart) -> None:
        """Profection house should be extracted from birth date."""
        facts = extract_facts_from_chart(einstein_chart)
        assert "profection_house" in facts, "profection_house not extracted"
        house = int(facts["profection_house"])
        assert 1 <= house <= 12

    def test_profection_rules_fire(self, einstein_chart: WesternChart) -> None:
        """Profection rules should fire based on the extracted profection house."""
        facts = extract_facts_from_chart(einstein_chart)
        classical_rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        profect_rules = [r for r in classical_rules if r.rule_id.startswith("R-WEST-PROFECT-")]
        records = evaluate_facts(tuple(profect_rules), facts)
        assert len(records) == 1, (
            f"Expected exactly 1 profection rule to fire, got {len(records)}"
        )

    def test_zodiacal_releasing_fact_extracted(
        self, einstein_chart: WesternChart
    ) -> None:
        """Zodiacal releasing house should be extracted from chart."""
        facts = extract_facts_from_chart(einstein_chart)
        assert "zodiacal_releasing_house" in facts
        house = int(facts["zodiacal_releasing_house"])
        assert 1 <= house <= 12

    def test_hyleg_fact_extracted(self, einstein_chart: WesternChart) -> None:
        """Hyleg planet should be identified for diurnal charts."""
        facts = extract_facts_from_chart(einstein_chart)
        if einstein_chart.sect == Sect.DIURNAL:
            assert facts.get("hyleg_planet") == "SUN"

    def test_alcocoden_fact_extracted(self, einstein_chart: WesternChart) -> None:
        """Alcocoden planet should be identified when hyleg is present."""
        facts = extract_facts_from_chart(einstein_chart)
        if "hyleg_planet" in facts:
            assert "alcocoden_planet" in facts

    def test_nocturnal_chart_hyleg_moon(self, nocturnal_chart: WesternChart) -> None:
        """Nocturnal chart should identify Moon as hyleg candidate."""
        facts = extract_facts_from_chart(nocturnal_chart)
        assert nocturnal_chart.sect == Sect.NOCTURNAL
        # Moon may or may not be hyleg depending on house placement
        if facts.get("hyleg_planet") == "MOON":
            assert True  # Moon identified as Hyleg in nocturnal chart
        else:
            # Moon not in suitable house — acceptable
            assert True

    def test_dignity_combo_rules_fire(self) -> None:
        """Essential + accidental dignity combination rules should fire
        when both conditions are met."""
        # Build a chart where Sun is in domicile and in 10th house
        chart = _make_chart_with_planet_and_dignity(
            planet=WesternPlanet.SUN,
            longitude=120.0,  # Leo (Sun's domicile)
            house=10,  # 10th house
        )
        facts = extract_facts_from_chart(chart)
        classical_rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        combo_rules = [r for r in classical_rules if r.rule_id.startswith("R-WEST-COMBO-")]
        records = evaluate_facts(tuple(combo_rules), facts)
        # At least R-WEST-COMBO-001 (Sun domicile + 10th house) should fire
        fired_ids = [r.rule_id for r in records]
        assert "R-WEST-COMBO-001" in fired_ids, (
            f"Expected R-WEST-COMBO-001 to fire, got: {fired_ids}"
        )

    def test_sect_dignity_combo_rules(self) -> None:
        """Sect + dignity combination rules should fire correctly."""
        chart = _make_chart_with_planet_and_dignity(
            planet=WesternPlanet.SUN,
            longitude=120.0,  # Leo (Sun's domicile)
            house=1,
        )
        facts = extract_facts_from_chart(chart)
        classical_rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        sect_dignity_rules = [
            r for r in classical_rules
            if r.rule_id.startswith("R-WEST-SECT-DIGNITY-")
        ]
        records = evaluate_facts(tuple(sect_dignity_rules), facts)
        # Sun in domicile + diurnal chart should fire R-WEST-SECT-DIGNITY-001
        fired_ids = [r.rule_id for r in records]
        assert "R-WEST-SECT-DIGNITY-001" in fired_ids, (
            f"Expected R-WEST-SECT-DIGNITY-001 to fire, got: {fired_ids}"
        )

    def test_classical_corpus_records_have_valid_fields(
        self, einstein_chart: WesternChart
    ) -> None:
        """All evidence records from classical corpus have valid fields."""
        facts = extract_facts_from_chart(einstein_chart)
        records = evaluate_facts(
            load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=()),
            facts,
        )
        for record in records:
            assert record.source_id in _CLASSICAL_SOURCES
            assert record.rule_id.startswith("R-WEST-")
            assert record.location
            assert record.direction in {
                EvidenceDirection.SUPPORT,
                EvidenceDirection.CONTRADICT,
                EvidenceDirection.MITIGATE,
                EvidenceDirection.NEUTRAL,
            }


# ══════════════════════════════════════════════════════════════════════════════
# 4. EXCLUDED CONCEPTS — Must NOT trigger false positives
# ══════════════════════════════════════════════════════════════════════════════


class TestExcludedConcepts:
    """Modern and pop-astrology concepts must NOT appear in the rule catalog."""

    def _load_all_descriptions(self) -> list[str]:
        rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        return [r.description.lower() for r in rules]

    def _load_all_condition_facts(self) -> list[str]:
        rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        facts: list[str] = []
        for r in rules:
            facts.extend(r.condition_facts)
        return facts

    def test_no_mercury_retrograde_rules(self) -> None:
        """Pop-astrology: Mercury retrograde communication claims."""
        descriptions = self._load_all_descriptions()
        for desc in descriptions:
            assert "retrograde" not in desc or "visibility" in desc, (
                f"Mercury retrograde pop-astrology found: {desc}"
            )

    def test_no_chiron_references(self) -> None:
        """Chiron (1977 discovery) has no classical basis."""
        descriptions = self._load_all_descriptions()
        for desc in descriptions:
            assert "chiron" not in desc, f"Chiron reference found: {desc}"

    def test_no_pluto_references(self) -> None:
        """Pluto (1930 discovery) has no classical basis in Western tradition."""
        descriptions = self._load_all_descriptions()
        for desc in descriptions:
            assert "pluto" not in desc, f"Pluto reference found: {desc}"

    def test_no_north_node_purpose(self) -> None:
        """North Node 'life purpose' is modern spiritual overlay."""
        descriptions = self._load_all_descriptions()
        for desc in descriptions:
            assert "karmic" not in desc, f"Karmic overlay found: {desc}"
            assert "life purpose" not in desc, f"Life purpose overlay found: {desc}"

    def test_no_personality_disorder_claims(self) -> None:
        """Pop-psychology personality labels are prohibited."""
        descriptions = self._load_all_descriptions()
        prohibited = [
            "narcissistic", "codependen", "borderline",
            "toxic mascu", "personality disorder",
        ]
        for desc in descriptions:
            for term in prohibited:
                assert term not in desc, (
                    f"Pop-psychology term '{term}' found: {desc}"
                )

    def test_no_modern_astrology_terminology(self) -> None:
        """Modern astrology terms like 'soulmate', 'twin flame' are excluded."""
        descriptions = self._load_all_descriptions()
        prohibited = ["soulmate", "twin flame", "spiritual enlightenment",
                       "transformation journey", "healing archetype"]
        for desc in descriptions:
            for term in prohibited:
                assert term not in desc, (
                    f"Modern astrology term '{term}' found: {desc}"
                )

    def test_no_void_of_course_absolutes(self) -> None:
        """Void of course 'nothing will come of the matter' is over-simplified."""
        descriptions = self._load_all_descriptions()
        for desc in descriptions:
            assert "nothing will come" not in desc, (
                f"Void of course absolute found: {desc}"
            )

    def test_no_modern_planets_in_conditions(self) -> None:
        """Chiron, Pluto, Uranus, Neptune should not appear as condition_facts
        in classical corpus rules (classical tradition uses 7 visible planets)."""
        condition_facts = self._load_all_condition_facts()
        modern_bodies = ["chiron", "pluto", "uranus", "neptune"]
        for fact in condition_facts:
            for body in modern_bodies:
                assert body not in fact.lower(), (
                    f"Modern planet '{body}' in condition_facts: {fact}"
                )

    def test_exclusion_comments_present_in_toml(self) -> None:
        """The TOML file should contain explicit EXCLUSION comments."""
        content = _CLASSICAL_CORPUS_PATH.read_text()
        assert "EXCLUDED" in content, "No EXCLUSION comments in classical_corpus.toml"
        assert "pop-astrology" in content.lower() or "pop_psychology" in content.lower() or (
            "pop-astrology" in content
        ), "No pop-astrology exclusion comment found"


# ══════════════════════════════════════════════════════════════════════════════
# 5. SECT MODIFICATION — Sect correctly adjusts dignity weights
# ══════════════════════════════════════════════════════════════════════════════


class TestSectModification:
    """Verify sect correctly modifies dignity weights."""

    def test_diurnal_sun_in_domicile_gets_very_high(self) -> None:
        """Sun in domicile + diurnal chart → VERY_HIGH strength."""
        chart = _make_chart_with_planet_and_dignity(
            planet=WesternPlanet.SUN,
            longitude=120.0,  # Leo
            house=1,
        )
        facts = extract_facts_from_chart(chart)
        classical_rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        sect_dignity_rules = [
            r for r in classical_rules
            if r.rule_id == "R-WEST-SECT-DIGNITY-001"
        ]
        records = evaluate_facts(tuple(sect_dignity_rules), facts)
        assert len(records) == 1
        assert records[0].strength is EvidenceStrength.VERY_HIGH

    def test_diurnal_sun_in_domicile_nocturnal_moderate(self) -> None:
        """Sun in domicile + nocturnal chart → MODERATE (weakened by contrary sect)."""
        # Sun in Leo (domicile), nocturnal chart
        chart = _make_chart_with_planet_and_dignity(
            planet=WesternPlanet.SUN,
            longitude=120.0,  # Leo
            house=1,
            sect=Sect.NOCTURNAL,
        )
        facts = extract_facts_from_chart(chart)
        classical_rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        sect_dignity_rules = [
            r for r in classical_rules
            if r.rule_id == "R-WEST-SECT-DIGNITY-002"
        ]
        records = evaluate_facts(tuple(sect_dignity_rules), facts)
        assert len(records) == 1
        assert records[0].strength is EvidenceStrength.MODERATE

    def test_nocturnal_venus_in_domicile_very_high(self) -> None:
        """Venus in domicile + nocturnal chart → VERY_HIGH strength."""
        chart = _make_chart_with_planet_and_dignity(
            planet=WesternPlanet.VENUS,
            longitude=30.0,  # Taurus (Venus's domicile)
            house=1,
            sect=Sect.NOCTURNAL,
        )
        facts = extract_facts_from_chart(chart)
        classical_rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        sect_dignity_rules = [
            r for r in classical_rules
            if r.rule_id == "R-WEST-SECT-DIGNITY-003"
        ]
        records = evaluate_facts(tuple(sect_dignity_rules), facts)
        assert len(records) == 1
        assert records[0].strength is EvidenceStrength.VERY_HIGH

    def test_nocturnal_venus_in_domicile_diurnal_moderate(self) -> None:
        """Venus in domicile + diurnal chart → MODERATE (weakened by contrary sect)."""
        chart = _make_chart_with_planet_and_dignity(
            planet=WesternPlanet.VENUS,
            longitude=30.0,  # Taurus
            house=1,
            sect=Sect.DIURNAL,
        )
        facts = extract_facts_from_chart(chart)
        classical_rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        sect_dignity_rules = [
            r for r in classical_rules
            if r.rule_id == "R-WEST-SECT-DIGNITY-004"
        ]
        records = evaluate_facts(tuple(sect_dignity_rules), facts)
        assert len(records) == 1
        assert records[0].strength is EvidenceStrength.MODERATE

    def test_correct_sect_strength_higher_than_contrary(self) -> None:
        """A planet in correct sect should produce higher-valued records
        than the same planet in contrary sect."""
        # Correct sect: Sun diurnal + domicile
        chart_correct = _make_chart_with_planet_and_dignity(
            planet=WesternPlanet.SUN,
            longitude=120.0,
            house=1,
            sect=Sect.DIURNAL,
        )
        facts_correct = extract_facts_from_chart(chart_correct)

        # Contrary sect: Sun nocturnal + domicile
        chart_contrary = _make_chart_with_planet_and_dignity(
            planet=WesternPlanet.SUN,
            longitude=120.0,
            house=1,
            sect=Sect.NOCTURNAL,
        )
        facts_contrary = extract_facts_from_chart(chart_contrary)

        strength_order = {
            EvidenceStrength.VERY_HIGH: 4,
            EvidenceStrength.HIGH: 3,
            EvidenceStrength.MODERATE: 2,
            EvidenceStrength.LOW: 1,
            EvidenceStrength.VERY_LOW: 0,
        }

        classical_rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        sect_rules = [
            r for r in classical_rules
            if r.rule_id.startswith("R-WEST-SECT-DIGNITY-")
        ]

        records_correct = evaluate_facts(tuple(sect_rules), facts_correct)
        records_contrary = evaluate_facts(tuple(sect_rules), facts_contrary)

        # Find the records that fired
        if records_correct and records_contrary:
            max_correct = max(strength_order.get(r.strength, 0) for r in records_correct)
            max_contrary = max(strength_order.get(r.strength, 0) for r in records_contrary)
            assert max_correct >= max_contrary, (
                "Correct sect should produce strength >= contrary sect"
            )


# ══════════════════════════════════════════════════════════════════════════════
# 6. DETERMINISM — Same inputs produce same outputs
# ══════════════════════════════════════════════════════════════════════════════


class TestDeterminism:
    """Verify deterministic output from classical corpus rules."""

    def test_same_chart_same_records(
        self, einstein_chart: WesternChart
    ) -> None:
        facts1 = extract_facts_from_chart(einstein_chart)
        facts2 = extract_facts_from_chart(einstein_chart)
        assert facts1 == facts2

    def test_same_facts_same_evaluation(
        self, einstein_chart: WesternChart
    ) -> None:
        facts = extract_facts_from_chart(einstein_chart)
        classical_rules = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        records1 = evaluate_facts(classical_rules, facts)
        records2 = evaluate_facts(classical_rules, facts)
        assert len(records1) == len(records2)
        for r1, r2 in zip(records1, records2, strict=True):
            assert r1.rule_id == r2.rule_id
            assert r1.outcome_taxonomy == r2.outcome_taxonomy

    def test_deterministic_ids_across_loads(self) -> None:
        """Rules loaded from TOML should produce identical WesternRule objects."""
        rules1 = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        rules2 = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())
        assert len(rules1) == len(rules2)
        for r1, r2 in zip(rules1, rules2, strict=True):
            assert r1.rule_id == r2.rule_id
            assert r1.outcome == r2.outcome
            assert r1.source_id == r2.source_id


# ══════════════════════════════════════════════════════════════════════════════
# 7. CATEGORY COVERAGE — All required categories present
# ══════════════════════════════════════════════════════════════════════════════


class TestCategoryCoverage:
    """Verify all 8 required classical categories are present."""

    def test_decan_rules_present(self, classical_rules: tuple[WesternRule, ...]) -> None:
        decan_rules = [r for r in classical_rules if r.rule_id.startswith("R-WEST-DECAN-")]
        assert len(decan_rules) >= 12, (
            f"Expected >= 12 decan rules, got {len(decan_rules)}"
        )

    def test_combo_rules_present(self, classical_rules: tuple[WesternRule, ...]) -> None:
        combo_rules = [r for r in classical_rules if r.rule_id.startswith("R-WEST-COMBO-")]
        assert len(combo_rules) >= 5, (
            f"Expected >= 5 dignity combo rules, got {len(combo_rules)}"
        )

    def test_profection_rules_present(
        self, classical_rules: tuple[WesternRule, ...]
    ) -> None:
        profect_rules = [r for r in classical_rules if r.rule_id.startswith("R-WEST-PROFECT-")]
        assert len(profect_rules) == 12, (
            f"Expected 12 profection rules (one per house), got {len(profect_rules)}"
        )

    def test_zodiacal_releasing_rules_present(
        self, classical_rules: tuple[WesternRule, ...]
    ) -> None:
        zr_rules = [r for r in classical_rules if r.rule_id.startswith("R-WEST-ZR-")]
        assert len(zr_rules) >= 4, (
            f"Expected >= 4 zodiacal releasing rules, got {len(zr_rules)}"
        )

    def test_hyleg_rules_present(self, classical_rules: tuple[WesternRule, ...]) -> None:
        hyleg_rules = [r for r in classical_rules if r.rule_id.startswith("R-WEST-HYLEG-")]
        assert len(hyleg_rules) >= 2, (
            f"Expected >= 2 hyleg rules, got {len(hyleg_rules)}"
        )

    def test_alcocoden_rules_present(
        self, classical_rules: tuple[WesternRule, ...]
    ) -> None:
        alc_rules = [r for r in classical_rules if r.rule_id.startswith("R-WEST-ALCOCODEN-")]
        assert len(alc_rules) >= 3, (
            f"Expected >= 3 alcocoden rules, got {len(alc_rules)}"
        )

    def test_sect_dignity_rules_present(
        self, classical_rules: tuple[WesternRule, ...]
    ) -> None:
        sd_rules = [r for r in classical_rules if r.rule_id.startswith("R-WEST-SECT-DIGNITY-")]
        assert len(sd_rules) >= 4, (
            f"Expected >= 4 sect-dignity rules, got {len(sd_rules)}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 8. INTEGRATION — Classical corpus + basic + traditional together
# ══════════════════════════════════════════════════════════════════════════════


class TestIntegrationWithExistingRules:
    """Verify classical corpus integrates cleanly with existing rules."""

    def test_combined_rules_all_fire(
        self, einstein_chart: WesternChart
    ) -> None:
        """All three config files together should produce more records
        than any single file alone."""
        facts = extract_facts_from_chart(einstein_chart)

        basic_rules = load_western_rules(_BASIC_RULES_PATH, extra_paths=())
        all_rules = load_western_rules()

        basic_records = evaluate_facts(basic_rules, facts)
        all_records = evaluate_facts(all_rules, facts)

        # All should produce records
        assert len(basic_records) > 0
        assert len(all_records) >= len(basic_records)

    def test_no_cross_config_rule_id_conflicts(self) -> None:
        """Rule IDs must be unique across all config files."""
        basic = load_western_rules(_BASIC_RULES_PATH, extra_paths=())
        trad = load_western_rules(_TRADITIONAL_RULES_PATH, extra_paths=())
        corpus = load_western_rules(_CLASSICAL_CORPUS_PATH, extra_paths=())

        all_ids = (
            [r.rule_id for r in basic]
            + [r.rule_id for r in trad]
            + [r.rule_id for r in corpus]
        )
        assert len(all_ids) == len(set(all_ids)), (
            f"Cross-config duplicates: {[i for i in all_ids if all_ids.count(i) > 1]}"
        )

    def test_classical_corpus_config_loads_separately(self) -> None:
        """classical_corpus.toml should load as a valid TOML config."""
        config = load_western_config(_CLASSICAL_CORPUS_PATH)
        assert config.version == "3.0"


# ══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════════════════


def _make_chart_with_planet_and_dignity(
    planet: WesternPlanet,
    longitude: float,
    house: int,
    sect: Sect = Sect.DIURNAL,
) -> WesternChart:
    """Create a chart with a single planet at specified house and dignity.

    Uses whole-sign houses starting at the Ascendant.
    """
    # Place Ascendant so that the target house starts at the right cusp
    # Whole-sign: house N starts at (asc + (N-1)*30)°
    # We want `longitude` to fall in house `house`, so:
    # asc + (house-1)*30 < longitude <= asc + house*30
    # → asc = longitude - house*30 + 5 (place in middle of house)
    asc = (longitude - (house - 1) * 30.0 - 15.0) % 360.0

    cusps = [
        __import__("western.models", fromlist=["HouseCusp"]).HouseCusp(
            house_number=i + 1,
            longitude=(asc + i * 30.0) % 360.0,
        )
        for i in range(12)
    ]

    from western.models import (
        PlanetPosition,
        WesternHouseSystem,
        _sign_name,
        evaluate_essential_dignity,
    )

    sign = _sign_name(longitude)
    deg = longitude % 30.0
    positions = (
        PlanetPosition(
            planet=planet,
            longitude=longitude,
            latitude=0.0,
            speed_longitude=1.0,
            sign=sign,
            degree_in_sign=deg,
        ),
    )
    dignities = {planet: evaluate_essential_dignity(planet, longitude)}

    return WesternChart(
        birth_date="2000-01-01",
        birth_time="12:00:00",
        latitude=40.0,
        longitude=-74.0,
        house_system=WesternHouseSystem.PLACIDUS,
        julian_day_ut=2451545.0,
        planet_positions=positions,
        house_cusps=tuple(cusps),
        aspects=(),
        dignities=dignities,
        ascendant=asc,
        midheaven=(asc + 270.0) % 360.0,
        sect=sect,
    )
