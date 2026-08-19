"""JRE-013 YogaService unit tests."""

from __future__ import annotations

import pytest
from jyotish import BodyId, RashiId

from yoga.models import (
    ConnectionType,
    YogaConfig,
    YogaId,
    YogaReport,
    YogaResult,
)
from yoga.service import YogaService
from tests.unit.yoga.conftest import (
    make_dhana_yoga_chart,
    make_gajakesari_chart,
    make_no_gajakesari_chart,
    make_no_raja_yoga_chart,
    make_planet_state,
    make_raja_yoga_chart,
    make_viparita_chart,
)


class TestYogaServiceInit:
    def test_default_config(self) -> None:
        service = YogaService()
        assert service.config.version == "0.1.0"

    def test_custom_config(self) -> None:
        config = YogaConfig(min_bala_ratio=0.8)
        service = YogaService(config)
        assert service.config.min_bala_ratio == 0.8


class TestGajakesariYoga:
    def test_present_when_jupiter_in_kendra_from_moon(self) -> None:
        """Jupiter at 90 (Cancer), Moon at 0 (Aries) — 4th from Moon."""
        service = YogaService()
        states = make_gajakesari_chart()
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        assert gaja.is_present is True

    def test_absent_when_not_in_kendra(self) -> None:
        """Jupiter at 30 (Taurus), Moon at 0 (Aries) — 2nd from Moon."""
        service = YogaService()
        states = make_no_gajakesari_chart()
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        assert gaja.is_present is False

    def test_jupiter_in_7th_from_moon(self) -> None:
        """Jupiter at 180 (Libra), Moon at 0 (Aries) — 7th from Moon."""
        service = YogaService()
        states = (
            make_planet_state(BodyId.MOON, 0.0),
            make_planet_state(BodyId.JUPITER, 180.0),
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        assert gaja.is_present is True

    def test_jupiter_in_10th_from_moon(self) -> None:
        """Jupiter at 270 (Capricorn), Moon at 0 (Aries) — 10th from Moon."""
        service = YogaService()
        states = (
            make_planet_state(BodyId.MOON, 0.0),
            make_planet_state(BodyId.JUPITER, 270.0),
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        assert gaja.is_present is True

    def test_jupiter_in_1st_from_moon(self) -> None:
        """Jupiter at 5 (Aries), Moon at 0 (Aries) — same sign, 1st."""
        service = YogaService()
        states = (
            make_planet_state(BodyId.MOON, 0.0),
            make_planet_state(BodyId.JUPITER, 5.0),
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        assert gaja.is_present is True

    def test_missing_planets(self) -> None:
        """Without Jupiter, Gajakesari should not be present."""
        service = YogaService()
        states = (make_planet_state(BodyId.MOON, 0.0),)
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        assert gaja.is_present is False


class TestRajaYoga:
    def test_present_when_conjunction(self) -> None:
        """Lagna Aries: Mars (1st lord) conjunct Sun (5th lord)."""
        service = YogaService()
        states = make_raja_yoga_chart()
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        raja = result.result_for(YogaId.RAJA_YOGA)
        assert raja is not None
        assert raja.is_present is True

    def test_absent_when_no_connection(self) -> None:
        """Lagna Aries: Mars and Sun in different signs, no aspect."""
        service = YogaService()
        states = make_no_raja_yoga_chart()
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        raja = result.result_for(YogaId.RAJA_YOGA)
        assert raja is not None
        assert raja.is_present is False

    def test_no_lagna(self) -> None:
        """Without lagna, Raja Yoga cannot be evaluated."""
        service = YogaService()
        states = make_raja_yoga_chart()
        result = service.identify_yogas(states, lagna_sign=None)
        raja = result.result_for(YogaId.RAJA_YOGA)
        assert raja is not None
        assert raja.is_present is False


class TestDhanaYoga:
    def test_present_when_conjunction(self) -> None:
        """Lagna Aries: Venus (2nd lord) conjunct Saturn (11th lord)."""
        service = YogaService()
        states = make_dhana_yoga_chart()
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        dhana = result.result_for(YogaId.DHANA_YOGA)
        assert dhana is not None
        assert dhana.is_present is True

    def test_absent_when_no_connection(self) -> None:
        """Lagna Aries: Venus and Saturn in different signs."""
        service = YogaService()
        states = (
            make_planet_state(BodyId.VENUS, 0.0),
            make_planet_state(BodyId.SATURN, 120.0),
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        dhana = result.result_for(YogaId.DHANA_YOGA)
        assert dhana is not None
        assert dhana.is_present is False


class TestViparitaRajaYoga:
    def test_present_when_conjunction(self) -> None:
        """Lagna Aries: Mercury (6th lord) conjunct Mars (8th lord)."""
        service = YogaService()
        states = make_viparita_chart()
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        viparita = result.result_for(YogaId.VIPARITA_RAJA_YOGA)
        assert viparita is not None
        assert viparita.is_present is True

    def test_absent_when_no_connection(self) -> None:
        """Lagna Aries: Mercury and Mars in different signs."""
        service = YogaService()
        states = (
            make_planet_state(BodyId.MERCURY, 0.0),
            make_planet_state(BodyId.MARS, 120.0),
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        viparita = result.result_for(YogaId.VIPARITA_RAJA_YOGA)
        assert viparita is not None
        assert viparita.is_present is False


class TestValidation:
    def test_empty_planet_states(self) -> None:
        service = YogaService()
        from yoga.errors import InvalidYogaRequestError
        with pytest.raises(InvalidYogaRequestError):
            service.identify_yogas(planet_states=())

    def test_non_tuple_input(self) -> None:
        service = YogaService()
        from yoga.errors import InvalidYogaRequestError
        with pytest.raises(InvalidYogaRequestError):
            service.identify_yogas(planet_states=[make_planet_state(BodyId.SUN, 0.0)])  # type: ignore[arg-type]
