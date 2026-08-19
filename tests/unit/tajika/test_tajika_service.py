"""Unit tests for TajikaService."""

from __future__ import annotations

from jyotish import BodyId, RashiId

from tajika.models import SahamType, TajikaReport
from tajika.service import TajikaService
from tests.unit.tajika.conftest import (
    make_sun_state,
    make_moon_state,
    make_jupiter_state,
    make_venus_state,
    make_mars_state,
    make_mercury_state,
    make_saturn_state,
)


class TestTajikaServiceBasic:
    def test_single_year(self) -> None:
        svc = TajikaService()
        planets = (
            make_sun_state(10.0),
            make_moon_state(33.0),
            make_mars_state(60.0),
            make_mercury_state(90.0),
            make_jupiter_state(150.0),
            make_venus_state(210.0),
            make_saturn_state(270.0),
        )
        report = svc.calculate_tajika(
            natal_moon_rashi=RashiId.MESHA,
            lagna_longitude=100.0,
            planet_states=planets,
            elapsed_years=1,
            year_lord=BodyId.JUPITER,
            lagna_lord=BodyId.SUN,
        )
        assert isinstance(report, TajikaReport)
        assert report.muntha.rashi == RashiId.VRISHABHA  # Aries + 1 = Taurus

    def test_12_year_cycle(self) -> None:
        svc = TajikaService()
        planets = (
            make_sun_state(10.0),
            make_moon_state(33.0),
            make_mars_state(60.0),
            make_mercury_state(90.0),
            make_jupiter_state(150.0),
            make_venus_state(210.0),
            make_saturn_state(270.0),
        )
        report = svc.calculate_tajika(
            natal_moon_rashi=RashiId.MESHA,
            lagna_longitude=100.0,
            planet_states=planets,
            elapsed_years=12,
            year_lord=BodyId.JUPITER,
            lagna_lord=BodyId.SUN,
        )
        assert report.muntha.rashi == RashiId.MESHA  # Back to Aries

    def test_sahams_computed(self) -> None:
        svc = TajikaService()
        planets = (
            make_sun_state(10.0),
            make_moon_state(33.0),
            make_mars_state(60.0),
            make_mercury_state(90.0),
            make_jupiter_state(150.0),
            make_venus_state(210.0),
            make_saturn_state(270.0),
        )
        report = svc.calculate_tajika(
            natal_moon_rashi=RashiId.MESHA,
            lagna_longitude=100.0,
            planet_states=planets,
            elapsed_years=1,
            year_lord=BodyId.JUPITER,
            lagna_lord=BodyId.SUN,
        )
        assert len(report.sahams) == 10  # All classical Sahams

    def test_deterministic(self) -> None:
        svc = TajikaService()
        planets = (make_sun_state(10.0),)
        r1 = svc.calculate_tajika(
            natal_moon_rashi=RashiId.MESHA,
            lagna_longitude=100.0,
            planet_states=planets,
            elapsed_years=5,
            year_lord=BodyId.JUPITER,
            lagna_lord=BodyId.SUN,
        )
        r2 = svc.calculate_tajika(
            natal_moon_rashi=RashiId.MESHA,
            lagna_longitude=100.0,
            planet_states=planets,
            elapsed_years=5,
            year_lord=BodyId.JUPITER,
            lagna_lord=BodyId.SUN,
        )
        assert r1.to_dict() == r2.to_dict()


class TestTajikaServiceValidation:
    def test_empty_planets_raises(self) -> None:
        svc = TajikaService()
        import pytest
        with pytest.raises(Exception):
            svc.calculate_tajika(
                natal_moon_rashi=RashiId.MESHA,
                lagna_longitude=100.0,
                planet_states=(),
                elapsed_years=1,
                year_lord=BodyId.JUPITER,
                lagna_lord=BodyId.SUN,
            )

    def test_negative_years_raises(self) -> None:
        svc = TajikaService()
        import pytest
        with pytest.raises(Exception):
            svc.calculate_tajika(
                natal_moon_rashi=RashiId.MESHA,
                lagna_longitude=100.0,
                planet_states=(make_sun_state(10.0),),
                elapsed_years=-1,
                year_lord=BodyId.JUPITER,
                lagna_lord=BodyId.SUN,
            )
