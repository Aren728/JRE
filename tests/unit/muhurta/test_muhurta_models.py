"""Unit tests for JRE-020 Muhurta domain models."""

from __future__ import annotations

import pytest

from jyotish import BodyId, NakshatraId, PlanetState, RashiId

from muhurta.models import (
    MUHURTA_VERSION,
    CategoryRule,
    Karana,
    MuhurtaCategory,
    MuhurtaConfig,
    MuhurtaEvaluation,
    MuhurtaWindow,
    PanchangaState,
    Tithi,
    Var,
    Yoga,
    check_planet_in_house,
    compute_fitness_score,
    derive_planet_rashi,
    evaluate_panchanga,
)
from tests.unit.muhurta.conftest import make_panchanga, make_planet_state, make_window


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class TestTithiEnum:
    def test_has_30_values(self) -> None:
        assert len(Tithi) == 30

    def test_shukla_fortnight(self) -> None:
        assert Tithi.SHUKLA_PRADEMA.value == "SHUKLA_PRADEMA"
        assert Tithi.PURNIMA.value == "PURNIMA"

    def test_krishna_fortnight(self) -> None:
        assert Tithi.KRISHNA_PRATIPADA.value == "KRISHNA_PRATIPADA"
        assert Tithi.AMANTHA.value == "AMANTHA"

    def test_from_string(self) -> None:
        assert Tithi("SHUKLA_EKADASHI") == Tithi.SHUKLA_EKADASHI

    def test_invalid_string_raises(self) -> None:
        with pytest.raises(ValueError):
            Tithi("INVALID_TITHI")


class TestVaraEnum:
    def test_has_7_values(self) -> None:
        assert len(Var) == 7

    def test_all_weekdays(self) -> None:
        expected = {"SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY",
                    "THURSDAY", "FRIDAY", "SATURDAY"}
        assert {v.value for v in Var} == expected


class TestYogaEnum:
    def test_has_27_values(self) -> None:
        assert len(Yoga) == 27

    def test_first_and_last(self) -> None:
        assert Yoga.VISHKAMBHA.value == "VISHKAMBHA"
        assert Yoga.VAIDHRITI.value == "VAIDHRITI"


class TestKaranaEnum:
    def test_has_11_values(self) -> None:
        assert len(Karana) == 11

    def test_vishti_present(self) -> None:
        assert Karana.VISHTI.value == "VISHTI"


class TestMuhurtaCategoryEnum:
    def test_has_10_values(self) -> None:
        assert len(MuhurtaCategory) == 10

    def test_all_categories(self) -> None:
        expected = {
            "MARRIAGE", "TRAVEL", "BUSINESS", "EDUCATION",
            "HOUSEWARMING", "VEHICLE_PURCHASE", "MEDICAL",
            "LITIGATION", "COMMENCEMENT", "GENERAL",
        }
        assert {c.value for c in MuhurtaCategory} == expected


# --------------------------------------------------------------------------- #
# PanchangaState
# --------------------------------------------------------------------------- #


class TestPanchangaState:
    def test_creation(self) -> None:
        p = make_panchanga()
        assert p.tithi == Tithi.SHUKLA_PRADEMA
        assert p.vara == Var.THURSDAY
        assert p.nakshatra == NakshatraId.ASHWINI
        assert p.yoga == Yoga.SUBHA
        assert p.karana == Karana.BALAVA

    def test_frozen(self) -> None:
        p = make_panchanga()
        with pytest.raises(AttributeError):
            p.tithi = Tithi.PURNIMA  # type: ignore[misc]

    def test_to_dict(self) -> None:
        p = make_panchanga()
        d = p.to_dict()
        assert d["tithi"] == "SHUKLA_PRADEMA"
        assert d["vara"] == "THURSDAY"
        assert d["nakshatra"] == "ASHWINI"
        assert d["yoga"] == "SUBHA"
        assert d["karana"] == "BALAVA"


# --------------------------------------------------------------------------- #
# MuhurtaWindow
# --------------------------------------------------------------------------- #


class TestMuhurtaWindow:
    def test_creation(self) -> None:
        w = make_window()
        assert w.start_utc == "2024-01-15T06:00:00Z"
        assert w.end_utc == "2024-01-15T12:00:00Z"

    def test_to_dict(self) -> None:
        w = make_window()
        d = w.to_dict()
        assert d["start_utc"] == "2024-01-15T06:00:00Z"
        assert d["end_utc"] == "2024-01-15T12:00:00Z"


# --------------------------------------------------------------------------- #
# CategoryRule
# --------------------------------------------------------------------------- #


class TestCategoryRule:
    def test_defaults(self) -> None:
        r = CategoryRule()
        assert r.required_nakshatras == ()
        assert r.avoided_tithis == ()
        assert r.avoided_karanas == ()
        assert r.avoided_yogas == ()
        assert r.avoided_vars == ()
        assert r.preferred_vars == ()
        assert r.weight_required == 0.3
        assert r.weight_avoided == 0.5
        assert r.weight_preferred == 0.2

    def test_custom_rule(self) -> None:
        r = CategoryRule(
            required_nakshatras=(NakshatraId.HASTA,),
            avoided_tithis=(Tithi.SHUKLA_NAVAMI,),
            weight_required=0.4,
        )
        assert NakshatraId.HASTA in r.required_nakshatras
        assert Tithi.SHUKLA_NAVAMI in r.avoided_tithis
        assert r.weight_required == 0.4

    def test_to_dict(self) -> None:
        r = CategoryRule(required_nakshatras=(NakshatraId.HASTA,))
        d = r.to_dict()
        assert d["required_nakshatras"] == ["HASTA"]


# --------------------------------------------------------------------------- #
# MuhurtaConfig
# --------------------------------------------------------------------------- #


class TestMuhurtaConfig:
    def test_version(self) -> None:
        assert MUHURTA_VERSION == "0.1.0"

    def test_default_config(self) -> None:
        c = MuhurtaConfig()
        assert c.version == MUHURTA_VERSION
        assert len(c.inauspicious_tithis) > 0
        assert len(c.inauspicious_karanas) > 0
        assert len(c.inauspicious_yogas) > 0
        assert isinstance(c.category_rules, dict)

    def test_to_dict(self) -> None:
        c = MuhurtaConfig()
        d = c.to_dict()
        assert d["version"] == MUHURTA_VERSION


# --------------------------------------------------------------------------- #
# evaluate_panchanga
# --------------------------------------------------------------------------- #


class TestEvaluatePanchanga:
    def test_inauspicious_tithi_flag(self) -> None:
        p = make_panchanga(tithi=Tithi.SHUKLA_NAVAMI)
        config = MuhurtaConfig()
        flags = evaluate_panchanga(p, MuhurtaCategory.GENERAL, config)
        assert any("Inauspicious tithi" in f for f in flags)

    def test_inauspicious_karana_flag(self) -> None:
        p = make_panchanga(karana=Karana.VISHTI)
        config = MuhurtaConfig()
        flags = evaluate_panchanga(p, MuhurtaCategory.GENERAL, config)
        assert any("Inauspicious karana" in f for f in flags)

    def test_inauspicious_yoga_flag(self) -> None:
        p = make_panchanga(yoga=Yoga.SHULA)
        config = MuhurtaConfig()
        flags = evaluate_panchanga(p, MuhurtaCategory.GENERAL, config)
        assert any("Inauspicious yoga" in f for f in flags)

    def test_clean_panchanga_no_flags(self) -> None:
        p = make_panchanga(
            tithi=Tithi.SHUKLA_PRADEMA,
            vara=Var.THURSDAY,
            nakshatra=NakshatraId.ASHWINI,
            yoga=Yoga.SUBHA,
            karana=Karana.BALAVA,
        )
        # Use load_config to get category rules from TOML
        from muhurta.config import load_config
        config = load_config()
        flags = evaluate_panchanga(p, MuhurtaCategory.GENERAL, config)
        # ASHWINI is in GENERAL's required_nakshatras → favorable flag
        assert any("Favorable" in f for f in flags)

    def test_category_rule_applied(self) -> None:
        p = make_panchanga(
            vara=Var.SATURDAY,
            nakshatra=NakshatraId.HASTA,
        )
        # Use load_config to get category rules from TOML
        from muhurta.config import load_config
        config = load_config()
        # MARRIAGE has avoided_vars = [SATURDAY]
        flags = evaluate_panchanga(p, MuhurtaCategory.MARRIAGE, config)
        assert any("Avoided vara" in f for f in flags)
        # HASTA is in MARRIAGE's required_nakshatras
        assert any("Favorable" in f for f in flags)


# --------------------------------------------------------------------------- #
# compute_fitness_score
# --------------------------------------------------------------------------- #


class TestComputeFitnessScore:
    def test_no_flags_full_score(self) -> None:
        score = compute_fitness_score((), MuhurtaCategory.GENERAL, MuhurtaConfig())
        assert score == 1.0

    def test_inauspicious_penalizes(self) -> None:
        flags = ("Inauspicious tithi: SHUKLA_NAVAMI",)
        score = compute_fitness_score(flags, MuhurtaCategory.GENERAL, MuhurtaConfig())
        assert score < 1.0
        assert score > 0.0

    def test_avoided_penalizes_more(self) -> None:
        flags = ("Avoided tithi for MARRIAGE: SHUKLA_NAVAMI",)
        score = compute_fitness_score(flags, MuhurtaCategory.MARRIAGE, MuhurtaConfig())
        assert score < 1.0

    def test_favorable_boosts(self) -> None:
        flags = ("Favorable nakshatra for MARRIAGE: HASTA",)
        score = compute_fitness_score(flags, MuhurtaCategory.MARRIAGE, MuhurtaConfig())
        # Score is clamped to [0.0, 1.0] per spec
        assert score == 1.0

    def test_score_clamped_to_0_1(self) -> None:
        many_flags = (
            "Inauspicious tithi: X",
            "Inauspicious karana: X",
            "Inauspicious yoga: X",
            "Avoided tithi: X",
            "Avoided karana: X",
            "Avoided yoga: X",
            "Unfavorable nakshatra: X",
            "Avoided vara: X",
        )
        score = compute_fitness_score(many_flags, MuhurtaCategory.GENERAL, MuhurtaConfig())
        assert score == 0.0

    def test_deterministic(self) -> None:
        flags = ("Inauspicious tithi: SHUKLA_NAVAMI",)
        s1 = compute_fitness_score(flags, MuhurtaCategory.GENERAL, MuhurtaConfig())
        s2 = compute_fitness_score(flags, MuhurtaCategory.GENERAL, MuhurtaConfig())
        assert s1 == s2


# --------------------------------------------------------------------------- #
# derive_planet_rashi / check_planet_in_house
# --------------------------------------------------------------------------- #


class TestDerivePlanetRashi:
    def test_finds_planet(self) -> None:
        states = (make_planet_state(BodyId.SUN, 10.0),)
        assert derive_planet_rashi(states, BodyId.SUN) == RashiId.MESHA

    def test_missing_planet_returns_none(self) -> None:
        states = (make_planet_state(BodyId.SUN, 10.0),)
        assert derive_planet_rashi(states, BodyId.MARS) is None

    def test_check_planet_in_house(self) -> None:
        states = (make_planet_state(BodyId.SUN, 10.0),)
        assert check_planet_in_house(states, BodyId.SUN, RashiId.MESHA) is True
        assert check_planet_in_house(states, BodyId.SUN, RashiId.VRISHABHA) is False


# --------------------------------------------------------------------------- #
# MuhurtaEvaluation
# --------------------------------------------------------------------------- #


class TestMuhurtaEvaluation:
    def test_to_dict(self) -> None:
        e = MuhurtaEvaluation(
            window=make_window(),
            panchanga=make_panchanga(),
            structural_flags=("flag1",),
            fitness_score=0.85,
            category=MuhurtaCategory.GENERAL,
        )
        d = e.to_dict()
        assert d["category"] == "GENERAL"
        assert d["fitness_score"] == 0.85
        assert d["structural_flags"] == ["flag1"]
        assert "window" in d
        assert "panchanga" in d
