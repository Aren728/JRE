"""Unit tests for JRS-069: Western Traditional Doctrine rules.

Tests rule loading, chart evaluation, SystemAssessment production,
and deterministic output for Sect, Joys, Terms, Mutual Receptions,
and Accidental Dignities.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from jrs.evidence.models import EvidenceDirection, EvidenceStrength
from jrs.western.config import load_western_rules
from jrs.western.models import (
    WesternOutcomeTaxonomy,
    WesternRule,
    evaluate_rule,
    extract_facts_from_chart,
)
from western.models import (
    HouseCusp,
    Sect,
    WesternChart,
    WesternDignity,
    WesternHouseSystem,
    WesternPlanet,
    _sign_name,
)
from western.service import WesternCalculationService

# ── Paths ────────────────────────────────────────────────────────────────────

_CONFIG_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "config" / "western"
)
_TRADITIONAL_RULES_PATH = _CONFIG_DIR / "traditional_rules.toml"
_BASIC_RULES_PATH = _CONFIG_DIR / "basic_rules.toml"

_WESTERN_SVC = WesternCalculationService()


# ── Fixtures ─────────────────────────────────────────────────────────────────


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
def traditional_rules() -> tuple[WesternRule, ...]:
    """Load traditional rules from traditional_rules.toml."""
    return load_western_rules(_TRADITIONAL_RULES_PATH, extra_paths=())


@pytest.fixture
def all_rules() -> tuple[WesternRule, ...]:
    """Load all rules (basic + traditional)."""
    return load_western_rules(_BASIC_RULES_PATH)


# ── Sect Enum Tests ──────────────────────────────────────────────────────────


class TestSect:
    """Tests for the Sect enum and chart_sect calculation."""

    def test_sect_values(self) -> None:
        assert Sect.DIURNAL.value == "DIURNAL"
        assert Sect.NOCTURNAL.value == "NOCTURNAL"

    def test_einstein_has_sect(self, einstein_chart: WesternChart) -> None:
        assert einstein_chart.sect in (Sect.DIURNAL, Sect.NOCTURNAL)

    def test_einstein_diurnal(self, einstein_chart: WesternChart) -> None:
        # Einstein born 10:50 AM in Ulm — should be diurnal
        assert einstein_chart.sect == Sect.DIURNAL

    def test_sect_in_to_dict(self, einstein_chart: WesternChart) -> None:
        d = einstein_chart.to_dict()
        assert d["sect"] in ("DIURNAL", "NOCTURNAL")

    def test_sect_in_facts(self, einstein_chart: WesternChart) -> None:
        facts = extract_facts_from_chart(einstein_chart)
        assert facts["chart_sect"] in ("DIURNAL", "NOCTURNAL")

    def test_nocturnal_chart(self) -> None:
        """A midnight birth should produce a nocturnal chart."""
        chart = _WESTERN_SVC.calculate(
            birth_date=dt.date(1980, 6, 21),
            birth_time=dt.time(0, 0, 0),
            latitude=51.5,
            longitude=-0.1,
        )
        assert chart.sect == Sect.NOCTURNAL


# ── Traditional Rules Config Loading Tests ───────────────────────────────────


class TestTraditionalConfigLoading:
    """Tests for traditional_rules.toml loading."""

    def test_traditional_rules_load(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        assert len(traditional_rules) > 0

    def test_all_rules_have_valid_outcomes(
        self, traditional_rules: tuple[WesternRule, ...]
    ) -> None:
        valid_outcomes = {o.value for o in WesternOutcomeTaxonomy}
        for rule in traditional_rules:
            assert rule.outcome.value in valid_outcomes

    def test_all_rules_have_source(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        valid_sources = {"PTOLEMY", "LILLY", "BONATTI", "DOROTHEUS", "MORINUS"}
        for rule in traditional_rules:
            msg = f"{rule.rule_id} has invalid source: {rule.source_id}"
            assert rule.source_id in valid_sources, msg

    def test_all_rules_have_location(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        for rule in traditional_rules:
            assert rule.location, f"{rule.rule_id} has no location"

    def test_all_rules_have_valid_directions(
        self, traditional_rules: tuple[WesternRule, ...]
    ) -> None:
        for rule in traditional_rules:
            assert rule.direction.value in {"SUPPORT", "CONTRADICT", "MITIGATE", "NEUTRAL"}

    def test_all_rules_have_valid_strengths(
        self, traditional_rules: tuple[WesternRule, ...]
    ) -> None:
        valid_strengths = {s.value for s in EvidenceStrength}
        for rule in traditional_rules:
            assert rule.strength.value in valid_strengths


# ── Rule Category Counts ─────────────────────────────────────────────────────


class TestRuleCategories:
    """Verify all rule categories are present in the traditional config."""

    def test_sect_rules_present(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        sect_rules = [r for r in traditional_rules if r.rule_id.startswith("W-SECT-")]
        assert len(sect_rules) >= 5, f"Expected >= 5 sect rules, got {len(sect_rules)}"

    def test_joy_rules_present(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        joy_rules = [r for r in traditional_rules if r.rule_id.startswith("W-JOY-")]
        assert len(joy_rules) >= 5, f"Expected >= 5 joy rules, got {len(joy_rules)}"

    def test_term_rules_present(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        term_rules = [r for r in traditional_rules if r.rule_id.startswith("W-TERM-")]
        assert len(term_rules) >= 3, f"Expected >= 3 term rules, got {len(term_rules)}"

    def test_mutual_reception_rules_present(
        self, traditional_rules: tuple[WesternRule, ...]
    ) -> None:
        mr_rules = [r for r in traditional_rules if r.rule_id.startswith("W-MUTUAL-RECEPTION-")]
        assert len(mr_rules) >= 4, f"Expected >= 4 mutual reception rules, got {len(mr_rules)}"

    def test_cazimi_rules_present(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        cazimi_rules = [r for r in traditional_rules if r.rule_id.startswith("W-CAZIMI-")]
        assert len(cazimi_rules) >= 3, f"Expected >= 3 cazimi rules, got {len(cazimi_rules)}"

    def test_combust_rules_present(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        combust_rules = [r for r in traditional_rules if r.rule_id.startswith("W-COMBUST-")]
        assert len(combust_rules) >= 3, f"Expected >= 3 combust rules, got {len(combust_rules)}"

    def test_beams_rules_present(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        beams_rules = [r for r in traditional_rules if r.rule_id.startswith("W-BEAMS-")]
        assert len(beams_rules) >= 2, f"Expected >= 2 beams rules, got {len(beams_rules)}"


# ── Sect Rule Evaluation Tests ───────────────────────────────────────────────


class TestSectRuleEvaluation:
    """Tests for sect-based rule evaluation."""

    def test_diurnal_sect_supports_sun_authority(self) -> None:
        rule = WesternRule(
            rule_id="W-SECT-SUN-DIURNAL",
            description="Sun in diurnal chart",
            condition_facts=("chart_sect=DIURNAL",),
            outcome=WesternOutcomeTaxonomy.LEADERSHIP_AUTHORITY,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
            source_id="LILLY",
            location="Ch. 21",
        )
        record = evaluate_rule(rule, {"chart_sect": "DIURNAL"})
        assert record is not None
        assert record.outcome_taxonomy == "LEADERSHIP_AUTHORITY"
        assert record.direction is EvidenceDirection.SUPPORT

    def test_diurnal_sect_contradicts_sun_at_night(self) -> None:
        rule = WesternRule(
            rule_id="W-SECT-SUN-NOCTURNAL",
            description="Sun in nocturnal chart",
            condition_facts=("chart_sect=NOCTURNAL",),
            outcome=WesternOutcomeTaxonomy.LEADERSHIP_AUTHORITY,
            direction=EvidenceDirection.CONTRADICT,
            strength=EvidenceStrength.MODERATE,
            source_id="LILLY",
            location="Ch. 21",
        )
        record = evaluate_rule(rule, {"chart_sect": "NOCTURNAL"})
        assert record is not None
        assert record.direction is EvidenceDirection.CONTRADICT

    def test_nocturnal_mitigates_mars(self) -> None:
        rule = WesternRule(
            rule_id="W-SECT-MARS-NOCTURNAL",
            description="Mars in nocturnal chart",
            condition_facts=("chart_sect=NOCTURNAL",),
            outcome=WesternOutcomeTaxonomy.EMOTIONAL_TENSION,
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.MODERATE,
            source_id="DOROTHEUS",
            location="C.I.4",
        )
        record = evaluate_rule(rule, {"chart_sect": "NOCTURNAL"})
        assert record is not None
        assert record.direction is EvidenceDirection.MITIGATE


# ── Planetary Joy Extraction Tests ──────────────────────────────────────────


class TestPlanetaryJoyExtraction:
    """Tests for planetary joy fact extraction."""

    def test_sun_joy_detected_when_in_9th(self) -> None:
        """Build a chart where Sun is in the 9th house."""
        # Ascendant at 0° = 0°, 9th cusp starts at 240°
        # Place Sun at 250° (9th house)
        chart = _make_chart_with_planet(
            planet=WesternPlanet.SUN,
            longitude=250.0,
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("sun_joy") == "true"

    def test_moon_joy_detected_when_in_3rd(self) -> None:
        """Build a chart where Moon is in the 3rd house."""
        # 3rd cusp starts at 60°, Moon at 70°
        chart = _make_chart_with_planet(
            planet=WesternPlanet.MOON,
            longitude=70.0,
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("moon_joy") == "true"

    def test_no_joy_when_wrong_house(self) -> None:
        """Sun in 1st house should not have joy."""
        chart = _make_chart_with_planet(
            planet=WesternPlanet.SUN,
            longitude=20.0,
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert "sun_joy" not in facts

    def test_venus_joy_detected_when_in_5th(self) -> None:
        """Venus at 140° with Asc at 0° → 5th house (120°–150°)."""
        chart = _make_chart_with_planet(
            planet=WesternPlanet.VENUS,
            longitude=140.0,
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("venus_joy") == "true"

    def test_jupiter_joy_detected_when_in_11th(self) -> None:
        """Jupiter at 320° with Asc at 0° → 11th house (300°–330°)."""
        chart = _make_chart_with_planet(
            planet=WesternPlanet.JUPITER,
            longitude=320.0,
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("jupiter_joy") == "true"

    def test_mars_joy_detected_when_in_6th(self) -> None:
        """Mars at 160° with Asc at 0° → 6th house (150°–180°)."""
        chart = _make_chart_with_planet(
            planet=WesternPlanet.MARS,
            longitude=160.0,
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("mars_joy") == "true"

    def test_saturn_joy_detected_when_in_12th(self) -> None:
        """Saturn at 350° with Asc at 0° → 12th house (330°–360°)."""
        chart = _make_chart_with_planet(
            planet=WesternPlanet.SATURN,
            longitude=350.0,
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("saturn_joy") == "true"


# ── Egyptian Terms Extraction Tests ──────────────────────────────────────────


class TestEgyptianTermsExtraction:
    """Tests for Egyptian terms/bounds fact extraction."""

    def test_term_ruler_extracted(self) -> None:
        """A planet's term ruler should be extracted from the chart."""
        chart = _make_chart_with_planet(
            planet=WesternPlanet.MERCURY,
            longitude=5.0,  # Aries 0-6°: Jupiter's term
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("mercury_term_ruler") == "JUPITER"

    def test_venus_term_in_aries(self) -> None:
        """Venus at Aries 8° (6-14°): Venus's term."""
        chart = _make_chart_with_planet(
            planet=WesternPlanet.VENUS,
            longitude=38.0,  # Aries 8°
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("venus_term_ruler") == "VENUS"

    def test_mars_term_in_scorpio(self) -> None:
        """Mars at Scorpio 5° (0-7°): Mars's term."""
        chart = _make_chart_with_planet(
            planet=WesternPlanet.MARS,
            longitude=215.0,  # Scorpio 5°
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("mars_term_ruler") == "MARS"


# ── Mutual Reception Extraction Tests ────────────────────────────────────────


class TestMutualReceptionExtraction:
    """Tests for mutual reception fact extraction."""

    def test_no_mutual_reception_without_both(self) -> None:
        """A single planet cannot form a mutual reception."""
        chart = _make_chart_with_planets(
            planets=[
                (WesternPlanet.VENUS, 5.0),   # Aries (Mars's domicile)
            ],
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        mr_keys = [k for k in facts if k.startswith("mutual_reception_")]
        assert len(mr_keys) == 0


# ── Accidental Dignity Extraction Tests ──────────────────────────────────────


class TestAccidentalDignityExtraction:
    """Tests for cazimi, combust, and under-the-beams extraction."""

    def test_cazimi_detected(self) -> None:
        """Venus within 0.5° of Sun should be cazimi."""
        chart = _make_chart_with_planets(
            planets=[
                (WesternPlanet.SUN, 100.0),
                (WesternPlanet.VENUS, 100.3),
            ],
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("venus_cazimi") == "true"

    def test_combust_detected(self) -> None:
        """Venus 5° from Sun should be combust (not cazimi)."""
        chart = _make_chart_with_planets(
            planets=[
                (WesternPlanet.SUN, 100.0),
                (WesternPlanet.VENUS, 105.0),
            ],
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("venus_combust") == "true"
        assert "venus_cazimi" not in facts

    def test_under_beams_detected(self) -> None:
        """Venus 15° from Sun should be under the beams."""
        chart = _make_chart_with_planets(
            planets=[
                (WesternPlanet.SUN, 100.0),
                (WesternPlanet.VENUS, 115.0),
            ],
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("venus_under_beams") == "true"
        assert "venus_combust" not in facts

    def test_no_accidental_when_far(self) -> None:
        """Venus 90° from Sun should have no accidental dignity issues."""
        chart = _make_chart_with_planets(
            planets=[
                (WesternPlanet.SUN, 100.0),
                (WesternPlanet.VENUS, 190.0),
            ],
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert "venus_cazimi" not in facts
        assert "venus_combust" not in facts
        assert "venus_under_beams" not in facts

    def test_mercury_cazimi(self) -> None:
        """Mercury within 0.5° of Sun should be cazimi."""
        chart = _make_chart_with_planets(
            planets=[
                (WesternPlanet.SUN, 100.0),
                (WesternPlanet.MERCURY, 99.8),
            ],
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("mercury_cazimi") == "true"

    def test_mars_combust(self) -> None:
        """Mars 7° from Sun should be combust."""
        chart = _make_chart_with_planets(
            planets=[
                (WesternPlanet.SUN, 100.0),
                (WesternPlanet.MARS, 107.0),
            ],
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("mars_combust") == "true"

    def test_moon_under_beams(self) -> None:
        """Moon 16° from Sun should be under the beams."""
        chart = _make_chart_with_planets(
            planets=[
                (WesternPlanet.SUN, 100.0),
                (WesternPlanet.MOON, 116.0),
            ],
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("moon_under_beams") == "true"

    def test_jupiter_cazimi(self) -> None:
        """Jupiter within 0.5° of Sun should be cazimi."""
        chart = _make_chart_with_planets(
            planets=[
                (WesternPlanet.SUN, 100.0),
                (WesternPlanet.JUPITER, 100.4),
            ],
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("jupiter_cazimi") == "true"

    def test_saturn_cazimi(self) -> None:
        """Saturn within 0.5° of Sun should be cazimi."""
        chart = _make_chart_with_planets(
            planets=[
                (WesternPlanet.SUN, 100.0),
                (WesternPlanet.SATURN, 99.7),
            ],
            asc=0.0,
        )
        facts = extract_facts_from_chart(chart)
        assert facts.get("saturn_cazimi") == "true"


# ── Full Chart Assessment Tests with Traditional Rules ───────────────────────


class TestTraditionalRuleAssessment:
    """Integration tests for traditional rule evaluation against real charts."""

    def test_einstein_facts_include_sect(self, einstein_chart: WesternChart) -> None:
        facts = extract_facts_from_chart(einstein_chart)
        assert "chart_sect" in facts
        assert facts["chart_sect"] in ("DIURNAL", "NOCTURNAL")

    def test_einstein_facts_include_terms(self, einstein_chart: WesternChart) -> None:
        facts = extract_facts_from_chart(einstein_chart)
        term_keys = [k for k in facts if k.endswith("_term_ruler")]
        assert len(term_keys) > 0

    def test_traditional_rules_fire_on_einstein(self, einstein_chart: WesternChart) -> None:
        """At least some traditional rules should fire on a real chart."""
        rules = load_western_rules(_TRADITIONAL_RULES_PATH, extra_paths=())
        facts = extract_facts_from_chart(einstein_chart)
        from jrs.western.models import evaluate_facts
        records = evaluate_facts(rules, facts)
        # With sect rules and term rules, at least a few should fire
        assert len(records) > 0

    def test_all_traditional_records_have_valid_fields(
        self, einstein_chart: WesternChart
    ) -> None:
        rules = load_western_rules(_TRADITIONAL_RULES_PATH, extra_paths=())
        facts = extract_facts_from_chart(einstein_chart)
        from jrs.western.models import evaluate_facts
        records = evaluate_facts(rules, facts)
        valid_sources = {"PTOLEMY", "LILLY", "BONATTI", "DOROTHEUS", "MORINUS"}
        for record in records:
            assert record.source_id in valid_sources
            assert record.rule_id.startswith("W-")
            assert record.location
            assert record.direction in {
                EvidenceDirection.SUPPORT,
                EvidenceDirection.CONTRADICT,
                EvidenceDirection.MITIGATE,
                EvidenceDirection.NEUTRAL,
            }


# ── Mutual Rule ID Conflicts ─────────────────────────────────────────────────


class TestNoRuleIDConflicts:
    """Verify no rule IDs are duplicated across basic and traditional configs."""

    def test_no_duplicate_rule_ids(self, all_rules: tuple[WesternRule, ...]) -> None:
        ids = [r.rule_id for r in all_rules]
        dupes = [i for i in ids if ids.count(i) > 1]
        assert len(ids) == len(set(ids)), f"Duplicate rule IDs: {dupes}"


# ── Determinism Tests ────────────────────────────────────────────────────────


class TestDeterminism:
    """Tests for deterministic traditional rule output."""

    def test_same_chart_same_traditional_facts(self, einstein_chart: WesternChart) -> None:
        facts1 = extract_facts_from_chart(einstein_chart)
        facts2 = extract_facts_from_chart(einstein_chart)
        assert facts1 == facts2

    def test_traditional_facts_deterministic(self, einstein_chart: WesternChart) -> None:
        facts = extract_facts_from_chart(einstein_chart)
        # Sect should be deterministic
        assert facts["chart_sect"] in ("DIURNAL", "NOCTURNAL")


# ── Source Attribution Tests ─────────────────────────────────────────────────


class TestSourceAttribution:
    """Verify all traditional rules have classical source attribution."""

    def test_no_empty_source_ids(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        for rule in traditional_rules:
            assert rule.source_id, f"{rule.rule_id} has empty source_id"

    def test_no_empty_locations(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        for rule in traditional_rules:
            assert rule.location, f"{rule.rule_id} has empty location"

    def test_classical_sources_only(self, traditional_rules: tuple[WesternRule, ...]) -> None:
        valid_sources = {"PTOLEMY", "LILLY", "BONATTI", "DOROTHEUS", "MORINUS"}
        for rule in traditional_rules:
            assert rule.source_id in valid_sources, (
                f"{rule.rule_id} has non-classical source: {rule.source_id}"
            )


# ── Helper Functions ─────────────────────────────────────────────────────────


def _make_chart_with_planet(
    planet: WesternPlanet,
    longitude: float,
    asc: float,
) -> WesternChart:
    """Create a minimal chart with a single planet for testing."""
    return _make_chart_with_planets([(planet, longitude)], asc)


def _make_chart_with_planets(
    planets: list[tuple[WesternPlanet, float]],
    asc: float,
) -> WesternChart:
    """Create a minimal chart with specified planets for testing.

    Generates evenly-spaced whole-sign house cusps from the Ascendant.
    """
    # Whole-sign houses: each cusp is 30° apart from Ascendant
    cusps = [
        HouseCusp(house_number=i + 1, longitude=(asc + i * 30.0) % 360.0)
        for i in range(12)
    ]

    from western.models import (
        PlanetPosition,
        evaluate_essential_dignity,
    )

    positions = []
    dignities: dict[WesternPlanet, WesternDignity] = {}
    for p, lon in planets:
        sign = _sign_name(lon)
        deg = lon % 30.0
        positions.append(
            PlanetPosition(
                planet=p,
                longitude=lon,
                latitude=0.0,
                speed_longitude=1.0,
                sign=sign,
                degree_in_sign=deg,
            )
        )
        dignities[p] = evaluate_essential_dignity(p, lon)

    return WesternChart(
        birth_date="2000-01-01",
        birth_time="12:00:00",
        latitude=40.0,
        longitude=-74.0,
        house_system=WesternHouseSystem.PLACIDUS,
        julian_day_ut=2451545.0,
        planet_positions=tuple(positions),
        house_cusps=tuple(cusps),
        aspects=(),
        dignities=dignities,
        ascendant=asc,
        midheaven=(asc + 270.0) % 360.0,
        sect=Sect.DIURNAL,
    )
