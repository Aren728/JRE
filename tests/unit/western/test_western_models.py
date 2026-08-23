"""Unit tests for JRE-066 Western Astrology data models.

Tests enums, essential dignity evaluation, aspect calculation helpers,
and deterministic serialization.  No Swiss Ephemeris calls — pure logic.
"""

from __future__ import annotations

from src.western.models import (
    ASPECT_ANGLES,
    ASPECT_ORBS,
    DOMICILE_SIGNS,
    EXALTATION_SIGNS,
    SECONDARY_DOMICILE,
    WesternAspect,
    WesternAspectType,
    WesternChart,
    WesternDignity,
    WesternHouseSystem,
    WesternPlanet,
    _angular_distance,
    _degree_in_sign,
    _sign_index,
    _sign_name,
    compute_all_aspects,
    compute_aspect,
    evaluate_essential_dignity,
)

# ── Enum Tests ───────────────────────────────────────────────────────────────


class TestWesternPlanet:
    """WesternPlanet enum coverage."""

    def test_all_planets_defined(self) -> None:
        expected = {
            "SUN", "MOON", "MERCURY", "VENUS", "MARS",
            "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO",
            "NORTH_NODE", "SOUTH_NODE", "CHIRON",
        }
        actual = {p.value for p in WesternPlanet}
        assert actual == expected

    def test_planet_count(self) -> None:
        assert len(WesternPlanet) == 13

    def test_string_enum(self) -> None:
        assert WesternPlanet.SUN == "SUN"
        assert WesternPlanet.PLUTO == "PLUTO"


class TestWesternHouseSystem:
    """WesternHouseSystem enum coverage."""

    def test_all_systems(self) -> None:
        expected = {"PLACIDUS", "WHOLE_SIGN", "EQUAL"}
        actual = {h.value for h in WesternHouseSystem}
        assert actual == expected


class TestWesternDignity:
    """WesternDignity enum coverage."""

    def test_all_dignities(self) -> None:
        expected = {"DOMICILE", "EXALTATION", "DETRIMENT", "FALL", "PEREGRINE"}
        actual = {d.value for d in WesternDignity}
        assert actual == expected


class TestWesternAspectType:
    """WesternAspectType enum coverage."""

    def test_all_aspect_types(self) -> None:
        expected = {"CONJUNCTION", "OPPOSITION", "SQUARE", "TRINE", "SEXTILE"}
        actual = {a.value for a in WesternAspectType}
        assert actual == expected

    def test_aspect_count(self) -> None:
        assert len(WesternAspectType) == 5


# ── Sign Helper Tests ────────────────────────────────────────────────────────


class TestSignHelpers:
    """Tests for sign index/name/degree helpers."""

    def test_aries_start(self) -> None:
        assert _sign_index(0.0) == 0
        assert _sign_name(0.0) == "ARIES"

    def test_taurus_start(self) -> None:
        assert _sign_index(30.0) == 1
        assert _sign_name(30.0) == "TAURUS"

    def test_pisces_end(self) -> None:
        assert _sign_index(359.99) == 11
        assert _sign_name(359.99) == "PISCES"

    def test_wrap_around(self) -> None:
        assert _sign_index(360.0) == 0  # wraps to Aries

    def test_mid_sign(self) -> None:
        assert _sign_name(15.0) == "ARIES"
        assert _sign_name(45.0) == "TAURUS"
        assert _sign_name(345.0) == "PISCES"

    def test_degree_in_sign(self) -> None:
        assert abs(_degree_in_sign(0.0) - 0.0) < 1e-10
        assert abs(_degree_in_sign(30.0) - 0.0) < 1e-10
        assert abs(_degree_in_sign(15.5) - 15.5) < 1e-10
        assert abs(_degree_in_sign(359.99) - 29.99) < 0.01


# ── Essential Dignity Tests ──────────────────────────────────────────────────


class TestEssentialDignity:
    """Tests for evaluate_essential_dignity function."""

    def test_sun_in_leo_is_domicile(self) -> None:
        # Leo starts at 120°
        assert evaluate_essential_dignity(WesternPlanet.SUN, 135.0) == WesternDignity.DOMICILE

    def test_sun_in_aquarius_is_detriment(self) -> None:
        # Aquarius starts at 300°, opposite Leo (120°)
        assert evaluate_essential_dignity(WesternPlanet.SUN, 315.0) == WesternDignity.DETRIMENT

    def test_sun_in_aries_is_exaltation(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.SUN, 15.0) == WesternDignity.EXALTATION

    def test_sun_in_libra_is_fall(self) -> None:
        # Libra starts at 180°, opposite Aries (0°)
        assert evaluate_essential_dignity(WesternPlanet.SUN, 195.0) == WesternDignity.FALL

    def test_sun_in_taurus_is_peregrine(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.SUN, 45.0) == WesternDignity.PEREGRINE

    def test_moon_in_taurus_is_domicile(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.MOON, 45.0) == WesternDignity.DOMICILE

    def test_mars_in_aries_is_domicile(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.MARS, 15.0) == WesternDignity.DOMICILE

    def test_mars_in_scorpio_is_domicile_secondary(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.MARS, 225.0) == WesternDignity.DOMICILE

    def test_mars_in_capricorn_is_exaltation(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.MARS, 285.0) == WesternDignity.EXALTATION

    def test_mars_in_cancer_is_fall(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.MARS, 105.0) == WesternDignity.FALL

    def test_mars_in_libra_is_detriment(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.MARS, 195.0) == WesternDignity.DETRIMENT

    def test_jupiter_in_sagittarius_is_domicile(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.JUPITER, 255.0) == WesternDignity.DOMICILE

    def test_jupiter_in_pisces_is_secondary_domicile(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.JUPITER, 345.0) == WesternDignity.DOMICILE

    def test_jupiter_in_cancer_is_exaltation(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.JUPITER, 105.0) == WesternDignity.EXALTATION

    def test_saturn_in_capricorn_is_domicile(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.SATURN, 285.0) == WesternDignity.DOMICILE

    def test_saturn_in_aquarius_is_secondary_domicile(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.SATURN, 315.0) == WesternDignity.DOMICILE

    def test_saturn_in_libra_is_exaltation(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.SATURN, 195.0) == WesternDignity.EXALTATION

    def test_saturn_in_aries_is_fall(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.SATURN, 15.0) == WesternDignity.FALL

    def test_uranus_in_aquarius_is_domicile(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.URANUS, 315.0) == WesternDignity.DOMICILE

    def test_neptune_in_pisces_is_domicile(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.NEPTUNE, 345.0) == WesternDignity.DOMICILE

    def test_pluto_in_scorpio_is_domicile(self) -> None:
        assert evaluate_essential_dignity(WesternPlanet.PLUTO, 225.0) == WesternDignity.DOMICILE

    def test_sign_boundary_start(self) -> None:
        # Exactly at sign boundary
        assert evaluate_essential_dignity(WesternPlanet.SUN, 120.0) == WesternDignity.DOMICILE

    def test_sign_boundary_end(self) -> None:
        # Just before next sign
        assert evaluate_essential_dignity(WesternPlanet.SUN, 149.99) == WesternDignity.DOMICILE

    def test_dignity_tables_non_empty(self) -> None:
        assert len(DOMICILE_SIGNS) > 0
        assert len(EXALTATION_SIGNS) > 0
        assert len(SECONDARY_DOMICILE) > 0


# ── Aspect Calculation Tests ─────────────────────────────────────────────────


class TestAngularDistance:
    """Tests for _angular_distance helper."""

    def test_same_longitude(self) -> None:
        assert _angular_distance(90.0, 90.0) == 0.0

    def test_opposite(self) -> None:
        assert _angular_distance(0.0, 180.0) == 180.0

    def test_wrap_around(self) -> None:
        assert abs(_angular_distance(350.0, 10.0) - 20.0) < 1e-10

    def test_60_degrees(self) -> None:
        assert _angular_distance(0.0, 60.0) == 60.0

    def test_90_degrees(self) -> None:
        assert _angular_distance(0.0, 90.0) == 90.0


class TestComputeAspect:
    """Tests for compute_aspect function."""

    def test_exact_conjunction(self) -> None:
        result = compute_aspect(
            WesternPlanet.SUN, 90.0, 1.0,
            WesternPlanet.MOON, 90.0, 13.0,
        )
        assert result is not None
        assert result.aspect_type == WesternAspectType.CONJUNCTION
        assert result.orb == 0.0

    def test_exact_opposition(self) -> None:
        result = compute_aspect(
            WesternPlanet.SUN, 90.0, 1.0,
            WesternPlanet.MOON, 270.0, -1.0,
        )
        assert result is not None
        assert result.aspect_type == WesternAspectType.OPPOSITION
        assert result.orb == 0.0

    def test_exact_square(self) -> None:
        result = compute_aspect(
            WesternPlanet.SUN, 0.0, 1.0,
            WesternPlanet.MOON, 90.0, 13.0,
        )
        assert result is not None
        assert result.aspect_type == WesternAspectType.SQUARE
        assert result.orb == 0.0

    def test_exact_trine(self) -> None:
        result = compute_aspect(
            WesternPlanet.SUN, 0.0, 1.0,
            WesternPlanet.MOON, 120.0, 13.0,
        )
        assert result is not None
        assert result.aspect_type == WesternAspectType.TRINE
        assert result.orb == 0.0

    def test_exact_sextile(self) -> None:
        result = compute_aspect(
            WesternPlanet.SUN, 0.0, 1.0,
            WesternPlanet.MOON, 60.0, 13.0,
        )
        assert result is not None
        assert result.aspect_type == WesternAspectType.SEXTILE
        assert result.orb == 0.0

    def test_no_aspect_far_off(self) -> None:
        result = compute_aspect(
            WesternPlanet.SUN, 0.0, 1.0,
            WesternPlanet.MOON, 45.0, 13.0,
        )
        assert result is None

    def test_conjunction_within_orb(self) -> None:
        result = compute_aspect(
            WesternPlanet.SUN, 90.0, 1.0,
            WesternPlanet.MOON, 95.0, 13.0,
        )
        assert result is not None
        assert result.aspect_type == WesternAspectType.CONJUNCTION
        assert abs(result.orb - 5.0) < 1e-10

    def test_same_planet_returns_none(self) -> None:
        result = compute_aspect(
            WesternPlanet.SUN, 90.0, 1.0,
            WesternPlanet.SUN, 90.0, 1.0,
        )
        assert result is None

    def test_applying_aspect(self) -> None:
        # Speed difference means aspect is applying
        result = compute_aspect(
            WesternPlanet.SUN, 90.0, 1.0,
            WesternPlanet.MOON, 95.0, 13.0,
        )
        assert result is not None
        assert result.applying is True

    def test_aspect_angles_match_constants(self) -> None:
        assert ASPECT_ANGLES[WesternAspectType.CONJUNCTION] == 0.0
        assert ASPECT_ANGLES[WesternAspectType.OPPOSITION] == 180.0
        assert ASPECT_ANGLES[WesternAspectType.SQUARE] == 90.0
        assert ASPECT_ANGLES[WesternAspectType.TRINE] == 120.0
        assert ASPECT_ANGLES[WesternAspectType.SEXTILE] == 60.0

    def test_aspect_orbs_positive(self) -> None:
        for aspect_type, orb in ASPECT_ORBS.items():
            assert orb > 0, f"{aspect_type} has non-positive orb"


class TestComputeAllAspects:
    """Tests for compute_all_aspects function."""

    def test_empty_input(self) -> None:
        result = compute_all_aspects({})
        assert result == ()

    def test_single_planet(self) -> None:
        result = compute_all_aspects({WesternPlanet.SUN: (90.0, 1.0)})
        assert result == ()

    def test_conjunction_pair(self) -> None:
        positions = {
            WesternPlanet.SUN: (90.0, 1.0),
            WesternPlanet.MOON: (90.5, 13.0),
        }
        result = compute_all_aspects(positions)
        assert len(result) == 1
        assert result[0].aspect_type == WesternAspectType.CONJUNCTION

    def test_sorted_by_type_then_orb(self) -> None:
        positions = {
            WesternPlanet.SUN: (0.0, 1.0),
            WesternPlanet.MOON: (120.0, 13.0),
            WesternPlanet.MARS: (240.0, 0.5),
        }
        result = compute_all_aspects(positions)
        # Three trines: Sun-Moon, Sun-Mars, Moon-Mars (all 120°)
        assert len(result) == 3
        assert all(a.aspect_type == WesternAspectType.TRINE for a in result)
        # All orbs should be 0 (exact trines)
        assert all(a.orb == 0.0 for a in result)

    def test_no_duplicate_pairs(self) -> None:
        positions = {
            WesternPlanet.SUN: (0.0, 1.0),
            WesternPlanet.MOON: (90.0, 13.0),
        }
        result = compute_all_aspects(positions)
        # Only one aspect (Sun-Moon), not Moon-Sun
        assert len(result) == 1


# ── Data Class Tests ─────────────────────────────────────────────────────────


class TestWesternAspect:
    """WesternAspect dataclass tests."""

    def test_to_dict(self) -> None:
        aspect = WesternAspect(
            planet_a=WesternPlanet.SUN,
            planet_b=WesternPlanet.MOON,
            aspect_type=WesternAspectType.CONJUNCTION,
            exact_angle=90.0,
            orb=2.5,
            applying=True,
        )
        d = aspect.to_dict()
        assert d["planet_a"] == "SUN"
        assert d["planet_b"] == "MOON"
        assert d["aspect_type"] == "CONJUNCTION"
        assert d["exact_angle"] == 90.0
        assert d["orb"] == 2.5
        assert d["applying"] is True

    def test_frozen(self) -> None:
        aspect = WesternAspect(
            planet_a=WesternPlanet.SUN,
            planet_b=WesternPlanet.MOON,
            aspect_type=WesternAspectType.CONJUNCTION,
            exact_angle=0.0,
            orb=0.0,
            applying=False,
        )
        try:
            aspect.orb = 5.0  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass


class TestWesternChart:
    """WesternChart dataclass tests."""

    def test_deterministic_id_computed(self) -> None:
        chart = WesternChart(
            birth_date="2000-01-01",
            birth_time="12:00:00",
            latitude=40.0,
            longitude=-74.0,
            house_system=WesternHouseSystem.PLACIDUS,
            julian_day_ut=2451545.0,
            planet_positions=(),
            house_cusps=(),
            aspects=(),
            dignities={},
            ascendant=0.0,
            midheaven=0.0,
        )
        assert chart.deterministic_id != ""
        assert len(chart.deterministic_id) == 16

    def test_same_content_same_id(self) -> None:
        kwargs = dict(
            birth_date="2000-01-01",
            birth_time="12:00:00",
            latitude=40.0,
            longitude=-74.0,
            house_system=WesternHouseSystem.PLACIDUS,
            julian_day_ut=2451545.0,
            planet_positions=(),
            house_cusps=(),
            aspects=(),
            dignities={},
            ascendant=0.0,
            midheaven=0.0,
        )
        c1 = WesternChart(**kwargs)
        c2 = WesternChart(**kwargs)
        assert c1.deterministic_id == c2.deterministic_id

    def test_different_content_different_id(self) -> None:
        base = dict(
            birth_date="2000-01-01",
            birth_time="12:00:00",
            latitude=40.0,
            longitude=-74.0,
            house_system=WesternHouseSystem.PLACIDUS,
            julian_day_ut=2451545.0,
            planet_positions=(),
            house_cusps=(),
            aspects=(),
            dignities={},
            ascendant=0.0,
            midheaven=0.0,
        )
        c1 = WesternChart(**base)
        c2 = WesternChart(**{**base, "ascendant": 1.0})
        assert c1.deterministic_id != c2.deterministic_id

    def test_to_dict_roundtrip(self) -> None:
        chart = WesternChart(
            birth_date="2000-01-01",
            birth_time="12:00:00",
            latitude=40.0,
            longitude=-74.0,
            house_system=WesternHouseSystem.PLACIDUS,
            julian_day_ut=2451545.0,
            planet_positions=(),
            house_cusps=(),
            aspects=(),
            dignities={WesternPlanet.SUN: WesternDignity.DOMICILE},
            ascendant=123.456,
            midheaven=234.567,
        )
        d = chart.to_dict()
        assert d["birth_date"] == "2000-01-01"
        assert d["house_system"] == "PLACIDUS"
        assert d["dignities"]["SUN"] == "DOMICILE"
        assert d["ascendant"] == 123.456

    def test_frozen(self) -> None:
        chart = WesternChart(
            birth_date="2000-01-01",
            birth_time="12:00:00",
            latitude=40.0,
            longitude=-74.0,
            house_system=WesternHouseSystem.PLACIDUS,
            julian_day_ut=2451545.0,
            planet_positions=(),
            house_cusps=(),
            aspects=(),
            dignities={},
            ascendant=0.0,
            midheaven=0.0,
        )
        try:
            chart.ascendant = 1.0  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass
