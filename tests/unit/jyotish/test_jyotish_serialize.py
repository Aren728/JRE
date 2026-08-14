"""Serialization: stable machine-readable output, exact float round-trip."""

from __future__ import annotations

import json

from tests.unit.jyotish.conftest import make_planet_state

from jyotish.models import (
    BirthData,
    EclipseClassification,
    EclipseContact,
    EclipseEvent,
    EclipseKind,
    JyotishConfig,
    Pada,
    TransitEvent,
    TransitEventKind,
    TransitReferencePoint,
)
from jyotish.serialize import (
    birth_from_dict,
    config_from_dict,
    eclipse_query_from_dict,
    planetary_request_from_dict,
    result_to_dict,
    result_to_json,
    transit_query_from_dict,
)


def test_planet_state_serialization_shape():
    state = make_planet_state()
    data = json.loads(result_to_json(state))
    assert data["body"] == "SUN"
    assert data["rashi"] == "SIMHA"  # 120 deg
    assert isinstance(data["pada"], int)
    assert data["timestamp_utc_iso"] == "2000-01-01T12:00:00Z"
    assert data["retrograde"] == "DIRECT"


def test_exact_float_round_trip():
    state = make_planet_state(longitude_used=119.2566111903)
    data = json.loads(result_to_json(state))
    assert data["longitude_used"] == 119.2566111903


def test_jyotish_config_round_trip():
    config = JyotishConfig()
    restored = config_from_dict(json.loads(json.dumps(config.to_dict())))
    assert restored == config


def test_birth_data_round_trip():
    birth = BirthData(
        date="1990-06-15", time="10:00:00", timezone="Asia/Kolkata",
        latitude=28.6139, longitude=77.209,
    )
    restored = birth_from_dict(json.loads(json.dumps(birth.to_dict())))
    assert restored == birth


def test_transit_event_serialization():
    event = TransitEvent(
        body="SUN",  # type: ignore[arg-type]
        kind=TransitEventKind.RASHI_INGRESS,
        event_julian_day_ut=2451545.5,
        event_utc_iso="2000-01-02T00:00:00Z",
        boundary_deg=30.0,
        reached="VRISHABHA",  # type: ignore[arg-type]
        direction="DIRECT",  # type: ignore[arg-type]
        search_metadata=None,  # type: ignore[arg-type]
    )
    data = result_to_dict(event)
    assert data["kind"] == "RASHI_INGRESS"
    assert data["boundary_deg"] == 30.0


def test_eclipse_event_serialization():
    event = EclipseEvent(
        kind=EclipseKind.SOLAR,
        classification=EclipseClassification.TOTAL,
        maximum_jd_ut=2451545.5,
        maximum_utc_iso="2000-01-02T00:00:00Z",
        contacts=(EclipseContact("MAX", 2451545.5, "2000-01-02T00:00:00Z"),),
        magnitude=1.0,
        node_positions=(),
        solar_lunar_positions=(),
        geographic_visibility=None,
        pre_event_interval_days=0.5,
        post_event_interval_days=0.5,
        provider_id="fake.eclipse",
        ephemeris_version="fake",
    )
    data = result_to_dict(event)
    assert data["kind"] == "SOLAR"
    assert data["classification"] == "TOTAL"
    assert data["contacts"][0]["phase"] == "MAX"
    assert data["geographic_visibility"] is None


def test_pada_serializes_as_int():
    # 17.0° is within BHARANI (13°20′–26°40′) at 3°40′ into it -> pada 2.
    state = make_planet_state(longitude_used=17.0)
    assert state.pada is Pada.PADA_2
    data = json.loads(result_to_json(state))
    assert data["pada"] == 2


def test_query_from_dict_normalizers():
    p = planetary_request_from_dict(
        {
            "date": "1990-06-15", "time": "10:00:00",
            "timezone": "Asia/Kolkata", "latitude": "28.6139",
            "longitude": "77.209",
        }
    )
    assert p["latitude"] == 28.6139
    assert p["bodies"] is None
    t = transit_query_from_dict(
        {"start_utc_iso": "2000-01-01T00:00:00Z", "end_utc_iso": "2000-01-02T00:00:00Z"}
    )
    assert t["kinds"] is None
    e = eclipse_query_from_dict(
        {
            "start_utc_iso": "2000-01-01T00:00:00Z",
            "end_utc_iso": "2000-02-01T00:00:00Z",
            "kind": "LUNAR",
        }
    )
    assert e["kind"] == "LUNAR"


def test_serialization_contains_no_interpretation():
    state = make_planet_state()
    blob = json.dumps(result_to_dict(state)).lower()
    for term in ("benefic", "malefic", "yoga", "dasha", "gochar", "prediction", "kundali"):
        assert term not in blob


def test_transit_reference_point_serialization():
    assert TransitReferencePoint.LAGNA.value == "LAGNA"
    data = result_to_dict(TransitReferencePoint.MOON)
    assert data == "MOON"
