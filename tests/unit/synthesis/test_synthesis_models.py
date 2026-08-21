"""Unit tests for JRE-022 Synthesis domain models."""

from __future__ import annotations

import pytest

from synthesis.models import (
    SYNTHESIS_VERSION,
    AshtakavargaIndicator,
    AvasthaIndicator,
    BalaIndicator,
    ConditionType,
    DashaIndicator,
    HouseIndicator,
    SynthesisCategory,
    SynthesisConfig,
    SynthesisInput,
    SynthesisReport,
    SynthesisRule,
    Verdict,
    VerdictStrength,
    YogaIndicator,
    classify_strength,
    compute_category_score,
    evaluate_condition,
    generate_verdicts,
)
from tests.unit.synthesis.conftest import (
    make_ashtakavarga_indicator,
    make_avastha_indicator,
    make_bala_indicator,
    make_dasha_indicator,
    make_house_indicator,
    make_yoga_indicator,
)


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class TestSynthesisCategory:
    def test_has_10_values(self) -> None:
        assert len(SynthesisCategory) == 10

    def test_from_string(self) -> None:
        assert SynthesisCategory("CAREER") == SynthesisCategory.CAREER

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            SynthesisCategory("INVALID")


class TestConditionType:
    def test_has_13_values(self) -> None:
        assert len(ConditionType) == 13

    def test_all_types(self) -> None:
        expected = {
            "YOGA_PRESENT", "YOGA_ABSENT", "BALA_ABOVE", "BALA_BELOW",
            "DASHA_LORD_IS", "PLANET_IN_HOUSE", "PLANET_ASPECTS_HOUSE",
            "HOUSE_LORD_IN_HOUSE", "ASHTAKAVARGA_ABOVE", "AVASTHA_STATE",
            "KARAKA_PRESENT", "COMBINED_AND", "COMBINED_OR",
        }
        assert {c.value for c in ConditionType} == expected


class TestVerdictStrength:
    def test_has_5_values(self) -> None:
        assert len(VerdictStrength) == 5

    def test_ordering(self) -> None:
        assert VerdictStrength.VERY_STRONG.value == "VERY_STRONG"
        assert VerdictStrength.VERY_WEAK.value == "VERY_WEAK"


# --------------------------------------------------------------------------- #
# Input indicators
# --------------------------------------------------------------------------- #


class TestYogaIndicator:
    def test_creation(self) -> None:
        y = make_yoga_indicator("GAJAKESARI_YOGA", True)
        assert y.yoga_id == "GAJAKESARI_YOGA"
        assert y.present is True

    def test_to_dict(self) -> None:
        y = make_yoga_indicator("RAJA_YOGA", False)
        d = y.to_dict()
        assert d["yoga_id"] == "RAJA_YOGA"
        assert d["present"] is False


class TestBalaIndicator:
    def test_creation(self) -> None:
        b = make_bala_indicator("JUPITER", "SHADBALA", 6.5)
        assert b.planet == "JUPITER"
        assert b.value == 6.5

    def test_to_dict(self) -> None:
        b = make_bala_indicator()
        d = b.to_dict()
        assert d["planet"] == "JUPITER"
        assert d["bala_type"] == "SHADBALA"
        assert d["value"] == 6.0


class TestDashaIndicator:
    def test_creation(self) -> None:
        d = make_dasha_indicator("SATURN")
        assert d.lord == "SATURN"

    def test_to_dict(self) -> None:
        d = make_dasha_indicator()
        d_dict = d.to_dict()
        assert d_dict["lord"] == "JUPITER"


class TestHouseIndicator:
    def test_creation(self) -> None:
        h = make_house_indicator("MARS", 3)
        assert h.planet == "MARS"
        assert h.house == 3

    def test_to_dict(self) -> None:
        h = make_house_indicator()
        d = h.to_dict()
        assert d["planet"] == "JUPITER"
        assert d["house"] == 10


class TestSynthesisInput:
    def test_defaults(self) -> None:
        s = SynthesisInput()
        assert s.yogas == ()
        assert s.balas == ()
        assert s.dasha is None

    def test_to_dict(self) -> None:
        s = SynthesisInput(
            yogas=(make_yoga_indicator(),),
            balas=(make_bala_indicator(),),
        )
        d = s.to_dict()
        assert len(d["yogas"]) == 1
        assert len(d["balas"]) == 1


# --------------------------------------------------------------------------- #
# Core models
# --------------------------------------------------------------------------- #


class TestSynthesisRule:
    def test_creation(self) -> None:
        r = SynthesisRule(
            category=SynthesisCategory.CAREER,
            condition_type=ConditionType.YOGA_PRESENT,
            condition_params={"yoga_id": "RAJA_YOGA"},
            weight=3.0,
        )
        assert r.category == SynthesisCategory.CAREER
        assert r.weight == 3.0

    def test_to_dict(self) -> None:
        r = SynthesisRule(
            category=SynthesisCategory.WEALTH,
            condition_type=ConditionType.BALA_ABOVE,
            condition_params={"planet": "JUPITER", "threshold": 5.0},
            weight=2.0,
        )
        d = r.to_dict()
        assert d["category"] == "WEALTH"
        assert d["condition_type"] == "BALA_ABOVE"
        assert d["weight"] == 2.0


class TestVerdict:
    def test_creation(self) -> None:
        v = Verdict(
            category=SynthesisCategory.CAREER,
            score=7.5,
            strength=VerdictStrength.STRONG,
            evidence_ids=("RAJA_YOGA",),
        )
        assert v.score == 7.5
        assert v.strength == VerdictStrength.STRONG

    def test_to_dict(self) -> None:
        v = Verdict(
            category=SynthesisCategory.CAREER,
            score=7.5,
            strength=VerdictStrength.STRONG,
            evidence_ids=("RAJA_YOGA",),
        )
        d = v.to_dict()
        assert d["category"] == "CAREER"
        assert d["score"] == 7.5
        assert d["strength"] == "STRONG"
        assert d["evidence_ids"] == ["RAJA_YOGA"]


class TestSynthesisReport:
    def test_verdict_for(self) -> None:
        report = SynthesisReport(
            verdicts=(
                Verdict(
                    category=SynthesisCategory.CAREER,
                    score=7.5,
                    strength=VerdictStrength.STRONG,
                    evidence_ids=(),
                ),
            ),
        )
        assert report.verdict_for(SynthesisCategory.CAREER) is not None
        assert report.verdict_for(SynthesisCategory.WEALTH) is None

    def test_to_dict(self) -> None:
        report = SynthesisReport(verdicts=())
        d = report.to_dict()
        assert d["verdicts"] == []
        assert d["version"] == SYNTHESIS_VERSION


class TestSynthesisConfig:
    def test_version(self) -> None:
        assert SYNTHESIS_VERSION == "0.1.0"

    def test_defaults(self) -> None:
        c = SynthesisConfig()
        assert c.version == SYNTHESIS_VERSION
        assert "VERY_STRONG" in c.strength_thresholds
        assert c.score_range == (0.0, 10.0)

    def test_to_dict(self) -> None:
        c = SynthesisConfig()
        d = c.to_dict()
        assert d["version"] == SYNTHESIS_VERSION


# --------------------------------------------------------------------------- #
# evaluate_condition
# --------------------------------------------------------------------------- #


class TestEvaluateCondition:
    def test_yoga_present_true(self) -> None:
        data = SynthesisInput(
            yogas=(YogaIndicator(yoga_id="RAJA_YOGA", present=True),),
        )
        assert evaluate_condition(
            ConditionType.YOGA_PRESENT,
            {"yoga_id": "RAJA_YOGA"},
            data,
        ) is True

    def test_yoga_present_false(self) -> None:
        data = SynthesisInput(
            yogas=(YogaIndicator(yoga_id="DHANA_YOGA", present=True),),
        )
        assert evaluate_condition(
            ConditionType.YOGA_PRESENT,
            {"yoga_id": "RAJA_YOGA"},
            data,
        ) is False

    def test_yoga_absent_true(self) -> None:
        data = SynthesisInput(
            yogas=(YogaIndicator(yoga_id="DHANA_YOGA", present=True),),
        )
        assert evaluate_condition(
            ConditionType.YOGA_ABSENT,
            {"yoga_id": "RAJA_YOGA"},
            data,
        ) is True

    def test_bala_above_true(self) -> None:
        data = SynthesisInput(
            balas=(BalaIndicator(planet="JUPITER", bala_type="SHADBALA", value=7.0),),
        )
        assert evaluate_condition(
            ConditionType.BALA_ABOVE,
            {"planet": "JUPITER", "bala_type": "SHADBALA", "threshold": 5.0},
            data,
        ) is True

    def test_bala_above_false(self) -> None:
        data = SynthesisInput(
            balas=(BalaIndicator(planet="JUPITER", bala_type="SHADBALA", value=3.0),),
        )
        assert evaluate_condition(
            ConditionType.BALA_ABOVE,
            {"planet": "JUPITER", "bala_type": "SHADBALA", "threshold": 5.0},
            data,
        ) is False

    def test_bala_below_true(self) -> None:
        data = SynthesisInput(
            balas=(BalaIndicator(planet="SATURN", bala_type="SHADBALA", value=2.0),),
        )
        assert evaluate_condition(
            ConditionType.BALA_BELOW,
            {"planet": "SATURN", "bala_type": "SHADBALA", "threshold": 5.0},
            data,
        ) is True

    def test_dasha_lord_is_true(self) -> None:
        data = SynthesisInput(
            dasha=DashaIndicator(lord="JUPITER", period_start="", period_end=""),
        )
        assert evaluate_condition(
            ConditionType.DASHA_LORD_IS,
            {"planet": "JUPITER"},
            data,
        ) is True

    def test_dasha_lord_is_false(self) -> None:
        data = SynthesisInput(
            dasha=DashaIndicator(lord="SATURN", period_start="", period_end=""),
        )
        assert evaluate_condition(
            ConditionType.DASHA_LORD_IS,
            {"planet": "JUPITER"},
            data,
        ) is False

    def test_dasha_none(self) -> None:
        data = SynthesisInput()
        assert evaluate_condition(
            ConditionType.DASHA_LORD_IS,
            {"planet": "JUPITER"},
            data,
        ) is False

    def test_planet_in_house_true(self) -> None:
        data = SynthesisInput(
            house_occupancies=(HouseIndicator(planet="SUN", house=10),),
        )
        assert evaluate_condition(
            ConditionType.PLANET_IN_HOUSE,
            {"planet": "SUN", "house": 10},
            data,
        ) is True

    def test_planet_in_house_false(self) -> None:
        data = SynthesisInput(
            house_occupancies=(HouseIndicator(planet="SUN", house=1),),
        )
        assert evaluate_condition(
            ConditionType.PLANET_IN_HOUSE,
            {"planet": "SUN", "house": 10},
            data,
        ) is False

    def test_ashtakavarga_above_true(self) -> None:
        data = SynthesisInput(
            ashtakavarga=(AshtakavargaIndicator(house=2, score=32),),
        )
        assert evaluate_condition(
            ConditionType.ASHTAKAVARGA_ABOVE,
            {"house": 2, "threshold": 28},
            data,
        ) is True

    def test_avastha_state_true(self) -> None:
        data = SynthesisInput(
            avasthas=(AvasthaIndicator(planet="SUN", state="DEEPTADI"),),
        )
        assert evaluate_condition(
            ConditionType.AVASTHA_STATE,
            {"planet": "SUN", "state": "DEEPTADI"},
            data,
        ) is True

    def test_karaka_present_true(self) -> None:
        data = SynthesisInput(
            house_occupancies=(HouseIndicator(planet="JUPITER", house=5),),
        )
        assert evaluate_condition(
            ConditionType.KARAKA_PRESENT,
            {"karaka": "JUPITER", "house": 5},
            data,
        ) is True


# --------------------------------------------------------------------------- #
# classify_strength
# --------------------------------------------------------------------------- #


class TestClassifyStrength:
    def test_very_strong(self) -> None:
        thresholds = {"VERY_STRONG": 8.0, "STRONG": 6.0, "MODERATE": 4.0, "WEAK": 2.0, "VERY_WEAK": 0.0}
        assert classify_strength(9.0, thresholds) == VerdictStrength.VERY_STRONG

    def test_strong(self) -> None:
        thresholds = {"VERY_STRONG": 8.0, "STRONG": 6.0, "MODERATE": 4.0, "WEAK": 2.0, "VERY_WEAK": 0.0}
        assert classify_strength(7.0, thresholds) == VerdictStrength.STRONG

    def test_moderate(self) -> None:
        thresholds = {"VERY_STRONG": 8.0, "STRONG": 6.0, "MODERATE": 4.0, "WEAK": 2.0, "VERY_WEAK": 0.0}
        assert classify_strength(5.0, thresholds) == VerdictStrength.MODERATE

    def test_weak(self) -> None:
        thresholds = {"VERY_STRONG": 8.0, "STRONG": 6.0, "MODERATE": 4.0, "WEAK": 2.0, "VERY_WEAK": 0.0}
        assert classify_strength(3.0, thresholds) == VerdictStrength.WEAK

    def test_very_weak(self) -> None:
        thresholds = {"VERY_STRONG": 8.0, "STRONG": 6.0, "MODERATE": 4.0, "WEAK": 2.0, "VERY_WEAK": 0.0}
        assert classify_strength(1.0, thresholds) == VerdictStrength.VERY_WEAK


# --------------------------------------------------------------------------- #
# compute_category_score
# --------------------------------------------------------------------------- #


class TestComputeCategoryScore:
    def test_no_rules_zero_score(self) -> None:
        score, evidence = compute_category_score((), SynthesisInput())
        assert score == 0.0
        assert evidence == []

    def test_matching_rule_adds_weight(self) -> None:
        rules = (
            SynthesisRule(
                category=SynthesisCategory.CAREER,
                condition_type=ConditionType.YOGA_PRESENT,
                condition_params={"yoga_id": "RAJA_YOGA"},
                weight=3.0,
            ),
        )
        data = SynthesisInput(
            yogas=(YogaIndicator(yoga_id="RAJA_YOGA", present=True),),
        )
        score, evidence = compute_category_score(rules, data)
        assert score == 3.0
        assert len(evidence) == 1

    def test_non_matching_rule_zero_weight(self) -> None:
        rules = (
            SynthesisRule(
                category=SynthesisCategory.CAREER,
                condition_type=ConditionType.YOGA_PRESENT,
                condition_params={"yoga_id": "RAJA_YOGA"},
                weight=3.0,
            ),
        )
        data = SynthesisInput(
            yogas=(YogaIndicator(yoga_id="DHANA_YOGA", present=True),),
        )
        score, _ = compute_category_score(rules, data)
        assert score == 0.0


# --------------------------------------------------------------------------- #
# generate_verdicts
# --------------------------------------------------------------------------- #


class TestGenerateVerdicts:
    def test_empty_rules_empty_verdicts(self) -> None:
        verdicts = generate_verdicts({}, SynthesisInput(), {"VERY_STRONG": 8.0, "STRONG": 6.0, "MODERATE": 4.0, "WEAK": 2.0, "VERY_WEAK": 0.0})
        assert verdicts == ()

    def test_produces_verdict_per_category(self) -> None:
        rules = {
            "CAREER": (
                SynthesisRule(
                    category=SynthesisCategory.CAREER,
                    condition_type=ConditionType.YOGA_PRESENT,
                    condition_params={"yoga_id": "RAJA_YOGA"},
                    weight=3.0,
                ),
            ),
            "WEALTH": (
                SynthesisRule(
                    category=SynthesisCategory.WEALTH,
                    condition_type=ConditionType.YOGA_PRESENT,
                    condition_params={"yoga_id": "GAJAKESARI_YOGA"},
                    weight=2.5,
                ),
            ),
        }
        data = SynthesisInput(
            yogas=(
                YogaIndicator(yoga_id="RAJA_YOGA", present=True),
                YogaIndicator(yoga_id="GAJAKESARI_YOGA", present=True),
            ),
        )
        thresholds = {"VERY_STRONG": 8.0, "STRONG": 6.0, "MODERATE": 4.0, "WEAK": 2.0, "VERY_WEAK": 0.0}
        verdicts = generate_verdicts(rules, data, thresholds)
        assert len(verdicts) == 2
        categories = {v.category for v in verdicts}
        assert SynthesisCategory.CAREER in categories
        assert SynthesisCategory.WEALTH in categories

    def test_deterministic(self) -> None:
        rules = {
            "CAREER": (
                SynthesisRule(
                    category=SynthesisCategory.CAREER,
                    condition_type=ConditionType.YOGA_PRESENT,
                    condition_params={"yoga_id": "RAJA_YOGA"},
                    weight=3.0,
                ),
            ),
        }
        data = SynthesisInput(
            yogas=(YogaIndicator(yoga_id="RAJA_YOGA", present=True),),
        )
        thresholds = {"VERY_STRONG": 8.0, "STRONG": 6.0, "MODERATE": 4.0, "WEAK": 2.0, "VERY_WEAK": 0.0}
        v1 = generate_verdicts(rules, data, thresholds)
        v2 = generate_verdicts(rules, data, thresholds)
        assert v1 == v2
