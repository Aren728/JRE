"""JRE-012 Drik integration tests.

End-to-end tests verifying:
- Full aspect graph computation for multiple planets
- Special aspects for Mars, Jupiter, Saturn
- Serialization round-trip
- Determinism across multiple calls
"""

from __future__ import annotations

import json
import math

import pytest
from jyotish import BodyId

from drik.models import (
    AspectDirection,
    AspectType,
    DrikConfig,
    DrikResult,
)
from drik.serialize import result_to_dict, result_to_json
from drik.service import DrikService
from tests.unit.drik.conftest import make_planet_state


class TestFullAspectGraph:
    """Integration: compute aspect graph for a realistic chart."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = DrikService()
        self.sun = make_planet_state(BodyId.SUN, 100.0)
        self.moon = make_planet_state(BodyId.MOON, 280.0)
        self.mars = make_planet_state(BodyId.MARS, 45.0)
        self.mercury = make_planet_state(BodyId.MERCURY, 115.0)
        self.jupiter = make_planet_state(BodyId.JUPITER, 200.0)
        self.venus = make_planet_state(BodyId.VENUS, 85.0)
        self.saturn = make_planet_state(BodyId.SATURN, 320.0)
        self.states = (
            self.sun, self.moon, self.mars, self.mercury,
            self.jupiter, self.venus, self.saturn,
        )
        self.result = self.service.calculate_aspects(self.states)

    def test_result_has_aspects(self) -> None:
        assert len(self.result.aspects) > 0

    def test_all_aspects_have_valid_planets(self) -> None:
        for app in self.result.aspects:
            assert isinstance(app.source_planet, BodyId)
            assert isinstance(app.target_planet, BodyId)

    def test_no_self_aspects(self) -> None:
        for app in self.result.aspects:
            assert app.source_planet != app.target_planet

    def test_all_aspects_have_valid_type(self) -> None:
        for app in self.result.aspects:
            assert isinstance(app.aspect_type, AspectType)

    def test_all_aspects_have_valid_direction(self) -> None:
        for app in self.result.aspects:
            assert isinstance(app.direction, AspectDirection)

    def test_orb_non_negative(self) -> None:
        for app in self.result.aspects:
            assert app.orb_deg >= 0.0

    def test_ideal_angle_valid(self) -> None:
        valid_angles = {60.0, 90.0, 120.0, 180.0, 210.0, 240.0, 270.0}
        for app in self.result.aspects:
            assert app.ideal_angle_deg in valid_angles

    def test_sun_moon_opposition(self) -> None:
        """Sun at 100, Moon at 280 — should have 7th house aspect."""
        sun_moon = [
            a for a in self.result.aspects
            if {a.source_planet, a.target_planet} == {BodyId.SUN, BodyId.MOON}
        ]
        assert len(sun_moon) >= 1
        assert any(a.house_offset == 7 for a in sun_moon)


class TestMarsSpecialAspectsIntegration:
    """Integration: verify Mars special aspects in a multi-planet chart."""

    def test_mars_4th_aspect_detected(self) -> None:
        """Mars at 0 (Aries), Jupiter at 90 (Cancer) — Mars 4th aspect."""
        service = DrikService()
        mars = make_planet_state(BodyId.MARS, 0.0)
        jupiter = make_planet_state(BodyId.JUPITER, 90.0)
        result = service.calculate_aspects((mars, jupiter))
        mars_aspects = [a for a in result.aspects if a.source_planet == BodyId.MARS]
        assert any(a.house_offset == 4 for a in mars_aspects)

    def test_mars_8th_aspect_detected(self) -> None:
        """Mars at 0, Sun at 210 — Mars 8th aspect."""
        service = DrikService()
        mars = make_planet_state(BodyId.MARS, 0.0)
        sun = make_planet_state(BodyId.SUN, 210.0)
        result = service.calculate_aspects((mars, sun))
        mars_aspects = [a for a in result.aspects if a.source_planet == BodyId.MARS]
        assert any(a.house_offset == 8 for a in mars_aspects)


class TestDeterminismIntegration:
    """Integration: verify deterministic output."""

    def test_same_inputs_same_output(self) -> None:
        service = DrikService()
        sun = make_planet_state(BodyId.SUN, 0.0)
        moon = make_planet_state(BodyId.MOON, 180.0)
        mars = make_planet_state(BodyId.MARS, 90.0)

        r1 = service.calculate_aspects((sun, moon, mars))
        r2 = service.calculate_aspects((sun, moon, mars))

        assert len(r1.aspects) == len(r2.aspects)
        for a1, a2 in zip(r1.aspects, r2.aspects):
            assert a1.source_planet == a2.source_planet
            assert a1.target_planet == a2.target_planet
            assert a1.orb_deg == a2.orb_deg

    def test_json_deterministic(self) -> None:
        service = DrikService()
        sun = make_planet_state(BodyId.SUN, 0.0)
        moon = make_planet_state(BodyId.MOON, 180.0)

        r1 = service.calculate_aspects((sun, moon))
        r2 = service.calculate_aspects((sun, moon))

        assert result_to_json(r1) == result_to_json(r2)


class TestSerializationIntegration:
    """Integration: verify serialization round-trip."""

    def test_dict_round_trip(self) -> None:
        service = DrikService()
        sun = make_planet_state(BodyId.SUN, 0.0)
        moon = make_planet_state(BodyId.MOON, 180.0)
        result = service.calculate_aspects((sun, moon))

        d = result_to_dict(result)
        assert isinstance(d, dict)
        assert "aspects" in d
        assert len(d["aspects"]) == len(result.aspects)

    def test_json_round_trip(self) -> None:
        service = DrikService()
        sun = make_planet_state(BodyId.SUN, 0.0)
        moon = make_planet_state(BodyId.MOON, 180.0)
        result = service.calculate_aspects((sun, moon))

        json_str = result_to_json(result)
        parsed = json.loads(json_str)
        assert "aspects" in parsed


class TestBoundaryConditions:
    def test_single_planet(self) -> None:
        """Single planet should produce no aspects."""
        service = DrikService()
        sun = make_planet_state(BodyId.SUN, 0.0)
        result = service.calculate_aspects((sun,))
        assert len(result.aspects) == 0

    def test_two_planets_no_aspect(self) -> None:
        """Two planets in non-aspecting positions."""
        service = DrikService()
        sun = make_planet_state(BodyId.SUN, 0.0)
        mercury = make_planet_state(BodyId.MERCURY, 30.0)  # 2nd house
        result = service.calculate_aspects((sun, mercury))
        sun_aspects = [a for a in result.aspects if a.source_planet == BodyId.SUN]
        assert len(sun_aspects) == 0

    def test_custom_orb(self) -> None:
        """Custom orb should affect detection."""
        sun = make_planet_state(BodyId.SUN, 0.0)
        moon = make_planet_state(BodyId.MOON, 170.0)  # 10 degrees off 180

        tight = DrikService(DrikConfig(default_orb_deg=5.0))
        loose = DrikService(DrikConfig(default_orb_deg=15.0))

        r_tight = tight.calculate_aspects((sun, moon))
        r_loose = loose.calculate_aspects((sun, moon))

        sun_tight = [a for a in r_tight.aspects if a.source_planet == BodyId.SUN]
        sun_loose = [a for a in r_loose.aspects if a.source_planet == BodyId.SUN]

        assert len(sun_tight) == 0  # Outside tight orb
        assert len(sun_loose) == 1  # Inside loose orb
