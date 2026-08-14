"""``JyotishService`` facade with deterministic fakes (both modes).

GENERIC vs INDIVIDUAL separation (req. L): generic calls never involve birth
data; individual calls echo birth data as a snapshot only.
"""

from __future__ import annotations

import datetime as dt

import pytest
from tests.unit.jyotish.conftest import FakeAstronomy, FakeEclipseProvider, FakeHouseProvider

from astronomy.models import BodyId
from jyotish.eclipse import EclipseRegistry
from jyotish.errors import (
    InvalidBirthDataError,
    InvalidConfigError,
)
from jyotish.houses import HouseCuspRegistry
from jyotish.models import (
    BirthData,
    HouseSystem,
    RashiId,
    TransitReferencePoint,
    ZodiacMode,
)
from jyotish.service import JyotishService


def _service(**overrides):
    astronomy = FakeAstronomy()
    house_registry = HouseCuspRegistry()
    house_registry.register(FakeHouseProvider(), tuple(HouseSystem))
    eclipse_registry = EclipseRegistry()
    eclipse_registry.register(FakeEclipseProvider())
    config = overrides.pop("config", None)
    return JyotishService(
        astronomy=astronomy,
        house_registry=house_registry,
        eclipse_registry=eclipse_registry,
        config=config,
    )


def test_generic_planetary_state_no_birth_data():
    service = _service()
    states = service.planetary_state(
        dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", 0.0, 0.0
    )
    assert len(states) == 9
    assert all(s.body is not None for s in states)
    for state in states:
        assert 0.0 <= state.longitude_used < 360.0
        assert state.rashi in RashiId
        assert state.timestamp_utc_iso  # echoed from astronomy
        assert state.provider_id == "fake.astronomy"
        assert state.ephemeris_version == "18"


def test_generic_bodies_subset():
    service = _service()
    states = service.planetary_state(
        dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", 0.0, 0.0,
        bodies=(BodyId.MOON, BodyId.SUN),
    )
    assert [s.body for s in states] == [BodyId.SUN, BodyId.MOON]


def test_generic_pair_geometry():
    service = _service()
    states = service.planetary_state(
        dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", 0.0, 0.0
    )
    pairs = service.pair_geometry(states)
    assert len(pairs) == 36
    assert all(p.same_bhava is None for p in pairs)  # generic mode: no chart


def test_generic_events_between():
    service = _service()
    events = service.events_between(
        "2000-01-01T00:00:00Z", "2000-02-01T00:00:00Z",
        (BodyId.SUN, BodyId.MOON),
    )
    # Fake astronomy moves the Sun ~0.98 deg/day, Moon ~13 deg/day -> many events.
    assert len(events) > 10
    assert all(e.body in (BodyId.SUN, BodyId.MOON) for e in events)


def test_individual_chart_echoes_birth_snapshot():
    service = _service()
    birth = BirthData(
        date="1990-06-15", time="10:00:00", timezone="Asia/Kolkata",
        latitude=28.6139, longitude=77.209,
    )
    chart = service.chart(birth)
    assert chart.birth_snapshot == birth
    assert len(chart.bhavas) == 12
    assert chart.lagna.rashi in RashiId
    assert chart.provider_metadata  # astronomy + house provider metadata


def test_individual_chart_bhavas_consistent():
    service = _service()
    birth = BirthData(
        date="1990-06-15", time="10:00:00", timezone="Asia/Kolkata",
        latitude=28.6139, longitude=77.209,
    )
    chart = service.chart(birth)
    # Each planet is an occupant of exactly one bhava.
    for state in chart.planet_states:
        containing = [b for b in chart.bhavas if state.body in b.occupants]
        assert len(containing) == 1, f"{state.body.value} in {len(containing)} bhavas"


def test_transit_through_houses_references():
    service = _service()
    birth = BirthData(
        date="1990-06-15", time="10:00:00", timezone="Asia/Kolkata",
        latitude=28.6139, longitude=77.209,
    )
    for reference in (
        TransitReferencePoint.LAGNA, TransitReferencePoint.MOON, TransitReferencePoint.SUN
    ):
        result = service.transit_through_houses(
            birth, dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", reference=reference
        )
        assert result.reference is reference
        assert len(result.entries) == 9
        for entry in result.entries:
            assert 1 <= entry.natal_house_number <= 12
            assert entry.natal_house_lord is not None
        # Different references produce different numbering for at least one body.
        assert result.entries[0].natal_house_number >= 1


def test_transit_through_houses_references_differ():
    service = _service()
    birth = BirthData(
        date="1990-06-15", time="10:00:00", timezone="Asia/Kolkata",
        latitude=28.6139, longitude=77.209,
    )
    lagna = service.transit_through_houses(
        birth, dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", reference=TransitReferencePoint.LAGNA
    )
    moon = service.transit_through_houses(
        birth, dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", reference=TransitReferencePoint.MOON
    )
    # Sun/Moon rashi differ from lagna rashi, so at least one house number differs.
    lagna_numbers = {e.body: e.natal_house_number for e in lagna.entries}
    moon_numbers = {e.body: e.natal_house_number for e in moon.entries}
    assert any(lagna_numbers[b] != moon_numbers[b] for b in lagna_numbers)


def test_invalid_birth_date_raises():
    service = _service()
    birth = BirthData(
        date="1500-01-01", time="10:00:00", timezone="Asia/Kolkata",
        latitude=28.6139, longitude=77.209,
    )
    with pytest.raises(InvalidBirthDataError, match="before the accepted range"):
        service.chart(birth)


def test_invalid_birth_latitude_raises():
    service = _service()
    birth = BirthData(
        date="1990-06-15", time="10:00:00", timezone="Asia/Kolkata",
        latitude=95.0, longitude=77.209,
    )
    with pytest.raises(InvalidBirthDataError, match="latitude"):
        service.chart(birth)


def test_sidereal_without_ayanamsa_rejected():
    from jyotish.models import JyotishConfig

    service = _service(config=None)
    with pytest.raises(InvalidConfigError, match="ayanamsa"):
        service.planetary_state(
            dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", 0.0, 0.0,
            config=JyotishConfig(zodiac_mode=ZodiacMode.SIDEREAL, ayanamsa=None),
        )


def test_tropical_mode_config():
    from jyotish.models import JyotishConfig

    service = _service()
    states = service.planetary_state(
        dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", 0.0, 0.0,
        config=JyotishConfig(zodiac_mode=ZodiacMode.TROPICAL, ayanamsa=None),
    )
    for state in states:
        assert state.longitude_used == state.longitude_tropical


def test_config_echo_in_results():
    from jyotish.models import JyotishConfig

    cfg = JyotishConfig(house_system=HouseSystem.PLACIDUS)
    service = _service(config=cfg)
    birth = BirthData(
        date="1990-06-15", time="10:00:00", timezone="Asia/Kolkata",
        latitude=28.6139, longitude=77.209,
    )
    chart = service.chart(birth)
    assert chart.config == cfg


def test_ephemeris_version_pin_mismatch_raises():
    from jyotish.errors import ProviderCompatibilityError
    from jyotish.models import JyotishConfig

    service = _service()
    with pytest.raises(ProviderCompatibilityError, match="ephemeris version pin"):
        service.planetary_state(
            dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", 0.0, 0.0,
            config=JyotishConfig(ephemeris_version="17"),
        )


def test_ephemeris_version_pin_match_passes():
    from jyotish.models import JyotishConfig

    service = _service()
    states = service.planetary_state(
        dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", 0.0, 0.0,
        config=JyotishConfig(ephemeris_version="18"),
    )
    assert states


def test_unknown_house_system_raises_typed_error():
    """A raw-string house_system must raise ``InvalidConfigError`` at the
    service boundary (SPEC §19/§20) — never an AttributeError inside the
    house registry (TEST-PLAN §5)."""
    from jyotish.models import JyotishConfig

    service = _service()
    birth = BirthData(
        date="1990-06-15", time="10:00:00", timezone="Asia/Kolkata",
        latitude=28.6139, longitude=77.209,
    )
    with pytest.raises(InvalidConfigError, match="house_system"):
        service.chart(birth, config=JyotishConfig(house_system="BOGUS"))  # type: ignore[arg-type]


def test_unknown_reference_point_raises_typed_error():
    """An unknown transit reference point must raise
    ``UnsupportedReferencePointError`` (SPEC §14.2 / TEST-PLAN §5) — never an
    AttributeError from formatting the error message."""
    from jyotish.errors import UnsupportedReferencePointError

    service = _service()
    birth = BirthData(
        date="1990-06-15", time="10:00:00", timezone="Asia/Kolkata",
        latitude=28.6139, longitude=77.209,
    )
    with pytest.raises(UnsupportedReferencePointError, match="unknown reference"):
        service.transit_through_houses(
            birth, dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC",
            reference="BOGUS",  # type: ignore[arg-type]
        )


def test_empty_config_dict_shape_accepted_end_to_end():
    """DATA-CONTRACT §10 documents ``"config": {}`` for the eclipse query;
    the documented shape must work end-to-end (defaults, not ayanamsa=None
    which SIDEREAL mode would reject)."""
    from jyotish.serialize import config_from_dict

    service = _service()
    events = service.eclipses(
        "2000-01-01T00:00:00Z", "2000-02-01T00:00:00Z",
        config=config_from_dict({}),
    )
    assert events


def test_generic_individual_same_core():
    """Both modes derive states via the same astronomy path (req. L)."""
    service = _service()
    birth = BirthData(
        date="1990-06-15", time="10:00:00", timezone="Asia/Kolkata",
        latitude=28.6139, longitude=77.209,
    )
    chart = service.chart(birth)
    # The same astronomy fake yields the same JD for the same instant; the
    # natal and generic paths must agree on the underlying longitude frames.
    natal_sun = next(s for s in chart.planet_states if s.body is BodyId.SUN)
    generic_sun = next(
        s
        for s in service.planetary_state(
            dt.date(1990, 6, 15), dt.time(10, 0, 0), "Asia/Kolkata", 28.6139, 77.209
        )
        if s.body is BodyId.SUN
    )
    assert natal_sun.longitude_used == generic_sun.longitude_used
    assert natal_sun.rashi is generic_sun.rashi
