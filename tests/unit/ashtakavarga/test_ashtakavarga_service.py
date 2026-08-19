"""Unit tests for AshtakavargaService."""

from __future__ import annotations

from jyotish import BodyId

from ashtakavarga.models import compute_planet_bindus
from ashtakavarga.service import AshtakavargaService
from tests.unit.ashtakavarga.conftest import (
    make_sun_state,
    make_moon_state,
    make_planet_state,
)


class TestAshtakavargaServiceBasic:
    def test_single_planet(self) -> None:
        svc = AshtakavargaService()
        sun = make_sun_state(10.0)  # Aries
        report = svc.calculate_ashtakavarga((sun,))
        assert len(report.bhinnashtakavarga) == 1
        assert report.bhinnashtakavarga[0].planet == BodyId.SUN

    def test_multi_planet(self) -> None:
        svc = AshtakavargaService()
        sun = make_sun_state(10.0)
        moon = make_moon_state(33.0)
        report = svc.calculate_ashtakavarga((sun, moon))
        assert len(report.bhinnashtakavarga) == 2

    def test_sarvashtakavarga_length(self) -> None:
        svc = AshtakavargaService()
        sun = make_sun_state(10.0)
        report = svc.calculate_ashtakavarga((sun,))
        assert len(report.sarvashtakavarga.bindus) == 12

    def test_deterministic(self) -> None:
        svc = AshtakavargaService()
        sun = make_sun_state(10.0)
        r1 = svc.calculate_ashtakavarga((sun,))
        r2 = svc.calculate_ashtakavarga((sun,))
        assert r1.to_dict() == r2.to_dict()


class TestAshtakavargaServiceValidation:
    def test_empty_tuple_raises(self) -> None:
        svc = AshtakavargaService()
        import pytest
        with pytest.raises(Exception):
            svc.calculate_ashtakavarga(())

    def test_non_tuple_raises(self) -> None:
        svc = AshtakavargaService()
        import pytest
        with pytest.raises(Exception):
            svc.calculate_ashtakavarga([make_sun_state(10.0)])  # type: ignore
