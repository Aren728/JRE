"""QA requirement 16: astronomical calculations contain NO astrological
interpretation.

The result envelope exposes raw astronomy only: positions, speeds, retrograde
state, metadata. No rashi/nakshatra/house/yoga/dasha/gochar/prediction
quantities are computed or emitted. The static gate (unit) scans the source;
this test scans the actual runtime output of the real provider.
"""

from __future__ import annotations

from tests.integration.astronomy.conftest import make_request

FORBIDDEN = (
    "rashi",
    "nakshatra",
    "bhava",
    "yoga",
    "dasha",
    "gochar",
    "benefic",
    "malefic",
    "house",
    "prediction",
    "varga",
    "kundali",
)


def test_result_has_no_astrology_fields(service):
    result = service.compute(make_request())
    d = result.to_dict()
    keys = " ".join(k.lower() for k in d)
    pos_keys = " ".join(k.lower() for k in d["positions"][0])
    combined = f"{keys} {pos_keys}"
    for term in FORBIDDEN:
        assert term not in combined


def test_position_fields_are_strictly_astronomical(service):
    result = service.compute(make_request())
    allowed = {
        "body",
        "longitude_tropical",
        "longitude_sidereal",
        "latitude",
        "distance_au",
        "speed_longitude",
        "speed_latitude",
        "speed_distance",
        "retrograde",
        "position_type",
        "ayanamsa_value",
    }
    for pos in result.positions:
        assert set(pos.to_dict().keys()) == allowed


def test_service_output_only_astronomy(service):
    result = service.compute(make_request())
    # The envelope carries exactly the documented sections.
    assert set(result.to_dict().keys()) == {
        "request_snapshot",
        "timestamp_utc_iso",
        "timestamp_local_iso",
        "julian_day_ut",
        "positions",
        "provider",
        "provider_run",
        "config",
    }
