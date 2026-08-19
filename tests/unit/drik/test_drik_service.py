"""JRE-012 DrikService unit tests."""

from __future__ import annotations

import math

import pytest
from jyotish import BodyId

from drik.models import (
    AspectDirection,
    AspectType,
    DrikConfig,
    DrikResult,
)
from drik.service import DrikService
from tests.unit.drik.conftest import (
    make_jupiter_5th_aspect,
    make_jupiter_9th_aspect,
    make_mars_4th_aspect,
    make_mars_8th_aspect,
    make_opposition_pair,
    make_planet_state,
    make_saturn_3rd_aspect,
    make_saturn_10th_aspect,
)


class TestDrikServiceInit:
    def test_default_config(self) -> None:
        service = DrikService()
        assert service.config.version == "0.1.0"

    def test_custom_config(self) -> None:
        config = DrikConfig(default_orb_deg=10.0)
        service = DrikService(config)
        assert service.config.default_orb_deg == 10.0


class TestStandardAspect:
    def test_opposition_detected(self) -> None:
        """Planets at 180 degrees should produce a 7th house aspect."""
        sun, moon = make_opposition_pair()
        service = DrikService()
        result = service.calculate_aspects((sun, moon))
        assert len(result.aspects) >= 2  # Sun->Moon and Moon->Sun
        for app in result.aspects:
            assert app.aspect_type == AspectType.STANDARD
            assert app.house_offset == 7
            assert math.isclose(app.ideal_angle_deg, 180.0, abs_tol=0.1)

    def test_opposition_exact_orb(self) -> None:
        """Exact opposition should have orb near 0."""
        sun, moon = make_opposition_pair()
        service = DrikService()
        result = service.calculate_aspects((sun, moon))
        for app in result.aspects:
            assert math.isclose(app.orb_deg, 0.0, abs_tol=0.1)


class TestMarsSpecialAspects:
    def test_4th_aspect(self) -> None:
        """Mars at 0, target at 90 — 4th house aspect."""
        mars, sun = make_mars_4th_aspect()
        service = DrikService()
        result = service.calculate_aspects((mars, sun))
        mars_aspects = [a for a in result.aspects if a.source_planet == BodyId.MARS]
        assert len(mars_aspects) == 1
        assert mars_aspects[0].aspect_type == AspectType.MARS_SPECIAL
        assert mars_aspects[0].house_offset == 4
        assert math.isclose(mars_aspects[0].ideal_angle_deg, 90.0, abs_tol=0.1)

    def test_8th_aspect(self) -> None:
        """Mars at 0, target at 210 — 8th house aspect."""
        mars, sun = make_mars_8th_aspect()
        service = DrikService()
        result = service.calculate_aspects((mars, sun))
        mars_aspects = [a for a in result.aspects if a.source_planet == BodyId.MARS]
        assert len(mars_aspects) == 1
        assert mars_aspects[0].aspect_type == AspectType.MARS_SPECIAL
        assert mars_aspects[0].house_offset == 8
        assert math.isclose(mars_aspects[0].ideal_angle_deg, 210.0, abs_tol=0.1)


class TestJupiterSpecialAspects:
    def test_5th_aspect(self) -> None:
        """Jupiter at 0, target at 120 — 5th house aspect."""
        jup, sun = make_jupiter_5th_aspect()
        service = DrikService()
        result = service.calculate_aspects((jup, sun))
        jup_aspects = [a for a in result.aspects if a.source_planet == BodyId.JUPITER]
        assert len(jup_aspects) == 1
        assert jup_aspects[0].aspect_type == AspectType.JUPITER_SPECIAL
        assert jup_aspects[0].house_offset == 5

    def test_9th_aspect(self) -> None:
        """Jupiter at 0, target at 240 — 9th house aspect."""
        jup, sun = make_jupiter_9th_aspect()
        service = DrikService()
        result = service.calculate_aspects((jup, sun))
        jup_aspects = [a for a in result.aspects if a.source_planet == BodyId.JUPITER]
        assert len(jup_aspects) == 1
        assert jup_aspects[0].aspect_type == AspectType.JUPITER_SPECIAL
        assert jup_aspects[0].house_offset == 9


class TestSaturnSpecialAspects:
    def test_3rd_aspect(self) -> None:
        """Saturn at 0, target at 60 — 3rd house aspect."""
        sat, sun = make_saturn_3rd_aspect()
        service = DrikService()
        result = service.calculate_aspects((sat, sun))
        sat_aspects = [a for a in result.aspects if a.source_planet == BodyId.SATURN]
        assert len(sat_aspects) == 1
        assert sat_aspects[0].aspect_type == AspectType.SATURN_SPECIAL
        assert sat_aspects[0].house_offset == 3

    def test_10th_aspect(self) -> None:
        """Saturn at 0, target at 270 — 10th house aspect."""
        sat, sun = make_saturn_10th_aspect()
        service = DrikService()
        result = service.calculate_aspects((sat, sun))
        sat_aspects = [a for a in result.aspects if a.source_planet == BodyId.SATURN]
        assert len(sat_aspects) == 1
        assert sat_aspects[0].aspect_type == AspectType.SATURN_SPECIAL
        assert sat_aspects[0].house_offset == 10


class TestNoAspect:
    def test_no_aspect_for_non_aspecting_pair(self) -> None:
        """Mercury at 0, Sun at 30 — 2nd house, no aspect."""
        mercury = make_planet_state(BodyId.MERCURY, 0.0)
        sun = make_planet_state(BodyId.SUN, 30.0)
        service = DrikService()
        result = service.calculate_aspects((mercury, sun))
        mercury_aspects = [a for a in result.aspects if a.source_planet == BodyId.MERCURY]
        assert len(mercury_aspects) == 0


class TestOrb:
    def test_within_orb(self) -> None:
        """Aspect slightly off exact should still be detected."""
        sun = make_planet_state(BodyId.SUN, 0.0)
        moon = make_planet_state(BodyId.MOON, 175.0)  # 5 degrees off 180
        service = DrikService(DrikConfig(default_orb_deg=6.0))
        result = service.calculate_aspects((sun, moon))
        sun_aspects = [a for a in result.aspects if a.source_planet == BodyId.SUN]
        assert len(sun_aspects) == 1
        assert sun_aspects[0].orb_deg < 6.0

    def test_outside_orb(self) -> None:
        """Aspect far from exact should not be detected."""
        sun = make_planet_state(BodyId.SUN, 0.0)
        moon = make_planet_state(BodyId.MOON, 150.0)  # 30 degrees off 180
        service = DrikService(DrikConfig(default_orb_deg=6.0))
        result = service.calculate_aspects((sun, moon))
        sun_aspects = [a for a in result.aspects if a.source_planet == BodyId.SUN]
        assert len(sun_aspects) == 0


class TestGetAspectRules:
    def test_rules_count(self) -> None:
        service = DrikService()
        rules = service.get_aspect_rules()
        # 9 planets, each with at least 1 rule (7th house)
        assert len(rules) >= 9

    def test_mars_has_3_rules(self) -> None:
        service = DrikService()
        rules = service.get_aspect_rules()
        mars_rules = [r for r in rules if r.source_planet == BodyId.MARS]
        assert len(mars_rules) == 3  # 4th, 7th, 8th


class TestValidation:
    def test_empty_planet_states(self) -> None:
        service = DrikService()
        from drik.errors import InvalidDrikRequestError
        with pytest.raises(InvalidDrikRequestError):
            service.calculate_aspects(planet_states=())

    def test_non_tuple_input(self) -> None:
        service = DrikService()
        from drik.errors import InvalidDrikRequestError
        with pytest.raises(InvalidDrikRequestError):
            service.calculate_aspects(planet_states=[make_planet_state(BodyId.SUN, 0.0)])  # type: ignore[arg-type]
