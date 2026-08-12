"""QA requirements 6, 7, 17: invalid datetime / coordinates / error handling.

All validation errors must surface as typed errors at the service boundary,
never as raw provider errors or silent fallback.
"""

from __future__ import annotations

import datetime as dt
import math

import pytest
from tests.integration.astronomy.conftest import make_request

from astronomy.errors import (
    EphemerisDataError,
    EphemerisError,
    InvalidCoordinatesError,
    InvalidTimestampError,
    UnsupportedProviderError,
)


@pytest.mark.parametrize(
    "timezone",
    ["IST", "PST", "EST", "GMT+5", "unknown/zone", "Mars/Olympus_Mons"],
)
def test_invalid_timezone(service, timezone):
    with pytest.raises(InvalidTimestampError):
        service.compute(make_request(timezone=timezone))


def test_dst_gap_local_time_rejected(service):
    # 2024-03-10 02:30 does not exist in America/New_York.
    with pytest.raises(InvalidTimestampError):
        service.compute(
            make_request(
                date=dt.date(2024, 3, 10),
                time=dt.time(2, 30, 0),
                timezone="America/New_York",
            )
        )


def test_pre_gregorian_date_rejected(service):
    with pytest.raises(InvalidTimestampError):
        service.compute(make_request(date=dt.date(1582, 10, 4)))


def test_invalid_latitude(service):
    for lat in (91.0, -90.1, math.nan, math.inf, -math.inf):
        with pytest.raises(InvalidCoordinatesError):
            service.compute(make_request(latitude=lat))


def test_invalid_longitude(service):
    for lon in (181.0, -180.5, math.nan, math.inf, -math.inf):
        with pytest.raises(InvalidCoordinatesError):
            service.compute(make_request(longitude=lon))


def test_boundary_coordinates_accepted(service):
    # Lat/lon at the extremes are valid.
    service.compute(make_request(latitude=90.0, longitude=180.0))
    service.compute(make_request(latitude=-90.0, longitude=-180.0))


def test_empty_bodies_rejected(service):
    with pytest.raises(EphemerisError, match="bodies must not be empty"):
        service.compute(make_request(bodies=()))


def test_unknown_provider_rejected(service):
    with pytest.raises(UnsupportedProviderError):
        service.compute(make_request(provider_id="no.such.provider"))


def test_fallback_disabled_raises_data_error(service, tmp_path):
    import shutil

    from tests.integration.astronomy.conftest import DATA_DIR

    from astronomy.models import CalculationConfig

    # A directory with the required files but a corrupted checksum forces the
    # SWIEPH data error path when fallback is disallowed.
    for name in ("sepl_18.se1", "semo_18.se1"):
        shutil.copy2(DATA_DIR / name, tmp_path / name)
    path = tmp_path / "sepl_18.se1"
    data = bytearray(path.read_bytes())
    data[100] ^= 0xFF
    path.write_bytes(bytes(data))

    config = CalculationConfig(
        ephemeris_path=str(tmp_path), allow_fallback=False
    )
    with pytest.raises(EphemerisDataError):
        service.compute(make_request(config=config))


def test_errors_are_typed_ephemeris_errors():
    assert issubclass(InvalidTimestampError, EphemerisError)
    assert issubclass(InvalidCoordinatesError, EphemerisError)
    assert issubclass(UnsupportedProviderError, EphemerisError)
    assert issubclass(EphemerisDataError, EphemerisError)
