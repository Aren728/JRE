"""Runtime output contains NO astrological interpretation (req. I, §16).

The static gate scans source; these tests scan actual runtime payloads from
the real provider, mirroring the JRE-002 no-interpretation test.
"""

from __future__ import annotations

import datetime as dt

from tests.integration.jyotish.conftest import make_birth

FORBIDDEN = (
    "benefic",
    "malefic",
    "yoga",
    "dasha",
    "gochar",
    "prediction",
    "varga",
    "muhurta",
    "wealth",
    "marriage",
    "career",
    "fortune",
    "auspicious",
    "inauspicious",
)


def _assert_no_interpretation(blob: str, label: str):
    lowered = blob.lower()
    for term in FORBIDDEN:
        assert term not in lowered, f"{label} contains interpretation term {term!r}"


def test_planet_state_payload_clean(service):
    states = service.planetary_state(dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", 0.0, 0.0)
    for state in states:
        _assert_no_interpretation(str(state.to_dict()), "PlanetState")


def test_pair_geometry_payload_clean(service):
    states = service.planetary_state(dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC", 0.0, 0.0)
    pairs = service.pair_geometry(states)
    for pair in pairs:
        _assert_no_interpretation(str(pair.to_dict()), "PairGeometry")


def test_chart_payload_clean(service):
    chart = service.chart(make_birth())
    _assert_no_interpretation(str(chart.to_dict()), "NatalChart")


def test_transit_event_payload_clean(service):
    from astronomy.models import BodyId
    from jyotish.models import TransitEventKind

    events = service.events_between(
        "2001-01-01T00:00:00Z", "2001-06-01T00:00:00Z",
        (BodyId.SUN, BodyId.MOON),
        (TransitEventKind.RASHI_INGRESS,),
    )
    assert events
    for event in events:
        _assert_no_interpretation(str(event.to_dict()), "TransitEvent")


def test_transit_through_houses_payload_clean(service):
    from jyotish.models import TransitReferencePoint

    result = service.transit_through_houses(
        make_birth(), dt.date(2000, 1, 1), dt.time(12, 0, 0), "UTC",
        reference=TransitReferencePoint.MOON,
    )
    _assert_no_interpretation(str(result.to_dict()), "TransitThroughHouses")
