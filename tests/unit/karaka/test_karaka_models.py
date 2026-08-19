"""JRE-014 Karaka model tests."""

from __future__ import annotations

from jyotish import BodyId

from karaka.models import (
    KARAKA_VERSION,
    CHARA_KARAKA_RANKS,
    DEFAULT_NAISARGIKA,
    DEFAULT_STHIRA,
    KarakaAssignment,
    KarakaCategory,
    KarakaConfig,
    KarakaReport,
    KarakaType,
    compute_chara_karakas,
    validate,
)
from tests.unit.karaka.conftest import make_planet_state


class TestConstants:
    def test_version(self) -> None:
        assert KARAKA_VERSION == "0.1.0"

    def test_naisargika_all_planets(self) -> None:
        for planet in BodyId:
            if planet in {BodyId.RAHU, BodyId.KETU}:
                continue
            assert planet in DEFAULT_NAISARGIKA

    def test_sthira_has_categories(self) -> None:
        assert KarakaCategory.ATMA in DEFAULT_STHIRA
        assert KarakaCategory.DHANA in DEFAULT_STHIRA
        assert KarakaCategory.DARA in DEFAULT_STHIRA

    def test_chara_ranks_count(self) -> None:
        assert len(CHARA_KARAKA_RANKS) == 7

    def test_chara_first_is_atma(self) -> None:
        assert CHARA_KARAKA_RANKS[0] == KarakaCategory.ATMA


class TestKarakaCategory:
    def test_all_values(self) -> None:
        cats = [c.value for c in KarakaCategory]
        assert "ATMA" in cats
        assert "PUTRA" in cats
        assert "DHANA" in cats
        assert "DARA" in cats
        assert "BHRATRU" in cats


class TestKarakaType:
    def test_all_types(self) -> None:
        types = [t.value for t in KarakaType]
        assert "NAISARGIKA" in types
        assert "STHIRA" in types
        assert "CHARA" in types
        assert "VISHESHA" in types


class TestKarakaAssignment:
    def test_construction(self) -> None:
        a = KarakaAssignment(
            category=KarakaCategory.ATMA,
            planet=BodyId.SUN,
            karaka_type=KarakaType.NAISARGIKA,
            rank=1,
            strength_modifier=0.9,
        )
        assert a.category == KarakaCategory.ATMA
        assert a.planet == BodyId.SUN
        assert a.strength_modifier == 0.9


class TestKarakaReport:
    def test_karakas_for_category(self) -> None:
        a1 = KarakaAssignment(
            category=KarakaCategory.ATMA,
            planet=BodyId.SUN,
            karaka_type=KarakaType.NAISARGIKA,
            rank=1,
        )
        a2 = KarakaAssignment(
            category=KarakaCategory.DHANA,
            planet=BodyId.JUPITER,
            karaka_type=KarakaType.STHIRA,
            rank=1,
        )
        report = KarakaReport(assignments=(a1, a2))
        atma = report.karakas_for_category(KarakaCategory.ATMA)
        assert len(atma) == 1
        assert atma[0].planet == BodyId.SUN

    def test_karakas_for_planet(self) -> None:
        a1 = KarakaAssignment(
            category=KarakaCategory.ATMA,
            planet=BodyId.SUN,
            karaka_type=KarakaType.NAISARGIKA,
            rank=1,
        )
        report = KarakaReport(assignments=(a1,))
        sun_karakas = report.karakas_for_planet(BodyId.SUN)
        assert len(sun_karakas) == 1

    def test_karakas_by_type(self) -> None:
        a1 = KarakaAssignment(
            category=KarakaCategory.ATMA,
            planet=BodyId.SUN,
            karaka_type=KarakaType.NAISARGIKA,
            rank=1,
        )
        a2 = KarakaAssignment(
            category=KarakaCategory.ATMA,
            planet=BodyId.SUN,
            karaka_type=KarakaType.CHARA,
            rank=1,
        )
        report = KarakaReport(assignments=(a1, a2))
        nais = report.karakas_by_type(KarakaType.NAISARGIKA)
        assert len(nais) == 1


class TestComputeCharaKarakas:
    def test_highest_degree_is_atmakaraka(self) -> None:
        """Planet with highest degree-in-sign should be Atmakaraka."""
        states = (
            make_planet_state(BodyId.SUN, 100.0),    # 10 deg in sign
            make_planet_state(BodyId.MOON, 33.0),    # 3 deg in sign
            make_planet_state(BodyId.MARS, 200.0),   # 20 deg in sign
            make_planet_state(BodyId.MERCURY, 165.0), # 15 deg in sign
            make_planet_state(BodyId.JUPITER, 95.0),  # 5 deg in sign
            make_planet_state(BodyId.VENUS, 357.0),   # 27 deg in sign
            make_planet_state(BodyId.SATURN, 250.0),  # 10 deg in sign
        )
        result = compute_chara_karakas(states, count=7)
        assert len(result) == 7
        # Venus at 27 deg should be rank 1 (Atmakaraka)
        assert result[0] == (KarakaCategory.ATMA, BodyId.VENUS)

    def test_count_limits_results(self) -> None:
        states = (
            make_planet_state(BodyId.SUN, 100.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 200.0),
        )
        result = compute_chara_karakas(states, count=2)
        assert len(result) == 2

    def test_empty_states(self) -> None:
        result = compute_chara_karakas((), count=7)
        assert len(result) == 0


class TestKarakaConfig:
    def test_defaults(self) -> None:
        config = KarakaConfig()
        assert config.version == "0.1.0"
        assert config.chara_planet_count == 7

    def test_from_dict(self) -> None:
        data = {
            "version": "0.2.0",
            "chara_planet_count": 8,
            "naisargika": {"SUN": "ATMA"},
            "sthira": {"ATMA": "SUN"},
        }
        config = KarakaConfig.from_dict(data)
        assert config.version == "0.2.0"
        assert config.chara_planet_count == 8

    def test_validate(self) -> None:
        config = KarakaConfig()
        validated = validate(config)
        assert validated is config

    def test_validate_empty_version(self) -> None:
        from karaka.errors import InvalidKarakaConfigError
        import pytest
        config = KarakaConfig(version="")
        with pytest.raises(InvalidKarakaConfigError):
            validate(config)


class TestSerialization:
    def test_result_to_dict(self) -> None:
        from karaka.serialize import result_to_dict
        a = KarakaAssignment(
            category=KarakaCategory.ATMA,
            planet=BodyId.SUN,
            karaka_type=KarakaType.NAISARGIKA,
            rank=1,
        )
        d = result_to_dict(a)
        assert isinstance(d, dict)
        assert d["category"] == "ATMA"
        assert d["planet"] == "SUN"
