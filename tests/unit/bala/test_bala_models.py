"""JRE-011 Bala model tests.

Tests for dataclass construction, validation, serialization, and
pure derivation helpers.
"""

from __future__ import annotations

import math

from jyotish import BodyId

from bala.models import (
    BALA_PLANETS,
    BALA_VERSION,
    DEFAULT_MINIMUM_RUPAS,
    DEFAULT_NAISARGIKA_VIRUPAS,
    DIG_BALA_PEAK_HOUSE,
    EXALTATION_DEGREES,
    DEBILITATION_DEGREES,
    KENDRA_HOUSES,
    VIRUPAS_PER_RUPA,
    BalaConfig,
    BalaSystem,
    IshtaKashtaPhala,
    KalaBalaComponents,
    ShadbalaComponents,
    ShadbalaReport,
    ShadbalaResult,
    SthanaBalaComponents,
    get_dignity,
    validate,
)


class TestConstants:
    """Verify constants are well-formed."""

    def test_virupas_per_rupa(self) -> None:
        assert VIRUPAS_PER_RUPA == 60

    def test_bala_planets_count(self) -> None:
        assert len(BALA_PLANETS) == 9

    def test_bala_planets_include_all(self) -> None:
        for body in BodyId:
            assert body in BALA_PLANETS

    def test_version_is_string(self) -> None:
        assert isinstance(BALA_VERSION, str)
        assert BALA_VERSION == "0.1.0"

    def test_exaltation_debilitation_opposite(self) -> None:
        """Exaltation and debilitation should be 180 degrees apart."""
        for planet in EXALTATION_DEGREES:
            if planet in {BodyId.RAHU, BodyId.KETU}:
                continue  # Rahu/Ketu have special rules
            exalt = EXALTATION_DEGREES[planet]
            debil = DEBILITATION_DEGREES[planet]
            diff = (exalt - debil) % 360.0
            assert math.isclose(diff, 180.0, abs_tol=0.1), (
                f"{planet}: exalt={exalt}, debil={debil}, diff={diff}"
            )

    def test_dig_bala_peaks_for_all_planets(self) -> None:
        for planet in BALA_PLANETS:
            assert planet in DIG_BALA_PEAK_HOUSE
            house = DIG_BALA_PEAK_HOUSE[planet]
            assert 1 <= house <= 12

    def test_kendra_houses(self) -> None:
        assert KENDRA_HOUSES == frozenset({1, 4, 7, 10})

    def test_naisargika_strengths_sum(self) -> None:
        total = sum(DEFAULT_NAISARGIKA_VIRUPAS.values())
        # Total should be approximately 248.58 (sum of all 9 planets)
        assert math.isclose(total, 248.58, rel_tol=0.01)

    def test_minimum_rupas_for_all_planets(self) -> None:
        for planet in BALA_PLANETS:
            assert planet.value in DEFAULT_MINIMUM_RUPAS
            assert DEFAULT_MINIMUM_RUPAS[planet] > 0


class TestGetDignity:
    """Test the get_dignity helper."""

    def test_own_sign(self) -> None:
        assert get_dignity(BodyId.SUN, BodyId.SUN) == "OWN"

    def test_friend_sign(self) -> None:
        # Sun in Moon's sign (Cancer) -- Moon is friend of Sun
        assert get_dignity(BodyId.SUN, BodyId.MOON) == "FRIEND"

    def test_enemy_sign(self) -> None:
        # Sun in Venus's sign (Libra) -- Venus is enemy of Sun
        assert get_dignity(BodyId.SUN, BodyId.VENUS) == "ENEMY"

    def test_neutral_or_enemy(self) -> None:
        # Sun in Saturn's sign
        result = get_dignity(BodyId.SUN, BodyId.SATURN)
        assert result in {"ENEMY", "NEUTRAL", "FRIEND"}

    def test_intermediary_friend(self) -> None:
        # Jupiter in Moon's sign
        result = get_dignity(BodyId.JUPITER, BodyId.MOON)
        assert result in {"FRIEND", "NEUTRAL"}


class TestSthanaBalaComponents:
    """Test SthanaBalaComponents dataclass."""

    def test_defaults(self) -> None:
        comp = SthanaBalaComponents()
        assert comp.total == 0.0

    def test_total(self) -> None:
        comp = SthanaBalaComponents(
            uchcha_bala=30.0,
            saptavargaja_bala=10.0,
            ojhayugma_bala=20.0,
            kendradi_bala=45.0,
            drekkana_bala=8.0,
        )
        assert comp.total == 113.0


class TestKalaBalaComponents:
    """Test KalaBalaComponents dataclass."""

    def test_defaults(self) -> None:
        comp = KalaBalaComponents()
        assert comp.total == 0.0

    def test_total(self) -> None:
        comp = KalaBalaComponents(
            nathonnatha_bala=30.0,
            paksha_bala=45.0,
            tribhaga_bala=10.0,
            ayana_bala=20.0,
            yudhdha_bala=0.0,
        )
        assert comp.total == 105.0


class TestShadbalaComponents:
    """Test ShadbalaComponents dataclass."""

    def test_defaults(self) -> None:
        comp = ShadbalaComponents()
        assert comp.total_virupas == 0.0
        assert comp.total_rupas == 0.0

    def test_total_virupas(self) -> None:
        comp = ShadbalaComponents(
            sthana_bala=SthanaBalaComponents(uchcha_bala=30.0),
            dig_bala=45.0,
            kala_bala=KalaBalaComponents(nathonnatha_bala=25.0),
            cheshta_bala=40.0,
            naisargika_bala=50.0,
            drik_bala=10.0,
        )
        assert comp.total_virupas == 200.0
        assert math.isclose(comp.total_rupas, 200.0 / 60.0, rel_tol=1e-10)


class TestIshtaKashtaPhala:
    """Test IshtaKashtaPhala dataclass."""

    def test_defaults(self) -> None:
        phala = IshtaKashtaPhala()
        assert phala.ishta_phala == 0.0
        assert phala.kashta_phala == 0.0

    def test_values(self) -> None:
        phala = IshtaKashtaPhala(ishta_phala=30.0, kashta_phala=25.0)
        assert phala.ishta_phala == 30.0
        assert phala.kashta_phala == 25.0


class TestShadbalaResult:
    """Test ShadbalaResult dataclass."""

    def test_construction(self) -> None:
        result = ShadbalaResult(
            planet=BodyId.SUN,
            components=ShadbalaComponents(),
            total_virupas=150.0,
            total_rupas=2.5,
            minimum_required=5.0,
            ratio=0.5,
            ishta_kashta=IshtaKashtaPhala(),
        )
        assert result.planet == BodyId.SUN
        assert result.total_virupas == 150.0
        assert result.ratio == 0.5


class TestShadbalaReport:
    """Test ShadbalaReport dataclass."""

    def test_result_for(self) -> None:
        result = ShadbalaResult(
            planet=BodyId.SUN,
            components=ShadbalaComponents(),
            total_virupas=150.0,
            total_rupas=2.5,
            minimum_required=5.0,
            ratio=0.5,
            ishta_kashta=IshtaKashtaPhala(),
        )
        report = ShadbalaReport(results=(result,))
        assert report.result_for(BodyId.SUN) is result
        assert report.result_for(BodyId.MOON) is None


class TestBalaConfig:
    """Test BalaConfig dataclass."""

    def test_defaults(self) -> None:
        config = BalaConfig()
        assert config.version == "0.1.0"
        assert config.max_depth == 1

    def test_from_dict(self) -> None:
        data = {
            "version": "0.2.0",
            "max_depth": 2,
            "minimum_rupas": {"SUN": 6.0},
            "naisargika_virupas": {"SUN": 70.0},
        }
        config = BalaConfig.from_dict(data)
        assert config.version == "0.2.0"
        assert config.max_depth == 2

    def test_validate(self) -> None:
        config = BalaConfig()
        validated = validate(config)
        assert validated is config

    def test_validate_empty_version(self) -> None:
        from bala.errors import InvalidBalaConfigError
        import pytest
        config = BalaConfig(version="")
        with pytest.raises(InvalidBalaConfigError):
            validate(config)


class TestSerialization:
    """Test serialization round-trip."""

    def test_result_to_dict(self) -> None:
        from bala.serialize import result_to_dict
        result = ShadbalaResult(
            planet=BodyId.SUN,
            components=ShadbalaComponents(),
            total_virupas=150.0,
            total_rupas=2.5,
            minimum_required=5.0,
            ratio=0.5,
            ishta_kashta=IshtaKashtaPhala(),
        )
        d = result_to_dict(result)
        assert isinstance(d, dict)
        assert d["planet"] == "SUN"
        assert d["total_virupas"] == 150.0

    def test_config_to_dict(self) -> None:
        from bala.serialize import result_to_dict
        config = BalaConfig()
        d = result_to_dict(config)
        assert isinstance(d, dict)
        assert d["version"] == "0.1.0"
