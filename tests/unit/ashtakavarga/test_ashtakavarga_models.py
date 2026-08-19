"""Unit tests for Ashtakavarga domain models."""

from __future__ import annotations

from jyotish import BodyId

from ashtakavarga.models import (
    PlanetAshtakavarga,
    Sarvashtakavarga,
    AshtakavargaReport,
    compute_planet_bindus,
    compute_sarvashtakavarga,
    CLASSICAL_BINDU_RULES,
)


class TestClassicalBinduRules:
    def test_all_7_planets_defined(self) -> None:
        assert len(CLASSICAL_BINDU_RULES) == 7

    def test_each_rule_tuple_is_ints(self) -> None:
        for planet, houses in CLASSICAL_BINDU_RULES.items():
            assert isinstance(planet, BodyId)
            assert all(isinstance(h, int) for h in houses)

    def test_all_house_values_1_to_12(self) -> None:
        for planet, houses in CLASSICAL_BINDU_RULES.items():
            for h in houses:
                assert 1 <= h <= 12, f"{planet} has invalid house {h}"


class TestComputePlanetBindus:
    def test_sun_in_aries_gives_to_correct_houses(self) -> None:
        # Sun in Aries (index 0): gives to houses 1,2,4,7,8,9,10,11
        bindus = compute_planet_bindus(BodyId.SUN, 0)
        assert len(bindus) == 12
        # House 1 from Aries = Aries (index 0) → 4 bindus
        assert bindus[0] == 4
        # House 2 from Aries = Taurus (index 1) → 4 bindus
        assert bindus[1] == 4
        # House 3 from Aries = Gemini (index 2) → 0 bindus (not in Sun's list)
        assert bindus[2] == 0
        # House 4 from Aries = Cancer (index 3) → 4 bindus
        assert bindus[3] == 4

    def test_sun_in_taurus_shifts_correctly(self) -> None:
        # Sun in Taurus (index 1): gives to houses 1,2,4,7,8,9,10,11
        # House 1 from Taurus = Taurus (index 1) → 4 bindus
        bindus = compute_planet_bindus(BodyId.SUN, 1)
        assert bindus[1] == 4
        # House 2 from Taurus = Gemini (index 2) → 4 bindus
        assert bindus[2] == 4
        # House 3 from Taurus = Cancer (index 3) → 0 bindus
        assert bindus[3] == 0

    def test_bindus_always_non_negative(self) -> None:
        for planet in CLASSICAL_BINDU_RULES:
            for rashi_idx in range(12):
                bindus = compute_planet_bindus(planet, rashi_idx)
                assert all(b >= 0 for b in bindus), (
                    f"{planet} in rashi {rashi_idx} has negative bindus"
                )

    def test_bindus_sum_matches_rule_count(self) -> None:
        """Total bindus for a planet = len(rules) * 4."""
        for planet, houses in CLASSICAL_BINDU_RULES.items():
            bindus = compute_planet_bindus(planet, 0)
            assert sum(bindus) == len(houses) * 4


class TestComputeSarvashtakavarga:
    def test_sums_all_planets(self) -> None:
        pa1 = PlanetAshtakavarga(planet=BodyId.SUN, bindus=(4, 4, 0, 4, 0, 0, 4, 4, 4, 4, 4, 0))
        pa2 = PlanetAshtakavarga(planet=BodyId.MOON, bindus=(4, 0, 0, 0, 0, 4, 4, 4, 0, 0, 4, 4))
        sarva = compute_sarvashtakavarga((pa1, pa2))
        assert sarva.bindus[0] == 8  # 4+4
        assert sarva.bindus[1] == 4  # 4+0
        assert sarva.bindus[2] == 0  # 0+0


class TestPlanetAshtakavarga:
    def test_to_dict(self) -> None:
        pa = PlanetAshtakavarga(
            planet=BodyId.SUN,
            bindus=(4, 4, 0, 4, 0, 0, 4, 4, 4, 4, 4, 0),
        )
        d = pa.to_dict()
        assert d["planet"] == "SUN"
        assert isinstance(d["bindus"], list)
        assert len(d["bindus"]) == 12


class TestSarvashtakavarga:
    def test_to_dict(self) -> None:
        sv = Sarvashtakavarga(bindus=(28, 24, 16, 28, 16, 20, 28, 28, 24, 24, 28, 16))
        d = sv.to_dict()
        assert isinstance(d["bindus"], list)
        assert len(d["bindus"]) == 12


class TestAshtakavargaReport:
    def test_result_for(self) -> None:
        pa = PlanetAshtakavarga(planet=BodyId.SUN, bindus=(4,) * 12)
        sv = Sarvashtakavarga(bindus=(4,) * 12)
        report = AshtakavargaReport(
            bhinnashtakavarga=(pa,),
            sarvashtakavarga=sv,
        )
        assert report.result_for(BodyId.SUN) is not None
        assert report.result_for(BodyId.MOON) is None

    def test_to_dict(self) -> None:
        pa = PlanetAshtakavarga(planet=BodyId.SUN, bindus=(4,) * 12)
        sv = Sarvashtakavarga(bindus=(4,) * 12)
        report = AshtakavargaReport(
            bhinnashtakavarga=(pa,),
            sarvashtakavarga=sv,
        )
        d = report.to_dict()
        assert "bhinnashtakavarga" in d
        assert "sarvashtakavarga" in d
