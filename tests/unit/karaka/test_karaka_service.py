"""JRE-014 KarakaService unit tests."""

from __future__ import annotations

import pytest
from jyotish import BodyId

from karaka.models import (
    KarakaCategory,
    KarakaConfig,
    KarakaReport,
    KarakaType,
)
from karaka.service import KarakaService
from tests.unit.karaka.conftest import make_classical_planets, make_planet_state


class TestKarakaServiceInit:
    def test_default_config(self) -> None:
        service = KarakaService()
        assert service.config.version == "0.1.0"

    def test_custom_config(self) -> None:
        config = KarakaConfig(chara_planet_count=5)
        service = KarakaService(config)
        assert service.config.chara_planet_count == 5


class TestNaisargikaKarakas:
    def test_sun_is_atma(self) -> None:
        service = KarakaService()
        states = make_classical_planets()
        result = service.calculate_karakas(states)
        nais = result.karakas_by_type(KarakaType.NAISARGIKA)
        sun_nais = [a for a in nais if a.planet == BodyId.SUN]
        assert len(sun_nais) == 1
        assert sun_nais[0].category == KarakaCategory.ATMA

    def test_jupiter_is_putra(self) -> None:
        service = KarakaService()
        states = make_classical_planets()
        result = service.calculate_karakas(states)
        nais = result.karakas_by_type(KarakaType.NAISARGIKA)
        jup_nais = [a for a in nais if a.planet == BodyId.JUPITER]
        assert len(jup_nais) == 1
        assert jup_nais[0].category == KarakaCategory.PUTRA

    def test_all_classical_planets_have_naisargika(self) -> None:
        service = KarakaService()
        states = make_classical_planets()
        result = service.calculate_karakas(states)
        nais = result.karakas_by_type(KarakaType.NAISARGIKA)
        assert len(nais) == 7


class TestSthiraKarakas:
    def test_atma_is_sun(self) -> None:
        service = KarakaService()
        states = make_classical_planets()
        result = service.calculate_karakas(states)
        sthi = result.karakas_by_type(KarakaType.STHIRA)
        atma_sthi = [a for a in sthi if a.category == KarakaCategory.ATMA]
        assert len(atma_sthi) == 1
        assert atma_sthi[0].planet == BodyId.SUN

    def test_dhana_is_jupiter(self) -> None:
        service = KarakaService()
        states = make_classical_planets()
        result = service.calculate_karakas(states)
        sthi = result.karakas_by_type(KarakaType.STHIRA)
        dhana_sthi = [a for a in sthi if a.category == KarakaCategory.DHANA]
        assert len(dhana_sthi) == 1
        assert dhana_sthi[0].planet == BodyId.JUPITER


class TestCharaKarakas:
    def test_chara_assignments_present(self) -> None:
        service = KarakaService()
        states = make_classical_planets()
        result = service.calculate_karakas(states)
        chara = result.karakas_by_type(KarakaType.CHARA)
        assert len(chara) == 7

    def test_chara_ranks_sequential(self) -> None:
        service = KarakaService()
        states = make_classical_planets()
        result = service.calculate_karakas(states)
        chara = result.karakas_by_type(KarakaType.CHARA)
        ranks = sorted(a.rank for a in chara)
        assert ranks == [1, 2, 3, 4, 5, 6, 7]

    def test_chara_highest_degree_is_ak(self) -> None:
        """Planet with highest degree-in-sign should be Atmakaraka."""
        service = KarakaService()
        # Venus at 357° has 27° in sign — highest among classical planets
        states = (
            make_planet_state(BodyId.SUN, 100.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 200.0),
            make_planet_state(BodyId.MERCURY, 165.0),
            make_planet_state(BodyId.JUPITER, 95.0),
            make_planet_state(BodyId.VENUS, 357.0),
            make_planet_state(BodyId.SATURN, 250.0),
        )
        result = service.calculate_karakas(states)
        chara = result.karakas_by_type(KarakaType.CHARA)
        ak = [a for a in chara if a.category == KarakaCategory.ATMA]
        assert len(ak) == 1
        assert ak[0].planet == BodyId.VENUS
        assert ak[0].rank == 1


class TestValidation:
    def test_empty_planet_states(self) -> None:
        service = KarakaService()
        from karaka.errors import InvalidKarakaRequestError
        with pytest.raises(InvalidKarakaRequestError):
            service.calculate_karakas(planet_states=())

    def test_non_tuple_input(self) -> None:
        service = KarakaService()
        from karaka.errors import InvalidKarakaRequestError
        with pytest.raises(InvalidKarakaRequestError):
            service.calculate_karakas(planet_states=[make_planet_state(BodyId.SUN, 0.0)])  # type: ignore[arg-type]
