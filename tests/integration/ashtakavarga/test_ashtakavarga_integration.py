"""Integration tests for JRE-016 Ashtakavarga engine."""

from __future__ import annotations

from jyotish import BodyId

from ashtakavarga import AshtakavargaService, AshtakavargaReport
from ashtakavarga.models import (
    CLASSICAL_BINDU_RULES,
    BINDUS_PER_CONTRIBUTION,
    compute_planet_bindus,
)
from tests.unit.ashtakavarga.conftest import (
    make_sun_state,
    make_moon_state,
    make_mars_state,
    make_mercury_state,
    make_jupiter_state,
    make_venus_state,
    make_saturn_state,
    make_planet_state,
)


class TestAshtakavargaIntegration:
    """Full Ashtakavarga computation against known reference states."""

    def test_single_planet_bindu_sum(self) -> None:
        """Each planet's total bindus = len(rules) * 4."""
        svc = AshtakavargaService()
        sun = make_sun_state(10.0)
        report = svc.calculate_ashtakavarga((sun,))
        pa = report.result_for(BodyId.SUN)
        assert pa is not None
        expected = len(CLASSICAL_BINDU_RULES[BodyId.SUN]) * BINDUS_PER_CONTRIBUTION
        assert sum(pa.bindus) == expected

    def test_all_planets_computed(self) -> None:
        svc = AshtakavargaService()
        planets = (
            make_sun_state(10.0),
            make_moon_state(33.0),
            make_mars_state(60.0),
            make_mercury_state(90.0),
            make_jupiter_state(150.0),
            make_venus_state(210.0),
            make_saturn_state(270.0),
        )
        report = svc.calculate_ashtakavarga(planets)
        assert len(report.bhinnashtakavarga) == 7
        assert len(report.sarvashtakavarga.bindus) == 12

    def test_sarvashtakavarga_is_sum(self) -> None:
        svc = AshtakavargaService()
        planets = (
            make_sun_state(10.0),
            make_moon_state(33.0),
        )
        report = svc.calculate_ashtakavarga(planets)
        # Manually compute expected sarvashtakavarga
        pa1 = compute_planet_bindus(BodyId.SUN, 0)  # Aries
        pa2 = compute_planet_bindus(BodyId.MOON, 1)  # Taurus (33° ≈ Taurus)
        for i in range(12):
            expected = pa1[i] + pa2[i]
            assert report.sarvashtakavarga.bindus[i] == expected

    def test_deterministic_output(self) -> None:
        svc = AshtakavargaService()
        sun = make_sun_state(10.0)
        r1 = svc.calculate_ashtakavarga((sun,))
        r2 = svc.calculate_ashtakavarga((sun,))
        assert r1.to_dict() == r2.to_dict()

    def test_report_to_dict_is_serializable(self) -> None:
        svc = AshtakavargaService()
        report = svc.calculate_ashtakavarga((make_sun_state(10.0),))
        d = report.to_dict()
        assert isinstance(d, dict)
        assert "bhinnashtakavarga" in d
        assert "sarvashtakavarga" in d

    def test_sarvashtakavarga_non_negative(self) -> None:
        svc = AshtakavargaService()
        planets = (
            make_sun_state(10.0),
            make_moon_state(33.0),
            make_mars_state(60.0),
            make_mercury_state(90.0),
            make_jupiter_state(150.0),
            make_venus_state(210.0),
            make_saturn_state(270.0),
        )
        report = svc.calculate_ashtakavarga(planets)
        for bindu in report.sarvashtakavarga.bindus:
            assert bindu >= 0

    def test_max_sarvashtakavarga(self) -> None:
        """Max possible Sarvashtakavarga = 7 planets * 48 bindus = 336,
        but actual max depends on planetary positions. With all planets
        in the same rashi, each rashi gets contributions from all 7 planets."""
        svc = AshtakavargaService()
        # All planets in Aries (rashi index 0)
        planets = (
            make_sun_state(10.0),
            make_moon_state(15.0),
            make_mars_state(20.0),
            make_mercury_state(5.0),
            make_jupiter_state(25.0),
            make_venus_state(8.0),
            make_saturn_state(12.0),
        )
        report = svc.calculate_ashtakavarga(planets)
        # Each rashi's total should be <= 336
        for bindu in report.sarvashtakavarga.bindus:
            assert bindu <= 336
