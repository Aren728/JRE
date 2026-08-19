"""JRE-012 Drik model tests."""

from __future__ import annotations

import math

from jyotish import BodyId

from drik.models import (
    DRIK_VERSION,
    DEFAULT_ASPECT_HOUSES,
    HOUSE_OFFSET_DEGREES,
    AspectApplication,
    AspectDirection,
    AspectRule,
    AspectType,
    DrikConfig,
    DrikResult,
    validate,
)


class TestConstants:
    def test_version(self) -> None:
        assert DRIK_VERSION == "0.1.0"

    def test_all_planets_have_aspect_rules(self) -> None:
        for body in BodyId:
            assert body.value in DEFAULT_ASPECT_HOUSES

    def test_all_planets_have_standard_aspect(self) -> None:
        for planet, houses in DEFAULT_ASPECT_HOUSES.items():
            assert 7 in houses, f"{planet} missing 7th house aspect"

    def test_mars_special_aspects(self) -> None:
        houses = DEFAULT_ASPECT_HOUSES[BodyId.MARS]
        assert 4 in houses
        assert 8 in houses

    def test_jupiter_special_aspects(self) -> None:
        houses = DEFAULT_ASPECT_HOUSES[BodyId.JUPITER]
        assert 5 in houses
        assert 9 in houses

    def test_saturn_special_aspects(self) -> None:
        houses = DEFAULT_ASPECT_HOUSES[BodyId.SATURN]
        assert 3 in houses
        assert 10 in houses

    def test_house_offset_degrees(self) -> None:
        assert HOUSE_OFFSET_DEGREES[7] == 180.0
        assert HOUSE_OFFSET_DEGREES[4] == 90.0
        assert HOUSE_OFFSET_DEGREES[8] == 210.0
        assert HOUSE_OFFSET_DEGREES[5] == 120.0
        assert HOUSE_OFFSET_DEGREES[9] == 240.0
        assert HOUSE_OFFSET_DEGREES[3] == 60.0
        assert HOUSE_OFFSET_DEGREES[10] == 270.0


class TestAspectType:
    def test_standard(self) -> None:
        assert AspectType.STANDARD.value == "STANDARD"

    def test_mars_special(self) -> None:
        assert AspectType.MARS_SPECIAL.value == "MARS_SPECIAL"


class TestAspectDirection:
    def test_applying(self) -> None:
        assert AspectDirection.APPLYING.value == "APPLYING"

    def test_separating(self) -> None:
        assert AspectDirection.SEPARATING.value == "SEPARATING"

    def test_exact(self) -> None:
        assert AspectDirection.EXACT.value == "EXACT"


class TestAspectRule:
    def test_construction(self) -> None:
        rule = AspectRule(
            source_planet=BodyId.MARS,
            target_house_offset=4,
            aspect_type=AspectType.MARS_SPECIAL,
        )
        assert rule.source_planet == BodyId.MARS
        assert rule.target_house_offset == 4

    def test_to_dict(self) -> None:
        from drik.serialize import result_to_dict
        rule = AspectRule(
            source_planet=BodyId.MARS,
            target_house_offset=4,
            aspect_type=AspectType.MARS_SPECIAL,
        )
        d = result_to_dict(rule)
        assert d["source_planet"] == "MARS"
        assert d["target_house_offset"] == 4


class TestAspectApplication:
    def test_construction(self) -> None:
        app = AspectApplication(
            source_planet=BodyId.SUN,
            target_planet=BodyId.MOON,
            aspect_type=AspectType.STANDARD,
            ideal_angle_deg=180.0,
            angular_distance_deg=180.0,
            orb_deg=0.0,
            direction=AspectDirection.EXACT,
            house_offset=7,
        )
        assert app.source_planet == BodyId.SUN
        assert app.orb_deg == 0.0


class TestDrikResult:
    def test_aspects_for(self) -> None:
        app = AspectApplication(
            source_planet=BodyId.SUN,
            target_planet=BodyId.MOON,
            aspect_type=AspectType.STANDARD,
            ideal_angle_deg=180.0,
            angular_distance_deg=180.0,
            orb_deg=0.0,
            direction=AspectDirection.EXACT,
            house_offset=7,
        )
        result = DrikResult(aspects=(app,))
        assert len(result.aspects_for(BodyId.SUN)) == 1
        assert len(result.aspects_for(BodyId.MOON)) == 0

    def test_aspects_involving(self) -> None:
        app = AspectApplication(
            source_planet=BodyId.SUN,
            target_planet=BodyId.MOON,
            aspect_type=AspectType.STANDARD,
            ideal_angle_deg=180.0,
            angular_distance_deg=180.0,
            orb_deg=0.0,
            direction=AspectDirection.EXACT,
            house_offset=7,
        )
        result = DrikResult(aspects=(app,))
        assert len(result.aspects_involving(BodyId.SUN)) == 1
        assert len(result.aspects_involving(BodyId.MOON)) == 1
        assert len(result.aspects_involving(BodyId.MARS)) == 0


class TestDrikConfig:
    def test_defaults(self) -> None:
        config = DrikConfig()
        assert config.version == "0.1.0"
        assert config.default_orb_deg == 6.0

    def test_from_dict(self) -> None:
        data = {
            "version": "0.2.0",
            "default_orb_deg": 10.0,
            "aspect_houses": {"SUN": [7], "MARS": [4, 7, 8]},
        }
        config = DrikConfig.from_dict(data)
        assert config.version == "0.2.0"
        assert config.default_orb_deg == 10.0

    def test_validate(self) -> None:
        config = DrikConfig()
        validated = validate(config)
        assert validated is config

    def test_validate_empty_version(self) -> None:
        from drik.errors import InvalidDrikConfigError
        import pytest
        config = DrikConfig(version="")
        with pytest.raises(InvalidDrikConfigError):
            validate(config)

    def test_validate_negative_orb(self) -> None:
        from drik.errors import InvalidDrikConfigError
        import pytest
        config = DrikConfig(default_orb_deg=-1.0)
        with pytest.raises(InvalidDrikConfigError):
            validate(config)
