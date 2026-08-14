"""Generic vs Individual separation (req. L) with the real ephemeris."""

from __future__ import annotations

import datetime as dt

from tests.integration.jyotish.conftest import make_birth


def test_generic_planetary_state_has_no_birth_fields(service):
    states = service.planetary_state(dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", 0.0, 0.0)
    for state in states:
        payload = state.to_dict()
        assert "birth" not in payload
        assert "natal" not in payload
        assert "house_number" not in payload


def test_generic_pair_geometry_no_bhava(service):
    states = service.planetary_state(dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", 0.0, 0.0)
    pairs = service.pair_geometry(states)
    assert all(p.same_bhava is None for p in pairs)
    assert all(p.same_rashi is not None for p in pairs)


def test_individual_chart_echoes_birth_snapshot(service):
    birth = make_birth()
    chart = service.chart(birth)
    assert chart.birth_snapshot == birth
    assert chart.lagna is not None
    assert len(chart.bhavas) == 12
    assert len(chart.planet_states) == 9


def test_individual_transit_against_kundali(service):
    from jyotish.models import TransitReferencePoint

    birth = make_birth()
    result = service.transit_through_houses(
        birth, dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC",
        reference=TransitReferencePoint.LAGNA,
    )
    assert result.birth_snapshot == birth
    assert len(result.entries) == 9
    for entry in result.entries:
        assert 1 <= entry.natal_house_number <= 12
        assert entry.natal_house_lord is not None
    # No interpretation: entries carry only geometric facts.
    for entry in result.entries:
        payload = entry.to_dict()
        blob = str(payload).lower()
        for term in ("good", "bad", "fortune", "wealth", "marriage", "career", "prediction"):
            assert term not in blob


def test_same_instant_generic_and_natal_agree(service):
    """The natal planetary states equal the generic states for the same instant."""
    birth = make_birth()
    chart = service.chart(birth)
    generic = service.planetary_state(
        dt.date(1990, 6, 15), dt.time(10, 0, 0), "Asia/Kolkata", birth.latitude, birth.longitude
    )
    for natal, gen in zip(chart.planet_states, generic, strict=True):
        assert natal.body == gen.body
        assert natal.longitude_used == gen.longitude_used
        assert natal.rashi == gen.rashi
