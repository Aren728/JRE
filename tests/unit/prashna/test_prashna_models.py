"""Unit tests for JRE-019 Prashna domain models."""

from __future__ import annotations

from jyotish import BodyId, NakshatraId, RashiId

from prashna.models import (
    DEFAULT_HOUSE_MAPPINGS,
    PRASHNA_VERSION,
    PrashnaCategory,
    PrashnaChart,
    PrashnaConfig,
    PrashnaHouseMapping,
    PrashnaReport,
    QueryLocation,
    compute_prashna_lagna,
    resolve_house_mapping,
)


# --------------------------------------------------------------------------- #
# QueryLocation
# --------------------------------------------------------------------------- #


class TestQueryLocation:
    def test_creation(self) -> None:
        loc = QueryLocation(latitude=28.6139, longitude=77.2090)
        assert loc.latitude == 28.6139
        assert loc.longitude == 77.2090

    def test_to_dict(self) -> None:
        loc = QueryLocation(latitude=10.0, longitude=20.0)
        d = loc.to_dict()
        assert d["latitude"] == 10.0
        assert d["longitude"] == 20.0

    def test_frozen(self) -> None:
        loc = QueryLocation(latitude=10.0, longitude=20.0)
        import pytest
        with pytest.raises(AttributeError):
            loc.latitude = 0.0  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# PrashnaCategory enum
# --------------------------------------------------------------------------- #


class TestPrashnaCategory:
    def test_all_values(self) -> None:
        expected = {
            "WEALTH", "CAREER", "MARRIAGE", "HEALTH", "EDUCATION",
            "PROPERTY", "LITIGATION", "TRAVEL", "CHILDREN", "GENERAL",
        }
        actual = {c.value for c in PrashnaCategory}
        assert actual == expected

    def test_from_string(self) -> None:
        assert PrashnaCategory("WEALTH") == PrashnaCategory.WEALTH
        assert PrashnaCategory("CAREER") == PrashnaCategory.CAREER

    def test_invalid_string_raises(self) -> None:
        import pytest
        with pytest.raises(ValueError):
            PrashnaCategory("INVALID")


# --------------------------------------------------------------------------- #
# compute_prashna_lagna
# --------------------------------------------------------------------------- #


class TestComputePrashnaLagna:
    def test_sun_lord_gives_leo(self) -> None:
        assert compute_prashna_lagna(BodyId.SUN) == RashiId.SIMHA

    def test_moon_lord_gives_cancer(self) -> None:
        assert compute_prashna_lagna(BodyId.MOON) == RashiId.KARKA

    def test_mars_lord_gives_aries(self) -> None:
        assert compute_prashna_lagna(BodyId.MARS) == RashiId.MESHA

    def test_mercury_lord_gives_virgo(self) -> None:
        assert compute_prashna_lagna(BodyId.MERCURY) == RashiId.KANYA

    def test_jupiter_lord_gives_sagittarius(self) -> None:
        assert compute_prashna_lagna(BodyId.JUPITER) == RashiId.DHANUSHA

    def test_venus_lord_gives_taurus(self) -> None:
        assert compute_prashna_lagna(BodyId.VENUS) == RashiId.VRISHABHA

    def test_saturn_lord_gives_capricorn(self) -> None:
        assert compute_prashna_lagna(BodyId.SATURN) == RashiId.MAKARA

    def test_all_lords_give_valid_rashi(self) -> None:
        for lord in [BodyId.SUN, BodyId.MOON, BodyId.MARS, BodyId.MERCURY,
                     BodyId.JUPITER, BodyId.VENUS, BodyId.SATURN]:
            result = compute_prashna_lagna(lord)
            assert isinstance(result, RashiId)


# --------------------------------------------------------------------------- #
# resolve_house_mapping
# --------------------------------------------------------------------------- #


class TestResolveHouseMapping:
    def test_wealth_mapping(self) -> None:
        mapping = resolve_house_mapping(PrashnaCategory.WEALTH, DEFAULT_HOUSE_MAPPINGS)
        assert mapping.primary_house == 2
        assert mapping.secondary_house == 11
        assert mapping.query_category == PrashnaCategory.WEALTH

    def test_career_mapping(self) -> None:
        mapping = resolve_house_mapping(PrashnaCategory.CAREER, DEFAULT_HOUSE_MAPPINGS)
        assert mapping.primary_house == 10
        assert mapping.secondary_house == 6

    def test_marriage_mapping(self) -> None:
        mapping = resolve_house_mapping(PrashnaCategory.MARRIAGE, DEFAULT_HOUSE_MAPPINGS)
        assert mapping.primary_house == 7
        assert mapping.secondary_house == 2

    def test_health_mapping(self) -> None:
        mapping = resolve_house_mapping(PrashnaCategory.HEALTH, DEFAULT_HOUSE_MAPPINGS)
        assert mapping.primary_house == 1
        assert mapping.secondary_house == 8

    def test_education_mapping(self) -> None:
        mapping = resolve_house_mapping(PrashnaCategory.EDUCATION, DEFAULT_HOUSE_MAPPINGS)
        assert mapping.primary_house == 4
        assert mapping.secondary_house == 9

    def test_property_mapping(self) -> None:
        mapping = resolve_house_mapping(PrashnaCategory.PROPERTY, DEFAULT_HOUSE_MAPPINGS)
        assert mapping.primary_house == 4
        assert mapping.secondary_house == 11

    def test_litigation_mapping(self) -> None:
        mapping = resolve_house_mapping(PrashnaCategory.LITIGATION, DEFAULT_HOUSE_MAPPINGS)
        assert mapping.primary_house == 6
        assert mapping.secondary_house == 7

    def test_travel_mapping(self) -> None:
        mapping = resolve_house_mapping(PrashnaCategory.TRAVEL, DEFAULT_HOUSE_MAPPINGS)
        assert mapping.primary_house == 3
        assert mapping.secondary_house == 12

    def test_children_mapping(self) -> None:
        mapping = resolve_house_mapping(PrashnaCategory.CHILDREN, DEFAULT_HOUSE_MAPPINGS)
        assert mapping.primary_house == 5
        assert mapping.secondary_house == 11

    def test_general_mapping(self) -> None:
        mapping = resolve_house_mapping(PrashnaCategory.GENERAL, DEFAULT_HOUSE_MAPPINGS)
        assert mapping.primary_house == 1
        assert mapping.secondary_house == 7

    def test_unknown_category_falls_back_to_general(self) -> None:
        mapping = resolve_house_mapping(PrashnaCategory.GENERAL, {})
        assert mapping.primary_house == 1
        assert mapping.secondary_house == 7


# --------------------------------------------------------------------------- #
# PrashnaHouseMapping
# --------------------------------------------------------------------------- #


class TestPrashnaHouseMapping:
    def test_to_dict(self) -> None:
        m = PrashnaHouseMapping(
            query_category=PrashnaCategory.CAREER,
            primary_house=10,
            secondary_house=6,
        )
        d = m.to_dict()
        assert d["query_category"] == "CAREER"
        assert d["primary_house"] == 10
        assert d["secondary_house"] == 6


# --------------------------------------------------------------------------- #
# PrashnaChart
# --------------------------------------------------------------------------- #


class TestPrashnaChart:
    def test_to_dict(self) -> None:
        chart = PrashnaChart(
            query_time_utc="2024-01-15T10:30:00Z",
            query_location=QueryLocation(latitude=28.0, longitude=77.0),
            prashna_lagna=RashiId.MESHA,
            query_moon_rashi=RashiId.VRISHABHA,
        )
        d = chart.to_dict()
        assert d["query_time_utc"] == "2024-01-15T10:30:00Z"
        assert d["prashna_lagna"] == "MESHA"
        assert d["query_moon_rashi"] == "VRISHABHA"
        assert d["query_location"]["latitude"] == 28.0


# --------------------------------------------------------------------------- #
# PrashnaReport
# --------------------------------------------------------------------------- #


class TestPrashnaReport:
    def test_to_dict(self) -> None:
        report = PrashnaReport(
            chart=PrashnaChart(
                query_time_utc="2024-01-15T10:30:00Z",
                query_location=QueryLocation(latitude=28.0, longitude=77.0),
                prashna_lagna=RashiId.MESHA,
                query_moon_rashi=RashiId.VRISHABHA,
            ),
            house_mapping=PrashnaHouseMapping(
                query_category=PrashnaCategory.WEALTH,
                primary_house=2,
                secondary_house=11,
            ),
        )
        d = report.to_dict()
        assert "chart" in d
        assert "house_mapping" in d
        assert d["version"] == PRASHNA_VERSION

    def test_version(self) -> None:
        assert PRASHNA_VERSION == "0.1.0"


# --------------------------------------------------------------------------- #
# PrashnaConfig
# --------------------------------------------------------------------------- #


class TestPrashnaConfig:
    def test_default_config(self) -> None:
        config = PrashnaConfig()
        assert config.version == PRASHNA_VERSION
        assert config.default_category == "GENERAL"
        assert "WEALTH" in config.house_mappings
        assert config.house_mappings["WEALTH"] == (2, 11)

    def test_to_dict(self) -> None:
        config = PrashnaConfig()
        d = config.to_dict()
        assert d["version"] == PRASHNA_VERSION
        assert d["default_category"] == "GENERAL"
