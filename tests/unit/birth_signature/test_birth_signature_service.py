"""Unit tests for BirthSignatureService."""

from __future__ import annotations

import json

import pytest

from birth_signature.errors import InvalidSignatureRequestError
from birth_signature.models import (
    AmPm,
    BirthSignature,
    DayNightPeriod,
    Tithi,
    Yoga,
)
from birth_signature.service import BirthSignatureService
from jyotish import BodyId, NakshatraId, PlanetState, RashiId


class TestServiceInit:
    """Tests for BirthSignatureService initialization."""

    def test_default_init(self) -> None:
        service = BirthSignatureService()
        assert service is not None


class TestCreateSignature:
    """Tests for the create_signature method."""

    def test_basic_signature(
        self,
        sun_at_10_moon_at_33: tuple[
            tuple[PlanetState, ...], object
        ],
    ) -> None:
        """Test basic signature creation with known inputs."""

        planet_states, lagna = sun_at_10_moon_at_33
        service = BirthSignatureService()
        sig = service.create_signature(
            planet_states,
            lagna,  # type: ignore[arg-type]
            local_hour=10.0,
            local_minute=30.0,
        )

        assert isinstance(sig, BirthSignature)
        # Sun at 10° in ASHWINI (MESHA)
        assert sig.sun_rashi == RashiId.MESHA
        # Moon at 33° in ROHINI (VRISHABHA)
        assert sig.moon_rashi == RashiId.VRISHABHA
        # Moon at 33° -> KRITTIKA (26.667° to 40.0°)
        assert sig.nakshatra == NakshatraId.KRITTIKA
        # Tithi: Moon-Sun = 23°, floor(23/12)+1 = 2 = SHUKLA_DVITIYA
        assert sig.tithi == Tithi.SHUKLA_DVITIYA
        # AM since hour < 12
        assert sig.am_pm == AmPm.AM
        # Day since 6 <= hour < 18
        assert sig.day_night_period == DayNightPeriod.DAY

    def test_conjunction_signature(
        self,
        sun_at_0_moon_at_0: tuple[
            tuple[PlanetState, ...], object
        ],
    ) -> None:
        """Test signature with Sun and Moon conjunct."""

        planet_states, lagna = sun_at_0_moon_at_0
        service = BirthSignatureService()
        sig = service.create_signature(
            planet_states,
            lagna,  # type: ignore[arg-type]
            local_hour=6.0,
        )

        # Both at 0° -> PRATIPADA
        assert sig.tithi == Tithi.SHUKLA_PRATIPADA
        # Yoga: (0+0)/13.333 = 0, yoga = 1 = VISHKAMBHA
        assert sig.yoga == Yoga.VISHKAMBHA
        # Both in MESHA
        assert sig.sun_rashi == RashiId.MESHA
        assert sig.moon_rashi == RashiId.MESHA

    def test_full_moon_signature(
        self,
        sun_at_100_moon_at_200: tuple[
            tuple[PlanetState, ...], object
        ],
    ) -> None:
        """Test signature with near-full-moon configuration."""

        planet_states, lagna = sun_at_100_moon_at_200
        service = BirthSignatureService()
        sig = service.create_signature(
            planet_states,
            lagna,  # type: ignore[arg-type]
            local_hour=20.0,
        )

        # Moon-Sun = 100°, floor(100/12)+1 = 9 = SHUKLA_NAVAMI
        assert sig.tithi == Tithi.SHUKLA_NAVAMI
        # PM since hour >= 12
        assert sig.am_pm == AmPm.PM
        # Night since hour >= 18
        assert sig.day_night_period == DayNightPeriod.NIGHT

    def test_wrapping_distance(
        self,
        sun_at_250_moon_at_50: tuple[
            tuple[PlanetState, ...], object
        ],
    ) -> None:
        """Test signature with wrapping Sun-Moon distance."""

        planet_states, lagna = sun_at_250_moon_at_50
        service = BirthSignatureService()
        sig = service.create_signature(
            planet_states,
            lagna,  # type: ignore[arg-type]
            local_hour=14.0,
        )

        # (50-250) % 360 = 160°, floor(160/12)+1 = 14 = SHUKLA_CHATURDASHI
        assert sig.tithi == Tithi.SHUKLA_CHATURDASHI
        assert sig.am_pm == AmPm.PM

    def test_invalid_request_empty_states(self) -> None:
        """Test that empty planet_states raises error."""
        lagna = _make_lagna(45.0)
        service = BirthSignatureService()
        with pytest.raises(InvalidSignatureRequestError):
            service.create_signature((), lagna)

    def test_invalid_request_no_sun(self) -> None:
        """Test that missing SUN raises error."""

        service = BirthSignatureService()
        moon = _make_planet_state(BodyId.MOON, 33.0)
        lagna = _make_lagna(45.0)
        with pytest.raises(InvalidSignatureRequestError):
            service.create_signature((moon,), lagna)

    def test_invalid_request_no_moon(self) -> None:
        """Test that missing MOON raises error."""
        service = BirthSignatureService()
        sun = _make_planet_state(BodyId.SUN, 10.0)
        lagna = _make_lagna(45.0)
        with pytest.raises(InvalidSignatureRequestError):
            service.create_signature((sun,), lagna)

    def test_invalid_request_wrong_type(self) -> None:
        """Test that wrong types raise error."""
        service = BirthSignatureService()
        with pytest.raises(InvalidSignatureRequestError):
            service.create_signature("not a tuple", _make_lagna(45.0))  # type: ignore[arg-type]

    def test_deterministic_output(
        self,
        sun_at_10_moon_at_33: tuple[
            tuple[PlanetState, ...], object
        ],
    ) -> None:
        """Test that output is deterministic."""

        planet_states, lagna = sun_at_10_moon_at_33
        service = BirthSignatureService()
        sig1 = service.create_signature(
            planet_states,
            lagna,  # type: ignore[arg-type]
            local_hour=10.0,
        )
        sig2 = service.create_signature(
            planet_states,
            lagna,  # type: ignore[arg-type]
            local_hour=10.0,
        )
        assert sig1.deterministic_id == sig2.deterministic_id
        d1 = json.dumps(sig1.to_dict(), sort_keys=True)
        d2 = json.dumps(sig2.to_dict(), sort_keys=True)
        assert d1 == d2

    def test_all_fields_populated(
        self,
        sun_at_10_moon_at_33: tuple[
            tuple[PlanetState, ...], object
        ],
    ) -> None:
        """Test that all BirthSignature fields are populated."""

        planet_states, lagna = sun_at_10_moon_at_33
        service = BirthSignatureService()
        sig = service.create_signature(
            planet_states,
            lagna,  # type: ignore[arg-type]
            local_hour=10.0,
        )

        assert sig.lagna is not None
        assert sig.sun_rashi is not None
        assert sig.moon_rashi is not None
        assert sig.nakshatra is not None
        assert sig.pada is not None
        assert sig.weekday is not None
        assert sig.hora is not None
        assert sig.tithi is not None
        assert sig.karana is not None
        assert sig.yoga is not None
        assert sig.day_night_period is not None
        assert sig.am_pm is not None
        assert sig.deterministic_id != ""

    def test_only_fact_output(
        self,
        sun_at_10_moon_at_33: tuple[
            tuple[PlanetState, ...], object
        ],
    ) -> None:
        """CRITICAL: Verify that output contains only facts, no interpretations."""

        planet_states, lagna = sun_at_10_moon_at_33
        service = BirthSignatureService()
        sig = service.create_signature(
            planet_states,
            lagna,  # type: ignore[arg-type]
            local_hour=10.0,
        )

        d = sig.to_dict()
        all_values = " ".join(str(v) for v in d.values()).lower()

        # No interpretation keywords
        assert "personality" not in all_values
        assert "temperament" not in all_values
        assert "character" not in all_values
        assert "nature" not in all_values
        assert "prediction" not in all_values
        assert "fortune" not in all_values

    def test_to_dict_roundtrip(
        self,
        sun_at_10_moon_at_33: tuple[
            tuple[PlanetState, ...], object
        ],
    ) -> None:
        """Test that to_dict produces valid JSON."""

        planet_states, lagna = sun_at_10_moon_at_33
        service = BirthSignatureService()
        sig = service.create_signature(
            planet_states,
            lagna,  # type: ignore[arg-type]
            local_hour=10.0,
        )
        d = sig.to_dict()
        # Should be JSON-serializable
        json_str = json.dumps(d, sort_keys=True)
        assert len(json_str) > 0


# --------------------------------------------------------------------------- #
# Helpers (local, not shared with conftest to avoid import issues)
# --------------------------------------------------------------------------- #


def _make_planet_state(
    body: BodyId,
    longitude: float,
    julian_day_ut: float = 2451545.0,
) -> PlanetState:
    """Build a PlanetState at a specific longitude."""
    from jyotish import (
        DmsValue,
        RetrogradeState,
        degree_in_nakshatra,
        degree_in_rashi,
        lord_of,
        nakshatra_of,
        pada_of,
        rashi_of,
    )

    return PlanetState(
        body=body,
        longitude_tropical=longitude,
        longitude_sidereal=longitude,
        longitude_used=longitude,
        dms=DmsValue(degrees=int(longitude), minutes=0, seconds=0.0, sign=1),
        rashi=rashi_of(longitude),
        degree_in_rashi=degree_in_rashi(longitude),
        nakshatra=nakshatra_of(longitude),
        nakshatra_lord=lord_of(nakshatra_of(longitude)),
        pada=pada_of(longitude),
        degree_in_nakshatra=degree_in_nakshatra(longitude),
        latitude=0.0,
        speed_longitude=13.0,
        retrograde=RetrogradeState.DIRECT,
        timestamp_utc_iso="2000-01-01T12:00:00Z",
        julian_day_ut=julian_day_ut,
        provider_id="test",
        ephemeris_version="test",
    )


def _make_lagna(ascendant_longitude: float = 45.0) -> object:
    """Build a LagnaState at a specific ascendant longitude."""
    from jyotish import (
        DmsValue,
        HouseSystem,
        LagnaState,
        degree_in_nakshatra,
        degree_in_rashi,
        lord_of,
        nakshatra_of,
        pada_of,
        rashi_of,
    )

    return LagnaState(
        ascendant_longitude_deg=ascendant_longitude,
        dms=DmsValue(
            degrees=int(ascendant_longitude),
            minutes=0,
            seconds=0.0,
            sign=1,
        ),
        rashi=rashi_of(ascendant_longitude),
        degree_in_rashi=degree_in_rashi(ascendant_longitude),
        nakshatra=nakshatra_of(ascendant_longitude),
        nakshatra_lord=lord_of(nakshatra_of(ascendant_longitude)),
        pada=pada_of(ascendant_longitude),
        degree_in_nakshatra=degree_in_nakshatra(ascendant_longitude),
        bhava_relationship=None,
        house_system=HouseSystem.WHOLE_SIGN,
    )
