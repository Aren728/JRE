"""JRE-013 Yoga model tests."""

from __future__ import annotations

from jyotish import BodyId

from yoga.models import (
    YOGA_VERSION,
    KENDRA_HOUSES,
    TRIKONA_HOUSES,
    DUSTHANA_HOUSES,
    ConnectionType,
    YogaConfig,
    YogaCondition,
    YogaId,
    YogaReport,
    YogaResult,
    YogaRuleType,
    house_from_lagna,
    rashi_number,
    validate,
)


class TestConstants:
    def test_version(self) -> None:
        assert YOGA_VERSION == "0.1.0"

    def test_kendra_houses(self) -> None:
        assert KENDRA_HOUSES == frozenset({1, 4, 7, 10})

    def test_trikona_houses(self) -> None:
        assert TRIKONA_HOUSES == frozenset({1, 5, 9})

    def test_dusthana_houses(self) -> None:
        assert DUSTHANA_HOUSES == frozenset({6, 8, 12})


class TestRashiNumber:
    def test_aries(self) -> None:
        assert rashi_number("MESHA") == 1

    def test_libra(self) -> None:
        assert rashi_number("TULA") == 7

    def test_pisces(self) -> None:
        assert rashi_number("MEENA") == 12


class TestHouseFromLagna:
    def test_first_house(self) -> None:
        assert house_from_lagna(1, 1) == 1

    def test_seventh_house(self) -> None:
        assert house_from_lagna(1, 7) == 7

    def test_wraparound(self) -> None:
        assert house_from_lagna(10, 2) == 5


class TestConnectionType:
    def test_conjunction(self) -> None:
        assert ConnectionType.CONJUNCTION.value == "CONJUNCTION"

    def test_aspect(self) -> None:
        assert ConnectionType.ASPECT.value == "ASPECT"

    def test_exchange(self) -> None:
        assert ConnectionType.EXCHANGE.value == "EXCHANGE"


class TestYogaId:
    def test_all_ids(self) -> None:
        ids = [y.value for y in YogaId]
        assert "GAJAKESARI_YOGA" in ids
        assert "RAJA_YOGA" in ids
        assert "DHANA_YOGA" in ids
        assert "VIPARITA_RAJA_YOGA" in ids


class TestYogaCondition:
    def test_construction(self) -> None:
        cond = YogaCondition(
            condition_type="KENDRA_FROM",
            planets_involved=(BodyId.JUPITER, BodyId.MOON),
            houses_involved=(4,),
        )
        assert cond.condition_type == "KENDRA_FROM"
        assert BodyId.JUPITER in cond.planets_involved


class TestYogaResult:
    def test_present(self) -> None:
        result = YogaResult(
            yoga_id=YogaId.GAJAKESARI_YOGA,
            is_present=True,
            strength_modifier=0.8,
            evidence=("Jupiter in Kendra from Moon",),
        )
        assert result.is_present is True
        assert result.strength_modifier == 0.8

    def test_absent(self) -> None:
        result = YogaResult(
            yoga_id=YogaId.GAJAKESARI_YOGA,
            is_present=False,
            strength_modifier=0.0,
            evidence=("Not present",),
        )
        assert result.is_present is False


class TestYogaReport:
    def test_active_yogas(self) -> None:
        r1 = YogaResult(
            yoga_id=YogaId.GAJAKESARI_YOGA,
            is_present=True,
            strength_modifier=1.0,
            evidence=(),
        )
        r2 = YogaResult(
            yoga_id=YogaId.RAJA_YOGA,
            is_present=False,
            strength_modifier=0.0,
            evidence=(),
        )
        report = YogaReport(results=(r1, r2))
        assert len(report.active_yogas) == 1
        assert report.active_yogas[0].yoga_id == YogaId.GAJAKESARI_YOGA

    def test_result_for(self) -> None:
        r1 = YogaResult(
            yoga_id=YogaId.DHANA_YOGA,
            is_present=True,
            strength_modifier=0.5,
            evidence=(),
        )
        report = YogaReport(results=(r1,))
        assert report.result_for(YogaId.DHANA_YOGA) is r1
        assert report.result_for(YogaId.RAJA_YOGA) is None


class TestYogaConfig:
    def test_defaults(self) -> None:
        config = YogaConfig()
        assert config.version == "0.1.0"
        assert config.min_bala_ratio == 0.5
        assert len(config.enabled_yogas) == 4

    def test_from_dict(self) -> None:
        data = {
            "version": "0.2.0",
            "min_bala_ratio": 0.8,
            "enabled_yogas": ["GAJAKESARI_YOGA"],
        }
        config = YogaConfig.from_dict(data)
        assert config.version == "0.2.0"
        assert len(config.enabled_yogas) == 1

    def test_validate(self) -> None:
        config = YogaConfig()
        validated = validate(config)
        assert validated is config

    def test_validate_empty_version(self) -> None:
        from yoga.errors import InvalidYogaConfigError
        import pytest
        config = YogaConfig(version="")
        with pytest.raises(InvalidYogaConfigError):
            validate(config)


class TestSerialization:
    def test_result_to_dict(self) -> None:
        from yoga.serialize import result_to_dict
        result = YogaResult(
            yoga_id=YogaId.GAJAKESARI_YOGA,
            is_present=True,
            strength_modifier=1.0,
            evidence=("test",),
        )
        d = result_to_dict(result)
        assert isinstance(d, dict)
        assert d["yoga_id"] == "GAJAKESARI_YOGA"
        assert d["is_present"] is True
